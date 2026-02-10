# API Reference: Memory System v2.0

Complete reference for all scripts and their APIs.

---

## Phase 1: Context Management

### pre-execution-optimizer.py

**Purpose**: Optimize tool parameters before execution to reduce context usage.

#### CLI Usage

```bash
# Test optimizer
python pre-execution-optimizer.py --test-large-file

# Optimize Read parameters
python pre-execution-optimizer.py --optimize Read --params '{"file_path": "/path/to/file.py"}'

# Optimize Grep parameters
python pre-execution-optimizer.py --optimize Grep --params '{"pattern": "function", "path": "/path"}'

# Get statistics
python pre-execution-optimizer.py --stats
```

#### Python API

```python
from pre_execution_optimizer import PreExecutionOptimizer

optimizer = PreExecutionOptimizer()

# Optimize Read
result = optimizer.optimize('Read', {'file_path': '/path/to/large_file.py'})
# Returns: {
#   'should_optimize': True/False,
#   'optimized': {params with limits},
#   'reasoning': 'explanation',
#   'savings': 'estimated token savings'
# }

# Optimize Grep
result = optimizer.optimize('Grep', {'pattern': 'class', 'path': '/project'})
# Returns: {
#   'should_optimize': True/False,
#   'optimized': {params with head_limit},
#   'reasoning': 'explanation'
# }

# Get stats
stats = optimizer.get_statistics()
# Returns: {
#   'total_optimizations': N,
#   'by_tool': {...},
#   'total_savings_estimate': 'X tokens'
# }
```

#### Configuration

Edit in script:
```python
self.max_file_lines = 500  # Max lines to read without limit
self.grep_head_limit = 100  # Default head_limit for Grep
self.cache_threshold = 3    # File accesses before caching
```

---

### context-extractor.py

**Purpose**: Extract essential information from tool outputs after execution.

#### CLI Usage

```bash
# Extract from Read output
python context-extractor.py --extract-read "file contents..." "/path/to/file.py"

# Extract from Grep output
python context-extractor.py --extract-grep "grep results..." "search_pattern"

# Extract from Bash output
python context-extractor.py --extract-bash "command output..." "command"

# Get statistics
python context-extractor.py --stats
```

#### Python API

```python
from context_extractor import ContextExtractor

extractor = ContextExtractor()

# Extract from Read
summary = extractor.extract_read_output(
    content="full file contents...",
    file_path="/path/to/file.py"
)
# Returns: {
#   'type': 'summary',
#   'lines': N,
#   'summary': 'structure: classes, functions, imports',
#   'should_cache': True/False
# }

# Extract from Grep
summary = extractor.extract_grep_output(
    output="grep results...",
    pattern="search_term",
    file_count=50
)
# Returns: {
#   'type': 'summary',
#   'summary': 'key matches',
#   'full_results_in_log': True
# }

# Get stats
stats = extractor.get_statistics()
# Returns: {
#   'total_extractions': N,
#   'by_tool': {...},
#   'cache_recommendations': N
# }
```

---

### context-cache.py

**Purpose**: Intelligent caching system for file summaries and query results.

#### CLI Usage

```bash
# Get cache statistics
python context-cache.py --stats

# Get file summary from cache
python context-cache.py --get-summary "/path/to/file.py"

# Set file summary
python context-cache.py --set-summary "/path/to/file.py" "summary text"

# Clear expired entries
python context-cache.py --clear-expired

# Clear all cache
python context-cache.py --clear-all
```

#### Python API

```python
from context_cache import ContextCache

cache = ContextCache()

# Get file summary
summary = cache.get_file_summary('/path/to/file.py')
# Returns: summary string or None if not cached/expired

# Set file summary
cache.set_file_summary(
    file_path='/path/to/file.py',
    summary='File structure: 5 classes, 20 functions'
)

# Get query result
result = cache.get_query_result('search term')
# Returns: result string or None

# Set query result
cache.set_query_result(
    query='search term',
    result='search results...'
)

# Clear expired
cleared = cache.clear_expired()
# Returns: number of entries cleared

# Get stats
stats = cache.get_statistics()
# Returns: {
#   'summary_cache_entries': N,
#   'query_cache_entries': N,
#   'total_size_mb': X,
#   'hit_rate': 'X%'
# }
```

