"""
Payment History Routes for WWMAA Backend

Provides endpoints for fetching payment history with pagination,
filtering, and CSV export capabilities. Integrates with ZeroDB
for payment record storage and Stripe for receipt/invoice URLs.
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
import csv
import io

from fastapi import APIRouter, HTTPException, status, Depends, Query, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

from backend.services.zerodb_service import get_zerodb_client, ZeroDBError, ZeroDBNotFoundError
from backend.services.auth_service import AuthService
from backend.middleware.auth_middleware import get_current_user
from backend.models.schemas import Payment, PaymentStatus
from backend.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/payments", tags=["payments"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class PaymentListResponse(BaseModel):
    """Response model for payment listing"""
    payments: List[Dict[str, Any]] = Field(..., description="List of payments")
    total: int = Field(..., description="Total number of payments")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")


class PaymentDetailResponse(BaseModel):
    """Response model for single payment detail"""
    id: str = Field(..., description="Payment ID")
    user_id: str = Field(..., description="User ID")
    amount: float = Field(..., description="Payment amount")
    currency: str = Field(..., description="Currency code")
    status: str = Field(..., description="Payment status")
    payment_method: Optional[str] = Field(None, description="Payment method (last 4 digits)")
    description: Optional[str] = Field(None, description="Payment description")
    receipt_url: Optional[str] = Field(None, description="Stripe receipt URL")
    invoice_url: Optional[str] = Field(None, description="Stripe invoice URL")
    refunded_amount: float = Field(default=0.0, description="Refunded amount")
    created_at: str = Field(..., description="Payment creation date")
    processed_at: Optional[str] = Field(None, description="Processing timestamp")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_payment_response(payment: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format payment data for API response

    Args:
        payment: Raw payment data from ZeroDB

    Returns:
        Formatted payment response
    """
    # Extract payment method last 4 digits if available
    payment_method = payment.get("payment_method", "")
    if isinstance(payment_method, str) and len(payment_method) > 4:
        payment_method = f"****{payment_method[-4:]}"

    # Build receipt and invoice URLs from Stripe
    receipt_url = payment.get("receipt_url")
    invoice_url = None

    # If we have a stripe charge ID, construct the receipt URL
    stripe_charge_id = payment.get("stripe_charge_id")
    if stripe_charge_id and not receipt_url:
        receipt_url = f"https://dashboard.stripe.com/charges/{stripe_charge_id}"

    # If we have a stripe payment intent ID, construct invoice URL
    stripe_payment_intent_id = payment.get("stripe_payment_intent_id")
    if stripe_payment_intent_id:
        invoice_url = f"https://dashboard.stripe.com/invoices/{stripe_payment_intent_id}"

    return {
        "id": str(payment.get("id")),
        "user_id": str(payment.get("user_id")),
        "amount": payment.get("amount", 0.0),
        "currency": payment.get("currency", "USD"),
        "status": payment.get("status", "pending"),
        "payment_method": payment_method,
        "description": payment.get("description"),
        "receipt_url": receipt_url,
        "invoice_url": invoice_url,
        "refunded_amount": payment.get("refunded_amount", 0.0),
        "refunded_at": payment.get("refunded_at"),
        "refund_reason": payment.get("refund_reason"),
        "created_at": payment.get("created_at"),
        "processed_at": payment.get("processed_at"),
    }


def filter_payments_by_date_range(
    payments: List[Dict[str, Any]],
    start_date: Optional[datetime],
    end_date: Optional[datetime]
) -> List[Dict[str, Any]]:
    """
    Filter payments by date range

    Args:
        payments: List of payment records
        start_date: Start date filter (inclusive)
        end_date: End date filter (inclusive)

    Returns:
        Filtered list of payments
    """
    if not start_date and not end_date:
        return payments

    filtered = []
    for payment in payments:
        created_at = payment.get("created_at")
        if not created_at:
            continue

        # Parse datetime if it's a string
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                continue

        # Check date range
        if start_date and created_at < start_date:
            continue
        if end_date and created_at > end_date:
            continue

        filtered.append(payment)

    return filtered


# ============================================================================
# ROUTES
# ============================================================================

