# Performance Profiling Dashboard - Quick Start Guide

## 🚀 Getting Started in 60 Seconds

### 1. Start the Application
```bash
cd C:\Users\techd\Documents\workspace-spring-tool-suite-4-4.27.0-new\claude-monitoring-system\src
python run.py
```

### 2. Open Your Browser
```
http://localhost:5000
```

### 3. Login
```
Username: admin
Password: admin
```

### 4. Navigate to Performance Profiling
Click **"Performance"** in the sidebar (between "Alert Routing" and "Policies")

### 5. View the Dashboard
You should see:
- ✓ 4 KPI cards (Total Ops, Avg Time, Slow Ops, Optimization Rate)
- ✓ 2 charts (Response Time Trends, Operations by Tool)
- ✓ AI Recommendations section
- ✓ Slow Operations table

---

## 📊 Understanding the Dashboard

### KPI Cards (Top Row)

#### Total Operations
- Shows count of all operations tracked
- Updates every 30 seconds
- Timeframe: Last 24 hours

#### Average Response Time
- Mean duration of all operations
- Measured in milliseconds (ms)
- Lower is better

#### Slow Operations
- Count of operations taking >2 seconds
- Indicates potential bottlenecks
- Should be minimized

#### Optimization Rate
- Percentage using optimizations (offset/limit/head_limit)
- Target: >80%
- Higher is better

### Charts (Middle Row)

#### Response Time Trends (Line Chart)
- Shows average duration over 7 days
- Helps identify performance regression
- Look for upward trends (bad) or downward (good)

#### Operations by Tool (Doughnut Chart)
- Distribution of tool usage
- Read, Write, Grep, Bash, etc.
- Helps identify most-used tools

### AI Recommendations (Third Row)

Color-coded alerts with:
- **Title**: Brief description
- **Description**: Detailed explanation
- **Suggestion**: How to fix
- **Example**: Code snippet

Severity levels:
- 🔴 Critical (red) - Immediate action needed
- 🟡 High (yellow) - Should fix soon
- 🔵 Medium (blue) - Optimize when possible
- ⚪ Low (white) - Nice to have

### Slow Operations Table (Bottom Row)

Columns:
- **Tool**: Which tool was used (Read, Grep, etc.)
- **Target**: File path or command
- **Duration**: How long it took (ms)
- **Time**: When it happened
- **Optimization**: Whether optimizations were used

---

## 🧪 Testing the Dashboard

### Run the Test Script
```bash
cd C:\Users\techd\Documents\workspace-spring-tool-suite-4-4.27.0-new\claude-monitoring-system
python test_performance.py
```

### Expected Output
```
============================================================
Testing PerformanceProfiler
============================================================

1. Tracking sample operations...
2. Getting statistics...
   Total operations: 10
   Average duration: 1900.10ms
   Slow operations: 4
   Optimization rate: 60.0%

[OK] PerformanceProfiler test passed!

============================================================
Testing BottleneckAnalyzer
============================================================

1. Generating recommendations...
   Found 1 recommendations

[OK] BottleneckAnalyzer test passed!

ALL TESTS PASSED! [OK]
```

---

## 🔍 API Endpoints Reference

### Get Statistics
```bash
curl http://localhost:5000/api/performance/stats
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total_operations": 100,
    "avg_duration_ms": 1234.5,
    "slow_operations_count": 5,
    "optimization_rate": 75.0,
    "tools_breakdown": {
      "Read": 50,
      "Write": 20,
      "Grep": 15,
      "Bash": 10,
      "Edit": 5
    }
  }
}
```

### Get Slow Operations
```bash
curl "http://localhost:5000/api/performance/slow-operations?threshold=2000&limit=10"
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "tool": "Read",
      "target": "large_file.py",
      "duration_ms": 3500.0,
      "timestamp": "2026-02-15T10:30:45",
      "success": true,
      "optimization_applied": false,
      "size_bytes": 125000
    }
  ],
  "count": 1
}
```

### Get Recommendations
```bash
curl http://localhost:5000/api/performance/recommendations
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "type": "optimization",
      "severity": "high",
      "title": "5 Large Files Read Without Optimization",
      "description": "Found 5 files (total 2.5MB) read without offset/limit parameters.",
      "suggestion": "Use Read tool with offset and limit parameters for files >500 lines.",
      "example": "Read(file_path=\"large_file.py\", offset=0, limit=500)"
    }
  ],
  "count": 1
}
```

### Get Trends
```bash
curl "http://localhost:5000/api/performance/trends?days=7"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "labels": ["2026-02-09", "2026-02-10", "2026-02-11", "2026-02-12", "2026-02-13", "2026-02-14", "2026-02-15"],
    "avg_durations": [1500, 1450, 1400, 1600, 1550, 1500, 1480],
    "operation_counts": [100, 120, 110, 130, 115, 125, 118],
    "slow_op_counts": [5, 4, 3, 6, 5, 4, 4]
  }
}
```

---

## 💻 Tracking Operations in Code

### Import the Service
```python
from services.monitoring.performance_profiler import PerformanceProfiler

profiler = PerformanceProfiler()
```

### Track an Operation
```python
import time

start = time.time()
# Your operation here
duration_ms = (time.time() - start) * 1000

profiler.track_operation(
    tool='Read',
    target='file.py',
    duration_ms=duration_ms,
    metadata={'lines': 100},
    success=True,
    optimization_applied=True  # Did you use offset/limit?
)
```

