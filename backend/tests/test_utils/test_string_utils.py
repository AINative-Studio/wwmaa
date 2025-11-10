"""
Unit Tests - String Utility Functions

Tests string manipulation, formatting, and search query normalization.

Test Coverage:
- String normalization
- Search query cleaning
- Slug generation
- Name formatting
- Text truncation
- Case conversion
"""

import pytest
from typing import Optional


# Mock utility functions - These will be replaced with actual implementation
def normalize_search_query(query: str) -> str:
    """
    Normalize a search query for consistent searching.

    - Convert to lowercase
    - Remove extra whitespace
    - Remove special characters (except spaces and hyphens)
    - Trim leading/trailing whitespace
    """
    if not query:
        return ""

    # Convert to lowercase
    normalized = query.lower()

    # Remove special characters except spaces, hyphens, and alphanumeric
    import re
    normalized = re.sub(r'[^a-z0-9\s-]', '', normalized)

    # Replace multiple spaces with single space
    normalized = re.sub(r'\s+', ' ', normalized)

    # Trim whitespace
    normalized = normalized.strip()

    return normalized


def generate_slug(text: str) -> str:
    """
    Generate a URL-friendly slug from text.

    - Convert to lowercase
    - Replace spaces with hyphens
    - Remove special characters
    - Remove duplicate hyphens
    """
    if not text:
        return ""

    import re

    # Convert to lowercase
    slug = text.lower()

    # Replace spaces and underscores with hyphens
    slug = slug.replace(' ', '-').replace('_', '-')

    # Remove special characters except hyphens
    slug = re.sub(r'[^a-z0-9-]', '', slug)

    # Remove duplicate hyphens
    slug = re.sub(r'-+', '-', slug)

    # Remove leading/trailing hyphens
    slug = slug.strip('-')

    return slug


