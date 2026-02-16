# Security Best Practices (MANDATORY)

**🚨 CRITICAL: Security is non-negotiable! Follow these practices ALWAYS! 🚨**

## Secret Management

### ❌ NEVER DO:
```java
// ❌ NEVER hardcode secrets!
String password = "admin123";
String apiKey = "sk_live_abc123xyz";
String dbUrl = "mongodb://admin:password@localhost:27017";
```

### ✅ ALWAYS DO:
```java
// ✅ Use Secret Manager
@Value("${db.password}")  // Fetched from Secret Manager
private String dbPassword;

@Value("${api.key}")
private String apiKey;
```

### Secret Manager Configuration
```yaml
# microservice application.yml (ONLY THIS!)
secret-manager:
  client:
    enabled: true
    project-name: "m2-surgricals"
    base-url: "http://localhost:8085/api/v1/secrets"
```

**Secrets are auto-injected at startup:**
```java
// Secrets available as ${SECRET_KEY}
spring.datasource.password=${DB_PASSWORD}
jwt.secret=${JWT_SECRET}
email.password=${EMAIL_PASSWORD}
```

## Authentication & Authorization

### JWT Token Security

**✅ CORRECT Implementation:**
```java
@Service
public class JwtService {

    @Value("${jwt.secret}")  // From Secret Manager
    private String secret;

    @Value("${jwt.expiration}")  // From Config Server
    private Long expiration;

    public String generateToken(UserDetails userDetails) {
        Map<String, Object> claims = new HashMap<>();
        return Jwts.builder()
            .setClaims(claims)
            .setSubject(userDetails.getUsername())
            .setIssuedAt(new Date())
            .setExpiration(new Date(System.currentTimeMillis() + expiration))
            .signWith(SignatureAlgorithm.HS256, secret)
            .compact();
    }

    public Boolean validateToken(String token, UserDetails userDetails) {
        try {
            final String username = extractUsername(token);
            return username.equals(userDetails.getUsername())
                && !isTokenExpired(token);
        } catch (Exception e) {
            log.error("Invalid JWT token: {}", e.getMessage());
            return false;
        }
    }
}
```

### Password Security

**✅ ALWAYS hash passwords:**
```java
@Configuration
public class SecurityConfig {

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder(12); // Strong hashing
    }
}

@Service
public class UserService {

    @Autowired
    private PasswordEncoder passwordEncoder;

    public void createUser(RegisterUserForm form) {
        User user = new User();
        user.setPassword(passwordEncoder.encode(form.getPassword())); // ✅ Hash it!
        userRepository.save(user);
    }

    public boolean verifyPassword(String rawPassword, String hashedPassword) {
        return passwordEncoder.matches(rawPassword, hashedPassword);
    }
}
```

**❌ NEVER store plain text passwords:**
```java
// ❌ NEVER DO THIS!
user.setPassword(form.getPassword()); // Plain text storage = security disaster!
```

### Role-Based Access Control (RBAC)

```java
@PreAuthorize("hasRole('ADMIN')")
@DeleteMapping("/{id}")
public ResponseEntity<ApiResponseDto<Void>> deleteUser(@PathVariable Long id) {
    userService.deleteUser(id);
    return ResponseEntity.ok(ApiResponseDto.success("User deleted", null));
}

@PreAuthorize("hasAnyRole('ADMIN', 'MANAGER')")
@GetMapping("/reports")
public ResponseEntity<ApiResponseDto<List<ReportDto>>> getReports() {
    // Only ADMIN or MANAGER can access
}

@PreAuthorize("hasRole('USER') or #userId == authentication.principal.id")
@GetMapping("/{userId}/profile")
public ResponseEntity<ApiResponseDto<UserDto>> getProfile(@PathVariable Long userId) {
    // User can access own profile OR admin can access any
}
```

## Input Validation

### ✅ ALWAYS validate user inputs:
```java
public class RegisterUserForm extends ValidationMessageConstants {

    @NotBlank(message = EMAIL_REQUIRED)
    @Email(message = EMAIL_INVALID)
    @Size(max = 100, message = EMAIL_MAX_LENGTH)
    private String email;

    @NotBlank(message = PASSWORD_REQUIRED)
    @Pattern(
        regexp = "^(?=.*[0-9])(?=.*[a-z])(?=.*[A-Z])(?=.*[@#$%^&+=])(?=\\S+$).{8,}$",
        message = PASSWORD_PATTERN
    )
    private String password;

    @NotBlank(message = NAME_REQUIRED)
    @Size(min = 2, max = 50, message = NAME_LENGTH)
    @Pattern(regexp = "^[a-zA-Z\\s]+$", message = NAME_PATTERN)
    private String name;

    @Pattern(regexp = "^\\+?[1-9]\\d{9,14}$", message = PHONE_INVALID)
    private String phone;
}
```

