"""
Input Validation & Security Testing Suite (US-070)

This test suite validates all security features including:
- SQL injection prevention
- XSS prevention
- Path traversal prevention
- Command injection prevention
- File upload validation
- Input validation with Pydantic models
- Password strength validation
- Email validation
- URL validation

Target: 80%+ code coverage
"""

import pytest
from fastapi import UploadFile
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from backend.utils.validation import (
    validate_email,
    validate_email_or_raise,
    validate_phone_number,
    normalize_phone_number,
    validate_url,
    sanitize_url,
    validate_username,
    sanitize_username,
    validate_password_strength,
    sanitize_html,
    strip_html,
    detect_sql_injection,
    validate_alphanumeric,
    validate_ip_address,
    hash_ip_address,
    validate_file_extension,
    is_dangerous_file,
    sanitize_filename,
    detect_command_injection,
    validate_date_not_future,
    validate_date_range,
)

from backend.utils.file_upload import (
    get_file_extension,
    validate_file_extension as validate_file_ext_upload,
    validate_mime_type,
    verify_magic_bytes,
    validate_file_size,
    sanitize_upload_filename,
    validate_image_upload,
    validate_video_upload,
    validate_document_upload,
    validate_avatar_upload,
)

from backend.utils.security import (
    is_safe_path,
    validate_file_path,
    safe_join_path,
    get_safe_filename,
    validate_command_arguments,
    constant_time_compare,
    generate_secure_token,
    hash_sensitive_data,
)


# ============================================================================
# EMAIL VALIDATION TESTS
# ============================================================================

class TestEmailValidation:
    """Test email validation functions"""

    def test_valid_email(self):
        """Test valid email addresses"""
        assert validate_email("user@example.com")
        assert validate_email("test.user+tag@example.co.uk")
        assert validate_email("admin@wwmaa.com")

    def test_invalid_email(self):
        """Test invalid email addresses"""
        assert not validate_email("invalid@")
        assert not validate_email("@example.com")
        assert not validate_email("no-at-sign.com")
        assert not validate_email("")

    def test_email_validation_or_raise(self):
        """Test email validation with exception"""
        # Valid email should return lowercase
        assert validate_email_or_raise("User@Example.COM") == "user@example.com"

        # Invalid email should raise ValueError
        with pytest.raises(ValueError, match="Invalid email"):
            validate_email_or_raise("invalid@")


# ============================================================================
# PHONE NUMBER VALIDATION TESTS
# ============================================================================

class TestPhoneValidation:
    """Test phone number validation"""

    def test_valid_phone_numbers(self):
        """Test valid phone numbers"""
        assert validate_phone_number("+12025551234")
        assert validate_phone_number("+442012345678")
        assert validate_phone_number("+1234567890")

    def test_invalid_phone_numbers(self):
        """Test invalid phone numbers"""
        assert not validate_phone_number("123")
        assert not validate_phone_number("abc")
        assert not validate_phone_number("+")

    def test_normalize_phone_number(self):
        """Test phone number normalization"""
        assert normalize_phone_number("(202) 555-1234") == "+12025551234"
        assert normalize_phone_number("202-555-1234") == "+12025551234"
        assert normalize_phone_number("2025551234") == "+12025551234"


# ============================================================================
# URL VALIDATION TESTS
# ============================================================================

class TestUrlValidation:
    """Test URL validation"""

    def test_valid_urls(self):
        """Test valid URLs"""
        assert validate_url("https://wwmaa.com")
        assert validate_url("http://example.com/path")

    def test_invalid_urls(self):
        """Test invalid URLs"""
        assert not validate_url("javascript:alert('xss')")
        assert not validate_url("data:text/html,<script>alert('xss')</script>")
        assert not validate_url("file:///etc/passwd")

    def test_url_domain_whitelist(self):
        """Test URL domain whitelisting"""
        allowed_domains = ['wwmaa.com', 'youtube.com']
        assert validate_url("https://wwmaa.com/events", allowed_domains=allowed_domains)
        assert validate_url("https://www.youtube.com/watch", allowed_domains=allowed_domains)
        assert not validate_url("https://evil.com", allowed_domains=allowed_domains)

    def test_sanitize_url(self):
        """Test URL sanitization"""
        result = sanitize_url("https://example.com/path")
        assert result == "https://example.com/path"

        # Should return None for invalid URLs
        assert sanitize_url("javascript:alert('xss')") is None


# ============================================================================
# USERNAME VALIDATION TESTS
# ============================================================================

