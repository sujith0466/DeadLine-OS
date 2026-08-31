import React, { useState, useEffect, useCallback } from 'react';
import {
  Sparkles,
  TrendingUp,
  AlertTriangle,
  Clock,
  ArrowRight,
  RefreshCw,
  Sliders,
  DollarSign,
  Info,
  Calendar,
  ArrowUpRight,
  ArrowDownRight,
  ShieldAlert,
  ChevronRight,
  X
} from 'lucide-react';
import { api } from '../../api';
import { useBusinessAuth } from '../../context/BusinessAuthContext';
import { BusinessPageHeader } from '../../components/Business/BusinessPageHeader';
import { ExecutiveMetricCard } from '../../components/Business/ExecutiveMetricCard';
import { FinancialNumber } from '../../components/Business/FinancialNumber';
import { BusinessDataTable } from '../../components/Business/BusinessDataTable';
import type { ColumnDef } from '../../components/Business/BusinessDataTable';
import { DetailDrawer } from '../../components/Business/DetailDrawer';
import { BusinessLoadingState } from '../../components/Business/BusinessLoadingState';
import { BusinessEmptyState } from '../../components/Business/BusinessEmptyState';
import { BusinessErrorState } from '../../components/Business/BusinessErrorState';
import { useNavigate } from 'react-router-dom';

interface TrendPoint extends Record<string, any> {
  period: string;
  label: string;
  income: string;
  expense: string;
  net_flow: string;
  transaction_count: number;
}

interface ForecastWeek extends Record<string, any> {
  week_number: number;
  start_date: string;
  end_date: string;
  label: string;
  projected_inflows: string;
  projected_outflows: string;
  net_flow: string;
  projected_ending_cash: string;
  is_deficit: boolean;
  inflow_count: number;
  outflow_count: number;
}

interface RecommendationItem {
  id: string;
  priority: 'CRITICAL' | 'HIGH' | 'MEDIUM';
  title: string;
  category: string;
  reason: string;
  grounding_fact: string;
  suggested_action: string;
  action_route: string;
}

interface ScenarioData {
  name: string;
  description: string;
  realization_rate_pct: number;
  collection_delay_days: number;
  expense_multiplier: number;
  starting_cash: string;
  projected_inflows: string;
  projected_outflows: string;
  projected_ending_cash: string;
  variance_from_starting: string;
  has_deficit: boolean;
  projected_runway_days: number | null;
}