@router.get("", response_model=PaymentListResponse)
async def list_payments(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    start_date: Optional[str] = Query(None, description="Start date filter (ISO 8601)"),
    end_date: Optional[str] = Query(None, description="End date filter (ISO 8601)"),
    status: Optional[str] = Query(None, description="Payment status filter"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get paginated payment history for the current user

    Query Parameters:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 10, max: 100)
    - start_date: Filter payments after this date (ISO 8601 format)
    - end_date: Filter payments before this date (ISO 8601 format)
    - status: Filter by payment status (paid, failed, refunded, etc.)

    Returns:
        Paginated list of payments with metadata
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found in token"
            )

        logger.info(f"Fetching payments for user {user_id} (page={page}, per_page={per_page})")

        # Get ZeroDB client
        zerodb = get_zerodb_client()

        # Build filters for ZeroDB query
        filters = {"user_id": {"$eq": str(user_id)}}

        # Add status filter if provided
        if status:
            filters["status"] = {"$eq": status}

        # Query payments from ZeroDB (fetch more than needed for date filtering)
        result = zerodb.query_documents(
            collection="payments",
            filters=filters,
            limit=1000,  # Fetch a large set for date filtering
            offset=0,
            sort={"created_at": "desc"}
        )

        payments = result.get("documents", [])
        logger.info(f"Found {len(payments)} total payments for user {user_id}")

        # Parse date filters
        start_date_obj = None
        end_date_obj = None

        if start_date:
            try:
                start_date_obj = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid start_date format. Use ISO 8601 format."
                )

        if end_date:
            try:
                end_date_obj = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid end_date format. Use ISO 8601 format."
                )

        # Filter by date range if provided
        if start_date_obj or end_date_obj:
            payments = filter_payments_by_date_range(payments, start_date_obj, end_date_obj)
            logger.info(f"After date filtering: {len(payments)} payments")

        # Calculate pagination
        total = len(payments)
        total_pages = (total + per_page - 1) // per_page
        offset = (page - 1) * per_page

        # Slice for current page
        paginated_payments = payments[offset:offset + per_page]

        # Format payments for response
        formatted_payments = [format_payment_response(p) for p in paginated_payments]

        return PaymentListResponse(
            payments=formatted_payments,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )

    except HTTPException:
        raise
    except ZeroDBError as e:
        logger.error(f"ZeroDB error fetching payments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch payment history"
        )
    except Exception as e:
        logger.error(f"Error fetching payments: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.get("/{payment_id}", response_model=PaymentDetailResponse)
async def get_payment(
    payment_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get details for a specific payment

    Path Parameters:
    - payment_id: Payment ID

    Returns:
        Payment details

    Raises:
        404: Payment not found or access denied
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found in token"
            )

        logger.info(f"Fetching payment {payment_id} for user {user_id}")

        # Get ZeroDB client
        zerodb = get_zerodb_client()

        # Fetch payment from ZeroDB
        payment = zerodb.get_document(
            collection="payments",
            document_id=payment_id
        )

        # Verify the payment belongs to the current user
        if str(payment.get("user_id")) != str(user_id):
            logger.warning(f"User {user_id} attempted to access payment {payment_id} belonging to another user")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )

        # Format and return payment
        return format_payment_response(payment)

    except HTTPException:
        raise
    except ZeroDBNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    except ZeroDBError as e:
        logger.error(f"ZeroDB error fetching payment {payment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch payment details"
        )
    except Exception as e:
        logger.error(f"Error fetching payment {payment_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post("/create-renewal-session")
async def create_renewal_session(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a Stripe Checkout session for membership renewal

    Validates user has an active or expiring membership and creates
    a checkout session to renew at the current tier.

    Returns:
        Checkout session URL and details

    Raises:
        401: User not authenticated
        400: User has no active membership to renew
        500: Stripe API error
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found in token"
            )

        logger.info(f"Creating renewal session for user {user_id}")

        # Get ZeroDB client
        zerodb = get_zerodb_client()

        # Find user's current active subscription
        result = zerodb.query_documents(
            collection="subscriptions",
            filters={
                "user_id": {"$eq": str(user_id)},
                "status": {"$in": ["active", "past_due"]}
            },
            sort={"created_at": "desc"},
            limit=1
        )

        subscriptions = result.get("documents", [])
        if not subscriptions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active membership found to renew. Please purchase a new membership."
            )

        current_subscription = subscriptions[0]
        tier = current_subscription.get("tier")

        # Validate tier is renewable (not free)
        if tier == "free":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Free tier memberships cannot be renewed"
            )

        logger.info(f"Found active subscription for user {user_id}, tier: {tier}")

        # Get user email for checkout
        try:
            user_result = zerodb.get_document("users", user_id)
            user = user_result.get("data", {})
            customer_email = user.get("email")
            stripe_customer_id = user.get("stripe_customer_id")
        except Exception as e:
            logger.error(f"Error fetching user data: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch user information"
            )

        # Import Stripe service
        from backend.services.stripe_service import get_stripe_service
        stripe_service = get_stripe_service()

        # Create renewal checkout session
        try:
            session_data = stripe_service.create_renewal_checkout_session(
                user_id=user_id,
                tier_id=tier,
                subscription_id=current_subscription.get("id"),
                customer_email=customer_email,
                stripe_customer_id=stripe_customer_id
            )

            logger.info(
                f"Renewal checkout session created: {session_data.get('session_id')} "
                f"for user {user_id}, tier {tier}"
            )

            return {
                "session_id": session_data.get("session_id"),
                "url": session_data.get("url"),
                "amount": session_data.get("amount"),
                "currency": session_data.get("currency"),
                "tier": tier,
                "mode": session_data.get("mode"),
                "expires_at": session_data.get("expires_at")
            }

        except Exception as e:
            logger.error(f"Failed to create renewal checkout session: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create renewal checkout session: {str(e)}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in create_renewal_session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.get("/export/csv")
async def export_payments_csv(
    start_date: Optional[str] = Query(None, description="Start date filter (ISO 8601)"),
    end_date: Optional[str] = Query(None, description="End date filter (ISO 8601)"),
    status: Optional[str] = Query(None, description="Payment status filter"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Export payment history to CSV

    Query Parameters:
    - start_date: Filter payments after this date (ISO 8601 format)
    - end_date: Filter payments before this date (ISO 8601 format)
    - status: Filter by payment status

    Returns:
        CSV file with payment history
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found in token"
            )

        logger.info(f"Exporting payments to CSV for user {user_id}")

        # Get ZeroDB client
        zerodb = get_zerodb_client()

        # Build filters
        filters = {"user_id": {"$eq": str(user_id)}}
        if status:
            filters["status"] = {"$eq": status}

        # Query all payments
        result = zerodb.query_documents(
            collection="payments",
            filters=filters,
            limit=10000,  # Large limit for export
            offset=0,
            sort={"created_at": "desc"}
        )

        payments = result.get("documents", [])

        # Parse and apply date filters
        start_date_obj = None
        end_date_obj = None

        if start_date:
            try:
                start_date_obj = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid start_date format"
                )

        if end_date:
            try:
                end_date_obj = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid end_date format"
                )

        if start_date_obj or end_date_obj:
            payments = filter_payments_by_date_range(payments, start_date_obj, end_date_obj)

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            "Date",
            "Amount",
            "Currency",
            "Status",
            "Payment Method",
            "Description",
            "Refunded Amount",
            "Receipt URL",
            "Invoice URL"
        ])

        # Write data rows
        for payment in payments:
            formatted = format_payment_response(payment)
            writer.writerow([
                formatted.get("created_at", ""),
                formatted.get("amount", 0.0),
                formatted.get("currency", "USD"),
                formatted.get("status", ""),
                formatted.get("payment_method", ""),
                formatted.get("description", ""),
                formatted.get("refunded_amount", 0.0),
                formatted.get("receipt_url", ""),
                formatted.get("invoice_url", "")
            ])

        # Prepare response
        output.seek(0)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"wwmaa_payments_{timestamp}.csv"

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except HTTPException:
        raise
    except ZeroDBError as e:
        logger.error(f"ZeroDB error exporting payments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export payment history"
        )
    except Exception as e:
        logger.error(f"Error exporting payments: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )
