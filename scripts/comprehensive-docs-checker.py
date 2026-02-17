#!/usr/bin/env python3
"""
Comprehensive Documentation Checker & Creator

Checks all git repositories for:
1. Missing README.md and CLAUDE.md files
2. Comprehensiveness of existing files
3. Auto-creates missing files with comprehensive content
4. Updates non-comprehensive files

Author: Claude Code (Memory System v2.5.0)
Date: 2026-02-17
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class DocumentationChecker:
    """Checks and creates comprehensive documentation in all git repos"""

    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.results = {
            'checked': 0,
            'missing_readme': [],
            'missing_claude_md': [],
            'non_comprehensive_readme': [],
            'non_comprehensive_claude_md': [],
            'created_readme': [],
            'created_claude_md': [],
            'updated_readme': [],
            'updated_claude_md': []
        }

    def find_git_repos(self) -> List[Path]:
        """Find all git repositories recursively"""
        git_repos = []

        for root, dirs, files in os.walk(self.root_path):
            if '.git' in dirs:
                git_repos.append(Path(root))
                # Don't recurse into this repo's subdirectories
                dirs.clear()

        return git_repos

    def check_file_exists(self, repo_path: Path, filename: str) -> bool:
        """Check if a file exists in the repo"""
        return (repo_path / filename).exists()

    def check_file_comprehensive(self, file_path: Path, file_type: str) -> Tuple[bool, str]:
        """
        Check if a file is comprehensive

        Returns: (is_comprehensive, reason)
        """
        if not file_path.exists():
            return False, "File does not exist"

        content = file_path.read_text(encoding='utf-8', errors='ignore')
        lines = content.split('\n')

        # Minimum requirements
        min_lines = 50  # Comprehensive docs should be substantial

        if len(lines) < min_lines:
            return False, f"Too short ({len(lines)} lines, need {min_lines}+)"

        if file_type == 'README':
            # Check for essential sections (flexible matching)
            required_sections = {
                'Title': '# ',
                'Sections': '## ',
                'TOC': ('Table of Contents', '## Table of Contents'),
                'Architecture': ('Architecture', '## Architecture'),
                'Setup': ('Getting Started', 'Local Development', 'Installation', '## Getting Started', '## Local Development'),
            }

            missing_sections = []
            for section_name, section_patterns in required_sections.items():
                if isinstance(section_patterns, tuple):
                    # Check if ANY of the patterns exist
                    if not any(pattern in content for pattern in section_patterns):
                        missing_sections.append(section_name)
                else:
                    # Single pattern
                    if section_patterns not in content:
                        missing_sections.append(section_name)

            if missing_sections:
                return False, f"Missing sections: {', '.join(missing_sections)}"

        elif file_type == 'CLAUDE':
            # Check for essential sections (flexible matching)
            required_sections = {
                'Title': '# ',
                'Sections': '## ',
                'Overview': ('PROJECT OVERVIEW', 'SERVICE OVERVIEW', 'APPLICATION OVERVIEW'),
                'Structure': ('PROJECT STRUCTURE', 'Directory Layout'),
                'Specific': ('PROJECT-SPECIFIC', 'SERVICE-SPECIFIC', 'APPLICATION-SPECIFIC'),
            }

            missing_sections = []
            for section_name, section_patterns in required_sections.items():
                if isinstance(section_patterns, tuple):
                    # Check if ANY of the patterns exist
                    if not any(pattern in content for pattern in section_patterns):
                        missing_sections.append(section_name)
                else:
                    # Single pattern
                    if section_patterns not in content:
                        missing_sections.append(section_name)

            if missing_sections:
                return False, f"Missing sections: {', '.join(missing_sections)}"

        return True, "Comprehensive"

    def get_repo_info(self, repo_path: Path) -> Dict[str, str]:
        """Extract repository information"""
        info = {
            'name': repo_path.name,
            'path': str(repo_path),
            'is_service': False,
            'is_project_root': False,
            'is_frontend': False,
            'is_backend_service': False,
            'project_name': '',
            'service_name': '',
            'base_package': '',
            'port': '',
            'description': ''
        }

        # Determine type
        if 'frontend' in str(repo_path).lower() or '-ui' in repo_path.name:
            info['is_frontend'] = True
            info['description'] = f"Frontend application for {repo_path.name}"
        elif '-service' in repo_path.name or '-utility' in repo_path.name:
            info['is_backend_service'] = True
            info['is_service'] = True

            # Extract project and service name
            parts = repo_path.name.split('-')
            if len(parts) >= 2:
                info['project_name'] = parts[0]
                info['service_name'] = '-'.join(parts[1:])
                info['base_package'] = f"com.techdeveloper.{info['project_name']}.{parts[1]}"

        # Try to extract port from pom.xml or application.yml
        pom_xml = repo_path / 'pom.xml'
        if pom_xml.exists():
            # This is a Java service
            try:
                content = pom_xml.read_text(encoding='utf-8', errors='ignore')
                if '<artifactId>' in content:
                    # Extract artifact ID
                    start = content.find('<artifactId>') + 12
                    end = content.find('</artifactId>', start)
                    info['name'] = content[start:end]
            except Exception:
                pass

        return info

    def check_repo(self, repo_path: Path) -> Dict:
        """Check a single repository for documentation"""
        result = {
            'repo': str(repo_path),
            'name': repo_path.name,
            'has_readme': False,
            'has_claude_md': False,
            'readme_comprehensive': False,
            'claude_md_comprehensive': False,
            'readme_reason': '',
            'claude_md_reason': '',
            'needs_readme': False,
            'needs_claude_md': False,
            'needs_readme_update': False,
            'needs_claude_md_update': False
        }

        # Check README.md
        readme_path = repo_path / 'README.md'
        result['has_readme'] = readme_path.exists()

        if result['has_readme']:
            is_comp, reason = self.check_file_comprehensive(readme_path, 'README')
            result['readme_comprehensive'] = is_comp
            result['readme_reason'] = reason

            if not is_comp:
                result['needs_readme_update'] = True
                self.results['non_comprehensive_readme'].append(str(repo_path))
        else:
            result['needs_readme'] = True
            self.results['missing_readme'].append(str(repo_path))

        # Check CLAUDE.md
        claude_md_path = repo_path / 'CLAUDE.md'
        result['has_claude_md'] = claude_md_path.exists()

        if result['has_claude_md']:
            is_comp, reason = self.check_file_comprehensive(claude_md_path, 'CLAUDE')
            result['claude_md_comprehensive'] = is_comp
            result['claude_md_reason'] = reason

            if not is_comp:
                result['needs_claude_md_update'] = True
                self.results['non_comprehensive_claude_md'].append(str(repo_path))
        else:
            result['needs_claude_md'] = True
            self.results['missing_claude_md'].append(str(repo_path))

        self.results['checked'] += 1
        return result

    def generate_readme_content(self, repo_info: Dict) -> str:
        """Generate comprehensive README.md content"""
        name = repo_info['name']

        if repo_info['is_backend_service']:
            # Backend service README
            service_name = repo_info['service_name']
            project_name = repo_info['project_name'].capitalize()

            content = f"""# {project_name} {service_name.replace('-', ' ').title()}