#### Configuration

```python
self.file_summary_ttl = 86400  # 24 hours
self.query_result_ttl = 3600   # 1 hour
self.max_cache_size_mb = 100   # Max cache size
```

---

### session-state.py

**Purpose**: Maintain session state outside Claude's context.

#### CLI Usage

```bash
# Initialize session
python session-state.py --init

# Add task
python session-state.py --add-task "Implement authentication"

# Mark task complete
python session-state.py --complete-task "Implement authentication"

# Add file
python session-state.py --add-file "/path/to/file.py" "Created user model"

# Add decision
python session-state.py --add-decision "Use JWT tokens"

# Get summary
python session-state.py --summary

# Save session
python session-state.py --save "session_name"

# Load session
python session-state.py --load "session_name"
```

#### Python API

```python
from session_state import SessionState

state = SessionState()

# Add task
state.add_task('Implement authentication')

# Complete task
state.complete_task('Implement authentication')

# Add file
state.add_file('/path/to/file.py', 'Created user model')

# Add decision
state.add_decision('decision_type', 'Use JWT tokens', 'Security requirement')

# Get summary
summary = state.get_summary()
# Returns: {
#   'active_tasks': [...],
#   'completed_tasks': [...],
#   'files_modified': [...],
#   'key_decisions': [...],
#   'pending_work': [...]
# }

# Save state
state.save_to_file('session_name')

# Load state
state.load_from_file('session_name')
```

---

### context-monitor-v2.py

**Purpose**: Enhanced context monitoring with actionable recommendations.

#### CLI Usage

```bash
# Get current status
python context-monitor-v2.py --current-status

# Simulate usage level
python context-monitor-v2.py --simulate 75

# Get recommendations
python context-monitor-v2.py --recommendations

# Initialize monitoring
python context-monitor-v2.py --init
```

#### Python API

```python
from context_monitor_v2 import ContextMonitorV2

monitor = ContextMonitorV2()

# Get current status
status = monitor.get_current_status()
# Returns: {
#   'percentage': 65.5,
#   'level': 'green',  # green/yellow/orange/red
#   'status': 'OK',
#   'recommendations': [...]
# }

# Get recommendations for level
recommendations = monitor.get_recommendations_for_level('yellow')
# Returns: [
#   'Use cached summaries instead of re-reading files',
#   'Reference session state for history',
#   ...
# ]

# Simulate usage
status = monitor.simulate_usage(85)
# Returns: status dict for 85% usage
```

#### Status Levels

| Level | Range | Status | Action |
|-------|-------|--------|--------|
| Green | <70% | OK | Normal operation |
| Yellow | 70-84% | Warning | Use cache, optimize |
| Orange | 85-89% | Critical | Reference state, compact |
| Red | 90%+ | Emergency | Save session, restart |

---

## Phase 2: Daemon Infrastructure

### daemon-manager.py

**Purpose**: Cross-platform daemon launcher and manager.

#### CLI Usage

```bash
# Start daemon
python daemon-manager.py --start context-daemon

# Start all daemons
python daemon-manager.py --start-all

# Stop daemon
python daemon-manager.py --stop context-daemon

# Stop all daemons
python daemon-manager.py --stop-all

# Restart daemon
python daemon-manager.py --restart context-daemon

# Get daemon status
python daemon-manager.py --status context-daemon

# Get all statuses (table format)
python daemon-manager.py --status-all --format table

# Get all statuses (JSON format)
python daemon-manager.py --status-all --format json

# Test Windows compatibility
python daemon-manager.py --test-windows
```

#### Python API

```python
from daemon_manager import DaemonManager

manager = DaemonManager()

# Start daemon
result = manager.start_daemon('context-daemon')
# Returns: {
#   'status': 'started'|'already_running'|'failed',
#   'pid': process_id,
#   'message': 'explanation'
# }

# Stop daemon
result = manager.stop_daemon('context-daemon')
# Returns: {
#   'status': 'stopped'|'not_running'|'failed',
#   'message': 'explanation'
# }

# Get status
status = manager.get_daemon_status('context-daemon')
# Returns: {
#   'daemon': 'context-daemon',
#   'running': True/False,
#   'pid': process_id or None,
#   'uptime': 'X minutes'
# }

# Get all statuses
statuses = manager.get_all_statuses()
# Returns: {
#   'context-daemon': {...},
#   'failure-prevention-daemon': {...},
#   ...
# }
```

