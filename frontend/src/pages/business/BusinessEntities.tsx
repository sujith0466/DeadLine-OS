import React, { useState, useEffect, useCallback } from 'react';
import {
  Building2,
  Plus,
  ArrowRightLeft,
  Search,
  CheckCircle2,
  Globe,
  X,
} from 'lucide-react';
import { api } from '../../api';
import { useBusinessAuth } from '../../context/BusinessAuthContext';
import { BusinessPageHeader } from '../../components/Business/BusinessPageHeader';
import { ExecutiveMetricCard } from '../../components/Business/ExecutiveMetricCard';
import { FinancialNumber } from '../../components/Business/FinancialNumber';
import { StatusBadge } from '../../components/Business/StatusBadge';
import { BusinessDataTable } from '../../components/Business/BusinessDataTable';
import type { ColumnDef } from '../../components/Business/BusinessDataTable';
import { DetailDrawer } from '../../components/Business/DetailDrawer';
import { BusinessLoadingState } from '../../components/Business/BusinessLoadingState';
import { BusinessEmptyState } from '../../components/Business/BusinessEmptyState';
import { BusinessErrorState } from '../../components/Business/BusinessErrorState';
import { EntitiesSubNav } from '../../components/Business/EntitiesSubNav';
import { EntityManagementModal } from '../../components/Business/EntityManagementModal';

interface BusinessEntityRecord extends Record<string, any> {
  id: string;
  workspace_id: string;
  name: string;
  legal_name?: string;
  entity_code?: string;
  tax_identifier?: string;
  currency: string;
  is_default: boolean;
  status: 'ACTIVE' | 'INACTIVE';
  created_at: string;
  updated_at: string;
}

interface InterEntityTransferRecord extends Record<string, any> {
  id: string;
  source_workspace_id: string;
  source_entity_id?: string;
  source_entity_name?: string;
  destination_workspace_id: string;
  destination_entity_id?: string;
  destination_entity_name?: string;
  amount: string;
  currency: string;
  transfer_date: string;
  reference_note?: string;
  status: 'PENDING' | 'SETTLED' | 'CANCELLED';
  created_at: string;
}

