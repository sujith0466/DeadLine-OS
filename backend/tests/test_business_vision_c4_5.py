"""
DeadlineOS Business OS — C4.5 Ambient Camera Calibration & Edge Synchronization Tests
======================================================================================
Covers camera device registration, pairing token authentication, geometric ROI calibration,
calibration versioning, historical observation provenance, edge batch synchronization,
idempotent duplicate suppression, clock-skew defenses, RBAC, multi-tenant isolation,
inventory ledger immutability, and forensic audit event logging.
"""

import uuid
from decimal import Decimal
from datetime import datetime, timezone, date, timedelta
import pytest

from database.db import db
from models.user import User
from models.business import (
    Workspace,
    WorkspaceMember,
    BusinessLocation,
    BusinessProduct,
    CommercialPartner,
    BusinessShelfZone,
    BusinessCameraDevice,
    BusinessCameraCalibration,
    BusinessVisualObservation,
    BusinessStockMovement,
    AuditEvent
)
from services.business.camera_calibration_service import CameraCalibrationService
from services.business.edge_sync_service import EdgeSyncService
from utils.errors import APIError


# ── Fixtures & Helper ──────────────────────────────────────────────────────────

def _auth_headers(user_id: str, workspace_id: str) -> dict:
    return {
        "Authorization": f"Bearer {user_id}",
        "X-Workspace-Id": workspace_id,
        "Content-Type": "application/json"
    }


