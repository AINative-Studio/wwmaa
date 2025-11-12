"""
ZeroDB Client Wrapper Service

Provides a comprehensive Python client for interacting with ZeroDB API.
Includes CRUD operations, vector search, object storage, connection pooling,
retry logic with exponential backoff, and comprehensive error handling.

OpenTelemetry Instrumentation:
- All ZeroDB operations are traced with custom spans
- Span names follow pattern: zerodb.{operation}
- Attributes include: collection_name, document_id, operation_type, filter_query
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

# OpenTelemetry imports (gracefully handle if not available)
try:
    from backend.observability.tracing_utils import with_span, add_span_attributes, set_span_error
    _tracing_available = True
except ImportError:
    logger.debug("OpenTelemetry tracing not available for ZeroDB service")
    _tracing_available = False


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
        email: Optional[str] = None,
        password: Optional[str] = None,
        project_id: Optional[str] = None,
        timeout: int = 10,
        max_retries: int = 3,
        pool_connections: int = 10,
        pool_maxsize: int = 10
    ):
        """
        Initialize ZeroDB client with project-based API support

        Args:
            api_key: ZeroDB API key (defaults to settings.ZERODB_API_KEY) - used for legacy methods
            base_url: ZeroDB API base URL (defaults to settings.ZERODB_API_BASE_URL)
            email: ZeroDB account email (defaults to settings.ZERODB_EMAIL) - used for JWT authentication
            password: ZeroDB account password (defaults to settings.ZERODB_PASSWORD) - used for JWT authentication
            project_id: ZeroDB project ID (defaults to settings.ZERODB_PROJECT_ID)
            timeout: Request timeout in seconds (default: 10)
            max_retries: Maximum number of retries for failed requests (default: 3)
            pool_connections: Number of connection pool connections (default: 10)
            pool_maxsize: Maximum size of connection pool (default: 10)
        """
        self.api_key = api_key or settings.ZERODB_API_KEY
        self.base_url = (base_url or str(settings.ZERODB_API_BASE_URL)).rstrip('/')
        self.email = email or settings.ZERODB_EMAIL
        self.password = password or settings.ZERODB_PASSWORD
        self.project_id = project_id or getattr(settings, 'ZERODB_PROJECT_ID', None)
        self.timeout = timeout
        self._jwt_token = None
        self._jwt_token_expiry = None

        if not self.base_url:
            raise ZeroDBConnectionError("ZERODB_API_BASE_URL is required")

        # Configure session with connection pooling and retry logic
        self.session = self._create_session(max_retries, pool_connections, pool_maxsize)

        # Initialize headers (JWT token will be added when needed)
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # If using project-based API, authenticate to get JWT token
        if self.project_id and self.email and self.password:
            logger.info(f"ZeroDBClient initialized with project-based API (project_id: {self.project_id})")
            self._authenticate()
        elif self.api_key:
            # Legacy API key authentication
            self.headers["Authorization"] = f"Bearer {self.api_key}"
            logger.info(f"ZeroDBClient initialized with legacy API key authentication")
        else:
            logger.warning("ZeroDBClient initialized without authentication credentials")

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

    def _authenticate(self) -> None:
        """
        Authenticate with ZeroDB using email/password to get JWT token

        This method is called automatically during initialization if email and password are provided.
        The JWT token is stored and used for subsequent requests.

        Raises:
            ZeroDBAuthenticationError: If authentication fails
        """
        if not self.email or not self.password:
            raise ZeroDBAuthenticationError("Email and password are required for authentication")

        url = self._build_url("v1", "public", "auth", "login-json")

        payload = {
            "username": self.email,
            "password": self.password
        }

        logger.info(f"Authenticating with ZeroDB using email: {self.email}")

        try:
            response = self.session.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json", "Accept": "application/json"},
                timeout=self.timeout
            )

            response.raise_for_status()
            data = response.json()

            access_token = data.get("access_token")
            if not access_token:
                raise ZeroDBAuthenticationError("No access token returned from authentication")

            self._jwt_token = access_token
            self.headers["Authorization"] = f"Bearer {access_token}"

            logger.info("Successfully authenticated with ZeroDB")

        except requests.exceptions.HTTPError as e:
            error_message = f"Authentication failed: {e}"
            try:
                error_data = response.json()
                error_message = error_data.get("detail") or error_data.get("message") or error_message
            except ValueError:
                pass

            logger.error(error_message)
            raise ZeroDBAuthenticationError(error_message)

        except requests.exceptions.RequestException as e:
            logger.error(f"Authentication request failed: {e}")
            raise ZeroDBConnectionError(f"Failed to authenticate: {e}")

    def _ensure_authenticated(self) -> None:
        """
        Ensure the client is authenticated with a valid JWT token

        If the token has expired or is not present, re-authenticate.
        """
        if not self._jwt_token:
            if self.email and self.password:
                self._authenticate()
            else:
                raise ZeroDBAuthenticationError("No authentication token available")

    def _get_project_url(self, *parts: str) -> str:
        """
        Build a project-specific URL for the project-based API

        Args:
            *parts: URL path parts to append after the project ID

        Returns:
            Complete project URL string

        Example:
            _get_project_url("database", "tables", "users", "rows")
            -> https://api.ainative.studio/v1/projects/{project_id}/database/tables/users/rows
        """
        if not self.project_id:
            raise ZeroDBError("Project ID is required for project-based API calls")

        return self._build_url("v1", "projects", self.project_id, *parts)

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
        if not _tracing_available:
            return self._create_document_impl(collection, data, document_id)

        with with_span(
            "zerodb.create_document",
            attributes={
                "db.system": "zerodb",
                "db.operation": "create",
                "db.collection": collection,
                "document.id": document_id,
            }
        ) as span:
            try:
                result = self._create_document_impl(collection, data, document_id)
                add_span_attributes(**{"document.created_id": result.get("id")})
                return result
            except Exception as e:
                set_span_error(span, e)
                raise

    def _create_document_impl(
        self,
        collection: str,
        data: Dict[str, Any],
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Implementation of create_document"""
        # Use project-based API if project_id is configured
        if self.project_id:
            return self._create_row(collection, data, document_id)

        # Legacy collection-based API
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

    def _create_row(
        self,
        table_name: str,
        data: Dict[str, Any],
        row_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a row in a table using the project-based API

        Args:
            table_name: Name of the table
            data: Row data to create
            row_id: Optional custom row ID (not typically supported by project API)

        Returns:
            Created row formatted as document for backward compatibility
        """
        self._ensure_authenticated()
        url = self._get_project_url("database", "tables", table_name, "rows")

        # Project API requires row_data wrapper
        payload = {"row_data": data}

        logger.info(f"Creating row in table '{table_name}'")
        response = self.session.post(
            url,
            json=payload,
            headers=self.headers,
            timeout=self.timeout
        )

        result = self._handle_response(response)

        # Transform project API response to collection API format
        row_id = result.get("row_id")
        row_data = result.get("row_data", {})

        logger.info(f"Row created successfully with ID: {row_id}")

        return {
            "id": row_id,
            "data": row_data,
            "table_name": result.get("table_name")
        }

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
        Query documents from a collection/table with filters

        This method supports both legacy collection-based API and project-based table API.
        If project_id is configured, it uses the project-based API with tables/rows.

        Args:
            collection: Name of the collection or table
            filters: Filter criteria (e.g., {"status": "active", "age": {"$gte": 18}})
            limit: Maximum number of documents to return (default: 10)
            offset: Number of documents to skip (default: 0)
            sort: Sort criteria (e.g., {"created_at": "desc"})

        Returns:
            Query results with documents and metadata

        Raises:
            ZeroDBError: If query fails
        """
        # Use project-based API if project_id is configured
        if self.project_id:
            return self._query_rows(collection, filters, limit, offset, sort)

        # Legacy collection-based API
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

    def _query_rows(
        self,
        table_name: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        offset: int = 0,
        sort: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Query rows from a table using the project-based API

        Args:
            table_name: Name of the table
            filters: Filter criteria
            limit: Maximum number of rows to return
            offset: Number of rows to skip
            sort: Sort criteria

        Returns:
            Query results formatted as collection-style documents for backward compatibility

        Note:
            As of 2025-11-12, the ZeroDB project API endpoints are returning 500 errors
            with "super(): no arguments". This is a server-side issue that needs to be
            resolved on the ZeroDB platform. The implementation follows the correct API
            specification from the OpenAPI docs.
        """
        self._ensure_authenticated()
        url = self._get_project_url("database", "tables", table_name, "rows")

        # Note: The ZeroDB project API may not support filters in GET requests
        # For now, we'll fetch all rows and filter client-side if needed
        params = {}
        if limit:
            params["limit"] = limit
        if offset:
            params["offset"] = offset

        logger.info(f"Querying table '{table_name}' with filters: {filters}")
        logger.debug(f"Request URL: {url}")
        logger.debug(f"Request params: {params}")

        response = self.session.get(
            url,
            params=params,
            headers=self.headers,
            timeout=self.timeout
        )

        result = self._handle_response(response)

        # Transform project API response to collection API format for backward compatibility
        rows = result.get("rows", [])

        # Apply filters client-side if provided
        if filters:
            filtered_rows = []
            for row in rows:
                row_data = row.get("row_data", {})
                match = True
                for key, value in filters.items():
                    if row_data.get(key) != value:
                        match = False
                        break
                if match:
                    filtered_rows.append(row)
            rows = filtered_rows

        # Convert rows to documents format
        documents = []
        for row in rows:
            documents.append({
                "id": row.get("row_id"),
                "data": row.get("row_data", {})
            })

        logger.info(f"Query returned {len(documents)} documents")

        return {
            "documents": documents,
            "total": len(documents),
            "limit": limit,
            "offset": offset
        }

    def update_document(
        self,
        collection: str,
        document_id: str,
        data: Dict[str, Any],
        merge: bool = True
    ) -> Dict[str, Any]:
        """
        Update a document in a collection/table

        This method supports both legacy collection-based API and project-based table API.
        If project_id is configured, it uses the project-based API with tables/rows.

        Args:
            collection: Name of the collection or table
            document_id: ID of the document/row to update
            data: Updated document data
            merge: If True, merge with existing data; if False, replace entirely

        Returns:
            Updated document

        Raises:
            ZeroDBNotFoundError: If document doesn't exist
            ZeroDBValidationError: If data is invalid
            ZeroDBError: If update fails
        """
        # Use project-based API if project_id is configured
        if self.project_id:
            return self._update_row(collection, document_id, data, merge)

        # Legacy collection-based API
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

    def _update_row(
        self,
        table_name: str,
        row_id: str,
        data: Dict[str, Any],
        merge: bool = True
    ) -> Dict[str, Any]:
        """
        Update a row in a table using the project-based API

        Args:
            table_name: Name of the table
            row_id: ID of the row to update
            data: Updated row data
            merge: If True, merge with existing data; if False, replace entirely

        Returns:
            Updated row formatted as document for backward compatibility
        """
        self._ensure_authenticated()
        url = self._get_project_url("database", "tables", table_name, "rows", row_id)

        # If merge is True, fetch existing data first
        if merge:
            try:
                # Fetch existing row
                response = self.session.get(
                    url,
                    headers=self.headers,
                    timeout=self.timeout
                )
                existing = self._handle_response(response)
                existing_data = existing.get("row_data", {})

                # Merge data
                merged_data = {**existing_data, **data}
                payload = {"row_data": merged_data}
            except Exception as e:
                logger.warning(f"Failed to fetch existing row for merge: {e}")
                # If fetch fails, just use the new data
                payload = {"row_data": data}
        else:
            payload = {"row_data": data}

        logger.info(f"Updating row '{row_id}' in table '{table_name}'")
        response = self.session.put(
            url,
            json=payload,
            headers=self.headers,
            timeout=self.timeout
        )

        result = self._handle_response(response)

        # Transform project API response to collection API format
        logger.info(f"Row '{row_id}' updated successfully")

        return {
            "id": result.get("row_id", row_id),
            "data": result.get("row_data", data),
            "table_name": result.get("table_name")
        }

    def list_tables(self) -> Dict[str, Any]:
        """
        List all tables in the current project

        This method is only available when using the project-based API.

        Returns:
            List of table names and metadata

        Raises:
            ZeroDBError: If project_id is not configured or listing fails
        """
        if not self.project_id:
            raise ZeroDBError("Project ID is required to list tables")

        self._ensure_authenticated()
        url = self._get_project_url("database", "tables")

        logger.info(f"Listing tables for project '{self.project_id}'")

        response = self.session.get(
            url,
            headers=self.headers,
            timeout=self.timeout
        )

        result = self._handle_response(response)
        logger.info(f"Found {len(result.get('tables', []))} tables")

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

    def upload_object_from_bytes(
        self,
        key: str,
        content: bytes,
        content_type: str = "application/json",
        metadata: Optional[Dict[str, str]] = None,
        ttl: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Upload content from bytes to ZeroDB object storage

        Args:
            key: Object storage key (path)
            content: File content as bytes
            content_type: MIME type of the content
            metadata: Optional metadata for the object
            ttl: Time-to-live in seconds (for automatic expiry)

        Returns:
            Upload confirmation with object URL and metadata

        Raises:
            ZeroDBError: If upload fails
        """
        url = self._build_url("storage", "upload")

        import io

        # Create file-like object from bytes
        file_obj = io.BytesIO(content)

        # Prepare multipart form data
        files = {
            "file": (key.split("/")[-1], file_obj, content_type)
        }

        data = {
            "path": key  # Include path to store in specific location
        }

        if metadata:
            import json
            data["metadata"] = json.dumps(metadata)

        if ttl:
            data["ttl"] = str(ttl)

        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        logger.info(f"Uploading object to key '{key}' ({len(content)} bytes, ttl={ttl})")
        response = self.session.post(
            url,
            files=files,
            data=data,
            headers=headers,
            timeout=self.timeout * 3  # Longer timeout for uploads
        )

        result = self._handle_response(response)
        logger.info(f"Object uploaded successfully to '{key}'")
        return result

    def generate_signed_url(
        self,
        key: str,
        expiry_seconds: int = 3600,
        method: str = "GET"
    ) -> str:
        """
        Generate a signed URL for secure access to an object

        Args:
            key: Object storage key
            expiry_seconds: How long the URL should be valid (in seconds)
            method: HTTP method (GET, PUT, DELETE)

        Returns:
            Signed URL string

        Raises:
            ZeroDBError: If URL generation fails
        """
        url = self._build_url("storage", "signed-url")

        payload = {
            "key": key,
            "expiry_seconds": expiry_seconds,
            "method": method
        }

        logger.info(f"Generating signed URL for '{key}' (expiry={expiry_seconds}s)")
        response = self.session.post(
            url,
            json=payload,
            headers=self.headers,
            timeout=self.timeout
        )

        result = self._handle_response(response)
        signed_url = result.get("signed_url") or result.get("url")

        if not signed_url:
            # Fallback: construct direct URL
            signed_url = self._build_url("storage", "objects", key)
            logger.warning(f"No signed URL returned, using direct URL: {signed_url}")

        logger.info(f"Signed URL generated for '{key}'")
        return signed_url

    def get_object_metadata(self, key: str) -> Dict[str, Any]:
        """
        Get metadata for an object without downloading it

        Args:
            key: Object storage key

        Returns:
            Object metadata including size, content_type, created_at, etc.

        Raises:
            ZeroDBNotFoundError: If object doesn't exist
            ZeroDBError: If metadata retrieval fails
        """
        url = self._build_url("storage", "metadata", key)

        logger.info(f"Getting metadata for object '{key}'")
        response = self.session.get(
            url,
            headers=self.headers,
            timeout=self.timeout
        )

        result = self._handle_response(response)
        logger.info(f"Metadata retrieved for '{key}'")
        return result

    def delete_object_by_key(self, key: str) -> Dict[str, Any]:
        """
        Delete an object by its storage key (path)

        Args:
            key: Object storage key (path)

        Returns:
            Deletion confirmation

        Raises:
            ZeroDBNotFoundError: If object doesn't exist
            ZeroDBError: If deletion fails
        """
        url = self._build_url("storage", "objects", key)

        logger.info(f"Deleting object at key '{key}'")
        response = self.session.delete(
            url,
            headers=self.headers,
            timeout=self.timeout
        )

        result = self._handle_response(response)
        logger.info(f"Object at '{key}' deleted successfully")
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
