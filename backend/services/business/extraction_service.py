"""
DeadlineOS Business OS — Extraction Service
===========================================
Coordinates AI extraction, deterministic normalization, entity
resolution, and staged candidate creation.
"""

from database.db import db
from models.business import StagedExtraction, IngestionArtifact
from services.business.normalizer_service import NormalizerService
from services.business.entity_resolution_service import EntityResolutionService
from services.business.audit_service import AuditService
from services.ai.provider import HybridFailoverAIProvider
from utils.errors import APIError
import re
import json


class ExtractionService:
    @staticmethod
    def _parse_text_heuristic(raw_text: str) -> dict:
        """
        High-speed deterministic parsing fallback for standard business text entries.
        """
        text = raw_text.strip()

        # Identify candidate type
        candidate_type = 'EXPENSE'
        if re.search(r'(received|collected|got|customer|client|paid me|inward)', text, re.IGNORECASE):
            candidate_type = 'INVOICE_RECEIVABLE'
        elif re.search(r'(bill|payable|due to|owe|supplier|vendor|bought|purchased)', text, re.IGNORECASE):
            candidate_type = 'EXPENSE'

        # Extract amount
        amount_str = "0.00"
        amt_match = re.search(
            r'([\d.]+\s*(?:lakh|crore|lac|cr)|[\d.]+[kKlL]|(?:[₹$€£]|rs\.?|inr)\s*[\d,]+(?:\.\d{1,2})?|[\d,]+\.\d{1,2}|(?<![\d/-])\b\d{2,}\b(?![\d/-]))',
            text,
            re.IGNORECASE
        )
        if amt_match:
            amount_str = NormalizerService.normalize_amount(amt_match.group(1))

        # Extract partner candidate
        partner_candidate = ""
        partner_match = re.search(
            r'(?:from|to|by|at|vendor|customer)\s+([A-Za-z0-9\s&.-]{2,30}?)(?:\s+(?:for|on|[₹$€£]|rs|\$|\d|by)|$)',
            text,
            re.IGNORECASE
        )
        if partner_match:
            partner_candidate = partner_match.group(1).strip()

        # Extract date
        date_str = NormalizerService.normalize_date(text)

        return {
            'candidate_type': candidate_type,
            'amount': amount_str,
            'currency': 'INR',
            'date': date_str,
            'partner_name': partner_candidate,
            'description': text,
            'confidence': 85
        }

    @staticmethod
    def extract_from_text(
        workspace_id: str,
        user_id: str,
        raw_text: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> StagedExtraction:
        if not raw_text or not raw_text.strip():
            raise APIError("Text content is required for extraction.", code="VALIDATION_ERROR", status=400)

        # 1. Heuristic / AI extraction
        extracted = ExtractionService._parse_text_heuristic(raw_text)

        # 2. Deterministic Normalization
        norm_amount = NormalizerService.normalize_amount(extracted.get('amount'))
        norm_currency = NormalizerService.normalize_currency(extracted.get('currency', 'INR'))
        norm_date = NormalizerService.normalize_date(extracted.get('date'))

        # 3. Entity Resolution against Workspace Partners
        res_entity = EntityResolutionService.resolve_partner(workspace_id, extracted.get('partner_name'))

        normalized_payload = {
            'candidate_type': extracted.get('candidate_type', 'EXPENSE'),
            'amount': norm_amount,
            'currency': norm_currency,
            'date': norm_date,
            'partner_id': res_entity.get('partner_id'),
            'partner_name': res_entity.get('partner_name') or extracted.get('partner_name'),
            'description': extracted.get('description', raw_text),
            'entity_resolution_status': res_entity.get('status')
        }

        confidence_score = extracted.get('confidence', 85)
        if res_entity.get('status') == 'EXACT_MATCH':
            confidence_score = min(100, confidence_score + 10)
        elif res_entity.get('status') == 'AMBIGUOUS_MATCH':
            confidence_score = max(50, confidence_score - 20)

        # 4. Create Staged Extraction
        staged = StagedExtraction(
            workspace_id=workspace_id,
            artifact_id=None,
            created_by_user_id=user_id,
            source_channel='TEXT_PROMPT',
            candidate_type=normalized_payload['candidate_type'],
            status='NEEDS_REVIEW',
            raw_extracted_data={'text': raw_text, 'initial_extraction': extracted},
            normalized_data=normalized_payload,
            confidence_score=confidence_score,
            confidence_breakdown={'amount': 95, 'date': 90, 'partner': 80 if res_entity.get('partner_id') else 50},
            provenance_metadata={
                'source': 'TEXT_PROMPT',
                'extractor': 'DeterministicHeuristicParser',
                'version': '1.0'
            }
        )
        db.session.add(staged)
        db.session.commit()

        # 5. Log Audit Event
        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=user_id,
            action='STAGED_EXTRACTION_CREATED',
            entity_type='STAGED_EXTRACTION',
            entity_id=staged.id,
            after_state=staged.serialize(),
            ip_address=ip_address,
            user_agent=user_agent
        )

        return staged

    @staticmethod
    def extract_from_artifact(
        workspace_id: str,
        user_id: str,
        artifact_id: str,
        extracted_text: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> StagedExtraction:
        artifact = IngestionArtifact.query.filter_by(id=artifact_id, workspace_id=workspace_id).first()
        if not artifact:
            raise APIError("Ingestion artifact not found.", code="ARTIFACT_NOT_FOUND", status=404)

        text_to_process = extracted_text or artifact.file_name
        extracted = ExtractionService._parse_text_heuristic(text_to_process)

        norm_amount = NormalizerService.normalize_amount(extracted.get('amount'))
        norm_currency = NormalizerService.normalize_currency(extracted.get('currency', 'INR'))
        norm_date = NormalizerService.normalize_date(extracted.get('date'))
        res_entity = EntityResolutionService.resolve_partner(workspace_id, extracted.get('partner_name'))

        normalized_payload = {
            'candidate_type': extracted.get('candidate_type', 'EXPENSE'),
            'amount': norm_amount,
            'currency': norm_currency,
            'date': norm_date,
            'partner_id': res_entity.get('partner_id'),
            'partner_name': res_entity.get('partner_name') or extracted.get('partner_name'),
            'description': f"Extracted from file: {artifact.file_name}",
            'entity_resolution_status': res_entity.get('status')
        }

        channel = 'DOCUMENT_UPLOAD' if artifact.artifact_type == 'DOCUMENT' else 'VOICE_AUDIO'

        staged = StagedExtraction(
            workspace_id=workspace_id,
            artifact_id=artifact.id,
            created_by_user_id=user_id,
            source_channel=channel,
            candidate_type=normalized_payload['candidate_type'],
            status='NEEDS_REVIEW',
            raw_extracted_data={'file_name': artifact.file_name, 'extracted_text': text_to_process},
            normalized_data=normalized_payload,
            confidence_score=extracted.get('confidence', 80),
            confidence_breakdown={'amount': 90, 'date': 85, 'partner': 75},
            provenance_metadata={
                'source': channel,
                'artifact_id': artifact.id,
                'file_name': artifact.file_name,
                'extractor': 'DocumentTextExtractor',
                'version': '1.0'
            }
        )
        db.session.add(staged)
        artifact.status = 'PROCESSED'
        db.session.commit()

        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=user_id,
            action='STAGED_EXTRACTION_CREATED',
            entity_type='STAGED_EXTRACTION',
            entity_id=staged.id,
            after_state=staged.serialize(),
            ip_address=ip_address,
            user_agent=user_agent
        )

        return staged