#### Managed Daemons

1. context-daemon
2. failure-prevention-daemon
3. policy-daemon
4. session-daemon
5. skills-daemon
6. model-daemon
7. token-daemon
8. health-monitor

---

### pid-tracker.py

**Purpose**: Track and verify daemon PIDs with health monitoring.

#### CLI Usage

```bash
# Check if daemon is running
python pid-tracker.py --is-running context-daemon

# Get daemon PID
python pid-tracker.py --get-pid context-daemon

# Set daemon PID
python pid-tracker.py --set-pid context-daemon 12345

# Verify daemon (PID file matches running process)
python pid-tracker.py --verify context-daemon

# Verify all daemons
python pid-tracker.py --verify-all

# Get health score
python pid-tracker.py --health

# Kill daemon (for testing)
python pid-tracker.py --kill context-daemon
```

#### Python API

```python
from pid_tracker import PIDTracker

tracker = PIDTracker()

# Check if running
is_running = tracker.is_daemon_running('context-daemon')
# Returns: True/False

# Get PID
pid = tracker.get_daemon_pid('context-daemon')
# Returns: PID (int) or None

# Set PID
tracker.set_daemon_pid('context-daemon', 12345)

# Verify daemon
is_valid = tracker.verify_daemon('context-daemon')
# Returns: True if PID file matches running process

# Get health score
health = tracker.get_health_score()
# Returns: {
#   'total_daemons': 8,
#   'running_daemons': 8,
#   'health_score': 100.0,
#   'status': 'healthy'
# }

# Monitor health
report = tracker.monitor_health()
# Returns: {
#   'timestamp': '...',
#   'daemons': {daemon: status},
#   'health_score': X,
#   'issues': [...]
# }
```

---

### health-monitor-daemon.py

**Purpose**: Monitor daemon health and auto-restart dead daemons.

#### CLI Usage

```bash
# Start health monitor (as daemon)
python health-monitor-daemon.py --start

# Stop health monitor
python health-monitor-daemon.py --stop

# Get status
python health-monitor-daemon.py --status

# Run health check once (no daemon)
python health-monitor-daemon.py --check-once

# Get restart history
python health-monitor-daemon.py --history context-daemon
```

#### Configuration

Edit in script:
```python
CHECK_INTERVAL = 300  # 5 minutes
MAX_RESTARTS_PER_HOUR = 3
RESTART_COOLDOWN = 60  # seconds
```

#### Restart History

Located in: `~/.claude/memory/.restarts/{daemon}_restart_history.json`

Format:
```json
[
  {
    "restart_index": 1,
    "timestamp": "2026-02-09T12:00:00",
    "reason": "Process not found",
    "success": true,
    "new_pid": 12345
  }
]
```

---

### daemon-logger.py

**Purpose**: Proper logging infrastructure for daemons.

#### Python API Only

```python
from daemon_logger import DaemonLogger

logger = DaemonLogger('context-daemon')

# Log info
logger.info('Daemon started')

# Log warning
logger.warning('High memory usage')

# Log error
logger.error('Failed to process request')

# Log to policy hits
logger.log_policy_hit('CONTEXT_OPTIMIZATION', 'Applied pre-execution optimization')

# Log to health
logger.log_health_event('DAEMON_RESTART', 'Auto-restarted after crash')
```

#### Log Locations

- Daemon-specific: `~/.claude/memory/logs/daemons/{daemon-name}.log`
- Policy hits: `~/.claude/memory/logs/policy-hits.log`
- Health events: `~/.claude/memory/logs/health.log`

#### Log Format

```
[2026-02-09 12:00:00] INFO | Daemon started
[2026-02-09 12:00:01] WARNING | High memory usage: 250MB
[2026-02-09 12:00:02] ERROR | Failed to connect to service
```