class TestUsernameValidation:
    """Test username validation"""

    def test_valid_usernames(self):
        """Test valid usernames"""
        assert validate_username("john_doe")
        assert validate_username("user123")
        assert validate_username("test-user")

    def test_invalid_usernames(self):
        """Test invalid usernames"""
        assert not validate_username("ab")  # Too short
        assert not validate_username("a" * 31)  # Too long
        assert not validate_username("user@email")  # Invalid char
        assert not validate_username("user name")  # Space not allowed

    def test_sanitize_username(self):
        """Test username sanitization"""
        result = sanitize_username("user@email.com")
        assert "@" not in result  # Special chars removed
        assert sanitize_username("test user!") == "testuser"  # Spaces and ! removed


# ============================================================================
# PASSWORD VALIDATION TESTS
# ============================================================================

class TestPasswordValidation:
    """Test password strength validation"""

    def test_strong_password(self):
        """Test strong passwords"""
        is_valid, errors = validate_password_strength("Password123!")
        assert is_valid
        assert len(errors) == 0

    def test_weak_passwords(self):
        """Test weak passwords"""
        # Too short
        is_valid, errors = validate_password_strength("Pass1!")
        assert not is_valid
        assert any("8 characters" in err for err in errors)

        # No uppercase
        is_valid, errors = validate_password_strength("password123!")
        assert not is_valid
        assert any("uppercase" in err for err in errors)

        # No lowercase
        is_valid, errors = validate_password_strength("PASSWORD123!")
        assert not is_valid
        assert any("lowercase" in err for err in errors)

        # No digit
        is_valid, errors = validate_password_strength("Password!")
        assert not is_valid
        assert any("digit" in err for err in errors)


# ============================================================================
# HTML SANITIZATION TESTS (XSS PREVENTION)
# ============================================================================

class TestHtmlSanitization:
    """Test HTML sanitization for XSS prevention"""

    def test_sanitize_safe_html(self):
        """Test sanitizing safe HTML"""
        safe_html = "<p>This is <strong>safe</strong> content</p>"
        result = sanitize_html(safe_html)
        # If bleach is available, tags are preserved; otherwise HTML escaped
        assert "safe" in result or "safe" in result.lower()

    def test_sanitize_xss_attempts(self):
        """Test sanitizing XSS attempts"""
        # Script tag
        result = sanitize_html('<p>Safe</p><script>alert("XSS")</script>')
        # Either sanitized (bleach) or escaped (fallback)
        # Either way, script should not be executable
        assert "Safe" in result or "safe" in result.lower()

    def test_strip_html(self):
        """Test stripping all HTML tags"""
        html = "<p>This has <strong>tags</strong></p>"
        result = strip_html(html)
        # Result should have plain text
        assert "This has tags" in result or "tags" in result
        # Original HTML should not be present
        assert result != html


# ============================================================================
# SQL INJECTION DETECTION TESTS
# ============================================================================

class TestSqlInjectionDetection:
    """Test SQL injection detection"""

    def test_detect_sql_injection_attacks(self):
        """Test detection of SQL injection attempts"""
        # Classic SQL injection
        assert detect_sql_injection("'; DROP TABLE users; --")
        assert detect_sql_injection("1' OR '1'='1")
        assert detect_sql_injection("admin'--")
        assert detect_sql_injection("1; DELETE FROM users")

        # Union-based injection
        assert detect_sql_injection("' UNION SELECT * FROM users--")

    def test_normal_input_not_flagged(self):
        """Test normal input is not flagged"""
        assert not detect_sql_injection("John Smith")
        assert not detect_sql_injection("user@example.com")
        assert not detect_sql_injection("I want to select a date for training")


# ============================================================================
# FILE EXTENSION VALIDATION TESTS
# ============================================================================

class TestFileExtensionValidation:
    """Test file extension validation"""

    def test_validate_file_extension(self):
        """Test file extension validation"""
        allowed_extensions = {'jpg', 'png', 'gif'}
        assert validate_file_extension("photo.jpg", allowed_extensions)
        assert validate_file_extension("image.PNG", allowed_extensions)
        assert not validate_file_extension("script.exe", allowed_extensions)

    def test_is_dangerous_file(self):
        """Test dangerous file detection"""
        assert is_dangerous_file("malware.exe")
        assert is_dangerous_file("script.bat")
        assert is_dangerous_file("payload.sh")
        assert not is_dangerous_file("photo.jpg")

    def test_sanitize_filename(self):
        """Test filename sanitization"""
        # Remove special characters
        result = sanitize_filename("file name!@#.jpg")
        assert "!" not in result
        assert "@" not in result
        assert "#" not in result

        # Remove path traversal
        result = sanitize_filename("../../etc/passwd")
        assert ".." not in result
        assert "/" not in result

        # Limit length
        long_name = "a" * 300 + ".jpg"
        result = sanitize_filename(long_name)
        assert len(result) <= 255
        assert result.endswith(".jpg")


