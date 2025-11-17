# Admin Settings API Reference

Quick reference guide for admin settings endpoints.

---

## Authentication

All endpoints require admin authentication:

```
Authorization: Bearer <admin_jwt_token>
```

---

## Endpoints

### 1. Get All Settings

```http
GET /api/admin/settings
```

**Response**: Complete settings with decrypted sensitive fields

```json
{
  "id": "uuid",
  "created_at": "2025-11-14T12:00:00",
  "updated_at": "2025-11-14T12:30:00",
  "org_name": "WWMAA",
  "org_email": "info@wwmaa.com",
  "org_phone": "+1-555-1234",
  "org_address": "123 Main St, City, State",
  "org_website": "https://wwmaa.com",
  "org_description": "Organization description",
  "smtp_host": "smtp.gmail.com",
  "smtp_port": 587,
  "smtp_username": "noreply@wwmaa.com",
  "smtp_password": "decrypted_password",
  "smtp_from_email": "noreply@wwmaa.com",
  "smtp_from_name": "WWMAA Team",
  "smtp_use_tls": true,
  "smtp_use_ssl": false,
  "stripe_publishable_key": "pk_live_...",
  "stripe_secret_key": "sk_live_...",
  "stripe_webhook_secret": "whsec_...",
  "stripe_enabled": true,
  "membership_tiers": { ... },
  "settings_version": 1
}
```

---

### 2. Get Email Settings (Masked)

```http
GET /api/admin/settings/email
```

**Response**: Email settings with masked password

```json
{
  "smtp_host": "smtp.gmail.com",
  "smtp_port": 587,
  "smtp_username": "noreply@wwmaa.com",
  "smtp_password": "••••••••word",
  "smtp_from_email": "noreply@wwmaa.com",
  "smtp_from_name": "WWMAA Team",
  "smtp_use_tls": true,
  "smtp_use_ssl": false,
  "last_email_test_at": "2025-11-14T12:00:00",
  "last_email_test_result": "success",
  "last_email_test_error": null
}
```

---

### 3. Get Stripe Settings (Masked)

```http
GET /api/admin/settings/stripe
```

**Response**: Stripe settings with masked secrets

```json
{
  "stripe_publishable_key": "pk_live_1234567890",
  "stripe_secret_key": "sk_live_••••••7890",
  "stripe_webhook_secret": "whsec_••••••c456",
  "stripe_enabled": true
}
```

---

### 4. Update Organization Settings

```http
PATCH /api/admin/settings/org
```

**Request Body** (all fields optional):

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
- `org_name`: 1-200 characters
- `org_email`: Valid email format
- `org_phone`: Valid phone format (international supported)
- `org_address`: Max 500 characters
- `org_website`: Valid URL
- `org_description`: Max 2000 characters

**Response**: Full settings object

---

### 5. Update Email/SMTP Settings

```http
PATCH /api/admin/settings/email
```

**Request Body** (all fields optional):

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

**Validation**:
- `smtp_host`: Max 255 characters, no SQL injection
- `smtp_port`: 1-65535
- `smtp_username`: Max 255 characters
- `smtp_password`: Max 255 characters (encrypted before storage)
- `smtp_from_email`: Valid email format
- `smtp_from_name`: Max 200 characters
- `smtp_use_tls`: Boolean
- `smtp_use_ssl`: Boolean

**Security**: Password is encrypted using Fernet before storage

**Response**: Full settings object

---

### 6. Send Test Email

```http
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

**Validation**:
- `test_email`: Valid email format (required)
- `test_subject`: Max 200 characters, no HTML
- `test_message`: Max 1000 characters, no HTML

**Success Response**:

```json
{
  "success": true,
  "message": "Test email sent successfully to admin@example.com",
  "timestamp": "2025-11-14T12:34:56.789012"
}
```

**Error Responses**:

```json
// SMTP not configured
{
  "detail": "SMTP settings are not fully configured. Please configure SMTP host, port, and from email."
}

// Authentication failed
{
  "detail": "SMTP authentication failed: (535, b'5.7.8 Username and Password not accepted')"
}

// Connection error
{
  "detail": "SMTP error: [Errno 61] Connection refused"
}
```

**Notes**:
- Requires `smtp_host`, `smtp_port`, and `smtp_from_email` to be configured
- Actually sends email to test SMTP connection
- Logs result in settings (`last_email_test_at`, `last_email_test_result`, `last_email_test_error`)

---

### 7. Update Stripe Settings

```http
PATCH /api/admin/settings/stripe
```

**Request Body** (all fields optional):

```json
{
  "stripe_publishable_key": "pk_test_1234567890",
  "stripe_secret_key": "sk_test_abcdefghij",
  "stripe_webhook_secret": "whsec_test_xyz123",
  "stripe_enabled": true
}
```

**Validation**:
- `stripe_publishable_key`: Must start with `pk_`
- `stripe_secret_key`: Must start with `sk_`
- `stripe_webhook_secret`: Must start with `whsec_`
- `stripe_enabled`: Boolean

**Security**:
- `stripe_secret_key` encrypted before storage
- `stripe_webhook_secret` encrypted before storage
- Publishable key stored in plaintext (public by design)

**Response**: Full settings object

---

### 8. Update Membership Tiers

```http
PATCH /api/admin/settings/membership-tiers
```

**Request Body** (partial updates supported):

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
    "stripe_price_id": "price_basic_monthly"
  },
  "premium": {
    "name": "Premium",
    "price": 49.99,
    "currency": "USD",
    "interval": "month",
    "features": [
      "All Basic features",
      "Live training sessions",
      "1-on-1 coaching sessions",
      "Advanced techniques library",
      "Priority support"
    ],
    "stripe_price_id": "price_premium_monthly"
  },
  "lifetime": {
    "name": "Lifetime",
    "price": 999.99,
    "currency": "USD",
    "interval": "one_time",
    "features": [
      "All Premium features",
      "Lifetime access",
      "Exclusive events access",
      "Certification programs",
      "VIP support"
    ],
    "stripe_price_id": "price_lifetime"
  }
}
```

