# Migration Skill

**VERSION:** 1.0.0
**STATUS:** ✅ ACTIVE
**TYPE:** Critical System Migration Handler

---

## 🎯 SKILL PURPOSE

**Handle ALL types of critical migrations with zero downtime and rollback capability:**
- Framework version upgrades (Spring Boot, Angular, React, etc.)
- Database schema migrations (Flyway, Liquibase, manual)
- API version migrations (v1 → v2, breaking changes)
- Dependency upgrades (major version bumps)
- Cloud infrastructure migrations (AWS, Azure, GCP)
- Microservice architecture migrations (monolith → microservices)
- Authentication system migrations (OAuth, JWT versions)
- Data migrations (database transfers, cloud migrations)

---

## 🚨 CRITICAL RULES

### 1. **ALWAYS Create Backup First**
```bash
# Before ANY migration
- Database: Full backup + verification
- Code: Git commit + tag (pre-migration-{version})
- Config: Backup all configuration files
- Data: Export critical data to safe location
```

### 2. **ALWAYS Have Rollback Plan**
```bash
# Every migration MUST have:
- Documented rollback steps
- Automated rollback script
- Tested rollback procedure
- Rollback time estimate
```

### 3. **ALWAYS Test in Staging First**
```bash
# Migration order:
1. Local environment
2. Development environment
3. Staging environment
4. Production environment (with approval)
```

### 4. **NEVER Skip Breaking Change Analysis**
```bash
# Before migration, document:
- What breaks
- What changes
- What's deprecated
- What's removed
- What's new
```

---

## 📋 MIGRATION WORKFLOW

### Phase 1: Analysis & Planning
```bash
# 1. Identify migration type
python ~/.claude/skills/migration/detect-migration-type.py \
  --current-version "{CURRENT}" \
  --target-version "{TARGET}" \
  --framework "{FRAMEWORK}"

# Output: migration_plan.json with:
# - Migration type (framework, db, api, etc.)
# - Breaking changes list
# - Deprecation warnings
# - Estimated time
# - Risk level (LOW/MEDIUM/HIGH/CRITICAL)

# 2. Analyze impact
python ~/.claude/skills/migration/analyze-impact.py \
  --project-root "{ROOT}" \
  --migration-plan migration_plan.json

# Output: impact_report.json with:
# - Files affected
# - Code changes needed
# - Dependencies to update
# - Config changes needed
# - Database changes needed

# 3. Create migration checklist
python ~/.claude/skills/migration/create-checklist.py \
  --migration-plan migration_plan.json \
  --impact-report impact_report.json

# Output: migration_checklist.md
```

### Phase 2: Backup & Safety
```bash
# 1. Create comprehensive backup
python ~/.claude/skills/migration/create-backup.py \
  --backup-type full \
  --include database,code,config,data

# Output: backup_manifest.json with:
# - Backup location
# - Backup timestamp
# - Backup verification checksum
# - Restore procedure

# 2. Create rollback script
python ~/.claude/skills/migration/create-rollback-script.py \
  --current-version "{CURRENT}" \
  --target-version "{TARGET}" \
  --backup-manifest backup_manifest.json

# Output: rollback.sh (executable script)

# 3. Test rollback (dry-run)
bash ~/.claude/skills/migration/rollback.sh --dry-run
```

### Phase 3: Pre-Migration
```bash
# 1. Update dependencies (if needed)
python ~/.claude/skills/migration/update-dependencies.py \
  --migration-plan migration_plan.json \
  --strategy gradual  # or aggressive

# 2. Fix deprecation warnings
python ~/.claude/skills/migration/fix-deprecations.py \
  --scan-directory "{PROJECT_ROOT}" \
  --auto-fix true  # or false for manual review

# 3. Run pre-migration tests
python ~/.claude/skills/migration/run-pre-tests.py \
  --test-suite full  # all tests must pass
```

### Phase 4: Migration Execution
```bash
# 1. Execute migration
python ~/.claude/skills/migration/execute-migration.py \
  --migration-plan migration_plan.json \
  --strategy step-by-step  # or all-at-once (risky!)

# Steps:
# - Phase 1: Code changes
# - Phase 2: Config updates
# - Phase 3: Database migration
# - Phase 4: Dependency updates
# - Phase 5: Build verification
# - Phase 6: Test execution

# 2. Monitor migration progress
tail -f ~/.claude/skills/migration/logs/migration-{timestamp}.log

# 3. Handle failures (auto-rollback on critical errors)
# Script automatically rolls back on:
# - Build failures
# - Test failures (>10% failure rate)
# - Database migration errors
# - Critical dependency conflicts
```

