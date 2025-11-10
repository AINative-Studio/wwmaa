"""
Comprehensive Unit Tests for BackupService

Tests cover all backup and restore functionality including:
- Collection data export (full and incremental)
- Backup compression and decompression
- Upload/download from ZeroDB Object Storage
- Backup metadata management
- Retention policy enforcement
- Full restore workflow with validation
- Error handling and edge cases

Target: 80%+ code coverage
"""

import gzip
import json
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, MagicMock, patch, call
from uuid import uuid4

from backend.services.backup_service import (
    BackupService,
    BackupError,
    RestoreError,
    BACKUP_METADATA_COLLECTION,
    BACKUP_VERSION
)
from backend.services.zerodb_service import ZeroDBError, ZeroDBNotFoundError


class TestBackupServiceInitialization:
    """Test BackupService initialization and configuration"""

    def test_init_with_defaults(self):
        """Test initialization with default parameters"""
        with patch('backend.services.backup_service.ZeroDBClient'):
            service = BackupService()

            assert service is not None
            assert service.client is not None
            assert service.temp_dir.exists()
            assert len(service.collections) == 14  # All collections from schemas

    def test_init_with_custom_client(self):
        """Test initialization with custom ZeroDB client"""
        mock_client = Mock()
        service = BackupService(client=mock_client)

        assert service.client == mock_client

    def test_init_with_custom_temp_dir(self, tmp_path):
        """Test initialization with custom temporary directory"""
        custom_dir = tmp_path / "custom_backups"

        with patch('backend.services.backup_service.ZeroDBClient'):
            service = BackupService(temp_dir=str(custom_dir))

            assert service.temp_dir == custom_dir
            assert custom_dir.exists()

    def test_get_all_collections(self):
        """Test retrieving all collection names"""
        with patch('backend.services.backup_service.ZeroDBClient'):
            service = BackupService()
            collections = service.get_all_collections()

            assert isinstance(collections, list)
            assert len(collections) == 14
            assert "users" in collections
            assert "profiles" in collections
            assert "events" in collections


class TestBackupMetadata:
    """Test backup metadata operations"""

    @pytest.fixture
    def mock_service(self):
        """Create BackupService with mocked client"""
        mock_client = Mock()
        return BackupService(client=mock_client)

    def test_get_last_backup_timestamp_found(self, mock_service):
        """Test retrieving last backup timestamp when backup exists"""
        timestamp = datetime.utcnow().isoformat()
        mock_service.client.query_documents.return_value = {
            "documents": [{"completed_at": timestamp}]
        }

        result = mock_service.get_last_backup_timestamp("users", "full")

        assert result is not None
        assert isinstance(result, datetime)
        mock_service.client.query_documents.assert_called_once()

    def test_get_last_backup_timestamp_not_found(self, mock_service):
        """Test retrieving last backup timestamp when no backup exists"""
        mock_service.client.query_documents.return_value = {"documents": []}

        result = mock_service.get_last_backup_timestamp("users", "full")

        assert result is None

    def test_get_last_backup_timestamp_error(self, mock_service):
        """Test handling error when retrieving last backup timestamp"""
        mock_service.client.query_documents.side_effect = ZeroDBError("Connection failed")

        result = mock_service.get_last_backup_timestamp("users", "full")

        assert result is None

    def test_save_backup_metadata_success(self, mock_service):
        """Test saving backup metadata successfully"""
        mock_service.client.create_document.return_value = {"id": "backup_123"}

        result = mock_service.save_backup_metadata(
            backup_id="users_full_20250109_120000",
            collection="users",
            backup_type="full",
            file_name="users_full_20250109_120000.json.gz",
            file_size=1024,
            document_count=100
        )

        assert result == {"id": "backup_123"}
        mock_service.client.create_document.assert_called_once()

        # Verify metadata structure
        call_args = mock_service.client.create_document.call_args
        metadata = call_args[1]["data"]

        assert metadata["backup_id"] == "users_full_20250109_120000"
        assert metadata["collection"] == "users"
        assert metadata["backup_type"] == "full"
        assert metadata["file_size"] == 1024
        assert metadata["document_count"] == 100
        assert metadata["status"] == "completed"
        assert metadata["version"] == BACKUP_VERSION

    def test_save_backup_metadata_with_additional(self, mock_service):
        """Test saving backup metadata with additional fields"""
        mock_service.client.create_document.return_value = {"id": "backup_123"}

        additional = {"custom_field": "custom_value"}
        result = mock_service.save_backup_metadata(
            backup_id="users_full_20250109_120000",
            collection="users",
            backup_type="full",
            file_name="test.json.gz",
            file_size=1024,
            document_count=100,
            additional_metadata=additional
        )

        call_args = mock_service.client.create_document.call_args
        metadata = call_args[1]["data"]

        assert metadata["custom_field"] == "custom_value"

    def test_save_backup_metadata_error(self, mock_service):
        """Test error handling when saving backup metadata fails"""
        mock_service.client.create_document.side_effect = ZeroDBError("Save failed")

        with pytest.raises(BackupError, match="Failed to save backup metadata"):
            mock_service.save_backup_metadata(
                backup_id="backup_123",
                collection="users",
                backup_type="full",
                file_name="test.json.gz",
                file_size=1024,
                document_count=100
            )


