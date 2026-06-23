"""
DeadlineOS — Database Initializer
====================================
Creates all tables defined by SQLAlchemy models and optionally seeds
the database with realistic demo data for the hackathon demo.

Usage:
    python -m database.init_db            # create tables only
    python -m database.init_db --seed     # create tables + seed demo data
"""

import sys
import uuid
import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


def init_db(app) -> None:
    """
    Drop and recreate all tables inside the given Flask app context.
    Safe to call multiple times — existing tables are preserved unless
    drop_first=True is passed (not exposed here for safety).
    """
    from database.db import db  # noqa: F401    # Import all models here so SQLAlchemy knows about them
    import models.task
    import models.intelligence
    import models.intervention
    import models.goal  # noqa: F401  ensure all models are imported so metadata is populated

    with app.app_context():
        db.create_all()
        logger.info("[DB] All database tables created (or already exist).")


def seed_db(app) -> None:
    """
    Populate the database with realistic demo tasks for hackathon presentation.
    Skips seeding if data already exists.
    """
    from database.db import db
    from models.task import Task

    with app.app_context():
        # Guard: only seed on empty DB
        if Task.query.count() > 0:
            logger.info("[SEED] Database already seeded -- skipping.")
            return

        now = datetime.now(timezone.utc)

        demo_tasks = [
            Task(
                id=str(uuid.uuid4()),
                title="Prepare Investor Pitch Deck",
                description="Create a 10-slide deck covering product vision, traction, and ask.",
                deadline=now + timedelta(hours=36),
                estimated_hours=8.0,
                category="work",
                status="in_progress",
                source="manual",
            ),
            Task(
                id=str(uuid.uuid4()),
                title="Submit Hackathon Project",
                description="Final submission for Vibe2Ship 2026 — code + demo video + README.",
                deadline=now + timedelta(hours=12),
                estimated_hours=4.0,
                category="work",
                status="pending",
                source="manual",
            ),
            Task(
                id=str(uuid.uuid4()),
                title="Complete Q2 Performance Review",
                description="Self-assessment form for the engineering team.",
                deadline=now + timedelta(days=2),
                estimated_hours=2.0,
                category="work",
                status="pending",
                source="manual",
            ),
            Task(
                id=str(uuid.uuid4()),
                title="Read System Design Interview Book",
                description="Finish chapters 5–8 before the interview next week.",
                deadline=now + timedelta(days=5),
                estimated_hours=6.0,
                category="study",
                status="pending",
                source="manual",
            ),
            Task(
                id=str(uuid.uuid4()),
                title="Write Blog Post: AI Productivity in 2026",
                description="1500-word article for the company engineering blog.",
                deadline=now + timedelta(days=3),
                estimated_hours=3.0,
                category="work",
                status="pending",
                source="manual",
            ),
        ]

        db.session.bulk_save_objects(demo_tasks)
        db.session.commit()
        logger.info("[SEED] Seeded %d demo tasks.", len(demo_tasks))


# ── CLI entry-point ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import os
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from app import create_app

    flask_app = create_app()
    init_db(flask_app)

    if "--seed" in sys.argv:
        seed_db(flask_app)
        print("✅  Database initialised and seeded.")
    else:
        print("✅  Database initialised. Run with --seed to add demo data.")
