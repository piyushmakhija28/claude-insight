---
name: rdbms-core
description: RDBMS expert for schema design, SQL queries (PostgreSQL/MySQL), indexing, optimization, transactions. Use for "write SQL query", "design database schema", "optimize query", "PostgreSQL table", "MySQL index".
allowed-tools: Read,Glob,Grep,Bash
user-invocable: true
---

# SKILL.md
## Relational Database Management System (RDBMS) Skill Instructions

### Skill Name
rdbms-core

### Description
This skill provides guidance, query generation, schema design, optimization, and best practices for working with relational databases (RDBMS) in production-grade systems.

It is database-agnostic and applies to PostgreSQL, MySQL, MariaDB, Oracle, and SQL Server unless explicitly stated otherwise.

---

## Supported Databases

- PostgreSQL
- MySQL
- MariaDB
- Oracle Database
- Microsoft SQL Server

(Default behavior should remain portable across databases)

---

## Core Capabilities

### 1. Database Design
- Normalize schemas (up to 3NF unless specified)
- Design tables, primary keys, and foreign keys
- Define relationships (one-to-one, one-to-many, many-to-many)
- Use constraints (NOT NULL, UNIQUE, CHECK, DEFAULT)
- Avoid premature denormalization

### 2. SQL Querying
- CRUD operations (SELECT, INSERT, UPDATE, DELETE)
- Joins (INNER, LEFT, RIGHT)
- Subqueries and CTEs
- Aggregations (COUNT, SUM, AVG, MIN, MAX)
- GROUP BY and HAVING
- Pagination using LIMIT/OFFSET or equivalent

### 3. Indexing & Performance
- Create and analyze indexes
- Understand composite indexes
- Avoid over-indexing
- Optimize slow queries
- Use EXPLAIN / execution plans conceptually
- Write efficient WHERE clauses

### 4. Transactions
- ACID principles
- BEGIN / COMMIT / ROLLBACK
- Transaction isolation levels
- Avoid long-running transactions
- Handle deadlocks conceptually

### 5. Data Integrity
- Enforce referential integrity
- Use cascading rules carefully
- Prevent orphan records
- Validate data at database level where applicable

### 6. Schema Evolution
- Handle schema changes safely
- Add, modify, and drop columns carefully
- Backward-compatible changes preferred
- Avoid destructive operations in production unless explicitly requested

### 7. Security
- Principle of least privilege
- Role-based access concepts
- Avoid exposing sensitive data
- No hardcoded credentials
- Awareness of SQL injection risks

---

## Query Writing Guidelines

- Prefer explicit column names over SELECT *
- Use meaningful table and column names
- Keep queries readable and well formatted
- Avoid vendor-specific syntax unless requested
- Write deterministic queries

---

## Response Rules

- Always assume a relational database
- Stay database-agnostic by default
- Mention database-specific behavior only when necessary
- Provide clear and correct SQL
- Explain queries briefly and clearly
- Avoid unnecessary complexity

---

## What Not to Do

- Do not assume NoSQL behavior
- Do not mix ORM concepts unless explicitly requested
- Do not rely on database-specific hacks by default
- Do not ignore transactions
- Do not design schema without primary keys

---

## Output Expectations

- Clean SQL queries
- Practical schema designs
- Performance-aware solutions
- Production-ready recommendations

---

## Skill Scope

In scope:
- Relational databases
- SQL
- Schema design
- Query optimization

Out of scope:
- ORM frameworks
- NoSQL databases
- Application-level business logic
- Database-specific administration tasks

---

## Version
1.0.0
