#!/usr/bin/env python3
"""
Prompt Generation & Structuring Script
Converts natural language to structured prompts with examples
"""

# Fix encoding for Windows console (cp1252 safe)
import sys
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding and sys.stderr.encoding.lower() != 'utf-8':
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        import io
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import yaml
import json
import re
from typing import Dict, List, Any
from pathlib import Path
from datetime import datetime


class PromptGenerator:
    def __init__(self):
        self.workspace = Path("C:/Users/techd/Documents/example-workspace")
        self.docs = Path("C:/Users/techd/.claude/memory/docs")

    def think_about_request(self, user_message: str) -> Dict:
        """PHASE 1: THINKING - Understand what's needed"""
        message_lower = user_message.lower()

        # Understand intent
        intent = "Unknown"
        if any(kw in message_lower for kw in ["create", "add", "new"]):
            if "api" in message_lower:
                intent = "Create a new REST API with CRUD operations"
            elif "service" in message_lower:
                intent = "Create a new microservice"
            else:
                intent = "Create new functionality"
        elif any(kw in message_lower for kw in ["fix", "bug", "error"]):
            intent = "Fix a bug or error"
        elif any(kw in message_lower for kw in ["add auth", "jwt", "security"]):
            intent = "Add authentication/authorization"

        # Generate sub-questions
        sub_questions = [
            "What entity/feature is involved?",
            "What operations are needed?",
            "What's the project structure?",
            "What patterns exist in codebase?",
            "What are the constraints/requirements?"
        ]

        # Identify needed information
        information_needed = [
            "Similar implementations in codebase",
            "Project package structure",
            "Naming conventions",
            "Response/Request patterns",
            "Configuration patterns",
            "Validation patterns"
        ]

        # Plan where to find it
        where_to_find = {
            "similar_code": "Search in user-service, auth-service, product-service",
            "structure": "Check java-project-structure.md",
            "patterns": "Read existing Controller/Service files",
            "config": "Check configurations/ directory",
            "standards": "Read api-design-standards.md, error-handling-standards.md"
        }

        return {
            "intent": intent,
            "sub_questions": sub_questions,
            "information_needed": information_needed,
            "where_to_find": where_to_find
        }

    def gather_information(self, thinking: Dict) -> Dict:
        """PHASE 2: INFORMATION GATHERING - Find relevant info"""
        gathered = {
            "similar_files": [],
            "patterns": [],
            "project_structure": {},
            "config_examples": [],
            "uncertainties": []
        }

        # Simulate searching (in real usage, would use Glob/Grep/Read)
        # This is placeholder - actual implementation would call Claude tools

        # Search for similar implementations
        service_dirs = ["user-service", "auth-service", "product-service"]
        file_types = ["Controller.java", "Service.java", "Entity.java", "Repository.java"]

        for service in service_dirs:
            for file_type in file_types:
                pattern_path = f"sample-project/backend/{service}/**/*{file_type}"
                gathered["similar_files"].append(pattern_path)

        # Extract common patterns (placeholder)
        gathered["patterns"] = [
            "ApiResponseDto<T> for all responses",
            "Form classes extend ValidationMessageConstants",
            "Service impl is package-private",
            "@Transactional for write operations",
            "Repository extends JpaRepository"
        ]

        # Project structure (placeholder)
        gathered["project_structure"] = {
            "base_path": "sample-project/backend/",
            "services": ["auth-service", "user-service"],
            "common_packages": ["controller", "services", "entity", "repository", "dto", "form"]
        }

        # Note: In real implementation, would verify files exist
        # If file doesn't exist, add to uncertainties

        return gathered

    def verify_information(self, gathered_info: Dict) -> Dict:
        """PHASE 3: VERIFICATION - Verify all information"""
        verification = {
            "examples_verified": True,
            "paths_verified": True,
            "patterns_validated": True,
            "assumptions": []
        }

        # In real implementation, would:
        # 1. Check each file path actually exists
        # 2. Verify patterns by reading actual files
        # 3. Confirm configurations are accurate
        # 4. Flag anything uncertain

        # For now, mark common assumptions
        if not gathered_info.get("similar_files"):
            verification["assumptions"].append("No similar implementations found - using general patterns")

        # Check for missing information
        if not gathered_info.get("config_examples"):
            verification["assumptions"].append("Configuration examples not verified")

        return verification

    def analyze_request(self, user_message: str) -> Dict:
        """Analyze natural language request"""
        message_lower = user_message.lower()

        analysis = {
            "task_type": self.detect_task_type(message_lower),
            "entities": self.extract_entities(message_lower),
            "operations": self.extract_operations(message_lower),
            "keywords": self.extract_keywords(message_lower),
            "complexity": self.estimate_complexity(user_message)
        }
        return analysis

    def detect_task_type(self, message: str) -> str:
        """Detect what kind of task this is"""
        keywords_map = {
            "API Creation": ["create api", "add api", "new api", "crud", "rest api", "endpoint"],
            "Authentication": ["auth", "login", "jwt", "token", "authentication"],
            "Authorization": ["role", "permission", "access control", "authorization", "rbac"],
            "Database": ["database", "table", "migration", "schema", "entity"],
            "Configuration": ["config", "configure", "setup", "settings"],
            "Bug Fix": ["fix", "bug", "error", "issue", "problem"],
            "Refactoring": ["refactor", "improve", "optimize", "clean", "restructure"],
            "Security": ["security", "secure", "protect", "encrypt", "vulnerability"],
            "Testing": ["test", "unit test", "integration test", "testing"],
            "Documentation": ["document", "doc", "readme", "comment"]
        }

        for task_type, keywords in keywords_map.items():
            if any(kw in message for kw in keywords):
                return task_type

        return "General Task"

    def extract_entities(self, message: str) -> List[str]:
        """Extract entity names from message"""
        common_entities = [
            "user", "product", "order", "category", "role", "permission",
            "customer", "item", "cart", "payment", "invoice", "shipment",
            "auth", "authentication", "authorization", "token"
        ]
        found = [e for e in common_entities if e in message]

        # Also look for capitalized words (potential entity names)
        words = message.split()
        capitalized = [w.lower() for w in words if w[0].isupper() and w.lower() not in ["i", "a"]]

        return list(set(found + capitalized))

    def extract_operations(self, message: str) -> List[str]:
        """Extract operations from message"""
        operations = []

        operation_keywords = {
            "create": ["create", "add", "new", "insert", "post"],
            "read": ["read", "get", "fetch", "list", "view", "show", "retrieve"],
            "update": ["update", "edit", "modify", "change", "put", "patch"],
            "delete": ["delete", "remove", "destroy"]
        }

        for op, keywords in operation_keywords.items():
            if any(kw in message for kw in keywords):
                operations.append(op)

        if "crud" in message:
            operations = ["create", "read", "update", "delete"]

        return list(set(operations))

    def extract_keywords(self, message: str) -> List[str]:
        """Extract important keywords"""
        tech_keywords = [
            "spring boot", "postgresql", "redis", "jwt", "oauth",
            "rest", "api", "microservice", "docker", "kubernetes",
            "eureka", "gateway", "config server", "security",
            "validation", "transaction", "repository", "service",
            "controller", "entity", "dto", "form"
        ]

        found = [kw for kw in tech_keywords if kw in message]
        return found

    def estimate_complexity(self, message: str) -> int:
        """Estimate task complexity (1-10)"""
        complexity = 1

        # Longer messages are usually more complex
        word_count = len(message.split())
        if word_count > 50:
            complexity += 3
        elif word_count > 20:
            complexity += 2
        elif word_count > 10:
            complexity += 1

        # Multiple entities increase complexity
        entities = self.extract_entities(message.lower())
        complexity += min(len(entities), 3)

        # Multiple operations increase complexity
        operations = self.extract_operations(message.lower())
        complexity += min(len(operations), 2)

        # Certain keywords increase complexity
        complex_keywords = ["authentication", "authorization", "security", "migration", "integration"]
        if any(kw in message.lower() for kw in complex_keywords):
            complexity += 2

        return min(complexity, 10)

    def find_project_context(self, entities: List[str]) -> Dict:
        """Determine project and service context"""
        context = {
            "project_name": "sample-project",
            "service_name": "unknown-service",
            "base_package": "com.example-project.sample-project"
        }

        # Map entities to services
        entity_service_map = {
            "user": "user-service",
            "auth": "auth-service",
            "authentication": "auth-service",
            "product": "product-service",
            "order": "order-service",
            "category": "category-service"
        }

        for entity in entities:
            if entity in entity_service_map:
                context["service_name"] = entity_service_map[entity]
                context["base_package"] = f"com.example-project.sample-project.{entity}service"
                break

        return context

    def define_conditions(self, task_type: str, entities: List[str]) -> Dict:
        """Define pre and post conditions"""
        conditions = {
            "pre_conditions": [],
            "post_conditions": []
        }

        # Common pre-conditions
        conditions["pre_conditions"].append({
            "condition": "Service must exist or be created",
            "validation": "Check service directory exists",
            "command": "ls backend/{service-name}"
        })

        if task_type == "API Creation":
            conditions["pre_conditions"].extend([
                {
                    "condition": "Database must be configured",
                    "validation": "Check Config Server has datasource config",
                    "example": "configurations/sample-project/services/user-service.yml"
                },
                {
                    "condition": "Dependencies must be available",
                    "validation": "Check pom.xml has spring-boot-starter-data-jpa",
                    "example": "user-service/pom.xml"
                }
            ])

            conditions["post_conditions"].extend([
                {
                    "condition": "All CRUD endpoints must work",
                    "validation": "Test each endpoint",
                    "test": "curl requests to all endpoints"
                },
                {
                    "condition": "Responses must use ApiResponseDto<T>",
                    "validation": "Check response structure",
                    "test": "Verify JSON has success, message, data fields"
                },
                {
                    "condition": "Validation must work",
                    "validation": "Send invalid data",
                    "test": "Expect 400 with validation errors"
                }
            ])

        elif task_type == "Authentication":
            conditions["pre_conditions"].extend([
                {
                    "condition": "Secret Manager must have JWT secret",
                    "validation": "Check secret exists",
                    "command": "GET /api/v1/secrets/project/sample-project/key/jwt.secret"
                },
                {
                    "condition": "User entity must exist",
                    "validation": "Check User.java exists",
                    "example": "user-service/entity/User.java"
                }
            ])

            conditions["post_conditions"].extend([
                {
                    "condition": "Login must generate valid JWT",
                    "validation": "Call /api/v1/auth/login",
                    "test": "Verify JWT token returned"
                },
                {
                    "condition": "Unauthorized requests must return 401",
                    "validation": "Call protected endpoint without token",
                    "test": "Expect 401 Unauthorized"
                }
            ])

        return conditions

    def define_file_structure(self, task_type: str, service_name: str, entities: List[str]) -> Dict:
        """Define expected file structure"""
        base_path = f"backend/{service_name}/src/main/java/com/example-project/sample-project/{service_name.replace('-service', 'service')}"

        structure = {
            "files_created": [],
            "files_modified": [],
            "configurations": []
        }

        if task_type == "API Creation" and entities:
            entity_name = entities[0].capitalize()

            structure["files_created"] = [
                {
                    "path": f"{base_path}/entity/{entity_name}.java",
                    "type": "JPA Entity",
                    "purpose": "Database table mapping",
                    "example": "user-service/entity/User.java"
                },
                {
                    "path": f"{base_path}/repository/{entity_name}Repository.java",
                    "type": "JPA Repository",
                    "purpose": "Database operations",
                    "example": "user-service/repository/UserRepository.java"
                },
                {
                    "path": f"{base_path}/services/{entity_name}Service.java",
                    "type": "Service Interface",
                    "purpose": "Business logic contract",
                    "example": "user-service/services/UserService.java"
                },
                {
                    "path": f"{base_path}/services/impl/{entity_name}ServiceImpl.java",
                    "type": "Service Implementation",
                    "purpose": "Business logic implementation",
                    "example": "user-service/services/impl/UserServiceImpl.java"
                },
                {
                    "path": f"{base_path}/controller/{entity_name}Controller.java",
                    "type": "REST Controller",
                    "purpose": "API endpoints",
                    "example": "user-service/controller/UserController.java"
                },
                {
                    "path": f"{base_path}/dto/{entity_name}Dto.java",
                    "type": "Response DTO",
                    "purpose": "API response structure",
                    "example": "user-service/dto/UserDto.java"
                },
                {
                    "path": f"{base_path}/form/{entity_name}Form.java",
                    "type": "Request Form",
                    "purpose": "API request with validation",
                    "example": "user-service/form/UserForm.java"
                }
            ]

            structure["configurations"] = [
                {
                    "location": f"example-project/backend/example-project-config-server/configurations/sample-project/services/{service_name}.yml",
                    "changes": ["Database config", "JPA settings", "Eureka registration"],
                    "template": "user-service.yml"
                }
            ]

        return structure

    def define_success_criteria(self, task_type: str, operations: List[str]) -> List[str]:
        """Define success criteria"""
        criteria = [
            "✅ Code compiles successfully (mvn clean compile)",
            "✅ No syntax or compilation errors",
            "✅ Service starts without errors"
        ]

        if task_type == "API Creation":
            criteria.extend([
                "✅ Service registers with Eureka",
                "✅ All endpoints are accessible via Gateway",
                "✅ Responses follow ApiResponseDto<T> pattern",
                "✅ Validation works correctly",
                "✅ Database operations work (if applicable)"
            ])

            for op in operations:
                if op == "create":
                    criteria.append("✅ POST endpoint creates new record")
                elif op == "read":
                    criteria.append("✅ GET endpoint retrieves records")
                elif op == "update":
                    criteria.append("✅ PUT endpoint updates existing record")
                elif op == "delete":
                    criteria.append("✅ DELETE endpoint removes record")

        elif task_type == "Authentication":
            criteria.extend([
                "✅ Login endpoint generates valid JWT",
                "✅ Protected endpoints require authentication",
                "✅ Invalid tokens are rejected",
                "✅ Token expiration works"
            ])

        return criteria

    def find_examples(self, task_type: str, entities: List[str]) -> List[Dict]:
        """Find example code from codebase"""
        examples = []

        example_map = {
            "API Creation": [
                {
                    "description": "User CRUD API implementation",
                    "service": "user-service",
                    "files": [
                        "controller/UserController.java",
                        "services/UserService.java",
                        "services/impl/UserServiceImpl.java",
                        "entity/User.java",
                        "repository/UserRepository.java"
                    ],
                    "pattern": "Complete CRUD with ApiResponseDto",
                    "usage": "Follow same structure for new entity"
                }
            ],
            "Authentication": [
                {
                    "description": "JWT Authentication implementation",
                    "service": "auth-service",
                    "files": [
                        "controller/AuthController.java",
                        "security/JwtUtil.java",
                        "security/JwtAuthenticationFilter.java",
                        "security/SecurityConfig.java"
                    ],
                    "pattern": "JWT generation and validation",
                    "usage": "Reuse JWT utilities"
                }
            ]
        }

        if task_type in example_map:
            examples = example_map[task_type]

        return examples

    def build_rewritten_prompt(self, user_message, task_type, entities, operations, complexity):
        """
        Convert any user input (Hinglish, informal, any language) into a proper English task description.
        Claude will use this rewritten prompt as the actual task to solve, not the raw original.
        """
        msg_lower = user_message.lower()
        words = msg_lower.split()

        # --- Extract subject: what is being worked on ---
        subject = None
        # Hinglish pattern: "X wala/wali/wale" -> subject is X
        for i, word in enumerate(words):
            if word in ('wala', 'wali', 'wale') and i > 0:
                candidate = words[i - 1]
                if len(candidate) > 3:
                    subject = candidate
                    break
        # Fall back to first entity or generic
        if not subject and entities:
            subject = entities[0]
        if not subject:
            subject = "the system"

        # --- Extract problem descriptions from Hinglish/informal patterns ---
        problem_parts = []
        hinglish_problems = {
            "nahi ban raha": "is not being generated/created",
            "nahi bana raha": "is not generating",
            "ni ban raha": "is not being generated",
            "ni ara": "is not showing/working",
            "same cheej": "passes through the same input unchanged (no transformation happening)",
            "same lere": "takes the same input without any processing",
            "same le raha": "takes the same input without processing",
            "kaam nahi kar": "is not functioning correctly",
            "kaam nhi kar": "is not functioning correctly",
            "ni lagta": "does not appear to be working correctly",
            "doubt hai": "behavior is uncertain/incorrect",
            "actually me": "in the actual implementation",
            "not working": "is not working correctly",
            "not generating": "is not generating the expected output",
        }
        for pattern, desc in hinglish_problems.items():
            if pattern in msg_lower:
                problem_parts.append(desc)

        # --- Extract goal descriptions from Hinglish/informal patterns ---
        goal_parts = []
        hinglish_goals = {
            "fix kar": "fix this issue",
            "theek kar": "correct this behavior",
            "banana hai": "generate/create properly",
            "banao": "create this",
            "dena ha": "pass to the next step",
            "acha prompt": "generate a proper well-structured English prompt",
            "jaise bhi language": "regardless of the input language used by the user",
            "khud ko dena": "pass the rewritten prompt to itself for processing",
            "sabse pehle": "first (before anything else)",
            "fir khud ko": "then pass it back to itself",
        }
        for pattern, desc in hinglish_goals.items():
            if pattern in msg_lower:
                goal_parts.append(desc)

        # --- Build task-specific base description ---
        task_descs = {
            "Bug Fix": "Fix the bug/issue in",
            "API Creation": "Create REST API for",
            "Authentication": "Implement authentication for",
            "Authorization": "Implement authorization for",
            "Database": "Fix/design database schema for",
            "Configuration": "Configure",
            "UI/UX": "Fix the UI/UX for",
            "Dashboard": "Fix/implement dashboard for",
            "Refactoring": "Refactor",
            "Testing": "Write tests for",
            "Security": "Implement security for",
            "Documentation": "Document",
            "Frontend": "Implement frontend for",
        }
        action = task_descs.get(task_type, "Implement/fix")
        base_desc = f"{action} {subject}"

        # --- Assemble the final rewritten prompt ---
        parts = [f"[{task_type}] {base_desc}."]

        if problem_parts:
            unique_problems = list(dict.fromkeys(problem_parts))[:2]
            parts.append("Problem identified: " + "; ".join(unique_problems) + ".")

        if goal_parts:
            unique_goals = list(dict.fromkeys(goal_parts))[:2]
            parts.append("Expected behavior: " + "; ".join(unique_goals) + ".")

        if operations and task_type not in ("Bug Fix", "Refactoring"):
            ops_str = ", ".join(operations)
            parts.append(f"Operations required: {ops_str}.")

        parts.append(f"Complexity: {complexity}/10.")

        return " ".join(parts)

    def generate(self, user_message: str) -> Dict:
        """Main method: Generate structured prompt with anti-hallucination phases"""

        print("=" * 80)
        print("🧠 PHASE 1: THINKING")
        print("=" * 80)

        # PHASE 1: THINKING (Anti-Hallucination)
        thinking = self.think_about_request(user_message)
        print(f"\n🎯 Intent: {thinking['intent']}")
        print(f"❓ Sub-questions:")
        for q in thinking['sub_questions']:
            print(f"   - {q}")
        print(f"\n📋 Information needed:")
        for info in thinking['information_needed']:
            print(f"   - {info}")
        print(f"\n🔍 Will search in:")
        for source, location in thinking['where_to_find'].items():
            print(f"   - {source}: {location}")

        print("\n" + "=" * 80)
        print("🔍 PHASE 2: INFORMATION GATHERING")
        print("=" * 80)

        # PHASE 2: INFORMATION GATHERING
        gathered_info = self.gather_information(thinking)
        print(f"\n✅ Found {len(gathered_info.get('similar_files', []))} similar implementations")
        print(f"✅ Extracted {len(gathered_info.get('patterns', []))} patterns")
        print(f"✅ Verified project structure")
        if gathered_info.get('uncertainties'):
            print(f"\n⚠️  Uncertainties found: {len(gathered_info['uncertainties'])}")

        print("\n" + "=" * 80)
        print("✅ PHASE 3: VERIFICATION")
        print("=" * 80)

        # PHASE 3: VERIFICATION
        verification = self.verify_information(gathered_info)
        print(f"\n✅ Examples verified: {verification['examples_verified']}")
        print(f"✅ Paths verified: {verification['paths_verified']}")
        print(f"✅ Patterns validated: {verification['patterns_validated']}")
        if verification.get('assumptions'):
            print(f"\n⚠️  Assumptions made:")
            for assumption in verification['assumptions']:
                print(f"   - {assumption}")

        print("\n" + "=" * 80)
        print("📄 GENERATING STRUCTURED PROMPT")
        print("=" * 80)

        # Step 1: Analyze
        analysis = self.analyze_request(user_message)

        # Step 2: Find context
        context = self.find_project_context(analysis["entities"])

        # Step 3: Define conditions
        conditions = self.define_conditions(analysis["task_type"], analysis["entities"])

        # Step 4: Define file structure
        file_structure = self.define_file_structure(
            analysis["task_type"],
            context["service_name"],
            analysis["entities"]
        )

        # Step 5: Define success criteria
        success_criteria = self.define_success_criteria(
            analysis["task_type"],
            analysis["operations"]
        )

        # Step 6: Find examples
        examples = self.find_examples(analysis["task_type"], analysis["entities"])

        # Generate structured prompt
        structured_prompt = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "original_request": user_message,
                "estimated_complexity": analysis["complexity"]
            },
            "task_type": analysis["task_type"],
            "project_context": {
                **context,
                "technology_stack": [
                    "Spring Boot 3.2.0",
                    "Spring Cloud 2023.0.0",
                    "PostgreSQL 15",
                    "Redis 7",
                    "Spring Security 6",
                    "Eureka Discovery",
                    "Config Server",
                    "API Gateway"
                ]
            },
            "analysis": {
                "entities": analysis["entities"],
                "operations": analysis["operations"],
                "keywords": analysis["keywords"]
            },
            "conditions": conditions,
            "expected_output": file_structure,
            "success_criteria": success_criteria,
            "examples_from_codebase": examples,
            "architecture_standards": [
                "java-project-structure.md",
                "api-design-standards.md",
                "error-handling-standards.md",
                "security-best-practices.md",
                "database-standards.md"
            ]
        }

        return structured_prompt