### Phase 5: Post-Migration Verification
```bash
# 1. Run post-migration tests
python ~/.claude/skills/migration/run-post-tests.py \
  --test-suite full \
  --include smoke,integration,e2e

# 2. Verify functionality
python ~/.claude/skills/migration/verify-migration.py \
  --check-list all

# Verifies:
# - All services running
# - All endpoints responding
# - Database integrity
# - Configuration correctness
# - Performance benchmarks

# 3. Generate migration report
python ~/.claude/skills/migration/generate-report.py \
  --output migration_report.md
```

### Phase 6: Cleanup & Documentation
```bash
# 1. Clean deprecated code
python ~/.claude/skills/migration/cleanup-deprecated.py \
  --remove-commented-code true \
  --remove-unused-imports true

# 2. Update documentation
python ~/.claude/skills/migration/update-docs.py \
  --migration-report migration_report.md

# 3. Tag release
gh release create "post-migration-{version}" \
  --title "Migration to {TARGET_VERSION}" \
  --notes-file migration_report.md
```

---

## 🔧 MIGRATION TYPES HANDLED

### 1. Framework Migration (Spring Boot Example)

**Spring Boot 2.7 → 3.2**
```bash
# Invoke skill
/migration --type framework \
  --framework "Spring Boot" \
  --from "2.7.18" \
  --to "3.2.0"

# What it does:
# 1. Analyze breaking changes:
#    - javax.* → jakarta.*
#    - spring.datasource.* property changes
#    - Security config changes
#    - Actuator endpoint changes

# 2. Create migration plan:
#    Step 1: Update parent POM
#    Step 2: Replace javax with jakarta
#    Step 3: Update security config
#    Step 4: Update application.yml
#    Step 5: Fix deprecations
#    Step 6: Run tests

# 3. Execute with validation at each step

# 4. Auto-rollback if any step fails
```

### 2. Database Migration

**PostgreSQL 12 → 15**
```bash
# Invoke skill
/migration --type database \
  --engine postgresql \
  --from "12.x" \
  --to "15.x"

# What it does:
# 1. Backup current database (full dump)
# 2. Check compatibility issues
# 3. Generate migration SQL
# 4. Test migration on copy
# 5. Execute migration with monitoring
# 6. Verify data integrity
# 7. Update connection configs
```

**Flyway Migration**
```bash
# Invoke skill
/migration --type flyway \
  --create-migration "add_user_roles_table"

# What it does:
# 1. Generate migration file: V{timestamp}__add_user_roles_table.sql
# 2. Add rollback file: U{timestamp}__add_user_roles_table.sql
# 3. Validate migration syntax
# 4. Test on local database
# 5. Generate migration documentation
```

### 3. API Migration

**REST API v1 → v2**
```bash
# Invoke skill
/migration --type api \
  --from "v1" \
  --to "v2" \
  --strategy dual-running  # v1 and v2 run simultaneously

# What it does:
# 1. Identify breaking changes in API
# 2. Create v2 endpoints
# 3. Maintain v1 endpoints (deprecated)
# 4. Add version routing
# 5. Update client SDKs
# 6. Document migration path for API consumers
# 7. Set deprecation timeline for v1
```

### 4. Dependency Migration

**Node.js Dependencies Major Upgrade**
```bash
# Invoke skill
/migration --type dependencies \
  --package-manager npm \
  --strategy safe  # upgrade one by one

# What it does:
# 1. Analyze package.json for major version updates
# 2. Check breaking changes for each package
# 3. Create dependency graph
# 4. Upgrade in correct order (dependencies first)
# 5. Run tests after each upgrade
# 6. Rollback if tests fail
```

### 5. Cloud Migration

**On-Premise → AWS**
```bash
# Invoke skill
/migration --type cloud \
  --from on-premise \
  --to aws \
  --strategy lift-and-shift  # or refactor

# What it does:
# 1. Analyze current infrastructure
# 2. Create AWS architecture diagram
# 3. Set up AWS resources (Terraform/CloudFormation)
# 4. Create data migration plan
# 5. Set up parallel environments
# 6. Migrate data incrementally
# 7. Switch traffic gradually (blue-green deployment)
# 8. Decommission old infrastructure
```

### 6. Microservice Migration

