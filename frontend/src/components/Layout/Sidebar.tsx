import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, CalendarClock, LifeBuoy, Zap, Camera, Settings, Network, BarChart3, Calendar as CalendarIcon, AlertOctagon, Target, FileText, Mic } from 'lucide-react';

export const Sidebar: React.FC = () => {
  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'AI Command Center', path: '/command-center', icon: Network },
    { name: 'AI Planner', path: '/planner', icon: CalendarClock },
    { name: 'Rescue Center', path: '/rescue', icon: LifeBuoy },
    { name: 'Goals & Habits', path: '/goals', icon: Target },
    { name: 'Digital Twin', path: '/digital-twin', icon: Zap },
    { name: 'Document Intel', path: '/documents', icon: FileText },
    { name: 'Voice Copilot', path: '/voice', icon: Mic },
    { name: 'Vision Upload', path: '/vision', icon: Camera },
    { name: 'Interventions', path: '/interventions', icon: AlertOctagon },
    { name: 'Smart Calendar', path: '/calendar', icon: CalendarIcon },
    { name: 'Analytics', path: '/analytics', icon: BarChart3 },
  ];

  return (
    <div className="w-64 h-screen fixed left-0 top-0 border-r border-white/10 bg-background/50 backdrop-blur-xl flex flex-col pt-6 pb-6 z-20">
      <div className="px-6 mb-10 flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-primary to-secondary flex items-center justify-center">
          <Zap className="w-5 h-5 text-white" />
        </div>
        <span className="text-xl font-bold tracking-tight text-white">Deadline<span className="text-primary">OS</span></span>
      </div>

      <div className="flex-1 px-4 space-y-2">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                isActive 
                  ? 'bg-white/10 text-white shadow-inner border border-white/5' 
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`
            }
          >
            <item.icon className="w-5 h-5" />
            <span className="font-medium">{item.name}</span>
          </NavLink>
        ))}
      </div>

      <div className="px-4 mt-auto">
        <button className="flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 text-gray-400 hover:text-white hover:bg-white/5 w-full">
          <Settings className="w-5 h-5" />
          <span className="font-medium">Settings</span>
        </button>
      </div>
    </div>
  );
};
