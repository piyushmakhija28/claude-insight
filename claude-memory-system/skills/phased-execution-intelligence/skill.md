# Phased Execution Intelligence (System-Level Skill)

## Metadata
- **Skill Name**: phased-execution-intelligence
- **Version**: 1.0.0
- **Category**: System / Execution Strategy
- **Priority**: SYSTEM-LEVEL (Applied AFTER planning, BEFORE execution)
- **Status**: ALWAYS ACTIVE
- **Auto-invocation**: YES (automatic for large/complex tasks)

---

## Purpose

This skill **intelligently breaks down large tasks into manageable phases** with checkpoint-based execution. It prevents:
- ❌ Missing requirements in complex multi-part tasks
- ❌ Context overflow from trying to do everything in one session
- ❌ User frustration when large tasks fail midway
- ❌ Loss of progress when session ends prematurely

**Key Insight**: Large tasks need structured execution with clear checkpoints. One massive session = high risk of failure or missed details.

**Solution**: Break into phases → Execute phase → Checkpoint → Resume next phase

---

## Core Principle

**Large Task Execution Strategy**:
```
Small Task (< 3 parts):
└─ Execute directly in one session

Medium Task (3-5 parts):
└─ Phase breakdown optional (ask user)

Large Task (6+ parts):
└─ MANDATORY phase breakdown
    ├─ Phase 1 (foundational work)
    ├─ Phase 2 (core features)
    ├─ Phase 3 (integration/testing)
    └─ Use --resume between phases
```

**Checkpoint Formula**:
```
Phase Complete =
    All todos done +
    Working state verified +
    Summary created +
    Next phase plan ready

Then: User can --resume for next phase
```

---

## When This Skill Activates

### Trigger Points

**1. Large Prompt Detection (ALWAYS)**
- User request has 6+ distinct requirements
- User request spans multiple domains (auth + UI + DB + testing)
- User says keywords: "complete", "full", "entire", "end-to-end"
- Estimated work > 30 minutes or > 10 file changes

**2. Mid-Execution Scope Growth (CONDITIONAL)**
- Initial task small, but scope keeps expanding
- User adds "also do X, Y, Z" during execution
- Phase 1 reveals more work needed than estimated

**3. Explicit User Request**
- User says "break this into phases"
- User wants structured approach for large project

---

## Task Size Classification

### Scoring System (0-10 Scale)

```python
task_size_score = 0

# Factor 1: Number of Distinct Requirements (+0 to +3)
if requirements_count <= 2:
    task_size_score += 0
elif requirements_count <= 5:
    task_size_score += 1
elif requirements_count <= 8:
    task_size_score += 2
else:  # 9+ requirements
    task_size_score += 3

# Factor 2: Domain Span (+0 to +3)
domains = count_unique_domains(task)  # backend, frontend, DB, DevOps, testing
if domains == 1:
    task_size_score += 0
elif domains == 2:
    task_size_score += 1
elif domains == 3:
    task_size_score += 2
else:  # 4+ domains
    task_size_score += 3

# Factor 3: Estimated Effort (+0 to +2)
if estimated_files <= 3:
    task_size_score += 0
elif estimated_files <= 8:
    task_size_score += 1
else:  # 9+ files
    task_size_score += 2

# Factor 4: Dependencies (+0 to +2)
if dependencies == "independent parts":
    task_size_score += 0
elif dependencies == "some sequential":
    task_size_score += 1
else:  # complex dependency chain
    task_size_score += 2

# Total: 0-10
task_size_score = min(task_size_score, 10)
```

---

## Decision Matrix

| Task Size Score | Classification | Strategy |
|----------------|----------------|----------|
| 0-2 | Small | Execute directly (no phases) |
| 3-5 | Medium | Optional phases (ask user) |
| 6-10 | Large | **MANDATORY phased execution** |

---

## Phase Breakdown Strategy

### Step 1: Analyze Task Structure

```
User Request: "Build authentication system with JWT, OAuth, email verification, admin dashboard"

Analysis:
├─ Requirements: 4 major (JWT, OAuth, email, admin)
├─ Domains: 3 (backend auth, frontend UI, email service)
├─ Estimated files: 12+
├─ Dependencies: Sequential (auth → OAuth → admin)
Score: 8 → Large task → MANDATORY phases
```

### Step 2: Create Phase Plan

**Phase Breakdown Rules**:
1. **Foundation First**: Core infrastructure (DB, models, base auth)
2. **Core Features**: Main functionality (login, JWT, etc.)
3. **Extensions**: Additional features (OAuth, email)
4. **Polish**: Admin UI, testing, documentation

**Each Phase Should**:
- Have 2-5 major todos (not too many)
- Be completable in one focused session (30-60 min)
- Have clear success criteria
- Leave system in working state

### Step 3: Create Todos Per Phase

```markdown
## Phase 1: Core Authentication (Session 1)
- [ ] Setup JWT library & configuration
- [ ] Create User model & database schema
- [ ] Implement login/logout endpoints
- [ ] Add token generation & validation
- [ ] Test basic auth flow

Success Criteria: Can login and get valid JWT token

## Phase 2: OAuth Integration (Session 2 - resume)
- [ ] Setup OAuth providers (Google, GitHub)
- [ ] Create OAuth callback handlers
- [ ] Link OAuth accounts to users
- [ ] Test OAuth login flow

Success Criteria: Can login via Google/GitHub OAuth

## Phase 3: Email & Admin (Session 3 - resume)
- [ ] Setup email service
- [ ] Implement email verification flow
- [ ] Create admin dashboard UI
- [ ] Add user management endpoints
- [ ] Integration testing

Success Criteria: Full auth system working with email verification and admin panel
```

---

## Checkpoint Mechanism

### What is a Checkpoint?

A **checkpoint** is a verified stable state between phases where:
1. ✅ All phase todos completed
2. ✅ Code is working (tests pass, app runs)
3. ✅ Changes committed to git
4. ✅ Summary of what was done
5. ✅ Clear next steps documented

### Checkpoint Creation Process

```markdown
End of Phase 1:

1. **Verify Completion**
   - Check all todos: ✓ Done
   - Run tests: ✓ Passing
   - Run app: ✓ Working

2. **Commit State**
   git add .
   git commit -m "Phase 1 complete: Core authentication with JWT"

3. **Create Summary**
   ## Phase 1 Summary (COMPLETED)

   What was done:
   - JWT setup with secret key configuration
   - User model with bcrypt password hashing
   - Login/logout endpoints (POST /login, /logout)
   - Token validation middleware

   Files changed: 5
   - src/models/User.js
   - src/routes/auth.js
   - src/middleware/authMiddleware.js
   - src/config/jwt.js
   - tests/auth.test.js

   Status: ✅ Working - Can login and receive JWT token

   Next Phase: OAuth Integration (Google, GitHub)

4. **Inform User**
   "Phase 1 complete! ✅

   You can now login and receive JWT tokens. The authentication foundation is working.

   To continue with Phase 2 (OAuth integration), use:
   claude --resume

   Or take a break and resume later. Your progress is saved."
```

---

## Resume Workflow

### How --resume Works

```
Session 1:
└─ Phase 1 execution → Checkpoint created

User runs: claude --resume

Session 2 (resumed):
├─ Load Phase 1 summary
├─ Verify checkpoint state (git status, tests)
├─ Start Phase 2 execution
└─ Complete Phase 2 → New checkpoint

User runs: claude --resume

Session 3 (resumed):
├─ Load Phase 2 summary
├─ Start Phase 3 execution
└─ Complete → Final summary
```

### Resume Context Loading

