# Java Spring Boot Project Structure (MANDATORY)

**🚨 CRITICAL: Follow this structure for ALL Java Spring Boot microservices! 🚨**

## Base Package Convention

```
com.techdeveloper.${projectname}
```

**✅ CORRECT:**
- `com.techdeveloper` (company's own projects)
- `com.techdeveloper.m2surgricals` (client project)

**❌ WRONG:**
- `com.techdeveloper.m2surgricals.m2surgricals` (duplicate!)

## Package Structure

| Package | Purpose | Contains |
|---------|---------|----------|
| `controller` | REST endpoints | `@RestController` classes |
| `dto` | Response objects | DTOs returned to client |
| `form` | Request objects | `@RequestBody` classes |
| `constants` | All constants/enums | Message constants, enums |
| `exceptions` | Custom exceptions | Exception classes |
| `services` | Service interfaces | ONLY interfaces |
| `services.impl` | Service implementations | Package-private impls |
| `services.helper` | Helper methods | Abstract helper classes |
| `utils` | Utilities | Date, String utilities |
| `repository` | Data access | JPA/MongoDB repos |
| `config` | Configurations | Security, beans configs |
| `entity` | Database entities | `@Entity`/`@Document` |
| `event` | Event system | Events, listeners |
| `annotations` | Custom annotations | Validators |
| `annotations.groups` | Validation groups | Group interfaces |
| `annotations.sequence` | Validation sequence | `ValidationSequence.java` |

## Mandatory Inheritance Rules

### Form Classes
```java
// ✅ CORRECT
public class RegisterUserForm extends ValidationMessageConstants {
    @NotBlank(message = EMAIL_REQUIRED)
    private String email;
}
```

### Service Implementation Pattern
```java
// Helper extends ServiceMessageConstants
public abstract class UserServiceHelper extends ServiceMessageConstants {
    protected String formatName(String name) { ... }
}

// Impl extends Helper, implements Interface
@Service
class UserServiceImpl extends UserServiceHelper implements UserService {
    @Override
    public ApiResponseDto<Void> add(String name) {
        return ApiResponseDto.<Void>builder()
            .message(USER_ADDED_SUCCESSFULLY)
            .status(201)
            .success(true)
            .build();
    }
}
```

## ApiResponseDto<T> (MANDATORY!)

**ALL controller responses MUST use `ApiResponseDto<T>` wrapper!**

```java
@Builder
@Getter
@JsonInclude(Include.NON_NULL)
@NoArgsConstructor
@AllArgsConstructor
public class ApiResponseDto<T> implements Serializable {
    private T data;
    private String message;
    private boolean success;
    private int status;
    private final long timestamp = System.currentTimeMillis();
}
```

### Controller Pattern
```java
@PostMapping
public ResponseEntity<ApiResponseDto<Void>> add(
        @Validated(ValidationSequence.class)
        @RequestBody CategoryForm form) {

    ApiResponseDto<Void> response = categoryService.add(form.getName());
    return new ResponseEntity<>(response, HttpStatus.valueOf(response.getStatus()));
}
```

### Service Interface Pattern
```java
public interface CategoryService {
    @Transactional(rollbackFor = DataAccessException.class, propagation = Propagation.REQUIRES_NEW)
    ApiResponseDto<Void> add(String name);

    ApiResponseDto<CategoryDTO> getById(Long id);
    ApiResponseDto<List<CategoryDTO>> getAll();
}
```

## Generic Type Usage
- `ApiResponseDto<Void>` - add, update, delete
- `ApiResponseDto<UserDTO>` - single object
- `ApiResponseDto<List<UserDTO>>` - list
- `ApiResponseDto<Page<UserDTO>>` - paginated

## Response Examples

**Success with data:**
```json
{"data": {...}, "success": true, "status": 200, "timestamp": 1738425600000}
```

**Success without data:**
```json
{"message": "Created", "success": true, "status": 201, "timestamp": 1738425600000}
```

**Error:**
```json
{"message": "Not found", "success": false, "status": 404, "timestamp": 1738425600000}
```

## Golden Rules

1. ✅ NO hardcoding - constants package only
2. ✅ DTO = response, Form = request (NEVER confuse!)
3. ✅ ALL responses use `ApiResponseDto<T>`
4. ✅ Service impl extends helper, implements interface
5. ✅ Service impl is package-private
6. ✅ `@Transactional` for write operations
7. ✅ ValidationSequence for validation

## Project Structure Example

```
com.techdeveloper.backend/
├── controller/
├── dto/
├── form/
├── constants/
│   └── enums/
├── exceptions/
├── services/
├── services.impl/
├── services.helper/
├── utils/
├── repository/
├── config/
├── entity/
├── event/
├── annotations/
├── annotations.groups/
└── annotations.sequence/
    └── ValidationSequence.java
```

## Validation Checklist

Before creating any class:
- Response object? → `dto`
- Request object? → `form`
- Service? → Interface in `services`, impl in `services.impl`
- Constant? → `constants`
- Entity? → `entity`

**🚨 NEVER violate this structure! 🚨**
