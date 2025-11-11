"""
Enhanced Input Validation Utilities (US-070)

This module provides comprehensive input validation and sanitization utilities
to prevent injection attacks, XSS, path traversal, and other security vulnerabilities.

Security Features:
- Email validation with DNS checks
- Phone number validation (E.164 format)
- URL validation with domain whitelisting
- Username/alphanumeric validation
- Password strength validation
- HTML sanitization (XSS prevention)
- SQL keyword detection (paranoid check)
- Path traversal prevention
- Command injection prevention
"""

import re
import hashlib
import ipaddress
from typing import Optional, List, Set
from urllib.parse import urlparse
from pydantic import EmailStr, HttpUrl, validator

# Import dnspython if available (optional dependency for DNS checks)
try:
    import dns.resolver
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False


# ============================================================================
# CONSTANTS - Whitelists, Patterns, and Limits
# ============================================================================

# Allowed HTML tags for rich text content (blog posts, event descriptions)
ALLOWED_HTML_TAGS = ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'a', 'h1', 'h2', 'h3', 'h4', 'blockquote', 'code', 'pre']
ALLOWED_HTML_ATTRIBUTES = {
    'a': ['href', 'title', 'target'],
    'blockquote': ['cite'],
    'code': ['class'],
}

# Allowed URL schemes
ALLOWED_URL_SCHEMES = ['http', 'https']

# Allowed domains for URLs (add more as needed)
ALLOWED_DOMAINS = [
    'wwmaa.com',
    'youtube.com',
    'youtu.be',
    'vimeo.com',
    'twitter.com',
    'facebook.com',
    'instagram.com',
    'linkedin.com',
]

# SQL keywords to detect (paranoid check - ZeroDB uses parameterized queries)
SQL_KEYWORDS = {
    'select', 'insert', 'update', 'delete', 'drop', 'create', 'alter', 'exec', 'execute',
    'union', 'script', 'javascript', 'onload', 'onerror', 'eval', 'expression',
    'from', 'where', 'having', 'group by', 'order by', '--', ';--', '/*', '*/',
    'xp_', 'sp_', 'shutdown', 'truncate', 'grant', 'revoke',
}

# Dangerous file extensions
DANGEROUS_FILE_EXTENSIONS = {
    'exe', 'bat', 'cmd', 'com', 'pif', 'scr', 'vbs', 'js', 'jar', 'sh', 'bash',
    'ps1', 'dll', 'sys', 'msi', 'app', 'deb', 'rpm', 'dmg', 'pkg',
}

# Username validation pattern (alphanumeric + underscore/hyphen)
USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{3,30}$')

# Phone number pattern (E.164 format: +1234567890)
# Must start with + and have 7-15 digits total
PHONE_PATTERN = re.compile(r'^\+[1-9]\d{6,14}$')

# Password requirements
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128


# ============================================================================
# EMAIL VALIDATION
# ============================================================================

def validate_email(email: str, check_dns: bool = False) -> bool:
    """
    Validate email address with optional DNS check

    Args:
        email: Email address to validate
        check_dns: Whether to perform DNS MX record check

    Returns:
        True if email is valid, False otherwise

    Example:
        >>> validate_email("user@example.com")
        True
        >>> validate_email("invalid@")
        False
    """
    # Basic format validation using EmailStr
    try:
        # Pydantic's EmailStr performs RFC 5322 validation
        from pydantic import EmailStr
        EmailStr._validate(email)
    except Exception:
        return False

    # Optional DNS check (requires dnspython)
    if check_dns and DNS_AVAILABLE:
        try:
            domain = email.split('@')[1]
            dns.resolver.resolve(domain, 'MX')
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout):
            return False
        except Exception:
            # DNS check failed, but email format is valid
            pass

    return True


def validate_email_or_raise(email: str, check_dns: bool = False) -> str:
    """
    Validate email and raise ValueError if invalid

    Args:
        email: Email address to validate
        check_dns: Whether to perform DNS MX record check

    Returns:
        Lowercase email address

    Raises:
        ValueError: If email is invalid
    """
    if not validate_email(email, check_dns):
        raise ValueError(f"Invalid email address: {email}")
    return email.lower()


# ============================================================================
# PHONE NUMBER VALIDATION
# ============================================================================

