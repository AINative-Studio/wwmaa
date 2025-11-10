# 🗄️ WWMAA Storage Architecture

**Date:** January 2025
**Version:** 1.0 - FINAL

---

## ✅ Confirmed Storage Stack

### **1. ZeroDB (All Data + Object Storage)**

#### **A. Document/Collection Storage**
- **Purpose:** All structured application data
- **Collections:**
  - users, applications, approvals, subscriptions, payments
  - profiles, events, rsvps, training_sessions
  - search_queries, content_index, media_assets, audit_logs
- **Access:** ZeroDB HTTP API
- **Operations:** CRUD via API calls

#### **B. Vector Storage**
- **Purpose:** Semantic search embeddings
- **Used For:** AI-powered search feature
- **Collections:** content_index (with vector embeddings)
- **Access:** ZeroDB Vector Search API

#### **C. Object Storage**
- **Purpose:** File storage (images, documents, certificates, backups)
- **Used For:**
  - User profile pictures
  - Membership application certificates
  - Instructor credentials
  - Blog post images
  - Event promotional images
  - System backups (JSON exports)
  - Member directory photos
- **Access:** ZeroDB Object Storage API
- **API Endpoints:**
  - Upload: `POST /api/objects/upload`
  - Download: `GET /api/objects/{object_id}`
  - Delete: `DELETE /api/objects/{object_id}`
  - List: `GET /api/objects?collection=&prefix=`

---

### **2. Cloudflare (Video ONLY)**

#### **A. Cloudflare Calls**
- **Purpose:** WebRTC for live training sessions
- **Used For:** Real-time video conferencing during training
- **NOT Used For:** File storage, backups, or static content

#### **B. Cloudflare Stream**
- **Purpose:** Video-on-demand (VOD) storage and playback
- **Used For:**
  - Recorded training sessions
  - Tutorial videos
  - Event recordings
- **NOT Used For:** General file storage, images, or documents

#### **C. Cloudflare CDN (Optional)**
- **Purpose:** CDN for Next.js static assets (JS, CSS)
- **Used For:** Frontend performance optimization
- **NOT Used For:** User-generated content storage

---

### **3. Railway**
- **Purpose:** Hosting platform
- **Used For:**
  - Python backend API deployment
  - Next.js frontend deployment
  - Redis instance (caching, rate limiting)
- **NOT Used For:** Data storage or file storage

---

## ❌ Technologies NOT Used

### **Explicitly Excluded:**
- ❌ **AWS S3** - No Amazon Web Services at all
- ❌ **Cloudflare R2** - Using ZeroDB Object Storage instead
- ❌ **Supabase** - Using ZeroDB instead
- ❌ **PostgreSQL** - Using ZeroDB instead
- ❌ **MongoDB** - Using ZeroDB instead
- ❌ **Google Cloud Storage** - Using ZeroDB Object Storage instead
- ❌ **Azure Blob Storage** - Using ZeroDB Object Storage instead

---

## 📁 File Storage Mapping

| File Type | Storage Location | API Used |
|-----------|------------------|----------|
| **User Uploads** | ZeroDB Object Storage | ZeroDB Object API |
| Profile pictures | ZeroDB Object Storage | ZeroDB Object API |
| Application certificates | ZeroDB Object Storage | ZeroDB Object API |
| Instructor credentials | ZeroDB Object Storage | ZeroDB Object API |
| **Content Media** | ZeroDB Object Storage | ZeroDB Object API |
| Blog post images | ZeroDB Object Storage | ZeroDB Object API |
| Event promotional images | ZeroDB Object Storage | ZeroDB Object API |
| Founder profile photo | ZeroDB Object Storage | ZeroDB Object API |
| **System Files** | ZeroDB Object Storage | ZeroDB Object API |
| Database backups (JSON) | ZeroDB Object Storage | ZeroDB Object API |
| Export files | ZeroDB Object Storage | ZeroDB Object API |
| **Video Files** | Cloudflare Stream | Cloudflare Stream API |
| Training session recordings | Cloudflare Stream | Cloudflare Stream API |
| Tutorial videos | Cloudflare Stream | Cloudflare Stream API |
| Event recordings | Cloudflare Stream | Cloudflare Stream API |

---

## 🔧 Implementation Details

### **ZeroDB Object Storage Usage**

#### **Python Backend Example:**

