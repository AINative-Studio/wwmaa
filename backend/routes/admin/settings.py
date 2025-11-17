"""
Admin Settings Routes

Endpoints for managing persistent admin configuration settings including
organization information, email/SMTP settings, Stripe configuration, and
membership tier definitions.

All settings are stored in the admin_settings collection with sensitive
values encrypted at rest.
"""

import logging
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import ValidationError

from backend.models.schemas import AdminSettings
from backend.models.request_schemas import (
    OrganizationSettingsUpdate,
    EmailSettingsUpdate,
    StripeSettingsUpdate,
    MembershipTiersUpdate,
    EmailTestRequest,
    AdminSettingsResponse,
)
from backend.services.zerodb_service import ZeroDBClient
from backend.utils.encryption import encrypt_value, decrypt_value
from backend.middleware.auth_middleware import RoleChecker
from backend.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin-settings"])
config = get_settings()


def get_db() -> ZeroDBClient:
    """Dependency to get ZeroDB client"""
    return ZeroDBClient()


async def get_or_create_settings(db: ZeroDBClient) -> AdminSettings:
    """
    Get the active settings document or create default if doesn't exist

    Args:
        db: ZeroDB client instance

    Returns:
        AdminSettings: The active settings document
    """
    try:
        # Query for active settings (there should only be one)
        results = db.query_documents(
            collection_name="admin_settings",
            filter_query={"is_active": True},
            limit=1
        )

        if results and len(results) > 0:
            # Return existing settings
            return AdminSettings(**results[0])
        else:
            # Create default settings
            default_settings = AdminSettings()
            created = db.insert_document(
                collection_name="admin_settings",
                document=default_settings.model_dump(mode='json')
            )
            logger.info("Created default admin settings")
            return AdminSettings(**created)

    except Exception as e:
        logger.error(f"Failed to get or create settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve settings: {str(e)}"
        )


def mask_sensitive_value(value: Optional[str], show_chars: int = 4) -> Optional[str]:
    """
    Mask a sensitive value showing only the last few characters

    Args:
        value: The value to mask
        show_chars: Number of characters to show at the end

    Returns:
        Masked string (e.g., "sk_live_••••••••1234") or None if value is None
    """
    if not value:
        return None

    # For very short values, mask everything except last 4 chars
    if len(value) <= show_chars:
        return "••••"

    # Determine prefix (e.g., "sk_live_", "pk_test_", "whsec_")
    prefix = ""
    if "_" in value:
        parts = value.split("_", 2)
        if len(parts) >= 2:
            prefix = f"{parts[0]}_{parts[1]}_"
            remaining = value[len(prefix):]
        else:
            remaining = value
    else:
        remaining = value

    # Show last N characters, mask the rest
    if len(remaining) > show_chars:
        masked = f"{prefix}{'•' * (len(remaining) - show_chars)}{remaining[-show_chars:]}"
    else:
        masked = f"{prefix}{'•' * len(remaining)}"

    return masked


def decrypt_settings_for_response(settings: AdminSettings) -> dict:
    """
    Decrypt sensitive fields in settings for API response

    Args:
        settings: AdminSettings instance with encrypted fields

    Returns:
        dict: Settings with decrypted sensitive fields
    """
    settings_dict = settings.model_dump(mode='json')

    # Decrypt SMTP password
    if settings_dict.get('smtp_password_encrypted'):
        try:
            settings_dict['smtp_password'] = decrypt_value(settings_dict['smtp_password_encrypted'])
        except Exception as e:
            logger.warning(f"Failed to decrypt SMTP password: {e}")
            settings_dict['smtp_password'] = None
    else:
        settings_dict['smtp_password'] = None

    # Remove encrypted field from response
    settings_dict.pop('smtp_password_encrypted', None)

    # Decrypt Stripe secret key
    if settings_dict.get('stripe_secret_key_encrypted'):
        try:
            settings_dict['stripe_secret_key'] = decrypt_value(settings_dict['stripe_secret_key_encrypted'])
        except Exception as e:
            logger.warning(f"Failed to decrypt Stripe secret key: {e}")
            settings_dict['stripe_secret_key'] = None
    else:
        settings_dict['stripe_secret_key'] = None

    settings_dict.pop('stripe_secret_key_encrypted', None)

    # Decrypt Stripe webhook secret
    if settings_dict.get('stripe_webhook_secret_encrypted'):
        try:
            settings_dict['stripe_webhook_secret'] = decrypt_value(settings_dict['stripe_webhook_secret_encrypted'])
        except Exception as e:
            logger.warning(f"Failed to decrypt Stripe webhook secret: {e}")
            settings_dict['stripe_webhook_secret'] = None
    else:
        settings_dict['stripe_webhook_secret'] = None

    settings_dict.pop('stripe_webhook_secret_encrypted', None)

    return settings_dict


