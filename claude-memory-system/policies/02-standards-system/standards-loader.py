#!/usr/bin/env python3
"""
Coding Standards Loader
Loads all coding standards before execution
"""

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
        print(f"🔧 CODING STANDARDS LOADER")
        print(f"{'='*70}\n")

        print("📋 Loading standards from documentation...\n")

        # 1. Java Project Structure
        print("  [1/12] Java Project Structure...")
        self.standards['java_structure'] = self.load_java_structure()
        print("         ✅ Loaded")

        # 2. Config Server Rules
        print("  [2/12] Config Server Rules...")
        self.standards['config_server'] = self.load_config_server_rules()
        print("         ✅ Loaded")

        # 3. Secret Management
        print("  [3/12] Secret Management...")
        self.standards['secret_management'] = self.load_secret_management()
        print("         ✅ Loaded")

        # 4. Response Format
        print("  [4/12] Response Format...")
        self.standards['response_format'] = self.load_response_format()
        print("         ✅ Loaded")

        # 5. API Design
        print("  [5/12] API Design Standards...")
        self.standards['api_design'] = self.load_api_design()
        print("         ✅ Loaded")

        # 6. Database Standards
        print("  [6/12] Database Standards...")
        self.standards['database'] = self.load_database_standards()
        print("         ✅ Loaded")

        # 7. Error Handling
        print("  [7/12] Error Handling...")
        self.standards['error_handling'] = self.load_error_handling()
        print("         ✅ Loaded")

        # 8. Service Layer Pattern
        print("  [8/12] Service Layer Pattern...")
        self.standards['service_pattern'] = self.load_service_pattern()
        print("         ✅ Loaded")

        # 9. Entity Pattern
        print("  [9/12] Entity Pattern...")
        self.standards['entity_pattern'] = self.load_entity_pattern()
        print("         ✅ Loaded")

        # 10. Controller Pattern
        print(" [10/12] Controller Pattern...")
        self.standards['controller_pattern'] = self.load_controller_pattern()
        print("         ✅ Loaded")

        # 11. Constants Organization
        print(" [11/12] Constants Organization...")
        self.standards['constants'] = self.load_constants_organization()
        print("         ✅ Loaded")

        # 12. Common Utilities
        print(" [12/12] Common Utilities...")
        self.standards['utilities'] = self.load_common_utilities()
        print("         ✅ Loaded")

        print(f"\n{'='*70}")
        print(f"✅ ALL STANDARDS LOADED SUCCESSFULLY")
        print(f"{'='*70}\n")

        print(f"📊 Summary:")
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
                'ALL other configs (DB, Redis, Feign, etc.) → Config Server',
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

        print(f"💾 Standards cached to: {cache_file}")

    def display_summary(self):
        """Display summary of loaded standards"""
        print(f"\n{'='*70}")
        print(f"📋 STANDARDS SUMMARY")
        print(f"{'='*70}\n")

        for name, standard in self.standards.items():
            print(f"• {name.replace('_', ' ').title()}")
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
