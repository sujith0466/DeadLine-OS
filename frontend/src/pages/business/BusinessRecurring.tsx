import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  RefreshCw,
  Plus,
  Play,
  Pause,
  Zap,
  History,
  Search,
  DollarSign,
  Calendar,
  CheckCircle2,
  AlertTriangle,
  Eye,
} from 'lucide-react';
import { api } from '../../api';
import { useBusinessAuth } from '../../context/BusinessAuthContext';
import { BusinessPageHeader } from '../../components/Business/BusinessPageHeader';
import { OperationsSubNav } from '../../components/Business/OperationsSubNav';
import { BusinessDataTable } from '../../components/Business/BusinessDataTable';
import { DetailDrawer } from '../../components/Business/DetailDrawer';
import { StatusBadge } from '../../components/Business/StatusBadge';
import { FinancialNumber } from '../../components/Business/FinancialNumber';
import { BusinessLoadingState } from '../../components/Business/BusinessLoadingState';
import { BusinessEmptyState } from '../../components/Business/BusinessEmptyState';
import { BusinessErrorState } from '../../components/Business/BusinessErrorState';
import { RecurringObligationModal } from '../../components/Business/RecurringObligationModal';
import { AutomationLogsDrawer } from '../../components/Business/AutomationLogsDrawer';

