# Strapi CMS Setup Guide for WWMAA

## Overview

This guide covers the complete setup and usage of Strapi CMS for managing blog content in the WWMAA project. Strapi replaces BeeHiiv for blog content management, while BeeHiiv will continue to be used solely for email list management.

## Table of Contents

1. [Architecture](#architecture)
2. [Local Development Setup](#local-development-setup)
3. [Docker Setup](#docker-setup)
4. [Content Type Schema](#content-type-schema)
5. [API Access](#api-access)
6. [Environment Variables](#environment-variables)
7. [Admin Panel](#admin-panel)
8. [API Endpoints](#api-endpoints)
9. [Integration with Backend](#integration-with-backend)
10. [Production Deployment](#production-deployment)

---

## Architecture

### Components

- **Strapi CMS**: Headless CMS running on port 1337
- **SQLite**: Development database (local)
- **PostgreSQL**: Production database (Docker/Railway)
- **Article Content Type**: Custom content type for blog articles

### Port Configuration

- **Local Development**: Port 1337
- **Docker**: Port 1337 (exposed)
- **PostgreSQL**: Port 5433 (external), 5432 (internal)

---

## Local Development Setup

### Prerequisites

- Node.js 18+ or 20+
- npm 6+

### Installation Steps

The Strapi CMS is already installed in the `/cms` directory with all necessary configuration.

1. **Navigate to CMS directory**:
   ```bash
   cd cms
   ```

2. **Install dependencies** (if not already installed):
   ```bash
   npm install
   ```

3. **Configure environment variables**:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and update the security keys (optional for development):
   ```bash
   # Generate secure keys using:
   openssl rand -base64 32
   ```

4. **Start Strapi in development mode**:
   ```bash
   npm run develop
   ```

5. **Access the admin panel**:
   - URL: `http://localhost:1337/admin`
   - Create your admin account on first run

### Development Commands

```bash
# Start development server (with auto-reload)
npm run develop

# Start production server
npm run start

# Build production bundle
npm run build

# Clean cache and build files
npm run clean
```

---

## Docker Setup

### Running with Docker Compose

1. **Start all services**:
   ```bash
   docker-compose up -d
   ```

2. **Start only Strapi and database**:
   ```bash
   docker-compose up -d strapi strapi-db
   ```

3. **View logs**:
   ```bash
   docker-compose logs -f strapi
   ```

4. **Stop services**:
   ```bash
   docker-compose down
   ```

5. **Clean volumes** (WARNING: deletes data):
   ```bash
   docker-compose down -v
   ```

### Docker Services

#### Strapi Service
- **Container**: `wwmaa-strapi`
- **Port**: 1337
- **Database**: PostgreSQL (strapi-db)
- **Volumes**:
  - `./cms` → `/app` (code)
  - `strapi-uploads` → `/app/public/uploads` (media files)

#### PostgreSQL Service
- **Container**: `wwmaa-strapi-db`
- **Port**: 5433 (external), 5432 (internal)
- **Database**: `strapi`
- **User**: `strapi`
- **Volume**: `strapi-db-data` (persistent data)

---

## Content Type Schema

### Article Content Type

The Article content type is pre-configured with the following fields:

#### Fields

| Field Name | Type | Required | Description |
|------------|------|----------|-------------|
| `title` | String | Yes | Article title (max 255 chars) |
| `slug` | UID | Yes | URL-friendly identifier (auto-generated from title) |
| `excerpt` | Text | Yes | Short summary (max 500 chars) |
| `content` | Rich Text | Yes | Full article content with formatting |
| `author` | String | Yes | Author name (default: "WWMAA Team") |
| `published_at` | DateTime | No | Publication date/time |
| `featured_image` | Media | No | Featured image (images only) |
| `category` | Enumeration | Yes | Article category (see below) |
| `tags` | JSON | No | Article tags (array) |
| `meta_title` | String | No | SEO meta title (max 60 chars) |
| `meta_description` | Text | No | SEO meta description (max 160 chars) |
| `read_time` | Integer | No | Estimated reading time in minutes (default: 5) |
| `featured` | Boolean | No | Featured article flag (default: false) |

#### Categories

- AI & Technology
- Industry News
- Best Practices
- Case Studies
- Product Updates
- Thought Leadership

#### Draft and Publish

The Article content type supports **draft and publish** workflow:
- Articles can be saved as drafts
- Published articles are available via the API
- Draft articles are not returned by default API queries

### Schema Location

```
/cms/src/api/article/content-types/article/schema.json
```

---

## API Access

### Public Access Configuration

To allow public access to articles (required for frontend):

1. Go to **Settings** → **Users & Permissions Plugin** → **Roles** → **Public**
2. Under **Permissions** → **Article**:
   - Enable `find` (list articles)
   - Enable `findOne` (get single article)
3. Click **Save**

### API Token Creation

For backend API access (more secure):

1. Go to **Settings** → **API Tokens** → **Create new API Token**
2. Configure:
   - **Name**: "Backend API Token"
   - **Token duration**: Unlimited or set expiration
   - **Token type**: Read-only or Full access
3. Copy the generated token (shown only once!)
4. Add to backend `.env`:
   ```bash
   STRAPI_API_TOKEN=your_token_here
   ```

### Using API Tokens

Include the token in API requests:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  http://localhost:1337/api/articles
```

---

## Environment Variables

### Local Development (.env)

```bash
# Server
HOST=0.0.0.0
PORT=1337
PUBLIC_URL=http://localhost:1337

# Security Keys
APP_KEYS=key1,key2,key3,key4
API_TOKEN_SALT=your_token_salt
ADMIN_JWT_SECRET=your_admin_secret
TRANSFER_TOKEN_SALT=your_transfer_salt
JWT_SECRET=your_jwt_secret

# Database (SQLite)
DATABASE_CLIENT=sqlite
DATABASE_FILENAME=database/.tmp/data.db
```

### Docker/Production (.env)

Add to root `.env` file:

```bash
# Strapi Configuration
STRAPI_DATABASE_PASSWORD=your_secure_database_password
STRAPI_PUBLIC_URL=https://your-domain.com/cms
STRAPI_APP_KEYS=key1,key2,key3,key4
STRAPI_API_TOKEN_SALT=your_token_salt
STRAPI_ADMIN_JWT_SECRET=your_admin_secret
STRAPI_TRANSFER_TOKEN_SALT=your_transfer_salt
STRAPI_JWT_SECRET=your_jwt_secret
```

### Generating Secure Keys

Use OpenSSL to generate secure random keys:

```bash
openssl rand -base64 32
```

Run this command 5 times to generate all required keys.

---

## Admin Panel

### First Run Setup

1. **Access admin panel**:
   - Local: `http://localhost:1337/admin`
   - Docker: `http://localhost:1337/admin`

2. **Create admin account**:
   - First name
   - Last name
   - Email
   - Password

3. **Configure permissions** (see [API Access](#api-access))

### Creating Articles

1. Go to **Content Manager** → **Article** → **Create new entry**
2. Fill in required fields:
   - Title
   - Slug (auto-generated)
   - Excerpt
   - Content (use rich text editor)
   - Author
   - Category
3. Optional fields:
   - Upload featured image
   - Add tags
   - Set publication date
   - Add SEO meta information
   - Set read time
   - Mark as featured
4. **Save as draft** or **Publish**

### Managing Articles

- **List view**: View all articles with filters
- **Edit**: Click on any article to edit
- **Delete**: Select articles and use bulk actions
- **Search**: Search by title, content, or author
- **Filter**: Filter by category, published status, etc.

---

## API Endpoints

### Base URL

- **Local**: `http://localhost:1337/api`
- **Docker**: `http://localhost:1337/api`
- **Production**: `https://your-domain.com/api`

### Available Endpoints

#### List All Articles

```http
GET /api/articles
```

**Query Parameters**:
- `pagination[page]`: Page number (default: 1)
- `pagination[pageSize]`: Items per page (default: 25, max: 100)
- `sort`: Sort field (e.g., `publishedAt:desc`)
- `filters[category][$eq]`: Filter by category
- `filters[featured][$eq]`: Filter featured articles
- `populate`: Populate relations (e.g., `featured_image`)

**Example**:
```bash
# Get first page of articles
curl http://localhost:1337/api/articles

# Get featured articles
curl http://localhost:1337/api/articles?filters[featured][$eq]=true

# Get articles with images
curl http://localhost:1337/api/articles?populate=featured_image

# Get by category
curl http://localhost:1337/api/articles?filters[category][$eq]=AI%20%26%20Technology
```

#### Get Single Article

```http
GET /api/articles/:id
GET /api/articles?filters[slug][$eq]=your-slug
```

**Example**:
```bash
# By ID
curl http://localhost:1337/api/articles/1?populate=featured_image

# By slug
curl http://localhost:1337/api/articles?filters[slug][$eq]=my-article-slug&populate=featured_image
```

### Response Format

```json
{
  "data": [
    {
      "id": 1,
      "documentId": "abc123",
      "title": "Article Title",
      "slug": "article-title",
      "excerpt": "Short summary of the article...",
      "content": "Full article content...",
      "author": "WWMAA Team",
      "category": "AI & Technology",
      "tags": ["AI", "Machine Learning"],
      "meta_title": "SEO Title",
      "meta_description": "SEO description",
      "read_time": 5,
      "featured": false,
      "createdAt": "2025-01-01T00:00:00.000Z",
      "updatedAt": "2025-01-01T00:00:00.000Z",
      "publishedAt": "2025-01-01T00:00:00.000Z",
      "locale": null,
      "featured_image": {
        "id": 1,
        "url": "/uploads/image.jpg",
        "alternativeText": "Image alt text",
        "width": 1200,
        "height": 630
      }
    }
  ],
  "meta": {
    "pagination": {
      "page": 1,
      "pageSize": 25,
      "pageCount": 1,
      "total": 1
    }
  }
}
```

---

## Integration with Backend

### Python/FastAPI Integration

Create a service to fetch articles from Strapi:

```python
# backend/services/strapi_service.py
import httpx
from typing import List, Optional, Dict, Any
from backend.core.config import settings

class StrapiService:
    def __init__(self):
        self.base_url = settings.STRAPI_URL  # http://localhost:1337/api
        self.api_token = settings.STRAPI_API_TOKEN
        self.headers = {}
        if self.api_token:
            self.headers["Authorization"] = f"Bearer {self.api_token}"

    async def get_articles(
        self,
        page: int = 1,
        page_size: int = 25,
        category: Optional[str] = None,
        featured: Optional[bool] = None,
        populate: List[str] = None
    ) -> Dict[str, Any]:
        """Fetch articles from Strapi CMS"""
        params = {
            "pagination[page]": page,
            "pagination[pageSize]": page_size,
            "populate": populate or ["featured_image"],
            "sort": "publishedAt:desc"
        }

        if category:
            params["filters[category][$eq]"] = category
        if featured is not None:
            params["filters[featured][$eq]"] = featured

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/articles",
                params=params,
                headers=self.headers,
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()

    async def get_article_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """Fetch a single article by slug"""
        params = {
            "filters[slug][$eq]": slug,
            "populate": ["featured_image"]
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/articles",
                params=params,
                headers=self.headers,
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()

            if data.get("data"):
                return data["data"][0]
            return None
```

### Environment Variables for Backend

Add to `backend/.env`:

```bash
STRAPI_URL=http://localhost:1337/api
STRAPI_API_TOKEN=your_api_token_here  # Optional, for authenticated requests
```

### Frontend Integration

```typescript
// lib/strapi.ts
const STRAPI_URL = process.env.NEXT_PUBLIC_STRAPI_URL || 'http://localhost:1337/api';
const STRAPI_TOKEN = process.env.STRAPI_API_TOKEN;

interface Article {
  id: number;
  documentId: string;
  title: string;
  slug: string;
  excerpt: string;
  content: string;
  author: string;
  category: string;
  tags?: string[];
  featured: boolean;
  read_time: number;
  publishedAt: string;
  featured_image?: {
    url: string;
    alternativeText?: string;
  };
}

export async function getArticles(page = 1, pageSize = 10): Promise<Article[]> {
  const params = new URLSearchParams({
    'pagination[page]': page.toString(),
    'pagination[pageSize]': pageSize.toString(),
    'populate': 'featured_image',
    'sort': 'publishedAt:desc'
  });

  const headers: HeadersInit = {};
  if (STRAPI_TOKEN) {
    headers['Authorization'] = `Bearer ${STRAPI_TOKEN}`;
  }

  const response = await fetch(`${STRAPI_URL}/articles?${params}`, {
    headers,
    next: { revalidate: 60 } // Revalidate every 60 seconds
  });

  if (!response.ok) {
    throw new Error('Failed to fetch articles');
  }

  const data = await response.json();
  return data.data;
}

export async function getArticleBySlug(slug: string): Promise<Article | null> {
  const params = new URLSearchParams({
    'filters[slug][$eq]': slug,
    'populate': 'featured_image'
  });

  const headers: HeadersInit = {};
  if (STRAPI_TOKEN) {
    headers['Authorization'] = `Bearer ${STRAPI_TOKEN}`;
  }

  const response = await fetch(`${STRAPI_URL}/articles?${params}`, {
    headers,
    next: { revalidate: 60 }
  });

  if (!response.ok) {
    throw new Error('Failed to fetch article');
  }

  const data = await response.json();
  return data.data[0] || null;
}
```

---

## Production Deployment

### Railway Deployment

1. **Add Strapi service to Railway**:
   - Create new service
   - Connect to GitHub repo
   - Set root directory to `/cms`

2. **Add PostgreSQL database**:
   - Add PostgreSQL plugin
   - Railway will auto-configure DATABASE_URL

3. **Configure environment variables** in Railway:
   ```bash
   NODE_ENV=production
   HOST=0.0.0.0
   PORT=1337
   PUBLIC_URL=https://your-domain.com
   APP_KEYS=key1,key2,key3,key4
   API_TOKEN_SALT=your_salt
   ADMIN_JWT_SECRET=your_secret
   TRANSFER_TOKEN_SALT=your_salt
   JWT_SECRET=your_secret
   DATABASE_CLIENT=postgres
   DATABASE_HOST=${{POSTGRES.RAILWAY_PRIVATE_DOMAIN}}
   DATABASE_PORT=${{POSTGRES.RAILWAY_TCP_PROXY_PORT}}
   DATABASE_NAME=${{POSTGRES.PGDATABASE}}
   DATABASE_USERNAME=${{POSTGRES.PGUSER}}
   DATABASE_PASSWORD=${{POSTGRES.PGPASSWORD}}
   DATABASE_SSL=false
   ```

4. **Deploy**:
   - Push to main branch
   - Railway will auto-deploy

### Security Considerations

1. **Change all default secrets** in production
2. **Use strong, unique passwords** for database
3. **Enable CORS** only for trusted domains
4. **Use HTTPS** in production
5. **Limit API token permissions** to minimum required
6. **Regular backups** of PostgreSQL database
7. **Keep Strapi updated** to latest stable version

---

## Troubleshooting

### Common Issues

#### 1. Port Already in Use

```bash
Error: listen EADDRINUSE: address already in use :::1337
```

**Solution**: Change port in `.env`:
```bash
PORT=1338
```

#### 2. Database Connection Error

```bash
Error: connect ECONNREFUSED 127.0.0.1:5432
```

**Solution**: Ensure PostgreSQL is running (Docker):
```bash
docker-compose up -d strapi-db
```

#### 3. Permission Errors

```bash
Error: You don't have permission to access this resource
```

**Solution**: Configure public permissions in admin panel (see [API Access](#api-access))

#### 4. Build Errors

```bash
Error: Cannot find module '@strapi/strapi'
```

**Solution**: Reinstall dependencies:
```bash
cd cms
rm -rf node_modules package-lock.json
npm install
```

### Logs

View Strapi logs:

```bash
# Local
cd cms
npm run develop

# Docker
docker-compose logs -f strapi
```

---

## Additional Resources

- [Strapi Documentation](https://docs.strapi.io/)
- [Strapi API Reference](https://docs.strapi.io/dev-docs/api/rest)
- [Content Type Builder](https://docs.strapi.io/user-docs/content-type-builder)
- [REST API Parameters](https://docs.strapi.io/dev-docs/api/rest/parameters)

---

## Support

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review Strapi documentation
3. Contact the WWMAA development team
