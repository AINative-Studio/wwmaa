"""
Newsletter Service - BeeHiiv Integration for Member Auto-Subscribe

This service implements automatic newsletter subscription management:
- Auto-subscribes new members to Members Only list
- Manages Instructor tier subscriptions
- Syncs email changes across all lists
- Handles subscription cancellation workflows
- Respects user unsubscribe preferences

BeeHiiv List Structure:
- General: Public subscribers (opt-in required)
- Members Only: All active members (auto-subscribed, no double opt-in)
- Instructors: Members with Instructor tier (auto-subscribed)

Business Rules:
1. New members are automatically added to Members Only list
2. Instructors are automatically added to both Members Only and Instructors lists
3. Canceled members removed from Members Only but stay in General if opted-in
4. Email changes are synced across all BeeHiiv lists
5. Manual unsubscribes are respected and stored in preferences
"""

import logging
import asyncio
import httpx
from datetime import datetime
from typing import Dict, Any, List, Optional
from backend.config import settings
from backend.services.zerodb_service import ZeroDBClient, ZeroDBNotFoundError
from backend.models.schemas import SubscriptionTier, SubscriptionStatus, AuditAction

logger = logging.getLogger(__name__)


class NewsletterServiceError(Exception):
    """Base exception for newsletter service errors"""
    pass


class BeeHiivAPIError(NewsletterServiceError):
    """Exception raised when BeeHiiv API calls fail"""
    pass


class UnsubscribePreferenceError(NewsletterServiceError):
    """Exception raised when user has unsubscribe preferences"""
    pass


# BeeHiiv List Configuration
BEEHIIV_LISTS = {
    "general": "general",  # Public subscribers (opt-in required)
    "members_only": "members_only",  # Auto-subscribed active members
    "instructors": "instructors",  # Auto-subscribed instructor tier members
}


