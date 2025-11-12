"""
Subscriptions Routes for WWMAA Backend

Provides public endpoints for retrieving membership tier information
and pricing details.
"""

import logging
from typing import List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from backend.services.stripe_service import TIER_PRICING, MEMBERSHIP_TIER_NAMES
from backend.models.schemas import SubscriptionTier

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/subscriptions",
    tags=["subscriptions"]
)


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class SubscriptionTierBenefit(BaseModel):
    """Individual benefit item for a subscription tier"""
    description: str = Field(..., description="Benefit description")
    included: bool = Field(default=True, description="Whether benefit is included in tier")


class SubscriptionTierResponse(BaseModel):
    """Response model for subscription tier information"""
    id: str = Field(..., description="Tier ID (free, basic, premium, lifetime)")
    code: str = Field(..., description="Tier code (uppercase variant of ID)")
    name: str = Field(..., description="Display name of tier")
    price_usd: float = Field(..., description="Price in USD (0 for free tier)")
    billing_interval: str = Field(..., description="Billing interval (free, year, lifetime)")
    benefits: List[str] = Field(..., description="List of benefits included in tier")
    features: dict = Field(..., description="Detailed feature flags and settings")
    is_popular: bool = Field(default=False, description="Whether this is the most popular tier")


class SubscriptionTiersListResponse(BaseModel):
    """Response model for list of all subscription tiers"""
    tiers: List[SubscriptionTierResponse] = Field(..., description="List of available subscription tiers")
    total: int = Field(..., description="Total number of tiers")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_tier_benefits(tier: SubscriptionTier) -> List[str]:
    """
    Get human-readable benefits list for a subscription tier

    Args:
        tier: Subscription tier enum

    Returns:
        List of benefit descriptions
    """
    if tier == SubscriptionTier.FREE:
        return [
            "Access to public events",
            "Monthly newsletter subscription",
            "Community forum access",
        ]
    elif tier == SubscriptionTier.BASIC:
        return [
            "Access to all events",
            "Access to training video library (10 videos/month)",
            "Member directory access",
            "Monthly newsletter subscription",
            "10% discount on event registrations",
            "Community forum access",
        ]
    elif tier == SubscriptionTier.PREMIUM:
        return [
            "Access to all events",
            "Unlimited training video library access",
            "Member directory access",
            "Monthly newsletter subscription",
            "20% discount on event registrations",
            "Priority customer support",
            "Exclusive members-only content",
            "Community forum access",
            "Early access to new features",
        ]
    elif tier == SubscriptionTier.LIFETIME:
        return [
            "Lifetime access to all features",
            "Access to all events",
            "Unlimited training video library access",
            "Member directory access",
            "Monthly newsletter subscription",
            "25% discount on event registrations",
            "Priority customer support",
            "Exclusive members-only content",
            "Community forum access",
            "Early access to new features",
            "Founding member badge",
            "Instructor certification opportunities",
        ]

    return []


def get_tier_features(tier: SubscriptionTier) -> dict:
    """
    Get detailed feature flags for a subscription tier

    Args:
        tier: Subscription tier enum

    Returns:
        Dictionary of feature flags and settings
    """
    if tier == SubscriptionTier.FREE:
        return {
            "event_access": "public_only",
            "training_videos": False,
            "video_limit": 0,
            "member_directory": False,
            "newsletter": True,
            "discount_events": "0%",
            "priority_support": False,
            "exclusive_content": False,
            "community_forum": True,
        }
    elif tier == SubscriptionTier.BASIC:
        return {
            "event_access": "all",
            "training_videos": True,
            "video_limit": 10,
            "member_directory": True,
            "newsletter": True,
            "discount_events": "10%",
            "priority_support": False,
            "exclusive_content": False,
            "community_forum": True,
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
            "community_forum": True,
            "early_access": True,
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
            "community_forum": True,
            "early_access": True,
            "lifetime_access": True,
            "founding_member": True,
            "instructor_certification": True,
        }

    return {}


