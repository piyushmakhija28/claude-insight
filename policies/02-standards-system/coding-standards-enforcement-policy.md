# 🔧 Coding Standards Enforcement Policy

**VERSION:** 1.0.0
**CREATED:** 2026-02-16
**PRIORITY:** 🔴 CRITICAL - MIDDLE LAYER (Between Sync and Execution)
**STATUS:** 🟢 ACTIVE

---

## 📋 POLICY OVERVIEW

**PURPOSE:** Enforce coding standards and architectural rules BEFORE execution.

**POSITION IN FLOW:**
```
Sync System (Context + Session)
        ↓
🔴 RULES/STANDARDS SYSTEM (THIS POLICY)  ← Load rules BEFORE execution
        ↓
Execution System (Policies + Implementation)
```

**MANDATORY:** This policy MUST run after Sync System and BEFORE Execution System.

---

## 🎯 WHAT THIS SYSTEM DOES

### **Load ALL Coding Standards Before Code Generation:**

1. **Java/Spring Boot Structure Rules**
2. **Package Organization Standards**
3. **Config Server Usage Rules**
4. **Secret Management Patterns**
5. **Response Format Standards**
6. **Validation Patterns**
7. **Database Conventions**
8. **API Design Standards**
9. **Error Handling Rules**
10. **Common Utility Patterns**

**WHY:** So that EVERY piece of code generated follows the SAME standards!

---

## 📚 STANDARDS REGISTRY

### **1. Java Project Structure (MANDATORY)**

**Source:** `~/.claude/memory/docs/java-project-structure.md`

```
Base Package: com.techdeveloper.{projectname}.{servicename}

Package Structure:
├── controller/              # REST endpoints (public)
├── dto/                     # Response objects (public)
├── form/                    # Request objects (public)
├── constants/               # All constants/enums (public)
│   ├── ApiConstants.java
│   ├── MessageConstants.java
│   └── ValidationMessageConstants.java
├── enums/                   # Enums (public)
├── services/                # Service interfaces (public)
├── services.impl/           # Implementations (package-private)
├── services.helper/         # Helper classes (package-private)
├── entity/                  # Database entities (package-private)
├── repository/              # Data access (package-private)
├── client/                  # Feign clients (package-private)
├── config/                  # Configuration classes
├── exception/               # Custom exceptions
└── utils/                   # Common utilities

RULES:
✅ Service implementations are package-private
✅ Service implementations extend Helper classes
✅ All responses use ApiResponseDto<T>
✅ Form classes extend ValidationMessageConstants
✅ NO hardcoded messages (use constants)
✅ @Transactional on all write operations
```

---

### **2. Spring Cloud Config Server (MANDATORY)**

**Source:** `~/.claude/memory/docs/spring-cloud-config.md`

```
Config Location: {project}/backend/config-server/configurations/

Structure:
configurations/
├── application.yml                    # Global (ALL services)
├── {project}/
│   ├── common/*.yml                  # Project common
│   └── services/{service}.yml        # Service-specific

Microservice application.yml (ONLY THIS!):
spring:
  application:
    name: service-name
  config:
    import: "configserver:http://localhost:8888"
  cloud:
    config:
      fail-fast: true

secret-manager:
  client:
    enabled: true
    project-name: "project-name"

RULES:
✅ ONLY application name + config import in microservice
✅ ALL other configs (DB, Redis, Feign, etc.) → Config Server
❌ NEVER add database config in microservice application.yml
❌ NEVER add port numbers in microservice application.yml
❌ NEVER hardcode any config in microservice
```

---

### **3. Secret Management (MANDATORY)**

**Source:** `~/.claude/memory/docs/secret-management.md`

```
Services:
- Secret Manager: Port 1002
- Project Management: Port 8109

Microservice Config:
secret-manager:
  client:
    enabled: true
    project-name: "project-name"
    base-url: "http://localhost:8085/api/v1/secrets"

Secret Storage:
- Database passwords → Secret Manager
- API keys → Secret Manager
- JWT secrets → Secret Manager
- Email passwords → Secret Manager

Config Server Usage:
spring:
  datasource:
    password: ${SECRET:db-password}  # Fetch from Secret Manager

RULES:
✅ ALL secrets in Secret Manager
✅ Config server uses ${SECRET:key-name} syntax
❌ NEVER hardcode secrets
❌ NEVER commit .env files
❌ NEVER store secrets in application.yml
```

---

### **4. Response Format (MANDATORY)**

**Source:** `~/.claude/memory/docs/api-design-standards.md`

