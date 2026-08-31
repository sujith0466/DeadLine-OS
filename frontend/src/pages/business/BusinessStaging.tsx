import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  Inbox,
  Plus,
  Search,
  CheckCircle2,
  XCircle,
  Clock,
  ArrowRight,
  ShieldCheck,
  AlertTriangle,
  Check,
  Trash2,
  Eye,
  RefreshCw,
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
import { CaptureModal } from '../../components/Business/CaptureModal';

export interface StagedExtractionItem {
  id: string;
  workspace_id: string;
  source_channel: string;
  candidate_type: 'EXPENSE' | 'INVOICE_RECEIVABLE' | 'INVOICE_PAYABLE' | 'PAYMENT_RECORD' | 'NOTE';
  status: 'NEEDS_REVIEW' | 'CONFIRMED' | 'REJECTED';
  confidence_score: number;
  normalized_data: {
    amount?: string;
    currency?: string;
    date?: string;
    partner_id?: string | null;
    partner_name?: string | null;
    description?: string | null;
    category?: string | null;
    reference_number?: string | null;
  };
  raw_extracted_data?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export const BusinessStaging: React.FC = () => {
  const { activeWorkspace, role } = useBusinessAuth();

  const [items, setItems] = useState<StagedExtractionItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filter & Search states
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [candidateTypeFilter, setCandidateTypeFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Modals & Drawers
  const [isCaptureModalOpen, setIsCaptureModalOpen] = useState<boolean>(false);
  const [selectedItem, setSelectedItem] = useState<StagedExtractionItem | null>(null);
  const [isDetailDrawerOpen, setIsDetailDrawerOpen] = useState<boolean>(false);

  // Review Drawer Form State
  const [editCandidateType, setEditCandidateType] = useState<string>('EXPENSE');
  const [editAmount, setEditAmount] = useState<string>('');
  const [editCurrency, setEditCurrency] = useState<string>('INR');
  const [editDate, setEditDate] = useState<string>('');
  const [editPartnerName, setEditPartnerName] = useState<string>('');
  const [editDescription, setEditDescription] = useState<string>('');
  const [editCategory, setEditCategory] = useState<string>('');
  const [editReferenceNumber, setEditReferenceNumber] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'review' | 'raw' | 'provenance'>('review');

  // Mutation states
  const [isRejecting, setIsRejecting] = useState<boolean>(false);
  const [rejectReason, setRejectReason] = useState<string>('');
  const [commitTargetDomain, setCommitTargetDomain] = useState<'INVOICE' | 'TRANSACTION'>('TRANSACTION');
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const canWrite = role === 'OWNER' || role === 'ADMIN' || role === 'ACCOUNTANT';

  // Load items from backend
  const loadStagingItems = useCallback(async () => {
    if (!activeWorkspace) return;
    setLoading(true);
    setError(null);
    try {
      const params: any = { limit: 100 };
      if (statusFilter !== 'ALL') params.status = statusFilter;
      if (candidateTypeFilter !== 'ALL') params.candidate_type = candidateTypeFilter;

      const res = await api.listStagedItems(params);
      const fetched: StagedExtractionItem[] = res?.data?.staged_items || [];
      setItems(fetched);
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || err?.message || 'Failed to load staged items.');
    } finally {
      setLoading(false);
    }
  }, [activeWorkspace, statusFilter, candidateTypeFilter]);

  useEffect(() => {
    loadStagingItems();
  }, [loadStagingItems]);

  // Reactive listener for workspace switching
  useEffect(() => {
    const handleWorkspaceChange = () => {
      loadStagingItems();
    };
    window.addEventListener('deadline_workspace_changed', handleWorkspaceChange);
    return () => window.removeEventListener('deadline_workspace_changed', handleWorkspaceChange);
  }, [loadStagingItems]);

  // Handle opening review drawer
  const handleOpenReview = (item: StagedExtractionItem) => {
    setSelectedItem(item);
    setEditCandidateType(item.candidate_type || 'EXPENSE');
    setEditAmount(item.normalized_data?.amount || '');
    setEditCurrency(item.normalized_data?.currency || 'INR');
    setEditDate(item.normalized_data?.date || '');
    setEditPartnerName(item.normalized_data?.partner_name || '');
    setEditDescription(item.normalized_data?.description || '');
    setEditCategory(item.normalized_data?.category || '');
    setEditReferenceNumber(item.normalized_data?.reference_number || '');
    setActiveTab('review');
    setIsRejecting(false);
    setRejectReason('');
    setActionError(null);
    setActionSuccess(null);
    setIsDetailDrawerOpen(true);
  };

  // Handle Save Draft Update
  const handleSaveDraft = async () => {
    if (!selectedItem) return;
    setActionLoading(true);
    setActionError(null);
    setActionSuccess(null);
    try {
      const res = await api.updateStagedItem(selectedItem.id, {
        candidate_type: editCandidateType,
        normalized_data: {
          amount: editAmount,
          currency: editCurrency,
          date: editDate,
          partner_name: editPartnerName,
          description: editDescription,
          category: editCategory,
          reference_number: editReferenceNumber,
        },
      });
      const updated: StagedExtractionItem = res.data.staged_extraction;
      setSelectedItem(updated);
      setActionSuccess('Candidate fields updated.');
      loadStagingItems();
    } catch (err: any) {
      setActionError(err?.response?.data?.error?.message || err?.message || 'Failed to update candidate.');
    } finally {
      setActionLoading(false);
    }
  };

  // Handle Confirm Candidate
  const handleConfirm = async () => {
    if (!selectedItem) return;
    setActionLoading(true);
    setActionError(null);
    setActionSuccess(null);
    try {
      await handleSaveDraft();
      const res = await api.confirmStagedItem(selectedItem.id);
      const confirmed: StagedExtractionItem = res.data.staged_extraction;
      setSelectedItem(confirmed);
      setActionSuccess('Candidate confirmed and approved for ledger commit.');
      loadStagingItems();
    } catch (err: any) {
      setActionError(err?.response?.data?.error?.message || err?.message || 'Failed to confirm candidate.');
    } finally {
      setActionLoading(false);
    }
  };

  // Handle Reject Candidate
  const handleReject = async () => {
    if (!selectedItem) return;
    if (!rejectReason.trim()) {
      setActionError('Please specify a rejection reason.');
      return;
    }
    setActionLoading(true);
    setActionError(null);
    setActionSuccess(null);
    try {
      const res = await api.rejectStagedItem(selectedItem.id, rejectReason.trim());
      const rejected: StagedExtractionItem = res.data.staged_extraction;
      setSelectedItem(rejected);
      setActionSuccess('Candidate rejected and archived.');
      setIsRejecting(false);
      loadStagingItems();
    } catch (err: any) {
      setActionError(err?.response?.data?.error?.message || err?.message || 'Failed to reject candidate.');
    } finally {
      setActionLoading(false);
    }
  };

  // Handle Commit to Financial Ledger
  const handleCommit = async () => {
    if (!selectedItem) return;
    setActionLoading(true);
    setActionError(null);
    setActionSuccess(null);
    try {
      const res = await api.commitStagedItem(selectedItem.id, commitTargetDomain);
      setActionSuccess(res?.message || 'Successfully committed to authoritative financial ledger!');
      setTimeout(() => {
        setIsDetailDrawerOpen(false);
        setSelectedItem(null);
        loadStagingItems();
      }, 1200);
    } catch (err: any) {
      setActionError(err?.response?.data?.error?.message || err?.message || 'Failed to commit to ledger.');
    } finally {
      setActionLoading(false);
    }
  };

  // Filter items in memory for search
  const filteredItems = useMemo(() => {
    if (!searchQuery.trim()) return items;
    const q = searchQuery.toLowerCase();
    return items.filter(item => {
      const pName = item.normalized_data?.partner_name?.toLowerCase() || '';
      const desc = item.normalized_data?.description?.toLowerCase() || '';
      const cat = item.normalized_data?.category?.toLowerCase() || '';
      const ref = item.normalized_data?.reference_number?.toLowerCase() || '';
      const cType = item.candidate_type.toLowerCase();
      return pName.includes(q) || desc.includes(q) || cat.includes(q) || ref.includes(q) || cType.includes(q);
    });
  }, [items, searchQuery]);

  // Operational Queue KPIs
  const kpis = useMemo(() => {
    const pending = items.filter(i => i.status === 'NEEDS_REVIEW').length;
    const confirmed = items.filter(i => i.status === 'CONFIRMED').length;
    const rejected = items.filter(i => i.status === 'REJECTED').length;
    return {
      total: items.length,
      pending,
      confirmed,
      rejected,
    };
  }, [items]);

  // Candidate type visual helper
  const renderCandidateTypeBadge = (type: string) => {
    switch (type) {
      case 'EXPENSE':
        return <span className="px-2 py-0.5 rounded-md bg-rose-500/10 text-rose-400 border border-rose-500/20 text-xs font-semibold">Expense</span>;
      case 'INVOICE_RECEIVABLE':
        return <span className="px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-semibold">Invoice Receivable</span>;
      case 'INVOICE_PAYABLE':
        return <span className="px-2 py-0.5 rounded-md bg-amber-500/10 text-amber-400 border border-amber-500/20 text-xs font-semibold">Invoice Payable</span>;
      case 'PAYMENT_RECORD':
        return <span className="px-2 py-0.5 rounded-md bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 text-xs font-semibold">Payment</span>;
      case 'NOTE':
      default:
        return <span className="px-2 py-0.5 rounded-md bg-slate-500/10 text-slate-400 border border-slate-500/20 text-xs font-semibold">Note</span>;
    }
  };

  // Confidence score badge
  const renderConfidenceBadge = (score: number) => {
    let colorClass = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
    if (score < 50) {
      colorClass = 'bg-rose-500/10 text-rose-400 border-rose-500/20';
    } else if (score < 80) {
      colorClass = 'bg-amber-500/10 text-amber-400 border-amber-500/20';
    }
    return (
      <span className={`px-2 py-0.5 rounded-full border text-[11px] font-mono font-bold ${colorClass}`}>
        {score}%
      </span>
    );
  };

  const columns = [
    {
      key: 'source',
      header: 'Source / Channel',
      accessor: (item: StagedExtractionItem) => (
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-slate-800/80 border border-slate-700/50 flex items-center justify-center text-slate-300 font-bold text-xs capitalize">
            {item.source_channel === 'DOCUMENT' ? 'DOC' : item.source_channel === 'VOICE' ? 'MIC' : 'TXT'}
          </div>
          <div>
            <div className="text-xs font-semibold text-white capitalize">{item.source_channel.toLowerCase()}</div>
            <div className="text-[10px] text-slate-400 font-mono">{item.id.slice(0, 8)}...</div>
          </div>
        </div>
      ),
    },
    {
      key: 'type',
      header: 'Candidate Type',
      accessor: (item: StagedExtractionItem) => renderCandidateTypeBadge(item.candidate_type),
    },
    {
      key: 'partner',
      header: 'Counterparty / Details',
      accessor: (item: StagedExtractionItem) => (
        <div>
          <div className="text-xs font-semibold text-white">
            {item.normalized_data?.partner_name || 'Unassigned Counterparty'}
          </div>
          <div className="text-[11px] text-slate-400 truncate max-w-xs">
            {item.normalized_data?.description || item.normalized_data?.category || 'No memo extracted'}
          </div>
        </div>
      ),
    },
    {
      key: 'date',
      header: 'Date',
      accessor: (item: StagedExtractionItem) => (
        <span className="text-xs text-slate-300 font-mono">
          {item.normalized_data?.date || '—'}
        </span>
      ),
    },
    {
      key: 'amount',
      header: 'Amount',
      accessor: (item: StagedExtractionItem) => (
        item.normalized_data?.amount ? (
          <FinancialNumber
            value={item.normalized_data.amount}
            currency={item.normalized_data.currency || 'INR'}
          />
        ) : (
          <span className="text-xs text-slate-500 font-mono">—</span>
        )
      ),
    },
    {
      key: 'confidence',
      header: 'Confidence',
      accessor: (item: StagedExtractionItem) => renderConfidenceBadge(item.confidence_score),
    },
    {
      key: 'status',
      header: 'Status',
      accessor: (item: StagedExtractionItem) => <StatusBadge status={item.status} />,
    },
    {
      key: 'action',
      header: 'Action',
      accessor: (item: StagedExtractionItem) => (
        <button
          onClick={(e) => {
            e.stopPropagation();
            handleOpenReview(item);
          }}
          className="flex items-center gap-1 px-2.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-colors border border-slate-700/60 cursor-pointer"
        >
          <Eye className="w-3.5 h-3.5" />
          <span>{item.status === 'NEEDS_REVIEW' ? 'Review' : 'Inspect'}</span>
        </button>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <BusinessPageHeader
        breadcrumbs={[
          { label: 'Operations', href: '/business/staging' },
          { label: 'Staging Queue' },
        ]}
        title="Operational Staging & Review Queue"
        description="Human-in-the-loop review and verification barrier for captured receipts, invoices, and ledger notes."
        primaryAction={
          canWrite
            ? {
                label: 'Capture Entry',
                icon: Plus,
                onClick: () => setIsCaptureModalOpen(true),
              }
            : undefined
        }
        secondaryActions={[
          {
            label: 'Refresh',
            icon: RefreshCw,
            onClick: loadStagingItems,
          },
        ]}
      />

      {/* Sub Domain Nav */}
      <OperationsSubNav />

      {/* Operational KPI Metric Strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-md">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Total Captured</span>
            <Inbox className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold text-white mt-1 font-mono">{kpis.total}</div>
          <div className="text-[11px] text-slate-500 mt-0.5">Ingested via Text & Uploads</div>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-md">
          <div className="flex items-center justify-between text-amber-400 text-xs font-medium">
            <span>Awaiting Review</span>
            <Clock className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-amber-400 mt-1 font-mono">{kpis.pending}</div>
          <div className="text-[11px] text-slate-500 mt-0.5">Requires Human Approval</div>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-md">
          <div className="flex items-center justify-between text-emerald-400 text-xs font-medium">
            <span>Approved & Verified</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400 mt-1 font-mono">{kpis.confirmed}</div>
          <div className="text-[11px] text-slate-500 mt-0.5">Ready for Ledger Commit</div>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-md">
          <div className="flex items-center justify-between text-rose-400 text-xs font-medium">
            <span>Rejected / Discarded</span>
            <XCircle className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-bold text-slate-400 mt-1 font-mono">{kpis.rejected}</div>
          <div className="text-[11px] text-slate-500 mt-0.5">Audited Rejections</div>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="flex flex-col md:flex-row gap-3 items-center justify-between p-4 rounded-2xl bg-slate-900/40 border border-slate-800/80">
        <div className="flex flex-wrap gap-2 items-center w-full md:w-auto">
          {/* Status Filter */}
          <div className="flex rounded-xl bg-slate-950 p-1 border border-slate-800 text-xs">
            {['ALL', 'NEEDS_REVIEW', 'CONFIRMED', 'REJECTED'].map(st => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-3 py-1.5 rounded-lg font-semibold transition-colors cursor-pointer ${
                  statusFilter === st ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {st.replace('_', ' ')}
              </button>
            ))}
          </div>

          {/* Candidate Type Filter */}
          <select
            value={candidateTypeFilter}
            onChange={e => setCandidateTypeFilter(e.target.value)}
            className="px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 cursor-pointer"
          >
            <option value="ALL">All Types</option>
            <option value="EXPENSE">Expense</option>
            <option value="INVOICE_RECEIVABLE">Invoice Receivable</option>
            <option value="INVOICE_PAYABLE">Invoice Payable</option>
            <option value="PAYMENT_RECORD">Payment</option>
            <option value="NOTE">Note</option>
          </select>
        </div>

        {/* Search Field */}
        <div className="relative w-full md:w-72">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search counterparty or memo..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
        </div>
      </div>

      {/* Main Content Area */}
      {loading ? (
        <BusinessLoadingState type="table" rows={6} />
      ) : error ? (
        <BusinessErrorState message={error} onRetry={loadStagingItems} />
      ) : filteredItems.length === 0 ? (
        <BusinessEmptyState
          title="Staging Queue is Empty"
          description="All captured receipts and natural-language inputs have been reviewed and committed."
          actionLabel={canWrite ? "Capture New Input" : undefined}
          onAction={canWrite ? () => setIsCaptureModalOpen(true) : undefined}
        />
      ) : (
        <BusinessDataTable
          columns={columns}
          data={filteredItems}
          keyExtractor={(item) => item.id}
          onRowClick={(item) => handleOpenReview(item)}
        />
      )}

      {/* Interactive Review Drawer */}
      <DetailDrawer
        isOpen={isDetailDrawerOpen && !!selectedItem}
        onClose={() => setIsDetailDrawerOpen(false)}
        title="Review Staged Candidate"
        subtitle={`Candidate ID: ${selectedItem?.id || ''}`}
        status={selectedItem?.status}
      >
        {selectedItem && (
          <div className="space-y-6">
            {/* Tabs */}
            <div className="flex border-b border-slate-800 text-xs">
              <button
                onClick={() => setActiveTab('review')}
                className={`pb-2 px-3 font-semibold border-b-2 transition-colors cursor-pointer ${
                  activeTab === 'review' ? 'border-emerald-500 text-emerald-400' : 'border-transparent text-slate-400 hover:text-white'
                }`}
              >
                Review & Edit
              </button>
              <button
                onClick={() => setActiveTab('raw')}
                className={`pb-2 px-3 font-semibold border-b-2 transition-colors cursor-pointer ${
                  activeTab === 'raw' ? 'border-emerald-500 text-emerald-400' : 'border-transparent text-slate-400 hover:text-white'
                }`}
              >
                Raw Capture Content
              </button>
              <button
                onClick={() => setActiveTab('provenance')}
                className={`pb-2 px-3 font-semibold border-b-2 transition-colors cursor-pointer ${
                  activeTab === 'provenance' ? 'border-emerald-500 text-emerald-400' : 'border-transparent text-slate-400 hover:text-white'
                }`}
              >
                Provenance & Audit
              </button>
            </div>

            {/* Action Feedback */}
            {actionError && (
              <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>{actionError}</span>
              </div>
            )}
            {actionSuccess && (
              <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                <span>{actionSuccess}</span>
              </div>
            )}

            {/* TAB 1: Review & Edit */}
            {activeTab === 'review' && (
              <div className="space-y-4">
                <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 flex items-center justify-between text-xs">
                  <span className="text-slate-400">
                    Channel: <strong className="text-white capitalize">{selectedItem.source_channel.toLowerCase()}</strong>
                  </span>
                  <div className="flex items-center gap-2">
                    <span className="text-slate-400 text-[11px]">AI Confidence:</span>
                    {renderConfidenceBadge(selectedItem.confidence_score)}
                  </div>
                </div>

                <div className="space-y-3">
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1">Candidate Domain Type</label>
                    <select
                      value={editCandidateType}
                      disabled={!canWrite || selectedItem.status !== 'NEEDS_REVIEW'}
                      onChange={e => setEditCandidateType(e.target.value)}
                      className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-indigo-500 disabled:opacity-60"
                    >
                      <option value="EXPENSE">Expense (Money Out)</option>
                      <option value="INVOICE_RECEIVABLE">Invoice Receivable (Customer Inflow)</option>
                      <option value="INVOICE_PAYABLE">Invoice Payable (Vendor Outflow)</option>
                      <option value="PAYMENT_RECORD">Payment Record</option>
                      <option value="NOTE">General Business Note</option>
                    </select>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-semibold text-slate-400 mb-1">Amount</label>
                      <input
                        type="text"
                        value={editAmount}
                        disabled={!canWrite || selectedItem.status !== 'NEEDS_REVIEW'}
                        onChange={e => setEditAmount(e.target.value)}
                        placeholder="0.00"
                        className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-indigo-500 font-mono disabled:opacity-60"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-slate-400 mb-1">Date</label>
                      <input
                        type="date"
                        value={editDate}
                        disabled={!canWrite || selectedItem.status !== 'NEEDS_REVIEW'}
                        onChange={e => setEditDate(e.target.value)}
                        className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-indigo-500 disabled:opacity-60"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1">Counterparty / Partner</label>
                    <input
                      type="text"
                      value={editPartnerName}
                      disabled={!canWrite || selectedItem.status !== 'NEEDS_REVIEW'}
                      onChange={e => setEditPartnerName(e.target.value)}
                      placeholder="e.g. Acme Corp, AWS, Client Name"
                      className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-indigo-500 disabled:opacity-60"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1">Description / Notes</label>
                    <textarea
                      rows={2}
                      value={editDescription}
                      disabled={!canWrite || selectedItem.status !== 'NEEDS_REVIEW'}
                      onChange={e => setEditDescription(e.target.value)}
                      placeholder="Summary of the captured financial event"
                      className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-indigo-500 disabled:opacity-60"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-semibold text-slate-400 mb-1">Category</label>
                      <input
                        type="text"
                        value={editCategory}
                        disabled={!canWrite || selectedItem.status !== 'NEEDS_REVIEW'}
                        onChange={e => setEditCategory(e.target.value)}
                        placeholder="e.g. SOFTWARE, RENT"
                        className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-indigo-500 disabled:opacity-60"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-slate-400 mb-1">Reference Number</label>
                      <input
                        type="text"
                        value={editReferenceNumber}
                        disabled={!canWrite || selectedItem.status !== 'NEEDS_REVIEW'}
                        onChange={e => setEditReferenceNumber(e.target.value)}
                        placeholder="e.g. INV-1002"
                        className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-indigo-500 disabled:opacity-60"
                      />
                    </div>
                  </div>
                </div>

                {/* Review Decision Buttons */}
                {canWrite && selectedItem.status === 'NEEDS_REVIEW' && (
                  <div className="pt-4 border-t border-slate-800 space-y-3">
                    {isRejecting ? (
                      <div className="p-3 bg-rose-500/10 rounded-xl border border-rose-500/20 space-y-2">
                        <label className="block text-xs font-semibold text-rose-400">Reason for Rejection</label>
                        <input
                          type="text"
                          placeholder="e.g. Duplicate receipt or personal transaction"
                          value={rejectReason}
                          onChange={e => setRejectReason(e.target.value)}
                          className="w-full px-3 py-2 rounded-lg bg-black/40 border border-rose-500/30 text-xs text-white focus:outline-none"
                        />
                        <div className="flex gap-2 justify-end">
                          <button
                            onClick={() => setIsRejecting(false)}
                            className="px-3 py-1.5 text-xs text-slate-400 hover:text-white cursor-pointer"
                          >
                            Cancel
                          </button>
                          <button
                            onClick={handleReject}
                            disabled={actionLoading}
                            className="px-4 py-1.5 text-xs bg-rose-500 hover:bg-rose-600 text-white font-semibold rounded-lg cursor-pointer"
                          >
                            {actionLoading ? 'Rejecting...' : 'Confirm Rejection'}
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="flex items-center justify-between">
                        <button
                          onClick={() => setIsRejecting(true)}
                          className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold text-rose-400 hover:bg-rose-500/10 transition-colors cursor-pointer"
                        >
                          <Trash2 className="w-4 h-4" />
                          <span>Reject Candidate</span>
                        </button>

                        <div className="flex gap-2">
                          <button
                            onClick={handleSaveDraft}
                            disabled={actionLoading}
                            className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-300 bg-slate-800 hover:bg-slate-700 transition-colors cursor-pointer"
                          >
                            Save Draft
                          </button>
                          <button
                            onClick={handleConfirm}
                            disabled={actionLoading}
                            className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold text-black bg-emerald-500 hover:bg-emerald-600 transition-colors shadow-lg shadow-emerald-500/10 cursor-pointer"
                          >
                            <Check className="w-4 h-4" />
                            <span>Confirm & Approve</span>
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Commit Action for Approved Items */}
                {canWrite && selectedItem.status === 'CONFIRMED' && (
                  <div className="p-4 rounded-2xl bg-emerald-500/5 border border-emerald-500/20 space-y-3">
                    <div className="flex items-center gap-2 text-emerald-400 font-semibold text-xs">
                      <ShieldCheck className="w-4 h-4" />
                      <span>Ready for Authoritative Ledger Commitment</span>
                    </div>
                    <p className="text-xs text-slate-400">
                      This item has passed the human confirmation barrier. Commit it into the permanent business ledger.
                    </p>

                    <div className="flex items-center gap-3">
                      <select
                        value={commitTargetDomain}
                        onChange={e => setCommitTargetDomain(e.target.value as any)}
                        className="px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none"
                      >
                        <option value="TRANSACTION">Commit as Transaction (Ledger Record)</option>
                        <option value="INVOICE">Commit as Commercial Invoice</option>
                      </select>

                      <button
                        onClick={handleCommit}
                        disabled={actionLoading}
                        className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold text-black bg-emerald-500 hover:bg-emerald-600 transition-colors shadow-lg shadow-emerald-500/10 cursor-pointer"
                      >
                        <ArrowRight className="w-4 h-4" />
                        <span>{actionLoading ? 'Committing...' : 'Commit to Ledger'}</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* TAB 2: Raw Capture Content */}
            {activeTab === 'raw' && (
              <div className="space-y-3">
                <div className="text-xs text-slate-400">
                  Unprocessed extracted JSON payload from the AI extraction pipeline:
                </div>
                <pre className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-[11px] text-slate-300 font-mono overflow-x-auto max-h-96">
                  {JSON.stringify(selectedItem.raw_extracted_data || selectedItem.normalized_data, null, 2)}
                </pre>
              </div>
            )}

            {/* TAB 3: Provenance & Audit */}
            {activeTab === 'provenance' && (
              <div className="space-y-3 text-xs">
                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 space-y-2">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Staging ID:</span>
                    <span className="font-mono text-white">{selectedItem.id}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Workspace ID:</span>
                    <span className="font-mono text-white">{selectedItem.workspace_id}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Ingested At:</span>
                    <span className="text-white">{new Date(selectedItem.created_at).toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Last Modified:</span>
                    <span className="text-white">{new Date(selectedItem.updated_at).toLocaleString()}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </DetailDrawer>

      {/* Global Capture Modal */}
      <CaptureModal
        isOpen={isCaptureModalOpen}
        onClose={() => setIsCaptureModalOpen(false)}
        onSuccess={() => {
          setIsCaptureModalOpen(false);
          loadStagingItems();
        }}
      />
    </div>
  );
};
