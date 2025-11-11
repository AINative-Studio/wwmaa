# ZeroDB Vector Search Configuration

## Overview

This document describes the ZeroDB vector search setup for semantic content search in the WWMAA application. Vector search enables finding similar content based on meaning rather than exact keyword matches, using cosine similarity for measuring semantic similarity.

## Table of Contents

- [Collection Schema](#collection-schema)
- [Vector Configuration](#vector-configuration)
- [Embedding Strategy](#embedding-strategy)
- [API Methods](#api-methods)
- [Usage Examples](#usage-examples)
- [Best Practices](#best-practices)
- [Performance Optimization](#performance-optimization)
- [Troubleshooting](#troubleshooting)

## Collection Schema

### Collection Name: `content_index`

The `content_index` collection stores content chunks with their vector embeddings for semantic search.

### Schema Fields

```python
{
    "id": UUID,                           # Unique document identifier
    "source_type": SourceType,            # event | article | profile | video | training_session | document
    "source_id": UUID,                    # Reference to source document
    "url": str,                           # URL to the content (optional)

    # Content
    "title": str,                         # Content title (1-500 chars)
    "content_chunk": str,                 # Text content (10-8000 chars, optimal: 200-1000 tokens)
    "summary": str,                       # Brief summary (optional, max 1000 chars)

    # Vector Embedding
    "embedding": List[float],             # 1536-dimensional vector (required)
    "embedding_model": str,               # Default: "text-embedding-ada-002"

    # Metadata
    "metadata": dict,                     # Additional search filters (location, date, etc.)
    "author_id": UUID,                    # Content creator (optional)
    "tags": List[str],                    # Content tags
    "category": str,                      # Content category (optional)

    # Access Control
    "visibility": str,                    # "public" | "members_only" | "private"

    # Search Optimization
    "keywords": List[str],                # Keywords for hybrid search
    "search_weight": float,               # Ranking weight (0-10, default: 1.0)

    # Status
    "published_at": datetime,             # Publication timestamp (optional)
    "is_active": bool,                    # Active in search index (default: true)

    # Performance Tracking
    "search_count": int,                  # Times appeared in results (default: 0)
    "click_count": int,                   # Times clicked from results (default: 0)

    # Audit
    "created_at": datetime,               # Document creation timestamp
    "updated_at": datetime                # Last update timestamp
}
```

### Source Types

The `source_type` enum defines the type of content being indexed:

- `event` - Community events, tournaments, seminars
- `article` - Blog posts, news articles, educational content
- `profile` - User profiles, instructor bios
- `video` - Training videos, recordings, tutorials
- `training_session` - Live training session content
- `document` - Documents, PDFs, certificates

## Vector Configuration

### Embedding Dimensions

**1536 dimensions** - Optimized for OpenAI's `text-embedding-ada-002` model

```python
EMBEDDING_DIMENSION = 1536
```

### Similarity Metric

**Cosine Similarity** - Measures the cosine of the angle between two vectors

```python
SIMILARITY_METRIC = "cosine"
```

Cosine similarity ranges from -1 to 1:
- `1.0` - Identical vectors (perfect match)
- `0.0` - Orthogonal vectors (no similarity)
- `-1.0` - Opposite vectors (inverse similarity)

For semantic search, typical relevant results have scores > 0.7.

### Collection Configuration

When creating the vector collection:

```python
{
    "type": "vector",
    "config": {
        "dimension": 1536,
        "similarity_metric": "cosine"
    }
}
```

## Embedding Strategy

### Content Chunking

For optimal embedding quality:

1. **Chunk Size**: 200-1000 tokens (roughly 800-4000 characters)
2. **Overlap**: 10-15% overlap between chunks for context preservation
3. **Boundaries**: Split on natural boundaries (paragraphs, sentences)

### Recommended Chunking by Content Type

| Content Type | Chunk Size | Strategy |
|--------------|------------|----------|
| Event Descriptions | Full description | Single chunk if < 4000 chars |
| Articles | 500-1000 tokens | Paragraph-based chunks |
| Profiles | Full profile | Single chunk with key sections |
| Videos | 300-500 tokens | Timestamp-based segments |
| Training Sessions | 500 tokens | Topic-based segments |

### Embedding Best Practices

1. **Clean Text**: Remove HTML, special characters, excessive whitespace
2. **Context**: Include relevant context (title, category) in chunk
3. **Consistency**: Use same preprocessing for indexing and querying
4. **Freshness**: Re-embed when content changes significantly

## API Methods

### 1. Create Vector Collection

```python
from backend.services.zerodb_service import get_zerodb_client

client = get_zerodb_client()

result = client.create_vector_collection(
    collection="content_index",
    dimension=1536,
    similarity_metric="cosine",
    metadata_schema={
        "source_type": "string",
        "visibility": "string",
        "tags": "array"
    }
)
```

**Response:**
```json
{
    "collection": "content_index",
    "status": "created",
    "config": {
        "dimension": 1536,
        "similarity_metric": "cosine"
    }
}
```

### 2. Insert Vector

```python
# Generate embedding (using OpenAI or other service)
embedding = generate_embedding("Karate tournament in Los Angeles")

result = client.insert_vector(
    collection="content_index",
    vector=embedding,
    metadata={
        "source_type": "event",
        "source_id": "550e8400-e29b-41d4-a716-446655440000",
        "title": "LA Karate Championship",
        "content_chunk": "Annual karate tournament in Los Angeles featuring competitors from across California...",
        "url": "https://wwmaa.com/events/la-karate-championship",
        "tags": ["tournament", "karate", "los-angeles"],
        "visibility": "public",
        "search_weight": 1.5
    }
)
```

**Response:**
```json
{
    "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "status": "inserted",
    "collection": "content_index"
}
```

### 3. Batch Insert Vectors

For better performance when indexing multiple documents:

```python
vectors = [
    {
        "vector": embedding1,
        "metadata": {
            "source_type": "event",
            "title": "Event 1",
            "content_chunk": "...",
            # ... other fields
        }
    },
    {
        "vector": embedding2,
        "metadata": {
            "source_type": "article",
            "title": "Article 1",
            "content_chunk": "...",
            # ... other fields
        }
    }
]

result = client.batch_insert_vectors(
    collection="content_index",
    vectors=vectors
)
```

**Response:**
```json
{
    "inserted_count": 2,
    "inserted_ids": [
        "7c9e6679-7425-40de-944b-e07fc1f90ae7",
        "8d0f7780-8536-51ef-b15c-f18gd2g01bf8"
    ]
}
```

### 4. Vector Search

```python
# Generate query embedding
query_embedding = generate_embedding("martial arts tournaments near me")

results = client.vector_search(
    collection="content_index",
    query_vector=query_embedding,
    top_k=10,
    filters={
        "source_type": "event",
        "visibility": "public"
    },
    include_metadata=True,
    min_score=0.7
)
```

**Response:**
```json
{
    "results": [
        {
            "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
            "score": 0.89,
            "metadata": {
                "source_type": "event",
                "title": "LA Karate Championship",
                "content_chunk": "Annual karate tournament...",
                "url": "https://wwmaa.com/events/la-karate-championship",
                "tags": ["tournament", "karate", "los-angeles"]
            }
        },
        {
            "id": "8d0f7780-8536-51ef-b15c-f18gd2g01bf8",
            "score": 0.85,
            "metadata": {
                "source_type": "event",
                "title": "Southern California Martial Arts Open",
                "content_chunk": "Multi-discipline martial arts competition...",
                "url": "https://wwmaa.com/events/socal-ma-open",
                "tags": ["tournament", "competition", "california"]
            }
        }
    ],
    "total_results": 2,
    "query_time_ms": 45
}
```

## Usage Examples

### Example 1: Index Event Content

```python
from backend.services.zerodb_service import get_zerodb_client
from backend.models.schemas import ContentIndex, SourceType
from uuid import uuid4

# Assume we have an embedding generation function
def generate_embedding(text: str) -> List[float]:
    # Use OpenAI, AINative, or other embedding service
    # Returns 1536-dimensional vector
    pass

# Create content index entry
event_text = """
LA Karate Championship 2024
Join us for the premier karate tournament in Los Angeles.
Featuring black belt competitors from across California in kata and kumite divisions.
"""

embedding = generate_embedding(event_text)

content = ContentIndex(
    source_type=SourceType.EVENT,
    source_id=uuid4(),
    url="https://wwmaa.com/events/la-karate-championship",
    title="LA Karate Championship 2024",
    content_chunk=event_text,
    embedding=embedding,
    metadata={
        "location": "Los Angeles, CA",
        "event_date": "2024-12-15",
        "event_type": "tournament"
    },
    tags=["karate", "tournament", "los-angeles", "competition"],
    visibility="public",
    search_weight=2.0  # High priority event
)

# Insert into ZeroDB
client = get_zerodb_client()
result = client.insert_vector(
    collection="content_index",
    vector=content.embedding,
    metadata=content.model_dump(exclude={"embedding"})
)
```

### Example 2: Semantic Search

```python
def semantic_search(query: str, content_type: str = None, limit: int = 10):
    """
    Perform semantic search across indexed content

    Args:
        query: Natural language search query
        content_type: Filter by content type (optional)
        limit: Maximum results to return

    Returns:
        List of matching content with scores
    """
    # Generate query embedding
    query_embedding = generate_embedding(query)

    # Build filters
    filters = {}
    if content_type:
        filters["source_type"] = content_type

    # Search
    client = get_zerodb_client()
    results = client.vector_search(
        collection="content_index",
        query_vector=query_embedding,
        top_k=limit,
        filters=filters,
        min_score=0.7  # Only return relevant results
    )

    return results["results"]

# Usage
results = semantic_search("beginner friendly taekwondo classes", content_type="event")
for result in results:
    print(f"Score: {result['score']:.2f}")
    print(f"Title: {result['metadata']['title']}")
    print(f"URL: {result['metadata']['url']}")
    print("---")
```

### Example 3: Hybrid Search (Vector + Keyword)

```python
def hybrid_search(query: str, filters: dict = None, limit: int = 10):
    """
    Combine vector search with keyword filtering for better results
    """
    # Extract keywords from query
    keywords = extract_keywords(query)

    # Generate embedding
    query_embedding = generate_embedding(query)

    # Combine filters
    search_filters = filters or {}
    search_filters["keywords"] = {"$in": keywords}

    client = get_zerodb_client()
    results = client.vector_search(
        collection="content_index",
        query_vector=query_embedding,
        top_k=limit * 2,  # Get more results for keyword filtering
        filters=search_filters
    )

    # Re-rank based on combined score
    for result in results["results"]:
        keyword_score = calculate_keyword_match(keywords, result["metadata"]["keywords"])
        result["combined_score"] = 0.7 * result["score"] + 0.3 * keyword_score

    # Sort by combined score and return top results
    results["results"].sort(key=lambda x: x["combined_score"], reverse=True)
    return results["results"][:limit]
```

## Best Practices

### 1. Indexing Strategy

- **Incremental Indexing**: Index new content immediately upon creation
- **Batch Processing**: Use batch operations for bulk indexing (e.g., initial setup)
- **Update Strategy**: Re-index when content changes significantly (> 20% change)
- **Deletion**: Mark as `is_active: false` rather than deleting for audit trail

### 2. Search Optimization

- **Score Thresholds**: Set minimum score (0.7-0.8) to filter low-quality matches
- **Result Limits**: Start with top_k=10, adjust based on UI/UX needs
- **Caching**: Cache popular queries (Redis) for 5-15 minutes
- **Filtering**: Use metadata filters to narrow search space before vector search

### 3. Content Preparation

- **Text Cleaning**: Remove HTML, normalize whitespace, fix encoding
- **Context Addition**: Prepend title/category to chunk for better context
- **Language**: Ensure consistent language (primarily English for WWMAA)
- **Deduplication**: Avoid indexing duplicate or near-duplicate content

### 4. Monitoring

Track these metrics:
- Average search time (target: < 100ms)
- Average similarity scores (healthy: 0.7-0.95 for top results)
- Click-through rate on search results
- Number of queries with no results (target: < 5%)

### 5. Security

- **Access Control**: Filter results by user visibility level
- **PII Protection**: Don't include sensitive data in embeddings
- **Rate Limiting**: Limit search queries to prevent abuse
- **Input Validation**: Sanitize query inputs before embedding

## Performance Optimization

### 1. Index Optimization

```python
# Use appropriate search_weight for content prioritization
HIGH_PRIORITY = 2.0    # Featured events, important articles
NORMAL_PRIORITY = 1.0  # Regular content
LOW_PRIORITY = 0.5     # Archived or supplementary content
```

### 2. Query Optimization

```python
# Optimize for common queries
def optimized_search(query: str):
    # Check cache first
    cache_key = f"search:{hash(query)}"
    cached = redis_client.get(cache_key)
    if cached:
        return cached

    # Perform search
    results = semantic_search(query)

    # Cache results
    redis_client.setex(cache_key, 300, results)  # 5 min cache

    return results
```

### 3. Batch Operations

```python
# Process multiple documents efficiently
def index_content_batch(content_items: List[dict]):
    """Index multiple content items in one operation"""
    vectors = []

    for item in content_items:
        embedding = generate_embedding(item["text"])
        vectors.append({
            "vector": embedding,
            "metadata": item["metadata"]
        })

    # Single batch operation instead of multiple individual inserts
    client = get_zerodb_client()
    return client.batch_insert_vectors("content_index", vectors)
```

### 4. Metadata Filtering

```python
# Filter before vector search for better performance
filters = {
    "is_active": True,
    "visibility": "public",
    "source_type": {"$in": ["event", "article"]},
    "published_at": {"$gte": "2024-01-01"}
}

results = client.vector_search(
    collection="content_index",
    query_vector=embedding,
    filters=filters,  # Pre-filter to reduce search space
    top_k=10
)
```

## Troubleshooting

### Common Issues

#### 1. Low Similarity Scores

**Problem**: All search results have scores < 0.6

**Solutions**:
- Check embedding model consistency (same model for indexing and querying)
- Verify content quality (not too short or too generic)
- Review text preprocessing (ensure consistency)
- Consider re-embedding with better quality text

#### 2. Slow Search Performance

**Problem**: Search queries take > 500ms

**Solutions**:
- Add metadata filters to reduce search space
- Implement caching for common queries
- Use batch operations instead of multiple individual searches
- Check collection size (may need partitioning for > 1M documents)

#### 3. Embedding Dimension Mismatch

**Problem**: `ValueError: Embedding vector must have exactly 1536 dimensions`

**Solutions**:
- Verify embedding model outputs 1536 dimensions
- Check for truncated or padded vectors
- Ensure embedding generation is not failing silently

#### 4. No Results Returned

**Problem**: Search returns empty results for valid queries

**Solutions**:
- Check `is_active` flag on indexed content
- Verify `visibility` filters match user permissions
- Lower `min_score` threshold temporarily for testing
- Ensure content is properly indexed (check collection count)

#### 5. Duplicate Results

**Problem**: Same content appears multiple times in results

**Solutions**:
- Check for duplicate indexing (same source_id indexed multiple times)
- Implement deduplication in application layer
- Review chunking strategy (overlapping chunks too similar)

### Debug Utilities

```python
def debug_vector_search(query: str, collection: str = "content_index"):
    """Debug helper to inspect search results and scores"""
    client = get_zerodb_client()

    # Get embedding
    embedding = generate_embedding(query)

    print(f"Query: {query}")
    print(f"Embedding dimension: {len(embedding)}")
    print(f"Embedding sample: {embedding[:5]}...")

    # Search without filters
    results = client.vector_search(
        collection=collection,
        query_vector=embedding,
        top_k=20,
        include_metadata=True
    )

    print(f"\nTotal results: {len(results['results'])}")
    print("\nTop 5 results:")
    for i, result in enumerate(results['results'][:5], 1):
        print(f"\n{i}. Score: {result['score']:.4f}")
        print(f"   Title: {result['metadata']['title']}")
        print(f"   Type: {result['metadata']['source_type']}")
        print(f"   Preview: {result['metadata']['content_chunk'][:100]}...")

    return results
```

## References

- [OpenAI Embeddings Documentation](https://platform.openai.com/docs/guides/embeddings)
- [ZeroDB API Documentation](https://docs.ainative.studio/zerodb)
- [Cosine Similarity Explained](https://en.wikipedia.org/wiki/Cosine_similarity)
- [Vector Search Best Practices](https://www.pinecone.io/learn/vector-search/)

## Change Log

| Date | Version | Changes |
|------|---------|---------|
| 2024-11-10 | 1.0 | Initial documentation for US-035 |

## Support

For issues or questions:
- GitHub Issues: [wwmaa/backend](https://github.com/wwmaa/backend/issues)
- Email: dev@wwmaa.com
- Documentation: https://docs.wwmaa.com
