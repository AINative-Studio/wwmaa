"""
Blog Sync Service for BeeHiiv Integration

Handles syncing blog posts from BeeHiiv to ZeroDB.
Processes webhook events and performs full synchronization.

Features:
- Sync single post from webhook events
- Full sync of all BeeHiiv posts
- Image download and storage to ZeroDB Object Storage
- HTML content sanitization
- Slug generation with duplicate handling
- Read time calculation
- SEO metadata extraction

BeeHiiv API Documentation: https://developers.beehiiv.com/
"""

import logging
import re
import hashlib
import hmac
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
import requests
from io import BytesIO
from PIL import Image

from backend.config import settings
from backend.services.zerodb_service import get_zerodb_client
from backend.models.schemas import (
    Article,
    ArticleAuthor,
    ArticleSEOMetadata,
    ArticleStatus
)


logger = logging.getLogger(__name__)


class BlogSyncError(Exception):
    """Base exception for blog sync errors"""
    pass


class BeeHiivAPIError(Exception):
    """BeeHiiv API request error"""
    pass


class ImageDownloadError(Exception):
    """Image download/processing error"""
    pass


class BlogSyncService:
    """
    Service for syncing blog posts from BeeHiiv to ZeroDB

    This service handles:
    - Webhook event processing (post.published, post.updated, post.deleted)
    - Full sync of all BeeHiiv posts
    - Image downloading and storage
    - Content transformation and sanitization
    - Slug generation and deduplication
    """

    def __init__(self):
        self.zerodb = get_zerodb_client()
        self.beehiiv_api_key = settings.BEEHIIV_API_KEY
        self.beehiiv_publication_id = settings.BEEHIIV_PUBLICATION_ID
        self.beehiiv_webhook_secret = settings.BEEHIIV_WEBHOOK_SECRET
        self.beehiiv_api_base = "https://api.beehiiv.com/v2"

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify BeeHiiv webhook signature using HMAC SHA256

        Args:
            payload: Raw request body bytes
            signature: Signature from webhook header

        Returns:
            True if signature is valid, False otherwise
        """
        if not self.beehiiv_webhook_secret:
            logger.warning("BEEHIIV_WEBHOOK_SECRET not configured, skipping verification")
            return True

        try:
            # Calculate expected signature
            expected_signature = hmac.new(
                self.beehiiv_webhook_secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()

            # Compare signatures (constant-time comparison)
            return hmac.compare_digest(expected_signature, signature)

        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False

    def sync_post(self, beehiiv_post_data: Dict[str, Any]) -> Article:
        """
        Sync a single post from BeeHiiv webhook data

        Args:
            beehiiv_post_data: Post data from BeeHiiv webhook

        Returns:
            Article model instance

        Raises:
            BlogSyncError: If sync fails
        """
        try:
            beehiiv_post_id = beehiiv_post_data.get('id')

            if not beehiiv_post_id:
                raise BlogSyncError("Missing post ID in webhook data")

            logger.info(f"Syncing post {beehiiv_post_id} from BeeHiiv")

            # Check if post already exists
            existing_article = self._get_article_by_beehiiv_id(beehiiv_post_id)

            # Transform BeeHiiv data to Article schema
            article_data = self.transform_beehiiv_to_article(beehiiv_post_data)

            if existing_article:
                # Update existing article
                logger.info(f"Updating existing article {existing_article.id}")
                article = self.update_post(existing_article.id, article_data)
            else:
                # Create new article
                logger.info(f"Creating new article for BeeHiiv post {beehiiv_post_id}")

                # Ensure unique slug
                article_data['slug'] = self._ensure_unique_slug(article_data['slug'])

                # Create Article instance
                article = Article(**article_data)

                # Store in ZeroDB
                result = self.zerodb.create_document('articles', article.model_dump())
                article.id = UUID(result['id'])

            logger.info(f"Successfully synced article {article.id} (BeeHiiv ID: {beehiiv_post_id})")
            return article

        except Exception as e:
            logger.error(f"Error syncing post: {e}")
            raise BlogSyncError(f"Failed to sync post: {e}")

    def sync_all_posts(self, limit: Optional[int] = None) -> List[Article]:
        """
        Perform full sync of all BeeHiiv posts

        Args:
            limit: Maximum number of posts to sync (None for all)

        Returns:
            List of synced Article instances
        """
        try:
            logger.info("Starting full sync of BeeHiiv posts")

            # Fetch all posts from BeeHiiv API
            posts = self._fetch_all_posts_from_beehiiv(limit=limit)

            logger.info(f"Fetched {len(posts)} posts from BeeHiiv")

            synced_articles = []

            for post_data in posts:
                try:
                    article = self.sync_post(post_data)
                    synced_articles.append(article)
                except Exception as e:
                    logger.error(f"Error syncing post {post_data.get('id')}: {e}")
                    continue

            logger.info(f"Successfully synced {len(synced_articles)} articles")
            return synced_articles

        except Exception as e:
            logger.error(f"Error in full sync: {e}")
            raise BlogSyncError(f"Full sync failed: {e}")

    def fetch_post_from_beehiiv(self, post_id: str) -> Dict[str, Any]:
        """
        Fetch a single post from BeeHiiv API

        Args:
            post_id: BeeHiiv post ID

        Returns:
            Post data dictionary

        Raises:
            BeeHiivAPIError: If API request fails
        """
        try:
            url = f"{self.beehiiv_api_base}/publications/{self.beehiiv_publication_id}/posts/{post_id}"

            headers = {
                'Authorization': f'Bearer {self.beehiiv_api_key}',
                'Content-Type': 'application/json'
            }

            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            return data.get('data', data)

        except requests.RequestException as e:
            logger.error(f"BeeHiiv API error fetching post {post_id}: {e}")
            raise BeeHiivAPIError(f"Failed to fetch post from BeeHiiv: {e}")

    def transform_beehiiv_to_article(self, beehiiv_post: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform BeeHiiv post data to Article schema format

        Args:
            beehiiv_post: BeeHiiv post data

        Returns:
            Dictionary compatible with Article model
        """
        # Extract author information
        author_data = beehiiv_post.get('author', {})
        author = ArticleAuthor(
            name=author_data.get('name', 'Unknown Author'),
            email=author_data.get('email'),
            avatar_url=author_data.get('avatar_url'),
            bio=author_data.get('bio')
        )

        # Extract content
        content_html = beehiiv_post.get('content_html', beehiiv_post.get('content', ''))

        # Sanitize HTML content
        sanitized_content = self._sanitize_html(content_html)

        # Generate slug from title
        title = beehiiv_post.get('title', 'Untitled Post')
        slug = self._generate_slug(title)

        # Calculate read time
        read_time = self._calculate_read_time(sanitized_content)

        # Download and store images
        featured_image_url = None
        thumbnail_url = None
        original_featured_image = beehiiv_post.get('thumbnail_url') or beehiiv_post.get('featured_image_url')

        if original_featured_image:
            try:
                featured_image_url = self._download_and_store_image(
                    original_featured_image,
                    f"blog/featured/{slug}"
                )

                # Generate thumbnail
                thumbnail_url = self._generate_thumbnail(
                    original_featured_image,
                    f"blog/thumbnails/{slug}"
                )
            except Exception as e:
                logger.warning(f"Failed to download images: {e}")

        # Extract SEO metadata
        seo_metadata = self._extract_seo_metadata(beehiiv_post, title)

        # Determine status
        status = ArticleStatus.PUBLISHED if beehiiv_post.get('status') == 'published' else ArticleStatus.DRAFT

        # Parse published_at timestamp
        published_at = None
        if beehiiv_post.get('published_at'):
            try:
                published_at = datetime.fromisoformat(
                    beehiiv_post['published_at'].replace('Z', '+00:00')
                )
            except (ValueError, AttributeError):
                published_at = datetime.utcnow() if status == ArticleStatus.PUBLISHED else None

        return {
            'beehiiv_post_id': beehiiv_post.get('id'),
            'beehiiv_url': beehiiv_post.get('web_url'),
            'title': title,
            'slug': slug,
            'excerpt': beehiiv_post.get('excerpt') or self._generate_excerpt(sanitized_content),
            'content': sanitized_content,
            'content_format': 'html',
            'author': author,
            'featured_image_url': featured_image_url,
            'thumbnail_url': thumbnail_url,
            'original_featured_image_url': original_featured_image,
            'gallery_images': [],
            'category': beehiiv_post.get('categories', [None])[0] if beehiiv_post.get('categories') else None,
            'tags': beehiiv_post.get('tags', []),
            'status': status,
            'published_at': published_at,
            'view_count': 0,
            'read_time_minutes': read_time,
            'seo_metadata': seo_metadata,
            'last_synced_at': datetime.utcnow(),
            'sync_source': 'beehiiv',
            'indexed_at': None,
            'index_ids': []
        }

    def update_post(self, article_id: UUID, updates: Dict[str, Any]) -> Article:
        """
        Update an existing article

        Args:
            article_id: Article UUID
            updates: Dictionary of fields to update

        Returns:
            Updated Article instance
        """
        try:
            # Remove fields that shouldn't be updated
            updates.pop('id', None)
            updates.pop('created_at', None)

            # Update timestamp
            updates['updated_at'] = datetime.utcnow()
            updates['last_synced_at'] = datetime.utcnow()

            # Update in ZeroDB
            self.zerodb.update_document('articles', str(article_id), updates)

            # Fetch updated article
            article_data = self.zerodb.get_document('articles', str(article_id))

            return Article(**article_data)

        except Exception as e:
            logger.error(f"Error updating article {article_id}: {e}")
            raise BlogSyncError(f"Failed to update article: {e}")

    def delete_post(self, article_id: UUID) -> bool:
        """
        Delete (archive) an article

        Args:
            article_id: Article UUID

        Returns:
            True if successful
        """
        try:
            # Soft delete by setting status to archived
            self.zerodb.update_document('articles', str(article_id), {
                'status': ArticleStatus.ARCHIVED,
                'updated_at': datetime.utcnow()
            })

            logger.info(f"Archived article {article_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting article {article_id}: {e}")
            return False

    # =========================================================================
    # PRIVATE HELPER METHODS
    # =========================================================================

    def _get_article_by_beehiiv_id(self, beehiiv_post_id: str) -> Optional[Article]:
        """Get article by BeeHiiv post ID"""
        try:
            results = self.zerodb.query_documents(
                'articles',
                {'beehiiv_post_id': beehiiv_post_id},
                limit=1
            )

            if results:
                return Article(**results[0])

            return None

        except Exception as e:
            logger.error(f"Error querying article: {e}")
            return None

    def _fetch_all_posts_from_beehiiv(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch all posts from BeeHiiv API with pagination"""
        try:
            url = f"{self.beehiiv_api_base}/publications/{self.beehiiv_publication_id}/posts"

            headers = {
                'Authorization': f'Bearer {self.beehiiv_api_key}',
                'Content-Type': 'application/json'
            }

            all_posts = []
            page = 1

            while True:
                params = {
                    'page': page,
                    'limit': min(limit - len(all_posts), 100) if limit else 100,
                    'status': 'published'
                }

                response = requests.get(url, headers=headers, params=params, timeout=30)
                response.raise_for_status()

                data = response.json()
                posts = data.get('data', [])

                if not posts:
                    break

                all_posts.extend(posts)

                if limit and len(all_posts) >= limit:
                    all_posts = all_posts[:limit]
                    break

                # Check if there are more pages
                if not data.get('has_more', False):
                    break

                page += 1

            return all_posts

        except requests.RequestException as e:
            logger.error(f"BeeHiiv API error: {e}")
            raise BeeHiivAPIError(f"Failed to fetch posts from BeeHiiv: {e}")

    def _generate_slug(self, title: str) -> str:
        """
        Generate URL-friendly slug from title

        Args:
            title: Article title

        Returns:
            URL-friendly slug
        """
        # Convert to lowercase
        slug = title.lower()

        # Remove special characters, keep alphanumeric and spaces
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)

        # Replace spaces and multiple hyphens with single hyphen
        slug = re.sub(r'[\s-]+', '-', slug)

        # Remove leading/trailing hyphens
        slug = slug.strip('-')

        # Limit length
        slug = slug[:200]

        return slug or 'untitled-post'

    def _ensure_unique_slug(self, slug: str, attempt: int = 0) -> str:
        """
        Ensure slug is unique by appending number if necessary

        Args:
            slug: Base slug
            attempt: Current attempt number

        Returns:
            Unique slug
        """
        test_slug = f"{slug}-{attempt}" if attempt > 0 else slug

        # Check if slug exists
        results = self.zerodb.query_documents(
            'articles',
            {'slug': test_slug},
            limit=1
        )

        if results:
            # Slug exists, try next number
            return self._ensure_unique_slug(slug, attempt + 1)

        return test_slug

    def _sanitize_html(self, html: str) -> str:
        """
        Sanitize HTML content to prevent XSS

        Uses bleach library to whitelist safe HTML tags and attributes

        Args:
            html: Raw HTML content

        Returns:
            Sanitized HTML
        """
        try:
            import bleach

            # Allowed HTML tags
            allowed_tags = [
                'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                'blockquote', 'code', 'pre', 'hr', 'div', 'span',
                'ul', 'ol', 'li', 'a', 'img', 'table', 'thead', 'tbody', 'tr', 'th', 'td',
                'iframe', 'video', 'audio', 'source'
            ]

            # Allowed attributes
            allowed_attrs = {
                '*': ['class', 'id'],
                'a': ['href', 'title', 'target', 'rel'],
                'img': ['src', 'alt', 'title', 'width', 'height'],
                'iframe': ['src', 'width', 'height', 'frameborder', 'allowfullscreen'],
                'video': ['src', 'width', 'height', 'controls', 'autoplay', 'loop'],
                'audio': ['src', 'controls', 'autoplay', 'loop'],
                'source': ['src', 'type']
            }

            # Allowed protocols for links and images
            allowed_protocols = ['http', 'https', 'mailto']

            cleaned = bleach.clean(
                html,
                tags=allowed_tags,
                attributes=allowed_attrs,
                protocols=allowed_protocols,
                strip=True
            )

            return cleaned

        except ImportError:
            logger.warning("bleach library not installed, skipping HTML sanitization")
            return html

    def _calculate_read_time(self, content: str) -> int:
        """
        Calculate estimated read time in minutes

        Assumes average reading speed of 200 words per minute

        Args:
            content: Article content (HTML or text)

        Returns:
            Read time in minutes (minimum 1)
        """
        # Strip HTML tags
        text = re.sub(r'<[^>]+>', '', content)

        # Count words
        words = len(text.split())

        # Calculate minutes (200 words per minute)
        minutes = max(1, round(words / 200))

        return minutes

    def _generate_excerpt(self, content: str, max_length: int = 300) -> str:
        """
        Generate excerpt from content

        Args:
            content: Full content
            max_length: Maximum excerpt length

        Returns:
            Excerpt text
        """
        # Strip HTML tags
        text = re.sub(r'<[^>]+>', '', content)

        # Clean whitespace
        text = ' '.join(text.split())

        # Truncate
        if len(text) > max_length:
            text = text[:max_length].rsplit(' ', 1)[0] + '...'

        return text

    def _download_and_store_image(self, image_url: str, storage_path: str) -> str:
        """
        Download image and store in ZeroDB Object Storage

        Args:
            image_url: Source image URL
            storage_path: Storage path in ZeroDB

        Returns:
            Stored image URL

        Raises:
            ImageDownloadError: If download or storage fails
        """
        try:
            # Download image
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()

            # Store in ZeroDB Object Storage
            # Note: This is a placeholder - actual implementation depends on ZeroDB Object Storage API
            stored_url = self.zerodb.upload_object(
                collection='blog_images',
                object_path=storage_path,
                data=response.content,
                content_type=response.headers.get('content-type', 'image/jpeg')
            )

            return stored_url

        except Exception as e:
            logger.error(f"Error downloading image {image_url}: {e}")
            raise ImageDownloadError(f"Failed to download and store image: {e}")

    def _generate_thumbnail(self, image_url: str, storage_path: str, size: tuple = (300, 200)) -> str:
        """
        Generate thumbnail from image

        Args:
            image_url: Source image URL
            storage_path: Storage path for thumbnail
            size: Thumbnail size (width, height)

        Returns:
            Thumbnail URL
        """
        try:
            # Download original image
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()

            # Open with PIL
            img = Image.open(BytesIO(response.content))

            # Generate thumbnail
            img.thumbnail(size, Image.Resampling.LANCZOS)

            # Save to bytes
            output = BytesIO()
            img.save(output, format='JPEG', quality=85, optimize=True)
            output.seek(0)

            # Store in ZeroDB
            thumbnail_url = self.zerodb.upload_object(
                collection='blog_images',
                object_path=storage_path,
                data=output.read(),
                content_type='image/jpeg'
            )

            return thumbnail_url

        except Exception as e:
            logger.warning(f"Error generating thumbnail: {e}")
            # Return original image URL as fallback
            return image_url

    def _extract_seo_metadata(self, beehiiv_post: Dict[str, Any], title: str) -> ArticleSEOMetadata:
        """
        Extract SEO metadata from BeeHiiv post

        Args:
            beehiiv_post: BeeHiiv post data
            title: Article title

        Returns:
            ArticleSEOMetadata instance
        """
        excerpt = beehiiv_post.get('excerpt', '')

        return ArticleSEOMetadata(
            meta_title=beehiiv_post.get('meta_title') or title,
            meta_description=beehiiv_post.get('meta_description') or excerpt,
            og_title=beehiiv_post.get('og_title') or title,
            og_description=beehiiv_post.get('og_description') or excerpt,
            og_image=beehiiv_post.get('og_image') or beehiiv_post.get('thumbnail_url'),
            twitter_card='summary_large_image',
            twitter_title=title,
            twitter_description=excerpt,
            twitter_image=beehiiv_post.get('thumbnail_url'),
            keywords=beehiiv_post.get('tags', []),
            canonical_url=beehiiv_post.get('web_url')
        )


# ============================================================================
# SERVICE SINGLETON
# ============================================================================

_blog_sync_service = None


def get_blog_sync_service() -> BlogSyncService:
    """Get or create BlogSyncService singleton instance"""
    global _blog_sync_service
    if _blog_sync_service is None:
        _blog_sync_service = BlogSyncService()
    return _blog_sync_service
