#!/usr/bin/env python3
"""
ZeroDB Backup Script

This script exports all ZeroDB collections to compressed JSON files and uploads
them to ZeroDB Object Storage with proper metadata and retention policy.

Features:
- Full and incremental backups
- Gzip compression
- Upload to ZeroDB Object Storage
- Retention policy (30 daily, 12 monthly backups)
- Backup metadata tracking
- Error handling and logging

Usage:
    python backup_zerodb.py [--incremental] [--collections COLLECTIONS] [--dry-run]

Examples:
    # Full backup of all collections
    python backup_zerodb.py

    # Incremental backup
    python backup_zerodb.py --incremental

    # Backup specific collections
    python backup_zerodb.py --collections users,promotions

    # Dry run (no upload)
    python backup_zerodb.py --dry-run
"""

import argparse
import gzip
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add backend to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.zerodb_service import ZeroDBClient, ZeroDBError
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/tmp/zerodb_backup.log')
    ]
)
logger = logging.getLogger(__name__)

# Backup configuration
BACKUP_METADATA_COLLECTION = "backup_metadata"
DEFAULT_COLLECTIONS = ["users", "promotions", "members", "events", "approvals"]
RETENTION_DAILY = 30  # Keep last 30 daily backups
RETENTION_MONTHLY = 12  # Keep last 12 monthly backups
TEMP_DIR = "/tmp/zerodb_backups"


