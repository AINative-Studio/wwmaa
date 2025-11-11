#!/usr/bin/env python3
"""
Content Indexing Background Scheduler

Automated scheduler for running content indexing at regular intervals.
Uses APScheduler for reliable scheduling with graceful shutdown handling.

Usage:
    python backend/scripts/index_scheduler.py

Environment Variables:
    INDEXING_SCHEDULE_INTERVAL_HOURS: Hours between indexing runs (default: 6)
    PYTHON_ENV: Environment (development/staging/production)

Features:
    - Automatic incremental indexing every N hours
    - Graceful shutdown on SIGTERM/SIGINT
    - Comprehensive logging
    - Error handling and recovery
    - Monitoring and status tracking
"""

import logging
import signal
import sys
import time
from datetime import datetime
from typing import Optional

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
except ImportError:
    print("APScheduler is required. Install it with: pip install APScheduler")
    sys.exit(1)

# Add parent directory to path for imports
sys.path.insert(0, "/Users/aideveloper/Desktop/wwmaa")

from backend.config import settings
from backend.services.indexing_service import (
    get_indexing_service,
    ContentType,
    IndexingStatus
)

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.is_production else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/Users/aideveloper/Desktop/wwmaa/backend/logs/indexing_scheduler.log')
    ]
)

logger = logging.getLogger(__name__)


