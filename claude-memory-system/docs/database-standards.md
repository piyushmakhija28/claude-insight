# Database Standards (MANDATORY)

**🚨 CRITICAL: Follow these standards for ALL database interactions! 🚨**

## Entity Design

### Basic Entity Pattern
```java
@Entity
@Table(name = "users")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class User {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "email", nullable = false, unique = true, length = 100)
    private String email;

    @Column(name = "password", nullable = false)
    private String password;

    @Column(name = "name", nullable = false, length = 50)
    private String name;

    @Column(name = "phone", length = 15)
    private String phone;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false)
    private UserStatus status;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        status = UserStatus.ACTIVE;
    }

    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }
}
```

## Naming Conventions

### Table Names
- **Use snake_case**: `user_profiles`, `order_items`
- **Use plural**: `users`, `products`, `orders`

```java
@Entity
@Table(name = "user_profiles")  // ✅ Correct
public class UserProfile { }

@Entity
@Table(name = "UserProfile")    // ❌ Wrong
public class UserProfile { }
```

### Column Names
- **Use snake_case**: `first_name`, `created_at`
- **Be descriptive**: `email_verified_at` not `ev_at`

```java
@Column(name = "first_name")     // ✅ Correct
private String firstName;

@Column(name = "firstName")      // ❌ Wrong
private String firstName;
```

### Foreign Key Names
- **Format**: `{table}_id`

```java
@Column(name = "user_id")        // ✅ Correct
private Long userId;

@Column(name = "userId")         // ❌ Wrong
private Long userId;
```

## Relationships

### One-to-Many
```java
@Entity
@Table(name = "users")
public class User {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @OneToMany(mappedBy = "user", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<Order> orders = new ArrayList<>();

    // Helper methods
    public void addOrder(Order order) {
        orders.add(order);
        order.setUser(this);
    }

    public void removeOrder(Order order) {
        orders.remove(order);
        order.setUser(null);
    }
}

@Entity
@Table(name = "orders")
public class Order {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;
}
```

### Many-to-Many
```java
@Entity
@Table(name = "students")
public class Student {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToMany
    @JoinTable(
        name = "student_courses",
        joinColumns = @JoinColumn(name = "student_id"),
        inverseJoinColumns = @JoinColumn(name = "course_id")
    )
    private Set<Course> courses = new HashSet<>();
}

@Entity
@Table(name = "courses")
public class Course {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToMany(mappedBy = "courses")
    private Set<Student> students = new HashSet<>();
}
```

### One-to-One
```java
@Entity
@Table(name = "users")
public class User {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @OneToOne(mappedBy = "user", cascade = CascadeType.ALL, orphanRemoval = true)
    private UserProfile profile;
}

@Entity
@Table(name = "user_profiles")
public class UserProfile {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false, unique = true)
    private User user;
}
```

## Indexes

### Single Column Index
```java
@Entity
@Table(name = "users", indexes = {
    @Index(name = "idx_email", columnList = "email"),
    @Index(name = "idx_status", columnList = "status")
})
public class User {

    @Column(name = "email", nullable = false, unique = true)
    private String email;

    @Column(name = "status")
    private String status;
}
```

### Composite Index
```java
@Entity
@Table(name = "orders", indexes = {
    @Index(name = "idx_user_status", columnList = "user_id, status"),
    @Index(name = "idx_created_at", columnList = "created_at")
})
public class Order {

    @Column(name = "user_id")
    private Long userId;

    @Column(name = "status")
    private String status;

    @Column(name = "created_at")
    private LocalDateTime createdAt;
}
```

## Repository Pattern

### Basic Repository
```java
@Repository
public interface UserRepository extends JpaRepository<User, Long> {

    // ✅ Query Methods (Spring Data generates query)
    Optional<User> findByEmail(String email);

    List<User> findByStatus(UserStatus status);

    boolean existsByEmail(String email);

    long countByStatus(UserStatus status);

    List<User> findByCreatedAtBetween(LocalDateTime start, LocalDateTime end);

    // ✅ Custom Query
    @Query("SELECT u FROM User u WHERE u.email = :email AND u.status = :status")
    Optional<User> findByEmailAndStatus(@Param("email") String email,
                                       @Param("status") UserStatus status);

    // ✅ Native Query
    @Query(value = "SELECT * FROM users WHERE email LIKE %:keyword%",
           nativeQuery = true)
    List<User> searchByEmail(@Param("keyword") String keyword);

    // ✅ Update Query
    @Modifying
    @Query("UPDATE User u SET u.status = :status WHERE u.id = :id")
    int updateStatus(@Param("id") Long id, @Param("status") UserStatus status);

    // ✅ Delete Query
    @Modifying
    @Query("DELETE FROM User u WHERE u.status = :status")
    int deleteByStatus(@Param("status") UserStatus status);
}
```

