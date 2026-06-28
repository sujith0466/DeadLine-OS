from typing import Any, Dict, Optional
from flask import jsonify, g

def success_response(data: Any = None, message: str = "Success", status_code: int = 200) -> tuple:
    """
    Standardized success response.
    
    Format:
    {
        "status": "success",
        "message": message,
        "data": data,
        "request_id": "<correlation_id>"
    }
    """
    request_id = getattr(g, "request_id", None)
    
    response_body = {
        "status": "success",
        "message": message,
    }
    if data is not None:
        response_body["data"] = data
    if request_id:
        response_body["request_id"] = request_id
        
    return jsonify(response_body), status_code

def error_response(message: str, error_code: str = "INTERNAL_ERROR", status_code: int = 500, details: Optional[Dict[str, Any]] = None) -> tuple:
    """
    Standardized error response.
    
    Format:
    {
        "status": "error",
        "error": {
            "code": error_code,
            "message": message,
            "details": details
        },
        "request_id": "<correlation_id>"
    }
    """
    request_id = getattr(g, "request_id", None)
    
    error_obj = {
        "code": error_code,
        "message": message
    }
    if details:
        error_obj["details"] = details
        
    response_body = {
        "status": "error",
        "error": error_obj
    }
    if request_id:
        response_body["request_id"] = request_id
        
    return jsonify(response_body), status_code
