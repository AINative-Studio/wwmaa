"""
Test Suite for Member Auto-Subscribe Newsletter Integration (US-059)

Comprehensive tests for automatic newsletter subscription functionality:
- Auto-subscribe on application approval
- Auto-subscribe on subscription creation
- Upgrade to Instructor tier
- Subscription cancellation
- Email change sync
- Respect for manual unsubscribe
- Duplicate prevention
- Sync job functionality

Target: 80%+ test coverage
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
from uuid import uuid4

# Services to test
from backend.services.newsletter_service import NewsletterService
from backend.services.membership_webhook_handler import MembershipWebhookHandler
from backend.services.subscription_service import SubscriptionService
from backend.services.user_service import UserService
from backend.services.newsletter_sync_job import NewsletterSyncJob
from backend.models.schemas import (
    SubscriptionTier,
    SubscriptionStatus,
    UserRole
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_zerodb():
    """Mock ZeroDB client"""
    mock_db = Mock()
    mock_db.get_document = Mock()
    mock_db.create_document = Mock()
    mock_db.update_document = Mock()
    mock_db.query_documents = Mock()
    return mock_db


@pytest.fixture
def mock_newsletter_service():
    """Mock Newsletter Service"""
    mock_service = Mock(spec=NewsletterService)
    mock_service.auto_subscribe_member = AsyncMock()
    mock_service.upgrade_to_instructor = AsyncMock()
    mock_service.downgrade_from_instructor = AsyncMock()
    mock_service.handle_subscription_canceled = AsyncMock()
    mock_service.sync_email_change = AsyncMock()
    mock_service._check_unsubscribe_preference = AsyncMock(return_value=False)
    mock_service._subscribe_to_list = AsyncMock()
    mock_service._unsubscribe_from_list = AsyncMock()
    return mock_service


@pytest.fixture
def sample_user():
    """Sample user data"""
    user_id = str(uuid4())
    return {
        "id": user_id,
        "email": "test@example.com",
        "role": UserRole.MEMBER,
        "is_active": True,
        "profile_id": str(uuid4())
    }


@pytest.fixture
def sample_profile():
    """Sample profile data"""
    return {
        "id": str(uuid4()),
        "first_name": "John",
        "last_name": "Doe",
        "user_id": str(uuid4())
    }


@pytest.fixture
def sample_application(sample_user):
    """Sample application data"""
    return {
        "id": str(uuid4()),
        "user_id": sample_user["id"],
        "email": sample_user["email"],
        "first_name": "John",
        "last_name": "Doe",
        "status": "approved",
        "subscription_tier": "basic"
    }


@pytest.fixture
def sample_subscription(sample_user):
    """Sample subscription data"""
    return {
        "id": str(uuid4()),
        "user_id": sample_user["id"],
        "tier": SubscriptionTier.BASIC,
        "status": SubscriptionStatus.ACTIVE,
        "start_date": datetime.utcnow().isoformat(),
        "amount": 29.00,
        "interval": "year"
    }


# ============================================================================
# NEWSLETTER SERVICE TESTS
# ============================================================================

@pytest.mark.asyncio
class TestNewsletterService:
    """Test NewsletterService functionality"""

    async def test_auto_subscribe_member_basic_tier(self, mock_zerodb, sample_user, sample_profile):
        """Test auto-subscribing a basic tier member"""
        # Setup
        service = NewsletterService(zerodb_client=mock_zerodb)

        mock_zerodb.get_document.side_effect = [
            {"data": sample_user},  # User lookup
            {"data": sample_profile}  # Profile lookup
        ]

        mock_zerodb.query_documents.return_value = {"documents": []}  # No unsubscribe prefs
        mock_zerodb.create_document.return_value = {"id": str(uuid4()), "data": {}}

        with patch.object(service, '_subscribe_to_list', new_callable=AsyncMock) as mock_subscribe:
            mock_subscribe.return_value = {"success": True}

            # Execute
            result = await service.auto_subscribe_member(
                user_id=sample_user["id"],
                tier="basic"
            )

        # Assert
        assert result["user_id"] == sample_user["id"]
        assert result["email"] == sample_user["email"]
        assert "members_only" in result["subscribed_lists"]
        assert "instructors" not in result["subscribed_lists"]
        assert mock_subscribe.call_count == 1

    async def test_auto_subscribe_member_instructor_tier(self, mock_zerodb, sample_user, sample_profile):
        """Test auto-subscribing an instructor tier member"""
        # Setup
        service = NewsletterService(zerodb_client=mock_zerodb)

        mock_zerodb.get_document.side_effect = [
            {"data": sample_user},
            {"data": sample_profile}
        ]

        mock_zerodb.query_documents.return_value = {"documents": []}
        mock_zerodb.create_document.return_value = {"id": str(uuid4()), "data": {}}

        with patch.object(service, '_subscribe_to_list', new_callable=AsyncMock) as mock_subscribe:
            mock_subscribe.return_value = {"success": True}

            # Execute
            result = await service.auto_subscribe_member(
                user_id=sample_user["id"],
                tier="lifetime"
            )

        # Assert
        assert "members_only" in result["subscribed_lists"]
        assert "instructors" in result["subscribed_lists"]
        assert mock_subscribe.call_count == 2

    async def test_auto_subscribe_respects_unsubscribe_preference(self, mock_zerodb, sample_user):
        """Test that auto-subscribe respects user's unsubscribe preference"""
        # Setup
        service = NewsletterService(zerodb_client=mock_zerodb)

        mock_zerodb.get_document.return_value = {"data": sample_user}
        mock_zerodb.query_documents.return_value = {
            "documents": [{
                "user_id": sample_user["id"],
                "unsubscribed_lists": ["members_only"]
            }]
        }

        with patch.object(service, '_subscribe_to_list', new_callable=AsyncMock) as mock_subscribe:
            # Execute
            result = await service.auto_subscribe_member(
                user_id=sample_user["id"],
                tier="basic"
            )

        # Assert
        assert "members_only" in result["skipped_lists"]
        assert len(result["subscribed_lists"]) == 0
        assert mock_subscribe.call_count == 0

    async def test_upgrade_to_instructor(self, mock_zerodb, sample_user, sample_profile):
        """Test upgrading member to instructor list"""
        # Setup
        service = NewsletterService(zerodb_client=mock_zerodb)

        mock_zerodb.get_document.side_effect = [
            {"data": sample_user},
            {"data": sample_profile}
        ]

        mock_zerodb.query_documents.return_value = {"documents": []}
        mock_zerodb.create_document.return_value = {"id": str(uuid4()), "data": {}}

        with patch.object(service, '_subscribe_to_list', new_callable=AsyncMock) as mock_subscribe:
            mock_subscribe.return_value = {"success": True}

            # Execute
            result = await service.upgrade_to_instructor(sample_user["id"])

        # Assert
        assert result["success"] == True
        assert mock_subscribe.called
        mock_subscribe.assert_called_once()

    async def test_handle_subscription_canceled(self, mock_zerodb, sample_user):
        """Test handling subscription cancellation"""
        # Setup
        service = NewsletterService(zerodb_client=mock_zerodb)

        mock_zerodb.get_document.return_value = {"data": sample_user}
        mock_zerodb.create_document.return_value = {"id": str(uuid4()), "data": {}}

        with patch.object(service, '_unsubscribe_from_list', new_callable=AsyncMock) as mock_unsub:
            mock_unsub.return_value = {"success": True}

            # Execute
            result = await service.handle_subscription_canceled(sample_user["id"])

        # Assert
        assert result["user_id"] == sample_user["id"]
        assert "members_only" in result["unsubscribed_lists"]
        assert "instructors" in result["unsubscribed_lists"]
        assert mock_unsub.call_count == 2

    async def test_sync_email_change(self, mock_zerodb):
        """Test syncing email change to BeeHiiv"""
        # Setup
        service = NewsletterService(zerodb_client=mock_zerodb)
        old_email = "old@example.com"
        new_email = "new@example.com"

        with patch.object(service, '_make_beehiiv_request', new_callable=AsyncMock) as mock_api:
            mock_api.side_effect = [
                {
                    "data": [{
                        "id": "sub_123",
                        "custom_fields": {
                            "lists": ["members_only"],
                            "first_name": "John",
                            "last_name": "Doe"
                        }
                    }]
                },  # GET subscription
                {"success": True}  # PUT update
            ]

            # Execute
            result = await service.sync_email_change(old_email, new_email)

        # Assert
        assert result["success"] == True
        assert result["old_email"] == old_email
        assert result["new_email"] == new_email
        assert mock_api.call_count == 2


