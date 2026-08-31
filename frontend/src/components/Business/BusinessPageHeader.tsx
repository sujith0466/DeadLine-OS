import React from 'react';
import { Link } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { StatusBadge } from './StatusBadge';
import type { BusinessStatusType } from './StatusBadge';

export interface BreadcrumbItem {
  label: string;
  href?: string;
  icon?: LucideIcon;
}

export interface HeaderAction {
  label: string;
  onClick?: () => void;
  href?: string;
  icon?: LucideIcon;
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  disabled?: boolean;
  loading?: boolean;
}

export interface BusinessPageHeaderProps {
  title: string;
  description?: string;
  breadcrumbs?: BreadcrumbItem[];
  status?: BusinessStatusType;
  primaryAction?: HeaderAction;
  secondaryActions?: HeaderAction[];
  children?: React.ReactNode;
  className?: string;
}

export const BusinessPageHeader: React.FC<BusinessPageHeaderProps> = ({
  title,
  description,
  breadcrumbs = [],
  status,
  primaryAction,
  secondaryActions = [],
  children,
  className = '',
}) => {
  return (
    <div className={`mb-6 space-y-3 ${className}`}>
      {/* Breadcrumbs */}
      {breadcrumbs.length > 0 && (
        <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-xs text-slate-400">
          <Link
            to="/business/dashboard"
            className="hover:text-slate-200 transition-colors font-medium"
          >
            Business OS
          </Link>
          {breadcrumbs.map((crumb, idx) => {
            const isLast = idx === breadcrumbs.length - 1;
            const Icon = crumb.icon;

            return (
              <React.Fragment key={idx}>
                <ChevronRight className="w-3.5 h-3.5 text-slate-600 flex-shrink-0" />
                {crumb.href && !isLast ? (
                  <Link
                    to={crumb.href}
                    className="hover:text-slate-200 transition-colors flex items-center gap-1"
                  >
                    {Icon && <Icon className="w-3.5 h-3.5" />}
                    <span>{crumb.label}</span>
                  </Link>
                ) : (
                  <span
                    className={`flex items-center gap-1 ${
                      isLast ? 'text-slate-200 font-semibold' : 'text-slate-400'
                    }`}
                    aria-current={isLast ? 'page' : undefined}
                  >
                    {Icon && <Icon className="w-3.5 h-3.5" />}
                    <span>{crumb.label}</span>
                  </span>
                )}
              </React.Fragment>
            );
          })}
        </nav>
      )}

      {/* Main Title & Action Row */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-50 font-sans">
              {title}
            </h1>
            {status && <StatusBadge status={status} size="md" />}
          </div>
          {description && (
            <p className="text-sm text-slate-400 mt-1 max-w-3xl leading-relaxed">
              {description}
            </p>
          )}
        </div>

        {/* Action Buttons */}
        {(primaryAction || secondaryActions.length > 0) && (
          <div className="flex items-center flex-wrap gap-2.5 flex-shrink-0">
            {secondaryActions.map((action, idx) => {
              const ActionIcon = action.icon;
              const content = (
                <>
                  {ActionIcon && <ActionIcon className="w-4 h-4 text-slate-400 group-hover:text-white transition-colors" />}
                  <span>{action.label}</span>
                </>
              );

              const buttonClasses = `inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold border transition-all duration-200 shadow-sm disabled:opacity-50 disabled:cursor-not-allowed group outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/50 ${
                action.variant === 'danger'
                  ? 'bg-rose-500/10 border-rose-500/30 text-rose-400 hover:bg-rose-500/20 hover:border-rose-500/40'
                  : action.variant === 'ghost'
                  ? 'bg-transparent border-transparent text-slate-300 hover:bg-slate-800/80 hover:text-white'
                  : 'bg-slate-900/90 border-slate-800 text-slate-300 hover:bg-slate-800 hover:text-white hover:border-slate-700'
              }`;

              if (action.href) {
                return (
                  <Link key={idx} to={action.href} className={buttonClasses}>
                    {content}
                  </Link>
                );
              }

              return (
                <button
                  key={idx}
                  onClick={action.onClick}
                  disabled={action.disabled || action.loading}
                  className={buttonClasses}
                >
                  {content}
                </button>
              );
            })}

            {primaryAction && (
              (() => {
                const PrimaryIcon = primaryAction.icon;
                const content = (
                  <>
                    {PrimaryIcon && <PrimaryIcon className="w-4 h-4" />}
                    <span>{primaryAction.label}</span>
                  </>
                );

                const primaryClasses =
                  'inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-emerald-500 hover:bg-emerald-400 text-slate-950 shadow-lg shadow-emerald-500/20 hover:shadow-emerald-500/30 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed active:scale-[0.98] outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950';

                if (primaryAction.href) {
                  return (
                    <Link to={primaryAction.href} className={primaryClasses}>
                      {content}
                    </Link>
                  );
                }

                return (
                  <button
                    onClick={primaryAction.onClick}
                    disabled={primaryAction.disabled || primaryAction.loading}
                    className={primaryClasses}
                  >
                    {content}
                  </button>
                );
              })()
            )}
          </div>
        )}
      </div>

      {children}
    </div>
  );
};