```
ALL APIs return ApiResponseDto<T>:

public class ApiResponseDto<T> {
    private String status;      // "SUCCESS" or "ERROR"
    private String message;     // Human-readable message
    private T data;             // Actual data (or null)
    private String timestamp;   // ISO 8601 timestamp
}

Example:
{
  "status": "SUCCESS",
  "message": "Product retrieved successfully",
  "data": {
    "id": 123,
    "name": "Product Name"
  },
  "timestamp": "2026-02-16T14:30:00Z"
}

Controller Pattern:
@GetMapping("/{id}")
public ResponseEntity<ApiResponseDto<ProductResponseDto>> getById(@PathVariable Long id) {
    ProductResponseDto product = productService.findById(id);
    return ResponseEntity.ok(ApiResponseDto.success("Product retrieved", product));
}

RULES:
✅ ALL responses use ApiResponseDto<T>
✅ Message from MessageConstants (never hardcoded)
✅ Use .success() or .error() factory methods
❌ NEVER return raw DTOs
❌ NEVER return ResponseEntity<ProductDto>
❌ NEVER hardcode messages
```

---

### **5. Form Validation (MANDATORY)**

**Source:** `~/.claude/memory/docs/api-design-standards.md`

```
ALL request forms extend ValidationMessageConstants:

public class ProductCreateForm extends ValidationMessageConstants {

    @NotBlank(message = PRODUCT_NAME_REQUIRED)
    @Size(min = 3, max = 100, message = PRODUCT_NAME_SIZE)
    private String name;

    @NotNull(message = PRODUCT_PRICE_REQUIRED)
    @Min(value = 0, message = PRODUCT_PRICE_MIN)
    private BigDecimal price;

    @Pattern(regexp = "^(ACTIVE|INACTIVE)$", message = PRODUCT_STATUS_INVALID)
    private String status;
}

ValidationMessageConstants:
public class ValidationMessageConstants {
    public static final String PRODUCT_NAME_REQUIRED = "Product name is required";
    public static final String PRODUCT_NAME_SIZE = "Product name must be 3-100 characters";
    // ... all validation messages
}

RULES:
✅ Forms extend ValidationMessageConstants
✅ ALL validation messages in constants
✅ Use standard annotations (@NotBlank, @Size, @Pattern, etc.)
❌ NEVER hardcode validation messages
❌ NEVER use raw strings in @NotBlank(message = "...")
```

---

### **6. Service Layer Pattern (MANDATORY)**

**Source:** `~/.claude/memory/docs/java-project-structure.md`

```
Service Interface (public):
public interface ProductService {
    ProductResponseDto findById(Long id);
    ProductResponseDto create(ProductCreateForm form);
    ProductResponseDto update(Long id, ProductUpdateForm form);
    void delete(Long id);
}

Service Implementation (package-private):
@Service
class ProductServiceImpl extends ProductServiceHelper implements ProductService {

    private final ProductRepository productRepository;

    @Override
    public ProductResponseDto findById(Long id) {
        Product product = findProductById(id);  // From helper
        return mapToDto(product);               // From helper
    }

    @Override
    @Transactional
    public ProductResponseDto create(ProductCreateForm form) {
        validateProductName(form.getName());   // From helper
        Product product = buildProductEntity(form);
        product = productRepository.save(product);
        return mapToDto(product);
    }
}

Service Helper (package-private):
abstract class ProductServiceHelper {
    @Autowired
    protected ProductRepository productRepository;

    protected Product findProductById(Long id) {
        return productRepository.findById(id)
            .orElseThrow(() -> new ProductNotFoundException(id));
    }

    protected void validateProductName(String name) {
        if (productRepository.existsByName(name)) {
            throw new ProductAlreadyExistsException(name);
        }
    }

    protected ProductResponseDto mapToDto(Product product) {
        // Mapping logic
    }
}

RULES:
✅ Service interface is public
✅ Service implementation is package-private (no public modifier)
✅ Service implementation extends Helper
✅ Helper contains reusable logic
✅ @Transactional on write operations (create, update, delete)
❌ NEVER make implementation public
❌ NEVER put business logic directly in controller
```

---

### **7. Entity Pattern (MANDATORY)**

**Source:** `~/.claude/memory/docs/database-standards.md`

```
@Entity
@Table(name = "products")
class Product {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "name", nullable = false, length = 100)
    private String name;

    @Column(name = "price", nullable = false, precision = 10, scale = 2)
    private BigDecimal price;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", length = 20)
    private ProductStatus status;

    // Audit fields (MANDATORY)
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    @Column(name = "created_by")
    private Long createdBy;

    @Column(name = "updated_by")
    private Long updatedBy;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        updatedAt = LocalDateTime.now();
    }

    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }
}

RULES:
✅ Entity is package-private
✅ Table name explicitly specified
✅ Column names explicit (snake_case in DB)
✅ Audit fields mandatory (created_at, updated_at, created_by, updated_by)
✅ @PrePersist and @PreUpdate for timestamps
❌ NEVER use camelCase in DB column names
❌ NEVER make entity public
❌ NEVER skip audit fields
```