When user resumes, provide:
```markdown
## Resuming from Checkpoint

**Previous Phase**: Phase 1 - Core Authentication
**Status**: ✅ Completed
**Summary**: Implemented JWT-based auth with login/logout

**Current Phase**: Phase 2 - OAuth Integration
**Goal**: Add Google and GitHub OAuth login

**Todos for this phase**:
- [ ] Setup OAuth providers config
- [ ] Create OAuth callback routes
- [ ] Link OAuth to user accounts
- [ ] Test OAuth flow

Let's continue! Starting with OAuth provider setup...
```

---

## Integration with Existing Skills

### Execution Flow (Updated)

```
User Request
    ↓
1. context-management-core (validate context)
    ↓
2. model-selection-core (select model)
    ↓
3. task-planning-intelligence (plan vs direct?)
    ↓
    If planning needed → Plan mode
    ↓
4. phased-execution-intelligence (NEW!)
    ↓
    Calculate task size score (0-10)
    ↓
    ├─ Score 0-2: Execute directly (no phases)
    ├─ Score 3-5: Ask user about phases
    └─ Score 6-10: MANDATORY phase breakdown
         ↓
         Create phase plan
         ↓
         Create todos for Phase 1
         ↓
5. common-failures-prevention (before each tool)
    ↓
6. Execute Phase 1
    ↓
7. Phase complete?
    ├─ Yes → Create checkpoint → Inform user to --resume
    └─ No → Continue execution
    ↓
8. User runs --resume
    ↓
9. Load checkpoint → Execute next phase
```

---

## Decision Logic Examples

### Example 1: Small Task (Score = 2)
```
User: "Add a logout button to the navbar"

Analysis:
- Requirements: 1 (add button)
- Domains: 1 (frontend)
- Files: 2 (component, handler)
- Dependencies: None

Score: 2 → Small task
Decision: Execute directly (no phases needed)
Action: Just implement it
```

### Example 2: Medium Task (Score = 4)
```
User: "Add user profile page with edit capability"

Analysis:
- Requirements: 3 (profile view, edit form, save)
- Domains: 2 (frontend UI, backend API)
- Files: 5 (component, route, API, validation)
- Dependencies: Some (UI depends on API)

Score: 4 → Medium task
Decision: Ask user preference
Action: "I can do this in one go or break into 2 phases (backend API, then frontend). Prefer one session or phased?"
```

### Example 3: Large Task (Score = 8)
```
User: "Build complete authentication system with JWT, OAuth (Google, GitHub), email verification, password reset, and admin dashboard"

Analysis:
- Requirements: 6 major features
- Domains: 4 (backend, frontend, email, OAuth)
- Files: 15+
- Dependencies: Complex (auth → OAuth → admin)

Score: 8 → Large task
Decision: MANDATORY phased execution
Action: Create 3-4 phase plan with checkpoints
```

---

## Phase Design Patterns

### Pattern 1: Linear Phases (Sequential Dependencies)

```
Use when: Each phase builds on previous

Phase 1: Foundation
├─ Database setup
├─ Models
└─ Basic CRUD

Phase 2: Core Features
├─ Business logic
├─ API endpoints
└─ Validation

Phase 3: Advanced Features
├─ Complex operations
├─ Integration
└─ Testing

Example: E-commerce (products → cart → checkout)
```

### Pattern 2: Parallel Phases (Independent Components)

```
Use when: Parts can be done independently

Phase 1: Backend API
├─ Routes
├─ Controllers
└─ Database

Phase 2: Frontend UI (can resume independently)
├─ Components
├─ State management
└─ API integration

Example: Blog system (API can work alone, UI can work alone)
```

### Pattern 3: Vertical Slice Phases

```
Use when: Building feature by feature

Phase 1: User Management (complete vertical slice)
├─ User model
├─ User API
├─ User UI
└─ User tests

Phase 2: Post Management (complete vertical slice)
├─ Post model
├─ Post API
├─ Post UI
└─ Post tests

Example: Social media app (features can be added incrementally)
```

---

## Parallel Multi-Agent Execution (Advanced)

### Core Concept

When phases are **independent** (no dependencies between them), execute them **in parallel** using multiple agents instead of sequentially.

**Sequential Execution** (Traditional):
```
Phase 1: Backend API (30 min) → Complete
Wait for Phase 1...
Phase 2: Frontend UI (30 min) → Complete
Total: 60 minutes
```

**Parallel Execution** (Multi-Agent):
```
Phase 1: Backend API (Agent 1) } Both running
Phase 2: Frontend UI (Agent 2) } simultaneously
Total: 30 minutes (50% faster!)

Then: Sync point to integrate both
```

### Dependency Detection

Before deciding parallel vs sequential, analyze dependencies:

```python
def detect_dependencies(phases):
    dependencies = {}

    for phase in phases:
        # Check if phase uses output from other phases
        depends_on = []

        if phase.uses_files_from(other_phases):
            depends_on.append(other_phases)
        if phase.requires_output_from(other_phases):
            depends_on.append(other_phases)
        if phase.integrates_with(other_phases):
            depends_on.append(other_phases)

        dependencies[phase] = depends_on

    return dependencies

# Decision
if all_independent(dependencies):
    strategy = "PARALLEL"
elif some_independent(dependencies):
    strategy = "MIXED" # Some parallel, some sequential
else:
    strategy = "SEQUENTIAL"
```

### Dependency Analysis Matrix

| Phase A | Phase B | Dependency Type | Strategy |
|---------|---------|----------------|----------|
| Backend API | Frontend UI | None (API contract defined) | **PARALLEL** ✓ |
| Database Schema | API Endpoints | Strong (API needs schema) | **SEQUENTIAL** |
| User Auth | Post Management | Weak (shared user model) | **SEQUENTIAL** (safer) |
| Email Service | OAuth Service | None (independent services) | **PARALLEL** ✓ |
| Core Features | Testing | Strong (tests need features) | **SEQUENTIAL** |
| Documentation | Implementation | None (can write docs from spec) | **PARALLEL** ✓ |

### When to Use Parallel Agents

✅ **Use Parallel When**:
- Phases work on different domains (backend vs frontend)
- Phases work on different modules (auth service vs payment service)
- Clear interface/contract defined between phases
- No shared file modifications
- Each phase can be tested independently

❌ **Don't Use Parallel When**:
- Phase B needs output from Phase A
- Both phases modify same files (merge conflicts!)
- Integration complexity high
- User wants to review Phase A before Phase B starts
- Debugging would be harder with parallel execution

### Multi-Agent Orchestration Pattern

```markdown
Step 1: Analyze Task
User: "Build e-commerce with product catalog (backend + frontend)"

Analysis:
- Phase 1: Product API (backend)
- Phase 2: Product UI (frontend)
- Dependencies: None (API contract can be defined upfront)
- Strategy: PARALLEL

Step 2: Define Interface Contract
Before spawning agents, define contract:

API Contract:
- GET /api/products → [{id, name, price, image}]
- POST /api/products → {success, productId}
- GET /api/products/:id → {id, name, price, image, description}

Both agents work to this contract.

Step 3: Spawn Parallel Agents
"I'll execute these phases in parallel using multi-agent execution:

**Agent 1 (Backend)**:
- Setup Express API
- Product model & routes
- Database integration
- API tests

**Agent 2 (Frontend)**:
- React components
- API client (using contract)
- UI state management
- UI tests

Both agents will work simultaneously. I'll sync when both complete."

[Launch both agents in parallel]

Step 4: Monitor Progress
- Agent 1 status: In progress...
- Agent 2 status: In progress...

Step 5: Sync Point (Both Complete)
"Both phases complete! ✅

Agent 1: Backend API working
Agent 2: Frontend UI working

Now integrating both..."

Step 6: Integration Phase
- Connect Frontend to real Backend
- Integration testing
- Resolve any contract mismatches
```

### Parallel Execution Examples

#### Example 1: Full Stack App (Backend || Frontend)

