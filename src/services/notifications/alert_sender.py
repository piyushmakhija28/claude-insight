"""
Alert Sender
Handles Email and SMS alerts for critical system events
"""
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path


class AlertSender:
    """Send email and SMS alerts for critical events"""

    def __init__(self):
        self.config_dir = Path.home() / '.claude' / 'memory'
        self.config_file = self.config_dir / 'alert_config.json'
        self.ensure_config_file()

    def ensure_config_file(self):
        """Ensure alert configuration file exists"""
        if not self.config_file.exists():
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            default_config = {
                'email': {
                    'enabled': False,
                    'smtp_server': 'smtp.gmail.com',
                    'smtp_port': 587,
                    'username': '',
                    'password': '',
                    'from_email': '',
                    'recipients': [],
                    'use_tls': True
                },
                'sms': {
                    'enabled': False,
                    'provider': 'twilio',  # twilio, nexmo, aws_sns
                    'account_sid': '',
                    'auth_token': '',
                    'from_number': '',
                    'recipients': []
                },
                'alert_rules': {
                    'critical_only': True,
                    'include_warnings': False,
                    'alert_types': ['health_score', 'daemon_down', 'error_threshold'],
                    'quiet_hours': {
                        'enabled': False,
                        'start': '22:00',
                        'end': '08:00'
                    },
                    'rate_limiting': {
                        'enabled': True,
                        'max_alerts_per_hour': 10
                    }
                },
                'last_alerts': []
            }
            self.config_file.write_text(json.dumps(default_config, indent=2))

    def load_config(self):
        """Load alert configuration"""
        try:
            if self.config_file.exists():
                return json.loads(self.config_file.read_text())
            return {}
        except Exception as e:
            print(f"Error loading alert config: {e}")
            return {}

    def save_config(self, config):
        """Save alert configuration"""
        try:
            self.config_file.write_text(json.dumps(config, indent=2))
            return True
        except Exception as e:
            print(f"Error saving alert config: {e}")
            return False

    def is_quiet_hours(self, config):
        """Check if current time is within quiet hours"""
        if not config.get('alert_rules', {}).get('quiet_hours', {}).get('enabled', False):
            return False

        try:
            from datetime import datetime
            now = datetime.now().time()
            quiet_hours = config['alert_rules']['quiet_hours']
            start = datetime.strptime(quiet_hours['start'], '%H:%M').time()
            end = datetime.strptime(quiet_hours['end'], '%H:%M').time()

            if start < end:
                return start <= now <= end
            else:  # Crosses midnight
                return now >= start or now <= end
        except Exception:
            return False

    def check_rate_limit(self, config):
        """Check if rate limit has been exceeded"""
        if not config.get('alert_rules', {}).get('rate_limiting', {}).get('enabled', False):
            return False

        try:
            max_alerts = config['alert_rules']['rate_limiting'].get('max_alerts_per_hour', 10)
            last_alerts = config.get('last_alerts', [])

            # Filter alerts from last hour
            one_hour_ago = datetime.now().timestamp() - 3600
            recent_alerts = [a for a in last_alerts if a.get('timestamp', 0) > one_hour_ago]

            return len(recent_alerts) >= max_alerts
        except Exception:
            return False

    def should_send_alert(self, severity, alert_type, config):
        """Determine if alert should be sent based on rules"""
        # Check quiet hours
        if self.is_quiet_hours(config):
            return False

        # Check rate limit
        if self.check_rate_limit(config):
            return False

        # Check severity
        alert_rules = config.get('alert_rules', {})
        if alert_rules.get('critical_only', True) and severity != 'critical':
            if not (alert_rules.get('include_warnings', False) and severity == 'warning'):
                return False

        # Check alert type
        allowed_types = alert_rules.get('alert_types', [])
        if allowed_types and alert_type not in allowed_types:
            return False

        return True

    def send_email(self, subject, body, config):
        """Send email alert"""
        email_config = config.get('email', {})

        if not email_config.get('enabled', False):
            return {'success': False, 'message': 'Email alerts not enabled'}

        if not email_config.get('recipients'):
            return {'success': False, 'message': 'No email recipients configured'}

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = email_config.get('from_email', email_config.get('username', ''))
            msg['To'] = ', '.join(email_config['recipients'])

            # HTML body
            html_body = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                             color: white; padding: 20px; border-radius: 5px; }}
                    .content {{ padding: 20px; background: #f8f9fa; border-radius: 5px; margin-top: 10px; }}
                    .footer {{ color: #6c757d; font-size: 12px; margin-top: 20px; }}
                    .alert-critical {{ color: #dc3545; font-weight: bold; }}
                    .alert-warning {{ color: #ffc107; font-weight: bold; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h2>🤖 Claude Monitoring System Alert</h2>
                </div>
                <div class="content">
                    {body}
                </div>
                <div class="footer">
                    <p>This is an automated alert from Claude Monitoring System v2.5</p>
                    <p>Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
            </body>
            </html>
            """

            # Attach both plain text and HTML
            msg.attach(MIMEText(body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))

            # Connect to SMTP server
            smtp_server = email_config.get('smtp_server', 'smtp.gmail.com')
            smtp_port = email_config.get('smtp_port', 587)

            server = smtplib.SMTP(smtp_server, smtp_port)

            if email_config.get('use_tls', True):
                server.starttls()

            # Login
            username = email_config.get('username', '')
            password = email_config.get('password', '')
            if username and password:
                server.login(username, password)

            # Send email
            server.send_message(msg)
            server.quit()

            return {'success': True, 'message': 'Email sent successfully'}

        except Exception as e:
            return {'success': False, 'message': f'Email error: {str(e)}'}

    def send_sms(self, message, config):
        """Send SMS alert using configured provider"""
        sms_config = config.get('sms', {})

        if not sms_config.get('enabled', False):
            return {'success': False, 'message': 'SMS alerts not enabled'}

        if not sms_config.get('recipients'):
            return {'success': False, 'message': 'No SMS recipients configured'}

        provider = sms_config.get('provider', 'twilio')

        if provider == 'twilio':
            return self._send_twilio_sms(message, sms_config)
        else:
            return {'success': False, 'message': f'SMS provider {provider} not supported'}

    def _send_twilio_sms(self, message, sms_config):
        """Send SMS via Twilio"""
        try:
            from twilio.rest import Client

            account_sid = sms_config.get('account_sid', '')
            auth_token = sms_config.get('auth_token', '')
            from_number = sms_config.get('from_number', '')

            if not all([account_sid, auth_token, from_number]):
                return {'success': False, 'message': 'Twilio credentials not configured'}

            client = Client(account_sid, auth_token)

            # Send to all recipients
            results = []
            for recipient in sms_config.get('recipients', []):
                try:
                    msg = client.messages.create(
                        body=message,
                        from_=from_number,
                        to=recipient
                    )
                    results.append({'to': recipient, 'sid': msg.sid, 'status': msg.status})
                except Exception as e:
                    results.append({'to': recipient, 'error': str(e)})

            return {'success': True, 'message': 'SMS sent', 'results': results}

        except ImportError:
            return {'success': False, 'message': 'Twilio library not installed. Run: pip install twilio'}
        except Exception as e:
            return {'success': False, 'message': f'SMS error: {str(e)}'}

    def send_alert(self, alert_type, severity, title, message):
        """Send alert via configured channels (email/SMS)"""
        config = self.load_config()

        # Check if alert should be sent
        if not self.should_send_alert(severity, alert_type, config):
            return {
                'success': False,
                'message': 'Alert suppressed by rules (quiet hours, rate limit, or severity)',
                'email': None,
                'sms': None
            }

        results = {
            'success': True,
            'email': None,
            'sms': None
        }

        # Send email
        if config.get('email', {}).get('enabled', False):
            email_subject = f"[{severity.upper()}] {title}"
            email_body = f"{title}\n\n{message}\n\nAlert Type: {alert_type}\nSeverity: {severity}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            results['email'] = self.send_email(email_subject, email_body, config)

        # Send SMS (shorter message)
        if config.get('sms', {}).get('enabled', False):
            sms_message = f"[Claude Alert] {severity.upper()}: {title} - {message[:100]}"
            results['sms'] = self.send_sms(sms_message, config)

        # Record alert in history for rate limiting
        config.setdefault('last_alerts', [])
        config['last_alerts'].append({
            'timestamp': datetime.now().timestamp(),
            'type': alert_type,
            'severity': severity,
            'title': title
        })

        # Keep only last 100 alerts
        config['last_alerts'] = config['last_alerts'][-100:]
        self.save_config(config)

        return results

    def test_email(self, config):
        """Send test email"""
        subject = "[TEST] Claude Monitoring System"
        body = "This is a test email from Claude Monitoring System. If you receive this, email alerts are working correctly!"
        return self.send_email(subject, body, config)

    def test_sms(self, config):
        """Send test SMS"""
        message = "[TEST] Claude Monitoring System - SMS alerts are working!"
        return self.send_sms(message, config)
