#!/usr/bin/env python3
"""
Daemon Logger
Proper logging infrastructure for daemons with rotation and structured logging
"""

import sys
import logging
import json
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler

class DaemonLogger:
    def __init__(self, daemon_name, log_dir=None):
        self.daemon_name = daemon_name
        self.memory_dir = Path.home() / '.claude' / 'memory'

        if log_dir is None:
            self.log_dir = self.memory_dir / 'logs' / 'daemons'
        else:
            self.log_dir = Path(log_dir)

        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Log files
        self.daemon_log = self.log_dir / f'{daemon_name}.log'
        self.policy_log = self.memory_dir / 'logs' / 'policy-hits.log'
        self.health_log = self.memory_dir / 'logs' / 'health.log'

        # Create logger
        self.logger = self._create_logger()

    def _create_logger(self):
        """Create logger with rotation"""
        logger = logging.getLogger(self.daemon_name)
        logger.setLevel(logging.DEBUG)

        # Remove existing handlers
        logger.handlers.clear()

        # File handler with rotation (10MB max, 5 backups)
        file_handler = RotatingFileHandler(
            self.daemon_log,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)

        # Format: [timestamp] LEVEL | message
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Console handler for errors (optional)
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.ERROR)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        return logger

    def debug(self, message, **kwargs):
        """Log debug message"""
        if kwargs:
            message = f"{message} | {json.dumps(kwargs)}"
        self.logger.debug(message)

    def info(self, message, **kwargs):
        """Log info message"""
        if kwargs:
            message = f"{message} | {json.dumps(kwargs)}"
        self.logger.info(message)

    def warning(self, message, **kwargs):
        """Log warning message"""
        if kwargs:
            message = f"{message} | {json.dumps(kwargs)}"
        self.logger.warning(message)

    def error(self, message, **kwargs):
        """Log error message"""
        if kwargs:
            message = f"{message} | {json.dumps(kwargs)}"
        self.logger.error(message)

        # Also log to health.log
        self._log_to_health('ERROR', message)

    def critical(self, message, **kwargs):
        """Log critical message"""
        if kwargs:
            message = f"{message} | {json.dumps(kwargs)}"
        self.logger.critical(message)

        # Also log to health.log
        self._log_to_health('CRITICAL', message)

    def policy_hit(self, policy_name, action, context=None):
        """Log policy hit to policy-hits.log"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {policy_name} | {action}"

        if context:
            log_entry += f" | {context}"

        log_entry += "\n"

        # Write to policy-hits.log
        with open(self.policy_log, 'a', encoding='utf-8') as f:
            f.write(log_entry)

        # Also log to daemon log
        self.info(f"POLICY: {policy_name} | {action}")

    def health_event(self, event_type, message, severity='INFO'):
        """Log health event"""
        self._log_to_health(severity, f"{event_type}: {message}")

        # Also log to daemon log
        if severity == 'ERROR' or severity == 'CRITICAL':
            self.error(f"HEALTH: {event_type} | {message}")
        else:
            self.info(f"HEALTH: {event_type} | {message}")

    def _log_to_health(self, severity, message):
        """Write to health.log"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {self.daemon_name} | {severity} | {message}\n"

        with open(self.health_log, 'a', encoding='utf-8') as f:
            f.write(log_entry)

    def structured_log(self, event, data):
        """Log structured data as JSON"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'daemon': self.daemon_name,
            'event': event,
            'data': data
        }

        self.info(json.dumps(log_data))

    def log_startup(self, pid):
        """Log daemon startup"""
        self.info(f"Daemon started with PID {pid}")
        self.health_event('STARTUP', f'PID {pid}', 'INFO')

    def log_shutdown(self, reason='normal'):
        """Log daemon shutdown"""
        self.info(f"Daemon shutting down: {reason}")
        self.health_event('SHUTDOWN', reason, 'INFO')

    def log_iteration(self, iteration_num):
        """Log daemon iteration"""
        self.debug(f"Iteration {iteration_num}")

    def log_exception(self, exception, context=None):
        """Log exception with traceback"""
        import traceback

        tb = traceback.format_exc()
        message = f"Exception: {str(exception)}"

        if context:
            message += f" | Context: {context}"

        message += f"\n{tb}"

        self.error(message)

    def log_performance(self, operation, duration_ms, success=True):
        """Log performance metrics"""
        status = 'SUCCESS' if success else 'FAILED'
        self.debug(f"Performance: {operation} | {duration_ms}ms | {status}")

    def get_recent_logs(self, lines=50):
        """Get recent log lines"""
        if not self.daemon_log.exists():
            return []

        try:
            with open(self.daemon_log, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                return all_lines[-lines:]
        except:
            return []

    def rotate_logs(self):
        """Manually trigger log rotation"""
        for handler in self.logger.handlers:
            if isinstance(handler, RotatingFileHandler):
                handler.doRollover()

class MultiDaemonLogger:
    """Logger that can write to multiple daemon logs"""

    def __init__(self, daemon_names):
        self.loggers = {
            name: DaemonLogger(name)
            for name in daemon_names
        }

    def log_all(self, message, level='info'):
        """Log to all daemon logs"""
        for logger in self.loggers.values():
            getattr(logger, level)(message)

    def get_logger(self, daemon_name):
        """Get logger for specific daemon"""
        return self.loggers.get(daemon_name)

def test_logger():
    """Test daemon logger"""
    print("Testing daemon logger...")

    # Create test logger
    logger = DaemonLogger('test-daemon')

    print("1. Test basic logging")
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")

    print("2. Test structured logging")
    logger.structured_log('test_event', {'key': 'value', 'number': 123})

    print("3. Test policy hit")
    logger.policy_hit('test-policy', 'executed', 'test context')

    print("4. Test health event")
    logger.health_event('TEST', 'Testing health logging', 'INFO')

    print("5. Test startup/shutdown")
    logger.log_startup(12345)
    logger.log_shutdown('test complete')

    print("6. Test performance logging")
    logger.log_performance('test_operation', 150, success=True)

    print("7. Test exception logging")
    try:
        raise ValueError("Test exception")
    except Exception as e:
        logger.log_exception(e, context="test context")

    print("8. Get recent logs")
    recent = logger.get_recent_logs(10)
    print(f"   Recent logs: {len(recent)} lines")

    print("\n9. Check log files exist")
    print(f"   Daemon log: {logger.daemon_log.exists()}")
    print(f"   Policy log: {logger.policy_log.exists()}")
    print(f"   Health log: {logger.health_log.exists()}")

    print("\n[OK] All tests passed!")
    print(f"Log file: {logger.daemon_log}")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        test_logger()
    else:
        print("Daemon Logger Module")
        print("Usage in daemon scripts:")
        print("  from daemon_logger import DaemonLogger")
        print("  logger = DaemonLogger('my-daemon')")
        print("  logger.info('Message')")
        print("\nTest mode:")
        print("  python daemon-logger.py --test")