---

## Phase 3: Failure Prevention

### failure-detector-v2.py

**Purpose**: Detect failures from logs and extract patterns.

#### CLI Usage

```bash
# Analyze log file
python failure-detector-v2.py --analyze logs/policy-hits.log

# Analyze all logs
python failure-detector-v2.py --analyze-all

# Get statistics
python failure-detector-v2.py --stats

# Update KB from detected failures
python failure-detector-v2.py --update-kb
```

#### Python API

```python
from failure_detector_v2 import FailureDetectorV2

detector = FailureDetectorV2()

# Detect failures in log
failures = detector.detect_failures_in_log('logs/policy-hits.log')
# Returns: [
#   {
#     'timestamp': '...',
#     'tool': 'Bash',
#     'error': 'command not found',
#     'context': {...}
#   }
# ]

# Group failures
groups = detector.group_failures(failures)
# Returns: {
#   'Bash': [...],
#   'Edit': [...],
#   ...
# }

# Extract pattern
pattern = detector.extract_pattern(failure_dict)
# Returns: {
#   'pattern_id': 'bash_windows_command',
#   'signature': 'bash: del: command not found',
#   'tool': 'Bash',
#   'frequency': 5,
#   'confidence': 0.8
# }

# Get stats
stats = detector.get_statistics()
# Returns: {
#   'total_failures': N,
#   'by_tool': {...},
#   'patterns_detected': N
# }
```

#### Detected Error Patterns

15+ patterns across 5 tools:
- Bash: command not found, permission denied
- Edit: string not found, line number prefix
- Read: file too large, encoding error
- Grep: too many results, invalid regex
- Write: file exists, permission denied

---

### pre-execution-checker.py

**Purpose**: Check failure KB before execution and auto-apply fixes.

#### CLI Usage

```bash
# Check Bash command
python pre-execution-checker.py --tool Bash --command "del file.txt"

# Check Edit params
python pre-execution-checker.py --tool Edit --params '{"old_string": "  123\tdef foo"}'

# Check Read params
python pre-execution-checker.py --tool Read --params '{"file_path": "/path/to/large.py"}'

# Get KB statistics
python pre-execution-checker.py --stats

# Load KB
python pre-execution-checker.py --load-kb
```

#### Python API

```python
from pre_execution_checker import PreExecutionChecker

checker = PreExecutionChecker()

# Check Bash command
result = checker.check_bash_command('del file.txt')
# Returns: {
#   'has_issue': True,
#   'pattern': 'bash_windows_command',
#   'confidence': 1.0,
#   'auto_fix_applied': True,
#   'fixed_command': 'rm file.txt',
#   'explanation': 'Translated Windows command to Unix'
# }

# Check Edit parameters
result = checker.check_edit_params({'old_string': '  123\tdef foo'})
# Returns: {
#   'has_issue': True,
#   'pattern': 'edit_line_number_prefix',
#   'confidence': 0.8,
#   'auto_fix_applied': True,
#   'fixed_params': {'old_string': 'def foo'},
#   'explanation': 'Stripped line number prefix'
# }

# Get stats
stats = checker.get_statistics()
# Returns: {
#   'total_patterns': 7,
#   'high_confidence': 7,  # >=0.75
#   'by_tool': {
#     'Bash': 2,
#     'Edit': 2,
#     ...
#   }
# }
```

#### Auto-Fix Threshold

Patterns with confidence ≥0.75 are auto-applied.

---

### failure-pattern-extractor.py

**Purpose**: Extract patterns from failures and calculate confidence.

#### CLI Usage

```bash
# Extract patterns from failures
python failure-pattern-extractor.py --extract logs/failures.log

# Update KB with patterns
python failure-pattern-extractor.py --update-kb

# Get statistics
python failure-pattern-extractor.py --stats
```

#### Python API

