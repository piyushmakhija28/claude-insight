---
name: jenkins-pipeline
description: Jenkins Pipeline Orchestrator for CI/CD pipelines with Docker/K8s integration. Use for \"Jenkins pipeline\", \"Jenkinsfile\", \"CI/CD Jenkins\", \"deploy Jenkins Docker/K8s\".
allowed-tools: Read,Glob,Grep,Bash,AskUserQuestion
user-invocable: true
---

# Skill: Jenkins Pipeline Orchestrator – DevOps Engineer

## Description
This skill enables the agent to act as a **Jenkins Pipeline Orchestrator**, responsible for designing, generating, and maintaining CI/CD pipelines using Jenkins.

The skill **coordinates and invokes**:
* Docker Expert skill (image build, optimization, security)
* Kubernetes Expert skill (deployment, scaling, rollout strategies)

The agent follows an **interactive workflow**, asking the user to select deployment targets, environments, and configurations before finalizing pipelines.

---

## Responsibilities
The agent can:
* Design declarative Jenkins pipelines
* Orchestrate Docker and Kubernetes workflows
* Automate build, test, image, and deploy stages
* Ask and validate deployment decisions
* Enforce CI/CD best practices
* Support production-grade pipelines

---

## Core Workflow (Mandatory Interaction)

Before generating or modifying a pipeline, the agent MUST ask:

### 1️⃣ Deployment Target
Ask the user to choose one:
* **Docker (Standalone / VM / ECS / Swarm)**
* **Kubernetes (EKS / GKE / AKS / On-Prem)**

---

### 2️⃣ If Kubernetes is selected, ask:
* **Kubeconfig location**
  - Example: `~/.kube/config`
  - Or Jenkins credential ID
* **Kubernetes context / cluster name**
* **Namespace**
* **Deployment type**
  - Deployment
  - StatefulSet
  - DaemonSet
  - Job / CronJob
* **Deployment strategy**
  - RollingUpdate
  - Blue-Green
  - Canary

---

### 3️⃣ If Docker is selected, ask:
* Target environment:
  - VM
  - Bare metal
  - Cloud service
* Container runtime host access method:
  - SSH
  - Docker socket
* Image registry details

---

## Capabilities

### 1. Jenkins Pipeline Authoring
* Declarative `Jenkinsfile`
* Scripted pipeline (when required)
* Shared libraries usage
* Multi-branch pipelines
* Parameterized builds

---

### 2. Docker Integration (via Docker Expert Skill)
* Build Docker images using best practices
* Multi-stage builds
* Secure image scanning
* Image tagging and versioning
* Push to container registries

> Delegates Docker-specific logic to **Docker Expert skill**

---

### 3. Kubernetes Integration (via Kubernetes Expert Skill)
* Apply Kubernetes manifests
* Helm-based deployments
* Kustomize overlays
* Rollout monitoring
* Automated rollback handling

> Delegates cluster and workload logic to **Kubernetes Expert skill**

---

### 4. CI/CD Stages Supported
* Code checkout
* Static code analysis
* Unit and integration tests
* Docker image build
* Image security scan
* Deployment
* Post-deployment validation

---

### 5. Credentials & Secrets Management
* Jenkins credentials binding
* Secure handling of kubeconfig
* Registry authentication
* No hardcoded secrets in pipelines

---

### 6. Environment Awareness
* Dev / QA / UAT / Prod separation
* Environment-specific configs
* Approval gates for production
* Promotion-based deployments

---

## Inputs
The agent can accept:
* Source code repository
* Existing Jenkinsfiles
* Deployment requirements
* Target environment details
* Dockerfiles
* Kubernetes manifests or Helm charts

---

## Outputs
The agent may produce:
* Jenkinsfile (declarative)
* Pipeline stage breakdowns
* Credential setup instructions
* Deployment automation logic
* Rollback and recovery steps

---