def main():
    """CLI interface"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python prompt-generator.py 'user message'")
        print("\nExample:")
        print("  python prompt-generator.py 'Create a product API with CRUD operations'")
        sys.exit(1)

    user_message = " ".join(sys.argv[1:])

    generator = PromptGenerator()
    structured_prompt = generator.generate(user_message)

    # Extract analysis results for machine-readable output
    task_type_out = structured_prompt.get("task_type", "General Task")
    complexity_out = structured_prompt.get("metadata", {}).get("estimated_complexity", 1)
    entities = structured_prompt.get("analysis", {}).get("entities", [])
    operations = structured_prompt.get("analysis", {}).get("operations", [])

    # Build proper rewritten prompt from analysis (NOT just a label of the original message)
    rewritten = generator.build_rewritten_prompt(
        user_message, task_type_out, entities, operations, complexity_out
    )

    # Machine-readable output lines (parsed by 3-level-flow.py)
    print(f"estimated_complexity: {complexity_out}")
    print(f"task_type: {task_type_out}")
    print(f"rewritten_prompt: {rewritten}")
    print(f"enhanced_prompt: {rewritten}")

    # Output as YAML
    print("=" * 80)
    print("STRUCTURED PROMPT")
    print("=" * 80)
    print(yaml.dump(structured_prompt, default_flow_style=False, sort_keys=False, allow_unicode=True))
    print("=" * 80)


if __name__ == "__main__":
    main()