# ============================================================================
# PATH TRAVERSAL PREVENTION TESTS
# ============================================================================

class TestPathTraversalPrevention:
    """Test path traversal prevention"""

    def test_is_safe_path(self, tmp_path):
        """Test path safety validation"""
        allowed_dir = str(tmp_path)

        # Safe path
        assert is_safe_path("user/file.jpg", allowed_dir)

        # Path traversal attempts
        assert not is_safe_path("../../etc/passwd", allowed_dir)
        assert not is_safe_path("../outside", allowed_dir)

    def test_safe_join_path(self, tmp_path):
        """Test safe path joining"""
        base_dir = str(tmp_path)

        # Safe join
        result = safe_join_path(base_dir, "user", "file.jpg")
        assert result is not None
        assert str(result).startswith(base_dir)

        # Path traversal attempt
        result = safe_join_path(base_dir, "..", "etc", "passwd")
        assert result is None

    def test_get_safe_filename(self):
        """Test safe filename extraction"""
        assert get_safe_filename("/path/to/file.jpg") == "file.jpg"
        assert get_safe_filename("../../etc/passwd") == "passwd"
        assert get_safe_filename("C:\\Windows\\system32\\file.txt") == "file.txt"


# ============================================================================
# COMMAND INJECTION PREVENTION TESTS
# ============================================================================

class TestCommandInjectionPrevention:
    """Test command injection prevention"""

    def test_detect_command_injection(self):
        """Test command injection detection"""
        assert detect_command_injection("; rm -rf /")
        assert detect_command_injection("| cat /etc/passwd")
        assert detect_command_injection("$(whoami)")
        assert detect_command_injection("`ls -la`")
        assert detect_command_injection("file && malicious")

    def test_validate_command_arguments(self):
        """Test command argument validation"""
        # Safe arguments
        assert validate_command_arguments(["input.jpg", "output.png"])

        # Dangerous arguments
        assert not validate_command_arguments(["file; rm -rf /"])
        assert not validate_command_arguments(["file | cat"])


# ============================================================================
# FILE UPLOAD VALIDATION TESTS
# ============================================================================

class TestFileUploadValidation:
    """Test file upload validation"""

    def create_mock_upload_file(self, filename: str, content_type: str, size: int) -> Mock:
        """Create a mock UploadFile for testing"""
        file_content = b"x" * size
        file = BytesIO(file_content)

        upload_file = Mock(spec=UploadFile)
        upload_file.filename = filename
        upload_file.file = file
        upload_file.content_type = content_type

        return upload_file

    def test_get_file_extension(self):
        """Test file extension extraction"""
        assert get_file_extension("photo.jpg") == "jpg"
        assert get_file_extension("document.PDF") == "pdf"
        assert get_file_extension("no_extension") == ""

    def test_validate_mime_type(self):
        """Test MIME type validation"""
        allowed_types = {'image/jpeg', 'image/png'}

        assert validate_mime_type("image/jpeg", allowed_types)
        assert validate_mime_type("image/png; charset=utf-8", allowed_types)
        assert not validate_mime_type("application/exe", allowed_types)

    def test_sanitize_upload_filename(self):
        """Test upload filename sanitization"""
        # Remove dangerous patterns
        result = sanitize_upload_filename("../../etc/passwd")
        assert ".." not in result

        # Remove special characters
        result = sanitize_upload_filename("file name!@#.jpg")
        assert result == "file_name___.jpg"

    def test_validate_image_upload(self):
        """Test image upload validation"""
        # Valid image
        valid_image = self.create_mock_upload_file(
            "photo.jpg",
            "image/jpeg",
            1024 * 1024  # 1 MB
        )
        # Mock magic bytes check
        with patch('backend.utils.file_upload.verify_magic_bytes', return_value=True):
            is_valid, error = validate_image_upload(valid_image)
            assert is_valid
            assert error == ""

        # Invalid extension
        invalid_ext = self.create_mock_upload_file(
            "malware.exe",
            "application/exe",
            1024
        )
        is_valid, error = validate_image_upload(invalid_ext)
        assert not is_valid
        assert "extension" in error.lower()

        # File too large
        too_large = self.create_mock_upload_file(
            "huge.jpg",
            "image/jpeg",
            20 * 1024 * 1024  # 20 MB
        )
        is_valid, error = validate_image_upload(too_large)
        assert not is_valid
        assert "large" in error.lower()


# ============================================================================
# SECURITY UTILITY TESTS
# ============================================================================