```python
from failure_pattern_extractor import FailurePatternExtractor

extractor = FailurePatternExtractor()

# Extract patterns
patterns = extractor.extract_patterns(failures_list)
# Returns: [
#   {
#     'pattern_id': 'bash_windows_command',
#     'signature': 'bash: del: command not found',
#     'tool': 'Bash',
#     'frequency': 12,
#     'confidence': 1.0,  # >=10 occurrences
#     'solution': {...}
#   }
# ]

# Calculate confidence
confidence = extractor.calculate_confidence(frequency=12)
# Returns: 1.0 (>=10), 0.8 (5-9), 0.6 (3-4), 0.3 (<3)

# Suggest solution
solution = extractor.suggest_solution(pattern_dict)
# Returns: {
#   'type': 'translate',
#   'mapping': {'del': 'rm'}
# }
```

---

### failure-solution-learner.py

**Purpose**: Learn from successful fixes and reinforce solutions.

#### CLI Usage

```bash
# Log successful fix
python failure-solution-learner.py --log-success \
    "bash_windows_command" \
    "del -> rm" \
    '{"tool": "Bash", "context": "..."}'

# Get learning statistics
python failure-solution-learner.py --stats

# Get solution history
python failure-solution-learner.py --history bash_windows_command
```

#### Python API

```python
from failure_solution_learner import FailureSolutionLearner

learner = FailureSolutionLearner()

# Log success
learner.log_success(
    pattern_id='bash_windows_command',
    solution_applied='del -> rm',
    context={'tool': 'Bash', 'command': 'del file.txt'}
)
# Increases pattern confidence by +0.05

# Get stats
stats = learner.get_statistics()
# Returns: {
#   'total_learnings': N,
#   'patterns_reinforced': N,
#   'average_confidence_increase': X
# }

# Get history
history = learner.get_solution_history('bash_windows_command')
# Returns: [
#   {
#     'timestamp': '...',
#     'solution': 'del -> rm',
#     'success': True,
#     'confidence_before': 0.8,
#     'confidence_after': 0.85
#   }
# ]
```

---

## Phase 4: Policy Automation

### model-selection-enforcer.py

**Purpose**: Analyze requests and enforce correct model selection.

#### CLI Usage

```bash
# Analyze request
python model-selection-enforcer.py --analyze "Find all Python files"

# Enforce model selection
python model-selection-enforcer.py --enforce "Implement auth" sonnet

# Get usage statistics
python model-selection-enforcer.py --stats

# Test analyzer
python model-selection-enforcer.py --test

# Initialize
python model-selection-enforcer.py --init
```

#### Python API

```python
from model_selection_enforcer import ModelSelectionEnforcer

enforcer = ModelSelectionEnforcer()

# Analyze request
analysis = enforcer.analyze_request('Find all Python files')
# Returns: {
#   'recommended_model': 'haiku',
#   'confidence': 0.9,
#   'reasoning': 'Quick search operation',
#   'scores': {'haiku': 5, 'sonnet': 0, 'opus': 0}
# }

# Enforce model
result = enforcer.enforce('Implement authentication', current_model='sonnet')
# Returns: {
#   'should_change': False,
#   'analysis': {...},
#   'message': 'Correct model already selected'
# }

# Get stats
stats = enforcer.get_usage_stats(days=7)
# Returns: {
#   'total_requests': N,
#   'by_model': {'haiku': X, 'sonnet': Y, 'opus': Z},
#   'percentage': {'haiku': 40%, 'sonnet': 55%, 'opus': 5%}
# }
```

#### Model Keywords

**Haiku** (quick operations):
- search, find, grep, list, show, read, view, check, status, get

**Sonnet** (implementation):
- implement, create, write, edit, modify, update, fix, refactor, add, build

**Opus** (complex planning):
- design, architecture, plan, analyze, complex, system, strategy, approach

---

### model-selection-monitor.py

**Purpose**: Monitor model usage distribution and check compliance.

#### CLI Usage

```bash
# Get distribution
python model-selection-monitor.py --distribution --days 7

# Check compliance
python model-selection-monitor.py --check-compliance

# Generate full report
python model-selection-monitor.py --report --days 7

# Alert if non-compliant (exit code 1)
python model-selection-monitor.py --alert
```

#### Python API

