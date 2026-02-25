#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script to verify Claude Insight UI rendering
Simulates login and checks if new admin dashboard UI is being served
"""

import sys
import io
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from flask import session
from app import app
import re

def test_template_exists():
    """Test if base.html contains new admin layout"""
    print("=" * 70)
    print("TEST 1: Verify Template File Contains New UI")
    print("=" * 70)

    template_path = Path(__file__).parent / 'templates' / 'base.html'

    if not template_path.exists():
        print(f"❌ FAIL: Template not found at {template_path}")
        return False

    content = template_path.read_text(encoding='utf-8')

    # Check for new UI elements
    checks = {
        'admin-wrapper class': 'class="admin-wrapper"' in content,
        'admin-sidebar class': 'class="admin-sidebar"' in content,
        'sidebar-brand class': 'class="sidebar-brand"' in content,
        'admin-header class': 'class="admin-header"' in content,
        'admin-content class': 'class="admin-content"' in content,
        'professional CSS': '--primary-color: #6366f1' in content,
        'Fixed sidebar width': 'width: 260px' in content,
    }

    all_passed = True
    for check_name, result in checks.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {check_name}")
        if not result:
            all_passed = False

    print(f"\nFile size: {len(content)} bytes ({len(content.splitlines())} lines)")
    print(f"Modified: {template_path.stat().st_mtime}")

    return all_passed

def test_flask_configuration():
    """Test if Flask is configured correctly"""
    print("\n" + "=" * 70)
    print("TEST 2: Verify Flask Configuration")
    print("=" * 70)

    checks = {
        'Template folder exists': Path(app.template_folder).exists(),
        'Static folder exists': Path(app.static_folder).exists(),
        'base.html exists': (Path(app.template_folder) / 'base.html').exists(),
        'dashboard.html exists': (Path(app.template_folder) / 'dashboard.html').exists(),
    }

    all_passed = True
    for check_name, result in checks.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {check_name}")
        if not result:
            all_passed = False

    print(f"\nTemplate folder: {app.template_folder}")
    print(f"Static folder: {app.static_folder}")

    return all_passed

def test_login_renders():
    """Test if login page renders correctly"""
    print("\n" + "=" * 70)
    print("TEST 3: Test Login Page Rendering")
    print("=" * 70)

    with app.test_client() as client:
        response = client.get('/login')

        print(f"Status code: {response.status_code}")

        if response.status_code != 200:
            print("❌ FAIL: Login page did not return 200")
            return False

        html = response.data.decode('utf-8')

        checks = {
            'Contains DOCTYPE': '<!DOCTYPE html>' in html,
            'Contains admin-wrapper CSS': '.admin-wrapper' in html,
            'Contains admin-sidebar CSS': '.admin-sidebar' in html,
            'Contains login form': '<form method="POST"' in html,
            'Contains Claude Insight branding': 'Claude Insight' in html,
        }

        all_passed = True
        for check_name, result in checks.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {check_name}")
            if not result:
                all_passed = False

        return all_passed

def test_dashboard_renders():
    """Test if dashboard renders with new UI after login"""
    print("\n" + "=" * 70)
    print("TEST 4: Test Dashboard Rendering After Login")
    print("=" * 70)

    with app.test_client() as client:
        # Login first
        login_response = client.post('/login', data={
            'username': 'admin',
            'password': 'admin'
        }, follow_redirects=False)

        print(f"Login status: {login_response.status_code}")

        if login_response.status_code not in [200, 302]:
            print("❌ FAIL: Login failed")
            return False

        # Access dashboard
        dashboard_response = client.get('/dashboard', follow_redirects=True)

        print(f"Dashboard status: {dashboard_response.status_code}")

        if dashboard_response.status_code != 200:
            print("❌ FAIL: Dashboard did not return 200")
            return False

        html = dashboard_response.data.decode('utf-8')

        checks = {
            'Contains admin-wrapper div': '<div class="admin-wrapper">' in html,
            'Contains admin-sidebar': '<aside class="admin-sidebar"' in html,
            'Contains sidebar-brand': 'sidebar-brand' in html,
            'Contains admin-header': 'admin-header' in html or 'admin-content' in html,
            'Contains page-header': 'page-header' in html or 'page-title' in html,
            'Contains stat cards': 'stat-card' in html or 'card-body' in html,
            'Contains dashboard title': 'Dashboard' in html or 'System Dashboard' in html,
            'Contains logout link': 'logout' in html.lower(),
        }

        all_passed = True
        for check_name, result in checks.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {check_name}")
            if not result:
                all_passed = False

        # Count occurrences of key elements
        admin_wrapper_count = html.count('admin-wrapper')
        admin_sidebar_count = html.count('admin-sidebar')

        print(f"\nHTML size: {len(html)} bytes")
        print(f"'admin-wrapper' occurrences: {admin_wrapper_count}")
        print(f"'admin-sidebar' occurrences: {admin_sidebar_count}")

        return all_passed

def test_static_files():
    """Test if static files are accessible"""
    print("\n" + "=" * 70)
    print("TEST 5: Verify Static Files")
    print("=" * 70)

    static_folder = Path(app.static_folder)

    expected_files = [
        'css',  # folder
        'js',   # folder
    ]

    all_passed = True
    for item in expected_files:
        path = static_folder / item
        exists = path.exists()
        status = "✅ PASS" if exists else "❌ FAIL"
        print(f"{status}: {item} exists")
        if not exists:
            all_passed = False

    return all_passed

def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("CLAUDE INSIGHT UI RENDERING TEST SUITE")
    print("=" * 70)
    print(f"Project root: {Path(__file__).parent}")
    print(f"Python version: {sys.version}")
    print("=" * 70)

    tests = [
        ("Template File Check", test_template_exists),
        ("Flask Configuration", test_flask_configuration),
        ("Login Page Rendering", test_login_renders),
        ("Dashboard Rendering", test_dashboard_renders),
        ("Static Files Check", test_static_files),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n❌ ERROR in {test_name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n🎉 ALL TESTS PASSED! New UI is rendering correctly.")
        print("\nIf you're still seeing old UI in browser:")
        print("  1. Clear browser cache (Ctrl+Shift+R)")
        print("  2. Try incognito/private window")
        print("  3. Check browser console for errors (F12)")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED. Check errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