def get_billing_interval(tier: SubscriptionTier) -> str:
    """
    Get billing interval for a subscription tier

    Args:
        tier: Subscription tier enum

    Returns:
        Billing interval string
    """
    if tier == SubscriptionTier.FREE:
        return "free"
    elif tier == SubscriptionTier.LIFETIME:
        return "lifetime"
    else:
        return "year"


# ============================================================================
# ROUTES
# ============================================================================

@router.get(
    "/health",
    summary="Subscriptions Service Health Check",
    description="Check if subscriptions service is operational"
)
async def health_check():
    """
    Health check endpoint for subscriptions service

    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "subscriptions",
        "tiers_available": len(list(SubscriptionTier))
    }


@router.get(
    "",
    response_model=SubscriptionTiersListResponse,
    summary="Get All Subscription Tiers",
    description="Retrieve all available membership subscription tiers with pricing and benefits"
)
async def get_subscription_tiers():
    """
    Get all available subscription tiers

    Public endpoint that returns information about all membership tiers including:
    - Tier ID and name
    - Pricing in USD
    - Billing interval (year/lifetime)
    - List of benefits
    - Detailed feature flags

    This endpoint is used by the frontend to display membership options
    on the pricing page.

    Returns:
        SubscriptionTiersListResponse with all available tiers

    Raises:
        HTTPException 500: If an error occurs retrieving tier information
    """
    try:
        tiers = []

        # Build response for each tier
        for tier_enum in SubscriptionTier:
            # Get pricing (convert cents to dollars)
            price_cents = TIER_PRICING.get(tier_enum, 0)
            price_usd = price_cents / 100.0

            # Get tier name
            name = MEMBERSHIP_TIER_NAMES.get(tier_enum, tier_enum.value.title() + " Membership")

            # Build tier response
            tier_data = SubscriptionTierResponse(
                id=tier_enum.value,
                code=tier_enum.value.upper(),
                name=name,
                price_usd=price_usd,
                billing_interval=get_billing_interval(tier_enum),
                benefits=get_tier_benefits(tier_enum),
                features=get_tier_features(tier_enum),
                is_popular=(tier_enum == SubscriptionTier.PREMIUM)  # Premium is most popular
            )

            tiers.append(tier_data)

        logger.info(f"Retrieved {len(tiers)} subscription tiers")

        return SubscriptionTiersListResponse(
            tiers=tiers,
            total=len(tiers)
        )

    except Exception as e:
        logger.error(f"Error retrieving subscription tiers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve subscription tiers"
        )


@router.get(
    "/{tier_id}",
    response_model=SubscriptionTierResponse,
    summary="Get Subscription Tier by ID",
    description="Retrieve detailed information about a specific subscription tier"
)
async def get_subscription_tier(tier_id: str):
    """
    Get detailed information about a specific subscription tier

    Public endpoint that returns detailed information about a single membership tier.

    Args:
        tier_id: Subscription tier ID (free, basic, premium, lifetime)

    Returns:
        SubscriptionTierResponse with tier details

    Raises:
        HTTPException 400: If tier_id is invalid
        HTTPException 500: If an error occurs retrieving tier information
    """
    try:
        # Validate tier ID
        try:
            tier_enum = SubscriptionTier(tier_id.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid tier ID: {tier_id}. Valid tiers: free, basic, premium, lifetime"
            )

        # Get pricing (convert cents to dollars)
        price_cents = TIER_PRICING.get(tier_enum, 0)
        price_usd = price_cents / 100.0

        # Get tier name
        name = MEMBERSHIP_TIER_NAMES.get(tier_enum, tier_enum.value.title() + " Membership")

        # Build tier response
        tier_data = SubscriptionTierResponse(
            id=tier_enum.value,
            code=tier_enum.value.upper(),
            name=name,
            price_usd=price_usd,
            billing_interval=get_billing_interval(tier_enum),
            benefits=get_tier_benefits(tier_enum),
            features=get_tier_features(tier_enum),
            is_popular=(tier_enum == SubscriptionTier.PREMIUM)
        )

        logger.info(f"Retrieved subscription tier: {tier_id}")

        return tier_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving subscription tier {tier_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve subscription tier"
        )


