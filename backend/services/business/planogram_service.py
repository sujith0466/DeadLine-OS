"""
DeadlineOS Business OS — Planogram Verification Service (Phase C4.2)
====================================================================
Audits visual detections against configured physical shelf zones:
  - Facing deficit detection
  - Empty shelf and out-of-stock anomaly classification
  - Misplaced product detection
  - Damaged packaging identification
  - System stock baseline lookup & discrepancy calculation
"""

from decimal import Decimal
from typing import Dict, Any, Optional, List
from database.db import db
from models.business.shelf_zone import BusinessShelfZone
from models.business.product import BusinessProduct
from services.business.inventory_service import InventoryService


class PlanogramService:
    @staticmethod
    def audit_shelf_zone(
        workspace_id: str,
        location_id: str,
        shelf_zone: Optional[BusinessShelfZone],
        detected_items: List[Dict[str, Any]],
        matched_product_id: Optional[str],
        visual_count: Decimal,
        visual_facings: int
    ) -> Dict[str, Any]:
        """
        Compares visual extraction detections against shelf zone planogram configuration.
        Returns anomaly classification, compliance flags, and quantity discrepancy.
        """
        visual_count_dec = Decimal(str(visual_count or 0)).quantize(Decimal('0.01'))
        
        # 1. Look up live system stock at capture time for the target product
        target_product_id = matched_product_id or (shelf_zone.assigned_product_id if shelf_zone else None)
        system_stock = Decimal('0.00')
        if target_product_id and location_id:
            system_stock = InventoryService.get_available_stock(
                workspace_id=workspace_id,
                product_id=target_product_id,
                location_id=location_id
            )

        discrepancy_quantity = (visual_count_dec - system_stock).quantize(Decimal('0.01'))

        # 2. Check damaged packaging
        has_damaged = any(
            str(item.get('condition', '')).upper() == 'DAMAGED' 
            for item in (detected_items or [])
        )
        if has_damaged:
            return {
                'anomaly_detected': True,
                'anomaly_type': 'DAMAGED_PACKAGING',
                'system_stock_at_capture': system_stock,
                'discrepancy_quantity': discrepancy_quantity,
                'par_level_compliance': False,
                'capacity_utilization_pct': PlanogramService._calc_utilization(visual_count_dec, shelf_zone),
                'facing_compliance': False,
                'details': {'reason': 'Detected one or more units with damaged packaging'}
            }

        # 3. Zone-specific checks if a shelf zone fixture is bound
        if shelf_zone:
            expected_product_id = shelf_zone.assigned_product_id
            target_par = shelf_zone.reorder_threshold or Decimal('0.00')
            target_facings = shelf_zone.target_facings or 1

            # Misplaced Product check
            if expected_product_id and matched_product_id and matched_product_id != expected_product_id:
                return {
                    'anomaly_detected': True,
                    'anomaly_type': 'MISPLACED_PRODUCT',
                    'system_stock_at_capture': system_stock,
                    'discrepancy_quantity': discrepancy_quantity,
                    'par_level_compliance': False,
                    'capacity_utilization_pct': PlanogramService._calc_utilization(visual_count_dec, shelf_zone),
                    'facing_compliance': False,
                    'details': {
                        'expected_product_id': expected_product_id,
                        'detected_product_id': matched_product_id,
                        'reason': 'Detected product differs from assigned shelf planogram SKU'
                    }
                }

            # Empty Shelf check
            if visual_count_dec == Decimal('0.00'):
                anomaly_type = 'OUT_OF_STOCK' if system_stock > Decimal('0.00') else 'EMPTY_SHELF'
                return {
                    'anomaly_detected': True,
                    'anomaly_type': anomaly_type,
                    'system_stock_at_capture': system_stock,
                    'discrepancy_quantity': discrepancy_quantity,
                    'par_level_compliance': False,
                    'capacity_utilization_pct': Decimal('0.00'),
                    'facing_compliance': False,
                    'details': {
                        'reason': f"Shelf zone is empty (visual count is 0, system stock is {system_stock})"
                    }
                }

            # Facing Deficit check
            facing_compliance = True
            if target_facings > 0 and visual_facings < target_facings:
                facing_compliance = False
                return {
                    'anomaly_detected': True,
                    'anomaly_type': 'FACING_DEFICIT',
                    'system_stock_at_capture': system_stock,
                    'discrepancy_quantity': discrepancy_quantity,
                    'par_level_compliance': visual_count_dec >= target_par if target_par > 0 else True,
                    'capacity_utilization_pct': PlanogramService._calc_utilization(visual_count_dec, shelf_zone),
                    'facing_compliance': False,
                    'details': {
                        'target_facings': target_facings,
                        'visual_facings': visual_facings,
                        'reason': f"Front facings ({visual_facings}) below target facings ({target_facings})"
                    }
                }

            # Normal Shelf Condition
            return {
                'anomaly_detected': False,
                'anomaly_type': 'NONE',
                'system_stock_at_capture': system_stock,
                'discrepancy_quantity': discrepancy_quantity,
                'par_level_compliance': visual_count_dec >= target_par if target_par > 0 else True,
                'capacity_utilization_pct': PlanogramService._calc_utilization(visual_count_dec, shelf_zone),
                'facing_compliance': facing_compliance,
                'details': {'reason': 'Shelf zone matches planogram specifications'}
            }

        # 4. Unbound shelf zone fallback
        if visual_count_dec > Decimal('0.00') and not matched_product_id:
            return {
                'anomaly_detected': True,
                'anomaly_type': 'UNKNOWN_OBJECT',
                'system_stock_at_capture': system_stock,
                'discrepancy_quantity': discrepancy_quantity,
                'par_level_compliance': True,
                'capacity_utilization_pct': Decimal('0.00'),
                'facing_compliance': True,
                'details': {'reason': 'Unassigned visual objects detected on untracked fixture'}
            }

        return {
            'anomaly_detected': False,
            'anomaly_type': 'NONE',
            'system_stock_at_capture': system_stock,
            'discrepancy_quantity': discrepancy_quantity,
            'par_level_compliance': True,
            'capacity_utilization_pct': Decimal('0.00'),
            'facing_compliance': True,
            'details': {'reason': 'Visual observation verified without assigned shelf zone'}
        }

    @staticmethod
    def _calc_utilization(count: Decimal, shelf_zone: Optional[BusinessShelfZone]) -> Decimal:
        if not shelf_zone or not shelf_zone.expected_capacity or shelf_zone.expected_capacity <= Decimal('0.00'):
            return Decimal('0.00')
        pct = (count / shelf_zone.expected_capacity) * Decimal('100.00')
        return min(pct, Decimal('100.00')).quantize(Decimal('0.01'))
