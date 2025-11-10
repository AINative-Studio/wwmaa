"""
RSVP Service for WWMAA Backend

Handles event RSVP operations including:
- Capacity checking and validation
- RSVP creation for free and paid events
- Duplicate prevention
- Waitlist management
- RSVP cancellation with refund logic
- Integration with Stripe for paid events
- Email notifications with QR codes

Business Rules:
- Free events: Immediate RSVP confirmation
- Paid events: RSVP confirmed after Stripe checkout completion
- Capacity checking: Reject if full, offer waitlist
- Cancellation policy: Full refund if >24 hours before event
- Duplicate prevention: One RSVP per user per event
- QR codes: Generated for check-in at events
"""

import logging
import qrcode
import io
import base64
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4

from backend.config import settings
from backend.services.zerodb_service import get_zerodb_client, ZeroDBError, ZeroDBNotFoundError
from backend.services.stripe_service import get_stripe_service, CheckoutSessionError
from backend.services.email_service import get_email_service
from backend.models.schemas import RSVPStatus, PaymentStatus

logger = logging.getLogger(__name__)


class RSVPServiceError(Exception):
    """Base exception for RSVP service errors"""
    pass


class EventFullError(RSVPServiceError):
    """Exception raised when event is at full capacity"""
    pass


class DuplicateRSVPError(RSVPServiceError):
    """Exception raised when user already has an RSVP for this event"""
    pass


class CancellationError(RSVPServiceError):
    """Exception raised when RSVP cancellation fails"""
    pass


