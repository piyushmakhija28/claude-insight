# Migration Skill & Agent - Quick Start Guide

**VERSION:** 1.0.0
**LAST UPDATED:** 2026-02-15

---

## 🚀 QUICK START

### 1. Interactive Migration (Recommended for first-time users)

```bash
# Just type /migration and follow prompts
/migration

# Prompts:
# 1. Select migration type (framework, database, api, etc.)
# 2. Enter current version
# 3. Enter target version
# 4. Choose migration strategy (safe/aggressive)
# 5. Confirm backup creation
# 6. Review migration plan
# 7. Confirm execution
```

### 2. Direct Command (For experienced users)

```bash
# Spring Boot migration
/migration --framework "Spring Boot" --from "2.7.18" --to "3.2.0"

# Angular migration
/migration --framework "Angular" --from "15" --to "17"

# Database migration
/migration --type flyway --action "create" --name "add_user_roles"

# API migration
/migration --type api --from "v1" --to "v2" --strategy dual-running
```

### 3. Use Migration Expert Agent (For complex scenarios)

```bash
# Just ask Claude naturally:
"I need to migrate Spring Boot from 2.7 to 3.2 in our microservices"

# Or use Task tool:
Task(
  subagent_type="migration-expert",
  prompt="Migrate all microservices from Spring Boot 2.7.18 to 3.2.0 with zero downtime"
)
```

---

## 📋 COMMON SCENARIOS

### Scenario 1: Spring Boot Version Upgrade

```bash
# Problem: Need to upgrade Spring Boot 2.7 → 3.2

# Solution:
/migration --framework "Spring Boot" --from "2.7.18" --to "3.2.0"

# What happens:
# 1. ✅ Creates backup (code + DB)
# 2. ✅ Analyzes breaking changes (javax → jakarta, etc.)
# 3. ✅ Creates migration plan (7 steps)
# 4. ✅ Creates rollback script
# 5. ✅ Tests on staging
# 6. ✅ Executes migration step-by-step
# 7. ✅ Verifies success
# 8. ✅ Generates report

# Time: ~2 hours (auto-estimated)
# Risk: HIGH
# Rollback: Available (bash rollback.sh)
```

### Scenario 2: Database Schema Change

```bash
# Problem: Need to add new table for user roles

# Solution:
/migration --type flyway --action create --name "add_user_roles_table"

# What happens:
# 1. ✅ Creates V{timestamp}__add_user_roles_table.sql
# 2. ✅ Creates U{timestamp}__add_user_roles_table.sql (rollback)
# 3. ✅ Validates SQL syntax
# 4. ✅ Tests on local database
# 5. ✅ Generates migration documentation
# 6. ✅ Ready to commit

# Time: ~15 minutes
# Risk: MEDIUM
# Rollback: SQL rollback script available
```

### Scenario 3: Angular Version Upgrade

```bash
# Problem: Angular 15 → 17 (multiple major versions)

# Solution:
/migration --framework "Angular" --from "15" --to "17"

# What happens:
# 1. ✅ Runs ng update @angular/core@17 @angular/cli@17
# 2. ✅ Analyzes breaking changes
# 3. ✅ Updates deprecated APIs
# 4. ✅ Fixes standalone component issues
# 5. ✅ Updates routing configuration
# 6. ✅ Runs ng build
# 7. ✅ Runs ng test
# 8. ✅ Generates migration report

# Time: ~3 hours
# Risk: HIGH
# Rollback: Git revert available
```

### Scenario 4: API Versioning (v1 → v2)

```bash
# Problem: Breaking changes in API, need v2 while keeping v1

# Solution:
/migration --type api --from "v1" --to "v2" --strategy dual-running

# What happens:
# 1. ✅ Creates /api/v2 endpoints
# 2. ✅ Keeps /api/v1 endpoints running (deprecated)
# 3. ✅ Adds version routing in API Gateway
# 4. ✅ Documents v2 API (OpenAPI/Swagger)
# 5. ✅ Creates migration guide for API consumers
# 6. ✅ Sets deprecation timeline (6 months)
# 7. ✅ Monitors v1 vs v2 usage

# Time: ~1 week (incremental)
# Risk: MEDIUM
# Rollback: Remove v2 routing (instant)
```

