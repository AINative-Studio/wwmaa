# BeeHiiv Blog Sync - Quick Start Guide

## 5-Minute Setup

### Step 1: Install Dependencies
```bash
cd backend
pip install bleach Pillow requests
```

### Step 2: Configure Environment Variables
Add to your `.env` file:
```bash
BEEHIIV_API_KEY=your_api_key_here
BEEHIIV_PUBLICATION_ID=your_publication_id_here
BEEHIIV_WEBHOOK_SECRET=your_webhook_secret_here
```

**Get your credentials:**
1. **API Key**: BeeHiiv Dashboard → Settings → API → Generate API Key
2. **Publication ID**: From your dashboard URL: `app.beehiiv.com/publications/{ID}`
3. **Webhook Secret**: Created in Step 4 below

### Step 3: Run Initial Sync
```bash
# Test with first 5 posts
python backend/scripts/sync_beehiiv_posts.py --limit 5

# Sync all posts
python backend/scripts/sync_beehiiv_posts.py
```

### Step 4: Configure BeeHiiv Webhook
1. Go to BeeHiiv Dashboard → Settings → Webhooks
2. Click "Add Webhook"
3. Configure:
   - **URL**: `https://your-domain.com/api/webhooks/beehiiv/post`
   - **Events**:
     - ✓ post.published
     - ✓ post.updated
     - ✓ post.deleted
4. Copy the webhook secret to your `.env` file
5. Click "Test Webhook" to verify

### Step 5: Verify Setup
```bash
# Check health
curl https://your-domain.com/api/webhooks/beehiiv/health

# Expected response:
{
  "status": "healthy",
  "webhook_secret_configured": true,
  "api_key_configured": true,
  "publication_id_configured": true
}

# List synced posts
curl https://your-domain.com/api/blog/posts
```

---

## API Endpoints

### List Posts
```http
GET /api/blog/posts?page=1&limit=20&category=Beginners
```

### Get Single Post
```http
GET /api/blog/posts/{slug}
```

### List Categories
```http
GET /api/blog/categories
```

### List Tags
```http
GET /api/blog/tags
```

### Related Posts
```http
GET /api/blog/posts/related/{post_id}?limit=5
```

---

## Testing

```bash
# Run all tests
pytest backend/tests/test_blog* -v

# With coverage report
pytest backend/tests/test_blog* --cov --cov-report=html
```

---

## Troubleshooting

### Webhook not working?
1. Verify webhook URL is publicly accessible
2. Check `BEEHIIV_WEBHOOK_SECRET` matches BeeHiiv
3. Review logs: `tail -f logs/app.log | grep BeeHiiv`

### Images not showing?
1. Verify ZeroDB Object Storage is configured
2. Check image URLs are publicly accessible
3. Ensure `Pillow` library is installed

### Duplicate slug errors?
- Handled automatically - slugs get `-1`, `-2`, etc. appended

---

## Full Documentation

For complete documentation, see:
- **Setup & Configuration**: `/docs/blog-sync-beehiiv.md`
- **Implementation Details**: `/US-060-IMPLEMENTATION-SUMMARY.md`
- **API Reference**: `/docs/blog-sync-beehiiv.md#api-endpoints`

---

## Need Help?

1. Check `/docs/blog-sync-beehiiv.md` for detailed troubleshooting
2. Review logs for error messages
3. Run health check: `GET /api/webhooks/beehiiv/health`
4. Verify environment variables are set correctly

---

**Ready to go!** Publish a post in BeeHiiv and watch it automatically sync to your website. 🚀