@pytest.fixture
def fx_c45_env(app):
    """Sets up dual-tenant workspaces with RBAC members, locations, products, and shelf zones."""
    with app.app_context():
        sfx = uuid.uuid4().hex[:6]

        # 1. Users
        u_owner = User(id=str(uuid.uuid4()), email=f"c45_owner_{sfx}@test.com", full_name="C4.5 Owner")
        u_admin = User(id=str(uuid.uuid4()), email=f"c45_admin_{sfx}@test.com", full_name="C4.5 Admin")
        u_member = User(id=str(uuid.uuid4()), email=f"c45_member_{sfx}@test.com", full_name="C4.5 Member")
        u_accountant = User(id=str(uuid.uuid4()), email=f"c45_acct_{sfx}@test.com", full_name="C4.5 Accountant")
        u_viewer = User(id=str(uuid.uuid4()), email=f"c45_viewer_{sfx}@test.com", full_name="C4.5 Viewer")
        u_tenb = User(id=str(uuid.uuid4()), email=f"c45_tenb_{sfx}@test.com", full_name="C4.5 Tenant B")
        db.session.add_all([u_owner, u_admin, u_member, u_accountant, u_viewer, u_tenb])
        db.session.commit()

        # 2. Workspaces
        ws_a = Workspace(id=str(uuid.uuid4()), name=f"C4.5-WS-A-{sfx}", base_currency="INR")
        ws_b = Workspace(id=str(uuid.uuid4()), name=f"C4.5-WS-B-{sfx}", base_currency="INR")
        db.session.add_all([ws_a, ws_b])
        db.session.commit()

        # 3. Memberships
        db.session.add_all([
            WorkspaceMember(id=str(uuid.uuid4()), workspace_id=ws_a.id, user_id=u_owner.id, role="OWNER", status="ACTIVE"),
            WorkspaceMember(id=str(uuid.uuid4()), workspace_id=ws_a.id, user_id=u_admin.id, role="ADMIN", status="ACTIVE"),
            WorkspaceMember(id=str(uuid.uuid4()), workspace_id=ws_a.id, user_id=u_member.id, role="MEMBER", status="ACTIVE"),
            WorkspaceMember(id=str(uuid.uuid4()), workspace_id=ws_a.id, user_id=u_accountant.id, role="ACCOUNTANT", status="ACTIVE"),
            WorkspaceMember(id=str(uuid.uuid4()), workspace_id=ws_a.id, user_id=u_viewer.id, role="VIEWER", status="ACTIVE"),
            WorkspaceMember(id=str(uuid.uuid4()), workspace_id=ws_b.id, user_id=u_tenb.id, role="OWNER", status="ACTIVE"),
        ])
        db.session.commit()

        # 4. Locations
        loc_a = BusinessLocation(id=str(uuid.uuid4()), workspace_id=ws_a.id, name=f"Store A {sfx}", location_type="STORE", status="ACTIVE")
        loc_b = BusinessLocation(id=str(uuid.uuid4()), workspace_id=ws_b.id, name=f"Store B {sfx}", location_type="STORE", status="ACTIVE")
        db.session.add_all([loc_a, loc_b])
        db.session.commit()

        # 5. Product
        p_cereal = BusinessProduct(
            id=str(uuid.uuid4()),
            workspace_id=ws_a.id,
            sku=f"SKU-OATS-{sfx}",
            name="Organic Rolled Oats 1kg",
            unit="UNIT",
            cost_price=Decimal("120.00"),
            selling_price=Decimal("200.00"),
            reorder_level=Decimal("10.00"),
            status="ACTIVE"
        )
        db.session.add(p_cereal)
        db.session.commit()

        # 6. Shelf Zone
        zone_a = BusinessShelfZone(
            id=str(uuid.uuid4()),
            workspace_id=ws_a.id,
            location_id=loc_a.id,
            zone_code=f"SZ-AISLE3-{sfx}",
            name="Aisle 3 Cereal Bay 1",
            assigned_product_id=p_cereal.id,
            target_facings=4,
            expected_capacity=Decimal("30.00"),
            reorder_threshold=Decimal("10.00"),
            status="ACTIVE"
        )
        db.session.add(zone_a)
        db.session.commit()

        yield {
            "ws_a_id": ws_a.id,
            "ws_b_id": ws_b.id,
            "u_owner_id": u_owner.id,
            "u_admin_id": u_admin.id,
            "u_member_id": u_member.id,
            "u_accountant_id": u_accountant.id,
            "u_viewer_id": u_viewer.id,
            "u_tenb_id": u_tenb.id,
            "loc_a_id": loc_a.id,
            "loc_b_id": loc_b.id,
            "p_cereal_id": p_cereal.id,
            "zone_a_id": zone_a.id
        }


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_register_camera_device(client, fx_c45_env):
    """1. Registers an ambient camera device, generates a 256-bit token, and stores hash."""
    env = fx_c45_env
    ws_id = env["ws_a_id"]
    owner_id = env["u_owner_id"]
    loc_id = env["loc_a_id"]

    res = client.post(
        "/api/business/vision/devices",
        json={
            "location_id": loc_id,
            "device_code": "CAM-BAY-01",
            "name": "Overhead Camera Bay 1",
            "device_type": "FIXED_OVERHEAD",
            "firmware_version": "v1.4.2"
        },
        headers=_auth_headers(owner_id, ws_id)
    )
    assert res.status_code == 201
    data = res.get_json()["data"]
    assert data["device"]["device_code"] == "CAM-BAY-01"
    assert data["device"]["status"] == "ACTIVE"
    assert "pairing_token" in data
    assert data["pairing_token"].startswith("cam_live_")

    # Verify token is hashed in DB, never plaintext
    dev_db = BusinessCameraDevice.query.get(data["device"]["id"])
    assert dev_db.api_key_hash != data["pairing_token"]
    assert len(dev_db.api_key_hash) == 64  # SHA-256 hex


def test_camera_device_heartbeat_update(client, fx_c45_env):
    """2. Edge synchronization updates the camera device's last_heartbeat_at timestamp."""
    env = fx_c45_env
    ws_id = env["ws_a_id"]
    owner_id = env["u_owner_id"]
    loc_id = env["loc_a_id"]

    device, token = CameraCalibrationService.register_camera_device(
        workspace_id=ws_id,
        location_id=loc_id,
        data={"device_code": "CAM-HB-01", "name": "Heartbeat Test Cam"},
        actor_user_id=owner_id
    )
    assert device.last_heartbeat_at is None

    # Authenticate device
    authed_dev = EdgeSyncService.authenticate_device(ws_id, device.id, token)
    assert authed_dev.last_heartbeat_at is not None


