# Search Feature Setup Guide

## Quick Setup (2 Steps)

### 1. Set OpenAI API Key

Get your API key from: https://platform.openai.com/api-keys

Update your `.env` file:

```bash
# Change this line:
OPENAI_API_KEY=sk-placeholder-for-testing

# To your real key:
OPENAI_API_KEY=sk-proj-your-actual-openai-key-here
```

### 2. Restart Backend Server

```bash
# Kill existing server
pkill -f uvicorn

# Restart
uvicorn backend.app:app --reload --port 8000
```

**That's it!** The search feature is now fully functional.

## Verify Setup

### Quick Test
```bash
# Test the diagnostic script
PYTHONPATH=/Users/aideveloper/Desktop/wwmaa python3 scripts/test_search_pipeline.py
```

Expected output:
```
✅ PASSED: Environment Variables
✅ PASSED: Embedding Service
✅ PASSED: ZeroDB Client
✅ PASSED: Vector Search Service
✅ PASSED: AI Registry Service
✅ PASSED: Query Search Service

OVERALL: 6/6 tests passed (100%)
```

### Manual API Test

```bash
curl -X POST http://localhost:8000/api/search/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are good martial arts techniques for beginners?",
    "bypass_cache": false
  }'
```

Expected response:
```json
{
  "answer": "# Martial Arts Techniques for Beginners\n\nHere are some great techniques...",
  "sources": [
    {"title": "...", "url": "/events/...", "source_type": "event"}
  ],
  "media": {
    "videos": [],
    "images": []
  },
  "related_queries": [
    "best martial arts for self defense",
    "martial arts classes near me"
  ],
  "latency_ms": 1250,
  "cached": false
}
```

## Architecture Overview

### Search Pipeline (11 Steps)

```
User Query → Frontend → API Route → Backend Search Endpoint
                                           ↓
                                    1. Normalize Query
                                    2. Rate Limit Check
                                    3. Cache Check
                                           ↓
                                    4. OpenAI Embedding
                                           ↓
                                    5. ZeroDB Vector Search
                                           ↓
                                    6-7. OpenAI Answer Generation
                                           ↓
                                    8. Attach Media
                                    9. Cache Result
                                    10. Log Query
                                           ↓
                                    11. Return Response
```

### Services Used

1. **OpenAI API** (Embeddings & LLM)
   - Embedding Model: `text-embedding-3-small` (1536 dims)
   - LLM Model: `gpt-4o-mini` (fast, cheap)
   - Cost: ~$0.20 per 1000 searches (before caching)

2. **ZeroDB** (Vector Search & Storage)
   - Vector collections: events, articles, profiles, techniques
   - Authentication: JWT (email/password)
   - Project ID: `e4f3d95f-593f-4ae6-9017-24bff5f72c5e`

3. **Redis** (Caching)
   - Cache TTL: 5 minutes
   - Embedding cache: 24 hours
   - Connection: `redis://localhost:6379`

## Configuration Reference

### Environment Variables

```bash
# OpenAI Configuration (REQUIRED)
OPENAI_API_KEY=sk-proj-your-key-here

# ZeroDB Configuration (REQUIRED)
ZERODB_API_KEY=kLPiP0bzgKJ0CnNYVt1wq3qxbs2QgDeF2XwyUnxBEOM
ZERODB_API_BASE_URL=https://api.ainative.studio
ZERODB_PROJECT_ID=e4f3d95f-593f-4ae6-9017-24bff5f72c5e
ZERODB_EMAIL=admin@ainative.studio
ZERODB_PASSWORD=your-zerodb-password

# Redis Configuration (REQUIRED)
REDIS_URL=redis://localhost:6379

# Optional AI Configuration
AI_REGISTRY_MODEL=gpt-4o-mini
AI_REGISTRY_FALLBACK_MODEL=gpt-3.5-turbo
AI_REGISTRY_MAX_TOKENS=1000
AI_REGISTRY_TEMPERATURE=0.7
```

### Search Endpoint Parameters

**POST** `/api/search/query`

Request:
```json
{
  "query": "your search query here",
  "bypass_cache": false
}
```

Response:
```json
{
  "answer": "AI-generated markdown answer",
  "sources": [
    {
      "title": "Source title",
      "url": "/events/123",
      "source_type": "event"
    }
  ],
  "media": {
    "videos": [
      {
        "id": "video-id",
        "title": "Video title",
        "cloudflare_stream_id": "stream-id"
      }
    ],
    "images": [
      {
        "url": "https://...",
        "alt": "Image description",
        "zerodb_object_key": "key"
      }
    ]
  },
  "related_queries": [
    "Related query 1",
    "Related query 2",
    "Related query 3"
  ],
  "latency_ms": 1200,
  "cached": false
}
```

### Rate Limiting

- **Limit**: 10 requests per minute per IP address
- **Response**: 429 Too Many Requests (when exceeded)
- **Headers**:
  - `X-RateLimit-Limit`: 10
  - `X-RateLimit-Remaining`: 9
  - `X-RateLimit-Reset`: timestamp