```python
from model_selection_monitor import ModelSelectionMonitor

monitor = ModelSelectionMonitor()

# Get distribution
dist = monitor.get_distribution(days=7)
# Returns: {
#   'total_requests': N,
#   'counts': {'haiku': X, 'sonnet': Y, 'opus': Z},
#   'percentages': {'haiku': 40.0, 'sonnet': 55.0, 'opus': 5.0}
# }

# Check compliance
compliance = monitor.check_compliance(dist)
# Returns: {
#   'compliant': True/False,
#   'issues': [
#     {'model': 'haiku', 'type': 'underused', 'expected': '35-45%', 'actual': 30%}
#   ],
#   'warnings': [...]
# }

# Generate report
report = monitor.generate_report(days=7)
# Returns: {
#   'distribution': {...},
#   'compliance': {...},
#   'trends': {...},
#   'recommendations': [...]
# }
```

#### Expected Ranges

| Model | Expected | Purpose |
|-------|----------|---------|
| Haiku | 35-45% | Quick operations |
| Sonnet | 50-60% | Implementation |
| Opus | 3-8% | Complex planning |

---

### consultation-tracker.py

**Purpose**: Track user decisions to avoid repeated questions.

#### CLI Usage

```bash
# Check if should consult
python consultation-tracker.py --check "planning_mode"

# Log consultation
python consultation-tracker.py --log \
    "planning_mode" \
    "Should I enter plan mode?" \
    '["yes","no"]' \
    "yes"

# Get decision history
python consultation-tracker.py --history planning_mode

# Get all preferences
python consultation-tracker.py --preferences

# Reset preference
python consultation-tracker.py --reset planning_mode

# Get statistics
python consultation-tracker.py --stats
```

#### Python API

```python
from consultation_tracker import ConsultationTracker

tracker = ConsultationTracker()

# Check if should consult
result = tracker.should_consult('planning_mode')
# Returns: {
#   'should_ask': False,
#   'default': 'yes',
#   'reason': 'Consistent pattern detected (2 same choices)',
#   'confidence': 'high'
# }

# Log consultation
tracker.log_consultation(
    decision_type='planning_mode',
    question='Should I enter plan mode?',
    options=['yes', 'no'],
    user_choice='yes'
)

# Get history
history = tracker.get_decision_history('planning_mode')
# Returns: [
#   {
#     'timestamp': '...',
#     'question': 'Should I enter plan mode?',
#     'options': ['yes', 'no'],
#     'user_choice': 'yes'
#   }
# ]

# Get stats
stats = tracker.get_statistics()
# Returns: {
#   'total_consultations': N,
#   'consistent_preferences': M,
#   'decision_types': [...]
# }
```

#### Decision Types

- planning_mode
- testing_approach
- api_style
- error_handling
- commit_frequency
- documentation

---

### core-skills-enforcer.py

**Purpose**: Enforce mandatory skills execution order.

#### CLI Usage

```bash
# Start new session
python core-skills-enforcer.py --start-session

# Get next skill to execute
python core-skills-enforcer.py --next-skill

# Log skill execution
python core-skills-enforcer.py --log-skill context-management-core

# Skip skill with reason
python core-skills-enforcer.py --skip-skill adaptive-skill-intelligence --reason "Not applicable"

# Verify all mandatory executed
python core-skills-enforcer.py --verify

# Get execution order
python core-skills-enforcer.py --order

# Get statistics
python core-skills-enforcer.py --stats
```

#### Python API

```python
from core_skills_enforcer import CoreSkillsEnforcer

enforcer = CoreSkillsEnforcer()

# Start session
session_id = enforcer.start_session()

# Get next skill
next_skill = enforcer.get_next_skill()
# Returns: {
#   'skill': {
#     'name': 'context-management-core',
#     'priority': 1,
#     'required': True
#   },
#   'status': 'required',
#   'message': 'Execute this skill next'
# }

# Log execution
enforcer.log_skill_execution('context-management-core')

# Verify completion
result = enforcer.verify_execution()
# Returns: {
#   'complete': True/False,
#   'executed': ['context-management-core', 'model-selection-core'],
#   'missing': [],
#   'compliance': 100.0
# }

# Get stats
stats = enforcer.get_statistics()
# Returns: {
#   'total_sessions': N,
#   'compliance_rate': 100.0,
#   'average_skills_per_session': 2.5
# }
```

