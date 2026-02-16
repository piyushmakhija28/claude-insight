---
name: java-design-patterns-core
description: Structured guidance for applying design patterns in Java-based systems. Focuses on when, why, and how to use patterns in real production code for clean architecture and scalable applications.
allowed-tools: Read,Glob,Grep,Bash,Edit,Write
user-invocable: true
---

# Java Design Patterns Skill Instructions (Production-Oriented)

### Skill Name
java-design-patterns-core

### Description
This skill provides structured, practical guidance for applying design patterns in Java-based systems. It focuses on when, why, and how to use patterns in real production code, not theoretical definitions.

This skill is intended for clean architecture, maintainable code, and scalable Java applications.

---

## Core Principles (VERY IMPORTANT)

### 1. Pattern ≠ Solution
- Design patterns are tools, not rules
- Do not force patterns where simple code works
- Use patterns to reduce coupling, not to add complexity
- Readability and maintainability come first

---

## Pattern Categories

### 2. Creational Patterns
Used for object creation control.

- Singleton
- Factory Method
- Abstract Factory
- Builder
- Prototype

Use when:
- Object creation logic becomes complex
- Instantiation must be controlled or abstracted

Avoid when:
- Simple constructors are sufficient

---

### 3. Structural Patterns
Used for object composition and structure.

- Adapter
- Decorator
- Facade
- Proxy
- Composite

Use when:
- Integrating legacy or third-party code
- Adding behavior without modifying existing code
- Simplifying complex subsystems

---

### 4. Behavioral Patterns
Used for object interaction and responsibility flow.

- Strategy
- Observer
- Command
- Template Method
- Chain of Responsibility
- State

Use when:
- Behavior changes based on runtime conditions
- Logic branches start growing uncontrollably
- Responsibilities need clean separation

---

## Java-Specific Pattern Usage

### 5. Patterns in Modern Java
- Prefer composition over inheritance
- Use interfaces and lambdas where applicable
- Leverage immutability
- Combine patterns carefully (not excessively)
- Keep constructors simple

---

## Anti-Patterns Awareness

### 6. Common Java Anti-Patterns
- God Object
- Over-engineered factories
- Singleton abuse
- Deep inheritance hierarchies
- Pattern stacking without justification

Recognize anti-patterns early and refactor.

---

## Pattern Selection Strategy

### 7. Choosing the Right Pattern
Before applying a pattern, ask:
- What problem am I solving?
- Is this problem recurring?
- Can simpler code solve it?
- Will this reduce future change cost?

If answers are unclear:
- Do not apply a pattern yet

---

## Patterns & Architecture

### 8. Patterns in Layered Architecture
- Controller layer: Command, Template
- Service layer: Strategy, Facade
- Domain layer: State, Specification awareness
- Infrastructure layer: Adapter, Proxy

Patterns should respect layer boundaries.

---

## Refactoring with Patterns

### 9. Introducing Patterns Safely
- Start with working code
- Identify duplication or rigidity
- Introduce pattern incrementally
- Preserve behavior during refactor
- Avoid big-bang rewrites

---

## Testing & Patterns

### 10. Testability Considerations
- Patterns should improve testability
- Prefer dependency injection
- Mock behavior, not structure
- Avoid static-heavy designs

---

## Response Rules

- Use patterns only when justified
- Prefer clear Java examples
- Explain intent before implementation
- Avoid pattern jargon overload
- Focus on maintainable solutions

---

## What Not to Do

- Do not implement patterns for the sake of it
- Do not blindly copy textbook examples
- Do not create unnecessary abstractions
- Do not mix multiple patterns without reason
- Do not sacrifice readability

---

## Output Expectations

- Clean Java-centric examples
- Practical pattern usage
- Clear decision rationale
- Production-friendly designs
- Refactor-ready code structure

---

## Skill Scope

In scope:
- Java design patterns
- Object-oriented design
- Pattern-driven refactoring
- Clean architecture support

Out of scope:
- Framework-specific patterns
- Language-agnostic theory
- UI design patterns
- Distributed system patterns

---

## Version
1.0.0
