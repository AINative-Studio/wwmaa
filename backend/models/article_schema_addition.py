# ============================================================================
# ARTICLES COLLECTION - Blog Posts from BeeHiiv
# To be added to schemas.py before MEDIA_ASSETS section
# ============================================================================

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
from uuid import UUID


class ArticleAuthor(BaseModel):
    """Article author information"""
    model_config = ConfigDict(use_enum_values=True)

    name: str = Field(..., min_length=1, max_length=200, description="Author name")
    email: Optional[EmailStr] = Field(None, description="Author email")
    avatar_url: Optional[str] = Field(None, description="Author avatar URL")
    bio: Optional[str] = Field(None, max_length=1000, description="Author bio")


class ArticleSEOMetadata(BaseModel):
    """SEO metadata for articles"""
    model_config = ConfigDict(use_enum_values=True)

    meta_title: Optional[str] = Field(None, max_length=200, description="Meta title (override article title)")
    meta_description: Optional[str] = Field(None, max_length=500, description="Meta description")
    og_title: Optional[str] = Field(None, max_length=200, description="Open Graph title")
    og_description: Optional[str] = Field(None, max_length=500, description="Open Graph description")
    og_image: Optional[str] = Field(None, description="Open Graph image URL")
    twitter_card: Optional[str] = Field(None, max_length=50, description="Twitter card type (summary/summary_large_image)")
    twitter_title: Optional[str] = Field(None, max_length=200, description="Twitter title")
    twitter_description: Optional[str] = Field(None, max_length=500, description="Twitter description")
    twitter_image: Optional[str] = Field(None, description="Twitter image URL")
    keywords: List[str] = Field(default_factory=list, description="SEO keywords")
    canonical_url: Optional[str] = Field(None, description="Canonical URL")


class Article(BaseDocument):
    """
    Blog post/article synced from BeeHiiv

    This model stores blog content synced from BeeHiiv via webhooks.
    Posts are indexed for search and displayed on the website blog.
    """
    # BeeHiiv Integration
    beehiiv_post_id: str = Field(..., min_length=1, max_length=200, description="BeeHiiv post ID (unique)")
    beehiiv_url: Optional[str] = Field(None, description="Canonical BeeHiiv URL")

    # Content
    title: str = Field(..., min_length=1, max_length=500, description="Article title")
    slug: str = Field(..., min_length=1, max_length=300, description="URL-friendly slug (unique)")
    excerpt: Optional[str] = Field(None, max_length=1000, description="Short excerpt/summary")
    content: str = Field(..., min_length=1, description="Full article content (HTML or Markdown)")
    content_format: str = Field(default="html", max_length=20, description="Content format (html/markdown)")

    # Author
    author: ArticleAuthor = Field(..., description="Article author information")

    # Media
    featured_image_url: Optional[str] = Field(None, description="Featured image URL (stored in ZeroDB)")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail URL (300x200, stored in ZeroDB)")
    original_featured_image_url: Optional[str] = Field(None, description="Original BeeHiiv image URL")
    gallery_images: List[str] = Field(default_factory=list, description="Gallery image URLs")

    # Categorization
    category: Optional[str] = Field(None, max_length=100, description="Article category")
    tags: List[str] = Field(default_factory=list, description="Article tags")

    # Publishing
    status: ArticleStatus = Field(default=ArticleStatus.DRAFT, description="Article status")
    published_at: Optional[datetime] = Field(None, description="Publication timestamp")

    # Metrics
    view_count: int = Field(default=0, ge=0, description="Number of views")
    read_time_minutes: int = Field(default=0, ge=0, description="Estimated read time in minutes")

    # SEO
    seo_metadata: ArticleSEOMetadata = Field(
        default_factory=ArticleSEOMetadata,
        description="SEO metadata (title, description, OG tags)"
    )

    # Sync Information
    last_synced_at: datetime = Field(default_factory=datetime.utcnow, description="Last sync timestamp")
    sync_source: str = Field(default="beehiiv", max_length=50, description="Sync source (beehiiv/manual)")

    # Content Index Reference (for search)
    indexed_at: Optional[datetime] = Field(None, description="Search index timestamp")
    index_ids: List[UUID] = Field(default_factory=list, description="References to content_index documents")

    @field_validator('slug')
    @classmethod
    def validate_slug_format(cls, v):
        """Validate slug is URL-friendly (lowercase, hyphens, no special chars)"""
        import re
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError("Slug must contain only lowercase letters, numbers, and hyphens")
        return v

    @field_validator('read_time_minutes')
    @classmethod
    def validate_read_time_positive(cls, v):
        """Ensure read time is non-negative"""
        if v < 0:
            raise ValueError("read_time_minutes must be non-negative")
        return v
