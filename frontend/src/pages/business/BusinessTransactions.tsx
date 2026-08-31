import React, { useState, useEffect, useCallback } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import {
  Plus,
  RefreshCw,
  Search,
  ArrowDownRight,
  ArrowUpRight,
  RotateCcw,
  Receipt,
  Scale,
} from 'lucide-react';
import { api } from '../../api';
import { useBusinessAuth } from '../../context/BusinessAuthContext';
import { BusinessPageHeader } from '../../components/Business/BusinessPageHeader';
import { BusinessDataTable } from '../../components/Business/BusinessDataTable';
import type { ColumnDef } from '../../components/Business/BusinessDataTable';
import { StatusBadge } from '../../components/Business/StatusBadge';
import type { BusinessStatusType } from '../../components/Business/StatusBadge';
import { FinancialNumber } from '../../components/Business/FinancialNumber';
import { DetailDrawer } from '../../components/Business/DetailDrawer';
import { BusinessErrorState } from '../../components/Business/BusinessErrorState';

export interface TransactionRecord {
  id: string;
  transaction_type: 'INCOME' | 'EXPENSE' | 'ADJUSTMENT';
  amount: string;
  currency: string;
  transaction_date: string;
  reference_number?: string;
  description?: string;
  category?: string;
  status: BusinessStatusType;
  partner_id?: string;
  partner_name?: string;
  allocated_amount?: string;
  unallocated_amount?: string;
  allocations?: Array<{
    id: string;
    invoice_id: string;
    invoice_number?: string;
    allocated_amount: string;
    notes?: string;
  }>;
}

