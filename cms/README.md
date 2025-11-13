# WWMAA Strapi CMS

Headless CMS for managing blog content for the WWMAA platform.

## Quick Start

### Local Development

```bash
# Install dependencies
npm install

# Start development server
npm run develop

# Access admin panel
# http://localhost:1337/admin
```

### Docker

```bash
# From project root
docker-compose up -d strapi strapi-db

# Access admin panel
# http://localhost:1337/admin
```

## Documentation

See [STRAPI_CMS_SETUP.md](../docs/STRAPI_CMS_SETUP.md) for complete setup and usage guide.

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

### Required Variables

- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 1337)
- `APP_KEYS`: Comma-separated encryption keys (4 keys)
- `API_TOKEN_SALT`: Salt for API tokens
- `ADMIN_JWT_SECRET`: Secret for admin JWT
- `JWT_SECRET`: General JWT secret
- `DATABASE_CLIENT`: Database type (sqlite or postgres)

## Content Types

### Article

Blog articles with the following fields:

- **title** (String, required): Article title
- **slug** (UID, required): URL-friendly identifier
- **excerpt** (Text, required): Short summary
- **content** (Rich Text, required): Full article content
- **author** (String, required): Author name
- **published_at** (DateTime): Publication date
- **featured_image** (Media): Featured image
- **category** (Enum, required): Article category
- **tags** (JSON): Article tags
- **meta_title** (String): SEO meta title
- **meta_description** (Text): SEO meta description
- **read_time** (Integer): Estimated reading time
- **featured** (Boolean): Featured article flag

## API Endpoints

Base URL: `http://localhost:1337/api`

### Articles

```bash
# List articles
GET /api/articles

# Get single article
GET /api/articles/:id

# Get by slug
GET /api/articles?filters[slug][$eq]=article-slug

# Filter by category
GET /api/articles?filters[category][$eq]=AI%20%26%20Technology

# Get featured articles
GET /api/articles?filters[featured][$eq]=true

# Pagination
GET /api/articles?pagination[page]=1&pagination[pageSize]=10

# Populate relations
GET /api/articles?populate=featured_image
```

## Scripts

```bash
# Development (auto-reload)
npm run develop

# Production build
npm run build

# Start production server
npm run start

# Clean cache and build
npm run clean
```

## Database

### Development
- **Type**: SQLite
- **Location**: `database/.tmp/data.db`

### Production (Docker)
- **Type**: PostgreSQL
- **Container**: wwmaa-strapi-db
- **Port**: 5433 (external), 5432 (internal)

## Admin Panel

### First Time Setup

1. Start Strapi: `npm run develop`
2. Go to: `http://localhost:1337/admin`
3. Create admin account
4. Configure public permissions:
   - Settings → Users & Permissions → Public
   - Enable `find` and `findOne` for Article

### Creating Content

1. Content Manager → Article → Create new entry
2. Fill in required fields
3. Upload featured image (optional)
4. Save as draft or Publish

## Security

### Generate Secure Keys

Use OpenSSL to generate random keys:

```bash
openssl rand -base64 32
```

Run this 5 times to generate all required keys for production.

### API Tokens

Create API tokens for secure backend access:

1. Settings → API Tokens → Create new API Token
2. Set permissions (Read-only or Full access)
3. Copy token (shown once!)
4. Use in API requests:
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:1337/api/articles
   ```

## Integration

### Backend (Python/FastAPI)

```python
import httpx

async def get_articles():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:1337/api/articles",
            params={"populate": "featured_image"}
        )
        return response.json()
```

### Frontend (Next.js)

```typescript
export async function getArticles() {
  const response = await fetch(
    'http://localhost:1337/api/articles?populate=featured_image',
    { next: { revalidate: 60 } }
  );
  return response.json();
}
```

## Troubleshooting

### Port Already in Use

Change port in `.env`:
```bash
PORT=1338
```

### Permission Errors

Configure public permissions in admin panel:
- Settings → Users & Permissions → Public
- Enable `find` and `findOne` for Article

### Database Connection Issues

Ensure PostgreSQL is running (Docker):
```bash
docker-compose up -d strapi-db
```

## Project Structure

```
cms/
├── config/              # Configuration files
│   ├── admin.js         # Admin panel config
│   ├── api.js           # API config
│   ├── database.js      # Database config
│   ├── middlewares.js   # Middleware config
│   └── server.js        # Server config
├── database/            # SQLite database (development)
├── public/              # Public assets
│   └── uploads/         # Uploaded media files
├── src/
│   ├── api/             # API endpoints
│   │   └── article/     # Article content type
│   └── index.js         # Main entry point
├── .env                 # Environment variables (not in git)
├── .env.example         # Example environment variables
├── .gitignore           # Git ignore rules
├── package.json         # Dependencies and scripts
└── README.md            # This file
```

## License

MIT