class TestExportCollectionData:
    """Test collection data export functionality"""

    @pytest.fixture
    def mock_service(self):
        """Create BackupService with mocked client"""
        mock_client = Mock()
        return BackupService(client=mock_client)

    def test_export_collection_full_backup(self, mock_service):
        """Test full collection export"""
        mock_documents = [
            {"id": "1", "name": "User 1"},
            {"id": "2", "name": "User 2"}
        ]

        mock_service.client.query_documents.return_value = {
            "documents": mock_documents
        }

        result = mock_service.export_collection_data("users", incremental=False)

        assert result["collection"] == "users"
        assert result["backup_type"] == "full"
        assert result["document_count"] == 2
        assert len(result["documents"]) == 2
        assert result["version"] == BACKUP_VERSION
        assert "timestamp" in result

    def test_export_collection_incremental_backup(self, mock_service):
        """Test incremental collection export with timestamp filter"""
        since_timestamp = datetime.utcnow() - timedelta(days=1)
        mock_documents = [{"id": "1", "name": "Updated User"}]

        mock_service.client.query_documents.return_value = {
            "documents": mock_documents
        }

        result = mock_service.export_collection_data(
            "users",
            incremental=True,
            since_timestamp=since_timestamp
        )

        assert result["backup_type"] == "incremental"
        assert result["document_count"] == 1
        assert result["since_timestamp"] == since_timestamp.isoformat()

        # Verify filters were applied
        call_args = mock_service.client.query_documents.call_args
        filters = call_args[1]["filters"]
        assert "updated_at" in filters

    def test_export_collection_paginated(self, mock_service):
        """Test paginated export for large collections"""
        # First batch: 100 documents
        first_batch = [{"id": str(i), "name": f"User {i}"} for i in range(100)]
        # Second batch: 50 documents (last page)
        second_batch = [{"id": str(i), "name": f"User {i}"} for i in range(100, 150)]

        mock_service.client.query_documents.side_effect = [
            {"documents": first_batch},
            {"documents": second_batch}
        ]

        result = mock_service.export_collection_data("users")

        assert result["document_count"] == 150
        assert len(result["documents"]) == 150
        assert mock_service.client.query_documents.call_count == 2

    def test_export_collection_empty(self, mock_service):
        """Test export of empty collection"""
        mock_service.client.query_documents.return_value = {"documents": []}

        result = mock_service.export_collection_data("users")

        assert result["document_count"] == 0
        assert len(result["documents"]) == 0

    def test_export_collection_error(self, mock_service):
        """Test error handling when export fails"""
        mock_service.client.query_documents.side_effect = ZeroDBError("Query failed")

        with pytest.raises(BackupError, match="Failed to export collection"):
            mock_service.export_collection_data("users")


