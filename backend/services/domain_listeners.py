import logging
from services.runtime.event_bus import activity_started, activity_completed
from models.task import Task
from models.goal import Goal
from database.db import db

logger = logging.getLogger(__name__)

@activity_started.connect
def handle_activity_started(sender, **kwargs):
    payload = kwargs.get('payload', {})
    entity_id = payload.get('entity_id')
    entity_type = payload.get('entity_type', '').upper()
    
    if not entity_id or not entity_type:
        return

    logger.info(f"DomainListener: Received activity_started for {entity_type} {entity_id}")
    
    try:
        if entity_type == 'TASK':
            task = db.session.get(Task, entity_id)
            if task and task.status != 'done':
                task.status = 'in_progress'
                db.session.add(task)
                db.session.commit()
        elif entity_type == 'GOAL':
            goal = db.session.get(Goal, entity_id)
            if goal and goal.status != 'Completed':
                goal.status = 'In Progress'
                db.session.add(goal)
                db.session.commit()
    except Exception as e:
        logger.error(f"Failed to update domain model on activity start: {e}")
        db.session.rollback()

@activity_completed.connect
def handle_activity_completed(sender, **kwargs):
    payload = kwargs.get('payload', {})
    entity_id = payload.get('entity_id')
    entity_type = payload.get('entity_type', '').upper()
    
    if not entity_id or not entity_type:
        return

    logger.info(f"DomainListener: Received activity_completed for {entity_type} {entity_id}")
    
    try:
        if entity_type == 'TASK':
            task = db.session.get(Task, entity_id)
            if task and task.status != 'done':
                task.status = 'done'
                db.session.add(task)
                db.session.commit()
        elif entity_type == 'GOAL':
            goal = db.session.get(Goal, entity_id)
            if goal and goal.status != 'Completed':
                goal.status = 'Completed'
                db.session.add(goal)
                db.session.commit()
    except Exception as e:
        logger.error(f"Failed to update domain model on activity complete: {e}")
        db.session.rollback()
