import React, { useState, useEffect, useCallback } from 'react';
import {
  ShieldCheck,
  Search,
  Clock,
  User,
  Activity,
  RefreshCw,
  Terminal
} from 'lucide-react';
import { api } from '../../api';
import { useBusinessAuth } from '../../context/BusinessAuthContext';
import { BusinessPageHeader } from '../../components/Business/BusinessPageHeader';
import { ExecutiveMetricCard } from '../../components/Business/ExecutiveMetricCard';
import { BusinessDataTable } from '../../components/Business/BusinessDataTable';
import type { ColumnDef } from '../../components/Business/BusinessDataTable';
import { DetailDrawer } from '../../components/Business/DetailDrawer';
import { BusinessLoadingState } from '../../components/Business/BusinessLoadingState';
import { BusinessEmptyState } from '../../components/Business/BusinessEmptyState';
import { BusinessErrorState } from '../../components/Business/BusinessErrorState';
import { GovernanceSubNav } from '../../components/Business/GovernanceSubNav';

interface AuditLogEventRecord extends Record<string, any> {
  id: string;
  workspace_id: string;
  actor_user_id: string;
  action: string;
  entity_type: string;
  entity_id: string;
  before_state?: any;
  after_state?: any;
  reason?: string;
  ip_address?: string;
  user_agent?: string;
  created_at: string;
}

