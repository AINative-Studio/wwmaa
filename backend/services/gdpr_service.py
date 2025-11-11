"""
GDPR Compliance Service - Data Export and Deletion

Provides GDPR-compliant functionality for users to exercise their data rights:
1. Data Export (Article 20): Right to data portability
2. Data Deletion (Article 17): Right to erasure ("Right to be Forgotten")

Data Export:
- Collects all user data from ZeroDB collections
- Formats as structured JSON with descriptions
- Provides secure temporary download links (24-hour expiry)
- Sends email notifications when ready

Data Deletion:
- Password confirmation required
- Asynchronous background processing
- Soft delete with anonymization
- Selective retention for legal compliance (payments: 7 years, audit logs: 1 year)
- Stripe subscription cancellation
- Email confirmation before logout

Collections Included:
- profiles: User profile information
- applications: Membership application history
- subscriptions: Subscription and membership history
- payments: Payment transaction history
- rsvps: Event RSVP history
- search_queries: Search query history
- session_attendance: Training session attendance
- audit_logs: User action audit logs
"""

import logging
import json
import uuid
import asyncio
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from passlib.context import CryptContext
import stripe

from backend.services.zerodb_service import ZeroDBClient, ZeroDBError
from backend.services.email_service import EmailService
from backend.config import get_settings
from backend.utils.anonymization import (
    anonymize_user_id,
    anonymize_email,
    anonymize_document,
    anonymize_user_reference,
    create_anonymization_audit_log,
    should_retain_resource,
    get_retention_period_days,
    AnonymizationType
)
from backend.models.schemas import AuditAction

logger = logging.getLogger(__name__)
settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class GDPRServiceError(Exception):
    """Base exception for GDPR service errors"""
    pass


class DataExportError(GDPRServiceError):
    """Exception raised when data export fails"""
    pass


class InvalidPasswordError(GDPRServiceError):
    """Exception raised when password verification fails"""
    pass


class AccountAlreadyDeletedException(GDPRServiceError):
    """Exception raised when account is already deleted"""
    pass


class DeletionInProgressError(GDPRServiceError):
    """Exception raised when deletion is already in progress"""
    pass