class IndexingScheduler:
    """
    Background scheduler for automated content indexing.

    Runs incremental indexing at configured intervals and handles
    graceful shutdown on termination signals.
    """

    def __init__(self):
        """Initialize the indexing scheduler."""
        self.indexing_service = get_indexing_service()
        self.scheduler = BackgroundScheduler()
        self.is_running = False

        # Get interval from settings
        self.interval_hours = settings.INDEXING_SCHEDULE_INTERVAL_HOURS

        logger.info(
            f"IndexingScheduler initialized "
            f"(interval={self.interval_hours}h, env={settings.PYTHON_ENV})"
        )

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        # Add event listeners
        self.scheduler.add_listener(
            self._job_executed_listener,
            EVENT_JOB_EXECUTED
        )
        self.scheduler.add_listener(
            self._job_error_listener,
            EVENT_JOB_ERROR
        )

    def _signal_handler(self, signum, frame):
        """
        Handle termination signals for graceful shutdown.

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        signal_name = signal.Signals(signum).name
        logger.info(f"Received {signal_name}, initiating graceful shutdown...")
        self.stop()
        sys.exit(0)

    def _job_executed_listener(self, event):
        """
        Listener for successful job execution.

        Args:
            event: APScheduler job execution event
        """
        logger.info(f"Indexing job completed successfully: {event.job_id}")

    def _job_error_listener(self, event):
        """
        Listener for job errors.

        Args:
            event: APScheduler job error event
        """
        logger.error(
            f"Indexing job failed: {event.job_id}, "
            f"exception: {event.exception}"
        )

    def run_indexing(self):
        """
        Execute incremental indexing for all content types.

        This is the main job function that gets scheduled.
        """
        logger.info("=" * 80)
        logger.info(f"Starting scheduled indexing run at {datetime.now()}")
        logger.info("=" * 80)

        try:
            # Get current status
            status = self.indexing_service.get_status()

            # Don't start a new run if already running
            if status["status"] == IndexingStatus.RUNNING.value:
                logger.warning("Indexing already in progress, skipping this run")
                return

            # Index each content type incrementally
            content_types = [
                ContentType.EVENTS,
                ContentType.ARTICLES,
                ContentType.TRAINING_VIDEOS,
                ContentType.MEMBER_PROFILES
            ]

            total_indexed = 0
            total_skipped = 0
            total_errors = 0

            for content_type in content_types:
                logger.info(f"Indexing {content_type.value}...")

                try:
                    result = self.indexing_service.index_collection(
                        content_type=content_type,
                        incremental=True
                    )

                    indexed = result.get("indexed", 0)
                    skipped = result.get("skipped", 0)
                    errors = result.get("errors", 0)

                    total_indexed += indexed
                    total_skipped += skipped
                    total_errors += errors

                    logger.info(
                        f"  {content_type.value}: "
                        f"{indexed} indexed, {skipped} skipped, {errors} errors"
                    )

                except Exception as e:
                    logger.error(f"Error indexing {content_type.value}: {e}")
                    total_errors += 1

            # Log summary
            logger.info("-" * 80)
            logger.info(
                f"Indexing run completed: "
                f"{total_indexed} indexed, {total_skipped} skipped, {total_errors} errors"
            )
            logger.info("=" * 80)

        except Exception as e:
            logger.error(f"Error in scheduled indexing run: {e}", exc_info=True)

    def start(self):
        """
        Start the scheduler and run initial indexing.

        Runs an immediate indexing job and then schedules recurring jobs.
        """
        if self.is_running:
            logger.warning("Scheduler is already running")
            return

        logger.info("Starting indexing scheduler...")

        try:
            # Run initial indexing immediately (optional)
            if settings.is_development:
                logger.info("Running initial indexing job...")
                self.run_indexing()

            # Schedule recurring indexing job
            self.scheduler.add_job(
                func=self.run_indexing,
                trigger=IntervalTrigger(hours=self.interval_hours),
                id='incremental_indexing',
                name='Incremental Content Indexing',
                replace_existing=True,
                max_instances=1  # Prevent overlapping runs
            )

            # Start the scheduler
            self.scheduler.start()
            self.is_running = True

            logger.info(
                f"Scheduler started successfully. "
                f"Next run in {self.interval_hours} hours"
            )

            # Keep the script running
            try:
                while self.is_running:
                    time.sleep(60)  # Wake up every minute to check status
            except (KeyboardInterrupt, SystemExit):
                logger.info("Received shutdown signal")
                self.stop()

        except Exception as e:
            logger.error(f"Error starting scheduler: {e}", exc_info=True)
            self.stop()
            sys.exit(1)

    def stop(self):
        """Stop the scheduler gracefully."""
        if not self.is_running:
            logger.info("Scheduler is not running")
            return

        logger.info("Stopping indexing scheduler...")

        try:
            # Shutdown the scheduler
            if self.scheduler.running:
                self.scheduler.shutdown(wait=True)

            self.is_running = False
            logger.info("Scheduler stopped successfully")

        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")

    def get_next_run_time(self) -> Optional[str]:
        """
        Get the next scheduled run time.

        Returns:
            ISO format timestamp of next run or None
        """
        try:
            job = self.scheduler.get_job('incremental_indexing')
            if job and job.next_run_time:
                return job.next_run_time.isoformat()
            return None
        except Exception as e:
            logger.error(f"Error getting next run time: {e}")
            return None

    def trigger_manual_run(self):
        """
        Trigger an immediate indexing run manually.

        This can be called via API or command line.
        """
        logger.info("Manual indexing run triggered")
        self.run_indexing()


def main():
    """
    Main entry point for the scheduler script.

    Creates and starts the IndexingScheduler.
    """
    logger.info("=" * 80)
    logger.info("WWMAA Content Indexing Scheduler")
    logger.info("=" * 80)
    logger.info(f"Environment: {settings.PYTHON_ENV}")
    logger.info(f"Interval: {settings.INDEXING_SCHEDULE_INTERVAL_HOURS} hours")
    logger.info(f"OpenAI Model: {settings.OPENAI_EMBEDDING_MODEL}")
    logger.info("=" * 80)

    # Create logs directory if it doesn't exist
    import os
    log_dir = '/Users/aideveloper/Desktop/wwmaa/backend/logs'
    os.makedirs(log_dir, exist_ok=True)

    # Create and start scheduler
    scheduler = IndexingScheduler()

    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        scheduler.stop()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
