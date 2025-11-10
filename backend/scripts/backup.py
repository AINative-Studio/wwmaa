#!/usr/bin/env python3
"""
Unified ZeroDB Backup & Restore CLI

This script provides a unified command-line interface for all backup and restore operations.
It replaces the separate backup_zerodb.py and restore_zerodb.py scripts with a single,
comprehensive tool.

Features:
- Create full and incremental backups
- Restore from backups with validation
- List available backups
- Cleanup old backups based on age
- Support for all 14 ZeroDB collections
- Comprehensive logging and error handling

Commands:
- --backup: Create backups (full or incremental)
- --restore <backup_id>: Restore from a specific backup
- --list: List all available backups
- --cleanup --days <N>: Delete backups older than N days

Usage Examples:
    # Backup all collections (full backup)
    python backup.py --backup

    # Backup all collections (incremental)
    python backup.py --backup --incremental

    # Backup specific collections
    python backup.py --backup --collections users,profiles,events

    # List all available backups
    python backup.py --list

    # List backups for specific collection
    python backup.py --list --collection users

    # Restore specific backup
    python backup.py --restore users_full_20250109_120000

    # Restore with validation only
    python backup.py --restore users_full_20250109_120000 --validate-only

    # Cleanup backups older than 30 days
    python backup.py --cleanup --days 30

    # Dry run (no actual changes)
    python backup.py --backup --dry-run
    python backup.py --restore users_full_20250109_120000 --dry-run

Author: WWMAA Development Team
Version: 1.0.0
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Add backend to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.backup_service import BackupService, BackupError, RestoreError
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/tmp/zerodb_backup_cli.log')
    ]
)
logger = logging.getLogger(__name__)


def print_header(title: str):
    """Print formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_backup_list(backups: List[dict], show_details: bool = False):
    """
    Print formatted list of backups

    Args:
        backups: List of backup metadata dictionaries
        show_details: If True, show additional details
    """
    if not backups:
        print("No backups found.")
        return

    print(f"{'Backup ID':<45} {'Collection':<18} {'Type':<12} {'Date':<20} {'Docs':<8} {'Size':<12}")
    print("-" * 120)

    for backup in backups:
        backup_id = backup.get("backup_id", "N/A")[:44]
        collection = backup.get("collection", "N/A")[:17]
        backup_type = backup.get("backup_type", "N/A")[:11]
        completed_at = backup.get("completed_at", "N/A")
        doc_count = backup.get("document_count", 0)
        file_size = backup.get("file_size", 0)

        # Format timestamp
        try:
            dt = datetime.fromisoformat(completed_at)
            date_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            date_str = completed_at[:19]

        # Format file size
        if file_size > 1024 * 1024:
            size_str = f"{file_size / 1024 / 1024:.2f} MB"
        elif file_size > 1024:
            size_str = f"{file_size / 1024:.2f} KB"
        else:
            size_str = f"{file_size} B"

        print(f"{backup_id:<45} {collection:<18} {backup_type:<12} {date_str:<20} {doc_count:<8} {size_str:<12}")

        if show_details:
            print(f"  File: {backup.get('file_name', 'N/A')}")
            print(f"  Path: {backup.get('object_path', 'N/A')}")
            print()


