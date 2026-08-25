"""
DeadlineOS — Notification Grouping Service
==========================================
Aggregates closely scheduled notifications within a rolling time window into
a consolidated digest notification, preventing notification fatigue.
"""

import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from database.db import db
from models.notification import Notification, NotificationStatus, NotificationType
from services.notifications.repository import NotificationRepository
from utils.timezone import utc_now


class GroupingService:
    """Consolidates clustered notifications deterministically."""

    DEFAULT_GROUP_WINDOW_MINUTES = 15
    SEVERITY_ORDER = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}

    @classmethod
    def group_pending_notifications(
        cls,
        user_id: str,
        window_minutes: int = DEFAULT_GROUP_WINDOW_MINUTES
    ) -> List[Notification]:
        """
        Scans pending/scheduled notifications for user_id and groups clusters
        exceeding 2 items into a single consolidated summary notification.
        """
        now = utc_now()
        horizon = now + timedelta(hours=24)

        # Get ungrouped scheduled or delivered notifications
        candidates = (
            Notification.query.filter_by(user_id=user_id, group_id=None)
            .filter(Notification.status.in_([NotificationStatus.SCHEDULED, NotificationStatus.DELIVERED]))
            .filter(Notification.scheduled_at != None)
            .filter(Notification.scheduled_at <= horizon)
            .order_by(Notification.scheduled_at.asc())
            .all()
        )

        if len(candidates) < 2:
            return candidates

        # Cluster by window
        clusters: List[List[Notification]] = []
        current_cluster: List[Notification] = []
        cluster_start: Optional[datetime] = None

        for n in candidates:
            n_time = n.scheduled_at.replace(tzinfo=timezone.utc) if n.scheduled_at.tzinfo is None else n.scheduled_at
            if not cluster_start:
                cluster_start = n_time
                current_cluster.append(n)
            elif (n_time - cluster_start) <= timedelta(minutes=window_minutes):
                current_cluster.append(n)
            else:
                if len(current_cluster) >= 2:
                    clusters.append(current_cluster)
                current_cluster = [n]
                cluster_start = n_time

        if len(current_cluster) >= 2:
            clusters.append(current_cluster)

        # Create consolidated group notifications
        group_notifications: List[Notification] = []
        for cluster in clusters:
            group_id = str(uuid.uuid4())
            count = len(cluster)
            
            # Find highest severity in cluster
            top_sev = max(
                (n.severity or "info" for n in cluster),
                key=lambda s: cls.SEVERITY_ORDER.get(s, 0)
            )

            # Earliest scheduled time in cluster
            first_time = min(
                (n.scheduled_at.replace(tzinfo=timezone.utc) if n.scheduled_at.tzinfo is None else n.scheduled_at for n in cluster)
            )

            # Update child notifications
            activity_titles = []
            for n in cluster:
                n.group_id = group_id
                activity_titles.append(n.title)

            # Create group parent notification
            summary_title = f"{count} activities scheduled soon"
            summary_desc = ", ".join(activity_titles[:3])
            if count > 3:
                summary_desc += f" and {count - 3} more"

            group_notif = Notification(
                user_id=user_id,
                notification_type=NotificationType.REMINDER,
                title=summary_title,
                description=summary_desc,
                severity=top_sev,
                status=NotificationStatus.DELIVERED if first_time <= now else NotificationStatus.SCHEDULED,
                scheduled_at=first_time,
                delivered_at=now if first_time <= now else None,
                group_id=group_id,
                action_url="/today",
                category="Planner"
            )
            NotificationRepository.save(group_notif)
            group_notifications.append(group_notif)

        db.session.commit()
        return group_notifications
