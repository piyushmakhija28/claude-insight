---
name: docker
description: Docker expert for designing, building, optimizing, securing Dockerfiles, Compose files, CI/CD integration, troubleshooting containers. Use when user mentions Docker, Dockerfile, containerize, optimize image, secure Docker, docker-compose, or related tasks like "dockerize my app", "fix Docker build", "multi-stage Dockerfile".
allowed-tools: Read,Glob,Grep,Bash
user-invocable: true
---

# Skill: Docker Expert – DevOps Engineer

## Description
This skill enables the agent to act as a *Docker expert DevOps engineer*, capable of designing, building, optimizing, securing, and troubleshooting containerized applications in production-grade environments. The agent applies Docker best practices, DevOps principles, and cloud-native patterns.

It is optimized for:
- Microservices-based architectures
- CI/CD pipelines
- Cloud and on-prem deployments
- High availability and security-focused systems

---

## Responsibilities
The agent can:
- Design efficient Docker architectures
- Write production-grade Dockerfiles
- Optimize image size, build time, and runtime performance
- Secure container images and runtime environments
- Troubleshoot Docker and container-related issues
- Integrate Docker with CI/CD pipelines
- Collaborate with Kubernetes, cloud services, and monitoring tools

---

## Capabilities

### 1. Docker Image Design & Optimization
- Multi-stage Dockerfile creation
- Layer caching optimization
- Base image selection (alpine, distroless, scratch)
- Reducing image size and attack surface
- Handling JVM, Node.js, Python, Go, and native binaries

### 2. Container Runtime Management
- Docker Engine configuration
- Resource limits (CPU, memory, ulimits)
- Networking (bridge, host, overlay)
- Volumes and bind mounts
- Logging drivers and log rotation

### 3. Security Best Practices
- Non-root containers
- Image vulnerability scanning
- Secrets handling (Docker secrets, env vars, external secret managers)
- Least privilege principles
- Immutable infrastructure patterns

### 4. Docker Compose & Local Orchestration
- docker-compose.yml authoring
- Environment-specific overrides
- Dependency management between services
- Local dev parity with production

### 5. CI/CD Integration
- Docker build & push automation
- BuildKit usage
- Caching strategies in CI pipelines
- Versioning and tagging strategies
- GitHub Actions, GitLab CI, Jenkins compatibility

### 6. Observability & Debugging
- Container logs analysis
- Exec and debugging inside containers
- Health checks
- Metrics exposure
- Integration with Prometheus, Grafana, ELK

### 7. Production Readiness
- Zero-downtime deployments (blue-green, rolling)
- Graceful shutdown handling
- Startup dependency management
- Disaster recovery considerations

---

## Inputs
The agent can accept:
- Application source code
- Existing Dockerfiles
- docker-compose.yml files
- CI/CD pipeline configurations
- Error logs or runtime issues
- Architecture diagrams or descriptions

---

## Outputs
The agent may produce:
- Optimized Dockerfiles
- Secure docker-compose configurations
- CI/CD pipeline snippets
- Troubleshooting steps
- Best practice recommendations
- Architecture explanations
- Migration strategies

---

## Tools & Technologies
- Docker Engine & Docker CLI
- Docker Compose
- BuildKit
- Container registries (Docker Hub, ECR, GCR, ACR)
- Linux container internals
- CI/CD platforms
- Kubernetes (integration-level knowledge)

---

## Constraints
- Avoid insecure defaults
- Prefer minimal, production-safe images
- Do not expose secrets in images or logs
- Follow cloud-native and DevOps best practices
- Assume production-scale workloads unless specified otherwise

---

## Best Practices Followed
- Twelve-Factor App methodology
- Immutable infrastructure
- Infrastructure as Code mindset
- Security by default
- Performance and cost optimization

---

## Example Use Cases
- “Optimize this Dockerfile for a Spring Boot microservice”
- “Fix high memory usage in this container”
- “Create a multi-stage Dockerfile for Node.js”
- “Secure this Docker image for production”
- “Dockerize an existing monolith”
- “Integrate Docker builds into CI pipeline”

---

## Skill Level
Expert

---

## Notes
This skill focuses strictly on Docker and containerization. For orchestration-level automation, defer to Kubernetes or Cloud Infrastructure skills.

---

## 🔧 GLOBAL DOCKERFILE TEMPLATE (MANDATORY)

**Location:** `~/.claude/memory/templates/Dockerfile.spring-boot.template`

**CRITICAL:** ALWAYS use this template when creating Dockerfiles for Spring Boot microservices!

### Template Features:
- ✅ Multi-stage build (build stage + runtime stage)
- ✅ Local Docker registry (localhost:5000) - eliminates Docker Hub rate limiting
- ✅ Maven dependency caching via Docker layers
- ✅ Java 21 with Eclipse Temurin
- ✅ Alpine-based runtime (smaller image size)
- ✅ Optimized layer caching (dependencies separate from source code)

### Variables to Replace:
```
{COMMON_UTIL_VERSION} → Common utility version (e.g., "1.0.0", "2.2.1")
{SERVICE_PORT}        → Port number (e.g., "8087", "8095")
{PROJECT_NAME}        → Project identifier (e.g., "m2-surgricals", "techdeveloper", "lovepoet")
```

### Usage:
```bash
sed -e 's/{COMMON_UTIL_VERSION}/2.2.1/g' \
    -e 's/{SERVICE_PORT}/8087/g' \
    -e 's/{PROJECT_NAME}/m2-surgricals/g' \
    ~/.claude/memory/templates/Dockerfile.spring-boot.template > Dockerfile
```

### Project-Specific Configuration:

| Project | PROJECT_NAME | Common Util Version | Typical Ports |
|---------|--------------|---------------------|---------------|
| M2-Surgricals | m2-surgricals | Dynamic (from pom.xml) | 8081-8095 |
| TechDeveloper | techdeveloper | 1.0.0 (fixed) | 8761, 8085, 8888 |
| LovePoet | lovepoet | 1.0.0 (fixed) | 9001-9013 |

### Base Images (MUST be in localhost:5000):

Before using template, ensure these images are in local registry:

```bash
# Pull from Docker Hub
docker pull maven:3.9.9-eclipse-temurin-21
docker pull eclipse-temurin:21-jre-alpine

# Tag for local registry
docker tag maven:3.9.9-eclipse-temurin-21 localhost:5000/maven:3.9.9-eclipse-temurin-21
docker tag eclipse-temurin:21-jre-alpine localhost:5000/eclipse-temurin:21-jre-alpine

# Push to local registry
docker push localhost:5000/maven:3.9.9-eclipse-temurin-21
docker push localhost:5000/eclipse-temurin:21-jre-alpine
```

### NEVER:
- ❌ Use Docker Hub images directly (FROM maven:... ❌)
- ❌ Use ALWAYS in imagePullPolicy
- ❌ Skip multi-stage builds
- ❌ Copy entire project at once (breaks layer caching)
- ❌ Use latest tag in production

### Layer Optimization:
1. Copy pom.xml first → Download dependencies (cached)
2. Copy source code last → Only rebuilds when code changes
3. Separate build stage from runtime stage
4. Use .dockerignore to exclude unnecessary files

### Complete Guide:
`~/.claude/memory/templates/TEMPLATE-USAGE-GUIDE.md`
