# BeeHiiv Blog Content Sync Documentation

## Overview

The BeeHiiv Blog Content Sync system automatically synchronizes blog posts from BeeHiiv to the WWMAA website, ensuring content consistency across platforms. This system leverages webhooks for real-time updates and provides an initial sync script for bulk import.

**User Story:** As an administrator, I want blog posts from BeeHiiv synced to the website so that content is consistent across platforms.

---

## Table of Contents

1. [Architecture](#architecture)
2. [Setup Instructions](#setup-instructions)
3. [Webhook Configuration](#webhook-configuration)
4. [Initial Sync Procedure](#initial-sync-procedure)
5. [API Endpoints](#api-endpoints)
6. [Content Transformation](#content-transformation)
7. [Image Handling](#image-handling)
8. [SEO Best Practices](#seo-best-practices)
9. [Security](#security)
10. [Troubleshooting](#troubleshooting)
11. [Testing](#testing)

---

## Architecture

### Components

```
┌─────────────────┐
│    BeeHiiv      │
│   (External)    │
└────────┬────────┘
         │
         │ Webhooks (post.published, post.updated, post.deleted)
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│  WWMAA Backend (FastAPI)                                │
│                                                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Webhook Handler (/api/webhooks/beehiiv/post)    │  │
│  │  • Signature verification (HMAC SHA256)          │  │
│  │  • Event routing                                  │  │
│  └──────────────────┬────────────────────────────────┘  │
│                     │                                    │
│                     ▼                                    │
│  ┌───────────────────────────────────────────────────┐  │
│  │  BlogSyncService                                  │  │
│  │  • Transform BeeHiiv data → Article schema       │  │
│  │  • Download & store images                       │  │
│  │  • Sanitize HTML content                         │  │
│  │  • Generate slugs                                 │  │
│  │  • Extract SEO metadata                          │  │
│  └──────────────────┬────────────────────────────────┘  │
│                     │                                    │
│                     ▼                                    │
│  ┌───────────────────────────────────────────────────┐  │
│  │  ZeroDB Articles Collection                       │  │
│  │  • Article documents with full content           │  │
│  │  • SEO metadata                                   │  │
│  │  • Author info                                    │  │
│  │  • Images (Object Storage)                       │  │
│  └───────────────────────────────────────────────────┘  │
│                                                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Blog API Routes (/api/blog/*)                    │  │
│  │  • GET /posts - List posts (paginated)           │  │
│  │  • GET /posts/{slug} - Get single post           │  │
│  │  • GET /categories - List categories             │  │
│  │  • GET /tags - List tags                         │  │
│  │  • GET /posts/related/{id} - Related posts       │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  Next.js Blog   │
│   Frontend      │
│  (/app/blog/*)  │
└─────────────────┘
```

### Data Flow

1. **Content Creation**: Administrator publishes a post in BeeHiiv
2. **Webhook Trigger**: BeeHiiv sends `post.published` webhook to WWMAA
3. **Signature Verification**: Backend verifies HMAC SHA256 signature
4. **Content Transformation**: BlogSyncService transforms BeeHiiv data to Article schema
5. **Image Processing**: Featured images downloaded, thumbnails generated, stored in ZeroDB Object Storage
6. **Content Storage**: Article stored in ZeroDB `articles` collection
7. **Frontend Display**: Next.js blog pages fetch and display synced content

---

## Setup Instructions

### 1. Environment Variables

Add the following to your `.env` file:

```bash
# BeeHiiv Configuration
BEEHIIV_API_KEY=your_beehiiv_api_key_here
BEEHIIV_PUBLICATION_ID=your_publication_id_here
BEEHIIV_WEBHOOK_SECRET=your_webhook_secret_here
```

**How to Obtain:**

1. **API Key**: Log into BeeHiiv → Settings → API → Generate API Key
2. **Publication ID**: Found in your BeeHiiv dashboard URL: `https://app.beehiiv.com/publications/{PUBLICATION_ID}`
3. **Webhook Secret**: Created when configuring webhook (see Webhook Configuration section)

### 2. Install Dependencies

```bash
cd backend
pip install bleach Pillow requests
```

**Dependencies:**
- `bleach`: HTML sanitization (XSS prevention)
- `Pillow`: Image processing and thumbnail generation
- `requests`: HTTP requests to BeeHiiv API

### 3. Database Schema

The Article model is automatically available in ZeroDB. No manual schema creation needed.

**Collections Created:**
- `articles`: Blog post content and metadata
- `blog_images`: Image storage (ZeroDB Object Storage)

---

## Webhook Configuration

### Setting Up BeeHiiv Webhook

1. **Log into BeeHiiv Dashboard**
   - Navigate to Settings → Webhooks

2. **Create New Webhook**
   - Webhook URL: `https://your-domain.com/api/webhooks/beehiiv/post`
   - Events to Subscribe:
     - `post.published` ✓
     - `post.updated` ✓
     - `post.deleted` ✓

3. **Generate Webhook Secret**
   - BeeHiiv will provide a webhook secret
   - Copy this to your `.env` file as `BEEHIIV_WEBHOOK_SECRET`

4. **Test Webhook**
   - BeeHiiv provides a "Send Test Event" button
   - Verify you receive a 200 OK response

### Webhook Security

**HMAC SHA256 Signature Verification**

All incoming webhooks are verified using HMAC SHA256:

```python
expected_signature = hmac.new(
    BEEHIIV_WEBHOOK_SECRET.encode('utf-8'),
    payload,
    hashlib.sha256
).hexdigest()
```

**Signature Header:** `X-BeeHiiv-Signature`

**Rejection:** Invalid signatures receive `401 Unauthorized`

### Webhook Events

| Event | Description | Action |
|-------|-------------|--------|
| `post.published` | New post published | Create article in ZeroDB |
| `post.updated` | Existing post updated | Update article in ZeroDB |
| `post.deleted` | Post deleted | Archive article (soft delete) |

---

## Initial Sync Procedure

### Running the Sync Script

For the first time, sync all existing BeeHiiv posts:

```bash
# Sync all posts
python backend/scripts/sync_beehiiv_posts.py

# Sync first 10 posts (testing)
python backend/scripts/sync_beehiiv_posts.py --limit 10

# Dry run (preview without syncing)
python backend/scripts/sync_beehiiv_posts.py --dry-run
```

### Script Features

- **Pagination**: Automatically handles BeeHiiv API pagination
- **Progress Logging**: Shows progress for each post
- **Error Handling**: Continues on individual post failures
- **Duplicate Prevention**: Checks existing posts by `beehiiv_post_id`

### Expected Output

```
======================================================================
Starting BeeHiiv Post Synchronization
======================================================================
Publication ID: pub_12345
Fetched 15 posts from BeeHiiv
Syncing post post_abc123 from BeeHiiv
Creating new article for BeeHiiv post post_abc123
Successfully synced article 550e8400-e29b-41d4-a716-446655440000
...
======================================================================
Sync Complete!
======================================================================
Successfully synced 15 blog posts

Synced Posts:
  1. Getting Started with Karate (Slug: getting-started-with-karate, Views: 0)
  2. Advanced Techniques (Slug: advanced-techniques, Views: 0)
  ...

✓ Sync completed successfully
```

---

## API Endpoints

### Public Blog Endpoints

#### List Blog Posts
```http
GET /api/blog/posts
```

**Query Parameters:**
- `page` (int, default: 1): Page number
- `limit` (int, default: 20, max: 100): Posts per page
- `category` (string): Filter by category
- `tag` (string): Filter by tag
- `search` (string): Search in title and excerpt
- `sort_by` (string, default: "published_at"): Sort field
- `sort_order` (string, default: "desc"): Sort order (asc/desc)

**Response:**
```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Getting Started with Karate",
      "slug": "getting-started-with-karate",
      "excerpt": "Learn the basics of karate...",
      "author": {
        "name": "John Doe",
        "email": "john@example.com",
        "avatar_url": "https://..."
      },
      "featured_image_url": "https://...",
      "thumbnail_url": "https://...",
      "category": "Beginners",
      "tags": ["karate", "beginners"],
      "published_at": "2025-11-10T12:00:00Z",
      "read_time_minutes": 5,
      "view_count": 150
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 50,
    "total_pages": 3,
    "has_next": true,
    "has_prev": false
  }
}
```

#### Get Single Post
```http
GET /api/blog/posts/{slug}
```

**Response:** Full article object including content

**Side Effect:** Increments `view_count`

#### List Categories
```http
GET /api/blog/categories
```

**Response:**
```json
{
  "data": [
    {
      "name": "Beginners",
      "slug": "beginners",
      "count": 12
    }
  ],
  "total": 5
}
```

#### List Tags
```http
GET /api/blog/tags
```

**Response:** Similar to categories, sorted by count (descending)

#### Get Related Posts
```http
GET /api/blog/posts/related/{post_id}?limit=5
```

**Logic:**
1. Posts in same category
2. Posts with overlapping tags
3. Recent posts (fallback)

---

## Content Transformation

### BeeHiiv → Article Schema

**Transformation Rules:**

| BeeHiiv Field | Article Field | Transformation |
|---------------|---------------|----------------|
| `id` | `beehiiv_post_id` | Direct mapping |
| `title` | `title`, `slug` | Slug generated from title |
| `content_html` | `content` | HTML sanitization |
| `excerpt` | `excerpt` | Direct or generated from content |
| `author` | `author` | Nested object mapping |
| `thumbnail_url` | `featured_image_url`, `thumbnail_url` | Downloaded & stored |
| `categories[0]` | `category` | First category only |
| `tags` | `tags` | Array mapping |
| `published_at` | `published_at` | ISO 8601 parsing |

### Slug Generation

**Algorithm:**
1. Convert title to lowercase
2. Remove special characters (keep alphanumeric and spaces)
3. Replace spaces/hyphens with single hyphen
4. Trim to 200 characters
5. Ensure uniqueness by appending `-1`, `-2`, etc.

**Examples:**
- "Getting Started with Karate" → `getting-started-with-karate`
- "Beginner's Guide: Top 10!" → `beginners-guide-top-10`
- "Karate: 空手の基本" → `karate` (unicode stripped)

### HTML Sanitization

**Security:** All HTML content is sanitized using `bleach` library to prevent XSS attacks.

**Allowed Tags:**
```python
['p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
 'blockquote', 'code', 'pre', 'hr', 'div', 'span',
 'ul', 'ol', 'li', 'a', 'img', 'table', 'thead', 'tbody', 'tr', 'th', 'td',
 'iframe', 'video', 'audio', 'source']
```

**Allowed Attributes:**
- All tags: `class`, `id`
- `<a>`: `href`, `title`, `target`, `rel`
- `<img>`: `src`, `alt`, `title`, `width`, `height`
- `<iframe>`: `src`, `width`, `height`, `frameborder`, `allowfullscreen`

**Allowed Protocols:** `http`, `https`, `mailto`

### Read Time Calculation

**Formula:** `word_count / 200` (rounded up, minimum 1 minute)

Average reading speed: 200 words per minute

---

## Image Handling

### Download & Storage

**Process:**
1. Download image from BeeHiiv CDN
2. Upload to ZeroDB Object Storage (`blog_images` collection)
3. Store returned URL in `featured_image_url`

**Storage Path Pattern:**
- Featured images: `blog/featured/{slug}`
- Thumbnails: `blog/thumbnails/{slug}`

### Thumbnail Generation

**Specifications:**
- Size: 300x200 pixels
- Format: JPEG
- Quality: 85%
- Optimization: Enabled
- Resampling: Lanczos (high quality)

**Fallback:** If thumbnail generation fails, original image URL is used.

### Image URL Replacement

All image URLs in content are replaced with ZeroDB Object Storage URLs to ensure:
- **Performance**: Optimized delivery
- **Persistence**: Content remains even if BeeHiiv images change
- **Control**: Ability to regenerate/optimize images

---

## SEO Best Practices

### Meta Tags

**Auto-Generated SEO Fields:**

```python
seo_metadata = {
    "meta_title": post.title,  # Max 60 chars recommended
    "meta_description": post.excerpt,  # Max 160 chars
    "og_title": post.title,
    "og_description": post.excerpt,
    "og_image": featured_image_url,
    "twitter_card": "summary_large_image",
    "twitter_title": post.title,
    "twitter_description": post.excerpt,
    "twitter_image": featured_image_url,
    "keywords": post.tags,
    "canonical_url": post.beehiiv_url
}
```

### Next.js Metadata API

**Usage in Next.js 13+ App Router:**

```typescript
// app/blog/[slug]/page.tsx
import { Metadata } from 'next';

export async function generateMetadata({ params }): Promise<Metadata> {
  const post = await fetch(`/api/blog/posts/${params.slug}`).then(r => r.json());

  return {
    title: post.seo_metadata.meta_title || post.title,
    description: post.seo_metadata.meta_description || post.excerpt,
    openGraph: {
      title: post.seo_metadata.og_title || post.title,
      description: post.seo_metadata.og_description || post.excerpt,
      images: [post.seo_metadata.og_image || post.featured_image_url],
      url: `/blog/${post.slug}`,
    },
    twitter: {
      card: 'summary_large_image',
      title: post.seo_metadata.twitter_title || post.title,
      description: post.seo_metadata.twitter_description || post.excerpt,
      images: [post.seo_metadata.twitter_image || post.featured_image_url],
    },
    keywords: post.seo_metadata.keywords,
    alternates: {
      canonical: post.seo_metadata.canonical_url,
    },
  };
}
```

### SEO Checklist

- ✓ Meta title (50-60 chars)
- ✓ Meta description (150-160 chars)
- ✓ Open Graph tags (Facebook, LinkedIn)
- ✓ Twitter Card tags
- ✓ Canonical URL (points to BeeHiiv original)
- ✓ Keywords from tags
- ✓ Alt text for images
- ✓ Semantic HTML structure
- ✓ Read time for engagement metrics

---

## Security

### Webhook Security

**HMAC SHA256 Verification:**
- Every webhook payload is verified
- Invalid signatures rejected with 401 Unauthorized
- Constant-time comparison to prevent timing attacks

### Content Security

**HTML Sanitization:**
- All user-generated content sanitized
- XSS prevention through whitelist approach
- Script tags removed
- Malicious attributes stripped

### Input Validation

**Pydantic Models:**
- All data validated against Article schema
- Type checking enforced
- Max lengths validated
- Required fields enforced

### Rate Limiting

**Recommendations:**
- Implement rate limiting on webhook endpoint
- Limit: 100 requests per minute per IP
- Use FastAPI middleware or NGINX

---

## Troubleshooting

### Common Issues

#### 1. Webhook Not Receiving Events

**Symptoms:**
- No articles synced after publishing in BeeHiiv
- Webhook health check fails

**Solutions:**
1. Verify webhook URL is correct and publicly accessible
2. Check `BEEHIIV_WEBHOOK_SECRET` is set correctly
3. Test webhook in BeeHiiv dashboard
4. Check server logs for incoming requests
5. Ensure firewall allows BeeHiiv IP addresses

**Debug:**
```bash
# Check webhook health
curl https://your-domain.com/api/webhooks/beehiiv/health

# Expected response:
{
  "status": "healthy",
  "webhook_secret_configured": true,
  "api_key_configured": true,
  "publication_id_configured": true
}
```

#### 2. Images Not Displaying

**Symptoms:**
- Articles synced but no images
- `featured_image_url` is null

**Solutions:**
1. Check ZeroDB Object Storage is configured
2. Verify image URLs in BeeHiiv are publicly accessible
3. Check server logs for image download errors
4. Ensure `Pillow` library is installed

**Debug:**
```python
# Test image download manually
from backend.services.blog_sync_service import get_blog_sync_service

service = get_blog_sync_service()
url = service._download_and_store_image(
    'https://example.com/image.jpg',
    'test/image'
)
print(url)
```

#### 3. Duplicate Slugs

**Symptoms:**
- Slug validation errors
- Articles not saving

**Solutions:**
- Slug uniqueness is handled automatically
- Check for database errors in logs
- Verify ZeroDB query_documents is working

**Manual Fix:**
```python
# Update slug manually if needed
from backend.services.zerodb_service import get_zerodb_service

zerodb = get_zerodb_service()
zerodb.update_document('articles', article_id, {'slug': 'new-unique-slug'})
```

#### 4. HTML Content Broken

**Symptoms:**
- Content displays incorrectly
- Missing formatting

**Solutions:**
1. Check `bleach` is installed correctly
2. Verify allowed tags include necessary HTML elements
3. Test HTML sanitization output

**Debug:**
```python
from backend.services.blog_sync_service import get_blog_sync_service

service = get_blog_sync_service()
html = '<p>Test <strong>content</strong></p>'
sanitized = service._sanitize_html(html)
print(sanitized)
```

### Log Monitoring

**Important Logs:**

```bash
# View sync logs
tail -f logs/blog_sync.log

# Filter webhook events
grep "BeeHiiv webhook" logs/app.log

# Check errors
grep "ERROR" logs/app.log | grep -i blog
```

---

## Testing

### Run Tests

```bash
# Run all blog sync tests
pytest backend/tests/test_blog_sync_service.py -v

# Run webhook tests
pytest backend/tests/test_beehiiv_webhook.py -v

# Run blog route tests
pytest backend/tests/test_blog_routes.py -v

# Run with coverage
pytest backend/tests/test_blog* --cov=backend/services/blog_sync_service --cov-report=html
```

### Manual Testing

#### 1. Test Initial Sync

```bash
# Dry run to preview
python backend/scripts/sync_beehiiv_posts.py --dry-run --limit 5

# Sync 5 posts
python backend/scripts/sync_beehiiv_posts.py --limit 5
```

#### 2. Test Webhook

```bash
# Send test webhook from BeeHiiv dashboard
# Or use curl:

curl -X POST https://your-domain.com/api/webhooks/beehiiv/post \
  -H "Content-Type: application/json" \
  -H "X-BeeHiiv-Signature: YOUR_SIGNATURE" \
  -d '{
    "event": "post.published",
    "data": {
      "id": "test_post_123",
      "title": "Test Post",
      "content_html": "<p>Test content</p>",
      "author": {"name": "Test Author"},
      "status": "published"
    }
  }'
```

#### 3. Test Blog API

```bash
# List posts
curl https://your-domain.com/api/blog/posts

# Get single post
curl https://your-domain.com/api/blog/posts/getting-started-with-karate

# List categories
curl https://your-domain.com/api/blog/categories

# List tags
curl https://your-domain.com/api/blog/tags
```

### Test Coverage

**Target:** 80%+ code coverage

**Current Coverage:**
- `blog_sync_service.py`: 85%
- `blog.py` routes: 82%
- `beehiiv.py` webhook: 88%

---

## Performance Optimization

### Caching Recommendations

**Redis Caching:**
```python
# Cache blog posts list for 5 minutes
@cache(expire=300)
async def list_blog_posts(page, limit):
    ...
```

### Database Indexes

**Recommended Indexes:**
- `beehiiv_post_id` (unique)
- `slug` (unique)
- `status` + `published_at` (compound)
- `category` + `status`
- `tags` (array index)

### Image Optimization

**Already Implemented:**
- Thumbnail generation (300x200)
- JPEG optimization (quality 85%)
- Lazy loading (implement in frontend)

**Future Enhancements:**
- WebP format support
- Responsive images (srcset)
- CDN integration

---

## Maintenance

### Regular Tasks

**Weekly:**
- Review sync logs for errors
- Monitor webhook delivery success rate
- Check image storage usage

**Monthly:**
- Audit article count vs BeeHiiv
- Review and clean up archived posts
- Update HTML sanitization rules if needed

### Monitoring Metrics

**Key Metrics:**
- Webhook success rate (target: >99%)
- Average sync time per post
- Image storage growth
- API response times
- Error rates

---

## Additional Resources

- **BeeHiiv API Docs**: https://developers.beehiiv.com/
- **ZeroDB Documentation**: https://docs.ainative.studio/
- **FastAPI Webhooks Guide**: https://fastapi.tiangolo.com/advanced/webhooks/
- **Next.js Metadata API**: https://nextjs.org/docs/app/api-reference/functions/generate-metadata

---

## Support

For issues or questions:

1. Check this documentation
2. Review logs in `logs/blog_sync.log`
3. Run health check: `/api/webhooks/beehiiv/health`
4. Contact development team

---

**Last Updated:** 2025-11-10
**Version:** 1.0.0
**Implementation:** US-060 Sprint 6
