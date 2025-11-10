"""
Attendee Management Service for WWMAA Backend

Provides functionality for managing event attendees including:
- Querying and filtering attendees
- CSV export
- Bulk email sending
- Check-in management
- Waitlist promotion
"""

import logging
import csv
import io
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from backend.services.zerodb_service import get_zerodb_client, ZeroDBError
from backend.services.email_service import get_email_service, EmailSendError
from backend.models.schemas import RSVP, RSVPStatus, Event

# Configure logging
logger = logging.getLogger(__name__)


class AttendeeServiceError(Exception):
    """Base exception for attendee service errors"""
    pass


class AttendeeService:
    """
    Service for managing event attendees

    Provides methods for:
    - Listing attendees with filters
    - Exporting attendee data to CSV
    - Sending bulk emails
    - Managing check-ins
    - Promoting waitlist members
    """

    def __init__(self):
        """Initialize Attendee Service"""
        self.db = get_zerodb_client()
        self.email_service = get_email_service()
        logger.info("AttendeeService initialized")

    def get_attendees(
        self,
        event_id: UUID,
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get attendees for an event with optional filtering

        Args:
            event_id: Event UUID
            status: Filter by RSVP status (confirmed, waitlist, canceled, etc.)
            search: Search by name or email
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            Dictionary with attendees and metadata

        Raises:
            AttendeeServiceError: If query fails
        """
        try:
            # Build filters
            filters = {"event_id": str(event_id)}

            if status:
                # Support multiple statuses
                if status == "all":
                    pass  # No status filter
                elif status == "checked-in":
                    # Check-in status is when checked_in_at is not null
                    filters["checked_in_at"] = {"$ne": None}
                elif status == "no-show":
                    # No-show: confirmed but not checked in (event has passed)
                    filters["status"] = RSVPStatus.CONFIRMED.value
                    filters["checked_in_at"] = None
                else:
                    filters["status"] = status

            logger.info(f"Querying attendees for event {event_id} with filters: {filters}")

            # Query RSVPs from ZeroDB
            result = self.db.query_documents(
                collection="rsvps",
                filters=filters,
                limit=limit,
                offset=offset,
                sort={"created_at": "desc"}
            )

            attendees = result.get("documents", [])

            # Search filter (if provided)
            if search and attendees:
                search_lower = search.lower()
                # Note: This is a simple client-side filter
                # For production, consider implementing server-side search
                attendees = [
                    att for att in attendees
                    if search_lower in att.get("user_email", "").lower() or
                       search_lower in att.get("user_name", "").lower()
                ]

            logger.info(f"Found {len(attendees)} attendees")

            return {
                "attendees": attendees,
                "total": len(attendees),
                "limit": limit,
                "offset": offset
            }

        except ZeroDBError as e:
            logger.error(f"Database error fetching attendees: {e}")
            raise AttendeeServiceError(f"Failed to fetch attendees: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching attendees: {e}")
            raise AttendeeServiceError(f"Unexpected error: {e}")

    def export_attendees_csv(
        self,
        event_id: UUID,
        status: Optional[str] = None
    ) -> str:
        """
        Export attendees to CSV format

        Args:
            event_id: Event UUID
            status: Optional status filter

        Returns:
            CSV string

        Raises:
            AttendeeServiceError: If export fails
        """
        try:
            # Get all attendees (no limit)
            result = self.get_attendees(
                event_id=event_id,
                status=status,
                limit=10000  # High limit for export
            )

            attendees = result["attendees"]

            # Create CSV in memory
            output = io.StringIO()

            # Define CSV fields
            fieldnames = [
                "Name",
                "Email",
                "Phone",
                "RSVP Date",
                "Status",
                "Payment Status",
                "Payment Amount",
                "Check-in Status",
                "Check-in Time",
                "Guests Count",
                "Notes"
            ]

            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()

            # Write attendee data
            for attendee in attendees:
                rsvp_date = attendee.get("created_at", "")
                if rsvp_date:
                    try:
                        rsvp_date = datetime.fromisoformat(rsvp_date.replace('Z', '+00:00'))
                        rsvp_date = rsvp_date.strftime("%Y-%m-%d %H:%M:%S")
                    except Exception:
                        pass

                check_in_time = attendee.get("checked_in_at", "")
                if check_in_time:
                    try:
                        check_in_time = datetime.fromisoformat(check_in_time.replace('Z', '+00:00'))
                        check_in_time = check_in_time.strftime("%Y-%m-%d %H:%M:%S")
                    except Exception:
                        pass

                check_in_status = "Checked In" if attendee.get("checked_in_at") else "Not Checked In"

                writer.writerow({
                    "Name": attendee.get("user_name", ""),
                    "Email": attendee.get("user_email", ""),
                    "Phone": attendee.get("user_phone", ""),
                    "RSVP Date": rsvp_date,
                    "Status": attendee.get("status", ""),
                    "Payment Status": attendee.get("payment_status", "N/A"),
                    "Payment Amount": attendee.get("payment_amount", "N/A"),
                    "Check-in Status": check_in_status,
                    "Check-in Time": check_in_time,
                    "Guests Count": attendee.get("guests_count", 0),
                    "Notes": attendee.get("notes", "")
                })

            csv_content = output.getvalue()
            output.close()

            logger.info(f"Exported {len(attendees)} attendees to CSV")

            return csv_content

        except AttendeeServiceError:
            raise
        except Exception as e:
            logger.error(f"Error exporting attendees to CSV: {e}")
            raise AttendeeServiceError(f"CSV export failed: {e}")

    def send_bulk_email(
        self,
        event_id: UUID,
        subject: str,
        message: str,
        status_filter: Optional[str] = None,
        user_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send bulk email to attendees

        Args:
            event_id: Event UUID
            subject: Email subject
            message: Email body (HTML supported)
            status_filter: Optional filter by RSVP status
            user_email: Email of user sending (for tracking)

        Returns:
            Dictionary with send results

        Raises:
            AttendeeServiceError: If sending fails
        """
        try:
            # Get attendees
            result = self.get_attendees(
                event_id=event_id,
                status=status_filter,
                limit=10000
            )

            attendees = result["attendees"]

            if not attendees:
                return {
                    "sent": 0,
                    "failed": 0,
                    "message": "No attendees found matching criteria"
                }

            sent_count = 0
            failed_count = 0
            errors = []

            # Send email to each attendee
            for attendee in attendees:
                email = attendee.get("user_email")
                name = attendee.get("user_name", "Attendee")

                if not email:
                    failed_count += 1
                    errors.append(f"No email for attendee: {name}")
                    continue

                try:
                    # Create HTML email body
                    html_body = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="UTF-8">
                        <style>
                            body {{
                                font-family: Arial, sans-serif;
                                line-height: 1.6;
                                color: #333;
                                max-width: 600px;
                                margin: 0 auto;
                                padding: 20px;
                            }}
                            .header {{
                                background-color: #8B0000;
                                color: white;
                                padding: 20px;
                                text-align: center;
                                border-radius: 5px 5px 0 0;
                            }}
                            .content {{
                                background-color: #f9f9f9;
                                padding: 30px;
                                border-radius: 0 0 5px 5px;
                            }}
                            .footer {{
                                margin-top: 30px;
                                padding-top: 20px;
                                border-top: 1px solid #ddd;
                                font-size: 12px;
                                color: #666;
                                text-align: center;
                            }}
                        </style>
                    </head>
                    <body>
                        <div class="header">
                            <h1>WWMAA Event Update</h1>
                        </div>
                        <div class="content">
                            <h2>Hello, {name}!</h2>
                            {message}
                        </div>
                        <div class="footer">
                            <p>Women's Martial Arts Association of America</p>
                            <p>This email was sent to event attendees.</p>
                        </div>
                    </body>
                    </html>
                    """

                    # Plain text version
                    text_body = f"Hello, {name}!\n\n{message}\n\n---\nWomen's Martial Arts Association of America"

                    # Send email via Postmark
                    self.email_service._send_email(
                        to_email=email,
                        subject=subject,
                        html_body=html_body,
                        text_body=text_body,
                        tag="event-bulk-email",
                        metadata={
                            "event_id": str(event_id),
                            "attendee_name": name,
                            "sent_by": user_email or "system"
                        }
                    )

                    sent_count += 1
                    logger.info(f"Sent bulk email to {email}")

                except EmailSendError as e:
                    failed_count += 1
                    errors.append(f"Failed to send to {email}: {str(e)}")
                    logger.error(f"Failed to send email to {email}: {e}")
                except Exception as e:
                    failed_count += 1
                    errors.append(f"Error sending to {email}: {str(e)}")
                    logger.error(f"Unexpected error sending to {email}: {e}")

            return {
                "sent": sent_count,
                "failed": failed_count,
                "total": len(attendees),
                "errors": errors[:10]  # Limit errors returned
            }

        except AttendeeServiceError:
            raise
        except Exception as e:
            logger.error(f"Error sending bulk email: {e}")
            raise AttendeeServiceError(f"Bulk email failed: {e}")

    def check_in_attendee(
        self,
        rsvp_id: UUID,
        checked_in_by: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Mark an attendee as checked in

        Args:
            rsvp_id: RSVP UUID
            checked_in_by: UUID of user who performed check-in

        Returns:
            Updated RSVP data

        Raises:
            AttendeeServiceError: If check-in fails
        """
        try:
            # Update RSVP with check-in timestamp
            update_data = {
                "checked_in_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

            if checked_in_by:
                update_data["checked_in_by"] = str(checked_in_by)

            result = self.db.update_document(
                collection="rsvps",
                document_id=str(rsvp_id),
                data=update_data,
                merge=True
            )

            logger.info(f"Checked in attendee {rsvp_id}")

            return result

        except ZeroDBError as e:
            logger.error(f"Database error checking in attendee: {e}")
            raise AttendeeServiceError(f"Check-in failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error checking in attendee: {e}")
            raise AttendeeServiceError(f"Unexpected error: {e}")

    def mark_no_show(
        self,
        rsvp_id: UUID,
        marked_by: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Mark an attendee as a no-show

        Args:
            rsvp_id: RSVP UUID
            marked_by: UUID of user who marked no-show

        Returns:
            Updated RSVP data

        Raises:
            AttendeeServiceError: If operation fails
        """
        try:
            # Update RSVP with no-show marker
            update_data = {
                "no_show": True,
                "no_show_marked_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

            if marked_by:
                update_data["no_show_marked_by"] = str(marked_by)

            result = self.db.update_document(
                collection="rsvps",
                document_id=str(rsvp_id),
                data=update_data,
                merge=True
            )

            logger.info(f"Marked attendee {rsvp_id} as no-show")

            return result

        except ZeroDBError as e:
            logger.error(f"Database error marking no-show: {e}")
            raise AttendeeServiceError(f"No-show marking failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error marking no-show: {e}")
            raise AttendeeServiceError(f"Unexpected error: {e}")

    def promote_from_waitlist(
        self,
        event_id: UUID,
        count: int = 1
    ) -> Dict[str, Any]:
        """
        Promote attendees from waitlist to confirmed

        Args:
            event_id: Event UUID
            count: Number of attendees to promote

        Returns:
            Dictionary with promotion results

        Raises:
            AttendeeServiceError: If promotion fails
        """
        try:
            # Get waitlist attendees (ordered by RSVP date)
            result = self.db.query_documents(
                collection="rsvps",
                filters={
                    "event_id": str(event_id),
                    "status": RSVPStatus.WAITLIST.value
                },
                limit=count,
                sort={"created_at": "asc"}  # First-come, first-served
            )

            waitlist_attendees = result.get("documents", [])

            if not waitlist_attendees:
                return {
                    "promoted": 0,
                    "message": "No attendees on waitlist"
                }

            promoted_count = 0
            promoted_attendees = []

            # Promote each attendee
            for attendee in waitlist_attendees[:count]:
                try:
                    rsvp_id = attendee.get("id")

                    # Update status to confirmed
                    self.db.update_document(
                        collection="rsvps",
                        document_id=rsvp_id,
                        data={
                            "status": RSVPStatus.CONFIRMED.value,
                            "promoted_at": datetime.utcnow().isoformat(),
                            "updated_at": datetime.utcnow().isoformat()
                        },
                        merge=True
                    )

                    promoted_count += 1
                    promoted_attendees.append({
                        "id": rsvp_id,
                        "name": attendee.get("user_name"),
                        "email": attendee.get("user_email")
                    })

                    # TODO: Send notification email to promoted attendee
                    logger.info(f"Promoted attendee {rsvp_id} from waitlist")

                except Exception as e:
                    logger.error(f"Error promoting attendee: {e}")

            return {
                "promoted": promoted_count,
                "attendees": promoted_attendees,
                "message": f"Promoted {promoted_count} attendee(s) from waitlist"
            }

        except ZeroDBError as e:
            logger.error(f"Database error promoting waitlist: {e}")
            raise AttendeeServiceError(f"Waitlist promotion failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error promoting waitlist: {e}")
            raise AttendeeServiceError(f"Unexpected error: {e}")

    def get_attendee_stats(self, event_id: UUID) -> Dict[str, Any]:
        """
        Get attendance statistics for an event

        Args:
            event_id: Event UUID

        Returns:
            Dictionary with statistics

        Raises:
            AttendeeServiceError: If query fails
        """
        try:
            # Get all attendees
            result = self.get_attendees(event_id=event_id, limit=10000)
            attendees = result["attendees"]

            # Calculate statistics
            total = len(attendees)
            confirmed = sum(1 for a in attendees if a.get("status") == RSVPStatus.CONFIRMED.value)
            waitlist = sum(1 for a in attendees if a.get("status") == RSVPStatus.WAITLIST.value)
            canceled = sum(1 for a in attendees if a.get("status") == RSVPStatus.CANCELED.value)
            checked_in = sum(1 for a in attendees if a.get("checked_in_at") is not None)
            no_show = sum(1 for a in attendees if a.get("no_show") is True)

            return {
                "total": total,
                "confirmed": confirmed,
                "waitlist": waitlist,
                "canceled": canceled,
                "checked_in": checked_in,
                "no_show": no_show,
                "pending": total - confirmed - waitlist - canceled
            }

        except AttendeeServiceError:
            raise
        except Exception as e:
            logger.error(f"Error getting attendee stats: {e}")
            raise AttendeeServiceError(f"Stats query failed: {e}")


# Global service instance (singleton pattern)
_attendee_service_instance: Optional[AttendeeService] = None


def get_attendee_service() -> AttendeeService:
    """
    Get or create the global AttendeeService instance

    Returns:
        AttendeeService instance
    """
    global _attendee_service_instance

    if _attendee_service_instance is None:
        _attendee_service_instance = AttendeeService()

    return _attendee_service_instance
