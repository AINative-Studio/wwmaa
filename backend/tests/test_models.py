"""
Unit Tests for ZeroDB Pydantic Models

This test suite validates all Pydantic models for ZeroDB collections.
Tests cover field validation, enum values, relationships, and edge cases.

Run tests:
    pytest backend/tests/test_models.py -v

Run with coverage:
    pytest backend/tests/test_models.py --cov=backend.models --cov-report=term-missing
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4, UUID
from pydantic import ValidationError

# Import all models and enums
from backend.models import (
    BaseDocument,
    User, Application, Approval, Subscription, Payment,
    Profile, Event, RSVP, TrainingSession, SessionAttendance,
    SearchQuery, ContentIndex, MediaAsset, AuditLog,
    UserRole, ApplicationStatus, ApprovalStatus,
    SubscriptionTier, SubscriptionStatus, PaymentStatus,
    EventType, EventVisibility, RSVPStatus, AttendanceStatus,
    MediaType, AuditAction,
    get_all_models, get_model_by_collection
)


# ============================================================================
# BASE DOCUMENT TESTS
# ============================================================================

class TestBaseDocument:
    """Test BaseDocument model"""

    def test_base_document_default_fields(self):
        """Test that BaseDocument auto-generates required fields"""
        doc = BaseDocument()
        assert isinstance(doc.id, UUID)
        assert isinstance(doc.created_at, datetime)
        assert isinstance(doc.updated_at, datetime)

    def test_base_document_custom_id(self):
        """Test BaseDocument with custom UUID"""
        custom_id = uuid4()
        doc = BaseDocument(id=custom_id)
        assert doc.id == custom_id

    def test_base_document_timestamps(self):
        """Test that created_at and updated_at are set correctly"""
        before = datetime.utcnow()
        doc = BaseDocument()
        after = datetime.utcnow()
        assert before <= doc.created_at <= after
        assert before <= doc.updated_at <= after

    def test_base_document_json_encoding(self):
        """Test JSON serialization of BaseDocument"""
        doc = BaseDocument()
        json_data = doc.model_dump()
        assert isinstance(json_data['id'], UUID)
        assert isinstance(json_data['created_at'], datetime)


# ============================================================================
# USER MODEL TESTS
# ============================================================================

class TestUser:
    """Test User model"""

    def test_user_creation_minimal(self):
        """Test User creation with minimal required fields"""
        user = User(
            email="test@example.com",
            password_hash="hashed_password_123"
        )
        assert user.email == "test@example.com"
        assert user.password_hash == "hashed_password_123"
        assert user.role == UserRole.PUBLIC
        assert user.is_active is True
        assert user.is_verified is False

    def test_user_email_lowercase(self):
        """Test that email is converted to lowercase"""
        user = User(
            email="TEST@EXAMPLE.COM",
            password_hash="hashed_password_123"
        )
        assert user.email == "test@example.com"

    def test_user_invalid_email(self):
        """Test that invalid email raises ValidationError"""
        with pytest.raises(ValidationError):
            User(email="invalid-email", password_hash="hash")

    def test_user_all_fields(self):
        """Test User creation with all fields"""
        user = User(
            email="admin@wwmaa.com",
            password_hash="hashed_password",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
            last_login=datetime.utcnow(),
            profile_id=uuid4()
        )
        assert user.role == UserRole.ADMIN
        assert user.is_verified is True
        assert isinstance(user.last_login, datetime)
        assert isinstance(user.profile_id, UUID)

    def test_user_role_enum_values(self):
        """Test all UserRole enum values"""
        for role in [UserRole.PUBLIC, UserRole.MEMBER, UserRole.INSTRUCTOR,
                     UserRole.BOARD_MEMBER, UserRole.ADMIN]:
            user = User(email="test@example.com", password_hash="hash", role=role)
            assert user.role == role


# ============================================================================
# APPLICATION MODEL TESTS
# ============================================================================

class TestApplication:
    """Test Application model"""

    def test_application_creation_minimal(self):
        """Test Application creation with minimal fields"""
        app = Application(
            user_id=uuid4(),
            first_name="John",
            last_name="Doe",
            email="john@example.com"
        )
        assert app.status == ApplicationStatus.DRAFT
        assert app.country == "USA"
        assert app.subscription_tier == SubscriptionTier.FREE
        assert len(app.disciplines) == 0

    def test_application_status_workflow(self):
        """Test all application status transitions"""
        app = Application(
            user_id=uuid4(),
            first_name="Jane",
            last_name="Smith",
            email="jane@example.com"
        )

        # Test status transitions
        assert app.status == ApplicationStatus.DRAFT
        app.status = ApplicationStatus.SUBMITTED
        assert app.status == ApplicationStatus.SUBMITTED

    def test_application_martial_arts_info(self):
        """Test martial arts specific fields"""
        app = Application(
            user_id=uuid4(),
            first_name="Bruce",
            last_name="Lee",
            email="bruce@example.com",
            disciplines=["Kung Fu", "Wing Chun", "Boxing"],
            experience_years=25,
            current_rank="Master",
            school_affiliation="Jun Fan Gung Fu Institute"
        )
        assert len(app.disciplines) == 3
        assert app.experience_years == 25
        assert "Kung Fu" in app.disciplines

    def test_application_invalid_experience_years(self):
        """Test validation of experience_years (0-100)"""
        with pytest.raises(ValidationError):
            Application(
                user_id=uuid4(),
                first_name="Test",
                last_name="User",
                email="test@example.com",
                experience_years=150  # Invalid: > 100
            )

    def test_application_address_fields(self):
        """Test address fields"""
        app = Application(
            user_id=uuid4(),
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            address_line1="123 Main St",
            address_line2="Apt 4B",
            city="Seattle",
            state="WA",
            zip_code="98101"
        )
        assert app.city == "Seattle"
        assert app.state == "WA"
        assert app.zip_code == "98101"


# ============================================================================
# APPROVAL MODEL TESTS
# ============================================================================

class TestApproval:
    """Test Approval model"""

    def test_approval_creation(self):
        """Test Approval creation"""
        approval = Approval(
            application_id=uuid4(),
            approver_id=uuid4()
        )
        assert approval.status == ApprovalStatus.PENDING
        assert approval.priority == 0
        assert len(approval.conditions) == 0

    def test_approval_with_conditions(self):
        """Test approval with conditional requirements"""
        approval = Approval(
            application_id=uuid4(),
            approver_id=uuid4(),
            status=ApprovalStatus.APPROVED,
            conditions=["Submit proof of rank", "Attend orientation"],
            priority=5
        )
        assert len(approval.conditions) == 2
        assert approval.priority == 5

    def test_approval_invalid_priority(self):
        """Test that priority must be 0-10"""
        with pytest.raises(ValidationError):
            Approval(
                application_id=uuid4(),
                approver_id=uuid4(),
                priority=15  # Invalid: > 10
            )


# ============================================================================
# SUBSCRIPTION MODEL TESTS
# ============================================================================

class TestSubscription:
    """Test Subscription model"""

    def test_subscription_creation(self):
        """Test Subscription creation"""
        sub = Subscription(
            user_id=uuid4(),
            tier=SubscriptionTier.BASIC,
            start_date=datetime.utcnow(),
            amount=29.99
        )
        assert sub.tier == SubscriptionTier.BASIC
        assert sub.status == SubscriptionStatus.ACTIVE
        assert sub.currency == "USD"
        assert sub.interval == "month"
        assert sub.amount == 29.99

    def test_subscription_all_tiers(self):
        """Test all subscription tiers"""
        for tier in [SubscriptionTier.FREE, SubscriptionTier.BASIC,
                     SubscriptionTier.PREMIUM, SubscriptionTier.LIFETIME]:
            sub = Subscription(
                user_id=uuid4(),
                tier=tier,
                start_date=datetime.utcnow(),
                amount=0.0 if tier == SubscriptionTier.FREE else 29.99
            )
            assert sub.tier == tier

    def test_subscription_stripe_integration(self):
        """Test Stripe integration fields"""
        sub = Subscription(
            user_id=uuid4(),
            tier=SubscriptionTier.PREMIUM,
            start_date=datetime.utcnow(),
            amount=49.99,
            stripe_subscription_id="sub_1234567890",
            stripe_customer_id="cus_0987654321"
        )
        assert sub.stripe_subscription_id == "sub_1234567890"
        assert sub.stripe_customer_id == "cus_0987654321"

    def test_subscription_invalid_amount(self):
        """Test that amount must be non-negative"""
        with pytest.raises(ValidationError):
            Subscription(
                user_id=uuid4(),
                tier=SubscriptionTier.BASIC,
                start_date=datetime.utcnow(),
                amount=-10.0  # Invalid: negative
            )


# ============================================================================
# PAYMENT MODEL TESTS
# ============================================================================

class TestPayment:
    """Test Payment model"""

    def test_payment_creation(self):
        """Test Payment creation"""
        payment = Payment(
            user_id=uuid4(),
            amount=29.99,
            status=PaymentStatus.SUCCEEDED
        )
        assert payment.amount == 29.99
        assert payment.currency == "USD"
        assert payment.refunded_amount == 0.0

    def test_payment_refund(self):
        """Test payment refund fields"""
        payment = Payment(
            user_id=uuid4(),
            amount=49.99,
            status=PaymentStatus.REFUNDED,
            refunded_amount=49.99,
            refunded_at=datetime.utcnow(),
            refund_reason="Customer requested refund"
        )
        assert payment.status == PaymentStatus.REFUNDED
        assert payment.refunded_amount == 49.99
        assert isinstance(payment.refunded_at, datetime)

    def test_payment_stripe_fields(self):
        """Test Stripe integration fields"""
        payment = Payment(
            user_id=uuid4(),
            amount=99.99,
            status=PaymentStatus.SUCCEEDED,
            stripe_payment_intent_id="pi_1234567890",
            stripe_charge_id="ch_0987654321",
            payment_method="card"
        )
        assert payment.stripe_payment_intent_id == "pi_1234567890"
        assert payment.payment_method == "card"


# ============================================================================
# PROFILE MODEL TESTS
# ============================================================================

class TestProfile:
    """Test Profile model"""

    def test_profile_creation_minimal(self):
        """Test Profile creation with minimal fields"""
        profile = Profile(
            user_id=uuid4(),
            first_name="John",
            last_name="Doe"
        )
        assert profile.first_name == "John"
        assert profile.country == "USA"
        assert profile.newsletter_subscribed is False
        assert profile.public_profile is False
        assert profile.event_notifications is True

    def test_profile_martial_arts_data(self):
        """Test martial arts specific profile data"""
        profile = Profile(
            user_id=uuid4(),
            first_name="Master",
            last_name="Miyagi",
            disciplines=["Karate", "Kobudo"],
            ranks={"Karate": "10th Dan", "Kobudo": "8th Dan"},
            instructor_certifications=["Certified Instructor", "Master Instructor"],
            schools_affiliated=["Miyagi-Do Karate"]
        )
        assert len(profile.disciplines) == 2
        assert profile.ranks["Karate"] == "10th Dan"
        assert len(profile.instructor_certifications) == 2

    def test_profile_social_links(self):
        """Test social media links"""
        profile = Profile(
            user_id=uuid4(),
            first_name="Social",
            last_name="User",
            social_links={
                "instagram": "https://instagram.com/user",
                "facebook": "https://facebook.com/user",
                "youtube": "https://youtube.com/@user"
            }
        )
        assert len(profile.social_links) == 3
        assert "instagram" in profile.social_links


# ============================================================================
# EVENT MODEL TESTS
# ============================================================================

class TestEvent:
    """Test Event model"""

    def test_event_creation_minimal(self):
        """Test Event creation with minimal fields"""
        event = Event(
            title="Karate Training Session",
            event_type=EventType.TRAINING,
            start_datetime=datetime.utcnow(),
            end_datetime=datetime.utcnow() + timedelta(hours=2),
            organizer_id=uuid4()
        )
        assert event.title == "Karate Training Session"
        assert event.visibility == EventVisibility.PUBLIC
        assert event.current_attendees == 0
        assert event.is_virtual is False

    def test_event_virtual_event(self):
        """Test virtual event creation"""
        event = Event(
            title="Online Seminar",
            event_type=EventType.SEMINAR,
            start_datetime=datetime.utcnow(),
            end_datetime=datetime.utcnow() + timedelta(hours=1),
            organizer_id=uuid4(),
            is_virtual=True,
            virtual_url="https://meet.example.com/room123"
        )
        assert event.is_virtual is True
        assert event.virtual_url is not None

    def test_event_capacity_management(self):
        """Test event capacity fields"""
        event = Event(
            title="Limited Capacity Event",
            event_type=EventType.TRAINING,
            start_datetime=datetime.utcnow(),
            end_datetime=datetime.utcnow() + timedelta(hours=2),
            organizer_id=uuid4(),
            max_attendees=30,
            current_attendees=15,
            waitlist_enabled=True
        )
        assert event.max_attendees == 30
        assert event.current_attendees == 15
        assert event.waitlist_enabled is True

    def test_event_all_types(self):
        """Test all event types"""
        for event_type in [EventType.TRAINING, EventType.SEMINAR,
                          EventType.COMPETITION, EventType.SOCIAL,
                          EventType.MEETING, EventType.OTHER]:
            event = Event(
                title=f"{event_type} Event",
                event_type=event_type,
                start_datetime=datetime.utcnow(),
                end_datetime=datetime.utcnow() + timedelta(hours=1),
                organizer_id=uuid4()
            )
            assert event.event_type == event_type


# ============================================================================
# RSVP MODEL TESTS
# ============================================================================

class TestRSVP:
    """Test RSVP model"""

    def test_rsvp_creation(self):
        """Test RSVP creation"""
        rsvp = RSVP(
            event_id=uuid4(),
            user_id=uuid4()
        )
        assert rsvp.status == RSVPStatus.PENDING
        assert rsvp.guests_count == 0
        assert rsvp.reminder_sent is False
        assert rsvp.confirmation_sent is False

    def test_rsvp_with_guests(self):
        """Test RSVP with guest count"""
        rsvp = RSVP(
            event_id=uuid4(),
            user_id=uuid4(),
            status=RSVPStatus.CONFIRMED,
            guests_count=3
        )
        assert rsvp.guests_count == 3
        assert rsvp.status == RSVPStatus.CONFIRMED

    def test_rsvp_invalid_guests_count(self):
        """Test that guests_count must be 0-10"""
        with pytest.raises(ValidationError):
            RSVP(
                event_id=uuid4(),
                user_id=uuid4(),
                guests_count=15  # Invalid: > 10
            )


# ============================================================================
# TRAINING SESSION MODEL TESTS
# ============================================================================

class TestTrainingSession:
    """Test TrainingSession model"""

    def test_training_session_creation(self):
        """Test TrainingSession creation"""
        session = TrainingSession(
            title="Advanced Kata Practice",
            instructor_id=uuid4(),
            session_date=datetime.utcnow(),
            duration_minutes=90,
            discipline="Karate"
        )
        assert session.title == "Advanced Kata Practice"
        assert session.duration_minutes == 90
        assert session.members_only is True
        assert session.is_public is False
        assert session.recording_status == "not_recorded"

    def test_training_session_with_video(self):
        """Test TrainingSession with video recording"""
        session = TrainingSession(
            title="Kumite Techniques",
            instructor_id=uuid4(),
            session_date=datetime.utcnow(),
            duration_minutes=120,
            discipline="Karate",
            cloudflare_stream_id="cf_stream_123",
            video_url="https://stream.example.com/video123",
            video_duration_seconds=7200,
            recording_status="completed"
        )
        assert session.cloudflare_stream_id == "cf_stream_123"
        assert session.video_duration_seconds == 7200

    def test_training_session_invalid_duration(self):
        """Test that duration must be 1-480 minutes"""
        with pytest.raises(ValidationError):
            TrainingSession(
                title="Invalid Session",
                instructor_id=uuid4(),
                session_date=datetime.utcnow(),
                duration_minutes=500,  # Invalid: > 480
                discipline="Karate"
            )


# ============================================================================
# SESSION ATTENDANCE MODEL TESTS
# ============================================================================

class TestSessionAttendance:
    """Test SessionAttendance model"""

    def test_session_attendance_creation(self):
        """Test SessionAttendance creation"""
        attendance = SessionAttendance(
            training_session_id=uuid4(),
            user_id=uuid4(),
            status=AttendanceStatus.PRESENT
        )
        assert attendance.status == AttendanceStatus.PRESENT

    def test_session_attendance_with_video_tracking(self):
        """Test attendance with video viewing data"""
        attendance = SessionAttendance(
            training_session_id=uuid4(),
            user_id=uuid4(),
            status=AttendanceStatus.PRESENT,
            video_watch_percentage=75.5,
            last_watched_position=3600,
            participation_score=85
        )
        assert attendance.video_watch_percentage == 75.5
        assert attendance.last_watched_position == 3600
        assert attendance.participation_score == 85

    def test_session_attendance_invalid_score(self):
        """Test that participation_score must be 0-100"""
        with pytest.raises(ValidationError):
            SessionAttendance(
                training_session_id=uuid4(),
                user_id=uuid4(),
                status=AttendanceStatus.PRESENT,
                participation_score=150  # Invalid: > 100
            )


# ============================================================================
# SEARCH QUERY MODEL TESTS
# ============================================================================

class TestSearchQuery:
    """Test SearchQuery model"""

    def test_search_query_creation(self):
        """Test SearchQuery creation"""
        query = SearchQuery(
            query_text="martial arts techniques"
        )
        assert query.query_text == "martial arts techniques"
        assert query.results_count == 0
        assert len(query.top_result_ids) == 0

    def test_search_query_with_results(self):
        """Test SearchQuery with results"""
        result_ids = [uuid4(), uuid4(), uuid4()]
        query = SearchQuery(
            user_id=uuid4(),
            query_text="karate kata",
            results_count=3,
            top_result_ids=result_ids,
            response_time_ms=150,
            click_through_rate=0.33
        )
        assert query.results_count == 3
        assert len(query.top_result_ids) == 3
        assert query.response_time_ms == 150

    def test_search_query_with_embedding(self):
        """Test SearchQuery with embedding vector"""
        # Simulate OpenAI ada-002 embedding (1536 dimensions)
        embedding = [0.1] * 1536
        query = SearchQuery(
            query_text="search query",
            embedding_vector=embedding,
            intent="informational"
        )
        assert len(query.embedding_vector) == 1536
        assert query.intent == "informational"


# ============================================================================
# CONTENT INDEX MODEL TESTS
# ============================================================================

class TestContentIndex:
    """Test ContentIndex model"""

    def test_content_index_creation(self):
        """Test ContentIndex creation"""
        # Create embedding vector (1536 dimensions)
        embedding = [0.5] * 1536
        content = ContentIndex(
            content_type="event",
            content_id=uuid4(),
            title="Annual Karate Tournament",
            body="Join us for the annual karate tournament...",
            embedding_vector=embedding
        )
        assert content.content_type == "event"
        assert len(content.embedding_vector) == 1536
        assert content.visibility == "public"
        assert content.is_active is True
        assert content.search_weight == 1.0

    def test_content_index_with_metadata(self):
        """Test ContentIndex with full metadata"""
        embedding = [0.3] * 1536
        content = ContentIndex(
            content_type="article",
            content_id=uuid4(),
            title="Karate History",
            body="The history of karate...",
            summary="A brief overview of karate history",
            embedding_vector=embedding,
            author_id=uuid4(),
            tags=["karate", "history", "martial arts"],
            category="education",
            keywords=["karate", "okinawa", "martial arts"],
            search_weight=2.5
        )
        assert len(content.tags) == 3
        assert content.search_weight == 2.5
        assert "karate" in content.keywords


# ============================================================================
# MEDIA ASSET MODEL TESTS
# ============================================================================

class TestMediaAsset:
    """Test MediaAsset model"""

    def test_media_asset_image(self):
        """Test image media asset"""
        asset = MediaAsset(
            media_type=MediaType.IMAGE,
            filename="profile.jpg",
            file_size_bytes=524288,
            mime_type="image/jpeg",
            uploaded_by=uuid4(),
            width=1920,
            height=1080
        )
        assert asset.media_type == MediaType.IMAGE
        assert asset.width == 1920
        assert asset.height == 1080
        assert asset.storage_provider == "zerodb"

    def test_media_asset_video(self):
        """Test video media asset"""
        asset = MediaAsset(
            media_type=MediaType.VIDEO,
            filename="training_session.mp4",
            file_size_bytes=104857600,
            mime_type="video/mp4",
            uploaded_by=uuid4(),
            storage_provider="cloudflare",
            cloudflare_stream_id="cf_vid_123",
            duration_seconds=3600
        )
        assert asset.media_type == MediaType.VIDEO
        assert asset.storage_provider == "cloudflare"
        assert asset.duration_seconds == 3600

    def test_media_asset_access_control(self):
        """Test media asset access control"""
        asset = MediaAsset(
            media_type=MediaType.DOCUMENT,
            filename="certificate.pdf",
            file_size_bytes=102400,
            mime_type="application/pdf",
            uploaded_by=uuid4(),
            is_public=False,
            access_roles=[UserRole.MEMBER, UserRole.ADMIN]
        )
        assert asset.is_public is False
        assert UserRole.MEMBER in asset.access_roles


# ============================================================================
# AUDIT LOG MODEL TESTS
# ============================================================================

class TestAuditLog:
    """Test AuditLog model"""

    def test_audit_log_creation(self):
        """Test AuditLog creation"""
        log = AuditLog(
            user_id=uuid4(),
            action=AuditAction.CREATE,
            resource_type="applications",
            resource_id=uuid4(),
            description="Created new membership application"
        )
        assert log.action == AuditAction.CREATE
        assert log.success is True
        assert log.severity == "info"

    def test_audit_log_with_changes(self):
        """Test AuditLog with change tracking"""
        log = AuditLog(
            user_id=uuid4(),
            action=AuditAction.UPDATE,
            resource_type="users",
            resource_id=uuid4(),
            description="Updated user role",
            changes={
                "role": {
                    "old": "member",
                    "new": "instructor"
                }
            }
        )
        assert "role" in log.changes
        assert log.changes["role"]["old"] == "member"
        assert log.changes["role"]["new"] == "instructor"

    def test_audit_log_failed_action(self):
        """Test AuditLog for failed action"""
        log = AuditLog(
            user_id=uuid4(),
            action=AuditAction.DELETE,
            resource_type="events",
            resource_id=uuid4(),
            description="Attempted to delete event",
            success=False,
            error_message="Permission denied",
            severity="warning"
        )
        assert log.success is False
        assert log.error_message == "Permission denied"
        assert log.severity == "warning"


# ============================================================================
# HELPER FUNCTION TESTS
# ============================================================================

class TestHelperFunctions:
    """Test helper functions"""

    def test_get_all_models(self):
        """Test get_all_models returns all 14 collections"""
        models = get_all_models()
        assert len(models) == 14
        assert "users" in models
        assert "applications" in models
        assert "events" in models
        assert "audit_logs" in models

    def test_get_model_by_collection(self):
        """Test get_model_by_collection"""
        user_model = get_model_by_collection("users")
        assert user_model == User

        event_model = get_model_by_collection("events")
        assert event_model == Event

        invalid_model = get_model_by_collection("nonexistent")
        assert invalid_model is None


# ============================================================================
# ENUM TESTS
# ============================================================================

class TestEnums:
    """Test all enum types"""

    def test_user_role_enum(self):
        """Test UserRole enum values"""
        assert UserRole.PUBLIC.value == "public"
        assert UserRole.ADMIN.value == "admin"

    def test_application_status_enum(self):
        """Test ApplicationStatus enum values"""
        assert ApplicationStatus.DRAFT.value == "draft"
        assert ApplicationStatus.APPROVED.value == "approved"

    def test_payment_status_enum(self):
        """Test PaymentStatus enum values"""
        assert PaymentStatus.SUCCEEDED.value == "succeeded"
        assert PaymentStatus.REFUNDED.value == "refunded"

    def test_event_type_enum(self):
        """Test EventType enum values"""
        assert EventType.TRAINING.value == "training"
        assert EventType.COMPETITION.value == "competition"


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestModelRelationships:
    """Test relationships between models"""

    def test_user_to_profile_relationship(self):
        """Test User -> Profile 1:1 relationship"""
        user_id = uuid4()
        profile_id = uuid4()

        user = User(
            email="test@example.com",
            password_hash="hash",
            profile_id=profile_id
        )

        profile = Profile(
            user_id=user_id,
            first_name="Test",
            last_name="User"
        )

        # Verify relationship can be established
        assert user.profile_id == profile_id
        assert profile.user_id == user_id

    def test_application_to_approval_relationship(self):
        """Test Application -> Approval 1:Many relationship"""
        application_id = uuid4()

        application = Application(
            user_id=uuid4(),
            first_name="Test",
            last_name="User",
            email="test@example.com"
        )

        # Create multiple approvals for one application
        approval1 = Approval(
            application_id=application_id,
            approver_id=uuid4()
        )

        approval2 = Approval(
            application_id=application_id,
            approver_id=uuid4()
        )

        assert approval1.application_id == application_id
        assert approval2.application_id == application_id

    def test_event_to_rsvp_relationship(self):
        """Test Event -> RSVP 1:Many relationship"""
        event_id = uuid4()

        event = Event(
            title="Test Event",
            event_type=EventType.TRAINING,
            start_datetime=datetime.utcnow(),
            end_datetime=datetime.utcnow() + timedelta(hours=1),
            organizer_id=uuid4()
        )

        # Create multiple RSVPs for one event
        rsvp1 = RSVP(event_id=event_id, user_id=uuid4())
        rsvp2 = RSVP(event_id=event_id, user_id=uuid4())

        assert rsvp1.event_id == event_id
        assert rsvp2.event_id == event_id


# ============================================================================
# EDGE CASES & VALIDATION TESTS
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_empty_string_validation(self):
        """Test that required string fields can be empty (Pydantic allows empty strings)"""
        # Pydantic V2 allows empty strings by default
        # Use min_length constraint if you want to prevent empty strings
        user = User(email="test@example.com", password_hash="")
        assert user.password_hash == ""

    def test_uuid_validation(self):
        """Test UUID field validation"""
        # Valid UUID
        valid_uuid = uuid4()
        user = User(
            email="test@example.com",
            password_hash="hash",
            profile_id=valid_uuid
        )
        assert user.profile_id == valid_uuid

        # Invalid UUID should raise error
        with pytest.raises(ValidationError):
            User(
                email="test@example.com",
                password_hash="hash",
                profile_id="not-a-uuid"
            )

    def test_datetime_validation(self):
        """Test datetime field validation"""
        # Valid datetime
        event = Event(
            title="Test",
            event_type=EventType.TRAINING,
            start_datetime=datetime.utcnow(),
            end_datetime=datetime.utcnow() + timedelta(hours=1),
            organizer_id=uuid4()
        )
        assert isinstance(event.start_datetime, datetime)

        # Invalid datetime should raise error
        with pytest.raises(ValidationError):
            Event(
                title="Test",
                event_type=EventType.TRAINING,
                start_datetime="not-a-datetime",
                end_datetime=datetime.utcnow(),
                organizer_id=uuid4()
            )

    def test_array_field_defaults(self):
        """Test that array fields default to empty lists"""
        profile = Profile(
            user_id=uuid4(),
            first_name="Test",
            last_name="User"
        )
        assert profile.disciplines == []
        assert profile.instructor_certifications == []
        assert profile.schools_affiliated == []

    def test_dict_field_defaults(self):
        """Test that dict fields default to empty dicts"""
        subscription = Subscription(
            user_id=uuid4(),
            tier=SubscriptionTier.BASIC,
            start_date=datetime.utcnow(),
            amount=29.99
        )
        assert subscription.features == {}
        assert subscription.metadata == {}


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=backend.models", "--cov-report=term-missing"])
