"""
DeadlineOS Business OS — Voice-Assisted Operations Service (Phase C2.5)
========================================================================
Translates voice audio / speech-to-text transcripts into structured
operational candidates (stock adjustments, transfers, tasks, purchase requests).

CRITICAL ARCHITECTURAL INVARIANT: Zero-Bypass Staging Trust Boundary.
Voice transcriptions NEVER directly mutate physical stock or financial records.
All voice operations MUST stage into StagedExtraction (status='NEEDS_REVIEW')
awaiting explicit human verification and commit.
"""

import uuid
import re
from datetime import datetime, timezone, timedelta, date
from decimal import Decimal
from database.db import db
from models.business import (
    StagedExtraction,
    BusinessLocation,
    BusinessProduct,
    CommercialPartner,
    WorkspaceMember,
)
from services.business.audit_service import AuditService
from utils.errors import APIError


class VoiceOperationsService:
    """
    Intelligent voice intent and entity parser for business operations.
    """

    @staticmethod
    def process_voice_operation(
        workspace_id: str,
        actor_user_id: str,
        transcript: str,
        audio_duration_seconds: float = None,
        context_hints: dict = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> dict:
        """
        Parses voice transcript, extracts structured operational intent,
        matches workspace entities (products, locations, partners, members),
        and safely creates a StagedExtraction record in NEEDS_REVIEW status.
        """
        clean_text = (transcript or "").strip()
        if not clean_text:
            raise APIError("Voice transcript cannot be empty.", code="EMPTY_TRANSCRIPT", status=400)

        # 1. Classify intent & extract fields
        parsed_result = VoiceOperationsService._parse_transcript(workspace_id, clean_text, context_hints or {})

        candidate_type = parsed_result["candidate_type"]
        normalized_data = parsed_result["normalized_data"]
        confidence_score = parsed_result["confidence_score"]
        confidence_breakdown = parsed_result["confidence_breakdown"]

        # 2. Construct provenance metadata
        provenance = {
            "source_type": "VOICE_ASSISTED_OPERATIONS",
            "audio_duration_seconds": audio_duration_seconds,
            "raw_transcript": clean_text,
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "extracted_intent": candidate_type,
            "matched_entities": parsed_result.get("matched_entities", {})
        }

        # 3. Create StagedExtraction adhering to Zero-Bypass trust boundary
        staged = StagedExtraction(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            created_by_user_id=actor_user_id,
            source_channel="VOICE",
            candidate_type=candidate_type,
            status="NEEDS_REVIEW",
            raw_extracted_data={"transcript": clean_text, "raw_entities": parsed_result.get("raw_entities", {})},
            normalized_data=normalized_data,
            confidence_score=confidence_score,
            confidence_breakdown=confidence_breakdown,
            provenance_metadata=provenance,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        db.session.add(staged)
        db.session.commit()

        # 4. Forensic Audit Log
        AuditService.log_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action="VOICE_OPERATION_STAGED",
            entity_type="STAGED_EXTRACTION",
            entity_id=staged.id,
            after_state={
                "candidate_type": candidate_type,
                "confidence_score": confidence_score,
                "source_channel": "VOICE"
            },
            reason=f"Staged voice operation: {clean_text[:60]}",
            ip_address=ip_address,
            user_agent=user_agent
        )

        return {
            "staged_extraction": staged.serialize(),
            "intent_summary": {
                "candidate_type": candidate_type,
                "confidence_score": confidence_score,
                "extracted_fields": normalized_data,
                "raw_transcript": clean_text
            }
        }

    @staticmethod
    def get_voice_operations_history(
        workspace_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[list, int]:
        """
        Lists staged voice operations for the given workspace.
        """
        query = StagedExtraction.query.filter_by(
            workspace_id=workspace_id,
            source_channel="VOICE"
        ).order_by(StagedExtraction.created_at.desc())

        total = query.count()
        items = query.offset(offset).limit(limit).all()
        return [i.serialize() for i in items], total

    # ── Private Intent & Entity Extraction Engine ─────────────────────────────

    @staticmethod
    def _parse_transcript(workspace_id: str, text: str, hints: dict) -> dict:
        """
        Deterministic operational NLP matcher with entity resolver.
        """
        lower = text.lower()
        now = datetime.now(timezone.utc)

        # Lookup workspace context for entity resolution
        products = BusinessProduct.query.filter_by(workspace_id=workspace_id, status='ACTIVE').all()
        locations = BusinessLocation.query.filter_by(workspace_id=workspace_id, status='ACTIVE').all()
        partners = CommercialPartner.query.filter_by(workspace_id=workspace_id, status='ACTIVE').all()
        members = WorkspaceMember.query.filter_by(workspace_id=workspace_id, status='ACTIVE').all()

        matched_entities = {}
        matched_product = None
        matched_location = None
        matched_dest_location = None
        matched_partner = None

        # Resolve Product (match SKU or Name)
        for p in products:
            if p.sku and p.sku.lower() in lower:
                matched_product = p
                matched_entities["product"] = {"id": p.id, "sku": p.sku, "name": p.name}
                break
            elif p.name and p.name.lower() in lower:
                matched_product = p
                matched_entities["product"] = {"id": p.id, "sku": p.sku, "name": p.name}
                break

        # Resolve Location(s)
        for loc in locations:
            if loc.name and loc.name.lower() in lower:
                if not matched_location:
                    matched_location = loc
                    matched_entities["location"] = {"id": loc.id, "name": loc.name}
                else:
                    matched_dest_location = loc
                    matched_entities["destination_location"] = {"id": loc.id, "name": loc.name}

        # Resolve Partner
        for part in partners:
            if part.name and part.name.lower() in lower:
                matched_partner = part
                matched_entities["partner"] = {"id": part.id, "name": part.name}
                break

        # Extract numeric quantity
        qty_match = re.search(r'\b(\d+(?:\.\d+)?)\s*(?:units?|pcs?|items?|boxes?|packs?|kg|litres?)?\b', lower)
        extracted_qty = str(qty_match.group(1)) if qty_match else "1"

        # Extract cost / price if present
        cost_match = re.search(r'(?:costing|cost|price|at|@)\s*(?:rs\.?|inr|\$)?\s*(\d+(?:\.\d+)?)', lower)
        extracted_cost = str(cost_match.group(1)) if cost_match else (str(matched_product.cost_price) if matched_product else None)

        # ── Intent 1: Stock Transfer ──────────────────────────────────────────
        if any(w in lower for w in ["transfer", "move stock", "relocate"]):
            return {
                "candidate_type": "VOICE_STOCK_TRANSFER",
                "normalized_data": {
                    "product_id": matched_product.id if matched_product else None,
                    "product_name": matched_product.name if matched_product else None,
                    "source_location_id": matched_location.id if matched_location else None,
                    "source_location_name": matched_location.name if matched_location else None,
                    "destination_location_id": matched_dest_location.id if matched_dest_location else None,
                    "destination_location_name": matched_dest_location.name if matched_dest_location else None,
                    "quantity": extracted_qty,
                    "reason": text,
                    "transfer_date": now.date().isoformat()
                },
                "confidence_score": 90 if matched_product and matched_location else 75,
                "confidence_breakdown": {
                    "product_match": bool(matched_product),
                    "location_match": bool(matched_location),
                    "quantity_extracted": bool(qty_match)
                },
                "matched_entities": matched_entities
            }

        # ── Intent 2: Task Creation ───────────────────────────────────────────
        if any(w in lower for w in ["task", "assign", "inspect", "check warehouse", "todo", "follow up"]):
            # Priority detection
            priority = "MEDIUM"
            if any(w in lower for w in ["urgent", "critical", "emergency", "asap"]):
                priority = "URGENT"
            elif any(w in lower for w in ["high priority", "important", "high"]):
                priority = "HIGH"
            elif any(w in lower for w in ["low priority", "minor", "low"]):
                priority = "LOW"

            # Due date detection
            due = now.date() + timedelta(days=1)
            if "today" in lower:
                due = now.date()
            elif "tomorrow" in lower:
                due = now.date() + timedelta(days=1)
            elif "next week" in lower:
                due = now.date() + timedelta(days=7)

            clean_title = text
            for prefix in ["create task:", "task:", "create a task to", "task", "please"]:
                if lower.startswith(prefix):
                    clean_title = text[len(prefix):].strip()
                    break

            return {
                "candidate_type": "VOICE_TASK",
                "normalized_data": {
                    "title": clean_title[:120] if clean_title else "Voice Task",
                    "description": text,
                    "priority": priority,
                    "category": "INVENTORY" if matched_product or matched_location else "GENERAL",
                    "due_date": due.isoformat(),
                    "location_id": matched_location.id if matched_location else None,
                    "product_id": matched_product.id if matched_product else None
                },
                "confidence_score": 95 if len(text) > 10 else 80,
                "confidence_breakdown": {
                    "title_extracted": True,
                    "priority_detected": priority != "MEDIUM",
                    "due_date_calculated": True
                },
                "matched_entities": matched_entities
            }

        # ── Intent 3: Purchase Request Requisition ────────────────────────────
        if any(w in lower for w in ["purchase request", "reorder", "request order", "indent", "need to buy"]):
            return {
                "candidate_type": "VOICE_PURCHASE_REQUEST",
                "normalized_data": {
                    "product_id": matched_product.id if matched_product else None,
                    "product_name": matched_product.name if matched_product else None,
                    "quantity": extracted_qty,
                    "estimated_unit_cost": extracted_cost or "0.00",
                    "supplier_partner_id": matched_partner.id if matched_partner else (matched_product.preferred_supplier_partner_id if matched_product else None),
                    "destination_location_id": matched_location.id if matched_location else None,
                    "notes": text,
                    "required_by_date": (now.date() + timedelta(days=7)).isoformat()
                },
                "confidence_score": 90 if matched_product else 70,
                "confidence_breakdown": {
                    "product_match": bool(matched_product),
                    "quantity_extracted": bool(qty_match),
                    "supplier_match": bool(matched_partner)
                },
                "matched_entities": matched_entities
            }

        # ── Intent 4: Stock Movement / Inventory Adjustment (Default Operational)
        is_outgoing = any(w in lower for w in ["damaged", "scrapped", "removed", "shipped", "issued", "consumed", "sold", "out", "loss"])
        direction = "OUT" if is_outgoing else "IN"
        movement_type = "DAMAGED" if "damaged" in lower else ("SALE" if "sold" in lower else ("SCRAP" if "scrap" in lower else ("PURCHASE_RECEIVED" if "received" in lower else "MANUAL_ADJUSTMENT")))

        return {
            "candidate_type": "VOICE_INVENTORY_ADJUSTMENT",
            "normalized_data": {
                "product_id": matched_product.id if matched_product else None,
                "product_name": matched_product.name if matched_product else None,
                "location_id": matched_location.id if matched_location else None,
                "location_name": matched_location.name if matched_location else None,
                "direction": direction,
                "movement_type": movement_type,
                "quantity": extracted_qty,
                "unit_cost": extracted_cost,
                "reason": text,
                "movement_date": now.date().isoformat()
            },
            "confidence_score": 92 if matched_product and matched_location else (80 if matched_product else 65),
            "confidence_breakdown": {
                "product_match": bool(matched_product),
                "location_match": bool(matched_location),
                "direction_detected": True,
                "quantity_extracted": bool(qty_match)
            },
            "matched_entities": matched_entities
        }