### Caching

**Query Cache** (Redis):
- TTL: 5 minutes
- Key format: `search:query:{sha256_hash}`
- Hit rate target: 80%

**Embedding Cache** (Redis):
- TTL: 24 hours
- Key format: `embedding:text-embedding-3-small:{sha256_hash}`
- Reduces OpenAI API costs

## Performance Targets

### Latency
- **p50**: < 800ms
- **p95**: < 1200ms
- **p99**: < 2000ms
- **Timeout**: 10 seconds

### Cache Performance
- **Hit rate**: 80%+ (with normal traffic)
- **Cached latency**: < 100ms

### API Costs (per 1000 searches)

**Without Caching**:
- Embeddings: $0.0004
- LLM answers: $0.195
- **Total**: $0.195

**With 80% Cache Hit**:
- Effective cost: **$0.04 per 1000 searches**
- Monthly (10K searches): **$0.40**
- Monthly (100K searches): **$4.00**

## Troubleshooting

### Issue: "OPENAI_API_KEY not set"

**Solution**: Check your `.env` file
```bash
grep OPENAI_API_KEY .env
```

Should show:
```
OPENAI_API_KEY=sk-proj-...
```

### Issue: "404 Not Found on /v1/chat/completions"

**Solution**: Already fixed! Service now uses OpenAI API directly.

If you still see this, verify:
```bash
grep "base_url" backend/services/ai_registry_service.py
```

Should show:
```python
base_url: str = "https://api.openai.com"
```

### Issue: "No results found"

**Cause**: ZeroDB collections may be empty

**Solution**: Check if collections have data:
```python
from backend.services.zerodb_service import ZeroDBClient

client = ZeroDBClient()
events = client.query_documents("events", limit=10)
print(f"Events: {len(events.get('documents', []))}")
```

If empty, you need to seed data (optional for testing).

### Issue: Redis connection error

**Solution**: Start Redis:
```bash
# macOS
brew services start redis

# Linux
sudo systemctl start redis

# Docker
docker run -d -p 6379:6379 redis:alpine
```

## Testing

### Unit Tests
```bash
pytest backend/tests/test_query_search_service.py -v
pytest backend/tests/test_search_query_routes.py -v
```

### Integration Tests
```bash
pytest backend/tests/test_search_pipeline_integration.py -v
```

### Manual Frontend Test
1. Start backend: `uvicorn backend.app:app --reload`
2. Start frontend: `npm run dev`
3. Navigate to: http://localhost:3000/search
4. Enter query: "martial arts techniques"
5. Verify results appear with AI answer

## Monitoring

### Check Logs
```bash
# Backend logs
tail -f backend/logs/app.log

# Search-specific logs
grep "search_query" backend/logs/app.log

# OpenAI API calls
grep "AIRegistryService" backend/logs/app.log
```

### Performance Metrics
```bash
# Check cache hit rate
redis-cli INFO stats | grep keyspace_hits

# Check search latency
grep "Search completed" backend/logs/app.log | tail -20
```

## Advanced Configuration

### Customize LLM Model

Edit `backend/config.py` or `.env`:
```bash
AI_REGISTRY_MODEL=gpt-4o        # More accurate (but expensive)
AI_REGISTRY_MODEL=gpt-4o-mini   # Fast and cheap (default)
AI_REGISTRY_MODEL=gpt-3.5-turbo # Cheaper alternative
```

### Adjust Cache TTL

Edit `backend/services/query_search_service.py`:
```python
self.cache_ttl = 300  # 5 minutes (default)
self.cache_ttl = 600  # 10 minutes
self.cache_ttl = 60   # 1 minute (for testing)
```

### Customize Number of Results

Edit `backend/services/query_search_service.py`:
```python
self.top_k_results = 10  # Default
self.top_k_results = 20  # More results
self.top_k_results = 5   # Faster, less context
```

## Security Notes

### API Key Security
- ✅ Never commit API keys to git
- ✅ Use `.env` file (ignored by git)
- ✅ Rotate keys regularly
- ⚠️  Monitor usage on OpenAI dashboard

### Rate Limiting
- ✅ Enabled: 10 requests/minute per IP
- ✅ Prevents abuse and DoS
- ⚠️  Adjust if needed for high-traffic

### Data Privacy
- ✅ IP addresses hashed with SHA256
- ✅ Queries logged anonymously
- ✅ No PII stored in search logs

## Support

### Documentation
- Search Routes: `backend/routes/search.py`
- Query Service: `backend/services/query_search_service.py`
- AI Service: `backend/services/ai_registry_service.py`
- Vector Search: `backend/services/vector_search_service.py`
- Embeddings: `backend/services/embedding_service.py`

### Get Help
- Check logs: `backend/logs/app.log`
- Run diagnostic: `scripts/test_search_pipeline.py`
- Review tests: `backend/tests/test_*search*.py`

---

**Last Updated**: 2025-11-15
**Version**: 1.0
**Status**: Production Ready (after OpenAI key configuration)