**Monolith → Microservices**
```bash
# Invoke skill
/migration --type architecture \
  --from monolith \
  --to microservices \
  --decomposition-strategy domain-driven

# What it does:
# 1. Analyze monolith domain boundaries
# 2. Identify bounded contexts
# 3. Create service dependency graph
# 4. Extract services one by one (strangler pattern)
# 5. Set up API gateway
# 6. Implement service discovery
# 7. Add distributed tracing
# 8. Migrate data stores
```

### 7. Authentication Migration

**Session-based → JWT**
```bash
# Invoke skill
/migration --type auth \
  --from session-based \
  --to jwt \
  --strategy gradual-rollout

# What it does:
# 1. Implement JWT authentication alongside sessions
# 2. Add token generation endpoint
# 3. Update auth middleware to support both
# 4. Migrate users gradually (on next login)
# 5. Monitor JWT adoption rate
# 6. Deprecate session-based auth after 100% migration
```

---

## 📊 RISK ASSESSMENT

### Risk Levels

**LOW RISK:**
- Minor dependency updates (patch versions)
- Adding new features (no changes to existing)
- Configuration additions (non-breaking)

**MEDIUM RISK:**
- Minor version upgrades (with deprecations)
- Database schema additions (new columns/tables)
- API additions (new endpoints)

**HIGH RISK:**
- Major version upgrades (breaking changes)
- Database schema modifications (column changes)
- API modifications (endpoint changes)

**CRITICAL RISK:**
- Framework major version jump (2.x → 3.x)
- Database engine migration (MySQL → PostgreSQL)
- Architecture changes (monolith → microservices)
- Auth system replacement (complete overhaul)

### Risk Mitigation Strategy

```bash
# For CRITICAL migrations:
1. ✅ Multiple staging tests (3+ environments)
2. ✅ Feature flags for gradual rollout
3. ✅ Blue-green deployment
4. ✅ Automated rollback triggers
5. ✅ Real-time monitoring with alerts
6. ✅ Gradual traffic shift (10% → 50% → 100%)
7. ✅ 24/7 team availability during migration
8. ✅ Customer communication plan
```

---

## 🔄 ROLLBACK STRATEGIES

### Automatic Rollback Triggers

```python
# rollback.sh automatically triggers on:

# 1. Build failures
if ! mvn clean install; then
    echo "Build failed, rolling back..."
    bash rollback.sh
fi

# 2. Test failures (>10% failure rate)
FAILURE_RATE=$(python calculate_test_failures.py)
if [ "$FAILURE_RATE" -gt 10 ]; then
    echo "Test failure rate: $FAILURE_RATE%, rolling back..."
    bash rollback.sh
fi

# 3. Critical errors in logs
if grep -q "CRITICAL ERROR" logs/app.log; then
    echo "Critical errors detected, rolling back..."
    bash rollback.sh
fi

# 4. Performance degradation (>50% slower)
PERF_DEGRADATION=$(python check_performance.py)
if [ "$PERF_DEGRADATION" -gt 50 ]; then
    echo "Performance degraded by $PERF_DEGRADATION%, rolling back..."
    bash rollback.sh
fi

# 5. Manual trigger (user aborts)
if [ "$USER_ABORT" = "true" ]; then
    echo "User aborted migration, rolling back..."
    bash rollback.sh
fi
```

### Manual Rollback

```bash
# Quick rollback (restore backup)
bash ~/.claude/skills/migration/rollback.sh --quick

# Full rollback (step-by-step reverse)
bash ~/.claude/skills/migration/rollback.sh --full

# Partial rollback (specific phase)
bash ~/.claude/skills/migration/rollback.sh --phase database
```

---

## 📝 MIGRATION CHECKLIST TEMPLATE

