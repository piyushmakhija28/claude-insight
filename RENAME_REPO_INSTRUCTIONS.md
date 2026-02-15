# Git Repository Rename Instructions

## Current Setup
- **Repository**: https://github.com/piyushmakhija28/claude-monitoring-system
- **Local Path**: `C:\Users\techd\Documents\workspace-spring-tool-suite-4-4.27.0-new\claude-monitoring-system`

---

## 📝 Steps to Rename Repository

### Method 1: Rename on GitHub (Recommended) ✅

#### Step 1: GitHub पर rename करो

1. **Open GitHub repository**:
   ```
   https://github.com/piyushmakhija28/claude-monitoring-system
   ```

2. **Settings tab** पर जाओ (top-right में)

3. **General section** में scroll करके **Repository name** box ढूंढो

4. **New name enter करो**:
   - Suggested: `claude-insight`
   - या कोई भी नाम जो तुम चाहो

5. **"Rename" button** क्लिक करो

6. GitHub automatically redirect करेगा और old URLs काम करते रहेंगे (temporarily)

#### Step 2: Local git remote update करो

**Option A: Script use करो (Easy)**
```bash
cd C:\Users\techd\Documents\workspace-spring-tool-suite-4-4.27.0-new\claude-monitoring-system
bash update-git-remote.sh
```

**Option B: Manual command (यदि नाम `claude-insight` है)**
```bash
cd C:\Users\techd\Documents\workspace-spring-tool-suite-4-4.27.0-new\claude-monitoring-system
git remote set-url origin https://github.com/piyushmakhija28/claude-insight.git
```

**Option C: Manual command (custom name के लिए)**
```bash
cd C:\Users\techd\Documents\workspace-spring-tool-suite-4-4.27.0-new\claude-monitoring-system
git remote set-url origin https://github.com/piyushmakhija28/YOUR-NEW-REPO-NAME.git
```

#### Step 3: Verify करो

```bash
git remote -v
```

**Expected output:**
```
origin  https://github.com/piyushmakhija28/claude-insight.git (fetch)
origin  https://github.com/piyushmakhija28/claude-insight.git (push)
```

#### Step 4: Test करो

```bash
git pull
git push
```

Done! ✅

---

### Method 2: Create New Repository & Push

अगर तुम completely new repository चाहते हो:

#### Step 1: GitHub पर new repository बनाओ

1. GitHub पर जाओ: https://github.com/new
2. **Repository name**: `claude-insight` (या कोई भी नाम)
3. **Description**: "Claude Insight - Performance Analytics Dashboard for Claude Memory System"
4. **Private/Public**: चुन लो
5. **Create repository** क्लिक करो

#### Step 2: Local में remote change करो

```bash
cd C:\Users\techd\Documents\workspace-spring-tool-suite-4-4.27.0-new\claude-monitoring-system

# Old remote हटाओ
git remote remove origin

# New remote add करो
git remote add origin https://github.com/piyushmakhija28/claude-insight.git

# Push करो
git push -u origin main
```

#### Step 3: Old repository delete करो (optional)

GitHub पर जाकर old repository (`claude-monitoring-system`) को delete कर सकते हो:
1. Settings → Danger Zone → Delete this repository

---

## 🗂️ Directory Rename (Local)

अगर local directory का नाम भी बदलना है:

### Option 1: Windows Explorer से

1. Git bash/terminal बंद करो
2. Windows Explorer open करो
3. Directory पर right-click → Rename
4. `claude-monitoring-system` → `claude-insight`
5. Done!

### Option 2: Command से

```bash
cd C:\Users\techd\Documents\workspace-spring-tool-suite-4-4.27.0-new

# Directory rename करो
mv claude-monitoring-system claude-insight

# New directory में जाओ
cd claude-insight

# Verify git still works
git status
```

---

## ✅ Complete Checklist

- [ ] GitHub पर repository rename किया
- [ ] Local git remote updated
- [ ] `git remote -v` से verify किया
- [ ] `git pull` test किया
- [ ] `git push` test किया
- [ ] Local directory rename किया (optional)
- [ ] Old remote URL redirects working (GitHub automatically handles)

---

## 🔧 Quick Commands Reference

### Check current remote
```bash
git remote -v
```

### Update remote URL
```bash
git remote set-url origin https://github.com/piyushmakhija28/NEW-NAME.git
```

### Verify remote change
```bash
git config --get remote.origin.url
```

### Test connection
```bash
git remote show origin
```

---

## 🚨 Troubleshooting

### Problem: "Repository not found" error after push/pull

**Solution**: Remote URL probably not updated
```bash
# Check current URL
git remote -v

# Update to correct URL
git remote set-url origin https://github.com/piyushmakhija28/claude-insight.git
```

### Problem: Old URLs still showing

**Solution**: Clear git cache
```bash
git remote remove origin
git remote add origin https://github.com/piyushmakhija28/claude-insight.git
```

### Problem: Can't rename on GitHub (Settings tab missing)

**Solution**: Check if you have admin access to repository

---

## 📊 Recommended Names

Based on the project content, here are suggested names:

1. **claude-insight** ✅ (Best - matches dashboard name)
2. **claude-performance-monitor**
3. **claude-analytics-dashboard**
4. **claude-memory-insights**
5. **claude-profiling-dashboard**

---

## 💡 Note

GitHub automatically redirects old repository URLs to new ones for some time, but it's best to update local remotes immediately.

**Old URL** (will redirect):
```
https://github.com/piyushmakhija28/claude-monitoring-system.git
```

**New URL** (direct):
```
https://github.com/piyushmakhija28/claude-insight.git
```

---

**Created**: 2026-02-15
**Status**: Ready to execute
