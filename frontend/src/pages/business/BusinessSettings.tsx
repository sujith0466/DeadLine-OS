import React, { useState, useEffect } from 'react';
import {
  Building2,
  Globe,
  Save,
  CheckCircle2,
  DollarSign
} from 'lucide-react';
import { api } from '../../api';
import { useBusinessAuth } from '../../context/BusinessAuthContext';
import { BusinessPageHeader } from '../../components/Business/BusinessPageHeader';
import { ExecutiveMetricCard } from '../../components/Business/ExecutiveMetricCard';
import { GovernanceSubNav } from '../../components/Business/GovernanceSubNav';

export const BusinessSettings: React.FC = () => {
  const { activeWorkspace, hasPermission } = useBusinessAuth();

  const [name, setName] = useState('');
  const [legalName, setLegalName] = useState('');
  const [taxIdentifier, setTaxIdentifier] = useState('');
  const [baseCurrency, setBaseCurrency] = useState('INR');
  const [timezone, setTimezone] = useState('Asia/Kolkata');
  const [fiscalYearStart, setFiscalYearStart] = useState(4);

  const [saving, setSaving] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const canEdit = hasPermission('workspace:update');

  useEffect(() => {
    if (activeWorkspace) {
      setName(activeWorkspace.name || '');
      setLegalName(activeWorkspace.legal_name || '');
      setTaxIdentifier(activeWorkspace.tax_identifier || '');
      setBaseCurrency(activeWorkspace.base_currency || 'INR');
      setTimezone(activeWorkspace.timezone || 'Asia/Kolkata');
      setFiscalYearStart(activeWorkspace.fiscal_year_start_month || 4);
    }
  }, [activeWorkspace]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    try {
      setSaving(true);
      setError(null);
      setSuccessMessage(null);

      await api.updateCurrentWorkspace({
        name: name.trim(),
        legal_name: legalName.trim() || undefined,
        tax_identifier: taxIdentifier.trim() || undefined,
        base_currency: baseCurrency,
        timezone: timezone,
        fiscal_year_start_month: Number(fiscalYearStart),
      });

      setSuccessMessage('Workspace settings and global configuration updated successfully.');
      setTimeout(() => setSuccessMessage(null), 4000);
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || err?.message || 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <BusinessPageHeader
        title="Workspace & Global Settings"
        breadcrumbs={[
          { label: 'Governance', href: '/business/team' },
          { label: 'Workspace & Global Settings' },
        ]}
      />

      <GovernanceSubNav />

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <ExecutiveMetricCard
          label="Active Tenant Context"
          value={activeWorkspace?.name || 'Workspace'}
          subtext="Cryptographically verified tenant"
          icon={Building2}
          iconColor="text-indigo-400"
        />
        <ExecutiveMetricCard
          label="Base Financial Currency"
          value={baseCurrency}
          subtext="Authoritative ledger denomination"
          icon={DollarSign}
          iconColor="text-emerald-400"
        />
        <ExecutiveMetricCard
          label="Operating Timezone"
          value={timezone}
          subtext="Calendar day-boundary authority"
          icon={Globe}
          iconColor="text-purple-400"
        />
      </div>

      {/* Configuration Form */}
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm max-w-3xl">
        <form onSubmit={handleSave} className="space-y-6">
          {successMessage && (
            <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>{successMessage}</span>
            </div>
          )}

          {error && (
            <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs">
              {error}
            </div>
          )}

          {/* Identity Section */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Building2 className="w-4 h-4 text-indigo-400" />
              <span>Legal Entity Identity & Workspace Profile</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-semibold text-slate-400">Workspace Display Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  disabled={!canEdit}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white mt-1 focus:outline-none focus:border-indigo-500 disabled:opacity-50"
                  required
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-400">Registered Legal Name</label>
                <input
                  type="text"
                  value={legalName}
                  onChange={(e) => setLegalName(e.target.value)}
                  placeholder="e.g. Acme Corporation Private Limited"
                  disabled={!canEdit}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white mt-1 focus:outline-none focus:border-indigo-500 disabled:opacity-50"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-400">Tax Identifier / GSTIN / PAN / EIN</label>
              <input
                type="text"
                value={taxIdentifier}
                onChange={(e) => setTaxIdentifier(e.target.value)}
                placeholder="e.g. 27ABCDE1234F1Z5"
                disabled={!canEdit}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white mt-1 focus:outline-none focus:border-indigo-500 disabled:opacity-50 font-mono"
              />
            </div>
          </div>

          {/* Regional & Fiscal Section */}
          <div className="space-y-4 pt-6 border-t border-slate-800/80">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Globe className="w-4 h-4 text-indigo-400" />
              <span>Global Scale & Fiscal Configuration</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="text-xs font-semibold text-slate-400">Base Currency</label>
                <select
                  value={baseCurrency}
                  onChange={(e) => setBaseCurrency(e.target.value)}
                  disabled={!canEdit}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white mt-1 focus:outline-none focus:border-indigo-500 disabled:opacity-50"
                >
                  <option value="INR">INR (₹) - Indian Rupee</option>
                  <option value="USD">USD ($) - US Dollar</option>
                  <option value="EUR">EUR (€) - Euro</option>
                  <option value="GBP">GBP (£) - British Pound</option>
                  <option value="AED">AED (د.إ) - UAE Dirham</option>
                  <option value="SGD">SGD (S$) - Singapore Dollar</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-400">Timezone</label>
                <select
                  value={timezone}
                  onChange={(e) => setTimezone(e.target.value)}
                  disabled={!canEdit}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white mt-1 focus:outline-none focus:border-indigo-500 disabled:opacity-50"
                >
                  <option value="Asia/Kolkata">Asia/Kolkata (IST +05:30)</option>
                  <option value="UTC">UTC (+00:00)</option>
                  <option value="America/New_York">America/New_York (EST/EDT)</option>
                  <option value="Europe/London">Europe/London (GMT/BST)</option>
                  <option value="Asia/Dubai">Asia/Dubai (GST +04:00)</option>
                  <option value="Asia/Singapore">Asia/Singapore (SGT +08:00)</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-400">Fiscal Year Start</label>
                <select
                  value={fiscalYearStart}
                  onChange={(e) => setFiscalYearStart(Number(e.target.value))}
                  disabled={!canEdit}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white mt-1 focus:outline-none focus:border-indigo-500 disabled:opacity-50"
                >
                  <option value={4}>April (Standard India / UK)</option>
                  <option value={1}>January (Standard US / Calendar)</option>
                  <option value={7}>July (Standard Australia)</option>
                  <option value={10}>October (Standard US Federal)</option>
                </select>
              </div>
            </div>
          </div>

          {canEdit && (
            <div className="pt-4 flex items-center justify-end">
              <button
                type="submit"
                disabled={saving || !name.trim()}
                className="flex items-center gap-2 px-6 py-2.5 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white transition-all shadow-lg shadow-indigo-600/30 disabled:opacity-50"
              >
                <Save className="w-4 h-4" />
                <span>{saving ? 'Saving Changes...' : 'Save Workspace Configuration'}</span>
              </button>
            </div>
          )}
        </form>
      </div>
    </div>
  );
};

export default BusinessSettings;
