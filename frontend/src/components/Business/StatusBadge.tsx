import React from 'react';

export type BusinessStatusType =
  | 'PAID'
  | 'ISSUED'
  | 'OVERDUE'
  | 'DRAFT'
  | 'PENDING'
  | 'ACTIVE'
  | 'INACTIVE'
  | 'SUSPENDED'
  | 'INVITED'
  | 'FAILED'
  | 'PROCESSING'
  | 'COMMITTED'
  | 'REJECTED'
  | 'STAGED'
  | 'CONFIRMED'
  | 'PARTIALLY_PAID'
  | 'VOID'
  | 'PAUSED'
  | 'CANCELLED'
  | 'ARCHIVED'
  | string;

interface StatusBadgeProps {
  status: BusinessStatusType;
  className?: string;
  showDot?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

const getStatusConfig = (status: string) => {
  const norm = (status || '').toUpperCase().trim();

  // Success / Emerald
  if (['PAID', 'COMMITTED', 'ACTIVE', 'CONFIRMED', 'DELIVERED', 'RESOLVED'].includes(norm)) {
    return {
      bg: 'bg-emerald-500/10',
      border: 'border-emerald-500/30',
      text: 'text-emerald-400',
      dot: 'bg-emerald-400',
      glow: 'shadow-emerald-500/10',
      pulse: false,
    };
  }

  // Info / Cyan / Blue
  if (['ISSUED', 'SENT', 'STAGED', 'INVITED'].includes(norm)) {
    return {
      bg: 'bg-cyan-500/10',
      border: 'border-cyan-500/30',
      text: 'text-cyan-400',
      dot: 'bg-cyan-400',
      glow: 'shadow-cyan-500/10',
      pulse: false,
    };
  }

  // Warning / Amber
  if (['PENDING', 'PARTIALLY_PAID', 'PAUSED', 'DUE_SOON'].includes(norm)) {
    return {
      bg: 'bg-amber-500/10',
      border: 'border-amber-500/30',
      text: 'text-amber-400',
      dot: 'bg-amber-400',
      glow: 'shadow-amber-500/10',
      pulse: false,
    };
  }

  // Live / Processing / Pulsing
  if (['PROCESSING', 'SYNCING', 'RUNNING', 'LIVE'].includes(norm)) {
    return {
      bg: 'bg-teal-500/15',
      border: 'border-teal-500/40',
      text: 'text-teal-300',
      dot: 'bg-teal-400',
      glow: 'shadow-teal-500/20',
      pulse: true,
    };
  }

  // Danger / Rose / Red
  if (['OVERDUE', 'FAILED', 'SUSPENDED', 'REJECTED', 'CANCELLED', 'BOUNCED'].includes(norm)) {
    return {
      bg: 'bg-rose-500/10',
      border: 'border-rose-500/30',
      text: 'text-rose-400',
      dot: 'bg-rose-400',
      glow: 'shadow-rose-500/10',
      pulse: false,
    };
  }

  // Neutral / Slate
  return {
    bg: 'bg-slate-800/60',
    border: 'border-slate-700/60',
    text: 'text-slate-400',
    dot: 'bg-slate-500',
    glow: 'shadow-none',
    pulse: false,
  };
};

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  className = '',
  showDot = true,
  size = 'md',
}) => {
  const config = getStatusConfig(status);

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-[10px] gap-1',
    md: 'px-2.5 py-1 text-xs gap-1.5',
    lg: 'px-3 py-1.5 text-sm gap-2',
  }[size];

  const dotSize = {
    sm: 'w-1 h-1',
    md: 'w-1.5 h-1.5',
    lg: 'w-2 h-2',
  }[size];

  const formattedLabel = (status || '')
    .replace(/_/g, ' ')
    .toLowerCase()
    .replace(/\b\w/g, c => c.toUpperCase());

  return (
    <span
      className={`inline-flex items-center font-medium rounded-full border shadow-sm transition-colors ${config.bg} ${config.border} ${config.text} ${config.glow} ${sizeClasses} ${className}`}
    >
      {showDot && (
        <span
          className={`rounded-full ${config.dot} ${dotSize} ${
            config.pulse ? 'animate-ping' : ''
          }`}
        />
      )}
      <span className="truncate tracking-wide">{formattedLabel}</span>
    </span>
  );
};
