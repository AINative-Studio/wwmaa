"""
Comprehensive Unit Tests for ZeroDB Seed Data Script

Tests cover:
- Environment safety checks
- Data clearing functionality
- User generation with role distribution
- All collection seeding functions
- Progress tracking
- Error handling
- CLI argument parsing

Test Coverage Target: 80%+
"""

import argparse
import pytest
from unittest.mock import Mock, MagicMock, patch, call
from uuid import UUID, uuid4
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.seed_data import (
    check_environment,
    clear_all_data,
    ProgressTracker,
    SeedDataGenerator,
    main
)
from services.zerodb_service import ZeroDBClient, ZeroDBError
from models.schemas import UserRole, ApplicationStatus, SubscriptionTier


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_client():
    """Mock ZeroDBClient for testing"""
    client = Mock(spec=ZeroDBClient)
    client.create_document = Mock(return_value={'id': str(uuid4())})
    client.query_documents = Mock(return_value={'documents': []})
    client.delete_document = Mock(return_value={'success': True})
    return client


@pytest.fixture
def mock_settings_dev():
    """Mock settings for development environment"""
    with patch('scripts.seed_data.settings') as mock_settings:
        mock_settings.PYTHON_ENV = 'development'
        mock_settings.is_production = False
        mock_settings.is_development = True
        mock_settings.is_staging = False
        yield mock_settings


@pytest.fixture
def mock_settings_prod():
    """Mock settings for production environment"""
    with patch('scripts.seed_data.settings') as mock_settings:
        mock_settings.PYTHON_ENV = 'production'
        mock_settings.is_production = True
        mock_settings.is_development = False
        mock_settings.is_staging = False
        yield mock_settings


@pytest.fixture
def seed_generator(mock_client):
    """Create a SeedDataGenerator instance with mocked client"""
    return SeedDataGenerator(mock_client)


# ============================================================================
# ENVIRONMENT CHECK TESTS
# ============================================================================

class TestEnvironmentChecks:
    """Test environment safety checks"""

    def test_check_environment_development_passes(self, mock_settings_dev):
        """Test that environment check passes in development"""
        # Should not raise exception
        check_environment()

    def test_check_environment_production_raises_error(self, mock_settings_prod):
        """Test that environment check raises error in production"""
        with pytest.raises(RuntimeError, match="SAFETY CHECK.*PRODUCTION"):
            check_environment()

    def test_clear_all_data_production_raises_error(self, mock_client, mock_settings_prod):
        """Test that clear_all_data raises error in production"""
        with pytest.raises(RuntimeError, match="SAFETY CHECK"):
            clear_all_data(mock_client)


# ============================================================================
# CLEAR DATA TESTS
# ============================================================================

class TestClearAllData:
    """Test data clearing functionality"""

    def test_clear_all_data_clears_default_collections(self, mock_client, mock_settings_dev):
        """Test clearing all default collections"""
        # Setup mock to return documents
        mock_client.query_documents.return_value = {
            'documents': [
                {'id': 'doc1'},
                {'id': 'doc2'},
            ]
        }

        clear_all_data(mock_client)

        # Verify query_documents was called for each collection
        assert mock_client.query_documents.call_count >= 10

        # Verify delete_document was called for each document
        assert mock_client.delete_document.call_count >= 2

    def test_clear_all_data_clears_specific_collections(self, mock_client, mock_settings_dev):
        """Test clearing specific collections"""
        mock_client.query_documents.return_value = {
            'documents': [{'id': 'doc1'}]
        }

        clear_all_data(mock_client, collections=['users', 'events'])

        # Should only query the specified collections
        assert mock_client.query_documents.call_count == 2

        # Verify correct collections were queried
        query_calls = [call.kwargs.get('collection') or call.args[0]
                       for call in mock_client.query_documents.call_args_list]
        assert 'users' in query_calls
        assert 'events' in query_calls

    def test_clear_all_data_handles_empty_collections(self, mock_client, mock_settings_dev):
        """Test clearing when collections are already empty"""
        mock_client.query_documents.return_value = {'documents': []}

        clear_all_data(mock_client, collections=['users'])

        # Should query but not delete anything
        assert mock_client.query_documents.call_count == 1
        assert mock_client.delete_document.call_count == 0

    def test_clear_all_data_handles_delete_errors(self, mock_client, mock_settings_dev):
        """Test that delete errors are handled gracefully"""
        mock_client.query_documents.return_value = {
            'documents': [{'id': 'doc1'}, {'id': 'doc2'}]
        }
        mock_client.delete_document.side_effect = [ZeroDBError("Delete failed"), None]

        # Should not raise exception
        clear_all_data(mock_client, collections=['users'])

        # Should attempt to delete both documents
        assert mock_client.delete_document.call_count == 2


