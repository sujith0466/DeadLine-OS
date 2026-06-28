import logging
import io
from flask import Blueprint, send_file, current_app, g
from services.analytics_service import AnalyticsService
from utils.auth import require_auth
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

logger = logging.getLogger(__name__)
reports_bp = Blueprint("reports", __name__)

@reports_bp.route("/reports/download", methods=["GET"])
@require_auth
def download_report():
    """Generates an Executive Intelligence PDF Report using ReportLab."""
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = styles['Heading1']
        title_style.alignment = 1 # Center
        h2_style = styles['Heading2']
        normal_style = styles['Normal']
        
        elements = []
        
        # Header
        elements.append(Paragraph("DeadlineOS Executive Intelligence Report", title_style))
        elements.append(Spacer(1, 12))
        
        # Briefing
        briefing = AnalyticsService.generate_chief_of_staff_briefing(g.user_id)
        elements.append(Paragraph("AI Chief-of-Staff Briefing", h2_style))
        elements.append(Paragraph(briefing, normal_style))
        elements.append(Spacer(1, 24))
        
        # KPIs
        overview = AnalyticsService.get_overview(g.user_id)
        elements.append(Paragraph("Key Performance Indicators", h2_style))
        
        data = [
            ['Metric', 'Value'],
            ['Productivity Score', f"{overview.get('productivity_score', 0)}%"],
            ['Completion Rate', f"{overview.get('completion_rate', 0)}%"],
            ['Future Risk Forecast', overview.get('future_risk_forecast', 'Unknown')],
            ['AI Confidence', f"{overview.get('ai_confidence_score', 0)}%"]
        ]
        
        t = Table(data, colWidths=[200, 100])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#0f172a')),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#334155'))
        ]))
        elements.append(t)
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name='DeadlineOS_Intelligence_Report.pdf',
            mimetype='application/pdf'
        )
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        return {"error": "Report generation failed", "status": 500}, 500
