"""
Webhook Routes Package

This package contains webhook endpoint implementations for external services:
- Stripe payment webhooks
- Cloudflare Calls recording webhooks
"""

from . import cloudflare

__all__ = ["cloudflare"]
