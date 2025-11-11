"""
Search Service - US-040: Search Feedback System

This service handles search query logging, feedback submission, and analytics.
Provides privacy-focused feedback collection with IP hashing and admin review flagging.

Key Features:
- Log search queries with metadata
- Submit anonymous feedback (thumbs up/down + text)
- SHA256 IP hashing for privacy
- Automatic flagging of negative feedback
- Sentiment statistics and analytics
"""

import hashlib
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from backend.models.schemas import SearchQuery
from backend.services.zerodb_service import ZeroDBClient
from backend.config import get_settings

settings = get_settings()


class SearchService:
    """Service for search query logging and feedback management"""

    def __init__(self, zerodb_client: ZeroDBClient):
        """
        Initialize search service

        Args:
            zerodb_client: ZeroDB client instance for database operations
        """
        self.db = zerodb_client
        self.collection = "search_queries"
        # Salt for IP hashing - stored in environment for consistency
        self.ip_salt = settings.IP_HASH_SALT if hasattr(settings, 'IP_HASH_SALT') else "wwmaa-search-salt-2024"

    def hash_ip_address(self, ip_address: str) -> str:
        """
        Hash IP address with SHA256 for privacy

        Uses salt to prevent rainbow table attacks while maintaining
        ability to detect duplicate feedback from same IP.

        Args:
            ip_address: IP address to hash

        Returns:
            SHA256 hash of IP + salt (64 character hex string)
        """
        if not ip_address:
            return ""

        # Combine IP with salt and hash
        combined = f"{ip_address}{self.ip_salt}"
        return hashlib.sha256(combined.encode()).hexdigest()

    async def log_query(
        self,
        query_text: str,
        user_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        results_count: int = 0,
        response_time_ms: Optional[int] = None,
        intent: Optional[str] = None
    ) -> UUID:
        """
        Log a search query to the database

        Args:
            query_text: The search query string
            user_id: User ID if authenticated (None for anonymous)
            ip_address: User's IP address (will be hashed)
            user_agent: User agent string
            session_id: Session identifier
            results_count: Number of results returned
            response_time_ms: Query response time in milliseconds
            intent: Detected search intent (optional AI classification)

        Returns:
            UUID of created search query document
        """
        # Hash IP for privacy
        ip_hash = self.hash_ip_address(ip_address) if ip_address else None

        query_data = {
            "query_text": query_text,
            "user_id": user_id,
            "ip_hash": ip_hash,
            "user_agent": user_agent,
            "session_id": session_id,
            "results_count": results_count,
            "response_time_ms": response_time_ms,
            "intent": intent,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        # Create query document
        query = SearchQuery(**query_data)
        result = await self.db.create_document(self.collection, query.model_dump())

        return result["id"]

    async def submit_feedback(
        self,
        query_id: UUID,
        rating: str,
        feedback_text: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Submit feedback for a search query

        Validates the query exists, rating is valid, and updates the query
        document with feedback. Automatically flags negative feedback for review.

        Args:
            query_id: UUID of the search query
            rating: "positive" or "negative"
            feedback_text: Optional text feedback (max 2000 chars)
            ip_address: User's IP address (will be hashed for privacy)

        Returns:
            Updated query document

        Raises:
            ValueError: If query not found or rating invalid
        """
        # Validate rating
        if rating not in ["positive", "negative"]:
            raise ValueError("Rating must be 'positive' or 'negative'")

        # Check if query exists
        query = await self.db.get_document(self.collection, str(query_id))
        if not query:
            raise ValueError(f"Search query {query_id} not found")

        # Check if feedback already submitted
        if query.get("feedback_rating"):
            raise ValueError("Feedback already submitted for this query")

        # Hash IP for privacy
        ip_hash = self.hash_ip_address(ip_address) if ip_address else None

        # Prepare feedback update
        feedback_update = {
            "feedback_rating": rating,
            "feedback_text": feedback_text,
            "feedback_timestamp": datetime.utcnow(),
            "flagged_for_review": rating == "negative",  # Auto-flag negative feedback
            "updated_at": datetime.utcnow(),
        }

        # Update IP hash if not already set
        if ip_hash and not query.get("ip_hash"):
            feedback_update["ip_hash"] = ip_hash

        # Update query document
        updated_query = await self.db.update_document(
            self.collection,
            str(query_id),
            feedback_update
        )

        return updated_query

    async def get_feedback_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Calculate feedback statistics for analytics

        Args:
            start_date: Start date for statistics (optional)
            end_date: End date for statistics (optional)

        Returns:
            Dictionary with feedback statistics:
            - total_queries: Total search queries
            - queries_with_feedback: Queries that received feedback
            - positive_count: Number of positive ratings
            - negative_count: Number of negative ratings
            - feedback_rate: Percentage of queries with feedback
            - satisfaction_rate: Percentage of positive feedback
            - flagged_count: Number of flagged queries
            - with_text_count: Feedback with text comments
        """
        # Build query filters
        filters = {}
        if start_date:
            filters["created_at"] = {"$gte": start_date}
        if end_date:
            if "created_at" in filters:
                filters["created_at"]["$lte"] = end_date
            else:
                filters["created_at"] = {"$lte": end_date}

        # Get all queries in range
        all_queries = await self.db.query_documents(self.collection, filters)

        # Calculate statistics
        total_queries = len(all_queries)
        queries_with_feedback = [q for q in all_queries if q.get("feedback_rating")]
        positive_count = sum(1 for q in queries_with_feedback if q.get("feedback_rating") == "positive")
        negative_count = sum(1 for q in queries_with_feedback if q.get("feedback_rating") == "negative")
        flagged_count = sum(1 for q in all_queries if q.get("flagged_for_review"))
        with_text_count = sum(1 for q in queries_with_feedback if q.get("feedback_text"))

        feedback_count = len(queries_with_feedback)
        feedback_rate = (feedback_count / total_queries * 100) if total_queries > 0 else 0
        satisfaction_rate = (positive_count / feedback_count * 100) if feedback_count > 0 else 0

        return {
            "total_queries": total_queries,
            "queries_with_feedback": feedback_count,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "feedback_rate": round(feedback_rate, 2),
            "satisfaction_rate": round(satisfaction_rate, 2),
            "flagged_count": flagged_count,
            "with_text_count": with_text_count,
            "period": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
            }
        }

    async def get_flagged_feedback(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get queries flagged for review (negative feedback)

        Args:
            limit: Maximum number of results (default 50)
            offset: Number of results to skip (default 0)

        Returns:
            List of flagged query documents
        """
        filters = {"flagged_for_review": True}

        # Query with pagination
        flagged_queries = await self.db.query_documents(
            self.collection,
            filters,
            limit=limit,
            offset=offset,
            sort=[("feedback_timestamp", -1)]  # Most recent first
        )

        return flagged_queries

    async def get_all_feedback(
        self,
        rating: Optional[str] = None,
        has_text: Optional[bool] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get all feedback with optional filters

        Args:
            rating: Filter by rating ("positive" or "negative")
            has_text: Filter for feedback with text comments
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of results (default 50)
            offset: Number of results to skip (default 0)

        Returns:
            Dictionary with:
            - items: List of query documents with feedback
            - total: Total count of matching queries
            - limit: Applied limit
            - offset: Applied offset
        """
        # Build filters
        filters = {"feedback_rating": {"$ne": None}}  # Has feedback

        if rating:
            filters["feedback_rating"] = rating

        if has_text is not None:
            if has_text:
                filters["feedback_text"] = {"$ne": None}
            else:
                filters["feedback_text"] = None

        if start_date:
            filters["feedback_timestamp"] = {"$gte": start_date}
        if end_date:
            if "feedback_timestamp" in filters:
                filters["feedback_timestamp"]["$lte"] = end_date
            else:
                filters["feedback_timestamp"] = {"$lte": end_date}

        # Get total count
        all_matching = await self.db.query_documents(self.collection, filters)
        total = len(all_matching)

        # Get paginated results
        feedback_queries = await self.db.query_documents(
            self.collection,
            filters,
            limit=limit,
            offset=offset,
            sort=[("feedback_timestamp", -1)]  # Most recent first
        )

        return {
            "items": feedback_queries,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(feedback_queries) < total
        }

    async def unflag_feedback(self, query_id: UUID) -> Dict[str, Any]:
        """
        Remove review flag from a query (mark as reviewed)

        Args:
            query_id: UUID of the search query

        Returns:
            Updated query document
        """
        updated = await self.db.update_document(
            self.collection,
            str(query_id),
            {
                "flagged_for_review": False,
                "updated_at": datetime.utcnow()
            }
        )

        return updated
