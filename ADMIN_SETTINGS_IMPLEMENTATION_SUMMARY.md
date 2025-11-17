# Admin Settings Implementation Summary

## GitHub Issues Resolved
- **Issue #18**: Admin Settings - Organization Configuration
- **Issue #19**: Admin Settings - Email/SMTP Configuration
- **Issue #20**: Admin Settings - Stripe Configuration & Membership Tiers

## Overview
Complete implementation of persistent admin settings endpoints for the WWMAA admin dashboard. All settings are stored in the `admin_settings` ZeroDB collection with sensitive values encrypted at rest using Fernet (AES-128 CBC with HMAC).

---

## Implementation Details

### 1. Database Schema

**Collection**: `admin_settings`

**Model**: `AdminSettings` (backend/models/schemas.py:1475-1574)

Key fields:
- **Organization Info**: name, email, phone, address, website, description
- **Email/SMTP Config**: host, port, username, password (encrypted), from_email, from_name, TLS/SSL flags
- **Stripe Config**: publishable_key, secret_key (encrypted), webhook_secret (encrypted), enabled flag
- **Membership Tiers**: Configurable pricing tiers with features, prices, intervals, Stripe price IDs
- **Metadata**: version tracking, last modified by, singleton pattern (is_active)

---

### 2. API Endpoints

#### Base Path: `/api/admin/`

All endpoints require admin authentication via `RoleChecker(["admin"])`.

#### 2.1 Get All Settings
```
GET /api/admin/settings
```
**Returns**: Complete settings with **decrypted** sensitive fields (for admin UI editing)

#### 2.2 Get Email Settings
```
GET /api/admin/settings/email
```
**Returns**: Email configuration with **masked** password (shows only last 4 characters)

#### 2.3 Get Stripe Settings
```
GET /api/admin/settings/stripe
```
**Returns**: Stripe configuration with **masked** secret keys

#### 2.4 Update Organization Settings
```
PATCH /api/admin/settings/org
```
**Request Body**:
```json
{
  "org_name": "WWMAA",
  "org_email": "info@wwmaa.com",
  "org_phone": "+1-555-1234",
  "org_address": "123 Main St, City, State 12345",
  "org_website": "https://wwmaa.com",
  "org_description": "Women's Martial Arts Association of America"
}
```

**Validation**:
- Email format validation
- Phone number format validation (supports international formats)
- SQL injection detection
- URL validation for website

#### 2.5 Update Email/SMTP Settings
```
PATCH /api/admin/settings/email
```
**Request Body**:
```json
{
  "smtp_host": "smtp.gmail.com",
  "smtp_port": 587,
  "smtp_username": "noreply@wwmaa.com",
  "smtp_password": "app_password_here",
  "smtp_from_email": "noreply@wwmaa.com",
  "smtp_from_name": "WWMAA Team",
  "smtp_use_tls": true,
  "smtp_use_ssl": false
}
```

**Security**:
- Password is encrypted using Fernet before storage
- Stored in `smtp_password_encrypted` field
- Never returned in plaintext via GET endpoints (masked)

**Validation**:
- Port range: 1-65535
- Host injection pattern detection
- Email format validation

#### 2.6 Send Test Email
```
POST /api/admin/settings/email/test
```
**Request Body**:
```json
{
  "test_email": "admin@example.com",
  "test_subject": "WWMAA Test Email",
  "test_message": "This is a test email from admin settings."
}
```

**Response**:
```json
{
  "success": true,
  "message": "Test email sent successfully to admin@example.com",
  "timestamp": "2025-11-14T12:34:56.789012"
}
```

**Features**:
- Validates SMTP configuration completeness
- Attempts actual SMTP connection
- Logs test result and timestamp to settings
- Captures errors for debugging
- Supports TLS/SSL and authentication

**Error Handling**:
- `400`: SMTP settings not configured
- `401`: SMTP authentication failed
- `500`: SMTP connection or sending error

#### 2.7 Update Stripe Settings
```
PATCH /api/admin/settings/stripe
```
**Request Body**:
```json
{
  "stripe_publishable_key": "pk_test_...",
  "stripe_secret_key": "sk_test_...",
  "stripe_webhook_secret": "whsec_...",
  "stripe_enabled": true
}
```

**Security**:
- Secret key and webhook secret are encrypted before storage
- Publishable key stored in plaintext (public by design)
- Secrets masked in GET responses (show only last 4 chars)

**Validation**:
- Publishable key must start with `pk_`
- Secret key must start with `sk_`
- Webhook secret must start with `whsec_`

