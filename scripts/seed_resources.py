"""
Seed Sample Resources Script

Creates sample training resources in the database for testing and demonstration.
This script populates the resources collection with various types of resources
(videos, documents, PDFs) with different visibility levels.

Usage:
    python -m scripts.seed_resources
"""

import sys
import os
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.services.zerodb_service import get_zerodb_client
from backend.models.schemas import (
    ResourceCategory,
    ResourceVisibility,
    ResourceStatus,
)


# Sample resources data
SAMPLE_RESOURCES = [
    {
        "title": "Introduction to Brazilian Jiu-Jitsu",
        "description": "A comprehensive beginner's guide to Brazilian Jiu-Jitsu covering basic positions, submissions, and escapes. Perfect for new students starting their martial arts journey.",
        "category": ResourceCategory.VIDEO,
        "tags": ["bjj", "beginner", "fundamentals", "tutorial"],
        "external_url": "https://www.youtube.com/watch?v=example1",
        "visibility": ResourceVisibility.MEMBERS_ONLY,
        "status": ResourceStatus.PUBLISHED,
        "discipline": "Brazilian Jiu-Jitsu",
        "is_featured": True,
        "display_order": 1,
        "cloudflare_stream_id": "abc123def456",
        "video_duration_seconds": 1800,  # 30 minutes
        "thumbnail_url": "https://storage.wwmaa.com/thumbnails/bjj-intro.jpg"
    },
    {
        "title": "Advanced Guard Passing Techniques",
        "description": "Detailed breakdown of advanced guard passing strategies used by world-class competitors. Includes pressure passing, toreando, and leg drag techniques.",
        "category": ResourceCategory.VIDEO,
        "tags": ["bjj", "advanced", "guard-passing", "competition"],
        "external_url": "https://www.youtube.com/watch?v=example2",
        "visibility": ResourceVisibility.MEMBERS_ONLY,
        "status": ResourceStatus.PUBLISHED,
        "discipline": "Brazilian Jiu-Jitsu",
        "is_featured": True,
        "display_order": 2,
        "cloudflare_stream_id": "xyz789uvw456",
        "video_duration_seconds": 2400,  # 40 minutes
        "thumbnail_url": "https://storage.wwmaa.com/thumbnails/guard-passing.jpg"
    },
    {
        "title": "WWMAA Student Handbook 2025",
        "description": "Official student handbook containing code of conduct, training guidelines, belt promotion requirements, and organizational policies. Required reading for all members.",
        "category": ResourceCategory.PDF,
        "tags": ["handbook", "policies", "requirements", "essential"],
        "file_url": "https://storage.wwmaa.com/documents/student-handbook-2025.pdf",
        "file_name": "student-handbook-2025.pdf",
        "file_size_bytes": 2457600,  # 2.4 MB
        "file_type": "application/pdf",
        "visibility": ResourceVisibility.MEMBERS_ONLY,
        "status": ResourceStatus.PUBLISHED,
        "is_featured": False,
        "display_order": 10
    },
    {
        "title": "Training Log Template",
        "description": "Downloadable training log template to track your progress, techniques learned, and goals. Helps students stay organized and monitor their development.",
        "category": ResourceCategory.DOCUMENT,
        "tags": ["template", "tracking", "progress", "planning"],
        "file_url": "https://storage.wwmaa.com/documents/training-log-template.docx",
        "file_name": "training-log-template.docx",
        "file_size_bytes": 51200,  # 50 KB
        "file_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "visibility": ResourceVisibility.PUBLIC,
        "status": ResourceStatus.PUBLISHED,
        "is_featured": False,
        "display_order": 15
    },
    {
        "title": "Nutrition Guide for Martial Artists",
        "description": "Evidence-based nutrition recommendations for martial arts training and competition. Covers macronutrients, hydration, meal timing, and weight management strategies.",
        "category": ResourceCategory.PDF,
        "tags": ["nutrition", "health", "performance", "wellness"],
        "file_url": "https://storage.wwmaa.com/documents/nutrition-guide.pdf",
        "file_name": "nutrition-guide.pdf",
        "file_size_bytes": 1843200,  # 1.8 MB
        "file_type": "application/pdf",
        "visibility": ResourceVisibility.MEMBERS_ONLY,
        "status": ResourceStatus.PUBLISHED,
        "is_featured": False,
        "display_order": 20
    },
    {
        "title": "Instructor Certification Requirements",
        "description": "Comprehensive guide to WWMAA instructor certification process, including prerequisites, training hours, examination content, and ongoing education requirements.",
        "category": ResourceCategory.PDF,
        "tags": ["instructor", "certification", "teaching", "requirements"],
        "file_url": "https://storage.wwmaa.com/documents/instructor-cert-requirements.pdf",
        "file_name": "instructor-cert-requirements.pdf",
        "file_size_bytes": 983040,  # 960 KB
        "file_type": "application/pdf",
        "visibility": ResourceVisibility.INSTRUCTORS_ONLY,
        "status": ResourceStatus.PUBLISHED,
        "is_featured": False,
        "display_order": 30
    },
    {
        "title": "2025 Tournament Schedule",
        "description": "Complete schedule of WWMAA-sanctioned tournaments for 2025, including registration deadlines, weight classes, and competition rules.",
        "category": ResourceCategory.ARTICLE,
        "tags": ["tournament", "competition", "schedule", "2025"],
        "external_url": "https://www.wwmaa.com/tournaments/2025-schedule",
        "visibility": ResourceVisibility.PUBLIC,
        "status": ResourceStatus.PUBLISHED,
        "is_featured": True,
        "display_order": 5
    },
    {
        "title": "Warm-Up and Mobility Routine",
        "description": "20-minute warm-up and mobility routine designed specifically for martial arts training. Reduces injury risk and improves performance.",
        "category": ResourceCategory.VIDEO,
        "tags": ["warm-up", "mobility", "injury-prevention", "preparation"],
        "external_url": "https://www.youtube.com/watch?v=example3",
        "visibility": ResourceVisibility.MEMBERS_ONLY,
        "status": ResourceStatus.PUBLISHED,
        "discipline": "General",
        "is_featured": False,
        "display_order": 12,
        "cloudflare_stream_id": "warmup123",
        "video_duration_seconds": 1200,  # 20 minutes
        "thumbnail_url": "https://storage.wwmaa.com/thumbnails/warmup.jpg"
    },
    {
        "title": "Draft: Advanced Teaching Methodology",
        "description": "Draft document covering advanced teaching techniques for instructors. This is still being developed and reviewed.",
        "category": ResourceCategory.DOCUMENT,
        "tags": ["teaching", "instructor", "methodology", "draft"],
        "file_url": "https://storage.wwmaa.com/documents/teaching-methodology-draft.pdf",
        "file_name": "teaching-methodology-draft.pdf",
        "file_size_bytes": 512000,  # 500 KB
        "file_type": "application/pdf",
        "visibility": ResourceVisibility.INSTRUCTORS_ONLY,
        "status": ResourceStatus.DRAFT,
        "is_featured": False,
        "display_order": 100
    }
]


