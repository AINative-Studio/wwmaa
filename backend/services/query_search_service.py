"""
Query Search Service for WWMAA Backend

Implements comprehensive search functionality with 11-step query processing pipeline:
1. Normalize query (lowercase, trim)
2. Check rate limit (IP-based)
3. Check cache (5-minute TTL in Redis)
4. Generate query embedding (OpenAI)
5. ZeroDB vector search (top 10 results)
6. Send context to AI Registry
7. Get LLM answer
8. Attach relevant media (videos from Cloudflare Stream, images from ZeroDB Object Storage)
9. Cache result in Redis
10. Log query in ZeroDB
11. Return formatted response

Features:
- Full RAG (Retrieval Augmented Generation) pipeline
- Aggressive caching to reduce costs
- Media attachment from multiple sources
- Query logging for analytics
- Comprehensive error handling
- Performance monitoring

Dependencies:
- US-035: Vector Search Service
- US-036: Embedding Service
- US-037: AI Registry Service
- US-038: Search Query Endpoint (this implementation)
"""

import logging
import hashlib
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

import redis
from backend.config import get_settings
from backend.services.embedding_service import get_embedding_service, EmbeddingError
from backend.services.vector_search_service import get_vector_search_service, VectorSearchError
from backend.services.ai_registry_service import get_ai_registry_service, AIRegistryError
from backend.services.zerodb_service import get_zerodb_client, ZeroDBError

# Configure logging
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()


class QuerySearchError(Exception):
    """Base exception for query search operations"""
    pass


