# Logging Standards (MANDATORY)

**🚨 CRITICAL: Proper logging is essential for debugging, monitoring, and security! 🚨**

## Logging Framework

**Use SLF4J with Logback (Spring Boot default):**

```java
import lombok.extern.slf4j.Slf4j;

@Service
@Slf4j  // Lombok annotation - generates logger automatically
public class UserService {

    public void createUser(RegisterUserForm form) {
        log.info("Creating user with email: {}", form.getEmail());
        // ... business logic
        log.info("User created successfully with ID: {}", user.getId());
    }
}
```

## Log Levels

| Level | When to Use | Examples |
|-------|-------------|----------|
| **ERROR** | System errors, exceptions that need immediate attention | Database connection failed, Payment processing failed |
| **WARN** | Potential issues, deprecated features, recoverable errors | Failed login attempts, API rate limit approaching, Cache miss |
| **INFO** | Important business events, state changes | User registered, Order placed, Payment successful |
| **DEBUG** | Detailed flow for debugging (dev/staging only) | Method entry/exit, Variable values, Query parameters |
| **TRACE** | Very detailed (rarely used, dev only) | Loop iterations, Detailed object states |

## Logging Best Practices

### ✅ DO: Use Parameterized Logging
```java
// ✅ CORRECT - Parameterized (efficient)
log.info("User {} logged in from IP {}", userId, ipAddress);
log.error("Failed to process order {} for user {}", orderId, userId);

// ✅ Multiple parameters
log.info("Payment of {} processed for order {} by user {}",
    amount, orderId, userId);
```

### ❌ DON'T: Use String Concatenation
```java
// ❌ WRONG - Inefficient (string built even if level disabled)
log.info("User " + userId + " logged in from " + ipAddress);
log.debug("Processing order: " + order.toString());
```

### ✅ DO: Log Business Events
```java
@Service
@Slf4j
public class OrderService {

    public OrderDto createOrder(CreateOrderForm form) {
        log.info("Creating order for user: {}", form.getUserId());

        Order order = buildOrder(form);
        Order saved = orderRepository.save(order);

        log.info("Order created successfully - OrderID: {}, Total: {}",
            saved.getId(), saved.getTotal());

        return OrderMapper.toDto(saved);
    }

    public void cancelOrder(Long orderId) {
        log.warn("Order cancellation requested - OrderID: {}", orderId);

        Order order = getOrderById(orderId);
        order.setStatus(OrderStatus.CANCELLED);
        orderRepository.save(order);

        log.info("Order cancelled successfully - OrderID: {}", orderId);
    }
}
```

### ✅ DO: Log Exceptions with Context
```java
@Service
@Slf4j
public class PaymentService {

    public void processPayment(Long orderId, PaymentForm form) {
        try {
            log.info("Processing payment for order: {}", orderId);

            PaymentResponse response = paymentGateway.charge(form);

            log.info("Payment processed successfully - OrderID: {}, TransactionID: {}",
                orderId, response.getTransactionId());

        } catch (PaymentException e) {
            log.error("Payment failed for order: {} - Reason: {}",
                orderId, e.getMessage(), e);
            throw e;
        }
    }
}
```

### ❌ DON'T: Log Sensitive Data
```java
// ❌ NEVER LOG THESE!
log.info("User password: {}", password);
log.info("Credit card: {}", cardNumber);
log.info("CVV: {}", cvv);
log.info("JWT token: {}", token);
log.info("API key: {}", apiKey);
log.info("Session ID: {}", sessionId);
log.info("OTP: {}", otp);
log.info("Secret key: {}", secretKey);

// ✅ Instead, log safely
log.info("User authenticated successfully: {}", userId);
log.info("Payment method ending with: {}", last4Digits);
log.info("Token generated for user: {}", userId);
```

### ✅ DO: Mask Sensitive Data
```java
public class LoggingUtils {

    public static String maskEmail(String email) {
        if (email == null || !email.contains("@")) return "***";
        String[] parts = email.split("@");
        return parts[0].charAt(0) + "***@" + parts[1];
    }

    public static String maskCardNumber(String cardNumber) {
        if (cardNumber == null || cardNumber.length() < 4) return "****";
        return "****-****-****-" + cardNumber.substring(cardNumber.length() - 4);
    }

    public static String maskPhone(String phone) {
        if (phone == null || phone.length() < 4) return "****";
        return "******" + phone.substring(phone.length() - 4);
    }
}

// Usage
log.info("User registered - Email: {}", LoggingUtils.maskEmail(email));
log.info("Payment method added - Card: {}",
    LoggingUtils.maskCardNumber(cardNumber));
```

## Controller Logging

