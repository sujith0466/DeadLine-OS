import React, { useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Sparkles,
  FileDown,
  LogOut,
  User,
  Shield,
  ExternalLink,
  ChevronDown,
  Layers,
} from 'lucide-react';
import { WorkspaceSwitcher } from './WorkspaceSwitcher';
import { BusinessDomainNav } from './BusinessDomainNav';
import { useAuth } from '../../context/AuthContext';
import { useBusinessAuth } from '../../context/BusinessAuthContext';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';

interface BusinessHeaderProps {
  onOpenCopilot?: () => void;
  onOpenExport?: () => void;
  className?: string;
}

export const BusinessHeader: React.FC<BusinessHeaderProps> = ({
  onOpenCopilot,
  onOpenExport,
  className = '',
}) => {
  const navigate = useNavigate();
  const shouldReduceMotion = useReducedMotion();
  const { user, signOut } = useAuth();
  const { role, activeWorkspace } = useBusinessAuth();

  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const profileRef = useRef<HTMLDivElement>(null);
  const profileButtonRef = useRef<HTMLButtonElement>(null);

  // Close profile on click outside or Escape
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) {
        setIsProfileOpen(false);
      }
    };
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isProfileOpen) {
        setIsProfileOpen(false);
        profileButtonRef.current?.focus();
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    window.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isProfileOpen]);

  const handleLogout = async () => {
    try {
      localStorage.setItem('deadlineos-landing-mode', 'business');
      await signOut();
      navigate('/?mode=business');
    } catch (err) {
      console.error('Logout error:', err);
      navigate('/?mode=business');
    }
  };

  return (
    <header
      className={`sticky top-0 z-40 w-full bg-[#030712]/90 backdrop-blur-xl border-b border-slate-800/80 ${className}`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 gap-3">
          {/* Left: Brand + Workspace Switcher + LIVE Pill */}
          <div className="flex items-center gap-3 flex-shrink-0">
            <Link
              to="/business/dashboard"
              className="flex items-center gap-2 outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/50 rounded-lg p-1 -m-1"
            >
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center text-slate-950 font-black shadow-md shadow-emerald-500/20">
                <Layers className="w-4 h-4" />
              </div>
              <div className="hidden sm:flex flex-col">
                <span className="text-xs font-black tracking-tight text-white flex items-center gap-1">
                  DEADLINE<span className="text-emerald-400">OS</span>
                </span>
                <span className="text-[9px] uppercase tracking-widest text-slate-500 font-bold -mt-0.5">
                  Business OS
                </span>
              </div>
            </Link>

            <div className="h-5 w-px bg-slate-800 hidden sm:block" />

            <WorkspaceSwitcher />

            <div className="hidden md:inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-[10px] font-bold text-emerald-400">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>LIVE</span>
            </div>
          </div>

          {/* Center: Domain Navigation */}
          <div className="hidden lg:flex items-center justify-center flex-1 max-w-xl px-2">
            <BusinessDomainNav />
          </div>

          {/* Right: Quick Actions + Copilot + Profile */}
          <div className="flex items-center gap-2 flex-shrink-0">
            {/* AI Copilot Trigger */}
            {onOpenCopilot && (
              <button
                onClick={onOpenCopilot}
                title="Ask Business AI Copilot (Ctrl+K)"
                aria-label="Ask Business AI Copilot (Shortcut: Control + K)"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 hover:bg-emerald-500/20 text-xs font-bold text-emerald-300 transition-colors shadow-sm shadow-emerald-500/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/50"
              >
                <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
                <span className="hidden sm:inline">Copilot</span>
                <kbd className="hidden md:inline-block px-1 py-0.2 rounded bg-emerald-500/20 text-[9px] font-mono text-emerald-300 ml-0.5">
                  ⌘K
                </kbd>
              </button>
            )}

            {/* Accountant Export Trigger */}
            {onOpenExport && (
              <button
                onClick={onOpenExport}
                title="Accountant Audit Package & Export"
                aria-label="Generate Accountant Audit Package & Financial Export"
                className="p-2 rounded-xl bg-slate-900/90 border border-slate-800 hover:border-slate-700 hover:bg-slate-800 text-slate-300 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/50"
              >
                <FileDown className="w-4 h-4 text-slate-400" />
              </button>
            )}

            {/* Profile / Account Dropdown */}
            <div ref={profileRef} className="relative">
              <button
                ref={profileButtonRef}
                onClick={() => setIsProfileOpen(!isProfileOpen)}
                aria-haspopup="menu"
                aria-expanded={isProfileOpen}
                aria-label="User profile and account settings menu"
                className="flex items-center gap-1.5 p-1.5 rounded-xl bg-slate-900/90 border border-slate-800 hover:border-slate-700 text-slate-300 transition-colors outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/50"
              >
                <div className="w-6 h-6 rounded-lg bg-slate-800 flex items-center justify-center text-xs font-bold text-slate-300">
                  {user?.email ? user.email.charAt(0).toUpperCase() : <User className="w-3.5 h-3.5" />}
                </div>
                <ChevronDown className="w-3 h-3 text-slate-500" />
              </button>

              <AnimatePresence>
                {isProfileOpen && (
                  <motion.div
                    role="menu"
                    aria-label="User Account Menu"
                    initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, y: 6, scale: 0.98 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, y: 4, scale: 0.98 }}
                    transition={{ duration: 0.15, ease: 'easeOut' }}
                    className="absolute right-0 mt-2 w-64 rounded-2xl bg-[#0B0F19] border border-slate-800 shadow-2xl shadow-black/80 backdrop-blur-2xl z-50 p-2 overflow-hidden"
                  >
                    {/* User Identity Info */}
                    <div className="px-3 py-2 border-b border-slate-800/80 mb-1">
                      <div className="text-xs font-bold text-slate-200 truncate">
                        {user?.email || 'Business User'}
                      </div>
                      <div className="flex items-center gap-1.5 text-[10px] text-slate-500 mt-0.5">
                        <Shield className="w-3 h-3 text-emerald-400" />
                        <span className="capitalize">{role || 'Owner'}</span>
                        <span>•</span>
                        <span>{activeWorkspace?.name || 'Workspace'}</span>
                      </div>
                    </div>

                    {/* Switch to Personal OS Link */}
                    <Link
                      to="/dashboard"
                      onClick={() => setIsProfileOpen(false)}
                      className="flex items-center justify-between px-3 py-2 rounded-xl text-xs text-slate-300 hover:text-white hover:bg-slate-800/60 transition-colors"
                    >
                      <div className="flex items-center gap-2">
                        <ExternalLink className="w-3.5 h-3.5 text-slate-400" />
                        <span>Switch to Personal OS</span>
                      </div>
                      <span className="text-[10px] text-slate-500">Personal</span>
                    </Link>

                    {/* Workspace Selector */}
                    <Link
                      to="/business/select"
                      onClick={() => setIsProfileOpen(false)}
                      className="flex items-center justify-between px-3 py-2 rounded-xl text-xs text-slate-300 hover:text-white hover:bg-slate-800/60 transition-colors"
                    >
                      <span>Switch Business Workspace</span>
                    </Link>

                    {/* Sign Out */}
                    <div className="border-t border-slate-800/80 mt-1 pt-1">
                      <button
                        onClick={handleLogout}
                        className="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-xs text-rose-400 hover:bg-rose-500/10 transition-colors font-medium text-left"
                      >
                        <LogOut className="w-3.5 h-3.5" />
                        <span>Sign Out of Business OS</span>
                      </button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>

        {/* Mobile Domain Nav Bar (visible only on small viewports) */}
        <div className="lg:hidden py-2 border-t border-slate-800/60 overflow-x-auto no-scrollbar">
          <BusinessDomainNav />
        </div>
      </div>
    </header>
  );
};