### Scenario 5: PostgreSQL Version Upgrade

```bash
# Problem: PostgreSQL 12 → 15 upgrade

# Solution:
/migration --type database --engine postgresql --from "12" --to "15"

# What happens:
# 1. ✅ Full database backup (verified)
# 2. ✅ Checks compatibility issues
# 3. ✅ Creates new PostgreSQL 15 instance
# 4. ✅ Restores backup to new instance
# 5. ✅ Tests new database thoroughly
# 6. ✅ Gradual traffic shift (10% → 50% → 100%)
# 7. ✅ Decommissions old instance after 7 days

# Time: ~1 day (with monitoring)
# Risk: CRITICAL
# Rollback: Switch back to old instance (<1 min)
```

---

## 🛡️ SAFETY FEATURES

### Feature 1: Auto-Backup
```bash
# Every migration automatically creates:
- Git commit + tag (pre-migration-{timestamp})
- Database backup (if applicable)
- Configuration backup
- Critical data export

# Backup verification:
- Checksum validation
- Restore test (dry-run)
- Documented restore procedure
```

### Feature 2: Auto-Rollback
```bash
# Migration automatically rolls back if:
- Build fails
- Test failure rate >10%
- Critical errors detected
- Performance degradation >50%
- Database errors
- Service crashes

# Rollback time: <5 minutes
```

### Feature 3: Step-by-Step Validation
```bash
# Each migration step is validated:
Step 1: Update dependency
  → Validate: Build succeeds
  → If fails: Rollback to Step 0

Step 2: Update code
  → Validate: Tests pass
  → If fails: Rollback to Step 0

Step 3: Deploy
  → Validate: Services healthy
  → If fails: Rollback to Step 0
```

### Feature 4: Staging Tests
```bash
# Every migration is tested on staging before production:
1. Test on local environment
2. Test on dev environment
3. Test on staging environment (production replica)
4. Get approval
5. Deploy to production (monitored)
```

---

## 📊 MIGRATION REPORTS

### Sample Migration Report

```markdown
# Migration Report: Spring Boot 2.7.18 → 3.2.0

**Date:** 2026-02-15
**Duration:** 2h 15m
**Status:** ✅ SUCCESS

## Summary
- Framework: Spring Boot
- From: 2.7.18
- To: 3.2.0
- Risk Level: HIGH
- Files Changed: 52
- Tests: 127/127 passed

## Breaking Changes
1. javax.* → jakarta.* namespace change
   - Affected files: 45
   - Auto-fixed: Yes

2. Spring Security API changes
   - Affected files: 8
   - Manual fixes: 3

3. Application properties renamed
   - Affected files: 1
   - Auto-fixed: Yes

## Migration Steps
✅ Step 1: Updated POM (5 minutes)
✅ Step 2: Replaced imports (15 minutes)
✅ Step 3: Updated Security config (30 minutes)
✅ Step 4: Updated application.yml (5 minutes)
✅ Step 5: Build verification (10 minutes)
✅ Step 6: Test execution (45 minutes)
✅ Step 7: Staging deployment (25 minutes)

## Verification
✅ All services running
✅ All endpoints responding (200 OK)
✅ No errors in logs
✅ Performance within baseline (<5% variance)
✅ Database integrity verified
✅ Security scan passed

## Rollback Information
- Rollback script: rollback.sh
- Rollback time: <5 minutes
- Backup location: backups/pre-migration-20260215/

## Recommendations
1. Monitor production for 24 hours
2. Keep backup for 30 days
3. Update documentation
4. Train team on Spring Boot 3.2 features

## Next Steps
1. Deploy to production (scheduled: 2026-02-16 02:00 AM)
2. Monitor error rates
3. Clean up deprecated code
4. Update developer guides
```

---

## 🎯 BEST PRACTICES

### 1. Always Test on Staging First
```bash
# NEVER skip staging tests
✅ Local → Dev → Staging → Production

# If you skip staging:
❌ Risk: CRITICAL
❌ Rollback probability: HIGH
❌ Downtime risk: HIGH
```

### 2. Create Backup Even for "Safe" Migrations
```bash
# Even for patch updates:
✅ Create backup (takes 2 minutes)
✅ Test rollback (takes 1 minute)

# Better safe than sorry!
```