class TestCompressionOperations:
    """Test backup compression and decompression"""

    @pytest.fixture
    def mock_service(self, tmp_path):
        """Create BackupService with temporary directory"""
        mock_client = Mock()
        return BackupService(client=mock_client, temp_dir=str(tmp_path))

    def test_compress_backup_success(self, mock_service):
        """Test successful backup compression"""
        data = {
            "collection": "users",
            "backup_type": "full",
            "timestamp": datetime.utcnow().isoformat(),
            "document_count": 2,
            "documents": [
                {"id": "1", "name": "User 1"},
                {"id": "2", "name": "User 2"}
            ]
        }

        output_path = mock_service.temp_dir / "test_backup.json.gz"
        file_size = mock_service.compress_backup(data, output_path)

        assert output_path.exists()
        assert file_size > 0
        assert file_size < len(json.dumps(data).encode())  # Compressed is smaller

    def test_compress_and_decompress_roundtrip(self, mock_service):
        """Test compression and decompression round trip"""
        original_data = {
            "collection": "users",
            "backup_type": "full",
            "timestamp": datetime.utcnow().isoformat(),
            "document_count": 3,
            "documents": [
                {"id": "1", "name": "User 1"},
                {"id": "2", "name": "User 2"},
                {"id": "3", "name": "User 3"}
            ]
        }

        # Compress
        output_path = mock_service.temp_dir / "roundtrip_test.json.gz"
        mock_service.compress_backup(original_data, output_path)

        # Decompress
        decompressed_data = mock_service.decompress_backup(output_path)

        assert decompressed_data == original_data
        assert decompressed_data["document_count"] == 3
        assert len(decompressed_data["documents"]) == 3

    def test_compress_backup_invalid_path(self, mock_service):
        """Test compression with invalid output path"""
        data = {"collection": "users", "documents": []}
        invalid_path = Path("/invalid/path/backup.json.gz")

        with pytest.raises(BackupError, match="Failed to compress backup"):
            mock_service.compress_backup(data, invalid_path)

    def test_decompress_backup_invalid_file(self, mock_service):
        """Test decompression of invalid file"""
        invalid_file = mock_service.temp_dir / "invalid.json.gz"
        invalid_file.write_bytes(b"not a gzip file")

        with pytest.raises(RestoreError, match="Failed to decompress backup"):
            mock_service.decompress_backup(invalid_file)

    def test_decompress_backup_not_found(self, mock_service):
        """Test decompression of non-existent file"""
        non_existent = mock_service.temp_dir / "nonexistent.json.gz"

        with pytest.raises(RestoreError, match="Failed to decompress backup"):
            mock_service.decompress_backup(non_existent)