---

### **8. Repository Pattern (MANDATORY)**

**Source:** `~/.claude/memory/docs/database-standards.md`

```
Repository is package-private:
interface ProductRepository extends JpaRepository<Product, Long> {

    Optional<Product> findByName(String name);

    boolean existsByName(String name);

    @Query("SELECT p FROM Product p WHERE p.status = :status")
    List<Product> findByStatus(@Param("status") ProductStatus status);

    @Query("SELECT p FROM Product p WHERE p.name LIKE %:keyword%")
    Page<Product> searchByName(@Param("keyword") String keyword, Pageable pageable);
}

RULES:
✅ Repository is package-private
✅ Use method naming conventions (findBy, existsBy, etc.)
✅ Complex queries use @Query
✅ Pagination with Pageable
❌ NEVER make repository public
❌ NEVER write raw SQL (use JPQL)
```

---

### **9. Controller Pattern (MANDATORY)**

**Source:** `~/.claude/memory/docs/api-design-standards.md`

```
@RestController
@RequestMapping("/api/v1/products")
public class ProductController {

    private final ProductService productService;

    @GetMapping("/{id}")
    public ResponseEntity<ApiResponseDto<ProductResponseDto>> getById(
        @PathVariable Long id
    ) {
        ProductResponseDto product = productService.findById(id);
        return ResponseEntity.ok(
            ApiResponseDto.success(MessageConstants.PRODUCT_RETRIEVED, product)
        );
    }

    @PostMapping
    public ResponseEntity<ApiResponseDto<ProductResponseDto>> create(
        @Valid @RequestBody ProductCreateForm form
    ) {
        ProductResponseDto product = productService.create(form);
        return ResponseEntity.status(HttpStatus.CREATED)
            .body(ApiResponseDto.success(MessageConstants.PRODUCT_CREATED, product));
    }

    @PutMapping("/{id}")
    public ResponseEntity<ApiResponseDto<ProductResponseDto>> update(
        @PathVariable Long id,
        @Valid @RequestBody ProductUpdateForm form
    ) {
        ProductResponseDto product = productService.update(id, form);
        return ResponseEntity.ok(
            ApiResponseDto.success(MessageConstants.PRODUCT_UPDATED, product)
        );
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<ApiResponseDto<Void>> delete(@PathVariable Long id) {
        productService.delete(id);
        return ResponseEntity.ok(
            ApiResponseDto.success(MessageConstants.PRODUCT_DELETED, null)
        );
    }
}

RULES:
✅ Controller is public
✅ Base path /api/v1/{resource}
✅ Use standard HTTP methods (GET, POST, PUT, DELETE)
✅ @Valid on request body
✅ Messages from constants
✅ Return ApiResponseDto wrapper
❌ NEVER put business logic in controller
❌ NEVER hardcode messages
❌ NEVER return raw DTOs
```

---

### **10. Exception Handling (MANDATORY)**

**Source:** `~/.claude/memory/docs/error-handling-standards.md`

```
Custom Exceptions:
public class ProductNotFoundException extends RuntimeException {
    public ProductNotFoundException(Long id) {
        super("Product not found with id: " + id);
    }
}

public class ProductAlreadyExistsException extends RuntimeException {
    public ProductAlreadyExistsException(String name) {
        super("Product already exists with name: " + name);
    }
}

Global Exception Handler:
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(ProductNotFoundException.class)
    public ResponseEntity<ApiResponseDto<Void>> handleNotFound(ProductNotFoundException ex) {
        return ResponseEntity.status(HttpStatus.NOT_FOUND)
            .body(ApiResponseDto.error(ex.getMessage()));
    }

    @ExceptionHandler(ProductAlreadyExistsException.class)
    public ResponseEntity<ApiResponseDto<Void>> handleAlreadyExists(ProductAlreadyExistsException ex) {
        return ResponseEntity.status(HttpStatus.CONFLICT)
            .body(ApiResponseDto.error(ex.getMessage()));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiResponseDto<Map<String, String>>> handleValidation(
        MethodArgumentNotValidException ex
    ) {
        Map<String, String> errors = new HashMap<>();
        ex.getBindingResult().getFieldErrors().forEach(error ->
            errors.put(error.getField(), error.getDefaultMessage())
        );
        return ResponseEntity.status(HttpStatus.BAD_REQUEST)
            .body(ApiResponseDto.error("Validation failed", errors));
    }
}

RULES:
✅ Custom exceptions for domain errors
✅ Global exception handler with @RestControllerAdvice
✅ Return ApiResponseDto for all errors
✅ Appropriate HTTP status codes
❌ NEVER swallow exceptions
❌ NEVER expose stack traces to client
```