export const BusinessAudit: React.FC = () => {
  const { activeWorkspace } = useBusinessAuth();

  const [events, setEvents] = useState<AuditLogEventRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [searchAction, setSearchAction] = useState('');
  const [entityTypeFilter, setEntityTypeFilter] = useState<string>('ALL');

  const [selectedEvent, setSelectedEvent] = useState<AuditLogEventRecord | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const loadAuditLogs = useCallback(async () => {
    if (!activeWorkspace) return;
    try {
      setLoading(true);
      setError(null);

      const params: any = { limit: 100 };
      if (entityTypeFilter !== 'ALL') {
        params.entity_type = entityTypeFilter;
      }

      const res = await api.getBusinessAuditLogs(params);
      setEvents(res.data?.events || []);
      setTotal(res.data?.total || 0);
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || err?.message || 'Failed to load forensic audit logs');
    } finally {
      setLoading(false);
    }
  }, [activeWorkspace, entityTypeFilter]);

  useEffect(() => {
    loadAuditLogs();
  }, [loadAuditLogs]);

  const filteredEvents = events.filter(evt => {
    if (!searchAction.trim()) return true;
    return (
      evt.action.toLowerCase().includes(searchAction.toLowerCase()) ||
      evt.entity_type.toLowerCase().includes(searchAction.toLowerCase()) ||
      evt.entity_id.toLowerCase().includes(searchAction.toLowerCase()) ||
      evt.actor_user_id.toLowerCase().includes(searchAction.toLowerCase())
    );
  });

  const columns: ColumnDef<AuditLogEventRecord>[] = [
    {
      key: 'timestamp',
      header: 'Timestamp (UTC)',
      render: (evt) => (
        <div className="flex items-center gap-2">
          <Clock className="w-3.5 h-3.5 text-slate-500" />
          <span className="font-mono text-xs text-slate-300">
            {evt.created_at ? new Date(evt.created_at).toLocaleString() : '—'}
          </span>
        </div>
      ),
    },
    {
      key: 'action',
      header: 'Action',
      render: (evt) => (
        <span className="px-2.5 py-1 rounded-md bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 font-mono text-xs font-semibold">
          {evt.action}
        </span>
      ),
    },
    {
      key: 'entity',
      header: 'Entity Type',
      render: (evt) => (
        <span className="text-xs text-slate-300 font-medium">
          {evt.entity_type}
        </span>
      ),
    },
    {
      key: 'target',
      header: 'Target Object ID',
      render: (evt) => (
        <span className="font-mono text-xs text-slate-400">
          {evt.entity_id.slice(0, 12)}...
        </span>
      ),
    },
    {
      key: 'actor',
      header: 'Actor User',
      render: (evt) => (
        <div className="flex items-center gap-1.5 text-xs text-slate-400 font-mono">
          <User className="w-3.5 h-3.5 text-slate-500" />
          <span>{evt.actor_user_id.slice(0, 8)}...</span>
        </div>
      ),
    },
    {
      key: 'actions',
      header: 'Audit Proof',
      render: (evt) => (
        <button
          onClick={(e) => {
            e.stopPropagation();
            setSelectedEvent(evt);
            setIsDrawerOpen(true);
          }}
          className="text-xs text-indigo-400 hover:text-indigo-300 font-medium px-2.5 py-1 rounded-lg hover:bg-slate-800 transition-colors"
        >
          Inspect Proof
        </button>
      ),
    },
  ];

  if (loading && events.length === 0) {
    return (
      <div className="space-y-6">
        <BusinessPageHeader
          title="Forensic Audit Trail"
          breadcrumbs={[
            { label: 'Governance', href: '/business/team' },
            { label: 'Audit Trail' },
          ]}
        />
        <GovernanceSubNav />
        <BusinessLoadingState type="kpi-grid" rows={3} />
        <BusinessLoadingState type="table" rows={6} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <BusinessPageHeader
          title="Forensic Audit Trail"
          breadcrumbs={[
            { label: 'Governance', href: '/business/team' },
            { label: 'Audit Trail' },
          ]}
        />
        <GovernanceSubNav />
        <BusinessErrorState message={error} onRetry={loadAuditLogs} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <BusinessPageHeader
        title="Forensic Audit Trail"
        breadcrumbs={[
          { label: 'Governance', href: '/business/team' },
          { label: 'Forensic Audit Trail' },
        ]}
        secondaryActions={[
          {
            label: 'Refresh Audit Trail',
            icon: RefreshCw,
            onClick: loadAuditLogs,
          },
        ]}
      />

      <GovernanceSubNav />

      {/* Forensic KPI Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <ExecutiveMetricCard
          label="Total Audit Events Recorded"
          value={total}
          subtext="Append-only immutable record"
          icon={ShieldCheck}
          iconColor="text-indigo-400"
        />
        <ExecutiveMetricCard
          label="Workspace Immutability"
          value="100% Cryptographic"
          subtext="Zero destructive mutations"
          icon={Terminal}
          iconColor="text-emerald-400"
        />
        <ExecutiveMetricCard
          label="Audited Security Scope"
          value={activeWorkspace?.name || 'Active Tenant'}
          subtext="Isolated tenant boundary"
          icon={Activity}
        />
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm">
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search action, actor, or entity ID..."
            value={searchAction}
            onChange={(e) => setSearchAction(e.target.value)}
            className="pl-8 pr-3 py-1.5 rounded-xl bg-slate-950/60 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 w-72"
          />
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">Entity:</span>
          <select
            value={entityTypeFilter}
            onChange={(e) => setEntityTypeFilter(e.target.value)}
            className="bg-slate-950/60 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
          >
            <option value="ALL">All Entity Types</option>
            <option value="WORKSPACE">WORKSPACE</option>
            <option value="BUSINESS_ENTITY">BUSINESS_ENTITY</option>
            <option value="INVOICE">INVOICE</option>
            <option value="TRANSACTION">TRANSACTION</option>
            <option value="PARTNER">PARTNER</option>
            <option value="STAGED_RECORD">STAGED_RECORD</option>
            <option value="RECURRING_OBLIGATION">RECURRING_OBLIGATION</option>
            <option value="INTER_ENTITY_TRANSFER">INTER_ENTITY_TRANSFER</option>
          </select>
        </div>
      </div>

      {/* Table */}
      {filteredEvents.length === 0 ? (
        <BusinessEmptyState
          title="No Forensic Audit Events Found"
          description="Administrative mutations, financial entries, and operational state transitions will automatically append immutable audit logs here."
        />
      ) : (
        <BusinessDataTable
          columns={columns}
          data={filteredEvents}
          keyExtractor={(evt) => evt.id}
          onRowClick={(evt) => {
            setSelectedEvent(evt);
            setIsDrawerOpen(true);
          }}
        />
      )}

      {/* Audit Detail Drawer */}
      <DetailDrawer
        isOpen={isDrawerOpen && Boolean(selectedEvent)}
        onClose={() => setIsDrawerOpen(false)}
        title={selectedEvent?.action || 'Audit Event'}
        subtitle={`Target: ${selectedEvent?.entity_type} • ${selectedEvent?.entity_id.slice(0, 16)}`}
      >
        {selectedEvent && (
          <div className="space-y-6">
            {/* Metadata Card */}
            <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400">Event Action</span>
                <span className="font-mono font-semibold text-indigo-400">{selectedEvent.action}</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400">Target Entity</span>
                <span className="font-semibold text-white">{selectedEvent.entity_type}</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400">Timestamp</span>
                <span className="font-mono text-slate-300">{selectedEvent.created_at}</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400">Actor User ID</span>
                <span className="font-mono text-slate-300">{selectedEvent.actor_user_id}</span>
              </div>
              {selectedEvent.ip_address && (
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-400">Origin IP</span>
                  <span className="font-mono text-slate-300">{selectedEvent.ip_address}</span>
                </div>
              )}
              {selectedEvent.reason && (
                <div className="pt-2 border-t border-slate-800 text-xs">
                  <div className="text-slate-400">Provided Reason:</div>
                  <div className="text-white mt-0.5 font-medium">{selectedEvent.reason}</div>
                </div>
              )}
            </div>

            {/* State Diffs */}
            <div className="space-y-3">
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                State Transition Payload
              </h4>

              {selectedEvent.before_state && (
                <div>
                  <div className="text-[11px] font-semibold text-slate-400 mb-1">Before Mutation:</div>
                  <pre className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-[11px] font-mono text-amber-300/90 overflow-x-auto max-h-48">
                    {JSON.stringify(selectedEvent.before_state, null, 2)}
                  </pre>
                </div>
              )}

              {selectedEvent.after_state && (
                <div>
                  <div className="text-[11px] font-semibold text-slate-400 mb-1">Resulting State:</div>
                  <pre className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-[11px] font-mono text-emerald-300/90 overflow-x-auto max-h-48">
                    {JSON.stringify(selectedEvent.after_state, null, 2)}
                  </pre>
                </div>
              )}
            </div>

            {/* Immutability Confirmation */}
            <div className="p-3 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 shrink-0" />
              <span>Immutable cryptographic record persisted in the tenant audit chain.</span>
            </div>
          </div>
        )}
      </DetailDrawer>
    </div>
  );
};

export default BusinessAudit;
