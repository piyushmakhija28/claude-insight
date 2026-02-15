"""
Test script for Performance Profiler and Bottleneck Analyzer
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.monitoring.performance_profiler import PerformanceProfiler
from services.ai.bottleneck_analyzer import BottleneckAnalyzer

def test_performance_profiler():
    """Test PerformanceProfiler functionality"""
    print("=" * 60)
    print("Testing PerformanceProfiler")
    print("=" * 60)

    profiler = PerformanceProfiler()

    # Track some sample operations
    print("\n1. Tracking sample operations...")
    profiler.track_operation('Read', 'test.py', 150.5, {'lines': 100}, success=True, optimization_applied=True)
    profiler.track_operation('Read', 'large_file.py', 3500.0, {'lines': 1000}, success=True, optimization_applied=False)
    profiler.track_operation('Grep', 'pattern', 250.0, {'matches': 50}, success=True, optimization_applied=True)
    profiler.track_operation('Bash', 'npm install', 5500.0, {}, success=True, optimization_applied=False)
    profiler.track_operation('Write', 'output.txt', 100.0, {}, success=True, optimization_applied=True)

    # Get stats
    print("\n2. Getting statistics...")
    stats = profiler.get_stats_summary()
    print(f"   Total operations: {stats['total_operations']}")
    print(f"   Average duration: {stats['avg_duration_ms']:.2f}ms")
    print(f"   Slow operations: {stats['slow_operations_count']}")
    print(f"   Optimization rate: {stats['optimization_rate']:.1f}%")

    # Get slow operations
    print("\n3. Getting slow operations...")
    slow_ops = profiler.get_slow_operations(threshold_ms=2000)
    print(f"   Found {len(slow_ops)} slow operations")
    for op in slow_ops:
        print(f"   - {op['tool']}: {op['target'][:40]} ({op['duration_ms']:.0f}ms)")

    # Get bottlenecks
    print("\n4. Getting bottlenecks...")
    bottlenecks = profiler.get_bottlenecks()
    for tool, ops in bottlenecks.items():
        print(f"   {tool}: {len(ops)} bottleneck(s)")

    print("\n[OK] PerformanceProfiler test passed!")
    return profiler

def test_bottleneck_analyzer(profiler):
    """Test BottleneckAnalyzer functionality"""
    print("\n" + "=" * 60)
    print("Testing BottleneckAnalyzer")
    print("=" * 60)

    analyzer = BottleneckAnalyzer()

    # Get recommendations
    print("\n1. Generating recommendations...")
    slow_ops = profiler.get_slow_operations()
    recommendations = analyzer.generate_recommendations(slow_ops)

    print(f"   Found {len(recommendations)} recommendations")
    for i, rec in enumerate(recommendations, 1):
        print(f"\n   Recommendation {i}:")
        print(f"   - Type: {rec['type']}")
        print(f"   - Severity: {rec['severity']}")
        print(f"   - Title: {rec['title']}")
        print(f"   - Suggestion: {rec['suggestion'][:60]}...")

    print("\n[OK] BottleneckAnalyzer test passed!")

def main():
    """Run all tests"""
    try:
        profiler = test_performance_profiler()
        test_bottleneck_analyzer(profiler)

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED! [OK]")
        print("=" * 60)
        print("\nYou can now start the application:")
        print("cd src && python run.py")

    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
