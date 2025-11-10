"""
Billing Routes - Stripe Subscription Management

This module provides endpoints for managing subscriptions through Stripe,
including creating customer portal sessions for subscription management.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
import stripe

from backend.config import get_settings
from backend.middleware.auth_middleware import get_current_user
from backend.services.zerodb_service import ZeroDBClient

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize settings and Stripe
settings = get_settings()
stripe.api_key = settings.STRIPE_SECRET_KEY

# Create router
router = APIRouter(
    prefix="/api/billing",
    tags=["billing"],
    responses={404: {"description": "Not found"}}
)


class PortalSessionRequest(BaseModel):
    """Request model for creating a customer portal session"""
    return_url: str


class PortalSessionResponse(BaseModel):
    """Response model for portal session creation"""
    url: str


@router.post("/portal", response_model=PortalSessionResponse)
async def create_portal_session(
    request: PortalSessionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> PortalSessionResponse:
    """
    Create a Stripe Customer Portal session.

    Allows members to manage their subscription, update payment methods,
    view invoices, and cancel/reactivate subscriptions.

    Args:
        request: Portal session request with return URL
        current_user: Current authenticated user from JWT

    Returns:
        PortalSessionResponse with portal URL

    Raises:
        HTTPException: 400 if user has no Stripe customer ID
        HTTPException: 500 if portal session creation fails
    """
    try:
        user_id = current_user.get("id")
        user_email = current_user.get("email")

        logger.info(f"Creating portal session for user {user_id}")

        # Get user's subscription from ZeroDB to find Stripe customer ID
        zerodb = ZeroDBClient()

        # Query subscriptions collection for user's active subscription
        subscriptions_response = zerodb.query_documents(
            collection="subscriptions",
            filters={
                "user_id": {"$eq": user_id}
            },
            limit=1
        )

        if not subscriptions_response.get("documents"):
            logger.warning(f"No subscription found for user {user_id}")
            raise HTTPException(
                status_code=404,
                detail="No subscription found. Please purchase a membership first."
            )

        subscription_data = subscriptions_response["documents"][0]
        stripe_customer_id = subscription_data.get("stripe_customer_id")

        if not stripe_customer_id:
            logger.error(f"User {user_id} has subscription but no Stripe customer ID")
            raise HTTPException(
                status_code=400,
                detail="Invalid subscription data. Please contact support."
            )

        # Create Stripe Customer Portal session
        try:
            portal_session = stripe.billing_portal.Session.create(
                customer=stripe_customer_id,
                return_url=request.return_url,
            )

            logger.info(f"Portal session created successfully for user {user_id}")

            return PortalSessionResponse(url=portal_session.url)

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating portal session: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create billing portal session: {str(e)}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating portal session: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while creating the billing portal session"
        )


@router.get("/subscription")
async def get_subscription_details(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get current user's subscription details from ZeroDB.

    Returns subscription information including status, tier, billing dates,
    and payment method on file.

    Args:
        current_user: Current authenticated user from JWT

    Returns:
        Dictionary with subscription details

    Raises:
        HTTPException: 404 if no subscription found
        HTTPException: 500 if query fails
    """
    try:
        user_id = current_user.get("id")

        logger.info(f"Fetching subscription details for user {user_id}")

        # Query ZeroDB for user's subscription
        zerodb = ZeroDBClient()

        subscriptions_response = zerodb.query_documents(
            collection="subscriptions",
            filters={
                "user_id": {"$eq": user_id}
            },
            limit=1
        )

        if not subscriptions_response.get("documents"):
            logger.warning(f"No subscription found for user {user_id}")
            raise HTTPException(
                status_code=404,
                detail="No subscription found"
            )

        subscription = subscriptions_response["documents"][0]

        # Fetch additional details from Stripe if available
        stripe_subscription_id = subscription.get("stripe_subscription_id")
        payment_method = None
        upcoming_invoice = None
        recent_invoices = []

        if stripe_subscription_id:
            try:
                # Get Stripe subscription details
                stripe_sub = stripe.Subscription.retrieve(
                    stripe_subscription_id,
                    expand=['default_payment_method', 'latest_invoice']
                )

                # Extract payment method details
                if stripe_sub.default_payment_method:
                    pm = stripe_sub.default_payment_method
                    if hasattr(pm, 'card'):
                        payment_method = {
                            "id": pm.id,
                            "type": pm.type,
                            "brand": pm.card.brand,
                            "last4": pm.card.last4,
                            "exp_month": pm.card.exp_month,
                            "exp_year": pm.card.exp_year
                        }

                # Get upcoming invoice
                try:
                    upcoming = stripe.Invoice.upcoming(
                        customer=subscription.get("stripe_customer_id")
                    )
                    upcoming_invoice = {
                        "amount_due": upcoming.amount_due / 100,  # Convert cents to dollars
                        "currency": upcoming.currency,
                        "next_payment_attempt": upcoming.next_payment_attempt
                    }
                except stripe.error.StripeError:
                    logger.warning(f"Could not fetch upcoming invoice for user {user_id}")

                # Get recent invoices
                invoices = stripe.Invoice.list(
                    customer=subscription.get("stripe_customer_id"),
                    limit=5
                )
                recent_invoices = [
                    {
                        "id": inv.id,
                        "number": inv.number,
                        "amount_paid": inv.amount_paid / 100,  # Convert cents to dollars
                        "currency": inv.currency,
                        "status": inv.status,
                        "created": inv.created,
                        "invoice_pdf": inv.invoice_pdf,
                        "hosted_invoice_url": inv.hosted_invoice_url
                    }
                    for inv in invoices.data
                ]

            except stripe.error.StripeError as e:
                logger.warning(f"Stripe error fetching details: {str(e)}")

        # Build response
        response = {
            "subscription": {
                "id": subscription.get("id"),
                "user_id": subscription.get("user_id"),
                "tier": subscription.get("tier"),
                "tier_name": subscription.get("tier", "").title(),
                "status": subscription.get("status"),
                "price": subscription.get("price", 0),
                "currency": subscription.get("currency", "usd"),
                "stripe_subscription_id": subscription.get("stripe_subscription_id"),
                "stripe_customer_id": subscription.get("stripe_customer_id"),
                "current_period_start": subscription.get("current_period_start"),
                "current_period_end": subscription.get("current_period_end"),
                "next_billing_date": subscription.get("current_period_end"),
                "cancel_at_period_end": subscription.get("cancel_at_period_end", False),
                "canceled_at": subscription.get("canceled_at"),
                "trial_end": subscription.get("trial_end_date"),
                "created_at": subscription.get("created_at"),
                "updated_at": subscription.get("updated_at")
            },
            "payment_method": payment_method,
            "upcoming_invoice": upcoming_invoice,
            "recent_invoices": recent_invoices
        }

        logger.info(f"Successfully fetched subscription details for user {user_id}")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching subscription: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while fetching subscription details"
        )
