# Backend Utilities - Security & Validation

This directory contains utility modules for input validation, file handling, and security operations.

## Modules

### `validation.py` - Input Validation & Sanitization

Comprehensive input validation utilities to prevent injection attacks and ensure data integrity.

**Key Functions:**
- `validate_email()` - Email validation with optional DNS checks
- `validate_phone_number()` - E.164 phone number validation
- `validate_url()` - URL validation with scheme/domain whitelisting
- `validate_username()` - Username validation (alphanumeric + _-)
- `validate_password_strength()` - Strong password requirements
- `sanitize_html()` - XSS prevention via HTML cleaning
- `detect_sql_injection()` - Paranoid SQL injection detection
- `detect_command_injection()` - Command injection detection
- `validate_ip_address()` - IP address validation
- `sanitize_filename()` - Filename sanitization

**Usage Example:**
```python
from backend.utils.validation import validate_email, sanitize_html

# Email validation
if validate_email("user@example.com", check_dns=True):
    # Email is valid and domain has MX records
    pass

# HTML sanitization (XSS prevention)
clean_html = sanitize_html(user_content)
```

### `file_upload.py` - File Upload Validation

Secure file upload validation to prevent malicious file uploads.

**Key Functions:**
- `validate_image_upload()` - Comprehensive image validation
- `validate_video_upload()` - Video file validation
- `validate_document_upload()` - Document file validation
- `validate_avatar_upload()` - Avatar/profile picture validation
- `verify_magic_bytes()` - File type verification via magic bytes
- `sanitize_upload_filename()` - Secure filename sanitization

**Features:**
- Extension whitelisting
- MIME type validation
- Magic bytes verification (actual file type)
- File size limits
- Content scanning

**Usage Example:**
```python
from backend.utils.file_upload import validate_image_upload

is_valid, error = validate_image_upload(uploaded_file)
if not is_valid:
    raise HTTPException(status_code=400, detail=error)
```

### `security.py` - Security Utilities

Security utilities for path validation, subprocess execution, and cryptographic operations.

**Key Functions:**
- `is_safe_path()` - Path traversal prevention
- `safe_join_path()` - Safe path joining with boundary checks
- `safe_subprocess_run()` - Safe subprocess execution (no shell=True)
- `add_security_headers()` - Add security headers to responses
- `get_client_ip()` - Extract client IP from request
- `generate_secure_token()` - Cryptographically secure token generation
- `hash_sensitive_data()` - Privacy-preserving data hashing
- `constant_time_compare()` - Timing attack prevention

**Usage Example:**
```python
from backend.utils.security import is_safe_path, safe_subprocess_run

# Path traversal prevention
if not is_safe_path(user_path, UPLOADS_DIR):
    raise ValueError("Invalid path")

# Safe subprocess execution
safe_subprocess_run(["/usr/bin/convert", input_file, output_file])
```

## Security Features

### SQL Injection Prevention
- Parameterized queries (ZeroDB)
- SQL keyword detection (paranoid check)
- Input validation with Pydantic

### XSS Prevention
- HTML sanitization with bleach
- Whitelist of allowed HTML tags
- Content Security Policy headers

### Path Traversal Prevention
- Path boundary validation
- Symlink resolution
- Safe path joining

### Command Injection Prevention
- No `shell=True` usage
- Command whitelisting
- Argument validation

### File Upload Security
- Extension whitelisting
- MIME type validation
- Magic bytes verification
- Size limits
- Content scanning

## Dependencies

**Required:**
- `pydantic` - Data validation

**Optional:**
- `bleach` - HTML sanitization (XSS prevention)
- `python-magic` - File type detection (magic bytes)
- `dnspython` - DNS checks for email validation

If optional dependencies are not installed, the utilities will fall back to basic validation methods.

## Testing

Run the security test suite:

```bash
pytest backend/tests/test_input_validation.py -v
```

Run fuzzing tests:

```bash
python backend/scripts/fuzz_test.py --target http://localhost:8000
```

## Documentation

See `/docs/security/` for comprehensive security documentation:
- `input-validation-guide.md` - Input validation best practices
- `security-checklist.md` - Pre-deployment security checklist
- `dependencies.md` - Security dependencies documentation

## Security Standards

These utilities help achieve compliance with:
- OWASP Top 10 (2021)
- SANS Top 25 Most Dangerous Software Errors
- CWE/SANS Top 25
- NIST Cybersecurity Framework

## Support

For security issues, contact: security@wwmaa.com
