# GDPR Data Export API Documentation

## Overview

The GDPR Data Export API provides users with the ability to export all their personal data stored in the WWMAA platform, in compliance with GDPR Article 20 (Right to data portability) and Article 15 (Right of access).

## Base URL

```
Production: https://api.wwmaa.com
Staging: https://staging-api.wwmaa.com
Development: http://localhost:8000
```

## Authentication

All endpoints require JWT authentication via Bearer token:

```http
Authorization: Bearer <your_jwt_token>
```

## Endpoints

### 1. Request Data Export

Request a complete export of all your personal data.

**Endpoint:** `POST /api/privacy/export-data`

**Request:**
```http
POST /api/privacy/export-data
Authorization: Bearer <token>
Content-Type: application/json

{}
```

**Response (202 Accepted):**
```json
{
  "export_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "message": "Your data export has been generated successfully...",
  "download_url": "https://api.zerodb.io/storage/exports/...",
  "expiry_date": "2025-01-11T12:00:00Z",
  "file_size_bytes": 1024000,
  "record_counts": {
    "profiles": 1,
    "applications": 2,
    "subscriptions": 1,
    "payments": 5,
    "rsvps": 10,
    "search_queries": 50,
    "attendees": 20,
    "audit_logs": 100
  }
}
```

**Data Included:**
- **Profile information**: Name, email, profile data
- **Membership applications**: Application history and status
- **Subscriptions**: Subscription and membership history
- **Payment records**: Transaction history
- **Event RSVPs**: Event registration history
- **Search queries**: AI search query history
- **Training attendance**: Training session attendance records
- **Audit logs**: User activity and action logs

**Export Format:**
- Format: JSON (machine-readable)
- Includes human-readable cover letter
- All PII is included (except password hashes)
- Structured with descriptions for each data type

**Security:**
- Download link is signed and secure
- Link expires after 24 hours
- Only accessible by authenticated user
- Email notification sent when ready

**Rate Limiting:**
- Users can request one export per 24 hours

**Error Responses:**

```json
// 401 Unauthorized
{
  "detail": "Not authenticated"
}

// 400 Bad Request
{
  "detail": "Invalid user data in authentication token"
}

// 429 Too Many Requests
{
  "detail": "Export request rate limit exceeded. Please try again in 24 hours."
}

// 500 Internal Server Error
{
  "detail": "Failed to export data: <error message>"
}
```

---

### 2. Check Export Status

Check the status of a data export request.

**Endpoint:** `GET /api/privacy/export-status/{export_id}`

**Request:**
```http
GET /api/privacy/export-status/550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "export_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "created_at": "2025-01-10T12:00:00Z",
  "expiry_date": "2025-01-11T12:00:00Z",
  "file_size_bytes": 1024000
}
```

**Possible Status Values:**
- `processing`: Export is being generated
- `completed`: Export is ready for download
- `expired`: Export has expired and been deleted
- `not_found`: Export ID not found

**Error Responses:**

```json
// 404 Not Found
{
  "detail": "Export not found or has expired"
}

// 401 Unauthorized
{
  "detail": "Not authenticated"
}

// 403 Forbidden
{
  "detail": "Not authorized to access this export"
}
```

---

### 3. Delete Export File

Delete a data export file before its automatic expiry.

**Endpoint:** `DELETE /api/privacy/export/{export_id}`

**Request:**
```http
DELETE /api/privacy/export/550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "message": "Export file deleted successfully",
  "deleted": true
}
```

**Error Responses:**

```json
// 404 Not Found
{
  "detail": "Export not found or already deleted"
}

// 401 Unauthorized
{
  "detail": "Not authenticated"
}

// 403 Forbidden
{
  "detail": "Not authorized to delete this export"
}
```

---

### 4. Health Check

Check if privacy service is operational.

**Endpoint:** `GET /api/privacy/health`

**Request:**
```http
GET /api/privacy/health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "privacy",
  "timestamp": "2025-01-10T12:00:00Z"
}
```