def handle_backup(args):
    """
    Handle backup operation

    Args:
        args: Parsed command-line arguments
    """
    print_header("ZeroDB BACKUP")

    # Determine collections to backup
    if args.collections:
        collections = [c.strip() for c in args.collections.split(",")]
        print(f"Collections: {', '.join(collections)}")
    else:
        collections = None
        print("Collections: ALL (14 collections)")

    print(f"Backup Type: {'Incremental' if args.incremental else 'Full'}")
    print(f"Dry Run: {'Yes' if args.dry_run else 'No'}")
    print()

    if args.dry_run:
        print("DRY RUN MODE: No backups will be created or uploaded\n")

    try:
        backup_service = BackupService()

        if collections:
            # Backup specific collections
            results = []
            successful = []
            failed = []

            for collection in collections:
                try:
                    if not args.dry_run:
                        result = backup_service.backup_collection(
                            collection=collection,
                            incremental=args.incremental
                        )
                        results.append(result)
                        successful.append(collection)
                        print(f"✓ {collection}: {result['document_count']} docs, {result['file_size']:,} bytes")
                    else:
                        print(f"✓ {collection}: (dry run)")
                        successful.append(collection)

                except BackupError as e:
                    logger.error(f"Failed to backup '{collection}': {e}")
                    failed.append(collection)
                    print(f"✗ {collection}: FAILED - {e}")

            # Print summary
            print_header("BACKUP SUMMARY")
            print(f"Total Collections: {len(collections)}")
            print(f"Successful: {len(successful)}")
            print(f"Failed: {len(failed)}")

            if failed:
                print(f"\nFailed Collections: {', '.join(failed)}")
                sys.exit(1)

        else:
            # Backup all collections
            if not args.dry_run:
                result = backup_service.backup_all_collections(
                    incremental=args.incremental
                )

                # Print summary
                print_header("BACKUP SUMMARY")
                print(f"Status: {result['status'].upper()}")
                print(f"Total Collections: {result['total_collections']}")
                print(f"Successful: {result['successful']}")
                print(f"Failed: {result['failed']}")
                print(f"Duration: {result['duration_seconds']:.2f} seconds")

                if result['failed_collections']:
                    print(f"\nFailed Collections:")
                    for failure in result['failed_collections']:
                        print(f"  - {failure['collection']}: {failure['error']}")
                    sys.exit(1)

                print(f"\nSuccessful Collections:")
                for coll in result['successful_collections']:
                    print(f"  ✓ {coll}")

            else:
                print("DRY RUN: Would backup all 14 collections")
                print_header("BACKUP SUMMARY")
                print("No backups created (dry run mode)")

        print("\n✓ Backup operation completed successfully")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Backup operation failed: {e}")
        print(f"\n✗ ERROR: {e}")
        sys.exit(1)


def handle_restore(args):
    """
    Handle restore operation

    Args:
        args: Parsed command-line arguments
    """
    print_header("ZeroDB RESTORE")

    backup_id = args.restore
    print(f"Backup ID: {backup_id}")
    print(f"Merge Mode: {'Yes (merge with existing)' if args.merge else 'No (replace)'}")
    print(f"Validate Only: {'Yes' if args.validate_only else 'No'}")
    print(f"Dry Run: {'Yes' if args.dry_run else 'No'}")
    print()

    if args.dry_run:
        print("DRY RUN MODE: No documents will be restored to database\n")

    try:
        backup_service = BackupService()

        # Parse backup_id to extract collection name
        # Format: collection_type_timestamp
        parts = backup_id.split("_")
        if len(parts) < 3:
            raise RestoreError(
                f"Invalid backup ID format: '{backup_id}'. "
                f"Expected format: collection_type_timestamp"
            )

        collection = parts[0]
        print(f"Collection: {collection}")
        print()

        # Perform restore
        result = backup_service.restore_collection(
            collection=collection,
            backup_id=backup_id,
            merge=args.merge,
            validate_only=args.validate_only
        )

        # Print results
        print_header("RESTORE SUMMARY")
        print(f"Status: {result['status'].upper()}")
        print(f"Backup ID: {result['backup_id']}")
        print(f"Collection: {result['collection']}")

        if 'backup_type' in result:
            print(f"Backup Type: {result['backup_type']}")
        if 'backup_timestamp' in result:
            print(f"Backup Timestamp: {result['backup_timestamp']}")

        if result['status'] == 'validated':
            print(f"\n✓ Backup validation PASSED")
            print(f"  Document Count: {result['document_count']}")
        elif not args.validate_only:
            print(f"\nDocument Count: {result['document_count']}")
            print(f"Created: {result['created']}")
            print(f"Updated: {result['updated']}")
            print(f"Errors: {result['errors']}")

            if result['errors'] > 0:
                print(f"\nError Details (first 10):")
                for error in result.get('error_details', []):
                    print(f"  - {error}")

        if args.dry_run:
            print("\nNote: DRY RUN - No changes were made to the database")

        print("\n✓ Restore operation completed successfully")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Restore operation failed: {e}")
        print(f"\n✗ ERROR: {e}")
        sys.exit(1)