class TestStorageOperations:
    """Test ZeroDB Object Storage operations"""

    @pytest.fixture
    def mock_service(self, tmp_path):
        """Create BackupService with mocked client"""
        mock_client = Mock()
        return BackupService(client=mock_client, temp_dir=str(tmp_path))

    def test_upload_to_storage_success(self, mock_service):
        """Test successful upload to object storage"""
        # Create a test file
        test_file = mock_service.temp_dir / "test_backup.json.gz"
        test_file.write_bytes(b"test data")

        mock_service.client.upload_object.return_value = {
            "object_id": "obj_123",
            "url": "https://storage.example.com/backups/test_backup.json.gz"
        }

        metadata = {"collection": "users", "backup_type": "full"}
        result = mock_service.upload_to_storage(test_file, metadata)

        assert result["object_id"] == "obj_123"
        mock_service.client.upload_object.assert_called_once()

        # Verify upload parameters
        call_args = mock_service.client.upload_object.call_args
        assert call_args[1]["object_name"] == "backups/test_backup.json.gz"
        assert call_args[1]["metadata"] == metadata
        assert call_args[1]["content_type"] == "application/gzip"

    def test_upload_to_storage_error(self, mock_service):
        """Test error handling when upload fails"""
        test_file = mock_service.temp_dir / "test_backup.json.gz"
        test_file.write_bytes(b"test data")

        mock_service.client.upload_object.side_effect = ZeroDBError("Upload failed")

        with pytest.raises(BackupError, match="Failed to upload backup"):
            mock_service.upload_to_storage(test_file, {})

    def test_download_backup_success(self, mock_service):
        """Test successful backup download"""
        file_name = "users_full_20250109_120000.json.gz"
        expected_path = mock_service.temp_dir / file_name

        def mock_download(object_name, save_path):
            # Simulate file download by creating the file
            Path(save_path).write_bytes(b"downloaded data")

        mock_service.client.download_object.side_effect = mock_download

        result = mock_service.download_backup(file_name)

        assert result == expected_path
        assert expected_path.exists()
        mock_service.client.download_object.assert_called_once_with(
            object_name=f"backups/{file_name}",
            save_path=str(expected_path)
        )

    def test_download_backup_error(self, mock_service):
        """Test error handling when download fails"""
        mock_service.client.download_object.side_effect = ZeroDBError("Download failed")

        with pytest.raises(RestoreError, match="Failed to download backup"):
            mock_service.download_backup("nonexistent_backup.json.gz")


class TestRetentionPolicy:
    """Test backup retention policy enforcement"""

    @pytest.fixture
    def mock_service(self):
        """Create BackupService with mocked client"""
        mock_client = Mock()
        return BackupService(client=mock_client)

    def test_apply_retention_policy_keep_daily(self, mock_service):
        """Test retention policy keeps daily backups within 7 days"""
        now = datetime.utcnow()
        backups = []

        # Create 10 daily backups (last 10 days)
        for i in range(10):
            backup_date = now - timedelta(days=i)
            backups.append({
                "backup_id": f"users_full_{i}",
                "collection": "users",
                "completed_at": backup_date.isoformat(),
                "status": "completed",
                "file_name": f"backup_{i}.json.gz",
                "object_path": f"backups/backup_{i}.json.gz"
            })

        mock_service.client.query_documents.return_value = {"documents": backups}
        mock_service.client.delete_object.return_value = {}
        mock_service.client.delete_document.return_value = {}

        result = mock_service.apply_retention_policy("users")

        # Should keep 7 daily backups at minimum, may keep more for weekly
        assert result["total_backups"] == 10
        assert result["kept"] >= 7
        assert result["deleted"] >= 1

    def test_apply_retention_policy_keep_weekly(self, mock_service):
        """Test retention policy keeps weekly backups"""
        now = datetime.utcnow()
        backups = []

        # Create backups spanning 6 weeks
        for week in range(6):
            backup_date = now - timedelta(weeks=week)
            backups.append({
                "backup_id": f"users_full_week_{week}",
                "collection": "users",
                "completed_at": backup_date.isoformat(),
                "status": "completed",
                "file_name": f"backup_week_{week}.json.gz",
                "object_path": f"backups/backup_week_{week}.json.gz"
            })

        mock_service.client.query_documents.return_value = {"documents": backups}
        mock_service.client.delete_object.return_value = {}
        mock_service.client.delete_document.return_value = {}

        result = mock_service.apply_retention_policy("users")

        # Should keep recent backups based on policy
        assert result["total_backups"] == 6
        assert result["kept"] >= 4  # At least 4 weekly backups

    def test_apply_retention_policy_no_backups(self, mock_service):
        """Test retention policy with no existing backups"""
        mock_service.client.query_documents.return_value = {"documents": []}

        result = mock_service.apply_retention_policy("users")

        assert result["total_backups"] == 0
        assert result["kept"] == 0
        assert result["deleted"] == 0

    def test_apply_retention_policy_delete_error(self, mock_service):
        """Test handling deletion errors during retention enforcement"""
        now = datetime.utcnow()
        old_backup = {
            "backup_id": "users_full_old",
            "collection": "users",
            "completed_at": (now - timedelta(days=365)).isoformat(),
            "status": "completed",
            "file_name": "old_backup.json.gz",
            "object_path": "backups/old_backup.json.gz"
        }

        mock_service.client.query_documents.return_value = {"documents": [old_backup]}
        mock_service.client.delete_object.side_effect = ZeroDBError("Delete failed")

        # Should not raise error, just log warning
        result = mock_service.apply_retention_policy("users")

        assert result["deleted"] == 0