### Pagination
```java
@Repository
public interface UserRepository extends JpaRepository<User, Long> {

    Page<User> findByStatus(UserStatus status, Pageable pageable);

    @Query("SELECT u FROM User u WHERE u.name LIKE %:keyword%")
    Page<User> searchByName(@Param("keyword") String keyword, Pageable pageable);
}

// Usage in Service
public Page<UserDto> getUsers(int page, int size, String sortBy) {
    Pageable pageable = PageRequest.of(
        page - 1,  // Page starts from 0
        size,
        Sort.by(sortBy).descending()
    );

    Page<User> users = userRepository.findByStatus(UserStatus.ACTIVE, pageable);
    return users.map(UserMapper::toDto);
}
```

### Specifications (Dynamic Queries)
```java
public class UserSpecifications {

    public static Specification<User> hasEmail(String email) {
        return (root, query, cb) ->
            email == null ? null : cb.equal(root.get("email"), email);
    }

    public static Specification<User> hasStatus(UserStatus status) {
        return (root, query, cb) ->
            status == null ? null : cb.equal(root.get("status"), status);
    }

    public static Specification<User> createdBetween(LocalDateTime start,
                                                     LocalDateTime end) {
        return (root, query, cb) ->
            cb.between(root.get("createdAt"), start, end);
    }
}

// Repository
public interface UserRepository extends JpaRepository<User, Long>,
                                       JpaSpecificationExecutor<User> {
}

// Usage
Specification<User> spec = Specification
    .where(UserSpecifications.hasStatus(UserStatus.ACTIVE))
    .and(UserSpecifications.createdBetween(startDate, endDate));

List<User> users = userRepository.findAll(spec);
```

## Transaction Management

### Service Layer Transactions
```java
@Service
@Slf4j
public class OrderServiceImpl implements OrderService {

    @Autowired
    private OrderRepository orderRepository;

    @Autowired
    private InventoryService inventoryService;

    @Autowired
    private PaymentService paymentService;

    @Override
    @Transactional  // ✅ Use for write operations
    public OrderDto createOrder(CreateOrderForm form) {
        log.info("Creating order for user: {}", form.getUserId());

        // All operations in one transaction
        Order order = buildOrder(form);
        Order saved = orderRepository.save(order);

        inventoryService.reserveItems(order.getItems());
        paymentService.processPayment(order.getId(), form.getPaymentInfo());

        log.info("Order created successfully: {}", saved.getId());
        return OrderMapper.toDto(saved);
    }

    @Override
    @Transactional(readOnly = true)  // ✅ Read-only for performance
    public OrderDto getOrderById(Long id) {
        Order order = orderRepository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("Order", id.toString()));
        return OrderMapper.toDto(order);
    }

    @Override
    @Transactional
    public void cancelOrder(Long orderId) {
        log.warn("Cancelling order: {}", orderId);

        Order order = getOrder(orderId);
        order.setStatus(OrderStatus.CANCELLED);
        orderRepository.save(order);

        inventoryService.releaseItems(order.getItems());
        paymentService.refund(orderId);

        log.info("Order cancelled successfully: {}", orderId);
    }
}
```

### Transaction Propagation
```java
@Service
public class PaymentService {

    // Creates new transaction
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void logPaymentAttempt(Long orderId) {
        // This will commit even if parent transaction fails
    }

    // Uses existing transaction or creates new
    @Transactional(propagation = Propagation.REQUIRED)  // Default
    public void processPayment(Long orderId) {
        // Uses parent transaction if exists
    }

    // Must have existing transaction
    @Transactional(propagation = Propagation.MANDATORY)
    public void validatePayment(Long orderId) {
        // Throws exception if no transaction exists
    }
}
```

## Query Optimization

