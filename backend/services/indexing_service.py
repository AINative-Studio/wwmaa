"""
Content Indexing Service for WWMAA

Provides comprehensive content indexing functionality including:
- Content extraction from ZeroDB collections (events, articles, profiles, videos)
- Text chunking with tiktoken
- OpenAI embedding generation
- Batch processing for efficiency
- Incremental indexing with timestamp tracking
- Full reindex capability
- Error handling and retry logic

Collections Indexed:
- events: Event titles, descriptions, and locations
- articles: Blog article titles, content, and keywords
- training_videos: Video titles, transcripts, and metadata
- member_profiles: Member names, bios, and disciplines
"""

import logging
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

try:
    from openai import OpenAI
    from openai import OpenAIError, RateLimitError, APIError
except ImportError:
    raise ImportError(
        "OpenAI library is required. Install it with: pip install openai"
    )

from backend.config import settings
from backend.services.zerodb_service import get_zerodb_client, ZeroDBError
from backend.utils.text_chunking import chunk_text, count_tokens

# Configure logging
logger = logging.getLogger(__name__)


class ContentType(str, Enum):
    """Content types that can be indexed"""
    EVENTS = "events"
    ARTICLES = "articles"
    TRAINING_VIDEOS = "training_videos"
    MEMBER_PROFILES = "member_profiles"