def test_create_camera_calibration_profile(client, fx_c45_env):
    """3. Creates a spatial calibration profile with normalized ROI polygon and version 1."""
    env = fx_c45_env
    ws_id = env["ws_a_id"]
    owner_id = env["u_owner_id"]
    loc_id = env["loc_a_id"]
    zone_id = env["zone_a_id"]

    device, _ = CameraCalibrationService.register_camera_device(
        workspace_id=ws_id,
        location_id=loc_id,
        data={"device_code": "CAM-CALIB-01", "name": "Calib Cam 1"},
        actor_user_id=owner_id
    )

    polygon = [[0.1, 0.2], [0.9, 0.2], [0.9, 0.8], [0.1, 0.8]]
    facings = [0.25, 0.50, 0.75]

    res = client.post(
        "/api/business/vision/calibrations",
        json={
            "camera_device_id": device.id,
            "shelf_zone_id": zone_id,
            "roi_polygon": polygon,
            "facing_divisions": facings,
            "notes": "Initial shelf baseline calibration"
        },
        headers=_auth_headers(owner_id, ws_id)
    )
    assert res.status_code == 201
    calib = res.get_json()["data"]["calibration"]
    assert calib["calibration_version"] == 1
    assert calib["status"] == "ACTIVE"
    assert calib["roi_polygon"] == polygon
    assert calib["facing_divisions"] == facings


def test_recalibration_version_increment_and_supersede(client, fx_c45_env):
    """4. Updating calibration sets old version to SUPERSEDED and increments to version 2."""
    env = fx_c45_env
    ws_id = env["ws_a_id"]
    owner_id = env["u_owner_id"]
    loc_id = env["loc_a_id"]
    zone_id = env["zone_a_id"]

    device, _ = CameraCalibrationService.register_camera_device(
        workspace_id=ws_id,
        location_id=loc_id,
        data={"device_code": "CAM-RECALIB-01", "name": "Recalib Cam"},
        actor_user_id=owner_id
    )

    # v1
    c1 = CameraCalibrationService.create_or_update_calibration(
        workspace_id=ws_id,
        camera_device_id=device.id,
        shelf_zone_id=zone_id,
        data={"roi_polygon": [[0.1, 0.1], [0.8, 0.1], [0.8, 0.8], [0.1, 0.8]]},
        actor_user_id=owner_id
    )
    assert c1.calibration_version == 1
    assert c1.status == "ACTIVE"

    # v2 (Recalibration)
    c2 = CameraCalibrationService.create_or_update_calibration(
        workspace_id=ws_id,
        camera_device_id=device.id,
        shelf_zone_id=zone_id,
        data={"roi_polygon": [[0.15, 0.15], [0.85, 0.15], [0.85, 0.85], [0.15, 0.85]]},
        actor_user_id=owner_id
    )
    assert c2.calibration_version == 2
    assert c2.status == "ACTIVE"

    # Verify c1 is now SUPERSEDED
    c1_refreshed = BusinessCameraCalibration.query.get(c1.id)
    assert c1_refreshed.status == "SUPERSEDED"


def test_historical_observation_provenance_preserved(client, fx_c45_env):
    """5. Observations captured under calibration v1 maintain immutable provenance when v2 is published."""
    env = fx_c45_env
    ws_id = env["ws_a_id"]
    owner_id = env["u_owner_id"]
    loc_id = env["loc_a_id"]
    zone_id = env["zone_a_id"]

    device, token = CameraCalibrationService.register_camera_device(
        workspace_id=ws_id,
        location_id=loc_id,
        data={"device_code": "CAM-PROV-01", "name": "Provenance Cam"},
        actor_user_id=owner_id
    )

    # 1. Calibrate v1
    CameraCalibrationService.create_or_update_calibration(
        workspace_id=ws_id,
        camera_device_id=device.id,
        shelf_zone_id=zone_id,
        data={"roi_polygon": [[0.1, 0.1], [0.9, 0.1], [0.9, 0.9], [0.1, 0.9]]},
        actor_user_id=owner_id
    )

    # 2. Ingest observation at v1
    sync_res1 = EdgeSyncService.process_edge_sync_batch(
        workspace_id=ws_id,
        device=device,
        payload={
            "observations": [
                {
                    "client_observation_id": "cobs-prov-001",
                    "shelf_zone_id": zone_id,
                    "calibration_version": 1,
                    "visual_count": 15.0
                }
            ]
        }
    )
    obs1_id = sync_res1["results"][0]["server_observation_id"]

    # 3. Recalibrate to v2
    CameraCalibrationService.create_or_update_calibration(
        workspace_id=ws_id,
        camera_device_id=device.id,
        shelf_zone_id=zone_id,
        data={"roi_polygon": [[0.2, 0.2], [0.8, 0.2], [0.8, 0.8], [0.2, 0.8]]},
        actor_user_id=owner_id
    )

    # 4. Ingest observation at v2
    sync_res2 = EdgeSyncService.process_edge_sync_batch(
        workspace_id=ws_id,
        device=device,
        payload={
            "observations": [
                {
                    "client_observation_id": "cobs-prov-002",
                    "shelf_zone_id": zone_id,
                    "calibration_version": 2,
                    "visual_count": 12.0
                }
            ]
        }
    )
    obs2_id = sync_res2["results"][0]["server_observation_id"]

    # Verify obs1 and obs2 records in DB
    obs1 = BusinessVisualObservation.query.get(obs1_id)
    obs2 = BusinessVisualObservation.query.get(obs2_id)
    assert obs1.capture_device == f"EDGE:{device.device_code}:cobs-prov-001"
    assert obs2.capture_device == f"EDGE:{device.device_code}:cobs-prov-002"