### SQL Injection Prevention

**✅ ALWAYS use parameterized queries:**
```java
// ✅ JPA Repository (safe by default)
@Repository
public interface UserRepository extends JpaRepository<User, Long> {
    Optional<User> findByEmail(String email);
}

// ✅ Custom query with parameters
@Query("SELECT u FROM User u WHERE u.email = :email AND u.status = :status")
Optional<User> findByEmailAndStatus(@Param("email") String email,
                                    @Param("status") String status);

// ✅ Native query with parameters
@Query(value = "SELECT * FROM users WHERE email = :email", nativeQuery = true)
Optional<User> findByEmailNative(@Param("email") String email);
```

**❌ NEVER concatenate SQL strings:**
```java
// ❌ NEVER DO THIS! SQL Injection vulnerability!
String query = "SELECT * FROM users WHERE email = '" + email + "'";
```

### XSS (Cross-Site Scripting) Prevention

**✅ Sanitize HTML inputs:**
```java
import org.jsoup.Jsoup;
import org.jsoup.safety.Safelist;

public class SecurityUtils {

    public static String sanitizeHtml(String input) {
        if (input == null) return null;
        // Remove all HTML tags
        return Jsoup.clean(input, Safelist.none());
    }

    public static String sanitizeHtmlBasic(String input) {
        if (input == null) return null;
        // Allow basic formatting only
        return Jsoup.clean(input, Safelist.basic());
    }
}

// Usage in service
public UserDto createUser(RegisterUserForm form) {
    User user = new User();
    user.setName(SecurityUtils.sanitizeHtml(form.getName()));
    // ... save user
}
```

### Path Traversal Prevention

**✅ Validate file paths:**
```java
public class FileService {

    private static final String UPLOAD_DIR = "/var/app/uploads/";

    public void saveFile(String filename, MultipartFile file) {
        // ✅ Validate filename
        if (filename.contains("..") || filename.contains("/") || filename.contains("\\")) {
            throw new ValidationException("Invalid filename");
        }

        Path targetPath = Paths.get(UPLOAD_DIR, filename).normalize();

        // ✅ Ensure path is within allowed directory
        if (!targetPath.startsWith(UPLOAD_DIR)) {
            throw new ValidationException("Invalid file path");
        }

        // Save file
        Files.copy(file.getInputStream(), targetPath);
    }
}
```

**❌ NEVER trust user-provided paths:**
```java
// ❌ NEVER DO THIS! Path traversal vulnerability!
String filename = request.getParameter("file");
File file = new File("/var/app/uploads/" + filename); // Can access "../../../etc/passwd"
```

## Logging Security

### ✅ DO:
```java
// Log security events
log.info("User logged in successfully: {}", userId);
log.warn("Failed login attempt for email: {}", email);
log.error("Unauthorized access attempt to resource: {}", resourceId);

// Log without sensitive data
log.info("User {} updated profile", userId);
log.info("Payment processed for order: {}", orderId);
```

### ❌ DON'T:
```java
// ❌ NEVER log sensitive data!
log.info("User password: {}", password);
log.info("Credit card: {}", cardNumber);
log.info("JWT token: {}", token);
log.info("API key: {}", apiKey);
log.info("Session ID: {}", sessionId);
log.info("OTP code: {}", otp);
```

## CORS Configuration

**✅ Configure CORS properly:**
```java
@Configuration
public class CorsConfig {

    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurer() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/api/**")
                    .allowedOrigins("https://yourdomain.com") // ✅ Specific domain
                    .allowedMethods("GET", "POST", "PUT", "DELETE")
                    .allowedHeaders("*")
                    .allowCredentials(true)
                    .maxAge(3600);
            }
        };
    }
}
```

**❌ NEVER allow all origins in production:**
```java
// ❌ NEVER DO THIS in production!
registry.addMapping("/**")
    .allowedOrigins("*") // Security risk!
    .allowedMethods("*");
```

## Rate Limiting

**✅ Implement rate limiting:**
```java
@Component
public class RateLimitInterceptor implements HandlerInterceptor {

    private final Map<String, Integer> requestCounts = new ConcurrentHashMap<>();
    private static final int MAX_REQUESTS = 100;
    private static final long TIME_WINDOW = 60000; // 1 minute

    @Override
    public boolean preHandle(HttpServletRequest request,
                            HttpServletResponse response,
                            Object handler) {
        String clientId = getClientId(request);
        Integer count = requestCounts.getOrDefault(clientId, 0);

        if (count >= MAX_REQUESTS) {
            response.setStatus(HttpStatus.TOO_MANY_REQUESTS.value());
            return false;
        }

        requestCounts.put(clientId, count + 1);
        return true;
    }

    private String getClientId(HttpServletRequest request) {
        // Use IP or user ID
        return request.getRemoteAddr();
    }
}
```