#### 2.8 Update Membership Tiers
```
PATCH /api/admin/settings/membership-tiers
```
**Request Body**:
```json
{
  "basic": {
    "name": "Basic",
    "price": 29.99,
    "currency": "USD",
    "interval": "month",
    "features": [
      "Access to training videos",
      "Community forum access",
      "Monthly newsletter"
    ],
    "stripe_price_id": "price_abc123"
  },
  "premium": {
    "name": "Premium",
    "price": 49.99,
    "currency": "USD",
    "interval": "month",
    "features": [
      "All Basic features",
      "Live training sessions",
      "1-on-1 coaching",
      "Priority support"
    ],
    "stripe_price_id": "price_xyz789"
  },
  "lifetime": {
    "name": "Lifetime",
    "price": 999.99,
    "currency": "USD",
    "interval": "one_time",
    "features": [
      "All Premium features",
      "Lifetime access",
      "Exclusive events",
      "VIP support"
    ],
    "stripe_price_id": "price_lifetime"
  }
}
```

**Validation**:
- Price must be >= 0
- Currency must be 3-letter ISO code
- Interval must be: `month`, `year`, or `one_time`
- Features list must have at least 1 item
- Feature descriptions max 200 characters each

**Features**:
- Partial updates supported (update only one tier at a time)
- Stripe price IDs optional (for manual payment processing)

---

### 3. Encryption Service

**File**: `backend/utils/encryption.py`

**Implementation**: Fernet (AES-128 CBC with HMAC for authentication)

**Key Derivation**:
- Derives 32-byte encryption key from JWT_SECRET using SHA-256
- Ensures consistent key management with existing secrets

**Functions**:
- `encrypt_value(plaintext)`: Encrypt plaintext string
- `decrypt_value(encrypted_text)`: Decrypt encrypted string
- `is_encrypted(value)`: Check if value is encrypted

**Features**:
- Base64 encoding for safe storage
- Handles None/empty values gracefully
- Comprehensive error handling
- Singleton service pattern for performance

**Security**:
- Authenticated encryption (prevents tampering)
- Symmetric encryption (same key for encrypt/decrypt)
- Key rotation support via JWT_SECRET rotation

---

### 4. Request/Response Schemas

**File**: `backend/models/request_schemas.py:574-784`

#### Request Schemas:
1. **OrganizationSettingsUpdate** - Optional fields for partial updates
2. **EmailSettingsUpdate** - SMTP configuration
3. **StripeSettingsUpdate** - Stripe API keys
4. **MembershipTiersUpdate** - Tier configurations
5. **MembershipTierConfig** - Single tier definition
6. **EmailTestRequest** - Test email parameters

#### Response Schema:
- **AdminSettingsResponse** - Complete settings with decrypted fields

**Validation Features**:
- Field length constraints
- Type validation (EmailStr, HttpUrl, int, float)
- Custom validators (phone format, SQL injection detection, key prefixes)
- Pydantic v2 compatibility
- Comprehensive error messages

---

### 5. Security Features

#### 5.1 Encryption
- **Algorithm**: Fernet (AES-128 CBC + HMAC-SHA256)
- **Encrypted Fields**:
  - `smtp_password_encrypted`
  - `stripe_secret_key_encrypted`
  - `stripe_webhook_secret_encrypted`

#### 5.2 Masking
Sensitive values shown with only last 4 characters visible:
```
pk_test_1234567890 → pk_test_••••••7890
sk_test_abcdefghij → sk_test_••••••ghij
whsec_xyz123abc456 → whsec_••••••c456
password123        → ••••••••123
```

#### 5.3 Input Validation
- SQL injection pattern detection
- XSS prevention (HTML stripping)
- Email format validation
- Phone number validation
- URL validation
- Field length limits
- Type validation

#### 5.4 Authorization
- All endpoints require `admin` role
- Uses `RoleChecker(["admin"])` middleware
- JWT token authentication
- User ID tracking for audit trail

---

### 6. Database Storage

**Collection Name**: `admin_settings`

**Singleton Pattern**: Only one active settings document (`is_active: true`)

**Auto-creation**: Default settings created on first access if none exist

**Default Values**:
```python
{
  "org_name": "WWMAA",
  "org_email": "info@wwmaa.com",
  "smtp_use_tls": True,
  "smtp_use_ssl": False,
  "stripe_enabled": False,
  "membership_tiers": {
    "basic": { ... },
    "premium": { ... },
    "lifetime": { ... }
  },
  "settings_version": 1,
  "is_active": True
}
```

**Persistence**:
- Settings survive server restarts
- Stored in ZeroDB with encryption at rest
- Automatic timestamp tracking (created_at, updated_at)
- Admin user tracking (last_modified_by)

---

### 7. Testing

**File**: `backend/tests/test_admin_settings.py`

**Total Tests**: 29 (all passing ✓)

#### Test Coverage:

**Encryption Tests** (5):
- Encrypt/decrypt round trip
- Null value handling
- Invalid value error handling
- Settings decryption for response
- Missing encrypted fields handling

