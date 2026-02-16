#!/usr/bin/env python3
"""
Quick Test Script - Run subset of tests for fast validation

Usage:
    python tests/quick_test.py                    # Run quick tests
    python tests/quick_test.py --all              # Run all tests
    python tests/quick_test.py --specific app     # Run specific test
"""

import sys
import unittest
import argparse
from pathlib import Path
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


def run_quick_tests():
    """Run a subset of fast tests for quick validation"""
    print("=" * 70)
    print("QUICK TEST - Running subset of tests for fast validation")
    print("=" * 70)
    print()

    test_files = [
        'test_app_routes',
        'test_monitoring_services',
        'test_ai_services'
    ]

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    for test_file in test_files:
        try:
            module = __import__(test_file)
            suite.addTests(loader.loadTestsFromModule(module))
        except Exception as e:
            print(f"Warning: Could not load {test_file}: {e}")

    runner = unittest.TextTestRunner(verbosity=1)
    start_time = time.time()
    result = runner.run(suite)
    elapsed_time = time.time() - start_time

    print()
    print(f"Quick test completed in {elapsed_time:.2f}s")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    return result.wasSuccessful()


def run_specific_test(test_name):
    """Run a specific test file"""
    print(f"Running test: {test_name}")
    print()

    loader = unittest.TestLoader()

    try:
        module_name = f'test_{test_name}' if not test_name.startswith('test_') else test_name
        module = __import__(module_name)
        suite = loader.loadTestsFromModule(module)
    except ImportError as e:
        print(f"Error: Could not find test '{test_name}'")
        print(f"Details: {e}")
        return False

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


def list_available_tests():
    """List all available test files"""
    test_dir = Path(__file__).parent
    test_files = sorted(test_dir.glob('test_*.py'))

    print("Available tests:")
    print()
    for test_file in test_files:
        print(f"  - {test_file.stem}")
    print()


def main():
    parser = argparse.ArgumentParser(description='Quick test runner')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    parser.add_argument('--specific', help='Run specific test file')
    parser.add_argument('--list', action='store_true', help='List available tests')

    args = parser.parse_args()

    if args.list:
        list_available_tests()
        sys.exit(0)

    if args.all:
        # Run all tests using main runner
        from run_all_tests import discover_and_run_tests
        success = discover_and_run_tests(verbosity=1)
        sys.exit(0 if success else 1)

    if args.specific:
        success = run_specific_test(args.specific)
        sys.exit(0 if success else 1)

    # Default: run quick tests
    success = run_quick_tests()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
