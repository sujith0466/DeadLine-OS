import React, { useState, useEffect, useCallback } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import {
  Plus,
  RefreshCw,
  Search,
  Users,
  Building,
  Briefcase,
  Archive,
  Mail,
  Phone,
} from 'lucide-react';
import { api } from '../../api';
import { useBusinessAuth } from '../../context/BusinessAuthContext';
import { BusinessPageHeader } from '../../components/Business/BusinessPageHeader';
import { BusinessDataTable } from '../../components/Business/BusinessDataTable';
import type { ColumnDef } from '../../components/Business/BusinessDataTable';
import { StatusBadge } from '../../components/Business/StatusBadge';
import type { BusinessStatusType } from '../../components/Business/StatusBadge';
import { DetailDrawer } from '../../components/Business/DetailDrawer';
import { BusinessErrorState } from '../../components/Business/BusinessErrorState';

export interface CommercialPartnerRecord {
  id: string;
  partner_type: 'CUSTOMER' | 'VENDOR' | 'CONTRACTOR' | 'FINANCIAL_INSTITUTION';
  name: string;
  legal_name?: string;
  phone?: string;
  email?: string;
  tax_identifier?: string;
  credit_period_days?: number;
  status: BusinessStatusType;
  created_at: string;
}

export const BusinessPartners: React.FC = () => {
  const shouldReduceMotion = useReducedMotion();
  const { activeWorkspace, role } = useBusinessAuth();

  const isMemberOrAbove = role !== 'VIEWER';

  // Data state
  const [partners, setPartners] = useState<CommercialPartnerRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters & Search
  const [typeFilter, setTypeFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ACTIVE');
  const [searchQuery, setSearchQuery] = useState('');

  // Selected Detail Drawer
  const [selectedPartner, setSelectedPartner] = useState<CommercialPartnerRecord | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionFeedback, setActionFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Add Partner Drawer State
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [createType, setCreateType] = useState<'CUSTOMER' | 'VENDOR' | 'CONTRACTOR' | 'FINANCIAL_INSTITUTION'>('CUSTOMER');
  const [createName, setCreateName] = useState('');
  const [createLegalName, setCreateLegalName] = useState('');
  const [createPhone, setCreatePhone] = useState('');
  const [createEmail, setCreateEmail] = useState('');
  const [createTaxId, setCreateTaxId] = useState('');
  const [createCreditDays, setCreateCreditDays] = useState(30);
  const [createSubmitting, setCreateSubmitting] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  // Fetch Partners
  const fetchPartners = useCallback(async (isManualRefresh = false) => {
    if (!activeWorkspace?.id) return;

    if (isManualRefresh) setRefreshing(true);
    else setLoading(true);
    setError(null);

    try {
      const params: any = { limit: 100 };
      if (typeFilter !== 'ALL') params.type = typeFilter;
      if (statusFilter !== 'ALL') params.status = statusFilter;

      const res = await api.listCommercialPartners(params);
      if (res?.status === 'success') {
        setPartners(res.data?.partners || []);
      }
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || err?.message || 'Failed to load commercial partners');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [activeWorkspace?.id, typeFilter, statusFilter]);

  useEffect(() => {
    fetchPartners(false);

    const handleWorkspaceChange = () => fetchPartners(false);
    window.addEventListener('deadline_workspace_changed', handleWorkspaceChange);
    return () => {
      window.removeEventListener('deadline_workspace_changed', handleWorkspaceChange);
    };
  }, [fetchPartners]);

  // Filtered dataset
  const filteredPartners = partners.filter(p => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      p.name.toLowerCase().includes(q) ||
      (p.legal_name && p.legal_name.toLowerCase().includes(q)) ||
      (p.email && p.email.toLowerCase().includes(q)) ||
      (p.tax_identifier && p.tax_identifier.toLowerCase().includes(q))
    );
  });

  // KPI Calculations
  const customerCount = partners.filter(p => p.partner_type === 'CUSTOMER' && p.status === 'ACTIVE').length;
  const vendorCount = partners.filter(p => p.partner_type === 'VENDOR' && p.status === 'ACTIVE').length;
  const contractorCount = partners.filter(p => p.partner_type === 'CONTRACTOR' && p.status === 'ACTIVE').length;

  // Handle Archive Partner
  const handleArchivePartner = async (partnerId: string) => {
    const reason = window.prompt('Enter reason for archiving this commercial partner:');
    if (!reason) return;

    setActionLoading(true);
    setActionFeedback(null);
    try {
      const res = await api.archiveCommercialPartner(partnerId, reason);
      if (res?.status === 'success') {
        setActionFeedback({
          type: 'success',
          message: 'Partner archived successfully.',
        });
        setSelectedPartner(null);
        fetchPartners(true);
      }
    } catch (err: any) {
      setActionFeedback({
        type: 'error',
        message: err?.response?.data?.error?.message || err?.message || 'Failed to archive partner.',
      });
    } finally {
      setActionLoading(false);
    }
  };

  // Handle Create Partner Submit
  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateError(null);
    setCreateSubmitting(true);

    try {
      const payload = {
        partner_type: createType,
        name: createName.trim(),
        legal_name: createLegalName.trim() || undefined,
        phone: createPhone.trim() || undefined,
        email: createEmail.trim() || undefined,
        tax_identifier: createTaxId.trim() || undefined,
        credit_period_days: Number(createCreditDays) || 30,
      };

      const res = await api.createCommercialPartner(payload);
      if (res?.status === 'success') {
        setIsCreateOpen(false);
        fetchPartners(true);
        // Reset form
        setCreateName('');
        setCreateLegalName('');
        setCreatePhone('');
        setCreateEmail('');
        setCreateTaxId('');
        setCreateCreditDays(30);
      }
    } catch (err: any) {
      setCreateError(err?.response?.data?.error?.message || err?.message || 'Failed to add partner');
    } finally {
      setCreateSubmitting(false);
    }
  };

  const columns: ColumnDef<CommercialPartnerRecord>[] = [
    {
      key: 'name',
      header: 'Partner Name',
      sortable: true,
      render: row => (
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 font-bold text-xs">
            {row.name.charAt(0).toUpperCase()}
          </div>
          <div>
            <div className="font-semibold text-slate-100 text-xs">{row.name}</div>
            {row.legal_name && <div className="text-[10px] text-slate-500">{row.legal_name}</div>}
          </div>
        </div>
      ),
    },
    {
      key: 'partner_type',
      header: 'Type',
      sortable: true,
      render: row => (
        <span
          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
            row.partner_type === 'CUSTOMER'
              ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'
              : row.partner_type === 'VENDOR'
              ? 'bg-indigo-500/10 text-indigo-300 border border-indigo-500/20'
              : row.partner_type === 'CONTRACTOR'
              ? 'bg-amber-500/10 text-amber-300 border border-amber-500/20'
              : 'bg-cyan-500/10 text-cyan-300 border border-cyan-500/20'
          }`}
        >
          {row.partner_type}
        </span>
      ),
    },
    {
      key: 'contact',
      header: 'Contact Info',
      render: row => (
        <div className="text-[11px] text-slate-400 space-y-0.5">
          {row.email && (
            <div className="flex items-center gap-1.5 text-slate-300">
              <Mail className="w-3 h-3 text-slate-500" />
              <span>{row.email}</span>
            </div>
          )}
          {row.phone && (
            <div className="flex items-center gap-1.5 text-slate-500">
              <Phone className="w-3 h-3" />
              <span>{row.phone}</span>
            </div>
          )}
          {!row.email && !row.phone && <span className="text-slate-600">—</span>}
        </div>
      ),
    },
    {
      key: 'tax_identifier',
      header: 'Tax ID / GSTIN',
      render: row => (
        <span className="font-mono text-xs text-slate-300">
          {row.tax_identifier || '—'}
        </span>
      ),
    },
    {
      key: 'credit_period_days',
      header: 'Credit Terms',
      render: row => (
        <span className="text-xs text-slate-400">
          {row.credit_period_days ? `${row.credit_period_days} Days` : 'Immediate'}
        </span>
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
          { label: 'Financials', href: '/business/partners' },
          { label: 'Partners' },
        ]}
        title="Commercial Partners Registry"
        description="Authoritative master directory of customers, suppliers, contractors, and financial counterparties."
        status="ACTIVE"
        primaryAction={
          isMemberOrAbove
            ? {
                label: 'Add Partner',
                icon: Plus,
                onClick: () => setIsCreateOpen(true),
              }
            : undefined
        }
        secondaryActions={[
          {
            label: refreshing ? 'Syncing...' : 'Refresh',
            icon: RefreshCw,
            onClick: () => fetchPartners(true),
          },
        ]}
      />

      {/* 2. KPI Summary Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-4 rounded-2xl bg-[#0B0F19]/90 border border-slate-800/80 shadow-lg flex items-center justify-between">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-wider text-emerald-400">Active Customers</div>
            <div className="text-xl font-bold text-slate-100 mt-1 font-mono">{customerCount}</div>
          </div>
          <div className="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            <Users className="w-5 h-5" />
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-[#0B0F19]/90 border border-slate-800/80 shadow-lg flex items-center justify-between">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-wider text-indigo-400">Active Vendors</div>
            <div className="text-xl font-bold text-slate-100 mt-1 font-mono">{vendorCount}</div>
          </div>
          <div className="w-9 h-9 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
            <Building className="w-5 h-5" />
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-[#0B0F19]/90 border border-slate-800/80 shadow-lg flex items-center justify-between">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-wider text-amber-400">Contractors & Others</div>
            <div className="text-xl font-bold text-slate-100 mt-1 font-mono">{contractorCount}</div>
          </div>
          <div className="w-9 h-9 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
            <Briefcase className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* 3. Filter & Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 p-2 rounded-2xl bg-slate-900/60 border border-slate-800/80">
        <div className="flex items-center gap-1 overflow-x-auto no-scrollbar py-1">
          {['ALL', 'CUSTOMER', 'VENDOR', 'CONTRACTOR', 'FINANCIAL_INSTITUTION'].map(tp => (
            <button
              key={tp}
              onClick={() => setTypeFilter(tp)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-colors ${
                typeFilter === tp
                  ? 'bg-emerald-500/15 border border-emerald-500/30 text-emerald-300'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 border border-transparent'
              }`}
            >
              {tp === 'ALL' ? 'All Partners' : tp.replace('_', ' ')}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <div className="relative flex-1 sm:w-60">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by name, GSTIN..."
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
            <option value="ACTIVE">Active</option>
            <option value="ARCHIVED">Archived</option>
            <option value="ALL">All Status</option>
          </select>
        </div>
      </div>

      {/* 4. Partners Data Table */}
      {error && !loading && (
        <BusinessErrorState
          title="Failed to Load Partners"
          message={error}
          onRetry={() => fetchPartners(true)}
        />
      )}

      <BusinessDataTable
        columns={columns}
        data={filteredPartners}
        keyExtractor={item => item.id}
        loading={loading}
        emptyTitle="No Partners Registered"
        emptyDescription="There are no commercial partners matching the current filter criteria."
        emptyActionLabel={isMemberOrAbove ? 'Register First Partner' : undefined}
        onEmptyAction={() => setIsCreateOpen(true)}
        onRowClick={row => {
          setSelectedPartner(row);
          setActionFeedback(null);
        }}
      />

      {/* 5. Partner Detail Drawer */}
      <DetailDrawer
        isOpen={Boolean(selectedPartner)}
        onClose={() => setSelectedPartner(null)}
        title={selectedPartner?.name || 'Partner Details'}
        subtitle={selectedPartner?.legal_name || 'Commercial Counterparty'}
        status={selectedPartner?.status}
        width="md"
        footer={
          selectedPartner && (
            <div className="flex items-center justify-between w-full">
              {selectedPartner.status === 'ACTIVE' && isMemberOrAbove && (
                <button
                  onClick={() => handleArchivePartner(selectedPartner.id)}
                  disabled={actionLoading}
                  className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 text-rose-300 transition-colors disabled:opacity-50"
                >
                  <Archive className="w-3.5 h-3.5" />
                  <span>Archive Partner</span>
                </button>
              )}

              <button
                onClick={() => setSelectedPartner(null)}
                className="px-4 py-2 text-xs text-slate-400 hover:text-white rounded-xl bg-slate-800 ml-auto"
              >
                Close
              </button>
            </div>
          )
        }
      >
        {selectedPartner && (
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

            {/* Profile Overview */}
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-500 uppercase font-semibold text-[10px]">Partner Type</span>
                <span className="font-bold text-slate-200">{selectedPartner.partner_type}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500 uppercase font-semibold text-[10px]">Legal Business Name</span>
                <span className="text-slate-200">{selectedPartner.legal_name || '—'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500 uppercase font-semibold text-[10px]">Tax ID / GSTIN</span>
                <span className="font-mono text-slate-200">{selectedPartner.tax_identifier || '—'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500 uppercase font-semibold text-[10px]">Credit Terms</span>
                <span className="text-slate-200">
                  {selectedPartner.credit_period_days ? `${selectedPartner.credit_period_days} Days` : 'Immediate'}
                </span>
              </div>
            </div>

            {/* Contact Information */}
            <div>
              <h4 className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Contact Details
              </h4>
              <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800 space-y-2 text-xs">
                <div className="flex items-center gap-2 text-slate-300">
                  <Mail className="w-3.5 h-3.5 text-slate-500" />
                  <span>{selectedPartner.email || 'No email address registered'}</span>
                </div>
                <div className="flex items-center gap-2 text-slate-300">
                  <Phone className="w-3.5 h-3.5 text-slate-500" />
                  <span>{selectedPartner.phone || 'No phone number registered'}</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </DetailDrawer>

      {/* 6. Add Partner Drawer */}
      <DetailDrawer
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Register Commercial Partner"
        subtitle="Adds a verified customer, vendor, or contractor to this workspace."
        width="md"
      >
        <form onSubmit={handleCreateSubmit} className="space-y-4 text-xs">
          {createError && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300">
              {createError}
            </div>
          )}

          <div>
            <label className="block text-[11px] font-semibold text-slate-300 mb-1">Partner Type</label>
            <select
              value={createType}
              onChange={e => setCreateType(e.target.value as any)}
              className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500"
            >
              <option value="CUSTOMER">Customer (Client / Receivable Counterparty)</option>
              <option value="VENDOR">Vendor (Supplier / Payable Counterparty)</option>
              <option value="CONTRACTOR">Contractor (Service Provider)</option>
              <option value="FINANCIAL_INSTITUTION">Financial Institution / Bank</option>
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-300 mb-1">Display Name *</label>
            <input
              type="text"
              placeholder="e.g. Acme Corp or John Doe"
              value={createName}
              onChange={e => setCreateName(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500"
              required
            />
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-300 mb-1">Legal Registered Name</label>
            <input
              type="text"
              placeholder="e.g. Acme Technologies Private Limited"
              value={createLegalName}
              onChange={e => setCreateLegalName(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-semibold text-slate-300 mb-1">Email</label>
              <input
                type="email"
                placeholder="billing@partner.com"
                value={createEmail}
                onChange={e => setCreateEmail(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500"
              />
            </div>
            <div>
              <label className="block text-[11px] font-semibold text-slate-300 mb-1">Phone</label>
              <input
                type="tel"
                placeholder="+91 98765 43210"
                value={createPhone}
                onChange={e => setCreatePhone(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-semibold text-slate-300 mb-1">Tax ID / GSTIN</label>
              <input
                type="text"
                placeholder="27AABCU9603R1ZM"
                value={createTaxId}
                onChange={e => setCreateTaxId(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500 font-mono"
              />
            </div>
            <div>
              <label className="block text-[11px] font-semibold text-slate-300 mb-1">Credit Terms (Days)</label>
              <input
                type="number"
                min="0"
                value={createCreditDays}
                onChange={e => setCreateCreditDays(parseInt(e.target.value) || 0)}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500"
              />
            </div>
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
              {createSubmitting ? 'Registering...' : 'Register Partner'}
            </button>
          </div>
        </form>
      </DetailDrawer>
    </motion.div>
  );
};
export default BusinessPartners;