class TestBackupCollection:
    """Test complete backup workflow for single collection"""

    @pytest.fixture
    def mock_service(self, tmp_path):
        """Create BackupService with mocked client"""
        mock_client = Mock()
        service = BackupService(client=mock_client, temp_dir=str(tmp_path))

        # Mock successful operations
        mock_client.query_documents.return_value = {
            "documents": [{"id": "1", "name": "User 1"}]
        }
        mock_client.upload_object.return_value = {"object_id": "obj_123"}
        mock_client.create_document.return_value = {"id": "metadata_123"}

        return service

    def test_backup_collection_full_success(self, mock_service):
        """Test successful full backup of collection"""
        # Add query_documents side effects for retention policy
        mock_service.client.query_documents.side_effect = [
            {"documents": [{"id": "1", "name": "User 1"}]},  # Export data
            {"documents": []}  # Retention policy check
        ]

        result = mock_service.backup_collection("users", incremental=False)

        assert result["status"] == "success"
        assert result["collection"] == "users"
        assert result["backup_type"] == "full"
        assert result["document_count"] >= 0
        assert "backup_id" in result
        assert "timestamp" in result
        assert "file_size" in result

        # Verify all steps were called
        assert mock_service.client.query_documents.called
        assert mock_service.client.upload_object.called
        assert mock_service.client.create_document.called

    def test_backup_collection_incremental_no_previous(self, mock_service):
        """Test incremental backup falls back to full when no previous backup"""
        # No previous backup timestamp
        mock_service.client.query_documents.side_effect = [
            {"documents": []},  # No metadata found
            {"documents": [{"id": "1"}]},  # Collection data
            {"documents": []}  # Retention policy check
        ]

        result = mock_service.backup_collection("users", incremental=True)

        # Should fallback to full backup
        assert result["backup_type"] == "full"

    def test_backup_collection_export_error(self, mock_service):
        """Test error handling when export fails"""
        mock_service.client.query_documents.side_effect = ZeroDBError("Export failed")

        with pytest.raises(BackupError, match="Backup failed for collection"):
            mock_service.backup_collection("users")