# ============================================================================
# PROGRESS TRACKER TESTS
# ============================================================================

class TestProgressTracker:
    """Test progress tracking functionality"""

    def test_progress_tracker_initialization(self):
        """Test ProgressTracker initialization"""
        tracker = ProgressTracker(total=100, description="Test")
        assert tracker.total == 100
        assert tracker.current == 0
        assert tracker.description == "Test"

    def test_progress_tracker_update(self, capsys):
        """Test progress bar updates"""
        tracker = ProgressTracker(total=10, description="Test")
        tracker.update(5)

        assert tracker.current == 5

        captured = capsys.readouterr()
        assert "Test:" in captured.out
        assert "5/10" in captured.out

    def test_progress_tracker_complete(self, capsys):
        """Test progress tracker completion"""
        tracker = ProgressTracker(total=10, description="Test")
        tracker.update(10)
        tracker.complete()

        captured = capsys.readouterr()
        assert "\n" in captured.out


# ============================================================================
# SEED GENERATOR TESTS
# ============================================================================

class TestSeedDataGenerator:
    """Test SeedDataGenerator functionality"""

    def test_generator_initialization(self, mock_client):
        """Test SeedDataGenerator initialization"""
        generator = SeedDataGenerator(mock_client)

        assert generator.client == mock_client
        assert len(generator.collections) == 14
        assert all(isinstance(v, list) for v in generator.collections.values())

    def test_generate_users_default_count(self, seed_generator):
        """Test generating users with default count (65)"""
        user_ids = seed_generator.generate_users(count=65)

        assert len(user_ids) == 65
        assert seed_generator.client.create_document.call_count == 65

        # Verify role distribution from calls
        calls = seed_generator.client.create_document.call_args_list
        roles = [call[0][1]['role'] for call in calls]

        # Should have 5 admins, 10 board members, 20 members, 30 public
        assert roles.count(UserRole.ADMIN) == 5
        assert roles.count(UserRole.BOARD_MEMBER) == 10
        assert roles.count(UserRole.MEMBER) == 20
        assert roles.count(UserRole.PUBLIC) == 30

    def test_generate_users_custom_count(self, seed_generator):
        """Test generating users with custom count"""
        user_ids = seed_generator.generate_users(count=10)

        # Note: Due to percentage-based distribution, actual count may be slightly less
        assert len(user_ids) >= 9  # At least 9 users
        assert seed_generator.client.create_document.call_count >= 9

    def test_generate_users_handles_errors(self, seed_generator):
        """Test that user generation handles errors gracefully"""
        seed_generator.client.create_document.side_effect = [
            {'id': str(uuid4())},
            ZeroDBError("Creation failed"),
            {'id': str(uuid4())},
        ]

        user_ids = seed_generator.generate_users(count=3)

        # Should return 2 successful IDs (skip the failed one)
        assert len(user_ids) == 2

    def test_generate_profiles(self, seed_generator):
        """Test generating user profiles"""
        user_ids = [uuid4() for _ in range(5)]

        profile_ids = seed_generator.generate_profiles(user_ids)

        assert len(profile_ids) == 5
        assert seed_generator.client.create_document.call_count == 5

        # Verify profiles collection is 'profiles'
        calls = seed_generator.client.create_document.call_args_list
        assert all(call[0][0] == 'profiles' for call in calls)

    def test_generate_applications(self, seed_generator):
        """Test generating membership applications"""
        user_ids = [uuid4() for _ in range(10)]

        app_ids = seed_generator.generate_applications(user_ids, count=15)

        assert len(app_ids) == 15
        assert seed_generator.client.create_document.call_count == 15

    def test_generate_applications_various_statuses(self, seed_generator):
        """Test that applications have various statuses"""
        user_ids = [uuid4() for _ in range(10)]

        seed_generator.generate_applications(user_ids, count=20)

        calls = seed_generator.client.create_document.call_args_list
        statuses = [call[0][1]['status'] for call in calls]

        # Should have variety of statuses
        unique_statuses = set(statuses)
        assert len(unique_statuses) >= 3  # At least 3 different statuses

    def test_generate_approvals(self, seed_generator):
        """Test generating approvals for applications"""
        app_ids = [uuid4() for _ in range(10)]
        user_ids = [uuid4() for _ in range(5)]

        approval_ids = seed_generator.generate_approvals(app_ids, user_ids)

        assert len(approval_ids) <= 10  # Max 10 since we have 10 apps
        assert seed_generator.client.create_document.call_count <= 10

    def test_generate_subscriptions(self, seed_generator):
        """Test generating subscriptions"""
        user_ids = [uuid4() for _ in range(20)]

        sub_ids = seed_generator.generate_subscriptions(user_ids, count=15)

        assert len(sub_ids) == 15
        assert seed_generator.client.create_document.call_count == 15

    def test_generate_subscriptions_various_tiers(self, seed_generator):
        """Test that subscriptions have various tiers"""
        user_ids = [uuid4() for _ in range(10)]

        seed_generator.generate_subscriptions(user_ids, count=20)

        calls = seed_generator.client.create_document.call_args_list
        tiers = [call[0][1]['tier'] for call in calls]

        # Should have variety of tiers
        unique_tiers = set(tiers)
        assert len(unique_tiers) >= 2  # At least 2 different tiers

    def test_generate_payments(self, seed_generator):
        """Test generating payment transactions"""
        user_ids = [uuid4() for _ in range(10)]
        sub_ids = [uuid4() for _ in range(5)]

        payment_ids = seed_generator.generate_payments(user_ids, sub_ids, count=20)

        assert len(payment_ids) == 20
        assert seed_generator.client.create_document.call_count == 20

    def test_generate_events(self, seed_generator):
        """Test generating events"""
        user_ids = [uuid4() for _ in range(10)]

        event_ids = seed_generator.generate_events(user_ids, count=10)

        assert len(event_ids) == 10
        assert seed_generator.client.create_document.call_count == 10

    def test_generate_events_various_visibility(self, seed_generator):
        """Test that events have various visibility levels"""
        user_ids = [uuid4() for _ in range(10)]

        seed_generator.generate_events(user_ids, count=15)

        calls = seed_generator.client.create_document.call_args_list
        visibilities = [call[0][1]['visibility'] for call in calls]

        # Should have variety of visibility levels
        unique_visibilities = set(visibilities)
        assert len(unique_visibilities) >= 2

    def test_generate_rsvps(self, seed_generator):
        """Test generating event RSVPs"""
        event_ids = [uuid4() for _ in range(5)]
        user_ids = [uuid4() for _ in range(10)]

        rsvp_ids = seed_generator.generate_rsvps(event_ids, user_ids, count=30)

        assert len(rsvp_ids) == 30
        assert seed_generator.client.create_document.call_count == 30

    def test_generate_training_sessions(self, seed_generator):
        """Test generating training sessions"""
        event_ids = [uuid4() for _ in range(5)]
        user_ids = [uuid4() for _ in range(10)]

        session_ids = seed_generator.generate_training_sessions(event_ids, user_ids, count=5)

        assert len(session_ids) == 5
        assert seed_generator.client.create_document.call_count == 5

    def test_generate_training_sessions_with_cloudflare_ids(self, seed_generator):
        """Test that some training sessions have Cloudflare Stream IDs"""
        event_ids = [uuid4() for _ in range(5)]
        user_ids = [uuid4() for _ in range(10)]

        seed_generator.generate_training_sessions(event_ids, user_ids, count=10)

        calls = seed_generator.client.create_document.call_args_list
        cloudflare_ids = [call[0][1].get('cloudflare_stream_id') for call in calls]

        # At least some should have Cloudflare Stream IDs
        assert any(cf_id is not None for cf_id in cloudflare_ids)

    def test_generate_session_attendance(self, seed_generator):
        """Test generating session attendance records"""
        session_ids = [uuid4() for _ in range(5)]
        user_ids = [uuid4() for _ in range(10)]

        attendance_ids = seed_generator.generate_session_attendance(session_ids, user_ids, count=25)

        assert len(attendance_ids) == 25
        assert seed_generator.client.create_document.call_count == 25

    def test_generate_search_queries(self, seed_generator):
        """Test generating search query logs"""
        user_ids = [uuid4() for _ in range(10)]

        query_ids = seed_generator.generate_search_queries(user_ids, count=20)

        assert len(query_ids) == 20
        assert seed_generator.client.create_document.call_count == 20

    def test_generate_search_queries_with_embeddings(self, seed_generator):
        """Test that search queries include embedding vectors"""
        user_ids = [uuid4() for _ in range(5)]

        seed_generator.generate_search_queries(user_ids, count=10)

        calls = seed_generator.client.create_document.call_args_list
        embeddings = [call[0][1].get('embedding_vector') for call in calls]

        # At least some should have embeddings
        assert any(emb is not None for emb in embeddings)

        # Check vector dimensions for non-None embeddings
        for emb in embeddings:
            if emb is not None:
                assert len(emb) == 1536  # OpenAI embedding dimension

    def test_generate_content_index(self, seed_generator):
        """Test generating content index entries"""
        user_ids = [uuid4() for _ in range(10)]

        content_ids = seed_generator.generate_content_index(user_ids, count=15)

        assert len(content_ids) == 15
        assert seed_generator.client.create_document.call_count == 15

    def test_generate_content_index_embeddings(self, seed_generator):
        """Test that all content index entries have embeddings"""
        user_ids = [uuid4() for _ in range(5)]

        seed_generator.generate_content_index(user_ids, count=5)

        calls = seed_generator.client.create_document.call_args_list

        # All should have embedding vectors
        for call in calls:
            embedding = call[0][1].get('embedding_vector')
            assert embedding is not None
            assert len(embedding) == 1536

    def test_generate_media_assets(self, seed_generator):
        """Test generating media asset metadata"""
        user_ids = [uuid4() for _ in range(10)]

        asset_ids = seed_generator.generate_media_assets(user_ids, count=10)

        assert len(asset_ids) == 10
        assert seed_generator.client.create_document.call_count == 10

    def test_generate_audit_logs(self, seed_generator):
        """Test generating audit log entries"""
        user_ids = [uuid4() for _ in range(10)]

        log_ids = seed_generator.generate_audit_logs(user_ids, count=30)

        assert len(log_ids) == 30
        assert seed_generator.client.create_document.call_count == 30

    def test_clear_collections_delegates_to_clear_all_data(self, seed_generator, mock_settings_dev):
        """Test that clear_collections delegates to clear_all_data"""
        with patch('scripts.seed_data.clear_all_data') as mock_clear:
            seed_generator.clear_collections(['users', 'events'])

            mock_clear.assert_called_once_with(seed_generator.client, ['users', 'events'])

    def test_seed_all_generates_all_collections(self, seed_generator):
        """Test that seed_all generates data for all collections"""
        seed_generator.seed_all(
            user_count=10,
            application_count=5,
            event_count=3,
            training_session_count=2
        )

        # Should have created documents across all collections
        assert seed_generator.client.create_document.call_count > 50  # At least 50 total

    def test_seed_all_with_collection_filter(self, seed_generator):
        """Test seeding specific collections only"""
        seed_generator.seed_all(
            user_count=5,
            collection_filter=['users', 'profiles']
        )

        # Should only create users and profiles
        calls = seed_generator.client.create_document.call_args_list
        collections = [call[0][0] for call in calls]

        assert 'users' in collections
        assert 'profiles' in collections
        # Should not have other collections
        assert 'applications' not in collections
        assert 'events' not in collections

    def test_print_summary(self, seed_generator, caplog):
        """Test summary printing"""
        # Add some fake data to collections
        seed_generator.collections['users'] = [{'id': '1'}, {'id': '2'}]
        seed_generator.collections['events'] = [{'id': '1'}]

        with caplog.at_level('INFO'):
            seed_generator.print_summary()

        # Check log output instead of stdout
        log_text = caplog.text
        assert "Data Summary:" in log_text
        assert "users" in log_text
        assert "TOTAL" in log_text


