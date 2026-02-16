---
name: nosql-core
description: Guidance for NoSQL databases (MongoDB & Elasticsearch) including schema design, query patterns, indexing, and performance best practices for document stores and search engines.
allowed-tools: Read,Glob,Grep,Bash,Edit,Write
user-invocable: true
---

# NoSQL Database Skill Instructions (MongoDB & Elasticsearch)

### Skill Name
nosql-core

### Description
This skill provides guidance, schema design strategies, query patterns, indexing, and performance best practices for NoSQL databases, specifically document stores and search engines.

It focuses on MongoDB and Elasticsearch, following production-ready and scalable design principles.

---

## Supported NoSQL Databases

### Document Database
- MongoDB

### Search & Analytics Engine
- Elasticsearch

(Default behavior should respect the core philosophy of each database)

---

## Core Concepts

### 1. NoSQL Fundamentals
- Schema-less vs schema-flexible design
- Document-oriented data modeling
- Denormalization strategies
- Read vs write optimization
- Eventual consistency awareness

---

## MongoDB Capabilities

### 2. Data Modeling
- Document-based schema design
- Embedded documents vs references
- One-to-few and one-to-many modeling
- Avoid deep nesting
- Design for query patterns

### 3. CRUD Operations
- insertOne, insertMany
- find, findOne
- updateOne, updateMany
- deleteOne, deleteMany
- Projection and filtering

### 4. Indexing & Performance
- Single-field and compound indexes
- Text indexes
- Index selectivity
- Avoid excessive indexes
- Query explain awareness

### 5. Aggregation Framework
- $match, $project, $group
- $lookup (limited joins)
- $sort, $limit, $skip
- Pipeline-based data processing

### 6. Transactions
- Multi-document transactions awareness
- Use transactions only when required
- Session-based transaction handling

---

## Elasticsearch Capabilities

### 7. Index Design
- Index vs document concepts
- Mapping types and field definitions
- Keyword vs text fields
- Analyzers and tokenization
- Avoid dynamic mapping abuse

### 8. Search & Querying
- Match, term, range queries
- Bool queries
- Full-text search concepts
- Pagination with from/size and search_after
- Sorting and relevance scoring

### 9. Aggregations
- Bucket aggregations
- Metric aggregations
- Nested aggregations
- Analytics-focused querying

### 10. Performance & Scaling
- Shards and replicas awareness
- Index refresh intervals
- Bulk indexing
- Read-heavy vs write-heavy tuning

---

## Query & Design Guidelines

- Design data based on access patterns
- Prefer denormalization over joins
- Keep documents reasonably sized
- Use Elasticsearch for search, not transactions
- Use MongoDB as source of truth when applicable

---

## Response Rules

- Choose MongoDB or Elasticsearch based on use case
- Avoid RDBMS-style joins by default
- Provide clear query examples (JSON-based)
- Explain NoSQL trade-offs briefly
- Keep solutions production-oriented

---

## What Not to Do

- Do not treat NoSQL as relational databases
- Do not overuse transactions in MongoDB
- Do not use Elasticsearch as a primary database
- Do not rely on auto-generated mappings blindly
- Do not model everything as flat documents

---

## Output Expectations

- Clean, readable JSON queries
- Practical schema and mapping examples
- Performance-aware recommendations
- Real-world NoSQL usage patterns

---

## Skill Scope

In scope:
- MongoDB
- Elasticsearch
- Document modeling
- Search and analytics

Out of scope:
- RDBMS features
- ORM/JPA concepts
- Frontend search UI
- Low-level cluster administration

---

## Version
1.0.0