def validate_phone_number(phone: str, country_code: Optional[str] = None) -> bool:
    """
    Validate phone number in E.164 format

    Args:
        phone: Phone number (e.g., "+12025551234")
        country_code: Optional country code for validation (e.g., "US")

    Returns:
        True if phone number is valid, False otherwise

    Example:
        >>> validate_phone_number("+12025551234")
        True
        >>> validate_phone_number("123")
        False
    """
    if not phone or len(phone) < 3:
        return False

    # Remove whitespace and common separators
    cleaned = re.sub(r'[\s\-\(\)\.]', '', phone)

    # Check E.164 format
    if not PHONE_PATTERN.match(cleaned):
        return False

    # Country-specific validation (basic)
    if country_code == "US":
        # US numbers: +1 followed by 10 digits
        return cleaned.startswith('+1') and len(cleaned) == 12

    return True


def normalize_phone_number(phone: str) -> str:
    """
    Normalize phone number to E.164 format

    Args:
        phone: Phone number in any format

    Returns:
        Normalized phone number in E.164 format

    Example:
        >>> normalize_phone_number("(202) 555-1234")
        "+12025551234"
    """
    # Remove all non-digit characters except leading +
    cleaned = re.sub(r'[^\d+]', '', phone)

    # Add + if missing
    if not cleaned.startswith('+'):
        # Assume US country code if not provided
        if len(cleaned) == 10:
            cleaned = '+1' + cleaned
        elif len(cleaned) == 11 and cleaned.startswith('1'):
            cleaned = '+' + cleaned
        else:
            cleaned = '+' + cleaned

    return cleaned


# ============================================================================
# URL VALIDATION
# ============================================================================

def validate_url(url: str, allowed_schemes: Optional[List[str]] = None,
                 allowed_domains: Optional[List[str]] = None) -> bool:
    """
    Validate URL with scheme and domain whitelisting

    Args:
        url: URL to validate
        allowed_schemes: List of allowed schemes (default: http, https)
        allowed_domains: List of allowed domains (optional)

    Returns:
        True if URL is valid and allowed, False otherwise

    Example:
        >>> validate_url("https://wwmaa.com/events")
        True
        >>> validate_url("javascript:alert('xss')")
        False
    """
    if allowed_schemes is None:
        allowed_schemes = ALLOWED_URL_SCHEMES

    try:
        parsed = urlparse(url)

        # Check scheme
        if parsed.scheme not in allowed_schemes:
            return False

        # Check domain whitelist if provided
        if allowed_domains:
            domain = parsed.netloc.lower()
            # Remove port if present
            domain = domain.split(':')[0]

            # Check if domain or any parent domain is in whitelist
            domain_allowed = False
            for allowed_domain in allowed_domains:
                if domain == allowed_domain or domain.endswith('.' + allowed_domain):
                    domain_allowed = True
                    break

            if not domain_allowed:
                return False

        return True

    except Exception:
        return False


def sanitize_url(url: str, allowed_schemes: Optional[List[str]] = None) -> Optional[str]:
    """
    Sanitize URL by removing dangerous schemes and normalizing

    Args:
        url: URL to sanitize
        allowed_schemes: List of allowed schemes

    Returns:
        Sanitized URL or None if invalid
    """
    if not validate_url(url, allowed_schemes):
        return None

    try:
        parsed = urlparse(url)
        # Reconstruct URL with only safe components
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    except Exception:
        return None


# ============================================================================
# USERNAME VALIDATION
# ============================================================================

def validate_username(username: str, min_length: int = 3, max_length: int = 30) -> bool:
    """
    Validate username (alphanumeric + underscore/hyphen only)

    Args:
        username: Username to validate
        min_length: Minimum length (default: 3)
        max_length: Maximum length (default: 30)

    Returns:
        True if username is valid, False otherwise

    Example:
        >>> validate_username("john_doe")
        True
        >>> validate_username("john@doe")
        False
    """
    if not username or len(username) < min_length or len(username) > max_length:
        return False

    # Check pattern
    pattern = re.compile(f'^[a-zA-Z0-9_-]{{{min_length},{max_length}}}$')
    return bool(pattern.match(username))


def sanitize_username(username: str) -> str:
    """
    Sanitize username by removing invalid characters

    Args:
        username: Username to sanitize

    Returns:
        Sanitized username (alphanumeric + underscore/hyphen only)
    """
    # Remove all characters except alphanumeric, underscore, and hyphen
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '', username)
    return sanitized[:30]  # Limit to max length


# ============================================================================
# PASSWORD VALIDATION
# ============================================================================