def test_invalid_calibration_polygon_rejected(client, fx_c45_env):
    """6. Rejects non-normalized coordinates, coordinates > 1.0, or degenerate polygons."""
    env = fx_c45_env
    ws_id = env["ws_a_id"]
    owner_id = env["u_owner_id"]
    loc_id = env["loc_a_id"]
    zone_id = env["zone_a_id"]

    device, _ = CameraCalibrationService.register_camera_device(
        workspace_id=ws_id,
        location_id=loc_id,
        data={"device_code": "CAM-INVALID-01", "name": "Invalid Poly Cam"},
        actor_user_id=owner_id
    )

    # Out of bounds coordinate (1.5 > 1.0)
    res1 = client.post(
        "/api/business/vision/calibrations",
        json={
            "camera_device_id": device.id,
            "shelf_zone_id": zone_id,
            "roi_polygon": [[0.0, 0.0], [1.5, 0.0], [1.0, 1.0]]
        },
        headers=_auth_headers(owner_id, ws_id)
    )
    assert res1.status_code == 400

    # Degenerate (only 2 points)
    res2 = client.post(
        "/api/business/vision/calibrations",
        json={
            "camera_device_id": device.id,
            "shelf_zone_id": zone_id,
            "roi_polygon": [[0.1, 0.1], [0.2, 0.2]]
        },
        headers=_auth_headers(owner_id, ws_id)
    )
    assert res2.status_code == 400


def test_point_in_roi_polygon_mapping(client, fx_c45_env):
    """7. Maps detected item bounding box center to calibrated shelf zone polygon."""
    env = fx_c45_env
    ws_id = env["ws_a_id"]
    owner_id = env["u_owner_id"]
    loc_id = env["loc_a_id"]
    zone_id = env["zone_a_id"]

    device, _ = CameraCalibrationService.register_camera_device(
        workspace_id=ws_id,
        location_id=loc_id,
        data={"device_code": "CAM-MAP-01", "name": "Mapping Cam"},
        actor_user_id=owner_id
    )

    # Calibrate ROI in top-left quadrant [0.1, 0.1] to [0.5, 0.5]
    CameraCalibrationService.create_or_update_calibration(
        workspace_id=ws_id,
        camera_device_id=device.id,
        shelf_zone_id=zone_id,
        data={"roi_polygon": [[0.1, 0.1], [0.5, 0.1], [0.5, 0.5], [0.1, 0.5]]},
        actor_user_id=owner_id
    )

    # Inside box: [ymin=0.2, xmin=0.2, ymax=0.3, xmax=0.3] -> center is (0.25, 0.25)
    inside_bbox = [0.2, 0.2, 0.3, 0.3]
    mapped = CameraCalibrationService.map_bounding_box_to_shelf_zone(ws_id, device.id, inside_bbox)
    assert mapped is not None
    assert mapped[0].id == zone_id

    # Outside box: [ymin=0.7, xmin=0.7, ymax=0.8, xmax=0.8] -> center is (0.75, 0.75)
    outside_bbox = [0.7, 0.7, 0.8, 0.8]
    assert CameraCalibrationService.map_bounding_box_to_shelf_zone(ws_id, device.id, outside_bbox) is None


