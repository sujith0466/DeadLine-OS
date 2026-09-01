import React from 'react';
import { useLocation, Link } from 'react-router-dom';
import { motion, useReducedMotion } from 'framer-motion';
import {
  LayoutDashboard,
  LineChart,
  Receipt,
  Layers,
  Network,
  ShieldCheck,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

export interface DomainItem {
  id: string;
  label: string;
  href: string;
  icon: LucideIcon;
  subRoutes: string[];
}

export const BUSINESS_DOMAINS: DomainItem[] = [
  {
    id: 'command',
    label: 'Command',
    href: '/business/dashboard',
    icon: LayoutDashboard,
    subRoutes: ['/business/dashboard'],
  },
  {
    id: 'intelligence',
    label: 'Intelligence',
    href: '/business/intelligence',
    icon: LineChart,
    subRoutes: ['/business/intelligence'],
  },
  {
    id: 'financials',
    label: 'Financials',
    href: '/business/invoices',
    icon: Receipt,
    subRoutes: [
      '/business/invoices',
      '/business/transactions',
      '/business/partners',
    ],
  },
  {
    id: 'operations',
    label: 'Operations',
    href: '/business/tasks',
    icon: Layers,
    subRoutes: [
      '/business/tasks',
      '/business/inventory',
      '/business/staging',
      '/business/rescue',
      '/business/recurring',
    ],
  },
  {
    id: 'entities',
    label: 'Entities',
    href: '/business/entities',
    icon: Network,
    subRoutes: [
      '/business/entities',
      '/business/consolidation',
    ],
  },
  {
    id: 'governance',
    label: 'Governance',
    href: '/business/team',
    icon: ShieldCheck,
    subRoutes: [
      '/business/team',
      '/business/audit',
      '/business/settings',
    ],
  },
];

interface BusinessDomainNavProps {
  className?: string;
}

export const BusinessDomainNav: React.FC<BusinessDomainNavProps> = ({ className = '' }) => {
  const location = useLocation();
  const shouldReduceMotion = useReducedMotion();

  // Determine active domain based on current pathname
  const activeDomain =
    BUSINESS_DOMAINS.find(domain =>
      domain.subRoutes.some(route => location.pathname.startsWith(route))
    ) || BUSINESS_DOMAINS[0];

  return (
    <nav
      aria-label="Business Domains"
      className={`flex items-center gap-1 p-1 rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-md overflow-x-auto no-scrollbar max-w-full ${className}`}
    >
      {BUSINESS_DOMAINS.map(domain => {
        const isActive = activeDomain.id === domain.id;
        const Icon = domain.icon;

        return (
          <Link
            key={domain.id}
            to={domain.href}
            className={`relative flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-colors duration-200 flex-shrink-0 outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/50 ${
              isActive
                ? 'text-emerald-300 font-bold'
                : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.03]'
            }`}
          >
            {/* Active Highlight Pill (Framer Motion) */}
            {isActive && (
              <motion.div
                layoutId={shouldReduceMotion ? undefined : 'activeDomainPill'}
                transition={{ type: 'spring', stiffness: 450, damping: 35 }}
                className="absolute inset-0 rounded-xl bg-emerald-500/15 border border-emerald-500/30 shadow-sm shadow-emerald-500/10 pointer-events-none"
              />
            )}

            <Icon
              className={`w-3.5 h-3.5 transition-colors relative z-10 ${
                isActive ? 'text-emerald-400' : 'text-slate-500'
              }`}
            />
            <span className="relative z-10 tracking-wide">{domain.label}</span>
          </Link>
        );
      })}
    </nav>
  );
};