#### Mandatory Skills (in order)

1. **context-management-core** (Priority 1, REQUIRED)
2. **model-selection-core** (Priority 2, REQUIRED)
3. adaptive-skill-intelligence (Priority 3, Optional)
4. task-planning-intelligence (Priority 4, Optional)

---

## Phase 5: Integration & Testing

### dashboard-v2.sh

**Purpose**: Unified monitoring dashboard showing all systems.

#### Usage

```bash
# View full dashboard
bash ~/.claude/memory/dashboard-v2.sh

# View specific section
bash ~/.claude/memory/dashboard-v2.sh | grep -A 10 "DAEMON HEALTH"
```

#### Dashboard Sections

1. **Daemon Health** - Status of all 8 daemons
2. **Context Status** - Current usage and recommendations
3. **Failure Prevention** - KB stats and patterns
4. **Model Usage** - Distribution and compliance
5. **Consultation Preferences** - Learned preferences
6. **Core Skills Compliance** - Execution tracking
7. **Recent Activity** - Last 5 policy hits
8. **Overall Health Score** - System-wide health

#### Output Example

```
============================================================
         MEMORY SYSTEM DASHBOARD v2.0
============================================================

[1] DAEMON HEALTH
------------------------------------------------------------
  Status: ALL HEALTHY (8/8 daemons)

  Daemon                          PID      Status    Uptime
  context-daemon                  12345    RUNNING   120m
  ...

[2] CONTEXT STATUS
------------------------------------------------------------
  Usage: 45% (Level: green)
  Cache: 25 file summaries cached
  ...

[8] OVERALL HEALTH SCORE
------------------------------------------------------------
  Health Score: 100.0% - Excellent
```

---

### test-all-phases.py

**Purpose**: Comprehensive test suite for all phases.

#### Usage

```bash
# Run all tests
python test-all-phases.py

# Run specific phase
python test-all-phases.py --phase 1

# Verbose output
python test-all-phases.py --verbose
```

#### Test Suites

1. **Phase 1**: Context Optimization (pre-execution, cache, state, monitor)
2. **Phase 2**: Daemon Infrastructure (manager, PIDs, health, logger)
3. **Phase 3**: Failure Prevention (detection, KB, prevention, learning)
4. **Phase 4**: Policy Automation (model, consultation, skills)
5. **Integration**: System integration (dashboard, logs, directories)

#### Output Format

```
============================================================
TEST: Phase 1: Context Optimization
============================================================
Testing context optimization...
  [OK] Pre-execution optimizer working
  [OK] Context cache working
  [OK] Session state working
  [OK] Context monitor working
[OK] Phase 1: Context Optimization PASSED

...

TEST SUMMARY
============================================================
[OK] PASSED     Phase 1: Context Optimization
[OK] PASSED     Phase 2: Daemon Infrastructure
[OK] PASSED     Phase 3: Failure Prevention
[OK] PASSED     Phase 4: Policy Automation
[OK] PASSED     System Integration

Total: 5/5 tests passed

[OK] ALL TESTS PASSED!
```

---

### verify-system.sh

**Purpose**: System verification script checking all components.

#### Usage

```bash
# Run full verification
bash verify-system.sh

# Check specific phase
# (Not supported - runs all phases)
```

#### Verification Checks

**Phase 1**: 7 checks (files + directories)
**Phase 2**: 8 checks (files + directories + daemon health)
**Phase 3**: 6 checks (files + KB stats)
**Phase 4**: 5 checks (files + model analysis)
**Phase 5**: 3 checks (integration files)

#### Output

```
============================================================
SYSTEM VERIFICATION
============================================================

[1] Phase 1: Context Optimization
Checking Pre-execution optimizer... OK
Checking Context extractor... OK
...

VERIFICATION SUMMARY
============================================================
ALL CHECKS PASSED!

System Status: FULLY OPERATIONAL
  - All 4 phases implemented
  - All files present
  - All systems functional

Ready for production use!
```

Exit codes:
- 0: All checks passed
- 1: One or more checks failed

---

## Maintenance Scripts

### daily-health-check.sh

**Purpose**: Quick daily health verification of critical components.

