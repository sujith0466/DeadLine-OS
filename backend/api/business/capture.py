"""
DeadlineOS Business OS — Capture Endpoints
==========================================
Handles raw text entry and file upload ingestion into staged candidates.
"""

from flask import Blueprint, request, g
from utils.responses import success_response, error_response
from utils.errors import APIError
from middleware.business_context import require_workspace
from services.business.ingestion_service import IngestionService
from services.business.extraction_service import ExtractionService

capture_bp = Blueprint('biz_capture', __name__)


@capture_bp.route('/capture/text', methods=['POST'])
@require_workspace('staging:create')
def capture_text():
    """
    Ingests natural-language business notes/transactions and generates a staged candidate.
    """
    data = request.get_json() or {}
    text = data.get('text')
    if not text or not str(text).strip():
        return error_response("Field 'text' is required.", "VALIDATION_ERROR", 400)

    try:
        staged = ExtractionService.extract_from_text(
            workspace_id=g.workspace_id,
            user_id=g.user_id,
            raw_text=text.strip(),
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(
            data={"staged_extraction": staged.serialize()},
            message="Text captured and staged for review.",
            status_code=201
        )
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@capture_bp.route('/capture/upload', methods=['POST'])
@require_workspace('staging:create')
def capture_upload():
    """
    Uploads a document or audio artifact, calculates SHA-256, and creates a staged candidate.
    """
    if 'file' not in request.files:
        return error_response("No file provided in multipart request.", "VALIDATION_ERROR", 400)

    file = request.files['file']
    if not file.filename:
        return error_response("No selected filename.", "VALIDATION_ERROR", 400)

    file_bytes = file.read()
    artifact_type = request.form.get('artifact_type', 'DOCUMENT').upper()

    try:
        artifact, is_duplicate = IngestionService.store_artifact(
            workspace_id=g.workspace_id,
            uploader_user_id=g.user_id,
            file_bytes=file_bytes,
            filename=file.filename,
            content_type=file.content_type,
            artifact_type=artifact_type,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )

        staged = ExtractionService.extract_from_artifact(
            workspace_id=g.workspace_id,
            user_id=g.user_id,
            artifact_id=artifact.id,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )

        return success_response(
            data={
                "artifact": artifact.serialize(),
                "staged_extraction": staged.serialize(),
                "is_duplicate": is_duplicate
            },
            message="Artifact uploaded and staged for review.",
            status_code=201
        )
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)