def mask_settings_for_response(settings: AdminSettings) -> dict:
    """
    Mask sensitive fields in settings for API response (for security)

    Args:
        settings: AdminSettings instance with encrypted fields

    Returns:
        dict: Settings with masked sensitive fields
    """
    settings_dict = settings.model_dump(mode='json')

    # Decrypt and mask SMTP password
    if settings_dict.get('smtp_password_encrypted'):
        try:
            decrypted = decrypt_value(settings_dict['smtp_password_encrypted'])
            settings_dict['smtp_password'] = mask_sensitive_value(decrypted, show_chars=4) if decrypted else None
        except Exception as e:
            logger.warning(f"Failed to decrypt SMTP password: {e}")
            settings_dict['smtp_password'] = "••••••••"
    else:
        settings_dict['smtp_password'] = None

    # Remove encrypted field from response
    settings_dict.pop('smtp_password_encrypted', None)

    # Decrypt and mask Stripe secret key
    if settings_dict.get('stripe_secret_key_encrypted'):
        try:
            decrypted = decrypt_value(settings_dict['stripe_secret_key_encrypted'])
            settings_dict['stripe_secret_key'] = mask_sensitive_value(decrypted, show_chars=4) if decrypted else None
        except Exception as e:
            logger.warning(f"Failed to decrypt Stripe secret key: {e}")
            settings_dict['stripe_secret_key'] = "sk_••••••••"
    else:
        settings_dict['stripe_secret_key'] = None

    settings_dict.pop('stripe_secret_key_encrypted', None)

    # Decrypt and mask Stripe webhook secret
    if settings_dict.get('stripe_webhook_secret_encrypted'):
        try:
            decrypted = decrypt_value(settings_dict['stripe_webhook_secret_encrypted'])
            settings_dict['stripe_webhook_secret'] = mask_sensitive_value(decrypted, show_chars=4) if decrypted else None
        except Exception as e:
            logger.warning(f"Failed to decrypt Stripe webhook secret: {e}")
            settings_dict['stripe_webhook_secret'] = "whsec_••••••••"
    else:
        settings_dict['stripe_webhook_secret'] = None

    settings_dict.pop('stripe_webhook_secret_encrypted', None)

    return settings_dict


@router.get(
    "/settings",
    response_model=AdminSettingsResponse,
    summary="Get admin settings",
    description="Retrieve all admin configuration settings (admin only)"
)
async def get_admin_settings(
    current_user: dict = Depends(RoleChecker(["admin"])),
    db: ZeroDBClient = Depends(get_db)
):
    """
    Get all admin settings with decrypted sensitive fields

    Returns:
        AdminSettingsResponse: Complete settings configuration
    """
    try:
        settings = await get_or_create_settings(db)
        decrypted_settings = decrypt_settings_for_response(settings)

        return AdminSettingsResponse(**decrypted_settings)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get admin settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve settings: {str(e)}"
        )


