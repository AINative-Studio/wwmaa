"""
Session Analytics Service for WWMAA Backend

Provides comprehensive analytics for training sessions including:
- Attendance statistics (registered vs attended)
- Engagement metrics (chat, reactions, interactions)
- VOD metrics (views, watch time, drop-off points)
- Peak concurrent viewers
- Comparative analytics across sessions
- CSV export functionality
"""

import logging
import csv
import io
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from collections import defaultdict, Counter
from uuid import UUID

from backend.services.zerodb_service import (
    get_zerodb_client,
    ZeroDBError,
    ZeroDBNotFoundError,
    ZeroDBValidationError
)
from backend.config import settings

# Configure logging
logger = logging.getLogger(__name__)


class SessionAnalyticsError(Exception):
    """Base exception for session analytics errors"""
    pass


class CloudflareAnalyticsError(SessionAnalyticsError):
    """Exception raised when Cloudflare Analytics API fails"""
    pass


class SessionAnalyticsService:
    """
    Session Analytics Service

    Provides comprehensive analytics for training sessions including:
    - Attendance tracking and statistics
    - Engagement metrics (chat, reactions, questions)
    - VOD analytics from Cloudflare Stream
    - Peak concurrent viewer calculations
    - Comparative analytics across sessions
    - CSV export functionality for reporting
    """

    def __init__(self):
        """Initialize Session Analytics Service"""
        self.db = get_zerodb_client()
        self.sessions_collection = "training_sessions"
        self.attendance_collection = "session_attendance"
        self.chat_collection = "session_chat"
        self.feedback_collection = "session_feedback"
        self.reactions_collection = "session_reactions"

        # Cloudflare configuration
        self.cloudflare_account_id = settings.CLOUDFLARE_ACCOUNT_ID
        self.cloudflare_api_token = settings.CLOUDFLARE_API_TOKEN

        logger.info("SessionAnalyticsService initialized")

    def get_session_analytics(self, session_id: str) -> Dict[str, Any]:
        """
        Get comprehensive analytics for a training session

        Args:
            session_id: Training session ID

        Returns:
            Complete analytics dictionary with:
                - session_info: Basic session details
                - attendance: Attendance statistics
                - engagement: Engagement metrics
                - vod: Video-on-demand metrics
                - peak_viewers: Peak concurrent viewer data
                - feedback: Ratings and feedback summary

        Raises:
            ZeroDBNotFoundError: If session doesn't exist
            SessionAnalyticsError: If analytics generation fails
        """
        try:
            logger.info(f"Generating comprehensive analytics for session: {session_id}")

            # Get session details
            session = self.db.get_document(
                collection=self.sessions_collection,
                document_id=session_id
            )

            # Gather all analytics components
            attendance_stats = self.get_attendance_stats(session_id)
            engagement_metrics = self.get_engagement_metrics(session_id)
            peak_viewers = self.get_peak_concurrent_viewers(session_id)
            feedback_summary = self._get_feedback_summary(session_id)

            # Get VOD metrics if recording exists
            vod_metrics = {}
            cloudflare_video_id = session.get("cloudflare_video_id")
            if cloudflare_video_id:
                try:
                    vod_metrics = self.get_vod_metrics(session_id, cloudflare_video_id)
                except CloudflareAnalyticsError as e:
                    logger.warning(f"Failed to fetch VOD metrics: {e}")
                    vod_metrics = {"error": "VOD metrics unavailable"}

            # Calculate engagement score (0-100)
            engagement_score = self._calculate_engagement_score(
                attendance_stats,
                engagement_metrics,
                peak_viewers
            )

            analytics = {
                "session_id": session_id,
                "session_info": {
                    "title": session.get("title"),
                    "instructor_id": session.get("instructor_id"),
                    "session_date": session.get("session_date"),
                    "duration_minutes": session.get("duration_minutes"),
                    "session_status": session.get("session_status"),
                    "started_at": session.get("started_at"),
                    "ended_at": session.get("ended_at")
                },
                "attendance": attendance_stats,
                "engagement": engagement_metrics,
                "peak_viewers": peak_viewers,
                "vod": vod_metrics,
                "feedback": feedback_summary,
                "engagement_score": engagement_score,
                "generated_at": datetime.utcnow().isoformat()
            }

            logger.info(f"Analytics generated successfully for session: {session_id}")
            return analytics

        except ZeroDBNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to generate session analytics: {e}")
            raise SessionAnalyticsError(f"Failed to generate session analytics: {e}")

    def get_attendance_stats(self, session_id: str) -> Dict[str, Any]:
        """
        Get attendance statistics for a session

        Args:
            session_id: Training session ID

        Returns:
            Dictionary with:
                - total_registered: Number of RSVPs/registrations
                - total_attended: Number who joined live
                - attendance_rate: Percentage (attended/registered)
                - on_time_arrivals: Number who joined on time
                - late_arrivals: Number who joined late
                - average_duration_minutes: Average time spent in session
                - attendee_list: List of attendee records

        Raises:
            SessionAnalyticsError: If calculation fails
        """
        try:
            logger.info(f"Calculating attendance stats for session: {session_id}")

            # Get session details for start time
            session = self.db.get_document(
                collection=self.sessions_collection,
                document_id=session_id
            )

            session_start = session.get("started_at") or session.get("session_date")
            if isinstance(session_start, str):
                session_start = datetime.fromisoformat(session_start.replace("Z", "+00:00"))

            # Query attendance records
            attendance_result = self.db.query_documents(
                collection=self.attendance_collection,
                filters={"session_id": session_id},
                limit=1000
            )

            attendees = attendance_result.get("documents", [])

            # Calculate statistics
            total_registered = len(attendees)
            total_attended = sum(1 for a in attendees if a.get("joined_at"))

            on_time = 0
            late = 0
            durations = []

            for attendee in attendees:
                joined_at = attendee.get("joined_at")
                left_at = attendee.get("left_at")

                if joined_at:
                    # Parse timestamps
                    if isinstance(joined_at, str):
                        joined_at = datetime.fromisoformat(joined_at.replace("Z", "+00:00"))

                    # Check if on time (within 5 minutes of start)
                    if session_start:
                        time_diff = (joined_at - session_start).total_seconds() / 60
                        if time_diff <= 5:
                            on_time += 1
                        else:
                            late += 1

                    # Calculate duration
                    if left_at:
                        if isinstance(left_at, str):
                            left_at = datetime.fromisoformat(left_at.replace("Z", "+00:00"))
                        duration_minutes = (left_at - joined_at).total_seconds() / 60
                        durations.append(duration_minutes)

            attendance_rate = (total_attended / total_registered * 100) if total_registered > 0 else 0
            average_duration = sum(durations) / len(durations) if durations else 0

            stats = {
                "total_registered": total_registered,
                "total_attended": total_attended,
                "attendance_rate": round(attendance_rate, 2),
                "on_time_arrivals": on_time,
                "late_arrivals": late,
                "average_duration_minutes": round(average_duration, 2),
                "total_duration_minutes": sum(durations),
                "attendee_count": len(attendees)
            }

            logger.info(f"Attendance stats calculated: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Failed to calculate attendance stats: {e}")
            raise SessionAnalyticsError(f"Failed to calculate attendance stats: {e}")

    def get_engagement_metrics(self, session_id: str) -> Dict[str, Any]:
        """
        Get engagement metrics for a session

        Args:
            session_id: Training session ID

        Returns:
            Dictionary with:
                - chat_message_count: Total chat messages
                - unique_chatters: Number of unique participants who chatted
                - reaction_count: Total reactions given
                - reaction_breakdown: Count by reaction type
                - questions_asked: Number of questions (if tracked)
                - poll_participation: Poll response rate (if applicable)

        Raises:
            SessionAnalyticsError: If calculation fails
        """
        try:
            logger.info(f"Calculating engagement metrics for session: {session_id}")

            # Get chat messages
            chat_result = self.db.query_documents(
                collection=self.chat_collection,
                filters={"session_id": session_id},
                limit=10000
            )

            chat_messages = chat_result.get("documents", [])
            chat_message_count = len(chat_messages)

            # Count unique chatters
            unique_chatters = len(set(msg.get("user_id") for msg in chat_messages if msg.get("user_id")))

            # Count questions (messages ending with ?)
            questions_asked = sum(1 for msg in chat_messages if msg.get("message", "").strip().endswith("?"))

            # Get reactions
            reactions_result = self.db.query_documents(
                collection=self.reactions_collection,
                filters={"session_id": session_id},
                limit=10000
            )

            reactions = reactions_result.get("documents", [])
            reaction_count = len(reactions)

            # Breakdown by reaction type
            reaction_breakdown = Counter(r.get("reaction_type") for r in reactions if r.get("reaction_type"))

            # Calculate engagement rate (percentage of attendees who engaged)
            attendance_stats = self.get_attendance_stats(session_id)
            total_attended = attendance_stats.get("total_attended", 0)

            engaged_users = set()
            for msg in chat_messages:
                if msg.get("user_id"):
                    engaged_users.add(msg.get("user_id"))
            for reaction in reactions:
                if reaction.get("user_id"):
                    engaged_users.add(reaction.get("user_id"))

            engagement_rate = (len(engaged_users) / total_attended * 100) if total_attended > 0 else 0

            metrics = {
                "chat_message_count": chat_message_count,
                "unique_chatters": unique_chatters,
                "questions_asked": questions_asked,
                "reaction_count": reaction_count,
                "reaction_breakdown": dict(reaction_breakdown),
                "unique_engaged_users": len(engaged_users),
                "engagement_rate": round(engagement_rate, 2)
            }

            logger.info(f"Engagement metrics calculated: {metrics}")
            return metrics

        except Exception as e:
            logger.error(f"Failed to calculate engagement metrics: {e}")
            raise SessionAnalyticsError(f"Failed to calculate engagement metrics: {e}")

    def get_peak_concurrent_viewers(self, session_id: str) -> Dict[str, Any]:
        """
        Calculate peak concurrent viewers for a session

        Analyzes join/leave timestamps to determine the maximum number
        of concurrent viewers at any point during the session.

        Args:
            session_id: Training session ID

        Returns:
            Dictionary with:
                - peak_count: Maximum concurrent viewers
                - peak_timestamp: When peak occurred
                - timeline: List of (timestamp, count) tuples for charting

        Raises:
            SessionAnalyticsError: If calculation fails
        """
        try:
            logger.info(f"Calculating peak concurrent viewers for session: {session_id}")

            # Get all attendance records
            attendance_result = self.db.query_documents(
                collection=self.attendance_collection,
                filters={"session_id": session_id},
                limit=1000
            )

            attendees = attendance_result.get("documents", [])

            # Create events list (join/leave)
            events = []

            for attendee in attendees:
                joined_at = attendee.get("joined_at")
                left_at = attendee.get("left_at")

                if joined_at:
                    if isinstance(joined_at, str):
                        joined_at = datetime.fromisoformat(joined_at.replace("Z", "+00:00"))
                    events.append((joined_at, 1))  # +1 for join

                if left_at:
                    if isinstance(left_at, str):
                        left_at = datetime.fromisoformat(left_at.replace("Z", "+00:00"))
                    events.append((left_at, -1))  # -1 for leave

            # Sort events by timestamp
            events.sort(key=lambda x: x[0])

            # Calculate concurrent viewers at each event
            peak_count = 0
            peak_timestamp = None
            current_count = 0
            timeline = []

            for timestamp, delta in events:
                current_count += delta

                if current_count > peak_count:
                    peak_count = current_count
                    peak_timestamp = timestamp

                # Add to timeline (sample every event for detailed chart)
                timeline.append({
                    "timestamp": timestamp.isoformat(),
                    "viewers": current_count
                })

            # Sample timeline for charts (max 100 points to avoid overwhelming frontend)
            if len(timeline) > 100:
                step = len(timeline) // 100
                timeline = timeline[::step]

            result = {
                "peak_count": peak_count,
                "peak_timestamp": peak_timestamp.isoformat() if peak_timestamp else None,
                "timeline": timeline,
                "total_events": len(events)
            }

            logger.info(f"Peak concurrent viewers: {peak_count}")
            return result

        except Exception as e:
            logger.error(f"Failed to calculate peak concurrent viewers: {e}")
            raise SessionAnalyticsError(f"Failed to calculate peak concurrent viewers: {e}")

    def get_vod_metrics(self, session_id: str, video_id: str) -> Dict[str, Any]:
        """
        Get video-on-demand metrics from Cloudflare Stream Analytics

        Args:
            session_id: Training session ID
            video_id: Cloudflare Stream video ID

        Returns:
            Dictionary with:
                - total_views: Total number of views
                - unique_viewers: Number of unique viewers
                - total_watch_time_minutes: Total watch time
                - average_watch_time_minutes: Average watch time per viewer
                - completion_rate: Percentage who watched to end
                - drop_off_points: List of timestamps where viewers dropped off
                - quality_distribution: Playback quality breakdown
                - geographic_distribution: Views by country
                - device_distribution: Views by device type

        Raises:
            CloudflareAnalyticsError: If API call fails
        """
        try:
            logger.info(f"Fetching VOD metrics for video: {video_id}")

            if not self.cloudflare_account_id or not self.cloudflare_api_token:
                raise CloudflareAnalyticsError("Cloudflare credentials not configured")

            # Get video analytics from Cloudflare Stream API
            # Reference: https://developers.cloudflare.com/stream/analytics/
            url = f"https://api.cloudflare.com/client/v4/accounts/{self.cloudflare_account_id}/stream/analytics/views"

            headers = {
                "Authorization": f"Bearer {self.cloudflare_api_token}",
                "Content-Type": "application/json"
            }

            # Calculate time range (last 30 days or since session date)
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)

            params = {
                "videoId": video_id,
                "since": start_date.isoformat(),
                "until": end_date.isoformat()
            }

            response = requests.get(url, headers=headers, params=params, timeout=30)

            if not response.ok:
                logger.warning(f"Cloudflare Analytics API returned {response.status_code}")
                # Return mock data structure if API fails
                return self._get_mock_vod_metrics()

            data = response.json()

            if not data.get("success"):
                raise CloudflareAnalyticsError("Cloudflare API returned unsuccessful response")

            result = data.get("result", {})

            # Parse and structure the analytics data
            metrics = {
                "total_views": result.get("totalViews", 0),
                "unique_viewers": result.get("uniqueViewers", 0),
                "total_watch_time_minutes": round(result.get("totalTimeViewedMinutes", 0), 2),
                "average_watch_time_minutes": round(result.get("averageTimeViewedMinutes", 0), 2),
                "completion_rate": round(result.get("completionRate", 0) * 100, 2),
                "quality_distribution": result.get("qualityDistribution", {}),
                "geographic_distribution": result.get("countryViews", {}),
                "device_distribution": result.get("deviceDistribution", {}),
                "drop_off_points": self._parse_drop_off_points(result.get("viewershipTimeSeries", []))
            }

            logger.info(f"VOD metrics fetched: {metrics['total_views']} views")
            return metrics

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch Cloudflare analytics: {e}")
            raise CloudflareAnalyticsError(f"Failed to fetch Cloudflare analytics: {e}")
        except Exception as e:
            logger.error(f"Failed to get VOD metrics: {e}")
            raise CloudflareAnalyticsError(f"Failed to get VOD metrics: {e}")

    def get_comparative_analytics(self, session_ids: List[str]) -> Dict[str, Any]:
        """
        Compare analytics across multiple sessions

        Args:
            session_ids: List of session IDs to compare

        Returns:
            Dictionary with:
                - sessions: List of session comparisons
                - trends: Trend analysis (improving/declining)
                - averages: Average metrics across sessions

        Raises:
            SessionAnalyticsError: If comparison fails
        """
        try:
            logger.info(f"Comparing {len(session_ids)} sessions")

            if len(session_ids) < 2:
                raise SessionAnalyticsError("At least 2 sessions required for comparison")

            if len(session_ids) > 10:
                raise SessionAnalyticsError("Maximum 10 sessions can be compared at once")

            comparisons = []

            for session_id in session_ids:
                try:
                    analytics = self.get_session_analytics(session_id)

                    # Extract key metrics for comparison
                    comparison = {
                        "session_id": session_id,
                        "title": analytics["session_info"]["title"],
                        "session_date": analytics["session_info"]["session_date"],
                        "attendance_rate": analytics["attendance"]["attendance_rate"],
                        "total_attended": analytics["attendance"]["total_attended"],
                        "engagement_score": analytics["engagement_score"],
                        "chat_messages": analytics["engagement"]["chat_message_count"],
                        "peak_viewers": analytics["peak_viewers"]["peak_count"],
                        "average_rating": analytics["feedback"].get("average_rating", 0)
                    }

                    comparisons.append(comparison)

                except Exception as e:
                    logger.warning(f"Failed to get analytics for session {session_id}: {e}")
                    continue

            if not comparisons:
                raise SessionAnalyticsError("No valid session analytics found")

            # Calculate averages
            averages = {
                "attendance_rate": sum(s["attendance_rate"] for s in comparisons) / len(comparisons),
                "total_attended": sum(s["total_attended"] for s in comparisons) / len(comparisons),
                "engagement_score": sum(s["engagement_score"] for s in comparisons) / len(comparisons),
                "chat_messages": sum(s["chat_messages"] for s in comparisons) / len(comparisons),
                "peak_viewers": sum(s["peak_viewers"] for s in comparisons) / len(comparisons),
                "average_rating": sum(s["average_rating"] for s in comparisons) / len(comparisons)
            }

            # Detect trends (comparing first half to second half)
            trends = self._detect_trends(comparisons)

            result = {
                "sessions": comparisons,
                "averages": averages,
                "trends": trends,
                "total_sessions": len(comparisons),
                "comparison_date": datetime.utcnow().isoformat()
            }

            logger.info(f"Comparative analytics generated for {len(comparisons)} sessions")
            return result

        except SessionAnalyticsError:
            raise
        except Exception as e:
            logger.error(f"Failed to generate comparative analytics: {e}")
            raise SessionAnalyticsError(f"Failed to generate comparative analytics: {e}")

    def export_attendance_csv(self, session_id: str) -> str:
        """
        Export attendance report to CSV format

        Args:
            session_id: Training session ID

        Returns:
            CSV string with attendance data

        Raises:
            SessionAnalyticsError: If export fails
        """
        try:
            logger.info(f"Exporting attendance CSV for session: {session_id}")

            # Get session details
            session = self.db.get_document(
                collection=self.sessions_collection,
                document_id=session_id
            )

            # Get attendance records
            attendance_result = self.db.query_documents(
                collection=self.attendance_collection,
                filters={"session_id": session_id},
                limit=1000
            )

            attendees = attendance_result.get("documents", [])

            # Get engagement data for each attendee
            engagement_data = self._get_attendee_engagement(session_id)

            # Create CSV in memory
            output = io.StringIO()

            # Write BOM for Excel UTF-8 compatibility
            output.write('\ufeff')

            writer = csv.writer(output)

            # Write header
            headers = [
                "Session Name",
                "Attendee Name",
                "Email",
                "User ID",
                "Joined At",
                "Left At",
                "Duration (minutes)",
                "Status",
                "Messages Sent",
                "Reactions Given",
                "Questions Asked",
                "Watched VOD",
                "VOD Watch Time (minutes)",
                "VOD Completion %",
                "Rating",
                "Feedback"
            ]
            writer.writerow(headers)

            # Write data rows
            for attendee in attendees:
                user_id = attendee.get("user_id")
                joined_at = attendee.get("joined_at")
                left_at = attendee.get("left_at")

                # Calculate duration
                duration = 0
                if joined_at and left_at:
                    if isinstance(joined_at, str):
                        joined_at_dt = datetime.fromisoformat(joined_at.replace("Z", "+00:00"))
                    else:
                        joined_at_dt = joined_at

                    if isinstance(left_at, str):
                        left_at_dt = datetime.fromisoformat(left_at.replace("Z", "+00:00"))
                    else:
                        left_at_dt = left_at

                    duration = round((left_at_dt - joined_at_dt).total_seconds() / 60, 2)

                # Get engagement metrics for this user
                user_engagement = engagement_data.get(str(user_id), {})

                # Get feedback if exists
                feedback_record = self._get_user_feedback(session_id, user_id)

                row = [
                    session.get("title", ""),
                    attendee.get("user_name", ""),
                    attendee.get("user_email", ""),
                    str(user_id),
                    joined_at or "Not joined",
                    left_at or "Still in session" if joined_at else "Not joined",
                    duration if joined_at else 0,
                    "Attended" if joined_at else "Registered",
                    user_engagement.get("messages_sent", 0),
                    user_engagement.get("reactions_given", 0),
                    user_engagement.get("questions_asked", 0),
                    "Yes" if attendee.get("watched_vod") else "No",
                    attendee.get("vod_watch_time_minutes", 0),
                    attendee.get("vod_completion_percent", 0),
                    feedback_record.get("rating", ""),
                    feedback_record.get("comment", "")
                ]

                writer.writerow(row)

            csv_content = output.getvalue()
            output.close()

            logger.info(f"CSV export completed: {len(attendees)} records")
            return csv_content

        except Exception as e:
            logger.error(f"Failed to export attendance CSV: {e}")
            raise SessionAnalyticsError(f"Failed to export attendance CSV: {e}")

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    def _get_feedback_summary(self, session_id: str) -> Dict[str, Any]:
        """Get feedback and ratings summary for a session"""
        try:
            feedback_result = self.db.query_documents(
                collection=self.feedback_collection,
                filters={"session_id": session_id},
                limit=1000
            )

            feedback_records = feedback_result.get("documents", [])

            if not feedback_records:
                return {
                    "total_responses": 0,
                    "average_rating": 0,
                    "rating_distribution": {},
                    "top_themes": []
                }

            ratings = [f.get("rating", 0) for f in feedback_records if f.get("rating")]
            average_rating = sum(ratings) / len(ratings) if ratings else 0

            rating_distribution = Counter(ratings)

            # Extract top feedback themes (simple keyword extraction)
            comments = [f.get("comment", "") for f in feedback_records if f.get("comment")]
            top_themes = self._extract_feedback_themes(comments)

            return {
                "total_responses": len(feedback_records),
                "average_rating": round(average_rating, 2),
                "rating_distribution": dict(rating_distribution),
                "top_themes": top_themes,
                "response_rate": 0  # Would need total attendees to calculate
            }

        except Exception as e:
            logger.warning(f"Failed to get feedback summary: {e}")
            return {
                "total_responses": 0,
                "average_rating": 0,
                "rating_distribution": {},
                "top_themes": []
            }

    def _calculate_engagement_score(
        self,
        attendance: Dict[str, Any],
        engagement: Dict[str, Any],
        peak_viewers: Dict[str, Any]
    ) -> float:
        """
        Calculate overall engagement score (0-100)

        Factors:
        - Attendance rate (30%)
        - Engagement rate (40%)
        - Chat activity (15%)
        - Peak viewer retention (15%)
        """
        try:
            attendance_rate = attendance.get("attendance_rate", 0)
            engagement_rate = engagement.get("engagement_rate", 0)

            # Normalize chat activity (assume 1 message per minute is 100%)
            duration = attendance.get("average_duration_minutes", 60)
            chat_count = engagement.get("chat_message_count", 0)
            chat_score = min(100, (chat_count / duration) * 100) if duration > 0 else 0

            # Peak viewer retention (peak vs registered)
            total_registered = attendance.get("total_registered", 1)
            peak_count = peak_viewers.get("peak_count", 0)
            retention_score = (peak_count / total_registered * 100) if total_registered > 0 else 0

            # Weighted score
            score = (
                attendance_rate * 0.30 +
                engagement_rate * 0.40 +
                chat_score * 0.15 +
                retention_score * 0.15
            )

            return round(min(100, max(0, score)), 2)

        except Exception as e:
            logger.warning(f"Failed to calculate engagement score: {e}")
            return 0.0

    def _parse_drop_off_points(self, timeseries_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse drop-off points from Cloudflare timeseries data"""
        try:
            if not timeseries_data:
                return []

            drop_offs = []

            for i in range(1, len(timeseries_data)):
                prev_viewers = timeseries_data[i - 1].get("viewers", 0)
                curr_viewers = timeseries_data[i].get("viewers", 0)

                # Detect significant drop-off (>20% decrease)
                if prev_viewers > 0:
                    drop_percent = ((prev_viewers - curr_viewers) / prev_viewers) * 100

                    if drop_percent > 20:
                        drop_offs.append({
                            "timestamp": timeseries_data[i].get("timestamp"),
                            "viewers_before": prev_viewers,
                            "viewers_after": curr_viewers,
                            "drop_percent": round(drop_percent, 2)
                        })

            # Return top 5 drop-off points
            drop_offs.sort(key=lambda x: x["drop_percent"], reverse=True)
            return drop_offs[:5]

        except Exception as e:
            logger.warning(f"Failed to parse drop-off points: {e}")
            return []

    def _detect_trends(self, comparisons: List[Dict[str, Any]]) -> Dict[str, str]:
        """Detect trends across sessions (improving/declining)"""
        try:
            if len(comparisons) < 2:
                return {}

            # Sort by date
            sorted_sessions = sorted(comparisons, key=lambda x: x.get("session_date", ""))

            # Compare first half to second half
            mid_point = len(sorted_sessions) // 2
            first_half = sorted_sessions[:mid_point]
            second_half = sorted_sessions[mid_point:]

            def avg(sessions, key):
                values = [s[key] for s in sessions if s.get(key) is not None]
                return sum(values) / len(values) if values else 0

            trends = {}
            metrics = ["attendance_rate", "engagement_score", "average_rating"]

            for metric in metrics:
                first_avg = avg(first_half, metric)
                second_avg = avg(second_half, metric)

                if second_avg > first_avg * 1.1:  # 10% improvement
                    trends[metric] = "improving"
                elif second_avg < first_avg * 0.9:  # 10% decline
                    trends[metric] = "declining"
                else:
                    trends[metric] = "stable"

            return trends

        except Exception as e:
            logger.warning(f"Failed to detect trends: {e}")
            return {}

    def _extract_feedback_themes(self, comments: List[str]) -> List[str]:
        """Extract common themes from feedback comments (simple keyword extraction)"""
        try:
            # Simple keyword frequency analysis
            all_words = []

            for comment in comments:
                # Basic cleanup and tokenization
                words = comment.lower().split()
                # Filter out common words
                filtered = [w for w in words if len(w) > 4]
                all_words.extend(filtered)

            # Get top 5 most common keywords
            word_counts = Counter(all_words)
            top_themes = [word for word, count in word_counts.most_common(5)]

            return top_themes

        except Exception as e:
            logger.warning(f"Failed to extract feedback themes: {e}")
            return []

    def _get_attendee_engagement(self, session_id: str) -> Dict[str, Dict[str, int]]:
        """Get engagement metrics per attendee"""
        try:
            # Get chat messages per user
            chat_result = self.db.query_documents(
                collection=self.chat_collection,
                filters={"session_id": session_id},
                limit=10000
            )

            messages = chat_result.get("documents", [])

            # Get reactions per user
            reactions_result = self.db.query_documents(
                collection=self.reactions_collection,
                filters={"session_id": session_id},
                limit=10000
            )

            reactions = reactions_result.get("documents", [])

            # Aggregate by user
            user_engagement = defaultdict(lambda: {
                "messages_sent": 0,
                "reactions_given": 0,
                "questions_asked": 0
            })

            for msg in messages:
                user_id = str(msg.get("user_id"))
                user_engagement[user_id]["messages_sent"] += 1

                if msg.get("message", "").strip().endswith("?"):
                    user_engagement[user_id]["questions_asked"] += 1

            for reaction in reactions:
                user_id = str(reaction.get("user_id"))
                user_engagement[user_id]["reactions_given"] += 1

            return dict(user_engagement)

        except Exception as e:
            logger.warning(f"Failed to get attendee engagement: {e}")
            return {}

    def _get_user_feedback(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """Get feedback for a specific user"""
        try:
            feedback_result = self.db.query_documents(
                collection=self.feedback_collection,
                filters={
                    "session_id": session_id,
                    "user_id": str(user_id)
                },
                limit=1
            )

            feedback_records = feedback_result.get("documents", [])

            if feedback_records:
                return feedback_records[0]

            return {}

        except Exception as e:
            logger.warning(f"Failed to get user feedback: {e}")
            return {}

    def _get_mock_vod_metrics(self) -> Dict[str, Any]:
        """Return mock VOD metrics structure when API is unavailable"""
        return {
            "total_views": 0,
            "unique_viewers": 0,
            "total_watch_time_minutes": 0,
            "average_watch_time_minutes": 0,
            "completion_rate": 0,
            "quality_distribution": {},
            "geographic_distribution": {},
            "device_distribution": {},
            "drop_off_points": [],
            "note": "VOD metrics unavailable"
        }


# Global service instance (singleton pattern)
_service_instance: Optional[SessionAnalyticsService] = None


def get_session_analytics_service() -> SessionAnalyticsService:
    """
    Get or create the global Session Analytics Service instance

    Returns:
        SessionAnalyticsService instance
    """
    global _service_instance

    if _service_instance is None:
        _service_instance = SessionAnalyticsService()

    return _service_instance
