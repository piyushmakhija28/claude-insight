#!/usr/bin/env python3
"""
Comprehensive Unit Tests for AI Services

Tests all AI services including:
- AnomalyDetector
- PredictiveAnalytics
- BottleneckAnalyzer
"""

import unittest
import json
import tempfile
import os
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


class TestAnomalyDetector(unittest.TestCase):
    """Test suite for AnomalyDetector"""

    def setUp(self):
        """Set up test fixtures"""
        from services.ai.anomaly_detector import AnomalyDetector
        self.detector = AnomalyDetector()

    def test_detect_anomalies_empty_data(self):
        """Test anomaly detection with empty data"""
        data = []
        anomalies = self.detector.detect_anomalies(data)

        self.assertIsInstance(anomalies, list)
        self.assertEqual(len(anomalies), 0)

    def test_detect_anomalies_normal_data(self):
        """Test anomaly detection with normal data"""
        # Create normal distribution data
        data = [
            {'value': 100, 'timestamp': '2026-02-16 10:00:00'},
            {'value': 105, 'timestamp': '2026-02-16 10:01:00'},
            {'value': 98, 'timestamp': '2026-02-16 10:02:00'},
            {'value': 102, 'timestamp': '2026-02-16 10:03:00'},
        ]

        anomalies = self.detector.detect_anomalies(data, threshold=3.0)

        self.assertIsInstance(anomalies, list)
        # Normal data should have few/no anomalies
        self.assertLessEqual(len(anomalies), 1)

    def test_detect_anomalies_with_outliers(self):
        """Test anomaly detection with clear outliers"""
        data = [
            {'value': 100, 'timestamp': '2026-02-16 10:00:00'},
            {'value': 105, 'timestamp': '2026-02-16 10:01:00'},
            {'value': 1000, 'timestamp': '2026-02-16 10:02:00'},  # Outlier
            {'value': 98, 'timestamp': '2026-02-16 10:03:00'},
        ]

        anomalies = self.detector.detect_anomalies(data, threshold=2.0)

        self.assertIsInstance(anomalies, list)
        # Should detect the outlier
        self.assertGreater(len(anomalies), 0)

    def test_statistical_anomaly_detection(self):
        """Test statistical anomaly detection method"""
        values = [10, 12, 11, 10, 100, 11, 12]  # 100 is anomaly

        anomalies = self.detector.statistical_anomaly_detection(values, threshold=2.5)

        self.assertIsInstance(anomalies, list)
        self.assertGreater(len(anomalies), 0)

    def test_time_series_anomaly_detection(self):
        """Test time series anomaly detection"""
        data = []
        base_time = datetime.now()

        for i in range(20):
            data.append({
                'timestamp': (base_time + timedelta(minutes=i)).isoformat(),
                'value': 100 + (5 if i != 10 else 500)  # Spike at i=10
            })

        anomalies = self.detector.time_series_anomaly_detection(data)

        self.assertIsInstance(anomalies, list)

    def test_get_anomaly_score(self):
        """Test getting anomaly score for value"""
        values = [10, 12, 11, 10, 11, 12]
        mean = np.mean(values)
        std = np.std(values)

        score = self.detector.get_anomaly_score(100, mean, std)

        self.assertIsInstance(score, float)
        self.assertGreater(score, 0)


