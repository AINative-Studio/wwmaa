"""
Dunning Scheduler Script

Automated scheduler for processing dunning reminders at scheduled intervals.
Uses APScheduler to check for due dunning reminders and process them.

This script should run as a background process alongside the main FastAPI application.
It queries the dunning_records collection for records that need processing and
delegates to the DunningService for email sending and status updates.

Usage:
    python -m backend.scripts.dunning_scheduler

Environment Variables Required:
    - All standard backend environment variables from .env file
    - Specifically: ZERODB_API_KEY, POSTMARK_API_KEY, STRIPE_SECRET_KEY

Schedule:
    - Runs every 2 hours to check for due dunning reminders
    - Processes all reminders that are past their scheduled time
    - Logs all processing results for monitoring

Safety Features:
    - Idempotent processing (won't resend emails for same stage)
    - Error handling and retry logic
    - Comprehensive logging
    - Graceful shutdown on SIGTERM/SIGINT
"""

import logging
import signal
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

from backend.config import settings
from backend.services.dunning_service import (
    get_dunning_service,
    DunningService,
    DunningStage,
    DunningServiceError
)
from backend.services.zerodb_service import get_zerodb_client, ZeroDBError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/var/log/wwmaa/dunning_scheduler.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize services
dunning_service: DunningService = None
zerodb_client = None