### Full Example
```python
from services.monitoring.performance_profiler import PerformanceProfiler
from services.ai.bottleneck_analyzer import BottleneckAnalyzer
import time

# Initialize services
profiler = PerformanceProfiler()
analyzer = BottleneckAnalyzer()

# Track some operations
profiler.track_operation('Read', 'test.py', 150.5, {'lines': 100}, True, True)
profiler.track_operation('Read', 'large_file.py', 3500.0, {'lines': 1000}, True, False)
profiler.track_operation('Grep', 'pattern', 250.0, {'matches': 50}, True, True)
profiler.track_operation('Bash', 'npm install', 5500.0, {}, True, False)

# Get statistics
stats = profiler.get_stats_summary()
print(f"Total operations: {stats['total_operations']}")
print(f"Average duration: {stats['avg_duration_ms']:.2f}ms")
print(f"Slow operations: {stats['slow_operations_count']}")

# Get recommendations
slow_ops = profiler.get_slow_operations()
recommendations = analyzer.generate_recommendations(slow_ops)

for rec in recommendations:
    print(f"\n{rec['severity'].upper()}: {rec['title']}")
    print(f"Suggestion: {rec['suggestion']}")
```

---

## 📁 Data Storage

### Location
```
~/.claude/memory/performance/
```

### Files
```
operations_2026-02-15.json
operations_2026-02-14.json
operations_2026-02-13.json
...
```

### View Today's Data
```bash
cat ~/.claude/memory/performance/operations_$(date +%Y-%m-%d).json
```

### Check Storage Size
```bash
du -sh ~/.claude/memory/performance/
```

### Clean Old Files (Manual)
```bash
# Keep last 7 days, delete older
find ~/.claude/memory/performance/ -name "operations_*.json" -mtime +7 -delete
```

---

## 🎯 Common Use Cases

### 1. Find Slow Operations
**Dashboard**: Scroll to "Slow Operations" table
**API**: `GET /api/performance/slow-operations?threshold=2000&limit=20`

### 2. Get Optimization Suggestions
**Dashboard**: Check "AI Recommendations" section
**API**: `GET /api/performance/recommendations`

### 3. Monitor Trends
**Dashboard**: View "Response Time Trends" chart
**API**: `GET /api/performance/trends?days=7`

### 4. Check Tool Distribution
**Dashboard**: View "Operations by Tool" chart
**API**: `GET /api/performance/stats` (check `tools_breakdown`)

### 5. Identify Caching Opportunities
**Dashboard**: Look for "Files Read Multiple Times" recommendation
**Code**: Check `profiler.get_slow_operations()` for repeated targets

---

## 🔧 Troubleshooting

### Dashboard Not Loading
**Check**: Is the server running?
```bash
python run.py
```

**Check**: Browser console for errors (F12)

### No Data Showing
**Cause**: No operations tracked yet
**Solution**: Run test script or use the system normally
```bash
python test_performance.py
```

### Charts Not Rendering
**Cause**: Chart.js not loaded
**Solution**: Check internet connection (Chart.js is from CDN)

**Alternative**: Check browser console (F12) for errors

### Recommendations Not Appearing
**Cause**: No slow operations or everything is optimized
**Solution**: This is actually good! System is performing well.

### High Memory Usage
**Cause**: Too many operations tracked
**Solution**: Ring buffers auto-limit to 1000 operations. Should be <5MB.

**Check**:
```python
profiler = PerformanceProfiler()
print(f"Recent ops: {len(profiler.recent_operations)}")
print(f"Slow ops: {len(profiler.slow_operations)}")
```

---

## 📊 Performance Thresholds

### Operation Speed
- **Fast**: <500ms ✓
- **Normal**: 500-2000ms ✓
- **Slow**: 2000-5000ms ⚠️
- **Critical**: >5000ms 🔴

### Optimization Rate
- **Excellent**: >80% ✓
- **Good**: 60-80% ✓
- **Fair**: 40-60% ⚠️
- **Poor**: <40% 🔴

### Slow Operations Count
- **Excellent**: 0-5 ✓
- **Good**: 5-20 ✓
- **Fair**: 20-50 ⚠️
- **Poor**: >50 🔴

---

## 🎨 Customization

### Change Time Range
Buttons at top-right of dashboard:
- **24h**: Last 24 hours (default)
- **7d**: Last 7 days
- **30d**: Last 30 days

### Change Thresholds (Code)
```python
# In performance_profiler.py
self.SLOW_THRESHOLD = 3000  # 3 seconds instead of 2
self.CRITICAL_THRESHOLD = 10000  # 10 seconds instead of 5
```

### Change Auto-Refresh Interval
```javascript
// In performance-profiling.html
setInterval(() => {
    loadStats();
    loadRecommendations();
    loadSlowOperations();
}, 60000);  // 60 seconds instead of 30
```

---

## 📚 Further Reading

- **Full Documentation**: `PERFORMANCE_PROFILING_README.md`
- **Implementation Details**: `IMPLEMENTATION_SUMMARY.md`
- **Architecture Diagram**: `ARCHITECTURE_DIAGRAM.md`
- **API Docs**: http://localhost:5000/api/docs (when server running)

---

## 🆘 Support

### Check Logs
```bash
# Flask console output
python run.py

# Browser console
F12 → Console tab
```

### Test Services
```bash
python test_performance.py
```

### Verify Installation
```bash
# Check Python version (3.13+)
python --version

# Check Flask installed
python -c "import flask; print(flask.__version__)"

# Check file exists
ls src/services/monitoring/performance_profiler.py
ls templates/performance-profiling.html
```

---

## ✅ Quick Checklist

- [ ] Server running (`python run.py`)
- [ ] Logged in (admin/admin)
- [ ] Dashboard loads (http://localhost:5000/performance-profiling)
- [ ] KPI cards showing data
- [ ] Charts rendering
- [ ] Recommendations appearing (if any)
- [ ] Table populating
- [ ] Auto-refresh working (30s)

---

**Ready to optimize your performance!** 🚀

**Created**: 2026-02-15
**Version**: 1.0.0
