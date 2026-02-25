#!/usr/bin/env python3
"""
Coding Standards Loader
Loads all coding standards before execution
"""

# Fix encoding for Windows console (reconfigure in-place - avoids double-close exit code 1)
import sys
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


import json
import sys
from pathlib import Path
from datetime import datetime


class StandardsLoader:
    """
    Loads all coding standards from docs and policies
    Makes them available for execution phase
    """

    def __init__(self):
        self.memory_dir = Path.home() / ".claude" / "memory"
        self.docs_dir = self.memory_dir / "docs"
        self.standards = {}

    def load_all_standards(self):
        """Load all coding standards"""

        print(f"\n{'='*70}")
        print(f"[WRENCH] CODING STANDARDS LOADER")
        print(f"{'='*70}\n")

        print("[CLIPBOARD] Loading standards from documentation...\n")

        # 1. Java Project Structure
        print("  [1/12] Java Project Structure...")
        self.standards['java_structure'] = self.load_java_structure()
        print("         [CHECK] Loaded")

        # 2. Config Server Rules
        print("  [2/12] Config Server Rules...")
        self.standards['config_server'] = self.load_config_server_rules()
        print("         [CHECK] Loaded")

        # 3. Secret Management
        print("  [3/12] Secret Management...")
        self.standards['secret_management'] = self.load_secret_management()
        print("         [CHECK] Loaded")

        # 4. Response Format
        print("  [4/12] Response Format...")
        self.standards['response_format'] = self.load_response_format()
        print("         [CHECK] Loaded")

        # 5. API Design
        print("  [5/12] API Design Standards...")
        self.standards['api_design'] = self.load_api_design()
        print("         [CHECK] Loaded")

        # 6. Database Standards
        print("  [6/12] Database Standards...")
        self.standards['database'] = self.load_database_standards()
        print("         [CHECK] Loaded")

        # 7. Error Handling
        print("  [7/12] Error Handling...")
        self.standards['error_handling'] = self.load_error_handling()
        print("         [CHECK] Loaded")

        # 8. Service Layer Pattern
        print("  [8/12] Service Layer Pattern...")
        self.standards['service_pattern'] = self.load_service_pattern()
        print("         [CHECK] Loaded")

        # 9. Entity Pattern
        print("  [9/12] Entity Pattern...")
        self.standards['entity_pattern'] = self.load_entity_pattern()
        print("         [CHECK] Loaded")

        # 10. Controller Pattern
        print(" [10/12] Controller Pattern...")
        self.standards['controller_pattern'] = self.load_controller_pattern()
        print("         [CHECK] Loaded")

        # 11. Constants Organization
        print(" [11/12] Constants Organization...")
        self.standards['constants'] = self.load_constants_organization()
        print("         [CHECK] Loaded")

        # 12. Common Utilities
        print(" [12/14] Common Utilities...")
        self.standards['utilities'] = self.load_common_utilities()
        print("         [CHECK] Loaded")

        # 13. Documentation Standards
        print(" [13/14] Documentation Standards...")
        self.standards['documentation'] = self.load_documentation_standards()
        print("         [CHECK] Loaded")

        # 14. Kubernetes Network Policies
        print(" [14/15] Kubernetes Network Policies...")
        self.standards['network_policies'] = self.load_network_policies()
        print("         [CHECK] Loaded")

        # 15. K8s/Docker/Jenkins Infrastructure Rules
        print(" [15/15] K8s/Docker/Jenkins Infrastructure Rules...")
        self.standards['infra_rules'] = self.load_infra_rules()
        print("         [CHECK] Loaded")

        print(f"\n{'='*70}")
        print(f"[CHECK] ALL STANDARDS LOADED SUCCESSFULLY")
        print(f"{'='*70}\n")

        print(f"[CHART] Summary:")
        print(f"   Total Standards: {len(self.standards)}")
        print(f"   Rules Loaded: {self.count_total_rules()}")
        print(f"   Ready for Execution: YES\n")

        return self.standards

    def load_java_structure(self):
        """Load Java project structure rules"""
        return {
            'base_package': 'com.techdeveloper.{project}.{service}',
            'packages': {
                'controller': {'visibility': 'public', 'purpose': 'REST endpoints'},
                'dto': {'visibility': 'public', 'purpose': 'Response objects'},
                'form': {'visibility': 'public', 'purpose': 'Request objects'},
                'constants': {'visibility': 'public', 'purpose': 'All constants/enums'},
                'enums': {'visibility': 'public', 'purpose': 'Enums'},
                'services': {'visibility': 'public', 'purpose': 'Service interfaces'},
                'services.impl': {'visibility': 'package-private', 'purpose': 'Implementations'},
                'services.helper': {'visibility': 'package-private', 'purpose': 'Helper classes'},
                'entity': {'visibility': 'package-private', 'purpose': 'Database entities'},
                'repository': {'visibility': 'package-private', 'purpose': 'Data access'},
                'client': {'visibility': 'package-private', 'purpose': 'Feign clients'},
                'config': {'visibility': 'public', 'purpose': 'Configuration classes'},
                'exception': {'visibility': 'public', 'purpose': 'Custom exceptions'},
                'utils': {'visibility': 'public', 'purpose': 'Common utilities'}
            },
            'rules': [
                'Service implementations are package-private (no public modifier)',
                'Service implementations extend Helper class',
                'All responses use ApiResponseDto<T>',
                'Form classes extend ValidationMessageConstants',
                'NO hardcoded messages (use constants)',
                '@Transactional on all write operations (create, update, delete)'
            ]
        }

    def load_config_server_rules(self):
        """Load Config Server rules"""
        return {
            'config_location': 'backend/config-server/configurations/',
            'structure': {
                'global': 'application.yml (ALL services)',
                'project_common': '{project}/common/*.yml',
                'service_specific': '{project}/services/{service}.yml'
            },
            'microservice_yml': {
                'allowed': [
                    'spring.application.name',
                    'spring.config.import',
                    'spring.cloud.config.fail-fast',
                    'spring.cloud.config.retry.enabled',
                    'secret-manager.client.enabled',
                    'secret-manager.client.project-name',
                    'secret-manager.client.base-url'
                ],
                'forbidden': [
                    'server.port',
                    'spring.datasource.*',
                    'spring.jpa.*',
                    'spring.redis.*',
                    'feign.client.*',
                    'logging.*',
                    'Any database config',
                    'Any external service config'
                ]
            },
            'rules': [
                'ONLY application name + config import in microservice application.yml',
                'ALL other configs (DB, Redis, Feign, etc.) -> Config Server',
                'NEVER add database config in microservice',
                'NEVER add port numbers in microservice',
                'NEVER hardcode any config in microservice'
            ]
        }

    def load_secret_management(self):
        """Load Secret Management rules"""
        return {
            'services': {
                'secret_manager': {'port': 1002, 'purpose': 'Store/retrieve secrets'},
                'project_management': {'port': 8109, 'purpose': 'Manage projects'}
            },
            'microservice_config': {
                'enabled': 'true',
                'project_name': 'Required (e.g., m2-surgricals)',
                'base_url': 'http://localhost:8085/api/v1/secrets'
            },
            'secret_types': [
                'Database passwords',
                'API keys (third-party)',
                'JWT secrets',
                'Email passwords',
                'OAuth client secrets',
                'Encryption keys'
            ],
            'config_server_usage': {
                'syntax': '${SECRET:key-name}',
                'example': 'spring.datasource.password: ${SECRET:db-password}'
            },
            'rules': [
                'ALL secrets in Secret Manager (NEVER hardcode)',
                'Config server uses ${SECRET:key-name} syntax',
                'NEVER commit .env files',
                'NEVER store secrets in application.yml',
                'NEVER log secrets',
                'NEVER expose secrets in API responses'
            ]
        }

    def load_response_format(self):
        """Load response format standards"""
        return {
            'wrapper_class': 'ApiResponseDto<T>',
            'fields': {
                'status': {
                    'type': 'String',
                    'values': ['SUCCESS', 'ERROR'],
                    'required': True
                },
                'message': {
                    'type': 'String',
                    'source': 'MessageConstants (NEVER hardcoded)',
                    'required': True
                },
                'data': {
                    'type': 'T (generic)',
                    'nullable': True,
                    'purpose': 'Actual response data'
                },
                'timestamp': {
                    'type': 'String',
                    'format': 'ISO 8601 (yyyy-MM-ddTHH:mm:ssZ)',
                    'required': True
                }
            },
            'factory_methods': {
                'success': 'ApiResponseDto.success(message, data)',
                'error': 'ApiResponseDto.error(message)'
            },
            'example': {
                'status': 'SUCCESS',
                'message': 'Product retrieved successfully',
                'data': {'id': 123, 'name': 'Product Name'},
                'timestamp': '2026-02-16T14:30:00Z'
            },
            'rules': [
                'ALL API responses use ApiResponseDto<T>',
                'Message from MessageConstants (NEVER hardcoded)',
                'Use .success() or .error() factory methods',
                'NEVER return raw DTOs directly',
                'NEVER use ResponseEntity<ProductDto> (always wrap)',
                'NEVER hardcode messages in controllers'
            ]
        }

    def load_api_design(self):
        """Load API design standards"""
        return {
            'base_path': '/api/v1/{resource}',
            'http_methods': {
                'GET': 'Retrieve resource(s)',
                'POST': 'Create new resource',
                'PUT': 'Update existing resource',
                'DELETE': 'Delete resource'
            },
            'endpoint_patterns': {
                'get_all': 'GET /api/v1/products',
                'get_by_id': 'GET /api/v1/products/{id}',
                'create': 'POST /api/v1/products',
                'update': 'PUT /api/v1/products/{id}',
                'delete': 'DELETE /api/v1/products/{id}',
                'search': 'GET /api/v1/products/search?keyword=...'
            },
            'status_codes': {
                '200': 'OK (successful GET, PUT, DELETE)',
                '201': 'Created (successful POST)',
                '400': 'Bad Request (validation error)',
                '401': 'Unauthorized (authentication required)',
                '403': 'Forbidden (insufficient permissions)',
                '404': 'Not Found (resource not found)',
                '409': 'Conflict (duplicate resource)',
                '500': 'Internal Server Error (server error)'
            },
            'rules': [
                'Use standard REST patterns',
                'Consistent naming (/products, not /product)',
                '@Valid on request body',
                'Path variables for IDs',
                'Query params for filters/search',
                'Return appropriate status codes'
            ]
        }

    def load_database_standards(self):
        """Load database standards"""
        return {
            'naming_convention': {
                'table': 'snake_case (e.g., products, user_profiles)',
                'column': 'snake_case (e.g., created_at, first_name)',
                'index': 'idx_{table}_{column} (e.g., idx_products_name)'
            },
            'audit_fields': {
                'required': True,
                'fields': [
                    'created_at (TIMESTAMP)',
                    'updated_at (TIMESTAMP)',
                    'created_by (BIGINT)',
                    'updated_by (BIGINT)'
                ]
            },
            'jpa_annotations': {
                'entity': '@Entity @Table(name = "products")',
                'id': '@Id @GeneratedValue(strategy = IDENTITY)',
                'column': '@Column(name = "...", nullable = false)',
                'enum': '@Enumerated(EnumType.STRING)'
            },
            'rules': [
                'Entity is package-private',
                'Table name explicitly specified',
                'Column names explicit (snake_case)',
                'Audit fields mandatory',
                '@PrePersist and @PreUpdate for timestamps',
                'NEVER use camelCase in DB column names'
            ]
        }

    def load_error_handling(self):
        """Load error handling standards"""
        return {
            'exception_pattern': {
                'custom': 'extends RuntimeException',
                'message': 'Descriptive error message',
                'handler': '@RestControllerAdvice'
            },
            'common_exceptions': [
                '{Entity}NotFoundException',
                '{Entity}AlreadyExistsException',
                'ValidationException',
                'UnauthorizedException'
            ],
            'global_handler': {
                'annotation': '@RestControllerAdvice',
                'methods': [
                    '@ExceptionHandler(NotFoundException.class)',
                    '@ExceptionHandler(AlreadyExistsException.class)',
                    '@ExceptionHandler(MethodArgumentNotValidException.class)'
                ]
            },
            'rules': [
                'Custom exceptions for domain errors',
                'Global exception handler with @RestControllerAdvice',
                'Return ApiResponseDto for all errors',
                'Appropriate HTTP status codes',
                'NEVER swallow exceptions',
                'NEVER expose stack traces to client'
            ]
        }

    def load_service_pattern(self):
        """Load service layer pattern"""
        return {
            'interface': {
                'visibility': 'public',
                'name': '{Entity}Service',
                'methods': ['findById', 'create', 'update', 'delete']
            },
            'implementation': {
                'visibility': 'package-private (NO public keyword)',
                'name': '{Entity}ServiceImpl',
                'extends': '{Entity}ServiceHelper',
                'implements': '{Entity}Service',
                'annotation': '@Service'
            },
            'helper': {
                'visibility': 'package-private abstract class',
                'name': '{Entity}ServiceHelper',
                'purpose': 'Reusable logic, validation, mapping'
            },
            'rules': [
                'Service interface is public',
                'Service implementation is package-private',
                'Implementation extends Helper',
                'Helper contains reusable logic',
                '@Transactional on write operations',
                'NEVER put business logic in controller'
            ]
        }

    def load_entity_pattern(self):
        """Load entity pattern"""
        return {
            'visibility': 'package-private',
            'annotations': ['@Entity', '@Table(name = "...")'],
            'audit_fields_mandatory': True,
            'lifecycle_callbacks': ['@PrePersist', '@PreUpdate'],
            'rules': [
                'Entity is package-private',
                'Explicit table name',
                'Explicit column names (snake_case)',
                'Audit fields mandatory',
                'Lifecycle callbacks for timestamps'
            ]
        }

    def load_controller_pattern(self):
        """Load controller pattern"""
        return {
            'visibility': 'public',
            'annotations': ['@RestController', '@RequestMapping("/api/v1/...")'],
            'dependency_injection': 'Constructor injection',
            'validation': '@Valid on request body',
            'response': 'ResponseEntity<ApiResponseDto<T>>',
            'rules': [
                'Controller is public',
                'Base path /api/v1/{resource}',
                'Constructor injection for dependencies',
                '@Valid on request body',
                'Return ApiResponseDto wrapper',
                'NEVER put business logic in controller'
            ]
        }

    def load_constants_organization(self):
        """Load constants organization"""
        return {
            'classes': {
                'ApiConstants': 'API paths, versions',
                'MessageConstants': 'Response messages',
                'ValidationMessageConstants': 'Validation messages',
                'DatabaseConstants': 'DB-related constants',
                'SecurityConstants': 'Security-related constants'
            },
            'rules': [
                'ALL constants in appropriate constant classes',
                'NO magic numbers/strings in code',
                'Use constants everywhere',
                'NEVER hardcode strings/numbers',
                'NEVER duplicate constants'
            ]
        }

    def load_common_utilities(self):
        """Load common utilities"""
        return {
            'classes': {
                'DateTimeUtils': 'Date/time operations',
                'StringUtils': 'String operations',
                'ValidationUtils': 'Custom validations',
                'MapperUtils': 'DTO mapping'
            },
            'pattern': 'Static utility methods',
            'rules': [
                'Utility classes for common operations',
                'Reuse utilities across services',
                'Static methods only',
                'NEVER duplicate utility logic'
            ]
        }

    def load_documentation_standards(self):
        """Load documentation standards"""
        return {
            'structure': {
                'levels': 2,
                'level_1': {
                    'location': 'projectname/',
                    'purpose': 'Project overview (all backend + frontend repos)',
                    'files': ['README.md', 'CLAUDE.md']
                },
                'level_2': {
                    'location': 'projectname/backend/service-name/ OR projectname/frontend/app-name/',
                    'requirement': 'MUST have .git directory',
                    'purpose': 'Repository-specific documentation',
                    'files': ['README.md', 'CLAUDE.md']
                }
            },
            'forbidden_locations': [
                'projectname/backend/ (NO .git - not a repo)',
                'projectname/frontend/ (NO .git - not a repo)'
            ],
            'readme_structure': {
                'level_1_sections': [
                    'Table of Contents',
                    'Overview',
                    'Project Structure',
                    'Backend Services',
                    'Frontend Applications',
                    'Architecture',
                    'Configuration',
                    'Deployment',
                    'Development Guidelines'
                ],
                'level_2_sections': [
                    'Table of Contents',
                    'Overview',
                    'API Documentation',
                    'Setup Guide',
                    'Configuration',
                    'Database Schema',
                    'Testing',
                    'Deployment'
                ],
                'requirements': [
                    'Comprehensive content with indexing',
                    'Clickable anchor links',
                    'Horizontal separators between sections',
                    'Proper header hierarchy',
                    'All documentation consolidated'
                ]
            },
            'claude_md_structure': {
                'level_1_purpose': 'Project-level instructions',
                'level_2_purpose': 'Repository-specific instructions',
                'restrictions': [
                    'NEVER override global policies',
                    'NEVER duplicate README.md content',
                    'NEVER contain general documentation'
                ]
            },
            'consolidation': {
                'before_new_file': [
                    'Check if content belongs in README.md',
                    'Verify location has .git (for repo-level)',
                    'Only create at project root OR in git repos'
                ],
                'process': [
                    'Create comprehensive README.md with ToC',
                    'Move all content from other .md files into README.md',
                    'Delete all other .md files (except CLAUDE.md)',
                    'Update README.md ToC with all sections',
                    'Test all anchor links'
                ]
            },
            'rules': [
                '2 .md files at 2 LEVELS:',
                'Level 1 (Project Root): README.md + CLAUDE.md (project overview)',
                'Level 2 (Each Git Repo): README.md + CLAUDE.md (repo-specific)',
                'NO .md files in non-git folders (backend/, frontend/)',
                'NO separate .md files (API.md, Setup.md, Architecture.md, etc.)',
                'NO status/report files as separate .md files',
                'NO migration guides as separate files',
                'ALL content consolidated into README.md at appropriate level',
                'Table of Contents MANDATORY in README.md',
                'Anchor links MUST work for all sections'
            ]
        }

    def load_network_policies(self):
        """Load Kubernetes Network Policies standards"""
        return {
            'architecture': {
                'layers': 3,
                'layer_1': 'Service-level policies (each microservice)',
                'layer_2': 'Common namespace policies (shared infrastructure)',
                'layer_3': 'Central hub policy (Config Server, Eureka, Gateway, Secret Manager)'
            },
            'mandatory_for': [
                'ALL Kubernetes services',
                'ALL microservices (TechDeveloper, Surgricalswale, Lovepoet)',
                'ALL common namespace services (PostgreSQL, MongoDB, Redis, Elasticsearch, RabbitMQ, Prometheus)'
            ],
            'service_policy_template': {
                'location': 'k8s/network-policy.yaml (in each service)',
                'ingress_allows': [
                    'Gateway traffic (from PROJECT-gateway)',
                    'Internal namespace traffic (same namespace)',
                    'Prometheus monitoring (from common namespace)'
                ],
                'egress_allows': [
                    'DNS resolution (kube-system, MANDATORY)',
                    'Config Server (port 8888, MANDATORY)',
                    'Eureka Server (port 8761, MANDATORY)',
                    'Secret Manager (port 1002, MANDATORY)',
                    'Database (PostgreSQL 5432 OR MongoDB 27017)',
                    'Redis (port 6379, MANDATORY)',
                    'External HTTPS (ports 443, 80)',
                    'Internal namespace communication'
                ]
            },
            'common_namespace_policy_template': {
                'location': 'common-namespace-network-policies/{service}-network-policy.yaml',
                'ingress_allows': [
                    'TechDeveloper namespace',
                    'Surgricalswale namespace',
                    'Lovepoet namespace',
                    'Common namespace (internal)'
                ],
                'egress_allows': [
                    'DNS resolution (MANDATORY)',
                    'Internal common namespace communication'
                ]
            },
            'database_selection': {
                'postgresql': ['TechDeveloper (all services)', 'Surgricalswale (all services)'],
                'mongodb': ['Lovepoet (all services)']
            },
            'existing_common_policies': {
                'postgresql': 5432,
                'mongodb': 27017,
                'redis': 6379,
                'elasticsearch': '9200, 9300',
                'rabbitmq': '5672, 15672',
                'prometheus': 9090
            },
            'automatic_creation': {
                'trigger_1': 'Creating new microservice',
                'action_1': 'IMMEDIATELY create k8s/network-policy.yaml',
                'trigger_2': 'Adding new common namespace service',
                'action_2': 'IMMEDIATELY create {service}-network-policy.yaml in common-namespace-network-policies/',
                'trigger_3': 'Deploying existing service to K8s',
                'action_3': 'Check if network-policy.yaml exists, CREATE if not'
            },
            'templates': {
                'microservice': '~/.claude/memory/templates/network-policy-microservice.yaml',
                'common_namespace': '~/.claude/memory/templates/network-policy-common-namespace.yaml'
            },
            'documentation': '~/.claude/memory/docs/kubernetes-network-policies.md',
            'rules': [
                'MANDATORY: ALL K8s services MUST have network policies',
                'Create network policy AUTOMATICALLY when creating service (NEVER wait for user to ask)',
                'Use microservice template for project namespaces (techdeveloper/surgricalswale/lovepoet)',
                'Use common namespace template for shared infrastructure',
                'Database selection: PostgreSQL (TechDev/Surgrical), MongoDB (Lovepoet)',
                'ALWAYS include DNS egress (MANDATORY for K8s service discovery)',
                'Common namespace policies MUST allow ALL project namespaces',
                'Commit network policy WITH service creation (same commit)',
                'Apply to K8s cluster immediately after creation',
                'NEVER create K8s service without network policy',
                'NEVER skip network policy creation',
                'Update common namespace policies when new service added there'
            ]
        }

    def load_infra_rules(self):
        """Load K8s/Docker/Jenkins infrastructure standards (Standard 15)
        Based on comprehensive study of all projects: techdeveloper, surgricalswale, lovepoet, infrastructure
        These are actual working templates - follow EXACTLY when creating new services.
        """
        return {
            'name': 'K8s/Docker/Jenkins Infrastructure Standards',
            'version': '2.0.0',
            'updated': '2026-02-19',
            'source': 'Study of surgricalswale, lovepoet, techdeveloper, infrastructure projects',

            # --- REGISTRY AND NAMESPACES ---
            'docker_registry': '148.113.197.135:5000',
            'namespaces': {
                'common': 'Infrastructure: postgres, redis, mongodb, elasticsearch, rabbitmq, pgadmin',
                'techdeveloper': 'TechDeveloper microservices + frontend',
                'surgricalswale': 'Surgricalswale microservices + frontend',
                'lovepoet': 'Lovepoet microservices + frontend',
            },

            # --- K8S ARCHETYPE 1: SPRING BOOT MICROSERVICE ---
            'k8s_spring_boot': {
                'examples': ['surgricalswale-cart-service', 'lovepoet-user-service', 'techdeveloper-client-management-system'],
                'namespace': '{project} namespace (not common)',
                'image': '148.113.197.135:5000/{service-name}:latest',
                'imagePullPolicy': 'Always',
                'pod_securityContext': {
                    'runAsNonRoot': True,
                    'runAsUser': 1000,
                    'runAsGroup': 1000,
                    'fsGroup': 1000,
                },
                'container_securityContext': 'NONE - no container-level securityContext for Spring Boot',
                'dnsPolicy': 'ClusterFirst',
                'dnsConfig': 'options: ndots=1, timeout=2, attempts=2',
                'env_vars': [
                    'SPRING_PROFILES_ACTIVE: "{project},k8s"',
                    'SPRING_CONFIG_IMPORT: "configserver:http://techdeveloper-config-server.techdeveloper.svc.cluster.local:8888"',
                ],
                'resources': {
                    'requests': {'memory': '512Mi', 'cpu': '500m'},
                    'limits': {'memory': '1Gi', 'cpu': '1000m'},
                },
                'probes': {
                    'liveness': '/actuator/health/liveness delay=30 period=10 timeout=5 failure=3',
                    'readiness': '/actuator/health/readiness delay=20 period=5 timeout=3 failure=3 success=1',
                },
                'annotations': 'prometheus.io/scrape=true port={port} path=/actuator/prometheus',
                'initContainers': 'NONE (no hostPath volumes)',
                'template_yaml': (
                    'apiVersion: apps/v1\n'
                    'kind: Deployment\n'
                    'metadata:\n'
                    '  name: {service-name}\n'
                    '  namespace: {project}\n'
                    'spec:\n'
                    '  replicas: 1\n'
                    '  selector:\n'
                    '    matchLabels:\n'
                    '      app: {service-name}\n'
                    '  template:\n'
                    '    metadata:\n'
                    '      labels:\n'
                    '        app: {service-name}\n'
                    '      annotations:\n'
                    '        prometheus.io/scrape: "true"\n'
                    '        prometheus.io/port: "{port}"\n'
                    '        prometheus.io/path: "/actuator/prometheus"\n'
                    '    spec:\n'
                    '      dnsPolicy: ClusterFirst\n'
                    '      dnsConfig:\n'
                    '        options:\n'
                    '          - {name: ndots, value: "1"}\n'
                    '          - {name: timeout, value: "2"}\n'
                    '          - {name: attempts, value: "2"}\n'
                    '      securityContext:\n'
                    '        runAsNonRoot: true\n'
                    '        runAsUser: 1000\n'
                    '        runAsGroup: 1000\n'
                    '        fsGroup: 1000\n'
                    '      containers:\n'
                    '        - name: {service-name}\n'
                    '          image: 148.113.197.135:5000/{service-name}:latest\n'
                    '          imagePullPolicy: Always\n'
                    '          ports:\n'
                    '            - containerPort: {port}\n'
                    '          env:\n'
                    '            - name: SPRING_PROFILES_ACTIVE\n'
                    '              value: "{project},k8s"\n'
                    '            - name: SPRING_CONFIG_IMPORT\n'
                    '              value: "configserver:http://techdeveloper-config-server.techdeveloper.svc.cluster.local:8888"\n'
                    '          resources:\n'
                    '            requests:\n'
                    '              memory: "512Mi"\n'
                    '              cpu: "500m"\n'
                    '            limits:\n'
                    '              memory: "1Gi"\n'
                    '              cpu: "1000m"\n'
                    '          livenessProbe:\n'
                    '            httpGet:\n'
                    '              path: /actuator/health/liveness\n'
                    '              port: {port}\n'
                    '            initialDelaySeconds: 30\n'
                    '            periodSeconds: 10\n'
                    '            timeoutSeconds: 5\n'
                    '            failureThreshold: 3\n'
                    '          readinessProbe:\n'
                    '            httpGet:\n'
                    '              path: /actuator/health/readiness\n'
                    '              port: {port}\n'
                    '            initialDelaySeconds: 20\n'
                    '            periodSeconds: 5\n'
                    '            timeoutSeconds: 3\n'
                    '            failureThreshold: 3\n'
                    '            successThreshold: 1\n'
                ),
            },

            # --- K8S ARCHETYPE 2: INFRASTRUCTURE SERVICE ---
            'k8s_infra_service': {
                'examples': ['postgres', 'redis', 'mongodb', 'elasticsearch', 'rabbitmq'],
                'namespace': 'common',
                'labels_required': 'tier: infrastructure, managed-by: jenkins',
                'imagePullPolicy': 'IfNotPresent (use cached public images)',
                'strategy': 'RollingUpdate maxUnavailable=0 maxSurge=1 revisionHistoryLimit=3',
                'pod_securityContext': {
                    'runAsNonRoot': False,
                    'fsGroup': '{uid}',
                    'fsGroupChangePolicy': 'OnRootMismatch',
                },
                'initContainer_required': True,
                'initContainer_pattern': {
                    'name': 'fix-permissions',
                    'image': 'busybox',
                    'runAsUser': 0,
                    'command': 'chown -R {uid}:{gid} {mountPath}',
                    'examples': {
                        'postgres': 'chown -R 999:999 /var/lib/postgresql/data',
                        'redis': 'chown -R 999:999 /data',
                        'pgadmin': 'chown -R 5050:5050 /var/lib/pgadmin',
                    },
                },
                'container_securityContext': {
                    'allowPrivilegeEscalation': False,
                    'readOnlyRootFilesystem': False,
                    'runAsUser': '{uid}',
                    'runAsGroup': '{gid}',
                    'capabilities': 'drop: ALL, add: CHOWN SETUID SETGID',
                },
                'probes': 'Use exec probe (pg_isready, redis-cli ping, curl) not httpGet for infra services',
                'pdb': 'Include PodDisruptionBudget with minAvailable: 0',
                'terminationGracePeriodSeconds': 30,
                'sudo_images': {
                    'dpage/pgadmin4': 'Uses sudo in entrypoint to drop to uid 5050. NEVER add container securityContext. Use ONLY pod-level fsGroup: 5050',
                },
            },

            # --- K8S ARCHETYPE 3: ANGULAR FRONTEND ---
            'k8s_angular_frontend': {
                'examples': ['techdeveloper-ui', 'surgricalswale-ui'],
                'namespace': '{project} (same as backend)',
                'image': '148.113.197.135:5000/{app-name}:latest',
                'imagePullPolicy': 'Always',
                'pod_securityContext': {
                    'runAsNonRoot': True,
                    'runAsUser': 101,
                    'runAsGroup': 101,
                    'fsGroup': 101,
                    'note': 'nginx-unprivileged image uses uid 101',
                },
                'container_securityContext': {
                    'capabilities': 'drop: ALL',
                    'note': 'Only drop capabilities, no other fields needed',
                },
                'resources': {
                    'requests': {'memory': '128Mi', 'cpu': '100m'},
                    'limits': {'memory': '512Mi', 'cpu': '500m'},
                },
                'probes': {
                    'liveness': '/health delay=30 period=10 timeout=5 failure=3',
                    'readiness': '/health delay=10 period=5 timeout=3 failure=3 success=1',
                    'startup': '/health delay=0 period=5 timeout=3 failure=12 (= 60s max startup)',
                },
                'strategy': 'RollingUpdate maxSurge=1 maxUnavailable=0',
                'port': 8080,
                'annotations': 'prometheus.io/scrape=true port=8080 path=/health',
                'terminationGracePeriodSeconds': 30,
            },

            # --- DOCKERFILE ARCHETYPE 1: SPRING BOOT ---
            'dockerfile_spring_boot': {
                'base_image': '148.113.197.135:5000/eclipse-temurin:21-jre-alpine',
                'user': 'spring (uid 1000, gid 1000)',
                'type': 'Single-stage - JAR pre-built by Jenkins Maven (no multi-stage needed)',
                'template': (
                    'FROM 148.113.197.135:5000/eclipse-temurin:21-jre-alpine\n'
                    'WORKDIR /app\n'
                    'RUN addgroup -g 1000 spring && adduser -u 1000 -G spring -s /bin/sh -D spring\n'
                    'USER 1000:1000\n'
                    'COPY target/*.jar app.jar\n'
                    'EXPOSE {port}\n'
                    'ENTRYPOINT ["java",\n'
                    '    "-XX:+UseContainerSupport",\n'
                    '    "-XX:MaxRAMPercentage=75.0",\n'
                    '    "-XX:InitialRAMPercentage=25.0",\n'
                    '    "-XX:MinRAMPercentage=25.0",\n'
                    '    "-XX:+UseG1GC",\n'
                    '    "-XX:MaxGCPauseMillis=200",\n'
                    '    "-XX:+ParallelRefProcEnabled",\n'
                    '    "-XX:+DisableExplicitGC",\n'
                    '    "-XX:+UseStringDeduplication",\n'
                    '    "-Djava.security.egd=file:/dev/./urandom",\n'
                    '    "-jar", "app.jar"]\n'
                ),
                'jvm_flags': [
                    '-XX:+UseContainerSupport (respect container memory limits)',
                    '-XX:MaxRAMPercentage=75.0 (use 75% of container RAM)',
                    '-XX:InitialRAMPercentage=25.0',
                    '-XX:MinRAMPercentage=25.0',
                    '-XX:+UseG1GC (G1 garbage collector)',
                    '-XX:MaxGCPauseMillis=200 (max 200ms GC pause)',
                    '-XX:+ParallelRefProcEnabled',
                    '-XX:+DisableExplicitGC',
                    '-XX:+UseStringDeduplication',
                    '-Djava.security.egd=file:/dev/./urandom (faster SecureRandom)',
                ],
            },

            # --- DOCKERFILE ARCHETYPE 2: ANGULAR FRONTEND ---
            'dockerfile_angular': {
                'stage1_image': '148.113.197.135:5000/node:20-alpine',
                'stage2_image': '148.113.197.135:5000/nginx-unprivileged:1.27-alpine',
                'type': 'Multi-stage: node builds, nginx serves',
                'stage1_steps': [
                    'FROM 148.113.197.135:5000/node:20-alpine AS builder',
                    'WORKDIR /app',
                    'RUN apk add --no-cache python3 make g++ (native modules)',
                    'COPY package.json package-lock.json ./ (caching layer)',
                    'RUN npm ci --frozen-lockfile --prefer-offline --no-audit',
                    'COPY . .',
                    'RUN npm run build -- --configuration production --output-hashing all',
                    'RUN ls -la /app/dist/{app-name}/browser (fail-fast verification)',
                ],
                'stage2_steps': [
                    'FROM 148.113.197.135:5000/nginx-unprivileged:1.27-alpine',
                    'USER root (temporarily for setup)',
                    'RUN apk upgrade --no-cache && apk add --no-cache curl && rm -rf /var/cache/apk/*',
                    'RUN mkdir -p nginx cache dirs + chown -R 101:101 /var/cache/nginx',
                    'RUN rm -rf /usr/share/nginx/html/*',
                    'USER 101 (switch to nginx-unprivileged uid)',
                    'COPY --from=builder --chown=101:101 /app/dist/{app-name}/browser /usr/share/nginx/html',
                    'COPY --chown=101:101 nginx.conf /etc/nginx/conf.d/default.conf',
                    'EXPOSE 8080',
                    'HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 CMD curl -f http://localhost:8080/health || exit 1',
                    'ENV NGINX_ENTRYPOINT_QUIET_LOGS=1',
                    'CMD ["nginx", "-g", "daemon off;"]',
                ],
            },

            # --- JENKINS ARCHETYPE 1: SPRING BOOT MICROSERVICE ---
            'jenkins_spring_boot': {
                'description': 'Unix-only K8s agent pipeline - no isUnix() checks needed',
                'agent': 'kubernetes inheritFrom k8s-agent defaultContainer maven',
                'env': {
                    'LOCAL_REGISTRY': '148.113.197.135:5000',
                    'MAVEN_CACHE': '${WORKSPACE}/../.m2 (shared Maven cache across builds)',
                    'SERVICE_NAME': '{service-name}',
                    'K8S_NAMESPACE': '{project}',
                    'KUBECONFIG': '/var/jenkins_home/.kube/config',
                },
                'auto_rollback': False,
                'rollout_timeout': '1m',
                'docker_flags': '--network host --no-cache',
                'maven_flags': '-DskipTests -B -nsu -ntp -Dmaven.repo.local=${MAVEN_CACHE}',
                'stages': [
                    '1. Checkout: checkout scm',
                    '2. Build Dependencies: for each dependency - git clone + mvn clean install + docker build --network host + docker push',
                    '   Dependency order: techdeveloper-common-utility -> techdeveloper-secret-manager-client -> {project}-common-utility -> main service',
                    '3. Build & Package: mvn clean package -DskipTests -B -nsu -ntp -Dmaven.repo.local=${MAVEN_CACHE}',
                    '4. Build Docker Image: container(docker) docker build --network host --no-cache -t ${LOCAL_REGISTRY}/${SERVICE_NAME}:latest ${WORKSPACE}',
                    '5. Docker Push: docker push ${LOCAL_REGISTRY}/${SERVICE_NAME}:latest',
                    '6. Deploy: kubectl create namespace --dry-run=client | apply, kubectl apply -f k8s/, kubectl set image, kubectl rollout restart, kubectl rollout status --timeout=1m',
                ],
                'post': {
                    'success': 'echo success message',
                    'failure': 'echo failure (NO auto rollback for microservices)',
                    'always': 'container(docker) docker image prune -f, cleanWs()',
                },
            },

            # --- JENKINS ARCHETYPE 2: INFRASTRUCTURE SERVICE ---
            'jenkins_infra': {
                'description': 'Dual-OS pipeline with auto rollback - NO Docker build (uses public images)',
                'agent': 'kubernetes inheritFrom k8s-agent defaultContainer maven',
                'env': {
                    'SERVICE_NAME': '{service-name}',
                    'NAMESPACE': 'common',
                    'KUBECONFIG_UNIX': '/var/jenkins_home/.kube/config',
                    'KUBECONFIG_WIN': 'C:/Users/techd/.kube/config',
                    'DEPLOYMENT_TIMEOUT': '300s (5 min - infra needs more time)',
                },
                'parameters': 'SKIP_DEPLOY (booleanParam), DEPLOYMENT_MODE choice [rolling, recreate]',
                'auto_rollback': True,
                'rollout_timeout': '300s',
                'dual_os': True,
                'stages': [
                    '1. Pre-Deployment Validation: kubectl cluster-info, kubectl apply -f k8s/ --dry-run=client',
                    '2. Deploy to K8s (if !SKIP_DEPLOY): kubectl apply -f k8s/',
                    '3. Verify Rollout Status: kubectl rollout status deployment/${SERVICE_NAME} -n ${NAMESPACE} --timeout=${DEPLOYMENT_TIMEOUT}',
                    '4. Health Check: verify READY_PODS == TOTAL_PODS, kubectl get svc',
                    '5. Deployment Summary: kubectl describe deployment, kubectl get pods, kubectl get svc',
                ],
                'post': {
                    'success': 'echo success',
                    'failure': 'AUTO ROLLBACK: kubectl rollout undo deployment/${SERVICE_NAME} -n ${NAMESPACE}',
                    'unstable': 'echo UNSTABLE - review health checks',
                    'always': 'cleanWs()',
                },
            },

            # --- JENKINS ARCHETYPE 3: ANGULAR FRONTEND ---
            'jenkins_angular': {
                'description': 'Frontend pipeline with dual-OS, npm build + docker + deploy',
                'agent': 'kubernetes inheritFrom k8s-agent defaultContainer maven',
                'options': 'timestamps(), timeout(30, MINUTES), buildDiscarder(numToKeepStr=10)',
                'BUILD_TAG': '${env.BUILD_NUMBER}-${GIT_COMMIT[:7]}',
                'auto_rollback': False,
                'rollout_timeout': '1m',
                'dual_os': True,
                'stages': [
                    '1. Checkout: checkout scm + git rev-parse HEAD for BUILD_TAG',
                    '2. Install Dependencies: npm ci --frozen-lockfile --prefer-offline --no-audit',
                    '3. Lint: npm run lint || true (non-blocking)',
                    '4. Build Application: npm run build -- --configuration production --output-hashing all',
                    '5. Build Docker Image: docker build -t ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${BUILD_TAG} .',
                    '6. Tag: docker tag image:BUILD_TAG image:latest',
                    '7. Push: docker push both BUILD_TAG and latest tags',
                    '8. Deploy: kubectl create namespace --dry-run, kubectl apply -f k8s/, kubectl set image, kubectl rollout status --timeout=1m',
                ],
                'post': {
                    'success': 'echo success with image tag info',
                    'failure': 'echo failure',
                    'always': 'cleanWs()',
                },
            },

            # --- RULES (all rules for count) ---
            'rules': [
                # Namespace
                'NS1: Spring Boot microservices namespace = project name (techdeveloper/surgricalswale/lovepoet), NOT common',
                'NS2: Infrastructure services (postgres/redis/mongodb/elasticsearch/rabbitmq/pgadmin) go in common namespace',
                'NS3: Frontend services go in same project namespace as backend',
                # K8s Spring Boot
                'D1: Spring Boot deployment MUST have dnsPolicy ClusterFirst + dnsConfig ndots=1 timeout=2 attempts=2',
                'D2: Spring Boot pod securityContext: runAsNonRoot=true runAsUser=1000 runAsGroup=1000 fsGroup=1000',
                'D3: Spring Boot containers have NO container-level securityContext (pod-level only)',
                'D4: Spring Boot probes use /actuator/health/liveness and /actuator/health/readiness paths',
                'D5: Spring Boot probe settings: liveness delay=30 period=10 timeout=5 failure=3; readiness delay=20 period=5 timeout=3 failure=3 success=1',
                'D6: Spring Boot resources: requests mem=512Mi cpu=500m, limits mem=1Gi cpu=1000m',
                'D7: Spring Boot env MUST include SPRING_PROFILES_ACTIVE={project},k8s and SPRING_CONFIG_IMPORT configserver URL',
                'D8: Spring Boot image from 148.113.197.135:5000 with imagePullPolicy=Always',
                'D9: Spring Boot config server URL: http://techdeveloper-config-server.techdeveloper.svc.cluster.local:8888',
                'D10: Spring Boot has Prometheus annotations: scrape=true port={port} path=/actuator/prometheus',
                # K8s Infra
                'D11: Infra service MUST have initContainer fix-permissions when using PVC/hostPath volumes',
                'D12: initContainer: busybox image runAsUser=0 command=chown -R uid:gid mountPath',
                'D13: Infra pod securityContext: runAsNonRoot=false fsGroup={uid} fsGroupChangePolicy=OnRootMismatch',
                'D14: Infra container securityContext: allowPrivilegeEscalation=false readOnlyRootFilesystem=false runAsUser={uid} capabilities drop ALL add CHOWN+SETUID+SETGID',
                'D15: Infra strategy: RollingUpdate maxUnavailable=0 maxSurge=1 revisionHistoryLimit=3',
                'D16: Infra imagePullPolicy=IfNotPresent (use cached public images, not Always)',
                'D17: Infra labels: tier=infrastructure managed-by=jenkins',
                'D18: Infra services use exec probes (pg_isready, redis-cli) not httpGet probes',
                'D19: Infra deployments include PodDisruptionBudget with minAvailable=0',
                # K8s Angular
                'D20: Angular frontend pod securityContext: runAsNonRoot=true runAsUser=101 runAsGroup=101 fsGroup=101 (nginx-unprivileged uid)',
                'D21: Angular frontend container securityContext: capabilities drop ALL (nothing else)',
                'D22: Angular frontend resources: requests mem=128Mi cpu=100m, limits mem=512Mi cpu=500m',
                'D23: Angular frontend uses /health path for all probes (not /actuator)',
                'D24: Angular frontend MUST have startupProbe with failureThreshold=12 period=5 (allows 60s startup)',
                'D25: Angular frontend strategy: RollingUpdate maxSurge=1 maxUnavailable=0',
                # Dockerfile Spring Boot
                'DF1: Spring Boot Dockerfile base: 148.113.197.135:5000/eclipse-temurin:21-jre-alpine',
                'DF2: Spring Boot Dockerfile: addgroup -g 1000 spring && adduser -u 1000 -G spring -s /bin/sh -D spring, USER 1000:1000',
                'DF3: Spring Boot Dockerfile is SINGLE-STAGE: COPY target/*.jar app.jar (Jenkins Maven builds the JAR)',
                'DF4: Spring Boot JVM flags: UseContainerSupport MaxRAMPercentage=75 UseG1GC MaxGCPauseMillis=200 java.security.egd',
                # Dockerfile Angular
                'DF5: Angular Dockerfile Stage 1: 148.113.197.135:5000/node:20-alpine AS builder',
                'DF6: Angular Dockerfile Stage 1: npm ci --frozen-lockfile --prefer-offline --no-audit',
                'DF7: Angular Dockerfile Stage 1: npm run build -- --configuration production --output-hashing all',
                'DF8: Angular Dockerfile Stage 2: 148.113.197.135:5000/nginx-unprivileged:1.27-alpine',
                'DF9: Angular Dockerfile Stage 2: USER root temporarily to setup, then USER 101 (nginx-unprivileged uid)',
                'DF10: Angular Dockerfile Stage 2: mkdir nginx cache dirs + chown 101:101 before switching USER 101',
                'DF11: Angular Dockerfile Stage 2: HEALTHCHECK curl http://localhost:8080/health',
                # Jenkins Spring Boot
                'J1: Spring Boot Jenkins: k8s-agent defaultContainer=maven KUBECONFIG=/var/jenkins_home/.kube/config',
                'J2: Spring Boot Jenkins: MAVEN_CACHE=${WORKSPACE}/../.m2 shared across all builds',
                'J3: Spring Boot Jenkins: NO isUnix() checks (k8s agent is always Linux)',
                'J4: Spring Boot Jenkins: docker build --network host --no-cache',
                'J5: Spring Boot Jenkins: rollout timeout=1m, NO auto rollback on failure',
                'J6: Spring Boot Jenkins dependency build order: techdeveloper-common-utility -> secret-manager-client -> {project}-common-utility -> service',
                'J7: Spring Boot Jenkins post.always: docker image prune -f + cleanWs()',
                # Jenkins Infra
                'J8: Infra Jenkins: DEPLOYMENT_TIMEOUT=300s (5 min), Spring Boot uses 1m',
                'J9: Infra Jenkins: HAS isUnix() checks for dual-OS (KUBECONFIG_UNIX and KUBECONFIG_WIN)',
                'J10: Infra Jenkins: HAS auto rollback on failure: kubectl rollout undo',
                'J11: Infra Jenkins: HAS parameters SKIP_DEPLOY and DEPLOYMENT_MODE',
                'J12: Infra Jenkins: NO Docker build stages (uses pre-existing public images)',
                'J13: Infra Jenkins: Health check verifies READY_PODS == TOTAL_PODS before marking success',
                # Jenkins Angular
                'J14: Angular Jenkins: options timestamps() timeout(30min) buildDiscarder(10)',
                'J15: Angular Jenkins: pushes both BUILD_TAG (BUILD_NUMBER-GIT_COMMIT[:7]) and latest tags',
                'J16: Angular Jenkins: npm ci --frozen-lockfile --prefer-offline --no-audit',
                'J17: Angular Jenkins: rollout timeout=1m, NO auto rollback',
                # Security
                'SEC1: NEVER add allowPrivilegeEscalation=false or container runAsUser to sudo-based images (dpage/pgadmin4)',
                'SEC2: allowPrivilegeEscalation=false sets kernel no_new_privs flag, blocks sudo in container entrypoint',
                'SEC3: For pgadmin: ONLY pod-level fsGroup=5050, NO container-level securityContext',
                'SEC4: fsGroup does NOT reliably chown hostPath volumes - ALWAYS use initContainer for permission fix',
                'SEC5: initContainer fix-permissions must run as root (runAsUser: 0) to perform chown',
                # Git workflow
                'GIT1: ALWAYS run git log --oneline -10 before ANY K8s manifest change to understand history',
                'GIT2: If a field was removed in git history, READ the commit message before re-adding',
                'GIT3: kubectl rollout undo restores old spec but does NOT update last-applied-configuration annotation',
                'GIT4: After Jenkins auto rollback, cluster spec DIFFERS from local YAML - always verify: kubectl get deployment -n ns -o yaml',
                'GIT5: To fix state mismatch after rollback: kubectl delete deployment + kubectl apply (not just kubectl apply)',
                # Checklist
                'CL1: New K8s service checklist: correct archetype, initContainer if PVC+non-root, securityContext per image type, probes, resources, NetworkPolicy, Jenkins pipeline, Jenkins seed job',
            ],
        }

    def count_total_rules(self):
        """Count total number of rules loaded"""
        total = 0
        for standard in self.standards.values():
            if 'rules' in standard:
                total += len(standard['rules'])
        return total

    def save_to_cache(self, output_file='standards-cache.json'):
        """Save loaded standards to cache file"""
        cache_file = self.memory_dir / output_file

        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump({
                'loaded_at': datetime.now().isoformat(),
                'standards': self.standards
            }, f, indent=2)

        print(f"[FLOPPY] Standards cached to: {cache_file}")

    def display_summary(self):
        """Display summary of loaded standards"""
        print(f"\n{'='*70}")
        print(f"[CLIPBOARD] STANDARDS SUMMARY")
        print(f"{'='*70}\n")

        for name, standard in self.standards.items():
            print(f"- {name.replace('_', ' ').title()}")
            if 'rules' in standard:
                print(f"  Rules: {len(standard['rules'])}")
        print()


def main():
    """CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Load coding standards for execution"
    )
    parser.add_argument(
        '--load-all',
        action='store_true',
        help='Load all coding standards'
    )
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Display summary of loaded standards'
    )
    parser.add_argument(
        '--cache',
        action='store_true',
        help='Save standards to cache file'
    )

    args = parser.parse_args()

    loader = StandardsLoader()

    if args.load_all or not any(vars(args).values()):
        standards = loader.load_all_standards()

        if args.summary:
            loader.display_summary()

        if args.cache:
            loader.save_to_cache()

    elif args.summary:
        loader.load_all_standards()
        loader.display_summary()

    elif args.cache:
        loader.load_all_standards()
        loader.save_to_cache()


if __name__ == "__main__":
    main()