export const BusinessIntelligence: React.FC = () => {
  const { activeWorkspace } = useBusinessAuth();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState<'brief' | 'forecast' | 'scenarios' | 'trends'>('brief');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Data states
  const [brief, setBrief] = useState<any | null>(null);
  const [forecast, setForecast] = useState<any | null>(null);
  const [scenarios, setScenarios] = useState<Record<string, ScenarioData> | null>(null);
  const [trends, setTrends] = useState<any | null>(null);

  // Filter & control states
  const [forecastHorizon, setForecastHorizon] = useState<number>(90);
  const [trendMonths, setTrendMonths] = useState<number>(6);

  // Custom scenario modal state
  const [isCustomModalOpen, setIsCustomModalOpen] = useState(false);
  const [customRealization, setCustomRealization] = useState(80);
  const [customDelay, setCustomDelay] = useState(30);
  const [customInflation, setCustomInflation] = useState(115);
  const [customSimulating, setCustomSimulating] = useState(false);

  // Provenance drawer state
  const [selectedProvenance, setSelectedProvenance] = useState<any | null>(null);
  const [isProvenanceDrawerOpen, setIsProvenanceDrawerOpen] = useState(false);

  const loadAllIntelligence = useCallback(async () => {
    if (!activeWorkspace) return;
    try {
      setLoading(true);
      setError(null);

      const [bRes, fRes, sRes, tRes] = await Promise.all([
        api.getDecisionBrief().catch(() => ({ data: { brief: null } })),
        api.getCashForecast({ horizon_days: forecastHorizon }).catch(() => ({ data: { forecast: null } })),
        api.simulateScenarios({ horizon_days: 90 }).catch(() => ({ data: { scenarios: { scenarios: null } } })),
        api.getHistoricalTrends({ months: trendMonths }).catch(() => ({ data: { trends: null } }))
      ]);

      setBrief(bRes.data?.brief || null);
      setForecast(fRes.data?.forecast || null);
      setScenarios(sRes.data?.scenarios?.scenarios || null);
      setTrends(tRes.data?.trends || null);
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || err?.message || 'Failed to assemble executive intelligence');
    } finally {
      setLoading(false);
    }
  }, [activeWorkspace, forecastHorizon, trendMonths]);

  useEffect(() => {
    loadAllIntelligence();
  }, [loadAllIntelligence]);

  const handleSimulateCustom = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setCustomSimulating(true);
      const res = await api.simulateScenarios({
        custom_params: {
          realization_rate: customRealization,
          delay_days: customDelay,
          expense_inflation: customInflation
        },
        horizon_days: 90
      });
      setScenarios(res.data?.scenarios?.scenarios || null);
      setIsCustomModalOpen(false);
      setActiveTab('scenarios');
    } catch (err: any) {
      alert(err?.response?.data?.error?.message || 'Failed to simulate scenario');
    } finally {
      setCustomSimulating(false);
    }
  };

  const forecastColumns: ColumnDef<ForecastWeek>[] = [
    {
      key: 'week',
      header: 'Forecast Horizon',
      render: (w) => (
        <div className="flex items-center gap-2">
          <Calendar className="w-3.5 h-3.5 text-indigo-400" />
          <span className="font-semibold text-white">{w.label}</span>
        </div>
      ),
    },
    {
      key: 'inflows',
      header: 'Projected Inflows',
      render: (w) => (
        <div className="text-emerald-400 font-mono text-xs font-semibold">
          <FinancialNumber value={w.projected_inflows} />
          <span className="text-[10px] text-slate-500 ml-1">({w.inflow_count} items)</span>
        </div>
      ),
    },
    {
      key: 'outflows',
      header: 'Projected Outflows',
      render: (w) => (
        <div className="text-rose-400 font-mono text-xs font-semibold">
          <FinancialNumber value={w.projected_outflows} />
          <span className="text-[10px] text-slate-500 ml-1">({w.outflow_count} items)</span>
        </div>
      ),
    },
    {
      key: 'net',
      header: 'Net Weekly Flow',
      render: (w) => {
        const net = parseFloat(w.net_flow || '0');
        return (
          <div className={`font-mono text-xs font-bold ${net >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
            <FinancialNumber value={net} />
          </div>
        );
      },
    },
    {
      key: 'ending',
      header: 'Projected Ending Cash',
      render: (w) => (
        <div className="flex items-center gap-2">
          <span className={`font-mono text-xs font-bold ${w.is_deficit ? 'text-rose-400' : 'text-white'}`}>
            <FinancialNumber value={w.projected_ending_cash} />
          </span>
          {w.is_deficit && (
            <span className="px-2 py-0.5 rounded-full bg-rose-500/10 border border-rose-500/20 text-[10px] text-rose-400 font-semibold">
              DEFICIT
            </span>
          )}
        </div>
      ),
    },
  ];

  const trendColumns: ColumnDef<TrendPoint>[] = [
    {
      key: 'period',
      header: 'Historical Month',
      render: (t) => (
        <div className="font-semibold text-white flex items-center gap-2">
          <Clock className="w-3.5 h-3.5 text-slate-500" />
          <span>{t.label}</span>
        </div>
      ),
    },
    {
      key: 'income',
      header: 'Authoritative Inflows',
      render: (t) => (
        <span className="text-emerald-400 font-mono text-xs font-semibold">
          <FinancialNumber value={t.income} />
        </span>
      ),
    },
    {
      key: 'expense',
      header: 'Authoritative Burn',
      render: (t) => (
        <span className="text-rose-400 font-mono text-xs font-semibold">
          <FinancialNumber value={t.expense} />
        </span>
      ),
    },
    {
      key: 'net',
      header: 'Net Operating Flow',
      render: (t) => {
        const net = parseFloat(t.net_flow || '0');
        return (
          <span className={`font-mono text-xs font-bold ${net >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
            <FinancialNumber value={net} />
          </span>
        );
      },
    },
    {
      key: 'txs',
      header: 'Activity Density',
      render: (t) => (
        <span className="text-xs text-slate-400 font-mono">
          {t.transaction_count} settled txs
        </span>
      ),
    },
  ];

  if (loading && !brief) {
    return (
      <div className="space-y-6">
        <BusinessPageHeader
          title="Executive Intelligence & Decision Support"
          breadcrumbs={[{ label: 'Intelligence' }]}
        />
        <BusinessLoadingState type="kpi-grid" rows={4} />
        <BusinessLoadingState type="card" rows={3} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <BusinessPageHeader
          title="Executive Intelligence & Decision Support"
          breadcrumbs={[{ label: 'Intelligence' }]}
        />
        <BusinessErrorState message={error} onRetry={loadAllIntelligence} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <BusinessPageHeader
        title="Executive Intelligence & Decision Support"
        breadcrumbs={[
          { label: 'Intelligence', href: '/business/intelligence' },
          { label: 'Decision Engine' },
        ]}
        primaryAction={{
          label: 'Simulate Custom Scenario',
          icon: Sliders,
          onClick: () => setIsCustomModalOpen(true),
        }}
        secondaryActions={[
          {
            label: 'Refresh Analysis',
            icon: RefreshCw,
            onClick: loadAllIntelligence,
          },
        ]}
      />

      {/* Primary KPI Deck */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <ExecutiveMetricCard
          label="Confirmed Cash Reality"
          value={brief?.confirmed_cash || '0.00'}
          isCurrency={true}
          subtext="Authoritative ledger truth"
          icon={DollarSign}
          iconColor="text-emerald-400"
        />
        <ExecutiveMetricCard
          label="Projected 30d Position"
          value={brief?.projected_position_30d || '0.00'}
          isCurrency={true}
          subtext="Fact + committed invoices"
          icon={TrendingUp}
          iconColor="text-indigo-400"
        />
        <ExecutiveMetricCard
          label="Deterministic Runway"
          value={brief?.runway_days !== null ? `${brief?.runway_days} Days` : 'Calculating'}
          subtext={brief?.runway_state || 'STABLE'}
          icon={Clock}
          iconColor="text-purple-400"
        />
        <ExecutiveMetricCard
          label="Active Risk Signals"
          value={brief?.active_risks?.length || 0}
          subtext={brief?.financial_health || 'HEALTHY'}
          icon={AlertTriangle}
          iconColor={brief?.active_risks?.length > 0 ? 'text-amber-400' : 'text-emerald-400'}
        />
      </div>

      {/* Domain Navigation Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab('brief')}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all ${
              activeTab === 'brief'
                ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-600/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            Executive Decision Brief ({brief?.recommendations?.length || 0})
          </button>
          <button
            onClick={() => setActiveTab('forecast')}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all ${
              activeTab === 'forecast'
                ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-600/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            Cash Flow Forecast ({forecastHorizon}d)
          </button>
          <button
            onClick={() => setActiveTab('scenarios')}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all ${
              activeTab === 'scenarios'
                ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-600/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            Scenario Simulator (3 Models)
          </button>
          <button
            onClick={() => setActiveTab('trends')}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all ${
              activeTab === 'trends'
                ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-600/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            Historical Trends ({trendMonths}m)
          </button>
        </div>

        {/* Tab-specific selectors */}
        {activeTab === 'forecast' && (
          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-400">Horizon:</span>
            {[30, 60, 90].map((h) => (
              <button
                key={h}
                onClick={() => setForecastHorizon(h)}
                className={`px-2.5 py-1 rounded-lg font-mono text-[11px] font-medium transition-all ${
                  forecastHorizon === h ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
                }`}
              >
                {h} Days
              </button>
            ))}
          </div>
        )}

        {activeTab === 'trends' && (
          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-400">Timeframe:</span>
            {[3, 6, 12].map((m) => (
              <button
                key={m}
                onClick={() => setTrendMonths(m)}
                className={`px-2.5 py-1 rounded-lg font-mono text-[11px] font-medium transition-all ${
                  trendMonths === m ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
                }`}
              >
                {m} Months
              </button>
            ))}
          </div>
        )}
      </div>

      {/* TAB 1: EXECUTIVE DECISION BRIEF */}
      {activeTab === 'brief' && (
        <div className="space-y-6">
          {/* AI Grounding Notice */}
          <div className="p-4 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-start gap-3">
            <Sparkles className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
            <div className="text-xs space-y-1">
              <div className="font-semibold text-indigo-300">
                Authoritative Decision Hierarchy: FACT → SIGNAL → FORECAST → SCENARIO → RECOMMENDATION
              </div>
              <p className="text-slate-400 leading-relaxed">
                All recommendations are deterministically synthesized from confirmed ledger records, active receivables, payables, and recurring obligations. Actions are advisory and require human confirmation.
              </p>
            </div>
          </div>

          {/* Action Recommendations Queue */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-indigo-400" />
              <span>Prioritized Executive Recommendations ({brief?.recommendations?.length || 0})</span>
            </h3>

            {(!brief?.recommendations || brief.recommendations.length === 0) ? (
              <BusinessEmptyState
                title="Zero Urgent Risks or Operational Action Items"
                description="Your workspace liquidity, collections, and recurring obligations are in optimal balance."
              />
            ) : (
              <div className="grid grid-cols-1 gap-3">
                {brief.recommendations.map((rec: RecommendationItem) => (
                  <div
                    key={rec.id}
                    className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-slate-700 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-lg shadow-black/20"
                  >
                    <div className="space-y-1.5 flex-1">
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold font-mono ${
                          rec.priority === 'CRITICAL'
                            ? 'bg-rose-500/10 border border-rose-500/20 text-rose-400'
                            : rec.priority === 'HIGH'
                            ? 'bg-amber-500/10 border border-amber-500/20 text-amber-400'
                            : 'bg-indigo-500/10 border border-indigo-500/20 text-indigo-400'
                        }`}>
                          {rec.priority}
                        </span>
                        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                          {rec.category}
                        </span>
                      </div>

                      <h4 className="text-sm font-bold text-white">{rec.title}</h4>
                      <p className="text-xs text-slate-400">{rec.reason}</p>

                      <div className="text-[11px] text-slate-500 flex items-center gap-1.5 pt-1">
                        <Info className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                        <span><strong>Grounding Fact:</strong> {rec.grounding_fact}</span>
                      </div>
                    </div>

                    <button
                      onClick={() => navigate(rec.action_route)}
                      className="flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-all shadow-md shadow-indigo-600/20 shrink-0"
                    >
                      <span>{rec.suggested_action}</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Active Risk Indicators */}
          {brief?.active_risks && brief.active_risks.length > 0 && (
            <div className="p-5 rounded-2xl bg-amber-500/10 border border-amber-500/20 space-y-3">
              <h4 className="text-xs font-semibold text-amber-400 uppercase tracking-wider flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-amber-400" />
                <span>Deterministic Cash Risk Indicators ({brief.active_risks.length})</span>
              </h4>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {brief.active_risks.map((risk: any, i: number) => (
                  <div key={i} className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800/80 space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-white">{risk.title}</span>
                      <span className="font-mono text-amber-400 font-semibold">{risk.severity}</span>
                    </div>
                    <p className="text-xs text-slate-400">{risk.message}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: CASH FLOW FORECAST */}
      {activeTab === 'forecast' && (
        <div className="space-y-6">
          {forecast && (
            <>
              {/* Forecast Trajectory Summary */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 space-y-1">
                  <div className="text-xs text-slate-400 flex items-center gap-1.5">
                    <ArrowUpRight className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Total Projected Inflows</span>
                  </div>
                  <div className="text-lg font-bold text-emerald-400">
                    <FinancialNumber value={forecast.total_projected_inflows} />
                  </div>
                  <div className="text-[11px] text-slate-500">Scheduled receivables + recurring</div>
                </div>

                <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 space-y-1">
                  <div className="text-xs text-slate-400 flex items-center gap-1.5">
                    <ArrowDownRight className="w-3.5 h-3.5 text-rose-400" />
                    <span>Total Projected Outflows</span>
                  </div>
                  <div className="text-lg font-bold text-rose-400">
                    <FinancialNumber value={forecast.total_projected_outflows} />
                  </div>
                  <div className="text-[11px] text-slate-500">Committed bills + operational burn</div>
                </div>

                <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 space-y-1">
                  <div className="text-xs text-slate-400 flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5 text-indigo-400" />
                    <span>Forecast Minimum Point (Trough)</span>
                  </div>
                  <div className="text-lg font-bold text-white">
                    <FinancialNumber value={forecast.minimum_projected_cash} />
                  </div>
                  <div className="text-[11px] text-slate-500">Projected trough on {forecast.minimum_cash_date}</div>
                </div>
              </div>

              {/* Deficit Alert if any */}
              {forecast.has_projected_deficit && (
                <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
                  <div className="text-xs space-y-1">
                    <div className="font-semibold text-rose-300">Projected Liquidity Deficit Detected</div>
                    <p className="text-slate-400">
                      Based on committed bills and operational obligations, cash is projected to fall below zero on or around <strong>{forecast.first_deficit_date}</strong>. Accelerate receivables or defer discretionary payables.
                    </p>
                  </div>
                </div>
              )}

              {/* Weekly Trajectory Table */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-indigo-400" />
                    <span>Weekly Forward Cash Trajectory</span>
                  </h3>
                  <button
                    onClick={() => {
                      setSelectedProvenance({
                        title: 'Cash Flow Forecast Methodology',
                        method: forecast.methodology,
                        inputs: 'Confirmed Cash + Invoices (Receivable/Payable) + Active Recurring Commitments',
                        timestamp: forecast.generated_at,
                        coverage: `${forecast.forecast_horizon_days} Days Ahead`
                      });
                      setIsProvenanceDrawerOpen(true);
                    }}
                    className="text-xs text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1"
                  >
                    <span>View Provenance & Logic</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                </div>

                <BusinessDataTable
                  columns={forecastColumns}
                  data={forecast.weekly_trajectory || []}
                  keyExtractor={(w) => w.week_number.toString()}
                />
              </div>
            </>
          )}
        </div>
      )}

      {/* TAB 3: SCENARIO SIMULATOR */}
      {activeTab === 'scenarios' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Sliders className="w-4 h-4 text-indigo-400" />
              <span>Multi-Model Stress Testing & Liquidity Simulations</span>
            </h3>
            <button
              onClick={() => setIsCustomModalOpen(true)}
              className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 hover:bg-slate-800 transition-colors"
            >
              Adjust Simulation Levers
            </button>
          </div>

          {scenarios && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              {/* Baseline */}
              {scenarios.baseline && (
                <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-indigo-400 uppercase tracking-wider">
                      {scenarios.baseline.name}
                    </span>
                    <span className="px-2 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-[10px] text-indigo-300 font-mono">
                      STANDARD
                    </span>
                  </div>
                  <p className="text-xs text-slate-400">{scenarios.baseline.description}</p>

                  <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-400">Projected Ending Cash</span>
                      <span className="font-bold text-white font-mono">
                        <FinancialNumber value={scenarios.baseline.projected_ending_cash} />
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-400">Projected Inflows</span>
                      <span className="font-mono text-emerald-400">
                        <FinancialNumber value={scenarios.baseline.projected_inflows} />
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-400">Projected Outflows</span>
                      <span className="font-mono text-rose-400">
                        <FinancialNumber value={scenarios.baseline.projected_outflows} />
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* Conservative */}
              {scenarios.conservative && (
                <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-amber-400 uppercase tracking-wider">
                      {scenarios.conservative.name}
                    </span>
                    <span className="px-2 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/20 text-[10px] text-amber-300 font-mono">
                      CONSERVATIVE
                    </span>
                  </div>
                  <p className="text-xs text-slate-400">{scenarios.conservative.description}</p>

                  <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-400">Projected Ending Cash</span>
                      <span className="font-bold text-amber-300 font-mono">
                        <FinancialNumber value={scenarios.conservative.projected_ending_cash} />
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-400">Inflow Realization</span>
                      <span className="font-mono text-slate-200">85% (-15% slippage)</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-400">Expense Buffer</span>
                      <span className="font-mono text-slate-200">+10% buffer</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Stress Test */}
              {scenarios.stress && (
                <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-rose-400 uppercase tracking-wider">
                      {scenarios.stress.name}
                    </span>
                    <span className="px-2 py-0.5 rounded-full bg-rose-500/10 border border-rose-500/20 text-[10px] text-rose-300 font-mono">
                      DOWNSIDE
                    </span>
                  </div>
                  <p className="text-xs text-slate-400">{scenarios.stress.description}</p>

                  <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-400">Projected Ending Cash</span>
                      <span className={`font-bold font-mono ${scenarios.stress.has_deficit ? 'text-rose-400' : 'text-white'}`}>
                        <FinancialNumber value={scenarios.stress.projected_ending_cash} />
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-400">Inflow Realization</span>
                      <span className="font-mono text-slate-200">70% (-30% default)</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-400">Expense Shock</span>
                      <span className="font-mono text-slate-200">+25% surge</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Custom Scenario Result if active */}
          {scenarios?.custom && (
            <div className="p-5 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-indigo-400 uppercase tracking-wider">
                  Active Custom Simulation
                </span>
                <span className="text-xs text-slate-400 font-mono">
                  {scenarios.custom.description}
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                  <div className="text-[11px] text-slate-400">Custom Ending Liquidity</div>
                  <div className="text-base font-bold text-white font-mono">
                    <FinancialNumber value={scenarios.custom.projected_ending_cash} />
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                  <div className="text-[11px] text-slate-400">Simulated Outflows</div>
                  <div className="text-base font-bold text-rose-400 font-mono">
                    <FinancialNumber value={scenarios.custom.projected_outflows} />
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                  <div className="text-[11px] text-slate-400">Estimated Runway Days</div>
                  <div className="text-base font-bold text-indigo-300 font-mono">
                    {scenarios.custom.projected_runway_days !== null ? `${scenarios.custom.projected_runway_days} Days` : 'Stable'}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 4: HISTORICAL TRENDS */}
      {activeTab === 'trends' && (
        <div className="space-y-6">
          {trends && (
            <>
              {trends.insufficient_history ? (
                <BusinessEmptyState
                  title="Insufficient Historical Transactions"
                  description="At least 2 active calendar months of confirmed transactions are required to plot verified revenue and expense trends."
                />
              ) : (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 space-y-1">
                      <div className="text-xs text-slate-400">Avg Monthly Inflow</div>
                      <div className="text-lg font-bold text-emerald-400">
                        <FinancialNumber value={trends.avg_monthly_income} />
                      </div>
                      <div className="text-[11px] text-slate-500">Across {trends.months_analyzed} month window</div>
                    </div>

                    <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 space-y-1">
                      <div className="text-xs text-slate-400">Avg Monthly Burn</div>
                      <div className="text-lg font-bold text-rose-400">
                        <FinancialNumber value={trends.avg_monthly_expense} />
                      </div>
                      <div className="text-[11px] text-slate-500">Operational cash consumption</div>
                    </div>

                    <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 space-y-1">
                      <div className="text-xs text-slate-400">Avg Net Operating Flow</div>
                      <div className="text-lg font-bold text-white">
                        <FinancialNumber value={trends.avg_monthly_net_flow} />
                      </div>
                      <div className="text-[11px] text-slate-500">Monthly surplus / deficit</div>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                      <TrendingUp className="w-4 h-4 text-indigo-400" />
                      <span>Monthly Verified Settlement Breakdown</span>
                    </h3>

                    <BusinessDataTable
                      columns={trendColumns}
                      data={trends.trends || []}
                      keyExtractor={(t) => t.period}
                    />
                  </div>
                </>
              )}
            </>
          )}
        </div>
      )}

      {/* Custom Scenario Modal */}
      {isCustomModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl flex flex-col">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/40">
              <h3 className="font-semibold text-white flex items-center gap-2">
                <Sliders className="w-4 h-4 text-indigo-400" />
                Configure Custom Scenario Levers
              </h3>
              <button
                onClick={() => setIsCustomModalOpen(false)}
                className="text-slate-400 hover:text-white p-2 rounded-lg hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSimulateCustom} className="p-6 space-y-5">
              <div>
                <div className="flex items-center justify-between text-xs">
                  <label className="font-semibold text-slate-300">Receivable Realization Rate</label>
                  <span className="font-mono text-indigo-400 font-bold">{customRealization}%</span>
                </div>
                <input
                  type="range"
                  min="40"
                  max="100"
                  step="5"
                  value={customRealization}
                  onChange={(e) => setCustomRealization(Number(e.target.value))}
                  className="w-full mt-2 accent-indigo-500"
                />
                <div className="text-[11px] text-slate-500 mt-0.5">Assumed % of outstanding invoices successfully collected</div>
              </div>

              <div>
                <div className="flex items-center justify-between text-xs">
                  <label className="font-semibold text-slate-300">Collection Delay (Days)</label>
                  <span className="font-mono text-indigo-400 font-bold">{customDelay} Days</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="90"
                  step="15"
                  value={customDelay}
                  onChange={(e) => setCustomDelay(Number(e.target.value))}
                  className="w-full mt-2 accent-indigo-500"
                />
                <div className="text-[11px] text-slate-500 mt-0.5">Average collection lag past due date</div>
              </div>

              <div>
                <div className="flex items-center justify-between text-xs">
                  <label className="font-semibold text-slate-300">Operating Expense Inflation Factor</label>
                  <span className="font-mono text-rose-400 font-bold">+{customInflation - 100}%</span>
                </div>
                <input
                  type="range"
                  min="100"
                  max="150"
                  step="5"
                  value={customInflation}
                  onChange={(e) => setCustomInflation(Number(e.target.value))}
                  className="w-full mt-2 accent-indigo-500"
                />
                <div className="text-[11px] text-slate-500 mt-0.5">Contingency multiplier applied to bills and recurring burn</div>
              </div>

              <div className="pt-2 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setIsCustomModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={customSimulating}
                  className="px-5 py-2 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white transition-all shadow-lg shadow-indigo-600/30 disabled:opacity-50"
                >
                  {customSimulating ? 'Simulating...' : 'Run Simulation'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Provenance & Explanation Drawer */}
      <DetailDrawer
        isOpen={isProvenanceDrawerOpen && Boolean(selectedProvenance)}
        onClose={() => setIsProvenanceDrawerOpen(false)}
        title={selectedProvenance?.title || 'Calculation Provenance'}
        subtitle="Auditable Calculation Logic & Data Grounding"
      >
        {selectedProvenance && (
          <div className="space-y-5 text-xs">
            <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 space-y-2.5">
              <div>
                <div className="text-slate-400">Methodology</div>
                <div className="font-mono text-indigo-400 font-semibold mt-0.5">{selectedProvenance.method}</div>
              </div>
              <div>
                <div className="text-slate-400">Input Data Sources</div>
                <div className="text-white mt-0.5">{selectedProvenance.inputs}</div>
              </div>
              <div>
                <div className="text-slate-400">Coverage Horizon</div>
                <div className="text-white mt-0.5">{selectedProvenance.coverage}</div>
              </div>
              <div>
                <div className="text-slate-400">Computation Timestamp (UTC)</div>
                <div className="font-mono text-slate-300 mt-0.5">{selectedProvenance.timestamp}</div>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 leading-relaxed">
              <strong>Strict Financial Integrity Notice:</strong> Forward-looking cash forecasts and scenario simulations are ephemeral projections calculated from confirmed ledger commitments. They do not mutate authoritative accounting records.
            </div>
          </div>
        )}
      </DetailDrawer>
    </div>
  );
};

export default BusinessIntelligence;
