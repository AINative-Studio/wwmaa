"""
Stripe Payment Service for WWMAA Backend

Provides Stripe integration for payment processing including:
- Checkout session creation
- Subscription management
- Payment intent handling
- Webhook processing
"""

import logging
import stripe
from stripe.error import StripeError
from datetime import datetime
from typing import Optional, Dict, Any, List
from backend.config import settings
from backend.services.zerodb_service import ZeroDBClient, ZeroDBNotFoundError
from backend.models.schemas import SubscriptionTier, SubscriptionStatus

logger = logging.getLogger(__name__)


class StripeServiceError(Exception):
    """Base exception for Stripe service errors"""
    pass


class CheckoutSessionError(StripeServiceError):
    """Exception raised when checkout session creation fails"""
    pass


class SubscriptionError(StripeServiceError):
    """Exception raised for subscription-related errors"""
    pass


# Membership tier pricing (in cents) - Annual billing as per US-021
TIER_PRICING = {
    SubscriptionTier.FREE: 0,
    SubscriptionTier.BASIC: 2900,      # $29.00/year (US-021 requirement)
    SubscriptionTier.PREMIUM: 7900,    # $79.00/year (US-021 requirement)
    SubscriptionTier.LIFETIME: 14900,  # $149.00 one-time (US-021: Instructor tier)
}

# Mapping to US-021 membership tier names
MEMBERSHIP_TIER_NAMES = {
    SubscriptionTier.BASIC: "Basic Membership",
    SubscriptionTier.PREMIUM: "Premium Membership",
    SubscriptionTier.LIFETIME: "Instructor Membership",
}


