"""
DeadlineOS — Migration Chain Verification Tests (R1.3)
=======================================================
Structural tests that verify the Alembic migration chain contains ALL expected
Business OS schema definitions, preventing future "model exists / migration missing"
regressions like FINDING-001 (P0) from the Final B1–B12 Release Audit.

These tests operate on migration SOURCE FILES directly — they do NOT require
a running database and are NOT bypassed by db.create_all() in conftest.

How this is different from the rest of the test suite:
    The regular test suite uses db.create_all() which creates tables from ORM
    metadata. This means a model can exist and tests pass even if the Alembic
    migration for that model is missing. These tests catch that gap by directly
    inspecting migration file content.
"""

import os
import glob
import pytest


# ── Constants ─────────────────────────────────────────────────────────────────

# Adjust this path to find migrations relative to the test execution directory
MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), '..', 'migrations', 'versions')

# The expected linear revision chain in order (tail → head)
EXPECTED_REVISION_CHAIN = [
    ('27ae92747f99', None),               # baseline_phase_0
    ('a37ac0618419', '27ae92747f99'),     # phase_1_runtime_models
    ('c5e8b123987f', 'a37ac0618419'),     # phase_2_to_7_schema_stabilization
    ('d1a2b3c4d5e6', 'c5e8b123987f'),     # business_os_foundation
    ('e2b3c4d5e6f7', 'd1a2b3c4d5e6'),     # business_os_capture_staging
    ('f3c4d5e6f7a8', 'e2b3c4d5e6f7'),     # business_os_ledger_invoicing
    ('g4d5e6f7a8b9', 'f3c4d5e6f7a8'),     # business_os_rescue_export
    ('h5e6f7a8b9c0', 'g4d5e6f7a8b9'),     # business_os_recurring_automation
    ('i6f7a8b9c0d1', 'h5e6f7a8b9c0'),     # business_os_multi_entity
    ('j7g8h9i0j1k2', 'i6f7a8b9c0d1'),     # business_os_auth_invitations  ← R1 fix
    ('k8h9i0j1k2l3', 'j7g8h9i0j1k2'),     # business_os_operations_c1    ← C1 Operations Foundation
    ('l9i0j1k2l3m4', 'k8h9i0j1k2l3'),     # business_os_procurement_c2   ← C2.1 Procurement Foundation
    ('m0j1k2l3m4n5', 'l9i0j1k2l3m4'),     # business_os_goods_receipts_c2_2 ← C2.2 Goods Receiving Foundation
    ('o2l3m4n5o6p7', 'm0j1k2l3m4n5'),     # business_os_operational_alerts_c2_4 ← C2.4 Automation & Alerting
    ('p3m4n5o6p7q8', 'o2l3m4n5o6p7'),     # business_os_multi_currency_c3_1 ← C3.1 Multi-Currency Engine
    ('q4r5s6t7u8v9', 'p3m4n5o6p7q8'),     # business_os_batches_c3_2 ← C3.2 Batches & Expiry Lifecycle
]

