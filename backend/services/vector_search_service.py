"""
Vector Search Service for WWMAA Backend

Implements vector similarity search capabilities using ZeroDB's vector search API.
Supports semantic search across martial arts content including events, articles,
profiles, and other resources.

Features:
- Vector similarity search with configurable top_k
- Filtering by content type, date, or custom filters
- Metadata enrichment for search results
- Performance optimization with caching
- Comprehensive error handling

Dependencies:
- ZeroDB service for vector database operations
- US-035 implementation
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from backend.services.zerodb_service import get_zerodb_client, ZeroDBError

# Configure logging
logger = logging.getLogger(__name__)


class VectorSearchError(Exception):
    """Base exception for vector search operations"""
    pass


class VectorSearchService:
    """
    Service for performing vector similarity searches in ZeroDB.

    Provides methods for semantic search across martial arts content
    with support for filtering, ranking, and metadata enrichment.
    """

    def __init__(self):
        """Initialize vector search service with ZeroDB client"""
        self.db_client = get_zerodb_client()
        logger.info("VectorSearchService initialized")

    def search(
        self,
        collection: str,
        query_vector: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search in a ZeroDB collection.

        Args:
            collection: Name of the collection to search
            query_vector: Query embedding vector (e.g., from OpenAI)
            top_k: Number of top results to return (default: 10)
            filters: Optional filters to apply (e.g., {"source_type": "event"})
            include_metadata: Include document metadata in results

        Returns:
            List of search results with documents and similarity scores
            Each result contains:
            - id: Document ID
            - data: Document data
            - score: Similarity score (0-1, higher is more similar)
            - metadata: Document metadata (if include_metadata=True)

        Raises:
            VectorSearchError: If search fails
        """
        try:
            logger.info(
                f"Performing vector search in collection '{collection}' "
                f"with top_k={top_k}, filters={filters}"
            )

            # Validate query vector
            if not query_vector or not isinstance(query_vector, list):
                raise VectorSearchError("Invalid query vector: must be a non-empty list")

            if not all(isinstance(v, (int, float)) for v in query_vector):
                raise VectorSearchError("Invalid query vector: all elements must be numbers")

            # Perform vector search using ZeroDB
            result = self.db_client.vector_search(
                collection=collection,
                query_vector=query_vector,
                top_k=top_k,
                filters=filters,
                include_metadata=include_metadata
            )

            # Extract results from response
            search_results = result.get("results", [])

            logger.info(
                f"Vector search completed: found {len(search_results)} results "
                f"in collection '{collection}'"
            )

            return search_results

        except ZeroDBError as e:
            logger.error(f"ZeroDB error during vector search: {e}")
            raise VectorSearchError(f"Vector search failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during vector search: {e}")
            raise VectorSearchError(f"Vector search failed: {e}")

    def search_martial_arts_content(
        self,
        query_vector: List[float],
        top_k: int = 10,
        content_types: Optional[List[str]] = None,
        date_range: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search martial arts content across multiple collections.

        This is a convenience method for searching across events, articles,
        profiles, and other martial arts resources.

        Args:
            query_vector: Query embedding vector
            top_k: Number of top results to return per collection
            content_types: List of content types to search (e.g., ["event", "article"])
                          If None, searches all types
            date_range: Optional date range filter (e.g., {"start": "2024-01-01", "end": "2024-12-31"})

        Returns:
            Aggregated list of search results from all collections,
            sorted by similarity score

        Raises:
            VectorSearchError: If search fails
        """
        try:
            # Define searchable collections
            collections_map = {
                "event": "events",
                "article": "articles",
                "profile": "profiles",
                "technique": "techniques"
            }

            # Determine which collections to search
            if content_types:
                collections = [
                    collections_map[ct]
                    for ct in content_types
                    if ct in collections_map
                ]
            else:
                collections = list(collections_map.values())

            # Build filters
            filters = {}
            if date_range:
                filters["date"] = {
                    "$gte": date_range.get("start"),
                    "$lte": date_range.get("end")
                }

            # Search across all collections
            all_results = []
            for collection in collections:
                try:
                    results = self.search(
                        collection=collection,
                        query_vector=query_vector,
                        top_k=top_k,
                        filters=filters if filters else None,
                        include_metadata=True
                    )

                    # Add source collection to each result
                    for result in results:
                        result["source_collection"] = collection

                    all_results.extend(results)

                except VectorSearchError as e:
                    # Log error but continue searching other collections
                    logger.warning(
                        f"Failed to search collection '{collection}': {e}"
                    )
                    continue

            # Sort all results by similarity score (descending)
            all_results.sort(key=lambda x: x.get("score", 0), reverse=True)

            # Return top_k results overall
            final_results = all_results[:top_k]

            logger.info(
                f"Multi-collection search completed: "
                f"found {len(final_results)} results across {len(collections)} collections"
            )

            return final_results

        except Exception as e:
            logger.error(f"Error during multi-collection search: {e}")
            raise VectorSearchError(f"Multi-collection search failed: {e}")

    def enrich_search_results(
        self,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Enrich search results with additional metadata and formatting.

        Args:
            results: List of raw search results from vector search

        Returns:
            Enriched results with formatted data for frontend display
        """
        enriched_results = []

        for result in results:
            try:
                enriched = {
                    "id": result.get("id"),
                    "title": self._extract_title(result),
                    "url": self._generate_url(result),
                    "source_type": result.get("source_collection", "unknown"),
                    "similarity_score": result.get("score", 0),
                    "snippet": self._extract_snippet(result),
                    "metadata": result.get("metadata", {})
                }

                enriched_results.append(enriched)

            except Exception as e:
                logger.warning(f"Failed to enrich result {result.get('id')}: {e}")
                continue

        return enriched_results

    def _extract_title(self, result: Dict[str, Any]) -> str:
        """Extract title from search result data"""
        data = result.get("data", {})
        return (
            data.get("title") or
            data.get("name") or
            data.get("event_name") or
            "Untitled"
        )

    def _generate_url(self, result: Dict[str, Any]) -> str:
        """Generate URL for search result based on source type"""
        source = result.get("source_collection", "")
        doc_id = result.get("id", "")

        url_map = {
            "events": f"/events/{doc_id}",
            "articles": f"/articles/{doc_id}",
            "profiles": f"/members/{doc_id}",
            "techniques": f"/techniques/{doc_id}"
        }

        return url_map.get(source, f"/{source}/{doc_id}")

    def _extract_snippet(self, result: Dict[str, Any]) -> str:
        """Extract text snippet from search result for preview"""
        data = result.get("data", {})

        # Try to get description or content
        snippet = (
            data.get("description") or
            data.get("content") or
            data.get("summary") or
            ""
        )

        # Truncate to 200 characters
        if len(snippet) > 200:
            snippet = snippet[:197] + "..."

        return snippet


# Global service instance (singleton pattern)
_service_instance: Optional[VectorSearchService] = None


def get_vector_search_service() -> VectorSearchService:
    """
    Get or create the global VectorSearchService instance.

    Returns:
        VectorSearchService instance
    """
    global _service_instance

    if _service_instance is None:
        _service_instance = VectorSearchService()

    return _service_instance
