"""
Seed Sample Events for Testing

This script creates sample events in the database for testing the
Event Creation functionality (GitHub Issue #12).

Creates:
- Draft event (unpublished)
- Published event (visible on public events page)
- Online seminar event (published)
"""

import sys
import os
from datetime import datetime, timedelta
from uuid import uuid4

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.services.event_service import get_event_service
from backend.services.zerodb_service import get_zerodb_client
from backend.models.schemas import EventType, EventVisibility, EventStatus


def seed_events():
    """Seed sample events for testing"""
    print("=" * 80)
    print("SEEDING SAMPLE EVENTS FOR TESTING")
    print("=" * 80)

    event_service = get_event_service()
    db_client = get_zerodb_client()

    # Create a test admin user ID
    # In production, this would be an actual admin user UUID from the users collection
    admin_user_id = uuid4()
    print(f"\nUsing admin user ID: {admin_user_id}")

    # Sample events to create
    events = [
        {
            "title": "Summer Martial Arts Training Camp",
            "description": "<p>Join us for an intensive 3-day summer training camp featuring world-class instructors from multiple disciplines. This camp is designed for intermediate to advanced practitioners looking to enhance their skills and learn new techniques.</p><p><strong>What to Expect:</strong></p><ul><li>Daily training sessions in Karate, Judo, and Brazilian Jiu-Jitsu</li><li>Specialized workshops on competition strategy</li><li>Conditioning and flexibility training</li><li>Networking opportunities with martial artists worldwide</li></ul>",
            "event_type": EventType.LIVE_TRAINING.value,
            "visibility": EventVisibility.PUBLIC.value,
            "start_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "end_date": (datetime.now() + timedelta(days=33)).isoformat(),
            "timezone": "America/Los_Angeles",
            "location": "WWMAA Training Center, Los Angeles, CA",
            "is_online": False,
            "capacity": 50,
            "price": 299.99,
            "instructor_info": "Master Chen (8th Dan), Sensei Rodriguez (7th Dan), Professor Silva (6th Dan)",
            "status": EventStatus.PUBLISHED.value,  # Published - will appear on public page
        },
        {
            "title": "International Martial Arts Seminar - Advanced Techniques",
            "description": "<p>An exclusive online seminar featuring renowned martial arts masters from around the world. Learn advanced techniques, philosophy, and teaching methods.</p><p><strong>Seminar Topics:</strong></p><ul><li>Advanced striking combinations</li><li>Grappling and ground fighting strategies</li><li>Kata and forms mastery</li><li>Meditation and mental preparation</li><li>Teaching methodology for instructors</li></ul><p>Certificate of attendance provided to all participants.</p>",
            "event_type": EventType.SEMINAR.value,
            "visibility": EventVisibility.PUBLIC.value,
            "start_date": (datetime.now() + timedelta(days=45)).isoformat(),
            "end_date": (datetime.now() + timedelta(days=45, hours=4)).isoformat(),
            "timezone": "America/New_York",
            "location": "Online",
            "is_online": True,
            "virtual_url": "https://wwmaa.com/seminars/advanced-techniques",
            "capacity": 200,
            "price": 49.99,
            "instructor_info": "Multiple international instructors - see event details",
            "status": EventStatus.PUBLISHED.value,  # Published - will appear on public page
        },
        {
            "title": "Regional Championship Tournament - Fall 2025",
            "description": "<p>Annual regional championship tournament featuring competitors from across the country. Multiple divisions and categories available.</p><p><strong>Competition Categories:</strong></p><ul><li>Kumite (Sparring) - All belt levels</li><li>Kata (Forms) - Traditional and freestyle</li><li>Weapons demonstrations</li><li>Team events</li></ul><p>Registration deadline: 2 weeks before event. All competitors must be WWMAA members in good standing.</p>",
            "event_type": EventType.TOURNAMENT.value,
            "visibility": EventVisibility.PUBLIC.value,
            "start_date": (datetime.now() + timedelta(days=90)).isoformat(),
            "end_date": (datetime.now() + timedelta(days=91)).isoformat(),
            "timezone": "America/Chicago",
            "location": "Chicago Convention Center, Chicago, IL",
            "is_online": False,
            "capacity": 150,
            "price": 75.00,
            "instructor_info": "Tournament Director: Master Thompson",
            "status": EventStatus.DRAFT.value,  # Draft - will NOT appear on public page
        },
    ]

    created_events = []

    print(f"\nCreating {len(events)} sample events...")
    print("-" * 80)

    for i, event_data in enumerate(events, 1):
        try:
            print(f"\n[{i}/{len(events)}] Creating event: {event_data['title']}")
            print(f"  Type: {event_data['event_type']}")
            print(f"  Status: {event_data['status']}")
            print(f"  Location: {event_data['location']}")
            print(f"  Online: {event_data['is_online']}")
            print(f"  Price: ${event_data.get('price', 0):.2f}")
            print(f"  Capacity: {event_data.get('capacity', 'Unlimited')}")

            # Create the event
            result = event_service.create_event(
                event_data=event_data,
                created_by=admin_user_id
            )

            # If status is PUBLISHED, update is_published and published_at
            if event_data['status'] == EventStatus.PUBLISHED.value:
                db_client.update_document(
                    collection="events",
                    document_id=result['id'],
                    data={
                        "is_published": True,
                        "published_at": datetime.utcnow().isoformat()
                    },
                    merge=True
                )
                print(f"  ✓ Published event (visible on public events page)")
            else:
                print(f"  ✓ Draft event (only visible in admin panel)")

            created_events.append(result)
            print(f"  Event ID: {result['id']}")
            print(f"  Status: SUCCESS")

        except Exception as e:
            print(f"  Status: FAILED - {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 80)
    print("SEEDING COMPLETE")
    print("=" * 80)
    print(f"\nTotal events created: {len(created_events)}/{len(events)}")
    print(f"Published events (visible on public page): {sum(1 for e in events if e['status'] == EventStatus.PUBLISHED.value)}")
    print(f"Draft events (admin only): {sum(1 for e in events if e['status'] == EventStatus.DRAFT.value)}")

    print("\n" + "-" * 80)
    print("VERIFICATION STEPS:")
    print("-" * 80)
    print("1. Admin Panel - All Events:")
    print("   Navigate to: http://localhost:3000/dashboard/admin")
    print("   Click on 'Events' tab")
    print(f"   Expected: See all {len(events)} events listed")
    print()
    print("2. Public Events Page - Published Events Only:")
    print("   Navigate to: http://localhost:3000/events")
    print(f"   Expected: See 2 published events (not the draft tournament)")
    print()
    print("3. Test Create Event Modal:")
    print("   Navigate to: http://localhost:3000/dashboard/admin")
    print("   Click 'Events' tab → 'Create Event' button")
    print("   Fill in the form and submit")
    print("   Expected: Event appears in admin events list immediately")
    print()
    print("4. Test Publish Flow:")
    print("   In admin events list, find a draft event")
    print("   Click actions menu → Publish")
    print("   Refresh public events page")
    print("   Expected: Event now appears on public events page")
    print("=" * 80)

    return created_events


if __name__ == "__main__":
    try:
        seed_events()
    except Exception as e:
        print(f"\n❌ SEEDING FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
