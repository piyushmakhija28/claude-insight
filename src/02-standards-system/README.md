# 🟢 RULES/STANDARDS SYSTEM (Middle Layer)

**PURPOSE:** Load coding standards BEFORE code generation to ensure 100% consistency

---

## 📊 What This System Does

**Loads 12 Standard Categories:**

1. ✅ Java Project Structure (packages, visibility)
2. ✅ Config Server Rules (what goes where)
3. ✅ Secret Management (never hardcode)
4. ✅ Response Format (ApiResponseDto<T>)
5. ✅ API Design Standards (REST patterns)
6. ✅ Database Standards (naming, audit fields)
7. ✅ Error Handling (global handler, exceptions)
8. ✅ Service Layer Pattern (Helper, package-private)
9. ✅ Entity Pattern (audit fields, lifecycle)
10. ✅ Controller Pattern (validation, responses)
11. ✅ Constants Organization (no magic strings)
12. ✅ Common Utilities (reusable code)

**OUTPUT:** 100+ Rules loaded and ready to enforce

---

## 📁 Files in This Folder

### **Policy:**
- `coding-standards-enforcement-policy.md` - Complete standards policy

### **Scripts:**
- `standards-loader.py` - Load all coding standards

---

## 🎯 Usage

```bash
# Load all standards
python standards-loader.py --load-all

# Load with summary
python standards-loader.py --load-all --summary

# Load and cache
python standards-loader.py --load-all --cache
```

**Output:**
```
🔧 CODING STANDARDS LOADER
======================================================================

📋 Loading standards from documentation...

  [1/12] Java Project Structure... ✅
  [2/12] Config Server Rules... ✅
  ...
  [12/12] Common Utilities... ✅

======================================================================
✅ ALL STANDARDS LOADED SUCCESSFULLY
======================================================================

📊 Summary:
   Total Standards: 12
   Rules Loaded: 87
   Ready for Execution: YES
```

---

## 🔗 Dependencies

**Depends on:**
- Sync System (must run after)

**Used by:**
- Execution System (provides standards)

---

## ⚙️ Integration

**Position in Flow:**
```
🔵 SYNC SYSTEM (Context + Session)
        ↓
🟢 RULES/STANDARDS SYSTEM (THIS) - Load standards
        ↓
🔴 EXECUTION SYSTEM (Follow standards)
```

---

## ✅ Benefits

| Benefit | Description |
|---------|-------------|
| **100% Consistency** | All services follow same patterns |
| **Zero Violations** | Standards enforced before code generation |
| **No Re-work** | Code generated correctly first time |
| **Easy Maintenance** | Consistent code = easy to maintain |

---

## 📋 Loaded Standards Include

### **Java Structure:**
- Package structure (controller, dto, form, services, entity, etc.)
- Visibility rules (public vs package-private)
- Service implementation extends Helper
- All responses use ApiResponseDto<T>

### **Config Management:**
- Microservice application.yml has ONLY name + config import
- ALL other configs in Config Server
- Secrets in Secret Manager using ${SECRET:key-name}

### **Code Patterns:**
- Package-private service implementations
- Helper classes for reusable logic
- Constants for all messages (no hardcoding)
- @Transactional on write operations
- Audit fields mandatory (created_at, updated_at, etc.)

---

**STATUS:** 🟢 ACTIVE
**PRIORITY:** 🔴 CRITICAL (Must run before execution)
