"""
DeadlineOS Business OS — Vision & Shelf Monitoring REST API (Phase C4.1)
=======================================================================
REST API endpoints for shelf zone topology, planogram targets, secure media
ingestion, and visual observation records.
"""

from flask import Blueprint, request, g
import base64
from middleware.business_context import require_workspace
from services.business.shelf_zone_service import ShelfZoneService
from services.business.vision_ingestion_service import VisionIngestionService
from services.business.visual_extraction_service import VisualExtractionService
from services.business.planogram_service import PlanogramService
from services.business.discrepancy_reconciliation_service import DiscrepancyReconciliationService
from services.business.visual_restock_service import VisualRestockService
from utils.errors import APIError
from utils.responses import success_response, error_response

vision_bp = Blueprint('business_vision', __name__)


# ── Shelf Zone Topology ───────────────────────────────────────────────────────

@vision_bp.route('/zones', methods=['POST'])
@require_workspace('vision:manage')
def create_shelf_zone():
    """Creates a new physical shelf zone fixture in a workspace location."""
    data = request.get_json() or {}
    try:
        zone = ShelfZoneService.create_shelf_zone(
            workspace_id=g.workspace_id,
            actor_user_id=g.user_id,
            data=data,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        return success_response({
            'message': f"Shelf zone '{zone.zone_code}' created successfully.",
            'zone': zone.serialize()
        }, status_code=201)
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@vision_bp.route('/zones', methods=['GET'])
@require_workspace('vision:read')
def list_shelf_zones():
    """Lists and filters shelf zones in the workspace."""
    location_id = request.args.get('location_id')
    status = request.args.get('status')
    product_id = request.args.get('product_id')
    limit = min(int(request.args.get('limit', 100)), 200)
    offset = int(request.args.get('offset', 0))

    try:
        zones, total = ShelfZoneService.list_shelf_zones(
            workspace_id=g.workspace_id,
            location_id=location_id,
            status=status,
            product_id=product_id,
            limit=limit,
            offset=offset
        )
        return success_response({
            'zones': zones,
            'total': total,
            'limit': limit,
            'offset': offset
        })
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@vision_bp.route('/zones/<zone_id>', methods=['GET'])
@require_workspace('vision:read')
def get_shelf_zone(zone_id: str):
    """Retrieves a single shelf zone by ID."""
    try:
        zone = ShelfZoneService.get_shelf_zone_by_id(g.workspace_id, zone_id)
        return success_response({'zone': zone.serialize()})
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@vision_bp.route('/zones/<zone_id>', methods=['PUT', 'PATCH'])
@require_workspace('vision:manage')
def update_shelf_zone(zone_id: str):
    """Updates an existing shelf zone fixture."""
    data = request.get_json() or {}
    try:
        zone = ShelfZoneService.update_shelf_zone(
            workspace_id=g.workspace_id,
            zone_id=zone_id,
            actor_user_id=g.user_id,
            data=data,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        return success_response({
            'message': f"Shelf zone '{zone.zone_code}' updated successfully.",
            'zone': zone.serialize()
        })
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@vision_bp.route('/zones/<zone_id>/deactivate', methods=['POST'])
@require_workspace('vision:manage')
def deactivate_shelf_zone(zone_id: str):
    """Deactivates a shelf zone fixture."""
    data = request.get_json() or {}
    reason = data.get('reason')
    try:
        zone = ShelfZoneService.deactivate_shelf_zone(
            workspace_id=g.workspace_id,
            zone_id=zone_id,
            actor_user_id=g.user_id,
            reason=reason,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        return success_response({
            'message': f"Shelf zone '{zone.zone_code}' deactivated.",
            'zone': zone.serialize()
        })
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


# ── Visual Media Capture & Observation Ingestion ──────────────────────────────

@vision_bp.route('/capture', methods=['POST'])
@require_workspace('vision:capture')
def capture_shelf_image():
    """
    Ingests a visual shelf capture photo via multipart form-data or JSON base64:
    - Sanitizes EXIF/GPS metadata
    - Enforces 15MB limit and dimension caps
    - Creates IngestionArtifact and BusinessVisualObservation foundation records
    - Returns signed download URL (15-min TTL)
    """
    location_id = None
    shelf_zone_id = None
    capture_device = None
    filename = "shelf_capture.jpg"
    content_type = None
    image_bytes = None

    if request.is_json:
        data = request.get_json() or {}
        location_id = data.get('location_id')
        shelf_zone_id = data.get('shelf_zone_id')
        capture_device = data.get('capture_device')
        filename = data.get('filename', 'shelf_capture.jpg')
        content_type = data.get('content_type')
        b64_content = data.get('image_base64')
        if not b64_content:
            return error_response("Field 'image_base64' or multipart file is required.", "MISSING_IMAGE_DATA", 400)
        try:
            if ',' in b64_content:
                b64_content = b64_content.split(',', 1)[1]
            image_bytes = base64.b64decode(b64_content)
        except Exception:
            return error_response("Invalid base64 image encoding.", "INVALID_IMAGE_BASE64", 400)
    else:
        # Multipart form-data
        location_id = request.form.get('location_id')
        shelf_zone_id = request.form.get('shelf_zone_id')
        capture_device = request.form.get('capture_device')
        if 'file' not in request.files:
            return error_response("No image file provided in form-data ('file').", "MISSING_FILE", 400)
        uploaded_file = request.files['file']
        filename = uploaded_file.filename or "shelf_capture.jpg"
        content_type = uploaded_file.content_type
        image_bytes = uploaded_file.read()

    if not location_id:
        return error_response("Field 'location_id' is required.", "MISSING_LOCATION", 400)

    try:
        res = VisionIngestionService.ingest_shelf_capture(
            workspace_id=g.workspace_id,
            location_id=location_id,
            actor_user_id=g.user_id,
            image_bytes=image_bytes,
            filename=filename,
            content_type=content_type,
            shelf_zone_id=shelf_zone_id,
            capture_device=capture_device,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        return success_response({
            'message': "Visual shelf capture ingested successfully.",
            'observation': res
        }, status_code=201)
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@vision_bp.route('/observations', methods=['GET'])
@require_workspace('vision:read')
def list_observations():
    """Lists and filters visual observations in the workspace."""
    location_id = request.args.get('location_id')
    shelf_zone_id = request.args.get('shelf_zone_id')
    anomaly_only = request.args.get('anomaly_only', '').lower() in ('true', '1')
    status = request.args.get('status')
    limit = min(int(request.args.get('limit', 50)), 100)
    offset = int(request.args.get('offset', 0))

    try:
        observations, total = VisionIngestionService.list_observations(
            workspace_id=g.workspace_id,
            location_id=location_id,
            shelf_zone_id=shelf_zone_id,
            anomaly_only=anomaly_only,
            status=status,
            limit=limit,
            offset=offset
        )
        return success_response({
            'observations': observations,
            'total': total,
            'limit': limit,
            'offset': offset
        })
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@vision_bp.route('/observations/<observation_id>', methods=['GET'])
@require_workspace('vision:read')
def get_observation(observation_id: str):
    """Retrieves visual observation details with time-limited signed image URL."""
    try:
        obs = VisionIngestionService.get_observation_by_id(g.workspace_id, observation_id)
        return success_response({'observation': obs})
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


# ── Multimodal Extraction & Planogram Auditing (Phase C4.2) ───────────────────

@vision_bp.route('/observations/<observation_id>/extract', methods=['POST'])
@require_workspace('vision:review')
def trigger_observation_extraction(observation_id: str):
    """
    Triggers multimodal visual inference, SKU matching, and planogram auditing
    on an existing observation record.
    """
    try:
        service = VisualExtractionService()
        obs = service.process_observation_extraction(
            workspace_id=g.workspace_id,
            observation_id=observation_id,
            actor_user_id=g.user_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        return success_response({
            'message': "Visual extraction and planogram audit completed.",
            'observation': obs.serialize()
        })
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@vision_bp.route('/extract-direct', methods=['POST'])
@require_workspace('vision:capture')
def extract_direct_shelf_capture():
    """
    Performs complete ingestion and immediate multimodal visual extraction in a single request.
    """
    location_id = None
    shelf_zone_id = None
    capture_device = None
    filename = "shelf_capture.jpg"
    content_type = None
    image_bytes = None

    if request.is_json:
        data = request.get_json() or {}
        location_id = data.get('location_id')
        shelf_zone_id = data.get('shelf_zone_id')
        capture_device = data.get('capture_device')
        filename = data.get('filename', 'shelf_capture.jpg')
        content_type = data.get('content_type')
        b64_content = data.get('image_base64')
        if not b64_content:
            return error_response("Field 'image_base64' or multipart file is required.", "MISSING_IMAGE_DATA", 400)
        try:
            if ',' in b64_content:
                b64_content = b64_content.split(',', 1)[1]
            image_bytes = base64.b64decode(b64_content)
        except Exception:
            return error_response("Invalid base64 image encoding.", "INVALID_IMAGE_BASE64", 400)
    else:
        location_id = request.form.get('location_id')
        shelf_zone_id = request.form.get('shelf_zone_id')
        capture_device = request.form.get('capture_device')
        if 'file' not in request.files:
            return error_response("No image file provided in form-data ('file').", "MISSING_FILE", 400)
        uploaded_file = request.files['file']
        filename = uploaded_file.filename or "shelf_capture.jpg"
        content_type = uploaded_file.content_type
        image_bytes = uploaded_file.read()

    if not location_id:
        return error_response("Field 'location_id' is required.", "MISSING_LOCATION", 400)

    try:
        service = VisualExtractionService()
        obs_dict = service.extract_direct(
            workspace_id=g.workspace_id,
            location_id=location_id,
            actor_user_id=g.user_id,
            image_bytes=image_bytes,
            filename=filename,
            content_type=content_type,
            shelf_zone_id=shelf_zone_id,
            capture_device=capture_device,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        return success_response({
            'message': "Direct visual capture and extraction processed.",
            'observation': obs_dict
        }, status_code=201)
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@vision_bp.route('/observations/<observation_id>/planogram-audit', methods=['GET'])
@require_workspace('vision:read')
def get_observation_planogram_audit(observation_id: str):
    """
    Returns real-time planogram audit metrics comparing the observation against shelf zone targets.
    """
    try:
        from models.business.visual_observation import BusinessVisualObservation
        obs = BusinessVisualObservation.query.filter_by(
            id=observation_id,
            workspace_id=g.workspace_id
        ).first()
        if not obs:
            return error_response("Observation not found.", "OBSERVATION_NOT_FOUND", 404)

        audit = PlanogramService.audit_shelf_zone(
            workspace_id=g.workspace_id,
            location_id=obs.location_id,
            shelf_zone=obs.shelf_zone,
            detected_items=obs.detected_items or [],
            matched_product_id=obs.matched_product_id,
            visual_count=obs.visual_count,
            visual_facings=obs.visual_facings
        )
        return success_response({'planogram_audit': audit})
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


# ── Discrepancy Reconciliation & Staged Corrections (Phase C4.3) ──────────────

@vision_bp.route('/observations/<observation_id>/propose-reconciliation', methods=['POST'])
@require_workspace('vision:review')
def propose_observation_reconciliation(observation_id: str):
    """
    Proposes an inventory reconciliation candidate from an observation with non-zero discrepancy.
    """
    data = request.get_json(silent=True) or {}
    override_reason = data.get('reason')
    try:
        staged = DiscrepancyReconciliationService.propose_reconciliation(
            workspace_id=g.workspace_id,
            observation_id=observation_id,
            actor_user_id=g.user_id,
            override_reason=override_reason,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        if staged is None:
            return success_response({
                'message': "No discrepancy detected on observation; no reconciliation candidate created.",
                'is_noop': True,
                'staged_extraction': None
            }, status_code=200)

        return success_response({
            'message': "Reconciliation candidate proposed successfully.",
            'is_noop': False,
            'staged_extraction': staged.serialize()
        }, status_code=201)
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@vision_bp.route('/observations/<observation_id>/dismiss', methods=['POST'])
@require_workspace('vision:review')
def dismiss_observation(observation_id: str):
    """
    Dismisses an observation without mutating inventory. If an open staged candidate exists, rejects it.
    """
    data = request.get_json(silent=True) or {}
    reason = data.get('reason')
    try:
        obs = DiscrepancyReconciliationService.dismiss_observation(
            workspace_id=g.workspace_id,
            observation_id=observation_id,
            actor_user_id=g.user_id,
            reason=reason,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        return success_response({
            'message': "Observation dismissed successfully.",
            'observation': obs.serialize()
        })
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@vision_bp.route('/discrepancies', methods=['GET'])
@require_workspace('vision:read')
def list_discrepancies():
    """
    Lists pending visual observations with non-zero discrepancies.
    """
    location_id = request.args.get('location_id')
    shelf_zone_id = request.args.get('shelf_zone_id')
    limit = min(int(request.args.get('limit', 50)), 100)
    offset = int(request.args.get('offset', 0))

    try:
        items, total = DiscrepancyReconciliationService.list_pending_discrepancies(
            workspace_id=g.workspace_id,
            location_id=location_id,
            shelf_zone_id=shelf_zone_id,
            limit=limit,
            offset=offset
        )
        return success_response({
            'discrepancies': items,
            'total': total,
            'limit': limit,
            'offset': offset
        })
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


# ── Visual Restock Triggers & Cross-Border Freight (Phase C4.4) ──────────────

@vision_bp.route('/observations/<observation_id>/trigger-restock', methods=['POST'])
@require_workspace('vision:review')
def trigger_observation_restock(observation_id: str):
    """
    Evaluates visual shelf depletion, checks in-transit freight, and generates a draft PR & operational alert.
    """
    data = request.get_json(silent=True) or {}
    override_qty = None
    if 'override_quantity' in data and data['override_quantity'] is not None:
        try:
            from decimal import Decimal
            override_qty = Decimal(str(data['override_quantity']))
        except Exception:
            override_qty = None

    try:
        result = VisualRestockService.evaluate_and_trigger_restock(
            workspace_id=g.workspace_id,
            observation_id=observation_id,
            actor_user_id=g.user_id,
            override_quantity=override_qty,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        return success_response(result, status_code=201 if result.get('is_depleted') and result.get('purchase_request') else 200)
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@vision_bp.route('/restock-triggers', methods=['GET'])
@require_workspace('vision:read')
def list_restock_triggers():
    """
    Lists depleted shelf zones across workspace locations with shortfall metrics and in-transit correlation.
    """
    location_id = request.args.get('location_id')
    limit = min(int(request.args.get('limit', 50)), 100)
    offset = int(request.args.get('offset', 0))

    try:
        items, total = VisualRestockService.list_active_restock_triggers(
            workspace_id=g.workspace_id,
            location_id=location_id,
            limit=limit,
            offset=offset
        )
        return success_response({
            'restock_triggers': items,
            'total': total,
            'limit': limit,
            'offset': offset
        })
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@vision_bp.route('/zones/<zone_id>/in-transit', methods=['GET'])
@require_workspace('vision:read')
def get_zone_in_transit_freight(zone_id: str):
    """
    Returns active in-transit purchase orders and cross-border freight shipments for a shelf zone's assigned product.
    """
    try:
        zone = ShelfZoneService.get_shelf_zone_by_id(g.workspace_id, zone_id)
        if not zone.assigned_product_id:
            return success_response({
                'zone_id': zone.id,
                'product_id': None,
                'in_transit_quantity': '0.00',
                'active_pos_count': 0,
                'active_shipments_count': 0,
                'shipments': []
            })

        summary = VisualRestockService.get_in_transit_freight_summary(
            workspace_id=g.workspace_id,
            product_id=zone.assigned_product_id,
            location_id=zone.location_id
        )
        summary['zone_id'] = zone.id
        summary['zone_code'] = zone.zone_code
        return success_response(summary)
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