export const BusinessTransactions: React.FC = () => {
  const shouldReduceMotion = useReducedMotion();
  const { activeWorkspace, role } = useBusinessAuth();

  const isAccountantOrAdmin = role === 'OWNER' || role === 'ADMIN' || role === 'ACCOUNTANT';

  // Data state
  const [transactions, setTransactions] = useState<TransactionRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters & Search
  const [typeFilter, setTypeFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // Detail Drawer
  const [selectedTx, setSelectedTx] = useState<TransactionRecord | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionFeedback, setActionFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Record Transaction Drawer
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [partners, setPartners] = useState<Array<{ id: string; name: string }>>([]);
  const [createType, setCreateType] = useState<'INCOME' | 'EXPENSE' | 'ADJUSTMENT'>('INCOME');
  const [createAmount, setCreateAmount] = useState('');
  const [createCurrency, setCreateCurrency] = useState('INR');
  const [createDate, setCreateDate] = useState(new Date().toISOString().split('T')[0]);
  const [createRef, setCreateRef] = useState('');
  const [createPartnerId, setCreatePartnerId] = useState('');
  const [createDescription, setCreateDescription] = useState('');
  const [createCategory, setCreateCategory] = useState('OPERATING');
  const [createSubmitting, setCreateSubmitting] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  // Allocation Modal State
  const [isAllocateOpen, setIsAllocateOpen] = useState(false);
  const [openInvoices, setOpenInvoices] = useState<Array<{ id: string; invoice_number: string; balance_due: string; partner_name?: string }>>([]);
  const [selectedInvoiceId, setSelectedInvoiceId] = useState('');
  const [allocateAmount, setAllocateAmount] = useState('');
  const [allocateNotes, setAllocateNotes] = useState('');
  const [allocateLoading, setAllocateLoading] = useState(false);
  const [allocateError, setAllocateError] = useState<string | null>(null);

  // Fetch Transactions
  const fetchTransactions = useCallback(async (isManualRefresh = false) => {
    if (!activeWorkspace?.id) return;

    if (isManualRefresh) setRefreshing(true);
    else setLoading(true);
    setError(null);

    try {
      const params: any = { limit: 100 };
      if (typeFilter !== 'ALL') params.transaction_type = typeFilter;
      if (statusFilter !== 'ALL') params.status = statusFilter;

      const res = await api.listTransactions(params);
      if (res?.status === 'success') {
        setTransactions(res.data?.transactions || []);
      }
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || err?.message || 'Failed to load transactions');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [activeWorkspace?.id, typeFilter, statusFilter]);

  // Fetch Partners and Open Invoices for Allocations
  useEffect(() => {
    if (activeWorkspace?.id) {
      api.listCommercialPartners({ limit: 100 })
        .then(res => {
          if (res?.status === 'success') setPartners(res.data?.partners || []);
        })
        .catch(() => {});

      api.listInvoices({ status: 'ISSUED', limit: 100 })
        .then(res => {
          if (res?.status === 'success') setOpenInvoices(res.data?.invoices || []);
        })
        .catch(() => {});
    }
  }, [activeWorkspace?.id]);

  useEffect(() => {
    fetchTransactions(false);

    const handleWorkspaceChange = () => fetchTransactions(false);
    window.addEventListener('deadline_workspace_changed', handleWorkspaceChange);
    return () => {
      window.removeEventListener('deadline_workspace_changed', handleWorkspaceChange);
    };
  }, [fetchTransactions]);

  // Filtered dataset
  const filteredTransactions = transactions.filter(tx => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      (tx.reference_number && tx.reference_number.toLowerCase().includes(q)) ||
      (tx.partner_name && tx.partner_name.toLowerCase().includes(q)) ||
      (tx.description && tx.description.toLowerCase().includes(q)) ||
      (tx.category && tx.category.toLowerCase().includes(q))
    );
  });

  // KPI Calculations
  const totalIncome = transactions
    .filter(t => t.transaction_type === 'INCOME' && t.status !== 'REVERSED')
    .reduce((acc, curr) => acc + (parseFloat(curr.amount) || 0), 0);

  const totalExpense = transactions
    .filter(t => t.transaction_type === 'EXPENSE' && t.status !== 'REVERSED')
    .reduce((acc, curr) => acc + (parseFloat(curr.amount) || 0), 0);

  const netSettled = totalIncome - totalExpense;

  // Handle Reversal
  const handleReverseTransaction = async (txId: string) => {
    const reason = window.prompt(
      'Transactions are immutable facts. A counter-adjustment will be created in the ledger.\n\nEnter reversal reason:'
    );
    if (!reason) return;

    setActionLoading(true);
    setActionFeedback(null);
    try {
      const res = await api.reverseTransaction(txId, reason);
      if (res?.status === 'success') {
        setActionFeedback({
          type: 'success',
          message: 'Transaction reversed and append-only adjustment posted.',
        });
        setSelectedTx(null);
        fetchTransactions(true);
      }
    } catch (err: any) {
      setActionFeedback({
        type: 'error',
        message: err?.response?.data?.error?.message || err?.message || 'Failed to reverse transaction.',
      });
    } finally {
      setActionLoading(false);
    }
  };

  // Handle Create Transaction Submit
  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateError(null);
    setCreateSubmitting(true);

    try {
      const payload = {
        transaction_type: createType,
        amount: createAmount,
        currency: createCurrency,
        transaction_date: createDate,
        reference_number: createRef || undefined,
        partner_id: createPartnerId || undefined,
        description: createDescription || undefined,
        category: createCategory,
      };

      const res = await api.recordTransaction(payload);
      if (res?.status === 'success') {
        setIsCreateOpen(false);
        fetchTransactions(true);
        setCreateAmount('');
        setCreateRef('');
        setCreateDescription('');
      }
    } catch (err: any) {
      setCreateError(err?.response?.data?.error?.message || err?.message || 'Failed to record transaction');
    } finally {
      setCreateSubmitting(false);
    }
  };

  // Handle Payment Allocation Submit
  const handleAllocateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTx || !selectedInvoiceId || !allocateAmount) return;

    setAllocateLoading(true);
    setAllocateError(null);
    try {
      const payload = {
        transaction_id: selectedTx.id,
        allocations: [
          {
            invoice_id: selectedInvoiceId,
            allocated_amount: allocateAmount,
            notes: allocateNotes || undefined,
          },
        ],
      };

      const res = await api.allocatePayment(payload);
      if (res?.status === 'success') {
        setIsAllocateOpen(false);
        setSelectedInvoiceId('');
        setAllocateAmount('');
        setAllocateNotes('');
        setSelectedTx(null);
        fetchTransactions(true);
      }
    } catch (err: any) {
      setAllocateError(err?.response?.data?.error?.message || err?.message || 'Failed to allocate payment');
    } finally {
      setAllocateLoading(false);
    }
  };

  const columns: ColumnDef<TransactionRecord>[] = [
    {
      key: 'transaction_date',
      header: 'Date',
      sortable: true,
      render: row => (
        <span className="font-mono text-slate-300 text-xs">
          {new Date(row.transaction_date).toLocaleDateString()}
        </span>
      ),
    },
    {
      key: 'reference_number',
      header: 'Reference #',
      sortable: true,
      render: row => (
        <span className="font-mono font-semibold text-slate-200 text-xs">
          {row.reference_number || '—'}
        </span>
      ),
    },
    {
      key: 'partner_name',
      header: 'Counterparty / Partner',
      sortable: true,
      render: row => <span className="text-slate-200 font-medium">{row.partner_name || '—'}</span>,
    },
    {
      key: 'transaction_type',
      header: 'Type',
      sortable: true,
      render: row => (
        <span
          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
            row.transaction_type === 'INCOME'
              ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'
              : row.transaction_type === 'EXPENSE'
              ? 'bg-rose-500/10 text-rose-300 border border-rose-500/20'
              : 'bg-amber-500/10 text-amber-300 border border-amber-500/20'
          }`}
        >
          {row.transaction_type === 'INCOME' ? (
            <ArrowDownRight className="w-3 h-3" />
          ) : row.transaction_type === 'EXPENSE' ? (
            <ArrowUpRight className="w-3 h-3" />
          ) : (
            <RotateCcw className="w-3 h-3" />
          )}
          {row.transaction_type}
        </span>
      ),
    },
    {
      key: 'amount',
      header: 'Amount',
      align: 'right',
      sortable: true,
      render: row => (
        <FinancialNumber
          value={row.amount}
          currency={row.currency}
          variant={row.transaction_type === 'INCOME' ? 'positive' : row.transaction_type === 'EXPENSE' ? 'negative' : 'default'}
          className="font-bold"
        />
      ),
    },
    {
      key: 'status',
      header: 'Status',
      align: 'center',
      sortable: true,
      render: row => <StatusBadge status={row.status} size="sm" />,
    },
  ];

  return (
    <motion.div
      initial={shouldReduceMotion ? false : { opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: 'easeOut' }}
      className="space-y-6"
    >
      {/* 1. Header */}
      <BusinessPageHeader
        breadcrumbs={[
          { label: 'Business OS', href: '/business/dashboard' },
          { label: 'Financials', href: '/business/transactions' },
          { label: 'Transactions & Ledger' },
        ]}
        title="Commercial Money Movement & Ledger"
        description="Immutable settlement record, bank deposits, expenses, payment allocations, and append-only adjustments."
        status="ACTIVE"
        primaryAction={
          isAccountantOrAdmin
            ? {
                label: 'Record Transaction',
                icon: Plus,
                onClick: () => setIsCreateOpen(true),
              }
            : undefined
        }
        secondaryActions={[
          {
            label: refreshing ? 'Syncing...' : 'Refresh',
            icon: RefreshCw,
            onClick: () => fetchTransactions(true),
          },
        ]}
      />

      {/* 2. KPI Summary Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-4 rounded-2xl bg-[#0B0F19]/90 border border-slate-800/80 shadow-lg flex items-center justify-between">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-wider text-emerald-400">Total Inflows (Settled)</div>
            <div className="text-lg font-bold text-emerald-300 mt-1 font-mono">
              ₹{totalIncome.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </div>
          </div>
          <div className="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            <ArrowDownRight className="w-5 h-5" />
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-[#0B0F19]/90 border border-slate-800/80 shadow-lg flex items-center justify-between">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-wider text-rose-400">Total Outflows (Expenses)</div>
            <div className="text-lg font-bold text-rose-300 mt-1 font-mono">
              ₹{totalExpense.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </div>
          </div>
          <div className="w-9 h-9 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400">
            <ArrowUpRight className="w-5 h-5" />
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-[#0B0F19]/90 border border-slate-800/80 shadow-lg flex items-center justify-between">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Net Settled Cash</div>
            <div className={`text-lg font-bold mt-1 font-mono ${netSettled >= 0 ? 'text-emerald-300' : 'text-rose-300'}`}>
              ₹{netSettled.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </div>
          </div>
          <div className="w-9 h-9 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300">
            <Scale className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* 3. Filter & Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 p-2 rounded-2xl bg-slate-900/60 border border-slate-800/80">
        <div className="flex items-center gap-1 overflow-x-auto no-scrollbar py-1">
          {['ALL', 'INCOME', 'EXPENSE', 'ADJUSTMENT'].map(tp => (
            <button
              key={tp}
              onClick={() => setTypeFilter(tp)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-colors ${
                typeFilter === tp
                  ? 'bg-emerald-500/15 border border-emerald-500/30 text-emerald-300'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 border border-transparent'
              }`}
            >
              {tp === 'ALL' ? 'All Types' : tp}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <div className="relative flex-1 sm:w-60">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search reference, partner..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 text-xs rounded-xl bg-slate-950/80 border border-slate-800 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-colors"
            />
          </div>

          <select
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
            className="px-2.5 py-1.5 text-xs rounded-xl bg-slate-950/80 border border-slate-800 text-slate-300 focus:outline-none focus:border-emerald-500"
          >
            <option value="ALL">All Status</option>
            <option value="CONFIRMED">Confirmed</option>
            <option value="REVERSED">Reversed</option>
          </select>
        </div>
      </div>

      {/* 4. Transactions Data Table */}
      {error && !loading && (
        <BusinessErrorState
          title="Failed to Load Transactions"
          message={error}
          onRetry={() => fetchTransactions(true)}
        />
      )}

      <BusinessDataTable
        columns={columns}
        data={filteredTransactions}
        keyExtractor={item => item.id}
        loading={loading}
        emptyTitle="No Transactions Found"
        emptyDescription="There are no money movement records matching the current filter criteria."
        emptyActionLabel={isAccountantOrAdmin ? 'Record First Transaction' : undefined}
        onEmptyAction={() => setIsCreateOpen(true)}
        onRowClick={row => {
          setSelectedTx(row);
          setActionFeedback(null);
        }}
      />

      {/* 5. Transaction Detail Drawer */}
      <DetailDrawer
        isOpen={Boolean(selectedTx)}
        onClose={() => setSelectedTx(null)}
        title={selectedTx?.reference_number ? `Ref: ${selectedTx.reference_number}` : 'Transaction Record'}
        subtitle={selectedTx?.partner_name ? `Counterparty: ${selectedTx.partner_name}` : 'Ledger Entry'}
        status={selectedTx?.status}
        width="md"
        footer={
          selectedTx && (
            <div className="flex items-center justify-between w-full">
              <div className="flex items-center gap-2">
                {selectedTx.status === 'CONFIRMED' && isAccountantOrAdmin && (
                  <button
                    onClick={() => {
                      setIsAllocateOpen(true);
                    }}
                    className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 text-emerald-300 transition-colors"
                  >
                    <Receipt className="w-3.5 h-3.5" />
                    <span>Allocate to Invoice</span>
                  </button>
                )}

                {selectedTx.status === 'CONFIRMED' && isAccountantOrAdmin && (
                  <button
                    onClick={() => handleReverseTransaction(selectedTx.id)}
                    disabled={actionLoading}
                    className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 text-rose-300 transition-colors disabled:opacity-50"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    <span>Reverse</span>
                  </button>
                )}
              </div>

              <button
                onClick={() => setSelectedTx(null)}
                className="px-4 py-2 text-xs text-slate-400 hover:text-white rounded-xl bg-slate-800"
              >
                Close
              </button>
            </div>
          )
        }
      >
        {selectedTx && (
          <div className="space-y-6">
            {actionFeedback && (
              <div
                className={`p-3 rounded-xl text-xs border ${
                  actionFeedback.type === 'success'
                    ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                    : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
                }`}
              >
                {actionFeedback.message}
              </div>
            )}

            {/* Overview Box */}
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-[11px] text-slate-500 uppercase font-semibold">Amount</span>
                <FinancialNumber
                  value={selectedTx.amount}
                  currency={selectedTx.currency}
                  variant={selectedTx.transaction_type === 'INCOME' ? 'positive' : selectedTx.transaction_type === 'EXPENSE' ? 'negative' : 'default'}
                  className="text-base font-bold"
                />
              </div>
              <div className="flex justify-between text-xs text-slate-400">
                <span>Transaction Type</span>
                <span className="font-semibold text-slate-200 uppercase">{selectedTx.transaction_type}</span>
              </div>
              <div className="flex justify-between text-xs text-slate-400">
                <span>Settlement Date</span>
                <span className="font-mono text-slate-200">
                  {new Date(selectedTx.transaction_date).toLocaleDateString()}
                </span>
              </div>
              <div className="flex justify-between text-xs text-slate-400">
                <span>Category</span>
                <span className="text-slate-200">{selectedTx.category || 'OPERATING'}</span>
              </div>
            </div>

            {/* Description */}
            {selectedTx.description && (
              <div>
                <h4 className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Description</h4>
                <p className="text-xs text-slate-300 p-3 rounded-xl bg-slate-900/40 border border-slate-800/60 leading-relaxed">
                  {selectedTx.description}
                </p>
              </div>
            )}

            {/* Allocations History */}
            <div>
              <h4 className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Payment Allocations
              </h4>
              {selectedTx.allocations && selectedTx.allocations.length > 0 ? (
                <div className="space-y-2">
                  {selectedTx.allocations.map(al => (
                    <div
                      key={al.id}
                      className="p-3 rounded-xl bg-slate-900/40 border border-slate-800 flex justify-between items-center text-xs"
                    >
                      <div>
                        <div className="font-mono font-bold text-slate-200">
                          {al.invoice_number || `Invoice #${al.invoice_id.slice(0, 8)}`}
                        </div>
                        {al.notes && <div className="text-[10px] text-slate-500 mt-0.5">{al.notes}</div>}
                      </div>
                      <div className="font-mono text-emerald-400 font-bold">
                        ₹{parseFloat(al.allocated_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-500 p-3 rounded-xl bg-slate-900/20 border border-slate-800/40 text-center">
                  Unallocated in full.
                </p>
              )}
            </div>
          </div>
        )}
      </DetailDrawer>

      {/* 6. Record Transaction Drawer */}
      <DetailDrawer
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Record Commercial Transaction"
        subtitle="Appends an immutable money movement record to the general ledger."
        width="md"
      >
        <form onSubmit={handleCreateSubmit} className="space-y-4 text-xs">
          {createError && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300">
              {createError}
            </div>
          )}

          <div>
            <label className="block text-[11px] font-semibold text-slate-300 mb-1">Transaction Type</label>
            <select
              value={createType}
              onChange={e => setCreateType(e.target.value as any)}
              className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500"
            >
              <option value="INCOME">Income / Revenue (Customer Payment)</option>
              <option value="EXPENSE">Expense (Vendor / Operating Outflow)</option>
              <option value="ADJUSTMENT">Adjustment (Manual Journal Adjustment)</option>
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-semibold text-slate-300 mb-1">Amount</label>
              <input
                type="text"
                placeholder="50000.00"
                value={createAmount}
                onChange={e => setCreateAmount(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500 font-mono"
                required
              />
            </div>
            <div>
              <label className="block text-[11px] font-semibold text-slate-300 mb-1">Currency</label>
              <input
                type="text"
                value={createCurrency}
                onChange={e => setCreateCurrency(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-semibold text-slate-300 mb-1">Transaction Date</label>
              <input
                type="date"
                value={createDate}
                onChange={e => setCreateDate(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500"
                required
              />
            </div>
            <div>
              <label className="block text-[11px] font-semibold text-slate-300 mb-1">Reference #</label>
              <input
                type="text"
                placeholder="TXN-2026-001 or UTR"
                value={createRef}
                onChange={e => setCreateRef(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500 font-mono"
              />
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-300 mb-1">Counterparty Partner</label>
            <select
              value={createPartnerId}
              onChange={e => setCreatePartnerId(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500"
            >
              <option value="">Select Partner (Optional)...</option>
              {partners.map(p => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-300 mb-1">Category</label>
            <input
              type="text"
              value={createCategory}
              onChange={e => setCreateCategory(e.target.value)}
              placeholder="OPERATING, PAYROLL, INFRASTRUCTURE..."
              className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-300 mb-1">Description / Memo</label>
            <textarea
              rows={2}
              value={createDescription}
              onChange={e => setCreateDescription(e.target.value)}
              placeholder="Description of bank transaction..."
              className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div className="pt-3 border-t border-slate-800 flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setIsCreateOpen(false)}
              className="px-4 py-2 rounded-xl bg-slate-800 text-slate-400 hover:text-white"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createSubmitting}
              className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold disabled:opacity-50 shadow-md shadow-emerald-500/20"
            >
              {createSubmitting ? 'Recording...' : 'Record Transaction'}
            </button>
          </div>
        </form>
      </DetailDrawer>

      {/* 7. Payment Allocation Modal */}
      <DetailDrawer
        isOpen={isAllocateOpen}
        onClose={() => setIsAllocateOpen(false)}
        title="Allocate Payment to Invoice"
        subtitle={selectedTx ? `Allocating from Ref: ${selectedTx.reference_number || selectedTx.id.slice(0, 8)}` : ''}
        width="md"
      >
        <form onSubmit={handleAllocateSubmit} className="space-y-4 text-xs">
          {allocateError && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300">
              {allocateError}
            </div>
          )}

          <div>
            <label className="block text-[11px] font-semibold text-slate-300 mb-1">Select Open Invoice</label>
            <select
              value={selectedInvoiceId}
              onChange={e => {
                setSelectedInvoiceId(e.target.value);
                const inv = openInvoices.find(i => i.id === e.target.value);
                if (inv) {
                  setAllocateAmount(inv.balance_due);
                }
              }}
              className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500"
              required
            >
              <option value="">Select Invoice to settle...</option>
              {openInvoices.map(inv => (
                <option key={inv.id} value={inv.id}>
                  {inv.invoice_number} — Balance Due: ₹{parseFloat(inv.balance_due).toLocaleString('en-IN')}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-300 mb-1">Allocated Amount</label>
            <input
              type="text"
              placeholder="Amount to settle..."
              value={allocateAmount}
              onChange={e => setAllocateAmount(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500 font-mono"
              required
            />
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-300 mb-1">Notes / Allocation Memo</label>
            <input
              type="text"
              placeholder="e.g. Full settlement against milestone 1"
              value={allocateNotes}
              onChange={e => setAllocateNotes(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div className="pt-3 border-t border-slate-800 flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setIsAllocateOpen(false)}
              className="px-4 py-2 rounded-xl bg-slate-800 text-slate-400 hover:text-white"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={allocateLoading}
              className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold disabled:opacity-50 shadow-md shadow-emerald-500/20"
            >
              {allocateLoading ? 'Allocating...' : 'Confirm Allocation'}
            </button>
          </div>
        </form>
      </DetailDrawer>
    </motion.div>
  );
};
export default BusinessTransactions;