class BackupManager:
    """
    Manages ZeroDB backup operations including creation, compression,
    upload to object storage, and retention policy enforcement.
    """

    def __init__(self, client: Optional[ZeroDBClient] = None):
        """
        Initialize BackupManager

        Args:
            client: ZeroDB client instance (creates new if not provided)
        """
        self.client = client or ZeroDBClient()
        self.temp_dir = Path(TEMP_DIR)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        logger.info("BackupManager initialized")

    def get_last_backup_timestamp(self, collection: str, backup_type: str) -> Optional[str]:
        """
        Get timestamp of last backup for a collection

        Args:
            collection: Collection name
            backup_type: Type of backup ('full' or 'incremental')

        Returns:
            ISO timestamp string or None if no previous backup
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
                return documents[0].get("completed_at")

            return None
        except ZeroDBError as e:
            logger.warning(f"Could not retrieve last backup timestamp: {e}")
            return None

    def export_collection(
        self,
        collection: str,
        incremental: bool = False,
        last_backup_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Export collection data to JSON

        Args:
            collection: Collection name to export
            incremental: If True, export only changed documents
            last_backup_time: Timestamp of last backup (for incremental)

        Returns:
            Dict with collection data and metadata
        """
        logger.info(f"Exporting collection '{collection}' (incremental={incremental})")

        filters = {}
        if incremental and last_backup_time:
            # Query only documents updated since last backup
            filters = {
                "updated_at": {"$gte": last_backup_time}
            }

        documents = []
        offset = 0
        limit = 100
        total_docs = 0

        # Paginated export to handle large collections
        while True:
            try:
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
                total_docs += len(batch)

                logger.info(f"Exported {total_docs} documents from '{collection}'")

                # If we got fewer documents than limit, we're done
                if len(batch) < limit:
                    break

            except ZeroDBError as e:
                logger.error(f"Error exporting collection '{collection}': {e}")
                raise

        export_data = {
            "collection": collection,
            "backup_type": "incremental" if incremental else "full",
            "timestamp": datetime.utcnow().isoformat(),
            "document_count": len(documents),
            "last_backup_time": last_backup_time,
            "documents": documents
        }

        logger.info(f"Exported {len(documents)} documents from '{collection}'")
        return export_data

    def compress_backup(self, data: Dict[str, Any], output_path: Path) -> int:
        """
        Compress backup data to gzip file

        Args:
            data: Backup data dictionary
            output_path: Path to save compressed file

        Returns:
            Size of compressed file in bytes
        """
        logger.info(f"Compressing backup to '{output_path}'")

        json_data = json.dumps(data, indent=2, default=str)
        json_bytes = json_data.encode('utf-8')

        with gzip.open(output_path, 'wb') as f:
            f.write(json_bytes)

        file_size = output_path.stat().st_size
        compression_ratio = (1 - file_size / len(json_bytes)) * 100

        logger.info(
            f"Compressed {len(json_bytes)} bytes to {file_size} bytes "
            f"({compression_ratio:.1f}% compression)"
        )

        return file_size

    def upload_backup(self, file_path: Path, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upload backup file to ZeroDB Object Storage

        Args:
            file_path: Path to backup file
            metadata: Backup metadata

        Returns:
            Upload result from ZeroDB
        """
        object_name = f"backups/{file_path.name}"
        logger.info(f"Uploading backup to '{object_name}'")

        try:
            result = self.client.upload_object(
                file_path=str(file_path),
                object_name=object_name,
                metadata=metadata,
                content_type="application/gzip"
            )

            logger.info(f"Backup uploaded successfully: {object_name}")
            return result

        except ZeroDBError as e:
            logger.error(f"Failed to upload backup: {e}")
            raise

    def save_backup_metadata(
        self,
        collection: str,
        backup_type: str,
        file_name: str,
        file_size: int,
        document_count: int,
        backup_id: str
    ) -> Dict[str, Any]:
        """
        Save backup metadata to tracking collection

        Args:
            collection: Collection name that was backed up
            backup_type: Type of backup ('full' or 'incremental')
            file_name: Name of backup file
            file_size: Size of backup file in bytes
            document_count: Number of documents in backup
            backup_id: Unique backup identifier

        Returns:
            Created metadata document
        """
        metadata = {
            "backup_id": backup_id,
            "collection": collection,
            "backup_type": backup_type,
            "file_name": file_name,
            "object_path": f"backups/{file_name}",
            "file_size": file_size,
            "document_count": document_count,
            "status": "completed",
            "created_at": datetime.utcnow().isoformat(),
            "completed_at": datetime.utcnow().isoformat()
        }

        try:
            result = self.client.create_document(
                collection=BACKUP_METADATA_COLLECTION,
                data=metadata,
                document_id=backup_id
            )

            logger.info(f"Backup metadata saved: {backup_id}")
            return result

        except ZeroDBError as e:
            logger.error(f"Failed to save backup metadata: {e}")
            raise

    def cleanup_old_backups(self, collection: str):
        """
        Enforce retention policy by deleting old backups

        Retention policy:
        - Keep last 30 daily backups
        - Keep last 12 monthly backups (first backup of each month)

        Args:
            collection: Collection name
        """
        logger.info(f"Enforcing retention policy for '{collection}'")

        try:
            # Get all backups for this collection, sorted by date (newest first)
            result = self.client.query_documents(
                collection=BACKUP_METADATA_COLLECTION,
                filters={"collection": collection, "status": "completed"},
                sort={"completed_at": "desc"},
                limit=100
            )

            backups = result.get("documents", [])

            if not backups:
                logger.info("No backups found for retention policy enforcement")
                return

            # Separate daily and monthly backups
            daily_backups = []
            monthly_backups = {}

            for backup in backups:
                completed_at = datetime.fromisoformat(backup["completed_at"])
                month_key = completed_at.strftime("%Y-%m")

                # Track first backup of each month
                if month_key not in monthly_backups:
                    monthly_backups[month_key] = backup

                daily_backups.append(backup)

            # Determine which backups to keep
            keep_backup_ids = set()

            # Keep last 30 daily backups
            for backup in daily_backups[:RETENTION_DAILY]:
                keep_backup_ids.add(backup["backup_id"])

            # Keep last 12 monthly backups
            monthly_list = sorted(monthly_backups.items(), reverse=True)[:RETENTION_MONTHLY]
            for _, backup in monthly_list:
                keep_backup_ids.add(backup["backup_id"])

            # Delete old backups
            deleted_count = 0
            for backup in backups:
                if backup["backup_id"] not in keep_backup_ids:
                    try:
                        # Delete from object storage
                        self.client.delete_object(backup["file_name"])

                        # Delete metadata
                        self.client.delete_document(
                            collection=BACKUP_METADATA_COLLECTION,
                            document_id=backup["backup_id"]
                        )

                        deleted_count += 1
                        logger.info(f"Deleted old backup: {backup['backup_id']}")

                    except ZeroDBError as e:
                        logger.warning(f"Failed to delete backup {backup['backup_id']}: {e}")

            logger.info(
                f"Retention policy enforced: kept {len(keep_backup_ids)} backups, "
                f"deleted {deleted_count} old backups"
            )

        except ZeroDBError as e:
            logger.error(f"Error enforcing retention policy: {e}")

    def backup_collection(
        self,
        collection: str,
        incremental: bool = False,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Perform full backup workflow for a collection

        Args:
            collection: Collection name to backup
            incremental: If True, perform incremental backup
            dry_run: If True, don't upload to object storage

        Returns:
            Backup result summary
        """
        backup_type = "incremental" if incremental else "full"
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_id = f"{collection}_{backup_type}_{timestamp}"

        logger.info(f"Starting {backup_type} backup for '{collection}'")

        try:
            # Get last backup timestamp for incremental
            last_backup_time = None
            if incremental:
                last_backup_time = self.get_last_backup_timestamp(collection, "full")
                if not last_backup_time:
                    logger.warning(
                        f"No previous full backup found for '{collection}'. "
                        "Performing full backup instead."
                    )
                    incremental = False
                    backup_type = "full"

            # Export collection data
            export_data = self.export_collection(
                collection=collection,
                incremental=incremental,
                last_backup_time=last_backup_time
            )

            # Compress to file
            file_name = f"{backup_id}.json.gz"
            file_path = self.temp_dir / file_name
            file_size = self.compress_backup(export_data, file_path)

            upload_result = None
            if not dry_run:
                # Upload to object storage
                metadata = {
                    "collection": collection,
                    "backup_type": backup_type,
                    "timestamp": timestamp,
                    "document_count": str(export_data["document_count"])
                }
                upload_result = self.upload_backup(file_path, metadata)

                # Save metadata
                self.save_backup_metadata(
                    collection=collection,
                    backup_type=backup_type,
                    file_name=file_name,
                    file_size=file_size,
                    document_count=export_data["document_count"],
                    backup_id=backup_id
                )

                # Enforce retention policy
                self.cleanup_old_backups(collection)

            # Cleanup temp file
            file_path.unlink()

            result = {
                "status": "success",
                "backup_id": backup_id,
                "collection": collection,
                "backup_type": backup_type,
                "document_count": export_data["document_count"],
                "file_size": file_size,
                "file_name": file_name,
                "dry_run": dry_run,
                "upload_result": upload_result
            }

            logger.info(f"Backup completed successfully: {backup_id}")
            return result

        except Exception as e:
            logger.error(f"Backup failed for '{collection}': {e}")
            raise


def main():
    """Main entry point for backup script"""
    parser = argparse.ArgumentParser(
        description="ZeroDB Backup Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Perform incremental backup (only changed documents)"
    )

    parser.add_argument(
        "--collections",
        type=str,
        help="Comma-separated list of collections to backup (default: all)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform backup without uploading to object storage"
    )

    args = parser.parse_args()

    # Determine which collections to backup
    if args.collections:
        collections = [c.strip() for c in args.collections.split(",")]
    else:
        collections = DEFAULT_COLLECTIONS

    logger.info(f"Starting backup for collections: {collections}")
    logger.info(f"Incremental: {args.incremental}, Dry run: {args.dry_run}")

    backup_manager = BackupManager()
    results = []
    failed_collections = []

    for collection in collections:
        try:
            result = backup_manager.backup_collection(
                collection=collection,
                incremental=args.incremental,
                dry_run=args.dry_run
            )
            results.append(result)

        except Exception as e:
            logger.error(f"Failed to backup '{collection}': {e}")
            failed_collections.append(collection)

    # Print summary
    print("\n" + "=" * 80)
    print("BACKUP SUMMARY")
    print("=" * 80)

    for result in results:
        print(f"\nCollection: {result['collection']}")
        print(f"  Status: {result['status']}")
        print(f"  Backup ID: {result['backup_id']}")
        print(f"  Type: {result['backup_type']}")
        print(f"  Documents: {result['document_count']}")
        print(f"  File size: {result['file_size']:,} bytes")
        print(f"  File name: {result['file_name']}")
        if result['dry_run']:
            print("  Note: DRY RUN - Not uploaded")

    if failed_collections:
        print(f"\nFailed collections: {', '.join(failed_collections)}")
        sys.exit(1)

    print(f"\nBackup completed successfully for {len(results)} collections")
    sys.exit(0)


if __name__ == "__main__":
    main()
