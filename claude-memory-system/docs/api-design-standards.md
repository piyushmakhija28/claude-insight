# API Design Standards (MANDATORY)

**🚨 CRITICAL: Follow these standards for ALL REST APIs! 🚨**

## RESTful API Conventions

### HTTP Methods
| Method | Purpose | Idempotent | Request Body | Response Body |
|--------|---------|------------|--------------|---------------|
| GET | Read/Retrieve | Yes | No | Yes |
| POST | Create | No | Yes | Yes |
| PUT | Update (full) | Yes | Yes | Yes |
| PATCH | Update (partial) | No | Yes | Yes |
| DELETE | Delete | Yes | No | Optional |

### URL Structure
```
/{api-version}/{resource}/{id}/{sub-resource}
```

**✅ CORRECT:**
```
GET    /api/v1/users
GET    /api/v1/users/123
POST   /api/v1/users
PUT    /api/v1/users/123
DELETE /api/v1/users/123
GET    /api/v1/users/123/orders
```

**❌ WRONG:**
```
/api/v1/getUsers          ❌ (No verbs in URL!)
/api/v1/user              ❌ (Use plural!)
/api/v1/Users             ❌ (Use lowercase!)
/api/v1/user_list         ❌ (Use kebab-case!)
```

## Response Format (MANDATORY)

**ALL responses MUST use `ApiResponseDto<T>`:**

### Success Response
```json
{
  "status": true,
  "message": "User registered successfully",
  "data": {
    "id": "123",
    "email": "user@example.com",
    "name": "John Doe"
  }
}
```

### Error Response
```json
{
  "status": false,
  "message": "Email already exists",
  "data": null
}
```

### List Response
```json
{
  "status": true,
  "message": "Users retrieved successfully",
  "data": {
    "items": [...],
    "totalCount": 100,
    "page": 1,
    "pageSize": 10
  }
}
```

## HTTP Status Codes

| Code | Meaning | When to Use |
|------|---------|-------------|
| 200 | OK | Successful GET, PUT, PATCH, DELETE |
| 201 | Created | Successful POST (resource created) |
| 204 | No Content | Successful DELETE (no response body) |
| 400 | Bad Request | Validation errors, malformed request |
| 401 | Unauthorized | Authentication required/failed |
| 403 | Forbidden | Authenticated but not authorized |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate resource (email exists, etc.) |
| 500 | Internal Server Error | Server-side errors |

## Naming Conventions

### Resource Names
- **Use plural nouns**: `/users`, `/products`, `/orders`
- **Use kebab-case**: `/user-profiles`, `/order-items`
- **No verbs**: `/users` NOT `/getUsers`

### Query Parameters
```
GET /api/v1/users?page=1&size=10&sort=name,asc&filter=active
```

**Common parameters:**
- `page` - Page number (starts from 1)
- `size` / `limit` - Items per page
- `sort` - Sorting field and direction
- `filter` / `search` - Filter criteria

### Path Parameters
```
GET /api/v1/users/{userId}/orders/{orderId}
```

**Use camelCase for path variables in code:**
```java
@GetMapping("/users/{userId}/orders/{orderId}")
public ApiResponseDto<OrderDto> getOrder(
    @PathVariable Long userId,
    @PathVariable Long orderId
)
```

## Pagination Standard

**Request:**
```
GET /api/v1/users?page=1&size=10
```

**Response:**
```json
{
  "status": true,
  "message": "Users retrieved successfully",
  "data": {
    "items": [...],
    "pagination": {
      "currentPage": 1,
      "pageSize": 10,
      "totalItems": 100,
      "totalPages": 10,
      "hasNext": true,
      "hasPrevious": false
    }
  }
}
```

## Filtering and Searching

### Simple Filter
```
GET /api/v1/users?status=active&role=admin
```

### Search
```
GET /api/v1/users?search=john
```

### Advanced Filter (JSON in query param)
```
GET /api/v1/users?filter={"status":"active","age":{"$gte":18}}
```

## Sorting

```
GET /api/v1/users?sort=name,asc
GET /api/v1/users?sort=createdAt,desc
GET /api/v1/users?sort=name,asc&sort=email,asc  (multiple)
```

## Versioning

**Always include API version in URL:**
```
/api/v1/users
/api/v2/users
```

**NEVER version in:**
- Headers (hard to test in browser)
- Query params (pollutes URLs)

## Request/Response Examples