```python
from services.zerodb_service import zerodb_client

# Upload file to ZeroDB Object Storage
def upload_file_to_zerodb(file_data, filename, collection="user-uploads"):
    """
    Upload file to ZeroDB Object Storage

    Args:
        file_data: Binary file data
        filename: Original filename
        collection: Logical grouping (e.g., 'profile-pictures', 'certificates')

    Returns:
        object_id: Unique identifier for the uploaded file
    """
    response = zerodb_client.upload_object(
        collection=collection,
        filename=filename,
        data=file_data,
        metadata={
            "uploaded_at": datetime.utcnow().isoformat(),
            "content_type": get_content_type(filename)
        }
    )
    return response["object_id"]

# Download file from ZeroDB Object Storage
def download_file_from_zerodb(object_id):
    """
    Download file from ZeroDB Object Storage

    Args:
        object_id: Unique identifier of the file

    Returns:
        file_data: Binary file data
        metadata: File metadata (filename, content_type, etc.)
    """
    response = zerodb_client.download_object(object_id)
    return response["data"], response["metadata"]

# Delete file from ZeroDB Object Storage
def delete_file_from_zerodb(object_id):
    """Delete file from ZeroDB Object Storage"""
    zerodb_client.delete_object(object_id)

# List files in collection
def list_files_in_zerodb(collection="user-uploads", prefix=None):
    """
    List files in ZeroDB Object Storage collection

    Args:
        collection: Logical grouping
        prefix: Optional prefix for filtering (e.g., 'user_123/')

    Returns:
        List of file objects with metadata
    """
    response = zerodb_client.list_objects(
        collection=collection,
        prefix=prefix
    )
    return response["objects"]
```

#### **Backup Strategy:**

```python
# Backup script: /backend/scripts/backup_to_zerodb.py

import json
from datetime import datetime
from services.zerodb_service import zerodb_client

def backup_collection(collection_name):
    """
    Export collection data to JSON and store in ZeroDB Object Storage

    Args:
        collection_name: Name of the collection to backup
    """
    # Export all documents from collection
    documents = zerodb_client.query_documents(
        collection=collection_name,
        filters={},
        limit=10000  # Adjust based on collection size
    )

    # Create JSON backup file
    backup_data = {
        "collection": collection_name,
        "backup_date": datetime.utcnow().isoformat(),
        "document_count": len(documents),
        "documents": documents
    }

    # Upload backup to ZeroDB Object Storage
    filename = f"{collection_name}_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    zerodb_client.upload_object(
        collection="system-backups",
        filename=filename,
        data=json.dumps(backup_data, indent=2).encode('utf-8'),
        metadata={
            "backup_type": "collection",
            "collection_name": collection_name,
            "backup_date": datetime.utcnow().isoformat()
        }
    )

    print(f"Backed up {len(documents)} documents from {collection_name} to {filename}")

# Backup all collections
def backup_all_collections():
    collections = [
        "users", "applications", "approvals", "subscriptions",
        "payments", "profiles", "events", "rsvps",
        "training_sessions", "search_queries", "content_index",
        "media_assets", "audit_logs"
    ]

    for collection in collections:
        backup_collection(collection)

if __name__ == "__main__":
    backup_all_collections()
```

#### **File Upload API Endpoint:**

```python
# /backend/routes/uploads.py

from fastapi import APIRouter, UploadFile, File, HTTPException
from services.zerodb_service import zerodb_client
from middleware.auth_middleware import require_auth

router = APIRouter()

@router.post("/api/uploads/profile-picture")
@require_auth
async def upload_profile_picture(file: UploadFile = File(...), user_id: str = None):
    """
    Upload user profile picture to ZeroDB Object Storage
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type")

    # Validate file size (max 5MB)
    file_data = await file.read()
    if len(file_data) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large")

    # Upload to ZeroDB Object Storage
    object_id = zerodb_client.upload_object(
        collection="profile-pictures",
        filename=f"{user_id}_{file.filename}",
        data=file_data,
        metadata={
            "user_id": user_id,
            "content_type": file.content_type,
            "uploaded_at": datetime.utcnow().isoformat()
        }
    )

    # Update user profile with new profile picture URL
    zerodb_client.update_document(
        collection="profiles",
        document_id=user_id,
        data={"profile_picture_id": object_id}
    )

    return {
        "object_id": object_id,
        "url": f"/api/uploads/{object_id}"
    }

@router.get("/api/uploads/{object_id}")
async def get_uploaded_file(object_id: str):
    """
    Download file from ZeroDB Object Storage
    """
    try:
        file_data, metadata = zerodb_client.download_object(object_id)

        return Response(
            content=file_data,
            media_type=metadata.get("content_type", "application/octet-stream"),
            headers={
                "Content-Disposition": f"inline; filename=\"{metadata.get('filename', 'file')}\""
            }
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail="File not found")
```