class QuerySearchService:
    """
    Main query search service implementing the full query processing pipeline.

    Orchestrates:
    - Query normalization and validation
    - Embedding generation
    - Vector search
    - LLM answer generation
    - Media attachment
    - Caching and logging
    """

    def __init__(self):
        """Initialize query search service with all dependencies"""
        self.embedding_service = get_embedding_service()
        self.vector_search_service = get_vector_search_service()
        self.ai_registry_service = get_ai_registry_service()
        self.db_client = get_zerodb_client()

        # Initialize Redis for caching
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            self.redis_client.ping()
            logger.info("QuerySearchService initialized with Redis caching")
        except Exception as e:
            logger.warning(f"Redis unavailable, search caching disabled: {e}")
            self.redis_client = None

        # Configuration
        self.cache_ttl = 300  # 5 minutes
        self.top_k_results = 10
        self.timeout_seconds = 10

        logger.info("QuerySearchService initialized successfully")

    def search_query(
        self,
        query: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        bypass_cache: bool = False
    ) -> Dict[str, Any]:
        """
        Execute full search query processing pipeline.

        This implements all 11 steps of the search pipeline as specified
        in the US-038 requirements.

        Args:
            query: User's search query
            user_id: Optional authenticated user ID
            ip_address: Client IP address (for logging)
            bypass_cache: Skip cache check and update (for testing)

        Returns:
            Search response with answer, sources, media, related_queries, latency_ms

        Raises:
            QuerySearchError: If search fails at any step
        """
        start_time = time.time()
        pipeline_start = start_time
        error_message = None
        cached = False

        try:
            # Step 1: Normalize query
            logger.info(f"[Step 1/11] Normalizing query: '{query[:50]}...'")
            normalized_query = self._normalize_query(query)
            step_1_time = time.time()
            logger.debug(f"Step 1 completed in {int((step_1_time - start_time) * 1000)}ms")

            # Step 2: Rate limit check (handled by middleware, skip in service)
            logger.info("[Step 2/11] Rate limit check (handled by middleware)")
            step_2_time = time.time()

            # Step 3: Check cache
            if not bypass_cache:
                logger.info("[Step 3/11] Checking cache")
                cached_result = self._get_cached_result(normalized_query)
                if cached_result:
                    logger.info("Cache hit - returning cached result")
                    cached_result["cached"] = True
                    cached_result["latency_ms"] = int((time.time() - pipeline_start) * 1000)
                    return cached_result
                logger.debug("Cache miss - proceeding with search")
            else:
                logger.info("[Step 3/11] Bypassing cache")
            step_3_time = time.time()

            # Step 4: Generate query embedding
            logger.info("[Step 4/11] Generating query embedding")
            try:
                query_embedding = self.embedding_service.generate_embedding(
                    text=normalized_query,
                    use_cache=True
                )
                logger.info(f"Query embedding generated (dimension: {len(query_embedding)})")
            except EmbeddingError as e:
                logger.error(f"Embedding generation failed: {e}")
                raise QuerySearchError(f"Failed to generate query embedding: {e}")
            step_4_time = time.time()
            logger.debug(f"Step 4 completed in {int((step_4_time - step_3_time) * 1000)}ms")

            # Step 5: ZeroDB vector search
            logger.info(f"[Step 5/11] Performing vector search (top_k={self.top_k_results})")
            try:
                search_results = self.vector_search_service.search_martial_arts_content(
                    query_vector=query_embedding,
                    top_k=self.top_k_results,
                    content_types=None  # Search all types
                )
                logger.info(f"Vector search returned {len(search_results)} results")
            except VectorSearchError as e:
                logger.error(f"Vector search failed: {e}")
                raise QuerySearchError(f"Vector search failed: {e}")
            step_5_time = time.time()
            logger.debug(f"Step 5 completed in {int((step_5_time - step_4_time) * 1000)}ms")

            # Step 6 & 7: Send context to AI Registry and get LLM answer
            logger.info("[Step 6-7/11] Generating AI answer with context")
            try:
                ai_response = self.ai_registry_service.generate_answer(
                    query=query,  # Use original query, not normalized
                    context=search_results,
                    model="gpt-4o-mini",
                    temperature=0.7,
                    max_tokens=1000
                )
                answer = ai_response["answer"]
                logger.info(f"AI answer generated (tokens: {ai_response.get('tokens_used', 0)})")
            except AIRegistryError as e:
                logger.error(f"AI answer generation failed: {e}")
                # Fall back to a basic response if AI fails
                answer = self._generate_fallback_answer(search_results)
                logger.warning("Using fallback answer due to AI error")
            step_7_time = time.time()
            logger.debug(f"Steps 6-7 completed in {int((step_7_time - step_5_time) * 1000)}ms")

            # Step 8: Attach relevant media
            logger.info("[Step 8/11] Attaching relevant media")
            media = self._attach_media(search_results)
            logger.info(
                f"Attached {len(media.get('videos', []))} videos, "
                f"{len(media.get('images', []))} images"
            )
            step_8_time = time.time()
            logger.debug(f"Step 8 completed in {int((step_8_time - step_7_time) * 1000)}ms")

            # Generate sources from search results
            sources = self._format_sources(search_results)

            # Generate related queries (non-blocking, use empty list on error)
            try:
                related_queries = self.ai_registry_service.generate_related_queries(
                    query=query,
                    count=3
                )
            except Exception as e:
                logger.warning(f"Failed to generate related queries: {e}")
                related_queries = []

            # Build response
            response = {
                "answer": answer,
                "sources": sources,
                "media": media,
                "related_queries": related_queries,
                "latency_ms": int((time.time() - pipeline_start) * 1000),
                "cached": False
            }

            # Step 9: Cache result
            if not bypass_cache:
                logger.info("[Step 9/11] Caching result")
                self._cache_result(normalized_query, response)
            else:
                logger.info("[Step 9/11] Skipping cache (bypass enabled)")
            step_9_time = time.time()

            # Step 10: Log query
            logger.info("[Step 10/11] Logging query to ZeroDB")
            self._log_query(
                query=query,
                normalized_query=normalized_query,
                user_id=user_id,
                ip_address=ip_address,
                latency_ms=response["latency_ms"],
                cached=cached,
                error=None
            )
            step_10_time = time.time()

            # Step 11: Return formatted response
            logger.info(
                f"[Step 11/11] Search completed successfully in {response['latency_ms']}ms"
            )

            return response

        except QuerySearchError as e:
            error_message = str(e)
            logger.error(f"Search failed: {e}")
            raise
        except Exception as e:
            error_message = str(e)
            logger.error(f"Unexpected error during search: {e}")
            raise QuerySearchError(f"Search failed: {e}")
        finally:
            # Always log the query attempt (even on error)
            if error_message:
                total_latency = int((time.time() - pipeline_start) * 1000)
                try:
                    self._log_query(
                        query=query,
                        normalized_query=query.strip().lower() if query else "",
                        user_id=user_id,
                        ip_address=ip_address,
                        latency_ms=total_latency,
                        cached=False,
                        error=error_message
                    )
                except Exception as log_error:
                    logger.error(f"Failed to log error query: {log_error}")

    def _normalize_query(self, query: str) -> str:
        """
        Normalize query string.

        Args:
            query: Raw query string

        Returns:
            Normalized query (lowercase, trimmed)

        Raises:
            QuerySearchError: If query is invalid
        """
        if not query:
            raise QuerySearchError("Query cannot be empty")

        normalized = query.strip().lower()

        if not normalized:
            raise QuerySearchError("Query cannot be empty")

        if len(normalized) > 500:
            raise QuerySearchError("Query exceeds maximum length of 500 characters")

        return normalized

    def _get_cached_result(self, normalized_query: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached search result.

        Args:
            normalized_query: Normalized query string

        Returns:
            Cached result or None if not found
        """
        if not self.redis_client:
            return None

        try:
            cache_key = self._generate_cache_key(normalized_query)
            cached_data = self.redis_client.get(cache_key)

            if cached_data:
                result = json.loads(cached_data)
                logger.debug(f"Retrieved cached result for query: '{normalized_query[:50]}...'")
                return result

        except Exception as e:
            logger.warning(f"Failed to retrieve cached result: {e}")

        return None

    def _cache_result(self, normalized_query: str, result: Dict[str, Any]):
        """
        Cache search result.

        Args:
            normalized_query: Normalized query string
            result: Search result to cache
        """
        if not self.redis_client:
            return

        try:
            cache_key = self._generate_cache_key(normalized_query)
            cached_data = json.dumps(result)

            self.redis_client.setex(
                cache_key,
                self.cache_ttl,
                cached_data
            )

            logger.debug(f"Cached result for query: '{normalized_query[:50]}...'")

        except Exception as e:
            logger.warning(f"Failed to cache result: {e}")

    def _generate_cache_key(self, normalized_query: str) -> str:
        """
        Generate Redis cache key for query.

        Args:
            normalized_query: Normalized query string

        Returns:
            Cache key string
        """
        query_hash = hashlib.sha256(normalized_query.encode()).hexdigest()
        return f"search:query:{query_hash}"

    def _format_sources(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Format search results as sources for response.

        Args:
            search_results: Raw search results from vector search

        Returns:
            List of formatted source objects
        """
        sources = []

        for result in search_results:
            data = result.get("data", {})
            source_collection = result.get("source_collection", "unknown")

            # Extract title
            title = (
                data.get("title") or
                data.get("name") or
                data.get("event_name") or
                "Untitled"
            )

            # Generate URL
            doc_id = result.get("id", "")
            url_map = {
                "events": f"/events/{doc_id}",
                "articles": f"/articles/{doc_id}",
                "profiles": f"/members/{doc_id}",
                "techniques": f"/techniques/{doc_id}"
            }
            url = url_map.get(source_collection, f"/{source_collection}/{doc_id}")

            # Map collection to source type
            source_type_map = {
                "events": "event",
                "articles": "article",
                "profiles": "profile",
                "techniques": "technique"
            }
            source_type = source_type_map.get(source_collection, "resource")

            sources.append({
                "title": title,
                "url": url,
                "source_type": source_type
            })

        return sources

    def _attach_media(self, search_results: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, str]]]:
        """
        Attach relevant media (videos and images) from search results.

        Args:
            search_results: Search results from vector search

        Returns:
            Media object with videos and images
        """
        videos = []
        images = []

        for result in search_results:
            data = result.get("data", {})

            # Extract video information (Cloudflare Stream)
            if "video_id" in data or "cloudflare_stream_id" in data:
                video_id = data.get("cloudflare_stream_id") or data.get("video_id")
                video_title = (
                    data.get("video_title") or
                    data.get("title") or
                    "Video"
                )

                videos.append({
                    "id": video_id,
                    "title": video_title,
                    "cloudflare_stream_id": video_id
                })

            # Extract image information (ZeroDB Object Storage)
            if "image_url" in data or "zerodb_object_key" in data:
                image_url = data.get("image_url", "")
                image_key = data.get("zerodb_object_key", "")
                image_alt = data.get("image_alt") or data.get("title") or "Image"

                images.append({
                    "url": image_url,
                    "alt": image_alt,
                    "zerodb_object_key": image_key
                })

        return {
            "videos": videos[:5],  # Limit to 5 videos
            "images": images[:5]   # Limit to 5 images
        }

    def _generate_fallback_answer(self, search_results: List[Dict[str, Any]]) -> str:
        """
        Generate a basic fallback answer when AI service fails.

        Args:
            search_results: Search results from vector search

        Returns:
            Formatted fallback answer
        """
        if not search_results:
            return "I couldn't find any relevant information for your query. Please try rephrasing your question or searching for different keywords."

        # Build a simple answer from top results
        answer_parts = ["Here are some relevant resources I found:\n"]

        for i, result in enumerate(search_results[:3], 1):
            data = result.get("data", {})
            title = data.get("title") or data.get("name") or f"Resource {i}"
            description = data.get("description") or data.get("content") or ""

            if description:
                snippet = description[:200] + "..." if len(description) > 200 else description
                answer_parts.append(f"\n**{i}. {title}**\n{snippet}\n")

        return "".join(answer_parts)

    def _log_query(
        self,
        query: str,
        normalized_query: str,
        user_id: Optional[str],
        ip_address: Optional[str],
        latency_ms: int,
        cached: bool,
        error: Optional[str]
    ):
        """
        Log search query to ZeroDB for analytics.

        Args:
            query: Original query
            normalized_query: Normalized query
            user_id: Optional authenticated user ID
            ip_address: Client IP address
            latency_ms: Query latency in milliseconds
            cached: Whether result was from cache
            error: Error message if query failed
        """
        try:
            # Hash IP address for privacy
            ip_hash = None
            if ip_address:
                ip_hash = hashlib.sha256(ip_address.encode()).hexdigest()

            # Prepare log document
            log_data = {
                "query": query,
                "normalized_query": normalized_query,
                "user_id": user_id,
                "ip_hash": ip_hash,
                "timestamp": datetime.utcnow().isoformat(),
                "latency_ms": latency_ms,
                "cached": cached,
                "error": error,
                "success": error is None
            }

            # Store in ZeroDB
            self.db_client.create_document(
                collection="search_queries",
                data=log_data
            )

            logger.debug(f"Query logged to ZeroDB: {query[:50]}...")

        except ZeroDBError as e:
            logger.error(f"Failed to log query to ZeroDB: {e}")
        except Exception as e:
            logger.error(f"Unexpected error logging query: {e}")


# Global service instance (singleton pattern)
_service_instance: Optional[QuerySearchService] = None


def get_query_search_service() -> QuerySearchService:
    """
    Get or create the global QuerySearchService instance.

    Returns:
        QuerySearchService instance
    """
    global _service_instance

    if _service_instance is None:
        _service_instance = QuerySearchService()

    return _service_instance
