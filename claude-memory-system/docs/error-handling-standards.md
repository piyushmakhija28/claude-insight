# Error Handling Standards (MANDATORY)

**🚨 CRITICAL: Proper error handling prevents security issues and improves user experience! 🚨**

## Global Exception Handler

**ALWAYS create a global exception handler using `@ControllerAdvice`:**

```java
@ControllerAdvice
@Slf4j
public class GlobalExceptionHandler {

    @ExceptionHandler(ResourceNotFoundException.class)
    public ResponseEntity<ApiResponseDto<Void>> handleResourceNotFound(
            ResourceNotFoundException ex) {
        log.error("Resource not found: {}", ex.getMessage());
        return ResponseEntity
            .status(HttpStatus.NOT_FOUND)
            .body(ApiResponseDto.error(ex.getMessage()));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiResponseDto<Map<String, String>>> handleValidationErrors(
            MethodArgumentNotValidException ex) {
        Map<String, String> errors = new HashMap<>();
        ex.getBindingResult().getFieldErrors().forEach(error ->
            errors.put(error.getField(), error.getDefaultMessage())
        );

        log.error("Validation errors: {}", errors);
        return ResponseEntity
            .status(HttpStatus.BAD_REQUEST)
            .body(ApiResponseDto.error("Validation failed", errors));
    }

    @ExceptionHandler(DuplicateResourceException.class)
    public ResponseEntity<ApiResponseDto<Void>> handleDuplicateResource(
            DuplicateResourceException ex) {
        log.error("Duplicate resource: {}", ex.getMessage());
        return ResponseEntity
            .status(HttpStatus.CONFLICT)
            .body(ApiResponseDto.error(ex.getMessage()));
    }

    @ExceptionHandler(UnauthorizedException.class)
    public ResponseEntity<ApiResponseDto<Void>> handleUnauthorized(
            UnauthorizedException ex) {
        log.error("Unauthorized access: {}", ex.getMessage());
        return ResponseEntity
            .status(HttpStatus.UNAUTHORIZED)
            .body(ApiResponseDto.error(ex.getMessage()));
    }

    @ExceptionHandler(ForbiddenException.class)
    public ResponseEntity<ApiResponseDto<Void>> handleForbidden(
            ForbiddenException ex) {
        log.error("Forbidden access: {}", ex.getMessage());
        return ResponseEntity
            .status(HttpStatus.FORBIDDEN)
            .body(ApiResponseDto.error(ex.getMessage()));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiResponseDto<Void>> handleGlobalException(
            Exception ex) {
        log.error("Unexpected error occurred", ex);
        return ResponseEntity
            .status(HttpStatus.INTERNAL_SERVER_ERROR)
            .body(ApiResponseDto.error("An unexpected error occurred"));
    }
}
```

## Custom Exception Hierarchy

**Create specific exceptions for different error types:**

### Base Exception
```java
public abstract class BaseException extends RuntimeException {
    private final String errorCode;

    public BaseException(String message, String errorCode) {
        super(message);
        this.errorCode = errorCode;
    }

    public String getErrorCode() {
        return errorCode;
    }
}
```

### Resource Not Found Exception
```java
public class ResourceNotFoundException extends BaseException {
    public ResourceNotFoundException(String resource, String identifier) {
        super(
            String.format("%s not found with identifier: %s", resource, identifier),
            "RESOURCE_NOT_FOUND"
        );
    }
}

// Usage:
throw new ResourceNotFoundException("User", userId.toString());
```

### Duplicate Resource Exception
```java
public class DuplicateResourceException extends BaseException {
    public DuplicateResourceException(String resource, String field) {
        super(
            String.format("%s already exists with this %s", resource, field),
            "RESOURCE_ALREADY_EXISTS"
        );
    }
}

// Usage:
throw new DuplicateResourceException("User", "email");
```

### Validation Exception
```java
public class ValidationException extends BaseException {
    private final Map<String, String> errors;

    public ValidationException(String message, Map<String, String> errors) {
        super(message, "VALIDATION_ERROR");
        this.errors = errors;
    }

    public Map<String, String> getErrors() {
        return errors;
    }
}
```

