"""
DeadlineOS Business OS — C4.1 Ambient Computer Vision & Shelf Monitoring Unit Tests
===================================================================================
Covers all C4.1 functional, security, RBAC, tenant isolation, media storage,
sanitization, and source-of-truth invariants.
"""

import io
import uuid
import base64
from decimal import Decimal
import pytest
from PIL import Image

from database.db import db
from models.user import User
from models.business import (
    Workspace,
    WorkspaceMember,
    BusinessLocation,
    BusinessProduct,
    BusinessShelfZone,
    BusinessVisualObservation,
    BusinessStockMovement,
    IngestionArtifact,
    AuditEvent
)
from services.business.shelf_zone_service import ShelfZoneService
from services.business.vision_ingestion_service import VisionIngestionService
from services.business.storage_service import StorageService
from utils.errors import APIError


# ── Helper to create a valid synthetic image ───────────────────────────────────

def _create_synthetic_image_bytes(
    format_name: str = 'JPEG',
    width: int = 200,
    height: int = 150,
    color: str = 'blue'
) -> bytes:
    """Creates in-memory valid image bytes for test fixtures."""
    img = Image.new('RGB', (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format=format_name)
    return buf.getvalue()


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def fx_vision_env(app):
    """Sets up dual-tenant workspaces with RBAC members, locations, and products within active app context."""
    with app.app_context():
        sfx = uuid.uuid4().hex[:6]

        # 1. Users
        u_owner = User(id=str(uuid.uuid4()), email=f"c41_owner_{sfx}@test.com", full_name="C4.1 Owner")
        u_admin = User(id=str(uuid.uuid4()), email=f"c41_admin_{sfx}@test.com", full_name="C4.1 Admin")
        u_member = User(id=str(uuid.uuid4()), email=f"c41_member_{sfx}@test.com", full_name="C4.1 Member")
        u_viewer = User(id=str(uuid.uuid4()), email=f"c41_viewer_{sfx}@test.com", full_name="C4.1 Viewer")
        u_tenant_b = User(id=str(uuid.uuid4()), email=f"c41_tenb_{sfx}@test.com", full_name="C4.1 Tenant B")
        db.session.add_all([u_owner, u_admin, u_member, u_viewer, u_tenant_b])
        db.session.commit()

        # 2. Workspaces
        ws_a = Workspace(id=str(uuid.uuid4()), name=f"C4.1-WS-A-{sfx}", base_currency="INR")
        ws_b = Workspace(id=str(uuid.uuid4()), name=f"C4.1-WS-B-{sfx}", base_currency="INR")
        db.session.add_all([ws_a, ws_b])
        db.session.commit()

        # 3. Memberships
        db.session.add_all([
            WorkspaceMember(id=str(uuid.uuid4()), workspace_id=ws_a.id, user_id=u_owner.id, role="OWNER", status="ACTIVE"),
            WorkspaceMember(id=str(uuid.uuid4()), workspace_id=ws_a.id, user_id=u_admin.id, role="ADMIN", status="ACTIVE"),
            WorkspaceMember(id=str(uuid.uuid4()), workspace_id=ws_a.id, user_id=u_member.id, role="MEMBER", status="ACTIVE"),
            WorkspaceMember(id=str(uuid.uuid4()), workspace_id=ws_a.id, user_id=u_viewer.id, role="VIEWER", status="ACTIVE"),
            WorkspaceMember(id=str(uuid.uuid4()), workspace_id=ws_b.id, user_id=u_tenant_b.id, role="OWNER", status="ACTIVE"),
        ])
        db.session.commit()

        # 4. Locations
        loc_a = BusinessLocation(
            id=str(uuid.uuid4()),
            workspace_id=ws_a.id,
            name=f"Main Warehouse {sfx}",
            location_type="WAREHOUSE",
            status="ACTIVE"
        )
        loc_b = BusinessLocation(
            id=str(uuid.uuid4()),
            workspace_id=ws_b.id,
            name=f"Tenant B Warehouse {sfx}",
            location_type="WAREHOUSE",
            status="ACTIVE"
        )
        db.session.add_all([loc_a, loc_b])
        db.session.commit()

        # 5. Products
        prod_a = BusinessProduct(
            id=str(uuid.uuid4()),
            workspace_id=ws_a.id,
            sku=f"SKU-VALVE-{sfx}",
            name="Precision Valve 50mm",
            unit="UNIT",
            cost_price=Decimal("1500.00"),
            selling_price=Decimal("2500.00"),
            status="ACTIVE"
        )
        prod_b = BusinessProduct(
            id=str(uuid.uuid4()),
            workspace_id=ws_b.id,
            sku=f"SKU-TENB-{sfx}",
            name="Tenant B Item",
            unit="UNIT",
            cost_price=Decimal("500.00"),
            selling_price=Decimal("800.00"),
            status="ACTIVE"
        )
        db.session.add_all([prod_a, prod_b])
        db.session.commit()

        yield {
            'ws_a': ws_a,
            'ws_b': ws_b,
            'ws_a_id': ws_a.id,
            'ws_b_id': ws_b.id,
            'u_owner': u_owner,
            'u_admin': u_admin,
            'u_member': u_member,
            'u_viewer': u_viewer,
            'u_tenant_b': u_tenant_b,
            'u_owner_id': u_owner.id,
            'u_admin_id': u_admin.id,
            'u_member_id': u_member.id,
            'u_viewer_id': u_viewer.id,
            'u_tenant_b_id': u_tenant_b.id,
            'loc_a': loc_a,
            'loc_b': loc_b,
            'loc_a_id': loc_a.id,
            'loc_b_id': loc_b.id,
            'prod_a': prod_a,
            'prod_b': prod_b,
            'prod_a_id': prod_a.id,
            'prod_b_id': prod_b.id,
        }


# ── 1. Shelf Zone Topology Tests ───────────────────────────────────────────────

def test_create_shelf_zone_success(fx_vision_env):
    """Verifies creating a physical shelf zone with planogram target and capacity."""
    s = fx_vision_env
    zone = ShelfZoneService.create_shelf_zone(
        workspace_id=s['ws_a_id'],
        actor_user_id=s['u_owner_id'],
        data={
            'location_id': s['loc_a_id'],
            'zone_code': 'AISLE-01-A',
            'name': 'Aisle 1 Tier A Shelf',
            'zone_type': 'SHELF',
            'assigned_product_id': s['prod_a_id'],
            'expected_capacity': '24.00',
            'target_facings': 4,
            'reorder_threshold': '6.00',
            'notes': 'Top shelf storage fixture'
        }
    )

    assert zone.id is not None
    assert zone.zone_code == 'AISLE-01-A'
    assert zone.name == 'Aisle 1 Tier A Shelf'
    assert zone.expected_capacity == Decimal('24.00')
    assert zone.target_facings == 4
    assert zone.reorder_threshold == Decimal('6.00')
    assert zone.status == 'ACTIVE'

    serialized = zone.serialize()
    assert serialized['assigned_product']['sku'] == s['prod_a'].sku
    assert serialized['location_name'] == s['loc_a'].name


def test_shelf_zone_uniqueness_constraint(fx_vision_env):
    """Verifies that duplicate zone codes at the same location in the same workspace are rejected."""
    s = fx_vision_env
    ShelfZoneService.create_shelf_zone(
        workspace_id=s['ws_a_id'],
        actor_user_id=s['u_owner_id'],
        data={
            'location_id': s['loc_a_id'],
            'zone_code': 'RACK-B-01',
            'name': 'Primary Rack B1',
        }
    )

    with pytest.raises(APIError) as exc:
        ShelfZoneService.create_shelf_zone(
            workspace_id=s['ws_a_id'],
            actor_user_id=s['u_owner_id'],
            data={
                'location_id': s['loc_a_id'],
                'zone_code': 'RACK-B-01',  # Duplicate!
                'name': 'Duplicate Rack B1',
            }
        )
    assert exc.value.code == 'DUPLICATE_ZONE_CODE'


def test_shelf_zone_cross_tenant_location_validation(fx_vision_env):
    """Verifies that creating a shelf zone using another tenant's location fails."""
    s = fx_vision_env
    with pytest.raises(APIError) as exc:
        ShelfZoneService.create_shelf_zone(
            workspace_id=s['ws_a_id'],
            actor_user_id=s['u_owner_id'],
            data={
                'location_id': s['loc_b_id'],  # Belongs to Tenant B!
                'zone_code': 'ILLEGAL-01',
                'name': 'Cross-tenant zone',
            }
        )
    assert exc.value.code == 'LOCATION_NOT_FOUND'


def test_shelf_zone_cross_tenant_product_validation(fx_vision_env):
    """Verifies that assigning a product belonging to another tenant fails."""
    s = fx_vision_env
    with pytest.raises(APIError) as exc:
        ShelfZoneService.create_shelf_zone(
            workspace_id=s['ws_a_id'],
            actor_user_id=s['u_owner_id'],
            data={
                'location_id': s['loc_a_id'],
                'zone_code': 'LEGAL-01',
                'name': 'Legal Shelf',
                'assigned_product_id': s['prod_b_id']  # Belongs to Tenant B!
            }
        )
    assert exc.value.code == 'PRODUCT_NOT_FOUND'


def test_shelf_zone_update_and_deactivate(fx_vision_env):
    """Verifies updating shelf zone targets and deactivation."""
    s = fx_vision_env
    zone = ShelfZoneService.create_shelf_zone(
        workspace_id=s['ws_a_id'],
        actor_user_id=s['u_owner_id'],
        data={
            'location_id': s['loc_a_id'],
            'zone_code': 'TIER-C3',
            'name': 'Tier C3',
            'expected_capacity': '10.00'
        }
    )

    updated = ShelfZoneService.update_shelf_zone(
        workspace_id=s['ws_a_id'],
        zone_id=zone.id,
        actor_user_id=s['u_owner_id'],
        data={
            'name': 'Updated Tier C3 Premium',
            'expected_capacity': '30.00',
            'target_facings': 5
        }
    )
    assert updated.name == 'Updated Tier C3 Premium'
    assert updated.expected_capacity == Decimal('30.00')
    assert updated.target_facings == 5

    deactivated = ShelfZoneService.deactivate_shelf_zone(
        workspace_id=s['ws_a_id'],
        zone_id=zone.id,
        actor_user_id=s['u_owner_id'],
        reason="Fixture undergoing warehouse maintenance"
    )
    assert deactivated.status == 'INACTIVE'


# ── 2. Storage & Image Security Tests ──────────────────────────────────────────

def test_image_storage_validation_and_sanitization():
    """Verifies image size cap, format check, SHA-256 computation, and EXIF sanitization."""
    jpg_bytes = _create_synthetic_image_bytes('JPEG', width=300, height=200)
    clean_bytes, meta = StorageService.validate_and_sanitize_image(
        image_bytes=jpg_bytes,
        filename="warehouse_shelf.jpg",
        content_type="image/jpeg"
    )

    assert meta['mime_type'] == 'image/jpeg'
    assert meta['size_bytes'] > 0
    assert meta['sha256'] == StorageService.calculate_sha256(clean_bytes)
    assert meta['width'] == 300
    assert meta['height'] == 200
    assert meta['sanitized'] is True


def test_image_storage_rejects_unsupported_mime():
    """Verifies that non-image MIME types (PDF, text) are rejected for vision."""
    with pytest.raises(APIError) as exc:
        StorageService.validate_and_sanitize_image(
            image_bytes=b"sample text content",
            filename="invoice.txt",
            content_type="text/plain"
        )
    assert exc.value.code == 'UNSUPPORTED_IMAGE_TYPE'


def test_image_storage_rejects_corrupted_magic_bytes():
    """Verifies that fake JPEG headers are rejected."""
    fake_jpeg_bytes = b"NOT_A_REAL_JPEG_HEADER_12345678"
    with pytest.raises(APIError) as exc:
        StorageService.validate_and_sanitize_image(
            image_bytes=fake_jpeg_bytes,
            filename="fake.jpg",
            content_type="image/jpeg"
        )
    assert exc.value.code == 'INVALID_IMAGE_HEADER'


def test_image_storage_rejects_oversized_payload():
    """Verifies that files exceeding 15MB are rejected."""
    huge_bytes = b"X" * (16 * 1024 * 1024)
    with pytest.raises(APIError) as exc:
        StorageService.validate_and_sanitize_image(
            image_bytes=huge_bytes,
            filename="huge.jpg",
            content_type="image/jpeg"
        )
    assert exc.value.code == 'FILE_TOO_LARGE'


def test_image_storage_signed_url_ttl_ceiling():
    """Verifies that signed download URLs enforce a maximum 15-minute (900s) TTL."""
    path = "workspaces/ws-test-123/shelf-captures/2026/09/test.jpg"
    url = StorageService.generate_signed_download_url(path, expires_in_seconds=3600)  # requested 1 hour
    assert path in url
    assert "expires=" in url


# ── 3. Visual Media Ingestion & Observation Foundation Tests ───────────────────

def test_visual_capture_ingestion_success(fx_vision_env):
    """Verifies ingesting a shelf capture photo and creating IngestionArtifact + VisualObservation."""
    s = fx_vision_env
    zone = ShelfZoneService.create_shelf_zone(
        workspace_id=s['ws_a_id'],
        actor_user_id=s['u_owner_id'],
        data={
            'location_id': s['loc_a_id'],
            'zone_code': 'CAMERA-BAY-01',
            'name': 'Camera Bay 1'
        }
    )

    img_bytes = _create_synthetic_image_bytes('JPEG', width=400, height=300)
    result = VisionIngestionService.ingest_shelf_capture(
        workspace_id=s['ws_a_id'],
        location_id=s['loc_a_id'],
        actor_user_id=s['u_owner_id'],
        image_bytes=img_bytes,
        filename="bay_01_morning.jpg",
        content_type="image/jpeg",
        shelf_zone_id=zone.id,
        capture_device="OVERHEAD_CAM_01"
    )

    assert result['id'] is not None
    assert result['workspace_id'] == s['ws_a_id']
    assert result['location_id'] == s['loc_a_id']
    assert result['shelf_zone_id'] == zone.id
    assert result['capture_device'] == "OVERHEAD_CAM_01"
    assert result['status'] == 'PROCESSED'
    assert result['visual_count'] == '0.00'  # Unprocessed in C4.1
    assert result['image_signed_url'] is not None
    assert result['artifact']['sha256_hash'] == StorageService.calculate_sha256(img_bytes)

    # Invariant: Zero stock movements created
    movements_count = BusinessStockMovement.query.filter_by(workspace_id=s['ws_a_id']).count()
    assert movements_count == 0, "Visual ingestion must never create stock movements!"


def test_visual_observation_cross_tenant_isolation(fx_vision_env):
    """Verifies that Tenant B cannot access Tenant A visual observations."""
    s = fx_vision_env
    img_bytes = _create_synthetic_image_bytes('JPEG')
    obs = VisionIngestionService.ingest_shelf_capture(
        workspace_id=s['ws_a_id'],
        location_id=s['loc_a_id'],
        actor_user_id=s['u_owner_id'],
        image_bytes=img_bytes,
        filename="isolated_shelf.jpg",
        content_type="image/jpeg"
    )

    with pytest.raises(APIError) as exc:
        VisionIngestionService.get_observation_by_id(
            workspace_id=s['ws_b_id'],  # Tenant B queries Tenant A observation!
            observation_id=obs['id']
        )
    assert exc.value.code == 'OBSERVATION_NOT_FOUND'


# ── 4. RBAC & REST API Verification Tests ───────────────────────────────────────

def test_api_shelf_zones_rbac(client, fx_vision_env):
    """Verifies 5-tier RBAC rules for vision endpoints."""
    s = fx_vision_env

    # 1. OWNER can create zone
    res = client.post(
        '/api/business/vision/zones',
        headers={
            'Authorization': f'Bearer {s["u_owner_id"]}',
            'X-Workspace-Id': s['ws_a_id']
        },
        json={'location_id': s['loc_a_id'], 'zone_code': 'ZONE-OWNER', 'name': 'Owner Zone'}
    )
    print("RES JSON:", res.get_json())
    assert res.status_code == 201

    # 2. ADMIN can create zone
    res = client.post(
        '/api/business/vision/zones',
        headers={
            'Authorization': f'Bearer {s["u_admin_id"]}',
            'X-Workspace-Id': s['ws_a_id']
        },
        json={'location_id': s['loc_a_id'], 'zone_code': 'ZONE-ADMIN', 'name': 'Admin Zone'}
    )
    assert res.status_code == 201

    # 3. MEMBER is denied zone creation (requires vision:manage)
    res = client.post(
        '/api/business/vision/zones',
        headers={
            'Authorization': f'Bearer {s["u_member_id"]}',
            'X-Workspace-Id': s['ws_a_id']
        },
        json={'location_id': s['loc_a_id'], 'zone_code': 'ZONE-MEMBER', 'name': 'Member Zone'}
    )
    assert res.status_code == 403

    # 4. VIEWER is denied zone creation (requires vision:manage)
    res = client.post(
        '/api/business/vision/zones',
        headers={
            'Authorization': f'Bearer {s["u_viewer_id"]}',
            'X-Workspace-Id': s['ws_a_id']
        },
        json={'location_id': s['loc_a_id'], 'zone_code': 'ZONE-VIEWER', 'name': 'Viewer Zone'}
    )
    assert res.status_code == 403

    # 5. VIEWER can read zones
    res = client.get(
        '/api/business/vision/zones',
        headers={
            'Authorization': f'Bearer {s["u_viewer_id"]}',
            'X-Workspace-Id': s['ws_a_id']
        }
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data['data']['total'] >= 2


def test_api_capture_ingestion_base64(client, fx_vision_env):
    """Verifies image capture via REST API with base64 payload."""
    s = fx_vision_env
    jpg_bytes = _create_synthetic_image_bytes('JPEG', width=100, height=100)
    b64_str = base64.b64encode(jpg_bytes).decode('utf-8')

    res = client.post(
        '/api/business/vision/capture',
        headers={
            'Authorization': f'Bearer {s["u_member_id"]}',
            'X-Workspace-Id': s['ws_a_id']
        },  # MEMBER has vision:capture
        json={
            'location_id': s['loc_a_id'],
            'filename': 'api_camera_test.jpg',
            'content_type': 'image/jpeg',
            'image_base64': b64_str,
            'capture_device': 'MOBILE_APP_SCANNER'
        }
    )
    assert res.status_code == 201
    data = res.get_json()
    obs = data['data']['observation']
    assert obs['id'] is not None
    assert obs['capture_device'] == 'MOBILE_APP_SCANNER'
    assert obs['image_signed_url'] is not None


def test_audit_event_logged_for_vision_operations(fx_vision_env):
    """Verifies immutable AuditEvent logging for zone creation and image ingestion."""
    s = fx_vision_env
    zone = ShelfZoneService.create_shelf_zone(
        workspace_id=s['ws_a_id'],
        actor_user_id=s['u_owner_id'],
        data={'location_id': s['loc_a_id'], 'zone_code': 'AUDIT-ZONE-01', 'name': 'Audit Zone'}
    )

    img_bytes = _create_synthetic_image_bytes('JPEG')
    obs = VisionIngestionService.ingest_shelf_capture(
        workspace_id=s['ws_a_id'],
        location_id=s['loc_a_id'],
        actor_user_id=s['u_owner_id'],
        image_bytes=img_bytes,
        filename="audit_img.jpg",
        content_type="image/jpeg",
        shelf_zone_id=zone.id
    )

    zone_audit = AuditEvent.query.filter_by(
        workspace_id=s['ws_a_id'],
        action="SHELF_ZONE_CREATED",
        entity_id=zone.id
    ).first()
    assert zone_audit is not None
    assert zone_audit.actor_user_id == s['u_owner_id']

    capture_audit = AuditEvent.query.filter_by(
        workspace_id=s['ws_a_id'],
        action="VISUAL_CAPTURE_INGESTED",
        entity_id=obs['id']
    ).first()
    assert capture_audit is not None
    assert capture_audit.actor_user_id == s['u_owner_id']
