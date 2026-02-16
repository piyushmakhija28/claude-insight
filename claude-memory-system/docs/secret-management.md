# Secret Management Ecosystem (Custom Vault-Like System)

**🚨 CRITICAL: Centralized secret management for ALL microservices! 🚨**

## Overview

Custom-built, enterprise-grade secret management (similar to HashiCorp Vault):
- ✅ AES-256 encryption at rest
- ✅ Auto-injection at microservice startup
- ✅ Project-based isolation (multi-tenancy)
- ✅ Version control & audit logging

## System Components

```
C:\Users\techd\Documents\workspace-spring-tool-suite-4-4.27.0-new\techdeveloper\backend\
├── techdeveloper-client-management-system/      # Manages clients
├── techdeveloper-project-management-system/     # Manages projects (port 8109)
├── techdeveloper-secret-manager/                # Stores secrets (port 1002)
└── techdeveloper-secret-manager-client/         # Client SDK (Maven dependency)
```

## Data Model

```
Client (1) ←→ (N) Project
Project (1) ←→ (N) Secret
Secret (1) ←→ (N) SecretVersion
```

## API Endpoints

```bash
# Get secrets for project
GET /api/v1/secrets/project/{projectId}?includeValues=true

# Create secret
POST /api/v1/secrets
{
  "projectId": 1,
  "secretKey": "DATABASE_PASSWORD",
  "secretValue": "postgres123",
  "secretType": "DATABASE"
}

# Update/Delete
PUT /api/v1/secrets/{secretId}
DELETE /api/v1/secrets/{secretId}
```

## Microservice Configuration

**Maven Dependency:**
```xml
<dependency>
    <groupId>com.techdeveloper</groupId>
    <artifactId>techdeveloper-secret-manager-client</artifactId>
    <version>1.0.0</version>
</dependency>
```

**application.yml:**
```yaml
secret-manager:
  client:
    enabled: true
    project-name: "m2-surgricals"
    base-url: "http://localhost:8085/api/v1/secrets"
    project-service-url: "http://localhost:8085/api/v1/projects"
    service-name: "m2-surgricals-customer-service"
    connection-timeout: 5000
    read-timeout: 10000
    cache-enabled: true
    cache-ttl-minutes: 30
```

## How It Works

```
1. Microservice Startup
   ↓
2. SecretManagerEnvironmentPostProcessor Triggered (BEFORE ApplicationContext)
   ↓
3. Resolve Project ID (GET /api/v1/projects)
   ↓
4. Fetch Secrets (GET /api/v1/secrets/project/{id}?includeValues=true)
   ↓
5. Inject into Spring Environment as properties
   ↓
6. Config Server resolves ${SECRET_KEY} placeholders
   ↓
7. Application starts with secrets available
```

## Fallback Mechanism

Primary (via Gateway): `http://localhost:8085/api/v1/...`
Fallback (direct):
- Project API: `http://localhost:8109/api/v1/projects`
- Secret API: `http://localhost:1002/api/v1/secrets`

## Secret Types

```java
DATABASE, SMTP, API_KEY, OAUTH, ENCRYPTION_KEY, PAYMENT, SMS, CLOUD, CUSTOM
```

## Best Practices

**DO:**
- ✅ Store ALL sensitive data in Secret Manager
- ✅ Use descriptive keys (e.g., `M2_DATABASE_PASSWORD`)
- ✅ Use placeholder syntax: `${SECRET_KEY}`
- ✅ Project-based isolation

**DON'T:**
- ❌ Hardcode secrets in code/configs
- ❌ Commit secrets to Git
- ❌ Share secrets across projects

## Troubleshooting

**Secrets not loading:**
1. Check `secret-manager.client.enabled=true`
2. Verify `project-name` matches DB
3. Check services running (ports 1002, 8109)

**"Could not resolve projectId":**
1. Verify project exists in DB
2. Check case sensitivity
3. Verify API accessible

**🚨 GOLDEN RULE: ALL sensitive data goes in Secret Manager - NEVER hardcode! 🚨**