export interface RecurringObligationItem {
  id: string;
  workspace_id: string;
  partner_id?: string | null;
  partner_name?: string | null;
  entity_id?: string | null;
  title: string;
  category: 'RENT' | 'RETAINER' | 'SUBSCRIPTION' | 'PAYROLL' | 'TAX' | 'OTHER';
  obligation_type: 'RECEIVABLE' | 'PAYABLE';
  amount: string;
  currency: string;
  frequency: 'WEEKLY' | 'MONTHLY' | 'QUARTERLY' | 'ANNUAL' | 'CUSTOM';
  interval_count?: number;
  day_of_month?: number;
  start_date: string;
  end_date?: string | null;
  next_occurrence_date?: string | null;
  status: 'ACTIVE' | 'PAUSED' | 'CANCELLED';
  auto_generate_invoice: boolean;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export const BusinessRecurring: React.FC = () => {
  const { activeWorkspace, role } = useBusinessAuth();

  const [obligations, setObligations] = useState<RecurringObligationItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters & Search
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [typeFilter, setTypeFilter] = useState<string>('ALL');
  const [categoryFilter, setCategoryFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Modals & Drawers
  const [isCreateModalOpen, setIsCreateModalOpen] = useState<boolean>(false);
  const [isLogsDrawerOpen, setIsLogsDrawerOpen] = useState<boolean>(false);
  const [selectedObligation, setSelectedObligation] = useState<RecurringObligationItem | null>(null);
  const [isDetailDrawerOpen, setIsDetailDrawerOpen] = useState<boolean>(false);

  // Action states
  const [runningBatch, setRunningBatch] = useState<boolean>(false);
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [actionMessage, setActionMessage] = useState<{ text: string; isError: boolean } | null>(null);

  const canWrite = role === 'OWNER' || role === 'ADMIN' || role === 'ACCOUNTANT';

  // Load obligations from backend
  const fetchObligations = useCallback(async () => {
    if (!activeWorkspace) return;
    setLoading(true);
    setError(null);
    try {
      const params: any = {};
      if (statusFilter !== 'ALL') params.status = statusFilter;
      if (typeFilter !== 'ALL') params.obligation_type = typeFilter;

      const res = await api.listRecurringObligations(params);
      setObligations(res.data?.obligations || []);
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || err?.message || 'Failed to load recurring obligations.');
    } finally {
      setLoading(false);
    }
  }, [activeWorkspace, statusFilter, typeFilter]);

  useEffect(() => {
    fetchObligations();
  }, [fetchObligations]);

  // Reactive listener for workspace switching
  useEffect(() => {
    const handleWorkspaceChange = () => {
      fetchObligations();
    };
    window.addEventListener('deadline_workspace_changed', handleWorkspaceChange);
    return () => window.removeEventListener('deadline_workspace_changed', handleWorkspaceChange);
  }, [fetchObligations]);

  // Handle Pause
  const handlePause = async (id: string) => {
    setActionLoading(true);
    setActionMessage(null);
    try {
      await api.pauseRecurringObligation(id);
      setActionMessage({ text: 'Obligation paused.', isError: false });
      fetchObligations();
      if (selectedObligation?.id === id) {
        setSelectedObligation(prev => prev ? { ...prev, status: 'PAUSED' } : null);
      }
    } catch (err: any) {
      setActionMessage({ text: err?.response?.data?.error?.message || 'Failed to pause obligation.', isError: true });
    } finally {
      setActionLoading(false);
    }
  };

  // Handle Resume
  const handleResume = async (id: string) => {
    setActionLoading(true);
    setActionMessage(null);
    try {
      await api.resumeRecurringObligation(id);
      setActionMessage({ text: 'Obligation resumed.', isError: false });
      fetchObligations();
      if (selectedObligation?.id === id) {
        setSelectedObligation(prev => prev ? { ...prev, status: 'ACTIVE' } : null);
      }
    } catch (err: any) {
      setActionMessage({ text: err?.response?.data?.error?.message || 'Failed to resume obligation.', isError: true });
    } finally {
      setActionLoading(false);
    }
  };

  // Handle Cancel
  const handleCancel = async (id: string) => {
    if (!window.confirm('Are you sure you want to permanently cancel this recurring contract?')) return;
    setActionLoading(true);
    setActionMessage(null);
    try {
      await api.cancelRecurringObligation(id);
      setActionMessage({ text: 'Obligation cancelled.', isError: false });
      fetchObligations();
      if (selectedObligation?.id === id) {
        setSelectedObligation(prev => prev ? { ...prev, status: 'CANCELLED' } : null);
      }
    } catch (err: any) {
      setActionMessage({ text: err?.response?.data?.error?.message || 'Failed to cancel obligation.', isError: true });
    } finally {
      setActionLoading(false);
    }
  };

  // Handle Manual Force Trigger
  const handleTrigger = async (id: string) => {
    setActionLoading(true);
    setActionMessage(null);
    try {
      const res = await api.triggerRecurringObligation(id);
      setActionMessage({ text: res?.message || 'Obligation executed and invoice generated!', isError: false });
      fetchObligations();
    } catch (err: any) {
      setActionMessage({ text: err?.response?.data?.error?.message || 'Failed to trigger obligation execution.', isError: true });
    } finally {
      setActionLoading(false);
    }
  };

  // Handle Run Batch Automations
  const handleRunBatch = async () => {
    setRunningBatch(true);
    setActionMessage(null);
    try {
      const res = await api.runBatchAutomations();
      setActionMessage({ text: res?.message || 'Batch automation run completed.', isError: false });
      fetchObligations();
    } catch (err: any) {
      setActionMessage({ text: err?.response?.data?.error?.message || 'Failed to run batch automations.', isError: true });
    } finally {
      setRunningBatch(false);
    }
  };

  // Filter list by category and search
  const filteredObligations = useMemo(() => {
    return obligations.filter(item => {
      if (categoryFilter !== 'ALL' && item.category !== categoryFilter) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const t = item.title.toLowerCase();
        const p = item.partner_name?.toLowerCase() || '';
        const c = item.category.toLowerCase();
        const n = item.notes?.toLowerCase() || '';
        if (!t.includes(q) && !p.includes(q) && !c.includes(q) && !n.includes(q)) return false;
      }
      return true;
    });
  }, [obligations, categoryFilter, searchQuery]);

  // Operational KPIs
  const kpis = useMemo(() => {
    const active = obligations.filter(o => o.status === 'ACTIVE').length;
    const paused = obligations.filter(o => o.status === 'PAUSED').length;
    const receivables = obligations.filter(o => o.obligation_type === 'RECEIVABLE' && o.status === 'ACTIVE').length;
    const payables = obligations.filter(o => o.obligation_type === 'PAYABLE' && o.status === 'ACTIVE').length;
    return {
      total: obligations.length,
      active,
      paused,
      receivables,
      payables,
    };
  }, [obligations]);