---

### **Cloudflare Video Usage (ONLY for Video)**

#### **Cloudflare Calls (WebRTC):**
```python
# /backend/services/cloudflare_calls_service.py

import requests

class CloudflareCallsService:
    def __init__(self, account_id, api_token):
        self.account_id = account_id
        self.api_token = api_token
        self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/calls"

    def create_room(self, room_name):
        """Create WebRTC room for live training"""
        response = requests.post(
            f"{self.base_url}/rooms",
            headers={"Authorization": f"Bearer {self.api_token}"},
            json={"name": room_name}
        )
        return response.json()

    def start_recording(self, room_id):
        """Start recording live session"""
        response = requests.post(
            f"{self.base_url}/rooms/{room_id}/recordings",
            headers={"Authorization": f"Bearer {self.api_token}"}
        )
        return response.json()
```

#### **Cloudflare Stream (VOD):**
```python
# /backend/services/cloudflare_stream_service.py

import requests

class CloudflareStreamService:
    def __init__(self, account_id, api_token):
        self.account_id = account_id
        self.api_token = api_token
        self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/stream"

    def upload_video(self, video_data, metadata):
        """Upload recorded training session to Cloudflare Stream"""
        response = requests.post(
            f"{self.base_url}/direct_upload",
            headers={"Authorization": f"Bearer {self.api_token}"},
            json={
                "maxDurationSeconds": 3600,
                "metadata": metadata
            }
        )
        return response.json()
```

---

## 🔒 Security Considerations

### **ZeroDB Object Storage:**
- **Access Control:** API key authentication
- **Permissions:** Set per-collection permissions
- **Encryption:** Data encrypted at rest (managed by ZeroDB)
- **Retention:** Configure retention policies per collection
- **Versioning:** Enable object versioning for critical files

### **Cloudflare Stream:**
- **Access Control:** Signed URLs for member-only videos
- **DRM:** Optional DRM for premium content
- **Geo-restrictions:** Optional geographic restrictions

---

## 📊 Cost Optimization

### **ZeroDB Object Storage:**
- Store backups with longer retention
- Use lifecycle policies to archive old backups
- Compress backup files before upload

### **Cloudflare Stream:**
- Delete old recordings after X months (configurable)
- Use lower quality for non-critical recordings
- Store transcripts separately in ZeroDB (cheaper)

---

## 🚀 Environment Variables

### **Required for ZeroDB Object Storage:**
```bash
ZERODB_API_KEY=your_api_key
ZERODB_BASE_URL=https://api.zerodb.io/v1
ZERODB_PROJECT_ID=your_project_id
ZERODB_OBJECT_STORAGE_BUCKET=wwmaa-objects  # Optional bucket/namespace
```

### **Required for Cloudflare Video:**
```bash
CLOUDFLARE_ACCOUNT_ID=your_account_id
CLOUDFLARE_API_TOKEN=your_api_token
CLOUDFLARE_CALLS_APP_ID=your_calls_app_id  # For WebRTC
```

---

## ✅ Summary

| Service | Purpose | What's Stored | API Used |
|---------|---------|---------------|----------|
| **ZeroDB Collections** | Structured data | All application data | ZeroDB HTTP API |
| **ZeroDB Object Storage** | File storage | Images, documents, certificates, backups | ZeroDB Object API |
| **ZeroDB Vector Search** | Semantic search | Content embeddings | ZeroDB Vector API |
| **Cloudflare Calls** | Live video | N/A (real-time only) | Cloudflare Calls API |
| **Cloudflare Stream** | VOD | Recorded training videos | Cloudflare Stream API |
| **Railway** | Hosting | N/A (compute only) | N/A |

**NO AWS, NO CLOUDFLARE R2, NO OTHER CLOUD STORAGE**

Everything except video goes to **ZeroDB Object Storage API**.
