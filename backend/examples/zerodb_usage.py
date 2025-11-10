"""
ZeroDB Client Usage Examples

This file demonstrates how to use the ZeroDB client wrapper for various operations.
"""

from backend.services.zerodb_service import ZeroDBClient, get_zerodb_client
from datetime import datetime

# Example 1: Initialize a client
def example_initialize_client():
    """Initialize ZeroDB client"""
    # Using default configuration from .env
    client = ZeroDBClient()

    # Or with custom configuration
    custom_client = ZeroDBClient(
        api_key="your_api_key",
        base_url="https://api.ainative.studio",
        timeout=15
    )

    # Using as context manager (recommended)
    with ZeroDBClient() as client:
        # Client will automatically close when done
        pass


# Example 2: CRUD Operations
def example_crud_operations():
    """Demonstrate CRUD operations"""
    client = get_zerodb_client()

    # CREATE - Add a new user
    user_data = {
        "email": "john.doe@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "role": "member",
        "state": "CA",
        "disciplines": ["karate", "judo"],
        "created_at": datetime.utcnow().isoformat()
    }

    created_user = client.create_document("users", user_data)
    print(f"Created user with ID: {created_user['id']}")

    # READ - Get a specific user
    user_id = created_user['id']
    user = client.get_document("users", user_id)
    print(f"Retrieved user: {user['data']['email']}")

    # UPDATE - Update user information
    updated_data = {
        "phone": "+1-555-1234",
        "updated_at": datetime.utcnow().isoformat()
    }

    updated_user = client.update_document("users", user_id, updated_data, merge=True)
    print(f"Updated user: {updated_user}")

    # DELETE - Remove a user
    result = client.delete_document("users", user_id)
    print(f"Deleted user: {result}")


# Example 3: Query Documents
def example_query_documents():
    """Demonstrate document querying with filters"""
    client = get_zerodb_client()

    # Query active members in California
    filters = {
        "status": "active",
        "role": "member",
        "state": "CA"
    }

    results = client.query_documents(
        collection="users",
        filters=filters,
        limit=20,
        offset=0,
        sort={"created_at": "desc"}
    )

    print(f"Found {len(results['documents'])} users")
    for doc in results['documents']:
        print(f"  - {doc['data']['email']}")


# Example 4: Vector Search
def example_vector_search():
    """Demonstrate semantic vector search"""
    client = get_zerodb_client()

    # Assuming you have embeddings from an AI model
    query_embedding = [0.1, 0.2, 0.3, ...]  # 768-dim vector from embedding model

    # Search for similar content
    results = client.vector_search(
        collection="content_index",
        query_vector=query_embedding,
        top_k=10,
        filters={"category": "martial_arts"},
        include_metadata=True
    )

    print(f"Found {len(results['results'])} similar documents")
    for result in results['results']:
        print(f"  - {result['data']['title']} (score: {result['score']})")


# Example 5: Object Storage - Upload File
def example_upload_file():
    """Upload a file to ZeroDB object storage"""
    client = get_zerodb_client()

    # Upload a profile picture
    file_path = "/path/to/profile.jpg"

    result = client.upload_object(
        file_path=file_path,
        object_name="profiles/user_123_profile.jpg",
        metadata={"user_id": "123", "type": "profile_picture"},
        content_type="image/jpeg"
    )

    print(f"Uploaded file: {result['url']}")


# Example 6: Object Storage - Download File
def example_download_file():
    """Download a file from ZeroDB object storage"""
    client = get_zerodb_client()

    # Download to memory
    file_bytes = client.download_object("profiles/user_123_profile.jpg")
    print(f"Downloaded {len(file_bytes)} bytes")

    # Or download to file
    save_path = "/path/to/save/profile.jpg"
    result = client.download_object(
        "profiles/user_123_profile.jpg",
        save_path=save_path
    )
    print(f"File saved to: {result}")


# Example 7: Object Storage - List Objects
def example_list_objects():
    """List objects in storage"""
    client = get_zerodb_client()

    # List all profile pictures
    results = client.list_objects(
        prefix="profiles/",
        limit=50
    )

    print(f"Found {len(results['objects'])} objects")
    for obj in results['objects']:
        print(f"  - {obj['name']} ({obj['size']} bytes)")


# Example 8: Error Handling
def example_error_handling():
    """Demonstrate proper error handling"""
    from backend.services.zerodb_service import (
        ZeroDBError,
        ZeroDBAuthenticationError,
        ZeroDBNotFoundError,
        ZeroDBValidationError,
        ZeroDBConnectionError
    )

    client = get_zerodb_client()

    try:
        # Try to get a non-existent document
        user = client.get_document("users", "nonexistent_id")
    except ZeroDBNotFoundError as e:
        print(f"Document not found: {e}")
    except ZeroDBAuthenticationError as e:
        print(f"Authentication failed: {e}")
    except ZeroDBConnectionError as e:
        print(f"Connection error: {e}")
    except ZeroDBValidationError as e:
        print(f"Validation error: {e}")
    except ZeroDBError as e:
        print(f"General ZeroDB error: {e}")


# Example 9: Batch Operations
def example_batch_operations():
    """Create multiple documents efficiently"""
    client = get_zerodb_client()

    # Create multiple promotions
    promotions = [
        {
            "title": "10% Off All Equipment",
            "company": "Martial Arts Pro Shop",
            "discount_percentage": 10,
            "status": "active"
        },
        {
            "title": "Free Trial Month",
            "company": "Elite Karate Academy",
            "discount_percentage": 100,
            "status": "pending"
        }
    ]

    created_promotions = []
    for promo in promotions:
        result = client.create_document("promotions", promo)
        created_promotions.append(result)

    print(f"Created {len(created_promotions)} promotions")


# Example 10: Pagination
def example_pagination():
    """Paginate through large result sets"""
    client = get_zerodb_client()

    page_size = 20
    offset = 0
    all_users = []

    while True:
        results = client.query_documents(
            collection="users",
            filters={"status": "active"},
            limit=page_size,
            offset=offset
        )

        documents = results.get("documents", [])
        if not documents:
            break

        all_users.extend(documents)
        offset += page_size

        print(f"Fetched page at offset {offset}, total so far: {len(all_users)}")

    print(f"Total active users: {len(all_users)}")


if __name__ == "__main__":
    print("ZeroDB Client Usage Examples")
    print("=" * 50)

    # Run examples (commented out to prevent actual API calls)
    # example_initialize_client()
    # example_crud_operations()
    # example_query_documents()
    # example_vector_search()
    # example_upload_file()
    # example_download_file()
    # example_list_objects()
    # example_error_handling()
    # example_batch_operations()
    # example_pagination()