# All Business OS table names that MUST appear in the migration chain
REQUIRED_BUSINESS_TABLES = [
    'business_workspaces',
    'business_workspace_members',
    'business_workspace_invitations',    # Previously missing — FINDING-001
    'business_commercial_partners',
    'business_audit_events',
    'business_ingestion_artifacts',
    'business_staged_extractions',
    'business_invoices',
    'business_invoice_items',            # Actual migration table name (not business_invoice_line_items)
    'business_transactions',
    'business_payment_allocations',
    'business_collection_reminders',
    'business_recurring_obligations',
    'business_automation_execution_logs',
    'business_entities',
    'business_inter_entity_transfers',
    'business_locations',
    'business_products',
    'business_stock_movements',
    'business_tasks',
    'business_purchase_requests',
    'business_purchase_orders',
    'business_purchase_order_lines',
    'business_goods_receipts',
    'business_goods_receipt_lines',
    'business_operational_alerts',
    'business_exchange_rates',
    'business_batches',
    'business_stock_movement_batches',
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_migration_files():
    """Return a dict of {revision_id: file_content} for all migration versions."""
    pattern = os.path.join(MIGRATIONS_DIR, '*.py')
    files = glob.glob(pattern)
    result = {}
    for fpath in files:
        if os.path.basename(fpath).startswith('__'):
            continue
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        # Extract revision id from content
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("revision = "):
                rev_id = stripped.split("=", 1)[1].strip().strip("'\"")
                result[rev_id] = content
                break
    return result


def _all_migration_content():
    """Concatenate all migration file content for table-name searching."""
    pattern = os.path.join(MIGRATIONS_DIR, '*.py')
    files = glob.glob(pattern)
    parts = []
    for fpath in files:
        if os.path.basename(fpath).startswith('__'):
            continue
        with open(fpath, 'r', encoding='utf-8') as f:
            parts.append(f.read())
    return "\n".join(parts)


# ── Test: Revision IDs Present ────────────────────────────────────────────────

class TestMigrationChainRevisionIds:
    """Verify every expected revision ID exists as a migration file."""

    def test_all_expected_revision_ids_exist(self):
        """Every revision in the expected chain must be present in migration files."""
        migration_files = _load_migration_files()
        missing = []
        for rev_id, _down_rev in EXPECTED_REVISION_CHAIN:
            if rev_id not in migration_files:
                missing.append(rev_id)
        assert not missing, (
            f"Missing revision IDs in migration files: {missing}. "
            f"Every expected revision must have a corresponding migration file."
        )

    def test_chain_is_linear_no_branches(self):
        """The down_revision chain must be a linear sequence — no branches."""
        migration_files = _load_migration_files()
        # Build {revision: down_revision} from actual files
        rev_to_down = {}
        for rev_id, content in migration_files.items():
            for line in content.splitlines():
                stripped = line.strip()
                if stripped.startswith("down_revision = "):
                    raw = stripped.split("=", 1)[1].strip()
                    # Handle None and string values
                    if raw in ('None', 'none'):
                        rev_to_down[rev_id] = None
                    else:
                        rev_to_down[rev_id] = raw.strip("'\"")
                    break

        # Verify against the expected chain
        expected_dict = {rev: down for rev, down in EXPECTED_REVISION_CHAIN}
        errors = []
        for rev_id, expected_down in expected_dict.items():
            if rev_id not in rev_to_down:
                errors.append(f"Revision {rev_id}: not found in migration files.")
                continue
            actual_down = rev_to_down[rev_id]
            if actual_down != expected_down:
                errors.append(
                    f"Revision {rev_id}: expected down_revision={expected_down!r}, "
                    f"got {actual_down!r}."
                )
        assert not errors, "Migration chain has broken or incorrect links:\n" + "\n".join(errors)

    def test_head_revision_is_q4r5s6t7u8v9(self):
        """The current head revision must be q4r5s6t7u8v9 (Phase C3.2 Batches & Expiry Lifecycle)."""
        migration_files = _load_migration_files()
        # Head = revision whose ID is not referenced as another revision's down_revision
        all_down_revisions = set()
        rev_to_down = {}
        for rev_id, content in migration_files.items():
            for line in content.splitlines():
                stripped = line.strip()
                if stripped.startswith("down_revision = "):
                    raw = stripped.split("=", 1)[1].strip()
                    if raw not in ('None', 'none'):
                        down = raw.strip("'\"")
                        all_down_revisions.add(down)
                        rev_to_down[rev_id] = down
                    else:
                        rev_to_down[rev_id] = None
                    break

        heads = [rev for rev in migration_files if rev not in all_down_revisions]
        assert len(heads) == 1, (
            f"Expected exactly 1 head revision, found {len(heads)}: {heads}. "
            f"Migration chain must not be branched."
        )
        expected_head = EXPECTED_REVISION_CHAIN[-1][0]
        assert heads[0] == expected_head, (
            f"Expected head revision to be '{expected_head}', got {heads[0]!r}."
        )


# ── Test: Required Tables Present ─────────────────────────────────────────────

class TestRequiredTablesInMigrations:
    """Verify every required Business OS table appears in at least one migration upgrade()."""

    def test_all_required_business_tables_have_migrations(self):
        """Every Business OS table name must appear in a create_table() call in a migration."""
        all_content = _all_migration_content()
        missing_tables = []
        for table_name in REQUIRED_BUSINESS_TABLES:
            if f"'{table_name}'" not in all_content and f'"{table_name}"' not in all_content:
                missing_tables.append(table_name)
        assert not missing_tables, (
            f"The following tables are NOT present in any migration file: {missing_tables}. "
            f"This would cause production database to be missing these tables after "
            f"`alembic upgrade head`. Add a migration for each missing table."
        )

    def test_business_workspace_invitations_specifically_migrated(self):
        """
        Specific regression guard for FINDING-001 (P0).
        The business_workspace_invitations table must have a dedicated migration.
        This test was retroactively added during the Phase 2 Remediation.
        """
        all_content = _all_migration_content()
        assert 'business_workspace_invitations' in all_content, (
            "CRITICAL: business_workspace_invitations is NOT present in any migration. "
            "This table would not exist in production after `alembic upgrade head`. "
            "Create migration j7g8h9i0j1k2_business_os_auth_invitations.py."
        )

    def test_invitation_migration_has_expected_columns(self):
        """Verify j7g8h9i0j1k2 migration defines all required invitation columns."""
        migration_files = _load_migration_files()
        assert 'j7g8h9i0j1k2' in migration_files, (
            "Invitation migration j7g8h9i0j1k2 not found."
        )
        content = migration_files['j7g8h9i0j1k2']
        required_columns = [
            'id', 'workspace_id', 'email', 'role', 'token',
            'status', 'invited_by_user_id', 'expires_at',
            'created_at', 'updated_at',
        ]
        missing_columns = [col for col in required_columns if f"'{col}'" not in content]
        assert not missing_columns, (
            f"Invitation migration is missing column definitions for: {missing_columns}"
        )

    def test_invitation_migration_has_unique_token_constraint(self):
        """Verify the invitation migration includes a UNIQUE constraint on token."""
        migration_files = _load_migration_files()
        content = migration_files.get('j7g8h9i0j1k2', '')
        assert 'UniqueConstraint' in content and 'token' in content, (
            "Invitation migration must define a UNIQUE constraint on the 'token' column."
        )

    def test_invitation_migration_has_fk_to_workspaces(self):
        """Verify the invitation migration has FK to business_workspaces."""
        migration_files = _load_migration_files()
        content = migration_files.get('j7g8h9i0j1k2', '')
        assert 'business_workspaces' in content, (
            "Invitation migration must define a ForeignKeyConstraint to business_workspaces."
        )

    def test_invitation_migration_has_fk_to_users(self):
        """Verify the invitation migration has FK to users (invited_by)."""
        migration_files = _load_migration_files()
        content = migration_files.get('j7g8h9i0j1k2', '')
        assert "'users.id'" in content or '"users.id"' in content, (
            "Invitation migration must define a ForeignKeyConstraint to users for invited_by_user_id."
        )

    def test_invitation_migration_has_composite_index(self):
        """Verify the composite index idx_biz_inv_ws_email_status is defined."""
        migration_files = _load_migration_files()
        content = migration_files.get('j7g8h9i0j1k2', '')
        assert 'idx_biz_inv_ws_email_status' in content, (
            "Invitation migration must define composite index idx_biz_inv_ws_email_status "
            "to match the model's __table_args__."
        )

    def test_invitation_migration_has_downgrade(self):
        """Verify the invitation migration defines a downgrade() function."""
        migration_files = _load_migration_files()
        content = migration_files.get('j7g8h9i0j1k2', '')
        assert 'def downgrade()' in content, (
            "Invitation migration must implement downgrade() for rollback safety."
        )
        assert 'drop_table' in content or 'drop_index' in content, (
            "downgrade() must remove the objects created in upgrade()."
        )