def initialize_services():
    """
    Initialize dunning and database services

    This is called once at startup to create service instances.
    """
    global dunning_service, zerodb_client

    try:
        dunning_service = get_dunning_service()
        zerodb_client = get_zerodb_client()
        logger.info("Dunning scheduler services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        sys.exit(1)


def get_due_dunning_records() -> List[Dict[str, Any]]:
    """
    Query ZeroDB for dunning records that need processing

    A dunning record is due if:
    - It's in one of the reminder stages (not canceled)
    - The next reminder date has passed
    - It hasn't already been processed for this stage

    Returns:
        List of dunning records that need processing
    """
    try:
        # Query dunning_records for records in past_due subscriptions
        # that haven't reached the canceled stage yet
        results = zerodb_client.query(
            collection='dunning_records',
            query={
                'current_stage': {
                    '$in': [
                        DunningStage.PAYMENT_FAILED.value,
                        DunningStage.FIRST_REMINDER.value,
                        DunningStage.SECOND_REMINDER.value,
                        DunningStage.FINAL_WARNING.value
                    ]
                }
            },
            limit=100  # Process up to 100 records per run
        )

        due_records = []
        now = datetime.utcnow()

        for record in results:
            created_at = datetime.fromisoformat(record.get('created_at'))
            current_stage = record.get('current_stage')

            # Calculate days since dunning started
            days_past_due = (now - created_at).days

            # Check if this record is due for the next stage
            stage_enum = DunningStage(current_stage)
            next_stage = dunning_service._get_next_stage(stage_enum)

            if next_stage:
                days_required = DunningService.DUNNING_SCHEDULE[next_stage]

                if days_past_due >= days_required:
                    # This record is due for the next stage
                    due_records.append({
                        'record': record,
                        'next_stage': next_stage,
                        'days_past_due': days_past_due
                    })
                    logger.info(
                        f"Dunning record {record.get('id')} is due for "
                        f"{next_stage.value} (days past due: {days_past_due})"
                    )

        logger.info(f"Found {len(due_records)} dunning records due for processing")
        return due_records

    except ZeroDBError as e:
        logger.error(f"Database error querying dunning records: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error querying dunning records: {e}")
        return []


async def process_dunning_reminder(
    dunning_record_id: str,
    next_stage: DunningStage
) -> Dict[str, Any]:
    """
    Process a single dunning reminder

    Args:
        dunning_record_id: ID of the dunning record
        next_stage: The next dunning stage to process

    Returns:
        Processing result
    """
    try:
        result = await dunning_service.process_dunning_reminder(
            dunning_record_id=dunning_record_id,
            stage=next_stage
        )

        logger.info(
            f"Successfully processed dunning reminder {dunning_record_id} "
            f"for stage {next_stage.value}"
        )

        return result

    except DunningServiceError as e:
        logger.error(
            f"Dunning service error processing reminder {dunning_record_id}: {e}"
        )
        return {
            'success': False,
            'error': str(e),
            'dunning_record_id': dunning_record_id,
            'stage': next_stage.value
        }
    except Exception as e:
        logger.error(
            f"Unexpected error processing reminder {dunning_record_id}: {e}"
        )
        return {
            'success': False,
            'error': str(e),
            'dunning_record_id': dunning_record_id,
            'stage': next_stage.value
        }


async def process_all_due_dunning_reminders():
    """
    Main processing function that runs on schedule

    This function:
    1. Queries for all due dunning records
    2. Processes each record sequentially
    3. Logs results for monitoring
    4. Reports summary statistics
    """
    logger.info("Starting dunning reminder processing run...")
    start_time = datetime.utcnow()

    try:
        due_records = get_due_dunning_records()

        if not due_records:
            logger.info("No dunning reminders due for processing")
            return

        results = {
            'total': len(due_records),
            'succeeded': 0,
            'failed': 0,
            'skipped': 0
        }

        for item in due_records:
            record = item['record']
            next_stage = item['next_stage']
            dunning_record_id = record.get('id')

            try:
                result = await process_dunning_reminder(
                    dunning_record_id=str(dunning_record_id),
                    next_stage=next_stage
                )

                if result.get('success'):
                    results['succeeded'] += 1
                elif result.get('skipped'):
                    results['skipped'] += 1
                else:
                    results['failed'] += 1

            except Exception as e:
                logger.error(
                    f"Failed to process dunning record {dunning_record_id}: {e}"
                )
                results['failed'] += 1

        # Log summary
        elapsed_time = (datetime.utcnow() - start_time).total_seconds()
        logger.info(
            f"Dunning reminder processing run completed in {elapsed_time:.2f}s: "
            f"Total={results['total']}, "
            f"Succeeded={results['succeeded']}, "
            f"Failed={results['failed']}, "
            f"Skipped={results['skipped']}"
        )

    except Exception as e:
        logger.error(f"Error in dunning reminder processing run: {e}")


def scheduled_job():
    """
    Wrapper function for APScheduler

    APScheduler requires a synchronous function, so we wrap the async
    processing function here.
    """
    import asyncio

    logger.info("Dunning scheduler job triggered")

    try:
        # Create event loop if needed
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Run the async processing function
        loop.run_until_complete(process_all_due_dunning_reminders())

    except Exception as e:
        logger.error(f"Error in scheduled job: {e}")


def shutdown_handler(signum, frame):
    """
    Graceful shutdown handler for SIGTERM and SIGINT

    Args:
        signum: Signal number
        frame: Current stack frame
    """
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    scheduler.shutdown(wait=True)
    logger.info("Dunning scheduler stopped")
    sys.exit(0)


# Create scheduler instance
scheduler = BlockingScheduler(
    timezone='UTC',
    job_defaults={
        'coalesce': True,  # Combine missed runs into one
        'max_instances': 1,  # Only one instance at a time
        'misfire_grace_time': 300  # Allow 5 minutes grace for missed runs
    }
)


def main():
    """
    Main entry point for dunning scheduler

    Sets up signal handlers, initializes services, configures scheduler,
    and starts the blocking scheduler loop.
    """
    logger.info("Starting WWMAA Dunning Scheduler...")
    logger.info(f"Environment: {settings.PYTHON_ENV}")
    logger.info(f"Grace period: {dunning_service.grace_period_days if dunning_service else 14} days")

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)

    # Initialize services
    initialize_services()

    # Add scheduled job - runs every 2 hours
    scheduler.add_job(
        func=scheduled_job,
        trigger=IntervalTrigger(hours=2),
        id='dunning_reminder_processor',
        name='Process Due Dunning Reminders',
        replace_existing=True
    )

    logger.info("Dunning scheduler configured to run every 2 hours")

    # Run immediately on startup (optional - can be disabled)
    logger.info("Running initial dunning check...")
    scheduled_job()

    # Start scheduler (blocking)
    try:
        logger.info("Dunning scheduler started successfully")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Dunning scheduler stopped by user")
    except Exception as e:
        logger.error(f"Dunning scheduler crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