**Tier Configuration**:
- `name`: 1-100 characters (required)
- `price`: >= 0 (required)
- `currency`: 3-letter ISO code (required, default: "USD")
- `interval`: "month", "year", or "one_time" (required)
- `features`: Array of strings, min 1 item (required)
- `stripe_price_id`: Max 200 characters (optional)

**Validation**:
- Price cannot be negative
- Currency must be 3 characters
- Interval must be valid value
- At least one feature required
- Each feature max 200 characters

**Response**: Full settings object

---

## Error Responses

All endpoints return errors in this format:

```json
{
  "detail": "Error message here"
}
```

### HTTP Status Codes:

- `200 OK`: Success
- `400 Bad Request`: Validation error or incomplete configuration
- `401 Unauthorized`: Authentication failed or invalid token
- `403 Forbidden`: Not admin role
- `422 Unprocessable Entity`: Invalid request data
- `500 Internal Server Error`: Server error

---

## cURL Examples

### Get Settings

```bash
curl -X GET "http://localhost:8000/api/admin/settings" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Update Organization

```bash
curl -X PATCH "http://localhost:8000/api/admin/settings/org" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "org_name": "WWMAA",
    "org_email": "info@wwmaa.com"
  }'
```

### Update Email Settings

```bash
curl -X PATCH "http://localhost:8000/api/admin/settings/email" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_username": "noreply@wwmaa.com",
    "smtp_password": "app_password",
    "smtp_from_email": "noreply@wwmaa.com",
    "smtp_use_tls": true
  }'
```

### Send Test Email

```bash
curl -X POST "http://localhost:8000/api/admin/settings/email/test" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "test_email": "admin@example.com",
    "test_subject": "Test Email",
    "test_message": "Testing SMTP configuration"
  }'
```

### Update Stripe Settings

```bash
curl -X PATCH "http://localhost:8000/api/admin/settings/stripe" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "stripe_publishable_key": "pk_test_1234",
    "stripe_secret_key": "sk_test_5678",
    "stripe_webhook_secret": "whsec_9012",
    "stripe_enabled": true
  }'
```

### Update Membership Tier

```bash
curl -X PATCH "http://localhost:8000/api/admin/settings/membership-tiers" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "premium": {
      "name": "Premium",
      "price": 59.99,
      "currency": "USD",
      "interval": "month",
      "features": ["Feature 1", "Feature 2"]
    }
  }'
```

---

## TypeScript/JavaScript Examples

### Fetch Settings

```typescript
const response = await fetch('/api/admin/settings', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});
const settings = await response.json();
```

### Update and Handle Errors

```typescript
try {
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

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }

  const settings = await response.json();
  console.log('Updated:', settings);
} catch (error) {
  console.error('Failed to update:', error.message);
}
```

---

## Notes

1. **Encryption**: Sensitive fields (passwords, secret keys) are encrypted at rest using Fernet (AES-128 CBC + HMAC)

2. **Masking**: GET endpoints for specific settings return masked values (show only last 4 chars)

3. **Partial Updates**: All PATCH endpoints support partial updates - only send fields you want to change

4. **Validation**: All inputs are validated before processing (format, length, SQL injection, etc.)

5. **Persistence**: Settings survive server restarts (stored in ZeroDB)

6. **Singleton**: Only one active settings document per system

7. **Audit Trail**: Tracks `last_modified_by` and update timestamps

8. **Test Email**: Actually sends an email to verify SMTP configuration

---

## Common Issues

### "SMTP settings are not fully configured"
- Ensure `smtp_host`, `smtp_port`, and `smtp_from_email` are set before sending test email

### "SMTP authentication failed"
- Check username and password are correct
- For Gmail, use App Password, not account password
- Verify 2FA is enabled and App Password is generated

### "Stripe publishable key must start with 'pk_'"
- Verify you're using the correct Stripe key format
- Test keys: `pk_test_...`, Live keys: `pk_live_...`

### "401 Unauthorized"
- Ensure you have a valid admin JWT token
- Check token hasn't expired
- Verify user has admin role

---

## Security Best Practices

1. **Never log sensitive values** (passwords, API keys)
2. **Use HTTPS in production** to protect tokens in transit
3. **Rotate JWT secrets regularly**
4. **Use Stripe test keys during development**
5. **Enable 2FA for Gmail SMTP** and use App Passwords
6. **Restrict admin access** to trusted users only
7. **Monitor settings changes** via audit logs

---

For full API documentation, visit `/docs` when running the backend server.
