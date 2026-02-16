# GitHub CLI Enforcement Policy

**VERSION:** 1.0.0
**STATUS:** ✅ ACTIVE
**CREATED:** 2026-02-15

---

## 🎯 POLICY OBJECTIVE

**MANDATORY: Use GitHub CLI (`gh`) for ALL GitHub-related operations instead of manual GitHub UI or API calls.**

---

## 🚨 CRITICAL RULES

### Rule 1: Authentication Check (ALWAYS FIRST)

**Before ANY GitHub operation:**
```bash
gh auth status || gh auth login
```

**Why:**
- Prevents auth errors mid-operation
- Uses secure token management
- No manual PAT token handling

---

### Rule 2: Use `gh` for Repository Operations

| Operation | ❌ WRONG | ✅ CORRECT |
|-----------|----------|------------|
| Create repo | Manual GitHub UI | `gh repo create name --private` |
| Clone repo | `git clone https://...` | `gh repo clone owner/repo` |
| View repo | Open browser | `gh repo view owner/repo` |
| Fork repo | Click "Fork" button | `gh repo fork owner/repo` |
| Delete repo | Settings → Delete | `gh repo delete owner/repo` |
| Archive repo | Settings → Archive | `gh repo archive owner/repo` |
| Check private | Open repo settings | `gh repo view --json isPrivate` |

**Examples:**
```bash
# ✅ Create private repo
gh repo create my-project \
  --private \
  --description "My awesome project" \
  --clone

# ✅ Clone repo
gh repo clone owner/my-project

# ✅ View repo info
gh repo view owner/my-project

# ✅ Check if private
gh repo view owner/my-project --json isPrivate --jq .isPrivate
```

---

### Rule 3: Use `gh` for Pull Request Operations

| Operation | ❌ WRONG | ✅ CORRECT |
|-----------|----------|------------|
| Create PR | Manual GitHub UI | `gh pr create --title "..." --body "..."` |
| View PR | Open in browser | `gh pr view 123` |
| List PRs | GitHub UI | `gh pr list --state open` |
| Merge PR | Click "Merge" | `gh pr merge 123 --squash` |
| Close PR | Click "Close" | `gh pr close 123` |
| Review PR | GitHub UI | `gh pr review 123 --approve` |

**PR Creation Template:**
```bash
gh pr create \
  --title "TYPE: Brief description" \
  --body "$(cat <<'EOF'
## Summary
- Change 1
- Change 2
- Change 3

## Type
- [x] Feature
- [ ] Bug Fix
- [ ] Refactor
- [ ] Documentation

## Test Plan
- [x] Unit tests passed
- [x] Integration tests passed
- [x] Manual testing completed

## Related Issues
Closes #123

🤖 Created with Claude Code
EOF
)" \
  --base main \
  --head feature-branch \
  --label "enhancement" \
  --assignee @me
```

**PR Merge Options:**
```bash
# Squash merge (PREFERRED for feature branches)
gh pr merge 123 --squash --delete-branch

# Merge commit (for releases)
gh pr merge 123 --merge

# Rebase (for clean history)
gh pr merge 123 --rebase --delete-branch
```

---

### Rule 4: Use `gh` for Issue Operations

| Operation | ❌ WRONG | ✅ CORRECT |
|-----------|----------|------------|
| Create issue | Manual UI | `gh issue create --title "..." --body "..."` |
| View issue | Open browser | `gh issue view 456` |
| List issues | GitHub UI | `gh issue list --state open` |
| Close issue | Click "Close" | `gh issue close 456` |
| Assign issue | UI dropdown | `gh issue create --assignee @me` |

**Issue Creation Template:**
```bash
gh issue create \
  --title "BUG: Brief description" \
  --body "$(cat <<'EOF'
## Bug Description
[Clear, concise description of the bug]

## Steps to Reproduce
1. Step 1
2. Step 2
3. Step 3

## Expected Behavior
[What should happen]

## Actual Behavior
[What actually happens]

## Environment
- OS: Windows 11
- Version: v1.2.3
- Browser: Chrome 120

## Screenshots
[If applicable]

🤖 Created with Claude Code
EOF
)" \
  --label "bug" \
  --assignee @me \
  --milestone "v1.2.0"
```

---

### Rule 5: Use `gh` for Release Operations

| Operation | ❌ WRONG | ✅ CORRECT |
|-----------|----------|------------|
| Create release | Manual UI | `gh release create v1.0.0` |
| View releases | GitHub UI | `gh release list` |
| Download asset | Browser download | `gh release download v1.0.0` |
| Delete release | Settings → Delete | `gh release delete v1.0.0` |