class GDPRService:
    """
    GDPR Compliance Service for Data Export

    Provides functionality for users to export all their personal data
    in a machine-readable format (JSON) as required by GDPR Article 20.

    Features:
    - Collects data from all ZeroDB collections
    - Generates structured JSON export with descriptions
    - Creates temporary download links (24-hour expiry)
    - Sends email notifications when export is ready
    - Includes human-readable cover letter
    """

    # Collection names to export data from
    COLLECTIONS = {
        "profiles": "Profile Information",
        "applications": "Membership Applications",
        "subscriptions": "Subscription History",
        "payments": "Payment History",
        "rsvps": "Event RSVPs",
        "search_queries": "Search History",
        "attendees": "Training Attendance",
        "audit_logs": "Activity Logs"
    }

    # Export expiry time (24 hours)
    EXPORT_EXPIRY_HOURS = 24

    def __init__(
        self,
        db_client: Optional[ZeroDBClient] = None,
        email_service: Optional[EmailService] = None
    ):
        """
        Initialize GDPR Service

        Args:
            db_client: ZeroDB client instance (creates new if not provided)
            email_service: Email service instance (creates new if not provided)
        """
        self.db = db_client or ZeroDBClient()
        self.email_service = email_service or EmailService()
        logger.info("GDPRService initialized")

    async def export_user_data(self, user_id: str, user_email: str) -> Dict[str, Any]:
        """
        Export all user data from ZeroDB collections

        Collects data from all collections and generates a comprehensive
        JSON export file with human-readable structure and descriptions.

        Args:
            user_id: User ID to export data for
            user_email: User email for sending notification

        Returns:
            Export metadata including export_id and download URL

        Raises:
            DataExportError: If data export fails
        """
        try:
            logger.info(f"Starting data export for user {user_id}")

            # Generate unique export ID
            export_id = str(uuid.uuid4())
            export_date = datetime.utcnow()
            expiry_date = export_date + timedelta(hours=self.EXPORT_EXPIRY_HOURS)

            # Collect data from all collections
            export_data = {
                "export_metadata": {
                    "export_id": export_id,
                    "export_date": export_date.isoformat(),
                    "expiry_date": expiry_date.isoformat(),
                    "user_id": user_id,
                    "format_version": "1.0",
                    "gdpr_article": "Article 20 - Right to data portability"
                },
                "cover_letter": self._generate_cover_letter(user_email, export_date, expiry_date),
                "data": {}
            }

            # Collect data from each collection
            for collection_name, description in self.COLLECTIONS.items():
                try:
                    collection_data = await self._collect_collection_data(
                        collection_name,
                        user_id
                    )
                    export_data["data"][collection_name] = {
                        "description": description,
                        "record_count": len(collection_data),
                        "records": collection_data
                    }
                    logger.info(
                        f"Collected {len(collection_data)} records from {collection_name}"
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to collect data from {collection_name}: {str(e)}"
                    )
                    export_data["data"][collection_name] = {
                        "description": description,
                        "record_count": 0,
                        "records": [],
                        "error": f"Failed to retrieve: {str(e)}"
                    }

            # Convert to JSON
            export_json = json.dumps(export_data, indent=2, default=str)

            # Store export file in ZeroDB Object Storage
            file_name = f"data_export_{export_id}.json"
            object_key = f"gdpr_exports/{user_id}/{file_name}"

            # Upload to object storage with 24-hour TTL
            upload_result = await self._store_export_file(
                object_key,
                export_json,
                expiry_date
            )

            # Generate signed download URL
            download_url = await self._generate_download_url(
                object_key,
                expiry_date
            )

            # Record export request in audit logs
            await self._log_export_request(user_id, export_id)

            # Send email notification (asynchronous)
            await self._send_export_ready_email(
                user_email,
                download_url,
                expiry_date
            )

            logger.info(f"Data export completed successfully for user {user_id}")

            return {
                "export_id": export_id,
                "status": "completed",
                "download_url": download_url,
                "expiry_date": expiry_date.isoformat(),
                "file_size_bytes": len(export_json),
                "record_counts": {
                    collection: export_data["data"][collection]["record_count"]
                    for collection in self.COLLECTIONS.keys()
                }
            }

        except Exception as e:
            logger.error(f"Data export failed for user {user_id}: {str(e)}", exc_info=True)
            raise DataExportError(f"Failed to export user data: {str(e)}")

    async def _collect_collection_data(
        self,
        collection_name: str,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Collect all data for a user from a specific collection

        Args:
            collection_name: Name of the collection
            user_id: User ID to filter by

        Returns:
            List of documents from the collection
        """
        # Build filter query based on collection
        filter_query = self._build_filter_query(collection_name, user_id)

        try:
            # Query the collection
            result = self.db.find(
                collection=collection_name,
                filter_query=filter_query,
                limit=10000  # High limit to capture all data
            )

            # Clean sensitive data from records
            cleaned_data = self._clean_sensitive_data(
                result.get("documents", []),
                collection_name
            )

            return cleaned_data

        except ZeroDBError as e:
            # If collection doesn't exist, return empty list
            if "not found" in str(e).lower():
                logger.warning(f"Collection {collection_name} not found")
                return []
            raise

    def _build_filter_query(self, collection_name: str, user_id: str) -> Dict[str, Any]:
        """
        Build filter query for each collection type

        Args:
            collection_name: Name of the collection
            user_id: User ID to filter by

        Returns:
            Filter query dictionary
        """
        # Most collections use user_id field
        if collection_name in ["profiles", "applications", "subscriptions"]:
            return {"user_id": user_id}

        # Payments might use customer_id or user_id
        elif collection_name == "payments":
            return {"user_id": user_id}

        # RSVPs use user_id
        elif collection_name == "rsvps":
            return {"user_id": user_id}

        # Search queries use user_id
        elif collection_name == "search_queries":
            return {"user_id": user_id}

        # Attendees use user_id
        elif collection_name == "attendees":
            return {"user_id": user_id}

        # Audit logs use user_id
        elif collection_name == "audit_logs":
            return {"user_id": user_id}

        # Default: use user_id
        else:
            return {"user_id": user_id}

    def _clean_sensitive_data(
        self,
        records: List[Dict[str, Any]],
        collection_name: str
    ) -> List[Dict[str, Any]]:
        """
        Remove or redact sensitive data from records

        GDPR requires providing user data, but we should still protect
        certain sensitive fields like password hashes, internal IDs, etc.

        Args:
            records: List of records to clean
            collection_name: Name of the collection

        Returns:
            Cleaned records
        """
        cleaned = []

        # Fields to always remove
        remove_fields = ["_id", "password_hash", "password", "salt"]

        for record in records:
            cleaned_record = {}
            for key, value in record.items():
                # Skip sensitive fields
                if key not in remove_fields:
                    # Redact partial credit card numbers in payments
                    if collection_name == "payments" and key == "card_last4":
                        cleaned_record[key] = f"****{value}" if value else None
                    else:
                        cleaned_record[key] = value

            cleaned.append(cleaned_record)

        return cleaned

    def _generate_cover_letter(
        self,
        user_email: str,
        export_date: datetime,
        expiry_date: datetime
    ) -> Dict[str, str]:
        """
        Generate a human-readable cover letter explaining the export

        Args:
            user_email: User's email address
            export_date: When export was generated
            expiry_date: When export expires

        Returns:
            Cover letter dictionary
        """
        return {
            "title": "Your Personal Data Export from WWMAA",
            "introduction": (
                "This file contains all personal data we have collected about you "
                "as a user of the World Wide Martial Arts Association (WWMAA) platform. "
                "This export is provided in compliance with GDPR Article 20 "
                "(Right to data portability) and Article 15 (Right of access)."
            ),
            "recipient": user_email,
            "export_date": export_date.strftime("%B %d, %Y at %H:%M UTC"),
            "expiry_date": expiry_date.strftime("%B %d, %Y at %H:%M UTC"),
            "data_included": (
                "This export includes all data associated with your account: "
                "profile information, membership applications, subscription history, "
                "payment records, event RSVPs, search queries, training attendance, "
                "and activity logs."
            ),
            "format_notice": (
                "The data is provided in JSON format, which is machine-readable and "
                "can be processed by most modern programming languages and tools."
            ),
            "privacy_notice": (
                "This file contains your personal data. Please keep it secure and "
                "do not share it with others. The download link will expire in 24 hours."
            ),
            "contact_info": (
                "If you have questions about this export or your data privacy rights, "
                "please contact us at privacy@wwmaa.com"
            )
        }

    async def _store_export_file(
        self,
        object_key: str,
        content: str,
        expiry_date: datetime
    ) -> Dict[str, Any]:
        """
        Store export file in ZeroDB Object Storage with TTL

        Args:
            object_key: Object storage key
            content: File content (JSON string)
            expiry_date: When file should expire

        Returns:
            Upload result
        """
        try:
            # Calculate TTL in seconds
            ttl_seconds = int((expiry_date - datetime.utcnow()).total_seconds())

            # Upload to object storage using the new method
            result = self.db.upload_object_from_bytes(
                key=object_key,
                content=content.encode('utf-8'),
                content_type="application/json",
                metadata={
                    "purpose": "gdpr_export",
                    "expiry_date": expiry_date.isoformat()
                },
                ttl=ttl_seconds
            )

            logger.info(f"Export file stored: {object_key}")
            return result

        except Exception as e:
            logger.error(f"Failed to store export file: {str(e)}")
            raise DataExportError(f"Failed to store export file: {str(e)}")

    async def _generate_download_url(
        self,
        object_key: str,
        expiry_date: datetime
    ) -> str:
        """
        Generate signed download URL for export file

        Args:
            object_key: Object storage key
            expiry_date: URL expiry date

        Returns:
            Signed download URL
        """
        try:
            # Generate signed URL with expiry
            ttl_seconds = int((expiry_date - datetime.utcnow()).total_seconds())

            signed_url = self.db.generate_signed_url(
                key=object_key,
                expiry_seconds=ttl_seconds,
                method="GET"
            )

            logger.info(f"Generated signed URL for {object_key}")
            return signed_url

        except Exception as e:
            logger.error(f"Failed to generate download URL: {str(e)}")
            # Fallback to direct URL if signing not available
            return f"{settings.ZERODB_API_BASE_URL}/storage/objects/{object_key}"

    async def _log_export_request(self, user_id: str, export_id: str) -> None:
        """
        Log export request in audit logs

        Args:
            user_id: User ID
            export_id: Export ID
        """
        try:
            audit_entry = {
                "user_id": user_id,
                "action": "gdpr_data_export",
                "details": {
                    "export_id": export_id,
                    "timestamp": datetime.utcnow().isoformat()
                },
                "ip_address": None,  # Will be populated by route handler
                "user_agent": None,
                "created_at": datetime.utcnow().isoformat()
            }

            self.db.insert_one(
                collection="audit_logs",
                document=audit_entry
            )

            logger.info(f"Logged export request for user {user_id}")

        except Exception as e:
            # Don't fail export if logging fails
            logger.warning(f"Failed to log export request: {str(e)}")

    async def _send_export_ready_email(
        self,
        user_email: str,
        download_url: str,
        expiry_date: datetime
    ) -> None:
        """
        Send email notification when export is ready

        Args:
            user_email: Recipient email address
            download_url: Secure download URL
            expiry_date: URL expiry date
        """
        try:
            # Format expiry date for display
            expiry_display = expiry_date.strftime("%B %d, %Y at %H:%M UTC")

            # HTML email body
            html_body = f"""
            <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                        .header {{ background-color: #1a1a1a; color: white; padding: 20px; text-align: center; }}
                        .content {{ background-color: #f9f9f9; padding: 30px; border-radius: 5px; margin-top: 20px; }}
                        .button {{
                            display: inline-block;
                            background-color: #007bff;
                            color: white;
                            padding: 12px 30px;
                            text-decoration: none;
                            border-radius: 5px;
                            margin: 20px 0;
                        }}
                        .warning {{
                            background-color: #fff3cd;
                            border-left: 4px solid #ffc107;
                            padding: 15px;
                            margin: 20px 0;
                        }}
                        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>Your Data Export is Ready</h1>
                        </div>
                        <div class="content">
                            <p>Hello,</p>
                            <p>Your personal data export from WWMAA is ready for download.</p>

                            <p>This export contains all your personal data we have collected, including:</p>
                            <ul>
                                <li>Profile information</li>
                                <li>Membership application history</li>
                                <li>Subscription and payment records</li>
                                <li>Event RSVPs and training attendance</li>
                                <li>Search history and activity logs</li>
                            </ul>

                            <div style="text-align: center;">
                                <a href="{download_url}" class="button">Download Your Data</a>
                            </div>

                            <div class="warning">
                                <strong>Important:</strong> This download link will expire on {expiry_display}.
                                Please download your data before this time. The file contains sensitive personal
                                information - keep it secure and do not share it with others.
                            </div>

                            <p>The data is provided in JSON format, which is machine-readable and can be
                            processed by most modern programming languages and tools.</p>

                            <p>If you did not request this export, please contact us immediately at
                            <a href="mailto:privacy@wwmaa.com">privacy@wwmaa.com</a>.</p>

                            <p>This export is provided in compliance with GDPR Article 20 (Right to data portability)
                            and Article 15 (Right of access by the data subject).</p>
                        </div>
                        <div class="footer">
                            <p>World Wide Martial Arts Association (WWMAA)<br>
                            For questions about your data privacy rights, contact: privacy@wwmaa.com</p>
                        </div>
                    </div>
                </body>
            </html>
            """

            # Plain text version
            text_body = f"""
Your Data Export is Ready

Hello,

Your personal data export from WWMAA is ready for download.

Download your data here: {download_url}

IMPORTANT: This link will expire on {expiry_display}. Please download your data before this time.

This export contains all your personal data including profile information, membership applications,
subscriptions, payments, event RSVPs, and activity logs.

The file contains sensitive personal information - keep it secure and do not share it with others.

If you did not request this export, please contact us immediately at privacy@wwmaa.com.

---
World Wide Martial Arts Association (WWMAA)
For questions about your data privacy rights, contact: privacy@wwmaa.com
            """

            # Send email
            self.email_service._send_email(
                to_email=user_email,
                subject="Your WWMAA Data Export is Ready",
                html_body=html_body,
                text_body=text_body,
                tag="gdpr_export"
            )

            logger.info(f"Export ready email sent to {user_email}")

        except Exception as e:
            # Don't fail export if email fails
            logger.error(f"Failed to send export ready email: {str(e)}")

    async def get_export_status(self, user_id: str, export_id: str) -> Dict[str, Any]:
        """
        Get status of a data export request

        Args:
            user_id: User ID
            export_id: Export ID

        Returns:
            Export status information
        """
        try:
            # Check if export file exists in object storage
            object_key = f"gdpr_exports/{user_id}/data_export_{export_id}.json"

            # Check if object exists
            # Note: This is a placeholder - actual implementation depends on API
            try:
                object_info = self.db.get_object_metadata(key=object_key)

                return {
                    "export_id": export_id,
                    "status": "completed",
                    "created_at": object_info.get("created_at"),
                    "expiry_date": object_info.get("expiry_date"),
                    "file_size_bytes": object_info.get("size")
                }
            except:
                return {
                    "export_id": export_id,
                    "status": "not_found"
                }

        except Exception as e:
            logger.error(f"Failed to get export status: {str(e)}")
            raise GDPRServiceError(f"Failed to get export status: {str(e)}")

    async def delete_export(self, user_id: str, export_id: str) -> bool:
        """
        Delete an export file before expiry

        Args:
            user_id: User ID
            export_id: Export ID

        Returns:
            True if deleted successfully
        """
        try:
            object_key = f"gdpr_exports/{user_id}/data_export_{export_id}.json"

            # Delete from object storage
            self.db.delete_object_by_key(key=object_key)

            logger.info(f"Deleted export {export_id} for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete export: {str(e)}")
            return False

    # ============================================================================
    # DATA DELETION METHODS (GDPR Article 17 - Right to Erasure)
    # ============================================================================

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.

        Args:
            plain_password: Plain text password
            hashed_password: Hashed password

        Returns:
            True if password matches, False otherwise
        """
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False

    async def delete_user_account(
        self,
        user_id: str,
        password: str,
        initiated_by: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Delete user account and all associated data (GDPR Article 17).

        This is the main entry point for account deletion. It:
        1. Verifies the user's password
        2. Checks if deletion is already in progress
        3. Marks account as "deletion_in_progress"
        4. Initiates asynchronous background deletion
        5. Returns immediately to the user

        Args:
            user_id: ID of user to delete
            password: User's password for confirmation
            initiated_by: ID of user initiating deletion (should match user_id)
            reason: Optional reason for deletion

        Returns:
            Dict with deletion job status

        Raises:
            InvalidPasswordError: If password verification fails
            AccountAlreadyDeletedException: If account is already deleted
            DeletionInProgressError: If deletion is already in progress
            GDPRServiceError: If deletion initiation fails
        """
        try:
            # Get user
            user_result = self.db.get_document("users", user_id)
            user = user_result.get("data", {})

            if not user:
                raise GDPRServiceError(f"User {user_id} not found")

            # Check if already deleted
            if user.get("status") == "deleted":
                raise AccountAlreadyDeletedException(
                    "Account has already been deleted"
                )

            # Check if deletion is in progress
            if user.get("status") == "deletion_in_progress":
                raise DeletionInProgressError(
                    "Account deletion is already in progress"
                )

            # Verify password
            hashed_password = user.get("hashed_password")
            if not hashed_password or not self.verify_password(password, hashed_password):
                raise InvalidPasswordError(
                    "Invalid password. Account deletion requires password confirmation."
                )

            # Verify that user is deleting their own account
            if user_id != initiated_by:
                raise GDPRServiceError(
                    "Users can only delete their own accounts"
                )

            # Mark account as deletion in progress
            self.db.update_document(
                "users",
                user_id,
                {
                    "status": "deletion_in_progress",
                    "deletion_initiated_at": datetime.utcnow().isoformat(),
                    "deletion_reason": reason,
                    "updated_at": datetime.utcnow().isoformat()
                },
                merge=True
            )

            logger.info(f"Account deletion initiated for user {user_id}")

            # Create audit log
            self._create_audit_log_deletion(
                user_id=user_id,
                action=AuditAction.DELETE,
                resource_type="users",
                resource_id=user_id,
                description=f"Account deletion initiated: {reason or 'User request'}",
                metadata={
                    "initiated_by": initiated_by,
                    "reason": reason,
                    "gdpr_compliance": "Article 17 - Right to Erasure"
                }
            )

            # Start asynchronous deletion process
            asyncio.create_task(
                self._execute_account_deletion_async(user_id, user)
            )

            return {
                "success": True,
                "user_id": user_id,
                "status": "deletion_in_progress",
                "message": "Account deletion has been initiated. You will receive a confirmation email shortly.",
                "initiated_at": datetime.utcnow().isoformat()
            }

        except (InvalidPasswordError, AccountAlreadyDeletedException, DeletionInProgressError):
            raise
        except ZeroDBError:
            raise GDPRServiceError(f"User {user_id} not found")
        except Exception as e:
            logger.error(f"Error initiating account deletion: {e}")
            raise GDPRServiceError(f"Failed to initiate account deletion: {str(e)}")

    async def _execute_account_deletion_async(
        self,
        user_id: str,
        user: Dict[str, Any]
    ) -> None:
        """
        Execute the complete account deletion process asynchronously.

        This background task handles all deletion and anonymization operations:
        1. Cancel Stripe subscription
        2. Delete/anonymize user data
        3. Anonymize related resources
        4. Send confirmation email
        5. Update audit logs

        Args:
            user_id: ID of user to delete
            user: User document
        """
        try:
            logger.info(f"Starting asynchronous deletion for user {user_id}")

            deletion_results = {
                "user_id": user_id,
                "started_at": datetime.utcnow().isoformat(),
                "steps": []
            }

            # Step 1: Cancel Stripe subscription
            try:
                stripe_result = await self._cancel_stripe_subscription(user_id, user)
                deletion_results["steps"].append({
                    "step": "cancel_subscription",
                    "success": stripe_result.get("success", False),
                    "details": stripe_result
                })
            except Exception as e:
                logger.error(f"Error canceling Stripe subscription: {e}")
                deletion_results["steps"].append({
                    "step": "cancel_subscription",
                    "success": False,
                    "error": str(e)
                })

            # Step 2: Anonymize user profile
            try:
                profile_result = await self._anonymize_user_profile(user_id)
                deletion_results["steps"].append({
                    "step": "anonymize_profile",
                    "success": profile_result.get("success", False),
                    "details": profile_result
                })
            except Exception as e:
                logger.error(f"Error anonymizing profile: {e}")
                deletion_results["steps"].append({
                    "step": "anonymize_profile",
                    "success": False,
                    "error": str(e)
                })

            # Step 3: Anonymize application history
            try:
                application_result = await self._anonymize_applications(user_id)
                deletion_results["steps"].append({
                    "step": "anonymize_applications",
                    "success": application_result.get("success", False),
                    "details": application_result
                })
            except Exception as e:
                logger.error(f"Error anonymizing applications: {e}")
                deletion_results["steps"].append({
                    "step": "anonymize_applications",
                    "success": False,
                    "error": str(e)
                })

            # Step 4: Anonymize search queries
            try:
                search_result = await self._anonymize_search_queries(user_id)
                deletion_results["steps"].append({
                    "step": "anonymize_search_queries",
                    "success": search_result.get("success", False),
                    "details": search_result
                })
            except Exception as e:
                logger.error(f"Error anonymizing search queries: {e}")
                deletion_results["steps"].append({
                    "step": "anonymize_search_queries",
                    "success": False,
                    "error": str(e)
                })

            # Step 5: Anonymize training attendance
            try:
                attendance_result = await self._anonymize_training_attendance(user_id)
                deletion_results["steps"].append({
                    "step": "anonymize_training_attendance",
                    "success": attendance_result.get("success", False),
                    "details": attendance_result
                })
            except Exception as e:
                logger.error(f"Error anonymizing training attendance: {e}")
                deletion_results["steps"].append({
                    "step": "anonymize_training_attendance",
                    "success": False,
                    "error": str(e)
                })

            # Step 6: Anonymize event RSVPs
            try:
                rsvp_result = await self._anonymize_rsvps(user_id)
                deletion_results["steps"].append({
                    "step": "anonymize_rsvps",
                    "success": rsvp_result.get("success", False),
                    "details": rsvp_result
                })
            except Exception as e:
                logger.error(f"Error anonymizing RSVPs: {e}")
                deletion_results["steps"].append({
                    "step": "anonymize_rsvps",
                    "success": False,
                    "error": str(e)
                })

            # Step 7: Anonymize payments (retain for 7 years)
            try:
                payment_result = await self._anonymize_payment_records(user_id)
                deletion_results["steps"].append({
                    "step": "anonymize_payments",
                    "success": payment_result.get("success", False),
                    "details": payment_result
                })
            except Exception as e:
                logger.error(f"Error anonymizing payments: {e}")
                deletion_results["steps"].append({
                    "step": "anonymize_payments",
                    "success": False,
                    "error": str(e)
                })

            # Step 8: Soft delete user account
            try:
                user_result = await self._soft_delete_user(user_id, user)
                deletion_results["steps"].append({
                    "step": "soft_delete_user",
                    "success": user_result.get("success", False),
                    "details": user_result
                })
            except Exception as e:
                logger.error(f"Error soft deleting user: {e}")
                deletion_results["steps"].append({
                    "step": "soft_delete_user",
                    "success": False,
                    "error": str(e)
                })

            # Step 9: Invalidate all JWT tokens
            try:
                token_result = await self._invalidate_user_tokens(user_id)
                deletion_results["steps"].append({
                    "step": "invalidate_tokens",
                    "success": token_result.get("success", False),
                    "details": token_result
                })
            except Exception as e:
                logger.error(f"Error invalidating tokens: {e}")
                deletion_results["steps"].append({
                    "step": "invalidate_tokens",
                    "success": False,
                    "error": str(e)
                })

            # Step 10: Send confirmation email
            try:
                email_result = await self._send_deletion_confirmation_email(user)
                deletion_results["steps"].append({
                    "step": "send_confirmation_email",
                    "success": email_result.get("success", False),
                    "details": email_result
                })
            except Exception as e:
                logger.error(f"Error sending confirmation email: {e}")
                deletion_results["steps"].append({
                    "step": "send_confirmation_email",
                    "success": False,
                    "error": str(e)
                })

            deletion_results["completed_at"] = datetime.utcnow().isoformat()
            deletion_results["success"] = all(
                step.get("success", False) for step in deletion_results["steps"]
            )

            # Create final audit log
            self._create_audit_log_deletion(
                user_id=user_id,
                action=AuditAction.DELETE,
                resource_type="users",
                resource_id=user_id,
                description="Account deletion completed",
                metadata=deletion_results
            )

            logger.info(f"Account deletion completed for user {user_id}: {deletion_results}")

        except Exception as e:
            logger.error(f"Critical error in account deletion process: {e}")
            # Create error audit log
            self._create_audit_log_deletion(
                user_id=user_id,
                action=AuditAction.DELETE,
                resource_type="users",
                resource_id=user_id,
                description=f"Account deletion failed: {str(e)}",
                metadata={"error": str(e), "success": False}
            )

    async def _cancel_stripe_subscription(
        self,
        user_id: str,
        user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Cancel user's Stripe subscription immediately.

        Args:
            user_id: User ID
            user: User document

        Returns:
            Dict with cancellation status
        """
        try:
            # Query for active subscriptions
            subscriptions_result = self.db.query_documents(
                "subscriptions",
                filters={"user_id": user_id, "status": "active"},
                limit=10
            )

            subscriptions = subscriptions_result.get("documents", [])

            if not subscriptions:
                return {
                    "success": True,
                    "message": "No active subscriptions found",
                    "subscriptions_canceled": 0
                }

            canceled_count = 0
            errors = []

            for subscription in subscriptions:
                stripe_subscription_id = subscription.get("stripe_subscription_id")

                if stripe_subscription_id:
                    try:
                        # Cancel subscription in Stripe
                        stripe.Subscription.cancel(stripe_subscription_id)

                        # Update subscription in database
                        self.db.update_document(
                            "subscriptions",
                            subscription["id"],
                            {
                                "status": "canceled",
                                "canceled_at": datetime.utcnow().isoformat(),
                                "cancellation_reason": "account_deletion",
                                "updated_at": datetime.utcnow().isoformat()
                            },
                            merge=True
                        )

                        canceled_count += 1
                        logger.info(f"Canceled Stripe subscription {stripe_subscription_id}")

                    except stripe.error.StripeError as e:
                        logger.error(f"Stripe error canceling subscription: {e}")
                        errors.append(str(e))

            return {
                "success": len(errors) == 0,
                "subscriptions_canceled": canceled_count,
                "errors": errors if errors else None
            }

        except Exception as e:
            logger.error(f"Error canceling subscriptions: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _anonymize_user_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Anonymize user profile data.

        Args:
            user_id: User ID

        Returns:
            Dict with anonymization status
        """
        try:
            # Query for user profiles
            profiles_result = self.db.query_documents(
                "profiles",
                filters={"user_id": user_id},
                limit=10
            )

            profiles = profiles_result.get("documents", [])

            if not profiles:
                return {
                    "success": True,
                    "message": "No profiles found",
                    "profiles_anonymized": 0
                }

            anonymized_count = 0

            for profile in profiles:
                # Anonymize profile
                anonymized_profile = anonymize_document(
                    profile,
                    AnonymizationType.PROFILE,
                    user_id
                )

                # Update in database
                self.db.update_document(
                    "profiles",
                    profile["id"],
                    anonymized_profile,
                    merge=False  # Full replacement
                )

                anonymized_count += 1

            logger.info(f"Anonymized {anonymized_count} profile(s) for user {user_id}")

            return {
                "success": True,
                "profiles_anonymized": anonymized_count
            }

        except Exception as e:
            logger.error(f"Error anonymizing profiles: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _anonymize_applications(self, user_id: str) -> Dict[str, Any]:
        """
        Anonymize membership application history.

        Args:
            user_id: User ID

        Returns:
            Dict with anonymization status
        """
        try:
            # Query for applications
            applications_result = self.db.query_documents(
                "applications",
                filters={"user_id": user_id},
                limit=100
            )

            applications = applications_result.get("documents", [])

            if not applications:
                return {
                    "success": True,
                    "message": "No applications found",
                    "applications_anonymized": 0
                }

            anonymized_count = 0

            for application in applications:
                # Anonymize application
                anonymized_app = anonymize_document(
                    application,
                    AnonymizationType.APPLICATION,
                    user_id
                )

                # Update in database
                self.db.update_document(
                    "applications",
                    application["id"],
                    anonymized_app,
                    merge=False
                )

                anonymized_count += 1

            logger.info(f"Anonymized {anonymized_count} application(s) for user {user_id}")

            return {
                "success": True,
                "applications_anonymized": anonymized_count
            }

        except Exception as e:
            logger.error(f"Error anonymizing applications: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _anonymize_search_queries(self, user_id: str) -> Dict[str, Any]:
        """
        Anonymize AI search query history.

        Args:
            user_id: User ID

        Returns:
            Dict with anonymization status
        """
        try:
            # Query for search queries
            queries_result = self.db.query_documents(
                "search_queries",
                filters={"user_id": user_id},
                limit=1000
            )

            queries = queries_result.get("documents", [])

            if not queries:
                return {
                    "success": True,
                    "message": "No search queries found",
                    "queries_anonymized": 0
                }

            anonymized_count = 0

            for query in queries:
                # Anonymize search query
                anonymized_query = anonymize_document(
                    query,
                    AnonymizationType.SEARCH_QUERY,
                    user_id
                )

                # Update in database
                self.db.update_document(
                    "search_queries",
                    query["id"],
                    anonymized_query,
                    merge=False
                )

                anonymized_count += 1

            logger.info(f"Anonymized {anonymized_count} search quer(ies) for user {user_id}")

            return {
                "success": True,
                "queries_anonymized": anonymized_count
            }

        except Exception as e:
            logger.error(f"Error anonymizing search queries: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _anonymize_training_attendance(self, user_id: str) -> Dict[str, Any]:
        """
        Anonymize training session attendance records.

        Args:
            user_id: User ID

        Returns:
            Dict with anonymization status
        """
        try:
            # Query for attendance records
            attendance_result = self.db.query_documents(
                "session_attendance",
                filters={"user_id": user_id},
                limit=1000
            )

            attendance_records = attendance_result.get("documents", [])

            if not attendance_records:
                return {
                    "success": True,
                    "message": "No attendance records found",
                    "records_anonymized": 0
                }

            anonymized_count = 0

            for record in attendance_records:
                # Anonymize attendance record
                anonymized_record = anonymize_document(
                    record,
                    AnonymizationType.TRAINING_ATTENDANCE,
                    user_id
                )

                # Update in database
                self.db.update_document(
                    "session_attendance",
                    record["id"],
                    anonymized_record,
                    merge=False
                )

                anonymized_count += 1

            logger.info(f"Anonymized {anonymized_count} attendance record(s) for user {user_id}")

            return {
                "success": True,
                "records_anonymized": anonymized_count
            }

        except Exception as e:
            logger.error(f"Error anonymizing attendance records: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _anonymize_rsvps(self, user_id: str) -> Dict[str, Any]:
        """
        Anonymize event RSVP records (keep for organizers).

        Args:
            user_id: User ID

        Returns:
            Dict with anonymization status
        """
        try:
            # Query for RSVPs
            rsvps_result = self.db.query_documents(
                "rsvps",
                filters={"user_id": user_id},
                limit=1000
            )

            rsvps = rsvps_result.get("documents", [])

            if not rsvps:
                return {
                    "success": True,
                    "message": "No RSVPs found",
                    "rsvps_anonymized": 0
                }

            anonymized_count = 0

            for rsvp in rsvps:
                # Anonymize RSVP
                anonymized_rsvp = anonymize_document(
                    rsvp,
                    AnonymizationType.RSVP,
                    user_id
                )

                # Update in database
                self.db.update_document(
                    "rsvps",
                    rsvp["id"],
                    anonymized_rsvp,
                    merge=False
                )

                anonymized_count += 1

            logger.info(f"Anonymized {anonymized_count} RSVP(s) for user {user_id}")

            return {
                "success": True,
                "rsvps_anonymized": anonymized_count
            }

        except Exception as e:
            logger.error(f"Error anonymizing RSVPs: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _anonymize_payment_records(self, user_id: str) -> Dict[str, Any]:
        """
        Anonymize payment records (retain for 7 years per legal requirements).

        Args:
            user_id: User ID

        Returns:
            Dict with anonymization status
        """
        try:
            # Query for payments
            payments_result = self.db.query_documents(
                "payments",
                filters={"user_id": user_id},
                limit=1000
            )

            payments = payments_result.get("documents", [])

            if not payments:
                return {
                    "success": True,
                    "message": "No payment records found",
                    "payments_anonymized": 0
                }

            anonymized_count = 0
            retention_days = get_retention_period_days("payments")
            retention_until = (datetime.utcnow() + timedelta(days=retention_days)).isoformat()

            for payment in payments:
                # Anonymize payment but keep financial data
                anonymized_payment = {
                    **payment,
                    "user_id": f"deleted_user_{hashlib.sha256(user_id.encode()).hexdigest()[:8]}",
                    "email": anonymize_email(user_id),
                    "anonymized_at": datetime.utcnow().isoformat(),
                    "retention_until": retention_until,
                    "retention_reason": "legal_compliance_7_years"
                }

                # Remove PII but keep financial data
                pii_fields = ["name", "billing_address", "phone"]
                for field in pii_fields:
                    if field in anonymized_payment:
                        anonymized_payment[field] = "[REDACTED]"

                # Update in database
                self.db.update_document(
                    "payments",
                    payment["id"],
                    anonymized_payment,
                    merge=False
                )

                anonymized_count += 1

            logger.info(
                f"Anonymized {anonymized_count} payment record(s) for user {user_id} "
                f"(retention until {retention_until})"
            )

            return {
                "success": True,
                "payments_anonymized": anonymized_count,
                "retention_until": retention_until
            }

        except Exception as e:
            logger.error(f"Error anonymizing payment records: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _soft_delete_user(
        self,
        user_id: str,
        user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Soft delete and anonymize user account.

        Args:
            user_id: User ID
            user: User document

        Returns:
            Dict with deletion status
        """
        try:
            # Generate anonymized identifiers
            anonymized_name = anonymize_user_id(user_id)
            anonymized_email_addr = anonymize_email(user_id)

            # Soft delete with anonymization
            anonymized_user = {
                "id": user_id,
                "email": anonymized_email_addr,
                "hashed_password": "[DELETED]",
                "first_name": "[REDACTED]",
                "last_name": "[REDACTED]",
                "role": user.get("role"),  # Keep for audit purposes
                "status": "deleted",
                "is_active": False,
                "is_verified": False,
                "deleted_at": datetime.utcnow().isoformat(),
                "anonymized_at": datetime.utcnow().isoformat(),
                "anonymized_name": anonymized_name,
                "deletion_reason": user.get("deletion_reason"),
                "created_at": user.get("created_at"),  # Keep for audit
                "updated_at": datetime.utcnow().isoformat()
            }

            # Update user document
            self.db.update_document(
                "users",
                user_id,
                anonymized_user,
                merge=False
            )

            logger.info(f"Soft deleted and anonymized user {user_id}")

            return {
                "success": True,
                "user_id": user_id,
                "anonymized_name": anonymized_name
            }

        except Exception as e:
            logger.error(f"Error soft deleting user: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _send_deletion_confirmation_email(
        self,
        user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send account deletion confirmation email.

        Args:
            user: User document

        Returns:
            Dict with email send status
        """
        try:
            email = user.get("email", "unknown")
            first_name = user.get("first_name", "Member")

            # HTML email body
            html_body = f"""
            <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                        .header {{ background-color: #1a1a1a; color: white; padding: 20px; text-align: center; }}
                        .content {{ background-color: #f9f9f9; padding: 30px; border-radius: 5px; margin-top: 20px; }}
                        .warning {{
                            background-color: #f8d7da;
                            border-left: 4px solid #dc3545;
                            padding: 15px;
                            margin: 20px 0;
                        }}
                        .info {{
                            background-color: #d1ecf1;
                            border-left: 4px solid #0c5460;
                            padding: 15px;
                            margin: 20px 0;
                        }}
                        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>Account Deletion Confirmed</h1>
                        </div>
                        <div class="content">
                            <p>Hello {first_name},</p>

                            <p>This email confirms that your WWMAA account has been permanently deleted
                            in accordance with GDPR Article 17 (Right to Erasure).</p>

                            <div class="warning">
                                <strong>What has been deleted:</strong>
                                <ul>
                                    <li>All personal information and login credentials</li>
                                    <li>Profile data (anonymized)</li>
                                    <li>Membership application history (anonymized)</li>
                                    <li>Search query history (anonymized)</li>
                                    <li>Training attendance records (anonymized)</li>
                                    <li>Active subscriptions (canceled)</li>
                                </ul>
                            </div>

                            <div class="info">
                                <strong>What has been retained (anonymized):</strong>
                                <p>For legal and compliance reasons, the following data has been anonymized
                                but retained for the specified periods:</p>
                                <ul>
                                    <li>Payment records: Retained for 7 years (tax/legal compliance)</li>
                                    <li>Audit logs: Retained for 1 year (security requirement)</li>
                                    <li>Event RSVPs: Anonymized but kept for event organizers</li>
                                </ul>
                                <p>All personally identifiable information has been removed from these records.</p>
                            </div>

                            <p><strong>This action cannot be undone.</strong> If you wish to use WWMAA services
                            again in the future, you will need to create a new account.</p>

                            <p>If you did not request this account deletion, please contact us immediately at
                            <a href="mailto:privacy@wwmaa.com">privacy@wwmaa.com</a>.</p>

                            <p>Thank you for being part of the World Wide Martial Arts Association community.</p>
                        </div>
                        <div class="footer">
                            <p>World Wide Martial Arts Association (WWMAA)<br>
                            For questions about data privacy rights, contact: privacy@wwmaa.com</p>
                            <p>This email was sent in compliance with GDPR Article 17 (Right to Erasure)</p>
                        </div>
                    </div>
                </body>
            </html>
            """

            # Plain text version
            text_body = f"""
Account Deletion Confirmed

Hello {first_name},

This email confirms that your WWMAA account has been permanently deleted in accordance with GDPR Article 17 (Right to Erasure).

WHAT HAS BEEN DELETED:
- All personal information and login credentials
- Profile data (anonymized)
- Membership application history (anonymized)
- Search query history (anonymized)
- Training attendance records (anonymized)
- Active subscriptions (canceled)

WHAT HAS BEEN RETAINED (ANONYMIZED):
For legal and compliance reasons, the following data has been anonymized but retained:
- Payment records: Retained for 7 years (tax/legal compliance)
- Audit logs: Retained for 1 year (security requirement)
- Event RSVPs: Anonymized but kept for event organizers

All personally identifiable information has been removed from these records.

This action cannot be undone. If you wish to use WWMAA services again, you will need to create a new account.

If you did not request this account deletion, please contact us immediately at privacy@wwmaa.com.

Thank you for being part of the World Wide Martial Arts Association community.

---
World Wide Martial Arts Association (WWMAA)
For questions about data privacy rights, contact: privacy@wwmaa.com
            """

            # Send email
            self.email_service._send_email(
                to_email=email,
                subject="WWMAA Account Deletion Confirmed",
                html_body=html_body,
                text_body=text_body,
                tag="account_deletion"
            )

            logger.info(f"Deletion confirmation email sent to {email}")

            return {
                "success": True,
                "message": "Confirmation email sent",
                "email": email
            }

        except Exception as e:
            logger.error(f"Error sending confirmation email: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _invalidate_user_tokens(self, user_id: str) -> Dict[str, Any]:
        """
        Invalidate all JWT tokens for a user.

        This ensures the user is immediately logged out from all devices
        and cannot use any existing tokens after account deletion.

        Args:
            user_id: User ID

        Returns:
            Dict with token invalidation status
        """
        try:
            # Import AuthService here to avoid circular dependency
            from backend.services.auth_service import AuthService
            from backend.config import get_settings

            settings = get_settings()
            auth_service = AuthService(settings)

            # Invalidate all user tokens
            invalidated_count = auth_service.invalidate_all_user_tokens(user_id)

            logger.info(
                f"Invalidated {invalidated_count} token familie(s) for user {user_id}"
            )

            return {
                "success": True,
                "tokens_invalidated": invalidated_count,
                "message": f"All tokens for user {user_id} have been invalidated"
            }

        except Exception as e:
            logger.error(f"Error invalidating user tokens: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _create_audit_log_deletion(
        self,
        user_id: Optional[str],
        action: str,
        resource_type: str,
        resource_id: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Create an audit log entry for deletion operations.

        Args:
            user_id: User ID (None for system actions)
            action: Action type
            resource_type: Resource type
            resource_id: Resource ID
            description: Description
            metadata: Additional metadata
        """
        try:
            audit_data = {
                "user_id": user_id,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "description": description,
                "success": True,
                "severity": "info",
                "tags": ["gdpr", "data_deletion"],
                "metadata": metadata or {}
            }

            self.db.create_document("audit_logs", audit_data)
            logger.debug(f"Audit log created: {action} on {resource_type}/{resource_id}")
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