def handle_list(args):
    """
    Handle list backups operation

    Args:
        args: Parsed command-line arguments
    """
    print_header("AVAILABLE BACKUPS")

    try:
        backup_service = BackupService()

        backups = backup_service.list_backups(
            collection=args.collection,
            backup_type=args.backup_type,
            limit=args.limit
        )

        if not backups:
            print("No backups found matching the criteria.")
            sys.exit(0)

        # Group by collection if not filtering
        if not args.collection:
            collections = {}
            for backup in backups:
                coll = backup.get("collection")
                if coll not in collections:
                    collections[coll] = []
                collections[coll].append(backup)

            print(f"Total Backups: {len(backups)}")
            print(f"Collections: {len(collections)}\n")

            for coll, coll_backups in sorted(collections.items()):
                print(f"\n{coll.upper()} ({len(coll_backups)} backups):")
                print("-" * 80)
                print_backup_list(coll_backups, show_details=args.verbose)

        else:
            print(f"Collection: {args.collection}")
            print(f"Total Backups: {len(backups)}\n")
            print_backup_list(backups, show_details=args.verbose)

        sys.exit(0)

    except Exception as e:
        logger.error(f"List operation failed: {e}")
        print(f"\n✗ ERROR: {e}")
        sys.exit(1)


def handle_cleanup(args):
    """
    Handle cleanup old backups operation

    Args:
        args: Parsed command-line arguments
    """
    print_header("CLEANUP OLD BACKUPS")

    if not args.days:
        print("ERROR: --days parameter is required for cleanup operation")
        sys.exit(1)

    print(f"Cleanup Policy: Delete backups older than {args.days} days")
    print(f"Dry Run: {'Yes' if args.dry_run else 'No'}")
    print()

    if args.dry_run:
        print("DRY RUN MODE: No backups will be deleted\n")

    try:
        backup_service = BackupService()

        if not args.dry_run:
            result = backup_service.cleanup_old_backups(days=args.days)

            print_header("CLEANUP SUMMARY")
            print(f"Status: {result['status'].upper()}")
            print(f"Cutoff Date: {result['cutoff_date']}")
            print(f"Total Found: {result['total_found']}")
            print(f"Deleted: {result['deleted']}")
            print(f"Errors: {result['errors']}")

            if result['deleted'] > 0:
                print(f"\nDeleted Backup IDs:")
                for backup_id in result['deleted_ids'][:20]:  # Show first 20
                    print(f"  - {backup_id}")

                if len(result['deleted_ids']) > 20:
                    print(f"  ... and {len(result['deleted_ids']) - 20} more")

            if result.get('error_details'):
                print(f"\nErrors:")
                for error in result['error_details']:
                    print(f"  - {error}")

            print("\n✓ Cleanup operation completed successfully")
        else:
            print("DRY RUN: Would cleanup old backups")
            print("Run without --dry-run to perform actual cleanup")

        sys.exit(0)

    except Exception as e:
        logger.error(f"Cleanup operation failed: {e}")
        print(f"\n✗ ERROR: {e}")
        sys.exit(1)


def main():
    """Main entry point for backup CLI"""
    parser = argparse.ArgumentParser(
        description="ZeroDB Backup & Restore CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # Operation modes (mutually exclusive)
    operations = parser.add_mutually_exclusive_group(required=True)

    operations.add_argument(
        "--backup",
        action="store_true",
        help="Create backups of collections"
    )

    operations.add_argument(
        "--restore",
        type=str,
        metavar="BACKUP_ID",
        help="Restore from specific backup (e.g., users_full_20250109_120000)"
    )

    operations.add_argument(
        "--list",
        action="store_true",
        help="List available backups"
    )

    operations.add_argument(
        "--cleanup",
        action="store_true",
        help="Delete old backups (requires --days)"
    )

    # Backup options
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

    # Restore options
    parser.add_argument(
        "--merge",
        action="store_true",
        help="Merge with existing documents instead of replacing (restore only)"
    )

    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate backup without restoring (restore only)"
    )

    # List options
    parser.add_argument(
        "--collection",
        type=str,
        help="Filter backups by collection name (list only)"
    )

    parser.add_argument(
        "--backup-type",
        type=str,
        choices=["full", "incremental"],
        help="Filter backups by type (list only)"
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of backups to list (default: 50)"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed information (list only)"
    )

    # Cleanup options
    parser.add_argument(
        "--days",
        type=int,
        help="Delete backups older than N days (cleanup only)"
    )

    # General options
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate operation without making changes"
    )

    # Parse arguments
    args = parser.parse_args()

    # Route to appropriate handler
    try:
        if args.backup:
            handle_backup(args)
        elif args.restore:
            handle_restore(args)
        elif args.list:
            handle_list(args)
        elif args.cleanup:
            handle_cleanup(args)

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(130)

    except Exception as e:
        logger.exception("Unexpected error occurred")
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
