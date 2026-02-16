---
name: spring-boot-design-patterns-core
description: Practical guidance for applying design patterns in Spring Boot applications. Focuses on real-world backend systems, clean architecture, scalability, testability, and maintainability.
allowed-tools: Read,Glob,Grep,Bash,Edit,Write
user-invocable: true
---

# Spring Boot Design Patterns Skill Instructions (Production Ready)

### Skill Name
spring-boot-design-patterns-core

### Description
This skill provides practical guidance for applying design patterns specifically in Spring Boot applications. It focuses on real-world backend systems, clean architecture, scalability, testability, and maintainability using Spring Boot conventions and ecosystem features.

This skill builds on Java design patterns but adapts them to Spring Boot realities.

---

## Core Principles (NON-NEGOTIABLE)

### 1. Spring Boot First, Pattern Second
- Spring Boot already implements many patterns internally
- Do not re-implement what Spring provides
- Use patterns only when they improve clarity or flexibility
- Simpler Spring-native solutions are preferred

---

## Pattern Categories in Spring Boot

### 2. Creational Patterns (Spring-Aware)

#### Singleton
- Spring beans are Singleton by default
- Do not implement manual Singleton patterns
- Control lifecycle via Spring container

#### Factory Pattern
- Used via configuration classes
- Bean creation logic encapsulated in @Configuration
- Useful for conditional or environment-based beans

Use when:
- Object creation depends on configuration
- Multiple implementations exist

---

### 3. Structural Patterns (Most Common)

#### Facade
- Service layer acting as Facade
- Controllers should call services, not repositories
- Simplifies complex business flows

#### Adapter
- Used for external APIs, third-party integrations
- Keeps domain independent of external contracts

#### Proxy
- Used implicitly via Spring AOP
- Common for logging, security, transactions, caching

---

### 4. Behavioral Patterns (Very Important)

#### Strategy
- Used with interfaces + multiple implementations
- Common in payment, notification, and rule engines
- Often combined with @Qualifier or @Primary

#### Template Method
- Abstract base services with common flow
- Specific steps overridden by subclasses

#### Chain of Responsibility
- Filters, interceptors, and request pipelines
- Validation and processing chains

---

## Spring Boot–Specific Pattern Usage

### 5. Dependency Injection Pattern
- Constructor injection only
- Avoid field injection
- Prefer immutability

Spring handles object wiring; do not mix manual instantiation.

---

### 6. Repository Pattern
- Use Spring Data repositories
- Repositories handle persistence only
- No business logic inside repositories

---

### 7. DTO Pattern
- Separate API models from domain models
- Prevent entity leakage
- Enable backward-compatible APIs

---

### 8. Service Layer Pattern
- Business logic belongs in services
- Services should be cohesive and focused
- Avoid God services

---

### 9. Controller Pattern
- Controllers orchestrate request/response only
- No business logic
- Validate input and delegate to services

---

## Cross-Cutting Patterns (Spring Strength)

### 10. Aspect-Oriented Programming (AOP)
- Logging
- Security
- Transactions
- Auditing

Use AOP instead of manual boilerplate.

---

## Error Handling Patterns

### 11. Exception Handling
- Centralized exception handling
- Custom exceptions for domain errors
- Consistent error responses

---

## Configuration & Environment Patterns

### 12. Configuration Pattern
- Externalized configuration
- Profile-based beans
- Avoid hardcoded values

---

## Anti-Patterns in Spring Boot

### 13. What NOT to Do
- Manual Singleton implementation
- Fat controllers
- Business logic in repositories
- Overusing inheritance
- Excessive abstraction layers
- Circular dependencies

---

## Pattern Selection Strategy

### 14. Choosing the Right Pattern
Before applying a pattern:
- Identify the actual problem
- Check if Spring already solves it
- Evaluate complexity vs benefit
- Apply minimally

---

## Testing & Patterns

### 15. Testability Considerations
- Patterns should simplify testing
- Mock interfaces, not implementations
- Keep beans loosely coupled
- Avoid static-heavy designs

---

## Response Rules

- Prefer Spring-native solutions
- Explain intent before implementation
- Use patterns only when justified
- Keep code readable and maintainable
- Avoid overengineering

---

## What Not to Do

- Do not blindly apply GoF patterns
- Do not fight the Spring container
- Do not reimplement framework features
- Do not sacrifice clarity for abstraction

---

## Output Expectations

- Clean Spring Boot architecture
- Pattern-aware service design
- Scalable and testable code
- Framework-aligned solutions
- Production-ready examples

---

## Skill Scope

In scope:
- Spring Boot design patterns
- Backend architecture patterns
- Service, repository, controller patterns
- Cross-cutting concerns via AOP

Out of scope:
- UI patterns
- Distributed system patterns
- DevOps patterns
- Framework-internal implementation details

---

## Version
1.0.0
