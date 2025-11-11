# Content Indexing Pipeline - Quick Start Guide

## Setup

### 1. Install Dependencies
```bash
cd /Users/aideveloper/Desktop/wwmaa/backend
pip install openai==1.6.1 tiktoken==0.5.2
```

### 2. Configure Environment Variables
Add to your `.env` file:
```bash
# Required: OpenAI API Key for embeddings
OPENAI_API_KEY=sk-your-openai-api-key-here

# Optional: Customize indexing behavior
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002
INDEXING_SCHEDULE_INTERVAL_HOURS=6
INDEXING_CHUNK_SIZE=500
INDEXING_CHUNK_OVERLAP=50
INDEXING_BATCH_SIZE=100
```

## Usage

### Option 1: Manual Indexing via API

#### Trigger Full Reindex
```bash
curl -X POST http://localhost:8000/api/admin/indexing/trigger \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content_types": ["articles", "events", "training_videos", "member_profiles"],
    "incremental": false
  }'
```

#### Trigger Incremental Update
```bash
curl -X POST http://localhost:8000/api/admin/indexing/trigger \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "incremental": true
  }'
```

#### Index Specific Content Type
```bash
curl -X POST http://localhost:8000/api/admin/indexing/index-content \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content_type": "articles",
    "force": false
  }'
```

#### Index Specific Document
```bash
curl -X POST http://localhost:8000/api/admin/indexing/index-content \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content_type": "articles",
    "document_id": "article-123",
    "force": true
  }'
```

#### Check Indexing Status
```bash
curl http://localhost:8000/api/admin/indexing/status \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

Response:
```json
{
  "status": "idle",
  "current_operation": null,
  "stats": {
    "total_indexed": 150,
    "total_chunks": 450,
    "total_tokens": 225000,
    "errors": 0,
    "last_indexed_at": "2025-01-10T15:30:00Z"
  }
}
```

#### Get Indexing Statistics
```bash
curl http://localhost:8000/api/admin/indexing/stats \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

Response:
```json
{
  "total_documents_indexed": 150,
  "total_chunks": 450,
  "current_status": "idle",
  "by_content_type": {
    "articles": {
      "documents": 50,
      "chunks": 200,
      "last_indexed": "2025-01-10T15:30:00Z"
    },
    "events": {
      "documents": 30,
      "chunks": 90,
      "last_indexed": "2025-01-10T14:00:00Z"
    },
    "training_videos": {
      "documents": 40,
      "chunks": 100,
      "last_indexed": "2025-01-10T13:00:00Z"
    },
    "member_profiles": {
      "documents": 30,
      "chunks": 60,
      "last_indexed": "2025-01-10T12:00:00Z"
    }
  }
}
```

### Option 2: Automated Background Indexing

#### Start the Background Scheduler
```bash
cd /Users/aideveloper/Desktop/wwmaa/backend
python scripts/index_scheduler.py
```

The scheduler will:
- Run an initial indexing job (in development mode)
- Schedule recurring indexing every 6 hours (configurable)
- Log all operations to `logs/indexing_scheduler.log`
- Handle graceful shutdown on Ctrl+C or SIGTERM

#### Run as a Daemon (Production)
```bash
# Using nohup
nohup python scripts/index_scheduler.py > logs/scheduler.out 2>&1 &

# Using systemd (create /etc/systemd/system/wwmaa-indexing.service)
[Unit]
Description=WWMAA Content Indexing Scheduler
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/wwmaa/backend
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 scripts/index_scheduler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

# Enable and start
sudo systemctl enable wwmaa-indexing
sudo systemctl start wwmaa-indexing
sudo systemctl status wwmaa-indexing
```

## Programmatic Usage

### In Python Code

