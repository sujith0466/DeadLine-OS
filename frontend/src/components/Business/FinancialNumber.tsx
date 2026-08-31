import React from 'react';

interface FinancialNumberProps {
  value: number | string | null | undefined;
  currency?: string;
  className?: string;
  variant?: 'default' | 'positive' | 'negative' | 'muted' | 'auto';
  compact?: boolean;
  decimals?: number;
  showSign?: boolean;
}

export const formatCurrencySymbol = (currency?: string): string => {
  const curr = (currency || 'INR').toUpperCase();
  switch (curr) {
    case 'INR':
      return '₹';
    case 'USD':
      return '$';
    case 'EUR':
      return '€';
    case 'GBP':
      return '£';
    case 'JPY':
      return '¥';
    case 'AUD':
      return 'A$';
    case 'CAD':
      return 'C$';
    case 'SGD':
      return 'S$';
    case 'AED':
      return 'AED ';
    default:
      return `${curr} `;
  }
};

export const FinancialNumber: React.FC<FinancialNumberProps> = ({
  value,
  currency = 'INR',
  className = '',
  variant = 'default',
  compact = false,
  decimals = 2,
  showSign = false,
}) => {
  const numValue = typeof value === 'number' ? value : parseFloat(value as string) || 0;
  const isNegative = numValue < 0;
  const isPositive = numValue > 0;

  const symbol = formatCurrencySymbol(currency);

  let formattedNumber = '';

  if (compact) {
    const abs = Math.abs(numValue);
    if (abs >= 1_000_000_00) {
      // Crores in Indian numbering
      formattedNumber = `${(abs / 1_00_00_000).toFixed(decimals)} Cr`;
    } else if (abs >= 100_000) {
      // Lakhs
      formattedNumber = `${(abs / 1_00_000).toFixed(decimals)} L`;
    } else if (abs >= 1_000_000) {
      formattedNumber = `${(abs / 1_000_000).toFixed(decimals)}M`;
    } else if (abs >= 1_000) {
      formattedNumber = `${(abs / 1_000).toFixed(decimals)}k`;
    } else {
      formattedNumber = abs.toFixed(decimals);
    }
  } else {
    // Format according to Indian / International grouping
    formattedNumber = Math.abs(numValue).toLocaleString('en-IN', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
  }

  // Determine variant styling
  let colorClass = 'text-slate-100';
  if (variant === 'positive') colorClass = 'text-emerald-400';
  else if (variant === 'negative') colorClass = 'text-rose-400';
  else if (variant === 'muted') colorClass = 'text-slate-400';
  else if (variant === 'auto') {
    if (isPositive) colorClass = 'text-emerald-400';
    else if (isNegative) colorClass = 'text-rose-400';
    else colorClass = 'text-slate-300';
  }

  const signPrefix = showSign ? (isPositive ? '+' : isNegative ? '-' : '') : (isNegative ? '-' : '');

  return (
    <span className={`font-mono tabular-nums tracking-tight inline-flex items-baseline font-semibold ${colorClass} ${className}`}>
      <span className="opacity-75 mr-0.5 text-[0.85em] font-sans">{symbol}</span>
      <span>
        {signPrefix}
        {formattedNumber}
      </span>
    </span>
  );
};
