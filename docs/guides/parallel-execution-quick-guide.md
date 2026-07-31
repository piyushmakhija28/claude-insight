# 🚀 PARALLEL EXECUTION - QUICK USAGE GUIDE

**Version:** 1.0.0
**Last Updated:** 2026-02-16

---

## ⚡ TL;DR

**What it does:**
- Runs independent tasks in parallel using multiple subagents
- Auto-creates temporary skills/agents as needed
- Merges results intelligently
- Cleans up unused resources

**When it activates:**
- Automatically when 3+ independent tasks are detected
- No user action required!

**Expected speedup:**
- 3-10x faster execution

---

## 🎯 QUICK START

### For Users (Zero Setup Required)

Just use Claude Code as normal! The system automatically:

1. Detects when you have multiple independent tasks
2. Launches them in parallel if beneficial
3. Shows you a massive speedup

**Example:**

```
You: "Create auth-service, user-service, and product-service"

Claude:
✅ Detected 3 independent tasks
⚡ Launching parallel execution (estimated 3x speedup)
🚀 Task 1: Creating auth-service... (subagent: spring-boot-microservices)
🚀 Task 2: Creating user-service... (subagent: spring-boot-microservices)
🚀 Task 3: Creating product-service... (subagent: spring-boot-microservices)
⏳ Waiting for all tasks to complete...
✅ All 3 services created in 5.2 minutes (vs 15 min sequential)
📊 Speedup achieved: 2.9x
```

---

## 📋 MANUAL USAGE (Advanced)

### Analyze Tasks for Parallelization

```bash
python ~/.claude/memory/scripts/auto-parallel-detector.py --tasks-file tasks.json
```

**Output:**
```
⚡ PARALLEL EXECUTION RECOMMENDATION

✅ RECOMMENDATION: Use Parallel Execution
   Reason: Homogeneous tasks (service_creation), speedup: 3.0x
   Estimated Speedup: 3.0x

📊 METRICS:
   Total Tasks:         3
   Parallel Groups:     1
   Max Parallel Tasks:  3
```

---

### Execute Tasks in Parallel

```bash
# Create tasks.json with your tasks
cat > tasks.json << EOF
[
  {
    "id": "task-1",
    "type": "service_creation",
    "subject": "Create auth-service",
    "prompt": "Create Spring Boot auth-service",
    "subagent_type": "spring-boot-microservices",
    "blockedBy": []
  },
  {
    "id": "task-2",
    "type": "service_creation",
    "subject": "Create user-service",
    "prompt": "Create Spring Boot user-service",
    "subagent_type": "spring-boot-microservices",
    "blockedBy": []
  }
]
EOF

# Analyze
python ~/.claude/memory/scripts/parallel-task-analyzer.py --tasks-file tasks.json

# Execute (within Python or using Task tool)
# This would be called automatically by the execution system
```

---

### Create Temporary Skill

```bash
python ~/.claude/memory/scripts/temp-skill-agent-creator.py create-skill \
  --name graphql-migration-expert \
  --description "Expert in migrating REST APIs to GraphQL" \
  --capabilities "Analyze REST endpoints" "Generate resolvers" "Add subscriptions"
```

**Output:**
```
✅ Created temporary skill: graphql-migration-expert
📁 Location: /home/user/.claude/skills/temp/graphql-migration-expert
📄 File: /home/user/.claude/skills/temp/graphql-migration-expert/skill.md
```

---

### List Temporary Resources

```bash
python ~/.claude/memory/scripts/temp-skill-agent-creator.py list
```

**Output:**
```
📋 TEMPORARY RESOURCES

🔧 Temporary Skills (2):

  • graphql-migration-expert
    Created: 2026-02-16T10:30:00
    Usage: 3 times
    Last Used: 2026-02-16T10:45:00

  • legacy-api-adapter
    Created: 2026-02-15T14:20:00
    Usage: 1 time
    Last Used: 2026-02-15T14:25:00

🤖 Temporary Agents (1):

  • k8s-deployment-orchestrator
    Created: 2026-02-16T09:00:00
    Usage: 2 times
    Last Used: 2026-02-16T11:30:00
```

---

### Cleanup Temporary Resources

```bash
# Dry run (see what would be deleted)
python ~/.claude/memory/scripts/temp-resource-manager.py cleanup --dry-run

# Actual cleanup
python ~/.claude/memory/scripts/temp-resource-manager.py cleanup
```

**Output:**
```
🗑️ TEMPORARY RESOURCE CLEANUP

🔧 Checking 2 temporary skill(s)...

  ✅ KEEP: graphql-migration-expert
     Reason: Used 3 times - shows value

  🗑️ DELETE: legacy-api-adapter
     Reason: One-time use, no recent activity

📊 CLEANUP SUMMARY:
   Deleted:  1
   Kept:     1
   Promoted: 0
```

---

### Promote Temporary Skill to Permanent

```bash
python ~/.claude/memory/scripts/temp-resource-manager.py promote --name graphql-migration-expert
```

**Output:**
```
✅ Promoted graphql-migration-expert to permanent skill
```

Now the skill moves from `~/.claude/skills/temp/` to `~/.claude/skills/`

---

## 🎯 COMMON SCENARIOS

### Scenario 1: Create Multiple Services

**Input:**
```
User: "Create auth-service, user-service, and product-service"
```

**What Happens:**
1. Task breakdown creates 3 independent tasks
2. Parallel detector: "3 tasks, no dependencies → Parallel!"
3. All 3 services created simultaneously
4. Results merged
5. Total time: ~5 minutes (vs 15 minutes)

---

