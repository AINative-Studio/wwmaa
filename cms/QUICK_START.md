# Strapi CMS Quick Start

## 1. Install and Run Locally

```bash
# Navigate to CMS directory
cd cms

# Install dependencies (if not already done)
npm install

# Start Strapi in development mode
npm run develop
```

The admin panel will open automatically at: **http://localhost:1337/admin**

## 2. Create Admin Account

On first run, you'll be prompted to create an admin account:

- First name: Your first name
- Last name: Your last name
- Email: admin@wwmaa.com (or your email)
- Password: Choose a strong password

## 3. Configure Public API Access

To allow the frontend/backend to access articles:

1. Go to **Settings** (left sidebar)
2. Click **Users & Permissions Plugin** → **Roles**
3. Click **Public**
4. Expand **Article** under Permissions
5. Check ✓ **find** and ✓ **findOne**
6. Click **Save** (top right)

## 4. Create Your First Article

1. Go to **Content Manager** (left sidebar)
2. Click **Article** → **Create new entry**
3. Fill in the form:
   - **Title**: "Welcome to WWMAA Blog"
   - **Slug**: (auto-generated) "welcome-to-wwmaa-blog"
   - **Excerpt**: "A short introduction to our blog..."
   - **Content**: Write your article content using the rich text editor
   - **Author**: "WWMAA Team"
   - **Category**: Select "AI & Technology"
4. Click **Publish** (top right)

## 5. Test the API

Open a new terminal and test the API:

```bash
# List all articles
curl http://localhost:1337/api/articles

# Get articles with featured image
curl http://localhost:1337/api/articles?populate=featured_image

# Get specific article by slug
curl "http://localhost:1337/api/articles?filters[slug][\$eq]=welcome-to-wwmaa-blog"
```

## 6. Create API Token (Optional)

For secure backend access:

1. Go to **Settings** → **API Tokens** → **Create new API Token**
2. Configure:
   - Name: "Backend API Token"
   - Token duration: Unlimited
   - Token type: Read-only
3. Click **Save**
4. **Copy the token** (shown only once!)
5. Add to your backend `.env`:
   ```bash
   STRAPI_URL=http://localhost:1337/api
   STRAPI_API_TOKEN=paste_your_token_here
   ```

## 7. Run with Docker (Alternative)

Instead of running locally, you can use Docker:

```bash
# From project root directory
docker-compose up -d strapi strapi-db

# Wait for containers to start (60 seconds)
sleep 60

# Access admin panel
open http://localhost:1337/admin
```

## Next Steps

- Read the full documentation: [STRAPI_CMS_SETUP.md](../docs/STRAPI_CMS_SETUP.md)
- Create more articles
- Upload featured images
- Explore the Content Manager features
- Integrate with your frontend/backend

## Common Commands

```bash
# Development mode (auto-reload)
npm run develop

# Production build
npm run build

# Production server
npm run start

# Clean cache
npm run clean
```

## Accessing the Admin Panel

- **Local**: http://localhost:1337/admin
- **Docker**: http://localhost:1337/admin

## API Base URL

- **Local**: http://localhost:1337/api
- **Docker**: http://localhost:1337/api

## Need Help?

- See [README.md](./README.md) for more details
- Check [STRAPI_CMS_SETUP.md](../docs/STRAPI_CMS_SETUP.md) for complete guide
- Visit [Strapi Documentation](https://docs.strapi.io/)