class TestRestoreCollection:
    """Test collection restore functionality"""

    @pytest.fixture
    def mock_service(self, tmp_path):
        """Create BackupService with mocked client and test backup"""
        mock_client = Mock()
        service = BackupService(client=mock_client, temp_dir=str(tmp_path))

        # Create a test backup file
        backup_data = {
            "collection": "users",
            "backup_type": "full",
            "timestamp": datetime.utcnow().isoformat(),
            "document_count": 2,
            "documents": [
                {"id": "user_1", "name": "User 1"},
                {"id": "user_2", "name": "User 2"}
            ]
        }

        backup_file = tmp_path / "users_full_20250109_120000.json.gz"
        with gzip.open(backup_file, 'wb') as f:
            f.write(json.dumps(backup_data).encode())

        # Mock metadata retrieval
        mock_client.get_document.return_value = {
            "backup_id": "users_full_20250109_120000",
            "collection": "users",
            "file_name": "users_full_20250109_120000.json.gz"
        }

        # Mock download to just use existing file
        def mock_download(object_name, save_path):
            pass  # File already exists in tmp_path

        mock_client.download_object.side_effect = mock_download

        return service

    def test_restore_collection_validate_only(self, mock_service):
        """Test validation-only restore mode"""
        result = mock_service.restore_collection(
            "users",
            "users_full_20250109_120000",
            validate_only=True
        )

        assert result["status"] == "validated"
        assert result["valid"] == True
        assert result["document_count"] == 2

    def test_restore_collection_create_documents(self, mock_service):
        """Test restore creating new documents"""
        # Mock documents don't exist
        mock_service.client.get_document.side_effect = [
            # First call for backup metadata
            {
                "backup_id": "users_full_20250109_120000",
                "collection": "users",
                "file_name": "users_full_20250109_120000.json.gz"
            },
            # Subsequent calls for checking document existence
            ZeroDBNotFoundError("Not found"),
            ZeroDBNotFoundError("Not found")
        ]

        mock_service.client.create_document.return_value = {"id": "created"}

        result = mock_service.restore_collection(
            "users",
            "users_full_20250109_120000"
        )

        assert result["status"] == "completed"
        assert result["created"] == 2
        assert result["updated"] == 0
        assert result["errors"] == 0

    def test_restore_collection_update_documents(self, mock_service):
        """Test restore updating existing documents"""
        # Mock metadata retrieval first, then document existence checks
        mock_service.client.get_document.side_effect = [
            # First call for backup metadata
            {
                "backup_id": "users_full_20250109_120000",
                "collection": "users",
                "file_name": "users_full_20250109_120000.json.gz"
            },
            # Next calls for checking document existence
            {"id": "existing"},
            {"id": "existing"}
        ]
        mock_service.client.update_document.return_value = {"id": "updated"}

        result = mock_service.restore_collection(
            "users",
            "users_full_20250109_120000"
        )

        assert mock_service.client.update_document.call_count == 2
        assert result["updated"] == 2
        assert result["created"] == 0

    def test_restore_collection_merge_mode(self, mock_service):
        """Test restore with merge mode enabled"""
        mock_service.client.get_document.side_effect = [
            # First call for backup metadata
            {
                "backup_id": "users_full_20250109_120000",
                "collection": "users",
                "file_name": "users_full_20250109_120000.json.gz"
            },
            # Next calls for checking document existence
            {"id": "existing"},
            {"id": "existing"}
        ]
        mock_service.client.update_document.return_value = {"id": "updated"}

        result = mock_service.restore_collection(
            "users",
            "users_full_20250109_120000",
            merge=True
        )

        # Verify merge=True was passed to update_document
        call_args = mock_service.client.update_document.call_args_list
        for call in call_args:
            assert call[1]["merge"] == True

    def test_restore_collection_wrong_collection(self, mock_service):
        """Test error when backup is for different collection"""
        mock_service.client.get_document.return_value = {
            "backup_id": "profiles_full_20250109_120000",
            "collection": "profiles",  # Different collection
            "file_name": "profiles_full_20250109_120000.json.gz"
        }

        with pytest.raises(RestoreError, match="Collection mismatch"):
            mock_service.restore_collection(
                "users",
                "profiles_full_20250109_120000"
            )


