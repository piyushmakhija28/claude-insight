# Java Agent Collaboration Strategy

**🚨 IMPORTANT: How to work WITH agents, not FORCE agents! 🚨**

## The Smart Approach

**DON'T:** Force agents to follow all standards (confuses them)
**DO:** Take agent's logic/ideas → Apply to OUR structure

## Workflow

```
1. User Request → 2. Use Agent → 3. Agent Provides Logic
                                          ↓
4. I (Claude) Take Output → 5. Apply to OUR Structure → 6. Final Implementation
```

## My Responsibilities (Claude)

When working with Java agents:
1. ✅ Extract Logic from agent
2. ✅ Apply Structure (our packages)
3. ✅ Add `ApiResponseDto<T>` wrapper
4. ✅ Separate DTO (response) vs Form (request)
5. ✅ Use Constants (no hardcoding)
6. ✅ Service Pattern: Interface → Impl (extends Helper)
7. ✅ Config: Use `${PLACEHOLDER}` for secrets

## Agent's Responsibilities

Agents provide:
- ✅ Business Logic
- ✅ Best Practices
- ✅ Error Handling
- ✅ Validation Rules
- ✅ Database Queries

## What Agents DON'T Need to Know

- ❌ Our package structure
- ❌ ApiResponseDto wrapper
- ❌ DTO vs Form distinction
- ❌ Constants package
- ❌ Service helper pattern
- ❌ Config server/Secret manager

## Code Generation Quality Check

Before submitting Java code:
- ❓ Is `ApiResponseDto<T>` used? (MUST be YES)
- ❓ Are DTOs and Forms separate? (MUST be YES)
- ❓ Are all messages in constants? (MUST be YES)
- ❓ Is service impl package-private? (MUST be YES)
- ❓ Does service impl extend helper? (MUST be YES)
- ❓ Is base package `com.techdeveloper.*`? (MUST be YES)
- ❓ Is ValidationSequence used? (MUST be YES)
- ❓ Are transactions used for writes? (MUST be YES)

**If ANY answer is NO → FIX before providing code!**

## Key Takeaway

**Agent = Brain (logic, best practices)**
**Me = Hands (structure, standards, implementation)**

**Together = Perfect Code! 🚀**