@router.get(
    "/settings/email",
    summary="Get email settings",
    description="Retrieve email/SMTP configuration with masked password (admin only)"
)
async def get_email_settings(
    current_user: dict = Depends(RoleChecker(["admin"])),
    db: ZeroDBClient = Depends(get_db)
):
    """
    Get email/SMTP settings with masked password

    Returns:
        dict: Email configuration with masked sensitive fields
    """
    try:
        settings = await get_or_create_settings(db)
        masked_settings = mask_settings_for_response(settings)

        # Return only email-related fields
        email_settings = {
            "smtp_host": masked_settings.get("smtp_host"),
            "smtp_port": masked_settings.get("smtp_port"),
            "smtp_username": masked_settings.get("smtp_username"),
            "smtp_password": masked_settings.get("smtp_password"),  # Masked
            "smtp_from_email": masked_settings.get("smtp_from_email"),
            "smtp_from_name": masked_settings.get("smtp_from_name"),
            "smtp_use_tls": masked_settings.get("smtp_use_tls"),
            "smtp_use_ssl": masked_settings.get("smtp_use_ssl"),
            "last_email_test_at": masked_settings.get("last_email_test_at"),
            "last_email_test_result": masked_settings.get("last_email_test_result"),
            "last_email_test_error": masked_settings.get("last_email_test_error"),
        }

        return email_settings

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get email settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve email settings: {str(e)}"
        )


@router.get(
    "/settings/stripe",
    summary="Get Stripe settings",
    description="Retrieve Stripe configuration with masked secret keys (admin only)"
)
async def get_stripe_settings(
    current_user: dict = Depends(RoleChecker(["admin"])),
    db: ZeroDBClient = Depends(get_db)
):
    """
    Get Stripe settings with masked secret keys

    Returns:
        dict: Stripe configuration with masked sensitive fields
    """
    try:
        settings = await get_or_create_settings(db)
        masked_settings = mask_settings_for_response(settings)

        # Return only Stripe-related fields
        stripe_settings = {
            "stripe_publishable_key": masked_settings.get("stripe_publishable_key"),
            "stripe_secret_key": masked_settings.get("stripe_secret_key"),  # Masked
            "stripe_webhook_secret": masked_settings.get("stripe_webhook_secret"),  # Masked
            "stripe_enabled": masked_settings.get("stripe_enabled"),
        }

        return stripe_settings

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get Stripe settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve Stripe settings: {str(e)}"
        )


@router.patch(
    "/settings/org",
    response_model=AdminSettingsResponse,
    summary="Update organization settings",
    description="Update organization information (admin only)"
)
async def update_organization_settings(
    update_data: OrganizationSettingsUpdate,
    current_user: dict = Depends(RoleChecker(["admin"])),
    db: ZeroDBClient = Depends(get_db)
):
    """
    Update organization information settings

    Args:
        update_data: Organization settings to update

    Returns:
        AdminSettingsResponse: Updated settings
    """
    try:
        settings = await get_or_create_settings(db)

        # Update only provided fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(settings, key, value)

        # Update metadata
        settings.updated_at = datetime.utcnow()
        settings.last_modified_by = UUID(current_user['id'])

        # Save to database
        db.update_document(
            collection_name="admin_settings",
            document_id=str(settings.id),
            updates=settings.model_dump(mode='json')
        )

        logger.info(f"Updated organization settings by admin {current_user['email']}")

        decrypted_settings = decrypt_settings_for_response(settings)
        return AdminSettingsResponse(**decrypted_settings)

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update organization settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update organization settings: {str(e)}"
        )


@router.patch(
    "/settings/email",
    response_model=AdminSettingsResponse,
    summary="Update email/SMTP settings",
    description="Update email and SMTP configuration (admin only)"
)
async def update_email_settings(
    update_data: EmailSettingsUpdate,
    current_user: dict = Depends(RoleChecker(["admin"])),
    db: ZeroDBClient = Depends(get_db)
):
    """
    Update email/SMTP settings with password encryption

    Args:
        update_data: Email settings to update

    Returns:
        AdminSettingsResponse: Updated settings
    """
    try:
        settings = await get_or_create_settings(db)

        # Update only provided fields
        update_dict = update_data.model_dump(exclude_unset=True)

        # Encrypt SMTP password if provided
        if 'smtp_password' in update_dict and update_dict['smtp_password']:
            encrypted_password = encrypt_value(update_dict['smtp_password'])
            settings.smtp_password_encrypted = encrypted_password
            update_dict.pop('smtp_password')

        # Update other fields
        for key, value in update_dict.items():
            setattr(settings, key, value)

        # Update metadata
        settings.updated_at = datetime.utcnow()
        settings.last_modified_by = UUID(current_user['id'])

        # Save to database
        db.update_document(
            collection_name="admin_settings",
            document_id=str(settings.id),
            updates=settings.model_dump(mode='json')
        )

        logger.info(f"Updated email settings by admin {current_user['email']}")

        decrypted_settings = decrypt_settings_for_response(settings)
        return AdminSettingsResponse(**decrypted_settings)

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update email settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update email settings: {str(e)}"
        )