class TestPredictiveAnalytics(unittest.TestCase):
    """Test suite for PredictiveAnalytics"""

    def setUp(self):
        """Set up test fixtures"""
        from services.ai.predictive_analytics import PredictiveAnalytics
        self.analytics = PredictiveAnalytics()

    def test_predict_future_usage_empty(self):
        """Test prediction with empty historical data"""
        historical = []
        prediction = self.analytics.predict_future_usage(historical, hours=24)

        self.assertIsInstance(prediction, dict)
        self.assertIn('predictions', prediction)

    def test_predict_future_usage_linear(self):
        """Test linear trend prediction"""
        # Create linear growth data
        historical = []
        base_time = datetime.now()

        for i in range(10):
            historical.append({
                'timestamp': (base_time + timedelta(hours=i)).isoformat(),
                'value': 100 + (i * 10)  # Linear growth
            })

        prediction = self.analytics.predict_future_usage(historical, hours=5)

        self.assertIsInstance(prediction, dict)
        self.assertIn('predictions', prediction)
        self.assertIn('trend', prediction)

    def test_detect_trend(self):
        """Test trend detection"""
        # Upward trend
        values_up = [10, 20, 30, 40, 50]
        trend_up = self.analytics.detect_trend(values_up)
        self.assertEqual(trend_up, 'increasing')

        # Downward trend
        values_down = [50, 40, 30, 20, 10]
        trend_down = self.analytics.detect_trend(values_down)
        self.assertEqual(trend_down, 'decreasing')

        # Stable trend
        values_stable = [10, 11, 10, 11, 10]
        trend_stable = self.analytics.detect_trend(values_stable)
        self.assertEqual(trend_stable, 'stable')

    def test_calculate_forecast_confidence(self):
        """Test forecast confidence calculation"""
        historical = list(range(10))
        predictions = [10, 11, 12]

        confidence = self.analytics.calculate_forecast_confidence(historical, predictions)

        self.assertIsInstance(confidence, float)
        self.assertGreaterEqual(confidence, 0)
        self.assertLessEqual(confidence, 100)

    def test_predict_resource_needs(self):
        """Test resource needs prediction"""
        current_usage = {
            'cpu': 60,
            'memory': 70,
            'disk': 50
        }

        growth_rate = 0.1  # 10% growth

        predictions = self.analytics.predict_resource_needs(
            current_usage,
            growth_rate,
            days=30
        )

        self.assertIsInstance(predictions, dict)
        self.assertIn('cpu', predictions)
        self.assertIn('memory', predictions)

    def test_identify_usage_patterns(self):
        """Test usage pattern identification"""
        data = []
        base_time = datetime.now()

        # Create hourly pattern with peak at hour 12
        for i in range(24):
            value = 100 if i != 12 else 500
            data.append({
                'timestamp': (base_time + timedelta(hours=i)).isoformat(),
                'value': value
            })

        patterns = self.analytics.identify_usage_patterns(data)

        self.assertIsInstance(patterns, dict)
        self.assertIn('peak_hours', patterns)