### ✅ CORRECT Pattern
```java
@RestController
@RequestMapping("/api/v1/users")
@Slf4j
public class UserController {

    @Autowired
    private UserService userService;

    @PostMapping
    public ResponseEntity<ApiResponseDto<UserDto>> createUser(
            @Valid @RequestBody RegisterUserForm form) {

        log.info("POST /api/v1/users - Creating user with email: {}",
            LoggingUtils.maskEmail(form.getEmail()));

        UserDto user = userService.createUser(form);

        log.info("User created successfully - UserID: {}", user.getId());

        return ResponseEntity
            .status(HttpStatus.CREATED)
            .body(ApiResponseDto.success("User created successfully", user));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ApiResponseDto<UserDto>> getUser(@PathVariable Long id) {
        log.debug("GET /api/v1/users/{} - Fetching user", id);

        UserDto user = userService.getUserById(id);

        return ResponseEntity.ok(
            ApiResponseDto.success("User retrieved successfully", user)
        );
    }
}
```

## Service Layer Logging

### ✅ CORRECT Pattern
```java
@Service
@Slf4j
public class UserServiceImpl implements UserService {

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private PasswordEncoder passwordEncoder;

    @Override
    @Transactional
    public UserDto createUser(RegisterUserForm form) {
        log.info("Creating user - Email: {}", LoggingUtils.maskEmail(form.getEmail()));

        // Validation
        if (userRepository.existsByEmail(form.getEmail())) {
            log.warn("User creation failed - Email already exists: {}",
                LoggingUtils.maskEmail(form.getEmail()));
            throw new DuplicateResourceException("User", "email");
        }

        // Create user
        User user = new User();
        user.setEmail(form.getEmail());
        user.setPassword(passwordEncoder.encode(form.getPassword()));
        user.setName(form.getName());

        User saved = userRepository.save(user);
        log.info("User created successfully - UserID: {}, Email: {}",
            saved.getId(), LoggingUtils.maskEmail(saved.getEmail()));

        return UserMapper.toDto(saved);
    }

    @Override
    public UserDto getUserById(Long id) {
        log.debug("Fetching user by ID: {}", id);

        User user = userRepository.findById(id)
            .orElseThrow(() -> {
                log.error("User not found - UserID: {}", id);
                return new ResourceNotFoundException("User", id.toString());
            });

        log.debug("User found - UserID: {}", id);
        return UserMapper.toDto(user);
    }

    @Override
    @Transactional
    public void deleteUser(Long id) {
        log.warn("Deleting user - UserID: {}", id);

        User user = userRepository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("User", id.toString()));

        userRepository.delete(user);
        log.info("User deleted successfully - UserID: {}", id);
    }
}
```

## Exception Logging

### ✅ CORRECT Pattern
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

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiResponseDto<Void>> handleGlobalException(
            Exception ex) {
        log.error("Unexpected error occurred - Type: {}, Message: {}",
            ex.getClass().getSimpleName(), ex.getMessage(), ex);
        return ResponseEntity
            .status(HttpStatus.INTERNAL_SERVER_ERROR)
            .body(ApiResponseDto.error("An unexpected error occurred"));
    }
}
```

## Performance Logging

### ✅ Log Slow Operations
```java
@Service
@Slf4j
public class ReportService {

    public ReportDto generateReport(Long reportId) {
        long startTime = System.currentTimeMillis();

        log.info("Generating report - ReportID: {}", reportId);

        ReportDto report = buildReport(reportId);

        long duration = System.currentTimeMillis() - startTime;
        log.info("Report generated - ReportID: {}, Duration: {}ms",
            reportId, duration);

        if (duration > 5000) {
            log.warn("Slow report generation - ReportID: {}, Duration: {}ms",
                reportId, duration);
        }

        return report;
    }
}
```

## Configuration

### Logback Configuration (logback-spring.xml)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>

    <!-- Console Appender (Development) -->
    <appender name="CONSOLE" class="ch.qos.logback.core.ConsoleAppender">
        <encoder>
            <pattern>%d{yyyy-MM-dd HH:mm:ss} [%thread] %-5level %logger{36} - %msg%n</pattern>
        </encoder>
    </appender>

    <!-- File Appender (Production) -->
    <appender name="FILE" class="ch.qos.logback.core.rolling.RollingFileAppender">
        <file>logs/application.log</file>
        <rollingPolicy class="ch.qos.logback.core.rolling.TimeBasedRollingPolicy">
            <fileNamePattern>logs/application-%d{yyyy-MM-dd}.log</fileNamePattern>
            <maxHistory>30</maxHistory>
            <totalSizeCap>1GB</totalSizeCap>
        </rollingPolicy>
        <encoder>
            <pattern>%d{yyyy-MM-dd HH:mm:ss} [%thread] %-5level %logger{36} - %msg%n</pattern>
        </encoder>
    </appender>

    <!-- Error File Appender -->
    <appender name="ERROR_FILE" class="ch.qos.logback.core.rolling.RollingFileAppender">
        <file>logs/error.log</file>
        <filter class="ch.qos.logback.classic.filter.LevelFilter">
            <level>ERROR</level>
            <onMatch>ACCEPT</onMatch>
            <onMismatch>DENY</onMismatch>
        </filter>
        <rollingPolicy class="ch.qos.logback.core.rolling.TimeBasedRollingPolicy">
            <fileNamePattern>logs/error-%d{yyyy-MM-dd}.log</fileNamePattern>
            <maxHistory>30</maxHistory>
        </rollingPolicy>
        <encoder>
            <pattern>%d{yyyy-MM-dd HH:mm:ss} [%thread] %-5level %logger{36} - %msg%n</pattern>
        </encoder>
    </appender>

    <!-- Development Profile -->
    <springProfile name="dev">
        <root level="DEBUG">
            <appender-ref ref="CONSOLE"/>
        </root>
    </springProfile>

    <!-- Production Profile -->
    <springProfile name="prod">
        <root level="INFO">
            <appender-ref ref="FILE"/>
            <appender-ref ref="ERROR_FILE"/>
        </root>
    </springProfile>

</configuration>
```