class IndexingStatus(str, Enum):
    """Indexing operation status"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class IndexingService:
    """
    Service for indexing content into ZeroDB with OpenAI embeddings.

    Handles content extraction, chunking, embedding generation, and storage
    in the content_index collection.
    """

    # Collection name for storing indexed content
    INDEX_COLLECTION = "content_index"

    # Metadata collection for tracking indexing status
    INDEX_METADATA_COLLECTION = "indexing_metadata"

    def __init__(self):
        """Initialize the indexing service."""
        self.zerodb = get_zerodb_client()
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.embedding_model = settings.OPENAI_EMBEDDING_MODEL
        self.batch_size = settings.INDEXING_BATCH_SIZE

        # Track current indexing status
        self._status = IndexingStatus.IDLE
        self._current_operation = None
        self._stats = {
            "total_indexed": 0,
            "total_chunks": 0,
            "total_tokens": 0,
            "errors": 0,
            "last_indexed_at": None
        }

        logger.info(
            f"IndexingService initialized (model={self.embedding_model}, "
            f"batch_size={self.batch_size})"
        )

    def get_status(self) -> Dict[str, Any]:
        """
        Get current indexing status and statistics.

        Returns:
            Dictionary with status, stats, and current operation info
        """
        return {
            "status": self._status.value,
            "current_operation": self._current_operation,
            "stats": self._stats.copy()
        }

    def get_stats(self) -> Dict[str, Any]:
        """
        Get detailed indexing statistics.

        Returns:
            Dictionary with indexing statistics per content type
        """
        try:
            # Query metadata collection for statistics
            result = self.zerodb.query_documents(
                collection=self.INDEX_METADATA_COLLECTION,
                filters={},
                limit=100
            )

            metadata_docs = result.get("documents", [])

            # Aggregate statistics
            stats_by_type = {}
            total_documents = 0
            total_chunks = 0

            for doc in metadata_docs:
                data = doc.get("data", {})
                content_type = data.get("content_type")
                if content_type:
                    if content_type not in stats_by_type:
                        stats_by_type[content_type] = {
                            "documents": 0,
                            "chunks": 0,
                            "last_indexed": None
                        }

                    stats_by_type[content_type]["documents"] += 1
                    stats_by_type[content_type]["chunks"] += data.get("chunk_count", 0)
                    total_documents += 1
                    total_chunks += data.get("chunk_count", 0)

                    # Track latest indexing time
                    indexed_at = data.get("indexed_at")
                    if indexed_at:
                        if (not stats_by_type[content_type]["last_indexed"] or
                                indexed_at > stats_by_type[content_type]["last_indexed"]):
                            stats_by_type[content_type]["last_indexed"] = indexed_at

            return {
                "total_documents_indexed": total_documents,
                "total_chunks": total_chunks,
                "by_content_type": stats_by_type,
                "current_status": self._status.value
            }

        except Exception as e:
            logger.error(f"Error retrieving indexing stats: {e}")
            return {
                "total_documents_indexed": 0,
                "total_chunks": 0,
                "by_content_type": {},
                "error": str(e)
            }

    def extract_content_text(
        self,
        content_type: ContentType,
        document: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Extract searchable text from a document based on content type.

        Args:
            content_type: Type of content
            document: Document data from ZeroDB

        Returns:
            Tuple of (extracted_text, metadata)
        """
        data = document.get("data", {})
        doc_id = document.get("id", "unknown")

        if content_type == ContentType.EVENTS:
            # Events: title, description, location
            parts = [
                data.get("title", ""),
                data.get("description", ""),
                f"Location: {data.get('location', '')}" if data.get("location") else ""
            ]
            text = " ".join(filter(None, parts))
            metadata = {
                "content_type": content_type.value,
                "document_id": doc_id,
                "title": data.get("title", ""),
                "event_date": data.get("event_date"),
                "location": data.get("location")
            }

        elif content_type == ContentType.ARTICLES:
            # Articles: title, content, keywords
            parts = [
                data.get("title", ""),
                data.get("content", ""),
                f"Keywords: {', '.join(data.get('keywords', []))}" if data.get("keywords") else ""
            ]
            text = " ".join(filter(None, parts))
            metadata = {
                "content_type": content_type.value,
                "document_id": doc_id,
                "title": data.get("title", ""),
                "author": data.get("author"),
                "published_at": data.get("published_at"),
                "keywords": data.get("keywords", [])
            }

        elif content_type == ContentType.TRAINING_VIDEOS:
            # Training videos: title, transcript, metadata
            parts = [
                data.get("title", ""),
                data.get("description", ""),
                data.get("transcript", "")
            ]
            text = " ".join(filter(None, parts))
            metadata = {
                "content_type": content_type.value,
                "document_id": doc_id,
                "title": data.get("title", ""),
                "duration": data.get("duration"),
                "instructor": data.get("instructor"),
                "category": data.get("category")
            }

        elif content_type == ContentType.MEMBER_PROFILES:
            # Member profiles: name, bio, discipline
            parts = [
                data.get("name", ""),
                data.get("bio", ""),
                f"Discipline: {data.get('discipline', '')}" if data.get("discipline") else "",
                f"Location: {data.get('location', '')}" if data.get("location") else ""
            ]
            text = " ".join(filter(None, parts))
            metadata = {
                "content_type": content_type.value,
                "document_id": doc_id,
                "name": data.get("name", ""),
                "discipline": data.get("discipline"),
                "location": data.get("location"),
                "member_since": data.get("member_since")
            }

        else:
            raise ValueError(f"Unsupported content type: {content_type}")

        return text.strip(), metadata

    def generate_embeddings(
        self,
        texts: List[str],
        retry_count: int = 3,
        backoff_factor: float = 2.0
    ) -> List[List[float]]:
        """
        Generate embeddings for a list of texts using OpenAI API.

        Implements retry logic with exponential backoff for rate limits.

        Args:
            texts: List of text strings to embed
            retry_count: Number of retries on failure
            backoff_factor: Backoff multiplier for retries

        Returns:
            List of embedding vectors

        Raises:
            OpenAIError: If embedding generation fails after retries
        """
        if not texts:
            return []

        for attempt in range(retry_count):
            try:
                logger.info(f"Generating embeddings for {len(texts)} texts (attempt {attempt + 1})")

                response = self.openai_client.embeddings.create(
                    model=self.embedding_model,
                    input=texts
                )

                embeddings = [item.embedding for item in response.data]

                logger.info(f"Successfully generated {len(embeddings)} embeddings")
                return embeddings

            except RateLimitError as e:
                wait_time = backoff_factor ** attempt
                logger.warning(
                    f"Rate limit hit (attempt {attempt + 1}/{retry_count}). "
                    f"Waiting {wait_time}s before retry..."
                )
                if attempt < retry_count - 1:
                    time.sleep(wait_time)
                else:
                    logger.error(f"Rate limit exceeded after {retry_count} attempts")
                    raise

            except APIError as e:
                logger.error(f"OpenAI API error: {e}")
                if attempt < retry_count - 1:
                    wait_time = backoff_factor ** attempt
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise

            except OpenAIError as e:
                logger.error(f"OpenAI error: {e}")
                raise

        raise OpenAIError("Failed to generate embeddings after all retries")

    def index_document(
        self,
        content_type: ContentType,
        document: Dict[str, Any],
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Index a single document with embeddings.

        Args:
            content_type: Type of content being indexed
            document: Document data from ZeroDB
            force: Force reindex even if already indexed

        Returns:
            Dictionary with indexing results
        """
        doc_id = document.get("id")
        if not doc_id:
            logger.warning("Document missing ID, skipping")
            return {"success": False, "error": "Missing document ID"}

        try:
            # Check if already indexed (for incremental indexing)
            if not force:
                existing_metadata = self._get_index_metadata(content_type, doc_id)
                if existing_metadata:
                    doc_updated_at = document.get("data", {}).get("updated_at")
                    indexed_at = existing_metadata.get("indexed_at")

                    # Skip if already indexed and not updated since
                    if doc_updated_at and indexed_at and doc_updated_at <= indexed_at:
                        logger.debug(f"Document {doc_id} already indexed and up-to-date")
                        return {"success": True, "skipped": True, "reason": "already_indexed"}

            # Extract text content
            text, metadata = self.extract_content_text(content_type, document)

            if not text:
                logger.warning(f"No text content extracted from document {doc_id}")
                return {"success": False, "error": "No text content"}

            # Chunk text
            chunks = chunk_text(text, metadata=metadata)

            if not chunks:
                logger.warning(f"No chunks created for document {doc_id}")
                return {"success": False, "error": "No chunks created"}

            logger.info(f"Created {len(chunks)} chunks for document {doc_id}")

            # Process chunks in batches
            total_indexed = 0
            batch_texts = []
            batch_chunks = []

            for chunk in chunks:
                batch_texts.append(chunk["text"])
                batch_chunks.append(chunk)

                # Process batch when it reaches batch_size
                if len(batch_texts) >= self.batch_size:
                    indexed = self._index_chunk_batch(batch_texts, batch_chunks)
                    total_indexed += indexed
                    batch_texts = []
                    batch_chunks = []

            # Process remaining chunks
            if batch_texts:
                indexed = self._index_chunk_batch(batch_texts, batch_chunks)
                total_indexed += indexed

            # Store metadata about this indexing operation
            self._store_index_metadata(content_type, doc_id, len(chunks))

            logger.info(f"Successfully indexed document {doc_id} ({total_indexed} chunks)")

            return {
                "success": True,
                "document_id": doc_id,
                "chunks_indexed": total_indexed,
                "total_chunks": len(chunks)
            }

        except Exception as e:
            logger.error(f"Error indexing document {doc_id}: {e}")
            return {
                "success": False,
                "document_id": doc_id,
                "error": str(e)
            }

    def _index_chunk_batch(
        self,
        texts: List[str],
        chunks: List[Dict[str, Any]]
    ) -> int:
        """
        Index a batch of chunks with embeddings.

        Args:
            texts: List of text strings to embed
            chunks: List of chunk metadata

        Returns:
            Number of chunks successfully indexed
        """
        try:
            # Generate embeddings for the batch
            embeddings = self.generate_embeddings(texts)

            if len(embeddings) != len(chunks):
                logger.error(
                    f"Embedding count mismatch: {len(embeddings)} embeddings "
                    f"for {len(chunks)} chunks"
                )
                return 0

            # Store each chunk with its embedding
            indexed_count = 0
            for chunk, embedding in zip(chunks, embeddings):
                try:
                    # Create index document
                    index_doc = {
                        "text": chunk["text"],
                        "embedding": embedding,
                        "tokens": chunk["tokens"],
                        "chunk_index": chunk["chunk_index"],
                        "total_chunks": chunk["total_chunks"],
                        "metadata": chunk["metadata"],
                        "indexed_at": datetime.now(timezone.utc).isoformat()
                    }

                    # Store in content_index collection
                    self.zerodb.create_document(
                        collection=self.INDEX_COLLECTION,
                        data=index_doc
                    )

                    indexed_count += 1

                except ZeroDBError as e:
                    logger.error(f"Error storing chunk in ZeroDB: {e}")
                    self._stats["errors"] += 1

            return indexed_count

        except Exception as e:
            logger.error(f"Error indexing chunk batch: {e}")
            self._stats["errors"] += 1
            return 0

    def _get_index_metadata(
        self,
        content_type: ContentType,
        document_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get indexing metadata for a document.

        Args:
            content_type: Type of content
            document_id: Document ID

        Returns:
            Metadata dictionary or None if not found
        """
        try:
            result = self.zerodb.query_documents(
                collection=self.INDEX_METADATA_COLLECTION,
                filters={
                    "content_type": content_type.value,
                    "document_id": document_id
                },
                limit=1
            )

            docs = result.get("documents", [])
            if docs:
                return docs[0].get("data", {})

            return None

        except ZeroDBError as e:
            logger.error(f"Error retrieving index metadata: {e}")
            return None

    def _store_index_metadata(
        self,
        content_type: ContentType,
        document_id: str,
        chunk_count: int
    ):
        """
        Store metadata about an indexing operation.

        Args:
            content_type: Type of content indexed
            document_id: Document ID
            chunk_count: Number of chunks created
        """
        try:
            metadata = {
                "content_type": content_type.value,
                "document_id": document_id,
                "chunk_count": chunk_count,
                "indexed_at": datetime.now(timezone.utc).isoformat()
            }

            # Check if metadata already exists
            existing = self._get_index_metadata(content_type, document_id)

            if existing:
                # Update existing metadata
                # Note: This assumes the metadata document has an ID
                # You may need to adjust this based on your ZeroDB implementation
                logger.debug(f"Updating index metadata for {document_id}")
            else:
                # Create new metadata
                self.zerodb.create_document(
                    collection=self.INDEX_METADATA_COLLECTION,
                    data=metadata
                )

        except ZeroDBError as e:
            logger.error(f"Error storing index metadata: {e}")

    def index_collection(
        self,
        content_type: ContentType,
        incremental: bool = True,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Index all documents in a collection.

        Args:
            content_type: Type of content to index
            incremental: Only index new/updated documents
            limit: Maximum number of documents to index (for testing)

        Returns:
            Dictionary with indexing results
        """
        self._status = IndexingStatus.RUNNING
        self._current_operation = f"Indexing {content_type.value}"

        try:
            logger.info(
                f"Starting indexing for {content_type.value} "
                f"(incremental={incremental}, limit={limit})"
            )

            # Query documents from the collection
            result = self.zerodb.query_documents(
                collection=content_type.value,
                filters={},
                limit=limit or 1000,
                offset=0
            )

            documents = result.get("documents", [])
            total_docs = len(documents)

            logger.info(f"Found {total_docs} documents to process")

            # Index each document
            results = {
                "content_type": content_type.value,
                "total_documents": total_docs,
                "indexed": 0,
                "skipped": 0,
                "errors": 0,
                "error_details": []
            }

            for doc in documents:
                result = self.index_document(content_type, doc, force=not incremental)

                if result.get("success"):
                    if result.get("skipped"):
                        results["skipped"] += 1
                    else:
                        results["indexed"] += 1
                        self._stats["total_indexed"] += 1
                        self._stats["total_chunks"] += result.get("chunks_indexed", 0)
                else:
                    results["errors"] += 1
                    results["error_details"].append({
                        "document_id": result.get("document_id"),
                        "error": result.get("error")
                    })

            self._stats["last_indexed_at"] = datetime.now(timezone.utc).isoformat()
            self._status = IndexingStatus.COMPLETED
            self._current_operation = None

            logger.info(
                f"Completed indexing {content_type.value}: "
                f"{results['indexed']} indexed, {results['skipped']} skipped, "
                f"{results['errors']} errors"
            )

            return results

        except Exception as e:
            logger.error(f"Error indexing collection {content_type.value}: {e}")
            self._status = IndexingStatus.FAILED
            self._current_operation = None

            return {
                "content_type": content_type.value,
                "success": False,
                "error": str(e)
            }

    def reindex_all(self, content_types: Optional[List[ContentType]] = None) -> Dict[str, Any]:
        """
        Perform full reindex of all or specified content types.

        Args:
            content_types: List of content types to reindex (all if None)

        Returns:
            Dictionary with results for each content type
        """
        if content_types is None:
            content_types = list(ContentType)

        logger.info(f"Starting full reindex for {len(content_types)} content types")

        results = {}
        for content_type in content_types:
            try:
                result = self.index_collection(content_type, incremental=False)
                results[content_type.value] = result
            except Exception as e:
                logger.error(f"Error reindexing {content_type.value}: {e}")
                results[content_type.value] = {
                    "success": False,
                    "error": str(e)
                }

        logger.info("Full reindex completed")
        return results


# Global singleton instance
_indexing_service_instance = None


def get_indexing_service() -> IndexingService:
    """
    Get or create the global IndexingService instance.

    Returns:
        IndexingService instance
    """
    global _indexing_service_instance

    if _indexing_service_instance is None:
        _indexing_service_instance = IndexingService()

    return _indexing_service_instance