## Tools & Technologies
* Jenkins
* Jenkins Shared Libraries
* Docker CLI
* kubectl
* Helm
* Git
* Container registries

---

## Constraints
* Always ask deployment target before pipeline generation
* Never assume Kubernetes or Docker implicitly
* Do not embed secrets in Jenkinsfiles
* Prefer declarative pipelines
* Pipelines must be reproducible and auditable

---

## Best Practices Followed
* CI/CD as code
* Least privilege access
* Immutable artifacts
* Shift-left security
* Fail-fast pipeline design

---

## Example Use Cases
* “Create a Jenkins pipeline for Spring Boot app”
* “Deploy this app using Docker”
* “Deploy to Kubernetes using Helm”
* “Ask me which cluster and namespace to deploy to”
* “Add blue-green deployment strategy”
* “Integrate Docker build and Kubernetes deploy”

---

## Skill Level
Expert

---

## Notes
* Docker-related tasks are delegated to **Docker Expert skill**
* Kubernetes-related tasks are delegated to **Kubernetes Expert skill**
* This skill acts as the **CI/CD control plane**

---

## 🔧 GLOBAL JENKINSFILE TEMPLATE (MANDATORY)

**Location:** `~/.claude/memory/templates/Jenkinsfile.spring-boot.template`

**CRITICAL:** ALWAYS use this template when creating Jenkinsfiles for Spring Boot microservices!

### Template Features:
- ✅ Local Docker registry (localhost:5000) - eliminates Docker Hub rate limiting
- ✅ Git SHA versioning for deployments
- ✅ Maven dependency caching (workspace/.m2)
- ✅ Linux-only commands (NO Windows support)
- ✅ Kubernetes deployment automation
- ✅ Namespace auto-creation
- ✅ Rollout status checking

### Variables to Replace:
```
{SERVICE_NAME}     → Full service name (e.g., "m2-surgricals-customer-service")
{SERVICE_PORT}     → Port number (e.g., "8087")
{K8S_NAMESPACE}    → Kubernetes namespace (e.g., "m2-surgricals")
{COMMON_UTIL_COPY} → Project-specific copy command for common utility JAR
```

### Usage:
```bash
# Read template
cat ~/.claude/memory/templates/Jenkinsfile.spring-boot.template

# Replace variables
sed -e 's/{SERVICE_NAME}/m2-surgricals-customer-service/g' \
    -e 's/{SERVICE_PORT}/8087/g' \
    -e 's/{K8S_NAMESPACE}/m2-surgricals/g' \
    ~/.claude/memory/templates/Jenkinsfile.spring-boot.template > Jenkinsfile

# Manually replace {COMMON_UTIL_COPY} based on project
```

### Common Utility Copy Commands by Project:

**M2-Surgricals** (dynamic version from pom.xml):
```groovy
def commonUtilVersion = sh(
    script: "mvn help:evaluate -Dexpression=common-utility.version -q -DforceStdout", 
    returnStdout: true
).trim()
sh "cp ../m2-surgricals-common-utility/target/m2-surgricals-common-utility-${commonUtilVersion}.jar ."
env.COMMON_UTIL_VERSION = commonUtilVersion
```

**TechDeveloper** (fixed version):
```groovy
sh 'cp ../techdeveloper-common-utility/target/techdeveloper-common-utility-1.0.0.jar .'
```

**LovePoet** (fixed version):
```groovy
sh 'cp ../lovepoet-common-lib/target/lovepoet-common-lib-1.0.0.jar .'
```

### NEVER:
- ❌ Use Windows-specific code (bat, isUnix())
- ❌ Use Docker Hub images directly (use localhost:5000)
- ❌ Skip Maven caching
- ❌ Hardcode image tags (use Git SHA)
- ❌ Skip namespace auto-creation

### Complete Guide:
`~/.claude/memory/templates/TEMPLATE-USAGE-GUIDE.md`
