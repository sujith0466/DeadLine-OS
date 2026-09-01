import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { CheckSquare, Package, Inbox, ShieldAlert, RefreshCw } from 'lucide-react';

export const OperationsSubNav: React.FC = () => {
  const location = useLocation();

  const navItems = [
    {
      id: 'tasks',
      label: 'Tasks & Allocation',
      href: '/business/tasks',
      icon: CheckSquare,
    },
    {
      id: 'inventory',
      label: 'Inventory & Stock',
      href: '/business/inventory',
      icon: Package,
    },
    {
      id: 'staging',
      label: 'Staging Review Queue',
      href: '/business/staging',
      icon: Inbox,
    },
    {
      id: 'rescue',
      label: 'Receivable Rescue & Aging',
      href: '/business/rescue',
      icon: ShieldAlert,
    },
    {
      id: 'recurring',
      label: 'Recurring & Automations',
      href: '/business/recurring',
      icon: RefreshCw,
    },
  ];

  return (
    <nav
      aria-label="Operations sub-navigation"
      className="flex items-center gap-2 p-1 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-md overflow-x-auto no-scrollbar max-w-fit mb-6"
    >
      {navItems.map((item) => {
        const isActive = location.pathname === item.href;
        const Icon = item.icon;

        return (
          <Link
            key={item.id}
            to={item.href}
            aria-current={isActive ? 'page' : undefined}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold transition-all duration-200 cursor-pointer outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/50 flex-shrink-0 ${
              isActive
                ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]'
            }`}
          >
            <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-emerald-400' : 'text-slate-500'}`} />
            <span>{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
};
