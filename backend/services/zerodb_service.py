"""
ZeroDB Client Wrapper Service

Provides a comprehensive Python client for interacting with ZeroDB API.
Includes CRUD operations, vector search, object storage, connection pooling,
retry logic with exponential backoff, and comprehensive error handling.
"""

import logging
import time
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from backend.config import settings

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class ZeroDBError(Exception):
    """Base exception for ZeroDB operations"""
    pass


class ZeroDBConnectionError(ZeroDBError):
    """Exception raised for connection errors"""
    pass


class ZeroDBAuthenticationError(ZeroDBError):
    """Exception raised for authentication errors"""
    pass


class ZeroDBNotFoundError(ZeroDBError):
    """Exception raised when a resource is not found"""
    pass


class ZeroDBValidationError(ZeroDBError):
    """Exception raised for validation errors"""
    pass


class ZeroDBClient:
    """
    ZeroDB API Client Wrapper

    Provides methods for:
    - CRUD operations on documents
    - Vector similarity search
    - Object storage operations (upload, download, delete)
    - Connection pooling
    - Automatic retry with exponential backoff
    - Comprehensive error handling
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 10,
        max_retries: int = 3,
        pool_connections: int = 10,
        pool_maxsize: int = 10
    ):
        """
        Initialize ZeroDB client

        Args:
            api_key: ZeroDB API key (defaults to settings.ZERODB_API_KEY)
            base_url: ZeroDB API base URL (defaults to settings.ZERODB_API_BASE_URL)
            timeout: Request timeout in seconds (default: 10)
            max_retries: Maximum number of retries for failed requests (default: 3)
            pool_connections: Number of connection pool connections (default: 10)
            pool_maxsize: Maximum size of connection pool (default: 10)
        """
        self.api_key = api_key or settings.ZERODB_API_KEY
        self.base_url = (base_url or str(settings.ZERODB_API_BASE_URL)).rstrip('/')
        self.timeout = timeout

        if not self.api_key:
            raise ZeroDBAuthenticationError("ZERODB_API_KEY is required")
        if not self.base_url:
            raise ZeroDBConnectionError("ZERODB_API_BASE_URL is required")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # Configure session with connection pooling and retry logic
        self.session = self._create_session(max_retries, pool_connections, pool_maxsize)

        logger.info(f"ZeroDBClient initialized with base_url: {self.base_url}")

    def _create_session(
        self,
        max_retries: int,
        pool_connections: int,
        pool_maxsize: int
    ) -> requests.Session:
        """
        Create a requests session with connection pooling and retry logic

        Args:
            max_retries: Maximum number of retries
            pool_connections: Number of connection pool connections
            pool_maxsize: Maximum size of connection pool

        Returns:
            Configured requests.Session object
        """
        session = requests.Session()

        # Configure retry strategy with exponential backoff
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,  # Wait 1, 2, 4 seconds between retries
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE"]
        )

        # Configure HTTP adapter with connection pooling
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize
        )

        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _build_url(self, *parts: str) -> str:
        """
        Build a full URL from base URL and path parts

        Args:
            *parts: URL path parts to join

        Returns:
            Complete URL string
        """
        path = "/".join(str(part).strip("/") for part in parts if part)
        return urljoin(self.base_url + "/", path)

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Handle API response and raise appropriate exceptions

        Args:
            response: Response object from requests

        Returns:
            JSON response data

        Raises:
            ZeroDBAuthenticationError: For 401/403 errors
            ZeroDBNotFoundError: For 404 errors
            ZeroDBValidationError: For 400/422 errors
            ZeroDBError: For other errors
        """
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_data = {}
            try:
                error_data = response.json()
            except ValueError:
                error_data = {"detail": response.text}

            error_message = error_data.get("detail") or error_data.get("message") or str(e)

            if response.status_code in (401, 403):
                logger.error(f"Authentication error: {error_message}")
                raise ZeroDBAuthenticationError(f"Authentication failed: {error_message}")
            elif response.status_code == 404:
                logger.warning(f"Resource not found: {error_message}")
                raise ZeroDBNotFoundError(f"Resource not found: {error_message}")
            elif response.status_code in (400, 422):
                logger.error(f"Validation error: {error_message}")
                raise ZeroDBValidationError(f"Validation error: {error_message}")
            else:
                logger.error(f"API error: {error_message}")
                raise ZeroDBError(f"API error ({response.status_code}): {error_message}")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            raise ZeroDBConnectionError(f"Failed to connect to ZeroDB: {e}")
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout error: {e}")
            raise ZeroDBConnectionError(f"Request timed out: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            raise ZeroDBError(f"Request failed: {e}")

    # CRUD Operations

    def create_document(
        self,
        collection: str,
        data: Dict[str, Any],
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new document in a ZeroDB collection

        Args:
            collection: Name of the collection
            data: Document data to create
            document_id: Optional custom document ID

        Returns:
            Created document with ID and metadata

        Raises:
            ZeroDBValidationError: If data is invalid
            ZeroDBError: If creation fails
        """
        url = self._build_url("collections", collection, "documents")

        payload = {"data": data}
        if document_id:
            payload["id"] = document_id

        logger.info(f"Creating document in collection '{collection}'")
        response = self.session.post(
            url,
            json=payload,
            headers=self.headers,
            timeout=self.timeout
        )

        result = self._handle_response(response)
        logger.info(f"Document created successfully with ID: {result.get('id')}")
        return result

    def get_document(
        self,
        collection: str,
        document_id: str
    ) -> Dict[str, Any]:
        """
        Get a document by ID from a collection

        Args:
            collection: Name of the collection
            document_id: ID of the document to retrieve

        Returns:
            Document data

        Raises:
            ZeroDBNotFoundError: If document doesn't exist
            ZeroDBError: If retrieval fails
        """
        url = self._build_url("collections", collection, "documents", document_id)

        logger.info(f"Fetching document '{document_id}' from collection '{collection}'")
        try:
            response = self.session.get(
                url,
                headers=self.headers,
                timeout=self.timeout
            )
            result = self._handle_response(response)
            logger.info(f"Document '{document_id}' retrieved successfully")
            return result
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            raise ZeroDBConnectionError(f"Failed to connect to ZeroDB: {e}")
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout error: {e}")
            raise ZeroDBConnectionError(f"Request timed out: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            raise ZeroDBError(f"Request failed: {e}")

    def query_documents(
        self,
        collection: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        offset: int = 0,
        sort: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Query documents from a collection with filters

        Args:
            collection: Name of the collection
            filters: Filter criteria (e.g., {"status": "active", "age": {"$gte": 18}})
            limit: Maximum number of documents to return (default: 10)
            offset: Number of documents to skip (default: 0)
            sort: Sort criteria (e.g., {"created_at": "desc"})

        Returns:
            Query results with documents and metadata

        Raises:
            ZeroDBError: If query fails
        """
        url = self._build_url("collections", collection, "query")

        payload = {
            "filters": filters or {},
            "limit": limit,
            "offset": offset
        }

        if sort:
            payload["sort"] = sort

        logger.info(f"Querying collection '{collection}' with filters: {filters}")
        response = self.session.post(
            url,
            json=payload,
            headers=self.headers,
            timeout=self.timeout
        )

        result = self._handle_response(response)
        doc_count = len(result.get("documents", []))
        logger.info(f"Query returned {doc_count} documents")
        return result

    def update_document(
        self,
        collection: str,
        document_id: str,
        data: Dict[str, Any],
        merge: bool = True
    ) -> Dict[str, Any]:
        """
        Update a document in a collection

        Args:
            collection: Name of the collection
            document_id: ID of the document to update
            data: Updated document data
            merge: If True, merge with existing data; if False, replace entirely

        Returns:
            Updated document

        Raises:
            ZeroDBNotFoundError: If document doesn't exist
            ZeroDBValidationError: If data is invalid
            ZeroDBError: If update fails
        """
        url = self._build_url("collections", collection, "documents", document_id)

        payload = {
            "data": data,
            "merge": merge
        }

        logger.info(f"Updating document '{document_id}' in collection '{collection}'")
        response = self.session.put(
            url,
            json=payload,
            headers=self.headers,
            timeout=self.timeout
        )

        result = self._handle_response(response)
        logger.info(f"Document '{document_id}' updated successfully")
        return result

    def delete_document(
        self,
        collection: str,
        document_id: str
    ) -> Dict[str, Any]:
        """
        Delete a document from a collection

        Args:
            collection: Name of the collection
            document_id: ID of the document to delete

        Returns:
            Deletion confirmation

        Raises:
            ZeroDBNotFoundError: If document doesn't exist
            ZeroDBError: If deletion fails
        """
        url = self._build_url("collections", collection, "documents", document_id)

        logger.info(f"Deleting document '{document_id}' from collection '{collection}'")
        response = self.session.delete(
            url,
            headers=self.headers,
            timeout=self.timeout
        )

        result = self._handle_response(response)
        logger.info(f"Document '{document_id}' deleted successfully")
        return result

    # Vector Search Operations

    def create_vector_collection(
        self,
        collection: str,
        dimension: int = 1536,
        similarity_metric: str = "cosine",
        metadata_schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a vector search collection with specified configuration

        Args:
            collection: Name of the collection to create
            dimension: Vector dimension size (default: 1536 for OpenAI ada-002)
            similarity_metric: Similarity metric to use (cosine, euclidean, dot_product)
            metadata_schema: Optional schema for document metadata fields

        Returns:
            Collection creation confirmation with configuration

        Raises:
            ZeroDBValidationError: If configuration is invalid
            ZeroDBError: If creation fails

        Example:
            >>> client.create_vector_collection(
            ...     "content_index",
            ...     dimension=1536,
            ...     similarity_metric="cosine"
            ... )
        """
        url = self._build_url("collections", collection, "create")

        payload = {
            "type": "vector",
            "config": {
                "dimension": dimension,
                "similarity_metric": similarity_metric
            }
        }

        if metadata_schema:
            payload["metadata_schema"] = metadata_schema

        logger.info(
            f"Creating vector collection '{collection}' "
            f"(dimension={dimension}, metric={similarity_metric})"
        )
        response = self.session.post(
            url,
            json=payload,
            headers=self.headers,
            timeout=self.timeout
        )

        result = self._handle_response(response)
        logger.info(f"Vector collection '{collection}' created successfully")
        return result

    def insert_vector(
        self,
        collection: str,
        vector: List[float],
        metadata: Optional[Dict[str, Any]] = None,
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Insert a vector with metadata into a collection

        Args:
            collection: Name of the collection
            vector: Vector embedding to insert (must match collection dimension)
            metadata: Optional metadata to store with the vector
            document_id: Optional custom document ID

        Returns:
            Insertion confirmation with document ID

        Raises:
            ZeroDBValidationError: If vector dimension doesn't match collection
            ZeroDBError: If insertion fails

        Example:
            >>> embedding = [0.1, 0.2, ..., 0.9]  # 1536 dimensions
            >>> client.insert_vector(
            ...     "content_index",
            ...     vector=embedding,
            ...     metadata={"title": "Article", "source_type": "article"}
            ... )
        """
        url = self._build_url("collections", collection, "vectors")

        payload = {
            "vector": vector,
            "metadata": metadata or {}
        }

        if document_id:
            payload["id"] = document_id

        logger.info(
            f"Inserting vector into collection '{collection}' "
            f"(dimension={len(vector)})"
        )
        response = self.session.post(
            url,
            json=payload,
            headers=self.headers,
            timeout=self.timeout
        )

        result = self._handle_response(response)
        logger.info(f"Vector inserted successfully with ID: {result.get('id')}")
        return result

    def vector_search(
        self,
        collection: str,
        query_vector: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True,
        min_score: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Perform vector similarity search using cosine similarity

        Args:
            collection: Name of the collection
            query_vector: Query vector for similarity search
            top_k: Number of similar documents to return (default: 10)
            filters: Optional filters to apply before search
            include_metadata: Include document metadata in results
            min_score: Minimum similarity score threshold (0-1 for cosine)

        Returns:
            Search results with similar documents and similarity scores

        Raises:
            ZeroDBValidationError: If vector is invalid
            ZeroDBError: If search fails

        Example:
            >>> query_embedding = [0.1, 0.2, ..., 0.9]  # 1536 dimensions
            >>> results = client.vector_search(
            ...     "content_index",
            ...     query_vector=query_embedding,
            ...     top_k=5,
            ...     filters={"source_type": "event"}
            ... )
            >>> for result in results["results"]:
            ...     print(f"Score: {result['score']}, Title: {result['metadata']['title']}")
        """
        url = self._build_url("collections", collection, "vector-search")

        payload = {
            "vector": query_vector,
            "top_k": top_k,
            "include_metadata": include_metadata,
            "similarity_metric": "cosine"  # Explicitly set cosine similarity
        }

        if filters:
            payload["filters"] = filters

        if min_score is not None:
            payload["min_score"] = min_score

        logger.info(
            f"Performing vector search in collection '{collection}' "
            f"(top_k={top_k}, dimension={len(query_vector)})"
        )
        response = self.session.post(
            url,
            json=payload,
            headers=self.headers,
            timeout=self.timeout
        )

        result = self._handle_response(response)
        result_count = len(result.get("results", []))
        logger.info(f"Vector search returned {result_count} results")
        return result

    def batch_insert_vectors(
        self,
        collection: str,
        vectors: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Insert multiple vectors in a batch operation for better performance

        Args:
            collection: Name of the collection
            vectors: List of vector objects, each containing:
                - vector: List[float] - The embedding vector
                - metadata: Dict[str, Any] - Associated metadata
                - id: Optional[str] - Custom document ID

        Returns:
            Batch insertion confirmation with inserted IDs

        Raises:
            ZeroDBValidationError: If vectors are invalid
            ZeroDBError: If insertion fails

        Example:
            >>> vectors = [
            ...     {
            ...         "vector": [0.1, 0.2, ...],
            ...         "metadata": {"title": "Doc 1", "source_type": "article"}
            ...     },
            ...     {
            ...         "vector": [0.3, 0.4, ...],
            ...         "metadata": {"title": "Doc 2", "source_type": "event"}
            ...     }
            ... ]
            >>> client.batch_insert_vectors("content_index", vectors)
        """
        url = self._build_url("collections", collection, "vectors", "batch")

        payload = {
            "vectors": vectors
        }

        logger.info(f"Batch inserting {len(vectors)} vectors into collection '{collection}'")
        response = self.session.post(
            url,
            json=payload,
            headers=self.headers,
            timeout=self.timeout * 2  # Longer timeout for batch operations
        )

        result = self._handle_response(response)
        inserted_count = len(result.get("inserted_ids", []))
        logger.info(f"Successfully inserted {inserted_count} vectors")
        return result

    # Object Storage Operations

    def upload_object(
        self,
        file_path: str,
        object_name: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload a file to ZeroDB object storage

        Args:
            file_path: Path to the file to upload
            object_name: Name to store the object as (defaults to file basename)
            metadata: Optional metadata for the object
            content_type: MIME type of the file (auto-detected if not provided)

        Returns:
            Upload confirmation with object URL and metadata

        Raises:
            ZeroDBError: If upload fails
            FileNotFoundError: If file doesn't exist
        """
        import os
        import mimetypes

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        if not object_name:
            object_name = os.path.basename(file_path)

        if not content_type:
            content_type, _ = mimetypes.guess_type(file_path)
            content_type = content_type or "application/octet-stream"

        url = self._build_url("storage", "upload")

        # Prepare multipart form data
        files = {
            "file": (object_name, open(file_path, "rb"), content_type)
        }

        data = {}
        if metadata:
            data["metadata"] = str(metadata)

        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        logger.info(f"Uploading object '{object_name}' from '{file_path}'")
        response = self.session.post(
            url,
            files=files,
            data=data,
            headers=headers,
            timeout=self.timeout * 3  # Longer timeout for uploads
        )

        # Close the file
        files["file"][1].close()

        result = self._handle_response(response)
        logger.info(f"Object '{object_name}' uploaded successfully")
        return result

    def download_object(
        self,
        object_name: str,
        save_path: Optional[str] = None
    ) -> Union[bytes, str]:
        """
        Download a file from ZeroDB object storage

        Args:
            object_name: Name of the object to download
            save_path: Optional path to save the file (if not provided, returns bytes)

        Returns:
            File bytes if save_path not provided, else path to saved file

        Raises:
            ZeroDBNotFoundError: If object doesn't exist
            ZeroDBError: If download fails
        """
        url = self._build_url("storage", "download", object_name)

        logger.info(f"Downloading object '{object_name}'")
        response = self.session.get(
            url,
            headers=self.headers,
            timeout=self.timeout * 3,  # Longer timeout for downloads
            stream=True
        )

        # Check for errors but don't try to parse JSON
        if not response.ok:
            try:
                error_data = response.json()
                error_message = error_data.get("detail") or error_data.get("message") or "Download failed"
            except ValueError:
                error_message = response.text or "Download failed"

            if response.status_code == 404:
                raise ZeroDBNotFoundError(f"Object not found: {object_name}")
            else:
                raise ZeroDBError(f"Download failed ({response.status_code}): {error_message}")

        content = response.content
        logger.info(f"Object '{object_name}' downloaded successfully ({len(content)} bytes)")

        if save_path:
            with open(save_path, "wb") as f:
                f.write(content)
            logger.info(f"Object saved to '{save_path}'")
            return save_path

        return content

    def delete_object(
        self,
        object_name: str
    ) -> Dict[str, Any]:
        """
        Delete a file from ZeroDB object storage

        Args:
            object_name: Name of the object to delete

        Returns:
            Deletion confirmation

        Raises:
            ZeroDBNotFoundError: If object doesn't exist
            ZeroDBError: If deletion fails
        """
        url = self._build_url("storage", "delete", object_name)

        logger.info(f"Deleting object '{object_name}'")
        response = self.session.delete(
            url,
            headers=self.headers,
            timeout=self.timeout
        )

        result = self._handle_response(response)
        logger.info(f"Object '{object_name}' deleted successfully")
        return result

    def list_objects(
        self,
        prefix: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List objects in storage

        Args:
            prefix: Optional prefix to filter objects
            limit: Maximum number of objects to return
            offset: Number of objects to skip

        Returns:
            List of objects with metadata

        Raises:
            ZeroDBError: If listing fails
        """
        url = self._build_url("storage", "list")

        params = {
            "limit": limit,
            "offset": offset
        }

        if prefix:
            params["prefix"] = prefix

        logger.info(f"Listing objects (prefix='{prefix}', limit={limit})")
        response = self.session.get(
            url,
            params=params,
            headers=self.headers,
            timeout=self.timeout
        )

        result = self._handle_response(response)
        object_count = len(result.get("objects", []))
        logger.info(f"Listed {object_count} objects")
        return result

    def close(self):
        """Close the session and clean up resources"""
        if hasattr(self, 'session'):
            self.session.close()
            logger.info("ZeroDBClient session closed")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Global client instance (singleton pattern)
_client_instance: Optional[ZeroDBClient] = None


def get_zerodb_client() -> ZeroDBClient:
    """
    Get or create the global ZeroDB client instance

    Returns:
        ZeroDBClient instance
    """
    global _client_instance

    if _client_instance is None:
        _client_instance = ZeroDBClient()

    return _client_instance


# Convenience alias for backward compatibility
zerodb_client = get_zerodb_client()