def validate_password_strength(password: str) -> tuple[bool, List[str]]:
    """
    Validate password strength

    Requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character (optional but recommended)

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid, error_messages)

    Example:
        >>> validate_password_strength("Password123!")
        (True, [])
        >>> validate_password_strength("weak")
        (False, ["Password must be at least 8 characters", ...])
    """
    errors = []

    # Length check
    if len(password) < PASSWORD_MIN_LENGTH:
        errors.append(f"Password must be at least {PASSWORD_MIN_LENGTH} characters")
    if len(password) > PASSWORD_MAX_LENGTH:
        errors.append(f"Password must not exceed {PASSWORD_MAX_LENGTH} characters")

    # Uppercase check
    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")

    # Lowercase check
    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")

    # Digit check
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit")

    # Special character check (recommended)
    special_chars = r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]'
    if not re.search(special_chars, password):
        errors.append("Password should contain at least one special character")

    return (len(errors) == 0, errors)


# ============================================================================
# HTML SANITIZATION (XSS PREVENTION)
# ============================================================================

def sanitize_html(content: str, allowed_tags: Optional[List[str]] = None,
                  allowed_attributes: Optional[dict] = None,
                  strip: bool = True) -> str:
    """
    Sanitize HTML content to prevent XSS attacks

    Uses bleach library to clean HTML by:
    - Removing disallowed tags
    - Removing JavaScript and event handlers
    - Whitelisting safe tags and attributes

    Args:
        content: HTML content to sanitize
        allowed_tags: List of allowed HTML tags
        allowed_attributes: Dict of allowed attributes per tag
        strip: Whether to strip disallowed tags (vs escaping)

    Returns:
        Sanitized HTML content

    Example:
        >>> sanitize_html('<p>Safe</p><script>alert("XSS")</script>')
        '<p>Safe</p>'
    """
    try:
        import bleach

        if allowed_tags is None:
            allowed_tags = ALLOWED_HTML_TAGS
        if allowed_attributes is None:
            allowed_attributes = ALLOWED_HTML_ATTRIBUTES

        # Clean HTML
        cleaned = bleach.clean(
            content,
            tags=allowed_tags,
            attributes=allowed_attributes,
            strip=strip,
            strip_comments=True,
        )

        # Linkify URLs (convert plain text URLs to links)
        # cleaned = bleach.linkify(cleaned, skip_tags=['pre', 'code'])

        return cleaned
    except ImportError:
        # If bleach not available, do basic HTML escaping
        import html
        return html.escape(content)


def strip_html(content: str) -> str:
    """
    Strip all HTML tags from content

    Args:
        content: HTML content

    Returns:
        Plain text content without HTML tags
    """
    try:
        import bleach
        return bleach.clean(content, tags=[], strip=True)
    except ImportError:
        # If bleach not available, use basic regex stripping
        return re.sub(r'<[^>]+>', '', content)


# ============================================================================
# SQL INJECTION DETECTION (PARANOID CHECK)
# ============================================================================

def detect_sql_injection(input_string: str, strict: bool = False) -> bool:
    """
    Detect potential SQL injection attempts (paranoid check)

    Note: ZeroDB uses parameterized queries, so this is a paranoid check
    for additional security layer. Not a replacement for proper query parameterization.

    Args:
        input_string: Input string to check
        strict: Whether to use strict checking (more false positives)

    Returns:
        True if potential SQL injection detected, False otherwise

    Example:
        >>> detect_sql_injection("'; DROP TABLE users; --")
        True
        >>> detect_sql_injection("normal input")
        False
    """
    if not input_string:
        return False

    # Convert to lowercase for case-insensitive matching
    lower_input = input_string.lower()

    # Check for SQL keywords
    for keyword in SQL_KEYWORDS:
        if keyword in lower_input:
            # In strict mode, flag any SQL keyword
            if strict:
                return True

            # In normal mode, check for suspicious patterns
            # Allow keywords in normal text (e.g., "select a date")
            # Flag keywords followed by typical SQL syntax
            if re.search(rf'\b{keyword}\b.*[\*;\-]', lower_input):
                return True

    # Check for common SQL injection patterns
    sql_patterns = [
        r"'.*or.*'.*=.*'",  # ' OR '1'='1
        r'".*or.*".*=.*"',  # " OR "1"="1
        r";\s*drop\s+table",  # ; DROP TABLE
        r";\s*delete\s+from",  # ; DELETE FROM
        r"union.*select",  # UNION SELECT
        r"/\*.*\*/",  # /* comment */
        r"--",  # SQL comment
        r"xp_cmdshell",  # SQL Server command execution
    ]

    for pattern in sql_patterns:
        if re.search(pattern, lower_input, re.IGNORECASE):
            return True

    return False


