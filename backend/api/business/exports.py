"""
DeadlineOS Business OS — Accountant Export Endpoints
====================================================
Deterministic CSV streams and ZIP accountant export archives.
"""

from flask import Blueprint, request, g, Response, send_file
from datetime import datetime, date
from utils.responses import success_response, error_response
from middleware.business_context import require_workspace
from services.business.export_service import ExportService
import io

exports_bp = Blueprint('biz_exports', __name__)


def parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except Exception:
        return None


@exports_bp.route('/exports/accountant-package', methods=['GET'])
@require_workspace('transaction:read')
def get_accountant_package():
    start_date = parse_date(request.args.get('start_date'))
    end_date = parse_date(request.args.get('end_date'))

    try:
        zip_bytes, filename = ExportService.generate_accountant_package(
            workspace_id=g.workspace_id,
            user_id=g.user_id,
            start_date=start_date,
            end_date=end_date,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return send_file(
            io.BytesIO(zip_bytes),
            mimetype='application/zip',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@exports_bp.route('/exports/invoices.csv', methods=['GET'])
@require_workspace('transaction:read')
def get_invoices_csv():
    start_date = parse_date(request.args.get('start_date'))
    end_date = parse_date(request.args.get('end_date'))
    try:
        csv_data = ExportService.export_invoices_csv(g.workspace_id, start_date, end_date)
        return Response(csv_data, mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=invoices_export.csv'})
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@exports_bp.route('/exports/transactions.csv', methods=['GET'])
@require_workspace('transaction:read')
def get_transactions_csv():
    start_date = parse_date(request.args.get('start_date'))
    end_date = parse_date(request.args.get('end_date'))
    try:
        csv_data = ExportService.export_transactions_csv(g.workspace_id, start_date, end_date)
        return Response(csv_data, mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=transactions_export.csv'})
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)


@exports_bp.route('/exports/allocations.csv', methods=['GET'])
@require_workspace('transaction:read')
def get_allocations_csv():
    start_date = parse_date(request.args.get('start_date'))
    end_date = parse_date(request.args.get('end_date'))
    try:
        csv_data = ExportService.export_allocations_csv(g.workspace_id, start_date, end_date)
        return Response(csv_data, mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=payment_allocations_export.csv'})
    except Exception as e:
        return error_response(str(e), "INTERNAL_ERROR", 500)
