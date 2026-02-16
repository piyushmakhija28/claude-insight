# 🔄 Migration Skill & Expert Agent

**VERSION:** 1.0.0
**STATUS:** ✅ ACTIVE
**CREATED:** 2026-02-15

---

## 📦 WHAT WAS CREATED

### 1. Migration Skill (`/migration`)
**Location:** `~/.claude/skills/migration/`

**Purpose:** Handle ALL types of critical system migrations with zero downtime and guaranteed rollback

**Handles:**
- ✅ Framework migrations (Spring Boot, Angular, React, Node.js, .NET, Django)
- ✅ Database migrations (Flyway, Liquibase, engine migrations)
- ✅ API migrations (v1 → v2, breaking changes)
- ✅ Dependency upgrades (major version bumps)
- ✅ Cloud migrations (on-premise → AWS/Azure/GCP)
- ✅ Architecture migrations (monolith → microservices)
- ✅ Auth migrations (Session → JWT → OAuth2)

**Key Features:**
- 🛡️ **Auto-backup**: Creates verified backup before ANY change
- 🔄 **Auto-rollback**: Rolls back automatically on failures
- 📋 **Migration plan**: Generates step-by-step plan
- ✅ **Step validation**: Validates each step before proceeding
- 📊 **Reports**: Generates detailed migration reports
- 🧪 **Staging tests**: Tests on staging before production

### 2. Migration Expert Agent
**Location:** `~/.claude/memory/agents/migration-expert-agent.md`

**Purpose:** Specialized agent for complex migrations requiring analysis, planning, and execution

**Workflow:**
```
Phase 1: Discovery & Analysis (20%)
Phase 2: Planning & Risk Assessment (15%)
Phase 3: Backup & Safety (10%)
Phase 4: Pre-Migration Testing (30%)
Phase 5: Migration Execution (15%)
Phase 6: Post-Migration Verification (10%)
Phase 7: Monitoring & Stabilization (Ongoing)
Phase 8: Cleanup & Documentation (5%)
```

**Risk Levels:**
- 🟢 **LOW**: Patch updates (3.2.0 → 3.2.1)
- 🟡 **MEDIUM**: Minor updates (3.1 → 3.2)
- 🟠 **HIGH**: Major updates (2.7 → 3.2)
- 🔴 **CRITICAL**: Architecture changes (monolith → microservices)

---

## 🚀 USAGE

### Option 1: Interactive Mode
```bash
# Simple and guided
/migration

# Prompts will guide you through:
# 1. Migration type selection
# 2. Current/target versions
# 3. Migration strategy
# 4. Backup confirmation
# 5. Plan review
# 6. Execution confirmation
```

### Option 2: Direct Command
```bash
# Spring Boot migration
/migration --framework "Spring Boot" --from "2.7.18" --to "3.2.0"

# Angular migration
/migration --framework "Angular" --from "15" --to "17"

# Flyway database migration
/migration --type flyway --action create --name "add_user_roles_table"

# API migration
/migration --type api --from "v1" --to "v2" --strategy dual-running
```

### Option 3: Use Agent (Complex Scenarios)
```bash
# Natural language
"Migrate our Spring Boot microservices from 2.7 to 3.2"

# Or Task tool
Task(
  subagent_type="migration-expert",
  prompt="Migrate user-service from Spring Boot 2.7.18 to 3.2.0 with zero downtime"
)
```

---

## 📁 FILE STRUCTURE

```
~/.claude/skills/migration/
├── skill.md                    # Complete skill documentation
├── claude-code-skill.json      # Skill registration (for Claude Code)
├── QUICK-START.md              # This file
├── README.md                   # Quick reference
├── detect-migration-type.py    # Auto-detect migration type
├── analyze-impact.py           # Analyze migration impact
├── create-checklist.py         # Generate migration checklist
├── create-backup.py            # Create comprehensive backup
├── create-rollback-script.py   # Generate rollback script
├── update-dependencies.py      # Update dependencies safely
├── fix-deprecations.py         # Auto-fix deprecation warnings
├── execute-migration.py        # Execute migration steps
├── verify-migration.py         # Verify migration success
├── generate-report.py          # Generate migration report
├── rollback.sh                 # Rollback script (generated per migration)
├── logs/                       # Migration logs
├── backups/                    # Backup storage
└── templates/                  # Migration templates
    ├── spring-boot-migration.json
    ├── angular-migration.json
    ├── database-migration.json
    └── api-migration.json

~/.claude/memory/agents/
├── migration-expert-agent.md   # Agent definition & workflow
└── migration-expert-prompts.md # Agent system prompts (optional)
```