class TestValidateBackupData:
    """Test backup data validation"""

    @pytest.fixture
    def mock_service(self):
        """Create BackupService with mocked client"""
        mock_client = Mock()
        return BackupService(client=mock_client)

    def test_validate_backup_data_valid(self, mock_service):
        """Test validation of valid backup data"""
        valid_data = {
            "collection": "users",
            "backup_type": "full",
            "timestamp": datetime.utcnow().isoformat(),
            "document_count": 2,
            "documents": [
                {"id": "1", "name": "User 1"},
                {"id": "2", "name": "User 2"}
            ]
        }

        is_valid, issues = mock_service.validate_backup_data(valid_data)

        assert is_valid == True
        assert len(issues) == 0

    def test_validate_backup_data_missing_fields(self, mock_service):
        """Test validation fails for missing required fields"""
        invalid_data = {
            "collection": "users"
            # Missing other required fields
        }

        is_valid, issues = mock_service.validate_backup_data(invalid_data)

        assert is_valid == False
        assert len(issues) > 0
        assert any("Missing required field" in issue for issue in issues)

    def test_validate_backup_data_count_mismatch(self, mock_service):
        """Test validation fails for document count mismatch"""
        invalid_data = {
            "collection": "users",
            "backup_type": "full",
            "timestamp": datetime.utcnow().isoformat(),
            "document_count": 5,  # Says 5
            "documents": [{"id": "1"}]  # But only 1 document
        }

        is_valid, issues = mock_service.validate_backup_data(invalid_data)

        assert is_valid == False
        assert any("count mismatch" in issue.lower() for issue in issues)

    def test_validate_backup_data_invalid_collection(self, mock_service):
        """Test validation fails for unknown collection"""
        invalid_data = {
            "collection": "nonexistent_collection",
            "backup_type": "full",
            "timestamp": datetime.utcnow().isoformat(),
            "document_count": 0,
            "documents": []
        }

        is_valid, issues = mock_service.validate_backup_data(invalid_data)

        assert is_valid == False
        assert any("Unknown collection" in issue for issue in issues)


class TestBackupAllCollections:
    """Test backing up all collections"""

    @pytest.fixture
    def mock_service(self, tmp_path):
        """Create BackupService with mocked successful operations"""
        mock_client = Mock()
        service = BackupService(client=mock_client, temp_dir=str(tmp_path))

        # Mock successful operations
        mock_client.query_documents.return_value = {"documents": [{"id": "1"}]}
        mock_client.upload_object.return_value = {"object_id": "obj_123"}
        mock_client.create_document.return_value = {"id": "metadata_123"}

        return service

    def test_backup_all_collections_success(self, mock_service):
        """Test successful backup of all collections"""
        # Mock query_documents to return data for export and empty for retention
        def query_side_effect(*args, **kwargs):
            collection = kwargs.get("collection", "")
            if collection == BACKUP_METADATA_COLLECTION:
                return {"documents": []}  # No existing backups for retention
            return {"documents": [{"id": "1"}]}  # Collection data

        mock_service.client.query_documents.side_effect = query_side_effect

        result = mock_service.backup_all_collections()

        assert result["status"] == "completed"
        assert result["total_collections"] == 14
        assert result["successful"] == 14
        assert result["failed"] == 0
        assert len(result["successful_collections"]) == 14

    def test_backup_all_collections_with_failures(self, mock_service):
        """Test backup all with some failures"""
        # Make specific collection fail
        def query_side_effect(*args, **kwargs):
            collection = kwargs.get("collection", "")
            if collection == "users":
                raise ZeroDBError("Connection error")
            return {"documents": [{"id": "1"}]}

        mock_service.client.query_documents.side_effect = query_side_effect

        result = mock_service.backup_all_collections()

        assert result["status"] == "completed_with_errors"
        assert result["failed"] > 0
        assert len(result["failed_collections"]) > 0

    def test_backup_all_collections_exclude(self, mock_service):
        """Test backup all with exclusions"""
        exclude = ["audit_logs", "search_queries"]

        result = mock_service.backup_all_collections(exclude_collections=exclude)

        assert result["total_collections"] == 12  # 14 - 2 excluded
        assert all(coll not in result["successful_collections"] for coll in exclude)