  // Category badge visual helper
  const renderCategoryBadge = (category: string) => {
    switch (category) {
      case 'RENT':
        return <span className="px-2 py-0.5 rounded-md bg-purple-500/10 text-purple-400 border border-purple-500/20 text-xs font-semibold">Rent</span>;
      case 'RETAINER':
        return <span className="px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-semibold">Retainer</span>;
      case 'SUBSCRIPTION':
        return <span className="px-2 py-0.5 rounded-md bg-blue-500/10 text-blue-400 border border-blue-500/20 text-xs font-semibold">Subscription</span>;
      case 'PAYROLL':
        return <span className="px-2 py-0.5 rounded-md bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 text-xs font-semibold">Payroll</span>;
      case 'TAX':
        return <span className="px-2 py-0.5 rounded-md bg-rose-500/10 text-rose-400 border border-rose-500/20 text-xs font-semibold">Tax Compliance</span>;
      case 'OTHER':
      default:
        return <span className="px-2 py-0.5 rounded-md bg-slate-500/10 text-slate-400 border border-slate-500/20 text-xs font-semibold">{category}</span>;
    }
  };

  const columns = [
    {
      key: 'title',
      header: 'Contract / Category',
      accessor: (item: RecurringObligationItem) => (
        <div>
          <div className="text-xs font-semibold text-white flex items-center gap-2">
            <span>{item.title}</span>
            {renderCategoryBadge(item.category)}
          </div>
          <div className="text-[11px] text-slate-400 mt-0.5">
            {item.obligation_type === 'RECEIVABLE' ? 'Receivable (Income)' : 'Payable (Expense)'}
          </div>
        </div>
      ),
    },
    {
      key: 'partner',
      header: 'Counterparty',
      accessor: (item: RecurringObligationItem) => (
        <span className="text-xs text-slate-200 font-medium">
          {item.partner_name || 'Unassigned Counterparty'}
        </span>
      ),
    },
    {
      key: 'frequency',
      header: 'Frequency',
      accessor: (item: RecurringObligationItem) => (
        <span className="px-2 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-slate-300 text-[11px] font-semibold">
          {item.frequency}
        </span>
      ),
    },
    {
      key: 'amount',
      header: 'Amount',
      accessor: (item: RecurringObligationItem) => (
        <FinancialNumber value={item.amount} currency={item.currency || 'INR'} />
      ),
    },
    {
      key: 'next_due',
      header: 'Next Due Date',
      accessor: (item: RecurringObligationItem) => (
        <span className="text-xs text-slate-300 font-mono">
          {item.next_occurrence_date || '—'}
        </span>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      accessor: (item: RecurringObligationItem) => <StatusBadge status={item.status} />,
    },
    {
      key: 'actions',
      header: 'Actions',
      accessor: (item: RecurringObligationItem) => (
        <div className="flex items-center gap-1.5">
          {canWrite && (
            <>
              {item.status === 'ACTIVE' ? (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handlePause(item.id);
                  }}
                  disabled={actionLoading}
                  className="p-1.5 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/20 transition-colors cursor-pointer"
                  title="Pause Obligation"
                >
                  <Pause className="w-3.5 h-3.5" />
                </button>
              ) : item.status === 'PAUSED' ? (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleResume(item.id);
                  }}
                  disabled={actionLoading}
                  className="p-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/20 transition-colors cursor-pointer"
                  title="Resume Obligation"
                >
                  <Play className="w-3.5 h-3.5" />
                </button>
              ) : null}

              {item.status !== 'CANCELLED' && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleTrigger(item.id);
                  }}
                  disabled={actionLoading}
                  className="p-1.5 rounded-lg bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-400 border border-indigo-500/20 transition-colors cursor-pointer"
                  title="Force Trigger Execution"
                >
                  <Zap className="w-3.5 h-3.5" />
                </button>
              )}
            </>
          )}

          <button
            onClick={(e) => {
              e.stopPropagation();
              setSelectedObligation(item);
              setIsDetailDrawerOpen(true);
            }}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors cursor-pointer"
            title="Inspect Details"
          >
            <Eye className="w-3.5 h-3.5" />
          </button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <BusinessPageHeader
        breadcrumbs={[
          { label: 'Operations', href: '/business/staging' },
          { label: 'Recurring Obligations' },
        ]}
        title="Recurring Obligations & Automation"
        description="Scheduled retainers, payables, rent, payroll, and automated contract execution."
        primaryAction={
          canWrite
            ? {
                label: 'Create Obligation',
                icon: Plus,
                onClick: () => setIsCreateModalOpen(true),
              }
            : undefined
        }
        secondaryActions={[
          {
            label: 'Execution Logs',
            icon: History,
            onClick: () => setIsLogsDrawerOpen(true),
          },
          ...(canWrite
            ? [
                {
                  label: runningBatch ? 'Running Batch...' : 'Run Batch',
                  icon: Zap,
                  onClick: handleRunBatch,
                  disabled: runningBatch,
                },
              ]
            : []),
        ]}
      />

      {/* Operations Sub Nav */}
      <OperationsSubNav />

      {/* Action Notification Toast */}
      {actionMessage && (
        <div
          className={`p-3.5 rounded-xl border text-xs flex items-center justify-between ${
            actionMessage.isError
              ? 'bg-rose-500/10 border-rose-500/20 text-rose-400'
              : 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
          }`}
        >
          <div className="flex items-center gap-2">
            {actionMessage.isError ? <AlertTriangle className="w-4 h-4" /> : <CheckCircle2 className="w-4 h-4" />}
            <span>{actionMessage.text}</span>
          </div>
          <button onClick={() => setActionMessage(null)} className="text-slate-400 hover:text-white text-xs cursor-pointer">
            Dismiss
          </button>
        </div>
      )}

      {/* Operational KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-md">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Active Contracts</span>
            <RefreshCw className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400 mt-1 font-mono">{kpis.active}</div>
          <div className="text-[11px] text-slate-500 mt-0.5">Automated Execution Active</div>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-md">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Paused Contracts</span>
            <Pause className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-amber-400 mt-1 font-mono">{kpis.paused}</div>
          <div className="text-[11px] text-slate-500 mt-0.5">Execution Temporarily Frozen</div>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-md">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Active Receivables</span>
            <DollarSign className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold text-white mt-1 font-mono">{kpis.receivables}</div>
          <div className="text-[11px] text-slate-500 mt-0.5">Recurring Customer Inflows</div>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-md">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Active Payables</span>
            <Calendar className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-bold text-slate-300 mt-1 font-mono">{kpis.payables}</div>
          <div className="text-[11px] text-slate-500 mt-0.5">Rent, Payroll & Subscriptions</div>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="flex flex-col md:flex-row gap-3 items-center justify-between p-4 rounded-2xl bg-slate-900/40 border border-slate-800/80">
        <div className="flex flex-wrap gap-2 items-center w-full md:w-auto">
          {/* Status Filter */}
          <div className="flex rounded-xl bg-slate-950 p-1 border border-slate-800 text-xs">
            {['ALL', 'ACTIVE', 'PAUSED', 'CANCELLED'].map(st => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-3 py-1.5 rounded-lg font-semibold transition-colors cursor-pointer ${
                  statusFilter === st ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {st}
              </button>
            ))}
          </div>

          {/* Type Filter */}
          <select
            value={typeFilter}
            onChange={e => setTypeFilter(e.target.value)}
            className="px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 cursor-pointer"
          >
            <option value="ALL">All Types</option>
            <option value="RECEIVABLE">Receivables</option>
            <option value="PAYABLE">Payables</option>
          </select>

          {/* Category Filter */}
          <select
            value={categoryFilter}
            onChange={e => setCategoryFilter(e.target.value)}
            className="px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 cursor-pointer"
          >
            <option value="ALL">All Categories</option>
            <option value="RENT">Rent</option>
            <option value="RETAINER">Retainer</option>
            <option value="SUBSCRIPTION">Subscription</option>
            <option value="PAYROLL">Payroll</option>
            <option value="TAX">Tax Compliance</option>
            <option value="OTHER">Other</option>
          </select>
        </div>

        {/* Search Field */}
        <div className="relative w-full md:w-72">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search title, partner, category..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
        </div>
      </div>

      {/* Main Table */}
      {loading ? (
        <BusinessLoadingState type="table" rows={6} />
      ) : error ? (
        <BusinessErrorState message={error} onRetry={fetchObligations} />
      ) : filteredObligations.length === 0 ? (
        <BusinessEmptyState
          title="No Recurring Obligations Found"
          description="Schedule automated retainers, subscriptions, or rent obligations to automate monthly invoice generation."
          actionLabel={canWrite ? "Create Obligation" : undefined}
          onAction={canWrite ? () => setIsCreateModalOpen(true) : undefined}
        />
      ) : (
        <BusinessDataTable
          columns={columns}
          data={filteredObligations}
          keyExtractor={(item) => item.id}
          onRowClick={(item) => {
            setSelectedObligation(item);
            setIsDetailDrawerOpen(true);
          }}
        />
      )}

      {/* Detail Drawer */}
      <DetailDrawer
        isOpen={isDetailDrawerOpen && !!selectedObligation}
        onClose={() => setIsDetailDrawerOpen(false)}
        title={selectedObligation?.title || 'Contract Details'}
        subtitle={`ID: ${selectedObligation?.id || ''}`}
        status={selectedObligation?.status}
      >
        {selectedObligation && (
          <div className="space-y-6">
            <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-3">
              <div className="flex justify-between text-xs">
                <span className="text-slate-400">Category:</span>
                {renderCategoryBadge(selectedObligation.category)}
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-slate-400">Type:</span>
                <span className="text-white font-semibold">
                  {selectedObligation.obligation_type === 'RECEIVABLE' ? 'Customer Receivable (Inflow)' : 'Supplier Payable (Outflow)'}
                </span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-slate-400">Counterparty:</span>
                <span className="text-white font-semibold">{selectedObligation.partner_name || 'None'}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-slate-400">Contract Amount:</span>
                <FinancialNumber value={selectedObligation.amount} currency={selectedObligation.currency || 'INR'} />
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-slate-400">Frequency:</span>
                <span className="text-slate-200 font-semibold">{selectedObligation.frequency}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-slate-400">Next Occurrence:</span>
                <span className="text-emerald-400 font-mono">{selectedObligation.next_occurrence_date || '—'}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-slate-400">Auto Generate Invoice:</span>
                <span className="text-slate-200">{selectedObligation.auto_generate_invoice ? 'Yes' : 'No'}</span>
              </div>
              {selectedObligation.notes && (
                <div className="pt-2 border-t border-slate-800 text-xs">
                  <span className="text-slate-400 block mb-1">Notes:</span>
                  <p className="text-slate-300">{selectedObligation.notes}</p>
                </div>
              )}
            </div>

            {/* Lifecycle Controls */}
            {canWrite && (
              <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">Contract Lifecycle Actions</h4>
                <div className="grid grid-cols-2 gap-2">
                  {selectedObligation.status === 'ACTIVE' ? (
                    <button
                      onClick={() => handlePause(selectedObligation.id)}
                      disabled={actionLoading}
                      className="py-2.5 px-3 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/20 text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
                    >
                      <Pause className="w-3.5 h-3.5" />
                      <span>Pause Contract</span>
                    </button>
                  ) : selectedObligation.status === 'PAUSED' ? (
                    <button
                      onClick={() => handleResume(selectedObligation.id)}
                      disabled={actionLoading}
                      className="py-2.5 px-3 rounded-xl bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/20 text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
                    >
                      <Play className="w-3.5 h-3.5" />
                      <span>Resume Contract</span>
                    </button>
                  ) : null}

                  {selectedObligation.status !== 'CANCELLED' && (
                    <button
                      onClick={() => handleTrigger(selectedObligation.id)}
                      disabled={actionLoading}
                      className="py-2.5 px-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
                    >
                      <Zap className="w-3.5 h-3.5" />
                      <span>Force Trigger</span>
                    </button>
                  )}
                </div>

                {selectedObligation.status !== 'CANCELLED' && (
                  <button
                    onClick={() => handleCancel(selectedObligation.id)}
                    disabled={actionLoading}
                    className="w-full py-2 px-3 rounded-xl text-rose-400 hover:bg-rose-500/10 text-xs font-semibold transition-colors cursor-pointer text-center"
                  >
                    Cancel & Terminate Contract
                  </button>
                )}
              </div>
            )}
          </div>
        )}
      </DetailDrawer>

      {/* Modals & Drawers */}
      <RecurringObligationModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSuccess={() => {
          setIsCreateModalOpen(false);
          fetchObligations();
        }}
      />

      <AutomationLogsDrawer
        isOpen={isLogsDrawerOpen}
        onClose={() => setIsLogsDrawerOpen(false)}
      />
    </div>
  );
};
