"""
BeeHiiv Service - Newsletter and Email List Management

This service integrates with the BeeHiiv API to manage newsletter subscriptions,
publications, and email list operations.

API Documentation: https://developers.beehiiv.com/docs/v2/
Rate Limit: 1000 requests/hour
"""

import os
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class BeeHiivRateLimitError(Exception):
    """Raised when API rate limit is exceeded"""
    pass


class BeeHiivAPIError(Exception):
    """Raised when BeeHiiv API returns an error"""
    pass


class BeeHiivService:
    """
    BeeHiiv API Integration Service

    Handles subscriber management, publication creation, and newsletter sending.
    Implements rate limiting, retry logic, and error handling.
    """

    BASE_URL = "https://api.beehiiv.com/v2"
    RATE_LIMIT_PER_HOUR = 1000
    MAX_RETRIES = 3
    BACKOFF_FACTOR = 2  # Exponential backoff: 2, 4, 8 seconds

    def __init__(
        self,
        api_key: Optional[str] = None,
        publication_id: Optional[str] = None
    ):
        """
        Initialize BeeHiiv service

        Args:
            api_key: BeeHiiv API key (defaults to BEEHIIV_API_KEY env var)
            publication_id: BeeHiiv publication ID (defaults to BEEHIIV_PUBLICATION_ID env var)
        """
        self.api_key = api_key if api_key is not None else os.getenv("BEEHIIV_API_KEY")
        self.publication_id = publication_id if publication_id is not None else os.getenv("BEEHIIV_PUBLICATION_ID")

        if not self.api_key:
            raise ValueError("BeeHiiv API key is required. Set BEEHIIV_API_KEY environment variable.")

        # Initialize session with retry logic
        self.session = self._create_session()

        # Rate limiting tracking
        self._request_timestamps: List[float] = []

    def _create_session(self) -> requests.Session:
        """
        Create requests session with retry logic and exponential backoff

        Returns:
            Configured requests.Session object
        """
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=self.MAX_RETRIES,
            backoff_factor=self.BACKOFF_FACTOR,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Set default headers
        session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

        return session

    def _check_rate_limit(self):
        """
        Check and enforce rate limiting (1000 requests/hour)

        Raises:
            BeeHiivRateLimitError: If rate limit would be exceeded
        """
        current_time = time.time()
        one_hour_ago = current_time - 3600

        # Remove timestamps older than 1 hour
        self._request_timestamps = [
            ts for ts in self._request_timestamps if ts > one_hour_ago
        ]

        # Check if we've hit the rate limit
        if len(self._request_timestamps) >= self.RATE_LIMIT_PER_HOUR:
            oldest_request = min(self._request_timestamps)
            wait_time = 3600 - (current_time - oldest_request)
            raise BeeHiivRateLimitError(
                f"Rate limit exceeded. Please wait {wait_time:.0f} seconds."
            )

        # Record this request
        self._request_timestamps.append(current_time)

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to BeeHiiv API with rate limiting and error handling

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            data: Request body data
            params: Query parameters

        Returns:
            Response data as dictionary

        Raises:
            BeeHiivRateLimitError: If rate limit exceeded
            BeeHiivAPIError: If API returns an error
        """
        # Enforce rate limiting
        self._check_rate_limit()

        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"

        try:
            response = self.session.request(
                method=method.upper(),
                url=url,
                json=data,
                params=params,
                timeout=30
            )

            # Log request details
            logger.info(f"BeeHiiv API {method} {endpoint} - Status: {response.status_code}")

            # Handle rate limiting response
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                raise BeeHiivRateLimitError(
                    f"Rate limit exceeded. Retry after {retry_after} seconds."
                )

            # Raise for HTTP errors
            response.raise_for_status()

            # Return JSON response
            return response.json() if response.content else {}

        except requests.exceptions.HTTPError as e:
            if hasattr(e, 'response') and e.response is not None:
                error_msg = f"BeeHiiv API error: {e.response.status_code}"
                try:
                    error_data = e.response.json()
                    error_msg += f" - {error_data.get('message', str(error_data))}"
                except:
                    error_msg += f" - {e.response.text}"
            else:
                error_msg = f"BeeHiiv API error: {str(e)}"

            logger.error(error_msg)
            raise BeeHiivAPIError(error_msg)

        except requests.exceptions.RequestException as e:
            logger.error(f"BeeHiiv API request failed: {str(e)}")
            raise BeeHiivAPIError(f"Request failed: {str(e)}")

    # ========================================================================
    # SUBSCRIBER MANAGEMENT
    # ========================================================================

    def add_subscriber(
        self,
        email: str,
        name: Optional[str] = None,
        list_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        reactivate_existing: bool = True
    ) -> Dict[str, Any]:
        """
        Add a subscriber to an email list

        Args:
            email: Subscriber email address
            name: Subscriber full name
            list_id: Email list ID (optional, uses default publication)
            metadata: Custom metadata for the subscriber
            reactivate_existing: Reactivate if subscriber exists and is inactive

        Returns:
            Subscriber data
        """
        data = {
            "email": email.lower().strip(),
            "reactivate_existing": reactivate_existing,
            "send_welcome_email": True,
            "utm_source": "wwmaa_platform",
            "utm_medium": "api"
        }

        if name:
            data["name"] = name

        if metadata:
            data["custom_fields"] = metadata

        endpoint = f"publications/{self.publication_id}/subscriptions"

        return self._make_request("POST", endpoint, data=data)

    def remove_subscriber(
        self,
        email: str,
        list_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Remove a subscriber from an email list (unsubscribe)

        Args:
            email: Subscriber email address
            list_id: Email list ID (optional)

        Returns:
            Response data
        """
        # BeeHiiv uses email as the identifier for unsubscription
        endpoint = f"publications/{self.publication_id}/subscriptions/{email}"

        return self._make_request("DELETE", endpoint)

    def update_subscriber(
        self,
        email: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update subscriber information

        Args:
            email: Subscriber email address
            updates: Dictionary of fields to update (name, custom_fields, etc.)

        Returns:
            Updated subscriber data
        """
        endpoint = f"publications/{self.publication_id}/subscriptions/{email}"

        return self._make_request("PATCH", endpoint, data=updates)

    def get_subscriber(self, email: str) -> Dict[str, Any]:
        """
        Get subscriber details by email

        Args:
            email: Subscriber email address

        Returns:
            Subscriber data
        """
        endpoint = f"publications/{self.publication_id}/subscriptions/{email}"

        return self._make_request("GET", endpoint)

    def list_subscribers(
        self,
        list_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        List subscribers with optional filtering

        Args:
            list_id: Email list ID (optional)
            filters: Filter parameters (status, created_after, etc.)
            page: Page number for pagination
            limit: Number of results per page (max 100)

        Returns:
            Paginated subscriber list
        """
        params = {
            "page": page,
            "limit": min(limit, 100)
        }

        if filters:
            params.update(filters)

        endpoint = f"publications/{self.publication_id}/subscriptions"

        return self._make_request("GET", endpoint, params=params)

    # ========================================================================
    # PUBLICATION MANAGEMENT
    # ========================================================================

    def create_publication(
        self,
        title: str,
        content: str,
        subject: Optional[str] = None,
        preview_text: Optional[str] = None,
        content_tags: Optional[List[str]] = None,
        status: str = "draft"
    ) -> Dict[str, Any]:
        """
        Create a newsletter publication

        Args:
            title: Publication title
            content: Email content (HTML supported)
            subject: Email subject line (defaults to title)
            preview_text: Preview text for email clients
            content_tags: List of content tags
            status: Publication status (draft/confirmed)

        Returns:
            Publication data
        """
        data = {
            "title": title,
            "content": content,
            "status": status
        }

        if subject:
            data["subject"] = subject
        else:
            data["subject"] = title

        if preview_text:
            data["preview_text"] = preview_text

        if content_tags:
            data["content_tags"] = content_tags

        endpoint = f"publications/{self.publication_id}/posts"

        return self._make_request("POST", endpoint, data=data)

    def get_publication(self, post_id: str) -> Dict[str, Any]:
        """
        Get publication details

        Args:
            post_id: Publication/post ID

        Returns:
            Publication data
        """
        endpoint = f"publications/{self.publication_id}/posts/{post_id}"

        return self._make_request("GET", endpoint)

    def list_publications(
        self,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        List all publications with filtering

        Args:
            filters: Filter parameters (status, created_after, etc.)
            page: Page number for pagination
            limit: Number of results per page

        Returns:
            Paginated publication list
        """
        params = {
            "page": page,
            "limit": min(limit, 100)
        }

        if filters:
            params.update(filters)

        endpoint = f"publications/{self.publication_id}/posts"

        return self._make_request("GET", endpoint, params=params)

    def send_newsletter(
        self,
        post_id: str,
        send_to: str = "all"
    ) -> Dict[str, Any]:
        """
        Send newsletter to subscribers

        Args:
            post_id: Publication/post ID
            send_to: Target audience (all/free/premium)

        Returns:
            Send confirmation data
        """
        data = {
            "status": "confirmed",  # Confirms and sends the post
            "audience": send_to
        }

        endpoint = f"publications/{self.publication_id}/posts/{post_id}"

        return self._make_request("PATCH", endpoint, data=data)

    # ========================================================================
    # ANALYTICS & STATS
    # ========================================================================

    def get_subscriber_stats(self) -> Dict[str, Any]:
        """
        Get subscriber statistics for the publication

        Returns:
            Subscriber stats (total, active, growth, etc.)
        """
        endpoint = f"publications/{self.publication_id}/stats/subscriptions"

        return self._make_request("GET", endpoint)

    def get_publication_stats(self, post_id: str) -> Dict[str, Any]:
        """
        Get statistics for a specific publication

        Args:
            post_id: Publication/post ID

        Returns:
            Publication stats (opens, clicks, etc.)
        """
        endpoint = f"publications/{self.publication_id}/posts/{post_id}/stats"

        return self._make_request("GET", endpoint)

    # ========================================================================
    # VALIDATION & TESTING
    # ========================================================================

    def validate_api_key(self) -> bool:
        """
        Validate API key by making a test request

        Returns:
            True if API key is valid, False otherwise
        """
        try:
            endpoint = f"publications/{self.publication_id}"
            self._make_request("GET", endpoint)
            return True
        except BeeHiivAPIError:
            return False

    def send_test_email(
        self,
        email: str,
        subject: str,
        content: str
    ) -> Dict[str, Any]:
        """
        Send a test email (useful for setup verification)

        Args:
            email: Test recipient email
            subject: Email subject
            content: Email content (HTML supported)

        Returns:
            Send confirmation
        """
        # Create a draft post
        post = self.create_publication(
            title="Test Email",
            subject=subject,
            content=content,
            status="draft"
        )

        # Send test
        endpoint = f"publications/{self.publication_id}/posts/{post['data']['id']}/send_test"

        return self._make_request("POST", endpoint, data={"email": email})
