"""
AI-Powered Anomaly Detection
Uses statistical methods and machine learning to detect anomalies in system metrics
"""
import json
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from collections import deque


class AnomalyDetector:
    """Detect anomalies in system metrics using AI/ML algorithms"""

    def __init__(self):
        self.data_dir = Path.home() / '.claude' / 'memory' / 'anomalies'
        self.anomalies_file = self.data_dir / 'anomalies.json'
        self.models_file = self.data_dir / 'models.json'
        self.history_file = self.data_dir / 'history.json'

        # In-memory buffers for real-time detection
        self.health_score_buffer = deque(maxlen=100)
        self.error_count_buffer = deque(maxlen=100)
        self.context_usage_buffer = deque(maxlen=100)
        self.response_time_buffer = deque(maxlen=100)

        self.ensure_data_files()

    def ensure_data_files(self):
        """Ensure anomaly data files exist"""
        if not self.data_dir.exists():
            self.data_dir.mkdir(parents=True, exist_ok=True)

        if not self.anomalies_file.exists():
            self.anomalies_file.write_text(json.dumps({
                'anomalies': [],
                'last_updated': datetime.now().isoformat()
            }))

        if not self.models_file.exists():
            self.models_file.write_text(json.dumps({
                'models': {},
                'last_trained': None
            }))

        if not self.history_file.exists():
            self.history_file.write_text(json.dumps({
                'metrics_history': [],
                'last_updated': datetime.now().isoformat()
            }))

    def load_anomalies(self):
        """Load detected anomalies"""
        try:
            return json.loads(self.anomalies_file.read_text())
        except Exception as e:
            print(f"Error loading anomalies: {e}")
            return {'anomalies': [], 'last_updated': None}

    def save_anomalies(self, data):
        """Save detected anomalies"""
        try:
            data['last_updated'] = datetime.now().isoformat()
            self.anomalies_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            print(f"Error saving anomalies: {e}")

    def load_models(self):
        """Load trained models"""
        try:
            return json.loads(self.models_file.read_text())
        except Exception as e:
            print(f"Error loading models: {e}")
            return {'models': {}, 'last_trained': None}

    def save_models(self, data):
        """Save trained models"""
        try:
            data['last_trained'] = datetime.now().isoformat()
            self.models_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            print(f"Error saving models: {e}")

    def load_history(self):
        """Load metrics history"""
        try:
            return json.loads(self.history_file.read_text())
        except Exception as e:
            print(f"Error loading history: {e}")
            return {'metrics_history': [], 'last_updated': None}

    def save_history(self, data):
        """Save metrics history"""
        try:
            data['last_updated'] = datetime.now().isoformat()
            self.history_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            print(f"Error saving history: {e}")

    def add_metric_data(self, metric_name, value, timestamp=None):
        """Add metric data point for anomaly detection"""
        if timestamp is None:
            timestamp = datetime.now().isoformat()

        history = self.load_history()
        history['metrics_history'].append({
            'metric': metric_name,
            'value': value,
            'timestamp': timestamp
        })

        # Keep only last 10000 data points
        history['metrics_history'] = history['metrics_history'][-10000:]
        self.save_history(history)

        # Update in-memory buffers
        if metric_name == 'health_score':
            self.health_score_buffer.append(value)
        elif metric_name == 'error_count':
            self.error_count_buffer.append(value)
        elif metric_name == 'context_usage':
            self.context_usage_buffer.append(value)
        elif metric_name == 'response_time':
            self.response_time_buffer.append(value)

    def z_score_detection(self, values, current_value, threshold=3):
        """Detect anomaly using Z-score method"""
        if len(values) < 3:
            return False, 0, 0

        values_array = np.array(values)
        mean = np.mean(values_array)
        std = np.std(values_array)

        if std == 0:
            return False, mean, 0

        z_score = abs((current_value - mean) / std)
        is_anomaly = z_score > threshold

        return is_anomaly, mean, z_score

    def iqr_detection(self, values, current_value, multiplier=1.5):
        """Detect anomaly using Interquartile Range (IQR) method"""
        if len(values) < 4:
            return False, 0, 0, 0

        values_array = np.array(values)
        q1 = np.percentile(values_array, 25)
        q3 = np.percentile(values_array, 75)
        iqr = q3 - q1

        lower_bound = q1 - (multiplier * iqr)
        upper_bound = q3 + (multiplier * iqr)

        is_anomaly = current_value < lower_bound or current_value > upper_bound

        return is_anomaly, lower_bound, upper_bound, iqr

    def moving_average_detection(self, values, current_value, window=10, threshold_percent=0.3):
        """Detect anomaly using Moving Average method"""
        if len(values) < window:
            return False, 0, 0

        values_array = np.array(values)
        moving_avg = np.mean(values_array[-window:])
        deviation = abs(current_value - moving_avg) / moving_avg if moving_avg != 0 else 0

        is_anomaly = deviation > threshold_percent

        return is_anomaly, moving_avg, deviation

    def exponential_smoothing_detection(self, values, current_value, alpha=0.3, threshold=0.3):
        """Detect anomaly using Exponential Smoothing"""
        if len(values) < 2:
            return False, current_value, 0

        values_array = np.array(values)
        smoothed = values_array[0]

        for value in values_array[1:]:
            smoothed = alpha * value + (1 - alpha) * smoothed

        deviation = abs(current_value - smoothed) / smoothed if smoothed != 0 else 0
        is_anomaly = deviation > threshold

        return is_anomaly, smoothed, deviation

    def detect_trend_anomaly(self, values, window=20):
        """Detect sudden trend changes"""
        if len(values) < window * 2:
            return False, 'stable', 0

        values_array = np.array(values)
        first_half = values_array[-window*2:-window]
        second_half = values_array[-window:]

        first_trend = np.mean(np.diff(first_half))
        second_trend = np.mean(np.diff(second_half))

        trend_change = abs(second_trend - first_trend)

        if trend_change > 2:
            if second_trend > 0:
                return True, 'sudden_increase', trend_change
            else:
                return True, 'sudden_decrease', trend_change

        return False, 'stable', trend_change

    def detect_spike(self, values, current_value, spike_threshold=2):
        """Detect sudden spikes in metrics"""
        if len(values) < 5:
            return False, 0

        recent_avg = np.mean(list(values)[-5:])
        spike_ratio = current_value / recent_avg if recent_avg != 0 else 0

        is_spike = spike_ratio > spike_threshold or spike_ratio < (1 / spike_threshold)

        return is_spike, spike_ratio

    def detect_anomaly(self, metric_name, current_value, sensitivity='medium'):
        """
        Detect anomalies using multiple algorithms
        sensitivity: 'low', 'medium', 'high'
        """
        # Get historical data for this metric
        history = self.load_history()
        metric_data = [
            point['value'] for point in history['metrics_history']
            if point['metric'] == metric_name
        ]

        if len(metric_data) < 10:
            return {
                'is_anomaly': False,
                'confidence': 0,
                'methods': {},
                'message': 'Insufficient data for detection'
            }

        # Adjust thresholds based on sensitivity
        thresholds = {
            'low': {'z_score': 4, 'iqr_mult': 2.0, 'ma_percent': 0.5},
            'medium': {'z_score': 3, 'iqr_mult': 1.5, 'ma_percent': 0.3},
            'high': {'z_score': 2, 'iqr_mult': 1.0, 'ma_percent': 0.2}
        }
        thresh = thresholds.get(sensitivity, thresholds['medium'])

        results = {}

        # Z-score detection
        is_anom_z, mean, z_score = self.z_score_detection(
            metric_data, current_value, thresh['z_score']
        )
        results['z_score'] = {
            'anomaly': is_anom_z,
            'score': float(z_score),
            'mean': float(mean)
        }

        # IQR detection
        is_anom_iqr, lower, upper, iqr = self.iqr_detection(
            metric_data, current_value, thresh['iqr_mult']
        )
        results['iqr'] = {
            'anomaly': is_anom_iqr,
            'lower_bound': float(lower),
            'upper_bound': float(upper),
            'iqr': float(iqr)
        }

        # Moving Average detection
        is_anom_ma, ma, deviation = self.moving_average_detection(
            metric_data, current_value, threshold_percent=thresh['ma_percent']
        )
        results['moving_average'] = {
            'anomaly': is_anom_ma,
            'moving_avg': float(ma),
            'deviation': float(deviation)
        }

        # Exponential Smoothing
        is_anom_es, smoothed, es_dev = self.exponential_smoothing_detection(
            metric_data, current_value, threshold=thresh['ma_percent']
        )
        results['exponential_smoothing'] = {
            'anomaly': is_anom_es,
            'smoothed': float(smoothed),
            'deviation': float(es_dev)
        }

        # Trend anomaly detection
        is_trend_anom, trend_type, trend_change = self.detect_trend_anomaly(metric_data)
        results['trend'] = {
            'anomaly': is_trend_anom,
            'type': trend_type,
            'change': float(trend_change)
        }

        # Spike detection
        is_spike, spike_ratio = self.detect_spike(metric_data, current_value)
        results['spike'] = {
            'anomaly': is_spike,
            'ratio': float(spike_ratio)
        }

        # Aggregate results - anomaly if 2+ methods agree
        anomaly_count = sum([
            results['z_score']['anomaly'],
            results['iqr']['anomaly'],
            results['moving_average']['anomaly'],
            results['exponential_smoothing']['anomaly'],
            results['trend']['anomaly'],
            results['spike']['anomaly']
        ])

        is_anomaly = anomaly_count >= 2
        confidence = (anomaly_count / 6) * 100

        return {
            'is_anomaly': is_anomaly,
            'confidence': confidence,
            'methods': results,
            'anomaly_count': anomaly_count,
            'total_methods': 6
        }

    def record_anomaly(self, metric_name, current_value, detection_result):
        """Record detected anomaly"""
        if not detection_result['is_anomaly']:
            return

        anomalies = self.load_anomalies()

        anomaly = {
            'id': f"anomaly_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            'metric': metric_name,
            'value': current_value,
            'confidence': detection_result['confidence'],
            'methods': detection_result['methods'],
            'severity': self.calculate_severity(detection_result['confidence']),
            'timestamp': datetime.now().isoformat(),
            'acknowledged': False,
            'resolved': False
        }

        anomalies['anomalies'].insert(0, anomaly)

        # Keep only last 1000 anomalies
        anomalies['anomalies'] = anomalies['anomalies'][:1000]

        self.save_anomalies(anomalies)
        return anomaly

    def calculate_severity(self, confidence):
        """Calculate severity based on confidence"""
        if confidence >= 80:
            return 'critical'
        elif confidence >= 60:
            return 'high'
        elif confidence >= 40:
            return 'medium'
        else:
            return 'low'

    def get_anomalies(self, limit=50, severity=None, resolved=None):
        """Get recent anomalies with optional filters"""
        anomalies = self.load_anomalies()
        all_anomalies = anomalies.get('anomalies', [])

        # Filter by severity
        if severity:
            all_anomalies = [a for a in all_anomalies if a.get('severity') == severity]

        # Filter by resolved status
        if resolved is not None:
            all_anomalies = [a for a in all_anomalies if a.get('resolved') == resolved]

        return all_anomalies[:limit]

    def acknowledge_anomaly(self, anomaly_id):
        """Mark anomaly as acknowledged"""
        anomalies = self.load_anomalies()

        for anomaly in anomalies['anomalies']:
            if anomaly.get('id') == anomaly_id:
                anomaly['acknowledged'] = True
                anomaly['acknowledged_at'] = datetime.now().isoformat()
                self.save_anomalies(anomalies)
                return True

        return False

    def resolve_anomaly(self, anomaly_id, resolution_note=''):
        """Mark anomaly as resolved"""
        anomalies = self.load_anomalies()

        for anomaly in anomalies['anomalies']:
            if anomaly.get('id') == anomaly_id:
                anomaly['resolved'] = True
                anomaly['resolved_at'] = datetime.now().isoformat()
                anomaly['resolution_note'] = resolution_note
                self.save_anomalies(anomalies)
                return True

        return False

    def get_insights(self):
        """Generate AI insights from anomaly patterns"""
        anomalies = self.load_anomalies()
        all_anomalies = anomalies.get('anomalies', [])

        if not all_anomalies:
            return {
                'total_anomalies': 0,
                'insights': []
            }

        # Analyze last 24 hours
        cutoff = datetime.now() - timedelta(hours=24)
        recent = [
            a for a in all_anomalies
            if datetime.fromisoformat(a['timestamp']) > cutoff
        ]

        # Count by metric
        by_metric = {}
        for a in recent:
            metric = a.get('metric', 'unknown')
            by_metric[metric] = by_metric.get(metric, 0) + 1

        # Count by severity
        by_severity = {}
        for a in recent:
            severity = a.get('severity', 'low')
            by_severity[severity] = by_severity.get(severity, 0) + 1

        insights = []

        # Most problematic metric
        if by_metric:
            most_problematic = max(by_metric.items(), key=lambda x: x[1])
            insights.append({
                'type': 'metric_alert',
                'priority': 'high',
                'message': f"{most_problematic[0]} has {most_problematic[1]} anomalies in last 24h",
                'recommendation': f"Investigate {most_problematic[0]} for potential issues"
            })

        # Critical anomalies
        critical_count = by_severity.get('critical', 0)
        if critical_count > 0:
            insights.append({
                'type': 'severity_alert',
                'priority': 'critical',
                'message': f"{critical_count} critical anomalies detected",
                'recommendation': "Immediate attention required"
            })

        # Pattern detection
        if len(recent) > 5:
            insights.append({
                'type': 'pattern_alert',
                'priority': 'medium',
                'message': f"Increased anomaly activity: {len(recent)} anomalies in 24h",
                'recommendation': "System may be experiencing degradation"
            })

        return {
            'total_anomalies': len(all_anomalies),
            'recent_24h': len(recent),
            'by_metric': by_metric,
            'by_severity': by_severity,
            'insights': insights
        }

    def get_statistics(self):
        """Get anomaly detection statistics"""
        anomalies = self.load_anomalies()
        all_anomalies = anomalies.get('anomalies', [])

        if not all_anomalies:
            return {
                'total': 0,
                'by_severity': {},
                'by_metric': {},
                'resolved_count': 0,
                'unresolved_count': 0
            }

        by_severity = {}
        by_metric = {}
        resolved = 0

        for anomaly in all_anomalies:
            severity = anomaly.get('severity', 'low')
            metric = anomaly.get('metric', 'unknown')

            by_severity[severity] = by_severity.get(severity, 0) + 1
            by_metric[metric] = by_metric.get(metric, 0) + 1

            if anomaly.get('resolved'):
                resolved += 1

        return {
            'total': len(all_anomalies),
            'by_severity': by_severity,
            'by_metric': by_metric,
            'resolved_count': resolved,
            'unresolved_count': len(all_anomalies) - resolved
        }
