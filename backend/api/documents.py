import logging
from flask import Blueprint, jsonify, request
from services.document_service import DocumentService

logger = logging.getLogger(__name__)
documents_bp = Blueprint("documents", __name__)

@documents_bp.route("/documents/upload", methods=["POST"])
def upload_document():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"}), 400
        
    allowed_mimes = ["application/pdf", "text/plain", "text/markdown"]
    if file.mimetype not in allowed_mimes:
        return jsonify({"status": "error", "message": f"Unsupported file type: {file.mimetype}. Allowed: {', '.join(allowed_mimes)}"}), 400
        
    result = DocumentService.process_file(file)
    
    if "error" in result:
        return jsonify({"status": "error", "message": result["error"]}), 400
        
    return jsonify({
        "status": "success",
        "message": "Document processed and intelligence extracted successfully.",
        "data": result
    }), 200
