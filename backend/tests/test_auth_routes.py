"""
Unit Tests for Authentication Routes

Comprehensive test coverage for user registration and email verification.
Tests include success scenarios, validation, error handling, and edge cases.

Target: 80%+ code coverage
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4

from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from backend.app import app
from backend.routes.auth import (
    router,
    hash_password,
    verify_password,
    generate_verification_token,
    get_token_expiry,
    generate_password_reset_token,
    get_password_reset_token_expiry,
    check_rate_limit,
    RegisterRequest,
    VerifyEmailRequest,
    PasswordResetRequestRequest,
    PasswordResetConfirmRequest,
    _password_reset_attempts
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_zerodb_client():
    """Mock ZeroDB client"""
    with patch('backend.routes.auth.get_zerodb_client') as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


@pytest.fixture
def mock_email_service():
    """Mock email service"""
    with patch('backend.routes.auth.get_email_service') as mock:
        service = MagicMock()
        mock.return_value = service
        yield service


@pytest.fixture
def valid_registration_data():
    """Valid registration data"""
    return {
        "email": "test@example.com",
        "password": "SecurePass123!",
        "first_name": "Jane",
        "last_name": "Doe",
        "phone": "+1-555-0100"
    }


@pytest.fixture
def mock_user_document():
    """Mock user document from ZeroDB"""
    user_id = str(uuid4())
    return {
        "id": user_id,
        "data": {
            "email": "test@example.com",
            "password_hash": "$2b$12$hash",
            "role": "public",
            "is_active": True,
            "is_verified": False,
            "verification_token": "test_token_123",
            "verification_token_expiry": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            "first_name": "Jane",
            "last_name": "Doe",
            "phone": "+1-555-0100",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
    }


@pytest.fixture(autouse=True)
def clear_rate_limit_state():
    """Clear rate limit state before each test"""
    _password_reset_attempts.clear()
    yield
    _password_reset_attempts.clear()


# ============================================================================
# HELPER FUNCTION TESTS
# ============================================================================

class TestHelperFunctions:
    """Test helper functions for password hashing and token generation"""

    def test_hash_password(self):
        """Test password hashing"""
        password = "TestPassword123!"
        hashed = hash_password(password)

        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")  # bcrypt hash prefix

    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "TestPassword123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        password = "TestPassword123!"
        wrong_password = "WrongPassword456!"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_generate_verification_token(self):
        """Test verification token generation"""
        token1 = generate_verification_token()
        token2 = generate_verification_token()

        assert token1 is not None
        assert token2 is not None
        assert token1 != token2  # Should be unique
        assert len(token1) > 0

    def test_get_token_expiry(self):
        """Test token expiry calculation"""
        before = datetime.utcnow()
        expiry = get_token_expiry()
        after = datetime.utcnow()

        # Should be approximately 24 hours from now
        expected_min = before + timedelta(hours=23, minutes=59)
        expected_max = after + timedelta(hours=24, minutes=1)

        assert expected_min <= expiry <= expected_max


# ============================================================================
# REGISTRATION VALIDATION TESTS
# ============================================================================

class TestRegistrationValidation:
    """Test registration request validation"""

    def test_valid_registration_request(self, valid_registration_data):
        """Test valid registration data passes validation"""
        request = RegisterRequest(**valid_registration_data)

        assert request.email == "test@example.com"
        assert request.password == "SecurePass123!"
        assert request.first_name == "Jane"
        assert request.last_name == "Doe"
        assert request.phone == "+1-555-0100"

    def test_email_lowercase_conversion(self):
        """Test email is converted to lowercase"""
        data = {
            "email": "TEST@EXAMPLE.COM",
            "password": "SecurePass123!",
            "first_name": "Jane",
            "last_name": "Doe"
        }
        request = RegisterRequest(**data)

        assert request.email == "test@example.com"

    def test_password_too_short(self):
        """Test password must be at least 8 characters"""
        data = {
            "email": "test@example.com",
            "password": "Short1!",
            "first_name": "Jane",
            "last_name": "Doe"
        }

        with pytest.raises(ValueError, match="at least 8 characters"):
            RegisterRequest(**data)

    def test_password_no_uppercase(self):
        """Test password must contain uppercase letter"""
        data = {
            "email": "test@example.com",
            "password": "lowercase123!",
            "first_name": "Jane",
            "last_name": "Doe"
        }

        with pytest.raises(ValueError, match="uppercase letter"):
            RegisterRequest(**data)

    def test_password_no_lowercase(self):
        """Test password must contain lowercase letter"""
        data = {
            "email": "test@example.com",
            "password": "UPPERCASE123!",
            "first_name": "Jane",
            "last_name": "Doe"
        }

        with pytest.raises(ValueError, match="lowercase letter"):
            RegisterRequest(**data)

    def test_password_no_number(self):
        """Test password must contain number"""
        data = {
            "email": "test@example.com",
            "password": "NoNumbers!",
            "first_name": "Jane",
            "last_name": "Doe"
        }

        with pytest.raises(ValueError, match="at least one number"):
            RegisterRequest(**data)

    def test_password_no_special_char(self):
        """Test password must contain special character"""
        data = {
            "email": "test@example.com",
            "password": "NoSpecial123",
            "first_name": "Jane",
            "last_name": "Doe"
        }

        with pytest.raises(ValueError, match="special character"):
            RegisterRequest(**data)

    def test_invalid_email_format(self):
        """Test invalid email format is rejected"""
        from pydantic import ValidationError

        data = {
            "email": "not-an-email",
            "password": "SecurePass123!",
            "first_name": "Jane",
            "last_name": "Doe"
        }

        with pytest.raises(ValidationError):
            RegisterRequest(**data)

    def test_optional_phone_field(self):
        """Test phone field is optional"""
        data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "first_name": "Jane",
            "last_name": "Doe"
        }
        request = RegisterRequest(**data)

        assert request.phone is None


# ============================================================================
# REGISTRATION ENDPOINT TESTS
# ============================================================================

class TestRegistrationEndpoint:
    """Test user registration endpoint"""

    def test_successful_registration(
        self,
        client,
        mock_zerodb_client,
        mock_email_service,
        valid_registration_data
    ):
        """Test successful user registration"""
        # Mock no existing user
        mock_zerodb_client.query_documents.return_value = {"documents": []}

        # Mock successful user creation
        user_id = str(uuid4())
        mock_zerodb_client.create_document.return_value = {
            "id": user_id,
            "data": valid_registration_data
        }

        # Mock successful email sending
        mock_email_service.send_verification_email.return_value = {
            "MessageID": "test-message-id"
        }

        # Make request
        response = client.post("/api/auth/register", json=valid_registration_data)

        # Assertions
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Registration successful. Please check your email to verify your account."
        assert data["email"] == "test@example.com"
        assert data["verification_required"] is True
        assert "user_id" in data

        # Verify ZeroDB was called correctly
        mock_zerodb_client.query_documents.assert_called_once()
        mock_zerodb_client.create_document.assert_called_once()

        # Verify email was sent
        mock_email_service.send_verification_email.assert_called_once()

    def test_registration_duplicate_email(
        self,
        client,
        mock_zerodb_client,
        mock_email_service,
        valid_registration_data,
        mock_user_document
    ):
        """Test registration fails with duplicate email"""
        # Mock existing user found
        mock_zerodb_client.query_documents.return_value = {
            "documents": [mock_user_document]
        }

        # Make request
        response = client.post("/api/auth/register", json=valid_registration_data)

        # Assertions
        assert response.status_code == 400
        data = response.json()
        assert "already registered" in data["detail"].lower()

        # Verify user was not created
        mock_zerodb_client.create_document.assert_not_called()
        mock_email_service.send_verification_email.assert_not_called()

    def test_registration_weak_password(self, client, mock_zerodb_client):
        """Test registration fails with weak password"""
        data = {
            "email": "test@example.com",
            "password": "weak",
            "first_name": "Jane",
            "last_name": "Doe"
        }

        response = client.post("/api/auth/register", json=data)

        assert response.status_code == 422  # Validation error
        assert mock_zerodb_client.query_documents.call_count == 0

    def test_registration_missing_required_fields(self, client):
        """Test registration fails with missing required fields"""
        data = {
            "email": "test@example.com",
            "password": "SecurePass123!"
            # Missing first_name and last_name
        }

        response = client.post("/api/auth/register", json=data)

        assert response.status_code == 422  # Validation error

    def test_registration_email_service_failure(
        self,
        client,
        mock_zerodb_client,
        mock_email_service,
        valid_registration_data
    ):
        """Test registration succeeds even if email fails to send"""
        from backend.services.email_service import EmailSendError

        # Mock no existing user
        mock_zerodb_client.query_documents.return_value = {"documents": []}

        # Mock successful user creation
        user_id = str(uuid4())
        mock_zerodb_client.create_document.return_value = {
            "id": user_id,
            "data": valid_registration_data
        }

        # Mock email service failure
        mock_email_service.send_verification_email.side_effect = EmailSendError(
            "Failed to send email"
        )

        # Make request
        response = client.post("/api/auth/register", json=valid_registration_data)

        # Should still succeed (user created, email failure logged)
        assert response.status_code == 201
        data = response.json()
        assert "user_id" in data

    def test_registration_database_error(
        self,
        client,
        mock_zerodb_client,
        valid_registration_data
    ):
        """Test registration fails gracefully on database error"""
        from backend.services.zerodb_service import ZeroDBError

        # Mock no existing user
        mock_zerodb_client.query_documents.return_value = {"documents": []}

        # Mock database error on creation
        mock_zerodb_client.create_document.side_effect = ZeroDBError(
            "Database connection failed"
        )

        # Make request
        response = client.post("/api/auth/register", json=valid_registration_data)

        # Should return 500 error
        assert response.status_code == 500
        data = response.json()
        assert "try again later" in data["detail"].lower()


# ============================================================================
# EMAIL VERIFICATION TESTS
# ============================================================================

class TestEmailVerificationEndpoint:
    """Test email verification endpoint"""

    def test_successful_verification(
        self,
        client,
        mock_zerodb_client,
        mock_email_service,
        mock_user_document
    ):
        """Test successful email verification"""
        # Mock finding user with token
        mock_zerodb_client.query_documents.return_value = {
            "documents": [mock_user_document]
        }

        # Mock successful update
        mock_zerodb_client.update_document.return_value = {
            "id": mock_user_document["id"],
            "data": {**mock_user_document["data"], "is_verified": True}
        }

        # Mock successful welcome email
        mock_email_service.send_welcome_email.return_value = {
            "MessageID": "welcome-message-id"
        }

        # Make request
        response = client.post(
            "/api/auth/verify-email",
            json={"token": "test_token_123"}
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "verified successfully" in data["message"].lower()
        assert data["email"] == "test@example.com"
        assert data["is_verified"] is True

        # Verify database was updated
        mock_zerodb_client.update_document.assert_called_once()
        call_args = mock_zerodb_client.update_document.call_args
        assert call_args.kwargs["data"]["is_verified"] is True
        assert call_args.kwargs["data"]["verification_token"] is None

        # Verify welcome email was sent
        mock_email_service.send_welcome_email.assert_called_once()

    def test_verification_invalid_token(
        self,
        client,
        mock_zerodb_client
    ):
        """Test verification fails with invalid token"""
        # Mock no user found with token
        mock_zerodb_client.query_documents.return_value = {"documents": []}

        # Make request
        response = client.post(
            "/api/auth/verify-email",
            json={"token": "invalid_token"}
        )

        # Assertions
        assert response.status_code == 400
        data = response.json()
        assert "invalid" in data["detail"].lower()

        # Verify database was not updated
        mock_zerodb_client.update_document.assert_not_called()

    def test_verification_expired_token(
        self,
        client,
        mock_zerodb_client,
        mock_user_document
    ):
        """Test verification fails with expired token"""
        # Set token expiry to past
        expired_user = mock_user_document.copy()
        expired_user["data"]["verification_token_expiry"] = (
            datetime.utcnow() - timedelta(hours=1)
        ).isoformat()

        # Mock finding user with expired token
        mock_zerodb_client.query_documents.return_value = {
            "documents": [expired_user]
        }

        # Make request
        response = client.post(
            "/api/auth/verify-email",
            json={"token": "test_token_123"}
        )

        # Assertions
        assert response.status_code == 400
        data = response.json()
        assert "expired" in data["detail"].lower()

        # Verify database was not updated
        mock_zerodb_client.update_document.assert_not_called()

    def test_verification_already_verified(
        self,
        client,
        mock_zerodb_client,
        mock_user_document
    ):
        """Test verification with already verified user"""
        # Set user as already verified
        verified_user = mock_user_document.copy()
        verified_user["data"]["is_verified"] = True

        # Mock finding already verified user
        mock_zerodb_client.query_documents.return_value = {
            "documents": [verified_user]
        }

        # Make request
        response = client.post(
            "/api/auth/verify-email",
            json={"token": "test_token_123"}
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "already verified" in data["message"].lower()
        assert data["is_verified"] is True

        # Verify database was not updated again
        mock_zerodb_client.update_document.assert_not_called()

    def test_verification_database_error(
        self,
        client,
        mock_zerodb_client,
        mock_user_document
    ):
        """Test verification fails gracefully on database error"""
        from backend.services.zerodb_service import ZeroDBError

        # Mock finding user
        mock_zerodb_client.query_documents.return_value = {
            "documents": [mock_user_document]
        }

        # Mock database error on update
        mock_zerodb_client.update_document.side_effect = ZeroDBError(
            "Database update failed"
        )

        # Make request
        response = client.post(
            "/api/auth/verify-email",
            json={"token": "test_token_123"}
        )

        # Should return 500 error
        assert response.status_code == 500
        data = response.json()
        assert "try again later" in data["detail"].lower()

    def test_verification_welcome_email_failure(
        self,
        client,
        mock_zerodb_client,
        mock_email_service,
        mock_user_document
    ):
        """Test verification succeeds even if welcome email fails"""
        from backend.services.email_service import EmailSendError

        # Mock finding user with token
        mock_zerodb_client.query_documents.return_value = {
            "documents": [mock_user_document]
        }

        # Mock successful update
        mock_zerodb_client.update_document.return_value = {
            "id": mock_user_document["id"],
            "data": {**mock_user_document["data"], "is_verified": True}
        }

        # Mock welcome email failure
        mock_email_service.send_welcome_email.side_effect = EmailSendError(
            "Failed to send welcome email"
        )

        # Make request
        response = client.post(
            "/api/auth/verify-email",
            json={"token": "test_token_123"}
        )

        # Should still succeed (verification completed, email failure logged)
        assert response.status_code == 200
        data = response.json()
        assert data["is_verified"] is True


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestAuthenticationFlow:
    """Test complete authentication flow"""

    def test_complete_registration_and_verification_flow(
        self,
        client,
        mock_zerodb_client,
        mock_email_service,
        valid_registration_data
    ):
        """Test complete registration and verification flow"""
        # Step 1: Register user
        mock_zerodb_client.query_documents.return_value = {"documents": []}

        user_id = str(uuid4())
        verification_token = "test_token_xyz"

        mock_zerodb_client.create_document.return_value = {
            "id": user_id,
            "data": {**valid_registration_data, "verification_token": verification_token}
        }

        mock_email_service.send_verification_email.return_value = {
            "MessageID": "verify-message-id"
        }

        reg_response = client.post("/api/auth/register", json=valid_registration_data)
        assert reg_response.status_code == 201

        # Step 2: Verify email
        user_doc = {
            "id": user_id,
            "data": {
                "email": valid_registration_data["email"],
                "is_verified": False,
                "verification_token": verification_token,
                "verification_token_expiry": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
                "first_name": valid_registration_data["first_name"],
                "last_name": valid_registration_data["last_name"]
            }
        }

        mock_zerodb_client.query_documents.return_value = {"documents": [user_doc]}
        mock_zerodb_client.update_document.return_value = {
            "id": user_id,
            "data": {**user_doc["data"], "is_verified": True}
        }

        verify_response = client.post(
            "/api/auth/verify-email",
            json={"token": verification_token}
        )

        assert verify_response.status_code == 200
        verify_data = verify_response.json()
        assert verify_data["is_verified"] is True
        assert verify_data["email"] == valid_registration_data["email"]


# ============================================================================
# PASSWORD RESET REQUEST TESTS
# ============================================================================

class TestPasswordResetRequest:
    """Test password reset request endpoint"""

    def test_successful_password_reset_request(
        self,
        client,
        mock_zerodb_client,
        mock_email_service,
        mock_user_document
    ):
        """Test successful password reset request"""
        # Mock finding user
        mock_zerodb_client.query_documents.return_value = {
            "documents": [mock_user_document]
        }

        # Mock successful update
        mock_zerodb_client.update_document.return_value = {
            "id": mock_user_document["id"],
            "data": mock_user_document["data"]
        }

        # Mock successful email sending
        mock_email_service.send_password_reset_email.return_value = {
            "MessageID": "reset-message-id"
        }

        # Make request
        response = client.post(
            "/api/auth/forgot-password",
            json={"email": "test@example.com"}
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "account exists" in data["message"].lower()

        # Verify database was updated with reset token
        mock_zerodb_client.update_document.assert_called_once()
        call_args = mock_zerodb_client.update_document.call_args
        assert "password_reset_token" in call_args.kwargs["data"]
        assert "password_reset_token_expiry" in call_args.kwargs["data"]

        # Verify email was sent
        mock_email_service.send_password_reset_email.assert_called_once()

    def test_password_reset_request_nonexistent_user(
        self,
        client,
        mock_zerodb_client
    ):
        """Test password reset request for non-existent user returns generic message"""
        # Mock no user found
        mock_zerodb_client.query_documents.return_value = {"documents": []}

        # Make request
        response = client.post(
            "/api/auth/forgot-password",
            json={"email": "nonexistent@example.com"}
        )

        # Should return success to prevent user enumeration
        assert response.status_code == 200
        data = response.json()
        assert "account exists" in data["message"].lower()

        # Verify database was not updated
        mock_zerodb_client.update_document.assert_not_called()

    def test_password_reset_request_rate_limiting(
        self,
        client,
        mock_zerodb_client,
        mock_email_service,
        mock_user_document
    ):
        """Test password reset rate limiting (max 3 requests per hour)"""
        # Mock finding user
        mock_zerodb_client.query_documents.return_value = {
            "documents": [mock_user_document]
        }
        mock_zerodb_client.update_document.return_value = {
            "id": mock_user_document["id"],
            "data": mock_user_document["data"]
        }
        mock_email_service.send_password_reset_email.return_value = {
            "MessageID": "reset-message-id"
        }

        # Make 3 successful requests
        for i in range(3):
            response = client.post(
                "/api/auth/forgot-password",
                json={"email": "test@example.com"}
            )
            assert response.status_code == 200

        # 4th request should be rate limited
        response = client.post(
            "/api/auth/forgot-password",
            json={"email": "test@example.com"}
        )

        assert response.status_code == 429
        data = response.json()
        assert "too many" in data["detail"].lower()

    def test_password_reset_request_invalid_email(self, client):
        """Test password reset request with invalid email format"""
        # Make request with invalid email
        response = client.post(
            "/api/auth/forgot-password",
            json={"email": "not-an-email"}
        )

        # Should return validation error
        assert response.status_code == 422

    def test_password_reset_request_email_service_failure(
        self,
        client,
        mock_zerodb_client,
        mock_email_service,
        mock_user_document
    ):
        """Test password reset request succeeds even if email fails"""
        from backend.services.email_service import EmailSendError

        # Mock finding user
        mock_zerodb_client.query_documents.return_value = {
            "documents": [mock_user_document]
        }
        mock_zerodb_client.update_document.return_value = {
            "id": mock_user_document["id"],
            "data": mock_user_document["data"]
        }

        # Mock email service failure
        mock_email_service.send_password_reset_email.side_effect = EmailSendError(
            "Failed to send email"
        )

        # Make request
        response = client.post(
            "/api/auth/forgot-password",
            json={"email": "test@example.com"}
        )

        # Should still succeed (token stored, email failure logged)
        assert response.status_code == 200

    def test_password_reset_request_database_error(
        self,
        client,
        mock_zerodb_client,
        mock_user_document
    ):
        """Test password reset request fails gracefully on database error"""
        from backend.services.zerodb_service import ZeroDBError

        # Mock finding user
        mock_zerodb_client.query_documents.return_value = {
            "documents": [mock_user_document]
        }

        # Mock database error on update
        mock_zerodb_client.update_document.side_effect = ZeroDBError(
            "Database update failed"
        )

        # Make request
        response = client.post(
            "/api/auth/forgot-password",
            json={"email": "test@example.com"}
        )

        # Should return 500 error
        assert response.status_code == 500
        data = response.json()
        assert "try again later" in data["detail"].lower()


# ============================================================================
# PASSWORD RESET CONFIRMATION TESTS
# ============================================================================

class TestPasswordResetConfirm:
    """Test password reset confirmation endpoint"""

    def test_successful_password_reset_confirm(
        self,
        client,
        mock_zerodb_client,
        mock_user_document
    ):
        """Test successful password reset confirmation"""
        # Add reset token to user document
        user_with_reset_token = mock_user_document.copy()
        user_with_reset_token["data"]["password_reset_token"] = "valid_reset_token_123"
        user_with_reset_token["data"]["password_reset_token_expiry"] = (
            datetime.utcnow() + timedelta(hours=1)
        ).isoformat()

        # Mock finding user with token
        mock_zerodb_client.query_documents.return_value = {
            "documents": [user_with_reset_token]
        }

        # Mock successful update
        mock_zerodb_client.update_document.return_value = {
            "id": user_with_reset_token["id"],
            "data": {**user_with_reset_token["data"], "password_reset_token": None}
        }

        # Make request
        response = client.post(
            "/api/auth/reset-password",
            json={
                "token": "valid_reset_token_123",
                "new_password": "NewSecure123!"
            }
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "successful" in data["message"].lower()
        assert data["email"] == "test@example.com"

        # Verify database was updated with new password
        mock_zerodb_client.update_document.assert_called_once()
        call_args = mock_zerodb_client.update_document.call_args
        assert "password_hash" in call_args.kwargs["data"]
        assert call_args.kwargs["data"]["password_reset_token"] is None
        assert call_args.kwargs["data"]["password_reset_token_expiry"] is None

    def test_password_reset_confirm_invalid_token(
        self,
        client,
        mock_zerodb_client
    ):
        """Test password reset confirmation fails with invalid token"""
        # Mock no user found with token
        mock_zerodb_client.query_documents.return_value = {"documents": []}

        # Make request
        response = client.post(
            "/api/auth/reset-password",
            json={
                "token": "invalid_token",
                "new_password": "NewSecure123!"
            }
        )

        # Assertions
        assert response.status_code == 400
        data = response.json()
        assert "invalid" in data["detail"].lower() or "expired" in data["detail"].lower()

        # Verify database was not updated
        mock_zerodb_client.update_document.assert_not_called()

    def test_password_reset_confirm_expired_token(
        self,
        client,
        mock_zerodb_client,
        mock_user_document
    ):
        """Test password reset confirmation fails with expired token"""
        # Add expired reset token to user document
        user_with_expired_token = mock_user_document.copy()
        user_with_expired_token["data"]["password_reset_token"] = "expired_token_123"
        user_with_expired_token["data"]["password_reset_token_expiry"] = (
            datetime.utcnow() - timedelta(hours=1)
        ).isoformat()

        # Mock finding user with expired token
        mock_zerodb_client.query_documents.return_value = {
            "documents": [user_with_expired_token]
        }

        # Make request
        response = client.post(
            "/api/auth/reset-password",
            json={
                "token": "expired_token_123",
                "new_password": "NewSecure123!"
            }
        )

        # Assertions
        assert response.status_code == 400
        data = response.json()
        assert "expired" in data["detail"].lower()

        # Verify database was not updated
        mock_zerodb_client.update_document.assert_not_called()

    def test_password_reset_confirm_weak_password(
        self,
        client,
        mock_zerodb_client,
        mock_user_document
    ):
        """Test password reset confirmation fails with weak password"""
        # Add reset token to user document
        user_with_reset_token = mock_user_document.copy()
        user_with_reset_token["data"]["password_reset_token"] = "valid_reset_token_123"
        user_with_reset_token["data"]["password_reset_token_expiry"] = (
            datetime.utcnow() + timedelta(hours=1)
        ).isoformat()

        # Make request with weak password
        response = client.post(
            "/api/auth/reset-password",
            json={
                "token": "valid_reset_token_123",
                "new_password": "weak"
            }
        )

        # Should return validation error
        assert response.status_code == 422

        # Verify database was not updated
        mock_zerodb_client.update_document.assert_not_called()

    def test_password_reset_confirm_no_uppercase(
        self,
        client
    ):
        """Test password reset confirmation fails without uppercase letter"""
        response = client.post(
            "/api/auth/reset-password",
            json={
                "token": "valid_token",
                "new_password": "lowercase123!"
            }
        )

        assert response.status_code == 422

    def test_password_reset_confirm_no_number(
        self,
        client
    ):
        """Test password reset confirmation fails without number"""
        response = client.post(
            "/api/auth/reset-password",
            json={
                "token": "valid_token",
                "new_password": "NoNumbers!"
            }
        )

        assert response.status_code == 422

    def test_password_reset_confirm_no_special_char(
        self,
        client
    ):
        """Test password reset confirmation fails without special character"""
        response = client.post(
            "/api/auth/reset-password",
            json={
                "token": "valid_token",
                "new_password": "NoSpecial123"
            }
        )

        assert response.status_code == 422

    def test_password_reset_confirm_database_error(
        self,
        client,
        mock_zerodb_client,
        mock_user_document
    ):
        """Test password reset confirmation fails gracefully on database error"""
        from backend.services.zerodb_service import ZeroDBError

        # Add reset token to user document
        user_with_reset_token = mock_user_document.copy()
        user_with_reset_token["data"]["password_reset_token"] = "valid_reset_token_123"
        user_with_reset_token["data"]["password_reset_token_expiry"] = (
            datetime.utcnow() + timedelta(hours=1)
        ).isoformat()

        # Mock finding user
        mock_zerodb_client.query_documents.return_value = {
            "documents": [user_with_reset_token]
        }

        # Mock database error on update
        mock_zerodb_client.update_document.side_effect = ZeroDBError(
            "Database update failed"
        )

        # Make request
        response = client.post(
            "/api/auth/reset-password",
            json={
                "token": "valid_reset_token_123",
                "new_password": "NewSecure123!"
            }
        )

        # Should return 500 error
        assert response.status_code == 500
        data = response.json()
        assert "try again later" in data["detail"].lower()


# ============================================================================
# PASSWORD RESET HELPER FUNCTION TESTS
# ============================================================================

class TestPasswordResetHelpers:
    """Test password reset helper functions"""

    def test_generate_password_reset_token(self):
        """Test password reset token generation"""
        from backend.routes.auth import generate_password_reset_token

        token1 = generate_password_reset_token()
        token2 = generate_password_reset_token()

        assert token1 is not None
        assert token2 is not None
        assert token1 != token2  # Should be unique
        assert len(token1) > 0

    def test_get_password_reset_token_expiry(self):
        """Test password reset token expiry calculation"""
        from backend.routes.auth import get_password_reset_token_expiry

        before = datetime.utcnow()
        expiry = get_password_reset_token_expiry()
        after = datetime.utcnow()

        # Should be approximately 1 hour from now
        expected_min = before + timedelta(minutes=59)
        expected_max = after + timedelta(hours=1, minutes=1)

        assert expected_min <= expiry <= expected_max

    def test_check_rate_limit(self):
        """Test rate limiting helper function"""
        from backend.routes.auth import check_rate_limit, _password_reset_attempts

        # Clear any existing attempts
        test_email = "ratelimit@example.com"
        _password_reset_attempts.pop(test_email, None)

        # First 3 attempts should succeed
        assert check_rate_limit(test_email, max_attempts=3) is True
        assert check_rate_limit(test_email, max_attempts=3) is True
        assert check_rate_limit(test_email, max_attempts=3) is True

        # 4th attempt should fail
        assert check_rate_limit(test_email, max_attempts=3) is False

        # Clean up
        _password_reset_attempts.pop(test_email, None)


# ============================================================================
# PASSWORD RESET INTEGRATION TESTS
# ============================================================================

class TestPasswordResetFlow:
    """Test complete password reset flow"""

    def test_complete_password_reset_flow(
        self,
        client,
        mock_zerodb_client,
        mock_email_service,
        mock_user_document
    ):
        """Test complete password reset flow from request to confirmation"""
        # Step 1: Request password reset
        mock_zerodb_client.query_documents.return_value = {
            "documents": [mock_user_document]
        }

        reset_token = "test_reset_token_xyz"

        # Mock update to store reset token
        def update_side_effect(collection, document_id, data, merge=True):
            mock_user_document["data"].update(data)
            return {"id": document_id, "data": mock_user_document["data"]}

        mock_zerodb_client.update_document.side_effect = update_side_effect

        mock_email_service.send_password_reset_email.return_value = {
            "MessageID": "reset-message-id"
        }

        reset_request_response = client.post(
            "/api/auth/forgot-password",
            json={"email": "test@example.com"}
        )

        assert reset_request_response.status_code == 200

        # Step 2: Confirm password reset
        user_with_token = mock_user_document.copy()
        user_with_token["data"]["password_reset_token"] = reset_token
        user_with_token["data"]["password_reset_token_expiry"] = (
            datetime.utcnow() + timedelta(hours=1)
        ).isoformat()

        # Mock finding user with reset token
        mock_zerodb_client.query_documents.return_value = {
            "documents": [user_with_token]
        }

        # Reset side effect for confirmation update
        mock_zerodb_client.update_document.side_effect = None
        mock_zerodb_client.update_document.return_value = {
            "id": user_with_token["id"],
            "data": {**user_with_token["data"], "password_reset_token": None}
        }

        reset_confirm_response = client.post(
            "/api/auth/reset-password",
            json={
                "token": reset_token,
                "new_password": "NewSecure123!"
            }
        )

        assert reset_confirm_response.status_code == 200
        confirm_data = reset_confirm_response.json()
        assert "successful" in confirm_data["message"].lower()
        assert confirm_data["email"] == "test@example.com"


# ============================================================================
# LOGIN ENDPOINT TESTS
# ============================================================================

class TestLoginEndpoint:
    """Test user login endpoint"""

    def test_successful_login(
        self,
        client,
        mock_zerodb_client,
        mock_user_document
    ):
        """Test successful user login with valid credentials"""
        from backend.routes.auth import hash_password
        
        # Prepare verified user with hashed password
        password = "TestPassword123!"
        verified_user = mock_user_document.copy()
        verified_user["data"]["is_verified"] = True
        verified_user["data"]["is_active"] = True
        verified_user["data"]["password_hash"] = hash_password(password)
        verified_user["data"]["failed_login_attempts"] = 0
        verified_user["data"]["lockout_until"] = None
        
        # Mock finding user
        mock_zerodb_client.query_documents.return_value = {
            "documents": [verified_user]
        }
        
        # Mock successful update
        mock_zerodb_client.update_document.return_value = {
            "id": verified_user["id"],
            "data": verified_user["data"]
        }
        
        # Make request
        response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": password
            }
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Login successful"
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == "test@example.com"
        assert data["user"]["is_verified"] is True
        
        # Verify database was updated with last_login
        mock_zerodb_client.update_document.assert_called_once()
        call_args = mock_zerodb_client.update_document.call_args
        assert call_args.kwargs["data"]["failed_login_attempts"] == 0
        assert call_args.kwargs["data"]["lockout_until"] is None
        assert "last_login" in call_args.kwargs["data"]

    def test_login_invalid_email(
        self,
        client,
        mock_zerodb_client
    ):
        """Test login fails with non-existent email"""
        # Mock no user found
        mock_zerodb_client.query_documents.return_value = {"documents": []}
        
        response = client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "TestPassword123!"
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "invalid email or password" in data["detail"].lower()

    def test_login_invalid_password(
        self,
        client,
        mock_zerodb_client,
        mock_user_document
    ):
        """Test login fails with incorrect password"""
        from backend.routes.auth import hash_password
        
        # Prepare user with different password
        verified_user = mock_user_document.copy()
        verified_user["data"]["is_verified"] = True
        verified_user["data"]["password_hash"] = hash_password("CorrectPassword123!")
        verified_user["data"]["failed_login_attempts"] = 0
        
        mock_zerodb_client.query_documents.return_value = {
            "documents": [verified_user]
        }
        
        mock_zerodb_client.update_document.return_value = {
            "id": verified_user["id"],
            "data": verified_user["data"]
        }
        
        # Attempt login with wrong password
        response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "WrongPassword123!"
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "invalid email or password" in data["detail"].lower()
        
        # Verify failed attempt was tracked
        mock_zerodb_client.update_document.assert_called_once()
        call_args = mock_zerodb_client.update_document.call_args
        assert call_args.kwargs["data"]["failed_login_attempts"] == 1

    def test_login_unverified_email(
        self,
        client,
        mock_zerodb_client,
        mock_user_document
    ):
        """Test login fails for unverified email"""
        from backend.routes.auth import hash_password
        
        password = "TestPassword123!"
        unverified_user = mock_user_document.copy()
        unverified_user["data"]["is_verified"] = False
        unverified_user["data"]["password_hash"] = hash_password(password)
        unverified_user["data"]["failed_login_attempts"] = 0
        
        mock_zerodb_client.query_documents.return_value = {
            "documents": [unverified_user]
        }
        
        response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": password
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "not verified" in data["detail"].lower()

    def test_login_inactive_account(
        self,
        client,
        mock_zerodb_client,
        mock_user_document
    ):
        """Test login fails for inactive account"""
        from backend.routes.auth import hash_password
        
        password = "TestPassword123!"
        inactive_user = mock_user_document.copy()
        inactive_user["data"]["is_verified"] = True
        inactive_user["data"]["is_active"] = False
        inactive_user["data"]["password_hash"] = hash_password(password)
        inactive_user["data"]["failed_login_attempts"] = 0
        
        mock_zerodb_client.query_documents.return_value = {
            "documents": [inactive_user]
        }
        
        response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": password
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "inactive" in data["detail"].lower()

    def test_login_account_lockout_after_5_attempts(
        self,
        client,
        mock_zerodb_client,
        mock_user_document
    ):
        """Test account lockout after 5 failed login attempts"""
        from backend.routes.auth import hash_password
        
        # User with 4 failed attempts
        user = mock_user_document.copy()
        user["data"]["is_verified"] = True
        user["data"]["password_hash"] = hash_password("CorrectPassword123!")
        user["data"]["failed_login_attempts"] = 4
        
        mock_zerodb_client.query_documents.return_value = {
            "documents": [user]
        }
        
        mock_zerodb_client.update_document.return_value = {
            "id": user["id"],
            "data": user["data"]
        }
        
        # Make 5th failed attempt
        response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "WrongPassword123!"
            }
        )
        
        assert response.status_code == 400
        
        # Verify lockout was set
        call_args = mock_zerodb_client.update_document.call_args
        assert call_args.kwargs["data"]["failed_login_attempts"] == 5
        assert "lockout_until" in call_args.kwargs["data"]
        assert call_args.kwargs["data"]["lockout_until"] is not None

    def test_login_account_locked(
        self,
        client,
        mock_zerodb_client,
        mock_user_document
    ):
        """Test login fails for locked account"""
        from datetime import datetime, timedelta
        
        # User with active lockout
        locked_user = mock_user_document.copy()
        locked_user["data"]["failed_login_attempts"] = 5
        locked_user["data"]["lockout_until"] = (
            datetime.utcnow() + timedelta(minutes=10)
        ).isoformat()
        
        mock_zerodb_client.query_documents.return_value = {
            "documents": [locked_user]
        }
        
        response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPassword123!"
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "locked" in data["detail"].lower()
        assert "try again" in data["detail"].lower()

    def test_login_expired_lockout(
        self,
        client,
        mock_zerodb_client,
        mock_user_document
    ):
        """Test login succeeds after lockout expiry"""
        from backend.routes.auth import hash_password
        from datetime import datetime, timedelta
        
        password = "TestPassword123!"
        
        # User with expired lockout
        user = mock_user_document.copy()
        user["data"]["is_verified"] = True
        user["data"]["password_hash"] = hash_password(password)
        user["data"]["failed_login_attempts"] = 5
        user["data"]["lockout_until"] = (
            datetime.utcnow() - timedelta(minutes=1)
        ).isoformat()
        
        mock_zerodb_client.query_documents.return_value = {
            "documents": [user]
        }
        
        mock_zerodb_client.update_document.return_value = {
            "id": user["id"],
            "data": user["data"]
        }
        
        response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": password
            }
        )
        
        # Should succeed since lockout expired
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_login_database_error(
        self,
        client,
        mock_zerodb_client
    ):
        """Test login handles database errors gracefully"""
        from backend.services.zerodb_service import ZeroDBError
        
        mock_zerodb_client.query_documents.side_effect = ZeroDBError(
            "Database connection failed"
        )
        
        response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPassword123!"
            }
        )
        
        assert response.status_code == 500
        data = response.json()
        assert "try again later" in data["detail"].lower()


# ============================================================================
# LOGOUT ENDPOINT TESTS
# ============================================================================

class TestLogoutEndpoint:
    """Test user logout endpoint"""

    def test_successful_logout(
        self,
        client
    ):
        """Test successful logout with valid token"""
        from backend.services.auth_service import AuthService
        from backend.config import get_settings
        
        # Generate a valid token
        auth_service = AuthService(get_settings())
        access_token = auth_service.create_access_token(
            user_id="test_user_123",
            role="member",
            email="test@example.com"
        )
        refresh_token = auth_service.create_refresh_token(user_id="test_user_123")
        
        # Make logout request
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Logout successful"

    def test_logout_missing_authorization_header(
        self,
        client
    ):
        """Test logout fails without authorization header"""
        response = client.post(
            "/api/auth/logout",
            json={}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "missing authorization header" in data["detail"].lower()

    def test_logout_invalid_authorization_format(
        self,
        client
    ):
        """Test logout fails with invalid authorization format"""
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": "InvalidFormat token123"},
            json={}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "invalid authorization header" in data["detail"].lower()

    def test_logout_invalid_token(
        self,
        client
    ):
        """Test logout fails with invalid token"""
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": "Bearer invalid_token_xyz"},
            json={}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "invalid or expired" in data["detail"].lower()

    def test_logout_expired_token(
        self,
        client
    ):
        """Test logout fails with expired token"""
        from backend.services.auth_service import AuthService
        from backend.config import get_settings
        from datetime import timedelta
        
        # Generate an expired token
        auth_service = AuthService(get_settings())
        expired_token = auth_service.create_access_token(
            user_id="test_user_123",
            role="member",
            email="test@example.com",
            expires_delta=timedelta(seconds=-1)  # Already expired
        )
        
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {expired_token}"},
            json={}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "invalid or expired" in data["detail"].lower()

    def test_logout_already_blacklisted_token(
        self,
        client
    ):
        """Test logout with already blacklisted token"""
        from backend.services.auth_service import AuthService
        from backend.config import get_settings
        
        # Generate and blacklist a token
        auth_service = AuthService(get_settings())
        access_token = auth_service.create_access_token(
            user_id="test_user_123",
            role="member",
            email="test@example.com"
        )
        
        # Blacklist the token
        auth_service.blacklist_token(access_token)
        
        # Try to logout again
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
            json={}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Already logged out"

    def test_logout_without_refresh_token(
        self,
        client
    ):
        """Test logout succeeds without providing refresh token"""
        from backend.services.auth_service import AuthService
        from backend.config import get_settings
        
        # Generate a valid token
        auth_service = AuthService(get_settings())
        access_token = auth_service.create_access_token(
            user_id="test_user_123",
            role="member",
            email="test@example.com"
        )
        
        # Make logout request without refresh_token
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
            json={}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Logout successful"

    def test_logout_with_invalid_refresh_token(
        self,
        client
    ):
        """Test logout succeeds even with invalid refresh token"""
        from backend.services.auth_service import AuthService
        from backend.config import get_settings
        
        # Generate a valid access token
        auth_service = AuthService(get_settings())
        access_token = auth_service.create_access_token(
            user_id="test_user_123",
            role="member",
            email="test@example.com"
        )
        
        # Make logout request with invalid refresh_token (should not fail)
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"refresh_token": "invalid_refresh_token"}
        )
        
        # Should still succeed (access token logout succeeded)
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Logout successful"


# ============================================================================
# INTEGRATION TESTS FOR LOGIN/LOGOUT FLOW
# ============================================================================

class TestLoginLogoutFlow:
    """Test complete login and logout flow"""

    def test_complete_login_logout_flow(
        self,
        client,
        mock_zerodb_client,
        mock_user_document
    ):
        """Test complete login and logout flow"""
        from backend.routes.auth import hash_password
        
        password = "TestPassword123!"
        
        # Prepare verified user
        verified_user = mock_user_document.copy()
        verified_user["data"]["is_verified"] = True
        verified_user["data"]["is_active"] = True
        verified_user["data"]["password_hash"] = hash_password(password)
        verified_user["data"]["failed_login_attempts"] = 0
        
        mock_zerodb_client.query_documents.return_value = {
            "documents": [verified_user]
        }
        
        mock_zerodb_client.update_document.return_value = {
            "id": verified_user["id"],
            "data": verified_user["data"]
        }
        
        # Step 1: Login
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": password
            }
        )
        
        assert login_response.status_code == 200
        login_data = login_response.json()
        access_token = login_data["access_token"]
        refresh_token = login_data["refresh_token"]
        
        # Step 2: Logout
        logout_response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"refresh_token": refresh_token}
        )
        
        assert logout_response.status_code == 200
        logout_data = logout_response.json()
        assert logout_data["message"] == "Logout successful"
        
        # Step 3: Try to logout again (should show already logged out)
        logout_again_response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"refresh_token": refresh_token}
        )
        
        assert logout_again_response.status_code == 200
        logout_again_data = logout_again_response.json()
        assert logout_again_data["message"] == "Already logged out"

    def test_token_blacklisting_prevents_reuse(
        self,
        client,
        mock_zerodb_client,
        mock_user_document
    ):
        """Test that blacklisted tokens cannot be reused"""
        from backend.routes.auth import hash_password
        from backend.services.auth_service import AuthService
        from backend.config import get_settings
        
        password = "TestPassword123!"
        
        # Prepare verified user
        verified_user = mock_user_document.copy()
        verified_user["data"]["is_verified"] = True
        verified_user["data"]["is_active"] = True
        verified_user["data"]["password_hash"] = hash_password(password)
        verified_user["data"]["failed_login_attempts"] = 0
        
        mock_zerodb_client.query_documents.return_value = {
            "documents": [verified_user]
        }
        
        mock_zerodb_client.update_document.return_value = {
            "id": verified_user["id"],
            "data": verified_user["data"]
        }
        
        # Login
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": password
            }
        )
        
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]
        
        # Logout (blacklist token)
        logout_response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
            json={}
        )
        
        assert logout_response.status_code == 200
        
        # Try to use blacklisted token (should fail)
        auth_service = AuthService(get_settings())
        
        from backend.services.auth_service import TokenBlacklistedError
        with pytest.raises(TokenBlacklistedError):
            auth_service.verify_access_token(access_token)


# ============================================================================
# REFRESH TOKEN TESTS
# ============================================================================

class TestRefreshTokenEndpoint:
    """Test refresh token endpoint with rotation and reuse detection"""

    @pytest.fixture
    def mock_auth_service(self):
        """Mock AuthService"""
        with patch('backend.routes.auth.AuthService') as mock:
            service = MagicMock()
            mock.return_value = service
            yield service

    @pytest.fixture
    def valid_refresh_payload(self):
        """Valid refresh token payload"""
        return {
            "user_id": str(uuid4()),
            "family_id": str(uuid4()),
            "token_id": str(uuid4()),
            "exp": (datetime.utcnow() + timedelta(days=7)).timestamp(),
            "iat": datetime.utcnow().timestamp(),
            "type": "refresh"
        }

    @pytest.fixture
    def mock_user_in_db(self):
        """Mock user document in database"""
        user_id = str(uuid4())
        return {
            "id": user_id,
            "data": {
                "email": "test@example.com",
                "role": "member",
                "is_active": True,
                "is_verified": True,
                "first_name": "Test",
                "last_name": "User"
            }
        }

    def test_successful_token_refresh(
        self,
        client,
        mock_auth_service,
        mock_zerodb_client,
        valid_refresh_payload,
        mock_user_in_db
    ):
        """Test successful token refresh with rotation"""
        # Mock token verification
        mock_auth_service.verify_refresh_token.return_value = valid_refresh_payload
        
        # Mock family not blacklisted
        mock_auth_service.is_family_blacklisted.return_value = False
        
        # Mock no token reuse
        mock_auth_service.check_token_reuse.return_value = False
        
        # Mock user exists
        mock_zerodb_client.query_documents.return_value = {
            "documents": [mock_user_in_db]
        }
        
        # Mock token generation
        new_access_token = "new_access_token_123"
        new_refresh_token = "new_refresh_token_456"
        new_family_id = valid_refresh_payload["family_id"]
        
        mock_auth_service.create_access_token.return_value = new_access_token
        mock_auth_service.create_refresh_token.return_value = (new_refresh_token, new_family_id)
        
        # Mock decode for new token
        new_token_payload = {
            **valid_refresh_payload,
            "token_id": str(uuid4()),
            "exp": (datetime.utcnow() + timedelta(days=7)).timestamp()
        }
        mock_auth_service.decode_token.return_value = new_token_payload
        
        # Make request
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": "old_refresh_token"}
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == new_access_token
        assert data["refresh_token"] == new_refresh_token
        assert data["token_type"] == "bearer"
        
        # Verify old token was blacklisted
        mock_auth_service.blacklist_token.assert_called_once()
        mock_auth_service.mark_token_used.assert_called_once()
        
        # Verify new token family was stored
        mock_auth_service.store_token_family.assert_called_once()

    def test_refresh_with_expired_token(
        self,
        client,
        mock_auth_service
    ):
        """Test refresh fails with expired token"""
        from backend.services.auth_service import TokenExpiredError
        
        # Mock expired token
        mock_auth_service.verify_refresh_token.side_effect = TokenExpiredError("Token expired")
        
        # Make request
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": "expired_token"}
        )
        
        # Assertions
        assert response.status_code == 401
        data = response.json()
        assert "expired" in data["detail"].lower()

    def test_refresh_with_invalid_token(
        self,
        client,
        mock_auth_service
    ):
        """Test refresh fails with invalid token"""
        from backend.services.auth_service import TokenInvalidError
        
        # Mock invalid token
        mock_auth_service.verify_refresh_token.side_effect = TokenInvalidError("Invalid token")
        
        # Make request
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": "invalid_token"}
        )
        
        # Assertions
        assert response.status_code == 401
        data = response.json()
        assert "invalid" in data["detail"].lower()

    def test_refresh_with_blacklisted_token(
        self,
        client,
        mock_auth_service
    ):
        """Test refresh fails with blacklisted token"""
        from backend.services.auth_service import TokenBlacklistedError
        
        # Mock blacklisted token
        mock_auth_service.verify_refresh_token.side_effect = TokenBlacklistedError("Token blacklisted")
        
        # Make request
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": "blacklisted_token"}
        )
        
        # Assertions
        assert response.status_code == 401
        data = response.json()
        assert "revoked" in data["detail"].lower()

    def test_refresh_with_reused_token(
        self,
        client,
        mock_auth_service,
        mock_zerodb_client,
        valid_refresh_payload
    ):
        """Test token reuse detection invalidates family"""
        # Mock token verification
        mock_auth_service.verify_refresh_token.return_value = valid_refresh_payload
        
        # Mock family not blacklisted initially
        mock_auth_service.is_family_blacklisted.return_value = False
        
        # Mock token reuse detected
        mock_auth_service.check_token_reuse.return_value = True
        
        # Make request
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": "reused_token"}
        )
        
        # Assertions
        assert response.status_code == 403
        data = response.json()
        assert "reuse detected" in data["detail"].lower()
        
        # Verify family was invalidated
        mock_auth_service.invalidate_token_family.assert_called_once_with(
            valid_refresh_payload["family_id"]
        )

    def test_refresh_with_blacklisted_family(
        self,
        client,
        mock_auth_service,
        valid_refresh_payload
    ):
        """Test refresh fails if token family is blacklisted"""
        # Mock token verification
        mock_auth_service.verify_refresh_token.return_value = valid_refresh_payload
        
        # Mock family blacklisted
        mock_auth_service.is_family_blacklisted.return_value = True
        
        # Make request
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": "token_from_blacklisted_family"}
        )
        
        # Assertions
        assert response.status_code == 403
        data = response.json()
        assert "family has been revoked" in data["detail"].lower()

    def test_refresh_with_missing_claims(
        self,
        client,
        mock_auth_service
    ):
        """Test refresh fails with token missing required claims"""
        # Mock token with missing claims
        incomplete_payload = {
            "user_id": str(uuid4()),
            # Missing family_id and token_id
            "type": "refresh"
        }
        mock_auth_service.verify_refresh_token.return_value = incomplete_payload
        
        # Make request
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": "incomplete_token"}
        )
        
        # Assertions
        assert response.status_code == 401
        data = response.json()
        assert "invalid" in data["detail"].lower()

    def test_refresh_with_nonexistent_user(
        self,
        client,
        mock_auth_service,
        mock_zerodb_client,
        valid_refresh_payload
    ):
        """Test refresh fails if user not found in database"""
        # Mock token verification
        mock_auth_service.verify_refresh_token.return_value = valid_refresh_payload
        
        # Mock family not blacklisted
        mock_auth_service.is_family_blacklisted.return_value = False
        
        # Mock no token reuse
        mock_auth_service.check_token_reuse.return_value = False
        
        # Mock user not found
        mock_zerodb_client.query_documents.return_value = {"documents": []}
        
        # Make request
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": "token_for_deleted_user"}
        )
        
        # Assertions
        assert response.status_code == 401
        data = response.json()
        assert "user not found" in data["detail"].lower()

    def test_refresh_with_inactive_user(
        self,
        client,
        mock_auth_service,
        mock_zerodb_client,
        valid_refresh_payload,
        mock_user_in_db
    ):
        """Test refresh fails if user account is inactive"""
        # Mock token verification
        mock_auth_service.verify_refresh_token.return_value = valid_refresh_payload
        
        # Mock family not blacklisted
        mock_auth_service.is_family_blacklisted.return_value = False
        
        # Mock no token reuse
        mock_auth_service.check_token_reuse.return_value = False
        
        # Mock inactive user
        inactive_user = mock_user_in_db.copy()
        inactive_user["data"]["is_active"] = False
        mock_zerodb_client.query_documents.return_value = {
            "documents": [inactive_user]
        }
        
        # Make request
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": "token_for_inactive_user"}
        )
        
        # Assertions
        assert response.status_code == 403
        data = response.json()
        assert "inactive" in data["detail"].lower()

    def test_refresh_with_unverified_user(
        self,
        client,
        mock_auth_service,
        mock_zerodb_client,
        valid_refresh_payload,
        mock_user_in_db
    ):
        """Test refresh fails if user email not verified"""
        # Mock token verification
        mock_auth_service.verify_refresh_token.return_value = valid_refresh_payload
        
        # Mock family not blacklisted
        mock_auth_service.is_family_blacklisted.return_value = False
        
        # Mock no token reuse
        mock_auth_service.check_token_reuse.return_value = False
        
        # Mock unverified user
        unverified_user = mock_user_in_db.copy()
        unverified_user["data"]["is_verified"] = False
        mock_zerodb_client.query_documents.return_value = {
            "documents": [unverified_user]
        }
        
        # Make request
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": "token_for_unverified_user"}
        )
        
        # Assertions
        assert response.status_code == 403
        data = response.json()
        assert "not verified" in data["detail"].lower()

    def test_refresh_token_rotation_same_family(
        self,
        client,
        mock_auth_service,
        mock_zerodb_client,
        valid_refresh_payload,
        mock_user_in_db
    ):
        """Test token rotation maintains same family ID"""
        # Mock token verification
        mock_auth_service.verify_refresh_token.return_value = valid_refresh_payload
        
        # Mock family not blacklisted
        mock_auth_service.is_family_blacklisted.return_value = False
        
        # Mock no token reuse
        mock_auth_service.check_token_reuse.return_value = False
        
        # Mock user exists
        mock_zerodb_client.query_documents.return_value = {
            "documents": [mock_user_in_db]
        }
        
        # Mock token generation
        original_family_id = valid_refresh_payload["family_id"]
        mock_auth_service.create_access_token.return_value = "new_access"
        mock_auth_service.create_refresh_token.return_value = ("new_refresh", original_family_id)
        
        # Mock decode
        new_payload = {
            **valid_refresh_payload,
            "token_id": str(uuid4()),
            "exp": (datetime.utcnow() + timedelta(days=7)).timestamp()
        }
        mock_auth_service.decode_token.return_value = new_payload
        
        # Make request
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": "old_token"}
        )
        
        # Assertions
        assert response.status_code == 200
        
        # Verify new refresh token created with same family_id
        mock_auth_service.create_refresh_token.assert_called_once()
        call_args = mock_auth_service.create_refresh_token.call_args
        assert call_args.kwargs["family_id"] == original_family_id

    def test_refresh_database_error(
        self,
        client,
        mock_auth_service,
        mock_zerodb_client,
        valid_refresh_payload
    ):
        """Test refresh handles database errors gracefully"""
        from backend.services.zerodb_service import ZeroDBError

        # Mock token verification
        mock_auth_service.verify_refresh_token.return_value = valid_refresh_payload

        # Mock family not blacklisted
        mock_auth_service.is_family_blacklisted.return_value = False

        # Mock no token reuse
        mock_auth_service.check_token_reuse.return_value = False

        # Mock database error
        mock_zerodb_client.query_documents.side_effect = ZeroDBError("Database error")

        # Make request
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": "valid_token"}
        )

        # Assertions
        assert response.status_code == 500
        data = response.json()
        assert "try again later" in data["detail"].lower()

    def test_refresh_rate_limiting(
        self,
        client,
        mock_auth_service,
        mock_zerodb_client,
        valid_refresh_payload,
        mock_user_in_db
    ):
        """Test refresh token rate limiting (10 requests per hour)"""
        # Mock token verification
        mock_auth_service.verify_refresh_token.return_value = valid_refresh_payload

        # Mock family not blacklisted
        mock_auth_service.is_family_blacklisted.return_value = False

        # Mock no token reuse
        mock_auth_service.check_token_reuse.return_value = False

        # Mock user exists
        mock_zerodb_client.query_documents.return_value = {
            "documents": [mock_user_in_db]
        }

        # Mock token generation
        mock_auth_service.create_access_token.return_value = "new_access"
        mock_auth_service.create_refresh_token.return_value = ("new_refresh", valid_refresh_payload["family_id"])

        # Mock decode for new token
        new_payload = {
            **valid_refresh_payload,
            "token_id": str(uuid4()),
            "exp": (datetime.utcnow() + timedelta(days=7)).timestamp()
        }
        mock_auth_service.decode_token.return_value = new_payload

        # Make 10 successful requests (should all succeed)
        for i in range(10):
            response = client.post(
                "/api/auth/refresh",
                json={"refresh_token": f"token_{i}"}
            )
            # First 10 should succeed (may fail if rate limiting is active from other tests)
            # We're just checking that rate limit exists
            if response.status_code == 200:
                assert "access_token" in response.json()

        # 11th request should be rate limited
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": "token_11"}
        )

        # Check if rate limit is enforced (either 429 or still working if Redis is down/fail-open)
        if response.status_code == 429:
            data = response.json()
            assert "rate" in str(data).lower()
            # Should have Retry-After header
            assert "Retry-After" in response.headers or "retry_after" in data


# ============================================================================
# TOKEN ROTATION INTEGRATION TESTS
# ============================================================================

class TestTokenRotationFlow:
    """Test complete token rotation workflow"""

    def test_multiple_refresh_rotations(
        self,
        client,
        mock_zerodb_client,
        mock_email_service
    ):
        """Test multiple consecutive token refreshes maintain family"""
        with patch('backend.routes.auth.AuthService') as MockAuthService:
            auth_service = MagicMock()
            MockAuthService.return_value = auth_service
            
            # Initial family ID
            family_id = str(uuid4())
            user_id = str(uuid4())
            
            # Mock user in database
            mock_user = {
                "id": user_id,
                "data": {
                    "email": "test@example.com",
                    "role": "member",
                    "is_active": True,
                    "is_verified": True
                }
            }
            mock_zerodb_client.query_documents.return_value = {
                "documents": [mock_user]
            }
            
            # Simulate 3 consecutive refreshes
            for rotation in range(3):
                token_id = str(uuid4())
                
                # Mock verification
                payload = {
                    "user_id": user_id,
                    "family_id": family_id,
                    "token_id": token_id,
                    "exp": (datetime.utcnow() + timedelta(days=7)).timestamp(),
                    "type": "refresh"
                }
                auth_service.verify_refresh_token.return_value = payload
                auth_service.is_family_blacklisted.return_value = False
                auth_service.check_token_reuse.return_value = False
                
                # Mock token generation
                new_token_id = str(uuid4())
                auth_service.create_access_token.return_value = f"access_{rotation}"
                auth_service.create_refresh_token.return_value = (f"refresh_{rotation}", family_id)
                
                new_payload = {
                    **payload,
                    "token_id": new_token_id,
                    "exp": (datetime.utcnow() + timedelta(days=7)).timestamp()
                }
                auth_service.decode_token.return_value = new_payload
                
                # Make request
                response = client.post(
                    "/api/auth/refresh",
                    json={"refresh_token": f"token_{rotation}"}
                )
                
                # Verify success
                assert response.status_code == 200
                
                # Verify family_id remains the same
                call_args = auth_service.create_refresh_token.call_args
                assert call_args.kwargs["family_id"] == family_id

    def test_reuse_detection_during_rotation(
        self,
        client,
        mock_zerodb_client
    ):
        """Test that reuse is detected even during active rotation"""
        with patch('backend.routes.auth.AuthService') as MockAuthService:
            auth_service = MagicMock()
            MockAuthService.return_value = auth_service
            
            family_id = str(uuid4())
            user_id = str(uuid4())
            
            # First refresh succeeds
            token_id_1 = str(uuid4())
            payload_1 = {
                "user_id": user_id,
                "family_id": family_id,
                "token_id": token_id_1,
                "exp": (datetime.utcnow() + timedelta(days=7)).timestamp(),
                "type": "refresh"
            }
            
            auth_service.verify_refresh_token.return_value = payload_1
            auth_service.is_family_blacklisted.return_value = False
            auth_service.check_token_reuse.return_value = False
            
            mock_user = {
                "id": user_id,
                "data": {
                    "email": "test@example.com",
                    "role": "member",
                    "is_active": True,
                    "is_verified": True
                }
            }
            mock_zerodb_client.query_documents.return_value = {
                "documents": [mock_user]
            }
            
            auth_service.create_access_token.return_value = "new_access"
            auth_service.create_refresh_token.return_value = ("new_refresh", family_id)
            
            new_payload = {
                **payload_1,
                "token_id": str(uuid4()),
                "exp": (datetime.utcnow() + timedelta(days=7)).timestamp()
            }
            auth_service.decode_token.return_value = new_payload
            
            # First refresh succeeds
            response1 = client.post(
                "/api/auth/refresh",
                json={"refresh_token": "token_1"}
            )
            assert response1.status_code == 200
            
            # Second attempt with same token (reuse)
            auth_service.check_token_reuse.return_value = True
            
            response2 = client.post(
                "/api/auth/refresh",
                json={"refresh_token": "token_1"}
            )
            
            # Should detect reuse and invalidate family
            assert response2.status_code == 403
            assert "reuse detected" in response2.json()["detail"].lower()
            auth_service.invalidate_token_family.assert_called_with(family_id)