---

### **11. Constants Organization (MANDATORY)**

```
constants/
├── ApiConstants.java           # API paths, versions
├── MessageConstants.java        # Response messages
├── ValidationMessageConstants.java  # Validation messages
├── DatabaseConstants.java       # DB-related constants
└── SecurityConstants.java       # Security-related constants

ApiConstants:
public class ApiConstants {
    public static final String API_VERSION = "v1";
    public static final String API_BASE_PATH = "/api/" + API_VERSION;
    public static final String PRODUCTS_PATH = API_BASE_PATH + "/products";
}

MessageConstants:
public class MessageConstants {
    public static final String PRODUCT_RETRIEVED = "Product retrieved successfully";
    public static final String PRODUCT_CREATED = "Product created successfully";
    public static final String PRODUCT_UPDATED = "Product updated successfully";
    public static final String PRODUCT_DELETED = "Product deleted successfully";
}

RULES:
✅ ALL constants in appropriate constant classes
✅ NO magic numbers/strings in code
✅ Use constants everywhere
❌ NEVER hardcode strings/numbers
❌ NEVER duplicate constants
```

---

### **12. Common Utilities (MANDATORY)**

**Source:** Common patterns across projects

```
utils/
├── DateTimeUtils.java          # Date/time operations
├── StringUtils.java            # String operations
├── ValidationUtils.java        # Custom validations
└── MapperUtils.java            # DTO mapping

DateTimeUtils:
public class DateTimeUtils {
    public static String toIso8601(LocalDateTime dateTime) {
        return dateTime.format(DateTimeFormatter.ISO_DATE_TIME);
    }

    public static LocalDateTime now() {
        return LocalDateTime.now();
    }
}

MapperUtils:
public class MapperUtils {
    private static final ModelMapper modelMapper = new ModelMapper();

    public static <D, E> D map(E entity, Class<D> dtoClass) {
        return modelMapper.map(entity, dtoClass);
    }

    public static <D, E> List<D> mapList(List<E> entities, Class<D> dtoClass) {
        return entities.stream()
            .map(entity -> map(entity, dtoClass))
            .collect(Collectors.toList());
    }
}

RULES:
✅ Utility classes for common operations
✅ Reuse utilities across services
✅ Static methods only
❌ NEVER duplicate utility logic
❌ NEVER put utilities in service classes
```

---

## 🔄 ENFORCEMENT FLOW

### **When This System Runs:**

```
User Request: "Create Product API"
        ↓
SYNC SYSTEM:
✅ Load context (project structure, existing patterns)
✅ Load session (previous similar work)
        ↓
🔴 RULES/STANDARDS SYSTEM (THIS POLICY):
✅ Load Java project structure rules
✅ Load Spring Boot patterns
✅ Load config server rules
✅ Load secret management rules
✅ Load response format standards
✅ Load validation patterns
✅ Load all coding standards
        ↓
Rules Loaded & Ready!
        ↓
EXECUTION SYSTEM:
✅ Generate code following loaded rules
✅ Use ApiResponseDto wrapper
✅ Put configs in Config Server
✅ Store secrets in Secret Manager
✅ Follow package structure
✅ Extend Helper classes
✅ Use constants (never hardcode)
        ↓
Result: Code generated with 100% standards compliance! ✅
```

---

## 📊 STANDARDS LOADER (Script)

**File:** `~/.claude/memory/standards-loader.py`

