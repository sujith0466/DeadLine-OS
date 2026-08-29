"""
DeadlineOS Business OS — Entity Resolution Service
==================================================
Matches counterparty names against the workspace CommercialPartner registry.
Strictly workspace-scoped; flags ambiguous matches for human selection.
"""

from models.business import CommercialPartner


class EntityResolutionService:
    @staticmethod
    def resolve_partner(workspace_id: str, raw_partner_name: str) -> dict:
        if not raw_partner_name or not str(raw_partner_name).strip():
            return {
                'status': 'NO_PARTNER_SPECIFIED',
                'partner_id': None,
                'partner_name': None,
                'candidates': []
            }

        name_query = str(raw_partner_name).strip()

        # 1. Exact Match (case-insensitive)
        exact_match = CommercialPartner.query.filter(
            CommercialPartner.workspace_id == workspace_id,
            CommercialPartner.status == 'ACTIVE',
            CommercialPartner.name.ilike(name_query)
        ).first()

        if exact_match:
            return {
                'status': 'EXACT_MATCH',
                'partner_id': exact_match.id,
                'partner_name': exact_match.name,
                'candidates': [exact_match.serialize()]
            }

        # 2. Fuzzy / Substring Matches
        fuzzy_matches = CommercialPartner.query.filter(
            CommercialPartner.workspace_id == workspace_id,
            CommercialPartner.status == 'ACTIVE',
            CommercialPartner.name.ilike(f"%{name_query}%")
        ).limit(5).all()

        if len(fuzzy_matches) == 1:
            return {
                'status': 'HIGH_CONFIDENCE_MATCH',
                'partner_id': fuzzy_matches[0].id,
                'partner_name': fuzzy_matches[0].name,
                'candidates': [p.serialize() for p in fuzzy_matches]
            }
        elif len(fuzzy_matches) > 1:
            return {
                'status': 'AMBIGUOUS_MATCH',
                'partner_id': None,
                'partner_name': name_query,
                'candidates': [p.serialize() for p in fuzzy_matches]
            }

        # 3. No match found
        return {
            'status': 'NO_MATCH',
            'partner_id': None,
            'partner_name': name_query,
            'candidates': []
        }
