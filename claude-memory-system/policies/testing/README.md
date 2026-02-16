# 🧪 Testing

**Purpose:** Test scripts and testing policies for the memory system

---

## 📋 What This Contains

Test scripts to validate:
- System functionality
- Policy enforcement
- Skill detection
- Phase execution
- Infrastructure health

---

## 📁 Files in This Folder

### **Policy:**
- `test-case-policy.md` - Testing policy and standards

### **Phase Testing:**
- `test-all-phases.py` - Test all execution phases
- `test-phase2-infrastructure.py` - Test Phase 2 infrastructure

### **Skill Testing:**
- `test-all-skills.py` - Test all skill detection and execution

---

## 🎯 Usage

### **Test All Phases:**
```bash
python test-all-phases.py
```

**Tests:**
1. ✅ Phase 0: Prompt Generation
2. ✅ Phase 1: Task Breakdown
3. ✅ Phase 2: Plan Mode Suggestion
4. ✅ Phase 3: Context Check
5. ✅ Phase 4: Model Selection
6. ✅ Phase 5: Skill/Agent Selection
7. ✅ Phase 6: Tool Optimization
8. ✅ Phase 7: Recommendations
9. ✅ Phase 8: Progress Tracking
10. ✅ Phase 9: Git Auto-Commit
11. ✅ Phase 10: Session Save

### **Test All Skills:**
```bash
python test-all-skills.py
```

**Tests:**
- ✅ Context management skill
- ✅ Model selection skill
- ✅ Java Spring Boot skill
- ✅ Docker skill
- ✅ Kubernetes skill
- ✅ Jenkins skill
- ✅ RDBMS skill
- ✅ NoSQL skill
- ✅ All other skills

### **Test Infrastructure:**
```bash
python test-phase2-infrastructure.py
```

**Tests:**
- ✅ All 9 daemons running
- ✅ Log files exist and writable
- ✅ Session directory accessible
- ✅ Context cache working
- ✅ Recommendations generated
- ✅ PID files exist

---

## 📊 Test Results

**All tests output:**
- ✅ PASS - Test passed
- ❌ FAIL - Test failed with reason
- ⚠️ WARN - Test passed with warnings
- ⏭️ SKIP - Test skipped (dependency not met)

**Example Output:**
```
🧪 Testing Memory System
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Phase 0: Prompt Generation
  ✅ prompt-generator.py exists
  ✅ Anti-hallucination policy exists
  ✅ Prompt generation works
  Time: 0.5s

Phase 1: Task Breakdown
  ✅ task-phase-enforcer.py exists
  ✅ Task breakdown works
  ✅ Complexity calculation correct
  Time: 0.8s

...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Summary: 45/45 tests passed (100%)
Total Time: 12.3s
Status: 🟢 ALL TESTS PASSED
```

---

## 🔧 Adding New Tests

**Create new test file:**
```python
#!/usr/bin/env python3
"""Test description"""

import sys
import os
sys.path.append(os.path.expanduser("~/.claude/memory"))

def test_feature():
    """Test specific feature"""
    try:
        # Test code here
        return True, "Feature works"
    except Exception as e:
        return False, f"Feature failed: {e}"

if __name__ == "__main__":
    success, message = test_feature()
    print(f"{'✅' if success else '❌'} {message}")
    sys.exit(0 if success else 1)
```

**Add to test suite:**
1. Place in `testing/` folder
2. Add to `test-all-phases.py` or `test-all-skills.py`
3. Run test suite to verify

---

## 📝 Test Policy

**All changes must:**
1. ✅ Pass existing tests
2. ✅ Add tests for new features
3. ✅ Maintain >95% test coverage
4. ✅ Run tests before committing

**See `test-case-policy.md` for complete testing policy.**

---

## ✅ Benefits

- **Quality:** Catch bugs before production
- **Confidence:** Know system works correctly
- **Regression:** Prevent breaking existing features
- **Documentation:** Tests serve as examples

---

**Location:** `~/.claude/memory/testing/`