#### Usage

```bash
bash daily-health-check.sh
```

#### Checks Performed

1. Daemon Health (8/8 running?)
2. Health Score (target: >90%)
3. Recent Errors (last 24 hours)
4. Daemon Restarts (last 24 hours)
5. Disk Space (log file sizes)
6. Failure KB (patterns loaded)

#### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All checks passed (healthy) |
| 1 | Warnings detected (minor issues) |
| 2 | Critical issues (immediate attention required) |

#### Report Location

`~/.claude/memory/logs/daily-health-report-YYYYMMDD.txt`

#### Scheduling (Recommended)

```bash
# Run every day at 8 AM
0 8 * * * bash ~/.claude/memory/daily-health-check.sh

# Run twice daily (8 AM and 8 PM)
0 8,20 * * * bash ~/.claude/memory/daily-health-check.sh
```

#### Output Example

```
============================================================
         DAILY HEALTH CHECK
         Date: 2026-02-09 08:00:00
============================================================

[1] Checking Daemons...
  [OK] All daemons running (8/8)

[2] Checking Health Score...
  [OK] Health: 100.0% (Excellent)

[3] Checking Recent Errors...
  [OK] No errors in last 24 hours

[4] Checking Daemon Restarts...
  [OK] No restarts in last 24 hours

[5] Checking Disk Space...
  Memory system size: 2.5M
  Logs size: 350K
  [OK] All log files within limits

[6] Checking Failure KB...
  [OK] KB has 7 patterns

============================================================
         DAILY HEALTH SUMMARY
============================================================

[OK] SYSTEM HEALTHY

Status: ALL CHECKS PASSED
  - No critical issues
  - No warnings
  - All systems operational
```

---

### weekly-health-check.sh

**Purpose**: Comprehensive weekly health verification and reporting.

#### Usage

```bash
bash weekly-health-check.sh
```

#### Checks Performed

1. Verify all systems operational
2. Check log file sizes
3. Review failure patterns
4. Check model usage distribution
5. Verify daemon health
6. Check cache sizes
7. Review consultation patterns

---

### monthly-optimization.sh

**Purpose**: Monthly optimization and cleanup.

#### Usage

```bash
bash monthly-optimization.sh
```

#### Operations Performed

1. Optimize failure KB (prune low-frequency patterns)
2. Clear expired cache entries
3. Optimize log files
4. Review and update consultation preferences
5. Clean old restart history
6. Generate monthly report

---

## Environment Variables

### Optional Configuration

```bash
# Memory directory location (default: ~/.claude/memory)
export CLAUDE_MEMORY_DIR="/custom/path"

# Python executable (default: python)
export PYTHON_CMD="python3"

# Log level (default: INFO)
export LOG_LEVEL="DEBUG"
```

---

## Exit Codes

All scripts follow standard exit codes:

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Missing dependency |
| 3 | Configuration error |
| 4 | Permission denied |
| 5 | File not found |

---

## Common Patterns

### Check-Execute-Log Pattern

```python
# 1. Check if should execute
result = pre_execution_checker.check_bash_command(command)

# 2. Execute (with fix if needed)
command_to_run = result.get('fixed_command', command)
output = execute_bash(command_to_run)

# 3. Log result
if result.get('auto_fix_applied'):
    daemon_logger.log_policy_hit('FAILURE_PREVENTION', f'Auto-fixed: {command}')
```

### Daemon Pattern

```python
# 1. Start daemon via manager
daemon_manager.start_daemon('my-daemon')

# 2. Daemon writes PID
pid_tracker.set_daemon_pid('my-daemon', os.getpid())

# 3. Health monitor checks periodically
# 4. Auto-restart if dead
```

### Optimization Pattern

```python
# 1. Pre-execution optimization
optimized = pre_execution_optimizer.optimize(tool, params)

# 2. Execute with optimized params
result = execute_tool(optimized['params'])

# 3. Post-execution extraction
summary = context_extractor.extract(result)

# 4. Cache summary
context_cache.set_file_summary(file, summary)
```

---

**API Reference Version**: 1.0
**Last Updated**: 2026-02-09
**Compatible with**: Memory System v2.0