def format_full_name(first_name: str, last_name: str, middle_name: Optional[str] = None) -> str:
    """Format a person's full name"""
    if middle_name:
        return f"{first_name} {middle_name} {last_name}"
    return f"{first_name} {last_name}"


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length, adding suffix if truncated.
    Tries to break at word boundaries.
    """
    if len(text) <= max_length:
        return text

    # Account for suffix length
    truncate_at = max_length - len(suffix)

    # Try to find last space before truncate point
    last_space = text[:truncate_at].rfind(' ')

    if last_space > 0:
        return text[:last_space] + suffix

    # No space found, just hard truncate
    return text[:truncate_at] + suffix


def format_phone_number(phone: str) -> str:
    """
    Format a phone number as (XXX) XXX-XXXX.
    Input should be 10 digits.
    """
    # Remove any non-digit characters
    digits = ''.join(c for c in phone if c.isdigit())

    if len(digits) != 10:
        raise ValueError("Phone number must have exactly 10 digits")

    return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"


def to_title_case(text: str) -> str:
    """
    Convert text to title case, handling special cases.
    - Capitalize first letter of each word
    - Handle abbreviations like US, CA, etc.
    """
    # List of words that should stay lowercase (unless first word)
    lowercase_words = {'a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor', 'on', 'at', 'to', 'by', 'of', 'in'}

    words = text.split()
    result = []

    for i, word in enumerate(words):
        # First word is always capitalized
        if i == 0:
            result.append(word.capitalize())
        # Check if word should stay lowercase
        elif word.lower() in lowercase_words:
            result.append(word.lower())
        else:
            result.append(word.capitalize())

    return ' '.join(result)


# ============================================================================
# TEST CLASS: Search Query Normalization
# ============================================================================

@pytest.mark.unit
@pytest.mark.utils
class TestSearchQueryNormalization:
    """Test suite for search query normalization"""

    def test_normalize_simple_query(self):
        """Test normalizing a simple search query"""
        # Arrange
        query = "Test Query"

        # Act
        result = normalize_search_query(query)

        # Assert
        assert result == "test query"

    def test_normalize_removes_extra_whitespace(self):
        """Test that extra whitespace is removed"""
        # Arrange
        query = "test    query   with    spaces"

        # Act
        result = normalize_search_query(query)

        # Assert
        assert result == "test query with spaces"

    def test_normalize_removes_special_characters(self):
        """Test that special characters are removed"""
        # Arrange
        query = "test@query#with$special%chars"

        # Act
        result = normalize_search_query(query)

        # Assert
        assert result == "testquerywithspecialchars"

    def test_normalize_keeps_hyphens(self):
        """Test that hyphens are preserved"""
        # Arrange
        query = "test-query-with-hyphens"

        # Act
        result = normalize_search_query(query)

        # Assert
        assert result == "test-query-with-hyphens"

    def test_normalize_empty_string(self):
        """Test normalizing empty string"""
        # Arrange
        query = ""

        # Act
        result = normalize_search_query(query)

        # Assert
        assert result == ""

    def test_normalize_whitespace_only(self):
        """Test normalizing whitespace-only string"""
        # Arrange
        query = "   "

        # Act
        result = normalize_search_query(query)

        # Assert
        assert result == ""

    @pytest.mark.parametrize("query,expected", [
        ("Hello World", "hello world"),
        ("UPPERCASE", "uppercase"),
        ("MiXeD CaSe", "mixed case"),
        ("123 Numbers", "123 numbers"),
        ("Test-Hyphen", "test-hyphen"),
    ])
    def test_normalize_various_inputs(self, query, expected):
        """Test normalization with various inputs"""
        # Act
        result = normalize_search_query(query)

        # Assert
        assert result == expected


# ============================================================================
# TEST CLASS: Slug Generation
# ============================================================================

@pytest.mark.unit
@pytest.mark.utils
class TestSlugGeneration:
    """Test suite for URL slug generation"""

    def test_generate_simple_slug(self):
        """Test generating a simple slug"""
        # Arrange
        text = "Hello World"

        # Act
        result = generate_slug(text)

        # Assert
        assert result == "hello-world"

    def test_generate_slug_removes_special_chars(self):
        """Test that special characters are removed"""
        # Arrange
        text = "Hello! World?"

        # Act
        result = generate_slug(text)

        # Assert
        assert result == "hello-world"

    def test_generate_slug_replaces_spaces(self):
        """Test that spaces become hyphens"""
        # Arrange
        text = "Multiple Word Title"

        # Act
        result = generate_slug(text)

        # Assert
        assert result == "multiple-word-title"

    def test_generate_slug_removes_duplicate_hyphens(self):
        """Test that duplicate hyphens are removed"""
        # Arrange
        text = "Hello---World"

        # Act
        result = generate_slug(text)

        # Assert
        assert result == "hello-world"

    def test_generate_slug_empty_string(self):
        """Test slug generation with empty string"""
        # Arrange
        text = ""

        # Act
        result = generate_slug(text)

        # Assert
        assert result == ""


# ============================================================================
# TEST CLASS: Text Formatting
# ============================================================================

@pytest.mark.unit
@pytest.mark.utils
class TestTextFormatting:
    """Test suite for text formatting functions"""

    def test_format_full_name_without_middle(self):
        """Test formatting name without middle name"""
        # Arrange
        first = "John"
        last = "Doe"

        # Act
        result = format_full_name(first, last)

        # Assert
        assert result == "John Doe"

    def test_format_full_name_with_middle(self):
        """Test formatting name with middle name"""
        # Arrange
        first = "John"
        middle = "Michael"
        last = "Doe"

        # Act
        result = format_full_name(first, last, middle)

        # Assert
        assert result == "John Michael Doe"

    def test_truncate_short_text(self):
        """Test that short text is not truncated"""
        # Arrange
        text = "Short text"
        max_length = 20

        # Act
        result = truncate_text(text, max_length)

        # Assert
        assert result == "Short text"

    def test_truncate_long_text_at_word_boundary(self):
        """Test truncating long text at word boundary"""
        # Arrange
        text = "This is a very long text that needs to be truncated"
        max_length = 25

        # Act
        result = truncate_text(text, max_length)

        # Assert
        assert len(result) <= max_length
        assert result.endswith("...")
        assert result.startswith("This is a very")

    def test_truncate_with_custom_suffix(self):
        """Test truncation with custom suffix"""
        # Arrange
        text = "This is a very long text"
        max_length = 15
        suffix = " [more]"

        # Act
        result = truncate_text(text, max_length, suffix)

        # Assert
        assert result.endswith(" [more]")

    def test_format_phone_number(self):
        """Test phone number formatting"""
        # Arrange
        phone = "5551234567"

        # Act
        result = format_phone_number(phone)

        # Assert
        assert result == "(555) 123-4567"

    def test_format_phone_with_separators(self):
        """Test formatting phone that already has separators"""
        # Arrange
        phone = "555-123-4567"

        # Act
        result = format_phone_number(phone)

        # Assert
        assert result == "(555) 123-4567"

    def test_format_phone_invalid_length(self):
        """Test phone formatting with invalid length"""
        # Arrange
        phone = "123456789"  # Only 9 digits

        # Act & Assert
        with pytest.raises(ValueError, match="exactly 10 digits"):
            format_phone_number(phone)

    def test_to_title_case_simple(self):
        """Test title case conversion"""
        # Arrange
        text = "hello world"

        # Act
        result = to_title_case(text)

        # Assert
        assert result == "Hello World"

    def test_to_title_case_with_articles(self):
        """Test title case with articles that should be lowercase"""
        # Arrange
        text = "the quick brown fox"

        # Act
        result = to_title_case(text)

        # Assert
        assert result == "The Quick Brown Fox"  # First word capitalized

    @pytest.mark.parametrize("input_text,expected", [
        ("hello world", "Hello World"),
        ("UPPERCASE TEXT", "Uppercase Text"),
        ("mixed CaSe", "Mixed Case"),
        ("one", "One"),
    ])
    def test_title_case_variations(self, input_text, expected):
        """Test title case with various inputs"""
        # Act
        result = to_title_case(input_text)

        # Assert
        assert result == expected
