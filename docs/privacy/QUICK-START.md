# GDPR Data Export - Quick Start Guide

## For Frontend Developers

### 1. Request Data Export

```typescript
async function requestDataExport(authToken: string) {
  const response = await fetch('/api/privacy/export-data', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({})
  });

  if (response.status === 202) {
    const data = await response.json();
    return data; // { export_id, status, download_url, expiry_date, ... }
  }

  throw new Error('Export request failed');
}
```

### 2. Check Export Status

```typescript
async function checkExportStatus(authToken: string, exportId: string) {
  const response = await fetch(`/api/privacy/export-status/${exportId}`, {
    headers: {
      'Authorization': `Bearer ${authToken}`
    }
  });

  return await response.json();
}
```

### 3. Delete Export (Optional)

```typescript
async function deleteExport(authToken: string, exportId: string) {
  const response = await fetch(`/api/privacy/export/${exportId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${authToken}`
    }
  });

  return await response.json();
}
```

### 4. UI Implementation Example

```tsx
import { useState } from 'react';

function DataExportSettings() {
  const [loading, setLoading] = useState(false);
  const [exportData, setExportData] = useState(null);

  const handleExportRequest = async () => {
    setLoading(true);
    try {
      const token = getAuthToken(); // Your auth token function
      const result = await requestDataExport(token);
      setExportData(result);

      // Show success message
      toast.success(
        'Your data export is ready! Check your email for the download link.'
      );
    } catch (error) {
      toast.error('Failed to generate export. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="data-export-section">
      <h2>Export Your Data</h2>
      <p>
        Download a complete copy of all your personal data in JSON format.
        You'll receive an email with a download link valid for 24 hours.
      </p>

      <button
        onClick={handleExportRequest}
        disabled={loading}
        className="btn-primary"
      >
        {loading ? 'Generating Export...' : 'Export My Data'}
      </button>

      {exportData && (
        <div className="export-info">
          <p>✅ Export Generated Successfully</p>
          <p>File Size: {(exportData.file_size_bytes / 1024).toFixed(0)} KB</p>
          <p>Expires: {new Date(exportData.expiry_date).toLocaleString()}</p>
          <a
            href={exportData.download_url}
            className="btn-secondary"
            download
          >
            Download Now
          </a>
        </div>
      )}
    </div>
  );
}
```

---

## For Backend Developers

### Testing the API

```bash
# 1. Get authentication token
TOKEN="your_jwt_token_here"

# 2. Request data export
curl -X POST http://localhost:8000/api/privacy/export-data \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'

# 3. Check export status
EXPORT_ID="export_id_from_step_2"
curl http://localhost:8000/api/privacy/export-status/$EXPORT_ID \
  -H "Authorization: Bearer $TOKEN"

# 4. Delete export (optional)
curl -X DELETE http://localhost:8000/api/privacy/export/$EXPORT_ID \
  -H "Authorization: Bearer $TOKEN"
```

### Running Tests

```bash
# Run GDPR service tests
pytest backend/tests/test_gdpr_service.py -v

# Run with coverage
pytest backend/tests/test_gdpr_service.py \
  --cov=backend/services/gdpr_service \
  --cov-report=term-missing

# Run privacy route tests
pytest backend/tests/test_privacy_routes.py -v
```

### Adding New Data Collections

To add a new collection to the export:

1. **Update GDPR Service** (`backend/services/gdpr_service.py`):

```python
COLLECTIONS = {
    "profiles": "Profile Information",
    "applications": "Membership Applications",
    # ... existing collections ...
    "your_new_collection": "Your Collection Description"  # Add here
}
```

2. **Update Filter Query Builder** (if needed):

```python
def _build_filter_query(self, collection_name: str, user_id: str) -> Dict[str, Any]:
    if collection_name == "your_new_collection":
        return {"user_id": user_id}  # Or custom filter
    # ... existing logic ...
```

3. **Add Tests**:

```python
def test_build_filter_query_for_your_collection(gdpr_service):
    query = gdpr_service._build_filter_query("your_new_collection", "user_123")
    assert query == {"user_id": "user_123"}
```

---

## Environment Setup

### Required Environment Variables

```bash
# .env file
ZERODB_API_KEY=your_zerodb_api_key
ZERODB_API_BASE_URL=https://api.ainative.studio
POSTMARK_API_KEY=your_postmark_api_key
FROM_EMAIL=noreply@wwmaa.com
JWT_SECRET=your_32_character_or_longer_secret
```

### ZeroDB Collections

Ensure these collections exist:
- `profiles`
- `applications`
- `subscriptions`
- `payments`
- `rsvps`
- `search_queries`
- `attendees`
- `audit_logs`

---

## Common Integration Patterns

### React Hook

```typescript
import { useState, useCallback } from 'react';

export function useDataExport() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [exportData, setExportData] = useState(null);

  const requestExport = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const token = getAuthToken();
      const response = await fetch('/api/privacy/export-data', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
      });

      if (!response.ok) {
        throw new Error('Export request failed');
      }

      const data = await response.json();
      setExportData(data);
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { requestExport, loading, error, exportData };
}
```

### Vue Composable

```typescript
import { ref } from 'vue';

export function useDataExport() {
  const loading = ref(false);
  const error = ref<string | null>(null);
  const exportData = ref(null);

  async function requestExport() {
    loading.value = true;
    error.value = null;

    try {
      const token = getAuthToken();
      const response = await fetch('/api/privacy/export-data', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
      });

      if (!response.ok) {
        throw new Error('Export request failed');
      }

      const data = await response.json();
      exportData.value = data;
      return data;
    } catch (err) {
      error.value = err.message;
      throw err;
    } finally {
      loading.value = false;
    }
  }

  return { requestExport, loading, error, exportData };
}
```

---

## Troubleshooting

### Export Request Returns 401

**Issue:** Not authenticated
**Solution:** Ensure valid JWT token is included in Authorization header

### Export Request Returns 500

**Issue:** Server error during export generation
**Solution:**
1. Check ZeroDB connectivity
2. Verify all collections exist
3. Check server logs for detailed error
4. Ensure user has permission to access collections

### Email Not Received

**Issue:** Export email not delivered
**Solution:**
1. Check spam folder
2. Verify Postmark API key is valid
3. Check FROM_EMAIL is configured correctly
4. Verify email address is correct in user profile

### Download Link Expired

**Issue:** "Export not found" error
**Solution:**
- Links expire after 24 hours
- Request a new export
- Cannot extend existing links

---

## Best Practices

### Frontend

1. **Show Loading State:** Always show loading indicator during export
2. **Handle Errors:** Display user-friendly error messages
3. **Email First:** Emphasize that download link will be emailed
4. **Expiry Warning:** Clearly communicate 24-hour expiry
5. **Security Notice:** Warn users about data sensitivity

### Backend

1. **Validate Input:** Always validate user authentication
2. **Error Logging:** Log all errors with context
3. **Monitor Performance:** Track export generation times
4. **Audit Everything:** Log all export requests
5. **Test Coverage:** Maintain 80%+ test coverage

### Security

1. **Authentication Required:** Never allow unauthenticated exports
2. **User Isolation:** Users can only export their own data
3. **Signed URLs:** Use signed URLs for downloads
4. **TTL Enforcement:** Strictly enforce 24-hour expiry
5. **Audit Logs:** Maintain comprehensive audit trail

---

## Quick Reference

### HTTP Status Codes

- `202 Accepted` - Export request accepted and processing
- `200 OK` - Export status/deletion successful
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - Not authorized
- `404 Not Found` - Export not found or expired
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

### Export Statuses

- `processing` - Export is being generated
- `completed` - Export is ready for download
- `expired` - Export has expired
- `not_found` - Export doesn't exist

### File Sizes

- **Typical:** 100KB - 500KB
- **Active User:** 500KB - 2MB
- **Heavy User:** 2MB - 5MB
- **Max:** ~10MB (varies by activity)

---

## Additional Resources

- [Full API Documentation](./data-export-api.md)
- [Implementation Summary](./US-072-implementation-summary.md)
- [GDPR Compliance Guide](./gdpr-compliance.md)
- [Privacy Policy](./privacy-policy.md)

---

## Support

For technical questions:
- **Backend:** Check server logs and test output
- **Frontend:** Use browser console and network tab
- **General:** Contact support@wwmaa.com
