"""
Event Service for WWMAA Backend

Provides business logic for event management including:
- Event CRUD operations
- Soft delete with archive functionality
- Duplicate event creation
- Publish/unpublish toggle
- Image upload to ZeroDB Object Storage
- Event filtering and search
- Validation of event data
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from backend.services.zerodb_service import (
    get_zerodb_client,
    ZeroDBError,
    ZeroDBNotFoundError,
    ZeroDBValidationError
)
from backend.models.schemas import Event, EventStatus, EventType, EventVisibility

# Configure logging
logger = logging.getLogger(__name__)


class EventService:
    """
    Event Management Service

    Handles all business logic for event operations including:
    - Creating, reading, updating, and deleting events
    - Soft delete functionality
    - Event duplication
    - Publishing/unpublishing events
    - Image management with ZeroDB Object Storage
    """

    def __init__(self):
        """Initialize Event Service with ZeroDB client"""
        self.db = get_zerodb_client()
        self.collection = "events"

    def create_event(
        self,
        event_data: Dict[str, Any],
        created_by: UUID
    ) -> Dict[str, Any]:
        """
        Create a new event

        Args:
            event_data: Event data dictionary
            created_by: UUID of the user creating the event

        Returns:
            Created event with ID and metadata

        Raises:
            ZeroDBValidationError: If event data is invalid
            ZeroDBError: If creation fails
        """
        try:
            # Add audit fields
            event_data["created_by"] = str(created_by)
            event_data["organizer_id"] = str(created_by)
            event_data["status"] = event_data.get("status", EventStatus.DRAFT.value)
            event_data["is_deleted"] = False
            event_data["is_published"] = False
            event_data["current_attendees"] = 0

            # Validate dates
            start_date = event_data.get("start_date")
            end_date = event_data.get("end_date")

            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

            if end_date and start_date and end_date <= start_date:
                raise ZeroDBValidationError("end_date must be after start_date")

            # Validate capacity
            capacity = event_data.get("capacity")
            if capacity is not None and capacity <= 0:
                raise ZeroDBValidationError("capacity must be greater than 0")

            # Validate price
            price = event_data.get("price")
            if price is not None and price < 0:
                raise ZeroDBValidationError("price must be 0 or greater")

            # Create event in ZeroDB
            logger.info(f"Creating event: {event_data.get('title')}")
            result = self.db.create_document(
                collection=self.collection,
                data=event_data
            )

            logger.info(f"Event created successfully with ID: {result.get('id')}")
            return result

        except ZeroDBValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to create event: {e}")
            raise ZeroDBError(f"Failed to create event: {e}")

    def get_event(
        self,
        event_id: str,
        include_deleted: bool = False
    ) -> Dict[str, Any]:
        """
        Get an event by ID

        Args:
            event_id: Event ID
            include_deleted: Whether to include soft-deleted events

        Returns:
            Event data

        Raises:
            ZeroDBNotFoundError: If event doesn't exist
            ZeroDBError: If retrieval fails
        """
        try:
            logger.info(f"Fetching event: {event_id}")
            event = self.db.get_document(
                collection=self.collection,
                document_id=event_id
            )

            # Check if deleted
            if event.get("is_deleted") and not include_deleted:
                raise ZeroDBNotFoundError(f"Event not found: {event_id}")

            return event

        except ZeroDBNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to fetch event: {e}")
            raise ZeroDBError(f"Failed to fetch event: {e}")

    def list_events(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 20,
        offset: int = 0,
        include_deleted: bool = False,
        sort_by: str = "start_date",
        sort_order: str = "asc"
    ) -> Dict[str, Any]:
        """
        List events with filtering and pagination

        Args:
            filters: Filter criteria (e.g., {"event_type": "seminar", "visibility": "public"})
            limit: Maximum number of events to return
            offset: Number of events to skip
            include_deleted: Whether to include soft-deleted events
            sort_by: Field to sort by (default: start_date)
            sort_order: Sort order (asc or desc)

        Returns:
            Dictionary with events list and metadata

        Raises:
            ZeroDBError: If query fails
        """
        try:
            # Build filter criteria
            query_filters = filters or {}

            # Exclude deleted events by default
            if not include_deleted:
                query_filters["is_deleted"] = False

            # Build sort criteria
            sort_criteria = {sort_by: sort_order}

            logger.info(f"Listing events with filters: {query_filters}")
            result = self.db.query_documents(
                collection=self.collection,
                filters=query_filters,
                limit=limit,
                offset=offset,
                sort=sort_criteria
            )

            return result

        except Exception as e:
            logger.error(f"Failed to list events: {e}")
            raise ZeroDBError(f"Failed to list events: {e}")

    def update_event(
        self,
        event_id: str,
        event_data: Dict[str, Any],
        updated_by: UUID
    ) -> Dict[str, Any]:
        """
        Update an existing event

        Args:
            event_id: Event ID
            event_data: Updated event data
            updated_by: UUID of the user updating the event

        Returns:
            Updated event data

        Raises:
            ZeroDBNotFoundError: If event doesn't exist
            ZeroDBValidationError: If data is invalid
            ZeroDBError: If update fails
        """
        try:
            # Check if event exists and is not deleted
            existing_event = self.get_event(event_id)

            # Add audit fields
            event_data["updated_by"] = str(updated_by)
            event_data["updated_at"] = datetime.utcnow().isoformat()

            # Validate dates if provided
            start_date = event_data.get("start_date", existing_event.get("start_date"))
            end_date = event_data.get("end_date", existing_event.get("end_date"))

            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

            if end_date and start_date and end_date <= start_date:
                raise ZeroDBValidationError("end_date must be after start_date")

            # Validate capacity if provided
            capacity = event_data.get("capacity", existing_event.get("capacity"))
            if capacity is not None and capacity <= 0:
                raise ZeroDBValidationError("capacity must be greater than 0")

            # Validate price if provided
            price = event_data.get("price", existing_event.get("price"))
            if price is not None and price < 0:
                raise ZeroDBValidationError("price must be 0 or greater")

            # Update event in ZeroDB
            logger.info(f"Updating event: {event_id}")
            result = self.db.update_document(
                collection=self.collection,
                document_id=event_id,
                data=event_data,
                merge=True
            )

            logger.info(f"Event updated successfully: {event_id}")
            return result

        except (ZeroDBNotFoundError, ZeroDBValidationError):
            raise
        except Exception as e:
            logger.error(f"Failed to update event: {e}")
            raise ZeroDBError(f"Failed to update event: {e}")

    def delete_event(
        self,
        event_id: str,
        deleted_by: UUID,
        hard_delete: bool = False
    ) -> Dict[str, Any]:
        """
        Delete an event (soft delete by default)

        Args:
            event_id: Event ID
            deleted_by: UUID of the user deleting the event
            hard_delete: If True, permanently delete; if False, soft delete

        Returns:
            Deletion confirmation

        Raises:
            ZeroDBNotFoundError: If event doesn't exist
            ZeroDBError: If deletion fails
        """
        try:
            # Check if event exists
            event = self.get_event(event_id)

            if hard_delete:
                # Permanent deletion
                logger.info(f"Hard deleting event: {event_id}")
                result = self.db.delete_document(
                    collection=self.collection,
                    document_id=event_id
                )
            else:
                # Soft delete
                logger.info(f"Soft deleting event: {event_id}")
                result = self.db.update_document(
                    collection=self.collection,
                    document_id=event_id,
                    data={
                        "is_deleted": True,
                        "deleted_at": datetime.utcnow().isoformat(),
                        "deleted_by": str(deleted_by),
                        "status": EventStatus.DELETED.value,
                        "is_published": False
                    },
                    merge=True
                )

            logger.info(f"Event deleted successfully: {event_id}")
            return result

        except ZeroDBNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to delete event: {e}")
            raise ZeroDBError(f"Failed to delete event: {e}")

    def restore_event(
        self,
        event_id: str,
        restored_by: UUID
    ) -> Dict[str, Any]:
        """
        Restore a soft-deleted event

        Args:
            event_id: Event ID
            restored_by: UUID of the user restoring the event

        Returns:
            Restored event data

        Raises:
            ZeroDBNotFoundError: If event doesn't exist
            ZeroDBError: If restoration fails
        """
        try:
            # Check if event exists (including deleted)
            event = self.get_event(event_id, include_deleted=True)

            if not event.get("is_deleted"):
                raise ZeroDBValidationError("Event is not deleted")

            logger.info(f"Restoring event: {event_id}")
            result = self.db.update_document(
                collection=self.collection,
                document_id=event_id,
                data={
                    "is_deleted": False,
                    "deleted_at": None,
                    "deleted_by": None,
                    "status": EventStatus.DRAFT.value,
                    "updated_by": str(restored_by),
                    "updated_at": datetime.utcnow().isoformat()
                },
                merge=True
            )

            logger.info(f"Event restored successfully: {event_id}")
            return result

        except (ZeroDBNotFoundError, ZeroDBValidationError):
            raise
        except Exception as e:
            logger.error(f"Failed to restore event: {e}")
            raise ZeroDBError(f"Failed to restore event: {e}")

    def duplicate_event(
        self,
        event_id: str,
        created_by: UUID,
        title_suffix: str = " (Copy)"
    ) -> Dict[str, Any]:
        """
        Duplicate an existing event

        Args:
            event_id: Event ID to duplicate
            created_by: UUID of the user creating the duplicate
            title_suffix: Suffix to add to the title (default: " (Copy)")

        Returns:
            Duplicated event data

        Raises:
            ZeroDBNotFoundError: If event doesn't exist
            ZeroDBError: If duplication fails
        """
        try:
            # Get the original event
            original_event = self.get_event(event_id)

            # Create a copy of the event data
            event_data = original_event.copy()

            # Remove fields that shouldn't be copied
            fields_to_remove = [
                "id", "created_at", "updated_at", "created_by", "updated_by",
                "is_deleted", "deleted_at", "deleted_by",
                "is_published", "published_at",
                "current_attendees"
            ]

            for field in fields_to_remove:
                event_data.pop(field, None)

            # Update title
            event_data["title"] = original_event["title"] + title_suffix

            # Reset status to draft
            event_data["status"] = EventStatus.DRAFT.value

            # Create the duplicate event
            logger.info(f"Duplicating event: {event_id}")
            result = self.create_event(event_data, created_by)

            logger.info(f"Event duplicated successfully: {event_id} -> {result.get('id')}")
            return result

        except ZeroDBNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to duplicate event: {e}")
            raise ZeroDBError(f"Failed to duplicate event: {e}")

    def toggle_publish(
        self,
        event_id: str,
        updated_by: UUID
    ) -> Dict[str, Any]:
        """
        Toggle event publish status

        Args:
            event_id: Event ID
            updated_by: UUID of the user toggling publish status

        Returns:
            Updated event data with new publish status

        Raises:
            ZeroDBNotFoundError: If event doesn't exist
            ZeroDBError: If toggle fails
        """
        try:
            # Get the event
            event = self.get_event(event_id)

            # Toggle publish status
            new_publish_status = not event.get("is_published", False)

            update_data = {
                "is_published": new_publish_status,
                "updated_by": str(updated_by),
                "updated_at": datetime.utcnow().isoformat()
            }

            # Update status and published_at timestamp
            if new_publish_status:
                update_data["status"] = EventStatus.PUBLISHED.value
                update_data["published_at"] = datetime.utcnow().isoformat()
            else:
                update_data["status"] = EventStatus.DRAFT.value
                update_data["published_at"] = None

            logger.info(f"Toggling publish status for event: {event_id} to {new_publish_status}")
            result = self.db.update_document(
                collection=self.collection,
                document_id=event_id,
                data=update_data,
                merge=True
            )

            logger.info(f"Event publish status toggled successfully: {event_id}")
            return result

        except ZeroDBNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to toggle publish status: {e}")
            raise ZeroDBError(f"Failed to toggle publish status: {e}")

    def upload_event_image(
        self,
        file_path: str,
        event_id: Optional[str] = None,
        object_name: Optional[str] = None
    ) -> str:
        """
        Upload an event image to ZeroDB Object Storage

        Args:
            file_path: Path to the image file
            event_id: Optional event ID for organizing images
            object_name: Optional custom object name

        Returns:
            URL of the uploaded image

        Raises:
            FileNotFoundError: If file doesn't exist
            ZeroDBError: If upload fails
        """
        try:
            # Generate object name if not provided
            if not object_name:
                import os
                filename = os.path.basename(file_path)
                if event_id:
                    object_name = f"events/{event_id}/{filename}"
                else:
                    object_name = f"events/{uuid4()}/{filename}"

            logger.info(f"Uploading event image: {object_name}")
            result = self.db.upload_object(
                file_path=file_path,
                object_name=object_name,
                metadata={"type": "event_image", "event_id": event_id or ""}
            )

            # Get the URL from the result
            image_url = result.get("url") or result.get("object_url")

            logger.info(f"Event image uploaded successfully: {image_url}")
            return image_url

        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to upload event image: {e}")
            raise ZeroDBError(f"Failed to upload event image: {e}")

    def get_deleted_events(
        self,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "deleted_at",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """
        Get list of soft-deleted events (archive)

        Args:
            limit: Maximum number of events to return
            offset: Number of events to skip
            sort_by: Field to sort by (default: deleted_at)
            sort_order: Sort order (asc or desc)

        Returns:
            Dictionary with deleted events list and metadata

        Raises:
            ZeroDBError: If query fails
        """
        try:
            logger.info("Fetching deleted events")
            result = self.list_events(
                filters={"is_deleted": True},
                limit=limit,
                offset=offset,
                include_deleted=True,
                sort_by=sort_by,
                sort_order=sort_order
            )

            return result

        except Exception as e:
            logger.error(f"Failed to fetch deleted events: {e}")
            raise ZeroDBError(f"Failed to fetch deleted events: {e}")


# Global service instance (singleton pattern)
_service_instance: Optional[EventService] = None


def get_event_service() -> EventService:
    """
    Get or create the global Event Service instance

    Returns:
        EventService instance
    """
    global _service_instance

    if _service_instance is None:
        _service_instance = EventService()

    return _service_instance
