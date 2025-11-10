#!/usr/bin/env python3
"""
ZeroDB Restore Script

This script restores ZeroDB collections from compressed backup files stored
in ZeroDB Object Storage. Supports point-in-time recovery and dry-run mode.

Features:
- List available backups
- Download from ZeroDB Object Storage
- Decompress gzip files
- Restore collections
- Point-in-time recovery
- Dry-run mode for safety
- Backup validation

Usage:
    python restore_zerodb.py --list
    python restore_zerodb.py --backup-id BACKUP_ID [--dry-run] [--validate-only]
    python restore_zerodb.py --point-in-time TIMESTAMP [--collections COLLECTIONS]

Examples:
    # List available backups
    python restore_zerodb.py --list

    # Restore specific backup (dry run first)
    python restore_zerodb.py --backup-id users_full_20250109_120000 --dry-run

    # Restore specific backup
    python restore_zerodb.py --backup-id users_full_20250109_120000

    # Point-in-time recovery (latest backup before timestamp)
    python restore_zerodb.py --point-in-time "2025-01-09T12:00:00"

    # Validate backup without restoring
    python restore_zerodb.py --backup-id users_full_20250109_120000 --validate-only
"""

import argparse
import gzip
import json
import logging
import sys
from datetime import datetime
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
        logging.FileHandler('/tmp/zerodb_restore.log')
    ]
)
logger = logging.getLogger(__name__)

# Restore configuration
BACKUP_METADATA_COLLECTION = "backup_metadata"
TEMP_DIR = "/tmp/zerodb_restores"


