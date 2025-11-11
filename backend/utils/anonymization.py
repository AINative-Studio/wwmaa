"""
Anonymization Utilities for GDPR Compliance

This module provides utilities for anonymizing user data in compliance with GDPR
right to erasure requirements. It implements deterministic anonymization to
maintain referential integrity while removing Personally Identifiable Information (PII).

Key Features:
- Deterministic user ID hashing for referential integrity
- PII field removal (email, phone, address, etc.)
- Timestamp preservation for audit trails
- Non-PII field retention (IDs, counts, status fields)

Usage:
    from backend.utils.anonymization import anonymize_user_id, anonymize_document

    # Generate anonymized user identifier
    anon_id = anonymize_user_id("user_123")  # Returns: "Deleted User a1b2c3d4"

    # Anonymize a document
    anonymized = anonymize_document(user_data, AnonymizationType.USER)
"""

import hashlib
import logging
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class AnonymizationType(str, Enum):
    """Types of anonymization for different data categories"""
    USER = "user"
    PROFILE = "profile"
    APPLICATION = "application"
    SEARCH_QUERY = "search_query"
    TRAINING_ATTENDANCE = "training_attendance"
    RSVP = "rsvp"
    COMMENT = "comment"
    POST = "post"


# PII fields that must be removed/anonymized
PII_FIELDS = {
    "email",
    "phone",
    "phone_number",
    "address",
    "street_address",
    "city",
    "state",
    "postal_code",
    "zip_code",
    "country",
    "first_name",
    "last_name",
    "full_name",
    "name",
    "date_of_birth",
    "birth_date",
    "ssn",
    "social_security_number",
    "passport_number",
    "drivers_license",
    "emergency_contact",
    "emergency_phone",
    "bio",
    "biography",
    "profile_picture",
    "avatar",
    "photo_url",
    "profile_image",
    "ip_address",
    "user_agent",
    "device_id",
    "location",
    "coordinates",
    "latitude",
    "longitude",
    "billing_address",
    "shipping_address",
    "tax_id",
    "payment_method",
}


# Fields that should be preserved (not PII)
PRESERVE_FIELDS = {
    "id",
    "user_id",
    "created_at",
    "updated_at",
    "deleted_at",
    "status",
    "type",
    "tier",
    "amount",
    "currency",
    "count",
    "total",
    "timestamp",
    "event_id",
    "session_id",
    "application_id",
    "approval_id",
    "subscription_id",
    "payment_id",
    "invoice_id",
    "transaction_id",
}


def anonymize_user_id(user_id: str, prefix: str = "Deleted User") -> str:
    """
    Generate a deterministic anonymized user identifier.

    Uses SHA-256 hashing to create a consistent identifier that can be used
    for referential integrity across the database while removing PII.

    Args:
        user_id: Original user ID to anonymize
        prefix: Prefix for anonymized identifier (default: "Deleted User")

    Returns:
        Anonymized identifier string (e.g., "Deleted User a1b2c3d4")

    Example:
        >>> anonymize_user_id("user_12345")
        'Deleted User a1b2c3d4'
    """
    if not user_id:
        return f"{prefix} unknown"

    # Generate deterministic hash from user ID
    hash_suffix = hashlib.sha256(user_id.encode('utf-8')).hexdigest()[:8]
    return f"{prefix} {hash_suffix}"


def anonymize_email(user_id: str) -> str:
    """
    Generate an anonymized email address for deleted users.

    Args:
        user_id: Original user ID

    Returns:
        Anonymized email address

    Example:
        >>> anonymize_email("user_12345")
        'deleted-user-a1b2c3d4@anonymized.wwmaa.org'
    """
    hash_suffix = hashlib.sha256(user_id.encode('utf-8')).hexdigest()[:8]
    return f"deleted-user-{hash_suffix}@anonymized.wwmaa.org"


def should_anonymize_field(field_name: str, anonymization_type: AnonymizationType) -> bool:
    """
    Determine if a field should be anonymized based on its name and type.

    Args:
        field_name: Name of the field to check
        anonymization_type: Type of anonymization being performed

    Returns:
        True if field should be anonymized, False otherwise
    """
    field_lower = field_name.lower()

    # Always preserve system fields
    if field_lower in PRESERVE_FIELDS:
        return False

    # Always anonymize PII fields
    if field_lower in PII_FIELDS:
        return True

    # Type-specific rules
    if anonymization_type == AnonymizationType.SEARCH_QUERY:
        # Anonymize search queries but keep metadata
        return field_lower in {"query", "search_query", "search_term", "query_text"}

    if anonymization_type == AnonymizationType.COMMENT or anonymization_type == AnonymizationType.POST:
        # Keep content but anonymize author info
        return field_lower in {"author_name", "author_email", "author_id"}

    # Default: anonymize if it looks like PII
    pii_patterns = ["name", "email", "phone", "address", "contact"]
    return any(pattern in field_lower for pattern in pii_patterns)


