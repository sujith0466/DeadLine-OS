import React, { useState, useEffect, useRef } from 'react';
import { useBusinessAuth } from '../../context/BusinessAuthContext';
import { Building2, ChevronDown, Plus, Check, Shield } from 'lucide-react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';

interface WorkspaceSwitcherProps {
  className?: string;
}

export const WorkspaceSwitcher: React.FC<WorkspaceSwitcherProps> = ({ className = '' }) => {
  const { workspaces, activeWorkspace, selectWorkspace, createWorkspace, role } = useBusinessAuth();
  const shouldReduceMotion = useReducedMotion();

  const [isOpen, setIsOpen] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [newWsName, setNewWsName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  // Close on outside click or Escape
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setIsCreating(false);
      }
    };
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false);
        setIsCreating(false);
        buttonRef.current?.focus();
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    window.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen]);

  const handleSelect = async (id: string) => {
    try {
      await selectWorkspace(id);
      window.dispatchEvent(new CustomEvent('deadline_workspace_changed', { detail: id }));
      setIsOpen(false);
    } catch (err) {
      console.error('Failed to switch workspace:', err);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newWsName.trim()) return;

    setIsLoading(true);
    setCreateError(null);
    try {
      const created = await createWorkspace({ name: newWsName.trim() });
      setNewWsName('');
      setIsCreating(false);
      if (created?.id) {
        await handleSelect(created.id);
      }
    } catch (err: any) {
      setCreateError(err?.response?.data?.error?.message || err?.message || 'Failed to create workspace.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div ref={containerRef} className={`relative inline-block text-left ${className}`}>
      <button
        ref={buttonRef}
        onClick={() => setIsOpen(!isOpen)}
        aria-haspopup="menu"
        aria-expanded={isOpen}
        aria-label="Select active business workspace"
        className="group flex items-center gap-2.5 px-3 py-1.5 rounded-xl bg-slate-900/90 border border-slate-800 hover:border-slate-700 hover:bg-slate-800/80 text-xs font-semibold text-slate-200 transition-all duration-200 shadow-sm outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/50"
      >
        <div className="w-5 h-5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 group-hover:scale-105 transition-transform flex-shrink-0">
          <Building2 className="w-3 h-3" />
        </div>
        <span className="truncate max-w-[130px] sm:max-w-[180px] text-left">
          {activeWorkspace ? activeWorkspace.name : 'Select Workspace'}
        </span>
        <ChevronDown
          className={`w-3.5 h-3.5 text-slate-500 transition-transform duration-200 ${
            isOpen ? 'rotate-180 text-emerald-400' : 'group-hover:text-slate-300'
          }`}
        />
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            role="menu"
            aria-label="Workspaces"
            initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, y: 6, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, y: 4, scale: 0.98 }}
            transition={{ duration: 0.15, ease: 'easeOut' }}
            className="absolute left-0 mt-2 w-64 rounded-2xl bg-[#0B0F19] border border-slate-800 shadow-2xl shadow-black/80 backdrop-blur-2xl z-50 p-2 overflow-hidden"
          >
            {/* Header / Active Role */}
            <div className="flex items-center justify-between px-2.5 py-1.5 text-[11px] text-slate-400 border-b border-slate-800/60 pb-2 mb-1">
              <span className="font-semibold uppercase tracking-wider text-slate-400">Workspaces</span>
              {role && (
                <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-[10px] text-emerald-400 font-bold uppercase">
                  <Shield className="w-2.5 h-2.5" />
                  {role}
                </span>
              )}
            </div>

            {/* Workspace List */}
            <div className="max-h-56 overflow-y-auto space-y-1 py-1 no-scrollbar">
              {workspaces.map(ws => {
                const isActive = ws.id === activeWorkspace?.id;

                return (
                  <button
                    key={ws.id}
                    onClick={() => handleSelect(ws.id)}
                    className={`w-full flex items-center justify-between px-2.5 py-2 rounded-xl text-xs transition-all text-left ${
                      isActive
                        ? 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 font-semibold'
                        : 'text-slate-300 hover:bg-slate-800/60 hover:text-white border border-transparent'
                    }`}
                  >
                    <div className="truncate pr-2">
                      <div className="truncate text-slate-200">{ws.name}</div>
                      <div className="text-[10px] text-slate-500 flex items-center gap-1.5 mt-0.5">
                        <span className="capitalize">{ws.member_role?.toLowerCase() || 'member'}</span>
                        <span>•</span>
                        <span>{ws.base_currency || 'INR'}</span>
                      </div>
                    </div>
                    {isActive && (
                      <div className="w-4 h-4 rounded-full bg-emerald-500/20 flex items-center justify-center text-emerald-400 flex-shrink-0">
                        <Check className="w-2.5 h-2.5" />
                      </div>
                    )}
                  </button>
                );
              })}
            </div>

            {/* Create Workspace Inline */}
            <div className="border-t border-slate-800/80 mt-1 pt-1.5">
              {isCreating ? (
                <form onSubmit={handleCreate} className="p-1 space-y-2">
                  <input
                    type="text"
                    placeholder="Workspace Name..."
                    value={newWsName}
                    onChange={e => setNewWsName(e.target.value)}
                    className="w-full px-2.5 py-1.5 text-xs rounded-xl bg-slate-900 border border-slate-700 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-colors"
                    autoFocus
                  />
                  {createError && (
                    <p className="text-[10px] text-rose-400 px-1">{createError}</p>
                  )}
                  <div className="flex gap-1.5">
                    <button
                      type="submit"
                      disabled={isLoading || !newWsName.trim()}
                      className="flex-1 px-2.5 py-1.5 text-xs bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-slate-950 font-bold rounded-lg transition-colors shadow-sm"
                    >
                      {isLoading ? 'Creating...' : 'Create'}
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setIsCreating(false);
                        setCreateError(null);
                      }}
                      className="px-2.5 py-1.5 text-xs text-slate-400 hover:text-slate-200 bg-slate-800 rounded-lg"
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              ) : (
                <button
                  onClick={() => setIsCreating(true)}
                  className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-xl text-xs text-slate-400 hover:text-emerald-300 hover:bg-emerald-500/10 transition-colors font-medium"
                >
                  <Plus className="w-3.5 h-3.5 text-emerald-400" />
                  <span>New Workspace</span>
                </button>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
