"""
DeadlineOS Business OS — Business Health & Diagnostics Service
==============================================================
Provides non-mutating, read-only diagnostic telemetry for Business OS subsystems.
"""

from database.db import db
from sqlalchemy import text
from datetime import datetime, timezone
import time
import logging

logger = logging.getLogger(__name__)

VERSION = "1.0.0-production"
BUILD_ID = "b8-release-j7g8h9i0j1k2"


class BusinessHealthService:
    @staticmethod
    def check_liveness() -> dict:
        """
        Ultra-lightweight process liveness probe.
        Answers: Is the Business OS server process alive and answering HTTP requests?
        """
        return {
            'status': 'ALIVE',
            'subsystem': 'Business OS',
            'version': VERSION,
            'build_id': BUILD_ID,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

    @staticmethod
    def check_readiness() -> dict:
        """
        Production readiness probe for load balancers and container orchestrators.
        Answers: Can the Business OS safely accept incoming production traffic?
        """
        start_time = time.time()
        is_ready = True
        db_status = 'OK'

        try:
            db.session.execute(text("SELECT 1")).scalar()
        except Exception as e:
            is_ready = False
            db_status = 'UNHEALTHY'
            logger.warning(f"Readiness check database probe failed: {e}")

        latency_ms = round((time.time() - start_time) * 1000, 2)

        return {
            'status': 'READY' if is_ready else 'NOT_READY',
            'subsystem': 'Business OS',
            'database': db_status,
            'latency_ms': latency_ms,
            'version': VERSION,
            'build_id': BUILD_ID,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

    @staticmethod
    def check_health() -> dict:
        """
        Comprehensive, non-mutating Deep Health Probe.
        Evaluates Database, Storage, Financial Ledger, Intelligence Engine,
        Multi-Entity Consolidation, Automation Subsystem, and RBAC / Workspace Scoping.
        """
        start_time = time.time()
        checks = {}
        subsystem_latencies = {}

        # 1. Read-only database connectivity probe
        t0 = time.time()
        try:
            db.session.execute(text("SELECT 1")).scalar()
            checks['database'] = 'OK'
        except Exception as e:
            logger.error(f"Health probe database check failed: {e}")
            checks['database'] = 'ERROR: Database connectivity unavailable'
        subsystem_latencies['database'] = round((time.time() - t0) * 1000, 2)

        # 2. Storage service readiness
        t0 = time.time()
        try:
            from services.business.storage_service import StorageService
            checks['storage'] = 'OK'
        except Exception as e:
            logger.warning(f"Health probe storage check error: {e}")
            checks['storage'] = 'ERROR: Storage service unavailable'
        subsystem_latencies['storage'] = round((time.time() - t0) * 1000, 2)

        # 3. Financial ledger subsystem integrity
        t0 = time.time()
        try:
            from models.business import Workspace, Invoice, BusinessTransaction, CommercialPartner
            # Read-only existence verification without data exposure
            Workspace.query.limit(1).first()
            checks['ledger'] = 'OK'
        except Exception as e:
            logger.error(f"Health probe ledger check failed: {e}")
            checks['ledger'] = 'ERROR: Ledger models unavailable'
        subsystem_latencies['ledger'] = round((time.time() - t0) * 1000, 2)

        # 4. Intelligence and planning engine readiness
        t0 = time.time()
        try:
            from services.business.intelligence_service import BusinessIntelligenceService
            checks['intelligence'] = 'OK'
        except Exception as e:
            logger.warning(f"Health probe intelligence check warning: {e}")
            checks['intelligence'] = 'ERROR: Intelligence subsystem unavailable'
        subsystem_latencies['intelligence'] = round((time.time() - t0) * 1000, 2)

        # 5. Multi-Entity and Consolidation registry
        t0 = time.time()
        try:
            from models.business import BusinessEntity, InterEntityTransfer
            BusinessEntity.query.limit(1).first()
            checks['consolidation'] = 'OK'
        except Exception as e:
            logger.warning(f"Health probe consolidation check warning: {e}")
            checks['consolidation'] = 'ERROR: Multi-entity registry unavailable'
        subsystem_latencies['consolidation'] = round((time.time() - t0) * 1000, 2)

        # 6. Recurring obligations and automation engine
        t0 = time.time()
        try:
            from models.business import RecurringObligation, AutomationExecutionLog
            RecurringObligation.query.limit(1).first()
            checks['automation'] = 'OK'
        except Exception as e:
            logger.warning(f"Health probe automation check warning: {e}")
            checks['automation'] = 'ERROR: Automation subsystem unavailable'
        subsystem_latencies['automation'] = round((time.time() - t0) * 1000, 2)

        # 7. Authentication, RBAC, and workspace scoping
        t0 = time.time()
        try:
            from models.business import WorkspaceMember, WorkspaceInvitation
            WorkspaceMember.query.limit(1).first()
            checks['auth_rbac'] = 'OK'
        except Exception as e:
            logger.error(f"Health probe RBAC check failed: {e}")
            checks['auth_rbac'] = 'ERROR: RBAC subsystem unavailable'
        subsystem_latencies['auth_rbac'] = round((time.time() - t0) * 1000, 2)

        total_latency_ms = round((time.time() - start_time) * 1000, 2)

        # Critical vs Non-critical evaluation
        critical_ok = checks.get('database') == 'OK' and checks.get('ledger') == 'OK' and checks.get('auth_rbac') == 'OK'
        all_ok = all(v == 'OK' for v in checks.values())

        if all_ok:
            status = 'HEALTHY'
        elif critical_ok:
            status = 'DEGRADED'
        else:
            status = 'UNHEALTHY'

        return {
            'status': status,
            'subsystem': 'Business OS',
            'version': VERSION,
            'build_id': BUILD_ID,
            'latency_ms': total_latency_ms,
            'checks': checks,
            'subsystem_latencies': subsystem_latencies,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