class NewsletterService:
    """
    Service for managing BeeHiiv newsletter subscriptions

    Implements:
    - Auto-subscription for new members
    - Tier-based list management
    - Email change synchronization
    - Subscription cancellation handling
    - User preference tracking
    """

    BEEHIIV_API_BASE = "https://api.beehiiv.com/v2"

    def __init__(
        self,
        api_key: Optional[str] = None,
        publication_id: Optional[str] = None,
        zerodb_client: Optional[ZeroDBClient] = None
    ):
        """
        Initialize Newsletter Service

        Args:
            api_key: BeeHiiv API key (defaults to settings.BEEHIIV_API_KEY)
            publication_id: BeeHiiv publication ID (defaults to settings.BEEHIIV_PUBLICATION_ID)
            zerodb_client: Optional ZeroDB client instance
        """
        self.api_key = api_key or settings.BEEHIIV_API_KEY
        self.publication_id = publication_id or settings.BEEHIIV_PUBLICATION_ID
        self.db = zerodb_client or ZeroDBClient()

        if not self.api_key:
            raise NewsletterServiceError("BEEHIIV_API_KEY is required")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        logger.info("NewsletterService initialized")

    async def _make_beehiiv_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a request to BeeHiiv API with retry logic

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., "/subscriptions")
            data: Request body data
            params: Query parameters

        Returns:
            API response data

        Raises:
            BeeHiivAPIError: If API request fails after retries
        """
        url = f"{self.BEEHIIV_API_BASE}{endpoint}"
        max_retries = 3
        retry_delay = 1

        async with httpx.AsyncClient() as client:
            for attempt in range(max_retries):
                try:
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=self.headers,
                        json=data,
                        params=params,
                        timeout=30.0
                    )

                    if response.status_code in [200, 201]:
                        return response.json()
                    elif response.status_code == 404:
                        return {"error": "not_found", "status_code": 404}
                    elif response.status_code == 409:
                        # Already exists - treat as success
                        return {"error": "already_exists", "status_code": 409}
                    elif response.status_code >= 500:
                        # Server error - retry
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_delay * (attempt + 1))
                            continue

                    raise BeeHiivAPIError(
                        f"BeeHiiv API error: {response.status_code} - {response.text}"
                    )

                except httpx.TimeoutException:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay * (attempt + 1))
                        continue
                    raise BeeHiivAPIError("BeeHiiv API timeout after retries")

                except httpx.RequestError as e:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay * (attempt + 1))
                        continue
                    raise BeeHiivAPIError(f"BeeHiiv API request error: {str(e)}")

        raise BeeHiivAPIError("Max retries exceeded")

    async def _check_unsubscribe_preference(
        self,
        user_id: str,
        list_name: str
    ) -> bool:
        """
        Check if user has unsubscribed from a specific list

        Args:
            user_id: User ID
            list_name: List name to check

        Returns:
            True if user has unsubscribed, False otherwise
        """
        try:
            result = self.db.query_documents(
                "user_newsletter_preferences",
                filters={"user_id": user_id},
                limit=1
            )

            prefs = result.get("documents", [])
            if not prefs:
                return False

            pref = prefs[0]
            unsubscribed_lists = pref.get("unsubscribed_lists", [])
            return list_name in unsubscribed_lists

        except Exception as e:
            logger.warning(f"Error checking unsubscribe preference: {e}")
            return False

    async def _record_unsubscribe_preference(
        self,
        user_id: str,
        list_name: str,
        reason: Optional[str] = None
    ) -> None:
        """
        Record user's unsubscribe preference

        Args:
            user_id: User ID
            list_name: List name
            reason: Optional unsubscribe reason
        """
        try:
            # Try to get existing preferences
            result = self.db.query_documents(
                "user_newsletter_preferences",
                filters={"user_id": user_id},
                limit=1
            )

            prefs = result.get("documents", [])

            if prefs:
                # Update existing
                pref = prefs[0]
                pref_id = pref.get("id")
                unsubscribed_lists = pref.get("unsubscribed_lists", [])

                if list_name not in unsubscribed_lists:
                    unsubscribed_lists.append(list_name)

                self.db.update_document(
                    "user_newsletter_preferences",
                    str(pref_id),
                    {
                        "unsubscribed_lists": unsubscribed_lists,
                        "last_unsubscribe_at": datetime.utcnow().isoformat(),
                        "last_unsubscribe_reason": reason or "",
                        "updated_at": datetime.utcnow().isoformat()
                    },
                    merge=True
                )
            else:
                # Create new
                self.db.create_document(
                    "user_newsletter_preferences",
                    {
                        "user_id": user_id,
                        "unsubscribed_lists": [list_name],
                        "last_unsubscribe_at": datetime.utcnow().isoformat(),
                        "last_unsubscribe_reason": reason or "",
                        "subscribed_lists": []
                    }
                )

            logger.info(f"Recorded unsubscribe preference for user {user_id} from {list_name}")

        except Exception as e:
            logger.error(f"Error recording unsubscribe preference: {e}")

    async def auto_subscribe_member(
        self,
        user_id: str,
        tier: str
    ) -> Dict[str, Any]:
        """
        Auto-subscribe new member to appropriate newsletter lists

        Called when:
        - Application approved
        - Subscription created

        Args:
            user_id: User ID
            tier: Subscription tier (basic, premium, lifetime/instructor)

        Returns:
            Dict with subscription results

        Raises:
            NewsletterServiceError: If subscription fails
        """
        try:
            # Get user data
            user_result = self.db.get_document("users", user_id)
            user = user_result.get("data", {})

            if not user:
                raise NewsletterServiceError(f"User {user_id} not found")

            email = user.get("email")
            if not email:
                raise NewsletterServiceError(f"User {user_id} has no email")

            # Get user profile for name
            profile_id = user.get("profile_id")
            first_name = ""
            last_name = ""

            if profile_id:
                try:
                    profile_result = self.db.get_document("profiles", str(profile_id))
                    profile = profile_result.get("data", {})
                    first_name = profile.get("first_name", "")
                    last_name = profile.get("last_name", "")
                except:
                    pass

            results = {
                "user_id": user_id,
                "email": email,
                "tier": tier,
                "subscribed_lists": [],
                "skipped_lists": [],
                "errors": []
            }

            # Check if user unsubscribed from Members Only
            members_unsubscribed = await self._check_unsubscribe_preference(
                user_id,
                BEEHIIV_LISTS["members_only"]
            )

            if members_unsubscribed:
                logger.info(f"User {user_id} has unsubscribed from Members Only - skipping")
                results["skipped_lists"].append("members_only")
            else:
                # Subscribe to Members Only list
                members_result = await self._subscribe_to_list(
                    email=email,
                    list_name=BEEHIIV_LISTS["members_only"],
                    first_name=first_name,
                    last_name=last_name,
                    double_opt_in=False
                )

                if members_result.get("success"):
                    results["subscribed_lists"].append("members_only")
                else:
                    results["errors"].append(f"Members Only: {members_result.get('error')}")

            # If Instructor tier, add to Instructors list
            if tier in ["lifetime", SubscriptionTier.LIFETIME]:
                instructors_unsubscribed = await self._check_unsubscribe_preference(
                    user_id,
                    BEEHIIV_LISTS["instructors"]
                )

                if instructors_unsubscribed:
                    logger.info(f"User {user_id} has unsubscribed from Instructors - skipping")
                    results["skipped_lists"].append("instructors")
                else:
                    instructors_result = await self._subscribe_to_list(
                        email=email,
                        list_name=BEEHIIV_LISTS["instructors"],
                        first_name=first_name,
                        last_name=last_name,
                        double_opt_in=False
                    )

                    if instructors_result.get("success"):
                        results["subscribed_lists"].append("instructors")
                    else:
                        results["errors"].append(f"Instructors: {instructors_result.get('error')}")

            # Create audit log
            self._create_audit_log(
                user_id=user_id,
                action=AuditAction.CREATE,
                resource_type="newsletter_subscriptions",
                resource_id=user_id,
                description=f"Auto-subscribed member to newsletter lists: {', '.join(results['subscribed_lists'])}",
                changes={
                    "tier": tier,
                    "subscribed_lists": results["subscribed_lists"],
                    "skipped_lists": results["skipped_lists"]
                }
            )

            logger.info(
                f"Auto-subscribed user {user_id} to lists: {results['subscribed_lists']}"
            )

            return results

        except Exception as e:
            logger.error(f"Error auto-subscribing member: {e}")
            raise NewsletterServiceError(f"Failed to auto-subscribe member: {str(e)}")

    async def _subscribe_to_list(
        self,
        email: str,
        list_name: str,
        first_name: str = "",
        last_name: str = "",
        double_opt_in: bool = False
    ) -> Dict[str, Any]:
        """
        Subscribe email to a BeeHiiv list

        Args:
            email: Email address
            list_name: List name
            first_name: First name
            last_name: Last name
            double_opt_in: Whether to send confirmation email

        Returns:
            Dict with success status
        """
        try:
            # Check if already subscribed
            check_result = await self._make_beehiiv_request(
                "GET",
                f"/publications/{self.publication_id}/subscriptions",
                params={"email": email}
            )

            # If already exists, check list membership
            if check_result.get("data"):
                existing = check_result["data"][0] if isinstance(check_result["data"], list) else check_result["data"]
                current_lists = existing.get("custom_fields", {}).get("lists", [])

                if list_name in current_lists:
                    logger.info(f"Email {email} already subscribed to {list_name}")
                    return {"success": True, "already_exists": True}

            # Subscribe to list
            data = {
                "email": email,
                "reactivate_existing": True,
                "send_welcome_email": False,
                "utm_source": "wwmaa_membership",
                "utm_medium": "auto_subscribe",
                "referring_site": "wwmaa.com",
                "custom_fields": {
                    "lists": [list_name]
                }
            }

            if first_name:
                data["custom_fields"]["first_name"] = first_name
            if last_name:
                data["custom_fields"]["last_name"] = last_name

            result = await self._make_beehiiv_request(
                "POST",
                f"/publications/{self.publication_id}/subscriptions",
                data=data
            )

            if result.get("error") == "already_exists":
                return {"success": True, "already_exists": True}

            return {"success": True, "data": result}

        except BeeHiivAPIError as e:
            logger.error(f"BeeHiiv API error subscribing to {list_name}: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Error subscribing to list: {e}")
            return {"success": False, "error": str(e)}

    async def upgrade_to_instructor(self, user_id: str) -> Dict[str, Any]:
        """
        Add member to Instructors list when upgrading tier

        Args:
            user_id: User ID

        Returns:
            Dict with upgrade results
        """
        try:
            # Get user data
            user_result = self.db.get_document("users", user_id)
            user = user_result.get("data", {})
            email = user.get("email")

            if not email:
                raise NewsletterServiceError(f"User {user_id} has no email")

            # Check unsubscribe preference
            if await self._check_unsubscribe_preference(user_id, BEEHIIV_LISTS["instructors"]):
                logger.info(f"User {user_id} has unsubscribed from Instructors - skipping")
                return {
                    "success": False,
                    "skipped": True,
                    "reason": "User has unsubscribed"
                }

            # Get profile for name
            profile_id = user.get("profile_id")
            first_name = ""
            last_name = ""

            if profile_id:
                try:
                    profile_result = self.db.get_document("profiles", str(profile_id))
                    profile = profile_result.get("data", {})
                    first_name = profile.get("first_name", "")
                    last_name = profile.get("last_name", "")
                except:
                    pass

            # Add to Instructors list
            result = await self._subscribe_to_list(
                email=email,
                list_name=BEEHIIV_LISTS["instructors"],
                first_name=first_name,
                last_name=last_name,
                double_opt_in=False
            )

            # Create audit log
            self._create_audit_log(
                user_id=user_id,
                action=AuditAction.UPDATE,
                resource_type="newsletter_subscriptions",
                resource_id=user_id,
                description="Upgraded member to Instructors list",
                changes={"added_to_list": "instructors"}
            )

            logger.info(f"Upgraded user {user_id} to Instructors list")

            return result

        except Exception as e:
            logger.error(f"Error upgrading to instructor: {e}")
            raise NewsletterServiceError(f"Failed to upgrade to instructor: {str(e)}")

    async def downgrade_from_instructor(self, user_id: str) -> Dict[str, Any]:
        """
        Remove member from Instructors list when downgrading tier

        Args:
            user_id: User ID

        Returns:
            Dict with downgrade results
        """
        try:
            # Get user data
            user_result = self.db.get_document("users", user_id)
            user = user_result.get("data", {})
            email = user.get("email")

            if not email:
                raise NewsletterServiceError(f"User {user_id} has no email")

            # Remove from Instructors list
            result = await self._unsubscribe_from_list(
                email=email,
                list_name=BEEHIIV_LISTS["instructors"]
            )

            # Create audit log
            self._create_audit_log(
                user_id=user_id,
                action=AuditAction.UPDATE,
                resource_type="newsletter_subscriptions",
                resource_id=user_id,
                description="Downgraded member from Instructors list",
                changes={"removed_from_list": "instructors"}
            )

            logger.info(f"Downgraded user {user_id} from Instructors list")

            return result

        except Exception as e:
            logger.error(f"Error downgrading from instructor: {e}")
            raise NewsletterServiceError(f"Failed to downgrade from instructor: {str(e)}")

    async def handle_subscription_canceled(self, user_id: str) -> Dict[str, Any]:
        """
        Handle newsletter changes when subscription is canceled

        Removes from Members Only list but keeps in General if opted-in

        Args:
            user_id: User ID

        Returns:
            Dict with cancellation results
        """
        try:
            # Get user data
            user_result = self.db.get_document("users", user_id)
            user = user_result.get("data", {})
            email = user.get("email")

            if not email:
                raise NewsletterServiceError(f"User {user_id} has no email")

            results = {
                "user_id": user_id,
                "email": email,
                "unsubscribed_lists": [],
                "errors": []
            }

            # Remove from Members Only
            members_result = await self._unsubscribe_from_list(
                email=email,
                list_name=BEEHIIV_LISTS["members_only"]
            )

            if members_result.get("success"):
                results["unsubscribed_lists"].append("members_only")
            else:
                results["errors"].append(f"Members Only: {members_result.get('error')}")

            # Remove from Instructors if present
            instructors_result = await self._unsubscribe_from_list(
                email=email,
                list_name=BEEHIIV_LISTS["instructors"]
            )

            if instructors_result.get("success"):
                results["unsubscribed_lists"].append("instructors")
            else:
                results["errors"].append(f"Instructors: {instructors_result.get('error')}")

            # Keep in General list (don't unsubscribe)

            # Create audit log
            self._create_audit_log(
                user_id=user_id,
                action=AuditAction.UPDATE,
                resource_type="newsletter_subscriptions",
                resource_id=user_id,
                description=f"Removed from member lists due to cancellation: {', '.join(results['unsubscribed_lists'])}",
                changes={
                    "unsubscribed_lists": results["unsubscribed_lists"],
                    "kept_in_general": True
                }
            )

            logger.info(
                f"Handled subscription cancellation for user {user_id}: "
                f"removed from {results['unsubscribed_lists']}"
            )

            return results

        except Exception as e:
            logger.error(f"Error handling subscription cancellation: {e}")
            raise NewsletterServiceError(f"Failed to handle cancellation: {str(e)}")

    async def _unsubscribe_from_list(
        self,
        email: str,
        list_name: str
    ) -> Dict[str, Any]:
        """
        Unsubscribe email from a BeeHiiv list

        Args:
            email: Email address
            list_name: List name

        Returns:
            Dict with success status
        """
        try:
            # Get subscription ID
            check_result = await self._make_beehiiv_request(
                "GET",
                f"/publications/{self.publication_id}/subscriptions",
                params={"email": email}
            )

            if not check_result.get("data"):
                logger.info(f"Email {email} not found in BeeHiiv")
                return {"success": True, "not_found": True}

            subscription = check_result["data"][0] if isinstance(check_result["data"], list) else check_result["data"]
            subscription_id = subscription.get("id")

            if not subscription_id:
                return {"success": False, "error": "No subscription ID found"}

            # Update subscription to remove from list
            current_lists = subscription.get("custom_fields", {}).get("lists", [])
            updated_lists = [l for l in current_lists if l != list_name]

            result = await self._make_beehiiv_request(
                "PUT",
                f"/publications/{self.publication_id}/subscriptions/{subscription_id}",
                data={
                    "custom_fields": {
                        "lists": updated_lists
                    }
                }
            )

            return {"success": True, "data": result}

        except BeeHiivAPIError as e:
            logger.error(f"BeeHiiv API error unsubscribing from {list_name}: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Error unsubscribing from list: {e}")
            return {"success": False, "error": str(e)}

    async def sync_email_change(
        self,
        old_email: str,
        new_email: str
    ) -> Dict[str, Any]:
        """
        Sync email change across all BeeHiiv lists

        Args:
            old_email: Old email address
            new_email: New email address

        Returns:
            Dict with sync results
        """
        try:
            # Get old subscription
            check_result = await self._make_beehiiv_request(
                "GET",
                f"/publications/{self.publication_id}/subscriptions",
                params={"email": old_email}
            )

            if not check_result.get("data"):
                logger.info(f"Old email {old_email} not found in BeeHiiv - nothing to sync")
                return {"success": True, "not_found": True}

            subscription = check_result["data"][0] if isinstance(check_result["data"], list) else check_result["data"]
            subscription_id = subscription.get("id")
            current_lists = subscription.get("custom_fields", {}).get("lists", [])
            first_name = subscription.get("custom_fields", {}).get("first_name", "")
            last_name = subscription.get("custom_fields", {}).get("last_name", "")

            # Update email in BeeHiiv
            result = await self._make_beehiiv_request(
                "PUT",
                f"/publications/{self.publication_id}/subscriptions/{subscription_id}",
                data={
                    "email": new_email,
                    "custom_fields": {
                        "lists": current_lists,
                        "first_name": first_name,
                        "last_name": last_name
                    }
                }
            )

            logger.info(f"Synced email change from {old_email} to {new_email} in BeeHiiv")

            return {
                "success": True,
                "old_email": old_email,
                "new_email": new_email,
                "lists_synced": current_lists
            }

        except BeeHiivAPIError as e:
            logger.error(f"BeeHiiv API error syncing email change: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Error syncing email change: {e}")
            raise NewsletterServiceError(f"Failed to sync email change: {str(e)}")

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
                "tags": ["newsletter", "auto_subscribe"],
                "metadata": {}
            }

            self.db.create_document("audit_logs", audit_data)
            logger.debug(f"Audit log created: {action} on {resource_type}/{resource_id}")
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")

    # ========================================================================
    # PUBLIC NEWSLETTER SUBSCRIPTION (US-058)
    # ========================================================================

    async def public_subscribe(
        self,
        email: str,
        name: Optional[str] = None,
        interests: Optional[List[str]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        source: str = "website"
    ) -> Dict[str, Any]:
        """
        Public newsletter subscription with double opt-in

        Args:
            email: Subscriber email address
            name: Subscriber name (optional)
            interests: List of interests (e.g., ['events', 'training', 'news'])
            ip_address: Subscriber IP address for GDPR compliance
            user_agent: Browser user agent string
            source: Subscription source (website/checkout/member_signup)

        Returns:
            Dict with subscription details and status

        Raises:
            NewsletterServiceError: If subscription fails
        """
        import hashlib
        import jwt
        from uuid import uuid4

        email = email.lower().strip()

        # Check if subscriber already exists
        existing = await self._get_public_subscription_by_email(email)

        if existing:
            if existing.get("status") == "active":
                return {
                    "message": "This email is already subscribed to our newsletter",
                    "status": "already_subscribed",
                    "email": email
                }
            elif existing.get("status") == "pending":
                # Resend confirmation email
                await self._send_confirmation_email(
                    email=email,
                    name=name or existing.get("name"),
                    confirmation_token=existing["confirmation_token"]
                )
                return {
                    "message": "Confirmation email resent. Please check your inbox.",
                    "status": "pending",
                    "subscription_id": existing["id"]
                }

        # Create new subscription
        subscription_id = str(uuid4())
        confirmation_token = self._generate_confirmation_token(email, subscription_id)

        # Hash IP address for GDPR compliance
        ip_hash = None
        if ip_address:
            ip_hash = hashlib.sha256(ip_address.encode()).hexdigest()

        subscription_data = {
            "id": subscription_id,
            "email": email,
            "name": name,
            "interests": interests or [],
            "status": "pending",
            "confirmation_token": confirmation_token,
            "confirmation_token_expires_at": (
                datetime.utcnow() + timedelta(hours=24)
            ).isoformat(),
            "subscription_source": source,
            "ip_address_hash": ip_hash,
            "user_agent": user_agent,
            "consent_given": True,
            "consent_timestamp": datetime.utcnow().isoformat(),
            "subscribed_at": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        # Save to database
        self.db.create_document("newsletter_subscriptions", subscription_data)

        # Send confirmation email
        await self._send_confirmation_email(
            email=email,
            name=name or "Subscriber",
            confirmation_token=confirmation_token
        )

        # Log subscription event
        self._create_audit_log(
            user_id=None,
            action="create",
            resource_type="newsletter_subscription",
            resource_id=subscription_id,
            description=f"Newsletter subscription created: {email}",
            changes={"source": source, "status": "pending"}
        )

        logger.info(f"Newsletter subscription created: {email} (pending confirmation)")

        return {
            "message": "Please check your email to confirm your subscription",
            "status": "pending",
            "subscription_id": subscription_id
        }

    async def confirm_public_subscription(self, token: str) -> Dict[str, Any]:
        """
        Confirm newsletter subscription using verification token

        Args:
            token: JWT confirmation token from email

        Returns:
            Dict with confirmation status

        Raises:
            NewsletterServiceError: If confirmation fails
        """
        import jwt

        # Verify token
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM]
            )

            if payload.get("type") != "newsletter_confirmation":
                raise NewsletterServiceError("Invalid token type")

            email = payload["email"]
            subscription_id = payload["subscription_id"]

        except jwt.ExpiredSignatureError:
            raise NewsletterServiceError("Confirmation token has expired")
        except jwt.InvalidTokenError as e:
            raise NewsletterServiceError(f"Invalid confirmation token: {str(e)}")

        # Get subscription from database
        result = self.db.get_document("newsletter_subscriptions", subscription_id)
        subscription = result.get("data", {})

        if not subscription:
            raise NewsletterServiceError("Subscription not found")

        if subscription["status"] == "active":
            return {
                "message": "This subscription is already confirmed",
                "status": "active",
                "email": email
            }

        # Add to BeeHiiv General list
        try:
            beehiiv_result = await self._subscribe_to_list(
                email=email,
                name=subscription.get("name"),
                list_name="general",
                metadata={
                    "interests": subscription.get("interests", []),
                    "source": subscription.get("subscription_source"),
                    "confirmed_at": datetime.utcnow().isoformat()
                }
            )

            beehiiv_subscriber_id = beehiiv_result.get("id")

        except Exception as e:
            logger.error(f"Failed to add subscriber to BeeHiiv: {str(e)}")
            beehiiv_subscriber_id = None

        # Update subscription status
        self.db.update_document(
            "newsletter_subscriptions",
            subscription_id,
            {
                "status": "active",
                "confirmed_at": datetime.utcnow().isoformat(),
                "beehiiv_subscriber_id": beehiiv_subscriber_id,
                "updated_at": datetime.utcnow().isoformat()
            },
            merge=True
        )

        # Log confirmation event
        self._create_audit_log(
            user_id=None,
            action="update",
            resource_type="newsletter_subscription",
            resource_id=subscription_id,
            description=f"Newsletter subscription confirmed: {email}",
            changes={"status": "active", "confirmed": True}
        )

        logger.info(f"Newsletter subscription confirmed: {email}")

        return {
            "message": "Your subscription has been confirmed. Welcome!",
            "status": "active",
            "email": email,
            "subscription_id": subscription_id
        }

    async def public_unsubscribe(
        self,
        email: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Unsubscribe from newsletter

        Args:
            email: Subscriber email address
            reason: Reason for unsubscribing (optional)

        Returns:
            Dict with unsubscribe confirmation
        """
        email = email.lower().strip()

        # Get subscription from database
        subscription = await self._get_public_subscription_by_email(email)

        if not subscription:
            return {
                "message": "Email address is not subscribed",
                "status": "not_found",
                "email": email
            }

        if subscription["status"] == "unsubscribed":
            return {
                "message": "This email is already unsubscribed",
                "status": "unsubscribed",
                "email": email
            }

        subscription_id = subscription["id"]

        # Remove from BeeHiiv General list
        try:
            await self._unsubscribe_from_list(email, "general")
        except Exception as e:
            logger.warning(f"Failed to remove subscriber from BeeHiiv: {str(e)}")

        # Update subscription status
        self.db.update_document(
            "newsletter_subscriptions",
            subscription_id,
            {
                "status": "unsubscribed",
                "unsubscribed_at": datetime.utcnow().isoformat(),
                "unsubscribe_reason": reason,
                "updated_at": datetime.utcnow().isoformat()
            },
            merge=True
        )

        # Log unsubscribe event
        self._create_audit_log(
            user_id=None,
            action="delete",
            resource_type="newsletter_subscription",
            resource_id=subscription_id,
            description=f"Newsletter unsubscribe: {email}",
            changes={"status": "unsubscribed", "reason": reason}
        )

        logger.info(f"Newsletter unsubscribe: {email}")

        return {
            "message": "You have been unsubscribed from the newsletter",
            "status": "unsubscribed",
            "email": email
        }

    async def get_public_subscription_status(self, email: str) -> Dict[str, Any]:
        """
        Get subscription status for an email address

        Args:
            email: Subscriber email address

        Returns:
            Dict with subscription status and details
        """
        email = email.lower().strip()

        subscription = await self._get_public_subscription_by_email(email)

        if not subscription:
            return {
                "subscribed": False,
                "status": "not_found",
                "email": email
            }

        return {
            "subscribed": subscription["status"] == "active",
            "status": subscription["status"],
            "email": email,
            "name": subscription.get("name"),
            "interests": subscription.get("interests", []),
            "subscribed_at": subscription.get("subscribed_at"),
            "confirmed_at": subscription.get("confirmed_at")
        }

    async def update_public_preferences(
        self,
        email: str,
        interests: Optional[List[str]] = None,
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update subscriber preferences

        Args:
            email: Subscriber email address
            interests: Updated list of interests
            name: Updated name

        Returns:
            Updated subscription data
        """
        email = email.lower().strip()

        subscription = await self._get_public_subscription_by_email(email)

        if not subscription:
            raise NewsletterServiceError("Subscriber not found")

        if subscription["status"] != "active":
            raise NewsletterServiceError("Cannot update preferences for inactive subscription")

        subscription_id = subscription["id"]

        # Prepare update data
        update_data = {
            "updated_at": datetime.utcnow().isoformat()
        }

        if interests is not None:
            update_data["interests"] = interests

        if name is not None:
            update_data["name"] = name

        # Update in database
        self.db.update_document(
            "newsletter_subscriptions",
            subscription_id,
            update_data,
            merge=True
        )

        # Update in BeeHiiv
        if subscription.get("beehiiv_subscriber_id"):
            try:
                beehiiv_updates = {}
                if name:
                    beehiiv_updates["custom_fields"] = beehiiv_updates.get("custom_fields", {})
                    beehiiv_updates["custom_fields"]["name"] = name
                if interests:
                    beehiiv_updates["custom_fields"] = beehiiv_updates.get("custom_fields", {})
                    beehiiv_updates["custom_fields"]["interests"] = interests

                if beehiiv_updates:
                    await self._make_beehiiv_request(
                        "PATCH",
                        f"/publications/{self.publication_id}/subscriptions/{email}",
                        data=beehiiv_updates
                    )
            except Exception as e:
                logger.warning(f"Failed to update subscriber in BeeHiiv: {str(e)}")

        # Log update event
        self._create_audit_log(
            user_id=None,
            action="update",
            resource_type="newsletter_subscription",
            resource_id=subscription_id,
            description=f"Newsletter preferences updated: {email}",
            changes={"preferences_updated": True, "interests": interests}
        )

        logger.info(f"Newsletter preferences updated: {email}")

        # Get updated subscription
        result = self.db.get_document("newsletter_subscriptions", subscription_id)
        updated_subscription = result.get("data", {})

        return {
            "message": "Preferences updated successfully",
            "subscription": updated_subscription
        }

    async def _get_public_subscription_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get public subscription record by email address

        Args:
            email: Subscriber email address

        Returns:
            Subscription document or None if not found
        """
        result = self.db.query_documents(
            "newsletter_subscriptions",
            filters={"email": email.lower().strip()},
            limit=1
        )

        docs = result.get("documents", [])
        return docs[0] if docs else None

    def _generate_confirmation_token(self, email: str, subscription_id: str) -> str:
        """
        Generate JWT confirmation token for email verification

        Args:
            email: Subscriber email address
            subscription_id: Subscription UUID

        Returns:
            JWT token string
        """
        import jwt
        from datetime import timedelta

        payload = {
            "email": email,
            "subscription_id": subscription_id,
            "type": "newsletter_confirmation",
            "exp": datetime.utcnow() + timedelta(hours=24),
            "iat": datetime.utcnow()
        }

        token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        return token

    async def _send_confirmation_email(
        self,
        email: str,
        name: str,
        confirmation_token: str
    ):
        """
        Send confirmation email to subscriber

        Args:
            email: Subscriber email address
            name: Subscriber name
            confirmation_token: JWT confirmation token
        """
        from backend.services.email_service import EmailService

        # Build confirmation URL
        frontend_url = settings.PYTHON_BACKEND_URL.replace("localhost:8000", "localhost:3000")
        confirmation_url = f"{frontend_url}/newsletter/confirm?token={confirmation_token}"

        # Send email
        email_service = EmailService()
        try:
            email_service.send_newsletter_confirmation(
                email=email,
                name=name,
                confirmation_url=confirmation_url
            )
            logger.info(f"Confirmation email sent to: {email}")
        except Exception as e:
            logger.error(f"Failed to send confirmation email to {email}: {str(e)}")
            raise NewsletterServiceError(f"Failed to send confirmation email: {str(e)}")


# Singleton instance
_newsletter_service_instance = None


def get_newsletter_service() -> NewsletterService:
    """
    Get singleton newsletter service instance

    Returns:
        NewsletterService instance
    """
    global _newsletter_service_instance
    if _newsletter_service_instance is None:
        _newsletter_service_instance = NewsletterService()
    return _newsletter_service_instance
