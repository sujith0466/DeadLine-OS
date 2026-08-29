"""
DeadlineOS Business OS — Collection Reminders Endpoints
=======================================================
Tone-aware collection reminder drafting, dispatch, and history.
"""

from flask import Blueprint, request, g
from utils.responses import success_response, error_response
from utils.errors import APIError
from middleware.business_context import require_workspace
from services.business.reminder_service import ReminderService

reminders_bp = Blueprint('biz_reminders', __name__)


@reminders_bp.route('/reminders/draft', methods=['POST'])
@require_workspace('transaction:create')
def draft_reminder():
    data = request.get_json(silent=True) or {}
    invoice_id = data.get('invoice_id')
    tone = data.get('tone', 'POLITE')

    if not invoice_id:
        return error_response("invoice_id is required.", code="MISSING_PARAM", status=400)

    try:
        reminder = ReminderService.draft_reminder(
            workspace_id=g.workspace_id,
            user_id=g.user_id,
            invoice_id=invoice_id,
            tone=tone,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(data={'reminder': reminder.to_dict()}, message="Collection reminder drafted successfully.", status_code=201)
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@reminders_bp.route('/reminders/<reminder_id>/send', methods=['POST'])
@require_workspace('transaction:create')
def send_reminder(reminder_id):
    data = request.get_json(silent=True) or {}
    custom_message = data.get('custom_message')

    try:
        reminder = ReminderService.send_reminder(
            workspace_id=g.workspace_id,
            user_id=g.user_id,
            reminder_id=reminder_id,
            custom_message=custom_message,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return success_response(data={'reminder': reminder.to_dict()}, message="Collection reminder dispatched successfully.")
    except APIError as e:
        return error_response(e.message, e.code, e.status)
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@reminders_bp.route('/reminders', methods=['GET'])
@require_workspace('transaction:read')
def list_reminders():
    invoice_id = request.args.get('invoice_id')
    try:
        reminders = ReminderService.get_reminders(g.workspace_id, invoice_id=invoice_id)
        return success_response(data={'reminders': reminders, 'count': len(reminders)})
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)
