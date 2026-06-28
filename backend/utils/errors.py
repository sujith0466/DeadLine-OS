from werkzeug.exceptions import HTTPException
from marshmallow import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from flask import Flask, request
from utils.responses import error_response
import logging
import uuid
import traceback
import os

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Custom API Exception for known application errors."""
    def __init__(self, message: str, code: str = "API_ERROR", status: int = 400, details: dict = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status = status
        self.details = details or {}

def register_global_errors(app: Flask):
    """Register all global error handlers for the application."""
    
    is_dev = os.getenv("FLASK_ENV", "development") == "development"

    @app.errorhandler(ValidationError)
    def handle_marshmallow_error(err):
        """Handle Marshmallow validation errors explicitly."""
        return error_response(
            message="Validation failed",
            error_code="VALIDATION_ERROR",
            status_code=422,
            details=err.messages
        )

    @app.errorhandler(APIError)
    def handle_api_error(err):
        """Handle custom API errors."""
        return error_response(
            message=err.message,
            error_code=err.code,
            status_code=err.status,
            details=err.details
        )

    @app.errorhandler(HTTPException)
    def handle_http_exception(err):
        """Handle standard HTTP errors (e.g. 404, 405)."""
        return error_response(
            message=err.description,
            error_code=f"HTTP_{err.code}",
            status_code=err.code
        )

    @app.errorhandler(SQLAlchemyError)
    def handle_db_error(err):
        """Handle database errors and always rollback transaction."""
        from database.db import db
        db.session.rollback()
        logger.error(f"Database error on {request.path}: {str(err)}")
        return error_response(
            message="Database Service Unavailable. Please try again later.",
            error_code="DATABASE_ERROR",
            status_code=503
        )

    @app.errorhandler(Exception)
    def handle_unexpected_error(err):
        """Catch-all for unhandled exceptions."""
        error_id = str(uuid.uuid4())
        logger.error(f"Unhandled Exception [Error ID: {error_id}] on {request.method} {request.path}")
        logger.error(traceback.format_exc())

        message = "An unexpected server error occurred."
        details = None
        if is_dev:
            details = {"trace": traceback.format_exc(), "error_id": error_id}
        else:
            details = {"error_id": error_id}

        return error_response(
            message=message,
            error_code="INTERNAL_SERVER_ERROR",
            status_code=500,
            details=details
        )