### Unauthorized Exception
```java
public class UnauthorizedException extends BaseException {
    public UnauthorizedException(String message) {
        super(message, "UNAUTHORIZED");
    }
}

// Usage:
throw new UnauthorizedException("Invalid credentials");
```

### Forbidden Exception
```java
public class ForbiddenException extends BaseException {
    public ForbiddenException(String message) {
        super(message, "FORBIDDEN");
    }
}

// Usage:
throw new ForbiddenException("You don't have permission to access this resource");
```

### Business Logic Exception
```java
public class BusinessException extends BaseException {
    public BusinessException(String message, String errorCode) {
        super(message, errorCode);
    }
}

// Usage:
throw new BusinessException("Insufficient balance", "INSUFFICIENT_BALANCE");
```

## Exception Mapping to HTTP Status Codes

| Exception | HTTP Status | Error Code |
|-----------|-------------|------------|
| ResourceNotFoundException | 404 | RESOURCE_NOT_FOUND |
| DuplicateResourceException | 409 | RESOURCE_ALREADY_EXISTS |
| ValidationException | 400 | VALIDATION_ERROR |
| UnauthorizedException | 401 | UNAUTHORIZED |
| ForbiddenException | 403 | FORBIDDEN |
| BusinessException | 400 | Custom |
| IllegalArgumentException | 400 | BAD_REQUEST |
| Exception (catch-all) | 500 | INTERNAL_ERROR |

## Error Response Format

### Single Error
```json
{
  "status": false,
  "message": "User not found with identifier: 123",
  "errorCode": "RESOURCE_NOT_FOUND",
  "timestamp": "2026-02-09T10:30:00Z"
}
```

### Validation Errors
```json
{
  "status": false,
  "message": "Validation failed",
  "errorCode": "VALIDATION_ERROR",
  "errors": {
    "email": "Email is required",
    "password": "Password must be at least 8 characters"
  },
  "timestamp": "2026-02-09T10:30:00Z"
}
```

### Business Logic Error
```json
{
  "status": false,
  "message": "Insufficient balance for this transaction",
  "errorCode": "INSUFFICIENT_BALANCE",
  "timestamp": "2026-02-09T10:30:00Z"
}
```

## Service Layer Error Handling

### ✅ CORRECT - Throw Exceptions
```java
@Service
@Slf4j
public class UserServiceImpl implements UserService {

    @Autowired
    private UserRepository userRepository;

    @Override
    public UserDto getUserById(Long id) {
        User user = userRepository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("User", id.toString()));

        return UserMapper.toDto(user);
    }

    @Override
    public UserDto createUser(RegisterUserForm form) {
        // Check duplicate email
        if (userRepository.existsByEmail(form.getEmail())) {
            throw new DuplicateResourceException("User", "email");
        }

        User user = new User();
        user.setEmail(form.getEmail());
        user.setPassword(passwordEncoder.encode(form.getPassword()));

        User saved = userRepository.save(user);
        log.info("User created successfully: {}", saved.getId());

        return UserMapper.toDto(saved);
    }

    @Override
    @Transactional
    public void deleteUser(Long id) {
        User user = userRepository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("User", id.toString()));

        userRepository.delete(user);
        log.info("User deleted successfully: {}", id);
    }
}
```

### ❌ WRONG - Returning null or empty
```java
// DON'T DO THIS!
@Override
public UserDto getUserById(Long id) {
    User user = userRepository.findById(id).orElse(null);
    if (user == null) {
        return null; // ❌ Wrong! Throw exception instead
    }
    return UserMapper.toDto(user);
}
```

## Controller Error Handling

**Controllers should NOT catch exceptions - let GlobalExceptionHandler handle them:**

### ✅ CORRECT
```java
@RestController
@RequestMapping("/api/v1/users")
public class UserController {

    @Autowired
    private UserService userService;

    @GetMapping("/{id}")
    public ResponseEntity<ApiResponseDto<UserDto>> getUser(@PathVariable Long id) {
        UserDto user = userService.getUserById(id);
        // No try-catch! Exception will be caught by GlobalExceptionHandler
        return ResponseEntity.ok(
            ApiResponseDto.success("User retrieved successfully", user)
        );
    }
}
```

