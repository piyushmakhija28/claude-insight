#!/usr/bin/env python3
"""
Verification script for Claude Monitoring System enhancements
Checks if all new features are properly installed
"""

import os
import sys

def verify_files():
    """Verify all required files exist"""
    print("=" * 60)
    print("Claude Monitoring System - Enhancement Verification")
    print("=" * 60)
    print()

    base_path = os.path.dirname(os.path.abspath(__file__))

    required_files = {
        'Error Pages': [
            'templates/404.html',
            'templates/500.html'
        ],
        'Settings Page': [
            'templates/settings.html'
        ],
        'Documentation': [
            'ENHANCEMENTS_SUMMARY.md',
            'QUICK_START_GUIDE.md'
        ],
        'Main Application': [
            'app.py'
        ]
    }

    all_good = True

    for category, files in required_files.items():
        print(f"\n{category}:")
        print("-" * 60)
        for file in files:
            file_path = os.path.join(base_path, file)
            exists = os.path.exists(file_path)
            status = "[FOUND]" if exists else "[MISSING]"
            print(f"  {status}: {file}")
            if not exists:
                all_good = False

    return all_good

def verify_app_routes():
    """Verify required routes exist in app.py"""
    print("\n\nRoute Verification:")
    print("-" * 60)

    app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.py')

    if not os.path.exists(app_path):
        print("  [MISSING]: app.py file not found")
        return False

    with open(app_path, 'r', encoding='utf-8') as f:
        content = f.read()

    required_routes = {
        '/settings': '@app.route(\'/settings\')',
        '/api/export/sessions': '@app.route(\'/api/export/sessions\')',
        '/api/export/metrics': '@app.route(\'/api/export/metrics\')',
        '/api/export/logs': '@app.route(\'/api/export/logs\')',
        '404 handler': '@app.errorhandler(404)',
        '500 handler': '@app.errorhandler(500)'
    }

    all_good = True
    for route_name, route_code in required_routes.items():
        found = route_code in content
        status = "[FOUND]" if found else "[MISSING]"
        print(f"  {status}: {route_name}")
        if not found:
            all_good = False

    return all_good

def verify_imports():
    """Verify required imports exist in app.py"""
    print("\n\nImport Verification:")
    print("-" * 60)

    app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.py')

    if not os.path.exists(app_path):
        print("  [MISSING]: app.py file not found")
        return False

    with open(app_path, 'r', encoding='utf-8') as f:
        content = f.read()

    required_imports = {
        'Response': 'from flask import',
        'csv': 'import csv',
        'io': 'import io'
    }

    all_good = True
    for import_name, import_code in required_imports.items():
        found = import_code in content
        status = "[FOUND]" if found else "[MISSING]"
        print(f"  {status}: {import_name} ({import_code})")
        if not found:
            all_good = False

    return all_good

def verify_navbar():
    """Verify Settings link added to navbar"""
    print("\n\nNavbar Verification:")
    print("-" * 60)

    base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates/base.html')

    if not os.path.exists(base_path):
        print("  [MISSING]: templates/base.html not found")
        return False

    with open(base_path, 'r', encoding='utf-8') as f:
        content = f.read()

    checks = {
        'Settings link': 'url_for(\'settings\')',
        'Settings icon': '<i class="fas fa-cog"></i> Settings'
    }

    all_good = True
    for check_name, check_code in checks.items():
        found = check_code in content
        status = "[FOUND]" if found else "[MISSING]"
        print(f"  {status}: {check_name}")
        if not found:
            all_good = False

    return all_good

def verify_export_buttons():
    """Verify export buttons added to pages"""
    print("\n\nExport Button Verification:")
    print("-" * 60)

    pages = {
        'Dashboard (templates/dashboard.html)': 'export_metrics',
        'Sessions (templates/sessions.html)': 'export_sessions',
        'Logs (templates/logs.html)': 'export_logs'
    }

    all_good = True
    for page_name, export_route in pages.items():
        page_file = page_name.split('(')[1].strip(')')
        page_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), page_file)

        if not os.path.exists(page_path):
            print(f"  [MISSING]: {page_file}")
            all_good = False
            continue

        with open(page_path, 'r', encoding='utf-8') as f:
            content = f.read()

        found = export_route in content
        status = "[FOUND]" if found else "[MISSING]"
        print(f"  {status}: {page_name} -> {export_route}")
        if not found:
            all_good = False

    return all_good

def main():
    """Run all verifications"""
    results = []

    results.append(verify_files())
    results.append(verify_app_routes())
    results.append(verify_imports())
    results.append(verify_navbar())
    results.append(verify_export_buttons())

    print("\n\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    if all(results):
        print("\n[SUCCESS] ALL CHECKS PASSED!")
        print("\nAll enhancements are properly installed and configured.")
        print("\nYou can now run the application with:")
        print("  python app.py")
        print("\nThen access the new features:")
        print("  - Settings: http://localhost:5000/settings")
        print("  - Export: Available on Dashboard, Sessions, and Logs pages")
        print("  - Error Pages: Navigate to non-existent URL to test 404")
        print("\n")
        return 0
    else:
        print("\n[FAILED] SOME CHECKS FAILED!")
        print("\nPlease review the missing items above and ensure all")
        print("enhancements are properly installed.")
        print("\n")
        return 1

if __name__ == '__main__':
    sys.exit(main())
