"""
Custom Alert Routing and Escalation Engine
Advanced alert routing with multi-level escalation policies
"""
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict


class AlertRoutingEngine:
    """Manage alert routing rules and escalation policies"""

    def __init__(self):
        self.data_dir = Path.home() / '.claude' / 'memory' / 'alert_routing'
        self.routing_rules_file = self.data_dir / 'routing_rules.json'
        self.escalation_policies_file = self.data_dir / 'escalation_policies.json'
        self.on_call_schedules_file = self.data_dir / 'on_call_schedules.json'
        self.alert_history_file = self.data_dir / 'alert_history.json'
        self.notification_channels_file = self.data_dir / 'notification_channels.json'

        self.ensure_data_files()

    def ensure_data_files(self):
        """Ensure alert routing data files exist"""
        if not self.data_dir.exists():
            self.data_dir.mkdir(parents=True, exist_ok=True)

        if not self.routing_rules_file.exists():
            self.routing_rules_file.write_text(json.dumps({
                'rules': self.get_default_routing_rules(),
                'last_updated': datetime.now().isoformat()
            }, indent=2))

        if not self.escalation_policies_file.exists():
            self.escalation_policies_file.write_text(json.dumps({
                'policies': self.get_default_escalation_policies(),
                'last_updated': datetime.now().isoformat()
            }, indent=2))

        if not self.on_call_schedules_file.exists():
            self.on_call_schedules_file.write_text(json.dumps({
                'schedules': self.get_default_on_call_schedules(),
                'last_updated': datetime.now().isoformat()
            }, indent=2))

        if not self.alert_history_file.exists():
            self.alert_history_file.write_text(json.dumps({
                'alerts': [],
                'last_updated': datetime.now().isoformat()
            }, indent=2))

        if not self.notification_channels_file.exists():
            self.notification_channels_file.write_text(json.dumps({
                'channels': self.get_default_notification_channels(),
                'last_updated': datetime.now().isoformat()
            }, indent=2))

    def get_default_routing_rules(self):
        """Get default routing rules"""
        return [
            {
                'id': 'rule_1',
                'name': 'Critical Alerts',
                'enabled': True,
                'priority': 1,
                'conditions': {
                    'severity': ['critical'],
                    'logic': 'AND'
                },
                'actions': [
                    {
                        'type': 'notify',
                        'channels': ['email_primary', 'sms_primary', 'slack_critical']
                    },
                    {
                        'type': 'escalate',
                        'policy_id': 'policy_critical'
                    }
                ]
            },
            {
                'id': 'rule_2',
                'name': 'High Priority Alerts',
                'enabled': True,
                'priority': 2,
                'conditions': {
                    'severity': ['high'],
                    'logic': 'AND'
                },
                'actions': [
                    {
                        'type': 'notify',
                        'channels': ['email_primary', 'slack_alerts']
                    },
                    {
                        'type': 'escalate',
                        'policy_id': 'policy_high'
                    }
                ]
            },
            {
                'id': 'rule_3',
                'name': 'Business Hours Alerts',
                'enabled': True,
                'priority': 3,
                'conditions': {
                    'time_range': {'start': '09:00', 'end': '17:00'},
                    'days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
                    'logic': 'AND'
                },
                'actions': [
                    {
                        'type': 'notify',
                        'channels': ['email_primary']
                    }
                ]
            }
        ]

    def get_default_escalation_policies(self):
        """Get default escalation policies"""
        return [
            {
                'id': 'policy_critical',
                'name': 'Critical Escalation',
                'enabled': True,
                'levels': [
                    {
                        'level': 1,
                        'timeout_minutes': 5,
                        'targets': ['on_call_primary'],
                        'channels': ['email_primary', 'sms_primary']
                    },
                    {
                        'level': 2,
                        'timeout_minutes': 10,
                        'targets': ['on_call_secondary'],
                        'channels': ['email_secondary', 'sms_secondary', 'slack_critical']
                    },
                    {
                        'level': 3,
                        'timeout_minutes': 15,
                        'targets': ['manager'],
                        'channels': ['email_manager', 'sms_manager']
                    }
                ],
                'repeat': True,
                'max_repeats': 3
            },
            {
                'id': 'policy_high',
                'name': 'High Priority Escalation',
                'enabled': True,
                'levels': [
                    {
                        'level': 1,
                        'timeout_minutes': 15,
                        'targets': ['on_call_primary'],
                        'channels': ['email_primary', 'slack_alerts']
                    },
                    {
                        'level': 2,
                        'timeout_minutes': 30,
                        'targets': ['on_call_secondary'],
                        'channels': ['email_secondary', 'sms_secondary']
                    }
                ],
                'repeat': False
            }
        ]

    def get_default_on_call_schedules(self):
        """Get default on-call schedules"""
        return [
            {
                'id': 'schedule_1',
                'name': 'Primary On-Call',
                'type': 'weekly_rotation',
                'enabled': True,
                'rotation': [
                    {'user': 'admin', 'week': 1},
                    {'user': 'engineer_1', 'week': 2},
                    {'user': 'engineer_2', 'week': 3}
                ],
                'start_date': datetime.now().isoformat(),
                'timezone': 'UTC'
            },
            {
                'id': 'schedule_2',
                'name': 'Secondary On-Call',
                'type': 'weekly_rotation',
                'enabled': True,
                'rotation': [
                    {'user': 'engineer_2', 'week': 1},
                    {'user': 'admin', 'week': 2},
                    {'user': 'engineer_1', 'week': 3}
                ],
                'start_date': datetime.now().isoformat(),
                'timezone': 'UTC'
            }
        ]

    def get_default_notification_channels(self):
        """Get default notification channels"""
        return [
            {
                'id': 'email_primary',
                'name': 'Primary Email',
                'type': 'email',
                'enabled': True,
                'config': {
                    'recipients': ['admin@example.com']
                }
            },
            {
                'id': 'sms_primary',
                'name': 'Primary SMS',
                'type': 'sms',
                'enabled': True,
                'config': {
                    'phone_numbers': ['+1234567890']
                }
            },
            {
                'id': 'slack_critical',
                'name': 'Slack Critical Channel',
                'type': 'slack',
                'enabled': True,
                'config': {
                    'webhook_url': 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL',
                    'channel': '#critical-alerts'
                }
            },
            {
                'id': 'webhook_custom',
                'name': 'Custom Webhook',
                'type': 'webhook',
                'enabled': True,
                'config': {
                    'url': 'https://example.com/webhook',
                    'method': 'POST',
                    'headers': {
                        'Content-Type': 'application/json'
                    }
                }
            }
        ]

    def load_routing_rules(self):
        """Load routing rules"""
        try:
            return json.loads(self.routing_rules_file.read_text())
        except Exception as e:
            print(f"Error loading routing rules: {e}")
            return {'rules': [], 'last_updated': None}

    def save_routing_rules(self, data):
        """Save routing rules"""
        try:
            data['last_updated'] = datetime.now().isoformat()
            self.routing_rules_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            print(f"Error saving routing rules: {e}")

    def load_escalation_policies(self):
        """Load escalation policies"""
        try:
            return json.loads(self.escalation_policies_file.read_text())
        except Exception as e:
            print(f"Error loading escalation policies: {e}")
            return {'policies': [], 'last_updated': None}

    def save_escalation_policies(self, data):
        """Save escalation policies"""
        try:
            data['last_updated'] = datetime.now().isoformat()
            self.escalation_policies_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            print(f"Error saving escalation policies: {e}")

    def load_on_call_schedules(self):
        """Load on-call schedules"""
        try:
            return json.loads(self.on_call_schedules_file.read_text())
        except Exception as e:
            print(f"Error loading on-call schedules: {e}")
            return {'schedules': [], 'last_updated': None}

    def save_on_call_schedules(self, data):
        """Save on-call schedules"""
        try:
            data['last_updated'] = datetime.now().isoformat()
            self.on_call_schedules_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            print(f"Error saving on-call schedules: {e}")

    def load_notification_channels(self):
        """Load notification channels"""
        try:
            return json.loads(self.notification_channels_file.read_text())
        except Exception as e:
            print(f"Error loading notification channels: {e}")
            return {'channels': [], 'last_updated': None}

    def save_notification_channels(self, data):
        """Save notification channels"""
        try:
            data['last_updated'] = datetime.now().isoformat()
            self.notification_channels_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            print(f"Error saving notification channels: {e}")

    def load_alert_history(self):
        """Load alert history"""
        try:
            return json.loads(self.alert_history_file.read_text())
        except Exception as e:
            print(f"Error loading alert history: {e}")
            return {'alerts': [], 'last_updated': None}

    def save_alert_history(self, data):
        """Save alert history"""
        try:
            data['last_updated'] = datetime.now().isoformat()
            self.alert_history_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            print(f"Error saving alert history: {e}")

    def evaluate_conditions(self, alert, conditions):
        """Evaluate if alert matches routing rule conditions"""
        logic = conditions.get('logic', 'AND')
        matches = []

        # Check severity
        if 'severity' in conditions:
            matches.append(alert.get('severity') in conditions['severity'])

        # Check metric
        if 'metric' in conditions:
            matches.append(alert.get('metric') in conditions['metric'])

        # Check time range
        if 'time_range' in conditions:
            current_time = datetime.now().time()
            start_time = datetime.strptime(conditions['time_range']['start'], '%H:%M').time()
            end_time = datetime.strptime(conditions['time_range']['end'], '%H:%M').time()
            matches.append(start_time <= current_time <= end_time)

        # Check days
        if 'days' in conditions:
            current_day = datetime.now().strftime('%A')
            matches.append(current_day in conditions['days'])

        # Check tags
        if 'tags' in conditions:
            alert_tags = set(alert.get('tags', []))
            condition_tags = set(conditions['tags'])
            matches.append(bool(alert_tags & condition_tags))

        # Evaluate based on logic
        if logic == 'AND':
            return all(matches) if matches else False
        elif logic == 'OR':
            return any(matches) if matches else False
        else:
            return False

    def get_current_on_call(self, schedule_id):
        """Get current on-call person for a schedule"""
        schedules_data = self.load_on_call_schedules()
        schedule = next((s for s in schedules_data['schedules'] if s['id'] == schedule_id), None)

        if not schedule or not schedule.get('enabled'):
            return None

        if schedule['type'] == 'weekly_rotation':
            start_date = datetime.fromisoformat(schedule['start_date'])
            weeks_passed = (datetime.now() - start_date).days // 7
            rotation = schedule['rotation']
            current_index = weeks_passed % len(rotation)
            return rotation[current_index]['user']

        return None

    def route_alert(self, alert):
        """Route alert based on routing rules"""
        rules_data = self.load_routing_rules()
        rules = sorted(rules_data['rules'], key=lambda x: x.get('priority', 999))

        matched_rules = []
        actions_to_execute = []

        for rule in rules:
            if not rule.get('enabled'):
                continue

            if self.evaluate_conditions(alert, rule.get('conditions', {})):
                matched_rules.append(rule)
                actions_to_execute.extend(rule.get('actions', []))

        return {
            'matched_rules': matched_rules,
            'actions': actions_to_execute
        }

    def create_alert(self, alert_data):
        """Create and route a new alert"""
        alert_id = str(uuid.uuid4())
        alert = {
            'id': alert_id,
            'created_at': datetime.now().isoformat(),
            'status': 'active',
            'acknowledged': False,
            'resolved': False,
            'escalation_level': 0,
            'escalation_history': [],
            **alert_data
        }

        # Route the alert
        routing_result = self.route_alert(alert)
        alert['routing'] = routing_result

        # Save to history
        history = self.load_alert_history()
        history['alerts'].insert(0, alert)
        history['alerts'] = history['alerts'][:1000]  # Keep last 1000 alerts
        self.save_alert_history(history)

        # Execute actions
        for action in routing_result['actions']:
            if action['type'] == 'escalate':
                self.start_escalation(alert_id, action['policy_id'])

        return alert

    def start_escalation(self, alert_id, policy_id):
        """Start escalation for an alert"""
        policies_data = self.load_escalation_policies()
        policy = next((p for p in policies_data['policies'] if p['id'] == policy_id), None)

        if not policy or not policy.get('enabled'):
            return False

        history = self.load_alert_history()
        alert = next((a for a in history['alerts'] if a['id'] == alert_id), None)

        if not alert:
            return False

        # Initialize escalation
        alert['escalation'] = {
            'policy_id': policy_id,
            'policy_name': policy['name'],
            'current_level': 1,
            'started_at': datetime.now().isoformat(),
            'next_escalation_at': (datetime.now() + timedelta(minutes=policy['levels'][0]['timeout_minutes'])).isoformat()
        }

        # Record escalation history
        alert['escalation_history'].append({
            'level': 1,
            'timestamp': datetime.now().isoformat(),
            'targets': policy['levels'][0]['targets'],
            'channels': policy['levels'][0]['channels']
        })

        self.save_alert_history(history)
        return True

    def escalate_to_next_level(self, alert_id):
        """Escalate alert to next level"""
        history = self.load_alert_history()
        alert = next((a for a in history['alerts'] if a['id'] == alert_id), None)

        if not alert or not alert.get('escalation'):
            return False

        policies_data = self.load_escalation_policies()
        policy = next((p for p in policies_data['policies']
                      if p['id'] == alert['escalation']['policy_id']), None)

        if not policy:
            return False

        current_level = alert['escalation']['current_level']
        next_level = current_level + 1

        if next_level > len(policy['levels']):
            # Max escalation reached
            if policy.get('repeat') and alert['escalation'].get('repeat_count', 0) < policy.get('max_repeats', 1):
                # Restart escalation
                alert['escalation']['current_level'] = 1
                alert['escalation']['repeat_count'] = alert['escalation'].get('repeat_count', 0) + 1
                next_level = 1
            else:
                return False

        next_level_config = policy['levels'][next_level - 1]
        alert['escalation']['current_level'] = next_level
        alert['escalation']['next_escalation_at'] = (
            datetime.now() + timedelta(minutes=next_level_config['timeout_minutes'])
        ).isoformat()

        # Record escalation history
        alert['escalation_history'].append({
            'level': next_level,
            'timestamp': datetime.now().isoformat(),
            'targets': next_level_config['targets'],
            'channels': next_level_config['channels']
        })

        self.save_alert_history(history)
        return True

    def acknowledge_alert(self, alert_id, acknowledged_by):
        """Acknowledge an alert"""
        history = self.load_alert_history()
        alert = next((a for a in history['alerts'] if a['id'] == alert_id), None)

        if not alert:
            return False

        alert['acknowledged'] = True
        alert['acknowledged_at'] = datetime.now().isoformat()
        alert['acknowledged_by'] = acknowledged_by
        alert['status'] = 'acknowledged'

        self.save_alert_history(history)
        return True

    def resolve_alert(self, alert_id, resolved_by, resolution_note=''):
        """Resolve an alert"""
        history = self.load_alert_history()
        alert = next((a for a in history['alerts'] if a['id'] == alert_id), None)

        if not alert:
            return False

        alert['resolved'] = True
        alert['resolved_at'] = datetime.now().isoformat()
        alert['resolved_by'] = resolved_by
        alert['resolution_note'] = resolution_note
        alert['status'] = 'resolved'

        self.save_alert_history(history)
        return True

    def get_active_alerts(self):
        """Get all active alerts"""
        history = self.load_alert_history()
        return [a for a in history['alerts'] if a['status'] == 'active']

    def get_escalated_alerts(self):
        """Get alerts that are currently escalated"""
        history = self.load_alert_history()
        return [a for a in history['alerts']
                if a.get('escalation') and a['status'] in ['active', 'acknowledged']]

    def get_statistics(self):
        """Get alert routing statistics"""
        history = self.load_alert_history()
        alerts = history['alerts']

        if not alerts:
            return {
                'total_alerts': 0,
                'active': 0,
                'acknowledged': 0,
                'resolved': 0,
                'escalated': 0,
                'by_severity': {},
                'by_metric': {}
            }

        by_severity = defaultdict(int)
        by_metric = defaultdict(int)
        by_status = defaultdict(int)

        for alert in alerts:
            by_severity[alert.get('severity', 'unknown')] += 1
            by_metric[alert.get('metric', 'unknown')] += 1
            by_status[alert.get('status', 'unknown')] += 1

        return {
            'total_alerts': len(alerts),
            'active': by_status.get('active', 0),
            'acknowledged': by_status.get('acknowledged', 0),
            'resolved': by_status.get('resolved', 0),
            'escalated': len([a for a in alerts if a.get('escalation')]),
            'by_severity': dict(by_severity),
            'by_metric': dict(by_metric)
        }
