I need to setup Kubernetes deployment, Docker configuration, and a simplified Jenkins CI/CD pipeline for the current Spring Boot project. You MUST follow the exact architecture, naming conventions, and file patterns used in eureka-server and techdeveloper-config-server, while adapting resource limits to this specific service.

Here are the strict requirements:

1. Analysis & Context
Check for Secrets: Analyze 
pom.xml
 and application.yml.
IF the service requires database/external credentials: Add techdeveloper-secret-manager-client dependency and configure SECRET_MANAGER_CLIENT_BASE_URL.
IF standalone (like Eureka/Config Server): Do NOT add the client.
If NOT FOUND locally, you MUST check the techdeveloper-config-server repository for the service's configuration file (service-name.yml) to find the correct port.
Determine Resource Needs: Analyze the service complexity to determine appropriate Docker/K8s resource limits (Lightweight vs Heavyweight).
Check for Common Utility & Secret Manager Client:
IF the service depends on techdeveloper-common-utility:
You MUST follow the "Copy Pattern":
Jenkins: Do NOT build the utility. Copy the pre-built JAR from ../techdeveloper-common-utility/target/.
Dockerfile: Copy the JAR into the image and use mvn install:install-file to install it to the container's local repo.
IF the service depends on techdeveloper-secret-manager-client:
You MUST follow the "Copy Pattern":
Jenkins: Do NOT build the client. Copy the pre-built JAR from ../techdeveloper-secret-manager/techdeveloper-secret-manager-client/target/ (or appropriate path).
Dockerfile: Copy the JAR into the image and use mvn install:install-file to install it to the container's local repo.
2. Docker Configuration
Dockerfile: Create a multi-stage Dockerfile (Maven Build -> JRE Runtime).
IF Common Utility or Secret Client Dependency:
COPY dependency.jar /tmp/
RUN mvn install:install-file ...
Security: You MUST use numeric UID/GID 1000:1000.
Create user/group spring.
.dockerignore: Create a comprehensive file matching the eureka-server pattern.
Exclude: target/, .mvn/, .git/, .settings/, 
.classpath
, 
.project
, .factorypath, .vscode/, .idea/, *.iml, *.log, *.md (except README.md).
docker-compose.yml: Create for local development.
Network: Use external network microservices-network.
Healthcheck: Use wget or curl on /actuator/health.
JVM Options: Set -Xms and -Xmx based on your analysis (e.g., 256m/512m for basic apis, 512m/1g for heavy processing).
3. Kubernetes Manifests (k8s/ folder)
Create standard Kustomize-compatible manifests in k8s/:

namespace.yaml: Namespace techdeveloper.
deployment.yaml:
Image: project-name:latest (PullPolicy: IfNotPresent).
Security Context: runAsNonRoot: true, runAsUser: 1000, runAsGroup: 1000, fsGroup: 1000, Drop ALL capabilities.
Probes: Liveness & Readiness on /actuator/health (InitialDelay: ~60s).
Resources: Define Requests and Limits aligned with your chosen JVM options (ensure Limits > JVM Max Memory).
Annotations: prometheus.io/scrape: "true", port, path.
service.yaml:
Type: LoadBalancer.
SessionAffinity: ClientIP.
configmap.yaml:
Match environment variables from 
docker-compose.yml
.
Include infrastructure URLs (Postgres, RabbitMQ, Tempo, Zipkin) pointing to host.docker.internal (for local Docker Desktop K8s) or K8s DNS.
DO NOT create servicemonitor.yaml or kustomization.yaml.
Remove them if they exist. We deploy using kubectl apply -f k8s/ which applies all valid yaml files in the directory.
4. Jenkins Pipeline (
Jenkinsfile
)
Create a simplified Declarative Pipeline:

Tools: DO NOT use the 'tools' block. Rely on the agent's PATH for 'mvn' and 'java'.
OS Compatibility: You MUST use if (isUnix()) { sh '...' } else { bat '...' } for ALL shell steps to support both Windows and Linux agents.
Parameters: KUBECONFIG_PATH (string).
Stages:
IF Common Utility Dependency:
Copy Common Utility JAR (Copy from ../techdeveloper-common-utility/target/ to workspace)
Checkout
Build & Package (mvn clean package -DskipTests -B)
Build Docker Image (Local image project-name:latest)
Deploy to Kubernetes (kubectl apply -f k8s/, then rollout restart)
5. Documentation (
README.md
)
Rewrite the README to be comprehensive and "client-ready", exactly matching the depth of eureka-server:

Table of Contents
Prerequisites (Docker, K8s, Local)
Architecture Diagrams (ASCII art for Docker & K8s flows)
Detailed Configuration (Env vars table, config structure)
Deployment Steps (Step-by-step for Docker Compose & K8s)
Troubleshooting (Common errors layout)
Scaling & Monitoring
Constraint: Ensure strict consistency in file patterns while adapting memory/cpu values to the specific service.

6. Common Issues & Fixes (Critical)
*   **Networking**: Use `host.docker.internal` instead of `localhost` when connecting to services running on the host (outside K8s) from within a pod.
*   **Eureka Connection**: If Config Server overrides `EUREKA_CLIENT_SERVICEURL_DEFAULTZONE`, force it using `JAVA_TOOL_OPTIONS` in `deployment.yaml`:
    `value: "-Deureka.client.serviceUrl.defaultZone=http://eureka-server:8761/eureka/"`
*   **ConfigMap Loading**: A common error is defining `configmap.yaml` but forgetting to load it in `deployment.yaml`. Ensure you have:
    ```yaml
    envFrom:
    - configMapRef:
        name: your-service-config
    ```
*   **Database**:
    *   **Automation**: Create an `init.sh` script to check and create DB/Schema.
        ```bash
        #!/bin/bash
        set -e
        # Check/Create DB
        psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "postgres" <<-EOSQL
            SELECT 'CREATE DATABASE my_db' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'my_db')\gexec
        EOSQL
        # Check/Create Schema
        psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "my_db" <<-EOSQL
            CREATE SCHEMA IF NOT EXISTS my_schema;
        EOSQL
        ```
    *   **Local Config**: Mount it in `docker-compose.yml`:
        ```yaml
        volumes:
          - ./init.sh:/docker-entrypoint-initdb.d/init.sh
        ```
    *   **Connection**: Use `host.docker.internal` for local DBs.