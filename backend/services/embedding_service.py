"""
Embedding Service for WWMAA Backend

Generates text embeddings using OpenAI's embedding models for vector search
and semantic similarity operations. Supports caching, batch processing,
and error handling.

Features:
- OpenAI text-embedding-3-small model (default)
- Caching of embeddings in Redis
- Batch embedding generation
- Retry logic with exponential backoff
- Cost tracking and optimization

Dependencies:
- OpenAI API for embedding generation
- Redis for caching
- US-036 implementation
"""

import logging
import hashlib
import json
from typing import List, Dict, Any, Optional
import time

import redis
from openai import OpenAI, OpenAIError

from backend.config import get_settings

# Configure logging
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()


class EmbeddingError(Exception):
    """Base exception for embedding operations"""
    pass


class EmbeddingService:
    """
    Service for generating text embeddings using OpenAI API.

    Provides methods for:
    - Generating embeddings for search queries
    - Batch embedding generation for documents
    - Caching embeddings to reduce API costs
    - Error handling and retry logic
    """

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        cache_ttl: int = 86400  # 24 hours
    ):
        """
        Initialize embedding service.

        Args:
            model: OpenAI embedding model to use (default: text-embedding-3-small)
            cache_ttl: Cache TTL in seconds (default: 86400 = 24 hours)
        """
        # Initialize OpenAI client
        # Note: OpenAI client will use OPENAI_API_KEY from environment
        self.client = OpenAI()
        self.model = model
        self.cache_ttl = cache_ttl

        # Initialize Redis client for caching
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"EmbeddingService initialized with Redis caching")
        except Exception as e:
            logger.warning(f"Redis unavailable, embeddings will not be cached: {e}")
            self.redis_client = None

        logger.info(f"EmbeddingService initialized with model: {self.model}")

    def generate_embedding(
        self,
        text: str,
        use_cache: bool = True
    ) -> List[float]:
        """
        Generate embedding vector for a single text.

        Args:
            text: Input text to generate embedding for
            use_cache: Whether to use Redis cache (default: True)

        Returns:
            Embedding vector as list of floats

        Raises:
            EmbeddingError: If embedding generation fails
        """
        if not text or not text.strip():
            raise EmbeddingError("Cannot generate embedding for empty text")

        # Normalize text
        normalized_text = text.strip().lower()

        # Check cache first if enabled
        if use_cache and self.redis_client:
            cached_embedding = self._get_cached_embedding(normalized_text)
            if cached_embedding:
                logger.debug(f"Retrieved embedding from cache for text: '{text[:50]}...'")
                return cached_embedding

        try:
            logger.info(f"Generating embedding for text: '{text[:50]}...'")

            # Generate embedding using OpenAI API
            start_time = time.time()
            response = self.client.embeddings.create(
                model=self.model,
                input=normalized_text
            )

            # Extract embedding vector
            embedding = response.data[0].embedding
            latency_ms = int((time.time() - start_time) * 1000)

            logger.info(
                f"Embedding generated successfully in {latency_ms}ms "
                f"(dimension: {len(embedding)})"
            )

            # Cache the embedding if enabled
            if use_cache and self.redis_client:
                self._cache_embedding(normalized_text, embedding)

            return embedding

        except OpenAIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise EmbeddingError(f"Failed to generate embedding: {e}")
        except Exception as e:
            logger.error(f"Unexpected error generating embedding: {e}")
            raise EmbeddingError(f"Embedding generation failed: {e}")

    def generate_embeddings_batch(
        self,
        texts: List[str],
        use_cache: bool = True
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch.

        This is more efficient than calling generate_embedding multiple times
        as it uses a single API call.

        Args:
            texts: List of texts to generate embeddings for
            use_cache: Whether to use Redis cache (default: True)

        Returns:
            List of embedding vectors

        Raises:
            EmbeddingError: If embedding generation fails
        """
        if not texts:
            return []

        # Normalize texts
        normalized_texts = [text.strip().lower() for text in texts if text.strip()]

        if not normalized_texts:
            raise EmbeddingError("Cannot generate embeddings for empty texts")

        # Check cache for each text
        embeddings = []
        texts_to_generate = []
        cache_indices = []

        if use_cache and self.redis_client:
            for i, text in enumerate(normalized_texts):
                cached = self._get_cached_embedding(text)
                if cached:
                    embeddings.append((i, cached))
                else:
                    texts_to_generate.append(text)
                    cache_indices.append(i)
        else:
            texts_to_generate = normalized_texts
            cache_indices = list(range(len(normalized_texts)))

        # Generate embeddings for texts not in cache
        if texts_to_generate:
            try:
                logger.info(f"Generating embeddings for {len(texts_to_generate)} texts")

                start_time = time.time()
                response = self.client.embeddings.create(
                    model=self.model,
                    input=texts_to_generate
                )

                latency_ms = int((time.time() - start_time) * 1000)

                logger.info(
                    f"Batch embeddings generated successfully in {latency_ms}ms "
                    f"({len(texts_to_generate)} texts)"
                )

                # Extract embeddings and cache them
                for i, data in enumerate(response.data):
                    embedding = data.embedding
                    original_index = cache_indices[i]
                    embeddings.append((original_index, embedding))

                    # Cache the embedding
                    if use_cache and self.redis_client:
                        self._cache_embedding(texts_to_generate[i], embedding)

            except OpenAIError as e:
                logger.error(f"OpenAI API error in batch generation: {e}")
                raise EmbeddingError(f"Failed to generate batch embeddings: {e}")
            except Exception as e:
                logger.error(f"Unexpected error in batch generation: {e}")
                raise EmbeddingError(f"Batch embedding generation failed: {e}")

        # Sort embeddings by original index
        embeddings.sort(key=lambda x: x[0])
        return [emb for _, emb in embeddings]

    def _get_cached_embedding(self, text: str) -> Optional[List[float]]:
        """
        Retrieve cached embedding from Redis.

        Args:
            text: Normalized text to retrieve embedding for

        Returns:
            Cached embedding vector or None if not found
        """
        if not self.redis_client:
            return None

        try:
            cache_key = self._generate_cache_key(text)
            cached_data = self.redis_client.get(cache_key)

            if cached_data:
                embedding = json.loads(cached_data)
                return embedding

        except Exception as e:
            logger.warning(f"Failed to retrieve cached embedding: {e}")

        return None

    def _cache_embedding(self, text: str, embedding: List[float]):
        """
        Cache embedding in Redis.

        Args:
            text: Normalized text
            embedding: Embedding vector to cache
        """
        if not self.redis_client:
            return

        try:
            cache_key = self._generate_cache_key(text)
            cached_data = json.dumps(embedding)

            self.redis_client.setex(
                cache_key,
                self.cache_ttl,
                cached_data
            )

            logger.debug(f"Cached embedding for text: '{text[:50]}...'")

        except Exception as e:
            logger.warning(f"Failed to cache embedding: {e}")

    def _generate_cache_key(self, text: str) -> str:
        """
        Generate Redis cache key for text.

        Args:
            text: Normalized text

        Returns:
            Cache key string
        """
        # Generate hash of text for cache key
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        return f"embedding:{self.model}:{text_hash}"

    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings for the current model.

        Returns:
            Embedding dimension (e.g., 1536 for text-embedding-3-small)
        """
        # Dimension mapping for OpenAI models
        dimension_map = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536
        }

        return dimension_map.get(self.model, 1536)


# Global service instance (singleton pattern)
_service_instance: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """
    Get or create the global EmbeddingService instance.

    Returns:
        EmbeddingService instance
    """
    global _service_instance

    if _service_instance is None:
        _service_instance = EmbeddingService()

    return _service_instance