@router.patch(
    "/settings/stripe",
    response_model=AdminSettingsResponse,
    summary="Update Stripe settings",
    description="Update Stripe configuration with key encryption (admin only)"
)
async def update_stripe_settings(
    update_data: StripeSettingsUpdate,
    current_user: dict = Depends(RoleChecker(["admin"])),
    db: ZeroDBClient = Depends(get_db)
):
    """
    Update Stripe settings with secret key encryption

    Args:
        update_data: Stripe settings to update

    Returns:
        AdminSettingsResponse: Updated settings
    """
    try:
        settings = await get_or_create_settings(db)

        # Update only provided fields
        update_dict = update_data.model_dump(exclude_unset=True)

        # Encrypt Stripe secret key if provided
        if 'stripe_secret_key' in update_dict and update_dict['stripe_secret_key']:
            encrypted_key = encrypt_value(update_dict['stripe_secret_key'])
            settings.stripe_secret_key_encrypted = encrypted_key
            update_dict.pop('stripe_secret_key')

        # Encrypt Stripe webhook secret if provided
        if 'stripe_webhook_secret' in update_dict and update_dict['stripe_webhook_secret']:
            encrypted_secret = encrypt_value(update_dict['stripe_webhook_secret'])
            settings.stripe_webhook_secret_encrypted = encrypted_secret
            update_dict.pop('stripe_webhook_secret')

        # Update other fields (publishable key, enabled flag)
        for key, value in update_dict.items():
            setattr(settings, key, value)

        # Update metadata
        settings.updated_at = datetime.utcnow()
        settings.last_modified_by = UUID(current_user['id'])

        # Save to database
        db.update_document(
            collection_name="admin_settings",
            document_id=str(settings.id),
            updates=settings.model_dump(mode='json')
        )

        logger.info(f"Updated Stripe settings by admin {current_user['email']}")

        decrypted_settings = decrypt_settings_for_response(settings)
        return AdminSettingsResponse(**decrypted_settings)

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update Stripe settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update Stripe settings: {str(e)}"
        )


@router.patch(
    "/settings/membership-tiers",
    response_model=AdminSettingsResponse,
    summary="Update membership tiers",
    description="Update membership tier configurations (admin only)"
)
async def update_membership_tiers(
    update_data: MembershipTiersUpdate,
    current_user: dict = Depends(RoleChecker(["admin"])),
    db: ZeroDBClient = Depends(get_db)
):
    """
    Update membership tier configurations

    Args:
        update_data: Membership tier configurations to update

    Returns:
        AdminSettingsResponse: Updated settings
    """
    try:
        settings = await get_or_create_settings(db)

        # Update only provided tiers
        update_dict = update_data.model_dump(exclude_unset=True)

        for tier_name, tier_config in update_dict.items():
            if tier_config:
                # Ensure membership_tiers is a dict
                if not isinstance(settings.membership_tiers, dict):
                    settings.membership_tiers = {}

                # Update or add tier
                settings.membership_tiers[tier_name] = tier_config

        # Update metadata
        settings.updated_at = datetime.utcnow()
        settings.last_modified_by = UUID(current_user['id'])

        # Save to database
        db.update_document(
            collection_name="admin_settings",
            document_id=str(settings.id),
            updates=settings.model_dump(mode='json')
        )

        logger.info(f"Updated membership tiers by admin {current_user['email']}")

        decrypted_settings = decrypt_settings_for_response(settings)
        return AdminSettingsResponse(**decrypted_settings)

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update membership tiers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update membership tiers: {str(e)}"
        )


