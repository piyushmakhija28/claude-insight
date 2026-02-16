# GitHub CLI Usage Documentation

**VERSION:** 1.0.0
**STATUS:** ✅ ACTIVE
**CREATED:** 2026-02-15

---

## 📋 TABLE OF CONTENTS

1. [Installation & Setup](#installation--setup)
2. [Authentication](#authentication)
3. [Repository Operations](#repository-operations)
4. [Pull Request Operations](#pull-request-operations)
5. [Issue Operations](#issue-operations)
6. [Release Operations](#release-operations)
7. [Workflow Operations](#workflow-operations)
8. [Advanced Usage](#advanced-usage)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)

---

## 🚀 INSTALLATION & SETUP

### Install GitHub CLI

**Windows (Already installed in your system):**
```bash
# Verify installation
gh --version

# Expected output: gh version 2.x.x
```

**Alternative install methods:**
```bash
# Windows (Scoop)
scoop install gh

# Windows (Chocolatey)
choco install gh

# Windows (WinGet)
winget install --id GitHub.cli
```

### First-Time Setup

```bash
# 1. Check if already authenticated
gh auth status

# 2. If not authenticated, login
gh auth login

# Follow prompts:
# - What account do you want to log into? → GitHub.com
# - What is your preferred protocol for Git operations? → HTTPS
# - Authenticate GitHub CLI with your GitHub credentials? → Yes
# - How would you like to authenticate? → Login with a web browser

# 3. Verify authentication
gh auth status

# Expected output:
# ✓ Logged in to github.com as YOUR_USERNAME
# ✓ Git operations for github.com configured to use https protocol.
# ✓ Token: *******************
```

---

## 🔐 AUTHENTICATION

### Check Authentication Status

```bash
# Basic check
gh auth status

# Detailed check
gh auth status --show-token

# Check specific host
gh auth status --hostname github.com
```

### Login/Logout

```bash
# Login
gh auth login

# Login with token
gh auth login --with-token < token.txt

# Logout
gh auth logout

# Logout from specific host
gh auth logout --hostname github.com
```

### Refresh Token

```bash
# Refresh authentication token
gh auth refresh

# Refresh with specific scopes
gh auth refresh --scopes repo,workflow,admin:org
```

---

## 📦 REPOSITORY OPERATIONS

### Create Repository

```bash
# Create private repo
gh repo create my-project --private

# Create public repo
gh repo create my-project --public

# Create with description
gh repo create my-project \
  --private \
  --description "My awesome project"

# Create and clone immediately
gh repo create my-project \
  --private \
  --clone

# Create from template
gh repo create my-project \
  --template owner/template-repo \
  --private

# Create with .gitignore and license
gh repo create my-project \
  --private \
  --gitignore Node \
  --license MIT

# Create in organization
gh repo create org/my-project --private
```

### Clone Repository

```bash
# Clone your repo
gh repo clone my-project

# Clone someone else's repo
gh repo clone owner/repo

# Clone to specific directory
gh repo clone owner/repo ./custom-dir

# Clone and immediately cd into it
gh repo clone owner/repo && cd repo
```

### View Repository

```bash
# View repo details
gh repo view

# View specific repo
gh repo view owner/repo

# View in browser
gh repo view --web

# View as JSON
gh repo view --json name,description,isPrivate,defaultBranchRef

# Extract specific field
gh repo view --json isPrivate --jq .isPrivate
```

### List Repositories

```bash
# List your repos
gh repo list

# List with limit
gh repo list --limit 50

# List organization repos
gh repo list org

# List by language
gh repo list --language javascript

# List as JSON
gh repo list --json name,description,isPrivate
```

### Fork Repository

```bash
# Fork repo
gh repo fork owner/repo

# Fork and clone
gh repo fork owner/repo --clone

# Fork to organization
gh repo fork owner/repo --org my-org
```

### Archive/Delete Repository

```bash
# Archive repo
gh repo archive owner/repo

# Delete repo
gh repo delete owner/repo --confirm
```

### Repository Settings

```bash
# Set default branch
gh repo edit --default-branch main

# Enable/disable features
gh repo edit --enable-issues
gh repo edit --enable-wiki
gh repo edit --enable-projects

# Set visibility
gh repo edit --visibility private
gh repo edit --visibility public

# Add topics
gh repo edit --add-topic javascript,nodejs,backend
```

---

## 🔀 PULL REQUEST OPERATIONS

### Create Pull Request

**Basic PR:**
```bash
# Create PR (interactive)
gh pr create

# Create with title and body
gh pr create \
  --title "Feature: Add authentication" \
  --body "Added JWT authentication with Redis session storage"

# Create with full options
gh pr create \
  --title "Feature: Add authentication" \
  --body "Description" \
  --base main \
  --head feature-auth \
  --label enhancement \
  --assignee @me \
  --reviewer user1,user2 \
  --milestone v1.0.0

# Create draft PR
gh pr create --draft \
  --title "WIP: Authentication" \
  --body "Work in progress"
```

**PR with Template:**
```bash
gh pr create \
  --title "TYPE: Brief description" \
  --body "$(cat <<'EOF'
## Summary
- Change 1: Description
- Change 2: Description
- Change 3: Description

## Type of Change
- [x] Feature
- [ ] Bug Fix
- [ ] Refactor
- [ ] Documentation
- [ ] Testing

## Test Plan
- [x] Unit tests added/updated
- [x] Integration tests passed
- [x] Manual testing completed
- [ ] E2E tests passed

## Related Issues
Closes #123
Fixes #456

## Breaking Changes
- None

## Screenshots/Videos
[If applicable]

## Checklist
- [x] Code follows project style guidelines
- [x] Self-review completed
- [x] Comments added for complex logic
- [x] Documentation updated
- [x] No new warnings generated

## Reviewers
@user1 @user2

🤖 Created with Claude Code
EOF
)" \
  --base main \
  --head feature-branch
```

### View Pull Request

```bash
# View PR details
gh pr view 123

# View in browser
gh pr view 123 --web

# View as JSON
gh pr view 123 --json title,state,author,createdAt

# View PR diff
gh pr diff 123

# View PR commits
gh pr view 123 --json commits

# View PR checks
gh pr checks 123
```

### List Pull Requests

```bash
# List PRs
gh pr list

# List open PRs
gh pr list --state open

# List by author
gh pr list --author username

# List assigned to you
gh pr list --assignee @me

# List by label
gh pr list --label bug

# List with limit
gh pr list --limit 20

# List as JSON
gh pr list --json number,title,state,author
```

### Review Pull Request

```bash
# Approve PR
gh pr review 123 --approve

# Request changes
gh pr review 123 --request-changes \
  --body "Please fix the authentication logic"

# Comment on PR
gh pr review 123 --comment \
  --body "LGTM! Great work!"

# Approve with comment
gh pr review 123 --approve \
  --body "Approved! Excellent implementation."
```

### Merge Pull Request

```bash
# Squash merge (PREFERRED)
gh pr merge 123 --squash

# Squash merge with delete branch
gh pr merge 123 --squash --delete-branch

# Merge commit
gh pr merge 123 --merge

# Rebase merge
gh pr merge 123 --rebase

# Auto-merge when checks pass
gh pr merge 123 --auto --squash
```

### Update Pull Request

```bash
# Edit PR title
gh pr edit 123 --title "New title"

# Edit PR body
gh pr edit 123 --body "Updated description"

# Add label
gh pr edit 123 --add-label bug

# Remove label
gh pr edit 123 --remove-label enhancement

# Add assignee
gh pr edit 123 --add-assignee user1

# Add reviewer
gh pr edit 123 --add-reviewer user2

# Change base branch
gh pr edit 123 --base develop
```

### Close/Reopen Pull Request

```bash
# Close PR
gh pr close 123

# Close with comment
gh pr close 123 --comment "Closing as duplicate of #124"

# Reopen PR
gh pr reopen 123
```

### Check Out Pull Request

```bash
# Checkout PR locally
gh pr checkout 123

# Checkout by branch name
gh pr checkout feature-auth

# Checkout and test
gh pr checkout 123 && npm test
```

---

## 🐛 ISSUE OPERATIONS

### Create Issue

**Basic Issue:**
```bash
# Create issue (interactive)
gh issue create

# Create with title and body
gh issue create \
  --title "Bug: Login fails with special characters" \
  --body "Description of the bug"

# Create with full options
gh issue create \
  --title "Bug: Login fails" \
  --body "Description" \
  --label bug \
  --assignee @me \
  --milestone v1.0.0
```

**Issue with Template:**
```bash
gh issue create \
  --title "BUG: Brief description" \
  --body "$(cat <<'EOF'
## Bug Description
[Clear, concise description of what the bug is]

## Steps to Reproduce
1. Go to login page
2. Enter username with special characters (!@#$%)
3. Click login
4. See error

## Expected Behavior
Should accept special characters and login successfully

## Actual Behavior
Shows error: "Invalid username format"

## Environment
- OS: Windows 11
- Browser: Chrome 120.0.6099.130
- Version: v1.2.3

## Screenshots
[Attach screenshots if available]

## Additional Context
This started happening after the v1.2.0 update

## Possible Solution
May need to update regex validation in auth service

🤖 Created with Claude Code
EOF
)" \
  --label "bug" \
  --assignee @me
```

### View Issue

```bash
# View issue details
gh issue view 456

# View in browser
gh issue view 456 --web

# View as JSON
gh issue view 456 --json title,state,author,createdAt

# View issue comments
gh issue view 456 --json comments
```

### List Issues

```bash
# List issues
gh issue list

# List open issues
gh issue list --state open

# List closed issues
gh issue list --state closed

# List by author
gh issue list --author username

# List assigned to you
gh issue list --assignee @me

# List by label
gh issue list --label bug

# List with limit
gh issue list --limit 50

# List as JSON
gh issue list --json number,title,state,author
```

### Update Issue

```bash
# Edit issue title
gh issue edit 456 --title "New title"

# Edit issue body
gh issue edit 456 --body "Updated description"

# Add label
gh issue edit 456 --add-label bug

# Remove label
gh issue edit 456 --remove-label enhancement

# Add assignee
gh issue edit 456 --add-assignee user1
```

### Close/Reopen Issue

```bash
# Close issue
gh issue close 456

# Close with comment
gh issue close 456 --comment "Fixed in PR #123"

# Reopen issue
gh issue reopen 456
```

### Comment on Issue

```bash
# Add comment
gh issue comment 456 --body "Working on this"

# Add comment from file
gh issue comment 456 --body-file comment.md
```

---

## 🏷️ RELEASE OPERATIONS

### Create Release

**Basic Release:**
```bash
# Create release
gh release create v1.0.0

# Create with title and notes
gh release create v1.0.0 \
  --title "Release v1.0.0 - Authentication" \
  --notes "Added authentication feature"

# Create with assets
gh release create v1.0.0 \
  dist/app.jar \
  dist/app.zip
```

**Release with Template:**
```bash
gh release create v1.0.0 \
  --title "Release v1.0.0 - Authentication & User Management" \
  --notes "$(cat <<'EOF'
## 🎉 What's New

### Features
- ✅ JWT Authentication with Redis session storage
- ✅ User registration with email verification
- ✅ Password reset functionality
- ✅ Role-based access control (RBAC)

### Improvements
- ⚡ Improved login performance (2x faster)
- 🔒 Enhanced security with bcrypt password hashing
- 📝 Better error messages for auth failures

### Bug Fixes
- 🐛 Fixed session timeout issue (#123)
- 🐛 Fixed special characters in username (#456)
- 🐛 Fixed memory leak in token refresh (#789)

## ⚠️ Breaking Changes
- Changed API endpoint from `/auth/login` to `/api/v1/auth/login`
- Removed deprecated `password_hash` field from User model

## 📦 Assets
- `app.jar` - Executable JAR (Java 17+)
- `app.zip` - Source code archive
- `app-docs.pdf` - Documentation

## 📊 Statistics
- **Commits**: 45
- **Files Changed**: 120
- **Lines Added**: 3,500
- **Lines Removed**: 1,200

## 👥 Contributors
- @user1 (Lead Developer)
- @user2 (Testing)
- @user3 (Documentation)

## 🔗 Links
- [Full Changelog](https://github.com/owner/repo/compare/v0.9.0...v1.0.0)
- [Documentation](https://docs.example.com/v1.0.0)
- [Migration Guide](https://docs.example.com/migration/v1.0.0)

## 📝 Installation
```bash
# Download JAR
gh release download v1.0.0 -p app.jar

# Run
java -jar app.jar
```

🤖 Created with Claude Code
EOF
)" \
  --target main \
  dist/app.jar \
  dist/app.zip \
  dist/app-docs.pdf
```

### View Release

```bash
# View latest release
gh release view

# View specific release
gh release view v1.0.0

# View in browser
gh release view v1.0.0 --web

# View as JSON
gh release view v1.0.0 --json tagName,name,body,assets
```

### List Releases

```bash
# List releases
gh release list

# List with limit
gh release list --limit 20

# List as JSON
gh release list --json tagName,name,publishedAt
```

### Download Release

```bash
# Download all assets
gh release download v1.0.0

# Download specific asset
gh release download v1.0.0 -p app.jar

# Download to specific directory
gh release download v1.0.0 -D ./downloads

# Download latest release
gh release download
```

### Update Release

```bash
# Edit release notes
gh release edit v1.0.0 --notes "Updated notes"

# Mark as draft
gh release edit v1.0.0 --draft

# Mark as pre-release
gh release edit v1.0.0 --prerelease
```

### Delete Release

```bash
# Delete release
gh release delete v1.0.0

# Delete with confirmation
gh release delete v1.0.0 --yes
```

---

## ⚙️ WORKFLOW OPERATIONS

### List Workflows

```bash
# List workflows
gh workflow list

# List as JSON
gh workflow list --json name,state,id
```

### Run Workflow

```bash
# Run workflow
gh workflow run ci.yml

# Run on specific branch
gh workflow run ci.yml --ref feature-branch

# Run with inputs
gh workflow run deploy.yml \
  --ref main \
  --field environment=production \
  --field version=v1.0.0

# Run with raw inputs
gh workflow run deploy.yml \
  --ref main \
  --raw-field config='{"env":"prod","replicas":3}'
```

### List Workflow Runs

```bash
# List all runs
gh run list

# List runs for specific workflow
gh run list --workflow=ci.yml

# List recent runs
gh run list --limit 20

# List by status
gh run list --status=failure

# List by branch
gh run list --branch=main

# List as JSON
gh run list --json databaseId,status,conclusion,createdAt
```

### View Workflow Run

```bash
# View run details
gh run view 123456

# View in browser
gh run view 123456 --web

# View logs
gh run view 123456 --log

# View specific job
gh run view 123456 --job=build

# View as JSON
gh run view 123456 --json status,conclusion,databaseId
```

### Watch Workflow Run

```bash
# Watch run in real-time
gh run watch 123456

# Watch and show logs
gh run watch 123456 --exit-status
```

### Download Workflow Artifacts

```bash
# Download all artifacts
gh run download 123456

# Download specific artifact
gh run download 123456 -n artifact-name

# Download to directory
gh run download 123456 -D ./artifacts
```

### Cancel/Rerun Workflow

```bash
# Cancel run
gh run cancel 123456

# Rerun run
gh run rerun 123456

# Rerun failed jobs
gh run rerun 123456 --failed
```

---

## 🚀 ADVANCED USAGE

### Using JSON Output

```bash
# Get PR state
PR_STATE=$(gh pr view 123 --json state --jq .state)
echo "PR state: $PR_STATE"

# Get all open PRs as array
gh pr list --state open --json number,title | jq -r '.[] | "\(.number): \(.title)"'

# Get repo details
gh repo view --json name,description,isPrivate,defaultBranchRef | jq .

# Complex jq query
gh issue list --json number,title,labels | \
  jq -r '.[] | select(.labels | any(.name == "bug")) | "\(.number): \(.title)"'
```

### Using GraphQL

```bash
# Basic GraphQL query
gh api graphql -f query='
  query {
    viewer {
      login
      name
    }
  }
'

# Get repo issues
gh api graphql -f query='
  query($owner: String!, $repo: String!) {
    repository(owner: $owner, name: $repo) {
      issues(first: 10, states: OPEN) {
        nodes {
          number
          title
          author {
            login
          }
        }
      }
    }
  }
' -f owner=OWNER -f repo=REPO
```

### Using REST API

```bash
# GET request
gh api repos/owner/repo

# POST request
gh api repos/owner/repo/issues \
  --method POST \
  --field title="Issue title" \
  --field body="Issue body"

# PUT request
gh api repos/owner/repo/contents/file.txt \
  --method PUT \
  --field message="Update file" \
  --field content="$(base64 file.txt)"

# DELETE request
gh api repos/owner/repo/issues/123/labels/bug \
  --method DELETE
```

### Aliases

```bash
# Create alias
gh alias set prc 'pr create --draft'

# Use alias
gh prc --title "WIP: Feature"

# List aliases
gh alias list

# Delete alias
gh alias delete prc
```

### Extensions

```bash
# List installed extensions
gh extension list

# Install extension
gh extension install owner/gh-extension

# Upgrade extension
gh extension upgrade owner/gh-extension

# Remove extension
gh extension remove owner/gh-extension
```

---

## 🔧 TROUBLESHOOTING

### Common Issues

**Issue: Not authenticated**
```bash
# Solution: Login
gh auth login
```

**Issue: Permission denied**
```bash
# Solution: Refresh token with required scopes
gh auth refresh --scopes repo,workflow,admin:org
```

**Issue: Rate limit exceeded**
```bash
# Solution: Check rate limit
gh api rate_limit

# Wait or use different token
```

**Issue: Command not found**
```bash
# Solution: Install/update gh CLI
winget install --id GitHub.cli

# Or verify PATH
where gh
```

**Issue: Repository not found**
```bash
# Solution: Check if logged in to correct account
gh auth status

# Switch accounts
gh auth switch
```

### Debug Mode

```bash
# Enable debug output
GH_DEBUG=1 gh pr create

# Enable API debug
GH_DEBUG=api gh pr list
```

---

## ✅ BEST PRACTICES

### 1. **Always Check Authentication First**
```bash
gh auth status || gh auth login
```

### 2. **Use --json for Scripting**
```bash
# ✅ GOOD: Programmatic access
PR_NUMBER=$(gh pr create --json number --jq .number)

# ❌ BAD: Parsing text output
PR_NUMBER=$(gh pr create | grep -oP '#\K\d+')
```

### 3. **Use Heredocs for Multi-line Content**
```bash
# ✅ GOOD: Heredoc
gh pr create --body "$(cat <<'EOF'
Multi-line
content
here
EOF
)"

# ❌ BAD: Escaped newlines
gh pr create --body "Multi-line\ncontent\nhere"
```

### 4. **Handle Errors Gracefully**
```bash
# ✅ GOOD: Check command success
if gh pr view 123 > /dev/null 2>&1; then
  gh pr merge 123 --squash
else
  echo "PR not found"
fi
```

### 5. **Use Templates for Consistency**
```bash
# ✅ GOOD: Use template files
gh pr create --body-file .github/PULL_REQUEST_TEMPLATE.md
```

### 6. **Automate Repetitive Tasks**
```bash
# ✅ GOOD: Script for common workflows
#!/bin/bash
# create-feature-pr.sh
gh pr create \
  --title "Feature: $1" \
  --body "$(cat .github/PR_TEMPLATE.md)" \
  --label enhancement
```

### 7. **Use Aliases for Common Commands**
```bash
# Create useful aliases
gh alias set prs 'pr list --state open --assignee @me'
gh alias set issues 'issue list --state open --assignee @me'
gh alias set prc 'pr create --draft --assignee @me'
```

---

**VERSION:** 1.0.0
**STATUS:** ✅ ACTIVE
**LAST UPDATED:** 2026-02-15
**LOCATION:** `~/.claude/memory/docs/github-cli-usage.md`