class TestListBackups:
    """Test listing available backups"""

    @pytest.fixture
    def mock_service(self):
        """Create BackupService with mocked client"""
        mock_client = Mock()
        return BackupService(client=mock_client)

    def test_list_backups_all(self, mock_service):
        """Test listing all backups"""
        mock_backups = [
            {"backup_id": "users_full_1", "collection": "users"},
            {"backup_id": "profiles_full_1", "collection": "profiles"}
        ]

        mock_service.client.query_documents.return_value = {"documents": mock_backups}

        result = mock_service.list_backups()

        assert len(result) == 2
        assert result == mock_backups

    def test_list_backups_filtered(self, mock_service):
        """Test listing backups with filters"""
        mock_backups = [
            {"backup_id": "users_full_1", "collection": "users", "backup_type": "full"}
        ]

        mock_service.client.query_documents.return_value = {"documents": mock_backups}

        result = mock_service.list_backups(collection="users", backup_type="full")

        assert len(result) == 1
        assert result[0]["collection"] == "users"

        # Verify filters were applied
        call_args = mock_service.client.query_documents.call_args
        filters = call_args[1]["filters"]
        assert filters["collection"] == "users"
        assert filters["backup_type"] == "full"

    def test_list_backups_error(self, mock_service):
        """Test list backups handles errors gracefully"""
        mock_service.client.query_documents.side_effect = ZeroDBError("Connection error")

        result = mock_service.list_backups()

        assert result == []


class TestCleanupOldBackups:
    """Test cleanup of old backups"""

    @pytest.fixture
    def mock_service(self):
        """Create BackupService with mocked client"""
        mock_client = Mock()
        return BackupService(client=mock_client)

    def test_cleanup_old_backups_success(self, mock_service):
        """Test successful cleanup of old backups"""
        old_date = (datetime.utcnow() - timedelta(days=60)).isoformat()

        old_backups = [
            {
                "backup_id": "old_backup_1",
                "completed_at": old_date,
                "file_name": "old_1.json.gz",
                "object_path": "backups/old_1.json.gz"
            }
        ]

        mock_service.client.query_documents.return_value = {"documents": old_backups}
        mock_service.client.delete_object.return_value = {}
        mock_service.client.delete_document.return_value = {}

        result = mock_service.cleanup_old_backups(days=30)

        assert result["status"] == "completed"
        assert result["total_found"] == 1
        assert result["deleted"] == 1
        assert "old_backup_1" in result["deleted_ids"]

    def test_cleanup_old_backups_none_found(self, mock_service):
        """Test cleanup when no old backups exist"""
        mock_service.client.query_documents.return_value = {"documents": []}

        result = mock_service.cleanup_old_backups(days=30)

        assert result["deleted"] == 0
        assert result["total_found"] == 0


class TestContextManager:
    """Test BackupService as context manager"""

    def test_context_manager_usage(self):
        """Test using BackupService with context manager"""
        with patch('backend.services.backup_service.ZeroDBClient'):
            with BackupService() as service:
                assert service is not None
                assert hasattr(service, 'client')

            # After context exit, client should be closed
            # (verify close was called if client is a mock)


class TestEdgeCases:
    """Test edge cases and error conditions"""

    @pytest.fixture
    def mock_service(self, tmp_path):
        """Create BackupService with mocked client"""
        mock_client = Mock()
        return BackupService(client=mock_client, temp_dir=str(tmp_path))

    def test_backup_with_unicode_data(self, mock_service):
        """Test backup handles Unicode characters correctly"""
        unicode_docs = [
            {"id": "1", "name": "用户一", "bio": "こんにちは"},
            {"id": "2", "name": "مستخدم", "bio": "Здравствуйте"}
        ]

        mock_service.client.query_documents.return_value = {"documents": unicode_docs}

        result = mock_service.export_collection_data("users")

        assert result["document_count"] == 2
        assert result["documents"][0]["name"] == "用户一"

    def test_backup_with_large_documents(self, mock_service):
        """Test backup handles large documents"""
        large_doc = {
            "id": "1",
            "data": "x" * 1000000  # 1MB of data
        }

        mock_service.client.query_documents.return_value = {"documents": [large_doc]}

        result = mock_service.export_collection_data("users")

        assert result["document_count"] == 1
        assert len(result["documents"][0]["data"]) == 1000000