class RestoreManager:
    """
    Manages ZeroDB restore operations including listing backups,
    downloading from object storage, decompression, and restoration.
    """

    def __init__(self, client: Optional[ZeroDBClient] = None):
        """
        Initialize RestoreManager

        Args:
            client: ZeroDB client instance (creates new if not provided)
        """
        self.client = client or ZeroDBClient()
        self.temp_dir = Path(TEMP_DIR)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        logger.info("RestoreManager initialized")

    def list_backups(
        self,
        collection: Optional[str] = None,
        backup_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        List available backups from metadata collection

        Args:
            collection: Filter by collection name (optional)
            backup_type: Filter by backup type ('full' or 'incremental', optional)
            limit: Maximum number of backups to return

        Returns:
            List of backup metadata dictionaries
        """
        logger.info("Listing available backups")

        filters = {"status": "completed"}
        if collection:
            filters["collection"] = collection
        if backup_type:
            filters["backup_type"] = backup_type

        try:
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
            raise

    def get_backup_metadata(self, backup_id: str) -> Dict[str, Any]:
        """
        Get metadata for a specific backup

        Args:
            backup_id: Backup identifier

        Returns:
            Backup metadata dictionary
        """
        logger.info(f"Retrieving metadata for backup '{backup_id}'")

        try:
            metadata = self.client.get_document(
                collection=BACKUP_METADATA_COLLECTION,
                document_id=backup_id
            )

            logger.info(f"Found metadata for backup '{backup_id}'")
            return metadata

        except ZeroDBError as e:
            logger.error(f"Failed to retrieve backup metadata: {e}")
            raise

    def find_point_in_time_backup(
        self,
        collection: str,
        timestamp: str
    ) -> Optional[Dict[str, Any]]:
        """
        Find the most recent full backup before a given timestamp

        Args:
            collection: Collection name
            timestamp: ISO format timestamp

        Returns:
            Backup metadata or None if not found
        """
        logger.info(f"Finding backup for '{collection}' before {timestamp}")

        try:
            # Query full backups before the timestamp
            result = self.client.query_documents(
                collection=BACKUP_METADATA_COLLECTION,
                filters={
                    "collection": collection,
                    "backup_type": "full",
                    "completed_at": {"$lte": timestamp},
                    "status": "completed"
                },
                sort={"completed_at": "desc"},
                limit=1
            )

            backups = result.get("documents", [])
            if backups:
                logger.info(f"Found backup: {backups[0]['backup_id']}")
                return backups[0]

            logger.warning(f"No backup found before {timestamp}")
            return None

        except ZeroDBError as e:
            logger.error(f"Failed to find point-in-time backup: {e}")
            raise

    def download_backup(self, file_name: str) -> Path:
        """
        Download backup file from ZeroDB Object Storage

        Args:
            file_name: Name of backup file

        Returns:
            Path to downloaded file
        """
        object_path = f"backups/{file_name}"
        logger.info(f"Downloading backup from '{object_path}'")

        try:
            local_path = self.temp_dir / file_name

            self.client.download_object(
                object_name=object_path,
                save_path=str(local_path)
            )

            file_size = local_path.stat().st_size
            logger.info(f"Downloaded {file_size:,} bytes to '{local_path}'")

            return local_path

        except ZeroDBError as e:
            logger.error(f"Failed to download backup: {e}")
            raise

    def decompress_backup(self, file_path: Path) -> Dict[str, Any]:
        """
        Decompress and parse backup file

        Args:
            file_path: Path to compressed backup file

        Returns:
            Parsed backup data dictionary
        """
        logger.info(f"Decompressing backup from '{file_path}'")

        try:
            with gzip.open(file_path, 'rb') as f:
                json_data = f.read()

            data = json.loads(json_data.decode('utf-8'))

            logger.info(
                f"Decompressed {len(json_data):,} bytes, "
                f"found {data.get('document_count', 0)} documents"
            )

            return data

        except Exception as e:
            logger.error(f"Failed to decompress backup: {e}")
            raise

    def validate_backup(self, backup_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate backup data structure and content

        Args:
            backup_data: Backup data dictionary

        Returns:
            Validation result with status and details
        """
        logger.info("Validating backup data")

        issues = []

        # Check required fields
        required_fields = ["collection", "backup_type", "timestamp", "documents"]
        for field in required_fields:
            if field not in backup_data:
                issues.append(f"Missing required field: {field}")

        # Validate document count
        expected_count = backup_data.get("document_count", 0)
        actual_count = len(backup_data.get("documents", []))

        if expected_count != actual_count:
            issues.append(
                f"Document count mismatch: expected {expected_count}, "
                f"found {actual_count}"
            )

        # Validate document structure
        documents = backup_data.get("documents", [])
        if documents:
            sample_doc = documents[0]
            if not isinstance(sample_doc, dict):
                issues.append("Invalid document format: expected dictionary")

        result = {
            "valid": len(issues) == 0,
            "issues": issues,
            "collection": backup_data.get("collection"),
            "backup_type": backup_data.get("backup_type"),
            "document_count": actual_count
        }

        if result["valid"]:
            logger.info("Backup validation passed")
        else:
            logger.warning(f"Backup validation failed: {issues}")

        return result

    def restore_documents(
        self,
        collection: str,
        documents: List[Dict[str, Any]],
        dry_run: bool = False,
        merge: bool = False
    ) -> Dict[str, Any]:
        """
        Restore documents to a collection

        Args:
            collection: Collection name
            documents: List of documents to restore
            dry_run: If True, don't actually write to database
            merge: If True, merge with existing documents; if False, replace

        Returns:
            Restore result summary
        """
        logger.info(
            f"Restoring {len(documents)} documents to '{collection}' "
            f"(dry_run={dry_run}, merge={merge})"
        )

        if dry_run:
            logger.info("DRY RUN: No documents will be written to database")
            return {
                "status": "dry_run",
                "collection": collection,
                "document_count": len(documents),
                "created": 0,
                "updated": 0,
                "errors": 0
            }

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

                    # Document exists, update it
                    self.client.update_document(
                        collection=collection,
                        document_id=doc_id,
                        data=doc,
                        merge=merge
                    )
                    updated += 1

                except ZeroDBError:
                    # Document doesn't exist, create it
                    self.client.create_document(
                        collection=collection,
                        data=doc,
                        document_id=doc_id
                    )
                    created += 1

                # Log progress every 100 documents
                if i % 100 == 0:
                    logger.info(
                        f"Progress: {i}/{len(documents)} documents processed "
                        f"(created: {created}, updated: {updated}, errors: {errors})"
                    )

            except Exception as e:
                errors += 1
                error_msg = f"Error restoring document {i} (ID: {doc.get('id')}): {e}"
                logger.error(error_msg)
                error_details.append(error_msg)

        result = {
            "status": "completed" if errors == 0 else "completed_with_errors",
            "collection": collection,
            "document_count": len(documents),
            "created": created,
            "updated": updated,
            "errors": errors,
            "error_details": error_details[:10]  # Limit to first 10 errors
        }

        logger.info(
            f"Restore completed: {created} created, {updated} updated, "
            f"{errors} errors"
        )

        return result

    def restore_backup(
        self,
        backup_id: str,
        dry_run: bool = False,
        validate_only: bool = False,
        merge: bool = False
    ) -> Dict[str, Any]:
        """
        Perform full restore workflow for a backup

        Args:
            backup_id: Backup identifier
            dry_run: If True, don't actually write to database
            validate_only: If True, only validate backup without restoring
            merge: If True, merge with existing documents; if False, replace

        Returns:
            Restore result summary
        """
        logger.info(f"Starting restore for backup '{backup_id}'")

        try:
            # Get backup metadata
            metadata = self.get_backup_metadata(backup_id)

            # Download backup file
            file_path = self.download_backup(metadata["file_name"])

            # Decompress backup
            backup_data = self.decompress_backup(file_path)

            # Validate backup
            validation = self.validate_backup(backup_data)

            if not validation["valid"]:
                logger.error(f"Backup validation failed: {validation['issues']}")
                return {
                    "status": "failed",
                    "backup_id": backup_id,
                    "error": "Backup validation failed",
                    "validation": validation
                }

            if validate_only:
                logger.info("Validation complete (validate-only mode)")
                return {
                    "status": "validated",
                    "backup_id": backup_id,
                    "validation": validation
                }

            # Restore documents
            restore_result = self.restore_documents(
                collection=backup_data["collection"],
                documents=backup_data["documents"],
                dry_run=dry_run,
                merge=merge
            )

            # Cleanup temp file
            file_path.unlink()

            result = {
                "status": restore_result["status"],
                "backup_id": backup_id,
                "collection": backup_data["collection"],
                "backup_type": backup_data["backup_type"],
                "backup_timestamp": backup_data["timestamp"],
                "validation": validation,
                "restore": restore_result
            }

            logger.info(f"Restore completed for backup '{backup_id}'")
            return result

        except Exception as e:
            logger.error(f"Restore failed for backup '{backup_id}': {e}")
            raise


def print_backup_list(backups: List[Dict[str, Any]]):
    """Print formatted list of backups"""
    if not backups:
        print("\nNo backups found.")
        return

    print("\n" + "=" * 100)
    print("AVAILABLE BACKUPS")
    print("=" * 100)
    print(f"\n{'Backup ID':<40} {'Collection':<15} {'Type':<12} {'Date':<20} {'Docs':<8} {'Size':<12}")
    print("-" * 100)

    for backup in backups:
        backup_id = backup.get("backup_id", "N/A")
        collection = backup.get("collection", "N/A")
        backup_type = backup.get("backup_type", "N/A")
        completed_at = backup.get("completed_at", "N/A")
        doc_count = backup.get("document_count", 0)
        file_size = backup.get("file_size", 0)

        # Format timestamp
        try:
            dt = datetime.fromisoformat(completed_at)
            date_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            date_str = completed_at

        # Format file size
        if file_size > 1024 * 1024:
            size_str = f"{file_size / 1024 / 1024:.1f} MB"
        elif file_size > 1024:
            size_str = f"{file_size / 1024:.1f} KB"
        else:
            size_str = f"{file_size} B"

        print(f"{backup_id:<40} {collection:<15} {backup_type:<12} {date_str:<20} {doc_count:<8} {size_str:<12}")

    print()


def main():
    """Main entry point for restore script"""
    parser = argparse.ArgumentParser(
        description="ZeroDB Restore Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="List available backups"
    )

    parser.add_argument(
        "--backup-id",
        type=str,
        help="Backup ID to restore"
    )

    parser.add_argument(
        "--point-in-time",
        type=str,
        help="ISO timestamp for point-in-time recovery (e.g., '2025-01-09T12:00:00')"
    )

    parser.add_argument(
        "--collections",
        type=str,
        help="Comma-separated list of collections for point-in-time recovery"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform restore without actually writing to database"
    )

    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate backup without restoring"
    )

    parser.add_argument(
        "--merge",
        action="store_true",
        help="Merge with existing documents instead of replacing"
    )

    parser.add_argument(
        "--collection",
        type=str,
        help="Filter backups by collection (for --list)"
    )

    parser.add_argument(
        "--backup-type",
        type=str,
        choices=["full", "incremental"],
        help="Filter backups by type (for --list)"
    )

    args = parser.parse_args()

    restore_manager = RestoreManager()

    # List backups mode
    if args.list:
        backups = restore_manager.list_backups(
            collection=args.collection,
            backup_type=args.backup_type
        )
        print_backup_list(backups)
        sys.exit(0)

    # Point-in-time recovery mode
    if args.point_in_time:
        if not args.collections:
            print("Error: --collections required for point-in-time recovery")
            sys.exit(1)

        collections = [c.strip() for c in args.collections.split(",")]
        results = []

        for collection in collections:
            backup = restore_manager.find_point_in_time_backup(
                collection=collection,
                timestamp=args.point_in_time
            )

            if not backup:
                print(f"Error: No backup found for '{collection}' before {args.point_in_time}")
                continue

            print(f"\nRestoring '{collection}' from backup: {backup['backup_id']}")

            result = restore_manager.restore_backup(
                backup_id=backup["backup_id"],
                dry_run=args.dry_run,
                validate_only=args.validate_only,
                merge=args.merge
            )
            results.append(result)

        # Print summary
        print("\n" + "=" * 80)
        print("POINT-IN-TIME RESTORE SUMMARY")
        print("=" * 80)

        for result in results:
            print(f"\nCollection: {result['collection']}")
            print(f"  Status: {result['status']}")
            print(f"  Backup ID: {result['backup_id']}")
            if 'restore' in result:
                print(f"  Created: {result['restore']['created']}")
                print(f"  Updated: {result['restore']['updated']}")
                print(f"  Errors: {result['restore']['errors']}")

        sys.exit(0)

    # Restore specific backup mode
    if args.backup_id:
        result = restore_manager.restore_backup(
            backup_id=args.backup_id,
            dry_run=args.dry_run,
            validate_only=args.validate_only,
            merge=args.merge
        )

        # Print summary
        print("\n" + "=" * 80)
        print("RESTORE SUMMARY")
        print("=" * 80)
        print(f"\nBackup ID: {result['backup_id']}")
        print(f"Collection: {result['collection']}")
        print(f"Backup Type: {result['backup_type']}")
        print(f"Backup Timestamp: {result['backup_timestamp']}")
        print(f"Status: {result['status']}")

        if 'validation' in result:
            print(f"\nValidation: {'PASSED' if result['validation']['valid'] else 'FAILED'}")
            if result['validation']['issues']:
                print("  Issues:")
                for issue in result['validation']['issues']:
                    print(f"    - {issue}")

        if 'restore' in result and result['status'] != 'validated':
            print(f"\nRestore Results:")
            print(f"  Documents: {result['restore']['document_count']}")
            print(f"  Created: {result['restore']['created']}")
            print(f"  Updated: {result['restore']['updated']}")
            print(f"  Errors: {result['restore']['errors']}")

            if result['restore']['error_details']:
                print("\n  Error Details (first 10):")
                for error in result['restore']['error_details']:
                    print(f"    - {error}")

        if args.dry_run:
            print("\nNote: DRY RUN - No changes were made to the database")

        sys.exit(0)

    # No mode specified
    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
