import React from 'react';
import { Wallet, Hourglass, ArrowDownRight, ArrowUpRight } from 'lucide-react';
import { ExecutiveMetricCard } from '../ExecutiveMetricCard';
import { BusinessLoadingState } from '../BusinessLoadingState';
import { BusinessErrorState } from '../BusinessErrorState';
import type { CashPositionData, RunwayData } from '../../../hooks/useBusinessDashboard';
import type { BusinessStatusType } from '../StatusBadge';

interface BusinessCashRadarProps {
  cashPosition: CashPositionData | null;
  runway: RunwayData | null;
  loading: boolean;
  error?: string;
  onRetry?: () => void;
}

export const BusinessCashRadar: React.FC<BusinessCashRadarProps> = ({
  cashPosition,
  runway,
  loading,
  error,
  onRetry,
}) => {
  if (loading && !cashPosition && !runway) {
    return <BusinessLoadingState type="kpi-grid" className="mb-6" />;
  }

  if (error && !cashPosition && !runway) {
    return (
      <BusinessErrorState
        title="Cash & Runway Data Unavailable"
        message={error}
        onRetry={onRetry}
        className="mb-6"
      />
    );
  }

  const confirmedCash = cashPosition?.confirmed_cash || '0.00';
  const committedInflows = cashPosition?.committed_inflows || '0.00';
  const committedOutflows = cashPosition?.committed_outflows || '0.00';
  const currency = cashPosition?.currency || 'INR';

  // Map 5-tier runway state to StatusBadge semantic status
  let runwayStatus: BusinessStatusType = 'ACTIVE';
  let runwayValueText = '—';
  let runwaySubtext = runway?.message || 'Operational runway';

  if (runway) {
    switch (runway.state) {
      case 'RUNWAY_NEGATIVE':
        runwayStatus = 'OVERDUE';
        runwayValueText = '0 Days';
        break;
      case 'RUNWAY_STALE':
        runwayStatus = 'PENDING';
        runwayValueText = 'Stale Data';
        break;
      case 'RUNWAY_INSUFFICIENT_HISTORY':
        runwayStatus = 'PROCESSING';
        runwayValueText = 'Calculating';
        break;
      case 'RUNWAY_ZERO_BURN':
        runwayStatus = 'PAID';
        runwayValueText = 'Zero Burn';
        break;
      case 'CALCULATED':
        runwayStatus = runway.runway_days !== null && runway.runway_days < 30 ? 'OVERDUE' : 'ACTIVE';
        runwayValueText = `${runway.runway_days} Days`;
        break;
    }
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {/* 1. Confirmed Cash */}
      <ExecutiveMetricCard
        label="Confirmed Cash"
        value={confirmedCash}
        isCurrency={true}
        currency={currency}
        icon={Wallet}
        subtext="Settled bank & cash balance"
        status="ACTIVE"
      />

      {/* 2. Operational Runway */}
      <ExecutiveMetricCard
        label="Operational Runway"
        value={runwayValueText}
        isCurrency={false}
        icon={Hourglass}
        subtext={runwaySubtext}
        status={runwayStatus}
      />

      {/* 3. Committed 30D Inflows */}
      <ExecutiveMetricCard
        label="Committed Inflows (30D)"
        value={committedInflows}
        isCurrency={true}
        currency={currency}
        icon={ArrowDownRight}
        subtext="Receivables due in 30 days"
        status="ISSUED"
      />

      {/* 4. Committed 30D Outflows */}
      <ExecutiveMetricCard
        label="Committed Outflows (30D)"
        value={committedOutflows}
        isCurrency={true}
        currency={currency}
        icon={ArrowUpRight}
        subtext="Payables due in 30 days"
        status="DRAFT"
      />
    </div>
  );
};