---

## Complete Workflow Example

### Step 1: Request Export

```bash
curl -X POST https://api.wwmaa.com/api/privacy/export-data \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Response:**
```json
{
  "export_id": "abc123",
  "status": "completed",
  "download_url": "https://signed-url...",
  "expiry_date": "2025-01-11T12:00:00Z"
}
```

### Step 2: Check Email

User receives email notification:
- Subject: "Your WWMAA Data Export is Ready"
- Contains download link (valid for 24 hours)
- Security warnings about keeping data safe

### Step 3: Download Export

Click download link or use the URL from API response:

```bash
curl -o my_data.json "https://signed-url..."
```

### Step 4: Optional - Delete Export Early

```bash
curl -X DELETE https://api.wwmaa.com/api/privacy/export/abc123 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## Export File Structure

The exported JSON file follows this structure:

```json
{
  "export_metadata": {
    "export_id": "550e8400-e29b-41d4-a716-446655440000",
    "export_date": "2025-01-10T12:00:00Z",
    "expiry_date": "2025-01-11T12:00:00Z",
    "user_id": "user_123",
    "format_version": "1.0",
    "gdpr_article": "Article 20 - Right to data portability"
  },
  "cover_letter": {
    "title": "Your Personal Data Export from WWMAA",
    "introduction": "This file contains all personal data...",
    "recipient": "user@example.com",
    "export_date": "January 10, 2025 at 12:00 UTC",
    "expiry_date": "January 11, 2025 at 12:00 UTC",
    "data_included": "This export includes all data associated with your account...",
    "format_notice": "The data is provided in JSON format...",
    "privacy_notice": "This file contains your personal data...",
    "contact_info": "If you have questions about this export..."
  },
  "data": {
    "profiles": {
      "description": "Profile Information",
      "record_count": 1,
      "records": [
        {
          "id": "profile_1",
          "user_id": "user_123",
          "first_name": "John",
          "last_name": "Doe",
          "email": "john@example.com",
          "created_at": "2025-01-01T00:00:00Z"
        }
      ]
    },
    "applications": {
      "description": "Membership Applications",
      "record_count": 2,
      "records": [...]
    },
    "subscriptions": {
      "description": "Subscription History",
      "record_count": 1,
      "records": [...]
    },
    "payments": {
      "description": "Payment History",
      "record_count": 5,
      "records": [...]
    },
    "rsvps": {
      "description": "Event RSVPs",
      "record_count": 10,
      "records": [...]
    },
    "search_queries": {
      "description": "Search History",
      "record_count": 50,
      "records": [...]
    },
    "attendees": {
      "description": "Training Attendance",
      "record_count": 20,
      "records": [...]
    },
    "audit_logs": {
      "description": "Activity Logs",
      "record_count": 100,
      "records": [...]
    }
  }
}
```

---

## Data Privacy & Security

### What is Included
- All personal information you provided
- All activity data (applications, RSVPs, searches)
- Payment and subscription records
- Audit logs of your actions

### What is Excluded
- Password hashes (for security)
- Internal system IDs (not relevant to users)
- Other users' data
- System configuration data

### Data Redaction
- Credit card numbers are partially redacted (****1234)
- Internal database IDs are removed
- Password hashes are never included

### Security Measures
- Download links are cryptographically signed
- Links expire after 24 hours
- Files are automatically deleted after expiry
- Only the authenticated user can access their export
- Email notifications for all export requests
- Audit logs maintained for all operations

---

## GDPR Compliance

This API implements:

**GDPR Article 20 - Right to data portability:**
- Data provided in structured, machine-readable format (JSON)
- Complete data export without hindrance
- Ability to transmit data to another controller

**GDPR Article 15 - Right of access:**
- Confirmation that personal data is being processed
- Access to all personal data
- Information about the purposes of processing
- Categories of data concerned

---

## Technical Specifications