Microservice responsible for [SERVICE PURPOSE] in the {project_name} platform.

## Table of Contents

- [Architecture](#architecture)
- [API Endpoints](#api-endpoints)
- [Configuration](#configuration)
- [Local Development](#local-development)
- [Docker](#docker)
- [Jenkins CI/CD](#jenkins-cicd)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Troubleshooting](#troubleshooting)

## Architecture

| Component             | Details                             |
|-----------------------|-------------------------------------|
| **Framework**         | Spring Boot 4.x (Java 21)           |
| **Port**              | [PORT NUMBER]                       |
| **Database**          | PostgreSQL (`{repo_info['project_name']}`) |
| **Service Discovery** | Eureka Server                       |
| **Config**            | Spring Cloud Config Server          |
| **Secrets**           | TechDeveloper Secret Manager Client |
| **API Docs**          | Swagger / OpenAPI 3.0               |
| **Namespace**         | `{repo_info['project_name']}`       |

### Dependency Chain

```text
techdeveloper-common-utility
  └── techdeveloper-secret-manager-client
       └── {repo_info['project_name']}-common-utility
            └── {name}  ← this service
```

## API Endpoints

Base path: `/api/v1/[resource]`

### CRUD Operations

| Method   | Path                 | Description                  |
|----------|----------------------|------------------------------|
| `POST`   | `/`                  | Create a new [resource]      |
| `GET`    | `/{{id}}`            | Get [resource] by ID         |
| `GET`    | `/`                  | Get all [resources]          |
| `PUT`    | `/{{id}}`            | Update a [resource]          |
| `DELETE` | `/{{id}}`            | Delete a [resource]          |

## Configuration

### application.yml (Service-Specific)

**ONLY this configuration in service:**

```yaml
spring:
  application:
    name: {name}
  config:
    import: "configserver:http://localhost:8888"
  cloud:
    config:
      fail-fast: true
      retry:
        enabled: true

secret-manager:
  client:
    enabled: true
    project-name: "{repo_info['project_name']}"
    base-url: "http://localhost:8085/api/v1/secrets"
```

### Config Server Configuration

**Location:** `techdeveloper-config-server/configurations/{repo_info['project_name']}/services/{name}.yml`

**All other configs go here:**
- Database connection
- Redis configuration
- Feign client settings
- Port number
- Logging levels

## Local Development

### Prerequisites

- Java 21 or higher
- Maven 3.9+
- PostgreSQL 15+ (running on localhost:5432)
- Central services running (Config Server, Eureka, Secret Manager)

### Build & Run

**Start central services first:**

```bash
# 1. Config Server (MUST be first)
cd techdeveloper/backend/techdeveloper-config-server
mvn spring-boot:run

# 2. Eureka Server
cd techdeveloper/backend/techdeveloper-eureka-server
mvn spring-boot:run

# 3. Secret Manager
cd techdeveloper/backend/techdeveloper-secret-manager-service
mvn spring-boot:run
```

**Build common utility (if not already built):**

```bash
cd {repo_info['project_name']}/backend/{repo_info['project_name']}-common-utility
mvn clean install -DskipTests
```

**Run this service:**

```bash
cd {repo_info['project_name']}/backend/{name}
mvn clean install -DskipTests
mvn spring-boot:run
```

**Service will be available at:** `http://localhost:[PORT]`

### Testing

```bash
# Unit tests
mvn test

# Integration tests
mvn verify

# Skip tests
mvn clean install -DskipTests
```

### API Documentation

**Swagger UI:** `http://localhost:[PORT]/swagger-ui.html`

## Docker

### Build Docker Image

```bash
docker build -t 148.113.197.135:5000/{name}:1.0.0 .
```

### Push to Registry

```bash
docker push 148.113.197.135:5000/{name}:1.0.0
```

### Run Locally

```bash
docker run -p [PORT]:[PORT] \\
  -e SPRING_PROFILES_ACTIVE=dev \\
  148.113.197.135:5000/{name}:1.0.0
```

## Jenkins CI/CD

### Pipeline Stages

1. **Build** - Maven clean install
2. **Test** - Run unit and integration tests
3. **Docker Build** - Build Docker image
4. **Docker Push** - Push to private registry
5. **Deploy to K8s** - Deploy to Kubernetes cluster

### Jenkinsfile

```groovy
pipeline {{
    agent any
    stages {{
        stage('Build') {{ ... }}
        stage('Test') {{ ... }}
        stage('Docker Build') {{ ... }}
        stage('Docker Push') {{ ... }}
        stage('Deploy to K8s') {{ ... }}
    }}
}}
```

## Kubernetes Deployment

### Deploy to K8s

```bash
kubectl apply -f kubernetes/{name}-deployment.yaml
kubectl apply -f kubernetes/{name}-service.yaml
```

### Check Status

```bash
kubectl get pods -n {repo_info['project_name']}
kubectl get svc -n {repo_info['project_name']}
kubectl logs -f deployment/{name} -n {repo_info['project_name']}
```

### Namespace

**All resources deployed to:** `{repo_info['project_name']}`

## Troubleshooting

### Service Not Starting

**Check Config Server:**
```bash
curl http://localhost:8888/actuator/health
curl http://localhost:8888/{name}/default
```

**Check Eureka Registration:**
```bash
curl http://localhost:8761/
```

### Database Connection Failed

**Verify PostgreSQL:**
```bash
psql -U postgres -l | grep {repo_info['project_name']}
```

**Check credentials in Config Server and Secret Manager**

### Port Already in Use

```bash
# Find process
netstat -ano | findstr :[PORT]

# Kill process (Windows)
taskkill /PID <PID> /F
```

---

**Version:** 1.0.0
**Last Updated:** {self._get_current_date()}
**Status:** 🟢 Active Development
"""

        elif repo_info['is_frontend']:
            # Frontend README
            content = f"""# {name.replace('-', ' ').title()}

Frontend application for the {repo_info.get('project_name', 'project').capitalize()} platform, built with Angular 19.

## Table of Contents

- [Architecture](#architecture)
- [Getting Started](#getting-started)
- [Development](#development)
- [Build](#build)
- [Docker](#docker)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

## Architecture

| Component        | Details              |
|------------------|----------------------|
| **Framework**    | Angular 19           |
| **Language**     | TypeScript           |
| **UI Library**   | Angular Material     |
| **State**        | RxJS                 |
| **Build Tool**   | Angular CLI          |
| **Dev Port**     | 4200                 |

## Getting Started

### Prerequisites

- Node.js 20 or higher
- npm 10 or higher
- Angular CLI 19

### Install Dependencies

```bash
npm install
```

### Development Server

```bash
ng serve
```

Navigate to `http://localhost:4200/`

## Development

### Project Structure

```text
src/
├── app/
│   ├── components/     # Reusable components
│   ├── pages/          # Page components
│   ├── services/       # API services
│   ├── models/         # TypeScript interfaces
│   ├── guards/         # Route guards
│   └── interceptors/   # HTTP interceptors
├── assets/             # Static assets
├── environments/       # Environment configs
└── styles/             # Global styles
```

### Code Scaffolding

```bash
# Generate component
ng generate component components/my-component

# Generate service
ng generate service services/my-service

# Generate module
ng generate module modules/my-module
```

### Running Tests

```bash
# Unit tests
ng test

# E2E tests
ng e2e
```

## Build

### Development Build

```bash
ng build
```

### Production Build

```bash
ng build --configuration production
```

Output: `dist/{name}/`

## Docker

### Build Docker Image

```bash
docker build -t 148.113.197.135:5000/{name}:1.0.0 .
```

### Push to Registry

```bash
docker push 148.113.197.135:5000/{name}:1.0.0
```

### Run Locally

```bash
docker run -p 80:80 148.113.197.135:5000/{name}:1.0.0
```

## Deployment

### Kubernetes

```bash
kubectl apply -f kubernetes/{name}-deployment.yaml
kubectl apply -f kubernetes/{name}-service.yaml
kubectl apply -f kubernetes/{name}-ingress.yaml
```

### Nginx Configuration

Angular SPA requires history API fallback:

```nginx
location / {{
    try_files $uri $uri/ /index.html;
}}
```

## Troubleshooting

### Build Errors

```bash
# Clear cache
rm -rf node_modules package-lock.json
npm install
```

### Port Already in Use

```bash
# Kill process on port 4200
npx kill-port 4200
```

### Module Not Found

```bash
npm install
ng serve --poll=2000
```

---

**Version:** 1.0.0
**Last Updated:** {self._get_current_date()}
**Status:** 🟢 Active Development
"""

        else:
            # Generic README
            content = f"""# {name.replace('-', ' ').title()}

[PROJECT DESCRIPTION]

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
- [Development](#development)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

## Overview

[Describe what this project/service does]

## Architecture

[Describe the architecture, dependencies, and key components]

## Getting Started

### Prerequisites

[List prerequisites]

### Installation

[Installation steps]

### Running Locally

[How to run locally]

## Development

[Development guidelines, code structure, testing]

## Deployment

[Deployment instructions]

## Troubleshooting

[Common issues and solutions]

---

**Version:** 1.0.0
**Last Updated:** {self._get_current_date()}
**Status:** 🟢 Active Development
"""

        return content

    def generate_claude_md_content(self, repo_info: Dict) -> str:
        """Generate comprehensive CLAUDE.md content"""
        name = repo_info['name']

        if repo_info['is_backend_service']:
            # Backend service CLAUDE.md
            service_name = repo_info['service_name']
            project_name = repo_info['project_name'].capitalize()

            content = f"""# {name} - Claude Code Instructions

**Service:** {project_name} {service_name.replace('-', ' ').title()}
**Type:** Spring Boot Microservice
**Status:** 🟢 Active Development

---

## 📋 SERVICE OVERVIEW

**Purpose:** [Describe service purpose and responsibilities]

**Part of:** {project_name} E-Commerce Platform

**Important:** This file provides **ADDITIONAL** service-specific context. It does **NOT** override global CLAUDE.md policies or project-level CLAUDE.md instructions.

---

## 🏗️ PROJECT STRUCTURE

### Directory Layout

```text
{name}/
├── README.md                                # Service documentation
├── CLAUDE.md                                # This file (Claude instructions)
├── pom.xml                                  # Maven configuration
├── Dockerfile                               # Docker build
├── Jenkinsfile                              # CI/CD pipeline
├── kubernetes/                              # K8s manifests
│   ├── deployment.yaml
│   ├── service.yaml
│   └── ingress.yaml
└── src/
    ├── main/
    │   ├── java/
    │   │   └── com/
    │   │       └── techdeveloper/
    │   │           └── {repo_info['project_name']}/
    │   │               └── {service_name.split('-')[0]}/
    │   │                   ├── controller/           # REST endpoints
    │   │                   ├── dto/                  # Response objects
    │   │                   ├── form/                 # Request objects
    │   │                   ├── constants/            # Constants & enums
    │   │                   ├── services/             # Service interfaces
    │   │                   │   ├── impl/            # Implementations (package-private)
    │   │                   │   └── helper/          # Helper classes
    │   │                   ├── entity/               # JPA entities
    │   │                   ├── repository/           # Data access
    │   │                   └── config/               # Configuration
    │   └── resources/
    │       └── application.yml                       # Service config (minimal)
    └── test/
        └── java/                                     # Tests
```

### Git Repository

**This is a git repository** - `.git` folder exists here.

**Before ANY git command:**
```bash
test -d .git || echo "⚠️ No git repository in current directory"
```

---

## 🎯 SERVICE-SPECIFIC RULES

### 1. Service Configuration

**Base Package:**
```
com.techdeveloper.{repo_info['project_name']}.{service_name.split('-')[0]}
```

**Port:** `[PORT NUMBER]`

**Database Tables:** `[table_prefix]_*`

### 2. API Endpoints

**Base Path:** `/api/v1/[resource]`

**All endpoints follow:**
- ✅ REST conventions (GET, POST, PUT, DELETE)
- ✅ ApiResponseDto<T> for all responses
- ✅ Form validation with constants
- ✅ Swagger documentation

### 3. Configuration Management

**application.yml (ONLY THIS!):**
```yaml
spring:
  application:
    name: {name}
  config:
    import: "configserver:http://localhost:8888"
  cloud:
    config:
      fail-fast: true
      retry:
        enabled: true

secret-manager:
  client:
    enabled: true
    project-name: "{repo_info['project_name']}"
    base-url: "http://localhost:8085/api/v1/secrets"
```

**Config Server Path:**
```
techdeveloper-config-server/configurations/{repo_info['project_name']}/services/{name}.yml
```

**What goes in Config Server:**
- Database connection (datasource)
- Redis configuration
- Feign client settings
- Port number
- Logging configuration
- Service-specific properties

**❌ NEVER add to service application.yml:**
- Database configs
- Redis configs
- Port numbers
- Any environment-specific configs

### 4. Secret Management

**All secrets in Secret Manager (Port 1002)**

**Naming convention:**
```
{repo_info['project_name']}.{service_name}.{{secret-key}}
```

**Examples:**
- `{repo_info['project_name']}.{service_name}.api.key`
- `{repo_info['project_name']}.{service_name}.encryption.secret`

---

## 🔧 DEVELOPMENT WORKFLOW

### Starting This Service

**Prerequisites:**
1. ✅ Config Server running (localhost:8888)
2. ✅ Eureka Server running (localhost:8761)
3. ✅ Secret Manager running (localhost:1002)
4. ✅ PostgreSQL running (localhost:5432)
5. ✅ Common utility built

**Build & Run:**
```bash
# Build common utility first (if not built)
cd ../{repo_info['project_name']}-common-utility
mvn clean install -DskipTests

# Build and run this service
cd ../{name}
mvn clean install -DskipTests
mvn spring-boot:run
```

**Verify:**
```bash
# Health check
curl http://localhost:[PORT]/actuator/health

# Swagger
curl http://localhost:[PORT]/swagger-ui.html

# Eureka registration
curl http://localhost:8761/ | grep {name}
```

### Adding New Features

**1. Create Form (Request Validation):**
```java
package com.techdeveloper.{repo_info['project_name']}.{service_name.split('-')[0]}.form;

public class Create[Entity]Form extends ValidationMessageConstants {{
    @NotBlank(message = ValidationMessageConstants.[CONSTANT])
    private String fieldName;
}}
```

**2. Create DTO (Response):**
```java
package com.techdeveloper.{repo_info['project_name']}.{service_name.split('-')[0]}.dto;

public class [Entity]Dto {{
    private Long id;
    private String name;
}}
```

**3. Add Controller Endpoint:**
```java
@PostMapping
public ResponseEntity<ApiResponseDto<[Entity]Dto>> create(
    @Valid @RequestBody Create[Entity]Form form) {{
    [Entity]Dto entity = service.create(form);
    return ResponseEntity.ok(
        new ApiResponseDto<>(true, "Created successfully", entity)
    );
}}
```

**4. Update Service → Impl → Helper**

**5. Update README.md** with new endpoint documentation

---

## 📚 DEPENDENCIES

### Maven Dependencies

**From parent project ({repo_info['project_name']}-common-utility):**
- techdeveloper-common-utility
- techdeveloper-secret-manager-client
- Spring Boot starters
- PostgreSQL driver
- Lombok
- Validation

**Service-specific dependencies:**
- [Add service-specific dependencies here]

---

## 🐳 DOCKER & KUBERNETES

### Docker Image

**Registry:** `148.113.197.135:5000`

**Image name:** `148.113.197.135:5000/{name}:{{version}}`

**Build:**
```bash
docker build -t 148.113.197.135:5000/{name}:1.0.0 .
docker push 148.113.197.135:5000/{name}:1.0.0
```

### Kubernetes Deployment

**Namespace:** `{repo_info['project_name']}`

**Deployment:**
```bash
kubectl apply -f kubernetes/{name}-deployment.yaml -n {repo_info['project_name']}
kubectl apply -f kubernetes/{name}-service.yaml -n {repo_info['project_name']}
```

**Resource limits:**
- CPU: 500m
- Memory: 512Mi

**Health probes:**
- Liveness: `/actuator/health/liveness`
- Readiness: `/actuator/health/readiness`

---

## 🔍 TESTING

### Test Structure

```text
src/test/java/
├── controller/          # API tests
├── services/            # Business logic tests
└── repository/          # Data access tests
```

### Running Tests

```bash
# Unit tests
mvn test

# Integration tests
mvn verify

# Coverage report
mvn jacoco:report
```

---

## 🚨 SERVICE-SPECIFIC GOTCHAS

### 1. Config Server Dependency

**Must start BEFORE this service:**
- Config Server (8888)
- Eureka Server (8761)

**Startup will fail if Config Server is not available!**

### 2. Common Utility Dependency

**Must build common utility FIRST:**
```bash
cd ../{repo_info['project_name']}-common-utility
mvn clean install -DskipTests
```

### 3. Database Schema

**Tables are auto-created by Hibernate**

**Naming convention:**
- Table: `[table_prefix]_[entity_name]`
- Columns: snake_case

---

## 🎯 SERVICE-SPECIFIC CONVENTIONS

### API Response Format

**ALL endpoints return ApiResponseDto<T>:**

```json
{{
  "success": true,
  "message": "Operation successful",
  "data": {{ ... }}
}}
```

### Validation Messages

**ALL messages in constants:**
```java
public class ValidationMessageConstants {{
    public static final String [FIELD]_REQUIRED = "[Field] is required";
    public static final String [FIELD]_INVALID = "[Field] is invalid";
}}
```

### Audit Fields

**ALL entities extend AuditableEntity:**
```java
@Entity
public class [Entity] extends AuditableEntity {{
    // createdAt, updatedAt, createdBy, updatedBy inherited
}}
```

---

## 🔗 RELATED RESOURCES

### Project-Level

**Project CLAUDE.md:** `../{repo_info['project_name']}/CLAUDE.md`
**Project README:** `../{repo_info['project_name']}/README.md`

### Global Documentation

**Location:** `~/.claude/memory/docs/`

**Relevant docs:**
- `java-project-structure.md`
- `spring-cloud-config.md`
- `secret-management.md`
- `jpa-auditing-pattern.md`
- `centralized-auth-security-pattern.md`

---

## ✅ SUMMARY

**This CLAUDE.md provides:**
- ✅ Service-specific structure and configuration
- ✅ API endpoint patterns
- ✅ Development workflow (build, run, test)
- ✅ Docker/K8s deployment specifics
- ✅ Service-specific gotchas and conventions

**Global & project policies:**
- ✅ Applied automatically (NOT overridden)
- ✅ Inherited from global ~/.claude/CLAUDE.md
- ✅ Enhanced with project {repo_info['project_name']}/CLAUDE.md
- ✅ Merged with this service-specific context

---

**Service:** {name}
**Version:** 1.0.0
**Last Updated:** {self._get_current_date()}
**Status:** 🟢 Active Development
"""

        elif repo_info['is_frontend']:
            # Frontend CLAUDE.md
            content = f"""# {name} - Claude Code Instructions

**Application:** {name.replace('-', ' ').title()}
**Type:** Angular 19 Frontend
**Status:** 🟢 Active Development

---

## 📋 APPLICATION OVERVIEW

**Purpose:** Frontend application for [PROJECT] platform

**Important:** This file provides **ADDITIONAL** application-specific context. It does **NOT** override global CLAUDE.md policies.

---

## 🏗️ PROJECT STRUCTURE

### Directory Layout

```text
{name}/
├── README.md                    # Application documentation
├── CLAUDE.md                    # This file (Claude instructions)
├── package.json                 # Node dependencies
├── angular.json                 # Angular configuration
├── tsconfig.json                # TypeScript configuration
├── Dockerfile                   # Docker build
├── Jenkinsfile                  # CI/CD pipeline
├── kubernetes/                  # K8s manifests
└── src/
    ├── app/
    │   ├── components/          # Reusable components
    │   ├── pages/               # Page components
    │   ├── services/            # API services
    │   ├── models/              # TypeScript interfaces
    │   ├── guards/              # Route guards
    │   ├── interceptors/        # HTTP interceptors
    │   └── app.component.ts
    ├── assets/                  # Static assets
    ├── environments/            # Environment configs
    └── styles/                  # Global styles
```

### Git Repository

**This is a git repository** - `.git` folder exists here.

---

## 🎯 APPLICATION-SPECIFIC RULES

### 1. Development Server

**Port:** 4200
**URL:** http://localhost:4200

### 2. API Integration

**Base URL:**
- Development: `http://localhost:8085/api/v1`
- Production: `https://[domain]/api/v1`

**Gateway:** All API calls go through Gateway (port 8085)

### 3. Build Configuration

**Development:**
```bash
ng build
```

**Production:**
```bash
ng build --configuration production
```

---

## 🔧 DEVELOPMENT WORKFLOW

### Starting Application

```bash
# Install dependencies
npm install

# Start dev server
ng serve

# Open browser
http://localhost:4200
```

### Adding New Features

**1. Generate Component:**
```bash
ng generate component components/my-component
```

**2. Generate Service:**
```bash
ng generate service services/my-service
```

**3. Update Routing (if needed)**

### Testing

```bash
# Unit tests
ng test

# E2E tests
ng e2e
```

---

## 🐳 DOCKER & KUBERNETES

### Docker Image

**Registry:** `148.113.197.135:5000`
**Image:** `148.113.197.135:5000/{name}:{{version}}`

### Nginx Configuration

**SPA routing requires history API fallback:**

```nginx
location / {{
    try_files $uri $uri/ /index.html;
}}
```

---

## ✅ SUMMARY

**This CLAUDE.md provides:**
- ✅ Application-specific structure
- ✅ Development workflow
- ✅ Build and deployment specifics

**Global policies:** Apply automatically (NOT overridden)

---

**Application:** {name}
**Version:** 1.0.0
**Last Updated:** {self._get_current_date()}
**Status:** 🟢 Active Development
"""

        else:
            # Generic CLAUDE.md
            content = f"""# {name} - Claude Code Instructions

**Project:** {name.replace('-', ' ').title()}
**Type:** [PROJECT TYPE]
**Status:** 🟢 Active Development

---

## 📋 PROJECT OVERVIEW

[Describe project purpose and scope]

**Important:** This file provides **ADDITIONAL** project-specific context. It does **NOT** override global CLAUDE.md policies.

---

## 🏗️ PROJECT STRUCTURE

### Directory Layout

```text
{name}/
├── README.md                    # Project documentation
├── CLAUDE.md                    # This file (Claude instructions)
└── [PROJECT STRUCTURE]
```

---

## 🎯 PROJECT-SPECIFIC RULES

[Add project-specific rules, conventions, and guidelines]

---

## 🔧 DEVELOPMENT WORKFLOW

[Describe development workflow, build process, testing]

---

## ✅ SUMMARY

**This CLAUDE.md provides:**
- ✅ Project-specific context
- ✅ Development guidelines
- ✅ Project conventions

**Global policies:** Apply automatically (NOT overridden)

---

**Project:** {name}
**Version:** 1.0.0
**Last Updated:** {self._get_current_date()}
**Status:** 🟢 Active Development
"""

        return content

    def _get_current_date(self) -> str:
        """Get current date in YYYY-MM-DD format"""
        import datetime
        return datetime.datetime.now().strftime('%Y-%m-%d')

    def create_documentation(self, repo_path: Path, file_type: str, repo_info: Dict) -> bool:
        """Create comprehensive documentation file"""
        try:
            if file_type == 'README':
                file_path = repo_path / 'README.md'
                content = self.generate_readme_content(repo_info)
                self.results['created_readme'].append(str(repo_path))
            elif file_type == 'CLAUDE':
                file_path = repo_path / 'CLAUDE.md'
                content = self.generate_claude_md_content(repo_info)
                self.results['created_claude_md'].append(str(repo_path))
            else:
                return False

            file_path.write_text(content, encoding='utf-8')
            return True

        except Exception as e:
            print(f"Error creating {file_type} for {repo_path}: {e}")
            return False

    def update_documentation(self, repo_path: Path, file_type: str, repo_info: Dict) -> bool:
        """Update non-comprehensive documentation file"""
        # For now, we'll backup the old file and create a new comprehensive one
        try:
            if file_type == 'README':
                file_path = repo_path / 'README.md'
                backup_path = repo_path / 'README.md.backup'
                content = self.generate_readme_content(repo_info)
                self.results['updated_readme'].append(str(repo_path))
            elif file_type == 'CLAUDE':
                file_path = repo_path / 'CLAUDE.md'
                backup_path = repo_path / 'CLAUDE.md.backup'
                content = self.generate_claude_md_content(repo_info)
                self.results['updated_claude_md'].append(str(repo_path))
            else:
                return False

            # Backup existing file
            if file_path.exists():
                import shutil
                shutil.copy2(file_path, backup_path)

            # Write new comprehensive content
            file_path.write_text(content, encoding='utf-8')
            return True

        except Exception as e:
            print(f"Error updating {file_type} for {repo_path}: {e}")
            return False

    def run(self, auto_create: bool = False, auto_update: bool = False) -> Dict:
        """
        Run comprehensive documentation check

        Args:
            auto_create: Automatically create missing files
            auto_update: Automatically update non-comprehensive files

        Returns:
            Results dictionary
        """
        print("=" * 80)
        print("COMPREHENSIVE DOCUMENTATION CHECKER")
        print("=" * 80)
        print(f"Scanning: {self.root_path}")
        print()

        # Find all git repos
        repos = self.find_git_repos()
        print(f"Found {len(repos)} git repositories")
        print()

        # Check each repo
        for repo in repos:
            print(f"Checking: {repo.name}")
            repo_info = self.get_repo_info(repo)
            result = self.check_repo(repo)

            # Display results
            print(f"  README.md: {'✅' if result['has_readme'] else '❌'} ", end='')
            if result['has_readme']:
                if result['readme_comprehensive']:
                    print("(Comprehensive)")
                else:
                    print(f"(Not comprehensive: {result['readme_reason']})")
                    if auto_update:
                        print(f"  → Updating README.md...")
                        self.update_documentation(repo, 'README', repo_info)
            else:
                print("(Missing)")
                if auto_create:
                    print(f"  → Creating README.md...")
                    self.create_documentation(repo, 'README', repo_info)

            print(f"  CLAUDE.md: {'✅' if result['has_claude_md'] else '❌'} ", end='')
            if result['has_claude_md']:
                if result['claude_md_comprehensive']:
                    print("(Comprehensive)")
                else:
                    print(f"(Not comprehensive: {result['claude_md_reason']})")
                    if auto_update:
                        print(f"  → Updating CLAUDE.md...")
                        self.update_documentation(repo, 'CLAUDE', repo_info)
            else:
                print("(Missing)")
                if auto_create:
                    print(f"  → Creating CLAUDE.md...")
                    self.create_documentation(repo, 'CLAUDE', repo_info)

            print()

        # Summary
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Repositories checked: {self.results['checked']}")
        print(f"Missing README.md: {len(self.results['missing_readme'])}")
        print(f"Missing CLAUDE.md: {len(self.results['missing_claude_md'])}")
        print(f"Non-comprehensive README.md: {len(self.results['non_comprehensive_readme'])}")
        print(f"Non-comprehensive CLAUDE.md: {len(self.results['non_comprehensive_claude_md'])}")

        if auto_create:
            print(f"\nCreated README.md: {len(self.results['created_readme'])}")
            print(f"Created CLAUDE.md: {len(self.results['created_claude_md'])}")

        if auto_update:
            print(f"\nUpdated README.md: {len(self.results['updated_readme'])}")
            print(f"Updated CLAUDE.md: {len(self.results['updated_claude_md'])}")

        print("=" * 80)

        return self.results


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Check and create comprehensive documentation in all git repos"
    )
    parser.add_argument(
        'path',
        help='Root path to scan for git repositories'
    )
    parser.add_argument(
        '--auto-create',
        action='store_true',
        help='Automatically create missing documentation files'
    )
    parser.add_argument(
        '--auto-update',
        action='store_true',
        help='Automatically update non-comprehensive files'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )

    args = parser.parse_args()

    # Run checker
    checker = DocumentationChecker(args.path)
    results = checker.run(
        auto_create=args.auto_create,
        auto_update=args.auto_update
    )

    # Output JSON if requested
    if args.json:
        print(json.dumps(results, indent=2))

    # Exit code based on findings
    if (len(results['missing_readme']) > 0 or
        len(results['missing_claude_md']) > 0 or
        len(results['non_comprehensive_readme']) > 0 or
        len(results['non_comprehensive_claude_md']) > 0):
        sys.exit(1)  # Issues found
    else:
        sys.exit(0)  # All good


if __name__ == '__main__':
    main()