def anonymize_document(
    document: Dict[str, Any],
    anonymization_type: AnonymizationType,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Anonymize a document by removing or replacing PII fields.

    This function creates a new dictionary with PII fields removed or replaced
    while preserving non-PII fields needed for audit trails and referential integrity.

    Args:
        document: Original document to anonymize
        anonymization_type: Type of anonymization to apply
        user_id: Optional user ID for generating deterministic anonymized values

    Returns:
        Anonymized document with PII removed/replaced

    Example:
        >>> doc = {
        ...     "id": "123",
        ...     "email": "user@example.com",
        ...     "first_name": "John",
        ...     "last_name": "Doe",
        ...     "created_at": "2024-01-01T00:00:00Z",
        ...     "status": "active"
        ... }
        >>> anonymized = anonymize_document(doc, AnonymizationType.USER, "user_123")
        >>> print(anonymized)
        {
            "id": "123",
            "email": "deleted-user-a1b2c3d4@anonymized.wwmaa.org",
            "first_name": "[REDACTED]",
            "last_name": "[REDACTED]",
            "created_at": "2024-01-01T00:00:00Z",
            "status": "deleted"
        }
    """
    if not document:
        return document

    anonymized = {}
    doc_user_id = user_id or document.get("user_id") or document.get("id")

    for field, value in document.items():
        field_lower = field.lower()

        # Handle nested dictionaries
        if isinstance(value, dict):
            anonymized[field] = anonymize_document(value, anonymization_type, doc_user_id)
            continue

        # Handle lists
        if isinstance(value, list):
            anonymized[field] = [
                anonymize_document(item, anonymization_type, doc_user_id)
                if isinstance(item, dict)
                else item
                for item in value
            ]
            continue

        # Check if field should be anonymized
        if should_anonymize_field(field, anonymization_type):
            # Provide appropriate anonymized value based on field type
            if field_lower == "email":
                anonymized[field] = anonymize_email(doc_user_id)
            elif field_lower in {"first_name", "last_name", "full_name", "name"}:
                anonymized[field] = "[REDACTED]"
            elif field_lower in {"phone", "phone_number"}:
                anonymized[field] = "[REDACTED]"
            elif field_lower in {"address", "street_address"}:
                anonymized[field] = "[REDACTED]"
            elif field_lower in {"bio", "biography"}:
                anonymized[field] = "[REDACTED]"
            elif field_lower in {"query", "search_query", "search_term", "query_text"}:
                anonymized[field] = "[ANONYMIZED]"
            else:
                # Generic redaction for other PII
                anonymized[field] = "[REDACTED]"
        else:
            # Preserve non-PII fields
            anonymized[field] = value

    # Add anonymization metadata
    anonymized["anonymized_at"] = datetime.utcnow().isoformat()
    anonymized["anonymization_type"] = anonymization_type.value

    # Update status field if present
    if "status" in anonymized:
        anonymized["status"] = "deleted"

    return anonymized


def anonymize_user_reference(user_id: str) -> Dict[str, str]:
    """
    Generate an anonymized user reference for foreign key relationships.

    This preserves referential integrity while removing PII by replacing
    user identifiers with deterministic hashes.

    Args:
        user_id: Original user ID

    Returns:
        Dictionary with anonymized user reference fields

    Example:
        >>> anonymize_user_reference("user_12345")
        {
            "user_id": "deleted_user_a1b2c3d4",
            "anonymized_user_name": "Deleted User a1b2c3d4"
        }
    """
    hash_suffix = hashlib.sha256(user_id.encode('utf-8')).hexdigest()[:8]

    return {
        "user_id": f"deleted_user_{hash_suffix}",
        "anonymized_user_name": f"Deleted User {hash_suffix}",
        "anonymized_at": datetime.utcnow().isoformat()
    }


def create_anonymization_audit_log(
    user_id: str,
    anonymization_type: AnonymizationType,
    resource_type: str,
    resource_id: str,
    fields_anonymized: List[str]
) -> Dict[str, Any]:
    """
    Create an audit log entry for anonymization actions.

    Args:
        user_id: ID of user being anonymized
        anonymization_type: Type of anonymization performed
        resource_type: Type of resource anonymized
        resource_id: ID of resource anonymized
        fields_anonymized: List of fields that were anonymized

    Returns:
        Audit log entry dictionary
    """
    return {
        "user_id": user_id,
        "action": "anonymize",
        "resource_type": resource_type,
        "resource_id": resource_id,
        "anonymization_type": anonymization_type.value,
        "fields_anonymized": fields_anonymized,
        "timestamp": datetime.utcnow().isoformat(),
        "description": f"Anonymized {resource_type} as part of GDPR data deletion",
        "severity": "info",
        "tags": ["gdpr", "data_deletion", "anonymization"]
    }


def is_pii_field(field_name: str) -> bool:
    """
    Check if a field name indicates it contains PII.

    Args:
        field_name: Name of the field to check

    Returns:
        True if field is likely to contain PII, False otherwise
    """
    return field_name.lower() in PII_FIELDS


def get_retention_period_days(resource_type: str) -> int:
    """
    Get the retention period in days for different resource types.

    GDPR and legal requirements mandate different retention periods:
    - Payment records: 7 years (2555 days) - Tax/legal requirement
    - Audit logs: 1 year (365 days) - Security requirement
    - General data: 0 days (delete immediately)

    Args:
        resource_type: Type of resource

    Returns:
        Number of days to retain the resource
    """
    retention_periods = {
        "payments": 2555,  # 7 years for tax/legal compliance
        "invoices": 2555,  # 7 years for tax/legal compliance
        "audit_logs": 365,  # 1 year for security auditing
        "transactions": 2555,  # 7 years for financial records
        "subscriptions": 2555,  # 7 years for financial records
    }

    return retention_periods.get(resource_type, 0)


def should_retain_resource(resource_type: str) -> bool:
    """
    Determine if a resource should be retained (anonymized) vs deleted.

    Args:
        resource_type: Type of resource

    Returns:
        True if resource should be retained and anonymized, False if it should be deleted
    """
    # Resources that must be retained for legal/compliance reasons
    retained_resources = {
        "payments",
        "invoices",
        "transactions",
        "subscriptions",
        "audit_logs",
    }

    return resource_type in retained_resources


logger.info("Anonymization utilities module loaded")
