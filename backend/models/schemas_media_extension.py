"""
Extended Media Asset Schemas for Cloudflare Stream Integration

This module contains enhanced enums and schema extensions for the MediaAsset model
to support Cloudflare Stream VOD functionality. Import these into schemas.py.
"""

from enum import Enum

class MediaAssetStatus(str, Enum):
    """Media asset processing status"""
    UPLOADING = "uploading"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class MediaAccessLevel(str, Enum):
    """Media access control levels"""
    PUBLIC = "public"
    MEMBERS_ONLY = "members_only"
    TIER_SPECIFIC = "tier_specific"