```yaml
Task: "Build blog with posts API and UI"

Sequential Approach:
  Phase 1: Backend API (Agent 1)
    Duration: 30 min
    Wait...
  Phase 2: Frontend UI (Agent 2)
    Duration: 30 min
  Total: 60 min

Parallel Approach:
  Define API Contract First: 5 min

  Phase 1 (Agent 1): Backend API  }
  Phase 2 (Agent 2): Frontend UI  } Run parallel
  Duration: 30 min each            }

  Phase 3: Integration (Agent 3 or main)
    Duration: 10 min

  Total: 45 min (25% faster!)

Command:
"I'll use parallel multi-agent execution:
- Agent 1: Backend (spring-boot-microservices)
- Agent 2: Frontend (angular-engineer)
Both will work to this API contract: [contract]

Spawning agents in parallel..."

[Task tool called with run_in_background for both agents]
```

#### Example 2: Microservices (Service A || Service B || Service C)

```yaml
Task: "Build 3 microservices: Auth, Products, Orders"

Sequential: 3 × 30 min = 90 min

Parallel (3 agents):
  Define service contracts first: 10 min

  Agent 1: Auth Service      }
  Agent 2: Products Service  } All parallel
  Agent 3: Orders Service    }
  Duration: 30 min each      }

  Integration: 15 min
  Total: 55 min (40% faster!)

Strategy:
- Each service has defined API contract
- Services communicate via REST/gRPC
- Each can be developed independently
- Integration phase connects them
```

#### Example 3: Mixed Dependencies (Some Parallel, Some Sequential)

```yaml
Task: "Build auth system: Database → (Backend API || Frontend UI) → Testing"

Phase 1: Database Schema (Sequential - foundation)
  Duration: 15 min
  Agent: Main
  ↓
Phase 2 & 3: Parallel (both depend on Phase 1)
  Agent 1: Backend API  }
  Agent 2: Frontend UI  } Parallel
  Duration: 30 min      }
  ↓
Phase 4: Integration Testing (Sequential - needs both)
  Duration: 10 min
  Agent: Main

Total: 55 min
vs Sequential: 85 min (35% faster!)

Decision Logic:
- Phase 1: No dependencies → Start
- Phase 2 & 3: Both depend ONLY on Phase 1 → Parallel after Phase 1
- Phase 4: Depends on 2 & 3 → Wait for both
```

### Implementation with Task Tool

```markdown
Spawning Parallel Agents:

# Sequential (Old Way)
Task(subagent_type="spring-boot-microservices",
     prompt="Build product API")
→ Wait for completion...

Task(subagent_type="angular-engineer",
     prompt="Build product UI")
→ Wait for completion...

# Parallel (New Way)
Send SINGLE message with MULTIPLE Task calls:

Message with tools:
[
  Task(subagent_type="spring-boot-microservices",
       prompt="Build product API following contract: [contract]",
       description="Backend API development"),

  Task(subagent_type="angular-engineer",
       prompt="Build product UI following contract: [contract]",
       description="Frontend UI development")
]

Both agents execute simultaneously!

Monitor:
- Check TaskOutput for both agents
- Wait for both to complete
- Proceed to integration
```

### Sync Points & Integration

**Sync Point**: When parallel agents complete, merge their work.

```markdown
Phase 1: Backend (Agent 1) → Complete ✓
Phase 2: Frontend (Agent 2) → Complete ✓

Sync Point Activities:
1. **Review Both Outputs**
   - Backend: API endpoints working?
   - Frontend: UI components ready?

2. **Verify Contract Compliance**
   - Does Backend API match contract?
   - Does Frontend expect correct endpoints?

3. **Resolve Conflicts**
   - Did agents modify same config files? → Merge manually
   - Any mismatched assumptions? → Align both

4. **Integration**
   - Connect Frontend to Backend
   - Update API URLs
   - Test end-to-end flow

5. **Create Checkpoint**
   - Commit merged work
   - Summary: "Backend + Frontend integrated"
   - Next: Testing or next phase
```

---

## Context Handoff Mechanism (Critical for Same-Domain Multi-Phase)

### The Problem

When splitting **same-domain** large tasks into multiple phases using multiple agents:

```yaml
Problem Scenario:
  Task: "Build large React e-commerce frontend"
  Split into phases:
    Phase 1 (Agent 1): Product Listing
      - Creates ProductState interface
      - Creates ProductCard component
      - Defines product type structure

    Phase 2 (Agent 2): Shopping Cart
      - Needs ProductState (from Phase 1!)
      - Needs product types (from Phase 1!)
      - Needs ProductCard reference (from Phase 1!)

  Issue:
    Agent 2 has NO CONTEXT from Phase 1
    ↓
    Agent 2 creates duplicate/inconsistent ProductState
    ↓
    Integration nightmare: Mismatched types, duplicate components
```

