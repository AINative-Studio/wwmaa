#!/usr/bin/env python3
"""
BeeHiiv Initial Sync Script

Performs a full synchronization of all published posts from BeeHiiv to ZeroDB.

Usage:
    python backend/scripts/sync_beehiiv_posts.py [--limit N] [--dry-run]

Options:
    --limit N: Limit number of posts to sync (for testing)
    --dry-run: Show what would be synced without actually syncing

Environment Variables Required:
    BEEHIIV_API_KEY: BeeHiiv API key
    BEEHIIV_PUBLICATION_ID: BeeHiiv publication ID
    BEEHIIV_WEBHOOK_SECRET: BeeHiiv webhook secret (optional)

Example:
    # Sync all posts
    python backend/scripts/sync_beehiiv_posts.py

    # Sync first 10 posts (testing)
    python backend/scripts/sync_beehiiv_posts.py --limit 10

    # Dry run (no actual sync)
    python backend/scripts/sync_beehiiv_posts.py --dry-run
"""

import sys
import argparse
import logging
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir.parent))

from backend.services.blog_sync_service import get_blog_sync_service, BlogSyncError
from backend.config import settings


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def validate_environment():
    """
    Validate required environment variables are set

    Raises:
        ValueError: If required variables are missing
    """
    missing = []

    if not settings.BEEHIIV_API_KEY:
        missing.append('BEEHIIV_API_KEY')

    if not settings.BEEHIIV_PUBLICATION_ID:
        missing.append('BEEHIIV_PUBLICATION_ID')

    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            f"Please set these in your .env file or environment."
        )

    logger.info("Environment validation passed")
    logger.info(f"Publication ID: {settings.BEEHIIV_PUBLICATION_ID}")


def sync_posts(limit: int = None, dry_run: bool = False):
    """
    Sync posts from BeeHiiv

    Args:
        limit: Maximum number of posts to sync
        dry_run: If True, don't actually sync

    Returns:
        Number of posts synced
    """
    try:
        blog_sync_service = get_blog_sync_service()

        logger.info("="*70)
        logger.info("Starting BeeHiiv Post Synchronization")
        logger.info("="*70)

        if dry_run:
            logger.warning("DRY RUN MODE - No changes will be made")

        if limit:
            logger.info(f"Sync limit: {limit} posts")

        # Perform sync
        if dry_run:
            # In dry run, just fetch posts without syncing
            posts = blog_sync_service._fetch_all_posts_from_beehiiv(limit=limit)

            logger.info(f"\nWould sync {len(posts)} posts:")
            for i, post in enumerate(posts, 1):
                logger.info(
                    f"  {i}. {post.get('title', 'Untitled')} "
                    f"(ID: {post.get('id')}, Status: {post.get('status')})"
                )

            return 0

        else:
            # Actual sync
            articles = blog_sync_service.sync_all_posts(limit=limit)

            logger.info(f"\n{'='*70}")
            logger.info(f"Sync Complete!")
            logger.info(f"{'='*70}")
            logger.info(f"Successfully synced {len(articles)} blog posts")

            # Display summary
            if articles:
                logger.info("\nSynced Posts:")
                for i, article in enumerate(articles, 1):
                    logger.info(
                        f"  {i}. {article.title} "
                        f"(Slug: {article.slug}, Views: {article.view_count})"
                    )

            return len(articles)

    except BlogSyncError as e:
        logger.error(f"Blog sync error: {e}")
        return -1

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return -1


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Sync blog posts from BeeHiiv to ZeroDB',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of posts to sync (for testing)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be synced without actually syncing'
    )

    args = parser.parse_args()

    try:
        # Validate environment
        validate_environment()

        # Sync posts
        count = sync_posts(limit=args.limit, dry_run=args.dry_run)

        if count >= 0:
            logger.info("\n✓ Sync completed successfully")
            sys.exit(0)
        else:
            logger.error("\n✗ Sync failed")
            sys.exit(1)

    except ValueError as e:
        logger.error(f"\n✗ Configuration error: {e}")
        sys.exit(1)

    except KeyboardInterrupt:
        logger.warning("\n✗ Sync cancelled by user")
        sys.exit(130)

    except Exception as e:
        logger.error(f"\n✗ Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