```markdown
# Migration Checklist: {FRAMEWORK} {FROM_VERSION} → {TO_VERSION}

## Pre-Migration
- [ ] Full backup created and verified
- [ ] Rollback script created and tested
- [ ] Staging environment prepared
- [ ] Breaking changes documented
- [ ] Team notified about migration
- [ ] Maintenance window scheduled (if needed)
- [ ] Monitoring alerts configured

## Migration Steps
- [ ] Phase 1: Dependency updates
  - [ ] Update POM/package.json
  - [ ] Resolve conflicts
  - [ ] Build succeeds
  - [ ] Tests pass

- [ ] Phase 2: Code changes
  - [ ] Fix breaking changes
  - [ ] Update deprecated APIs
  - [ ] Remove obsolete code
  - [ ] Build succeeds
  - [ ] Tests pass

- [ ] Phase 3: Configuration updates
  - [ ] Update application.yml/properties
  - [ ] Update environment variables
  - [ ] Update Docker configs
  - [ ] Update K8s configs
  - [ ] Build succeeds
  - [ ] Tests pass

- [ ] Phase 4: Database migration (if applicable)
  - [ ] Backup database
  - [ ] Run migration scripts
  - [ ] Verify schema changes
  - [ ] Verify data integrity
  - [ ] Tests pass

## Post-Migration
- [ ] All services running
- [ ] All endpoints responding
- [ ] Performance benchmarks met
- [ ] No critical errors in logs
- [ ] Smoke tests passed
- [ ] Integration tests passed
- [ ] E2E tests passed
- [ ] Documentation updated
- [ ] Team notified of completion
- [ ] Git tag created
- [ ] Release notes published

## Rollback Ready
- [ ] Rollback script accessible
- [ ] Backup verified and accessible
- [ ] Team knows rollback procedure
- [ ] Rollback can be executed in <5 minutes
```

---

## 🎯 USAGE EXAMPLES

### Example 1: Spring Boot Migration
```bash
# Invoke skill
/migration --framework "Spring Boot" --from "2.7.18" --to "3.2.0"

# Skill automatically:
# 1. Creates backup
# 2. Analyzes breaking changes (javax → jakarta, etc.)
# 3. Updates POM
# 4. Replaces imports across codebase
# 5. Updates security config
# 6. Updates application.yml
# 7. Runs tests at each step
# 8. Rolls back if any step fails
# 9. Generates migration report
```

### Example 2: Database Schema Migration
```bash
# Invoke skill
/migration --type flyway --action "add_column" \
  --table "users" --column "email_verified BOOLEAN DEFAULT false"

# Skill automatically:
# 1. Generates V{timestamp}__add_email_verified_column.sql
# 2. Generates U{timestamp}__add_email_verified_column.sql (rollback)
# 3. Tests migration on local DB
# 4. Documents migration
# 5. Ready to commit
```

### Example 3: Angular Migration
```bash
# Invoke skill
/migration --framework "Angular" --from "15" --to "17"

# Skill automatically:
# 1. Runs ng update @angular/core@17 @angular/cli@17
# 2. Analyzes breaking changes
# 3. Updates deprecated APIs
# 4. Fixes standalone component issues
# 5. Updates routing config
# 6. Runs ng build
# 7. Runs ng test
# 8. Generates migration report
```

---

## 🔗 INTEGRATION WITH OTHER SKILLS

### Auto-invoked by:
- **commit skill**: Creates migration commit with detailed message
- **github skill**: Creates migration PR with checklist

### Invokes:
- **testing skill**: Runs comprehensive test suite
- **docker skill**: Updates Docker configs if needed
- **kubernetes skill**: Updates K8s manifests if needed

---

## 📂 SKILL FILES

```
~/.claude/skills/migration/
├── skill.md                           # This file
├── detect-migration-type.py           # Detects migration type
├── analyze-impact.py                  # Analyzes migration impact
├── create-checklist.py                # Generates migration checklist
├── create-backup.py                   # Creates comprehensive backup
├── create-rollback-script.py          # Generates rollback script
├── update-dependencies.py             # Updates dependencies safely
├── fix-deprecations.py                # Auto-fixes deprecation warnings
├── execute-migration.py               # Executes migration steps
├── verify-migration.py                # Verifies migration success
├── generate-report.py                 # Generates migration report
├── rollback.sh                        # Rollback script (generated)
├── logs/                              # Migration logs
├── backups/                           # Backup storage
└── templates/                         # Migration templates
    ├── spring-boot-migration.json
    ├── angular-migration.json
    ├── database-migration.json
    └── api-migration.json
```

---

## 🚀 QUICK START

```bash
# Invoke migration skill
/migration

# Interactive mode prompts:
# 1. Select migration type (framework, database, api, etc.)
# 2. Enter current version
# 3. Enter target version
# 4. Choose migration strategy (safe/aggressive)
# 5. Confirm backup creation
# 6. Review migration plan
# 7. Confirm execution

# Or use direct command:
/migration --framework "Spring Boot" --from "2.7.18" --to "3.2.0" --auto-approve
```

---

**VERSION:** 1.0.0
**STATUS:** ✅ ACTIVE
**SKILL OWNER:** Claude Migration Expert
**LAST UPDATED:** 2026-02-15