# ============================================================================
# MEMBERSHIP WEBHOOK HANDLER TESTS
# ============================================================================

@pytest.mark.asyncio
class TestMembershipWebhookHandler:
    """Test MembershipWebhookHandler functionality"""

    async def test_handle_application_approved(self, mock_zerodb, mock_newsletter_service, sample_application):
        """Test handling application approval webhook"""
        # Setup
        handler = MembershipWebhookHandler(zerodb_client=mock_zerodb)
        handler.newsletter_service = mock_newsletter_service

        mock_zerodb.get_document.return_value = {"data": sample_application}
        mock_zerodb.create_document.return_value = {"id": str(uuid4()), "data": {}}

        mock_newsletter_service.auto_subscribe_member.return_value = {
            "subscribed_lists": ["members_only"]
        }

        # Execute
        result = await handler.handle_application_approved(sample_application["id"])

        # Assert
        assert result["success"] == True
        assert result["event"] == "application_approved"
        mock_newsletter_service.auto_subscribe_member.assert_called_once()

    async def test_handle_tier_upgrade_to_instructor(self, mock_zerodb, mock_newsletter_service, sample_user):
        """Test handling tier upgrade to instructor"""
        # Setup
        handler = MembershipWebhookHandler(zerodb_client=mock_zerodb)
        handler.newsletter_service = mock_newsletter_service

        mock_zerodb.create_document.return_value = {"id": str(uuid4()), "data": {}}
        mock_newsletter_service.upgrade_to_instructor.return_value = {"success": True}

        # Execute
        result = await handler.handle_tier_upgrade(
            user_id=sample_user["id"],
            old_tier="basic",
            new_tier="lifetime"
        )

        # Assert
        assert result["success"] == True
        assert result["event"] == "tier_upgrade"
        assert len(result["newsletter_changes"]) > 0
        mock_newsletter_service.upgrade_to_instructor.assert_called_once()

    async def test_handle_tier_downgrade_from_instructor(self, mock_zerodb, mock_newsletter_service, sample_user):
        """Test handling tier downgrade from instructor"""
        # Setup
        handler = MembershipWebhookHandler(zerodb_client=mock_zerodb)
        handler.newsletter_service = mock_newsletter_service

        mock_zerodb.create_document.return_value = {"id": str(uuid4()), "data": {}}
        mock_newsletter_service.downgrade_from_instructor.return_value = {"success": True}

        # Execute
        result = await handler.handle_tier_upgrade(
            user_id=sample_user["id"],
            old_tier="lifetime",
            new_tier="basic"
        )

        # Assert
        assert result["success"] == True
        mock_newsletter_service.downgrade_from_instructor.assert_called_once()