def test_edge_sync_batch_ingestion_success(client, fx_c45_env):
    """8. Endpoint /edge/sync successfully ingests a batch of observations from paired device."""
    env = fx_c45_env
    ws_id = env["ws_a_id"]
    owner_id = env["u_owner_id"]
    loc_id = env["loc_a_id"]
    zone_id = env["zone_a_id"]

    device, token = CameraCalibrationService.register_camera_device(
        workspace_id=ws_id,
        location_id=loc_id,
        data={"device_code": "CAM-SYNC-01", "name": "Sync Cam 1"},
        actor_user_id=owner_id
    )

    res = client.post(
        "/api/business/vision/edge/sync",
        json={
            "sync_batch_id": "batch-101",
            "observations": [
                {
                    "client_observation_id": "cobs-sync-01",
                    "shelf_zone_id": zone_id,
                    "visual_count": 22.0,
                    "visual_facings": 4,
                    "overall_confidence": 0.96
                }
            ]
        },
        headers={
            "X-Workspace-Id": ws_id,
            "X-Device-Id": device.id,
            "X-Device-Token": token,
            "Content-Type": "application/json"
        }
    )
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["received_count"] == 1
    assert data["processed_count"] == 1
    assert data["duplicate_count"] == 0
    assert data["results"][0]["status"] == "PROCESSED"


def test_edge_sync_idempotency_duplicate_suppression(client, fx_c45_env):
    """9. Replaying an identical batch returns DUPLICATE_ACCEPTED without re-inserting observations."""
    env = fx_c45_env
    ws_id = env["ws_a_id"]
    owner_id = env["u_owner_id"]
    loc_id = env["loc_a_id"]
    zone_id = env["zone_a_id"]

    device, token = CameraCalibrationService.register_camera_device(
        workspace_id=ws_id,
        location_id=loc_id,
        data={"device_code": "CAM-DEDUP-01", "name": "Dedup Cam"},
        actor_user_id=owner_id
    )

    batch_payload = {
        "sync_batch_id": "batch-dedup-1",
        "observations": [
            {
                "client_observation_id": "cobs-dedup-01",
                "shelf_zone_id": zone_id,
                "visual_count": 18.0
            }
        ]
    }
    headers = {
        "X-Workspace-Id": ws_id,
        "X-Device-Id": device.id,
        "X-Device-Token": token,
        "Content-Type": "application/json"
    }

    # First send
    res1 = client.post("/api/business/vision/edge/sync", json=batch_payload, headers=headers)
    assert res1.status_code == 200
    assert res1.get_json()["data"]["processed_count"] == 1

    # Second send (Replay/Retry)
    res2 = client.post("/api/business/vision/edge/sync", json=batch_payload, headers=headers)
    assert res2.status_code == 200
    data2 = res2.get_json()["data"]
    assert data2["processed_count"] == 0
    assert data2["duplicate_count"] == 1
    assert data2["results"][0]["status"] == "DUPLICATE_ACCEPTED"