class TestBottleneckAnalyzer(unittest.TestCase):
    """Test suite for BottleneckAnalyzer"""

    def setUp(self):
        """Set up test fixtures"""
        from services.ai.bottleneck_analyzer import BottleneckAnalyzer
        self.analyzer = BottleneckAnalyzer()

    def test_analyze_performance_empty(self):
        """Test performance analysis with empty data"""
        metrics = []
        analysis = self.analyzer.analyze_performance(metrics)

        self.assertIsInstance(analysis, dict)

    def test_analyze_performance_with_bottlenecks(self):
        """Test performance analysis identifying bottlenecks"""
        metrics = [
            {'operation': 'read_file', 'duration': 1000, 'timestamp': '2026-02-16 10:00:00'},
            {'operation': 'write_file', 'duration': 50, 'timestamp': '2026-02-16 10:01:00'},
            {'operation': 'read_file', 'duration': 1200, 'timestamp': '2026-02-16 10:02:00'},
        ]

        analysis = self.analyzer.analyze_performance(metrics)

        self.assertIsInstance(analysis, dict)
        self.assertIn('bottlenecks', analysis)

    def test_identify_slow_operations(self):
        """Test identifying slow operations"""
        metrics = [
            {'operation': 'fast_op', 'duration': 10},
            {'operation': 'slow_op', 'duration': 1000},
            {'operation': 'medium_op', 'duration': 100},
        ]

        slow_ops = self.analyzer.identify_slow_operations(metrics, threshold=500)

        self.assertIsInstance(slow_ops, list)
        self.assertGreater(len(slow_ops), 0)

    def test_analyze_operation_frequency(self):
        """Test analyzing operation frequency"""
        metrics = [
            {'operation': 'op1', 'timestamp': '2026-02-16 10:00:00'},
            {'operation': 'op1', 'timestamp': '2026-02-16 10:01:00'},
            {'operation': 'op2', 'timestamp': '2026-02-16 10:02:00'},
            {'operation': 'op1', 'timestamp': '2026-02-16 10:03:00'},
        ]

        frequency = self.analyzer.analyze_operation_frequency(metrics)

        self.assertIsInstance(frequency, dict)
        self.assertIn('op1', frequency)
        self.assertEqual(frequency['op1'], 3)

    def test_calculate_percentiles(self):
        """Test percentile calculation"""
        durations = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]

        percentiles = self.analyzer.calculate_percentiles(durations)

        self.assertIsInstance(percentiles, dict)
        self.assertIn('p50', percentiles)
        self.assertIn('p95', percentiles)
        self.assertIn('p99', percentiles)

    def test_suggest_optimizations(self):
        """Test optimization suggestions"""
        bottlenecks = [
            {'operation': 'database_query', 'avg_duration': 1000},
            {'operation': 'file_read', 'avg_duration': 500}
        ]

        suggestions = self.analyzer.suggest_optimizations(bottlenecks)

        self.assertIsInstance(suggestions, list)
        self.assertGreater(len(suggestions), 0)

    def test_analyze_resource_utilization(self):
        """Test resource utilization analysis"""
        metrics = [
            {'cpu': 80, 'memory': 70, 'timestamp': '2026-02-16 10:00:00'},
            {'cpu': 85, 'memory': 75, 'timestamp': '2026-02-16 10:01:00'},
            {'cpu': 90, 'memory': 80, 'timestamp': '2026-02-16 10:02:00'},
        ]

        analysis = self.analyzer.analyze_resource_utilization(metrics)

        self.assertIsInstance(analysis, dict)
        self.assertIn('cpu', analysis)
        self.assertIn('memory', analysis)

    def test_detect_memory_leaks(self):
        """Test memory leak detection"""
        # Simulate memory leak - constantly increasing
        metrics = []
        for i in range(20):
            metrics.append({
                'memory': 50 + (i * 5),  # Constantly increasing
                'timestamp': f'2026-02-16 10:{i:02d}:00'
            })

        leak_detected = self.analyzer.detect_memory_leaks(metrics)

        self.assertIsInstance(leak_detected, bool)

    def test_analyze_concurrent_operations(self):
        """Test concurrent operations analysis"""
        operations = [
            {'start': '2026-02-16 10:00:00', 'end': '2026-02-16 10:01:00', 'type': 'op1'},
            {'start': '2026-02-16 10:00:30', 'end': '2026-02-16 10:01:30', 'type': 'op2'},
            {'start': '2026-02-16 10:02:00', 'end': '2026-02-16 10:03:00', 'type': 'op3'},
        ]

        analysis = self.analyzer.analyze_concurrent_operations(operations)

        self.assertIsInstance(analysis, dict)


class TestAIServiceIntegration(unittest.TestCase):
    """Integration tests for AI services working together"""

    def setUp(self):
        """Set up test fixtures"""
        from services.ai.anomaly_detector import AnomalyDetector
        from services.ai.predictive_analytics import PredictiveAnalytics
        from services.ai.bottleneck_analyzer import BottleneckAnalyzer

        self.detector = AnomalyDetector()
        self.analytics = PredictiveAnalytics()
        self.analyzer = BottleneckAnalyzer()

    def test_full_analysis_pipeline(self):
        """Test complete analysis pipeline"""
        # Generate sample data
        metrics = []
        base_time = datetime.now()

        for i in range(50):
            metrics.append({
                'timestamp': (base_time + timedelta(minutes=i)).isoformat(),
                'operation': 'test_op',
                'duration': 100 + (i * 2) + (1000 if i == 25 else 0),  # Spike at i=25
                'cpu': 60 + (i % 10),
                'memory': 50 + (i % 15)
            })

        # 1. Detect anomalies
        anomalies = self.detector.detect_anomalies(metrics)
        self.assertIsInstance(anomalies, list)

        # 2. Analyze bottlenecks
        bottlenecks = self.analyzer.analyze_performance(metrics)
        self.assertIsInstance(bottlenecks, dict)

        # 3. Predict future usage
        predictions = self.analytics.predict_future_usage(metrics, hours=12)
        self.assertIsInstance(predictions, dict)

        # All services should complete successfully
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