---

## 🎯 COMMON USE CASES

### Use Case 1: Spring Boot 2.7 → 3.2 Migration

**Problem:**
- Need to upgrade to Spring Boot 3.2
- Major breaking changes (javax → jakarta)
- Security API changes
- Application properties renamed

**Solution:**
```bash
/migration --framework "Spring Boot" --from "2.7.18" --to "3.2.0"
```

**What Happens:**
1. ✅ Backup created (code + DB)
2. ✅ Breaking changes identified (52 files affected)
3. ✅ Migration plan created (7 phases, ~2 hours)
4. ✅ Rollback script created
5. ✅ Tested on staging
6. ✅ Executed step-by-step
7. ✅ All tests passed (127/127)
8. ✅ Report generated

**Result:** Migration completed in 2h 15m with zero downtime

### Use Case 2: Database Schema Migration

**Problem:**
- Need to add new table for user roles
- Need rollback capability
- Need to test before production

**Solution:**
```bash
/migration --type flyway --action create --name "add_user_roles_table"
```

**What Happens:**
1. ✅ Creates V{timestamp}__add_user_roles_table.sql
2. ✅ Creates U{timestamp}__add_user_roles_table.sql (rollback)
3. ✅ Validates SQL syntax
4. ✅ Tests on local database
5. ✅ Documentation generated

**Result:** Migration files ready to commit in 15 minutes

### Use Case 3: API v1 → v2 Migration

**Problem:**
- Breaking changes in API
- Need to support both v1 and v2
- Gradual client migration

**Solution:**
```bash
/migration --type api --from "v1" --to "v2" --strategy dual-running
```

**What Happens:**
1. ✅ Creates /api/v2 endpoints
2. ✅ Keeps /api/v1 running (deprecated)
3. ✅ Adds version routing
4. ✅ Documents v2 API
5. ✅ Sets deprecation timeline (6 months)
6. ✅ Monitors usage

**Result:** Dual-running APIs with gradual migration over 6 months

### Use Case 4: PostgreSQL 12 → 15 Upgrade

**Problem:**
- Need to upgrade PostgreSQL
- Cannot afford downtime
- Data integrity critical

**Solution:**
```bash
/migration --type database --engine postgresql --from "12" --to "15"
```

**What Happens:**
1. ✅ Full database backup
2. ✅ New PostgreSQL 15 instance created
3. ✅ Backup restored to new instance
4. ✅ Gradual traffic shift (10% → 50% → 100%)
5. ✅ Old instance kept for 7 days

**Result:** Zero-downtime migration with instant rollback capability

---

## 🛡️ SAFETY GUARANTEES

### Every Migration MUST Have:

1. **✅ Full Backup**
   - Code: Git commit + tag
   - Database: Full dump (verified)
   - Config: All configuration files
   - Data: Critical data export

2. **✅ Rollback Script**
   - Automated rollback
   - Tested in dry-run mode
   - Rollback time <5 minutes

3. **✅ Migration Plan**
   - Step-by-step breakdown
   - Time estimates per step
   - Validation criteria per step

4. **✅ Staging Test**
   - Tested on staging before production
   - All tests must pass
   - Performance verified

5. **✅ Auto-Rollback Triggers**
   - Build failures
   - Test failures (>10%)
   - Critical errors
   - Performance degradation (>50%)
   - Database errors

---

## 📊 MIGRATION METRICS

### Success Criteria:
- ✅ All services running and healthy
- ✅ All tests passing (>95% pass rate)
- ✅ No critical errors in logs
- ✅ Performance within 10% of baseline
- ✅ Zero data loss
- ✅ Zero security vulnerabilities introduced
- ✅ Rollback capability verified

