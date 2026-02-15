# Spring Cloud Config Server (Centralized Configuration)

**🚨 CRITICAL: All microservices use centralized config server for configuration management! 🚨**

## 🔥 WORKFLOW - ALWAYS FOLLOW THIS ORDER!

**STEP 1: PEHLE CONFIG SERVER ME DEKHO (Check Config Server First!)**
```bash
# Config location
cd C:\Users\techd\Documents\workspace-spring-tool-suite-4-4.27.0-new\techdeveloper\backend\techdeveloper-config-server\configurations

# Check karo:
ls application.yml                              # Global configs (ALL services)
ls {project}/common/                            # Project common configs
ls {project}/services/{service-name}.yml        # Service-specific configs
```

**Redis, Kafka, Feign, Database, Email → Already hai! DUPLICATE MAT KARO!**
- Redis: `application.yml` (lines 40-51)
- Feign: `application.yml` (lines 139-145)
- RabbitMQ: `application.yml` (lines 53-62)

**STEP 2: Agar config nahi mila, decide karo:**
- **Common for ALL services?** → Add to `application.yml`
- **Common for project services?** → Add to `{project}/common/application-{name}.yml`
- **Service-specific only?** → Add to `{project}/services/{service-name}.yml`

**STEP 3: Microservice application.yml me SIRF yeh rakho:**
```yaml
spring:
  application:
    name: service-name
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
    project-name: "project-name"
```

**KUCH AUR NAHI! No Redis, No Feign, No Database, NOTHING!**

## Config Server Location
```
C:\Users\techd\Documents\workspace-spring-tool-suite-4-4.27.0-new\techdeveloper\backend\techdeveloper-config-server
```

## Configuration Directory Structure

```
configurations/
├── application.yml                        # Global config (ALL services)
├── eureka-server.yml                      # Eureka server config
├── gateway.yml                            # API Gateway routes
│
├── m2-surgricals/                         # Project: M2 Surgical
│   ├── common/                            # Common configs
│   │   ├── application-database.yml
│   │   ├── application-email.yml
│   │   ├── application-twilio.yml
│   │   ├── application-payment.yml
│   │   ├── application-cors.yml
│   │   ├── application-cache-channels.yml
│   │   ├── application-messaging.yml
│   │   └── application-secret-client.yml
│   └── services/                          # Service-specific configs
│       ├── m2-surgricals-customer-service.yml
│       ├── m2-surgricals-product-service.yml
│       └── ...
│
├── techdeveloper/                         # Project: TechDeveloper
└── lovepoet/                              # Project: LovePoet
```

## Quick Reference
- **New service config:** `configurations/{project}/services/{service-name}.yml`
- **Gateway route:** `configurations/gateway.yml`
- **Common config:** `configurations/{project}/common/application-*.yml`

## Configuration Hierarchy (Merge Order)
1. `configurations/application.yml` (Global)
2. `configurations/{project}/common/*.yml` (Project-level)
3. `configurations/{project}/services/{service-name}.yml` (Service-specific)

## Client-Side Configuration (Microservice)

**application.yml:**
```yaml
spring:
  application:
    name: m2-surgricals-customer-service  # MUST match config filename
  config:
    import: "configserver:http://localhost:8888"
  cloud:
    config:
      fail-fast: true
      retry:
        enabled: true
```

**Required Dependency:**
```xml
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-config</artifactId>
</dependency>
```

## YML vs PROPERTIES - CRITICAL RULE!

**MANDATORY: ALL projects use `.yml` files, NEVER `.properties` files!**

**❌ NEVER add in microservice's application.yml:**
- Redis config (already in global application.yml)
- Feign config (already in global application.yml)
- Database config (in common configs)
- Email config (in common configs)
- Server port (in service config on config server)
- API keys (in Secret Manager)

**Rule:** Microservice's application.yml = ONLY config server connection + secret-manager. NOTHING ELSE!

## Key Points
1. Config server at port 8888
2. YML only (never .properties)
3. Minimal microservice yml
4. `spring.application.name` MUST match config filename
5. Hierarchical: Global → Common → Service
6. Git-backed configs
7. Secrets via environment variables

## Troubleshooting

**Config server connection refused:**
1. Check config server running on 8888
2. Verify `spring.config.import` URL
3. Check config server logs

**Service not getting latest config:**
1. Verify Git repo has changes
2. Restart config server
3. Use `/actuator/refresh`

**Config file not found:**
1. Check `spring.application.name` matches filename
2. Verify file in Git repo
3. Check search-paths

**🚨 GOLDEN RULE: NEVER duplicate common configs in service files! 🚨**