# ============================================================================
# ALPHANUMERIC VALIDATION
# ============================================================================

def validate_alphanumeric(value: str, allow_spaces: bool = False,
                          allow_underscore: bool = False,
                          allow_hyphen: bool = False) -> bool:
    """
    Validate that string contains only alphanumeric characters

    Args:
        value: String to validate
        allow_spaces: Whether to allow spaces
        allow_underscore: Whether to allow underscores
        allow_hyphen: Whether to allow hyphens

    Returns:
        True if valid, False otherwise
    """
    if not value:
        return False

    # Build pattern
    pattern = r'^[a-zA-Z0-9'
    if allow_spaces:
        pattern += r'\s'
    if allow_underscore:
        pattern += '_'
    if allow_hyphen:
        pattern += '-'
    pattern += r']+$'

    return bool(re.match(pattern, value))


# ============================================================================
# IP ADDRESS VALIDATION
# ============================================================================

def validate_ip_address(ip: str) -> bool:
    """
    Validate IP address (IPv4 or IPv6)

    Args:
        ip: IP address to validate

    Returns:
        True if valid IP address, False otherwise
    """
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def hash_ip_address(ip: str) -> str:
    """
    Hash IP address for privacy-preserving storage

    Args:
        ip: IP address to hash

    Returns:
        SHA256 hash of IP address
    """
    return hashlib.sha256(ip.encode()).hexdigest()


# ============================================================================
# FILE EXTENSION VALIDATION
# ============================================================================

def validate_file_extension(filename: str, allowed_extensions: Set[str]) -> bool:
    """
    Validate file extension against whitelist

    Args:
        filename: Filename to validate
        allowed_extensions: Set of allowed extensions (without dot, e.g., {'jpg', 'png'})

    Returns:
        True if extension is allowed, False otherwise
    """
    if not filename or '.' not in filename:
        return False

    ext = filename.rsplit('.', 1)[1].lower()
    return ext in allowed_extensions


def is_dangerous_file(filename: str) -> bool:
    """
    Check if file has a dangerous extension

    Args:
        filename: Filename to check

    Returns:
        True if file has dangerous extension, False otherwise
    """
    if not filename or '.' not in filename:
        return False

    ext = filename.rsplit('.', 1)[1].lower()
    return ext in DANGEROUS_FILE_EXTENSIONS


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize filename by removing special characters and limiting length

    Args:
        filename: Filename to sanitize
        max_length: Maximum filename length

    Returns:
        Sanitized filename
    """
    # Remove path components (prevent directory traversal)
    filename = filename.split('/')[-1].split('\\')[-1]

    # Remove special characters except dot, underscore, hyphen
    sanitized = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)

    # Limit length
    if len(sanitized) > max_length:
        # Keep extension if present
        if '.' in sanitized:
            name, ext = sanitized.rsplit('.', 1)
            max_name_length = max_length - len(ext) - 1
            sanitized = name[:max_name_length] + '.' + ext
        else:
            sanitized = sanitized[:max_length]

    return sanitized


# ============================================================================
# COMMAND INJECTION DETECTION
# ============================================================================

def detect_command_injection(input_string: str) -> bool:
    """
    Detect potential command injection attempts

    Args:
        input_string: Input string to check

    Returns:
        True if potential command injection detected, False otherwise
    """
    if not input_string:
        return False

    # Check for shell metacharacters and dangerous patterns
    dangerous_patterns = [
        r';',  # Command separator
        r'\|',  # Pipe
        r'&',  # Background execution
        r'\$\(',  # Command substitution
        r'`',  # Backtick command substitution
        r'\n',  # Newline (command separator)
        r'>',  # Redirect
        r'<',  # Redirect
        r'\.\.',  # Parent directory
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, input_string):
            return True

    return False


# ============================================================================
# DATE VALIDATION
# ============================================================================

def validate_date_not_future(date_str: str, field_name: str = "date") -> bool:
    """
    Validate that date is not in the future (for birthdates, past events)

    Args:
        date_str: Date string in ISO format
        field_name: Name of field for error message

    Returns:
        True if date is valid and not in future, False otherwise
    """
    from datetime import datetime, timezone

    try:
        date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)

        if date > now:
            return False
        return True
    except Exception:
        return False


def validate_date_range(start_date: str, end_date: str) -> bool:
    """
    Validate that end date is after start date

    Args:
        start_date: Start date in ISO format
        end_date: End date in ISO format

    Returns:
        True if range is valid, False otherwise
    """
    from datetime import datetime

    try:
        start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        return end > start
    except Exception:
        return False
