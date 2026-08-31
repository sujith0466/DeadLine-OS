import React from 'react';
import { useLocation, Link } from 'react-router-dom';
import { Users, ShieldCheck, Settings, Activity } from 'lucide-react';

export const GovernanceSubNav: React.FC = () => {
  const location = useLocation();

  const tabs = [
    {
      label: 'Team & Access',
      href: '/business/team',
      icon: Users,
    },
    {
      label: 'Forensic Audit Trail',
      href: '/business/audit',
      icon: ShieldCheck,
    },
    {
      label: 'System Health & Certification',
      href: '/business/health',
      icon: Activity,
    },
    {
      label: 'Workspace & Global Settings',
      href: '/business/settings',
      icon: Settings,
    },
  ];

  return (
    <nav
      aria-label="Governance sub-navigation"
      className="flex items-center gap-1.5 p-1 bg-slate-900/60 backdrop-blur-md border border-slate-800/80 rounded-xl mb-6 w-fit overflow-x-auto no-scrollbar max-w-full"
    >
      {tabs.map((tab) => {
        const Icon = tab.icon;
        const isActive = location.pathname === tab.href;

        return (
          <Link
            key={tab.href}
            to={tab.href}
            aria-current={isActive ? 'page' : undefined}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/50 flex-shrink-0 ${
              isActive
                ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-600/30 font-semibold'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <Icon className="w-3.5 h-3.5" />
            <span>{tab.label}</span>
          </Link>
        );
      })}
    </nav>
  );
};