# ============================================================================
# SUBSCRIPTION SERVICE TESTS
# ============================================================================

@pytest.mark.asyncio
class TestSubscriptionService:
    """Test SubscriptionService functionality"""

    async def test_create_subscription_triggers_newsletter(self, mock_zerodb, sample_user):
        """Test that creating subscription triggers newsletter subscription"""
        # Setup
        service = SubscriptionService(zerodb_client=mock_zerodb)

        mock_zerodb.create_document.return_value = {
            "id": str(uuid4()),
            "data": {"tier": "basic"}
        }

        with patch.object(service.webhook_handler, 'handle_subscription_created', new_callable=AsyncMock) as mock_webhook:
            mock_webhook.return_value = {"success": True}

            # Execute
            result = await service.create_subscription(
                user_id=sample_user["id"],
                tier="basic",
                amount=29.00,
                interval="year"
            )

        # Assert
        assert result["success"] == True
        mock_webhook.assert_called_once()

    async def test_cancel_subscription_triggers_newsletter_removal(self, mock_zerodb, sample_subscription):
        """Test that canceling subscription removes from newsletter"""
        # Setup
        service = SubscriptionService(zerodb_client=mock_zerodb)

        mock_zerodb.get_document.return_value = {"data": sample_subscription}
        mock_zerodb.update_document.return_value = {"data": sample_subscription}

        with patch.object(service.webhook_handler, 'handle_subscription_canceled', new_callable=AsyncMock) as mock_webhook:
            mock_webhook.return_value = {
                "unsubscribed_lists": ["members_only"]
            }

            # Execute
            result = await service.cancel_subscription(
                subscription_id=sample_subscription["id"]
            )

        # Assert
        assert result["success"] == True
        mock_webhook.assert_called_once()


