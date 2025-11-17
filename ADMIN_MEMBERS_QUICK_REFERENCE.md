# Admin Members API - Quick Reference Guide

## API Endpoints Summary

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/admin/members` | Create new member | Admin |
| GET | `/api/admin/members` | List all members (paginated) | Admin |
| GET | `/api/admin/members/{id}` | Get single member | Admin |
| PUT | `/api/admin/members/{id}` | Update member | Admin |
| DELETE | `/api/admin/members/{id}` | Delete member | Admin |

---

## Quick Start Examples

### 1. Create Member

```bash
curl -X POST http://localhost:8000/api/admin/members \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -d '{
    "email": "john.doe@example.com",
    "password": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe",
    "role": "member",
    "phone": "+12025551234"
  }'
```

**Response (201)**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "john.doe@example.com",
  "role": "member",
  "is_active": true,
  "is_verified": false,
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+12025551234",
  "created_at": "2025-11-14T12:00:00Z",
  "updated_at": "2025-11-14T12:00:00Z",
  "last_login": null
}
```

### 2. List Members

```bash
# Basic listing
curl -X GET "http://localhost:8000/api/admin/members?limit=20&offset=0" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"

# With filters
curl -X GET "http://localhost:8000/api/admin/members?role=instructor&is_active=true" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"

# With search
curl -X GET "http://localhost:8000/api/admin/members?search=john" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

**Response (200)**:
```json
{
  "members": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "john.doe@example.com",
      "role": "member",
      "is_active": true,
      "first_name": "John",
      "last_name": "Doe",
      ...
    }
  ],
  "total": 100,
  "limit": 20,
  "offset": 0
}
```

### 3. Get Single Member

```bash
curl -X GET http://localhost:8000/api/admin/members/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### 4. Update Member

```bash
curl -X PUT http://localhost:8000/api/admin/members/550e8400-e29b-41d4-a716-446655440000 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -d '{
    "first_name": "Jane",
    "role": "instructor",
    "is_active": false
  }'
```

### 5. Delete Member

```bash
curl -X DELETE http://localhost:8000/api/admin/members/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

**Response (204)**: No content

---

## Request/Response Schemas

### Create Member Request
```typescript
{
  email: string;              // Required, unique, valid email
  password: string;           // Required, 8-128 chars, strong
  first_name: string;         // Required, 1-100 chars
  last_name: string;          // Required, 1-100 chars
  role?: "public" | "member" | "instructor" | "board_member" | "admin";  // Default: "member"
  is_active?: boolean;        // Default: true
  phone?: string;             // Optional, max 20 chars
}
```

### Update Member Request
```typescript
{
  email?: string;             // Optional, must be unique
  first_name?: string;        // Optional
  last_name?: string;         // Optional
  role?: string;              // Optional
  is_active?: boolean;        // Optional
  phone?: string;             // Optional
  password?: string;          // Optional, will be re-hashed
}
```

### Member Response
```typescript
{
  id: string;                 // UUID
  email: string;
  role: string;
  is_active: boolean;
  is_verified: boolean;
  first_name: string | null;
  last_name: string | null;
  phone: string | null;
  created_at: string;         // ISO 8601
  updated_at: string;         // ISO 8601
  last_login: string | null;  // ISO 8601
}
```

---

## Query Parameters (List Endpoint)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 10 | Results per page (1-100) |
| `offset` | integer | 0 | Number of results to skip |
| `role` | string | - | Filter by role (public, member, instructor, board_member, admin) |
| `is_active` | boolean | - | Filter by active status |
| `search` | string | - | Search in email, first_name, last_name |

**Examples**:
- `?limit=50&offset=100` - Get results 101-150
- `?role=instructor` - Only instructors
- `?is_active=true` - Only active members
- `?search=john` - Search for "john" in email/name

---

## HTTP Status Codes

| Status | Meaning | When It Occurs |
|--------|---------|----------------|
| 200 | OK | Successful GET or PUT |
| 201 | Created | Successful POST |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Invalid UUID format, self-deletion attempt |
| 403 | Forbidden | Not admin user |
| 404 | Not Found | Member doesn't exist |
| 409 | Conflict | Duplicate email |
| 422 | Unprocessable Entity | Validation error (weak password, invalid email, etc.) |
| 500 | Internal Server Error | Database error, profile creation failure |

---

## Validation Rules

### Email
- Must be valid RFC 5322 format
- Automatically converted to lowercase
- Must be unique across all users
- Example: `john.doe@example.com`

### Password
- Minimum 8 characters
- Maximum 128 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 number
- At least 1 special character (!@#$%^&*()_+-=[]{}|;:,.<>?)
- Example: `SecurePass123!`

### Names (first_name, last_name)
- 1-100 characters
- HTML tags stripped
- SQL injection patterns detected
- Whitespace trimmed
- Example: `John`, `Doe`

### Phone
- Optional
- Max 20 characters
- Any format accepted
- Example: `+12025551234`, `(202) 555-1234`

### Role
- Must be one of: `public`, `member`, `instructor`, `board_member`, `admin`
- Case-insensitive
- Defaults to `member` on creation

### UUID (member_id)
- Must be valid RFC 4122 UUID
- Example: `550e8400-e29b-41d4-a716-446655440000`

---

## Error Response Format

```json
{
  "detail": "Error message here"
}
```

**Examples**:
```json
// 400 Bad Request
{
  "detail": "Invalid member ID format"
}