**Release Creation Template:**
```bash
gh release create v1.0.0 \
  --title "Release v1.0.0 - Feature Name" \
  --notes "$(cat <<'EOF'
## What's New
- Feature 1
- Feature 2
- Bug fix 3

## Breaking Changes
- Change 1

## Contributors
- @user1
- @user2

## Full Changelog
https://github.com/owner/repo/compare/v0.9.0...v1.0.0
EOF
)" \
  --target main \
  dist/app.jar \
  dist/app.zip
```

---

### Rule 6: Use `gh` for Workflow Operations

| Operation | ❌ WRONG | ✅ CORRECT |
|-----------|----------|------------|
| List workflows | GitHub Actions UI | `gh workflow list` |
| Run workflow | Click "Run workflow" | `gh workflow run ci.yml` |
| View runs | Actions tab | `gh run list --workflow=ci.yml` |
| View logs | Click run → logs | `gh run view 123456 --log` |
| Cancel run | Click "Cancel" | `gh run cancel 123456` |

**Examples:**
```bash
# ✅ List all workflows
gh workflow list

# ✅ Run workflow
gh workflow run ci.yml \
  --ref feature-branch \
  --field environment=production

# ✅ View workflow runs
gh run list --workflow=ci.yml --limit 10

# ✅ View specific run logs
gh run view 123456 --log

# ✅ Watch run in real-time
gh run watch 123456

# ✅ Cancel running workflow
gh run cancel 123456
```

---

### Rule 7: Use `gh` for API Calls

| Operation | ❌ WRONG | ✅ CORRECT |
|-----------|----------|------------|
| Call API | `curl -H "Authorization: token"` | `gh api repos/owner/repo` |
| GraphQL | Manual GraphQL client | `gh api graphql -f query='...'` |

**Examples:**
```bash
# ✅ REST API call
gh api repos/owner/repo/pulls

# ✅ GraphQL query
gh api graphql -f query='
  query {
    repository(owner: "owner", name: "repo") {
      issues(first: 10) {
        nodes {
          title
          number
        }
      }
    }
  }
'

# ✅ POST request
gh api repos/owner/repo/issues \
  --method POST \
  --field title="Issue title" \
  --field body="Issue body"
```

---

## 🔄 AUTOMATION WORKFLOWS

### Workflow 1: Create Repo → Commit → PR → Merge

```bash
#!/bin/bash
# Complete GitHub workflow automation

# 1. Create repo
gh repo create my-project \
  --private \
  --description "Project description" \
  --clone

cd my-project

# 2. Make changes
echo "# My Project" > README.md
git add .
git commit -m "Initial commit"
git push origin main

# 3. Create feature branch
git checkout -b feature-auth
# ... make changes ...
git add .
git commit -m "Feature: Add authentication"
git push origin feature-auth

# 4. Create PR
gh pr create \
  --title "Feature: Add authentication" \
  --body "Added JWT authentication" \
  --base main \
  --head feature-auth

# 5. Check PR status
gh pr view

# 6. Merge PR
gh pr merge --squash --delete-branch

# 7. Create release
git checkout main
git pull
gh release create v1.0.0 \
  --title "Release v1.0.0" \
  --notes "Initial release"
```

---

### Workflow 2: Multi-Repo Operations

```bash
#!/bin/bash
# Batch operations across multiple repos

REPOS=("repo1" "repo2" "repo3")

# List all PRs across repos
for repo in "${REPOS[@]}"; do
  echo "=== $repo ==="
  gh pr list --repo owner/$repo --state open
done

# Create issue in all repos
for repo in "${REPOS[@]}"; do
  gh issue create \
    --repo owner/$repo \
    --title "Update dependencies" \
    --body "Please update all npm dependencies"
done

# Clone all repos
for repo in "${REPOS[@]}"; do
  gh repo clone owner/$repo
done
```

---

### Workflow 3: CI/CD Integration

```bash
#!/bin/bash
# Trigger CI/CD pipeline after deployment

# 1. Commit and push
git add .
git commit -m "Deploy: Production release"
git push origin main

# 2. Create release
gh release create v1.0.0 \
  --title "Production Release v1.0.0" \
  --notes "Production deployment"

# 3. Trigger deployment workflow
gh workflow run deploy.yml \
  --ref main \
  --field environment=production \
  --field version=v1.0.0

# 4. Watch deployment
gh run watch --workflow=deploy.yml
```

