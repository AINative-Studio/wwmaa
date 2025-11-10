# 🏗️ WWMAA Architecture Clarification

**Date:** January 2025
**Version:** 1.0

---

## Technology Stack Corrections

### ✅ **Confirmed Architecture**

#### **Frontend**
- **Framework:** Next.js 13+ (React, TypeScript)
- **UI Components:** shadcn/ui + Tailwind CSS
- **Styling:** Tailwind CSS
- **State Management:** React Context API
- **Client-Side:** TypeScript/JavaScript

#### **Backend API**
- ⚠️ **CORRECTED:** Python (NOT Node.js)
- **Framework:** Flask or FastAPI (to be determined)
- **Language:** Python 3.11+
- **API Structure:** RESTful APIs
- **File Extension:** `.py` (not `.ts`)

#### **Database**
- ⚠️ **CORRECTED:** AINative ZeroDB APIs (NOT Supabase)
- **Primary Data Store:** ZeroDB (ALL database operations)
- **Vector Search:** ZeroDB (semantic search)
- **Database Type:** Document/NoSQL-style via APIs
- **Access Method:** HTTP API calls to ZeroDB endpoints

---

## Architecture Implications

### **1. Database Layer**

#### **OLD (Incorrect):**
```
Frontend → Next.js API Routes (Node.js) → Supabase PostgreSQL
```

#### **NEW (Correct):**
```
Frontend (Next.js/React) → Python Backend API → ZeroDB APIs
```

### **2. Data Storage**

#### **NOT Using:**
- ❌ PostgreSQL
- ❌ Supabase
- ❌ SQL queries
- ❌ Database migrations (SQL files)
- ❌ Row-Level Security (RLS)
- ❌ SQL indexes
- ❌ Foreign key constraints (in SQL)

#### **NOW Using:**
- ✅ ZeroDB HTTP APIs
- ✅ JSON document storage
- ✅ API-based data operations (CRUD via HTTP)
- ✅ ZeroDB collections (not SQL tables)
- ✅ API-level authorization (not database-level RLS)
- ✅ Schema validation in Python code
- ✅ Vector embeddings for search

### **3. Backend Structure**

#### **File Structure:**
```
backend/
├── app.py                    # Flask/FastAPI main application
├── requirements.txt          # Python dependencies
├── config.py                 # Environment configuration
├── models/                   # Data models (Pydantic schemas)
│   ├── user.py
│   ├── application.py
│   ├── subscription.py
│   └── event.py
├── services/                 # Business logic
│   ├── zerodb_service.py    # ZeroDB API client
│   ├── auth_service.py      # Authentication logic
│   ├── payment_service.py   # Stripe integration
│   └── search_service.py    # AI search logic
├── routes/                   # API endpoints
│   ├── auth.py              # /api/auth/*
│   ├── applications.py      # /api/applications/*
│   ├── events.py            # /api/events/*
│   └── search.py            # /api/search/*
├── middleware/               # Middleware (rate limiting, auth)
│   ├── rate_limit.py
│   └── auth_middleware.py
├── utils/                    # Helper functions
│   ├── cache.py             # Redis/KV cache utils
│   ├── validation.py        # Input validation
│   └── email.py             # Email sending
└── tests/                    # Test files
    ├── test_auth.py
    └── test_applications.py
```

### **4. ZeroDB Operations**

#### **Collections (not SQL tables):**
- `users`
- `applications`
- `approvals`
- `subscriptions`
- `payments`
- `profiles`
- `events`
- `rsvps`
- `training_sessions`
- `session_attendance`
- `search_queries`
- `content_index`
- `media_assets`
- `audit_logs`

#### **Example ZeroDB API Calls (Python):**

```python
import requests

# ZeroDB API client
class ZeroDBClient:
    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def create_document(self, collection, data):
        """Create a new document in ZeroDB collection"""
        url = f"{self.base_url}/collections/{collection}/documents"
        response = requests.post(url, json=data, headers=self.headers)
        return response.json()

    def get_document(self, collection, document_id):
        """Get a document by ID"""
        url = f"{self.base_url}/collections/{collection}/documents/{document_id}"
        response = requests.get(url, headers=self.headers)
        return response.json()

    def query_documents(self, collection, filters=None, limit=10):
        """Query documents with filters"""
        url = f"{self.base_url}/collections/{collection}/query"
        payload = {"filters": filters or {}, "limit": limit}
        response = requests.post(url, json=payload, headers=self.headers)
        return response.json()

    def update_document(self, collection, document_id, data):
        """Update a document"""
        url = f"{self.base_url}/collections/{collection}/documents/{document_id}"
        response = requests.put(url, json=data, headers=self.headers)
        return response.json()

    def delete_document(self, collection, document_id):
        """Delete a document"""
        url = f"{self.base_url}/collections/{collection}/documents/{document_id}"
        response = requests.delete(url, headers=self.headers)
        return response.json()

    def vector_search(self, collection, query_vector, top_k=10):
        """Perform vector similarity search"""
        url = f"{self.base_url}/collections/{collection}/vector-search"
        payload = {"vector": query_vector, "top_k": top_k}
        response = requests.post(url, json=payload, headers=self.headers)
        return response.json()
```