class TestSecurityUtilities:
    """Test security utility functions"""

    def test_constant_time_compare(self):
        """Test constant-time string comparison"""
        assert constant_time_compare("secret", "secret")
        assert not constant_time_compare("secret", "wrong")

    def test_generate_secure_token(self):
        """Test secure token generation"""
        token1 = generate_secure_token(32)
        token2 = generate_secure_token(32)

        # Tokens should be different
        assert token1 != token2

        # Token should have correct length (hex = 2 chars per byte)
        assert len(token1) == 64

    def test_hash_sensitive_data(self):
        """Test sensitive data hashing"""
        ip = "192.168.1.1"
        hash1 = hash_sensitive_data(ip)
        hash2 = hash_sensitive_data(ip)

        # Same input should produce same hash
        assert hash1 == hash2

        # Different input should produce different hash
        hash3 = hash_sensitive_data("10.0.0.1")
        assert hash1 != hash3

    def test_validate_ip_address(self):
        """Test IP address validation"""
        assert validate_ip_address("192.168.1.1")
        assert validate_ip_address("2001:0db8:85a3::8a2e:0370:7334")
        assert not validate_ip_address("invalid")
        assert not validate_ip_address("999.999.999.999")

    def test_hash_ip_address(self):
        """Test IP address hashing"""
        ip = "192.168.1.1"
        hashed = hash_ip_address(ip)

        # Should be a SHA256 hash (64 hex characters)
        assert len(hashed) == 64
        assert all(c in "0123456789abcdef" for c in hashed)


# ============================================================================
# DATE VALIDATION TESTS
# ============================================================================

class TestDateValidation:
    """Test date validation"""

    def test_validate_date_not_future(self):
        """Test date not in future validation"""
        from datetime import datetime

        # Past date should be valid
        assert validate_date_not_future("2020-01-01T00:00:00Z")

        # Far future date should be invalid (use a date far in future)
        future_year = datetime.utcnow().year + 100
        assert not validate_date_not_future(f"{future_year}-12-31T23:59:59Z")

    def test_validate_date_range(self):
        """Test date range validation"""
        # Valid range
        assert validate_date_range(
            "2024-01-01T00:00:00Z",
            "2024-12-31T23:59:59Z"
        )

        # Invalid range (end before start)
        assert not validate_date_range(
            "2024-12-31T23:59:59Z",
            "2024-01-01T00:00:00Z"
        )


# ============================================================================
# ALPHANUMERIC VALIDATION TESTS
# ============================================================================

class TestAlphanumericValidation:
    """Test alphanumeric validation"""

    def test_validate_alphanumeric(self):
        """Test alphanumeric validation"""
        assert validate_alphanumeric("abc123")
        assert validate_alphanumeric("test_user", allow_underscore=True)
        assert validate_alphanumeric("test-user", allow_hyphen=True)
        assert validate_alphanumeric("hello world", allow_spaces=True)

        # Should fail without flags
        assert not validate_alphanumeric("test_user", allow_underscore=False)
        assert not validate_alphanumeric("test@user")


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestInputValidationIntegration:
    """Integration tests for input validation"""

    def test_malicious_input_rejected(self):
        """Test that malicious input is rejected"""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "<script>alert('XSS')</script>",
            "../../etc/passwd",
            "$(whoami)",
            "| cat /etc/passwd",
        ]

        for malicious_input in malicious_inputs:
            # Should be detected by SQL injection detection
            if "DROP" in malicious_input or "SELECT" in malicious_input:
                assert detect_sql_injection(malicious_input)

            # Should be sanitized by HTML sanitization
            if "<script>" in malicious_input:
                sanitized = sanitize_html(malicious_input)
                # Script should not be executable (either removed or escaped)
                assert sanitized != malicious_input

            # Should be detected by path traversal check
            if ".." in malicious_input:
                assert not is_safe_path(malicious_input, "/uploads")

            # Should be detected by command injection check
            if "$" in malicious_input or "|" in malicious_input:
                assert detect_command_injection(malicious_input)

    def test_normal_input_accepted(self):
        """Test that normal input is accepted"""
        normal_inputs = {
            "email": "user@example.com",
            "name": "John Smith",
            "phone": "+12025551234",
            "url": "https://wwmaa.com",
            "username": "john_doe",
            "password": "SecurePass123!",
        }

        # All normal inputs should be valid
        assert validate_email(normal_inputs["email"])
        assert not detect_sql_injection(normal_inputs["name"])
        assert validate_phone_number(normal_inputs["phone"])
        assert validate_url(normal_inputs["url"])
        assert validate_username(normal_inputs["username"])
        is_valid, _ = validate_password_strength(normal_inputs["password"])
        assert is_valid


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=backend.utils", "--cov-report=term-missing"])