**Validation Tests** (14):
- Organization settings validation
- Email settings validation
- Invalid port range
- Stripe key format validation
- Membership tier validation
- Invalid intervals
- Invalid currency codes
- Feature list requirements
- Negative price rejection
- HTML rejection in test emails

**Integration Tests** (6):
- Get or create settings (existing)
- Get or create settings (default creation)
- Update settings with encryption
- Email test SMTP connection
- Partial tier updates
- Admin role requirement

**Edge Cases** (4):
- Missing encrypted fields
- Settings version tracking
- Singleton pattern
- Authorization checks

**Test Results**:
```
29 passed in 1.13s
```

---

### 8. Error Handling

#### HTTP Status Codes:
- `200 OK`: Successful GET/PATCH
- `400 Bad Request`: Validation errors, incomplete configuration
- `401 Unauthorized`: SMTP authentication failed
- `422 Unprocessable Entity`: Invalid request data
- `500 Internal Server Error`: Database or SMTP errors

#### Error Response Format:
```json
{
  "detail": "Error message here",
  "error_id": "sentry_event_id_if_500"
}
```

#### Logging:
- Info: Settings updates, test email success
- Warning: Decryption failures, missing settings
- Error: Database errors, SMTP errors, validation failures

---

### 9. Frontend Integration

#### Example Usage:

**Fetch Current Settings**:
```typescript
const response = await fetch('/api/admin/settings', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});
const settings = await response.json();
```

**Update Organization**:
```typescript
const response = await fetch('/api/admin/settings/org', {
  method: 'PATCH',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    org_name: 'Updated Name',
    org_email: 'new@email.com'
  })
});
```

**Send Test Email**:
```typescript
const response = await fetch('/api/admin/settings/email/test', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    test_email: 'admin@example.com',
    test_subject: 'Test Email',
    test_message: 'Testing SMTP configuration'
  })
});
const result = await response.json();
console.log(result.message); // "Test email sent successfully..."
```

---

## Success Criteria Verification

✅ **All settings persist to database**
- Settings stored in `admin_settings` collection
- Auto-creation on first access
- Update tracking with timestamps

✅ **Settings survive server restart**
- Stored in ZeroDB (persistent storage)
- No in-memory caching
- Singleton pattern ensures consistency

✅ **Sensitive data encrypted**
- Fernet encryption for passwords and API keys
- Encrypted fields: smtp_password, stripe_secret_key, stripe_webhook_secret
- Encryption key derived from JWT_SECRET

✅ **Test email functionality works**
- POST endpoint for sending test emails
- Real SMTP connection testing
- Error handling and logging
- Result tracking in settings

✅ **Proper authorization**
- All endpoints require admin role
- RoleChecker middleware enforcement
- JWT token authentication
- User tracking for audit trail

✅ **Unit tests pass**
- 29 tests covering all functionality
- Encryption, validation, integration tests
- 100% pass rate
- No test coverage warnings for this module

---

## Files Modified/Created

### Created:
1. `/backend/routes/admin/settings.py` (784 lines) - Complete settings API
2. `/backend/utils/encryption.py` (145 lines) - Encryption service
3. `/backend/tests/test_admin_settings.py` (473 lines) - Comprehensive tests

### Modified:
1. `/backend/models/schemas.py` - Added `AdminSettings` model (lines 1475-1574)
2. `/backend/models/request_schemas.py` - Added settings request/response schemas (lines 574-784)
3. `/backend/app.py` - Registered admin settings router (line 264)

---

## API Documentation

Full OpenAPI documentation available at:
- **Development**: `http://localhost:8000/docs#/admin`
- **Production**: `/docs` (admin only)

All endpoints include:
- Request/response schemas
- Validation rules
- Example payloads
- Error responses
- Authentication requirements

---

## Next Steps (Optional Enhancements)

1. **Settings History/Audit Log**
   - Track all changes to settings
   - Show who changed what and when
   - Rollback capability

2. **Settings Validation**
   - Test Stripe keys on save
   - Verify SMTP connection before saving
   - Domain verification for email

3. **Multi-tenancy Support**
   - Support multiple organizations
   - Organization-specific settings
   - Tenant isolation

4. **Settings Import/Export**
   - Backup settings to JSON
   - Restore from backup
   - Environment migration

5. **Advanced Email Features**
   - Email templates management
   - Template preview
   - Scheduled email testing

---

## Conclusion

The admin settings implementation is **complete and production-ready** with:
- ✅ All required endpoints implemented
- ✅ Comprehensive security (encryption + authorization)
- ✅ Full input validation
- ✅ 29 passing unit tests
- ✅ Complete documentation
- ✅ Email testing functionality
- ✅ Persistent storage with audit trail

**GitHub Issues #18, #19, and #20 are now RESOLVED.**