---

## 🛡️ ERROR HANDLING

### Always Check Command Success

```bash
# ✅ GOOD: Check if PR exists before operations
if gh pr view 123 > /dev/null 2>&1; then
  echo "PR exists, proceeding with merge"
  gh pr merge 123 --squash
else
  echo "ERROR: PR #123 not found"
  exit 1
fi

# ✅ GOOD: Use --json for programmatic checks
PR_STATE=$(gh pr view 123 --json state --jq .state)
if [ "$PR_STATE" = "OPEN" ]; then
  gh pr merge 123 --squash
else
  echo "PR is not open, cannot merge"
fi

# ✅ GOOD: Check auth before operations
if ! gh auth status > /dev/null 2>&1; then
  echo "ERROR: Not authenticated, run 'gh auth login'"
  exit 1
fi
```

---

## 📊 BENEFITS OF USING `gh` CLI

### 1. **Security**
- ✅ No manual token management
- ✅ Secure credential storage
- ✅ Token auto-refresh
- ✅ No hardcoded PATs in scripts

### 2. **Automation**
- ✅ Easy scripting
- ✅ CI/CD integration
- ✅ Batch operations
- ✅ Reproducible workflows

### 3. **Efficiency**
- ✅ Faster than UI navigation
- ✅ No context switching
- ✅ Terminal-based workflow
- ✅ Keyboard-driven

### 4. **Reliability**
- ✅ Better error messages
- ✅ Built-in retries
- ✅ Pagination handling
- ✅ Offline caching

### 5. **Consistency**
- ✅ Same commands across platforms
- ✅ Versioned CLI
- ✅ Standard conventions
- ✅ Well-documented

---

## 🔧 INTEGRATION WITH OTHER POLICIES

### Integration with Git Auto-Commit Policy

**Auto-commit daemon MUST use `gh` for PR creation:**

```python
# In commit-daemon.py
def auto_create_pr():
    # After auto-commits
    if should_create_pr():
        subprocess.run([
            "gh", "pr", "create",
            "--title", generate_pr_title(),
            "--body", generate_pr_body(),
            "--base", "main",
            "--head", get_current_branch()
        ])
```

### Integration with Failure Prevention Policy

**Pre-execution checker MUST suggest `gh` over manual operations:**

```python
# In pre-execution-checker.py
def check_github_operation(command):
    if "github.com" in command and "gh" not in command:
        return {
            "warning": "Use 'gh' CLI instead of manual GitHub operations",
            "suggestion": convert_to_gh_command(command)
        }
```

---

## 📝 LOGGING

**Log all GitHub operations:**

```bash
# Log GitHub CLI usage
echo "[$(date '+%Y-%m-%d %H:%M:%S')] GH_CLI | ${GH_COMMAND} | SUCCESS" \
  >> ~/.claude/memory/logs/github-cli.log

# Example log entries:
# [2026-02-15 10:30:00] GH_CLI | gh repo create my-project | SUCCESS
# [2026-02-15 10:31:15] GH_CLI | gh pr create #123 | SUCCESS
# [2026-02-15 10:32:00] GH_CLI | gh pr merge 123 --squash | SUCCESS
```

---

## 📊 METRICS

**Track GitHub CLI usage:**

```bash
# Count operations by type
cat ~/.claude/memory/logs/github-cli.log | \
  awk '{print $4}' | sort | uniq -c

# Example output:
#   45 gh_repo_create
#   120 gh_pr_create
#   95 gh_pr_merge
#   30 gh_issue_create
#   15 gh_release_create
```

---

## 🚀 QUICK REFERENCE

### Most Common Operations

```bash
# Repo operations
gh repo create name --private --clone
gh repo clone owner/repo
gh repo view owner/repo

# PR operations
gh pr create --title "..." --body "..."
gh pr view 123
gh pr list --state open
gh pr merge 123 --squash --delete-branch

# Issue operations
gh issue create --title "..." --body "..."
gh issue view 456
gh issue list --state open
gh issue close 456

# Release operations
gh release create v1.0.0 --notes "..."
gh release list
gh release download v1.0.0

# Workflow operations
gh workflow run ci.yml
gh run list --workflow=ci.yml
gh run view 123456 --log
```

---

**VERSION:** 1.0.0
**STATUS:** ✅ ACTIVE
**POLICY OWNER:** Claude Memory System
**LAST REVIEWED:** 2026-02-15
