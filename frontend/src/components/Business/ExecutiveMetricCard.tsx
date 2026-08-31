import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { StatusBadge } from './StatusBadge';
import type { BusinessStatusType } from './StatusBadge';
import { FinancialNumber } from './FinancialNumber';

export interface MetricDelta {
  value: number | string;
  direction?: 'up' | 'down' | 'neutral';
  isPositiveGood?: boolean; // Default true (up is good/green)
  label?: string; // e.g. "vs last 30d"
}

export interface ExecutiveMetricCardProps {
  label: string;
  value: string | number;
  isCurrency?: boolean;
  currency?: string;
  icon?: LucideIcon;
  iconColor?: string;
  delta?: MetricDelta;
  status?: BusinessStatusType;
  subtext?: string;
  loading?: boolean;
  delay?: number;
  className?: string;
  onClick?: () => void;
}

export const ExecutiveMetricCard: React.FC<ExecutiveMetricCardProps> = ({
  label,
  value,
  isCurrency = false,
  currency = 'INR',
  icon: Icon,
  iconColor = 'text-emerald-400',
  delta,
  status,
  subtext,
  loading = false,
  delay = 0,
  className = '',
  onClick,
}) => {
  const shouldReduceMotion = useReducedMotion();

  if (loading) {
    return (
      <div className={`p-5 rounded-2xl bg-[#0B0F19]/90 border border-slate-800/80 shadow-xl ${className}`}>
        <div className="flex items-center justify-between mb-4">
          <div className="w-24 h-4 bg-slate-800/80 rounded animate-pulse" />
          <div className="w-8 h-8 rounded-xl bg-slate-800/60 animate-pulse" />
        </div>
        <div className="w-36 h-8 bg-slate-800/80 rounded-lg animate-pulse mb-3" />
        <div className="w-20 h-4 bg-slate-800/50 rounded animate-pulse" />
      </div>
    );
  }

  // Calculate delta color and icon
  let deltaColor = 'text-slate-400 bg-slate-800/50 border-slate-700/50';
  let DeltaIcon = Minus;

  if (delta) {
    const isUp = delta.direction === 'up' || (typeof delta.value === 'number' && delta.value > 0);
    const isDown = delta.direction === 'down' || (typeof delta.value === 'number' && delta.value < 0);
    const isPositiveGood = delta.isPositiveGood !== false;

    if (isUp) {
      DeltaIcon = TrendingUp;
      deltaColor = isPositiveGood
        ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
        : 'text-rose-400 bg-rose-500/10 border-rose-500/20';
    } else if (isDown) {
      DeltaIcon = TrendingDown;
      deltaColor = isPositiveGood
        ? 'text-rose-400 bg-rose-500/10 border-rose-500/20'
        : 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
    }
  }

  return (
    <motion.div
      initial={shouldReduceMotion ? false : { opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: delay * 0.05, ease: 'easeOut' }}
      whileHover={onClick && !shouldReduceMotion ? { y: -3 } : undefined}
      tabIndex={onClick ? 0 : undefined}
      role={onClick ? 'button' : undefined}
      aria-label={onClick ? `${label}: ${value}` : undefined}
      onClick={onClick}
      onKeyDown={e => {
        if (onClick && (e.key === 'Enter' || e.key === ' ')) {
          e.preventDefault();
          onClick();
        }
      }}
      className={`group relative p-5 rounded-2xl bg-[#0B0F19]/90 border border-slate-800/80 shadow-xl transition-all duration-300 hover:border-slate-700/80 hover:shadow-2xl hover:shadow-black/40 overflow-hidden outline-none ${
        onClick ? 'cursor-pointer hover:border-emerald-500/30 focus-visible:ring-2 focus-visible:ring-emerald-500/50' : ''
      } ${className}`}
    >
      {/* Ambient background light hint */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/5 rounded-full blur-3xl pointer-events-none group-hover:bg-emerald-500/10 transition-colors duration-500" />

      {/* Card Header: Label + Icon / Status */}
      <div className="flex items-center justify-between gap-2 mb-3">
        <span className="text-[11px] uppercase tracking-wider font-semibold text-slate-400 group-hover:text-slate-300 transition-colors">
          {label}
        </span>
        <div className="flex items-center gap-2">
          {status && <StatusBadge status={status} size="sm" />}
          {Icon && (
            <div className="p-2 rounded-xl bg-slate-900/90 border border-slate-800/80 text-slate-400 group-hover:text-white group-hover:border-slate-700 transition-colors">
              <Icon className={`w-4 h-4 ${iconColor}`} />
            </div>
          )}
        </div>
      </div>

      {/* Main KPI Value */}
      <div className="mb-2">
        {isCurrency ? (
          <FinancialNumber
            value={value}
            currency={currency}
            className="text-2xl sm:text-3xl font-bold tracking-tight text-white"
          />
        ) : (
          <div className="text-2xl sm:text-3xl font-bold font-mono tracking-tight text-white">
            {value}
          </div>
        )}
      </div>

      {/* Card Footer: Delta / Subtext */}
      {(delta || subtext) && (
        <div className="flex items-center flex-wrap gap-2 text-xs pt-1">
          {delta && (
            <span
              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold border ${deltaColor}`}
            >
              <DeltaIcon className="w-3 h-3" />
              <span>
                {typeof delta.value === 'number' && delta.value > 0 ? `+${delta.value}%` : `${delta.value}%`}
              </span>
            </span>
          )}
          {delta?.label && <span className="text-slate-500 text-[11px]">{delta.label}</span>}
          {subtext && !delta && <span className="text-slate-500 text-[11px]">{subtext}</span>}
        </div>
      )}
    </motion.div>
  );
};