```python
from backend.services.indexing_service import (
    get_indexing_service,
    ContentType
)

# Get service instance
indexing_service = get_indexing_service()

# Index a single document
document = {
    "id": "article-123",
    "data": {
        "title": "Introduction to Karate",
        "content": "Karate is a martial art...",
        "keywords": ["karate", "martial arts"]
    }
}

result = indexing_service.index_document(
    content_type=ContentType.ARTICLES,
    document=document,
    force=False  # Skip if already indexed
)

print(f"Indexed: {result['chunks_indexed']} chunks")

# Index entire collection
result = indexing_service.index_collection(
    content_type=ContentType.EVENTS,
    incremental=True,  # Only new/updated content
    limit=100  # Optional limit for testing
)

print(f"Indexed {result['indexed']} documents")

# Get current status
status = indexing_service.get_status()
print(f"Status: {status['status']}")

# Get statistics
stats = indexing_service.get_stats()
print(f"Total indexed: {stats['total_documents_indexed']}")
```

### Text Chunking Utility

```python
from backend.utils.text_chunking import chunk_text, count_tokens

# Chunk text
text = "Long article content here..."
chunks = chunk_text(
    text,
    max_tokens=500,
    overlap=50,
    metadata={"doc_id": "123", "type": "article"}
)

for chunk in chunks:
    print(f"Chunk {chunk['chunk_index']}: {chunk['tokens']} tokens")
    print(f"Text: {chunk['text'][:100]}...")

# Count tokens
token_count = count_tokens("Some text to analyze")
print(f"Tokens: {token_count}")
```

## Monitoring

### Check Logs
```bash
# Scheduler logs
tail -f /Users/aideveloper/Desktop/wwmaa/backend/logs/indexing_scheduler.log

# Application logs (if using uvicorn)
tail -f /Users/aideveloper/Desktop/wwmaa/backend/logs/app.log
```

### Monitor via Admin API
```bash
# Watch status in real-time
watch -n 5 'curl -s http://localhost:8000/api/admin/indexing/status \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" | jq'
```

## Troubleshooting

### Issue: "OpenAI API key not configured"
**Solution:** Add `OPENAI_API_KEY` to your `.env` file

### Issue: "Rate limit exceeded"
**Solution:** The service automatically retries with exponential backoff. Check logs for details.

### Issue: "No content extracted from document"
**Solution:** Ensure document has required fields (title, content, etc.)

### Issue: Indexing is slow
**Solutions:**
- Increase `INDEXING_BATCH_SIZE` (default: 100)
- Check OpenAI API rate limits
- Review network connectivity

### Issue: High memory usage
**Solutions:**
- Decrease `INDEXING_CHUNK_SIZE` (default: 500)
- Process collections in smaller batches
- Monitor chunk count in statistics

## Best Practices

1. **Initial Setup**
   - Start with a small batch (use `limit` parameter)
   - Monitor logs for any errors
   - Verify embeddings are stored correctly

2. **Production Use**
   - Run background scheduler as a daemon
   - Use incremental indexing for regular updates
   - Schedule full reindex during low-traffic hours

3. **Cost Optimization**
   - Use incremental indexing to avoid reprocessing
   - Adjust chunk size based on content type
   - Monitor OpenAI API usage

4. **Monitoring**
   - Set up alerts for failed indexing jobs
   - Track statistics via admin API
   - Review logs regularly

## Content Types Indexed

| Content Type | Fields Indexed | Typical Chunks |
|--------------|---------------|----------------|
| Events | title, description, location | 1-3 chunks |
| Articles | title, content, keywords | 5-20 chunks |
| Training Videos | title, transcript, metadata | 3-15 chunks |
| Member Profiles | name, bio, discipline | 1-2 chunks |

## API Rate Limits

OpenAI Embedding API limits (as of 2025):
- **Free tier**: 3,000 requests/day
- **Paid tier**: 500,000 requests/day

With batch size of 100:
- 100 documents = 1 request (typically)
- 10,000 documents = ~100 requests

## Cost Estimation

OpenAI text-embedding-ada-002 pricing (as of 2025):
- $0.0001 per 1,000 tokens

Example costs:
- 1,000 articles (avg 2,000 tokens each): ~$0.20
- 10,000 member profiles (avg 200 tokens each): ~$0.20
- Monthly incremental updates (1,000 changes): ~$0.20

## Support

For issues or questions:
1. Check logs first
2. Review this documentation
3. Check the implementation summary
4. Contact the development team

---

**Last Updated:** 2025-11-10
**Version:** 1.0.0
