import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '../api';
import { useBusinessAuth } from '../context/BusinessAuthContext';

export interface CashPositionData {
  confirmed_cash: string;
  committed_inflows: string;
  committed_outflows: string;
  projected_position: string;
  window_days: number;
  currency: string;
}

export interface RunwayData {
  state: 'RUNWAY_NEGATIVE' | 'RUNWAY_STALE' | 'RUNWAY_INSUFFICIENT_HISTORY' | 'RUNWAY_ZERO_BURN' | 'CALCULATED';
  runway_days: number | null;
  confirmed_cash: string;
  adbr_30: string;
  message: string;
}

export interface RiskAlert {
  code: string;
  severity: 'CRITICAL' | 'WARNING' | 'INFO';
  title: string;
  message: string;
  metric?: string;
}

export interface StagedItemSummary {
  id: string;
  source_type: string;
  candidate_type: string;
  status: string;
  created_at: string;
  extracted_data: Record<string, any>;
}

export interface AgingBucket {
  count: number;
  total: string;
  invoices: Array<{
    id: string;
    invoice_number: string;
    partner_name: string;
    balance_due: string;
    due_date: string;
    days_overdue: number;
  }>;
}

export interface AgingSummaryData {
  total_overdue_amount: string;
  total_overdue_count: number;
  as_of_date: string;
  buckets: {
    '1_to_30_days': AgingBucket;
    '31_to_60_days': AgingBucket;
    '61_to_90_days': AgingBucket;
    '90_plus_days': AgingBucket;
  };
}

export interface PriorityReceivable {
  id: string;
  invoice_number: string;
  partner_name: string;
  balance_due: string;
  due_date: string;
  days_overdue: number;
  priority_score: number;
}

export interface RecurringObligationSummary {
  id: string;
  title: string;
  obligation_type: string;
  amount: string;
  currency: string;
  frequency: string;
  next_due_date: string;
  status: string;
  partner_name?: string;
}

export function useBusinessDashboard() {
  const { activeWorkspace } = useBusinessAuth();

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastRefreshedAt, setLastRefreshedAt] = useState<Date | null>(null);

  const [cashPosition, setCashPosition] = useState<CashPositionData | null>(null);
  const [runway, setRunway] = useState<RunwayData | null>(null);
  const [risks, setRisks] = useState<RiskAlert[]>([]);
  const [stagedItems, setStagedItems] = useState<StagedItemSummary[]>([]);
  const [stagedTotal, setStagedTotal] = useState(0);
  const [agingSummary, setAgingSummary] = useState<AgingSummaryData | null>(null);
  const [priorities, setPriorities] = useState<PriorityReceivable[]>([]);
  const [recurring, setRecurring] = useState<RecurringObligationSummary[]>([]);

  // Per-section error state
  const [errors, setErrors] = useState<{
    cash?: string;
    runway?: string;
    risks?: string;
    staging?: string;
    rescue?: string;
    recurring?: string;
  }>({});

  const isMounted = useRef(true);
  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
    };
  }, []);

  const fetchDashboardData = useCallback(async (isManualRefresh = false) => {
    if (!activeWorkspace?.id) {
      setLoading(false);
      return;
    }

    if (isManualRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    const newErrors: typeof errors = {};

    // 1. Fetch Cash Position
    const cashPromise = api.getCashPosition(30)
      .then(res => {
        if (isMounted.current && res?.data?.cash_position) {
          setCashPosition(res.data.cash_position);
        }
      })
      .catch(err => {
        if (isMounted.current) {
          newErrors.cash = err?.message || 'Failed to load cash position';
        }
      });

    // 2. Fetch Runway
    const runwayPromise = api.getRunway()
      .then(res => {
        if (isMounted.current && res?.data?.runway) {
          setRunway(res.data.runway);
        }
      })
      .catch(err => {
        if (isMounted.current) {
          newErrors.runway = err?.message || 'Failed to load runway';
        }
      });

    // 3. Fetch Risks
    const risksPromise = api.getBusinessRisks()
      .then(res => {
        if (isMounted.current && Array.isArray(res?.data?.risks)) {
          setRisks(res.data.risks);
        }
      })
      .catch(err => {
        if (isMounted.current) {
          newErrors.risks = err?.message || 'Failed to load risk analysis';
        }
      });

    // 4. Fetch Staging Queue
    const stagingPromise = api.listStagedItems({ status: 'STAGED', limit: 5 })
      .then(res => {
        if (isMounted.current) {
          setStagedItems(res?.data?.staged_items || []);
          setStagedTotal(res?.data?.total || 0);
        }
      })
      .catch(err => {
        if (isMounted.current) {
          newErrors.staging = err?.message || 'Failed to load staging queue';
        }
      });

    // 5. Fetch Rescue Aging Summary
    const agingPromise = api.getRescueAgingSummary()
      .then(res => {
        if (isMounted.current && res?.data?.buckets) {
          setAgingSummary(res.data);
        }
      })
      .catch(err => {
        if (isMounted.current) {
          newErrors.rescue = err?.message || 'Failed to load overdue aging summary';
        }
      });

    // 6. Fetch Priority Receivables
    const prioritiesPromise = api.getPriorityReceivables(5)
      .then(res => {
        if (isMounted.current && Array.isArray(res?.data?.priorities)) {
          setPriorities(res.data.priorities);
        }
      })
      .catch(() => {
        // Non-blocking fallback
      });

    // 7. Fetch Recurring Obligations
    const recurringPromise = api.listRecurringObligations({ status: 'ACTIVE' })
      .then(res => {
        if (isMounted.current && Array.isArray(res?.data?.obligations)) {
          setRecurring(res.data.obligations);
        }
      })
      .catch(err => {
        if (isMounted.current) {
          newErrors.recurring = err?.message || 'Failed to load recurring obligations';
        }
      });

    await Promise.allSettled([
      cashPromise,
      runwayPromise,
      risksPromise,
      stagingPromise,
      agingPromise,
      prioritiesPromise,
      recurringPromise,
    ]);

    if (isMounted.current) {
      setErrors(newErrors);
      setLastRefreshedAt(new Date());
      setLoading(false);
      setRefreshing(false);
    }
  }, [activeWorkspace?.id]);

  useEffect(() => {
    fetchDashboardData(false);

    const handleStagingUpdate = () => fetchDashboardData(true);
    const handleWorkspaceChange = () => fetchDashboardData(false);

    window.addEventListener('deadline_staging_updated', handleStagingUpdate);
    window.addEventListener('deadline_workspace_changed', handleWorkspaceChange);

    return () => {
      window.removeEventListener('deadline_staging_updated', handleStagingUpdate);
      window.removeEventListener('deadline_workspace_changed', handleWorkspaceChange);
    };
  }, [fetchDashboardData]);

  return {
    loading,
    refreshing,
    lastRefreshedAt,
    cashPosition,
    runway,
    risks,
    stagedItems,
    stagedTotal,
    agingSummary,
    priorities,
    recurring,
    errors,
    refresh: () => fetchDashboardData(true),
  };
}