### Application Properties
```yaml
# application-dev.yml (Development)
logging:
  level:
    root: INFO
    com.techdeveloper: DEBUG
    org.springframework.web: DEBUG
    org.hibernate.SQL: DEBUG

# application-prod.yml (Production)
logging:
  level:
    root: WARN
    com.techdeveloper: INFO
    org.springframework.web: WARN
  file:
    name: logs/application.log
    max-size: 10MB
    max-history: 30
```

## What to Log

### ✅ ALWAYS LOG:
1. **Authentication events**: Login, logout, failed attempts
2. **Authorization failures**: Access denied events
3. **Business transactions**: Orders, payments, bookings
4. **State changes**: Status updates, approvals, cancellations
5. **External API calls**: Request/response, failures
6. **System errors**: Exceptions, failures, timeouts
7. **Security events**: Suspicious activities, rate limit hits
8. **Performance issues**: Slow queries, high response times

### ❌ NEVER LOG:
1. Passwords (plain or hashed)
2. Credit card numbers
3. CVV codes
4. JWT tokens
5. API keys/secrets
6. Session IDs
7. OTP codes
8. Private keys
9. Social security numbers
10. Any PII (Personally Identifiable Information) without masking

## Log Format Examples

### Success Events
```java
log.info("User authenticated successfully - UserID: {}", userId);
log.info("Order placed successfully - OrderID: {}, Amount: {}", orderId, amount);
log.info("Email sent successfully - Recipient: {}", maskedEmail);
```

### Warning Events
```java
log.warn("Failed login attempt - Email: {}, IP: {}", maskedEmail, ipAddress);
log.warn("Rate limit approaching - User: {}, Count: {}", userId, requestCount);
log.warn("Cache miss - Key: {}", cacheKey);
```

### Error Events
```java
log.error("Database connection failed - Retrying in 5s", exception);
log.error("Payment processing failed - OrderID: {}, Reason: {}",
    orderId, reason, exception);
log.error("External API call failed - URL: {}, Status: {}",
    apiUrl, statusCode, exception);
```

### Debug Events
```java
log.debug("Method entry - getUserById - UserID: {}", userId);
log.debug("Query executed - SQL: {}, Params: {}", sql, params);
log.debug("Method exit - getUserById - Result: {}", result);
```

## Monitoring & Alerts

### Setup Log Monitoring
```java
// Track critical errors
@Component
@Slf4j
public class ErrorMonitor {

    @EventListener
    public void onApplicationEvent(ErrorEvent event) {
        log.error("CRITICAL: {} - {}", event.getType(), event.getMessage());
        // Send alert to monitoring system (e.g., Sentry, New Relic)
    }
}
```

## Best Practices Summary

### ✅ DO:
1. Use SLF4J with Lombok's `@Slf4j`
2. Use parameterized logging
3. Log at appropriate levels (ERROR, WARN, INFO, DEBUG)
4. Log business events with context
5. Log exceptions with stack traces
6. Mask sensitive data before logging
7. Include request IDs for traceability
8. Use structured logging in production
9. Configure different log levels per environment
10. Set up log rotation and retention

### ❌ DON'T:
1. Use string concatenation in logs
2. Log sensitive data (passwords, tokens, cards)
3. Log at DEBUG level in production
4. Log without context (meaningless messages)
5. Swallow exceptions without logging
6. Log the same event multiple times
7. Use `System.out.println()` for logging
8. Log large objects without truncation
9. Ignore log monitoring and alerts
10. Keep DEBUG logs in production code

---

**Referenced in:** `~/.claude/CLAUDE.md`
**Version:** 1.0.0
**Last Updated:** 2026-02-09