class RSVPService:
    """
    Service for managing event RSVPs

    Features:
    - Capacity validation before RSVP
    - Duplicate RSVP prevention
    - Free event immediate confirmation
    - Paid event Stripe checkout integration
    - Waitlist management
    - RSVP cancellation with refund logic
    - Email notifications with QR codes
    """

    def __init__(self):
        """Initialize RSVP service with required dependencies"""
        self.db = get_zerodb_client()
        self.stripe_service = get_stripe_service()
        self.email_service = get_email_service()
        logger.info("RSVPService initialized")

    def check_event_capacity(self, event_id: str) -> Dict[str, Any]:
        """
        Check if event has available capacity

        Args:
            event_id: Event UUID

        Returns:
            Dict with capacity information:
            - has_capacity: bool
            - current_attendees: int
            - max_attendees: int or None
            - available_spots: int or None
            - waitlist_enabled: bool

        Raises:
            RSVPServiceError: If event not found or capacity check fails
        """
        try:
            # Get event details
            event_result = self.db.get_document("events", event_id)
            event = event_result.get("data", {})

            if not event:
                raise RSVPServiceError(f"Event {event_id} not found")

            max_attendees = event.get("max_attendees")
            current_attendees = event.get("current_attendees", 0)
            waitlist_enabled = event.get("waitlist_enabled", False)

            # If no max_attendees set, unlimited capacity
            if max_attendees is None:
                return {
                    "has_capacity": True,
                    "current_attendees": current_attendees,
                    "max_attendees": None,
                    "available_spots": None,
                    "waitlist_enabled": waitlist_enabled,
                    "is_unlimited": True
                }

            # Calculate available spots
            available_spots = max_attendees - current_attendees
            has_capacity = available_spots > 0

            return {
                "has_capacity": has_capacity,
                "current_attendees": current_attendees,
                "max_attendees": max_attendees,
                "available_spots": available_spots,
                "waitlist_enabled": waitlist_enabled,
                "is_unlimited": False
            }

        except ZeroDBNotFoundError:
            raise RSVPServiceError(f"Event {event_id} not found")
        except ZeroDBError as e:
            logger.error(f"Error checking event capacity: {e}")
            raise RSVPServiceError(f"Failed to check event capacity: {str(e)}")

    def check_duplicate_rsvp(self, event_id: str, user_id: str) -> Dict[str, Any]:
        """
        Check if user already has an RSVP for this event

        Args:
            event_id: Event UUID
            user_id: User UUID

        Returns:
            Dict with:
            - has_rsvp: bool
            - rsvp_id: UUID or None
            - status: RSVPStatus or None

        Raises:
            RSVPServiceError: If check fails
        """
        try:
            # Query for existing RSVP
            result = self.db.query_documents(
                collection="rsvps",
                filters={
                    "event_id": event_id,
                    "user_id": user_id
                },
                limit=1
            )

            documents = result.get("documents", [])

            if documents:
                rsvp = documents[0].get("data", {})
                return {
                    "has_rsvp": True,
                    "rsvp_id": rsvp.get("id"),
                    "status": rsvp.get("status")
                }

            return {
                "has_rsvp": False,
                "rsvp_id": None,
                "status": None
            }

        except ZeroDBError as e:
            logger.error(f"Error checking duplicate RSVP: {e}")
            raise RSVPServiceError(f"Failed to check for duplicate RSVP: {str(e)}")

    def generate_qr_code(self, rsvp_id: str, event_id: str, user_id: str) -> str:
        """
        Generate QR code for event check-in

        QR code contains JSON with rsvp_id, event_id, and user_id
        Returns base64-encoded PNG image

        Args:
            rsvp_id: RSVP UUID
            event_id: Event UUID
            user_id: User UUID

        Returns:
            Base64-encoded PNG image string
        """
        try:
            # Create QR code data
            qr_data = f"WWMAA-RSVP:{rsvp_id}:{event_id}:{user_id}"

            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)

            # Create image
            img = qr.make_image(fill_color="black", back_color="white")

            # Convert to base64
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()

            return img_str

        except Exception as e:
            logger.error(f"Error generating QR code: {e}")
            return ""

    def create_free_event_rsvp(
        self,
        event_id: str,
        user_id: str,
        user_name: str,
        user_email: str,
        user_phone: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create RSVP for free event with immediate confirmation

        Args:
            event_id: Event UUID
            user_id: User UUID
            user_name: User's full name
            user_email: User's email address
            user_phone: User's phone number (optional)

        Returns:
            Created RSVP data with:
            - rsvp_id: UUID
            - status: "confirmed"
            - qr_code: Base64-encoded PNG
            - event_details: Event information

        Raises:
            EventFullError: If event is at capacity
            DuplicateRSVPError: If user already has RSVP
            RSVPServiceError: For other errors
        """
        try:
            # Check for duplicate RSVP
            duplicate_check = self.check_duplicate_rsvp(event_id, user_id)
            if duplicate_check["has_rsvp"]:
                raise DuplicateRSVPError(
                    f"User {user_id} already has an RSVP for event {event_id} "
                    f"with status {duplicate_check['status']}"
                )

            # Check event capacity
            capacity_check = self.check_event_capacity(event_id)
            if not capacity_check["has_capacity"]:
                raise EventFullError(
                    f"Event {event_id} is at full capacity "
                    f"({capacity_check['max_attendees']} attendees)"
                )

            # Get event details
            event_result = self.db.get_document("events", event_id)
            event = event_result.get("data", {})

            # Verify event is free
            registration_fee = event.get("registration_fee", 0)
            if registration_fee and registration_fee > 0:
                raise RSVPServiceError(
                    "This is a paid event. Use create_paid_event_checkout instead."
                )

            # Create RSVP record
            now = datetime.utcnow()
            rsvp_id = str(uuid4())

            rsvp_data = {
                "id": rsvp_id,
                "event_id": event_id,
                "user_id": user_id,
                "user_name": user_name,
                "user_email": user_email,
                "user_phone": user_phone,
                "rsvp_date": now.isoformat(),
                "status": RSVPStatus.CONFIRMED.value,
                "payment_id": None,
                "payment_status": None,
                "check_in_status": False,
                "check_in_time": None,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat()
            }

            result = self.db.create_document("rsvps", rsvp_data)

            logger.info(f"Created free event RSVP {rsvp_id} for user {user_id}, event {event_id}")

            # Update event attendee count
            self.db.update_document(
                "events",
                event_id,
                {"current_attendees": capacity_check["current_attendees"] + 1},
                merge=True
            )

            # Generate QR code
            qr_code = self.generate_qr_code(rsvp_id, event_id, user_id)

            # Send confirmation email
            try:
                self.email_service.send_free_event_rsvp_confirmation(
                    email=user_email,
                    user_name=user_name,
                    event_title=event.get("title"),
                    event_date=event.get("start_datetime"),
                    event_location=event.get("location_name"),
                    event_address=event.get("address"),
                    qr_code=qr_code,
                    rsvp_id=rsvp_id
                )
                logger.info(f"Sent RSVP confirmation email to {user_email}")
            except Exception as e:
                logger.error(f"Failed to send RSVP confirmation email: {e}")
                # Don't fail RSVP if email fails

            return {
                "rsvp_id": rsvp_id,
                "status": RSVPStatus.CONFIRMED.value,
                "event_id": event_id,
                "event_title": event.get("title"),
                "event_date": event.get("start_datetime"),
                "qr_code": qr_code,
                "message": "RSVP confirmed successfully!"
            }

        except (EventFullError, DuplicateRSVPError):
            raise
        except ZeroDBError as e:
            logger.error(f"Database error creating RSVP: {e}")
            raise RSVPServiceError(f"Failed to create RSVP: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error creating RSVP: {e}")
            raise RSVPServiceError(f"Unexpected error: {str(e)}")

    def create_paid_event_checkout(
        self,
        event_id: str,
        user_id: str,
        user_email: str,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create Stripe checkout session for paid event RSVP

        RSVP is created after successful payment via webhook

        Args:
            event_id: Event UUID
            user_id: User UUID
            user_email: User's email address
            success_url: Custom success URL (optional)
            cancel_url: Custom cancel URL (optional)

        Returns:
            Stripe checkout session data with:
            - session_id: Stripe session ID
            - url: Checkout URL
            - amount: Event fee in cents

        Raises:
            EventFullError: If event is at capacity
            DuplicateRSVPError: If user already has RSVP
            RSVPServiceError: For other errors
        """
        try:
            # Check for duplicate RSVP
            duplicate_check = self.check_duplicate_rsvp(event_id, user_id)
            if duplicate_check["has_rsvp"]:
                raise DuplicateRSVPError(
                    f"User {user_id} already has an RSVP for event {event_id}"
                )

            # Check event capacity
            capacity_check = self.check_event_capacity(event_id)
            if not capacity_check["has_capacity"]:
                raise EventFullError(
                    f"Event {event_id} is at full capacity"
                )

            # Get event details
            event_result = self.db.get_document("events", event_id)
            event = event_result.get("data", {})

            registration_fee = event.get("registration_fee")
            if not registration_fee or registration_fee <= 0:
                raise RSVPServiceError(
                    "This is a free event. Use create_free_event_rsvp instead."
                )

            # Convert fee to cents
            amount_cents = int(registration_fee * 100)

            # Set default URLs if not provided
            if not success_url:
                frontend_url = settings.PYTHON_BACKEND_URL.replace(":8000", ":3000")
                success_url = f"{frontend_url}/events/{event_id}/rsvp/success?session_id={{CHECKOUT_SESSION_ID}}"

            if not cancel_url:
                frontend_url = settings.PYTHON_BACKEND_URL.replace(":8000", ":3000")
                cancel_url = f"{frontend_url}/events/{event_id}"

            # Create Stripe checkout session
            import stripe
            stripe.api_key = self.stripe_service.api_key

            session = stripe.checkout.Session.create(
                mode="payment",
                line_items=[{
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"Event Registration: {event.get('title')}",
                            "description": f"Registration for {event.get('title')} on {event.get('start_datetime')}",
                        },
                        "unit_amount": amount_cents,
                    },
                    "quantity": 1,
                }],
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=user_email,
                client_reference_id=user_id,
                metadata={
                    "type": "event_rsvp",
                    "event_id": event_id,
                    "user_id": user_id,
                },
                payment_method_types=["card"],
                expires_at=int((datetime.utcnow().timestamp()) + 1800),  # 30 minutes
            )

            logger.info(
                f"Created checkout session {session.id} for event {event_id}, "
                f"user {user_id}, amount ${registration_fee:.2f}"
            )

            return {
                "session_id": session.id,
                "url": session.url,
                "amount": amount_cents,
                "currency": "usd",
                "event_title": event.get("title"),
                "expires_at": session.expires_at
            }

        except (EventFullError, DuplicateRSVPError):
            raise
        except CheckoutSessionError as e:
            logger.error(f"Stripe checkout error: {e}")
            raise RSVPServiceError(f"Failed to create checkout session: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error creating paid event checkout: {e}")
            raise RSVPServiceError(f"Unexpected error: {str(e)}")

    def cancel_rsvp(
        self,
        rsvp_id: str,
        user_id: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cancel an RSVP with refund logic for paid events

        Refund Policy:
        - >24 hours before event: Full refund
        - <24 hours before event: No refund

        Args:
            rsvp_id: RSVP UUID
            user_id: User UUID (for authorization)
            reason: Cancellation reason (optional)

        Returns:
            Cancellation result with:
            - success: bool
            - refund_issued: bool
            - refund_amount: float or None
            - message: str

        Raises:
            CancellationError: If cancellation fails
            RSVPServiceError: For other errors
        """
        try:
            # Get RSVP details
            rsvp_result = self.db.get_document("rsvps", rsvp_id)
            rsvp = rsvp_result.get("data", {})

            if not rsvp:
                raise RSVPServiceError(f"RSVP {rsvp_id} not found")

            # Verify user owns this RSVP
            if str(rsvp.get("user_id")) != str(user_id):
                raise CancellationError("You don't have permission to cancel this RSVP")

            # Check if already canceled
            if rsvp.get("status") == RSVPStatus.CANCELED.value:
                return {
                    "success": True,
                    "refund_issued": False,
                    "refund_amount": None,
                    "message": "RSVP was already canceled"
                }

            # Get event details
            event_id = rsvp.get("event_id")
            event_result = self.db.get_document("events", event_id)
            event = event_result.get("data", {})

            event_start = datetime.fromisoformat(event.get("start_datetime").replace("Z", "+00:00"))
            now = datetime.utcnow()
            hours_until_event = (event_start - now).total_seconds() / 3600

            # Check if within cancellation window (24 hours)
            can_refund = hours_until_event > 24

            refund_issued = False
            refund_amount = None

            # Handle refund for paid events
            payment_id = rsvp.get("payment_id")
            if payment_id and can_refund:
                try:
                    # Get payment details
                    payment_result = self.db.get_document("payments", payment_id)
                    payment = payment_result.get("data", {})

                    stripe_charge_id = payment.get("stripe_charge_id")
                    if stripe_charge_id:
                        # Issue refund via Stripe
                        import stripe
                        stripe.api_key = self.stripe_service.api_key

                        refund = stripe.Refund.create(
                            charge=stripe_charge_id,
                            reason="requested_by_customer"
                        )

                        refund_amount = refund.amount / 100  # Convert cents to dollars
                        refund_issued = True

                        # Update payment record
                        self.db.update_document(
                            "payments",
                            payment_id,
                            {
                                "status": PaymentStatus.REFUNDED.value,
                                "refunded_amount": refund_amount,
                                "refunded_at": now.isoformat(),
                                "refund_reason": reason or "User requested cancellation"
                            },
                            merge=True
                        )

                        logger.info(f"Issued refund ${refund_amount:.2f} for RSVP {rsvp_id}")

                except Exception as e:
                    logger.error(f"Error issuing refund: {e}")
                    # Continue with cancellation even if refund fails

            # Update RSVP status
            self.db.update_document(
                "rsvps",
                rsvp_id,
                {
                    "status": RSVPStatus.CANCELED.value,
                    "canceled_at": now.isoformat(),
                    "cancellation_reason": reason,
                    "updated_at": now.isoformat()
                },
                merge=True
            )

            # Update event attendee count
            current_attendees = event.get("current_attendees", 0)
            if current_attendees > 0:
                self.db.update_document(
                    "events",
                    event_id,
                    {"current_attendees": current_attendees - 1},
                    merge=True
                )

            # Send cancellation confirmation email
            try:
                self.email_service.send_rsvp_cancellation_confirmation(
                    email=rsvp.get("user_email"),
                    user_name=rsvp.get("user_name"),
                    event_title=event.get("title"),
                    event_date=event.get("start_datetime"),
                    refund_issued=refund_issued,
                    refund_amount=refund_amount
                )
            except Exception as e:
                logger.error(f"Failed to send cancellation email: {e}")

            # Check waitlist and promote if available
            if event.get("waitlist_enabled"):
                self._promote_from_waitlist(event_id)

            message = "RSVP canceled successfully"
            if refund_issued:
                message += f" with ${refund_amount:.2f} refund"
            elif payment_id and not can_refund:
                message += " (no refund - within 24 hours of event)"

            logger.info(f"Canceled RSVP {rsvp_id} for user {user_id}")

            return {
                "success": True,
                "refund_issued": refund_issued,
                "refund_amount": refund_amount,
                "hours_until_event": hours_until_event,
                "message": message
            }

        except CancellationError:
            raise
        except ZeroDBError as e:
            logger.error(f"Database error canceling RSVP: {e}")
            raise RSVPServiceError(f"Failed to cancel RSVP: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error canceling RSVP: {e}")
            raise RSVPServiceError(f"Unexpected error: {str(e)}")

    def add_to_waitlist(
        self,
        event_id: str,
        user_id: str,
        user_name: str,
        user_email: str,
        user_phone: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add user to event waitlist

        Args:
            event_id: Event UUID
            user_id: User UUID
            user_name: User's full name
            user_email: User's email address
            user_phone: User's phone number (optional)

        Returns:
            Waitlist entry data

        Raises:
            RSVPServiceError: If waitlist add fails
        """
        try:
            # Check if waitlist is enabled
            event_result = self.db.get_document("events", event_id)
            event = event_result.get("data", {})

            if not event.get("waitlist_enabled"):
                raise RSVPServiceError("Waitlist is not enabled for this event")

            # Check for duplicate
            duplicate_check = self.check_duplicate_rsvp(event_id, user_id)
            if duplicate_check["has_rsvp"]:
                raise DuplicateRSVPError(
                    f"User already has an entry for this event with status {duplicate_check['status']}"
                )

            # Create waitlist RSVP
            now = datetime.utcnow()
            rsvp_id = str(uuid4())

            rsvp_data = {
                "id": rsvp_id,
                "event_id": event_id,
                "user_id": user_id,
                "user_name": user_name,
                "user_email": user_email,
                "user_phone": user_phone,
                "rsvp_date": now.isoformat(),
                "status": RSVPStatus.WAITLIST.value,
                "payment_id": None,
                "payment_status": None,
                "check_in_status": False,
                "check_in_time": None,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat()
            }

            result = self.db.create_document("rsvps", rsvp_data)

            logger.info(f"Added user {user_id} to waitlist for event {event_id}")

            # Send waitlist confirmation email
            try:
                self.email_service.send_waitlist_notification(
                    email=user_email,
                    user_name=user_name,
                    event_title=event.get("title"),
                    event_date=event.get("start_datetime")
                )
            except Exception as e:
                logger.error(f"Failed to send waitlist email: {e}")

            return {
                "rsvp_id": rsvp_id,
                "status": RSVPStatus.WAITLIST.value,
                "message": "You've been added to the waitlist. We'll notify you if a spot opens up."
            }

        except DuplicateRSVPError:
            raise
        except ZeroDBError as e:
            logger.error(f"Database error adding to waitlist: {e}")
            raise RSVPServiceError(f"Failed to add to waitlist: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error adding to waitlist: {e}")
            raise RSVPServiceError(f"Unexpected error: {str(e)}")

    def get_rsvp_status(self, event_id: str, user_id: str) -> Dict[str, Any]:
        """
        Get user's RSVP status for an event

        Args:
            event_id: Event UUID
            user_id: User UUID

        Returns:
            RSVP status information
        """
        try:
            # Check for existing RSVP
            duplicate_check = self.check_duplicate_rsvp(event_id, user_id)

            if not duplicate_check["has_rsvp"]:
                # Check event capacity
                capacity_check = self.check_event_capacity(event_id)

                return {
                    "has_rsvp": False,
                    "can_rsvp": capacity_check["has_capacity"],
                    "event_full": not capacity_check["has_capacity"],
                    "waitlist_available": capacity_check["waitlist_enabled"] and not capacity_check["has_capacity"],
                    "available_spots": capacity_check.get("available_spots")
                }

            # Get full RSVP details
            rsvp_result = self.db.get_document("rsvps", duplicate_check["rsvp_id"])
            rsvp = rsvp_result.get("data", {})

            return {
                "has_rsvp": True,
                "rsvp_id": duplicate_check["rsvp_id"],
                "status": rsvp.get("status"),
                "rsvp_date": rsvp.get("rsvp_date"),
                "payment_status": rsvp.get("payment_status"),
                "check_in_status": rsvp.get("check_in_status")
            }

        except Exception as e:
            logger.error(f"Error getting RSVP status: {e}")
            raise RSVPServiceError(f"Failed to get RSVP status: {str(e)}")

    def _promote_from_waitlist(self, event_id: str) -> None:
        """
        Promote first person from waitlist to confirmed when spot opens

        Args:
            event_id: Event UUID
        """
        try:
            # Check if there's capacity
            capacity_check = self.check_event_capacity(event_id)
            if not capacity_check["has_capacity"]:
                return

            # Find first waitlist entry
            result = self.db.query_documents(
                collection="rsvps",
                filters={
                    "event_id": event_id,
                    "status": RSVPStatus.WAITLIST.value
                },
                limit=1,
                order_by="created_at"
            )

            waitlist_entries = result.get("documents", [])
            if not waitlist_entries:
                return

            waitlist_rsvp = waitlist_entries[0].get("data", {})
            rsvp_id = waitlist_rsvp.get("id")

            # Get event details
            event_result = self.db.get_document("events", event_id)
            event = event_result.get("data", {})

            # Check if event is paid
            registration_fee = event.get("registration_fee", 0)

            if registration_fee and registration_fee > 0:
                # For paid events, send notification to complete payment
                try:
                    self.email_service.send_waitlist_spot_available_paid(
                        email=waitlist_rsvp.get("user_email"),
                        user_name=waitlist_rsvp.get("user_name"),
                        event_title=event.get("title"),
                        event_date=event.get("start_datetime"),
                        event_id=event_id,
                        registration_fee=registration_fee
                    )
                    logger.info(f"Notified waitlist user {waitlist_rsvp.get('user_id')} - payment required")
                except Exception as e:
                    logger.error(f"Failed to send waitlist promotion email: {e}")
            else:
                # For free events, automatically confirm
                self.db.update_document(
                    "rsvps",
                    rsvp_id,
                    {
                        "status": RSVPStatus.CONFIRMED.value,
                        "updated_at": datetime.utcnow().isoformat()
                    },
                    merge=True
                )

                # Update event count
                self.db.update_document(
                    "events",
                    event_id,
                    {"current_attendees": capacity_check["current_attendees"] + 1},
                    merge=True
                )

                # Generate QR code
                qr_code = self.generate_qr_code(
                    rsvp_id,
                    event_id,
                    waitlist_rsvp.get("user_id")
                )

                # Send confirmation email
                try:
                    self.email_service.send_free_event_rsvp_confirmation(
                        email=waitlist_rsvp.get("user_email"),
                        user_name=waitlist_rsvp.get("user_name"),
                        event_title=event.get("title"),
                        event_date=event.get("start_datetime"),
                        event_location=event.get("location_name"),
                        event_address=event.get("address"),
                        qr_code=qr_code,
                        rsvp_id=rsvp_id,
                        from_waitlist=True
                    )
                    logger.info(f"Promoted user {waitlist_rsvp.get('user_id')} from waitlist")
                except Exception as e:
                    logger.error(f"Failed to send waitlist promotion email: {e}")

        except Exception as e:
            logger.error(f"Error promoting from waitlist: {e}")
            # Don't raise - this is a background operation


# Global RSVP service instance (singleton pattern)
_rsvp_service_instance: Optional[RSVPService] = None


def get_rsvp_service() -> RSVPService:
    """
    Get or create the global RSVPService instance

    Returns:
        RSVPService instance
    """
    global _rsvp_service_instance

    if _rsvp_service_instance is None:
        _rsvp_service_instance = RSVPService()

    return _rsvp_service_instance
