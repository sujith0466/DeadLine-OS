import React, { useState, useEffect, useCallback } from 'react';
import {
  Building2,
  DollarSign,
  ArrowUpRight,
  ArrowDownRight,
  ShieldCheck,
  RefreshCw,
  Clock,
  Briefcase,
  SlidersHorizontal,
  CheckSquare,
  Square
} from 'lucide-react';
import { api } from '../../api';
import { useBusinessAuth } from '../../context/BusinessAuthContext';
import { BusinessPageHeader } from '../../components/Business/BusinessPageHeader';
import { ExecutiveMetricCard } from '../../components/Business/ExecutiveMetricCard';
import { FinancialNumber } from '../../components/Business/FinancialNumber';
import { BusinessDataTable } from '../../components/Business/BusinessDataTable';
import type { ColumnDef } from '../../components/Business/BusinessDataTable';
import { BusinessLoadingState } from '../../components/Business/BusinessLoadingState';
import { BusinessErrorState } from '../../components/Business/BusinessErrorState';
import { BusinessEmptyState } from '../../components/Business/BusinessEmptyState';
import { EntitiesSubNav } from '../../components/Business/EntitiesSubNav';

interface WorkspaceBreakdownRecord extends Record<string, any> {
  workspace_id: string;
  workspace_name: string;
  cash_position: string;
  receivables: string;
  payables: string;
  revenue: string;
  expenses: string;
  runway_days?: number;
}

interface ConsolidatedData {
  consolidated_cash: string;
  consolidated_revenue: string;
  consolidated_expenses: string;
  consolidated_receivables: string;
  consolidated_payables: string;
  inter_entity_eliminations: string;
  net_operating_cashflow: string;
  workspaces_count: number;
  workspace_breakdowns: WorkspaceBreakdownRecord[];
}