### ❌ WRONG
```java
// DON'T DO THIS!
@GetMapping("/{id}")
public ResponseEntity<ApiResponseDto<UserDto>> getUser(@PathVariable Long id) {
    try {
        UserDto user = userService.getUserById(id);
        return ResponseEntity.ok(ApiResponseDto.success("User retrieved", user));
    } catch (Exception e) {
        // ❌ Wrong! Let GlobalExceptionHandler handle this
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
            .body(ApiResponseDto.error("Error occurred"));
    }
}
```

## Validation Error Handling

### Form Validation
```java
public class RegisterUserForm extends ValidationMessageConstants {

    @NotBlank(message = EMAIL_REQUIRED)
    @Email(message = EMAIL_INVALID)
    private String email;

    @NotBlank(message = PASSWORD_REQUIRED)
    @Size(min = 8, message = PASSWORD_MIN_LENGTH)
    private String password;

    @NotBlank(message = NAME_REQUIRED)
    @Size(min = 2, max = 50, message = NAME_LENGTH)
    private String name;
}
```

### Controller Validation
```java
@PostMapping
public ResponseEntity<ApiResponseDto<UserDto>> createUser(
        @Valid @RequestBody RegisterUserForm form) { // @Valid triggers validation
    UserDto user = userService.createUser(form);
    return ResponseEntity
        .status(HttpStatus.CREATED)
        .body(ApiResponseDto.success("User created successfully", user));
}
```

## Logging Best Practices

### ✅ DO:
```java
// Log with appropriate level
log.info("User created successfully: {}", userId);
log.warn("Failed login attempt for user: {}", email);
log.error("Failed to process payment", exception);

// Use parameterized logging
log.info("User {} updated by {}", userId, currentUserId);

// Log exceptions with stack trace
log.error("Error processing request", exception);
```

### ❌ DON'T:
```java
// Don't log sensitive data
log.info("User password: {}", password); // ❌ NEVER!
log.info("Credit card: {}", cardNumber); // ❌ NEVER!

// Don't use string concatenation
log.info("User " + userId + " created"); // ❌ Inefficient

// Don't log without context
log.error("Error occurred"); // ❌ Too vague
```

## Error Messages

### User-Facing Messages
```java
// ✅ Clear and actionable
"Email already exists. Please use a different email or login."
"User not found. Please check the user ID and try again."
"Invalid credentials. Please check your email and password."

// ❌ Technical or vague
"Constraint violation on user_email_key"
"NullPointerException at line 42"
"Error 500"
```

### Constants for Messages
```java
public class ErrorMessages {
    // Resource Not Found
    public static final String USER_NOT_FOUND = "User not found with identifier: %s";
    public static final String ORDER_NOT_FOUND = "Order not found with identifier: %s";

    // Duplicate Resource
    public static final String EMAIL_EXISTS = "Email already exists";
    public static final String USERNAME_EXISTS = "Username already exists";

    // Validation
    public static final String INVALID_EMAIL = "Invalid email format";
    public static final String INVALID_PASSWORD = "Password must be at least 8 characters";

    // Authorization
    public static final String UNAUTHORIZED = "Authentication required";
    public static final String FORBIDDEN = "You don't have permission to access this resource";

    // Business Logic
    public static final String INSUFFICIENT_BALANCE = "Insufficient balance for this transaction";
}
```

## Best Practices Summary

### ✅ DO:
1. Always use `@ControllerAdvice` for global exception handling
2. Create specific exception classes for different error types
3. Map exceptions to appropriate HTTP status codes
4. Return consistent error response format (`ApiResponseDto`)
5. Log exceptions with proper context
6. Use meaningful error messages
7. Never expose stack traces to clients in production
8. Validate inputs using `@Valid` annotations
9. Throw exceptions in service layer, catch in global handler
10. Include error codes for client-side handling

### ❌ DON'T:
1. Catch exceptions in controllers (let global handler do it)
2. Return null or empty objects (throw exceptions instead)
3. Log sensitive data (passwords, tokens, credit cards)
4. Return technical error messages to users
5. Use generic Exception catches in business logic
6. Ignore exceptions or swallow them silently
7. Hardcode error messages (use constants)
8. Return different response formats for errors
9. Expose internal system details in error messages
10. Forget to log errors for debugging

---

**Referenced in:** `~/.claude/CLAUDE.md`
**Version:** 1.0.0
**Last Updated:** 2026-02-09
