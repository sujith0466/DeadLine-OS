"""
DeadlineOS Business OS — Operational Alert Service (Phase C2.4)
===============================================================
Proactive operational telemetry, signal evaluation, deduplicated alerting,
cooldown suppression, and signal-to-task synthesis.

Strict Invariants:
1. Signal != Alert != Task != Deadline.
2. Deduplication fingerprint prevents alert spamming across evaluation runs.
3. Cooldown window (e.g. 24 hours) prevents re-triggering while active.
4. Consequential actions emit forensic AuditEvents.
"""

import uuid
import hashlib
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal
from database.db import db
from models.business import (
    BusinessOperationalAlert,
    BusinessTask,
    BusinessProduct,
    BusinessPurchaseOrder,
    CommercialPartner,
    AuditEvent,
)
from services.business.operational_intelligence_service import OperationalIntelligenceService
from services.business.task_service import TaskService
from services.business.audit_service import AuditService
from utils.errors import APIError


class OperationalAlertService:

    @staticmethod
    def evaluate_operational_signals(workspace_id: str, actor_user_id: str = None) -> list:
        """
        Evaluates operational signals and generates deduplicated alerts:
        1. Stockout imminent (DIR <= 7 days or stock <= 0)
        2. Below safety stock / reorder level
        3. Overdue Purchase Orders (expected_delivery_date < today)
        4. Supplier Quality Degradation (Quality < 80% with >= 3 deliveries)
        5. Dead Stock Accumulation (> 60 days with 0 OUT movements)
        """
        created_alerts = []
        now = datetime.now(timezone.utc)
        today = date.today()

        # ── 1. Evaluate Inventory Velocity & Stockout Signals ───────────────────
        forecasts = OperationalIntelligenceService.get_inventory_forecast(workspace_id, window_days=30)
        for f in forecasts:
            prod_id = f['product_id']
            health = f['stock_health']
            stock = Decimal(f['factual_stock'])
            reorder = Decimal(f['reorder_level'])
            safety = Decimal(f['safety_stock'])

            if health == 'OUT_OF_STOCK':
                alert = OperationalAlertService._generate_alert_if_not_duplicate(
                    workspace_id=workspace_id,
                    alert_type='STOCKOUT_IMMINENT',
                    severity='CRITICAL',
                    title=f"Critical Stockout: {f['name']} is depleted",
                    description=f"Physical stock is 0 {f['unit']}. Reorder threshold is {reorder} {f['unit']}.",
                    entity_type='PRODUCT',
                    entity_id=prod_id,
                    recommended_action='CREATE_PURCHASE_REQUEST'
                )
                if alert:
                    created_alerts.append(alert)

            elif health == 'CRITICAL_RISK':
                dir_days = f['days_of_inventory_remaining']
                runout = f['projected_stockout_date']
                alert = OperationalAlertService._generate_alert_if_not_duplicate(
                    workspace_id=workspace_id,
                    alert_type='STOCKOUT_IMMINENT',
                    severity='CRITICAL',
                    title=f"Imminent Stockout Risk: {f['name']}",
                    description=f"Current stock ({stock} {f['unit']}) will deplete in ~{dir_days} days (Projected: {runout}) based on daily burn rate of {f['daily_burn_rate']}/day.",
                    entity_type='PRODUCT',
                    entity_id=prod_id,
                    recommended_action='CREATE_PURCHASE_REQUEST'
                )
                if alert:
                    created_alerts.append(alert)

            elif health == 'LOW_STOCK' or (stock <= reorder and reorder > Decimal('0.00')):
                alert = OperationalAlertService._generate_alert_if_not_duplicate(
                    workspace_id=workspace_id,
                    alert_type='BELOW_SAFETY_STOCK',
                    severity='WARNING',
                    title=f"Low Stock Warning: {f['name']}",
                    description=f"Current stock ({stock} {f['unit']}) is at or below reorder level ({reorder} {f['unit']}).",
                    entity_type='PRODUCT',
                    entity_id=prod_id,
                    recommended_action='CREATE_PURCHASE_REQUEST'
                )
                if alert:
                    created_alerts.append(alert)

            elif health == 'DEAD_STOCK':
                alert = OperationalAlertService._generate_alert_if_not_duplicate(
                    workspace_id=workspace_id,
                    alert_type='DEAD_STOCK_ACCUMULATION',
                    severity='INFO',
                    title=f"Dead Stock Detected: {f['name']}",
                    description=f"{stock} {f['unit']} on hand with zero consumption movements in over 60 days.",
                    entity_type='PRODUCT',
                    entity_id=prod_id,
                    recommended_action='INSPECT_INVENTORY'
                )
                if alert:
                    created_alerts.append(alert)

        # ── 2. Evaluate Overdue Purchase Orders ────────────────────────────────
        overdue_pos = BusinessPurchaseOrder.query.filter(
            BusinessPurchaseOrder.workspace_id == workspace_id,
            BusinessPurchaseOrder.status.in_(['SENT_TO_SUPPLIER', 'PARTIALLY_RECEIVED']),
            BusinessPurchaseOrder.expected_delivery_date < today
        ).all()

        for po in overdue_pos:
            days_overdue = (today - po.expected_delivery_date).days
            alert = OperationalAlertService._generate_alert_if_not_duplicate(
                workspace_id=workspace_id,
                alert_type='OVERDUE_PURCHASE_ORDER',
                severity='WARNING' if days_overdue <= 7 else 'CRITICAL',
                title=f"Overdue Purchase Order: {po.po_number}",
                description=f"Consignment expected on {po.expected_delivery_date.isoformat()} is {days_overdue} days past due from {po.supplier.name if po.supplier else 'supplier'}.",
                entity_type='PURCHASE_ORDER',
                entity_id=po.id,
                recommended_action='EXPEDITE_PO'
            )
            if alert:
                created_alerts.append(alert)

        # ── 3. Evaluate Supplier Quality Degradation ───────────────────────────
        suppliers = OperationalIntelligenceService.get_supplier_performance_summary(workspace_id)
        for s in suppliers:
            if s['status'] == 'RATED' and s['quality_acceptance_rate'] is not None:
                quality = Decimal(s['quality_acceptance_rate'])
                if quality < Decimal('80.0'):
                    alert = OperationalAlertService._generate_alert_if_not_duplicate(
                        workspace_id=workspace_id,
                        alert_type='SUPPLIER_QUALITY_DEGRADATION',
                        severity='WARNING',
                        title=f"Quality Alert: {s['supplier_name']}",
                        description=f"Supplier quality acceptance rate has degraded to {quality}% ({s['total_rejected_quantity']} units rejected across {s['completed_deliveries_count']} deliveries).",
                        entity_type='SUPPLIER',
                        entity_id=s['supplier_id'],
                        recommended_action='REVIEW_SUPPLIER'
                    )
                    if alert:
                        created_alerts.append(alert)

        return created_alerts

    @staticmethod
    def get_alerts(
        workspace_id: str,
        status: str = None,
        severity: str = None,
        entity_type: str = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[list, int]:
        """
        Lists operational alerts with filtering and pagination.
        """
        query = BusinessOperationalAlert.query.filter_by(workspace_id=workspace_id)
        if status:
            query = query.filter(BusinessOperationalAlert.status == status)
        if severity:
            query = query.filter(BusinessOperationalAlert.severity == severity)
        if entity_type:
            query = query.filter(BusinessOperationalAlert.entity_type == entity_type)

        total = query.count()
        alerts = query.order_by(
            # Sort order: CRITICAL > WARNING > INFO, then latest created
            BusinessOperationalAlert.created_at.desc()
        ).offset(offset).limit(limit).all()

        return [a.to_dict() for a in alerts], total

    @staticmethod
    def get_alert_by_id(workspace_id: str, alert_id: str) -> dict:
        alert = BusinessOperationalAlert.query.filter_by(
            id=alert_id,
            workspace_id=workspace_id
        ).first()
        if not alert:
            raise APIError("Operational alert not found.", code="ALERT_NOT_FOUND", status=404)
        return alert.to_dict()

    @staticmethod
    def acknowledge_alert(workspace_id: str, alert_id: str, actor_user_id: str) -> dict:
        """
        Acknowledges an active alert.
        """
        alert = BusinessOperationalAlert.query.filter_by(
            id=alert_id,
            workspace_id=workspace_id
        ).first()
        if not alert:
            raise APIError("Operational alert not found.", code="ALERT_NOT_FOUND", status=404)

        if alert.status != 'ACTIVE':
            raise APIError(f"Cannot acknowledge alert with status '{alert.status}'.", code="INVALID_STATUS", status=400)

        alert.status = 'ACKNOWLEDGED'
        alert.acknowledged_by_user_id = actor_user_id
        alert.acknowledged_at = datetime.now(timezone.utc)
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action='ALERT_ACKNOWLEDGED',
            entity_type='OPERATIONAL_ALERT',
            entity_id=alert.id,
            after_state={'status': 'ACKNOWLEDGED'}
        )
        return alert.to_dict()

    @staticmethod
    def resolve_alert(
        workspace_id: str,
        alert_id: str,
        actor_user_id: str,
        resolution_note: str = None
    ) -> dict:
        """
        Resolves an alert.
        """
        alert = BusinessOperationalAlert.query.filter_by(
            id=alert_id,
            workspace_id=workspace_id
        ).first()
        if not alert:
            raise APIError("Operational alert not found.", code="ALERT_NOT_FOUND", status=404)

        if alert.status in ('RESOLVED', 'DISMISSED'):
            raise APIError(f"Alert is already '{alert.status}'.", code="INVALID_STATUS", status=400)

        alert.status = 'RESOLVED'
        alert.resolved_by_user_id = actor_user_id
        alert.resolved_at = datetime.now(timezone.utc)
        alert.resolution_note = resolution_note
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action='ALERT_RESOLVED',
            entity_type='OPERATIONAL_ALERT',
            entity_id=alert.id,
            after_state={'status': 'RESOLVED', 'resolution_note': resolution_note}
        )
        return alert.to_dict()

    @staticmethod
    def dismiss_alert(workspace_id: str, alert_id: str, actor_user_id: str) -> dict:
        """
        Dismisses an alert.
        """
        alert = BusinessOperationalAlert.query.filter_by(
            id=alert_id,
            workspace_id=workspace_id
        ).first()
        if not alert:
            raise APIError("Operational alert not found.", code="ALERT_NOT_FOUND", status=404)

        alert.status = 'DISMISSED'
        alert.resolved_by_user_id = actor_user_id
        alert.resolved_at = datetime.now(timezone.utc)
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action='ALERT_DISMISSED',
            entity_type='OPERATIONAL_ALERT',
            entity_id=alert.id,
            after_state={'status': 'DISMISSED'}
        )
        return alert.to_dict()

    @staticmethod
    def create_task_from_alert(
        workspace_id: str,
        alert_id: str,
        actor_user_id: str,
        assignee_member_id: str = None,
        priority: str = None,
        due_date = None
    ) -> dict:
        """
        Synthesizes an assignable BusinessTask directly from an operational alert.
        Links task ID back to the alert and marks alert status as ACKNOWLEDGED.
        """
        alert = BusinessOperationalAlert.query.filter_by(
            id=alert_id,
            workspace_id=workspace_id
        ).first()
        if not alert:
            raise APIError("Operational alert not found.", code="ALERT_NOT_FOUND", status=404)

        if alert.generated_task_id:
            raise APIError("A task has already been generated from this alert.", code="TASK_ALREADY_GENERATED", status=400)

        task_priority = priority or ('URGENT' if alert.severity == 'CRITICAL' else ('HIGH' if alert.severity == 'WARNING' else 'MEDIUM'))
        task_due = due_date or (datetime.now(timezone.utc) + timedelta(days=2))

        # Create task via TaskService
        desc_text = f"Auto-generated from Operational Alert ({alert.alert_type}):\n{alert.description or ''}\nRecommended Action: {alert.recommended_action or 'Investigate'}"
        task_data = {
            'title': f"[ALERT] {alert.title}",
            'description': desc_text,
            'priority': task_priority,
            'status': 'TODO',
            'due_date': task_due.isoformat() if isinstance(task_due, datetime) else str(task_due),
            'assignee_member_id': assignee_member_id,
            'product_id': alert.entity_id if alert.entity_type == 'PRODUCT' else None,
        }

        task = TaskService.create_task(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            data=task_data
        )

        # Link alert
        alert.generated_task_id = task.id
        if alert.status == 'ACTIVE':
            alert.status = 'ACKNOWLEDGED'
            alert.acknowledged_by_user_id = actor_user_id
            alert.acknowledged_at = datetime.now(timezone.utc)
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action='ALERT_TASK_CREATED',
            entity_type='OPERATIONAL_ALERT',
            entity_id=alert.id,
            after_state={'generated_task_id': task.id}
        )

        return {
            'alert': alert.to_dict(),
            'task': task.serialize()
        }

    # ── Private Deduplication Helper ──────────────────────────────────────────

    @staticmethod
    def _generate_alert_if_not_duplicate(
        workspace_id: str,
        alert_type: str,
        severity: str,
        title: str,
        description: str,
        entity_type: str,
        entity_id: str,
        recommended_action: str = None,
        cooldown_hours: int = 24
    ) -> BusinessOperationalAlert:
        """
        Checks if an ACTIVE or ACKNOWLEDGED alert with matching fingerprint exists,
        or if currently within cooldown window. If not, generates and persists alert.
        """
        raw_key = f"{workspace_id}:{alert_type}:{entity_type}:{entity_id}"
        fingerprint = hashlib.sha256(raw_key.encode('utf-8')).hexdigest()[:32]
        now = datetime.now(timezone.utc)

        # 1. Check existing active/acknowledged alert
        existing = BusinessOperationalAlert.query.filter(
            BusinessOperationalAlert.workspace_id == workspace_id,
            BusinessOperationalAlert.dedup_fingerprint == fingerprint,
            BusinessOperationalAlert.status.in_(['ACTIVE', 'ACKNOWLEDGED'])
        ).first()

        if existing:
            return None  # Duplicate suppressed

        # 2. Check cooldown window on resolved/dismissed alert
        cooldown_match = BusinessOperationalAlert.query.filter(
            BusinessOperationalAlert.workspace_id == workspace_id,
            BusinessOperationalAlert.dedup_fingerprint == fingerprint,
            BusinessOperationalAlert.cooldown_until > now
        ).first()

        if cooldown_match:
            return None  # Cooldown suppressed

        # Create new alert
        alert = BusinessOperationalAlert(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            alert_type=alert_type,
            severity=severity,
            status='ACTIVE',
            title=title,
            description=description,
            entity_type=entity_type,
            entity_id=entity_id,
            dedup_fingerprint=fingerprint,
            cooldown_until=now + timedelta(hours=cooldown_hours),
            recommended_action=recommended_action,
            created_at=now,
            updated_at=now
        )
        db.session.add(alert)
        db.session.commit()
        return alert
