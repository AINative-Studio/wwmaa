"""
External API Performance Tracker

Provides utilities for tracking external API call performance for services like:
- Stripe (payment processing)
- BeeHiiv (newsletter management)
- Cloudflare (video/streaming)
- AI Registry (LLM orchestration)
"""

import time
import logging
from typing import Any, Callable, Dict, Optional
from functools import wraps
from contextlib import contextmanager

from backend.observability.metrics import track_external_api_call

logger = logging.getLogger(__name__)


class ExternalAPITracker:
    """
    Tracker for external API calls with automatic metrics collection.

    Tracks latency, throughput, and error rates for external services.
    """

    @staticmethod
    @contextmanager
    def track_stripe_call(operation: str):
        """
        Track a Stripe API call.

        Args:
            operation: Operation name (create_payment, create_subscription, etc.)

        Example:
            with ExternalAPITracker.track_stripe_call("create_payment"):
                stripe.PaymentIntent.create(...)
        """
        with track_external_api_call("stripe", operation):
            yield

    @staticmethod
    @contextmanager
    def track_beehiiv_call(operation: str):
        """
        Track a BeeHiiv API call.

        Args:
            operation: Operation name (get_subscriber, create_subscriber, etc.)

        Example:
            with ExternalAPITracker.track_beehiiv_call("create_subscriber"):
                beehiiv_service.create_subscriber(...)
        """
        with track_external_api_call("beehiiv", operation):
            yield

    @staticmethod
    @contextmanager
    def track_cloudflare_call(operation: str):
        """
        Track a Cloudflare API call.

        Args:
            operation: Operation name (upload_video, create_stream, etc.)

        Example:
            with ExternalAPITracker.track_cloudflare_call("upload_video"):
                cloudflare_service.upload_video(...)
        """
        with track_external_api_call("cloudflare", operation):
            yield

    @staticmethod
    @contextmanager
    def track_ai_registry_call(operation: str):
        """
        Track an AI Registry API call.

        Args:
            operation: Operation name (completion, embedding, classification, etc.)

        Example:
            with ExternalAPITracker.track_ai_registry_call("completion"):
                ai_registry.create_completion(...)
        """
        with track_external_api_call("ai_registry", operation):
            yield

    @staticmethod
    @contextmanager
    def track_openai_call(operation: str):
        """
        Track an OpenAI API call.

        Args:
            operation: Operation name (embedding, completion, etc.)

        Example:
            with ExternalAPITracker.track_openai_call("embedding"):
                openai.Embedding.create(...)
        """
        with track_external_api_call("openai", operation):
            yield

    @staticmethod
    def track_api_call(service: str, operation: str):
        """
        Generic decorator to track any external API call.

        Args:
            service: Service name
            operation: Operation name

        Returns:
            Decorator function

        Example:
            @ExternalAPITracker.track_api_call("stripe", "create_customer")
            def create_stripe_customer(email: str):
                return stripe.Customer.create(email=email)
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                with track_external_api_call(service, operation):
                    return func(*args, **kwargs)

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                with track_external_api_call(service, operation):
                    return await func(*args, **kwargs)

            # Return appropriate wrapper based on function type
            if hasattr(func, "__await__") or hasattr(func, "__aiter__"):
                return async_wrapper
            return sync_wrapper

        return decorator


# Convenience functions for specific services

def track_stripe(operation: str):
    """
    Decorator for Stripe API calls.

    Args:
        operation: Operation name

    Example:
        @track_stripe("create_payment")
        def create_payment():
            ...
    """
    return ExternalAPITracker.track_api_call("stripe", operation)


def track_beehiiv(operation: str):
    """
    Decorator for BeeHiiv API calls.

    Args:
        operation: Operation name

    Example:
        @track_beehiiv("create_subscriber")
        async def create_subscriber():
            ...
    """
    return ExternalAPITracker.track_api_call("beehiiv", operation)


def track_cloudflare(operation: str):
    """
    Decorator for Cloudflare API calls.

    Args:
        operation: Operation name

    Example:
        @track_cloudflare("upload_video")
        def upload_video():
            ...
    """
    return ExternalAPITracker.track_api_call("cloudflare", operation)


def track_ai_registry(operation: str):
    """
    Decorator for AI Registry API calls.

    Args:
        operation: Operation name

    Example:
        @track_ai_registry("completion")
        async def create_completion():
            ...
    """
    return ExternalAPITracker.track_api_call("ai_registry", operation)


def track_openai(operation: str):
    """
    Decorator for OpenAI API calls.

    Args:
        operation: Operation name

    Example:
        @track_openai("embedding")
        def create_embedding():
            ...
    """
    return ExternalAPITracker.track_api_call("openai", operation)