export const BusinessConsolidation: React.FC = () => {
  const { workspaces, activeWorkspace } = useBusinessAuth();

  const [data, setData] = useState<ConsolidatedData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedWorkspaceIds, setSelectedWorkspaceIds] = useState<string[]>([]);

  // Initialize selected workspaces with all user's active workspaces
  useEffect(() => {
    if (workspaces && workspaces.length > 0) {
      setSelectedWorkspaceIds(workspaces.map(w => w.id));
    }
  }, [workspaces]);

  const loadConsolidation = useCallback(async () => {
    if (selectedWorkspaceIds.length === 0) return;
    try {
      setLoading(true);
      setError(null);
      const res = await api.getConsolidatedOverview(selectedWorkspaceIds);
      setData(res.data?.overview || null);
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || err?.message || 'Failed to load consolidated financial overview');
    } finally {
      setLoading(false);
    }
  }, [selectedWorkspaceIds]);

  useEffect(() => {
    loadConsolidation();
  }, [loadConsolidation]);

  const toggleWorkspaceSelection = (wsId: string) => {
    setSelectedWorkspaceIds(prev => {
      if (prev.includes(wsId)) {
        if (prev.length === 1) return prev; // Keep at least one selected
        return prev.filter(id => id !== wsId);
      } else {
        return [...prev, wsId];
      }
    });
  };

  const selectAllWorkspaces = () => {
    setSelectedWorkspaceIds(workspaces.map(w => w.id));
  };

  const columns: ColumnDef<WorkspaceBreakdownRecord>[] = [
    {
      key: 'workspace',
      header: 'Workspace / Entity Group',
      render: (ws) => (
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            <Briefcase className="w-4 h-4" />
          </div>
          <div>
            <div className="font-semibold text-white flex items-center gap-2">
              <span>{ws.workspace_name}</span>
              {ws.workspace_id === activeWorkspace?.id && (
                <span className="px-2 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-[10px] text-indigo-400 font-medium">
                  Active Context
                </span>
              )}
            </div>
            <div className="text-xs text-slate-400 font-mono">
              {ws.workspace_id.slice(0, 8)}...
            </div>
          </div>
        </div>
      ),
    },
    {
      key: 'cash',
      header: 'Cash Position',
      render: (ws) => (
        <div className="font-semibold text-white">
          <FinancialNumber value={ws.cash_position} />
        </div>
      ),
    },
    {
      key: 'ar',
      header: 'Receivables (AR)',
      render: (ws) => (
        <div className="text-emerald-400 text-xs font-mono font-medium">
          <FinancialNumber value={ws.receivables} />
        </div>
      ),
    },
    {
      key: 'ap',
      header: 'Payables (AP)',
      render: (ws) => (
        <div className="text-rose-400 text-xs font-mono font-medium">
          <FinancialNumber value={ws.payables} />
        </div>
      ),
    },
    {
      key: 'flow',
      header: 'Net Flow (Rev - Exp)',
      render: (ws) => {
        const rev = parseFloat(ws.revenue || '0');
        const exp = parseFloat(ws.expenses || '0');
        const net = rev - exp;
        return (
          <div className={`text-xs font-mono font-semibold ${net >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
            <FinancialNumber value={net} />
          </div>
        );
      },
    },
    {
      key: 'runway',
      header: 'Runway',
      render: (ws) => (
        <div className="text-xs text-slate-300 flex items-center gap-1.5">
          <Clock className="w-3.5 h-3.5 text-slate-500" />
          <span>{ws.runway_days ? `${ws.runway_days} days` : 'Stable (>365d)'}</span>
        </div>
      ),
    },
  ];

  if (loading && !data) {
    return (
      <div className="space-y-6">
        <BusinessPageHeader
          title="Multi-Workspace Consolidation"
          breadcrumbs={[
            { label: 'Entities', href: '/business/entities' },
            { label: 'Consolidation' },
          ]}
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
          title="Multi-Workspace Consolidation"
          breadcrumbs={[
            { label: 'Entities', href: '/business/entities' },
            { label: 'Consolidation' },
          ]}
        />
        <EntitiesSubNav />
        <BusinessErrorState message={error} onRetry={loadConsolidation} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <BusinessPageHeader
        title="Multi-Workspace Consolidation"
        breadcrumbs={[
          { label: 'Entities', href: '/business/entities' },
          { label: 'Multi-Workspace Consolidation' },
        ]}
        secondaryActions={[
          {
            label: 'Refresh Consolidation',
            icon: RefreshCw,
            onClick: loadConsolidation,
          },
        ]}
      />

      <EntitiesSubNav />

      {/* Workspace Consolidation Scope Selector */}
      <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
            <SlidersHorizontal className="w-4 h-4 text-indigo-400" />
            <span>Consolidation Scope ({selectedWorkspaceIds.length} of {workspaces.length} Workspaces Included)</span>
          </div>
          {selectedWorkspaceIds.length < workspaces.length && (
            <button
              onClick={selectAllWorkspaces}
              className="text-xs text-indigo-400 hover:text-indigo-300 font-medium"
            >
              Select All
            </button>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {workspaces.map((ws) => {
            const isSelected = selectedWorkspaceIds.includes(ws.id);
            return (
              <button
                key={ws.id}
                onClick={() => toggleWorkspaceSelection(ws.id)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-medium transition-all ${
                  isSelected
                    ? 'bg-indigo-600/20 border border-indigo-500/40 text-indigo-300'
                    : 'bg-slate-950/60 border border-slate-800 text-slate-400 hover:text-slate-200'
                }`}
              >
                {isSelected ? (
                  <CheckSquare className="w-3.5 h-3.5 text-indigo-400" />
                ) : (
                  <Square className="w-3.5 h-3.5 text-slate-600" />
                )}
                <span>{ws.name}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Aggregate KPI Grid */}
      {data && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <ExecutiveMetricCard
            label="Consolidated Cash Truth"
            value={data.consolidated_cash}
            isCurrency={true}
            subtext={`Aggregated across ${data.workspaces_count} authorized workspaces`}
            icon={DollarSign}
            iconColor="text-emerald-400"
          />
          <ExecutiveMetricCard
            label="Consolidated Receivables"
            value={data.consolidated_receivables}
            isCurrency={true}
            subtext="Outstanding client invoices"
            icon={ArrowUpRight}
            iconColor="text-emerald-400"
          />
          <ExecutiveMetricCard
            label="Consolidated Payables"
            value={data.consolidated_payables}
            isCurrency={true}
            subtext="Committed vendor liabilities"
            icon={ArrowDownRight}
            iconColor="text-rose-400"
          />
          <ExecutiveMetricCard
            label="Inter-Entity Eliminations"
            value={data.inter_entity_eliminations}
            isCurrency={true}
            subtext="Internal transfers deducted"
            icon={ShieldCheck}
            iconColor="text-indigo-400"
          />
        </div>
      )}

      {/* Breakdown Table */}
      {data ? (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Building2 className="w-4 h-4 text-indigo-400" />
              <span>Workspace Entity Breakdown</span>
            </h3>
            <div className="text-xs text-slate-400">
              Net Operating Flow:{' '}
              <span className="font-semibold text-indigo-400 font-mono">
                <FinancialNumber value={data.net_operating_cashflow} />
              </span>
            </div>
          </div>

          <BusinessDataTable
            columns={columns}
            data={data.workspace_breakdowns || []}
            keyExtractor={(ws) => ws.workspace_id}
          />
        </div>
      ) : (
        <BusinessEmptyState
          title="No Workspaces Selected"
          description="Select one or more workspaces above to generate a consolidated multi-entity financial overview."
          actionLabel="Select All Workspaces"
          onAction={selectAllWorkspaces}
        />
      )}
    </div>
  );
};

export default BusinessConsolidation;
