import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  ShieldAlert,
  Send,
  RefreshCw,
  Search,
  Eye,
  History,
  AlertTriangle,
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
import { ReminderModal } from '../../components/Business/ReminderModal';

export interface AgingBucketData {
  count: number;
  total: string;
  invoices: Array<{
    id: string;
    invoice_number: string;
    partner_name: string;
    partner_id?: string | null;
    balance_due: string;
    due_date: string;
    days_overdue: number;
  }>;
}

export interface AgingSummary {
  workspace_id: string;
  as_of_date: string;
  total_overdue_amount: string;
  total_overdue_count: number;
  buckets: {
    '1_to_30_days': AgingBucketData;
    '31_to_60_days': AgingBucketData;
    '61_to_90_days': AgingBucketData;
    '90_plus_days': AgingBucketData;
  };
}

export interface PriorityReceivableItem {
  invoice_id: string;
  invoice_number: string;
  partner_id?: string | null;
  partner_name: string;
  balance_due: string;
  due_date: string;
  days_overdue: number;
  priority_score: string;
  recommended_tone: 'GENTLE' | 'POLITE' | 'URGENT' | 'LEGAL';
}

export const BusinessRescue: React.FC = () => {
  const { activeWorkspace, role } = useBusinessAuth();

  const [aging, setAging] = useState<AgingSummary | null>(null);
  const [priorities, setPriorities] = useState<PriorityReceivableItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters & Search
  const [bucketFilter, setBucketFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Modals & Drawers
  const [selectedReceivable, setSelectedReceivable] = useState<PriorityReceivableItem | null>(null);
  const [isDetailDrawerOpen, setIsDetailDrawerOpen] = useState<boolean>(false);
  const [reminderHistory, setReminderHistory] = useState<any[]>([]);
  const [loadingHistory, setLoadingHistory] = useState<boolean>(false);

  // Reminder Modal
  const [isReminderModalOpen, setIsReminderModalOpen] = useState<boolean>(false);
  const [activeInvoiceForReminder, setActiveInvoiceForReminder] = useState<string | null>(null);
  const [activeToneForReminder, setActiveToneForReminder] = useState<string>('POLITE');

  const canWrite = role === 'OWNER' || role === 'ADMIN' || role === 'ACCOUNTANT';

  // Fetch aging and priority data
  const fetchData = useCallback(async () => {
    if (!activeWorkspace) return;
    setLoading(true);
    setError(null);
    try {
      const [agingRes, prioritiesRes] = await Promise.all([
        api.getRescueAgingSummary(),
        api.getPriorityReceivables(50),
      ]);
      setAging(agingRes.data);
      setPriorities(prioritiesRes.data?.priorities || []);
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || err?.message || 'Failed to load debt rescue data.');
    } finally {
      setLoading(false);
    }
  }, [activeWorkspace]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Reactive listener for workspace switching
  useEffect(() => {
    const handleWorkspaceChange = () => {
      fetchData();
    };
    window.addEventListener('deadline_workspace_changed', handleWorkspaceChange);
    return () => window.removeEventListener('deadline_workspace_changed', handleWorkspaceChange);
  }, [fetchData]);

  // Open Drawer and load reminder history
  const handleOpenDetail = async (item: PriorityReceivableItem) => {
    setSelectedReceivable(item);
    setIsDetailDrawerOpen(true);
    setLoadingHistory(true);
    try {
      const res = await api.listCollectionReminders(item.invoice_id);
      setReminderHistory(res?.data?.reminders || []);
    } catch {
      setReminderHistory([]);
    } finally {
      setLoadingHistory(false);
    }
  };

  // Launch reminder modal
  const handleLaunchReminder = (invoiceId: string, recommendedTone: string = 'POLITE') => {
    setActiveInvoiceForReminder(invoiceId);
    setActiveToneForReminder(recommendedTone);
    setIsReminderModalOpen(true);
  };

  // Filter priorities list
  const filteredPriorities = useMemo(() => {
    return priorities.filter(item => {
      if (bucketFilter === '1_to_30_days' && (item.days_overdue < 1 || item.days_overdue > 30)) return false;
      if (bucketFilter === '31_to_60_days' && (item.days_overdue < 31 || item.days_overdue > 60)) return false;
      if (bucketFilter === '61_to_90_days' && (item.days_overdue < 61 || item.days_overdue > 90)) return false;
      if (bucketFilter === '90_plus_days' && item.days_overdue < 91) return false;

      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const pName = item.partner_name?.toLowerCase() || '';
        const invNum = item.invoice_number?.toLowerCase() || '';
        if (!pName.includes(q) && !invNum.includes(q)) return false;
      }
      return true;
    });
  }, [priorities, bucketFilter, searchQuery]);

  // Tone badge visual helper
  const renderToneBadge = (tone: string) => {
    switch (tone) {
      case 'GENTLE':
        return <span className="px-2 py-0.5 rounded-md bg-blue-500/10 text-blue-400 border border-blue-500/20 text-xs font-semibold">Gentle</span>;
      case 'POLITE':
        return <span className="px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-semibold">Polite</span>;
      case 'URGENT':
        return <span className="px-2 py-0.5 rounded-md bg-amber-500/10 text-amber-400 border border-amber-500/20 text-xs font-semibold">Urgent</span>;
      case 'LEGAL':
        return <span className="px-2 py-0.5 rounded-md bg-rose-500/10 text-rose-400 border border-rose-500/20 text-xs font-semibold">Legal Notice</span>;
      default:
        return <span className="px-2 py-0.5 rounded-md bg-slate-500/10 text-slate-400 border border-slate-500/20 text-xs font-semibold">{tone}</span>;
    }
  };

  const renderOverdueBadge = (days: number) => {
    let color = 'bg-amber-500/10 text-amber-400 border-amber-500/20';
    if (days > 90) {
      color = 'bg-rose-500/20 text-rose-400 border-rose-500/40 animate-pulse';
    } else if (days > 60) {
      color = 'bg-rose-500/10 text-rose-400 border-rose-500/20';
    } else if (days > 30) {
      color = 'bg-orange-500/10 text-orange-400 border-orange-500/20';
    }
    return (
      <span className={`px-2.5 py-0.5 rounded-full border text-xs font-mono font-bold ${color}`}>
        {days}d overdue
      </span>
    );
  };

  const columns = [
    {
      key: 'customer',
      header: 'Counterparty / Customer',
      accessor: (item: PriorityReceivableItem) => (
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-slate-800/80 border border-slate-700/50 flex items-center justify-center text-slate-200 font-bold text-xs">
            {item.partner_name?.slice(0, 2).toUpperCase() || 'CU'}
          </div>
          <div>
            <div className="text-xs font-semibold text-white">{item.partner_name}</div>
            <div className="text-[10px] text-slate-400 font-mono">{item.invoice_number}</div>
          </div>
        </div>
      ),
    },
    {
      key: 'delinquency',
      header: 'Delinquency',
      accessor: (item: PriorityReceivableItem) => renderOverdueBadge(item.days_overdue),
    },
    {
      key: 'due_date',
      header: 'Due Date',
      accessor: (item: PriorityReceivableItem) => (
        <span className="text-xs text-slate-300 font-mono">{item.due_date}</span>
      ),
    },
    {
      key: 'balance',
      header: 'Outstanding Balance',
      accessor: (item: PriorityReceivableItem) => (
        <FinancialNumber value={item.balance_due} currency="INR" />
      ),
    },
    {
      key: 'tone',
      header: 'Recommended Tone',
      accessor: (item: PriorityReceivableItem) => renderToneBadge(item.recommended_tone),
    },
    {
      key: 'actions',
      header: 'Recovery Action',
      accessor: (item: PriorityReceivableItem) => (
        <div className="flex items-center gap-2">
          {canWrite && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleLaunchReminder(item.invoice_id, item.recommended_tone);
              }}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-colors shadow-sm cursor-pointer"
            >
              <Send className="w-3 h-3" />
              <span>Draft Reminder</span>
            </button>
          )}
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleOpenDetail(item);
            }}
            className="p-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors border border-slate-700/60 cursor-pointer"
            title="Inspect Receivable"
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
          { label: 'Receivable Rescue' },
        ]}
        title="Receivable Rescue & Debt Recovery"
        description="Deterministic cash aging analysis and prioritized recovery workflows with human-approved communication dispatch."
        secondaryActions={[
          {
            label: loading ? 'Syncing...' : 'Refresh Aging',
            icon: RefreshCw,
            onClick: fetchData,
          },
        ]}
      />

      {/* Operations Sub Nav */}
      <OperationsSubNav />

      {/* Deterministic Aging Summary KPI Strip */}
      {aging && (
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-3.5">
          {/* Total Overdue */}
          <div className="col-span-2 lg:col-span-1 p-4 rounded-2xl bg-rose-500/5 border border-rose-500/20 backdrop-blur-md">
            <div className="flex items-center justify-between text-rose-400 text-xs font-semibold">
              <span>Total Overdue</span>
              <ShieldAlert className="w-4 h-4 text-rose-400" />
            </div>
            <div className="text-xl font-bold text-white mt-1">
              <FinancialNumber value={aging.total_overdue_amount} currency="INR" />
            </div>
            <div className="text-[11px] text-slate-400 mt-0.5">
              {aging.total_overdue_count} Delinquent Invoices
            </div>
          </div>

          {/* 1-30 Days */}
          <div
            onClick={() => setBucketFilter(bucketFilter === '1_to_30_days' ? 'ALL' : '1_to_30_days')}
            className={`p-4 rounded-2xl bg-slate-900/60 border transition-all cursor-pointer ${
              bucketFilter === '1_to_30_days' ? 'border-amber-500 bg-amber-500/5 shadow-md' : 'border-slate-800 hover:border-slate-700'
            }`}
          >
            <div className="text-xs font-medium text-amber-400">1–30 Days Overdue</div>
            <div className="text-lg font-bold text-white mt-1">
              <FinancialNumber value={aging.buckets['1_to_30_days'].total} currency="INR" />
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">
              {aging.buckets['1_to_30_days'].count} Invoices
            </div>
          </div>

          {/* 31-60 Days */}
          <div
            onClick={() => setBucketFilter(bucketFilter === '31_to_60_days' ? 'ALL' : '31_to_60_days')}
            className={`p-4 rounded-2xl bg-slate-900/60 border transition-all cursor-pointer ${
              bucketFilter === '31_to_60_days' ? 'border-orange-500 bg-orange-500/5 shadow-md' : 'border-slate-800 hover:border-slate-700'
            }`}
          >
            <div className="text-xs font-medium text-orange-400">31–60 Days Overdue</div>
            <div className="text-lg font-bold text-white mt-1">
              <FinancialNumber value={aging.buckets['31_to_60_days'].total} currency="INR" />
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">
              {aging.buckets['31_to_60_days'].count} Invoices
            </div>
          </div>

          {/* 61-90 Days */}
          <div
            onClick={() => setBucketFilter(bucketFilter === '61_to_90_days' ? 'ALL' : '61_to_90_days')}
            className={`p-4 rounded-2xl bg-slate-900/60 border transition-all cursor-pointer ${
              bucketFilter === '61_to_90_days' ? 'border-rose-500 bg-rose-500/5 shadow-md' : 'border-slate-800 hover:border-slate-700'
            }`}
          >
            <div className="text-xs font-medium text-rose-400">61–90 Days Overdue</div>
            <div className="text-lg font-bold text-white mt-1">
              <FinancialNumber value={aging.buckets['61_to_90_days'].total} currency="INR" />
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">
              {aging.buckets['61_to_90_days'].count} Invoices
            </div>
          </div>

          {/* 90+ Days */}
          <div
            onClick={() => setBucketFilter(bucketFilter === '90_plus_days' ? 'ALL' : '90_plus_days')}
            className={`p-4 rounded-2xl bg-slate-900/60 border transition-all cursor-pointer ${
              bucketFilter === '90_plus_days' ? 'border-rose-600 bg-rose-600/10 shadow-md' : 'border-slate-800 hover:border-slate-700'
            }`}
          >
            <div className="text-xs font-medium text-rose-500 flex items-center gap-1">
              <AlertTriangle className="w-3 h-3 text-rose-500" />
              <span>90+ Days (Critical)</span>
            </div>
            <div className="text-lg font-bold text-white mt-1">
              <FinancialNumber value={aging.buckets['90_plus_days'].total} currency="INR" />
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">
              {aging.buckets['90_plus_days'].count} Invoices
            </div>
          </div>
        </div>
      )}

      {/* Filter & Search Bar */}
      <div className="flex flex-col md:flex-row gap-3 items-center justify-between p-4 rounded-2xl bg-slate-900/40 border border-slate-800/80">
        <div className="flex flex-wrap gap-2 items-center w-full md:w-auto">
          <div className="flex rounded-xl bg-slate-950 p-1 border border-slate-800 text-xs">
            {['ALL', '1_to_30_days', '31_to_60_days', '61_to_90_days', '90_plus_days'].map(b => (
              <button
                key={b}
                onClick={() => setBucketFilter(b)}
                className={`px-3 py-1.5 rounded-lg font-semibold transition-colors cursor-pointer ${
                  bucketFilter === b ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {b === 'ALL' ? 'All Tiers' : b.replace(/_/g, ' ')}
              </button>
            ))}
          </div>
        </div>

        {/* Search Field */}
        <div className="relative w-full md:w-72">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search customer or invoice..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
        </div>
      </div>

      {/* Main Priority Queue */}
      {loading ? (
        <BusinessLoadingState type="table" rows={6} />
      ) : error ? (
        <BusinessErrorState message={error} onRetry={fetchData} />
      ) : filteredPriorities.length === 0 ? (
        <BusinessEmptyState
          title="No Overdue Receivables in this Tier"
          description="All customer invoices are currently paid or within standard payment terms."
        />
      ) : (
        <BusinessDataTable
          columns={columns}
          data={filteredPriorities}
          keyExtractor={(item) => item.invoice_id}
          onRowClick={(item) => handleOpenDetail(item)}
        />
      )}

      {/* Detail Drawer */}
      <DetailDrawer
        isOpen={isDetailDrawerOpen && !!selectedReceivable}
        onClose={() => setIsDetailDrawerOpen(false)}
        title="Receivable Recovery Record"
        subtitle={`Invoice: ${selectedReceivable?.invoice_number || ''}`}
        status={selectedReceivable && selectedReceivable.days_overdue > 60 ? 'OVERDUE' : 'ISSUED'}
      >
        {selectedReceivable && (
          <div className="space-y-6">
            {/* Metadata Summary */}
            <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-3">
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-400">Customer:</span>
                <span className="text-white font-semibold">{selectedReceivable.partner_name}</span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-400">Due Date:</span>
                <span className="text-slate-300 font-mono">{selectedReceivable.due_date}</span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-400">Delinquency:</span>
                {renderOverdueBadge(selectedReceivable.days_overdue)}
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-400">Outstanding Balance:</span>
                <FinancialNumber value={selectedReceivable.balance_due} currency="INR" />
              </div>
            </div>

            {/* Recommended Action */}
            <div className="p-4 rounded-2xl bg-indigo-500/5 border border-indigo-500/20 space-y-2">
              <div className="flex items-center gap-2 text-indigo-400 font-semibold text-xs">
                <span>Deterministic Action Advisory</span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                Recommended communication tone is <strong>{selectedReceivable.recommended_tone}</strong> based on {selectedReceivable.days_overdue} days delinquency and outstanding exposure of ₹{selectedReceivable.balance_due}.
              </p>
              {canWrite && (
                <button
                  onClick={() => {
                    setIsDetailDrawerOpen(false);
                    handleLaunchReminder(selectedReceivable.invoice_id, selectedReceivable.recommended_tone);
                  }}
                  className="w-full mt-2 flex items-center justify-center gap-2 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition-colors cursor-pointer"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>Draft & Review Reminder</span>
                </button>
              )}
            </div>

            {/* Reminder History Log */}
            <div className="space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <History className="w-3.5 h-3.5" />
                <span>Reminder Dispatch History</span>
              </h4>

              {loadingHistory ? (
                <div className="text-xs text-slate-500 italic p-3 bg-slate-950 rounded-xl border border-slate-800">
                  Loading reminder history...
                </div>
              ) : reminderHistory.length === 0 ? (
                <div className="text-xs text-slate-500 italic p-3 bg-slate-950 rounded-xl border border-slate-800">
                  No previous reminders dispatched for this invoice.
                </div>
              ) : (
                <div className="divide-y divide-slate-800/80 rounded-xl bg-slate-950 border border-slate-800 overflow-hidden">
                  {reminderHistory.map(rem => (
                    <div key={rem.id} className="p-3 space-y-1 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-white capitalize">{rem.tone.toLowerCase()} Tone</span>
                        <StatusBadge status={rem.status} />
                      </div>
                      <p className="text-[11px] text-slate-400 line-clamp-2">
                        {rem.custom_message || rem.message_body || 'No message content'}
                      </p>
                      <div className="text-[10px] text-slate-500 font-mono">
                        {rem.sent_at ? `Dispatched on ${new Date(rem.sent_at).toLocaleDateString()}` : `Drafted on ${new Date(rem.created_at).toLocaleDateString()}`}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </DetailDrawer>

      {/* Reminder Dispatch Modal */}
      <ReminderModal
        isOpen={isReminderModalOpen}
        onClose={() => {
          setIsReminderModalOpen(false);
          setActiveInvoiceForReminder(null);
          fetchData();
        }}
        invoiceId={activeInvoiceForReminder}
        initialTone={activeToneForReminder}
      />
    </div>
  );
};
