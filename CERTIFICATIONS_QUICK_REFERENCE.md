# Certifications API Quick Reference

## Base URL
`/api/certifications`

## Endpoints

### 1. List All Certifications
```
GET /api/certifications
```

**Query Parameters:**
- `level` (optional): Filter by certification level (Advanced, Intermediate, Beginner)

**Response:**
```json
{
  "data": [
    {
      "id": "cert_judo_instructor",
      "name": "Judo Instructor",
      "description": "Comprehensive instructor certification...",
      "requirements": [...],
      "duration": "3 years (renewable)",
      "level": "Advanced"
    }
  ],
  "total": 4
}
```

**Example Requests:**
```bash
# List all certifications
curl http://localhost:8000/api/certifications

# Filter by level
curl http://localhost:8000/api/certifications?level=Advanced
```

---

### 2. Get Certification by ID
```
GET /api/certifications/{id}
```

**Path Parameters:**
- `id`: Certification ID (e.g., `cert_judo_instructor`)

**Response:**
```json
{
  "id": "cert_judo_instructor",
  "name": "Judo Instructor",
  "description": "Comprehensive instructor certification...",
  "requirements": [
    "Minimum 2nd Dan black belt in Judo",
    "At least 5 years of active Judo practice",
    "Complete 40-hour instructor training course",
    "Pass written examination on Judo history and technique",
    "Demonstrate teaching proficiency in practical evaluation",
    "Current CPR and First Aid certification"
  ],
  "duration": "3 years (renewable)",
  "level": "Advanced"
}
```

**Example Requests:**
```bash
curl http://localhost:8000/api/certifications/cert_judo_instructor
curl http://localhost:8000/api/certifications/cert_karate_instructor
curl http://localhost:8000/api/certifications/cert_self_defense_instructor
curl http://localhost:8000/api/certifications/cert_tournament_official
```

---

### 3. Search Certifications
```
GET /api/certifications/search/by-name
```

**Query Parameters:**
- `q` (required): Search query (minimum 2 characters)

**Response:**
```json
{
  "data": [...],
  "total": 3,
  "query": "instructor"
}
```

**Example Requests:**
```bash
# Search for "judo"
curl http://localhost:8000/api/certifications/search/by-name?q=judo

# Search for "instructor"
curl http://localhost:8000/api/certifications/search/by-name?q=instructor

# Search for "tournament"
curl http://localhost:8000/api/certifications/search/by-name?q=tournament
```

---

### 4. List Certification Levels
```
GET /api/certifications/levels/list
```

**Response:**
```json
{
  "data": [
    {
      "name": "Advanced",
      "count": 2
    },
    {
      "name": "Intermediate",
      "count": 2
    }
  ],
  "total": 2
}
```

**Example Request:**
```bash
curl http://localhost:8000/api/certifications/levels/list
```

---

## Available Certifications

| ID | Name | Level | Duration |
|----|------|-------|----------|
| `cert_judo_instructor` | Judo Instructor | Advanced | 3 years (renewable) |
| `cert_karate_instructor` | Karate Instructor | Advanced | 3 years (renewable) |
| `cert_self_defense_instructor` | Self-Defense Instructor | Intermediate | 2 years (renewable) |
| `cert_tournament_official` | Tournament Official | Intermediate | 2 years (renewable) |

---

## Error Responses

### 404 Not Found
```json
{
  "detail": "Certification with ID 'cert_nonexistent' not found"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["query", "q"],
      "msg": "String should have at least 2 characters"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Failed to fetch certifications"
}
```

---

## Notes

- All endpoints are **public** (no authentication required)
- All search and filtering is **case-insensitive**
- Response times are fast (hardcoded data, no database queries)
- All endpoints include proper logging for monitoring
