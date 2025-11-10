"""
ZeroDB Backup & Recovery Service

This service provides comprehensive backup and restore functionality for all ZeroDB collections.
It handles backup creation, compression, upload to ZeroDB Object Storage, retention policies,
and full restore capabilities with validation.

Features:
- Full and incremental backups for all 14 collections
- Gzip compression for efficient storage
- Upload to ZeroDB Object Storage
- Automated retention policy (7 daily, 4 weekly, 12 monthly backups)
- Point-in-time recovery
- Backup validation and integrity checks
- Comprehensive error handling and logging

Collections:
- users, applications, approvals, subscriptions, payments
- profiles, events, rsvps, training_sessions, session_attendance
- search_queries, content_index, media_assets, audit_logs

Usage:
    from backend.services.backup_service import BackupService

    backup_service = BackupService()

    # Backup all collections
    result = backup_service.backup_all_collections()

    # Backup single collection
    result = backup_service.backup_collection("users")

    # Restore collection
    result = backup_service.restore_collection("users", "users_full_20250109_120000")

    # Restore all collections
    result = backup_service.restore_all_collections("/path/to/backup/directory")
"""

import gzip
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4

from backend.services.zerodb_service import ZeroDBClient, ZeroDBError
from backend.models.schemas import get_all_models
from backend.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Backup configuration constants
BACKUP_METADATA_COLLECTION = "backup_metadata"
BACKUP_VERSION = "1.0.0"
TEMP_DIR = "/tmp/zerodb_backups"

# Retention policy constants
RETENTION_DAILY_DAYS = 7  # Keep daily backups for 7 days
RETENTION_WEEKLY_WEEKS = 4  # Keep weekly backups for 4 weeks
RETENTION_MONTHLY_MONTHS = 12  # Keep monthly backups for 12 months


class BackupError(Exception):
    """Base exception for backup operations"""
    pass


class RestoreError(Exception):
    """Base exception for restore operations"""
    pass