### N+1 Problem Solution
```java
// ❌ WRONG - N+1 Problem
@Query("SELECT u FROM User u WHERE u.status = :status")
List<User> findByStatus(@Param("status") UserStatus status);
// Then accessing u.getOrders() causes N queries

// ✅ CORRECT - Use JOIN FETCH
@Query("SELECT u FROM User u LEFT JOIN FETCH u.orders WHERE u.status = :status")
List<User> findByStatusWithOrders(@Param("status") UserStatus status);
```

### Batch Operations
```java
@Repository
public interface UserRepository extends JpaRepository<User, Long> {

    // ✅ Batch insert
    @Override
    <S extends User> List<S> saveAll(Iterable<S> entities);
}

// Usage
List<User> users = buildUserList();
userRepository.saveAll(users);  // Batch insert
```

### Projection (DTO Query)
```java
// DTO Interface
public interface UserProjection {
    Long getId();
    String getEmail();
    String getName();
}

// Repository
@Query("SELECT u.id as id, u.email as email, u.name as name FROM User u")
List<UserProjection> findAllProjections();

// Or use class-based projection
@Query("SELECT new com.techdeveloper.dto.UserDto(u.id, u.email, u.name) FROM User u")
List<UserDto> findAllDtos();
```

## Database Migrations

### Flyway Configuration
```yaml
# application.yml (in Config Server)
spring:
  flyway:
    enabled: true
    locations: classpath:db/migration
    baseline-on-migrate: true
    baseline-version: 0
```

### Migration File Naming
```
src/main/resources/db/migration/
├── V1__create_users_table.sql
├── V2__create_orders_table.sql
├── V3__add_phone_to_users.sql
└── V4__create_order_items_table.sql
```

### Migration Example
```sql
-- V1__create_users_table.sql
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    name VARCHAR(50) NOT NULL,
    phone VARCHAR(15),
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    CONSTRAINT check_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_created_at ON users(created_at);

-- V2__create_orders_table.sql
CREATE TABLE orders (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    total DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created_at ON orders(created_at);
```

## Best Practices

### ✅ DO:
1. **Use `@Transactional` for write operations**
2. **Use `@Transactional(readOnly = true)` for read operations**
3. **Always validate foreign keys exist**
4. **Use indexes on frequently queried columns**
5. **Use pagination for large datasets**
6. **Use `FetchType.LAZY` for relationships (default for @ManyToOne)**
7. **Use JOIN FETCH to avoid N+1 problem**
8. **Use database migrations (Flyway/Liquibase)**
9. **Use projections/DTOs for queries that don't need full entities**
10. **Use batch operations for bulk inserts/updates**

### ❌ DON'T:
1. **Don't use `FetchType.EAGER` unless necessary**
2. **Don't load entire tables without pagination**
3. **Don't concatenate SQL strings (use parameters)**
4. **Don't ignore database constraints**
5. **Don't use `CascadeType.ALL` without understanding it**
6. **Don't forget to add indexes on foreign keys**
7. **Don't use `SELECT *` in production queries**
8. **Don't perform database operations in loops**
9. **Don't expose entities directly (use DTOs)**
10. **Don't forget to handle transactions properly**

## Common Patterns

### Soft Delete
```java
@Entity
@Table(name = "users")
@SQLDelete(sql = "UPDATE users SET deleted_at = CURRENT_TIMESTAMP WHERE id = ?")
@Where(clause = "deleted_at IS NULL")
public class User {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "deleted_at")
    private LocalDateTime deletedAt;
}
```

### Audit Fields
```java
@MappedSuperclass
@Data
public abstract class AuditableEntity {

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
        // Set createdBy from SecurityContext
    }

    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
        // Set updatedBy from SecurityContext
    }
}

// Usage
@Entity
@Table(name = "users")
public class User extends AuditableEntity {
    // Automatically has audit fields
}
```

### UUID as ID
```java
@Entity
@Table(name = "users")
public class User {

    @Id
    @GeneratedValue(generator = "UUID")
    @GenericGenerator(name = "UUID", strategy = "org.hibernate.id.UUIDGenerator")
    @Column(name = "id", updatable = false, nullable = false)
    private UUID id;
}
```

---

**Referenced in:** `~/.claude/CLAUDE.md`
**Version:** 1.0.0
**Last Updated:** 2026-02-09