### Scenario 2: Run Tests Across All Services

**Input:**
```
User: "Run tests in all microservices"
```

**What Happens:**
1. Task breakdown creates 1 task per service (5 services = 5 tasks)
2. Parallel detector: "5 tasks, no dependencies → Parallel!"
3. All tests run simultaneously
4. Results aggregated: "147 tests, 147 passed, 0 failed, 100% pass rate"
5. Total time: ~2 minutes (vs 10 minutes)

---

### Scenario 3: Specialized Task Needs Custom Skill

**Input:**
```
User: "Migrate all REST APIs to GraphQL"
```

**What Happens:**
1. Task breakdown creates migration tasks
2. Skill detector: "Need 'graphql-migration-expert' skill → Not found"
3. Auto-create temporary skill with GraphQL expertise
4. Use skill for all migration tasks (in parallel)
5. After completion: Usage count = 3 → Keep skill for future use

---

### Scenario 4: Git Operations Across Repos

**Input:**
```
User: "Push changes to all microservice repos"
```

**What Happens:**
1. Task breakdown creates 1 push task per repo (4 repos = 4 tasks)
2. Parallel detector: "4 tasks, independent repos → Parallel!"
3. All pushes happen simultaneously
4. Total time: ~3 seconds (vs 12 seconds)

---

## 📊 MONITORING

### Check Parallel Execution Stats

```bash
# View stats file
cat ~/.claude/memory/logs/parallel-execution-stats.json
```

**Output:**
```json
{
    "total_parallel_executions": 47,
    "total_tasks_parallelized": 183,
    "average_speedup": 3.2,
    "total_time_saved_minutes": 342,
    "temp_skills_created": 12,
    "temp_skills_kept": 5,
    "temp_agents_created": 8,
    "temp_agents_kept": 3,
    "merge_success_rate": 0.96,
    "failure_rate": 0.04
}
```

---

### View Recent Parallel Executions

```bash
tail -f ~/.claude/memory/logs/parallel-execution.log
```

---

## ⚙️ CONFIGURATION

**Location:** `~/.claude/memory/config/parallel-execution-config.json`

```json
{
    "enabled": true,
    "min_tasks_for_parallel": 3,
    "min_speedup_threshold": 1.5,
    "max_parallel_tasks": 10,
    "task_timeout_seconds": 600,
    "auto_create_temp_resources": true,
    "auto_cleanup_temp_resources": true,
    "temp_resource_retention_days": 30
}
```

**To disable parallel execution:**
```bash
echo '{"enabled": false}' > ~/.claude/memory/config/parallel-execution-config.json
```

**To increase max parallel tasks:**
```bash
# Edit config
vi ~/.claude/memory/config/parallel-execution-config.json

# Change "max_parallel_tasks": 10 to desired value
```

---

## 🚨 TROUBLESHOOTING

### Parallel Execution Not Triggering

**Check:**
1. At least 3 tasks created?
2. Tasks independent (no blockedBy dependencies)?
3. Estimated speedup >= 1.5x?
4. Parallel execution enabled in config?

**Debug:**
```bash
# Check config
cat ~/.claude/memory/config/parallel-execution-config.json

# Check task analysis
python ~/.claude/memory/scripts/parallel-task-analyzer.py --tasks-file tasks.json

# Check recommendation
python ~/.claude/memory/scripts/auto-parallel-detector.py --tasks-file tasks.json
```

---

### Temporary Resources Not Being Created

**Check:**
1. `auto_create_temp_resources: true` in config?
2. Required skill/agent actually doesn't exist?
3. Check logs: `~/.claude/memory/logs/parallel-execution.log`

---

### Results Not Merging Correctly

**Check:**
1. All parallel tasks completed successfully?
2. Result files present in `~/.claude/memory/temp/parallel-results/`?
3. Correct merge strategy selected?

**Debug:**
```bash
# Check result files
ls ~/.claude/memory/temp/parallel-results/

# Check merge strategy
cat ~/.claude/memory/config/parallel-execution-config.json | grep merge_strategies
```

---

## 📖 FURTHER READING

**Comprehensive Documentation:**
- `~/.claude/memory/03-execution-system/parallel-execution-policy.md` - Complete policy (45 KB)
- `~/.claude/memory/docs/parallel-execution-summary.md` - Implementation summary

**Related Policies:**
- `automatic-task-breakdown-policy.md` - Creates tasks for parallelization
- `auto-skill-agent-selection-policy.md` - Selects skills/agents
- `task-progress-tracking-policy.md` - Tracks parallel task progress

---

## 💡 TIPS & BEST PRACTICES

### ✅ DO:

1. **Let it work automatically** - System detects opportunities without your input
2. **Create clear, independent tasks** - Better parallelization
3. **Monitor speedup metrics** - See your time savings
4. **Review temporary resources** - Promote useful ones to permanent

### ❌ DON'T:

1. **Don't force parallelization** - Trust the auto-detector
2. **Don't create artificial dependencies** - Keep tasks independent
3. **Don't manually manage temp resources** - Auto-cleanup handles it
4. **Don't disable without reason** - You'll lose massive speedup

---

## 🎉 SUMMARY

**Parallel Execution System provides:**
- ✅ 3-10x faster execution
- ✅ Zero configuration required
- ✅ Automatic resource management
- ✅ Intelligent result merging
- ✅ Full integration with existing workflow

**Just use Claude Code normally, and watch your tasks complete in parallel!** 🚀

---

**VERSION:** 1.0.0
**LAST UPDATED:** 2026-02-16
**STATUS:** ✅ PRODUCTION READY
