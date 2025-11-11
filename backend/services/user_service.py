"""
User Service - User Management with Newsletter Integration

This service manages user account operations:
- User profile updates
- Email address changes with BeeHiiv sync (US-059)
- Account deactivation/reactivation
- User role management

Integrates with:
- BeeHiiv for email sync
- ZeroDB for user storage
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from backend.config import settings
from backend.services.zerodb_service import ZeroDBClient, ZeroDBNotFoundError
from backend.services.membership_webhook_handler import get_membership_webhook_handler
from backend.models.schemas import UserRole, AuditAction

logger = logging.getLogger(__name__)


class UserServiceError(Exception):
    """Base exception for user service errors"""
    pass


class UserNotFoundError(UserServiceError):
    """Exception raised when user is not found"""
    pass


class EmailAlreadyExistsError(UserServiceError):
    """Exception raised when email already exists"""
    pass


class UserService:
    """
    Service for managing user accounts

    Implements:
    - User profile management
    - Email change with newsletter sync
    - Account status management
    - Role management
    """

    def __init__(self, zerodb_client: Optional[ZeroDBClient] = None):
        """
        Initialize User Service

        Args:
            zerodb_client: Optional ZeroDB client instance
        """
        self.db = zerodb_client or ZeroDBClient()
        self.webhook_handler = get_membership_webhook_handler()
        logger.info("UserService initialized")

    async def update_user_email(
        self,
        user_id: str,
        new_email: str,
        verify_unique: bool = True
    ) -> Dict[str, Any]:
        """
        Update user email and sync to BeeHiiv

        Args:
            user_id: User ID
            new_email: New email address
            verify_unique: Whether to verify email uniqueness

        Returns:
            Dict with updated user data

        Raises:
            UserNotFoundError: If user not found
            EmailAlreadyExistsError: If email already exists
            UserServiceError: If update fails
        """
        try:
            # Get current user
            user_result = self.db.get_document("users", user_id)
            user = user_result.get("data", {})

            if not user:
                raise UserNotFoundError(f"User {user_id} not found")

            old_email = user.get("email")
            new_email = new_email.lower().strip()

            # Check if email is changing
            if old_email == new_email:
                return {
                    "success": True,
                    "message": "Email unchanged",
                    "user_id": user_id,
                    "email": new_email
                }

            # Verify email uniqueness if requested
            if verify_unique:
                existing = self.db.query_documents(
                    "users",
                    filters={"email": new_email},
                    limit=1
                )

                if existing.get("documents"):
                    existing_user = existing["documents"][0]
                    if existing_user.get("id") != user_id:
                        raise EmailAlreadyExistsError(
                            f"Email {new_email} is already registered to another user"
                        )

            # Update user email
            update_data = {
                "email": new_email,
                "updated_at": datetime.utcnow().isoformat(),
                "is_verified": False  # Require re-verification
            }

            updated_result = self.db.update_document(
                "users",
                user_id,
                update_data,
                merge=True
            )

            updated_user = updated_result.get("data", {})

            logger.info(f"User email updated: {user_id} from {old_email} to {new_email}")

            # Create audit log
            self._create_audit_log(
                user_id=user_id,
                action=AuditAction.UPDATE,
                resource_type="users",
                resource_id=user_id,
                description=f"Email updated: {old_email} -> {new_email}",
                changes={
                    "old_email": old_email,
                    "new_email": new_email
                }
            )

            # Sync to BeeHiiv if user is a member (US-059)
            newsletter_result = None
            user_role = user.get("role")

            if user_role in [UserRole.MEMBER, UserRole.INSTRUCTOR, UserRole.BOARD_MEMBER]:
                try:
                    newsletter_result = await self.webhook_handler.handle_email_changed(
                        user_id=user_id,
                        old_email=old_email,
                        new_email=new_email
                    )
                    logger.info(f"Newsletter email sync completed for user {user_id}")
                except Exception as e:
                    logger.error(f"Failed to sync email to newsletter: {e}")
                    # Don't fail user update if newsletter sync fails

            return {
                "success": True,
                "user_id": user_id,
                "user": updated_user,
                "old_email": old_email,
                "new_email": new_email,
                "newsletter_sync": newsletter_result
            }

        except ZeroDBNotFoundError:
            raise UserNotFoundError(f"User {user_id} not found")
        except Exception as e:
            logger.error(f"Error updating user email: {e}")
            raise UserServiceError(f"Failed to update user email: {str(e)}")

    def update_user_profile(
        self,
        user_id: str,
        profile_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update user profile information

        Args:
            user_id: User ID
            profile_data: Profile data to update

        Returns:
            Dict with updated user data

        Raises:
            UserNotFoundError: If user not found
            UserServiceError: If update fails
        """
        try:
            # Get user
            user_result = self.db.get_document("users", user_id)
            user = user_result.get("data", {})

            if not user:
                raise UserNotFoundError(f"User {user_id} not found")

            # Get or create profile
            profile_id = user.get("profile_id")

            if not profile_id:
                # Create new profile
                profile_create_data = {
                    "user_id": user_id,
                    **profile_data,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }

                profile_result = self.db.create_document("profiles", profile_create_data)
                profile_id = profile_result.get("id")
                profile = profile_result.get("data", {})

                # Link profile to user
                self.db.update_document(
                    "users",
                    user_id,
                    {"profile_id": profile_id},
                    merge=True
                )

                logger.info(f"Profile created for user {user_id}: {profile_id}")

            else:
                # Update existing profile
                profile_data["updated_at"] = datetime.utcnow().isoformat()

                profile_result = self.db.update_document(
                    "profiles",
                    str(profile_id),
                    profile_data,
                    merge=True
                )

                profile = profile_result.get("data", {})

                logger.info(f"Profile updated for user {user_id}")

            # Create audit log
            self._create_audit_log(
                user_id=user_id,
                action=AuditAction.UPDATE,
                resource_type="profiles",
                resource_id=str(profile_id),
                description="User profile updated",
                changes=profile_data
            )

            return {
                "success": True,
                "user_id": user_id,
                "profile_id": profile_id,
                "profile": profile
            }

        except ZeroDBNotFoundError:
            raise UserNotFoundError(f"User {user_id} not found")
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            raise UserServiceError(f"Failed to update user profile: {str(e)}")

    def deactivate_user(
        self,
        user_id: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Deactivate user account

        Args:
            user_id: User ID
            reason: Deactivation reason

        Returns:
            Dict with deactivation details

        Raises:
            UserNotFoundError: If user not found
            UserServiceError: If deactivation fails
        """
        try:
            # Get user
            user_result = self.db.get_document("users", user_id)
            user = user_result.get("data", {})

            if not user:
                raise UserNotFoundError(f"User {user_id} not found")

            # Update user status
            update_data = {
                "is_active": False,
                "updated_at": datetime.utcnow().isoformat()
            }

            updated_result = self.db.update_document(
                "users",
                user_id,
                update_data,
                merge=True
            )

            updated_user = updated_result.get("data", {})

            logger.info(f"User deactivated: {user_id}")

            # Create audit log
            self._create_audit_log(
                user_id=user_id,
                action=AuditAction.UPDATE,
                resource_type="users",
                resource_id=user_id,
                description=f"User account deactivated: {reason or 'No reason provided'}",
                changes={
                    "is_active": False,
                    "reason": reason
                }
            )

            return {
                "success": True,
                "user_id": user_id,
                "user": updated_user,
                "reason": reason
            }

        except ZeroDBNotFoundError:
            raise UserNotFoundError(f"User {user_id} not found")
        except Exception as e:
            logger.error(f"Error deactivating user: {e}")
            raise UserServiceError(f"Failed to deactivate user: {str(e)}")

    def reactivate_user(self, user_id: str) -> Dict[str, Any]:
        """
        Reactivate user account

        Args:
            user_id: User ID

        Returns:
            Dict with reactivation details

        Raises:
            UserNotFoundError: If user not found
            UserServiceError: If reactivation fails
        """
        try:
            # Get user
            user_result = self.db.get_document("users", user_id)
            user = user_result.get("data", {})

            if not user:
                raise UserNotFoundError(f"User {user_id} not found")

            # Update user status
            update_data = {
                "is_active": True,
                "updated_at": datetime.utcnow().isoformat()
            }

            updated_result = self.db.update_document(
                "users",
                user_id,
                update_data,
                merge=True
            )

            updated_user = updated_result.get("data", {})

            logger.info(f"User reactivated: {user_id}")

            # Create audit log
            self._create_audit_log(
                user_id=user_id,
                action=AuditAction.UPDATE,
                resource_type="users",
                resource_id=user_id,
                description="User account reactivated",
                changes={"is_active": True}
            )

            return {
                "success": True,
                "user_id": user_id,
                "user": updated_user
            }

        except ZeroDBNotFoundError:
            raise UserNotFoundError(f"User {user_id} not found")
        except Exception as e:
            logger.error(f"Error reactivating user: {e}")
            raise UserServiceError(f"Failed to reactivate user: {str(e)}")

    def update_user_role(
        self,
        user_id: str,
        new_role: str,
        updated_by: str
    ) -> Dict[str, Any]:
        """
        Update user role

        Args:
            user_id: User ID
            new_role: New role
            updated_by: ID of user making the change

        Returns:
            Dict with updated user data

        Raises:
            UserNotFoundError: If user not found
            UserServiceError: If update fails
        """
        try:
            # Get user
            user_result = self.db.get_document("users", user_id)
            user = user_result.get("data", {})

            if not user:
                raise UserNotFoundError(f"User {user_id} not found")

            old_role = user.get("role")

            # Update role
            update_data = {
                "role": new_role,
                "updated_at": datetime.utcnow().isoformat()
            }

            updated_result = self.db.update_document(
                "users",
                user_id,
                update_data,
                merge=True
            )

            updated_user = updated_result.get("data", {})

            logger.info(f"User role updated: {user_id} from {old_role} to {new_role}")

            # Create audit log
            self._create_audit_log(
                user_id=updated_by,
                action=AuditAction.UPDATE,
                resource_type="users",
                resource_id=user_id,
                description=f"User role updated: {old_role} -> {new_role}",
                changes={
                    "old_role": old_role,
                    "new_role": new_role
                }
            )

            return {
                "success": True,
                "user_id": user_id,
                "user": updated_user,
                "old_role": old_role,
                "new_role": new_role
            }

        except ZeroDBNotFoundError:
            raise UserNotFoundError(f"User {user_id} not found")
        except Exception as e:
            logger.error(f"Error updating user role: {e}")
            raise UserServiceError(f"Failed to update user role: {str(e)}")

    def _create_audit_log(
        self,
        user_id: Optional[str],
        action: str,
        resource_type: str,
        resource_id: str,
        description: str,
        changes: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Create an audit log entry

        Args:
            user_id: User ID (None for system actions)
            action: Action type
            resource_type: Resource type
            resource_id: Resource ID
            description: Description
            changes: Changes made
        """
        try:
            audit_data = {
                "user_id": user_id,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "description": description,
                "changes": changes or {},
                "success": True,
                "severity": "info",
                "tags": ["user_management"],
                "metadata": {}
            }

            self.db.create_document("audit_logs", audit_data)
            logger.debug(f"Audit log created: {action} on {resource_type}/{resource_id}")
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")


# Singleton instance
_user_service_instance = None


def get_user_service() -> UserService:
    """
    Get singleton user service instance

    Returns:
        UserService instance
    """
    global _user_service_instance
    if _user_service_instance is None:
        _user_service_instance = UserService()
    return _user_service_instance
