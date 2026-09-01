import React, { useState } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { Plus, RefreshCw } from 'lucide-react';
import { useBusinessAuth } from '../../context/BusinessAuthContext';
import { useBusinessDashboard } from '../../hooks/useBusinessDashboard';
import { BusinessPageHeader } from '../../components/Business/BusinessPageHeader';
import { BusinessCashRadar } from '../../components/Business/dashboard/BusinessCashRadar';
import { BusinessExecutiveBriefing } from '../../components/Business/dashboard/BusinessExecutiveBriefing';
import { BusinessAttentionPanel } from '../../components/Business/dashboard/BusinessAttentionPanel';
import { BusinessStagingRadar } from '../../components/Business/dashboard/BusinessStagingRadar';
import { BusinessRescueRadar } from '../../components/Business/dashboard/BusinessRescueRadar';
import { BusinessRecurringRadar } from '../../components/Business/dashboard/BusinessRecurringRadar';
import { CaptureModal } from '../../components/Business/CaptureModal';
import { BusinessCopilotModal } from '../../components/Business/BusinessCopilotModal';

export const BusinessDashboard: React.FC = () => {
  const shouldReduceMotion = useReducedMotion();
  const { activeWorkspace } = useBusinessAuth();
  const {
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
    overdueTasksCount,
    blockedTasksCount,
    lowStockCount,
    outOfStockCount,
    errors,
    refresh,
  } = useBusinessDashboard();

  const [isCaptureOpen, setIsCaptureOpen] = useState(false);
  const [isCopilotOpen, setIsCopilotOpen] = useState(false);

  const formatLastRefreshed = () => {
    if (!lastRefreshedAt) return 'Syncing...';
    return lastRefreshedAt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  return (
    <motion.div
      initial={shouldReduceMotion ? false : { opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: 'easeOut' }}
      className="space-y-6"
    >
      {/* 1. Executive Page Header */}
      <BusinessPageHeader
        breadcrumbs={[
          { label: 'Business OS', href: '/business/dashboard' },
          { label: 'Command', href: '/business/dashboard' },
          { label: 'Executive Dashboard' },
        ]}
        title={activeWorkspace ? `${activeWorkspace.name} Command Center` : 'Executive Command Center'}
        description={`Real-time liquidity, operational staging pipeline, and debt rescue telemetry for ${
          activeWorkspace?.name || 'Workspace'
        } (${activeWorkspace?.base_currency || 'INR'}).`}
        status="ACTIVE"
        primaryAction={{
          label: 'Capture Document',
          icon: Plus,
          onClick: () => setIsCaptureOpen(true),
        }}
        secondaryActions={[
          {
            label: refreshing ? 'Syncing...' : `Refreshed ${formatLastRefreshed()}`,
            icon: RefreshCw,
            onClick: refresh,
          },
        ]}
      />

      {/* 2. Financial Truth & Liquidity Radar (4 Primary KPIs) */}
      <BusinessCashRadar
        cashPosition={cashPosition}
        runway={runway}
        loading={loading}
        error={errors.cash || errors.runway}
        onRetry={refresh}
      />

      {/* 3. Executive Intelligence & Attention Radar (2-Column Grid) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-7">
          <BusinessExecutiveBriefing
            cashPosition={cashPosition}
            runway={runway}
            agingSummary={agingSummary}
            stagedCount={stagedTotal}
            onOpenCopilot={() => setIsCopilotOpen(true)}
            className="h-full"
          />
        </div>

        <div className="lg:col-span-5">
          <BusinessAttentionPanel
            risks={risks}
            overdueCount={agingSummary?.total_overdue_count || 0}
            stagedCount={stagedTotal}
            overdueTasksCount={overdueTasksCount}
            blockedTasksCount={blockedTasksCount}
            lowStockCount={lowStockCount}
            outOfStockCount={outOfStockCount}
            className="h-full"
          />
        </div>
      </div>

      {/* 4. Operational Queues & Execution Radars (3-Column Grid) */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Staging Pipeline */}
        <BusinessStagingRadar
          items={stagedItems}
          total={stagedTotal}
          loading={loading}
          error={errors.staging}
          onOpenCapture={() => setIsCaptureOpen(true)}
          onRetry={refresh}
        />

        {/* Debt Rescue & Recovery */}
        <BusinessRescueRadar
          agingSummary={agingSummary}
          priorities={priorities}
          loading={loading}
          error={errors.rescue}
          onRetry={refresh}
        />

        {/* Recurring Obligations */}
        <BusinessRecurringRadar
          obligations={recurring}
          loading={loading}
          error={errors.recurring}
          onRetry={refresh}
        />
      </div>

      {/* Capture Modal */}
      <CaptureModal
        isOpen={isCaptureOpen}
        onClose={() => setIsCaptureOpen(false)}
        onSuccess={() => {
          setIsCaptureOpen(false);
          refresh();
        }}
      />

      {/* Copilot Modal */}
      <BusinessCopilotModal
        isOpen={isCopilotOpen}
        onClose={() => setIsCopilotOpen(false)}
      />
    </motion.div>
  );
};
export default BusinessDashboard;
