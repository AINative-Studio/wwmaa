# Instructor Management API Reference
## Quick Reference for Frontend Integration

---

## Base URL
```
/api/admin/instructors
```

## Authentication
All endpoints require admin authentication. Include JWT token in Authorization header:
```
Authorization: Bearer <your_admin_jwt_token>
```

---

## Endpoints

### 1. List All Instructors
**GET** `/api/admin/instructors`

**Query Parameters:**
- `page` (optional, default: 1) - Page number
- `page_size` (optional, default: 20, max: 100) - Items per page
- `is_active` (optional) - Filter by active status (true/false)
- `discipline` (optional) - Filter by discipline (e.g., "Karate")

**Response (200 OK):**
```json
{
  "instructors": [
    {
      "id": "instructor-uuid",
      "email": "instructor@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "phone": "+12025551234",
      "bio": "Experienced instructor...",
      "city": "Los Angeles",
      "state": "CA",
      "disciplines": ["Karate", "Judo"],
      "certifications": ["Black Belt 3rd Dan"],
      "schools_affiliated": ["WWMAA Dojo"],
      "is_active": true,
      "role": "instructor",
      "created_at": "2025-01-01T00:00:00Z",
      "member_since": "2025-01-01T00:00:00Z"
    }
  ],
  "total": 45,
  "page": 1,
  "page_size": 20
}
```

---

### 2. Create New Instructor
**POST** `/api/admin/instructors`

**Request Body:**
```json
{
  "email": "new.instructor@example.com",
  "password": "SecurePass123!",
  "first_name": "Jane",
  "last_name": "Smith",
  "phone": "+12025551234",
  "bio": "Experienced martial arts instructor with 10+ years...",
  "city": "New York",
  "state": "NY",
  "disciplines": ["Taekwondo", "Kickboxing"],
  "certifications": ["Black Belt 4th Dan", "Certified Instructor"],
  "schools_affiliated": ["Elite Martial Arts Academy"]
}
```

**Required Fields:**
- `email` (must be unique)
- `password` (minimum 8 characters)
- `first_name`
- `last_name`

**Optional Fields:**
- `phone` (E.164 format: +12025551234)
- `bio`
- `city`
- `state`
- `disciplines` (array of strings)
- `certifications` (array of strings)
- `schools_affiliated` (array of strings)

**Response (201 Created):**
```json
{
  "id": "new-instructor-uuid",
  "email": "new.instructor@example.com",
  "first_name": "Jane",
  "last_name": "Smith",
  ...
}
```

**Error Responses:**
- `400 Bad Request` - Email already exists or validation failed
- `403 Forbidden` - Not admin user
- `500 Internal Server Error` - Database error

---

### 3. Get Instructor Details
**GET** `/api/admin/instructors/{instructor_id}`

**Response (200 OK):**
```json
{
  "id": "instructor-uuid",
  "email": "instructor@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+12025551234",
  "bio": "Experienced instructor...",
  "city": "Los Angeles",
  "state": "CA",
  "disciplines": ["Karate", "Judo"],
  "certifications": ["Black Belt 3rd Dan"],
  "schools_affiliated": ["WWMAA Dojo"],
  "is_active": true,
  "role": "instructor",
  "created_at": "2025-01-01T00:00:00Z",
  "member_since": "2025-01-01T00:00:00Z"
}
```

**Error Responses:**
- `404 Not Found` - Instructor not found or not instructor role
- `403 Forbidden` - Not admin user
- `400 Bad Request` - Invalid UUID format

---

### 4. Update Instructor Profile
**PUT** `/api/admin/instructors/{instructor_id}`

**Request Body (all fields optional):**
```json
{
  "first_name": "Updated Name",
  "last_name": "Updated Last",
  "phone": "+12025555678",
  "bio": "Updated bio...",
  "city": "San Francisco",
  "state": "CA",
  "disciplines": ["Karate", "Judo", "Aikido"],
  "certifications": ["Black Belt 5th Dan"],
  "schools_affiliated": ["New Dojo"],
  "is_active": true
}
```

**Response (200 OK):**
```json
{
  "id": "instructor-uuid",
  "email": "instructor@example.com",
  "first_name": "Updated Name",
  ...
}
```

**Error Responses:**
- `404 Not Found` - Instructor not found
- `403 Forbidden` - Not admin user
- `400 Bad Request` - Validation failed

---