def test_edge_sync_clock_skew_tolerance_and_clamping(client, fx_c45_env):
    """10. Offline timestamps within 24h are preserved; future timestamps > 15m are clamped to ingestion time."""
    env = fx_c45_env
    ws_id = env["ws_a_id"]
    owner_id = env["u_owner_id"]
    loc_id = env["loc_a_id"]
    zone_id = env["zone_a_id"]

    device, token = CameraCalibrationService.register_camera_device(
        workspace_id=ws_id,
        location_id=loc_id,
        data={"device_code": "CAM-SKEW-01", "name": "Skew Cam"},
        actor_user_id=owner_id
    )

    # 1. Offline capture from 6 hours ago
    past_ts = (datetime.now(timezone.utc) - timedelta(hours=6)).isoformat()
    # 2. Corrupted future capture from 2 hours in the future
    future_ts = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()

    batch_payload = {
        "observations": [
            {
                "client_observation_id": "cobs-past-01",
                "shelf_zone_id": zone_id,
                "capture_timestamp": past_ts,
                "visual_count": 10.0
            },
            {
                "client_observation_id": "cobs-future-01",
                "shelf_zone_id": zone_id,
                "capture_timestamp": future_ts,
                "visual_count": 10.0
            }
        ]
    }
    res = client.post(
        "/api/business/vision/edge/sync",
        json=batch_payload,
        headers={"X-Workspace-Id": ws_id, "X-Device-Id": device.id, "X-Device-Token": token}
    )
    assert res.status_code == 200

    obs_past = BusinessVisualObservation.query.filter_by(capture_device=f"EDGE:{device.device_code}:cobs-past-01").first()
    obs_future = BusinessVisualObservation.query.filter_by(capture_device=f"EDGE:{device.device_code}:cobs-future-01").first()

    # Past timestamp preserved
    past_hour = obs_past.capture_timestamp.hour
    assert past_hour == datetime.fromisoformat(past_ts).hour

    # Future timestamp clamped to roughly current time (not 2h ahead)
    obs_future_ts = obs_future.capture_timestamp
    if obs_future_ts.tzinfo is None:
        obs_future_ts = obs_future_ts.replace(tzinfo=timezone.utc)
    diff_future = abs((obs_future_ts - datetime.now(timezone.utc)).total_seconds())
    assert diff_future < 60  # Clamped to now


def test_edge_device_token_authentication(client, fx_c45_env):
    """11. Edge sync rejects invalid, mismatched, or revoked tokens with 401 Unauthorized."""
    env = fx_c45_env
    ws_id = env["ws_a_id"]
    owner_id = env["u_owner_id"]
    loc_id = env["loc_a_id"]

    device, token = CameraCalibrationService.register_camera_device(
        workspace_id=ws_id,
        location_id=loc_id,
        data={"device_code": "CAM-AUTH-01", "name": "Auth Cam"},
        actor_user_id=owner_id
    )

    # 1. Invalid Token
    res1 = client.post(
        "/api/business/vision/edge/sync",
        json={"observations": []},
        headers={"X-Workspace-Id": ws_id, "X-Device-Id": device.id, "X-Device-Token": "invalid_token_123"}
    )
    assert res1.status_code == 401

    # 2. Deactivate Device then test
    CameraCalibrationService.deactivate_camera_device(ws_id, device.id, owner_id)
    res2 = client.post(
        "/api/business/vision/edge/sync",
        json={"observations": []},
        headers={"X-Workspace-Id": ws_id, "X-Device-Id": device.id, "X-Device-Token": token}
    )
    assert res2.status_code == 401


def test_rbac_calibration_and_device_management(client, fx_c45_env):
    """12. OWNER and ADMIN can register/calibrate; MEMBER, ACCOUNTANT, VIEWER receive 403 Forbidden."""
    env = fx_c45_env
    ws_id = env["ws_a_id"]
    loc_id = env["loc_a_id"]
    zone_id = env["zone_a_id"]

    device_payload = {"location_id": loc_id, "device_code": "CAM-RBAC-01", "name": "RBAC Cam"}

    # OWNER -> 201
    assert client.post("/api/business/vision/devices", json=device_payload, headers=_auth_headers(env["u_owner_id"], ws_id)).status_code == 201

    # ADMIN -> 201 (different device code)
    device_payload["device_code"] = "CAM-RBAC-02"
    assert client.post("/api/business/vision/devices", json=device_payload, headers=_auth_headers(env["u_admin_id"], ws_id)).status_code == 201

    # MEMBER -> 403
    device_payload["device_code"] = "CAM-RBAC-03"
    assert client.post("/api/business/vision/devices", json=device_payload, headers=_auth_headers(env["u_member_id"], ws_id)).status_code == 403

    # ACCOUNTANT -> 403
    assert client.post("/api/business/vision/devices", json=device_payload, headers=_auth_headers(env["u_accountant_id"], ws_id)).status_code == 403

    # VIEWER -> 403
    assert client.post("/api/business/vision/devices", json=device_payload, headers=_auth_headers(env["u_viewer_id"], ws_id)).status_code == 403