### 3. Use Safe Strategy by Default
```bash
# Migration strategies:
- safe: Step-by-step with validation (RECOMMENDED)
- aggressive: All-at-once (RISKY)
- gradual: Phased rollout (for production)
- blue-green: Parallel environments (for critical systems)

# Default to "safe" unless you know what you're doing
```

### 4. Monitor After Migration
```bash
# First 24 hours after migration:
- Check error rates every 15 minutes
- Check performance metrics
- Check user feedback
- Be ready to rollback

# Keep rollback available for 7 days
```

### 5. Document Everything
```bash
# After migration:
- Update README.md
- Update API documentation
- Update deployment docs
- Share migration report with team
- Document lessons learned
```

---

## 🚨 COMMON MISTAKES TO AVOID

### ❌ Mistake 1: Skipping Backup
```bash
# WRONG: "It's just a patch update, no need for backup"
/migration --framework "Spring Boot" --from "3.2.0" --to "3.2.1" --skip-backup

# RIGHT: Always create backup
/migration --framework "Spring Boot" --from "3.2.0" --to "3.2.1"
```

### ❌ Mistake 2: Not Testing Rollback
```bash
# WRONG: Create rollback script but never test it
create_rollback_script()  # untested!

# RIGHT: Always test rollback in dry-run mode
bash rollback.sh --dry-run
```

### ❌ Mistake 3: Migrating Production Directly
```bash
# WRONG: Skip staging, go straight to production
migrate_production()  # DANGER!

# RIGHT: Test on staging first
migrate_staging() → verify() → migrate_production()
```

### ❌ Mistake 4: Ignoring Breaking Changes
```bash
# WRONG: "Let's upgrade and see what breaks"
upgrade_blindly()

# RIGHT: Analyze breaking changes first
analyze_breaking_changes() → plan_fixes() → execute_migration()
```

### ❌ Mistake 5: No Monitoring After Migration
```bash
# WRONG: Deploy and forget
deploy() → exit()

# RIGHT: Deploy and monitor
deploy() → monitor(duration="24h") → verify() → cleanup()
```

---

## 📞 GETTING HELP

### If Migration Fails:

```bash
# 1. Don't panic!
# 2. Check migration logs:
tail -f ~/.claude/skills/migration/logs/migration-{timestamp}.log

# 3. Check rollback script:
bash rollback.sh --dry-run

# 4. Execute rollback if needed:
bash rollback.sh

# 5. Analyze failure:
cat migration_report.md

# 6. Fix issues and retry
```

### If Rollback Fails:

```bash
# Emergency rollback (nuclear option):
# 1. Restore from backup manually
git checkout pre-migration-{timestamp}

# 2. Restore database (if applicable)
psql < backups/db_backup_{timestamp}.sql

# 3. Restart services
systemctl restart app

# 4. Verify services
curl http://localhost:8080/health
```

---

## 🎓 LEARNING RESOURCES

### Migration Skill Docs
- Full documentation: `~/.claude/skills/migration/skill.md`
- Agent definition: `~/.claude/memory/agents/migration-expert-agent.md`
- Quick start: This file

### Framework-Specific Guides
- Spring Boot migrations: Official Spring Boot migration guides
- Angular migrations: `ng update` documentation
- Database migrations: Flyway/Liquibase documentation

### Best Practices
- Blue-green deployments
- Canary releases
- Feature flags
- Database migration patterns

---

## ✅ CHECKLIST

Before starting migration:
- [ ] Read migration plan
- [ ] Understand breaking changes
- [ ] Backup created and verified
- [ ] Rollback script created and tested
- [ ] Staging environment prepared
- [ ] Team notified
- [ ] Maintenance window scheduled (if needed)

During migration:
- [ ] Execute step-by-step
- [ ] Validate after each step
- [ ] Monitor logs in real-time
- [ ] Check error rates
- [ ] Verify functionality

After migration:
- [ ] All services healthy
- [ ] All tests passed
- [ ] Performance baseline met
- [ ] No critical errors
- [ ] Documentation updated
- [ ] Team notified
- [ ] Migration report generated

---

**Happy Migrating! 🚀**

Remember: Measure twice, migrate once!

**VERSION:** 1.0.0
**STATUS:** ✅ ACTIVE
**LAST UPDATED:** 2026-02-15