export const BusinessEntities: React.FC = () => {
  const { activeWorkspace, workspaces, hasPermission } = useBusinessAuth();

  const [entities, setEntities] = useState<BusinessEntityRecord[]>([]);
  const [transfers, setTransfers] = useState<InterEntityTransferRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [activeTab, setActiveTab] = useState<'entities' | 'transfers'>('entities');

  const [selectedEntity, setSelectedEntity] = useState<BusinessEntityRecord | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isTransferModalOpen, setIsTransferModalOpen] = useState(false);

  // Transfer form state
  const [transferAmount, setTransferAmount] = useState('');
  const [transferDestWs, setTransferDestWs] = useState('');
  const [transferSourceEntity, setTransferSourceEntity] = useState('');
  const [transferDestEntity, setTransferDestEntity] = useState('');
  const [transferNote, setTransferNote] = useState('');
  const [transferSubmitting, setTransferSubmitting] = useState(false);
  const [transferError, setTransferError] = useState<string | null>(null);

  // Archive state
  const [archiveReason, setArchiveReason] = useState('');
  const [isArchiveDialogOpen, setIsArchiveDialogOpen] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  const canWrite = hasPermission('transaction:create');

  const loadData = useCallback(async () => {
    if (!activeWorkspace) return;
    try {
      setLoading(true);
      setError(null);

      const [entRes, transRes] = await Promise.all([
        api.listBusinessEntities(),
        api.listInterEntityTransfers({ limit: 50 }).catch(() => ({ data: { transfers: [] } }))
      ]);

      setEntities(entRes.data?.entities || []);
      setTransfers(transRes.data?.transfers || []);
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || err?.message || 'Failed to load business entities');
    } finally {
      setLoading(false);
    }
  }, [activeWorkspace]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleCreateSuccess = () => {
    setIsCreateModalOpen(false);
    loadData();
  };

  const handleRecordTransfer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!transferAmount || !activeWorkspace) return;

    try {
      setTransferSubmitting(true);
      setTransferError(null);

      await api.createInterEntityTransfer({
        destination_workspace_id: transferDestWs || activeWorkspace.id,
        source_entity_id: transferSourceEntity || undefined,
        destination_entity_id: transferDestEntity || undefined,
        amount: transferAmount,
        currency: activeWorkspace.base_currency || 'INR',
        reference_note: transferNote || undefined,
      });

      setIsTransferModalOpen(false);
      setTransferAmount('');
      setTransferNote('');
      loadData();
    } catch (err: any) {
      setTransferError(err?.response?.data?.error?.message || err?.message || 'Failed to record inter-entity transfer');
    } finally {
      setTransferSubmitting(false);
    }
  };

  const handleSetDefault = async (entity: BusinessEntityRecord) => {
    try {
      setActionLoading(true);
      await api.updateBusinessEntity(entity.id, { is_default: true });
      loadData();
      if (selectedEntity?.id === entity.id) {
        setSelectedEntity(prev => prev ? { ...prev, is_default: true } : null);
      }
    } catch (err: any) {
      alert(err?.response?.data?.error?.message || 'Failed to update default entity');
    } finally {
      setActionLoading(false);
    }
  };

  const handleArchiveEntity = async () => {
    if (!selectedEntity) return;
    try {
      setActionLoading(true);
      await api.archiveBusinessEntity(selectedEntity.id, archiveReason);
      setIsArchiveDialogOpen(false);
      setIsDrawerOpen(false);
      loadData();
    } catch (err: any) {
      alert(err?.response?.data?.error?.message || 'Failed to archive entity');
    } finally {
      setActionLoading(false);
    }
  };

  const filteredEntities = entities.filter(ent => {
    const matchesSearch =
      ent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (ent.legal_name && ent.legal_name.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (ent.entity_code && ent.entity_code.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (ent.tax_identifier && ent.tax_identifier.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesStatus = statusFilter === 'ALL' || ent.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const totalEntities = entities.length;
  const activeEntitiesCount = entities.filter(e => e.status === 'ACTIVE').length;
  const defaultEntity = entities.find(e => e.is_default);
  const totalTransfersRecorded = transfers.length;

  const entityColumns: ColumnDef<BusinessEntityRecord>[] = [
    {
      key: 'name',
      header: 'Entity / Subsidiary',
      render: (ent) => (
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            <Building2 className="w-4 h-4" />
          </div>
          <div>
            <div className="font-semibold text-white flex items-center gap-2">
              <span>{ent.name}</span>
              {ent.is_default && (
                <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-[10px] text-emerald-400 font-medium">
                  Primary Legal Entity
                </span>
              )}
            </div>
            <div className="text-xs text-slate-400">
              {ent.legal_name || 'Operating Division'}
            </div>
          </div>
        </div>
      ),
    },
    {
      key: 'code',
      header: 'Code',
      render: (ent) => (
        <span className="font-mono text-xs text-slate-300">
          {ent.entity_code || '—'}
        </span>
      ),
    },
    {
      key: 'tax',
      header: 'GSTIN / Tax ID',
      render: (ent) => (
        <span className="font-mono text-xs text-slate-300">
          {ent.tax_identifier || '—'}
        </span>
      ),
    },
    {
      key: 'currency',
      header: 'Currency',
      render: (ent) => (
        <span className="px-2 py-1 rounded-md bg-slate-800 text-xs font-mono text-slate-300">
          {ent.currency}
        </span>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (ent) => (
        <StatusBadge
          status={ent.status === 'ACTIVE' ? 'ACTIVE' : 'INACTIVE'}
        />
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (ent) => (
        <button
          onClick={(e) => {
            e.stopPropagation();
            setSelectedEntity(ent);
            setIsDrawerOpen(true);
          }}
          className="text-xs text-indigo-400 hover:text-indigo-300 font-medium px-2.5 py-1 rounded-lg hover:bg-slate-800 transition-colors"
        >
          Inspect
        </button>
      ),
    },
  ];

  const transferColumns: ColumnDef<InterEntityTransferRecord>[] = [
    {
      key: 'date',
      header: 'Transfer Date',
      render: (t) => (
        <span className="text-xs font-mono text-slate-300">
          {t.transfer_date}
        </span>
      ),
    },
    {
      key: 'route',
      header: 'Transfer Route',
      render: (t) => (
        <div className="flex items-center gap-2 text-xs">
          <span className="text-white font-medium">{t.source_entity_name || 'Source Unit'}</span>
          <ArrowRightLeft className="w-3 h-3 text-slate-500" />
          <span className="text-indigo-300 font-medium">{t.destination_entity_name || 'Destination Unit'}</span>
        </div>
      ),
    },
    {
      key: 'amount',
      header: 'Transfer Amount',
      render: (t) => (
        <div className="font-semibold text-white">
          <FinancialNumber value={t.amount} currency={t.currency} />
        </div>
      ),
    },
    {
      key: 'note',
      header: 'Reference Memo',
      render: (t) => (
        <span className="text-xs text-slate-400">
          {t.reference_note || 'Internal liquidity allocation'}
        </span>
      ),
    },
    {
      key: 'status',
      header: 'Settlement',
      render: (t) => (
        <StatusBadge
          status={t.status === 'SETTLED' ? 'ISSUED' : 'DRAFT'}
        />
      ),
    },
  ];

  if (loading && entities.length === 0) {
    return (
      <div className="space-y-6">
        <BusinessPageHeader
          title="Legal Entities & Subsidiaries"
          breadcrumbs={[{ label: 'Entities', href: '/business/entities' }]}
        />
        <EntitiesSubNav />
        <BusinessLoadingState type="kpi-grid" rows={4} />
        <BusinessLoadingState type="table" rows={6} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <BusinessPageHeader
          title="Legal Entities & Subsidiaries"
          breadcrumbs={[{ label: 'Entities', href: '/business/entities' }]}
        />
        <EntitiesSubNav />
        <BusinessErrorState message={error} onRetry={loadData} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <BusinessPageHeader
        title="Legal Entities & Subsidiaries"
        breadcrumbs={[
          { label: 'Entities', href: '/business/entities' },
          { label: 'Subsidiaries & Legal Entities' },
        ]}
        primaryAction={
          canWrite
            ? {
                label: 'Register Legal Entity',
                icon: Plus,
                onClick: () => setIsCreateModalOpen(true),
              }
            : undefined
        }
        secondaryActions={
          canWrite
            ? [
                {
                  label: 'Record Inter-Entity Transfer',
                  icon: ArrowRightLeft,
                  onClick: () => setIsTransferModalOpen(true),
                },
              ]
            : []
        }
      />

      {/* Sub Navigation */}
      <EntitiesSubNav />

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <ExecutiveMetricCard
          label="Total Registered Entities"
          value={totalEntities}
          subtext="Across active workspace"
          icon={Building2}
        />
        <ExecutiveMetricCard
          label="Active Legal Entities"
          value={activeEntitiesCount}
          subtext="Operating subsidiaries"
          icon={CheckCircle2}
          iconColor="text-emerald-400"
        />
        <ExecutiveMetricCard
          label="Primary Legal Entity"
          value={defaultEntity ? defaultEntity.name : 'Not Designated'}
          subtext={defaultEntity?.tax_identifier || 'Standard workspace base'}
          icon={Globe}
          iconColor="text-indigo-400"
        />
        <ExecutiveMetricCard
          label="Inter-Entity Transfers"
          value={totalTransfersRecorded}
          subtext="Internal settlements logged"
          icon={ArrowRightLeft}
        />
      </div>

      {/* Tabs & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab('entities')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
              activeTab === 'entities'
                ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-600/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            Operating Entities ({entities.length})
          </button>
          <button
            onClick={() => setActiveTab('transfers')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
              activeTab === 'transfers'
                ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-600/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            Inter-Entity Transfers ({transfers.length})
          </button>
        </div>

        {activeTab === 'entities' && (
          <div className="flex items-center gap-3">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search entity, code, or GSTIN..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 pr-3 py-1.5 rounded-xl bg-slate-950/60 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 w-64"
              />
            </div>

            <div className="flex items-center gap-1 bg-slate-950/60 border border-slate-800 rounded-xl p-1">
              {(['ALL', 'ACTIVE', 'INACTIVE'] as const).map((st) => (
                <button
                  key={st}
                  onClick={() => setStatusFilter(st)}
                  className={`px-2.5 py-1 rounded-lg text-[11px] font-medium transition-all ${
                    statusFilter === st
                      ? 'bg-indigo-600 text-white'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {st}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Main Table */}
      {activeTab === 'entities' ? (
        filteredEntities.length === 0 ? (
          <BusinessEmptyState
            title="No Legal Entities Found"
            description="Register multiple legal operating entities or branches to isolate tax accounts, invoicing identities, and inter-entity settlements."
            actionLabel={canWrite ? "Register First Legal Entity" : undefined}
            onAction={canWrite ? () => setIsCreateModalOpen(true) : undefined}
          />
        ) : (
          <BusinessDataTable
            columns={entityColumns}
            data={filteredEntities}
            keyExtractor={(ent) => ent.id}
            onRowClick={(ent) => {
              setSelectedEntity(ent);
              setIsDrawerOpen(true);
            }}
          />
        )
      ) : transfers.length === 0 ? (
        <BusinessEmptyState
          title="No Inter-Entity Transfers Recorded"
          description="Log internal liquidity transfers between subsidiaries or operating divisions with automatic cross-workspace consolidation eliminations."
          actionLabel={canWrite ? "Record First Transfer" : undefined}
          onAction={canWrite ? () => setIsTransferModalOpen(true) : undefined}
        />
      ) : (
        <BusinessDataTable
          columns={transferColumns}
          data={transfers}
          keyExtractor={(t) => t.id}
        />
      )}

      {/* Detail Drawer */}
      <DetailDrawer
        isOpen={isDrawerOpen && Boolean(selectedEntity)}
        onClose={() => {
          setIsDrawerOpen(false);
          setIsArchiveDialogOpen(false);
        }}
        title={selectedEntity?.name || 'Legal Entity'}
        subtitle={selectedEntity?.legal_name || 'Operating Entity Specification'}
      >
        {selectedEntity && (
          <div className="space-y-6">
            {/* Badges */}
            <div className="flex items-center justify-between p-4 rounded-2xl bg-slate-950/60 border border-slate-800">
              <div className="space-y-1">
                <div className="text-xs text-slate-400">Entity Status</div>
                <StatusBadge
                  status={selectedEntity.status === 'ACTIVE' ? 'ACTIVE' : 'INACTIVE'}
                />
              </div>
              <div className="space-y-1 text-right">
                <div className="text-xs text-slate-400">Operating Currency</div>
                <div className="text-sm font-mono font-semibold text-white">
                  {selectedEntity.currency}
                </div>
              </div>
            </div>

            {/* Legal Attributes */}
            <div className="space-y-3">
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Corporate Governance Identifiers
              </h4>
              <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 space-y-3">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-400">Registered Legal Name</span>
                  <span className="font-semibold text-white">
                    {selectedEntity.legal_name || selectedEntity.name}
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-400">Entity Short Code</span>
                  <span className="font-mono text-slate-200">
                    {selectedEntity.entity_code || '—'}
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-400">Tax Identifier / GSTIN</span>
                  <span className="font-mono text-indigo-400 font-semibold">
                    {selectedEntity.tax_identifier || 'Not Specified'}
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-400">Entity Role</span>
                  <span className="text-white">
                    {selectedEntity.is_default ? 'Primary Operating Entity' : 'Subsidiary / Division'}
                  </span>
                </div>
              </div>
            </div>

            {/* Cryptographic Provenance */}
            <div className="space-y-3">
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Provenance & System Coordinates
              </h4>
              <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 space-y-2 text-xs font-mono">
                <div className="text-slate-400">
                  ID: <span className="text-slate-200">{selectedEntity.id}</span>
                </div>
                <div className="text-slate-400">
                  Workspace: <span className="text-slate-200">{selectedEntity.workspace_id}</span>
                </div>
                <div className="text-slate-400">
                  Registered: <span className="text-slate-200">{selectedEntity.created_at}</span>
                </div>
              </div>
            </div>

            {/* Actions */}
            {canWrite && (
              <div className="space-y-3 pt-4 border-t border-slate-800">
                {!selectedEntity.is_default && selectedEntity.status === 'ACTIVE' && (
                  <button
                    disabled={actionLoading}
                    onClick={() => handleSetDefault(selectedEntity)}
                    className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-all shadow-md shadow-indigo-600/20"
                  >
                    Set as Primary Legal Entity
                  </button>
                )}

                {selectedEntity.status === 'ACTIVE' ? (
                  !isArchiveDialogOpen ? (
                    <button
                      onClick={() => setIsArchiveDialogOpen(true)}
                      className="w-full py-2.5 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 text-rose-400 text-xs font-semibold transition-all"
                    >
                      Deactivate / Archive Entity
                    </button>
                  ) : (
                    <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 space-y-3">
                      <div className="text-xs font-semibold text-rose-400">
                        Confirm Entity Archival
                      </div>
                      <p className="text-xs text-slate-400">
                        Archived entities cannot issue new invoices or record transactions, but existing financial audit records remain immutable.
                      </p>
                      <input
                        type="text"
                        placeholder="Reason for archival (e.g. Division merged)..."
                        value={archiveReason}
                        onChange={(e) => setArchiveReason(e.target.value)}
                        className="w-full bg-slate-950 border border-rose-500/30 rounded-xl px-3 py-2 text-xs text-white focus:outline-none"
                      />
                      <div className="flex items-center gap-2">
                        <button
                          disabled={actionLoading}
                          onClick={handleArchiveEntity}
                          className="flex-1 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold transition-all"
                        >
                          Confirm Archival
                        </button>
                        <button
                          onClick={() => setIsArchiveDialogOpen(false)}
                          className="px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition-all"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  )
                ) : (
                  <div className="p-3 rounded-xl bg-slate-800/50 text-center text-xs text-slate-500">
                    This legal entity is archived and inactive.
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </DetailDrawer>

      {/* Create Entity Modal */}
      <EntityManagementModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSuccess={handleCreateSuccess}
      />

      {/* Record Transfer Modal */}
      {isTransferModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl flex flex-col">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/40">
              <h3 className="font-semibold text-white flex items-center gap-2">
                <ArrowRightLeft className="w-4 h-4 text-indigo-400" />
                Record Inter-Entity Transfer
              </h3>
              <button
                onClick={() => setIsTransferModalOpen(false)}
                className="text-slate-400 hover:text-white p-2 rounded-lg hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleRecordTransfer} className="p-6 space-y-4">
              {transferError && (
                <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs">
                  {transferError}
                </div>
              )}

              {workspaces.length > 1 && (
                <div>
                  <label className="text-xs font-semibold text-slate-400">Destination Workspace</label>
                  <select
                    value={transferDestWs || activeWorkspace?.id || ''}
                    onChange={(e) => setTransferDestWs(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white mt-1 focus:outline-none focus:border-indigo-500"
                  >
                    {workspaces.map((ws) => (
                      <option key={ws.id} value={ws.id}>
                        {ws.name} {ws.id === activeWorkspace?.id ? '(Current Workspace)' : ''}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div>
                <label className="text-xs font-semibold text-slate-400">Transfer Amount ({activeWorkspace?.base_currency || 'INR'})</label>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  value={transferAmount}
                  onChange={(e) => setTransferAmount(e.target.value)}
                  placeholder="e.g. 50000.00"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white mt-1 focus:outline-none focus:border-indigo-500 font-mono"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-400">Source Entity</label>
                  <select
                    value={transferSourceEntity}
                    onChange={(e) => setTransferSourceEntity(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white mt-1 focus:outline-none focus:border-indigo-500"
                  >
                    <option value="">Primary Workspace Entity</option>
                    {entities.map((e) => (
                      <option key={e.id} value={e.id}>
                        {e.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-400">Destination Entity</label>
                  <select
                    value={transferDestEntity}
                    onChange={(e) => setTransferDestEntity(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white mt-1 focus:outline-none focus:border-indigo-500"
                  >
                    <option value="">Target Subsidiary / Division</option>
                    {entities.map((e) => (
                      <option key={e.id} value={e.id}>
                        {e.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-400">Reference Memo</label>
                <input
                  type="text"
                  value={transferNote}
                  onChange={(e) => setTransferNote(e.target.value)}
                  placeholder="e.g. Monthly IT shared service fee"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white mt-1 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setIsTransferModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={transferSubmitting || !transferAmount}
                  className="px-5 py-2 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white transition-all shadow-lg shadow-indigo-600/30 disabled:opacity-50"
                >
                  {transferSubmitting ? 'Recording...' : 'Record Settlement'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default BusinessEntities;