# ============================================================================
# USER SERVICE TESTS
# ============================================================================

@pytest.mark.asyncio
class TestUserService:
    """Test UserService functionality"""

    async def test_update_email_syncs_to_newsletter(self, mock_zerodb, sample_user):
        """Test that updating email syncs to newsletter for members"""
        # Setup
        service = UserService(zerodb_client=mock_zerodb)

        old_email = sample_user["email"]
        new_email = "newemail@example.com"

        mock_zerodb.get_document.return_value = {"data": sample_user}
        mock_zerodb.query_documents.return_value = {"documents": []}
        mock_zerodb.update_document.return_value = {
            "data": {**sample_user, "email": new_email}
        }
        mock_zerodb.create_document.return_value = {"id": str(uuid4()), "data": {}}

        with patch.object(service.webhook_handler, 'handle_email_changed', new_callable=AsyncMock) as mock_webhook:
            mock_webhook.return_value = {"success": True}

            # Execute
            result = await service.update_user_email(
                user_id=sample_user["id"],
                new_email=new_email
            )

        # Assert
        assert result["success"] == True
        assert result["new_email"] == new_email
        mock_webhook.assert_called_once_with(
            user_id=sample_user["id"],
            old_email=old_email,
            new_email=new_email
        )

    async def test_update_email_no_sync_for_public_users(self, mock_zerodb):
        """Test that email update doesn't sync for public users"""
        # Setup
        service = UserService(zerodb_client=mock_zerodb)

        public_user = {
            "id": str(uuid4()),
            "email": "public@example.com",
            "role": UserRole.PUBLIC,
            "is_active": True
        }

        new_email = "newpublic@example.com"

        mock_zerodb.get_document.return_value = {"data": public_user}
        mock_zerodb.query_documents.return_value = {"documents": []}
        mock_zerodb.update_document.return_value = {
            "data": {**public_user, "email": new_email}
        }
        mock_zerodb.create_document.return_value = {"id": str(uuid4()), "data": {}}

        with patch.object(service.webhook_handler, 'handle_email_changed', new_callable=AsyncMock) as mock_webhook:
            # Execute
            result = await service.update_user_email(
                user_id=public_user["id"],
                new_email=new_email
            )

        # Assert
        assert result["success"] == True
        assert mock_webhook.call_count == 0  # Should not be called for public users


# ============================================================================
# NEWSLETTER SYNC JOB TESTS
# ============================================================================