// 404 Not Found
{
  "detail": "Member with ID '550e8400-e29b-41d4-a716-446655440000' not found"
}

// 409 Conflict
{
  "detail": "A user with email 'john.doe@example.com' already exists"
}

// 422 Validation Error
{
  "detail": [
    "Password must be at least 8 characters",
    "Password must contain at least one uppercase letter",
    "Password must contain at least one special character"
  ]
}
```

---

## Security Notes

1. **Admin Only**: All endpoints require admin role authentication
2. **Password Security**:
   - Passwords are hashed with bcrypt (12 rounds)
   - Never stored in plaintext
   - Never returned in responses
3. **Self-Deletion Prevention**: Admin cannot delete their own account
4. **Input Sanitization**: All inputs sanitized for SQL injection and XSS
5. **Email Uniqueness**: Enforced at database level

---

## Testing Commands

```bash
# Run unit tests
python3 -m pytest backend/tests/test_admin_members_routes.py -v

# Run integration tests
python3 -m pytest backend/tests/test_admin_members_integration.py -v

# Run all member tests
python3 -m pytest backend/tests/test_admin_members*.py -v

# Run verification script (requires backend running)
python3 scripts/verify_admin_members_api.py
```

---

## Common Use Cases

### 1. Create Instructor Account
```bash
curl -X POST http://localhost:8000/api/admin/members \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "email": "instructor@example.com",
    "password": "InstructorPass123!",
    "first_name": "Jane",
    "last_name": "Smith",
    "role": "instructor"
  }'
```

### 2. Deactivate Member
```bash
curl -X PUT http://localhost:8000/api/admin/members/$MEMBER_ID \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"is_active": false}'
```

### 3. Promote Member to Instructor
```bash
curl -X PUT http://localhost:8000/api/admin/members/$MEMBER_ID \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"role": "instructor"}'
```

### 4. Search for Member by Email
```bash
curl -X GET "http://localhost:8000/api/admin/members?search=john.doe@example.com" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### 5. Get All Active Instructors
```bash
curl -X GET "http://localhost:8000/api/admin/members?role=instructor&is_active=true&limit=100" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### 6. Reset Member Password
```bash
curl -X PUT http://localhost:8000/api/admin/members/$MEMBER_ID \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"password": "NewSecurePass123!"}'
```

---

## Frontend Integration Example (React/TypeScript)

```typescript
// types.ts
export interface Member {
  id: string;
  email: string;
  role: 'public' | 'member' | 'instructor' | 'board_member' | 'admin';
  is_active: boolean;
  is_verified: boolean;
  first_name: string | null;
  last_name: string | null;
  phone: string | null;
  created_at: string;
  updated_at: string;
  last_login: string | null;
}