### Auto-Rollback Triggers:
- ❌ Build fails
- ❌ Test failure rate >10%
- ❌ Critical errors detected
- ❌ Response time >2x baseline
- ❌ Error rate increase >5%
- ❌ Database connection failures
- ❌ Service crash/restart loop

---

## 🔗 INTEGRATION

### Integrated with CLAUDE.md:
- ✅ Added migration section in CLAUDE.md
- ✅ Version updated to v2.4.0
- ✅ Usage examples documented
- ✅ Risk levels defined
- ✅ Auto-rollback triggers documented

### Integrated with Git Auto-Commit:
- ✅ Pre-migration tag: `pre-migration-{timestamp}`
- ✅ Post-migration tag: `post-migration-{timestamp}`
- ✅ Migration commit message format defined
- ✅ Rollback script included in commit

### Integrated with Other Skills:
- ✅ Uses `/commit` for migration commits
- ✅ Uses `/test` for running test suites
- ✅ Uses `/docker` for Docker config updates
- ✅ Uses `/kubernetes` for K8s manifest updates

---

## 📖 DOCUMENTATION

### Quick Reference:
- **Quick Start Guide:** `QUICK-START.md`
- **This File:** `README.md`

### Complete Documentation:
- **Skill Documentation:** `skill.md` (comprehensive)
- **Agent Definition:** `~/.claude/memory/agents/migration-expert-agent.md`
- **CLAUDE.md Section:** Migration section added

### Examples:
- Spring Boot migration examples
- Database migration examples
- API migration examples
- Angular migration examples
- PostgreSQL migration examples

---

## 🎓 LEARNING PATH

### Beginner:
1. Read QUICK-START.md
2. Try interactive mode: `/migration`
3. Test on small project (patch update)
4. Review generated migration report

### Intermediate:
1. Read skill.md
2. Use direct commands with parameters
3. Test major version migration (staging first!)
4. Understand rollback procedures

### Advanced:
1. Read agent definition
2. Use migration-expert agent for complex scenarios
3. Customize migration templates
4. Create custom migration scripts

---

## 🚨 IMPORTANT NOTES

### DO:
- ✅ Always create backup before migration
- ✅ Always test on staging first
- ✅ Always have rollback plan
- ✅ Always monitor after migration
- ✅ Read breaking changes documentation

### DON'T:
- ❌ Skip backup ("it's just a patch update")
- ❌ Skip staging tests ("let's test in production")
- ❌ Skip rollback testing ("we won't need it")
- ❌ Ignore breaking changes ("we'll fix it later")
- ❌ Rush migration ("let's finish in 1 hour")

---

## 📞 SUPPORT

### If You Need Help:

1. **Read Documentation First:**
   - QUICK-START.md (this file)
   - skill.md (complete guide)
   - agent definition

2. **Check Logs:**
   ```bash
   tail -f ~/.claude/skills/migration/logs/migration-{timestamp}.log
   ```

3. **Test Rollback:**
   ```bash
   bash rollback.sh --dry-run
   ```

4. **Execute Rollback if Needed:**
   ```bash
   bash rollback.sh
   ```

5. **Ask Migration Expert Agent:**
   ```bash
   "I need help with migration rollback"
   ```

---

## ✅ QUICK CHECKLIST

**Before Migration:**
- [ ] Backup created and verified
- [ ] Rollback script created and tested
- [ ] Staging environment prepared
- [ ] Breaking changes documented
- [ ] Team notified

**During Migration:**
- [ ] Execute step-by-step
- [ ] Validate after each step
- [ ] Monitor logs
- [ ] Check error rates

**After Migration:**
- [ ] All services healthy
- [ ] All tests passed
- [ ] Performance baseline met
- [ ] Documentation updated
- [ ] Team notified

---

## 🎉 READY TO MIGRATE!

```bash
# Start your first migration:
/migration

# Or ask naturally:
"I need to migrate Spring Boot from 2.7 to 3.2"

# Happy migrating! 🚀
```

---

**VERSION:** 1.0.0
**STATUS:** ✅ ACTIVE
**CREATED:** 2026-02-15
**LOCATION:** `~/.claude/skills/migration/`