### 5. Get Instructor Performance Metrics
**GET** `/api/admin/instructors/{instructor_id}/performance`

**Response (200 OK):**
```json
{
  "instructor_id": "instructor-uuid",
  "instructor_name": "John Doe",

  "total_classes_taught": 45,
  "total_students_taught": 120,
  "total_teaching_hours": 90.5,
  "average_attendance_rate": 85.3,

  "average_class_rating": 4.7,
  "total_ratings_received": 89,
  "class_completion_rate": 98.5,
  "student_retention_rate": 82.3,

  "total_chat_messages": 234,
  "total_resources_shared": 12,

  "positive_feedback_count": 78,
  "neutral_feedback_count": 8,
  "negative_feedback_count": 3,

  "disciplines_taught": ["Karate", "Judo"],
  "certifications": ["Black Belt 3rd Dan", "Certified Instructor"],

  "last_class_date": "2025-11-10T14:00:00Z",
  "last_review_date": "2025-10-01T00:00:00Z",
  "next_review_date": "2026-01-01T00:00:00Z",

  "period_start_date": "2025-01-01T00:00:00Z",
  "period_end_date": null
}
```

**Notes:**
- Metrics are calculated in real-time from database
- New instructors will have zero values
- `period_end_date` is null for current period

**Error Responses:**
- `404 Not Found` - Instructor not found
- `403 Forbidden` - Not admin user

---

### 6. Assign Instructor to Class
**POST** `/api/admin/instructors/classes/{class_id}/assign`

**Request Body:**
```json
{
  "instructor_id": "instructor-uuid",
  "replace_existing": false
}
```

**Fields:**
- `instructor_id` (required) - UUID of instructor to assign
- `replace_existing` (optional, default: false) - Replace current instructor if exists

**Response (200 OK) - Training Session:**
```json
{
  "message": "Instructor assigned to training session successfully",
  "class_type": "training_session",
  "class_id": "session-uuid",
  "instructor_id": "instructor-uuid",
  "replaced": false
}
```

**Response (200 OK) - Event:**
```json
{
  "message": "Instructor assigned to event successfully",
  "class_type": "event",
  "class_id": "event-uuid",
  "instructor_id": "instructor-uuid",
  "total_instructors": 3
}
```

**Error Responses:**
- `400 Bad Request` - Already assigned (without replace flag) or user not instructor
- `404 Not Found` - Class or instructor not found
- `403 Forbidden` - Not admin user

---

### 7. Remove Instructor from Class
**DELETE** `/api/admin/instructors/classes/{class_id}/instructors/{instructor_id}`

**Response (200 OK):**
```json
{
  "message": "Instructor removed from training session successfully",
  "class_type": "training_session"
}
```

**Error Responses:**
- `400 Bad Request` - Instructor not assigned to this class
- `404 Not Found` - Class not found
- `403 Forbidden` - Not admin user

---

## Frontend Integration Examples

### React/Next.js Example

```typescript
// api/instructors.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL;

interface Instructor {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  bio?: string;
  city?: string;
  state?: string;
  disciplines: string[];
  certifications: string[];
  schools_affiliated: string[];
  is_active: boolean;
  role: string;
  created_at: string;
  member_since?: string;
}

interface InstructorList {
  instructors: Instructor[];
  total: number;
  page: number;
  page_size: number;
}

// List instructors
export async function listInstructors(
  token: string,
  page = 1,
  pageSize = 20,
  isActive?: boolean,
  discipline?: string
): Promise<InstructorList> {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });

  if (isActive !== undefined) params.append('is_active', isActive.toString());
  if (discipline) params.append('discipline', discipline);

  const response = await fetch(`${API_BASE}/api/admin/instructors?${params}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) throw new Error('Failed to fetch instructors');
  return response.json();
}

// Create instructor
export async function createInstructor(
  token: string,
  data: {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
    phone?: string;
    bio?: string;
    city?: string;
    state?: string;
    disciplines?: string[];
    certifications?: string[];
    schools_affiliated?: string[];
  }
): Promise<Instructor> {
  const response = await fetch(`${API_BASE}/api/admin/instructors`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create instructor');
  }

  return response.json();
}

// Get instructor performance
export async function getInstructorPerformance(
  token: string,
  instructorId: string
) {
  const response = await fetch(
    `${API_BASE}/api/admin/instructors/${instructorId}/performance`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) throw new Error('Failed to fetch performance');
  return response.json();
}

