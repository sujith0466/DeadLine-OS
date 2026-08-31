import React, { useState, useEffect, useCallback } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import {
  Plus,
  RefreshCw,
  Search,
  FileText,
  Send,
  Ban,
  ArrowDownRight,
  ArrowUpRight,
  AlertCircle,
  Trash2,
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

export interface InvoiceItem {
  description: string;
  quantity: number;
  unit_price: string;
  tax_rate: string;
  discount_amount?: string;
}

export interface InvoiceRecord {
  id: string;
  invoice_number: string;
  invoice_type: 'RECEIVABLE' | 'PAYABLE';
  status: BusinessStatusType;
  issue_date: string;
  due_date: string;
  currency: string;
  subtotal: string;
  tax_amount: string;
  discount_amount?: string;
  total_amount: string;
  paid_amount: string;
  balance_due: string;
  partner_id?: string;
  partner_name?: string;
  notes?: string;
  line_items?: Array<{
    id: string;
    description: string;
    quantity: number;
    unit_price: string;
    tax_rate: string;
    line_total: string;
  }>;
  allocations?: Array<{
    id: string;
    transaction_id: string;
    allocated_amount: string;
    created_at: string;
  }>;
}

export const BusinessInvoices: React.FC = () => {
  const shouldReduceMotion = useReducedMotion();
  const { activeWorkspace, role } = useBusinessAuth();

  const isAccountantOrAdmin = role === 'OWNER' || role === 'ADMIN' || role === 'ACCOUNTANT';

  // Invoices list state
  const [invoices, setInvoices] = useState<InvoiceRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filter & Search state
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [typeFilter, setTypeFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // Selected Invoice Detail Drawer
  const [selectedInvoice, setSelectedInvoice] = useState<InvoiceRecord | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionFeedback, setActionFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Create Invoice Drawer State
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [partners, setPartners] = useState<Array<{ id: string; name: string }>>([]);
  const [createPartnerId, setCreatePartnerId] = useState('');
  const [createType, setCreateType] = useState<'RECEIVABLE' | 'PAYABLE'>('RECEIVABLE');
  const [createIssueDate, setCreateIssueDate] = useState(new Date().toISOString().split('T')[0]);
  const [createDueDate, setCreateDueDate] = useState(
    new Date(Date.now() + 14 * 86400000).toISOString().split('T')[0]
  );
  const [createCurrency, setCreateCurrency] = useState('INR');
  const [createNotes, setCreateNotes] = useState('');
  const [createItems, setCreateItems] = useState<InvoiceItem[]>([
    { description: 'Professional Services', quantity: 1, unit_price: '50000.00', tax_rate: '18.00' },
  ]);
  const [createError, setCreateError] = useState<string | null>(null);
  const [createSubmitting, setCreateSubmitting] = useState(false);

  // Fetch Invoices
  const fetchInvoices = useCallback(async (isManualRefresh = false) => {
    if (!activeWorkspace?.id) return;

    if (isManualRefresh) setRefreshing(true);
    else setLoading(true);
    setError(null);

    try {
      const params: any = { limit: 100 };
      if (statusFilter !== 'ALL') params.status = statusFilter;
      if (typeFilter !== 'ALL') params.invoice_type = typeFilter;

      const res = await api.listInvoices(params);
      if (res?.status === 'success') {
        setInvoices(res.data?.invoices || []);
      }
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || err?.message || 'Failed to load invoices');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [activeWorkspace?.id, statusFilter, typeFilter]);

  // Fetch Partners for Create Selector
  useEffect(() => {
    if (activeWorkspace?.id) {
      api.listCommercialPartners({ limit: 100 })
        .then(res => {
          if (res?.status === 'success') {
            setPartners(res.data?.partners || []);
          }
        })
        .catch(() => {});
    }
  }, [activeWorkspace?.id]);

  useEffect(() => {
    fetchInvoices(false);

    const handleWorkspaceChange = () => fetchInvoices(false);
    window.addEventListener('deadline_workspace_changed', handleWorkspaceChange);
    return () => {
      window.removeEventListener('deadline_workspace_changed', handleWorkspaceChange);
    };
  }, [fetchInvoices]);

  // Filtered dataset for search
  const filteredInvoices = invoices.filter(inv => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      inv.invoice_number.toLowerCase().includes(q) ||
      (inv.partner_name && inv.partner_name.toLowerCase().includes(q)) ||
      (inv.notes && inv.notes.toLowerCase().includes(q))
    );
  });

  // KPI calculations from fetched invoices
  const totalReceivables = invoices
    .filter(i => i.invoice_type === 'RECEIVABLE' && i.status !== 'VOID')
    .reduce((acc, curr) => acc + (parseFloat(curr.total_amount) || 0), 0);

  const totalOverdue = invoices
    .filter(i => i.invoice_type === 'RECEIVABLE' && i.status === 'OVERDUE')
    .reduce((acc, curr) => acc + (parseFloat(curr.balance_due) || 0), 0);

  const totalPayables = invoices
    .filter(i => i.invoice_type === 'PAYABLE' && i.status !== 'VOID')
    .reduce((acc, curr) => acc + (parseFloat(curr.total_amount) || 0), 0);

  // Handle Issue Invoice
  const handleIssueInvoice = async (invoiceId: string) => {
    setActionLoading(true);
    setActionFeedback(null);
    try {
      const res = await api.issueInvoice(invoiceId);
      if (res?.status === 'success') {
        setActionFeedback({ type: 'success', message: 'Invoice issued and financial arithmetic frozen.' });
        setSelectedInvoice(res.data?.invoice || null);
        fetchInvoices(true);
      }
    } catch (err: any) {
      setActionFeedback({
        type: 'error',
        message: err?.response?.data?.error?.message || err?.message || 'Failed to issue invoice.',
      });
    } finally {
      setActionLoading(false);
    }
  };

  // Handle Void Invoice
  const handleVoidInvoice = async (invoiceId: string) => {
    const reason = window.prompt('Please enter reason for voiding this invoice:');
    if (!reason) return;

    setActionLoading(true);
    setActionFeedback(null);
    try {
      const res = await api.voidInvoice(invoiceId, reason);
      if (res?.status === 'success') {
        setActionFeedback({ type: 'success', message: 'Invoice voided successfully.' });
        setSelectedInvoice(null);
        fetchInvoices(true);
      }
    } catch (err: any) {
      setActionFeedback({
        type: 'error',
        message: err?.response?.data?.error?.message || err?.message || 'Failed to void invoice.',
      });
    } finally {
      setActionLoading(false);
    }
  };

  // Handle Create Invoice Submit
  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateError(null);
    setCreateSubmitting(true);

    try {
      const payload = {
        partner_id: createPartnerId || undefined,
        invoice_type: createType,
        issue_date: createIssueDate,
        due_date: createDueDate,
        currency: createCurrency,
        notes: createNotes || undefined,
        items: createItems.map(it => ({
          description: it.description,
          quantity: Number(it.quantity),
          unit_price: it.unit_price,
          tax_rate: it.tax_rate,
        })),
      };

      const res = await api.createInvoice(payload);
      if (res?.status === 'success') {
        setIsCreateOpen(false);
        fetchInvoices(true);
        // Reset form
        setCreateNotes('');
        setCreateItems([{ description: 'Service / Item', quantity: 1, unit_price: '10000.00', tax_rate: '18.00' }]);
      }
    } catch (err: any) {
      setCreateError(err?.response?.data?.error?.message || err?.message || 'Failed to create invoice');
    } finally {
      setCreateSubmitting(false);
    }
  };

  const columns: ColumnDef<InvoiceRecord>[] = [
    {
      key: 'invoice_number',
      header: 'Invoice #',
      sortable: true,
      render: row => (
        <div className="flex items-center gap-2">
          <FileText className="w-3.5 h-3.5 text-emerald-400" />
          <span className="font-mono font-bold text-slate-100">{row.invoice_number}</span>
        </div>
      ),
    },
    {
      key: 'partner_name',
      header: 'Partner',
      sortable: true,
      render: row => (
        <div className="truncate max-w-[150px]">
          <span className="text-slate-200 font-medium">{row.partner_name || '—'}</span>
        </div>
      ),
    },
    {
      key: 'invoice_type',
      header: 'Type',
      sortable: true,
      render: row => (
        <span
          className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold uppercase ${
            row.invoice_type === 'RECEIVABLE'
              ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'
              : 'bg-indigo-500/10 text-indigo-300 border border-indigo-500/20'
          }`}
        >
          {row.invoice_type === 'RECEIVABLE' ? (
            <ArrowDownRight className="w-2.5 h-2.5" />
          ) : (
            <ArrowUpRight className="w-2.5 h-2.5" />
          )}
          {row.invoice_type}
        </span>
      ),
    },
    {
      key: 'issue_date',
      header: 'Issue / Due',
      render: row => (
        <div className="text-[11px] text-slate-400">
          <div>{new Date(row.issue_date).toLocaleDateString()}</div>
          <div className="text-[10px] text-slate-500">Due {new Date(row.due_date).toLocaleDateString()}</div>
        </div>
      ),
    },
    {
      key: 'total_amount',
      header: 'Total Amount',
      align: 'right',
      sortable: true,
      render: row => (
        <FinancialNumber
          value={row.total_amount}
          currency={row.currency}
          className="font-bold text-slate-100"
        />
      ),
    },
    {
      key: 'balance_due',
      header: 'Balance Due',
      align: 'right',
      sortable: true,
      render: row => (
        <FinancialNumber
          value={row.balance_due}
          currency={row.currency}
          variant={parseFloat(row.balance_due) > 0 && row.status === 'OVERDUE' ? 'negative' : 'default'}
          className="font-semibold"
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
          { label: 'Financials', href: '/business/invoices' },
          { label: 'Invoices & Receivables' },
        ]}
        title="Invoices & Billing Ledger"
        description="Authoritative commercial invoicing, client receivables, vendor payables, and settlement tracking."
        status="ACTIVE"
        primaryAction={
          isAccountantOrAdmin
            ? {
                label: 'Create Invoice',
                icon: Plus,
                onClick: () => setIsCreateOpen(true),
              }
            : undefined
        }
        secondaryActions={[
          {
            label: refreshing ? 'Syncing...' : 'Refresh',
            icon: RefreshCw,
            onClick: () => fetchInvoices(true),
          },
        ]}
      />

      {/* 2. KPI Summary Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-4 rounded-2xl bg-[#0B0F19]/90 border border-slate-800/80 shadow-lg flex items-center justify-between">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Total Receivables</div>
            <div className="text-lg font-bold text-slate-100 mt-1 font-mono">
              ₹{totalReceivables.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </div>
          </div>
          <div className="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            <ArrowDownRight className="w-5 h-5" />
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-[#0B0F19]/90 border border-slate-800/80 shadow-lg flex items-center justify-between">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-wider text-rose-400">Overdue Receivables</div>
            <div className="text-lg font-bold text-rose-300 mt-1 font-mono">
              ₹{totalOverdue.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </div>
          </div>
          <div className="w-9 h-9 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400">
            <AlertCircle className="w-5 h-5" />
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-[#0B0F19]/90 border border-slate-800/80 shadow-lg flex items-center justify-between">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-wider text-indigo-400">Total Payables</div>
            <div className="text-lg font-bold text-indigo-300 mt-1 font-mono">
              ₹{totalPayables.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </div>
          </div>
          <div className="w-9 h-9 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
            <ArrowUpRight className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* 3. Filter & Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 p-2 rounded-2xl bg-slate-900/60 border border-slate-800/80">
        <div className="flex items-center gap-1 overflow-x-auto no-scrollbar py-1">
          {['ALL', 'DRAFT', 'ISSUED', 'PARTIALLY_PAID', 'PAID', 'OVERDUE', 'VOID'].map(st => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-colors ${
                statusFilter === st
                  ? 'bg-emerald-500/15 border border-emerald-500/30 text-emerald-300'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 border border-transparent'
              }`}
            >
              {st === 'ALL' ? 'All Status' : st.replace('_', ' ')}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <div className="relative flex-1 sm:w-60">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search invoices..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 text-xs rounded-xl bg-slate-950/80 border border-slate-800 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-colors"
            />
          </div>

          <select
            value={typeFilter}
            onChange={e => setTypeFilter(e.target.value)}
            className="px-2.5 py-1.5 text-xs rounded-xl bg-slate-950/80 border border-slate-800 text-slate-300 focus:outline-none focus:border-emerald-500"
          >
            <option value="ALL">All Types</option>
            <option value="RECEIVABLE">Receivable</option>
            <option value="PAYABLE">Payable</option>
          </select>
        </div>
      </div>

      {/* 4. Invoices Data Table */}
      {error && !loading && (
        <BusinessErrorState
          title="Failed to Load Invoices"
          message={error}
          onRetry={() => fetchInvoices(true)}
        />
      )}

      <BusinessDataTable
        columns={columns}
        data={filteredInvoices}
        keyExtractor={item => item.id}
        loading={loading}
        emptyTitle="No Invoices Found"
        emptyDescription="There are no commercial invoices matching the current filter criteria."
        emptyActionLabel={isAccountantOrAdmin ? 'Create First Invoice' : undefined}
        onEmptyAction={() => setIsCreateOpen(true)}
        onRowClick={row => {
          setSelectedInvoice(row);
          setActionFeedback(null);
        }}
      />

      {/* 5. Detail Drawer */}
      <DetailDrawer
        isOpen={Boolean(selectedInvoice)}
        onClose={() => setSelectedInvoice(null)}
        title={selectedInvoice ? selectedInvoice.invoice_number : 'Invoice Detail'}
        subtitle={selectedInvoice?.partner_name ? `Partner: ${selectedInvoice.partner_name}` : 'Commercial Invoice'}
        status={selectedInvoice?.status}
        width="lg"
        footer={
          selectedInvoice && (
            <div className="flex items-center justify-between w-full">
              <div>
                {selectedInvoice.status === 'DRAFT' && isAccountantOrAdmin && (
                  <button
                    onClick={() => handleIssueInvoice(selectedInvoice.id)}
                    disabled={actionLoading}
                    className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold bg-emerald-500 hover:bg-emerald-400 text-slate-950 transition-colors disabled:opacity-50"
                  >
                    <Send className="w-3.5 h-3.5" />
                    <span>Issue Invoice</span>
                  </button>
                )}

                {selectedInvoice.status !== 'VOID' && isAccountantOrAdmin && (
                  <button
                    onClick={() => handleVoidInvoice(selectedInvoice.id)}
                    disabled={actionLoading}
                    className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 text-rose-300 transition-colors disabled:opacity-50 ml-2"
                  >
                    <Ban className="w-3.5 h-3.5" />
                    <span>Void Invoice</span>
                  </button>
                )}
              </div>

              <button
                onClick={() => setSelectedInvoice(null)}
                className="px-4 py-2 text-xs text-slate-400 hover:text-white rounded-xl bg-slate-800"
              >
                Close
              </button>
            </div>
          )
        }
      >
        {selectedInvoice && (
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

            {/* Overview Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-4 rounded-xl bg-slate-900/60 border border-slate-800/80">
              <div>
                <div className="text-[10px] text-slate-500 uppercase font-semibold">Invoice Type</div>
                <div className="text-xs font-bold text-slate-200 mt-0.5">{selectedInvoice.invoice_type}</div>
              </div>
              <div>
                <div className="text-[10px] text-slate-500 uppercase font-semibold">Issue Date</div>
                <div className="text-xs font-bold text-slate-200 mt-0.5">
                  {new Date(selectedInvoice.issue_date).toLocaleDateString()}
                </div>
              </div>
              <div>
                <div className="text-[10px] text-slate-500 uppercase font-semibold">Due Date</div>
                <div className="text-xs font-bold text-slate-200 mt-0.5">
                  {new Date(selectedInvoice.due_date).toLocaleDateString()}
                </div>
              </div>
              <div>
                <div className="text-[10px] text-slate-500 uppercase font-semibold">Currency</div>
                <div className="text-xs font-bold text-slate-200 mt-0.5">{selectedInvoice.currency}</div>
              </div>
            </div>

            {/* Line Items Table */}
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Line Items</h4>
              <div className="rounded-xl border border-slate-800 overflow-hidden">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-900/80 text-[10px] uppercase text-slate-500 border-b border-slate-800">
                    <tr>
                      <th className="px-3 py-2">Description</th>
                      <th className="px-3 py-2 text-center">Qty</th>
                      <th className="px-3 py-2 text-right">Unit Price</th>
                      <th className="px-3 py-2 text-right">Tax Rate</th>
                      <th className="px-3 py-2 text-right">Total</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {selectedInvoice.line_items && selectedInvoice.line_items.length > 0 ? (
                      selectedInvoice.line_items.map((item, idx) => (
                        <tr key={idx}>
                          <td className="px-3 py-2 text-slate-200">{item.description}</td>
                          <td className="px-3 py-2 text-center">{item.quantity}</td>
                          <td className="px-3 py-2 text-right font-mono">
                            ₹{parseFloat(item.unit_price).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                          </td>
                          <td className="px-3 py-2 text-right">{item.tax_rate}%</td>
                          <td className="px-3 py-2 text-right font-mono font-bold text-slate-100">
                            ₹{parseFloat(item.line_total).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={5} className="px-3 py-3 text-center text-slate-500">
                          No line items recorded.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Arithmetic Reconciliation Box */}
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2 text-xs">
              <div className="flex justify-between text-slate-400">
                <span>Subtotal</span>
                <span className="font-mono">
                  ₹{parseFloat(selectedInvoice.subtotal).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Tax Amount</span>
                <span className="font-mono">
                  + ₹{parseFloat(selectedInvoice.tax_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </span>
              </div>
              {selectedInvoice.discount_amount && parseFloat(selectedInvoice.discount_amount) > 0 && (
                <div className="flex justify-between text-emerald-400">
                  <span>Discount</span>
                  <span className="font-mono">
                    - ₹{parseFloat(selectedInvoice.discount_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </span>
                </div>
              )}
              <div className="pt-2 border-t border-slate-800 flex justify-between font-bold text-sm text-slate-100">
                <span>Total Amount</span>
                <span className="font-mono">
                  ₹{parseFloat(selectedInvoice.total_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </span>
              </div>
              <div className="flex justify-between text-slate-400 pt-1">
                <span>Paid to Date</span>
                <span className="font-mono text-emerald-400">
                  ₹{parseFloat(selectedInvoice.paid_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </span>
              </div>
              <div className="flex justify-between font-bold text-slate-200">
                <span>Balance Due</span>
                <span className="font-mono text-rose-300">
                  ₹{parseFloat(selectedInvoice.balance_due).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </span>
              </div>
            </div>

            {/* Notes */}
            {selectedInvoice.notes && (
              <div>
                <h4 className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Notes</h4>
                <p className="text-xs text-slate-300 p-3 rounded-xl bg-slate-900/40 border border-slate-800/60 leading-relaxed">
                  {selectedInvoice.notes}
                </p>
              </div>
            )}
          </div>
        )}
      </DetailDrawer>

      {/* 6. Create Invoice Drawer */}
      <DetailDrawer
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Create Commercial Invoice"
        subtitle="Generates a new invoice draft in the commercial ledger."
        width="lg"
      >
        <form onSubmit={handleCreateSubmit} className="space-y-4 text-xs">
          {createError && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300">
              {createError}
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-semibold text-slate-300 mb-1">Invoice Type</label>
              <select
                value={createType}
                onChange={e => setCreateType(e.target.value as any)}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500"
              >
                <option value="RECEIVABLE">Receivable (Customer Bill)</option>
                <option value="PAYABLE">Payable (Vendor Bill)</option>
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-300 mb-1">Partner</label>
              <select
                value={createPartnerId}
                onChange={e => setCreatePartnerId(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500"
              >
                <option value="">Select Commercial Partner...</option>
                {partners.map(p => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-[11px] font-semibold text-slate-300 mb-1">Issue Date</label>
              <input
                type="date"
                value={createIssueDate}
                onChange={e => setCreateIssueDate(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500"
                required
              />
            </div>
            <div>
              <label className="block text-[11px] font-semibold text-slate-300 mb-1">Due Date</label>
              <input
                type="date"
                value={createDueDate}
                onChange={e => setCreateDueDate(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500"
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

          {/* Line Items Editor */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-[11px] font-semibold text-slate-300 uppercase">Line Items</label>
              <button
                type="button"
                onClick={() =>
                  setCreateItems([
                    ...createItems,
                    { description: '', quantity: 1, unit_price: '0.00', tax_rate: '18.00' },
                  ])
                }
                className="text-xs text-emerald-400 hover:text-emerald-300 font-semibold"
              >
                + Add Item
              </button>
            </div>

            <div className="space-y-2">
              {createItems.map((item, idx) => (
                <div key={idx} className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
                  <div className="flex gap-2">
                    <input
                      type="text"
                      placeholder="Item Description..."
                      value={item.description}
                      onChange={e => {
                        const next = [...createItems];
                        next[idx].description = e.target.value;
                        setCreateItems(next);
                      }}
                      className="flex-1 px-3 py-1.5 text-xs rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500"
                      required
                    />
                    {createItems.length > 1 && (
                      <button
                        type="button"
                        onClick={() => setCreateItems(createItems.filter((_, i) => i !== idx))}
                        className="p-1.5 text-slate-500 hover:text-rose-400"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                  <div className="grid grid-cols-3 gap-2">
                    <div>
                      <span className="text-[10px] text-slate-500">Qty</span>
                      <input
                        type="number"
                        min="1"
                        value={item.quantity}
                        onChange={e => {
                          const next = [...createItems];
                          next[idx].quantity = parseInt(e.target.value) || 1;
                          setCreateItems(next);
                        }}
                        className="w-full px-2.5 py-1 text-xs rounded bg-slate-950 border border-slate-800 text-slate-200"
                      />
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500">Unit Price</span>
                      <input
                        type="text"
                        value={item.unit_price}
                        onChange={e => {
                          const next = [...createItems];
                          next[idx].unit_price = e.target.value;
                          setCreateItems(next);
                        }}
                        className="w-full px-2.5 py-1 text-xs rounded bg-slate-950 border border-slate-800 text-slate-200 font-mono"
                      />
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500">Tax Rate %</span>
                      <input
                        type="text"
                        value={item.tax_rate}
                        onChange={e => {
                          const next = [...createItems];
                          next[idx].tax_rate = e.target.value;
                          setCreateItems(next);
                        }}
                        className="w-full px-2.5 py-1 text-xs rounded bg-slate-950 border border-slate-800 text-slate-200"
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-300 mb-1">Notes / Terms</label>
            <textarea
              rows={2}
              value={createNotes}
              onChange={e => setCreateNotes(e.target.value)}
              placeholder="Payment terms, bank details, or delivery notes..."
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
              {createSubmitting ? 'Creating...' : 'Create Invoice Draft'}
            </button>
          </div>
        </form>
      </DetailDrawer>
    </motion.div>
  );
};
export default BusinessInvoices;