@router.post(
    "/settings/email/test",
    summary="Send test email",
    description="Send a test email using configured SMTP settings (admin only)"
)
async def send_test_email(
    test_request: EmailTestRequest,
    current_user: dict = Depends(RoleChecker(["admin"])),
    db: ZeroDBClient = Depends(get_db)
):
    """
    Send a test email using current SMTP settings

    Args:
        test_request: Test email parameters

    Returns:
        dict: Test result with success status
    """
    try:
        settings = await get_or_create_settings(db)

        # Validate SMTP settings are configured
        if not all([settings.smtp_host, settings.smtp_port, settings.smtp_from_email]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SMTP settings are not fully configured. Please configure SMTP host, port, and from email."
            )

        # Decrypt SMTP password
        smtp_password = None
        if settings.smtp_password_encrypted:
            try:
                smtp_password = decrypt_value(settings.smtp_password_encrypted)
            except Exception as e:
                logger.error(f"Failed to decrypt SMTP password: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to decrypt SMTP password"
                )

        # Create email message
        message = MIMEMultipart("alternative")
        message["Subject"] = test_request.test_subject
        message["From"] = settings.smtp_from_email
        message["To"] = test_request.test_email

        # Create plain text and HTML versions
        text_content = test_request.test_message
        html_content = f"""
        <html>
          <body>
            <p>{test_request.test_message}</p>
            <hr>
            <p><small>This is a test email from WWMAA Admin Settings.</small></p>
          </body>
        </html>
        """

        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")
        message.attach(part1)
        message.attach(part2)

        # Send email
        try:
            if settings.smtp_use_ssl:
                # Use SSL
                server = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=10)
            else:
                # Use regular connection with optional TLS
                server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10)
                if settings.smtp_use_tls:
                    server.starttls()

            # Login if credentials provided
            if settings.smtp_username and smtp_password:
                server.login(settings.smtp_username, smtp_password)

            # Send message
            server.send_message(message)
            server.quit()

            # Update test tracking in settings
            settings.last_email_test_at = datetime.utcnow()
            settings.last_email_test_result = "success"
            settings.last_email_test_error = None

            db.update_document(
                collection_name="admin_settings",
                document_id=str(settings.id),
                updates=settings.model_dump(mode='json')
            )

            logger.info(f"Test email sent successfully to {test_request.test_email}")

            return {
                "success": True,
                "message": f"Test email sent successfully to {test_request.test_email}",
                "timestamp": datetime.utcnow().isoformat()
            }

        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"SMTP authentication failed: {str(e)}"
            logger.error(error_msg)

            # Update failure in settings
            settings.last_email_test_at = datetime.utcnow()
            settings.last_email_test_result = "failed"
            settings.last_email_test_error = error_msg

            db.update_document(
                collection_name="admin_settings",
                document_id=str(settings.id),
                updates=settings.model_dump(mode='json')
            )

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error_msg
            )

        except smtplib.SMTPException as e:
            error_msg = f"SMTP error: {str(e)}"
            logger.error(error_msg)

            # Update failure in settings
            settings.last_email_test_at = datetime.utcnow()
            settings.last_email_test_result = "failed"
            settings.last_email_test_error = error_msg

            db.update_document(
                collection_name="admin_settings",
                document_id=str(settings.id),
                updates=settings.model_dump(mode='json')
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg
            )

        except Exception as e:
            error_msg = f"Failed to send email: {str(e)}"
            logger.error(error_msg)

            # Update failure in settings
            settings.last_email_test_at = datetime.utcnow()
            settings.last_email_test_result = "failed"
            settings.last_email_test_error = error_msg

            db.update_document(
                collection_name="admin_settings",
                document_id=str(settings.id),
                updates=settings.model_dump(mode='json')
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in test email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )
