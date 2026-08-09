import sys
import os
import logging
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import create_app
from database.db import db
from models.schedule import ScheduleSlot, Schedule
from models.user_settings import UserSettings
from utils.timezone import get_user_timezone

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def verify_migration():
    app = create_app()
    with app.app_context():
        # Fetch 3 real slots
        slots = db.session.execute(db.text("""
            SELECT s.id, s.start_time, s.end_time, s.user_id, sch.target_date 
            FROM schedule_slots s 
            JOIN schedules sch ON s.schedule_id = sch.id 
            LIMIT 10
            """)).fetchall()

        logger.info(f"Found {len(slots)} slots. Analyzing first 3...")

        for i, row in enumerate(slots[:3]):
            slot_id = row[0]
            start_val = row[1]
            end_val = row[2]
            user_id = row[3]
            target_date = row[4]

            user_tz = get_user_timezone(user_id)
            settings = UserSettings.query.filter_by(user_id=user_id).first()
            raw_stored_tz = (
                settings.profile.get("timezone")
                if settings and settings.profile
                else None
            )

            logger.info(f"\n--- Record {i+1} ---")
            logger.info(f"Record ID: {slot_id}")
            logger.info(f"User ID: {user_id}")
            logger.info(f"Original Stored Value: Unknown (Now {start_val})")
            logger.info(f"User Profile Timezone: {raw_stored_tz}")
            logger.info(f"Fallback Timezone Logic Output: {user_tz}")
            logger.info(f"Current Stored Start: {start_val}")


if __name__ == "__main__":
    verify_migration()
