"""
DeadlineOS Business OS — Task Service
======================================
Business logic for workspace task management, work allocation,
status transitions, and forensic audit logging.
"""

from database.db import db
from datetime import datetime, timezone
from models.business import BusinessTask, WorkspaceMember, BusinessLocation, BusinessProduct, BusinessEntity
from services.business.audit_service import AuditService
from utils.errors import APIError


class TaskService:
    VALID_STATUSES = {'TODO', 'IN_PROGRESS', 'BLOCKED', 'DONE', 'CANCELLED'}
    VALID_PRIORITIES = {'LOW', 'MEDIUM', 'HIGH', 'URGENT'}
    VALID_CATEGORIES = {'GENERAL', 'INVENTORY', 'PROCUREMENT', 'FACILITY', 'AUDIT', 'MAINTENANCE'}

    VALID_TRANSITIONS = {
        'TODO': {'IN_PROGRESS', 'CANCELLED'},
        'IN_PROGRESS': {'BLOCKED', 'DONE', 'CANCELLED', 'TODO'},
        'BLOCKED': {'IN_PROGRESS', 'CANCELLED'},
        'DONE': {'IN_PROGRESS'},  # Reopening completed task
        'CANCELLED': {'TODO'}     # Restoring cancelled task
    }

    @staticmethod
    def create_task(
        workspace_id: str,
        actor_user_id: str,
        data: dict,
        ip_address: str = None,
        user_agent: str = None
    ) -> BusinessTask:
        title = (data.get('title') or '').strip()
        if not title:
            raise APIError("Task 'title' is required.", "VALIDATION_ERROR", 400)

        priority = (data.get('priority') or 'MEDIUM').upper()
        if priority not in TaskService.VALID_PRIORITIES:
            raise APIError(f"Invalid priority '{priority}'. Allowed: {TaskService.VALID_PRIORITIES}", "VALIDATION_ERROR", 400)

        category = (data.get('category') or 'GENERAL').upper()
        if category not in TaskService.VALID_CATEGORIES:
            category = 'GENERAL'

        assignee_member_id = data.get('assignee_member_id')
        if assignee_member_id:
            member = WorkspaceMember.query.filter_by(id=assignee_member_id, workspace_id=workspace_id, status='ACTIVE').first()
            if not member:
                raise APIError("Assignee member not found or inactive in this workspace.", "VALIDATION_ERROR", 400)

        location_id = data.get('location_id')
        if location_id:
            loc = BusinessLocation.query.filter_by(id=location_id, workspace_id=workspace_id).first()
            if not loc:
                raise APIError("Referenced location not found in this workspace.", "VALIDATION_ERROR", 400)

        product_id = data.get('product_id')
        if product_id:
            prod = BusinessProduct.query.filter_by(id=product_id, workspace_id=workspace_id).first()
            if not prod:
                raise APIError("Referenced product not found in this workspace.", "VALIDATION_ERROR", 400)

        entity_id = data.get('entity_id')
        if entity_id:
            ent = BusinessEntity.query.filter_by(id=entity_id, workspace_id=workspace_id).first()
            if not ent:
                raise APIError("Referenced entity not found in this workspace.", "VALIDATION_ERROR", 400)

        parent_task_id = data.get('parent_task_id')
        if parent_task_id:
            pt = BusinessTask.query.filter_by(id=parent_task_id, workspace_id=workspace_id).first()
            if not pt:
                raise APIError("Parent task not found in this workspace.", "VALIDATION_ERROR", 400)

        due_date = None
        if data.get('due_date'):
            try:
                raw_dt = data['due_date'].replace('Z', '+00:00')
                due_date = datetime.fromisoformat(raw_dt)
                if due_date.tzinfo is None:
                    due_date = due_date.replace(tzinfo=timezone.utc)
            except Exception:
                raise APIError("Invalid ISO 8601 format for 'due_date'.", "VALIDATION_ERROR", 400)

        task = BusinessTask(
            workspace_id=workspace_id,
            title=title,
            description=data.get('description'),
            assignee_member_id=assignee_member_id,
            created_by_user_id=actor_user_id,
            priority=priority,
            status='TODO',
            due_date=due_date,
            entity_id=entity_id,
            location_id=location_id,
            product_id=product_id,
            parent_task_id=parent_task_id,
            category=category,
            notes=data.get('notes')
        )
        db.session.add(task)
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action="TASK_CREATED",
            entity_type="business_task",
            entity_id=task.id,
            after_state=task.serialize(),
            reason="Task created via Business OS Operations",
            ip_address=ip_address,
            user_agent=user_agent
        )
        return task

    @staticmethod
    def get_tasks(
        workspace_id: str,
        status: str = None,
        priority: str = None,
        assignee_member_id: str = None,
        location_id: str = None,
        product_id: str = None,
        category: str = None,
        search: str = None,
        limit: int = 50,
        offset: int = 0
    ):
        query = BusinessTask.query.filter_by(workspace_id=workspace_id)

        if status:
            query = query.filter_by(status=status.upper())
        if priority:
            query = query.filter_by(priority=priority.upper())
        if assignee_member_id:
            query = query.filter_by(assignee_member_id=assignee_member_id)
        if location_id:
            query = query.filter_by(location_id=location_id)
        if product_id:
            query = query.filter_by(product_id=product_id)
        if category:
            query = query.filter_by(category=category.upper())
        if search:
            query = query.filter(BusinessTask.title.ilike(f"%{search}%"))

        total = query.count()
        tasks = query.order_by(BusinessTask.created_at.desc()).offset(offset).limit(min(limit, 100)).all()
        return [t.serialize() for t in tasks], total

    @staticmethod
    def get_task_by_id(workspace_id: str, task_id: str) -> BusinessTask:
        task = BusinessTask.query.filter_by(id=task_id, workspace_id=workspace_id).first()
        if not task:
            raise APIError("Business task not found in this workspace.", "NOT_FOUND", 404)
        return task

    @staticmethod
    def update_task(
        workspace_id: str,
        actor_user_id: str,
        task_id: str,
        data: dict,
        ip_address: str = None,
        user_agent: str = None
    ) -> BusinessTask:
        task = TaskService.get_task_by_id(workspace_id, task_id)
        before_state = task.serialize()

        if 'title' in data:
            title = (data['title'] or '').strip()
            if not title:
                raise APIError("Task 'title' cannot be empty.", "VALIDATION_ERROR", 400)
            task.title = title

        if 'description' in data:
            task.description = data['description']

        if 'priority' in data:
            priority = (data['priority'] or 'MEDIUM').upper()
            if priority not in TaskService.VALID_PRIORITIES:
                raise APIError(f"Invalid priority '{priority}'.", "VALIDATION_ERROR", 400)
            task.priority = priority

        if 'category' in data:
            category = (data['category'] or 'GENERAL').upper()
            if category in TaskService.VALID_CATEGORIES:
                task.category = category

        if 'notes' in data:
            task.notes = data['notes']

        if 'location_id' in data:
            loc_id = data['location_id']
            if loc_id:
                loc = BusinessLocation.query.filter_by(id=loc_id, workspace_id=workspace_id).first()
                if not loc:
                    raise APIError("Location not found in this workspace.", "VALIDATION_ERROR", 400)
            task.location_id = loc_id

        if 'due_date' in data:
            if data['due_date']:
                try:
                    raw_dt = data['due_date'].replace('Z', '+00:00')
                    dt = datetime.fromisoformat(raw_dt)
                    task.due_date = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
                except Exception:
                    raise APIError("Invalid ISO 8601 format for 'due_date'.", "VALIDATION_ERROR", 400)
            else:
                task.due_date = None

        task.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action="TASK_UPDATED",
            entity_type="business_task",
            entity_id=task.id,
            before_state=before_state,
            after_state=task.serialize(),
            reason="Task metadata updated",
            ip_address=ip_address,
            user_agent=user_agent
        )
        return task

    @staticmethod
    def assign_task(
        workspace_id: str,
        actor_user_id: str,
        task_id: str,
        assignee_member_id: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> BusinessTask:
        task = TaskService.get_task_by_id(workspace_id, task_id)
        before_state = task.serialize()

        if assignee_member_id:
            member = WorkspaceMember.query.filter_by(id=assignee_member_id, workspace_id=workspace_id, status='ACTIVE').first()
            if not member:
                raise APIError("Assignee member not found or inactive in this workspace.", "VALIDATION_ERROR", 400)
            task.assignee_member_id = assignee_member_id
        else:
            task.assignee_member_id = None

        task.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action="TASK_ASSIGNED",
            entity_type="business_task",
            entity_id=task.id,
            before_state=before_state,
            after_state=task.serialize(),
            reason=f"Task assigned to member {assignee_member_id}",
            ip_address=ip_address,
            user_agent=user_agent
        )
        return task

    @staticmethod
    def transition_status(
        workspace_id: str,
        actor_user_id: str,
        task_id: str,
        new_status: str,
        reason: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> BusinessTask:
        task = TaskService.get_task_by_id(workspace_id, task_id)
        before_state = task.serialize()

        new_status = (new_status or '').upper()
        if new_status not in TaskService.VALID_STATUSES:
            raise APIError(f"Invalid status '{new_status}'. Allowed: {TaskService.VALID_STATUSES}", "VALIDATION_ERROR", 400)

        if new_status == task.status:
            return task

        allowed = TaskService.VALID_TRANSITIONS.get(task.status, set())
        if new_status not in allowed:
            raise APIError(
                f"Illegal status transition from '{task.status}' to '{new_status}'. Allowed: {list(allowed)}",
                "INVALID_STATE_TRANSITION",
                400
            )

        task.status = new_status
        if new_status == 'DONE':
            task.completed_at = datetime.now(timezone.utc)
            task.completed_by_user_id = actor_user_id
        else:
            task.completed_at = None
            task.completed_by_user_id = None

        task.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action="TASK_STATUS_CHANGED",
            entity_type="business_task",
            entity_id=task.id,
            before_state=before_state,
            after_state=task.serialize(),
            reason=reason or f"Status transitioned to {new_status}",
            ip_address=ip_address,
            user_agent=user_agent
        )
        return task

    @staticmethod
    def delete_task(
        workspace_id: str,
        actor_user_id: str,
        task_id: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> bool:
        task = TaskService.get_task_by_id(workspace_id, task_id)
        before_state = task.serialize()

        db.session.delete(task)
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action="TASK_DELETED",
            entity_type="business_task",
            entity_id=task_id,
            before_state=before_state,
            after_state=None,
            reason="Task deleted",
            ip_address=ip_address,
            user_agent=user_agent
        )
        return True