**Without Context Handoff**:
❌ Duplicate type definitions (Product defined twice, differently)
❌ Inconsistent interfaces (ProductState vs CartProductState)
❌ Redundant components (ProductCard recreated in Phase 2)
❌ Integration hell (Phase 1 + Phase 2 don't align)

**With Context Handoff**:
✅ Shared artifacts extracted from Phase 1
✅ Phase 2 agent receives artifacts as context
✅ No duplication, consistent structures
✅ Clean integration (both use same types)

### Core Concept

**Context Artifacts** = Reusable outputs from Phase 1 that Phase 2 needs

Types of artifacts:
1. **Type Definitions**: Interfaces, types, enums
2. **Shared Components**: Reusable UI components
3. **State Structures**: Redux slices, context providers
4. **Utility Functions**: Helpers, formatters, validators
5. **Style Tokens**: Theme variables, CSS constants
6. **API Contracts**: Request/response shapes
7. **Constants**: Config values, error messages

### Context Handoff Process

```markdown
Step 1: Phase 1 Execution (Agent 1)
  - Build Product Listing feature
  - Complete all Phase 1 todos
  - Tests pass
  ↓

Step 2: Extract Context Artifacts (Main Agent)
  Identify what Phase 2 will need:
  ✓ Types: Product, ProductState
  ✓ Components: ProductCard, ProductImage
  ✓ Utils: formatPrice, validateProduct
  ✓ Constants: PRODUCTS_API_URL, MAX_PRODUCTS
  ↓

Step 3: Create Artifact Summary
  ```typescript
  // Shared Artifacts from Phase 1

  // Types
  interface Product {
    id: string;
    name: string;
    price: number;
    image: string;
  }

  interface ProductState {
    items: Product[];
    loading: boolean;
    error: string | null;
  }

  // Components
  ProductCard: (props: {product: Product}) => JSX.Element
    Location: src/components/ProductCard.tsx
    Usage: <ProductCard product={product} />

  // Utils
  formatPrice: (price: number) => string
    Location: src/utils/formatPrice.ts
    Usage: formatPrice(19.99) → "$19.99"

  // Constants
  PRODUCTS_API_URL = "/api/products"
  ```
  ↓

Step 4: Phase 2 Execution (Agent 2 with Context)
  Prompt includes:
  "Build shopping cart feature.

  **IMPORTANT: Use existing artifacts from Phase 1**:
  [Paste artifact summary]

  Requirements:
  - Reuse Product type (don't redefine)
  - Import ProductCard component (don't recreate)
  - Use formatPrice utility
  - Follow same patterns as Phase 1"
  ↓

Step 5: Phase 2 Implementation
  Agent 2 now:
  ✓ Imports Product type (no duplication)
  ✓ Uses ProductCard component (consistent UI)
  ✓ Uses formatPrice (consistent formatting)
  ✓ Extends ProductState if needed (aligned structure)
  ↓

Step 6: Integration
  Phase 1 + Phase 2 seamlessly integrate
  No type conflicts, no duplicate code
```

### Artifact Extraction Strategy

#### What to Extract (Checklist)

```markdown
After Phase 1 completes, extract:

✓ **Type Definitions**
  - All interfaces, types, enums
  - Especially shared data structures
  - Location in codebase
  - Usage examples

✓ **Shared Components**
  - Reusable UI components
  - Component props signature
  - Import path
  - Usage pattern

✓ **State Management**
  - Redux slices/reducers
  - Context providers
  - State shape
  - Actions/mutations

✓ **Utility Functions**
  - Pure functions used across features
  - Input/output signature
  - Import path
  - Examples

✓ **Constants/Config**
  - API endpoints
  - Environment variables
  - Magic numbers/strings
  - Feature flags

✓ **Styling**
  - Theme tokens
  - CSS variables
  - Shared styles
  - Design system components

✓ **Patterns**
  - Code patterns established
  - Naming conventions
  - File structure
  - Architecture decisions
```

### Example: Frontend E-Commerce (Same Domain, Multi-Phase)

#### Scenario
```yaml
Task: "Build large React e-commerce frontend with product listing, cart, checkout"
Domain: Frontend only (React)
Size: Large (score 8)
Strategy: Multi-phase, sequential (Phase 1 → Phase 2 → Phase 3)
```

#### Phase 1: Product Listing (Agent 1)

```typescript
// Agent 1 creates:

// types/product.ts
export interface Product {
  id: string;
  name: string;
  price: number;
  image: string;
  description: string;
}

// state/productSlice.ts
export interface ProductState {
  items: Product[];
  loading: boolean;
  error: string | null;
}

// components/ProductCard.tsx
export const ProductCard: React.FC<{product: Product}> = ({product}) => {
  return (
    <div className="product-card">
      <img src={product.image} />
      <h3>{product.name}</h3>
      <p>{formatPrice(product.price)}</p>
    </div>
  );
};

// utils/formatPrice.ts
export const formatPrice = (price: number): string => {
  return `$${price.toFixed(2)}`;
};

// constants/api.ts
export const PRODUCTS_API = '/api/products';
```

#### Phase 1 Complete → Extract Artifacts

```markdown
## Phase 1 Artifacts (Product Listing Complete)

### Types (MUST REUSE)
Location: `src/types/product.ts`
```typescript
interface Product {
  id: string;
  name: string;
  price: number;
  image: string;
  description: string;
}

interface ProductState {
  items: Product[];
  loading: boolean;
  error: string | null;
}
```

### Components (MUST REUSE)
**ProductCard**
- Location: `src/components/ProductCard.tsx`
- Props: `{product: Product}`
- Usage: `<ProductCard product={product} />`

### Utils (MUST REUSE)
**formatPrice**
- Location: `src/utils/formatPrice.ts`
- Signature: `(price: number) => string`
- Example: `formatPrice(19.99)` → `"$19.99"`

### Constants (MUST USE)
- `PRODUCTS_API = '/api/products'` (src/constants/api.ts)

### Patterns Established
- State management: Redux Toolkit
- Component structure: Functional components with TypeScript
- Styling: CSS modules
- API calls: axios with async thunks

**CRITICAL**: Phase 2 MUST import these, NOT recreate them!
```

#### Phase 2: Shopping Cart (Agent 2 with Context)

**Prompt to Agent 2**:
```markdown
Build shopping cart feature for e-commerce app.

**CRITICAL: Use existing artifacts from Phase 1**

Phase 1 created these (DO NOT RECREATE):

1. **Product Type** (import from src/types/product.ts):
   ```typescript
   interface Product {
     id: string;
     name: string;
     price: number;
     image: string;
     description: string;
   }
   ```

2. **ProductCard Component** (import from src/components/ProductCard.tsx):
   - Shows product with image, name, price
   - Props: {product: Product}
   - Usage: <ProductCard product={product} />

3. **formatPrice Utility** (import from src/utils/formatPrice.ts):
   - Formats number to currency string
   - Usage: formatPrice(19.99) → "$19.99"

**Your Task**:
Build cart feature that:
- Uses Product type (import it!)
- Displays cart items with ProductCard (reuse it!)
- Shows total using formatPrice (reuse it!)
- New: Add CartItem type extending Product with quantity
- New: CartState for cart management
- New: Add to cart / remove from cart actions

**Requirements**:
✓ Import Product from src/types/product.ts
✓ Import ProductCard from src/components/ProductCard.tsx
✓ Import formatPrice from src/utils/formatPrice.ts
✓ Follow Redux Toolkit pattern (like Phase 1)
✓ Use CSS modules for styling (like Phase 1)
✓ Extend, don't duplicate!
```

**Agent 2 Result**:
```typescript
// ✅ Imports from Phase 1 (no duplication!)
import { Product } from '../types/product';
import { ProductCard } from '../components/ProductCard';
import { formatPrice } from '../utils/formatPrice';

// ✅ Extends Phase 1 types (aligned!)
export interface CartItem extends Product {
  quantity: number;
}

export interface CartState {
  items: CartItem[];
  total: number;
}

// ✅ Reuses Phase 1 components
export const CartItemView: React.FC<{item: CartItem}> = ({item}) => {
  return (
    <div className="cart-item">
      <ProductCard product={item} />
      <div className="quantity">Qty: {item.quantity}</div>
      <div className="subtotal">{formatPrice(item.price * item.quantity)}</div>
    </div>
  );
};

// ✅ Consistent patterns with Phase 1
// Redux slice, async thunks, CSS modules all match Phase 1 style
```

### Same-Domain vs Cross-Domain

| Aspect | Same-Domain (Frontend-only) | Cross-Domain (Backend + Frontend) |
|--------|---------------------------|----------------------------------|
| **Context Handoff** | CRITICAL (must share types/components) | OPTIONAL (just share API contract) |
| **Artifacts** | Types, components, utils, state | API contract only |
| **Risk if missed** | HIGH (duplicates, conflicts) | LOW (separate codebases) |
| **Example** | React app phases | Backend API + Frontend UI |

**When Context Handoff is CRITICAL**:
- ✅ Frontend split into phases (Phase 1 → Phase 2 → Phase 3)
- ✅ Backend split into phases (Service layers → Controllers → etc)
- ✅ Mobile app split into phases (Screens → Features → etc)
- ❌ Backend + Frontend parallel (separate codebases)
- ❌ Independent microservices (no shared code)

### Artifact Template

```markdown
## Context Artifacts from Phase [N]

### 1. Types & Interfaces
**Location**: `[path]`
```typescript
[Paste type definitions]
```

### 2. Shared Components
**[ComponentName]**
- Location: `[path]`
- Props: `[signature]`
- Usage: `[example]`

**[ComponentName2]**
- ...

### 3. Utilities
**[functionName]**
- Location: `[path]`
- Signature: `[type signature]`
- Example: `[usage example]`

### 4. State Management
**[SliceName]**
- Location: `[path]`
- State shape: `[interface]`
- Actions: `[list]`

### 5. Constants
- `[CONSTANT_NAME] = [value]` ([path])
- ...

### 6. Patterns to Follow
- [Pattern 1]
- [Pattern 2]
- ...

### 7. CRITICAL RULES
- ❌ DO NOT recreate types listed above
- ❌ DO NOT duplicate components
- ✅ ALWAYS import from locations specified
- ✅ EXTEND existing types if needed
- ✅ FOLLOW established patterns
```

### Implementation in Checkpoint

```markdown
End of Phase 1:

1. **Complete Phase 1 Work** ✓

2. **Extract Context Artifacts**
   - Review Phase 1 code
   - Identify reusable pieces
   - Document types, components, utils
   - Create artifact summary

3. **Git Commit with Artifacts**
   ```
   git commit -m "Phase 1 complete: Product Listing

   Created:
   - Product type (src/types/product.ts)
   - ProductCard component (src/components/ProductCard.tsx)
   - formatPrice utility (src/utils/formatPrice.ts)
   - ProductState (src/state/productSlice.ts)

   Artifacts for Phase 2:
   - See PHASE1_ARTIFACTS.md for reusable code
   - Phase 2 MUST import these, not recreate
   "
   ```

4. **Create PHASE1_ARTIFACTS.md**
   - Detailed artifact documentation
   - Import examples
   - Usage guidelines
   - Critical rules

5. **Inform User**
   "Phase 1 complete! ✅

   Created reusable artifacts:
   - Product types
   - ProductCard component
   - formatPrice utility

   Phase 2 will build on these (no duplication).

   To continue: claude --resume"

6. **When Phase 2 Starts (--resume)**
   Load artifacts into Phase 2 agent context:
   - Read PHASE1_ARTIFACTS.md
   - Include in Phase 2 agent prompt
   - Ensure Phase 2 imports, doesn't recreate
```

### Validation at Sync Point

```markdown
After Phase 2 completes:

✓ **Verify No Duplication**
  grep -r "interface Product" src/
  → Should find only ONE definition (Phase 1)

✓ **Verify Imports**
  grep -r "import.*Product.*from" src/
  → Phase 2 files should import from Phase 1 location

✓ **Verify Consistency**
  - Product type same in both phases?
  - formatPrice used consistently?
  - Components follow same patterns?

✓ **Integration Test**
  - Phase 1 + Phase 2 work together?
  - No type conflicts?
  - Shared components render correctly?
```

### Common Pitfalls & Solutions

#### Pitfall 1: Agent Recreates Types

```typescript
❌ BAD (Phase 2 agent recreates):
// Phase 2 creates ANOTHER Product type!
interface Product {
  id: number;  // Different! Phase 1 used string
  title: string;  // Different! Phase 1 used name
  cost: number;  // Different! Phase 1 used price
}

✅ GOOD (Phase 2 agent imports):
import { Product } from '../types/product';
// Uses Phase 1's Product type, no conflict!
```

**Solution**: Clear artifact documentation + explicit instructions to import

#### Pitfall 2: Inconsistent Patterns

```typescript
❌ BAD (Phase 2 uses different state pattern):
// Phase 1 used Redux Toolkit
// Phase 2 uses useState hooks
// → Inconsistent state management!

✅ GOOD (Phase 2 follows Phase 1 pattern):
// Phase 2 also uses Redux Toolkit
// Consistent with Phase 1
```

**Solution**: Document "Patterns Established" in artifacts

#### Pitfall 3: Missed Utilities

```typescript
❌ BAD (Phase 2 rewrites utility):
// Phase 2 creates formatCurrency (duplicate of formatPrice!)
const formatCurrency = (n) => `$${n.toFixed(2)}`;

✅ GOOD (Phase 2 imports utility):
import { formatPrice } from '../utils/formatPrice';
```

**Solution**: Explicitly list all utilities in artifacts

### Communication Template

```markdown
Template: Phase N Complete with Artifacts

"✅ Phase [N] Complete: [Feature Name]

**Artifacts Created** (for Phase [N+1]):

Types:
- `[TypeName]` (src/types/[file])

Components:
- `[ComponentName]` (src/components/[file])

Utils:
- `[functionName]` (src/utils/[file])

Constants:
- `[CONSTANT]` = [value]

**Phase [N+1] Requirements**:
❌ DO NOT recreate these types/components
✅ MUST import from locations above
✅ EXTEND if needed, don't duplicate

Artifact details saved in: PHASE[N]_ARTIFACTS.md

To continue with Phase [N+1]:
```bash
claude --resume
```

I'll load these artifacts into Phase [N+1] context automatically."
```

---

## Merge & Integration Strategy (Critical for Parallel Execution)

### The Merge Problem

When multiple agents work in parallel, their outputs need to be **merged** into a cohesive whole:

```yaml
Problem Scenario:
  Agent 1 (Backend): ✅ Complete → Works in isolation
  Agent 2 (Frontend): ✅ Complete → Works in isolation
  Agent 3 (Tests): ✅ Complete → Works in isolation

  But:
    ❌ How to merge all three?
    ❌ Git conflicts possible?
    ❌ Does integration work?
    ❌ How to create final checkpoint?
```

**Without Merge Strategy**:
❌ Manual merge confusion
❌ Git conflicts unresolved
❌ Integration failures
❌ No clear final state

**With Merge Strategy**:
✅ Orchestrated merge sequence
✅ Automated conflict detection
✅ Integration testing enforced
✅ Clean final checkpoint

### Core Merge Principle

**Sequential Merge Order** (Even for Parallel Work):
```
Agents work in parallel → All complete → Merge sequentially with validation

Why sequential merge?
- Easier conflict resolution (one at a time)
- Clear integration testing (incremental)
- Rollback simpler if issues found
- Git history cleaner
```

### Branch Management Strategy

#### Option 1: Feature Branches (Recommended)

```bash
# Setup
main branch (clean starting point)

# Agent 1 starts
git checkout -b phase-1-backend
[Agent 1 works...]
git commit -m "Backend API complete"

# Agent 2 starts (from main)
git checkout main
git checkout -b phase-2-frontend
[Agent 2 works...]
git commit -m "Frontend UI complete"

# Agent 3 starts (from main)
git checkout main
git checkout -b phase-3-tests
[Agent 3 works...]
git commit -m "Tests complete"

# All agents complete → Now merge sequentially
```

#### Option 2: Main Branch with Careful Coordination

```bash
# All agents work on main but different files
# Requires careful file conflict management
# Less safe, but simpler for small teams
```

**Recommendation**: Use **Option 1 (Feature Branches)** for parallel agents

### Merge Orchestration Process

```markdown
Step 1: All Agents Complete
  Agent 1 (Backend): ✅ Complete on branch phase-1-backend
  Agent 2 (Frontend): ✅ Complete on branch phase-2-frontend
  Agent 3 (Tests): ✅ Complete on branch phase-3-tests
  ↓

Step 2: Determine Merge Order
  Priority-based ordering:
  1. Foundation first (Backend API)
  2. Dependents next (Frontend, needs API)
  3. Validation last (Tests, needs both)

  Merge order: Backend → Frontend → Tests
  ↓

Step 3: Merge Agent 1 (Backend)
  git checkout main
  git merge phase-1-backend --no-ff

  Validation:
  - No conflicts (should be clean, first merge)
  - Run backend tests
  - Backend API working standalone?

  If valid: ✓ Proceed
  If issues: ✗ Fix before continuing
  ↓

Step 4: Merge Agent 2 (Frontend)
  git merge phase-2-frontend --no-ff

  Check for conflicts:
  - Config files (package.json, .env)?
  - Shared utilities?
  - Documentation?

  Resolve conflicts:
  - Keep both if possible
  - Merge intelligently
  - Test after resolution

  Validation:
  - Run frontend tests
  - Run backend tests (ensure no regression)
  - Integration test: Frontend → Backend
  - Does UI connect to API correctly?

  If valid: ✓ Proceed
  If issues: ✗ Fix before continuing
  ↓

Step 5: Merge Agent 3 (Tests)
  git merge phase-3-tests --no-ff

  Validation:
  - Run ALL tests (unit + integration + e2e)
  - Tests pass on merged codebase?
  - Coverage acceptable?

  If valid: ✓ Proceed
  If issues: ✗ Fix tests or code
  ↓

Step 6: Final Integration Validation
  Complete test suite:
  ✓ Unit tests (all modules)
  ✓ Integration tests (API + UI)
  ✓ E2E tests (full workflows)
  ✓ Manual smoke test

  Code quality:
  ✓ Linting passes
  ✓ Build succeeds
  ✓ No console errors

  If all pass: ✓ Create final checkpoint
  If any fail: ✗ Debug and fix
  ↓

Step 7: Final Checkpoint
  git commit -m "All phases integrated and tested

  Merged:
  - Phase 1: Backend API (phase-1-backend)
  - Phase 2: Frontend UI (phase-2-frontend)
  - Phase 3: Tests (phase-3-tests)

  Integration validated:
  ✓ All tests passing
  ✓ Backend + Frontend working together
  ✓ E2E workflows functioning

  Ready for deployment/next phase."
  ↓

Step 8: Cleanup Branches (Optional)
  git branch -d phase-1-backend
  git branch -d phase-2-frontend
  git branch -d phase-3-tests

  Branches merged and deleted, main branch clean
```

### Conflict Resolution Patterns

#### Common Conflict Scenarios

**Conflict 1: Config Files (package.json, .env)**

```json
// Agent 1 added:
{
  "dependencies": {
    "express": "^4.18.0"
  }
}

// Agent 2 added:
{
  "dependencies": {
    "react": "^18.2.0"
  }
}

// Conflict on merge!

✅ Resolution:
{
  "dependencies": {
    "express": "^4.18.0",  // Keep both
    "react": "^18.2.0"     // Keep both
  }
}

Then: npm install (validate dependencies work together)
```

**Conflict 2: Shared Utilities**

```typescript
// Agent 1 created:
// utils/api.ts
export const API_URL = 'http://localhost:3000';

// Agent 2 created:
// utils/api.ts (different content!)
export const fetchData = async (url) => {...};

// Conflict!

✅ Resolution:
// Merge both into same file
export const API_URL = 'http://localhost:3000';
export const fetchData = async (url) => {...};

Then: Test both agents' code still works
```

**Conflict 3: Documentation (README.md)**

```markdown
Agent 1 added:
## Backend API
...

Agent 2 added:
## Frontend Setup
...

Both modified same README section!

✅ Resolution:
## Backend API
[Agent 1 content]

## Frontend Setup
[Agent 2 content]

Merge both sections, organize logically
```

### Conflict Resolution Decision Tree

```
Git conflict detected
    ↓
Are changes in same logical area?
  ├─ No (different sections)
  │  └─ Keep both → Merge intelligently
  │     Example: Different dependencies, different README sections
  │
  └─ Yes (same area, conflicting)
      ↓
      Can both be kept?
      ├─ Yes → Merge values
      │  Example: Config with different keys
      │
      └─ No → Choose one or create hybrid
          ↓
          Which is correct?
          ├─ Agent 1 correct → Keep Agent 1
          ├─ Agent 2 correct → Keep Agent 2
          └─ Both needed → Create hybrid solution
              ↓
              After resolution:
              1. Test affected code
              2. Validate both agents' work still functions
              3. Document resolution in commit message
```

### Integration Testing Workflow

After each merge, run integration tests:

```bash
# After merging Agent 1 (Backend)
npm run test:backend
npm run start:backend  # Verify server starts
curl http://localhost:3000/health  # Health check

# After merging Agent 2 (Frontend)
npm run test:frontend
npm run test:backend  # Ensure no regression
npm run test:integration  # Frontend → Backend
npm run start  # Verify both start together

# After merging Agent 3 (Tests)
npm run test:all  # All tests
npm run test:e2e  # End-to-end
npm run lint  # Code quality
npm run build  # Production build
```

### Validation Checklist

```markdown
Before declaring merge complete:

✓ **Git State**
  - All branches merged cleanly
  - No unresolved conflicts
  - Commit history clear

✓ **Tests**
  - Unit tests: Passing
  - Integration tests: Passing
  - E2E tests: Passing
  - Coverage: Acceptable

✓ **Build**
  - Development build: Success
  - Production build: Success
  - No build warnings

✓ **Runtime**
  - Backend starts: Yes
  - Frontend starts: Yes
  - Both together: Yes
  - No console errors: Yes

✓ **Functionality**
  - API endpoints work: Yes
  - UI renders correctly: Yes
  - User workflows work: Yes
  - Data flows correctly: Yes

✓ **Code Quality**
  - Linting passes: Yes
  - No duplicate code: Yes
  - Consistent patterns: Yes
  - Documentation updated: Yes

✓ **Final Smoke Test**
  - Login works
  - Main feature works
  - No obvious bugs
  - Ready for deployment
```

### Automated Merge Script (Optional)

```bash
#!/bin/bash
# merge-parallel-agents.sh

echo "🔀 Starting parallel agent merge..."

# Step 1: Merge Backend
echo "📦 Merging Backend (Agent 1)..."
git checkout main
git merge phase-1-backend --no-ff -m "Merge backend API"

if [ $? -ne 0 ]; then
  echo "❌ Backend merge failed! Resolve conflicts manually."
  exit 1
fi

echo "✅ Backend merged. Running tests..."
npm run test:backend
if [ $? -ne 0 ]; then
  echo "❌ Backend tests failed!"
  exit 1
fi

# Step 2: Merge Frontend
echo "🎨 Merging Frontend (Agent 2)..."
git merge phase-2-frontend --no-ff -m "Merge frontend UI"

if [ $? -ne 0 ]; then
  echo "⚠️  Conflicts detected. Resolve manually, then run:"
  echo "   npm run test:integration"
  exit 1
fi

echo "✅ Frontend merged. Running integration tests..."
npm run test:integration
if [ $? -ne 0 ]; then
  echo "❌ Integration tests failed!"
  exit 1
fi

# Step 3: Merge Tests
echo "🧪 Merging Tests (Agent 3)..."
git merge phase-3-tests --no-ff -m "Merge test suite"

echo "✅ Tests merged. Running full test suite..."
npm run test:all
if [ $? -ne 0 ]; then
  echo "❌ Full test suite failed!"
  exit 1
fi

# Step 4: Final validation
echo "✅ All merges complete! Running final validation..."
npm run build
if [ $? -ne 0 ]; then
  echo "❌ Build failed!"
  exit 1
fi

echo "🎉 Merge successful! All tests passing."
echo "📝 Creating final checkpoint..."

git commit --allow-empty -m "Merge complete: All phases integrated

✅ Backend API
✅ Frontend UI
✅ Test Suite

All tests passing, build successful."

echo "✅ Merge orchestration complete!"
```

### Rollback Strategy

If merge causes issues:

```bash
# Scenario: Frontend merge broke something

# Option 1: Revert specific merge
git revert -m 1 <merge-commit-hash>
# Reverts Frontend merge, keeps Backend

# Option 2: Reset to before merge
git reset --hard <commit-before-frontend-merge>
# Warning: Loses Frontend merge, must redo

# Option 3: Fix forward
# Debug issue, fix in place, commit fix
# Recommended if issue is small
```

### Communication Template: Merge Progress

```markdown
Template: Merge Orchestration Status

"🔀 Merging parallel agent outputs...

**Merge Sequence**:
1. ✅ Backend (Agent 1) → Merged & validated
2. 🔄 Frontend (Agent 2) → Merging now...
3. ⏳ Tests (Agent 3) → Pending

**Current Status**:
- Merged: Backend API
- Validation: ✅ Backend tests passing
- Next: Merge Frontend, test integration

Will update when all merges complete..."

---

After all merges:

"✅ All agents merged successfully!

**Merged Components**:
✓ Backend API (Agent 1)
✓ Frontend UI (Agent 2)
✓ Test Suite (Agent 3)

**Validation Results**:
✓ Unit tests: 45/45 passing
✓ Integration tests: 12/12 passing
✓ E2E tests: 8/8 passing
✓ Build: Success
✓ Runtime: No errors

**Final Checkpoint**: Created
Commit: abc1234 'All phases integrated and validated'

Ready for deployment!"
```

### Special Case: Merge Conflicts with Same-Domain Phases

When merging same-domain sequential phases (e.g., Frontend Phase 1 + Phase 2):

```markdown
Expected: Should merge cleanly (context handoff prevents conflicts)

If conflicts occur:
1. Check if artifact handoff was followed
   - Did Phase 2 import or recreate types?
   - Conflict in type definitions? → Phase 2 didn't import!

2. Resolve by preferring Phase 1 definitions
   - Keep Phase 1's type definitions
   - Update Phase 2's code to use imports

3. Validate after resolution
   - Ensure Phase 2 imports work
   - Run tests for both phases
   - Integration should work seamlessly

Root cause: Context handoff not followed → Fix: Enforce imports
```

---

### Communication Template for Parallel Execution

```markdown
"I'll execute this using **parallel multi-agent execution** for faster completion:

## Dependency Analysis
- Phase 1 (Backend): Independent
- Phase 2 (Frontend): Independent
- Both work to API contract: [contract]

## Execution Plan

**Parallel Phases** (30 min):
├─ Agent 1 (spring-boot-microservices): Backend API
│  - Setup Express/Spring
│  - Product routes & controllers
│  - Database integration
│  - API tests
│
└─ Agent 2 (angular-engineer): Frontend UI
   - React/Angular components
   - API client (using contract)
   - State management
   - UI tests

**Then Sync** (10 min):
- Integrate both
- End-to-end testing
- Resolve any mismatches

**Total Time**: ~40 min vs ~60 min sequential (33% faster!)

Starting parallel execution now..."
```

### Error Handling in Parallel Execution

```yaml
Scenario 1: One Agent Fails
  Agent 1: ✅ Complete
  Agent 2: ❌ Failed at step 3

Action:
  1. Note Agent 1's success (checkpoint)
  2. Debug Agent 2's failure
  3. Option A: Retry Agent 2 only
  4. Option B: Switch to sequential if dependency issue

Scenario 2: Contract Mismatch
  Agent 1: Implemented GET /products (plural)
  Agent 2: Expects GET /product (singular)

Action:
  1. Detect mismatch at sync point
  2. Align both to contract (update one or both)
  3. Re-test integration
  4. Update contract documentation

Scenario 3: Merge Conflicts
  Both agents modified same config file differently

Action:
  1. Use git to detect conflicts
  2. Manually resolve (keep both changes if possible)
  3. Test merged result
  4. Document resolution
```

### Time Savings Calculator

```python
def calculate_parallel_savings(phases):
    sequential_time = sum(phase.duration for phase in phases)

    # Find longest parallel track
    parallel_groups = group_by_dependencies(phases)
    parallel_time = max(sum(phase.duration for phase in group)
                       for group in parallel_groups)

    savings = sequential_time - parallel_time
    savings_pct = (savings / sequential_time) * 100

    return {
        'sequential': sequential_time,
        'parallel': parallel_time,
        'savings': savings,
        'savings_pct': savings_pct
    }

Example:
Phases: [Backend: 30min, Frontend: 30min, Integration: 10min]
Dependencies: Backend || Frontend → Integration

Sequential: 30 + 30 + 10 = 70 min
Parallel: max(30, 30) + 10 = 40 min
Savings: 30 min (43%)
```

### When NOT to Use Parallel Agents

```markdown
❌ Case 1: User Wants Review Between Phases
User: "Let me review the backend before you do frontend"
→ Use sequential, checkpoint after backend

❌ Case 2: Learning/Uncertain Requirements
First time implementing feature, unclear requirements
→ Sequential allows learning from Phase 1 to inform Phase 2

❌ Case 3: High Integration Complexity
Phases tightly coupled, contract hard to define upfront
→ Sequential reduces integration debugging

❌ Case 4: Limited Parallelism Benefit
Phase 1: 5 min, Phase 2: 40 min
→ Parallel saves only 5 min, not worth coordination overhead

❌ Case 5: Same File Modifications
Both phases edit same core files
→ High merge conflict risk, sequential safer
```

### Decision Flowchart: Sequential vs Parallel

```
Are phases independent? (no shared dependencies)
  ├─ No → SEQUENTIAL
  └─ Yes
      ↓
  Can contract be defined upfront?
      ├─ No → SEQUENTIAL
      └─ Yes
          ↓
  Do phases modify different files?
      ├─ No (same files) → SEQUENTIAL
      └─ Yes
          ↓
  Is parallel time savings > 20%?
      ├─ No → SEQUENTIAL (not worth it)
      └─ Yes
          ↓
  Does user want review between phases?
      ├─ Yes → SEQUENTIAL
      └─ No → PARALLEL ✅
```

### Integration with Phase Scoring

```python
# Extended scoring includes parallel potential
def calculate_execution_strategy(task):
    size_score = calculate_task_size(task)  # 0-10

    if size_score < 3:
        return "single_session"

    phases = create_phase_breakdown(task)
    dependencies = analyze_dependencies(phases)

    if all_independent(dependencies) and len(phases) >= 2:
        return "parallel_multi_agent"
    elif some_independent(dependencies):
        return "mixed_parallel_sequential"
    else:
        return "sequential_phases"

# Example outcomes:
"Build full-stack app" → parallel_multi_agent
"Build auth system with tests" → mixed (DB → (API||UI) → Tests)
"Build feature A then B then C" → sequential_phases
```

---

## User Communication Templates

### Template 1: Phase Plan Announcement (Score 6-10)

```
"This is a large task that I'll break into [N] phases for better quality and tracking:

## Phase Breakdown

**Phase 1: [Name]** (This session)
- [Key goals]
- [Major todos]
Success: [Criteria]

**Phase 2: [Name]** (Next session via --resume)
- [Key goals]
- [Major todos]
Success: [Criteria]

**Phase 3: [Name]** (Final session via --resume)
- [Key goals]
- [Major todos]
Success: [Criteria]

After each phase, I'll create a checkpoint so you can:
- Review progress
- Take a break if needed
- Resume with `claude --resume`

Starting Phase 1 now..."
```

### Template 2: Checkpoint Complete

```
"✅ Phase [N] Complete!

## What Was Done
[Summary of accomplishments]

## Files Changed
[List of modified files]

## Testing
✓ Tests passing
✓ App running
✓ Changes committed

## Next Steps
Phase [N+1]: [Name]
Goal: [Brief description]

**To continue:**
```bash
claude --resume
```

Or take a break - your progress is saved and ready to resume anytime!"
```

### Template 3: Optional Phases (Score 3-5)

```
"This task has [N] components. I can either:

**Option 1: One session** (30-45 min)
- Do everything together
- Faster but less structured

**Option 2: [N] phases** (via --resume)
- Phase 1: [Components]
- Phase 2: [Components]
- More structured, easier to review

Which approach do you prefer?"
```

### Template 4: Resume Greeting

```
"Welcome back! Resuming from checkpoint...

**Last Session**: Phase [N] - [Name]
✅ Completed: [Summary]

**This Session**: Phase [N+1] - [Name]
🎯 Goal: [Description]

**Todos for this phase**:
[List]

Let's pick up where we left off!"
```

---

## Todo Structure Per Phase

### Good Phase Breakdown Example

```markdown
✅ GOOD - Balanced todos per phase:

## Phase 1: Database & Models (5 todos)
- [ ] Create database schema
- [ ] Setup Prisma/Sequelize ORM
- [ ] Define User model
- [ ] Define Post model
- [ ] Test model relationships

## Phase 2: API Endpoints (4 todos)
- [ ] Create auth routes
- [ ] Create post CRUD routes
- [ ] Add validation middleware
- [ ] Test API with Postman

## Phase 3: Frontend Integration (5 todos)
- [ ] Create React components
- [ ] Setup API client
- [ ] Implement auth flow UI
- [ ] Implement post management UI
- [ ] End-to-end testing
```

### Bad Phase Breakdown Example

```markdown
❌ BAD - Unbalanced phases:

## Phase 1: Everything Backend (15 todos)
- [ ] Database setup
- [ ] 10 models
- [ ] 20 API routes
- [ ] Authentication
- [ ] Authorization
[Too many todos - will take too long, high risk]

## Phase 2: Just CSS (1 todo)
- [ ] Style the app
[Too vague and small - not a real phase]
```

**Phase Balance Rules**:
- Each phase: 2-6 major todos (not too few, not too many)
- Each todo: 5-20 min of work (granular enough)
- Phase duration: 30-60 min max (keeps focus)
- Clear success criteria per phase

---

## Scope Creep Handling

### Mid-Execution Expansion

```
Initial Task: "Add login feature"

During Phase 1:
User: "Oh, also add OAuth"
User: "And password reset"
User: "And email verification"

Action:
1. Pause current phase
2. Recalculate task size (now 6+)
3. Create new phase plan:
   - Phase 1: Basic login (continue current)
   - Phase 2: OAuth integration (new)
   - Phase 3: Password reset + email (new)
4. Inform user:
   "Task scope expanded significantly. I'll complete Phase 1 (basic login) now,
    then we can --resume for OAuth and password features in separate phases."
```

---

## Token Efficiency

### Why Phased Execution Saves Tokens

**Without Phases** (Large task in one session):
```
Try to do everything → 60K tokens context
Miss some requirements → Redo → +20K tokens
Context gets messy → Confusion → +10K tokens
Total: 90K tokens, incomplete work
```

**With Phases** (Structured approach):
```
Phase 1: 20K tokens → Complete → Checkpoint
Phase 2: 15K tokens (clean context) → Complete → Checkpoint
Phase 3: 15K tokens → Complete → Done
Total: 50K tokens, complete work, better quality

Savings: 40K tokens (44%)
```

### Additional Benefits

- **Clean context per phase**: No bloat from previous phase details
- **Focused work**: Each phase has clear scope
- **Better planning**: Can adjust future phases based on Phase 1 learnings
- **User flexibility**: Can review/modify between phases

---

## Checkpoint Storage

### Where Checkpoints Live

**Option 1: Git Commits**
```bash
# Each phase ends with commit
git commit -m "Phase 1 complete: Core auth with JWT

- JWT setup & config
- User model with bcrypt
- Login/logout endpoints
- Token validation middleware

Tests passing. Ready for Phase 2 (OAuth)."
```

**Option 2: Session File (if available)**
```markdown
.claude/checkpoints/session-2024-01-22.md

## Checkpoint: Phase 1 Complete
Timestamp: 2024-01-22 14:30
Status: ✅ Complete

Summary: [...]
Files: [...]
Next: Phase 2 - OAuth
```

**Option 3: README Update**
```markdown
# Project Status

## Completed Phases
✅ Phase 1: Core Auth (2024-01-22)
⏳ Phase 2: OAuth (In Progress)
⬜ Phase 3: Admin Dashboard (Pending)
```

---

## Integration with TodoWrite

### TodoWrite for Each Phase

```
Phase 1 starts:
TodoWrite([
  {content: "Setup JWT config", status: "pending"},
  {content: "Create User model", status: "pending"},
  {content: "Implement login endpoint", status: "pending"},
  {content: "Add token validation", status: "pending"},
  {content: "Test auth flow", status: "pending"}
])

During Phase 1:
- Mark todos as in_progress, then completed
- User sees clear progress

Phase 1 complete:
- All todos marked completed
- Create checkpoint
- Clear todos (or archive)

Phase 2 starts (--resume):
TodoWrite([
  {content: "Setup OAuth providers", status: "pending"},
  {content: "Create callback routes", status: "pending"},
  ...
])
```

---

## Special Cases

### Case 1: User Wants to Skip Phases

```
User: "Just do it all at once, no phases"

Response:
- If score ≤ 5: Honor request
- If score 6-8: Warn but honor: "This is complex, but proceeding as requested..."
- If score 9-10: Strong recommend phases: "This is very large (10+ requirements).
  Doing it all at once risks missing details. Recommend phases. Still want all at once?"
```

### Case 2: Phase Fails Midway

```
Phase 2 execution → Error → Can't proceed

Action:
1. Document failure point in checkpoint
2. Mark incomplete todos
3. Create recovery plan
4. Inform user:
   "Phase 2 encountered an issue at [step]. I've checkpointed current state.
    To fix and resume:
    1. [Fix suggestion]
    2. claude --resume (will retry Phase 2)"
```

### Case 3: User Wants to Modify Future Phases

```
After Phase 1:
User: "Actually, skip OAuth. Just do email verification instead."

Action:
1. Acknowledge change
2. Update phase plan:
   - Phase 2: Email verification (modified)
   - Phase 3: Admin (unchanged)
3. Inform: "Phase plan updated. OAuth removed, email verification added to Phase 2."
```

---

## Quick Decision Flowchart

```
                    User Request Received
                           ↓
            [Planning intelligence determines approach]
                           ↓
            ┌──────────────────────────────┐
            │  Calculate Task Size Score   │
            │        (0-10 scale)          │
            └──────────────────────────────┘
                           ↓
              ┌────────────┴────────────┐
              ↓                         ↓
         Score 0-2                 Score 3-5              Score 6-10
              ↓                         ↓                      ↓
    ┌─────────────────┐      ┌──────────────────┐   ┌──────────────────┐
    │ Execute Direct  │      │  Ask User        │   │ Create Phases    │
    │ (No phases)     │      │  (Optional)      │   │ (MANDATORY)      │
    └─────────────────┘      └──────────────────┘   └──────────────────┘
              ↓                    ↓       ↓                  ↓
    ┌─────────────────┐           ↓       ↓         ┌──────────────────┐
    │  Work           │    ┌──────┘       └──────┐  │ Announce Plan    │
    │  Complete       │    ↓                     ↓  │ Show Phases      │
    └─────────────────┘  Phases            Direct   └──────────────────┘
                           ↓                 ↓              ↓
                    ┌─────────────┐   ┌──────────┐  ┌──────────────────┐
                    │ Create      │   │ Execute  │  │ Execute Phase 1  │
                    │ Phase Plan  │   │ All      │  └──────────────────┘
                    └─────────────┘   └──────────┘          ↓
                           ↓                              ┌──────────────────┐
                    ┌─────────────┐                      │ Phase Complete?  │
                    │ Execute     │                      └──────────────────┘
                    │ Phase 1     │                         ↓           ↓
                    └─────────────┘                        Yes          No
                           ↓                                ↓            ↓
                    ┌─────────────┐                  ┌──────────┐  Continue
                    │ Checkpoint  │                  │Create    │
                    │ Created     │                  │Checkpoint│
                    └─────────────┘                  └──────────┘
                           ↓                              ↓
                    ┌─────────────┐              ┌──────────────────┐
                    │ Inform User:│              │ Inform: --resume │
                    │ "Use --resume"│             │ for Phase 2      │
                    └─────────────┘              └──────────────────┘
                           ↓
                    User runs --resume
                           ↓
                    ┌─────────────┐
                    │ Load        │
                    │ Checkpoint  │
                    └─────────────┘
                           ↓
                    Execute Phase 2
                           ↓
                         [Repeat]
```

---

## Status

**Version**: 1.0.0
**Status**: ACTIVE (Automatic for large tasks)
**Created**: 2026-01-22
**Integration**: Works with task-planning-intelligence, TodoWrite, git workflow

---

## Summary (TL;DR)

**What**: Breaks large tasks into manageable phases with checkpoints
**How**: Task size scoring (0-10) → Phase breakdown → Execute → Checkpoint → Resume
**Why**: Prevents missed requirements, manages complexity, enables progress tracking
**When**: Mandatory for score 6-10, optional for 3-5, skip for 0-2

**Thresholds**:
- 0-2: Direct execution
- 3-5: Ask user
- 6-10: Mandatory phases

**Checkpoint**: Git commit + summary + next phase plan

**Resume**: `claude --resume` loads checkpoint and continues next phase

**Benefits**:
- 40%+ token savings (clean context per phase)
- Zero missed requirements (structured approach)
- User flexibility (can pause/resume anytime)
- Better quality (focused work per phase)

---

**Remember**: Big tasks → Small phases → Checkpoints → --resume → Success! 🎯
