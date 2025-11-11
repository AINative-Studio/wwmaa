"""
Instrumented ZeroDB Client with Performance Metrics

Wraps the base ZeroDB client with automatic performance tracking,
slow query logging, and Prometheus metrics.
"""

import time
from typing import Any, Dict, List, Optional

from backend.services.zerodb_service import ZeroDBClient
from backend.observability.metrics import track_zerodb_query
from backend.observability.slow_query_logger import log_slow_query


class InstrumentedZeroDBClient(ZeroDBClient):
    """
    ZeroDB client with automatic performance monitoring.

    Extends the base ZeroDBClient to add:
    - Prometheus metrics for all operations
    - Slow query logging
    - Automatic error tracking
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 10,
        max_retries: int = 3,
        pool_connections: int = 10,
        pool_maxsize: int = 10,
        slow_query_threshold: float = 1.0,
    ):
        """
        Initialize instrumented ZeroDB client.

        Args:
            api_key: ZeroDB API key
            base_url: ZeroDB API base URL
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            pool_connections: Number of connection pool connections
            pool_maxsize: Maximum size of connection pool
            slow_query_threshold: Threshold for slow query logging in seconds
        """
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize,
        )
        self.slow_query_threshold = slow_query_threshold

    def create_document(
        self,
        collection: str,
        data: Dict[str, Any],
        document_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create document with performance tracking."""
        with track_zerodb_query(collection, "create", self.slow_query_threshold):
            start_time = time.time()
            try:
                result = super().create_document(collection, data, document_id)
                duration = time.time() - start_time

                # Log slow queries
                if duration > self.slow_query_threshold:
                    log_slow_query(
                        collection=collection,
                        operation="create",
                        duration=duration,
                        query_details={"document_id": document_id},
                    )

                return result
            except Exception as e:
                duration = time.time() - start_time
                log_slow_query(
                    collection=collection,
                    operation="create",
                    duration=duration,
                    error=str(e),
                )
                raise

    def get_document(self, collection: str, document_id: str) -> Dict[str, Any]:
        """Get document with performance tracking."""
        with track_zerodb_query(collection, "get", self.slow_query_threshold):
            start_time = time.time()
            try:
                result = super().get_document(collection, document_id)
                duration = time.time() - start_time

                if duration > self.slow_query_threshold:
                    log_slow_query(
                        collection=collection,
                        operation="get",
                        duration=duration,
                        query_details={"document_id": document_id},
                    )

                return result
            except Exception as e:
                duration = time.time() - start_time
                log_slow_query(
                    collection=collection,
                    operation="get",
                    duration=duration,
                    query_details={"document_id": document_id},
                    error=str(e),
                )
                raise

    def query_documents(
        self,
        collection: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        offset: int = 0,
        sort: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Query documents with performance tracking."""
        with track_zerodb_query(collection, "query", self.slow_query_threshold):
            start_time = time.time()
            try:
                result = super().query_documents(collection, filters, limit, offset, sort)
                duration = time.time() - start_time

                result_count = len(result.get("documents", []))

                if duration > self.slow_query_threshold:
                    log_slow_query(
                        collection=collection,
                        operation="query",
                        duration=duration,
                        query_details={
                            "filters": filters,
                            "limit": limit,
                            "offset": offset,
                            "sort": sort,
                        },
                        result_count=result_count,
                    )

                return result
            except Exception as e:
                duration = time.time() - start_time
                log_slow_query(
                    collection=collection,
                    operation="query",
                    duration=duration,
                    query_details={"filters": filters, "limit": limit},
                    error=str(e),
                )
                raise

    def update_document(
        self,
        collection: str,
        document_id: str,
        data: Dict[str, Any],
        merge: bool = True,
    ) -> Dict[str, Any]:
        """Update document with performance tracking."""
        with track_zerodb_query(collection, "update", self.slow_query_threshold):
            start_time = time.time()
            try:
                result = super().update_document(collection, document_id, data, merge)
                duration = time.time() - start_time

                if duration > self.slow_query_threshold:
                    log_slow_query(
                        collection=collection,
                        operation="update",
                        duration=duration,
                        query_details={"document_id": document_id, "merge": merge},
                    )

                return result
            except Exception as e:
                duration = time.time() - start_time
                log_slow_query(
                    collection=collection,
                    operation="update",
                    duration=duration,
                    query_details={"document_id": document_id},
                    error=str(e),
                )
                raise

    def delete_document(self, collection: str, document_id: str) -> Dict[str, Any]:
        """Delete document with performance tracking."""
        with track_zerodb_query(collection, "delete", self.slow_query_threshold):
            start_time = time.time()
            try:
                result = super().delete_document(collection, document_id)
                duration = time.time() - start_time

                if duration > self.slow_query_threshold:
                    log_slow_query(
                        collection=collection,
                        operation="delete",
                        duration=duration,
                        query_details={"document_id": document_id},
                    )

                return result
            except Exception as e:
                duration = time.time() - start_time
                log_slow_query(
                    collection=collection,
                    operation="delete",
                    duration=duration,
                    query_details={"document_id": document_id},
                    error=str(e),
                )
                raise

    def vector_search(
        self,
        collection: str,
        query_vector: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True,
        min_score: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Vector search with performance tracking."""
        with track_zerodb_query(collection, "vector_search", self.slow_query_threshold):
            start_time = time.time()
            try:
                result = super().vector_search(
                    collection, query_vector, top_k, filters, include_metadata, min_score
                )
                duration = time.time() - start_time

                result_count = len(result.get("results", []))

                if duration > self.slow_query_threshold:
                    log_slow_query(
                        collection=collection,
                        operation="vector_search",
                        duration=duration,
                        query_details={
                            "top_k": top_k,
                            "vector_dimension": len(query_vector),
                            "filters": filters,
                            "min_score": min_score,
                        },
                        result_count=result_count,
                    )

                return result
            except Exception as e:
                duration = time.time() - start_time
                log_slow_query(
                    collection=collection,
                    operation="vector_search",
                    duration=duration,
                    query_details={"top_k": top_k, "vector_dimension": len(query_vector)},
                    error=str(e),
                )
                raise

    def batch_insert_vectors(
        self, collection: str, vectors: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Batch insert vectors with performance tracking."""
        with track_zerodb_query(collection, "batch_insert", self.slow_query_threshold):
            start_time = time.time()
            try:
                result = super().batch_insert_vectors(collection, vectors)
                duration = time.time() - start_time

                result_count = len(result.get("inserted_ids", []))

                if duration > self.slow_query_threshold:
                    log_slow_query(
                        collection=collection,
                        operation="batch_insert",
                        duration=duration,
                        query_details={"batch_size": len(vectors)},
                        result_count=result_count,
                    )

                return result
            except Exception as e:
                duration = time.time() - start_time
                log_slow_query(
                    collection=collection,
                    operation="batch_insert",
                    duration=duration,
                    query_details={"batch_size": len(vectors)},
                    error=str(e),
                )
                raise


# Global instrumented client instance
_instrumented_client: Optional[InstrumentedZeroDBClient] = None


def get_instrumented_zerodb_client() -> InstrumentedZeroDBClient:
    """
    Get or create the global instrumented ZeroDB client instance.

    Returns:
        InstrumentedZeroDBClient instance with metrics enabled
    """
    global _instrumented_client

    if _instrumented_client is None:
        _instrumented_client = InstrumentedZeroDBClient()

    return _instrumented_client