async def seed_resources():
    """Seed sample resources into the database"""
    db_client = get_zerodb_client()

    print("=" * 80)
    print("WWMAA Resources Seeding Script")
    print("=" * 80)
    print()

    # Create a test admin user ID for created_by field
    admin_user_id = str(uuid4())
    print(f"Using admin user ID: {admin_user_id}")
    print()

    created_count = 0
    skipped_count = 0

    for resource_data in SAMPLE_RESOURCES:
        try:
            # Check if resource already exists by title
            existing = db_client.query_documents(
                collection="resources",
                filters={"title": resource_data["title"]},
                limit=1
            )

            if existing.get("documents"):
                print(f"⏭️  SKIPPED: '{resource_data['title']}' (already exists)")
                skipped_count += 1
                continue

            # Prepare resource document
            resource_id = str(uuid4())
            now = datetime.utcnow()

            # Build resource data
            resource_doc = {
                "title": resource_data["title"],
                "description": resource_data["description"],
                "category": resource_data["category"].value,
                "tags": resource_data["tags"],
                "visibility": resource_data["visibility"].value,
                "status": resource_data["status"].value,
                "is_featured": resource_data["is_featured"],
                "display_order": resource_data["display_order"],
                "created_by": admin_user_id,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
                "view_count": 0,
                "download_count": 0,
            }

            # Add optional fields
            if "file_url" in resource_data:
                resource_doc["file_url"] = resource_data["file_url"]
                resource_doc["file_name"] = resource_data.get("file_name")
                resource_doc["file_size_bytes"] = resource_data.get("file_size_bytes")
                resource_doc["file_type"] = resource_data.get("file_type")

            if "external_url" in resource_data:
                resource_doc["external_url"] = resource_data["external_url"]

            if "discipline" in resource_data:
                resource_doc["discipline"] = resource_data["discipline"]

            if "cloudflare_stream_id" in resource_data:
                resource_doc["cloudflare_stream_id"] = resource_data["cloudflare_stream_id"]
                resource_doc["video_duration_seconds"] = resource_data.get("video_duration_seconds")
                resource_doc["thumbnail_url"] = resource_data.get("thumbnail_url")

            # Set published_at for published resources
            if resource_data["status"] == ResourceStatus.PUBLISHED:
                resource_doc["published_at"] = now.isoformat()
                resource_doc["published_by"] = admin_user_id

            # Create resource in database
            db_client.create_document(
                collection="resources",
                data=resource_doc,
                document_id=resource_id
            )

            status_emoji = "✅" if resource_data["status"] == ResourceStatus.PUBLISHED else "📝"
            visibility_emoji = {
                ResourceVisibility.PUBLIC: "🌍",
                ResourceVisibility.MEMBERS_ONLY: "👥",
                ResourceVisibility.INSTRUCTORS_ONLY: "🎓",
                ResourceVisibility.ADMIN_ONLY: "🔒"
            }.get(resource_data["visibility"], "❓")

            print(f"{status_emoji} {visibility_emoji} CREATED: '{resource_data['title']}'")
            print(f"   Category: {resource_data['category'].value}")
            print(f"   Visibility: {resource_data['visibility'].value}")
            print(f"   Status: {resource_data['status'].value}")
            print()

            created_count += 1

        except Exception as e:
            print(f"❌ ERROR creating '{resource_data['title']}': {e}")
            print()

    print("=" * 80)
    print(f"Seeding Complete!")
    print(f"  Created: {created_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Total: {len(SAMPLE_RESOURCES)}")
    print("=" * 80)
    print()
    print("You can now:")
    print("  1. Test the GET /api/resources endpoint")
    print("  2. View resources in the student dashboard")
    print("  3. Filter by category, discipline, or featured status")
    print()


if __name__ == "__main__":
    asyncio.run(seed_resources())