```python
#!/usr/bin/env python3
"""
Coding Standards Loader
Loads all coding standards before execution
"""

import json
from pathlib import Path


class StandardsLoader:
    def __init__(self):
        self.memory_dir = Path.home() / ".claude" / "memory"
        self.docs_dir = self.memory_dir / "docs"

        self.standards = {}

    def load_all_standards(self):
        """Load all coding standards"""

        print("🔧 Loading Coding Standards...")

        # 1. Java Project Structure
        self.standards['java_structure'] = self.load_java_structure()

        # 2. Config Server Rules
        self.standards['config_server'] = self.load_config_server_rules()

        # 3. Secret Management
        self.standards['secret_management'] = self.load_secret_management()

        # 4. Response Format
        self.standards['response_format'] = self.load_response_format()

        # 5. API Design
        self.standards['api_design'] = self.load_api_design()

        # 6. Database Standards
        self.standards['database'] = self.load_database_standards()

        # 7. Error Handling
        self.standards['error_handling'] = self.load_error_handling()

        print("✅ All standards loaded!")

        return self.standards

    def load_java_structure(self):
        """Load Java project structure rules"""
        return {
            'base_package': 'com.techdeveloper.{project}.{service}',
            'packages': {
                'controller': 'public',
                'dto': 'public',
                'form': 'public',
                'constants': 'public',
                'services': 'public (interfaces)',
                'services.impl': 'package-private',
                'services.helper': 'package-private',
                'entity': 'package-private',
                'repository': 'package-private',
                'client': 'package-private',
                'config': 'public',
                'exception': 'public',
                'utils': 'public'
            },
            'rules': [
                'Service implementations are package-private',
                'Service implementations extend Helper',
                'All responses use ApiResponseDto<T>',
                'Form classes extend ValidationMessageConstants',
                'NO hardcoded messages',
                '@Transactional on write operations'
            ]
        }

    def load_config_server_rules(self):
        """Load Config Server rules"""
        return {
            'location': 'config-server/configurations/',
            'microservice_yml': {
                'allowed': [
                    'spring.application.name',
                    'spring.config.import',
                    'secret-manager.client'
                ],
                'forbidden': [
                    'server.port',
                    'spring.datasource.*',
                    'spring.redis.*',
                    'feign.client.*'
                ]
            },
            'rules': [
                'ONLY name + config import in microservice',
                'ALL other configs in Config Server',
                'NEVER add database config in microservice',
                'NEVER hardcode any config'
            ]
        }

    def load_secret_management(self):
        """Load Secret Management rules"""
        return {
            'services': {
                'secret_manager': 1002,
                'project_management': 8109
            },
            'secrets': [
                'database passwords',
                'API keys',
                'JWT secrets',
                'email passwords'
            ],
            'usage': '${SECRET:key-name}',
            'rules': [
                'ALL secrets in Secret Manager',
                'Config server uses ${SECRET:} syntax',
                'NEVER hardcode secrets',
                'NEVER commit .env files'
            ]
        }

    def load_response_format(self):
        """Load response format standards"""
        return {
            'wrapper': 'ApiResponseDto<T>',
            'fields': {
                'status': 'SUCCESS or ERROR',
                'message': 'Human-readable message',
                'data': 'Actual data or null',
                'timestamp': 'ISO 8601'
            },
            'rules': [
                'ALL responses use ApiResponseDto<T>',
                'Message from MessageConstants',
                'NEVER return raw DTOs',
                'NEVER hardcode messages'
            ]
        }

    # ... more loaders
```

---

## 🎯 INTEGRATION IN FLOW

**Updated CLAUDE.md Execution Flow:**

```
Step 0: Context + Session (SYNC SYSTEM)
        ↓
🆕 Step 0.5: Load Coding Standards (RULES/STANDARDS SYSTEM)
   → python standards-loader.py --load-all
   → Standards loaded and available for execution
        ↓
Step 1-10: Execution (EXECUTION SYSTEM)
   → All code follows loaded standards
```

---

## ✅ BENEFITS

| Benefit | Description |
|---------|-------------|
| **100% Consistency** | All services follow same patterns |
| **Zero Violations** | Standards enforced before code generation |
| **No Re-work** | Code generated correctly first time |
| **Easy Maintenance** | Consistent code = easy to maintain |
| **Scalability** | Add new services with same standards |
| **Team Alignment** | Everyone follows same rules |

---

## 📝 EXAMPLE: Before vs After

### **WITHOUT Rules/Standards System:**
```
User: "Create Product API"
Claude: [Generates code with]
  ❌ Hardcoded messages
  ❌ Configs in microservice application.yml
  ❌ Public service implementation
  ❌ No ApiResponseDto wrapper
  ❌ Different from other services
```

### **WITH Rules/Standards System:**
```
User: "Create Product API"
        ↓
Load Standards First
        ↓
Claude: [Generates code with]
  ✅ Messages from constants
  ✅ Configs in Config Server
  ✅ Package-private service implementation
  ✅ ApiResponseDto wrapper
  ✅ Exactly like other services (consistent!)
```

---

**VERSION:** 1.0.0
**CREATED:** 2026-02-16
**LOCATION:** `~/.claude/memory/coding-standards-enforcement-policy.md`

**Ye raha middle layer bhai!** 🎯

Standards load honge BEFORE execution - perfect consistency! 🚀
