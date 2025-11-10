"""
Unit Tests - Validation Functions

Tests Pydantic schemas and custom validation logic.

Test Coverage:
- Email validation
- Phone number validation
- State code validation
- Date range validation
- Discount percentage validation
- Required field validation
- Data type validation
"""

import pytest
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, ValidationError, field_validator, EmailStr


# Mock Pydantic models - These will be replaced with actual implementation
class UserSchema(BaseModel):
    """User data validation schema"""
    email: EmailStr
    first_name: str
    last_name: str
    state: str
    phone: Optional[str] = None

    @field_validator('state')
    @classmethod
    def validate_state(cls, v: str) -> str:
        """Validate US state code"""
        valid_states = [
            'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
            'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
            'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
            'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
            'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
        ]
        if v.upper() not in valid_states:
            raise ValueError(f"Invalid state code: {v}")
        return v.upper()

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format"""
        if v is None:
            return v

        # Remove common separators
        cleaned = v.replace('-', '').replace('(', '').replace(')', '').replace(' ', '')

        if not cleaned.isdigit():
            raise ValueError("Phone number must contain only digits")

        if len(cleaned) != 10:
            raise ValueError("Phone number must be 10 digits")

        return cleaned


class PromotionSchema(BaseModel):
    """Promotion data validation schema"""
    title: str
    description: str
    discount_percentage: int
    start_date: datetime
    end_date: datetime

    @field_validator('discount_percentage')
    @classmethod
    def validate_discount(cls, v: int) -> int:
        """Validate discount percentage is between 1 and 100"""
        if v < 1 or v > 100:
            raise ValueError("Discount percentage must be between 1 and 100")
        return v

    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v: datetime, info) -> datetime:
        """Validate end_date is after start_date"""
        if 'start_date' in info.data:
            start_date = info.data['start_date']
            if v <= start_date:
                raise ValueError("end_date must be after start_date")
        return v


# ============================================================================
# TEST CLASS: User Validation Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.validation
class TestUserValidation:
    """Test suite for user data validation"""

    def test_valid_user_data(self):
        """Test validation passes with valid user data"""
        # Arrange
        user_data = {
            "email": "john.doe@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "state": "CA",
            "phone": "555-123-4567"
        }

        # Act
        user = UserSchema(**user_data)

        # Assert
        assert user.email == "john.doe@example.com"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.state == "CA"
        assert user.phone == "5551234567"  # Cleaned phone number

    def test_invalid_email_format(self):
        """Test validation fails with invalid email"""
        # Arrange
        user_data = {
            "email": "not-an-email",
            "first_name": "John",
            "last_name": "Doe",
            "state": "CA"
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            UserSchema(**user_data)

        # Assert error message contains email validation issue
        assert "email" in str(exc_info.value).lower()

    def test_invalid_state_code(self):
        """Test validation fails with invalid state code"""
        # Arrange
        user_data = {
            "email": "john.doe@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "state": "XX"  # Invalid state code
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            UserSchema(**user_data)

        # Assert
        assert "Invalid state code" in str(exc_info.value)

    def test_state_code_case_insensitive(self):
        """Test state codes are converted to uppercase"""
        # Arrange
        user_data = {
            "email": "john.doe@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "state": "ca"  # Lowercase
        }

        # Act
        user = UserSchema(**user_data)

        # Assert
        assert user.state == "CA"  # Should be uppercase

    def test_missing_required_field(self):
        """Test validation fails when required fields are missing"""
        # Arrange
        user_data = {
            "email": "john.doe@example.com",
            "first_name": "John",
            # Missing last_name and state
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            UserSchema(**user_data)

        # Assert multiple missing fields
        error_str = str(exc_info.value)
        assert "last_name" in error_str
        assert "state" in error_str

    def test_phone_number_cleaning(self):
        """Test phone numbers are cleaned and validated"""
        # Arrange
        user_data = {
            "email": "john.doe@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "state": "CA",
            "phone": "(555) 123-4567"
        }

        # Act
        user = UserSchema(**user_data)

        # Assert
        assert user.phone == "5551234567"

    def test_invalid_phone_number_length(self):
        """Test validation fails with wrong phone number length"""
        # Arrange
        user_data = {
            "email": "john.doe@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "state": "CA",
            "phone": "123456789"  # Only 9 digits
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            UserSchema(**user_data)

        # Assert
        assert "10 digits" in str(exc_info.value)

    def test_phone_number_with_letters(self):
        """Test validation fails with non-numeric phone"""
        # Arrange
        user_data = {
            "email": "john.doe@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "state": "CA",
            "phone": "555-CALL-NOW"
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            UserSchema(**user_data)

        # Assert
        assert "only digits" in str(exc_info.value)

    def test_optional_phone_field(self):
        """Test phone number is optional"""
        # Arrange
        user_data = {
            "email": "john.doe@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "state": "CA"
            # No phone provided
        }

        # Act
        user = UserSchema(**user_data)

        # Assert
        assert user.phone is None


# ============================================================================
# TEST CLASS: Promotion Validation Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.validation
class TestPromotionValidation:
    """Test suite for promotion data validation"""

    def test_valid_promotion_data(self):
        """Test validation passes with valid promotion data"""
        # Arrange
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=30)

        promo_data = {
            "title": "Summer Sale",
            "description": "Get 20% off all items",
            "discount_percentage": 20,
            "start_date": start_date,
            "end_date": end_date
        }

        # Act
        promo = PromotionSchema(**promo_data)

        # Assert
        assert promo.title == "Summer Sale"
        assert promo.discount_percentage == 20
        assert promo.end_date > promo.start_date

    def test_discount_percentage_too_low(self):
        """Test validation fails with discount below 1"""
        # Arrange
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=30)

        promo_data = {
            "title": "Sale",
            "description": "Description",
            "discount_percentage": 0,  # Invalid
            "start_date": start_date,
            "end_date": end_date
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            PromotionSchema(**promo_data)

        # Assert
        assert "between 1 and 100" in str(exc_info.value)

    def test_discount_percentage_too_high(self):
        """Test validation fails with discount above 100"""
        # Arrange
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=30)

        promo_data = {
            "title": "Sale",
            "description": "Description",
            "discount_percentage": 101,  # Invalid
            "start_date": start_date,
            "end_date": end_date
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            PromotionSchema(**promo_data)

        # Assert
        assert "between 1 and 100" in str(exc_info.value)

    def test_end_date_before_start_date(self):
        """Test validation fails when end_date is before start_date"""
        # Arrange
        start_date = datetime.utcnow()
        end_date = start_date - timedelta(days=1)  # Before start_date

        promo_data = {
            "title": "Sale",
            "description": "Description",
            "discount_percentage": 20,
            "start_date": start_date,
            "end_date": end_date
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            PromotionSchema(**promo_data)

        # Assert
        assert "after start_date" in str(exc_info.value)

    def test_end_date_same_as_start_date(self):
        """Test validation fails when end_date equals start_date"""
        # Arrange
        date = datetime.utcnow()

        promo_data = {
            "title": "Sale",
            "description": "Description",
            "discount_percentage": 20,
            "start_date": date,
            "end_date": date  # Same as start
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            PromotionSchema(**promo_data)

        # Assert
        assert "after start_date" in str(exc_info.value)

    @pytest.mark.parametrize("discount", [1, 25, 50, 75, 100])
    def test_valid_discount_percentages(self, discount):
        """Test various valid discount percentages"""
        # Arrange
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=30)

        promo_data = {
            "title": "Sale",
            "description": "Description",
            "discount_percentage": discount,
            "start_date": start_date,
            "end_date": end_date
        }

        # Act
        promo = PromotionSchema(**promo_data)

        # Assert
        assert promo.discount_percentage == discount
