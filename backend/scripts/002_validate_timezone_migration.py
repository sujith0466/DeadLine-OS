import sys
import os
import logging
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import create_app
from database.db import db
from models.schedule import ScheduleSlot

logging.basicConfig(level=logging.INFO, format="[VALIDATOR] %(message)s")
logger = logging.getLogger(__name__)


def validate_migration():
    app = create_app()
    with app.app_context():
        # Check current state of the database
        logger.info("Validating current migration state...")

        slots = db.session.execute(
            db.text("SELECT id, start_time, end_time FROM schedule_slots")
        ).fetchall()

        migrated_count = 0
        unmigrated_count = 0
        invalid_count = 0

        for row in slots:
            slot_id = row[0]
            start_val = str(row[1])
            end_val = str(row[2])

            # Check if it looks like a migrated UTC datetime (ISO format or similar length)
            if len(start_val) > 8 and (" " in start_val or "T" in start_val):
                migrated_count += 1
            elif len(start_val) <= 5 and ":" in start_val:
                unmigrated_count += 1
            else:
                invalid_count += 1

        logger.info(f"Total Slots: {len(slots)}")
        logger.info(f"Fully Migrated to UTC: {migrated_count}")
        logger.info(f"Unmigrated (HH:MM string): {unmigrated_count}")
        logger.info(f"Invalid format: {invalid_count}")

        if unmigrated_count == 0 and invalid_count == 0:
            logger.info("Migration Validation PASSED.")
        else:
            logger.error(
                "Migration Validation FAILED. Found unmigrated or invalid records."
            )


def simulate_rollback():
    app = create_app()
    with app.app_context():
        logger.info(
            "Starting rollback simulation (converting UTC datetimes back to HH:MM naive strings)..."
        )

        slots = db.session.execute(
            db.text("SELECT id, start_time, end_time FROM schedule_slots")
        ).fetchall()

        rolled_back_count = 0
        for row in slots:
            slot_id = row[0]
            start_val = str(row[1])
            end_val = str(row[2])

            # If already rolled back, skip
            if len(start_val) <= 5:
                continue

            # Attempt to parse the ISO string and revert to HH:MM
            try:
                # E.g. "2026-06-15 09:00:00+00" -> "09:00"
                start_dt = datetime.fromisoformat(start_val.replace(" ", "T"))
                end_dt = datetime.fromisoformat(end_val.replace(" ", "T"))

                # Note: This is an imperfect rollback because we lost the original user timezone
                # (it was overwritten with UTC or default). But for testing rollback structure, we just strip time.
                s_hhmm = start_dt.strftime("%H:%M")
                e_hhmm = end_dt.strftime("%H:%M")

                db.session.execute(
                    db.text(
                        "UPDATE schedule_slots SET start_time = :s, end_time = :e WHERE id = :id"
                    ),
                    {"s": s_hhmm, "e": e_hhmm, "id": slot_id},
                )
                rolled_back_count += 1
            except Exception as e:
                logger.error(f"Failed to parse and rollback slot {slot_id}: {e}")

        db.session.commit()
        logger.info(
            f"Rollback simulation complete. Rolled back {rolled_back_count} records."
        )


if __name__ == "__main__":
    if "--rollback" in sys.argv:
        simulate_rollback()
    else:
        validate_migration()
