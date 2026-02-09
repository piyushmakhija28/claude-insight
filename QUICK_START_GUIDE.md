# Quick Start Guide - New Features

## New Features Overview

### 1. Custom Error Pages
Professional 404 and 500 error pages with helpful navigation and matching design.

### 2. CSV Export Functionality
Export your data with one click:
- **Dashboard:** Export system metrics
- **Sessions:** Export session history
- **Logs:** Export activity logs

### 3. Settings Page
Customize your dashboard experience with preferences for:
- Auto-refresh intervals
- Default landing page
- Dashboard density
- Export formats
- Advanced options

---

## Quick Access

### Settings Page
**Navigation:** Click "Settings" in the navbar (next to Logout)

**Quick Settings:**
- Auto-Refresh: `30 seconds` (default)
- Theme: `Light Mode` (Dark mode coming soon)
- Default Page: `Dashboard`
- Export Format: `CSV`

### Export Data

**Export Sessions:**
1. Go to Sessions page
2. Scroll to "Recent Sessions (Last 10)"
3. Click "Export to CSV" button
4. File downloads: `claude_sessions_YYYYMMDD_HHMMSS.csv`

**Export Metrics:**
1. Go to Dashboard
2. Click "Export Metrics" button (top right)
3. File downloads: `claude_metrics_YYYYMMDD_HHMMSS.csv`

**Export Logs:**
1. Go to Logs page
2. Click "Export to CSV" button (top right)
3. File downloads: `claude_logs_YYYYMMDD_HHMMSS.csv`

---

## Settings Explained

### Display Settings

**Auto-Refresh Interval**
- Controls how often the dashboard updates automatically
- Options: Disabled, 30s, 60s, 120s, 300s
- Default: 30 seconds

**Default Page on Login**
- Sets which page loads after you log in
- Options: Dashboard, Cost Comparison, Policies, Logs, Sessions
- Default: Dashboard

**Dashboard Density**
- Adjusts spacing and card sizes
- Options: Comfortable, Compact, Spacious
- Default: Comfortable

### Data & Export

**Log Retention Period**
- How long to keep historical logs
- Options: 7, 30, 60, 90, 180 days
- Default: 30 days

**Default Export Format**
- Preferred format for exported data
- Options: CSV, JSON (coming soon), Excel (coming soon)
- Default: CSV

**Include Headers in Exports**
- Adds column headers to CSV files
- Default: Enabled

### Advanced Settings

**Show Debug Information**
- Displays additional technical details
- Default: Disabled

**Show API Response Times**
- Shows how long API calls take
- Default: Disabled

**Compact Navigation**
- Uses a smaller navigation bar
- Default: Disabled

---

## Tips & Tricks

### Settings Management
1. **Save Your Changes:** Settings won't persist until you click "Save Settings"
2. **Status Indicator:** Watch the status badge (Green = Saved, Yellow = Unsaved)
3. **Reset Anytime:** Use "Reset to Defaults" to restore original settings
4. **Clear Data:** Use with caution - clears all stored preferences

### Export Best Practices
1. **Regular Exports:** Export sessions regularly for record keeping
2. **Timestamp Naming:** Files include date/time to prevent overwrites
3. **CSV Format:** Opens easily in Excel, Google Sheets, or any text editor
4. **Headers Included:** Column headers make data easier to understand

### Error Pages
- **404 Page:** Includes quick links to all main sections
- **500 Page:** Offers troubleshooting tips and retry option
- **Navigation:** Both pages provide easy return to dashboard

---

## Keyboard Shortcuts (Future)

Coming in a future update:
- `Ctrl + E` - Export current page data
- `Ctrl + ,` - Open Settings
- `Ctrl + R` - Refresh dashboard
- `Ctrl + /` - Show keyboard shortcuts help

---

## Troubleshooting

### Settings Not Saving
- **Issue:** Settings revert after page reload
- **Solution:** Make sure to click "Save Settings" button
- **Check:** Look for green "Saved" status badge

### Export Not Working
- **Issue:** CSV file not downloading
- **Solution:** Check browser's download permissions
- **Check:** Look for blocked downloads in browser settings

### Error Pages Not Showing
- **Issue:** Default error pages appear instead
- **Solution:** Restart the Flask application
- **Check:** Verify templates folder contains 404.html and 500.html

---

## What's Coming Soon

### Planned Features
- Dark mode theme
- Browser notifications for system alerts
- JSON and Excel export formats
- Settings sync across devices
- Keyboard shortcuts
- Custom notification rules
- Export scheduling
- Data filtering before export

---

## Support

### Getting Help
1. Check the Settings page for configuration options
2. Review the ENHANCEMENTS_SUMMARY.md for technical details
3. Check browser console for JavaScript errors
4. Verify Flask is running without errors

### File Locations
- Settings Page: `http://localhost:5000/settings`
- Export Endpoints:
  - Sessions: `http://localhost:5000/api/export/sessions`
  - Metrics: `http://localhost:5000/api/export/metrics`
  - Logs: `http://localhost:5000/api/export/logs`

---

## Version Info
- **Version:** 2.0 (Enhanced)
- **Last Updated:** February 9, 2026
- **New Pages:** 3 (404, 500, Settings)
- **New Routes:** 4 (Settings + 3 Export endpoints)
- **New Features:** Custom errors, CSV export, Settings management

---

**Enjoy the enhanced Claude Monitoring System!**