def test_multitenant_isolation_cameras_and_sync(client, fx_c45_env):
    """13. Tenant B cannot access or sync to Tenant A's cameras or calibrations."""
    env = fx_c45_env
    ws_a = env["ws_a_id"]
    ws_b = env["ws_b_id"]
    owner_a = env["u_owner_id"]
    owner_b = env["u_tenb_id"]
    loc_a = env["loc_a_id"]

    # Register camera in Tenant A
    dev_a, token_a = CameraCalibrationService.register_camera_device(
        workspace_id=ws_a,
        location_id=loc_a,
        data={"device_code": "CAM-TEN-A", "name": "Tenant A Cam"},
        actor_user_id=owner_a
    )

    # Tenant B tries to get Tenant A's device
    res_get = client.get(f"/api/business/vision/devices/{dev_a.id}", headers=_auth_headers(owner_b, ws_b))
    assert res_get.status_code == 404

    # Tenant B tries to sync with Tenant A's device ID under Tenant B workspace
    res_sync = client.post(
        "/api/business/vision/edge/sync",
        json={"observations": []},
        headers={"X-Workspace-Id": ws_b, "X-Device-Id": dev_a.id, "X-Device-Token": token_a}
    )
    assert res_sync.status_code == 401


def test_inventory_ledger_immutability_edge_sync(client, fx_c45_env):
    """14. Edge sync and calibration operations NEVER directly create stock movements."""
    env = fx_c45_env
    ws_id = env["ws_a_id"]
    owner_id = env["u_owner_id"]
    loc_id = env["loc_a_id"]
    zone_id = env["zone_a_id"]

    device, token = CameraCalibrationService.register_camera_device(
        workspace_id=ws_id,
        location_id=loc_id,
        data={"device_code": "CAM-IMMUTABLE-01", "name": "Immutable Cam"},
        actor_user_id=owner_id
    )

    CameraCalibrationService.create_or_update_calibration(
        workspace_id=ws_id,
        camera_device_id=device.id,
        shelf_zone_id=zone_id,
        data={"roi_polygon": [[0.1, 0.1], [0.9, 0.1], [0.9, 0.9], [0.1, 0.9]]},
        actor_user_id=owner_id
    )

    EdgeSyncService.process_edge_sync_batch(
        workspace_id=ws_id,
        device=device,
        payload={
            "observations": [
                {"client_observation_id": "cobs-imm-1", "shelf_zone_id": zone_id, "visual_count": 0.0},
                {"client_observation_id": "cobs-imm-2", "shelf_zone_id": zone_id, "visual_count": 25.0}
            ]
        }
    )

    # Assert ZERO stock movements exist
    movements_count = BusinessStockMovement.query.filter_by(workspace_id=ws_id).count()
    assert movements_count == 0, f"Expected 0 stock movements, found {movements_count}!"


def test_audit_event_logging_device_and_calibration(client, fx_c45_env):
    """15. Verifies DEVICE_REGISTERED, CAMERA_CALIBRATED, and EDGE_SYNC_PROCESSED audit events."""
    env = fx_c45_env
    ws_id = env["ws_a_id"]
    owner_id = env["u_owner_id"]
    loc_id = env["loc_a_id"]
    zone_id = env["zone_a_id"]

    device, token = CameraCalibrationService.register_camera_device(
        workspace_id=ws_id,
        location_id=loc_id,
        data={"device_code": "CAM-AUDIT-01", "name": "Audit Cam"},
        actor_user_id=owner_id
    )
    calib = CameraCalibrationService.create_or_update_calibration(
        workspace_id=ws_id,
        camera_device_id=device.id,
        shelf_zone_id=zone_id,
        data={"roi_polygon": [[0.1, 0.1], [0.8, 0.1], [0.8, 0.8], [0.1, 0.8]]},
        actor_user_id=owner_id
    )
    EdgeSyncService.process_edge_sync_batch(
        workspace_id=ws_id,
        device=device,
        payload={"observations": [{"client_observation_id": "cobs-audit-1", "shelf_zone_id": zone_id, "visual_count": 5.0}]}
    )

    events = AuditEvent.query.filter_by(workspace_id=ws_id).all()
    actions = [e.action for e in events]
    assert "DEVICE_REGISTERED" in actions
    assert "CAMERA_CALIBRATED" in actions
    assert "EDGE_SYNC_PROCESSED" in actions