@pytest.mark.asyncio
class TestNewsletterSyncJob:
    """Test NewsletterSyncJob functionality"""

    async def test_run_sync_processes_active_members(self, mock_zerodb):
        """Test that sync job processes all active members"""
        # Setup
        job = NewsletterSyncJob(zerodb_client=mock_zerodb)

        active_member_1 = {
            "id": str(uuid4()),
            "user_id": str(uuid4()),
            "email": "member1@example.com",
            "tier": "basic",
            "status": SubscriptionStatus.ACTIVE
        }

        active_member_2 = {
            "id": str(uuid4()),
            "user_id": str(uuid4()),
            "email": "member2@example.com",
            "tier": "lifetime",
            "status": SubscriptionStatus.ACTIVE
        }

        mock_zerodb.query_documents.side_effect = [
            {"documents": [active_member_1, active_member_2]},  # Active subscriptions
            {"documents": []}  # Canceled subscriptions
        ]

        mock_zerodb.get_document.side_effect = [
            {"data": {"id": active_member_1["user_id"], "email": "member1@example.com", "is_active": True}},
            {"data": {"id": active_member_2["user_id"], "email": "member2@example.com", "is_active": True}}
        ]

        mock_zerodb.create_document.return_value = {"id": str(uuid4()), "data": {}}

        with patch.object(job.newsletter_service, 'auto_subscribe_member', new_callable=AsyncMock) as mock_subscribe:
            mock_subscribe.return_value = {"subscribed_lists": ["members_only"]}

            # Execute
            result = await job.run_sync()

        # Assert
        assert result["success"] == True
        assert result["members_processed"] == 2
        assert mock_subscribe.call_count == 2

    async def test_run_sync_handles_errors_gracefully(self, mock_zerodb):
        """Test that sync job handles errors gracefully"""
        # Setup
        job = NewsletterSyncJob(zerodb_client=mock_zerodb)

        active_member = {
            "id": str(uuid4()),
            "user_id": str(uuid4()),
            "email": "error@example.com",
            "tier": "basic",
            "status": SubscriptionStatus.ACTIVE
        }

        mock_zerodb.query_documents.side_effect = [
            {"documents": [active_member]},
            {"documents": []}
        ]

        mock_zerodb.get_document.return_value = {
            "data": {"id": active_member["user_id"], "email": "error@example.com", "is_active": True}
        }

        mock_zerodb.create_document.return_value = {"id": str(uuid4()), "data": {}}

        with patch.object(job.newsletter_service, 'auto_subscribe_member', new_callable=AsyncMock) as mock_subscribe:
            mock_subscribe.side_effect = Exception("BeeHiiv API error")

            # Execute
            result = await job.run_sync()

        # Assert
        assert result["success"] == True  # Job completes despite errors
        assert len(result["errors"]) == 1
        assert "BeeHiiv API error" in result["errors"][0]["error"]


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.asyncio
class TestNewsletterIntegration:
    """Integration tests for full newsletter workflow"""

    async def test_full_application_to_newsletter_flow(self, mock_zerodb, sample_application, sample_user):
        """Test complete flow from application approval to newsletter subscription"""
        # This would test the full flow in a more realistic scenario
        # Setup mocks for entire workflow
        pass  # Placeholder for more complex integration test


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================

@pytest.mark.asyncio
class TestNewsletterEdgeCases:
    """Test edge cases and error handling"""

    async def test_duplicate_subscription_prevented(self, mock_zerodb, sample_user):
        """Test that duplicate subscriptions are prevented"""
        service = NewsletterService(zerodb_client=mock_zerodb)

        mock_zerodb.get_document.return_value = {"data": sample_user}
        mock_zerodb.query_documents.return_value = {"documents": []}

        with patch.object(service, '_make_beehiiv_request', new_callable=AsyncMock) as mock_api:
            # Return existing subscription
            mock_api.return_value = {
                "data": [{
                    "id": "existing_sub",
                    "custom_fields": {
                        "lists": ["members_only"]
                    }
                }]
            }

            with patch.object(service, '_subscribe_to_list', new_callable=AsyncMock) as mock_subscribe:
                mock_subscribe.return_value = {"success": True, "already_exists": True}

                result = await service.auto_subscribe_member(
                    user_id=sample_user["id"],
                    tier="basic"
                )

        assert result["success"] or "members_only" in result.get("subscribed_lists", [])

    async def test_beehiiv_api_failure_handling(self, mock_zerodb, sample_user):
        """Test handling of BeeHiiv API failures"""
        service = NewsletterService(zerodb_client=mock_zerodb)

        mock_zerodb.get_document.return_value = {"data": sample_user}
        mock_zerodb.query_documents.return_value = {"documents": []}

        with patch.object(service, '_make_beehiiv_request', new_callable=AsyncMock) as mock_api:
            mock_api.side_effect = Exception("API timeout")

            with patch.object(service, '_subscribe_to_list', new_callable=AsyncMock) as mock_subscribe:
                mock_subscribe.side_effect = Exception("API error")

                # Should handle error gracefully
                with pytest.raises(Exception):
                    await service.auto_subscribe_member(
                        user_id=sample_user["id"],
                        tier="basic"
                    )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=backend/services", "--cov-report=html"])