#### **Example Usage:**

```python
from services.zerodb_service import zerodb_client

# Create user
user_data = {
    "email": "user@example.com",
    "name": "John Doe",
    "role": "member",
    "created_at": datetime.utcnow().isoformat()
}
user = zerodb_client.create_document("users", user_data)

# Query applications
filters = {"status": "pending", "created_at": {"$gte": "2025-01-01"}}
applications = zerodb_client.query_documents("applications", filters=filters, limit=20)

# Vector search
query_embedding = get_embedding("martial arts techniques")
results = zerodb_client.vector_search("content_index", query_embedding, top_k=10)
```

---

## Updated Environment Variables

### **Remove:**
- ❌ `NEXT_PUBLIC_SUPABASE_URL`
- ❌ `SUPABASE_ANON_KEY`
- ❌ `SUPABASE_SERVICE_ROLE_KEY`
- ❌ `DATABASE_URL`

### **Add/Keep:**
- ✅ `ZERODB_API_KEY` - ZeroDB API authentication
- ✅ `ZERODB_BASE_URL` - ZeroDB API endpoint
- ✅ `ZERODB_PROJECT_ID` - Project identifier
- ✅ `PYTHON_BACKEND_URL` - Backend API URL (e.g., `http://localhost:8000` or `https://api.wwmaa.com`)
- ✅ `STRIPE_SECRET_KEY`
- ✅ `STRIPE_WEBHOOK_SECRET`
- ✅ `JWT_SECRET`
- ✅ `REDIS_URL`
- ✅ `BEEHIIV_API_KEY`
- ✅ `CLOUDFLARE_ACCOUNT_ID`
- ✅ `CLOUDFLARE_API_TOKEN`
- ✅ `AINATIVE_API_KEY`
- ✅ `POSTMARK_API_KEY` (or SendGrid)

---

## Backend Framework Recommendation

### **Option 1: FastAPI (Recommended)**

**Pros:**
- Modern, fast (async/await support)
- Automatic API documentation (Swagger/OpenAPI)
- Built-in data validation (Pydantic)
- Type hints throughout
- Great for AI/ML integrations
- Excellent performance

**Example:**
```python
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel

app = FastAPI()

class ApplicationCreate(BaseModel):
    email: str
    name: str
    discipline: list[str]
    experience_years: int

@app.post("/api/applications")
async def create_application(app_data: ApplicationCreate):
    # Validate data (automatic via Pydantic)
    # Store in ZeroDB
    result = zerodb_client.create_document("applications", app_data.dict())
    return {"id": result["id"], "status": "pending"}
```

### **Option 2: Flask**

**Pros:**
- Simpler, more lightweight
- Mature ecosystem
- Easy to learn
- Good for smaller APIs

**Cons:**
- Less modern features
- Manual validation setup
- No built-in async support

---

## Deployment Considerations

### **Frontend (Next.js)**
- Deploy to: Vercel, Railway, or Cloudflare Pages
- Static pages + API proxy to Python backend
- Environment variable: `NEXT_PUBLIC_BACKEND_API_URL`

### **Backend (Python)**
- Deploy to: **Railway** (primary), or Render/Fly.io as alternatives
- Use: Gunicorn + Uvicorn workers (FastAPI) or Gunicorn (Flask)
- Containerize: Docker (optional but recommended)

### **Example Dockerfile (FastAPI):**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Storage Architecture (CRITICAL)

### **ZeroDB Provides THREE Services:**

1. **Document/Collection Storage** - All structured data (users, events, etc.)
2. **Vector Search** - Semantic search with embeddings
3. **Object Storage** - All file storage (images, documents, backups, certificates)

### **Cloudflare ONLY for Video:**

1. **Cloudflare Calls** - WebRTC for live training sessions
2. **Cloudflare Stream** - VOD for recorded training videos

### **NOT Using:**
- ❌ AWS S3
- ❌ Cloudflare R2
- ❌ Google Cloud Storage
- ❌ Azure Blob Storage

**All non-video files → ZeroDB Object Storage API**
**All videos → Cloudflare Stream**

See `STORAGE-ARCHITECTURE.md` for complete details.

---

## Next Steps

1. **Choose Backend Framework:** FastAPI (recommended) or Flask
2. **Set up Python project structure**
3. **Implement ZeroDB client wrapper**
4. **Define Pydantic models for all entities**
5. **Create API endpoints (routes)**
6. **Implement authentication middleware**
7. **Connect frontend to Python backend**
8. **Test ZeroDB operations**

---

## Questions to Confirm

1. **Backend Framework:** FastAPI or Flask? (Recommendation: FastAPI)
2. **ZeroDB API Documentation:** Do you have ZeroDB API docs/SDK?
3. **Deployment Platform:** Railway for both frontend and backend?
4. **Python Version:** 3.11+ is okay?
5. **Testing Framework:** pytest?

---

This document clarifies the corrected architecture and will guide the updated backlog.
