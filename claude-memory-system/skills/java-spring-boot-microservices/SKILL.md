---
name: java-spring-boot-microservices
description: Java Spring Boot microservices expert for code gen, architecture, security, DB integration (RDBMS/NoSQL). Use for "Spring Boot microservice", "REST API Spring", "JWT auth", "Spring Data JPA", "microservices Eureka".
allowed-tools: Read,Glob,Grep,Bash,Edit,Write
user-invocable: true
---

# SKILL.md
## Java & Spring Boot Microservices Skill Instructions

### Skill Name
java-spring-boot-microservices

### Description
This skill provides guidance, code generation, debugging, and best-practice recommendations for building scalable, secure, and production-ready Java Spring Boot microservices architectures.

This skill builds on top of foundational data skills and must follow their rules and constraints when working with databases.

---

## Skill Dependencies

This skill **extends and uses** the following base skills:

- rdbms-core
  (Relational database design, SQL querying, transactions, and integrity)

- nosql-core
  (Document databases and search engines such as MongoDB and Elasticsearch)

All database-related guidance must comply with the rules defined in these skills.

---

## Core Capabilities

### 1. Application Development
- Generate Spring Boot microservices using Java (17+ preferred)
- Use layered architecture (controller, service, repository)
- Apply RESTful API design principles
- Implement DTOs, validation, and global exception handling
- Keep business logic out of controllers

### 2. Microservices Architecture
- Service discovery (Eureka or equivalent)
- API Gateway patterns
- Inter-service communication (REST, Feign)
- Centralized configuration
- Distributed tracing and logging concepts
- Stateless service design

### 3. Data Management
- Use relational databases according to **rdbms-core**
- Use NoSQL databases according to **nosql-core**
- Spring Data JPA for RDBMS
- Spring Data MongoDB for MongoDB
- Elasticsearch used only for search and analytics
- Transaction management where applicable
- Pagination, sorting, and filtering
- Database migration awareness (Flyway / Liquibase concepts)

### 4. Security
- JWT-based authentication
- Role-based authorization
- Secure API design
- Configuration of Spring Security
- Proper handling of 401 and 403 errors
- No security logic inside controllers

### 5. Configuration & Environments
- Support for dev, stag, and prod profiles
- Environment variable–based configuration
- Externalized secrets handling
- Docker-friendly configuration practices
- Profile-specific beans where required

### 6. Testing
- Unit testing using JUnit and Mockito
- High test coverage focus
- Controller, service, and repository tests
- Mock external dependencies
- Avoid integration tests unless explicitly requested

### 7. DevOps & Deployment
- Docker and Docker Compose support
- Container networking awareness
- Health checks and readiness probes
- Basic CI/CD concepts
- JVM and container optimization hints
- Cloud-native startup awareness

---

## Coding Guidelines

- Use Java 17+ features where applicable
- Follow Spring Boot conventions
- Prefer constructor injection
- Avoid field injection
- Keep services cohesive and focused
- Write clean, readable, and maintainable code
- Do not introduce unnecessary abstractions
- Keep examples production-oriented

---

## Response Rules

- Always respect rules from rdbms-core and nosql-core
- Provide complete, runnable code when generating examples
- Prefer clarity over brevity
- Explain architectural decisions briefly when relevant
- Do not assume DevOps expertise unless specified
- Avoid overengineering
- Follow industry-standard naming conventions

---

## What Not to Do

- Do not mix RDBMS and NoSQL concepts incorrectly
- Do not treat NoSQL as relational databases
- Do not introduce deprecated Spring APIs
- Do not hardcode credentials
- Do not skip error handling
- Do not assume monolithic architecture
- Do not use Elasticsearch as a primary database

---

## Output Expectations

- Clear explanations
- Structured and idiomatic Spring Boot code
- Real-world microservice patterns
- Database usage aligned with underlying skill rules
- Enterprise-ready examples

---

## Skill Scope

This skill is focused on:
- Java
- Spring Boot
- Microservices architecture
- Database integration using existing data skills

Out of scope:
- Frontend frameworks
- Non-Java backend stacks
- Low-level JVM internals
- Database administration tasks

---

## Version
1.1.0