class BackupService:
    """
    Comprehensive backup and restore service for ZeroDB collections.

    This service manages the complete lifecycle of backups including creation,
    compression, storage, retention, and restoration with validation.
    """

    def __init__(self, client: Optional[ZeroDBClient] = None, temp_dir: Optional[str] = None):
        """
        Initialize BackupService

        Args:
            client: ZeroDB client instance (creates new if not provided)
            temp_dir: Temporary directory for backup files (default: /tmp/zerodb_backups)
        """
        self.client = client or ZeroDBClient()
        self.temp_dir = Path(temp_dir or TEMP_DIR)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.collections = list(get_all_models().keys())

        logger.info(
            f"BackupService initialized with {len(self.collections)} collections, "
            f"temp_dir: {self.temp_dir}"
        )

    def get_all_collections(self) -> List[str]:
        """
        Get list of all ZeroDB collection names

        Returns:
            List of collection names from schemas
        """
        return self.collections.copy()

    def get_last_backup_timestamp(
        self,
        collection: str,
        backup_type: str = "full"
    ) -> Optional[datetime]:
        """
        Get timestamp of last successful backup for a collection

        Args:
            collection: Collection name
            backup_type: Type of backup ('full' or 'incremental')

        Returns:
            DateTime of last backup or None if no previous backup exists
        """
        try:
            result = self.client.query_documents(
                collection=BACKUP_METADATA_COLLECTION,
                filters={
                    "collection": collection,
                    "backup_type": backup_type,
                    "status": "completed"
                },
                sort={"completed_at": "desc"},
                limit=1
            )

            documents = result.get("documents", [])
            if documents:
                timestamp_str = documents[0].get("completed_at")
                if timestamp_str:
                    return datetime.fromisoformat(timestamp_str)

            return None

        except ZeroDBError as e:
            logger.warning(f"Could not retrieve last backup timestamp for '{collection}': {e}")
            return None

    def export_collection_data(
        self,
        collection: str,
        incremental: bool = False,
        since_timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Export all documents from a collection to dictionary format

        Args:
            collection: Collection name to export
            incremental: If True, export only documents changed since last backup
            since_timestamp: For incremental backups, only export docs updated after this time

        Returns:
            Dictionary containing collection data and metadata

        Raises:
            BackupError: If export fails
        """
        logger.info(
            f"Exporting collection '{collection}' "
            f"(incremental={incremental}, since={since_timestamp})"
        )

        try:
            # Build filters for incremental backup
            filters = {}
            if incremental and since_timestamp:
                filters = {
                    "updated_at": {"$gte": since_timestamp.isoformat()}
                }

            # Paginated export to handle large collections
            documents = []
            offset = 0
            limit = 100
            total_exported = 0

            while True:
                result = self.client.query_documents(
                    collection=collection,
                    filters=filters,
                    limit=limit,
                    offset=offset,
                    sort={"created_at": "asc"}
                )

                batch = result.get("documents", [])
                if not batch:
                    break

                documents.extend(batch)
                offset += len(batch)
                total_exported += len(batch)

                logger.debug(f"Exported {total_exported} documents from '{collection}'")

                # If we got fewer documents than limit, we're done
                if len(batch) < limit:
                    break

            export_data = {
                "collection": collection,
                "backup_type": "incremental" if incremental else "full",
                "timestamp": datetime.utcnow().isoformat(),
                "document_count": len(documents),
                "since_timestamp": since_timestamp.isoformat() if since_timestamp else None,
                "version": BACKUP_VERSION,
                "documents": documents
            }

            logger.info(
                f"Successfully exported {len(documents)} documents from '{collection}'"
            )

            return export_data

        except ZeroDBError as e:
            error_msg = f"Failed to export collection '{collection}': {e}"
            logger.error(error_msg)
            raise BackupError(error_msg) from e

    def compress_backup(self, data: Dict[str, Any], output_path: Path) -> int:
        """
        Compress backup data to gzip file

        Args:
            data: Backup data dictionary to compress
            output_path: Path where compressed file will be saved

        Returns:
            Size of compressed file in bytes

        Raises:
            BackupError: If compression fails
        """
        logger.debug(f"Compressing backup to '{output_path}'")

        try:
            # Convert to JSON with proper formatting
            json_data = json.dumps(data, indent=2, default=str)
            json_bytes = json_data.encode('utf-8')
            original_size = len(json_bytes)

            # Compress with gzip
            with gzip.open(output_path, 'wb', compresslevel=9) as f:
                f.write(json_bytes)

            compressed_size = output_path.stat().st_size
            compression_ratio = (1 - compressed_size / original_size) * 100

            logger.info(
                f"Compressed {original_size:,} bytes to {compressed_size:,} bytes "
                f"({compression_ratio:.1f}% reduction)"
            )

            return compressed_size

        except Exception as e:
            error_msg = f"Failed to compress backup to '{output_path}': {e}"
            logger.error(error_msg)
            raise BackupError(error_msg) from e

    def upload_to_storage(
        self,
        file_path: Path,
        metadata: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Upload compressed backup file to ZeroDB Object Storage

        Args:
            file_path: Path to compressed backup file
            metadata: Metadata to attach to the uploaded object

        Returns:
            Upload result from ZeroDB Object Storage API

        Raises:
            BackupError: If upload fails
        """
        object_name = f"backups/{file_path.name}"
        logger.info(f"Uploading backup to ZeroDB Object Storage: '{object_name}'")

        try:
            result = self.client.upload_object(
                file_path=str(file_path),
                object_name=object_name,
                metadata=metadata,
                content_type="application/gzip"
            )

            logger.info(f"Successfully uploaded backup: {object_name}")
            return result

        except ZeroDBError as e:
            error_msg = f"Failed to upload backup to object storage: {e}"
            logger.error(error_msg)
            raise BackupError(error_msg) from e

    def save_backup_metadata(
        self,
        backup_id: str,
        collection: str,
        backup_type: str,
        file_name: str,
        file_size: int,
        document_count: int,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Save backup metadata to tracking collection

        Args:
            backup_id: Unique backup identifier
            collection: Collection name that was backed up
            backup_type: Type of backup ('full' or 'incremental')
            file_name: Name of backup file
            file_size: Size of compressed backup file in bytes
            document_count: Number of documents in backup
            additional_metadata: Optional additional metadata to store

        Returns:
            Created metadata document

        Raises:
            BackupError: If metadata save fails
        """
        try:
            metadata = {
                "backup_id": backup_id,
                "collection": collection,
                "backup_type": backup_type,
                "file_name": file_name,
                "object_path": f"backups/{file_name}",
                "file_size": file_size,
                "document_count": document_count,
                "status": "completed",
                "version": BACKUP_VERSION,
                "created_at": datetime.utcnow().isoformat(),
                "completed_at": datetime.utcnow().isoformat()
            }

            # Merge additional metadata if provided
            if additional_metadata:
                metadata.update(additional_metadata)

            result = self.client.create_document(
                collection=BACKUP_METADATA_COLLECTION,
                data=metadata,
                document_id=backup_id
            )

            logger.info(f"Saved backup metadata: {backup_id}")
            return result

        except ZeroDBError as e:
            error_msg = f"Failed to save backup metadata for '{backup_id}': {e}"
            logger.error(error_msg)
            raise BackupError(error_msg) from e

    def apply_retention_policy(self, collection: str) -> Dict[str, Any]:
        """
        Enforce backup retention policy by deleting old backups

        Retention policy:
        - Keep daily backups for 7 days
        - Keep weekly backups for 4 weeks (first backup of each week)
        - Keep monthly backups for 12 months (first backup of each month)

        Args:
            collection: Collection name to enforce retention for

        Returns:
            Summary of retention policy enforcement
        """
        logger.info(f"Enforcing retention policy for collection '{collection}'")

        try:
            # Get all completed backups for this collection
            result = self.client.query_documents(
                collection=BACKUP_METADATA_COLLECTION,
                filters={
                    "collection": collection,
                    "status": "completed"
                },
                sort={"completed_at": "desc"},
                limit=1000  # Should be enough for most cases
            )

            backups = result.get("documents", [])
            if not backups:
                logger.info(f"No backups found for '{collection}'")
                return {
                    "collection": collection,
                    "total_backups": 0,
                    "kept": 0,
                    "deleted": 0
                }

            now = datetime.utcnow()
            keep_backup_ids = set()

            # Track backups by time period
            daily_cutoff = now - timedelta(days=RETENTION_DAILY_DAYS)
            weekly_cutoff = now - timedelta(weeks=RETENTION_WEEKLY_WEEKS)
            monthly_cutoff = now - timedelta(days=RETENTION_MONTHLY_MONTHS * 30)

            weekly_backups = {}  # week_key -> backup
            monthly_backups = {}  # month_key -> backup

            for backup in backups:
                completed_at = datetime.fromisoformat(backup["completed_at"])
                backup_id = backup["backup_id"]

                # Keep all daily backups within retention period
                if completed_at >= daily_cutoff:
                    keep_backup_ids.add(backup_id)
                    continue

                # Track weekly backups (first of each week)
                if completed_at >= weekly_cutoff:
                    week_key = completed_at.strftime("%Y-W%U")
                    if week_key not in weekly_backups:
                        weekly_backups[week_key] = backup
                        keep_backup_ids.add(backup_id)
                    continue

                # Track monthly backups (first of each month)
                if completed_at >= monthly_cutoff:
                    month_key = completed_at.strftime("%Y-%m")
                    if month_key not in monthly_backups:
                        monthly_backups[month_key] = backup
                        keep_backup_ids.add(backup_id)

            # Delete old backups not in keep set
            deleted_count = 0
            deleted_ids = []

            for backup in backups:
                backup_id = backup["backup_id"]

                if backup_id not in keep_backup_ids:
                    try:
                        # Delete from object storage
                        object_path = backup.get("object_path", f"backups/{backup['file_name']}")
                        self.client.delete_object(object_path)

                        # Delete metadata document
                        self.client.delete_document(
                            collection=BACKUP_METADATA_COLLECTION,
                            document_id=backup_id
                        )

                        deleted_count += 1
                        deleted_ids.append(backup_id)
                        logger.info(f"Deleted old backup: {backup_id}")

                    except ZeroDBError as e:
                        logger.warning(f"Failed to delete backup '{backup_id}': {e}")

            summary = {
                "collection": collection,
                "total_backups": len(backups),
                "kept": len(keep_backup_ids),
                "deleted": deleted_count,
                "deleted_ids": deleted_ids
            }

            logger.info(
                f"Retention policy enforced for '{collection}': "
                f"kept {len(keep_backup_ids)}, deleted {deleted_count}"
            )

            return summary

        except ZeroDBError as e:
            logger.error(f"Failed to enforce retention policy for '{collection}': {e}")
            return {
                "collection": collection,
                "error": str(e),
                "total_backups": 0,
                "kept": 0,
                "deleted": 0
            }

    def backup_collection(
        self,
        collection: str,
        incremental: bool = False
    ) -> Dict[str, Any]:
        """
        Perform complete backup workflow for a single collection

        Args:
            collection: Name of collection to backup
            incremental: If True, perform incremental backup (only changed documents)

        Returns:
            Backup result summary with status and metadata

        Raises:
            BackupError: If any step of backup process fails
        """
        backup_type = "incremental" if incremental else "full"
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_id = f"{collection}_{backup_type}_{timestamp}"

        logger.info(f"Starting {backup_type} backup for collection '{collection}'")

        try:
            # For incremental backups, get last backup timestamp
            since_timestamp = None
            if incremental:
                since_timestamp = self.get_last_backup_timestamp(collection, "full")
                if not since_timestamp:
                    logger.warning(
                        f"No previous full backup found for '{collection}'. "
                        f"Performing full backup instead."
                    )
                    incremental = False
                    backup_type = "full"
                    backup_id = f"{collection}_full_{timestamp}"

            # Step 1: Export collection data
            export_data = self.export_collection_data(
                collection=collection,
                incremental=incremental,
                since_timestamp=since_timestamp
            )

            # Step 2: Compress to gzip file
            file_name = f"{backup_id}.json.gz"
            file_path = self.temp_dir / file_name
            file_size = self.compress_backup(export_data, file_path)

            # Step 3: Upload to ZeroDB Object Storage
            upload_metadata = {
                "collection": collection,
                "backup_type": backup_type,
                "timestamp": timestamp,
                "document_count": str(export_data["document_count"]),
                "version": BACKUP_VERSION
            }
            upload_result = self.upload_to_storage(file_path, upload_metadata)

            # Step 4: Save backup metadata
            self.save_backup_metadata(
                backup_id=backup_id,
                collection=collection,
                backup_type=backup_type,
                file_name=file_name,
                file_size=file_size,
                document_count=export_data["document_count"]
            )

            # Step 5: Enforce retention policy
            retention_result = self.apply_retention_policy(collection)

            # Step 6: Cleanup temporary file
            file_path.unlink()

            result = {
                "status": "success",
                "backup_id": backup_id,
                "collection": collection,
                "backup_type": backup_type,
                "timestamp": timestamp,
                "document_count": export_data["document_count"],
                "file_size": file_size,
                "file_name": file_name,
                "object_path": f"backups/{file_name}",
                "upload_result": upload_result,
                "retention_applied": retention_result
            }

            logger.info(
                f"Successfully completed {backup_type} backup for '{collection}': {backup_id}"
            )

            return result

        except Exception as e:
            error_msg = f"Backup failed for collection '{collection}': {e}"
            logger.error(error_msg)
            raise BackupError(error_msg) from e

    def backup_all_collections(
        self,
        incremental: bool = False,
        exclude_collections: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Backup all ZeroDB collections

        Args:
            incremental: If True, perform incremental backups where possible
            exclude_collections: Optional list of collections to exclude from backup

        Returns:
            Summary of all backup operations with individual results
        """
        logger.info(f"Starting backup of all collections (incremental={incremental})")

        exclude_set = set(exclude_collections or [])
        collections_to_backup = [c for c in self.collections if c not in exclude_set]

        results = []
        successful = []
        failed = []

        start_time = datetime.utcnow()

        for collection in collections_to_backup:
            try:
                result = self.backup_collection(
                    collection=collection,
                    incremental=incremental
                )
                results.append(result)
                successful.append(collection)

            except BackupError as e:
                logger.error(f"Failed to backup collection '{collection}': {e}")
                failed.append({
                    "collection": collection,
                    "error": str(e)
                })

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        summary = {
            "status": "completed" if not failed else "completed_with_errors",
            "total_collections": len(collections_to_backup),
            "successful": len(successful),
            "failed": len(failed),
            "duration_seconds": duration,
            "backup_type": "incremental" if incremental else "full",
            "timestamp": end_time.isoformat(),
            "successful_collections": successful,
            "failed_collections": failed,
            "results": results
        }

        logger.info(
            f"Backup all collections completed: {len(successful)} successful, "
            f"{len(failed)} failed in {duration:.2f}s"
        )

        return summary

    def download_backup(self, file_name: str) -> Path:
        """
        Download backup file from ZeroDB Object Storage

        Args:
            file_name: Name of backup file to download

        Returns:
            Path to downloaded file

        Raises:
            RestoreError: If download fails
        """
        object_path = f"backups/{file_name}"
        local_path = self.temp_dir / file_name

        logger.info(f"Downloading backup from '{object_path}'")

        try:
            self.client.download_object(
                object_name=object_path,
                save_path=str(local_path)
            )

            file_size = local_path.stat().st_size
            logger.info(f"Downloaded {file_size:,} bytes to '{local_path}'")

            return local_path

        except ZeroDBError as e:
            error_msg = f"Failed to download backup '{file_name}': {e}"
            logger.error(error_msg)
            raise RestoreError(error_msg) from e

    def decompress_backup(self, file_path: Path) -> Dict[str, Any]:
        """
        Decompress and parse backup file

        Args:
            file_path: Path to compressed backup file

        Returns:
            Parsed backup data dictionary

        Raises:
            RestoreError: If decompression or parsing fails
        """
        logger.info(f"Decompressing backup from '{file_path}'")

        try:
            with gzip.open(file_path, 'rb') as f:
                json_data = f.read()

            data = json.loads(json_data.decode('utf-8'))

            logger.info(
                f"Decompressed {len(json_data):,} bytes, "
                f"found {data.get('document_count', 0)} documents for "
                f"collection '{data.get('collection')}'"
            )

            return data

        except Exception as e:
            error_msg = f"Failed to decompress backup from '{file_path}': {e}"
            logger.error(error_msg)
            raise RestoreError(error_msg) from e

    def validate_backup_data(self, backup_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate backup data structure and integrity

        Args:
            backup_data: Backup data dictionary to validate

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        logger.debug("Validating backup data structure")

        issues = []

        # Check required fields
        required_fields = ["collection", "backup_type", "timestamp", "documents", "document_count"]
        for field in required_fields:
            if field not in backup_data:
                issues.append(f"Missing required field: '{field}'")

        # Validate document count matches
        expected_count = backup_data.get("document_count", 0)
        actual_count = len(backup_data.get("documents", []))

        if expected_count != actual_count:
            issues.append(
                f"Document count mismatch: expected {expected_count}, "
                f"found {actual_count}"
            )

        # Validate collection name exists in schema
        collection = backup_data.get("collection")
        if collection and collection not in self.collections:
            issues.append(f"Unknown collection: '{collection}'")

        # Validate backup type
        backup_type = backup_data.get("backup_type")
        if backup_type and backup_type not in ["full", "incremental"]:
            issues.append(f"Invalid backup type: '{backup_type}'")

        # Validate documents structure
        documents = backup_data.get("documents", [])
        if documents and not isinstance(documents[0], dict):
            issues.append("Invalid document format: expected dictionary")

        is_valid = len(issues) == 0

        if is_valid:
            logger.info("Backup data validation passed")
        else:
            logger.warning(f"Backup data validation failed: {issues}")

        return is_valid, issues

    def restore_collection(
        self,
        collection: str,
        backup_id: str,
        merge: bool = False,
        validate_only: bool = False
    ) -> Dict[str, Any]:
        """
        Restore a collection from a specific backup

        Args:
            collection: Name of collection to restore
            backup_id: ID of backup to restore from
            merge: If True, merge with existing documents; if False, replace
            validate_only: If True, only validate backup without restoring

        Returns:
            Restore result summary

        Raises:
            RestoreError: If restore fails
        """
        logger.info(
            f"Starting restore for collection '{collection}' from backup '{backup_id}' "
            f"(merge={merge}, validate_only={validate_only})"
        )

        try:
            # Step 1: Get backup metadata
            metadata = self.client.get_document(
                collection=BACKUP_METADATA_COLLECTION,
                document_id=backup_id
            )

            # Verify collection matches
            if metadata.get("collection") != collection:
                raise RestoreError(
                    f"Collection mismatch: backup is for '{metadata.get('collection')}', "
                    f"requested '{collection}'"
                )

            # Step 2: Download backup file
            file_name = metadata["file_name"]
            file_path = self.download_backup(file_name)

            # Step 3: Decompress backup
            backup_data = self.decompress_backup(file_path)

            # Step 4: Validate backup data
            is_valid, issues = self.validate_backup_data(backup_data)

            if not is_valid:
                raise RestoreError(f"Backup validation failed: {issues}")

            if validate_only:
                logger.info("Validation complete (validate-only mode)")
                return {
                    "status": "validated",
                    "backup_id": backup_id,
                    "collection": collection,
                    "valid": True,
                    "document_count": backup_data["document_count"]
                }

            # Step 5: Restore documents
            documents = backup_data["documents"]
            created = 0
            updated = 0
            errors = 0
            error_details = []

            for i, doc in enumerate(documents, 1):
                try:
                    doc_id = doc.get("id")

                    if not doc_id:
                        logger.warning(f"Document {i} has no ID, skipping")
                        errors += 1
                        continue

                    # Check if document exists
                    try:
                        existing_doc = self.client.get_document(
                            collection=collection,
                            document_id=doc_id
                        )

                        # Update existing document
                        self.client.update_document(
                            collection=collection,
                            document_id=doc_id,
                            data=doc,
                            merge=merge
                        )
                        updated += 1

                    except ZeroDBError:
                        # Create new document
                        self.client.create_document(
                            collection=collection,
                            data=doc,
                            document_id=doc_id
                        )
                        created += 1

                    # Log progress every 100 documents
                    if i % 100 == 0:
                        logger.info(
                            f"Progress: {i}/{len(documents)} documents "
                            f"(created: {created}, updated: {updated}, errors: {errors})"
                        )

                except Exception as e:
                    errors += 1
                    error_msg = f"Error restoring document {i} (ID: {doc.get('id')}): {e}"
                    logger.error(error_msg)
                    error_details.append(error_msg)

            # Step 6: Cleanup temporary file
            file_path.unlink()

            result = {
                "status": "completed" if errors == 0 else "completed_with_errors",
                "backup_id": backup_id,
                "collection": collection,
                "backup_type": backup_data["backup_type"],
                "backup_timestamp": backup_data["timestamp"],
                "document_count": len(documents),
                "created": created,
                "updated": updated,
                "errors": errors,
                "error_details": error_details[:10]  # Limit to first 10 errors
            }

            logger.info(
                f"Restore completed for '{collection}': "
                f"{created} created, {updated} updated, {errors} errors"
            )

            return result

        except Exception as e:
            error_msg = f"Restore failed for collection '{collection}': {e}"
            logger.error(error_msg)
            raise RestoreError(error_msg) from e

    def restore_all_collections(
        self,
        backup_directory: str,
        merge: bool = False,
        exclude_collections: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Restore all collections from a backup directory

        Args:
            backup_directory: Directory containing backup files
            merge: If True, merge with existing documents; if False, replace
            exclude_collections: Optional list of collections to exclude

        Returns:
            Summary of all restore operations
        """
        logger.info(f"Starting restore of all collections from '{backup_directory}'")

        backup_dir = Path(backup_directory)
        if not backup_dir.exists():
            raise RestoreError(f"Backup directory does not exist: '{backup_directory}'")

        exclude_set = set(exclude_collections or [])
        results = []
        successful = []
        failed = []

        start_time = datetime.utcnow()

        # Find all backup files in directory
        backup_files = list(backup_dir.glob("*.json.gz"))

        if not backup_files:
            raise RestoreError(f"No backup files found in '{backup_directory}'")

        for backup_file in backup_files:
            try:
                # Decompress and validate
                backup_data = self.decompress_backup(backup_file)
                collection = backup_data.get("collection")

                if collection in exclude_set:
                    logger.info(f"Skipping excluded collection: '{collection}'")
                    continue

                is_valid, issues = self.validate_backup_data(backup_data)
                if not is_valid:
                    logger.error(f"Invalid backup file '{backup_file.name}': {issues}")
                    failed.append({
                        "collection": collection,
                        "file": backup_file.name,
                        "error": f"Validation failed: {issues}"
                    })
                    continue

                # Restore documents
                documents = backup_data["documents"]
                created = 0
                updated = 0
                errors = 0

                for doc in documents:
                    try:
                        doc_id = doc.get("id")
                        if not doc_id:
                            errors += 1
                            continue

                        try:
                            self.client.get_document(collection=collection, document_id=doc_id)
                            self.client.update_document(
                                collection=collection,
                                document_id=doc_id,
                                data=doc,
                                merge=merge
                            )
                            updated += 1
                        except ZeroDBError:
                            self.client.create_document(
                                collection=collection,
                                data=doc,
                                document_id=doc_id
                            )
                            created += 1

                    except Exception as e:
                        errors += 1
                        logger.error(f"Error restoring document: {e}")

                result = {
                    "collection": collection,
                    "file": backup_file.name,
                    "document_count": len(documents),
                    "created": created,
                    "updated": updated,
                    "errors": errors
                }

                results.append(result)
                successful.append(collection)
                logger.info(
                    f"Restored '{collection}': {created} created, "
                    f"{updated} updated, {errors} errors"
                )

            except Exception as e:
                logger.error(f"Failed to restore from '{backup_file.name}': {e}")
                failed.append({
                    "file": backup_file.name,
                    "error": str(e)
                })

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        summary = {
            "status": "completed" if not failed else "completed_with_errors",
            "total_files": len(backup_files),
            "successful": len(successful),
            "failed": len(failed),
            "duration_seconds": duration,
            "timestamp": end_time.isoformat(),
            "successful_collections": successful,
            "failed_restores": failed,
            "results": results
        }

        logger.info(
            f"Restore all collections completed: {len(successful)} successful, "
            f"{len(failed)} failed in {duration:.2f}s"
        )

        return summary

    def list_backups(
        self,
        collection: Optional[str] = None,
        backup_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        List available backups with optional filtering

        Args:
            collection: Filter by collection name (optional)
            backup_type: Filter by backup type ('full' or 'incremental', optional)
            limit: Maximum number of backups to return

        Returns:
            List of backup metadata dictionaries
        """
        logger.info(f"Listing backups (collection={collection}, type={backup_type})")

        try:
            filters = {"status": "completed"}
            if collection:
                filters["collection"] = collection
            if backup_type:
                filters["backup_type"] = backup_type

            result = self.client.query_documents(
                collection=BACKUP_METADATA_COLLECTION,
                filters=filters,
                sort={"completed_at": "desc"},
                limit=limit
            )

            backups = result.get("documents", [])
            logger.info(f"Found {len(backups)} backups")

            return backups

        except ZeroDBError as e:
            logger.error(f"Failed to list backups: {e}")
            return []

    def cleanup_old_backups(self, days: int = 30) -> Dict[str, Any]:
        """
        Delete backups older than specified number of days

        Args:
            days: Delete backups older than this many days

        Returns:
            Summary of cleanup operation
        """
        logger.info(f"Cleaning up backups older than {days} days")

        cutoff_date = datetime.utcnow() - timedelta(days=days)
        deleted_count = 0
        deleted_ids = []
        errors = []

        try:
            # Get all backups older than cutoff
            result = self.client.query_documents(
                collection=BACKUP_METADATA_COLLECTION,
                filters={
                    "completed_at": {"$lt": cutoff_date.isoformat()},
                    "status": "completed"
                },
                limit=1000
            )

            old_backups = result.get("documents", [])

            for backup in old_backups:
                backup_id = backup["backup_id"]
                try:
                    # Delete from object storage
                    object_path = backup.get("object_path", f"backups/{backup['file_name']}")
                    self.client.delete_object(object_path)

                    # Delete metadata
                    self.client.delete_document(
                        collection=BACKUP_METADATA_COLLECTION,
                        document_id=backup_id
                    )

                    deleted_count += 1
                    deleted_ids.append(backup_id)
                    logger.info(f"Deleted old backup: {backup_id}")

                except ZeroDBError as e:
                    error_msg = f"Failed to delete backup '{backup_id}': {e}"
                    logger.warning(error_msg)
                    errors.append(error_msg)

            summary = {
                "status": "completed",
                "cutoff_date": cutoff_date.isoformat(),
                "total_found": len(old_backups),
                "deleted": deleted_count,
                "errors": len(errors),
                "deleted_ids": deleted_ids,
                "error_details": errors[:10]
            }

            logger.info(f"Cleanup completed: deleted {deleted_count} backups")
            return summary

        except ZeroDBError as e:
            logger.error(f"Cleanup failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "deleted": deleted_count
            }

    def close(self):
        """Close ZeroDB client and cleanup resources"""
        if hasattr(self, 'client'):
            self.client.close()
            logger.info("BackupService closed")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Convenience function for getting a BackupService instance
def get_backup_service() -> BackupService:
    """
    Get a new BackupService instance

    Returns:
        Configured BackupService instance
    """
    return BackupService()
