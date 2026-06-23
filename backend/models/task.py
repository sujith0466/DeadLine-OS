"""
DeadlineOS — Task Model
=========================
SQLAlchemy ORM model for the `tasks` table.

Maps directly to the database schema defined in the Master Blueprint.
Includes helper methods for serialization and status management.
"""

import uuid
from datetime import datetime, timezone

from database.db import db


class Task(db.Model):
    """
    Represents a user task tracked by DeadlineOS.

    Columns
    -------
    id              : UUID primary key (string)
    title           : Short task name (required)
    description     : Extended details (optional)
    deadline        : Absolute due datetime in UTC (required)
    estimated_hours : Effort estimate in decimal hours
    actual_hours    : Running total of logged hours
    category        : Freeform tag — work / personal / study
    status          : Lifecycle state — pending / in_progress / done / overdue
    source          : How the task was created — manual / vision / voice
    source_file     : Filename if extracted via Gemini Vision
    created_at      : UTC timestamp of record creation
    updated_at      : UTC timestamp of last modification
    """

    __tablename__ = "tasks"

    # ── Primary Key ───────────────────────────────────────────
    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # ── Core Fields ───────────────────────────────────────────
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    deadline = db.Column(db.DateTime, nullable=False)
    estimated_hours = db.Column(db.Float, nullable=True, default=1.0)
    actual_hours = db.Column(db.Float, nullable=False, default=0.0)

    # ── Classification ────────────────────────────────────────
    category = db.Column(db.String(50), nullable=True, default="work")
    status = db.Column(db.String(20), nullable=False, default="pending")
    #   Allowed values: pending | in_progress | done | overdue

    # ── Source Tracking ───────────────────────────────────────
    source = db.Column(db.String(20), nullable=False, default="manual")
    #   Allowed values: manual | vision | voice
    source_file = db.Column(db.String(512), nullable=True)

    # ── Intelligence ──────────────────────────────────────────
    ai_confidence = db.Column(db.Integer, nullable=True, default=92)

    # ── Timestamps ────────────────────────────────────────────
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # ── Repr ──────────────────────────────────────────────────
    def __repr__(self) -> str:
        return f"<Task id={self.id!r} title={self.title!r} status={self.status!r}>"

    # ── Computed Properties ───────────────────────────────────
    @property
    def is_overdue(self) -> bool:
        """True if deadline has passed and task is not done."""
        return (
            self.status not in ("done",)
            and datetime.now(timezone.utc) > self.deadline.replace(tzinfo=timezone.utc)
        )

    @property
    def hours_until_deadline(self) -> float:
        """Floating-point hours remaining until deadline (negative if past)."""
        delta = self.deadline.replace(tzinfo=timezone.utc) - datetime.now(timezone.utc)
        return round(delta.total_seconds() / 3600, 2)

    @property
    def completion_percentage(self) -> float:
        """
        Estimated completion % based on actual vs estimated hours.
        Capped at 99 until status is explicitly set to 'done'.
        """
        if self.status == "done":
            return 100.0
        if not self.estimated_hours or self.estimated_hours == 0:
            return 0.0
        raw = (self.actual_hours / self.estimated_hours) * 100
        return min(round(raw, 1), 99.0)

    # ── Serialization ─────────────────────────────────────────
    def to_dict(self) -> dict:
        """Return a JSON-serializable dictionary of this task."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "estimated_hours": self.estimated_hours,
            "actual_hours": self.actual_hours,
            "category": self.category,
            "status": self.status,
            "source": self.source,
            "source_file": self.source_file,
            "ai_confidence": self.ai_confidence,
            "is_overdue": self.is_overdue,
            "hours_until_deadline": self.hours_until_deadline,
            "completion_percentage": self.completion_percentage,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    # ── Class Methods ─────────────────────────────────────────
    @classmethod
    def get_all_pending(cls) -> list["Task"]:
        """Return all tasks that are not yet completed."""
        return cls.query.filter(cls.status != "done").order_by(cls.deadline.asc()).all()

    @classmethod
    def get_overdue(cls) -> list["Task"]:
        """Return tasks whose deadline has passed but are not marked done."""
        now = datetime.now(timezone.utc)
        return (
            cls.query.filter(cls.deadline < now, cls.status != "done")
            .order_by(cls.deadline.asc())
            .all()
        )