## Session Security

**✅ Secure session configuration:**
```yaml
# application.yml (in Config Server)
server:
  servlet:
    session:
      timeout: 30m
      cookie:
        http-only: true  # ✅ Prevent JavaScript access
        secure: true     # ✅ HTTPS only
        same-site: strict # ✅ CSRF protection
```

## API Security Headers

**✅ Add security headers:**
```java
@Configuration
public class SecurityHeadersConfig {

    @Bean
    public FilterRegistrationBean<SecurityHeadersFilter> securityHeadersFilter() {
        FilterRegistrationBean<SecurityHeadersFilter> registrationBean =
            new FilterRegistrationBean<>();
        registrationBean.setFilter(new SecurityHeadersFilter());
        registrationBean.addUrlPatterns("/*");
        return registrationBean;
    }
}

public class SecurityHeadersFilter implements Filter {

    @Override
    public void doFilter(ServletRequest request, ServletResponse response,
                        FilterChain chain) {
        HttpServletResponse httpResponse = (HttpServletResponse) response;

        // ✅ Security headers
        httpResponse.setHeader("X-Content-Type-Options", "nosniff");
        httpResponse.setHeader("X-Frame-Options", "DENY");
        httpResponse.setHeader("X-XSS-Protection", "1; mode=block");
        httpResponse.setHeader("Strict-Transport-Security",
            "max-age=31536000; includeSubDomains");
        httpResponse.setHeader("Content-Security-Policy",
            "default-src 'self'");

        chain.doFilter(request, response);
    }
}
```

## File Upload Security

**✅ Secure file upload:**
```java
@Service
public class FileUploadService {

    private static final List<String> ALLOWED_EXTENSIONS =
        Arrays.asList("jpg", "jpeg", "png", "pdf", "doc", "docx");
    private static final long MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

    public String uploadFile(MultipartFile file) {
        // ✅ Validate file size
        if (file.getSize() > MAX_FILE_SIZE) {
            throw new ValidationException("File size exceeds limit");
        }

        // ✅ Validate file extension
        String extension = getFileExtension(file.getOriginalFilename());
        if (!ALLOWED_EXTENSIONS.contains(extension.toLowerCase())) {
            throw new ValidationException("File type not allowed");
        }

        // ✅ Generate random filename
        String filename = UUID.randomUUID().toString() + "." + extension;

        // ✅ Scan for malware (if needed)
        // scanForMalware(file);

        // Save file
        return saveFile(filename, file);
    }

    private String getFileExtension(String filename) {
        return filename.substring(filename.lastIndexOf(".") + 1);
    }
}
```

## Dependency Security

**✅ Keep dependencies updated:**
```xml
<!-- pom.xml -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-security</artifactId>
    <!-- Always use latest stable version -->
</dependency>
```

**Check for vulnerabilities:**
```bash
# Run security audit
mvn dependency-check:check

# Update dependencies
mvn versions:use-latest-releases
```

## Environment-Specific Security

### Development
```yaml
# application-dev.yml
spring:
  security:
    debug: true  # OK for dev
logging:
  level:
    root: DEBUG  # OK for dev
```

### Production
```yaml
# application-prod.yml
spring:
  security:
    debug: false  # ✅ MUST be false
logging:
  level:
    root: WARN    # ✅ Minimize logging
server:
  error:
    include-stacktrace: never  # ✅ Hide stack traces
    include-message: never     # ✅ Hide error details
```

## Security Checklist

### ✅ ALWAYS DO:
1. Store secrets in Secret Manager (NEVER hardcode)
2. Hash passwords with BCrypt (strength 12+)
3. Validate ALL user inputs
4. Use parameterized queries (prevent SQL injection)
5. Sanitize HTML inputs (prevent XSS)
6. Validate file uploads (size, type, content)
7. Implement rate limiting
8. Use HTTPS in production
9. Add security headers
10. Configure CORS properly
11. Enable CSRF protection
12. Use secure session cookies
13. Implement proper authentication & authorization
14. Log security events (without sensitive data)
15. Keep dependencies updated
16. Use environment-specific configurations

### ❌ NEVER DO:
1. Hardcode secrets, passwords, or API keys
2. Store passwords in plain text
3. Trust user input without validation
4. Concatenate SQL strings (SQL injection risk)
5. Allow unrestricted file uploads
6. Log sensitive data (passwords, tokens, cards)
7. Use `allowedOrigins("*")` in production
8. Expose stack traces to clients
9. Run with debug mode in production
10. Ignore security warnings
11. Use default passwords
12. Disable security features
13. Trust client-side validation only
14. Return detailed error messages to users
15. Use outdated dependencies with known vulnerabilities

---

**Referenced in:** `~/.claude/CLAUDE.md`
**Version:** 1.0.0
**Last Updated:** 2026-02-09