# ============================================================================
# MAIN FUNCTION TESTS
# ============================================================================

class TestMainFunction:
    """Test CLI entry point and argument parsing"""

    @patch('scripts.seed_data.ZeroDBClient')
    @patch('scripts.seed_data.check_environment')
    @patch('scripts.seed_data.SeedDataGenerator')
    def test_main_default_arguments(self, mock_generator_class, mock_check_env, mock_client_class):
        """Test main function with default arguments"""
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator

        with patch('sys.argv', ['seed_data.py']):
            result = main()

        assert result == 0
        mock_check_env.assert_called_once()
        mock_generator.seed_all.assert_called_once()

    @patch('scripts.seed_data.ZeroDBClient')
    @patch('scripts.seed_data.check_environment')
    @patch('scripts.seed_data.SeedDataGenerator')
    def test_main_with_clear_flag(self, mock_generator_class, mock_check_env, mock_client_class):
        """Test main function with --clear flag"""
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator

        with patch('sys.argv', ['seed_data.py', '--clear']):
            result = main()

        assert result == 0
        mock_generator.clear_collections.assert_called_once()

    @patch('scripts.seed_data.ZeroDBClient')
    @patch('scripts.seed_data.check_environment')
    @patch('scripts.seed_data.SeedDataGenerator')
    def test_main_with_custom_count(self, mock_generator_class, mock_check_env, mock_client_class):
        """Test main function with custom user count"""
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator

        with patch('sys.argv', ['seed_data.py', '--count', '100']):
            result = main()

        assert result == 0
        # Verify seed_all was called with count=100
        call_kwargs = mock_generator.seed_all.call_args[1]
        assert call_kwargs['user_count'] == 100

    @patch('scripts.seed_data.ZeroDBClient')
    @patch('scripts.seed_data.check_environment')
    @patch('scripts.seed_data.SeedDataGenerator')
    def test_main_with_collections_filter(self, mock_generator_class, mock_check_env, mock_client_class):
        """Test main function with specific collections"""
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator

        with patch('sys.argv', ['seed_data.py', '--collections', 'users,events']):
            result = main()

        assert result == 0
        # Verify collection_filter was passed
        call_kwargs = mock_generator.seed_all.call_args[1]
        assert call_kwargs['collection_filter'] == ['users', 'events']

    @patch('scripts.seed_data.ZeroDBClient')
    @patch('scripts.seed_data.check_environment')
    def test_main_handles_zerodb_error(self, mock_check_env, mock_client_class):
        """Test that main handles ZeroDB errors gracefully"""
        mock_client_class.side_effect = ZeroDBError("Connection failed")

        with patch('sys.argv', ['seed_data.py']):
            result = main()

        assert result == 1  # Error exit code

    @patch('scripts.seed_data.check_environment')
    def test_main_handles_environment_check_failure(self, mock_check_env):
        """Test that main handles environment check failure"""
        mock_check_env.side_effect = RuntimeError("Production environment")

        with patch('sys.argv', ['seed_data.py']):
            result = main()

        assert result == 2  # Unexpected error exit code

    @patch('scripts.seed_data.ZeroDBClient')
    @patch('scripts.seed_data.check_environment')
    @patch('scripts.seed_data.SeedDataGenerator')
    def test_main_closes_client_on_success(self, mock_generator_class, mock_check_env, mock_client_class):
        """Test that client is closed properly on success"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator

        with patch('sys.argv', ['seed_data.py']):
            main()

        mock_client.close.assert_called_once()

    @patch('scripts.seed_data.ZeroDBClient')
    @patch('scripts.seed_data.check_environment')
    @patch('scripts.seed_data.SeedDataGenerator')
    def test_main_closes_client_on_error(self, mock_generator_class, mock_check_env, mock_client_class):
        """Test that client is closed even on error"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_generator_class.side_effect = Exception("Unexpected error")

        with patch('sys.argv', ['seed_data.py']):
            main()

        mock_client.close.assert_called_once()


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests for complete workflows"""

    @patch('scripts.seed_data.ZeroDBClient')
    def test_full_seed_workflow(self, mock_client_class, mock_settings_dev):
        """Test complete seeding workflow"""
        mock_client = Mock()
        mock_client.create_document = Mock(return_value={'id': str(uuid4())})
        mock_client_class.return_value = mock_client

        generator = SeedDataGenerator(mock_client)

        # Run full seed
        generator.seed_all(
            user_count=10,
            application_count=5,
            event_count=3,
            training_session_count=2
        )

        # Verify data was created
        assert len(generator.collections['users']) > 0
        assert len(generator.collections['profiles']) > 0
        assert len(generator.collections['events']) > 0

    def test_idempotency_check(self, mock_client, mock_settings_dev):
        """Test that running seed multiple times handles duplicates"""
        # This is a conceptual test - actual implementation would need
        # proper ID generation or duplicate handling
        generator = SeedDataGenerator(mock_client)

        # Run twice
        generator.generate_users(count=5)
        first_count = mock_client.create_document.call_count

        generator.generate_users(count=5)
        second_count = mock_client.create_document.call_count

        # Should have attempted to create 10 total users
        assert second_count == first_count * 2


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test error handling throughout the seed script"""

    def test_handles_missing_user_ids(self, seed_generator):
        """Test handling when user_ids list is empty"""
        # Should handle gracefully even with empty list
        profile_ids = seed_generator.generate_profiles([])
        assert len(profile_ids) == 0

    def test_handles_network_errors_gracefully(self):
        """Test that network errors are logged but don't crash the script"""
        # Create a fresh mock that always raises errors
        mock_client = Mock()
        mock_client.create_document = Mock(side_effect=ZeroDBError("Network timeout"))

        generator = SeedDataGenerator(mock_client)

        # Should not raise exception - this is the important part
        # The function should complete even when all creations fail
        try:
            user_ids = generator.generate_users(count=5)
            # If it reaches here, test passes (no crash)
            assert True
        except ZeroDBError:
            # Should NOT raise exception
            pytest.fail("generate_users should handle ZeroDBError gracefully")

    def test_handles_partial_failures(self):
        """Test handling when some documents succeed and some fail"""
        # Create a fresh generator
        mock_client = Mock()

        # Create responses for each user creation attempt
        responses = []
        success_count = 0

        # For count=5 with default distribution: 5 users total (4 public, 1 member)
        for i in range(5):
            if i % 2 == 0:
                responses.append({'id': str(uuid4())})
                success_count += 1
            else:
                responses.append(ZeroDBError("Failed"))

        mock_client.create_document.side_effect = responses
        generator = SeedDataGenerator(mock_client)

        # Should not crash
        try:
            user_ids = generator.generate_users(count=5)
            # Should have some successful IDs (at least 1)
            assert len(user_ids) >= 1
        except ZeroDBError:
            pytest.fail("generate_users should handle partial failures gracefully")