### Performance
- Export generation: < 30 seconds for typical user
- File size: Varies by user activity (typically 100KB - 5MB)
- Download speed: Limited by network and storage
- Concurrent exports: Processed asynchronously

### Storage
- **Platform:** ZeroDB Object Storage
- **TTL:** 24 hours (automatic deletion)
- **Encryption:** In-transit and at-rest
- **Access:** Signed URLs with expiration

### Email Notifications
- **Provider:** Postmark
- **Template:** HTML + Plain text
- **Delivery:** Typically < 1 minute
- **Tag:** `gdpr_export`

### Audit Logging
- All export requests logged
- Includes timestamp, user ID, export ID
- IP address and user agent tracked
- Logs retained for 1 year

---

## Integration Examples

### JavaScript/TypeScript

```typescript
// Request export
async function requestDataExport(token: string) {
  const response = await fetch('https://api.wwmaa.com/api/privacy/export-data', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({})
  });

  if (!response.ok) {
    throw new Error(`Export request failed: ${response.statusText}`);
  }

  const data = await response.json();
  return data;
}

// Check export status
async function checkExportStatus(token: string, exportId: string) {
  const response = await fetch(
    `https://api.wwmaa.com/api/privacy/export-status/${exportId}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );

  if (!response.ok) {
    throw new Error(`Status check failed: ${response.statusText}`);
  }

  return await response.json();
}

// Delete export
async function deleteExport(token: string, exportId: string) {
  const response = await fetch(
    `https://api.wwmaa.com/api/privacy/export/${exportId}`,
    {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );

  if (!response.ok) {
    throw new Error(`Delete failed: ${response.statusText}`);
  }

  return await response.json();
}
```

### Python

```python
import requests

def request_data_export(token: str) -> dict:
    """Request a data export"""
    response = requests.post(
        'https://api.wwmaa.com/api/privacy/export-data',
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        },
        json={}
    )
    response.raise_for_status()
    return response.json()

def check_export_status(token: str, export_id: str) -> dict:
    """Check export status"""
    response = requests.get(
        f'https://api.wwmaa.com/api/privacy/export-status/{export_id}',
        headers={'Authorization': f'Bearer {token}'}
    )
    response.raise_for_status()
    return response.json()

def delete_export(token: str, export_id: str) -> dict:
    """Delete an export"""
    response = requests.delete(
        f'https://api.wwmaa.com/api/privacy/export/{export_id}',
        headers={'Authorization': f'Bearer {token}'}
    )
    response.raise_for_status()
    return response.json()
```

---

## Troubleshooting

### Common Issues

**1. "Not authenticated" error**
- Ensure your JWT token is valid and not expired
- Check that the token is properly formatted in the Authorization header
- Verify you're using the correct authentication endpoint

**2. "Export not found" error**
- Export may have expired (24-hour limit)
- Verify the export_id is correct
- Ensure you're checking your own exports (not another user's)

**3. "Rate limit exceeded" error**
- Wait 24 hours before requesting another export
- Check if you have a pending export request

**4. Download link doesn't work**
- Links expire after 24 hours
- Request a new export if link has expired
- Ensure you're using the exact URL provided (don't modify it)

**5. Export file is too large**
- File size depends on your activity on the platform
- Use a reliable download manager for large files
- Check your available storage space

### Getting Help

For assistance with data exports:
- **Privacy questions:** privacy@wwmaa.com
- **Technical support:** support@wwmaa.com
- **General inquiries:** info@wwmaa.com

---

## Changelog

### Version 1.0 (2025-01-10)
- Initial release
- Support for all 8 data collections
- 24-hour TTL for exports
- Email notifications
- Signed download URLs
- Comprehensive audit logging

---

## Related Documentation

- [GDPR Account Deletion API](./account-deletion-api.md)
- [Privacy Policy](./privacy-policy.md)
- [Data Retention Policy](./data-retention.md)
- [Authentication Guide](../development/authentication.md)
