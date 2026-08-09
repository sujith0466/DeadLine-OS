"""
DeadlineOS Migration Script: 001_migrate_schedule_timezones.py
==============================================================
Migrates existing ScheduleSlot string 'HH:MM' times into UTC-aware datetimes.
Performs the following:
  1. Identifies all ScheduleSlots whose start_time is stored as a string <= 5 chars.
  2. Resolves the user's timezone via get_user_timezone().
  3. Uses slot_times_to_utc() to calculate the correct UTC datetimes based on the schedule target_date.
  4. Saves back to the database.
  5. Generates an auditable MIGRATION_REPORT.md listing default assignments.
"""

import sys
import os
import json
import logging
from datetime import datetime, timezone

# Allow imports from backend root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from database.db import db
from models.schedule import ScheduleSlot, Schedule
from utils.timezone import slot_times_to_utc, get_user_timezone, DEFAULT_TIMEZONE

logging.basicConfig(level=logging.INFO, format="[MIGRATION] %(message)s")
logger = logging.getLogger(__name__)


def migrate_timezones():
    app = create_app()

    with app.app_context():
        logger.info("Starting ScheduleSlot timezone migration to UTC...")

        # Alter columns to bypass varchar(5) limits before migrating
        try:
            if db.engine.name == "postgresql":
                db.session.execute(
                    db.text(
                        "ALTER TABLE schedule_slots ALTER COLUMN start_time TYPE VARCHAR(50)"
                    )
                )
                db.session.execute(
                    db.text(
                        "ALTER TABLE schedule_slots ALTER COLUMN end_time TYPE VARCHAR(50)"
                    )
                )
                db.session.commit()
            elif db.engine.name == "sqlite":
                # SQLite doesn't strictly enforce varchar lengths, but we can recreate or just ignore
                pass
        except Exception as e:
            logger.warning(f"Failed to alter columns (may already be migrated): {e}")
            db.session.rollback()

        try:
            # Using raw SQL bypasses SQLAlchemy's db.DateTime parsing logic
            # for data that currently exists as strings.
            slots_query = db.session.execute(
                db.text(
                    "SELECT s.id as slot_id, s.start_time, s.end_time, s.user_id, sch.target_date "
                    "FROM schedule_slots s "
                    "JOIN schedules sch ON s.schedule_id = sch.id"
                )
            ).fetchall()
        except Exception as e:
            logger.error(f"Failed to fetch existing slots: {e}")
            return

        migrated_count = 0
        audit_log = []

        for row in slots_query:
            slot_id = row[0]
            start_val = str(row[1])
            end_val = str(row[2])
            user_id = row[3]
            target_date = row[4]

            # If the value is already a full ISO/datetime string (e.g. '2026-07-16 10:00:00'), skip
            if len(start_val) > 8 or " " in start_val or "T" in start_val:
                continue

            # It's an old HH:MM string (or HH:MM:SS)
            start_hhmm = start_val[:5]
            end_hhmm = end_val[:5]

            # Resolve timezone with savepoints to prevent transaction aborts on lookup failures
            user_tz = None
            try:
                with db.session.begin_nested():
                    user_tz = get_user_timezone(user_id)
            except Exception as e:
                logger.warning(
                    f"Failed to lookup timezone for user {user_id}, using default."
                )
                db.session.rollback()

            # Audit log logic
            if not user_tz or user_tz == DEFAULT_TIMEZONE:
                reason = "No custom timezone found on profile; defaulting to UTC."
                audit_log.append(
                    {
                        "slot_id": slot_id,
                        "user_id": user_id,
                        "applied_timezone": user_tz or DEFAULT_TIMEZONE,
                        "original_start": start_hhmm,
                        "original_target_date": target_date,
                        "reason": reason,
                    }
                )

            tz_to_use = user_tz or DEFAULT_TIMEZONE

            try:
                with db.session.begin_nested():
                    s_utc, e_utc = slot_times_to_utc(
                        target_date, start_hhmm, end_hhmm, tz_to_use
                    )
                    # Raw update
                    db.session.execute(
                        db.text(
                            "UPDATE schedule_slots SET start_time = :s_utc, end_time = :e_utc WHERE id = :id"
                        ),
                        {"s_utc": s_utc, "e_utc": e_utc, "id": slot_id},
                    )
                migrated_count += 1
            except Exception as parse_err:
                logger.error(f"Failed to migrate slot {slot_id}: {parse_err}")
                db.session.rollback()

        db.session.commit()
        logger.info(
            f"Successfully migrated {migrated_count} ScheduleSlot records to UTC datetimes."
        )

        # Write Audit Log
        if audit_log:
            report_path = os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__), "..", "..", "MIGRATION_REPORT.md"
                )
            )
            try:
                with open(report_path, "w", encoding="utf-8") as f:
                    f.write("# Migration Report: Timezone Hardening\n\n")
                    f.write(
                        f"Migration completed at: {datetime.now(timezone.utc).isoformat()}\n"
                    )
                    f.write(f"Total slots migrated: {migrated_count}\n")
                    f.write(
                        f"Records requiring default timezone assignment: {len(audit_log)}\n\n"
                    )
                    f.write("## Default Timezone Audit Log\n\n")
                    f.write(
                        "| Slot ID | User ID | Applied Timezone | Original Time | Reason |\n"
                    )
                    f.write(
                        "|---------|---------|------------------|---------------|--------|\n"
                    )
                    for entry in audit_log:
                        f.write(
                            f"| {entry['slot_id']} | {entry['user_id']} | {entry['applied_timezone']} | {entry['original_target_date']} {entry['original_start']} | {entry['reason']} |\n"
                        )
                logger.info(f"Migration audit report written to: {report_path}")
            except Exception as io_err:
                logger.error(f"Failed to write migration report: {io_err}")


if __name__ == "__main__":
    migrate_timezones()