export interface CreateMemberData {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  role?: string;
  is_active?: boolean;
  phone?: string;
}

export interface UpdateMemberData {
  email?: string;
  first_name?: string;
  last_name?: string;
  role?: string;
  is_active?: boolean;
  phone?: string;
  password?: string;
}

export interface MemberListResponse {
  members: Member[];
  total: number;
  limit: number;
  offset: number;
}

// api.ts
const API_BASE = 'http://localhost:8000';

export async function createMember(data: CreateMemberData): Promise<Member> {
  const response = await fetch(`${API_BASE}/api/admin/members`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getAdminToken()}`
    },
    body: JSON.stringify(data)
  });

  if (!response.ok) {
    throw new Error(`Failed to create member: ${response.statusText}`);
  }

  return response.json();
}

export async function listMembers(
  limit = 10,
  offset = 0,
  filters?: { role?: string; is_active?: boolean; search?: string }
): Promise<MemberListResponse> {
  const params = new URLSearchParams({
    limit: limit.toString(),
    offset: offset.toString(),
    ...filters
  });

  const response = await fetch(
    `${API_BASE}/api/admin/members?${params}`,
    {
      headers: { 'Authorization': `Bearer ${getAdminToken()}` }
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to list members: ${response.statusText}`);
  }

  return response.json();
}

export async function updateMember(
  id: string,
  data: UpdateMemberData
): Promise<Member> {
  const response = await fetch(`${API_BASE}/api/admin/members/${id}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getAdminToken()}`
    },
    body: JSON.stringify(data)
  });

  if (!response.ok) {
    throw new Error(`Failed to update member: ${response.statusText}`);
  }

  return response.json();
}

export async function deleteMember(id: string): Promise<void> {
  const response = await fetch(`${API_BASE}/api/admin/members/${id}`, {
    method: 'DELETE',
    headers: { 'Authorization': `Bearer ${getAdminToken()}` }
  });

  if (!response.ok) {
    throw new Error(`Failed to delete member: ${response.statusText}`);
  }
}
```

---

## Troubleshooting

### Issue: 403 Forbidden
**Cause**: Not authenticated as admin
**Solution**: Ensure you're passing a valid admin JWT token in the Authorization header

### Issue: 409 Conflict (duplicate email)
**Cause**: Email already exists
**Solution**: Use a different email or update the existing member instead

### Issue: 422 Validation Error (weak password)
**Cause**: Password doesn't meet strength requirements
**Solution**: Ensure password has 8+ chars with uppercase, lowercase, numbers, and special characters

### Issue: 400 Bad Request (invalid UUID)
**Cause**: Member ID is not a valid UUID format
**Solution**: Ensure you're using a properly formatted UUID from a previous API response

### Issue: 500 Internal Server Error
**Cause**: Database error or profile creation failure
**Solution**: Check backend logs for specific error details

---

## Files Reference

| File | Purpose | Lines |
|------|---------|-------|
| `/backend/routes/admin/members.py` | API endpoints implementation | 806 |
| `/backend/tests/test_admin_members_routes.py` | Unit tests | 734 |
| `/backend/tests/test_admin_members_integration.py` | Integration tests | 445 |
| `/scripts/verify_admin_members_api.py` | Verification script | 430 |

---

## Related Documentation

- [Implementation Summary](./ISSUES_8_9_IMPLEMENTATION_SUMMARY.md)
- [API Architecture](./ADMIN_MEMBERS_API_ARCHITECTURE.md)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Validation](https://docs.pydantic.dev/)

---

**Last Updated**: 2025-11-14
**API Version**: 1.0.0
**Status**: Production Ready ✅