### Create User (POST)
**Request:**
```
POST /api/v1/users
Content-Type: application/json

{
  "email": "john@example.com",
  "password": "SecurePass123!",
  "name": "John Doe",
  "phone": "+1234567890"
}
```

**Response (201 Created):**
```json
{
  "status": true,
  "message": "User created successfully",
  "data": {
    "id": "123",
    "email": "john@example.com",
    "name": "John Doe",
    "createdAt": "2026-02-09T10:30:00Z"
  }
}
```

### Update User (PUT)
**Request:**
```
PUT /api/v1/users/123
Content-Type: application/json

{
  "name": "John Smith",
  "phone": "+9876543210"
}
```

**Response (200 OK):**
```json
{
  "status": true,
  "message": "User updated successfully",
  "data": {
    "id": "123",
    "email": "john@example.com",
    "name": "John Smith",
    "phone": "+9876543210",
    "updatedAt": "2026-02-09T10:35:00Z"
  }
}
```

### Get User (GET)
**Request:**
```
GET /api/v1/users/123
```

**Response (200 OK):**
```json
{
  "status": true,
  "message": "User retrieved successfully",
  "data": {
    "id": "123",
    "email": "john@example.com",
    "name": "John Smith",
    "phone": "+9876543210"
  }
}
```

### Delete User (DELETE)
**Request:**
```
DELETE /api/v1/users/123
```

**Response (200 OK):**
```json
{
  "status": true,
  "message": "User deleted successfully",
  "data": null
}
```

## Error Response Format

### Validation Error
```json
{
  "status": false,
  "message": "Validation failed",
  "errors": [
    {
      "field": "email",
      "message": "Email is required"
    },
    {
      "field": "password",
      "message": "Password must be at least 8 characters"
    }
  ]
}
```

### Business Logic Error
```json
{
  "status": false,
  "message": "Email already exists",
  "errorCode": "USER_EMAIL_EXISTS"
}
```

### System Error
```json
{
  "status": false,
  "message": "Internal server error",
  "errorCode": "INTERNAL_ERROR"
}
```

## Controller Implementation Pattern

```java
@RestController
@RequestMapping("/api/v1/users")
public class UserController {

    @Autowired
    private UserService userService;

    @PostMapping
    public ResponseEntity<ApiResponseDto<UserDto>> createUser(
            @Valid @RequestBody RegisterUserForm form) {
        UserDto user = userService.createUser(form);
        return ResponseEntity
            .status(HttpStatus.CREATED)
            .body(ApiResponseDto.success("User created successfully", user));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ApiResponseDto<UserDto>> getUser(
            @PathVariable Long id) {
        UserDto user = userService.getUserById(id);
        return ResponseEntity.ok(
            ApiResponseDto.success("User retrieved successfully", user)
        );
    }

    @PutMapping("/{id}")
    public ResponseEntity<ApiResponseDto<UserDto>> updateUser(
            @PathVariable Long id,
            @Valid @RequestBody UpdateUserForm form) {
        UserDto user = userService.updateUser(id, form);
        return ResponseEntity.ok(
            ApiResponseDto.success("User updated successfully", user)
        );
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<ApiResponseDto<Void>> deleteUser(
            @PathVariable Long id) {
        userService.deleteUser(id);
        return ResponseEntity.ok(
            ApiResponseDto.success("User deleted successfully", null)
        );
    }

    @GetMapping
    public ResponseEntity<ApiResponseDto<PageDto<UserDto>>> getUsers(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size) {
        PageDto<UserDto> users = userService.getUsers(page, size);
        return ResponseEntity.ok(
            ApiResponseDto.success("Users retrieved successfully", users)
        );
    }
}
```

## Best Practices

### ✅ DO:
- Use nouns for resources
- Use plural names
- Keep URLs consistent
- Use proper HTTP status codes
- Always return `ApiResponseDto<T>`
- Version your APIs
- Validate all inputs
- Document with Swagger/OpenAPI

### ❌ DON'T:
- Use verbs in URLs (`/getUser`)
- Mix singular/plural (`/user`, `/users`)
- Use underscores (`/user_profile`)
- Return raw objects (always wrap in `ApiResponseDto`)
- Expose internal IDs unnecessarily
- Return stack traces in production

---

**Referenced in:** `~/.claude/CLAUDE.md`
**Version:** 1.0.0
**Last Updated:** 2026-02-09
