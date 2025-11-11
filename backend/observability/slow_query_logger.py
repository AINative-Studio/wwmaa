"""
Slow Query Logger for ZeroDB Operations

Logs queries that exceed performance thresholds to file and sends alerts
for critically slow queries. Includes daily log rotation.
"""

import json
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional

from backend.config import get_settings

settings = get_settings()

# Configure slow query logger with rotation
SLOW_QUERY_LOG_DIR = Path("/var/log/wwmaa") if os.path.exists("/var/log") else Path("./logs")
SLOW_QUERY_LOG_DIR.mkdir(parents=True, exist_ok=True)
SLOW_QUERY_LOG_FILE = SLOW_QUERY_LOG_DIR / "slow_queries.log"

# Create slow query logger
slow_query_logger = logging.getLogger("slow_query")
slow_query_logger.setLevel(logging.INFO)
slow_query_logger.propagate = False

# Create rotating file handler (10MB per file, keep 5 backup files)
handler = RotatingFileHandler(
    SLOW_QUERY_LOG_FILE,
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=5,
)

# Create formatter for structured logging
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
handler.setFormatter(formatter)
slow_query_logger.addHandler(handler)

# Main application logger
logger = logging.getLogger(__name__)


class SlowQueryLogger:
    """
    Logger for slow database queries with configurable thresholds.

    Logs queries that exceed the threshold to a dedicated log file and
    sends alerts for critically slow queries (> 5 seconds).
    """

    def __init__(
        self,
        slow_threshold: float = 1.0,
        critical_threshold: float = 5.0,
    ):
        """
        Initialize slow query logger.

        Args:
            slow_threshold: Threshold in seconds for slow query logging (default: 1.0)
            critical_threshold: Threshold in seconds for critical alerts (default: 5.0)
        """
        self.slow_threshold = slow_threshold
        self.critical_threshold = critical_threshold

    def log_query(
        self,
        collection: str,
        operation: str,
        duration: float,
        query_details: Optional[Dict[str, Any]] = None,
        result_count: Optional[int] = None,
        error: Optional[str] = None,
    ):
        """
        Log a database query if it exceeds the slow threshold.

        Args:
            collection: Database collection name
            operation: Operation type (query, create, update, delete, vector_search)
            duration: Query duration in seconds
            query_details: Optional details about the query (filters, params, etc.)
            result_count: Number of results returned (if applicable)
            error: Error message if query failed
        """
        # Only log if duration exceeds slow threshold
        if duration < self.slow_threshold:
            return

        # Build log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "collection": collection,
            "operation": operation,
            "duration_seconds": round(duration, 3),
            "threshold_type": "critical" if duration >= self.critical_threshold else "slow",
        }

        if query_details:
            log_entry["query_details"] = self._sanitize_query_details(query_details)

        if result_count is not None:
            log_entry["result_count"] = result_count

        if error:
            log_entry["error"] = error

        # Log as JSON for easy parsing
        log_message = json.dumps(log_entry)

        # Determine log level based on severity
        if duration >= self.critical_threshold:
            slow_query_logger.critical(log_message)
            self._send_critical_alert(log_entry)
        else:
            slow_query_logger.warning(log_message)

        # Also log to main application logger
        logger.warning(
            f"Slow query detected: {operation} on {collection} "
            f"took {duration:.3f}s (threshold: {self.slow_threshold}s)"
        )

    def _sanitize_query_details(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize query details to remove sensitive information.

        Args:
            details: Query details dictionary

        Returns:
            Sanitized query details
        """
        sanitized = {}

        # List of keys that might contain sensitive data
        sensitive_keys = [
            "password",
            "token",
            "secret",
            "api_key",
            "credit_card",
            "ssn",
            "email",
        ]

        for key, value in details.items():
            # Check if key contains sensitive information
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_query_details(value)
            elif isinstance(value, list):
                # Limit array size in logs to prevent huge log entries
                if len(value) > 10:
                    sanitized[key] = f"[Array with {len(value)} items]"
                else:
                    sanitized[key] = value
            else:
                sanitized[key] = value

        return sanitized

    def _send_critical_alert(self, log_entry: Dict[str, Any]):
        """
        Send alert for critically slow queries (> 5 seconds).

        In production, this would integrate with Sentry, PagerDuty, or similar.
        For now, we just log it prominently.

        Args:
            log_entry: Log entry with query details
        """
        try:
            # In production, send to Sentry or alerting system
            # For now, log prominently
            logger.critical(
                f"CRITICAL SLOW QUERY ALERT: {log_entry['operation']} on "
                f"{log_entry['collection']} took {log_entry['duration_seconds']}s"
            )

            # If Sentry is configured, send event
            # This would be implemented when Sentry is added
            # import sentry_sdk
            # sentry_sdk.capture_message(
            #     f"Critical slow query: {log_entry['operation']}",
            #     level="error",
            #     extras=log_entry
            # )

        except Exception as e:
            logger.error(f"Failed to send critical slow query alert: {e}")

    def get_slow_query_stats(self) -> Dict[str, Any]:
        """
        Get statistics about slow queries from the log file.

        Returns:
            Dictionary with slow query statistics
        """
        try:
            if not SLOW_QUERY_LOG_FILE.exists():
                return {
                    "total_slow_queries": 0,
                    "critical_queries": 0,
                    "log_file": str(SLOW_QUERY_LOG_FILE),
                }

            total_slow = 0
            critical = 0

            with open(SLOW_QUERY_LOG_FILE, "r") as f:
                for line in f:
                    try:
                        # Parse JSON log entry
                        if "{" in line:
                            json_start = line.index("{")
                            entry = json.loads(line[json_start:])

                            total_slow += 1
                            if entry.get("threshold_type") == "critical":
                                critical += 1
                    except (json.JSONDecodeError, ValueError):
                        # Skip malformed lines
                        continue

            return {
                "total_slow_queries": total_slow,
                "critical_queries": critical,
                "log_file": str(SLOW_QUERY_LOG_FILE),
                "slow_threshold": self.slow_threshold,
                "critical_threshold": self.critical_threshold,
            }

        except Exception as e:
            logger.error(f"Failed to get slow query stats: {e}")
            return {"error": str(e)}


# Global slow query logger instance
_slow_query_logger: Optional[SlowQueryLogger] = None


def get_slow_query_logger(
    slow_threshold: float = 1.0,
    critical_threshold: float = 5.0,
) -> SlowQueryLogger:
    """
    Get or create the global slow query logger instance.

    Args:
        slow_threshold: Threshold in seconds for slow query logging (default: 1.0)
        critical_threshold: Threshold in seconds for critical alerts (default: 5.0)

    Returns:
        SlowQueryLogger instance
    """
    global _slow_query_logger

    if _slow_query_logger is None:
        _slow_query_logger = SlowQueryLogger(
            slow_threshold=slow_threshold,
            critical_threshold=critical_threshold,
        )

    return _slow_query_logger


def log_slow_query(
    collection: str,
    operation: str,
    duration: float,
    query_details: Optional[Dict[str, Any]] = None,
    result_count: Optional[int] = None,
    error: Optional[str] = None,
):
    """
    Convenience function to log a slow query.

    Args:
        collection: Database collection name
        operation: Operation type
        duration: Query duration in seconds
        query_details: Optional query details
        result_count: Number of results returned
        error: Error message if query failed
    """
    logger_instance = get_slow_query_logger()
    logger_instance.log_query(
        collection=collection,
        operation=operation,
        duration=duration,
        query_details=query_details,
        result_count=result_count,
        error=error,
    )