class StripeService:
    """
    Service for Stripe payment processing

    Implements:
    - Checkout session creation for membership payments
    - Subscription management
    - Payment webhook handling
    - Customer management
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        webhook_secret: Optional[str] = None,
        zerodb_client: Optional[ZeroDBClient] = None
    ):
        """
        Initialize Stripe Service

        Args:
            api_key: Stripe secret key (defaults to settings.STRIPE_SECRET_KEY)
            webhook_secret: Stripe webhook secret (defaults to settings.STRIPE_WEBHOOK_SECRET)
            zerodb_client: Optional ZeroDB client instance
        """
        self.api_key = api_key or settings.STRIPE_SECRET_KEY
        self.webhook_secret = webhook_secret or settings.STRIPE_WEBHOOK_SECRET
        self.db = zerodb_client or ZeroDBClient()

        if not self.api_key:
            raise StripeServiceError("STRIPE_SECRET_KEY is required")

        # Configure Stripe
        stripe.api_key = self.api_key

        logger.info("StripeService initialized")

    def create_checkout_session(
        self,
        user_id: str,
        application_id: str,
        tier_id: str,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
        customer_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a Stripe Checkout session for membership payment

        Args:
            user_id: UUID of the user
            application_id: UUID of the application
            tier_id: Subscription tier ID (basic, premium, lifetime)
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect after canceled payment
            customer_email: User's email address

        Returns:
            Dict containing:
            - session_id: Stripe checkout session ID
            - url: Checkout session URL
            - amount: Payment amount in cents
            - currency: Payment currency

        Raises:
            CheckoutSessionError: If session creation fails
            ValueError: If tier_id is invalid
        """
        try:
            # Validate tier
            if tier_id not in [tier.value for tier in SubscriptionTier]:
                raise ValueError(f"Invalid tier_id: {tier_id}")

            tier = SubscriptionTier(tier_id)

            # Free tier doesn't need payment
            if tier == SubscriptionTier.FREE:
                raise ValueError("Free tier does not require payment")

            # Get pricing
            amount = TIER_PRICING[tier]

            # Set default URLs if not provided
            if not success_url:
                frontend_url = settings.PYTHON_BACKEND_URL.replace(":8000", ":3000")
                success_url = f"{frontend_url}/membership/payment/success?session_id={{CHECKOUT_SESSION_ID}}"

            if not cancel_url:
                frontend_url = settings.PYTHON_BACKEND_URL.replace(":8000", ":3000")
                cancel_url = f"{frontend_url}/membership/payment/cancel"

            # Prepare line items
            line_items = []

            if tier == SubscriptionTier.LIFETIME:
                # One-time payment for lifetime membership
                line_items.append({
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": "WWMAA Lifetime Membership",
                            "description": "Lifetime access to WWMAA member benefits",
                        },
                        "unit_amount": amount,
                    },
                    "quantity": 1,
                })
                mode = "payment"
            else:
                # Recurring subscription for basic/premium (Annual billing per US-021)
                tier_name = MEMBERSHIP_TIER_NAMES.get(tier, "Basic" if tier == SubscriptionTier.BASIC else "Premium")
                line_items.append({
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"WWMAA {tier_name}",
                            "description": f"{tier_name} - Annual billing cycle (US-021)",
                        },
                        "unit_amount": amount,
                        "recurring": {
                            "interval": "year",  # Annual billing per US-021
                        },
                    },
                    "quantity": 1,
                })
                mode = "subscription"

            # Create checkout session
            session = stripe.checkout.Session.create(
                mode=mode,
                line_items=line_items,
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=customer_email,
                client_reference_id=user_id,
                metadata={
                    "user_id": user_id,
                    "application_id": application_id,
                    "tier_id": tier_id,
                },
                payment_method_types=["card"],
                expires_at=int((datetime.utcnow().timestamp()) + 1800),  # 30 minutes
            )

            # Store checkout session ID in application
            try:
                self.db.update_document(
                    "applications",
                    application_id,
                    {
                        "checkout_session_id": session.id,
                        "checkout_session_url": session.url,
                        "checkout_created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat()
                    },
                    merge=True
                )
                logger.info(f"Checkout session {session.id} stored in application {application_id}")
            except Exception as e:
                logger.error(f"Failed to store checkout session in application: {e}")
                # Don't fail if storage fails, session is still valid

            logger.info(
                f"Checkout session created: {session.id} for user {user_id}, "
                f"tier {tier_id}, amount ${amount/100:.2f}"
            )

            return {
                "session_id": session.id,
                "url": session.url,
                "amount": amount,
                "currency": "usd",
                "tier": tier_id,
                "mode": mode,
                "expires_at": session.expires_at
            }

        except StripeError as e:
            logger.error(f"Stripe API error creating checkout session: {e}")
            raise CheckoutSessionError(f"Failed to create checkout session: {str(e)}")
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating checkout session: {e}")
            raise CheckoutSessionError(f"Unexpected error: {str(e)}")

    def retrieve_checkout_session(self, session_id: str) -> Dict[str, Any]:
        """
        Retrieve a checkout session by ID

        Args:
            session_id: Stripe checkout session ID

        Returns:
            Checkout session data

        Raises:
            CheckoutSessionError: If retrieval fails
        """
        try:
            session = stripe.checkout.Session.retrieve(session_id)

            return {
                "id": session.id,
                "payment_status": session.payment_status,
                "customer": session.customer,
                "customer_email": session.customer_email,
                "amount_total": session.amount_total,
                "currency": session.currency,
                "metadata": session.metadata,
                "status": session.status,
            }

        except StripeError as e:
            logger.error(f"Stripe API error retrieving session: {e}")
            raise CheckoutSessionError(f"Failed to retrieve session: {str(e)}")

    def create_subscription_in_db(
        self,
        user_id: str,
        tier: str,
        stripe_subscription_id: Optional[str] = None,
        stripe_customer_id: Optional[str] = None,
        amount: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Create a subscription record in ZeroDB

        Args:
            user_id: UUID of the user
            tier: Subscription tier
            stripe_subscription_id: Stripe subscription ID (for recurring)
            stripe_customer_id: Stripe customer ID
            amount: Subscription amount

        Returns:
            Created subscription data

        Raises:
            SubscriptionError: If creation fails
        """
        try:
            tier_enum = SubscriptionTier(tier)

            # Determine interval based on tier (Annual billing per US-021)
            interval = "lifetime" if tier_enum == SubscriptionTier.LIFETIME else "year"

            # Calculate amount if not provided
            if amount is None:
                amount = TIER_PRICING[tier_enum] / 100  # Convert cents to dollars

            now = datetime.utcnow()

            subscription_data = {
                "user_id": user_id,
                "tier": tier,
                "status": SubscriptionStatus.ACTIVE,
                "stripe_subscription_id": stripe_subscription_id,
                "stripe_customer_id": stripe_customer_id,
                "start_date": now.isoformat(),
                "end_date": None,  # Will be set for non-lifetime subscriptions
                "trial_end_date": None,
                "canceled_at": None,
                "amount": amount,
                "currency": "USD",
                "interval": interval,
                "features": self._get_tier_features(tier_enum),
                "metadata": {
                    "created_via": "checkout_session",
                    "created_at": now.isoformat()
                }
            }

            result = self.db.create_document("subscriptions", subscription_data)

            logger.info(
                f"Subscription created in DB: {result.get('id')} for user {user_id}, "
                f"tier {tier}"
            )

            return result.get("data", {})

        except Exception as e:
            logger.error(f"Failed to create subscription in DB: {e}")
            raise SubscriptionError(f"Failed to create subscription: {str(e)}")

    def _get_tier_features(self, tier: SubscriptionTier) -> Dict[str, Any]:
        """
        Get features for a subscription tier

        Args:
            tier: Subscription tier

        Returns:
            Dict of tier features
        """
        if tier == SubscriptionTier.FREE:
            return {
                "event_access": "public_only",
                "training_videos": False,
                "member_directory": False,
                "newsletter": True,
            }
        elif tier == SubscriptionTier.BASIC:
            return {
                "event_access": "all",
                "training_videos": True,
                "video_limit": 10,
                "member_directory": True,
                "newsletter": True,
                "discount_events": "10%",
            }
        elif tier == SubscriptionTier.PREMIUM:
            return {
                "event_access": "all",
                "training_videos": True,
                "video_limit": "unlimited",
                "member_directory": True,
                "newsletter": True,
                "discount_events": "20%",
                "priority_support": True,
                "exclusive_content": True,
            }
        elif tier == SubscriptionTier.LIFETIME:
            return {
                "event_access": "all",
                "training_videos": True,
                "video_limit": "unlimited",
                "member_directory": True,
                "newsletter": True,
                "discount_events": "25%",
                "priority_support": True,
                "exclusive_content": True,
                "lifetime_access": True,
                "founding_member": True,
            }

        return {}

    def process_successful_payment(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Process a successful payment from checkout session

        Args:
            session_id: Stripe checkout session ID

        Returns:
            Dict with processing results

        Raises:
            SubscriptionError: If processing fails
        """
        try:
            # Retrieve session
            session = stripe.checkout.Session.retrieve(session_id)

            # Extract metadata
            user_id = session.metadata.get("user_id")
            application_id = session.metadata.get("application_id")
            tier_id = session.metadata.get("tier_id")

            if not all([user_id, application_id, tier_id]):
                raise SubscriptionError("Missing required metadata in session")

            # Create subscription in DB
            subscription = self.create_subscription_in_db(
                user_id=user_id,
                tier=tier_id,
                stripe_subscription_id=session.subscription if session.mode == "subscription" else None,
                stripe_customer_id=session.customer,
                amount=session.amount_total / 100 if session.amount_total else None
            )

            # Update application with payment success
            try:
                self.db.update_document(
                    "applications",
                    application_id,
                    {
                        "payment_completed": True,
                        "payment_completed_at": datetime.utcnow().isoformat(),
                        "subscription_id": subscription.get("id"),
                        "updated_at": datetime.utcnow().isoformat()
                    },
                    merge=True
                )
            except Exception as e:
                logger.error(f"Failed to update application with payment: {e}")

            logger.info(
                f"Payment processed successfully for session {session_id}, "
                f"user {user_id}, subscription {subscription.get('id')}"
            )

            return {
                "success": True,
                "user_id": user_id,
                "application_id": application_id,
                "subscription_id": subscription.get("id"),
                "tier": tier_id,
                "amount": session.amount_total / 100 if session.amount_total else 0,
            }

        except StripeError as e:
            logger.error(f"Stripe error processing payment: {e}")
            raise SubscriptionError(f"Failed to process payment: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing payment: {e}")
            raise SubscriptionError(f"Payment processing error: {str(e)}")

    def get_tier_pricing(self, tier: str) -> Dict[str, Any]:
        """
        Get pricing information for a tier

        Args:
            tier: Subscription tier ID

        Returns:
            Dict with pricing information
        """
        try:
            tier_enum = SubscriptionTier(tier)
            amount_cents = TIER_PRICING[tier_enum]

            return {
                "tier": tier,
                "amount_cents": amount_cents,
                "amount_dollars": amount_cents / 100,
                "currency": "USD",
                "interval": "lifetime" if tier_enum == SubscriptionTier.LIFETIME else "year",
                "features": self._get_tier_features(tier_enum)
            }
        except ValueError:
            raise ValueError(f"Invalid tier: {tier}")


# Global Stripe service instance (singleton pattern)
_stripe_service_instance: Optional[StripeService] = None


def get_stripe_service() -> StripeService:
    """
    Get or create the global StripeService instance

    Returns:
        StripeService instance
    """
    global _stripe_service_instance

    if _stripe_service_instance is None:
        _stripe_service_instance = StripeService()

    return _stripe_service_instance
