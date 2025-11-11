# WWMAA Performance Optimization Guide

## Overview

This guide documents common performance bottlenecks identified during load testing and provides proven optimization strategies for the WWMAA platform.

**Last Updated:** 2025-11-10
**Related:** US-080 (Load Testing), US-065 (OpenTelemetry), US-067 (Prometheus)

---

## Table of Contents

1. [Database Optimization](#database-optimization)
2. [Caching Strategies](#caching-strategies)
3. [API Performance](#api-performance)
4. [Search Optimization](#search-optimization)
5. [Real-Time Communication](#real-time-communication)
6. [Static Asset Delivery](#static-asset-delivery)
7. [Connection Pool Tuning](#connection-pool-tuning)
8. [Monitoring and Profiling](#monitoring-and-profiling)

---

## Database Optimization

### 1. Indexing Strategy

**Problem:** Slow queries during high load, especially for search and event listing.

**Solution:** Strategic database indexing on frequently queried columns.

#### Events Table Indexes

```sql
-- Composite index for event queries (status, date range, category)
CREATE INDEX idx_events_search ON events(status, start_date, category);

-- Index for location-based queries
CREATE INDEX idx_events_location ON events(location_city, location_state);

-- Index for instructor queries
CREATE INDEX idx_events_instructor ON events(instructor_id) WHERE instructor_id IS NOT NULL;

-- Full-text search index (if using PostgreSQL)
CREATE INDEX idx_events_fulltext ON events USING gin(to_tsvector('english', title || ' ' || description));
```

#### Event RSVPs Table Indexes

```sql
-- Composite index for RSVP lookups
CREATE INDEX idx_rsvps_event_user ON event_rsvps(event_id, user_id);

-- Index for user's RSVP history
CREATE INDEX idx_rsvps_user_status ON event_rsvps(user_id, status);

-- Index for event attendee list
CREATE INDEX idx_rsvps_event_status ON event_rsvps(event_id, status);
```

#### Users Table Indexes

```sql
-- Index for email lookups (login)
CREATE INDEX idx_users_email ON users(email) WHERE status = 'active';

-- Index for user search
CREATE INDEX idx_users_search ON users(first_name, last_name, status);
```

#### Verification

```sql
-- Check index usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- Find missing indexes (queries with high cost)
SELECT
    query,
    calls,
    total_time / calls as avg_time_ms,
    min_time,
    max_time
FROM pg_stat_statements
WHERE mean_time > 100  -- Queries taking > 100ms
ORDER BY avg_time_ms DESC
LIMIT 20;
```

### 2. Query Optimization

**Problem:** N+1 queries causing multiple database round trips.

**Solution:** Use eager loading and query optimization.

#### Python/SQLAlchemy Example

```python
# BAD: N+1 query
events = db.query(Event).all()
for event in events:
    instructor = event.instructor  # Separate query for each event
    rsvps = event.rsvps  # Separate query for each event

# GOOD: Eager loading
from sqlalchemy.orm import joinedload

events = (
    db.query(Event)
    .options(
        joinedload(Event.instructor),
        joinedload(Event.rsvps)
    )
    .all()
)
```

#### Query Result Limiting

```python
# Always use pagination for list endpoints
def get_events(page=1, limit=20):
    offset = (page - 1) * limit

    events = (
        db.query(Event)
        .filter(Event.status == 'active')
        .order_by(Event.start_date.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    total = db.query(Event).filter(Event.status == 'active').count()

    return {
        'events': events,
        'page': page,
        'limit': limit,
        'total': total,
        'pages': (total + limit - 1) // limit
    }
```

### 3. Connection Pooling

**Problem:** Connection pool exhaustion under load.

**Solution:** Optimize pool size and configuration.

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

# PostgreSQL connection pool configuration
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,              # Minimum connections
    max_overflow=20,           # Maximum additional connections
    pool_timeout=30,           # Wait time for connection
    pool_recycle=3600,         # Recycle connections after 1 hour
    pool_pre_ping=True,        # Verify connection before use
    echo=False,                # Disable SQL logging in production
)
```

**Monitoring:**

```sql
-- Check active connections
SELECT count(*), state
FROM pg_stat_activity
GROUP BY state;

-- Check connection pool usage
SELECT
    numbackends,
    xact_commit,
    xact_rollback,
    blks_read,
    blks_hit
FROM pg_stat_database
WHERE datname = 'wwmaa_production';
```

---

## Caching Strategies

### 1. Redis Cache Layer

**Problem:** Repeated queries for frequently accessed data.

**Solution:** Implement Redis caching with appropriate TTLs.

#### Cache Implementation

```python
import redis
import json
from functools import wraps

redis_client = redis.Redis(
    host='redis.wwmaa.com',
    port=6379,
    db=0,
    decode_responses=True
)

def cache_result(key_prefix, ttl=300):
    """Decorator for caching function results."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{hash(str(args) + str(kwargs))}"

            # Try to get from cache
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

            # Execute function
            result = func(*args, **kwargs)

            # Store in cache
            redis_client.setex(
                cache_key,
                ttl,
                json.dumps(result, default=str)
            )

            return result
        return wrapper
    return decorator
```

#### Cache Strategy by Endpoint

```python
from datetime import timedelta

# Event listings: 5 minute cache
@cache_result('events:list', ttl=300)
def get_events_list(filters):
    return db.query(Event).filter_by(**filters).all()

# Event details: 10 minute cache
@cache_result('events:detail', ttl=600)
def get_event_detail(event_id):
    return db.query(Event).filter_by(id=event_id).first()

# Search results: 10 minute cache
@cache_result('search:results', ttl=600)
def search_content(query, filters):
    return zerodb.search(query, filters)

# User session: 30 minute cache
@cache_result('user:session', ttl=1800)
def get_user_session(user_id):
    return db.query(User).filter_by(id=user_id).first()
```

#### Cache Invalidation

```python
def invalidate_cache_pattern(pattern):
    """Invalidate all keys matching pattern."""
    keys = redis_client.keys(pattern)
    if keys:
        redis_client.delete(*keys)

# Invalidate when data changes
def update_event(event_id, data):
    event = db.query(Event).filter_by(id=event_id).update(data)
    db.commit()

    # Invalidate related caches
    invalidate_cache_pattern(f'events:detail:{event_id}*')
    invalidate_cache_pattern('events:list:*')

    return event
```

### 2. Cache Warming

**Problem:** Cache misses during traffic spikes.

**Solution:** Pre-warm cache for popular content.

```python
import schedule
import time

def warm_popular_events():
    """Pre-cache popular events."""
    popular_event_ids = [1, 2, 3, 4, 5]  # From analytics

    for event_id in popular_event_ids:
        get_event_detail(event_id)  # Populates cache

    print(f"Warmed {len(popular_event_ids)} popular events")

def warm_trending_searches():
    """Pre-cache trending search queries."""
    trending_queries = ['karate', 'judo', 'aikido']  # From analytics

    for query in trending_queries:
        search_content(query, {})  # Populates cache

    print(f"Warmed {len(trending_queries)} trending searches")

# Schedule cache warming
schedule.every(5).minutes.do(warm_popular_events)
schedule.every(10).minutes.do(warm_trending_searches)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### 3. Cache Monitoring

```python
def get_cache_stats():
    """Get Redis cache statistics."""
    info = redis_client.info('stats')

    return {
        'hits': info['keyspace_hits'],
        'misses': info['keyspace_misses'],
        'hit_rate': info['keyspace_hits'] / (info['keyspace_hits'] + info['keyspace_misses']) * 100
                    if (info['keyspace_hits'] + info['keyspace_misses']) > 0 else 0,
        'memory_used': info['used_memory_human'],
        'connected_clients': info['connected_clients'],
    }
```

---

## API Performance

### 1. Rate Limiting

**Problem:** API abuse and unfair resource usage.

**Solution:** Implement per-user rate limiting.

```python
from fastapi import HTTPException, Request
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, redis_client, requests_per_minute=60):
        self.redis = redis_client
        self.requests_per_minute = requests_per_minute

    def is_allowed(self, user_id, endpoint):
        key = f"rate_limit:{endpoint}:{user_id}"
        current_minute = datetime.now().strftime("%Y%m%d%H%M")
        key_with_minute = f"{key}:{current_minute}"

        # Get current request count
        count = self.redis.get(key_with_minute)

        if count is None:
            # First request this minute
            self.redis.setex(key_with_minute, 60, 1)
            return True

        count = int(count)

        if count >= self.requests_per_minute:
            return False

        # Increment counter
        self.redis.incr(key_with_minute)
        return True

# Usage in FastAPI
rate_limiter = RateLimiter(redis_client, requests_per_minute=100)

@app.get("/api/search")
async def search(request: Request, query: str):
    user_id = get_user_id(request)

    if not rate_limiter.is_allowed(user_id, "search"):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later."
        )

    return perform_search(query)
```

### 2. Response Compression

**Problem:** Large response payloads increase latency.

**Solution:** Enable Gzip/Brotli compression.

```python
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware

app = FastAPI()

# Enable Gzip compression for responses > 1KB
app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### 3. Async Endpoints

**Problem:** Blocking I/O operations slow down API.

**Solution:** Use async/await for I/O-bound operations.

```python
import asyncio
from fastapi import FastAPI

app = FastAPI()

@app.get("/api/events/{event_id}")
async def get_event(event_id: int):
    # Run database query asynchronously
    event = await db.get_event_async(event_id)

    # Fetch related data in parallel
    instructor, rsvps = await asyncio.gather(
        db.get_instructor_async(event.instructor_id),
        db.get_rsvps_async(event_id)
    )

    return {
        'event': event,
        'instructor': instructor,
        'rsvps': rsvps
    }
```

---

## Search Optimization

### 1. ZeroDB Query Optimization

**Problem:** Slow semantic search queries under load.

**Solution:** Optimize embedding queries and implement caching.

```python
from zerodb import ZeroDBClient

zerodb = ZeroDBClient(api_key=ZERODB_API_KEY)

@cache_result('search:semantic', ttl=600)  # 10 minute cache
def semantic_search(query, filters=None, limit=20):
    """Optimized semantic search with caching."""
    results = zerodb.search(
        query=query,
        filters=filters,
        limit=limit,
        include_embeddings=False,  # Don't return embeddings (faster)
        timeout=5.0  # 5 second timeout
    )

    return results
```

### 2. Search Result Pagination

```python
def paginated_search(query, page=1, per_page=20):
    """Paginated search results."""
    offset = (page - 1) * per_page

    # Check cache first
    cache_key = f"search:{query}:{page}:{per_page}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    # Perform search
    results = zerodb.search(
        query=query,
        limit=per_page,
        offset=offset
    )

    # Cache results
    redis_client.setex(cache_key, 600, json.dumps(results, default=str))

    return results
```

### 3. Search Query Debouncing

**Frontend optimization to reduce search API calls:**

```typescript
// hooks/use-debounced-search.ts
import { useState, useEffect } from 'react';
import { useDebounce } from 'use-debounce';

export function useDebouncedSearch(query: string, delay: number = 500) {
  const [debouncedQuery] = useDebounce(query, delay);
  const [results, setResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);

  useEffect(() => {
    if (debouncedQuery.length < 3) {
      setResults([]);
      return;
    }

    setIsSearching(true);

    fetch(`/api/search?q=${encodeURIComponent(debouncedQuery)}`)
      .then(res => res.json())
      .then(data => {
        setResults(data.results);
        setIsSearching(false);
      })
      .catch(err => {
        console.error('Search failed:', err);
        setIsSearching(false);
      });
  }, [debouncedQuery]);

  return { results, isSearching };
}
```

---

## Real-Time Communication

### 1. WebSocket Connection Management

**Problem:** WebSocket connection pool exhaustion.

**Solution:** Implement connection pooling and heartbeat.

```python
from fastapi import WebSocket
import asyncio

class WebSocketManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}
        self.heartbeat_interval = 30  # seconds

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()

        if session_id not in self.active_connections:
            self.active_connections[session_id] = []

        self.active_connections[session_id].append(websocket)

        # Start heartbeat
        asyncio.create_task(self.heartbeat(websocket))

    async def disconnect(self, websocket: WebSocket, session_id: str):
        if session_id in self.active_connections:
            self.active_connections[session_id].remove(websocket)

            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

    async def heartbeat(self, websocket: WebSocket):
        """Send periodic heartbeat to keep connection alive."""
        try:
            while True:
                await asyncio.sleep(self.heartbeat_interval)
                await websocket.send_json({'type': 'ping'})
        except:
            pass  # Connection closed

    async def broadcast(self, session_id: str, message: dict):
        """Broadcast message to all connections in session."""
        if session_id not in self.active_connections:
            return

        disconnected = []

        for connection in self.active_connections[session_id]:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)

        # Remove disconnected clients
        for connection in disconnected:
            await self.disconnect(connection, session_id)

manager = WebSocketManager()
```

### 2. Redis Pub/Sub for Multi-Server WebSocket

**Problem:** Messages not broadcast across multiple WebSocket servers.

**Solution:** Use Redis pub/sub for cross-server messaging.

```python
import redis.asyncio as redis
import asyncio
import json

class RedisWebSocketBridge:
    def __init__(self, redis_url):
        self.redis = redis.from_url(redis_url)
        self.pubsub = self.redis.pubsub()

    async def publish_message(self, session_id: str, message: dict):
        """Publish message to Redis channel."""
        channel = f"session:{session_id}"
        await self.redis.publish(channel, json.dumps(message))

    async def subscribe_session(self, session_id: str, callback):
        """Subscribe to session messages."""
        channel = f"session:{session_id}"
        await self.pubsub.subscribe(channel)

        async for message in self.pubsub.listen():
            if message['type'] == 'message':
                data = json.loads(message['data'])
                await callback(data)

# Usage
bridge = RedisWebSocketBridge(REDIS_URL)

@app.websocket("/ws/session/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)

    # Subscribe to Redis channel
    async def on_redis_message(message):
        await websocket.send_json(message)

    asyncio.create_task(bridge.subscribe_session(session_id, on_redis_message))

    try:
        while True:
            data = await websocket.receive_json()

            # Publish to Redis (broadcasts to all servers)
            await bridge.publish_message(session_id, data)
    except:
        await manager.disconnect(websocket, session_id)
```

---

## Static Asset Delivery

### 1. CDN Configuration

**Problem:** Static assets served from application server.

**Solution:** Use CDN for static asset delivery.

```typescript
// next.config.js
module.exports = {
  assetPrefix: process.env.CDN_URL || '',
  images: {
    domains: ['cdn.wwmaa.com'],
    formats: ['image/webp', 'image/avif'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
  },
};
```

### 2. Image Optimization

```typescript
// components/optimized-image.tsx
import Image from 'next/image';

export function OptimizedImage({ src, alt, ...props }) {
  return (
    <Image
      src={src}
      alt={alt}
      loading="lazy"
      quality={80}
      placeholder="blur"
      {...props}
    />
  );
}
```

### 3. Asset Caching Headers

```python
from fastapi import Response
from fastapi.staticfiles import StaticFiles

class CachedStaticFiles(StaticFiles):
    def file_response(self, *args, **kwargs):
        response = super().file_response(*args, **kwargs)

        # Cache static assets for 1 year
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        response.headers["X-Content-Type-Options"] = "nosniff"

        return response

app.mount("/static", CachedStaticFiles(directory="static"), name="static")
```

---

## Connection Pool Tuning

### 1. PostgreSQL Configuration

```ini
# postgresql.conf

# Connection settings
max_connections = 100
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 2621kB
min_wal_size = 1GB
max_wal_size = 4GB
```

### 2. Redis Configuration

```ini
# redis.conf

# Connection settings
maxclients 10000
timeout 300
tcp-keepalive 60

# Memory management
maxmemory 2gb
maxmemory-policy allkeys-lru

# Performance
tcp-backlog 511
databases 16
```

### 3. Application Pool Configuration

```python
# config.py

import os

# Database
DATABASE_POOL_SIZE = int(os.getenv('DB_POOL_SIZE', 20))
DATABASE_MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', 20))
DATABASE_POOL_TIMEOUT = int(os.getenv('DB_POOL_TIMEOUT', 30))
DATABASE_POOL_RECYCLE = int(os.getenv('DB_POOL_RECYCLE', 3600))

# Redis
REDIS_MAX_CONNECTIONS = int(os.getenv('REDIS_MAX_CONNECTIONS', 50))
REDIS_SOCKET_TIMEOUT = int(os.getenv('REDIS_SOCKET_TIMEOUT', 5))
REDIS_SOCKET_CONNECT_TIMEOUT = int(os.getenv('REDIS_SOCKET_CONNECT_TIMEOUT', 5))
```

---

## Monitoring and Profiling

### 1. Query Performance Monitoring

```sql
-- Enable pg_stat_statements
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- View slowest queries
SELECT
    query,
    calls,
    total_time / 1000 as total_seconds,
    mean_time / 1000 as avg_seconds,
    max_time / 1000 as max_seconds
FROM pg_stat_statements
WHERE query NOT LIKE '%pg_stat_statements%'
ORDER BY total_time DESC
LIMIT 20;

-- Reset statistics
SELECT pg_stat_statements_reset();
```

### 2. Application Profiling

```python
import cProfile
import pstats
from functools import wraps

def profile(output_file=None):
    """Decorator to profile function execution."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            profiler = cProfile.Profile()
            profiler.enable()

            result = func(*args, **kwargs)

            profiler.disable()

            if output_file:
                profiler.dump_stats(output_file)
            else:
                stats = pstats.Stats(profiler)
                stats.sort_stats('cumulative')
                stats.print_stats(20)

            return result
        return wrapper
    return decorator

# Usage
@profile(output_file='search_profile.prof')
def perform_search(query):
    return search_implementation(query)
```

### 3. Custom Metrics

```python
from prometheus_client import Counter, Histogram, Gauge

# Custom Prometheus metrics
search_requests = Counter(
    'search_requests_total',
    'Total search requests',
    ['query_type']
)

search_latency = Histogram(
    'search_latency_seconds',
    'Search query latency',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
)

cache_hit_rate = Gauge(
    'cache_hit_rate',
    'Cache hit rate percentage'
)

# Usage
def perform_search(query, query_type='semantic'):
    search_requests.labels(query_type=query_type).inc()

    with search_latency.time():
        results = zerodb.search(query)

    return results
```

---

## Performance Checklist

Before deploying to production, ensure:

- [ ] Database indexes created on all high-traffic tables
- [ ] Connection pools properly sized (20-50 connections)
- [ ] Redis caching implemented for frequently accessed data
- [ ] Cache hit rate > 70%
- [ ] Rate limiting enabled on all public APIs
- [ ] Response compression enabled (Gzip/Brotli)
- [ ] CDN configured for static assets
- [ ] Image optimization implemented (WebP, lazy loading)
- [ ] WebSocket connection management in place
- [ ] Monitoring dashboards configured (Grafana)
- [ ] Alerting rules configured (Prometheus)
- [ ] Load tests passing with metrics within targets
- [ ] Auto-scaling policies configured
- [ ] Slow query alerts configured

---

## Additional Resources

- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [Redis Performance Optimization](https://redis.io/docs/management/optimization/)
- [FastAPI Performance](https://fastapi.tiangolo.com/async/)
- [k6 Load Testing](https://k6.io/docs/)
- [OpenTelemetry Best Practices](https://opentelemetry.io/docs/concepts/performance/)

---

**Maintained by:** DevOps Team
**Questions:** Contact #devops on Slack
**Updates:** Submit PR to this document with optimization findings