// Update instructor
export async function updateInstructor(
  token: string,
  instructorId: string,
  updates: Partial<Instructor>
): Promise<Instructor> {
  const response = await fetch(
    `${API_BASE}/api/admin/instructors/${instructorId}`,
    {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(updates),
    }
  );

  if (!response.ok) throw new Error('Failed to update instructor');
  return response.json();
}

// Assign to class
export async function assignInstructor(
  token: string,
  classId: string,
  instructorId: string,
  replaceExisting = false
) {
  const response = await fetch(
    `${API_BASE}/api/admin/instructors/classes/${classId}/assign`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        instructor_id: instructorId,
        replace_existing: replaceExisting,
      }),
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to assign instructor');
  }

  return response.json();
}
```

### Component Example

```tsx
// components/InstructorList.tsx
import { useState, useEffect } from 'react';
import { listInstructors, Instructor } from '@/api/instructors';

export default function InstructorList({ token }: { token: string }) {
  const [instructors, setInstructors] = useState<Instructor[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchInstructors() {
      try {
        setLoading(true);
        const data = await listInstructors(token, page, 20);
        setInstructors(data.instructors);
        setTotal(data.total);
      } catch (error) {
        console.error('Failed to load instructors:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchInstructors();
  }, [token, page]);

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      <h2>Instructors ({total})</h2>
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th>Disciplines</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {instructors.map(instructor => (
            <tr key={instructor.id}>
              <td>{instructor.first_name} {instructor.last_name}</td>
              <td>{instructor.email}</td>
              <td>{instructor.disciplines.join(', ')}</td>
              <td>{instructor.is_active ? 'Active' : 'Inactive'}</td>
              <td>
                <button onClick={() => viewPerformance(instructor.id)}>
                  View Performance
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div>
        <button
          disabled={page === 1}
          onClick={() => setPage(p => p - 1)}
        >
          Previous
        </button>
        <span>Page {page}</span>
        <button
          disabled={page * 20 >= total}
          onClick={() => setPage(p => p + 1)}
        >
          Next
        </button>
      </div>
    </div>
  );
}
```

---

## Validation Rules

### Email
- Must be valid email format
- Converted to lowercase
- Must be unique across system

### Password
- Minimum 8 characters
- Maximum 128 characters
- Strength validation applied

### Phone
- E.164 format: +[country code][number]
- Example: +12025551234
- Optional field

### Text Fields
- SQL injection prevention
- HTML sanitization (bio field)
- Max lengths enforced

### UUIDs
- Must be valid UUID format
- Validated on all ID parameters

---

## Common Error Codes

| Status | Meaning | Common Causes |
|--------|---------|---------------|
| 400 | Bad Request | Invalid input, validation failed, duplicate email |
| 401 | Unauthorized | Missing or invalid JWT token |
| 403 | Forbidden | User is not admin |
| 404 | Not Found | Instructor/class not found, wrong role |
| 500 | Internal Server Error | Database error, unexpected server error |

---

## Best Practices

1. **Always handle errors gracefully**
   - Display user-friendly error messages
   - Log errors for debugging
   - Provide fallback UI

2. **Use pagination for large lists**
   - Default page size: 20
   - Maximum page size: 100
   - Show total count to users

3. **Validate on frontend before API calls**
   - Email format
   - Phone number format
   - Required fields
   - Reduces unnecessary API calls

4. **Cache instructor data when appropriate**
   - List data can be cached briefly
   - Performance metrics should be fresh
   - Invalidate cache on updates

5. **Use optimistic updates for better UX**
   - Update UI immediately
   - Revert on error
   - Show loading states

6. **Implement proper loading states**
   - Show spinners during API calls
   - Disable buttons during operations
   - Prevent duplicate submissions

---

## Testing the API

Use curl or Postman to test:

```bash
# List instructors
curl -X GET "http://localhost:8000/api/admin/instructors?page=1&page_size=20" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Create instructor
curl -X POST "http://localhost:8000/api/admin/instructors" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!",
    "first_name": "Test",
    "last_name": "Instructor"
  }'

# Get performance
curl -X GET "http://localhost:8000/api/admin/instructors/INSTRUCTOR_ID/performance" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Support

For issues or questions:
- Check the implementation summary: `ISSUES_10_11_IMPLEMENTATION_SUMMARY.md`
- Review test cases: `backend/tests/test_admin_instructors.py`
- Check API logs for detailed error messages
