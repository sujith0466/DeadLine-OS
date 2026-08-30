import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import { Building2, ArrowRight, ShieldCheck, Plus, CheckCircle2, AlertTriangle, LogOut } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useBusinessAuth, type BusinessWorkspace, type BusinessRole } from '../../context/BusinessAuthContext';

export const WorkspaceSelector: React.FC = () => {
  const navigate = useNavigate();
  const shouldReduceMotion = useReducedMotion();
  const { user, signOut, loading: authLoading } = useAuth();
  const {
    workspaces,
    activeWorkspace,
    selectWorkspace,
    loading: bizLoading,
    error,
  } = useBusinessAuth();

  const [selectingId, setSelectingId] = useState<string | null>(null);
  const [selectionError, setSelectionError] = useState<string | null>(null);

  const handleSelect = async (ws: BusinessWorkspace) => {
    if (ws.status !== 'ACTIVE' || ws.member_status !== 'ACTIVE') {
      setSelectionError(`Access denied: Membership in "${ws.name}" is ${ws.member_status || ws.status}.`);
      return;
    }

    try {
      setSelectionError(null);
      setSelectingId(ws.id);
      await selectWorkspace(ws.id);
      navigate('/business/dashboard');
    } catch (err: any) {
      setSelectionError(err?.message || 'Failed to select workspace.');
      setSelectingId(null);
    }
  };

  const getRoleBadge = (role?: BusinessRole) => {
    switch (role) {
      case 'OWNER':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      case 'ADMIN':
        return 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20';
      case 'MEMBER':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
      case 'ACCOUNTANT':
        return 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20';
      case 'VIEWER':
      default:
        return 'bg-slate-500/10 text-slate-400 border-slate-500/20';
    }
  };

  const isLoading = authLoading || bizLoading;

  return (
    <div className="min-h-screen bg-[#020617] flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden selection:bg-emerald-500/30">
      {/* Background Glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[500px] bg-emerald-500/10 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute bottom-10 right-1/4 w-[400px] h-[400px] bg-teal-500/5 rounded-full blur-[120px] pointer-events-none" />

      {/* Grid Pattern */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b08_1px,transparent_1px),linear-gradient(to_bottom,#1e293b08_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_40%,#000_70%,transparent_100%)] pointer-events-none" />

      {/* Header Container */}
      <div className="max-w-2xl mx-auto w-full relative z-10 mb-8">
        <motion.div
          initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, y: -16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35 }}
          className="flex items-center justify-between gap-4 mb-4"
        >
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold tracking-wider uppercase backdrop-blur-md">
            <Building2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>Business OS • Workspace Gateway</span>
          </div>

          {user && (
            <div className="flex items-center gap-3">
              <span className="text-xs text-slate-400 hidden sm:inline">{user.email}</span>
              <button
                onClick={() => signOut()}
                className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white px-2.5 py-1.5 rounded-lg hover:bg-slate-800/60 transition-colors cursor-pointer"
                title="Sign Out"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Sign Out</span>
              </button>
            </div>
          )}
        </motion.div>

        <motion.div
          initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, delay: 0.05 }}
        >
          <h1 className="text-3xl sm:text-4xl font-black text-white tracking-tight">
            Select Organization
          </h1>
          <p className="mt-2 text-sm text-slate-400">
            Choose the business entity context you wish to operate in
          </p>
        </motion.div>
      </div>

      {/* Main Workspace Card Container */}
      <motion.div
        initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.1 }}
        className="max-w-2xl mx-auto w-full relative z-10"
      >
        {/* Error Banners */}
        <AnimatePresence mode="wait">
          {(error || selectionError) && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mb-6 rounded-xl bg-rose-500/10 border border-rose-500/20 p-4 flex items-start gap-3 text-rose-400 text-sm overflow-hidden"
              role="alert"
            >
              <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5 text-rose-400" />
              <div>
                <p className="font-semibold">Workspace Access Notice</p>
                <p className="mt-0.5 leading-relaxed">{selectionError || error}</p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* STATE 1: Loading Skeleton */}
        {isLoading && (
          <div className="space-y-4">
            {[1, 2].map((i) => (
              <div
                key={i}
                className="bg-slate-900/50 border border-slate-800/80 rounded-2xl p-6 animate-pulse"
              >
                <div className="flex items-center justify-between">
                  <div className="space-y-2">
                    <div className="h-5 w-48 bg-slate-800 rounded" />
                    <div className="h-4 w-32 bg-slate-800/60 rounded" />
                  </div>
                  <div className="h-8 w-24 bg-slate-800 rounded-full" />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* STATE 2: Zero Workspaces */}
        {!isLoading && workspaces.length === 0 && (
          <div className="bg-slate-900/60 backdrop-blur-xl border border-slate-800/80 rounded-2xl p-8 sm:p-10 text-center shadow-2xl">
            <div className="w-14 h-14 rounded-2xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center mx-auto mb-4 border border-emerald-500/20">
              <Building2 className="w-7 h-7" />
            </div>
            <h2 className="text-xl font-bold text-white mb-2">No Business Workspaces Found</h2>
            <p className="text-sm text-slate-400 max-w-md mx-auto mb-8 leading-relaxed">
              Your account is authenticated, but you are not yet a member of any commercial workspace. Create an organization to launch Business OS.
            </p>
            <Link
              to="/business/register"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-emerald-400 hover:bg-emerald-300 text-slate-950 font-bold text-sm shadow-lg shadow-emerald-500/20 transition-all hover:scale-105 cursor-pointer"
            >
              <Plus className="w-4 h-4" />
              <span>Create New Workspace</span>
            </Link>
          </div>
        )}

        {/* STATE 3 & 4: 1 or Multiple Workspaces */}
        {!isLoading && workspaces.length > 0 && (
          <div className="space-y-4">
            <div className="space-y-3">
              {workspaces.map((ws) => {
                const isSelected = activeWorkspace?.id === ws.id;
                const isSuspended = ws.status === 'SUSPENDED' || ws.member_status === 'SUSPENDED';
                const isSelectingThis = selectingId === ws.id;

                return (
                  <motion.button
                    key={ws.id}
                    onClick={() => !isSuspended && !isSelectingThis && handleSelect(ws)}
                    disabled={isSuspended || isSelectingThis}
                    whileHover={isSuspended || shouldReduceMotion ? {} : { scale: 1.01 }}
                    whileTap={isSuspended || shouldReduceMotion ? {} : { scale: 0.99 }}
                    className={`w-full text-left p-6 rounded-2xl border transition-all relative overflow-hidden cursor-pointer ${
                      isSuspended
                        ? 'bg-slate-950/40 border-slate-800/40 opacity-60 cursor-not-allowed'
                        : isSelected
                        ? 'bg-slate-900/90 border-emerald-500/60 shadow-xl shadow-emerald-500/5 ring-1 ring-emerald-500/30'
                        : 'bg-slate-900/60 hover:bg-slate-900/80 border-slate-800/80 hover:border-slate-700'
                    }`}
                  >
                    {/* Active Accent Bar */}
                    {isSelected && (
                      <div className="absolute top-0 left-0 bottom-0 w-1.5 bg-gradient-to-b from-emerald-400 to-teal-500" />
                    )}

                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                      {/* Left: Metadata */}
                      <div className="space-y-1.5">
                        <div className="flex items-center gap-2.5 flex-wrap">
                          <h3 className="text-lg font-bold text-white tracking-tight">
                            {ws.name}
                          </h3>
                          {isSelected && (
                            <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-md border border-emerald-500/20">
                              <CheckCircle2 className="w-3 h-3" /> Active Context
                            </span>
                          )}
                          {isSuspended && (
                            <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded-md border border-rose-500/20">
                              <AlertTriangle className="w-3 h-3" /> Suspended
                            </span>
                          )}
                        </div>

                        {ws.legal_name && (
                          <p className="text-xs text-slate-400 font-medium">{ws.legal_name}</p>
                        )}

                        <div className="flex items-center gap-3 text-xs text-slate-500 pt-1">
                          <span>Currency: <strong className="text-slate-300">{ws.base_currency}</strong></span>
                          <span>•</span>
                          <span>Timezone: <strong className="text-slate-300">{ws.timezone}</strong></span>
                        </div>
                      </div>

                      {/* Right: Role & CTA */}
                      <div className="flex items-center gap-3 shrink-0 self-end sm:self-center">
                        <div className={`px-3 py-1 rounded-full border text-xs font-bold uppercase tracking-wider ${getRoleBadge(ws.member_role)}`}>
                          {ws.member_role || 'MEMBER'}
                        </div>

                        <div className={`w-9 h-9 rounded-xl flex items-center justify-center transition-colors ${
                          isSelected
                            ? 'bg-emerald-400 text-slate-950 shadow-md shadow-emerald-500/20'
                            : 'bg-slate-800 text-slate-300 group-hover:bg-slate-700'
                        }`}>
                          {isSelectingThis ? (
                            <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                          ) : (
                            <ArrowRight className="w-4 h-4" />
                          )}
                        </div>
                      </div>
                    </div>
                  </motion.button>
                );
              })}
            </div>

            {/* Bottom Actions Container */}
            <div className="pt-6 flex flex-col sm:flex-row items-center justify-between gap-4 border-t border-slate-800/80">
              <Link
                to="/business/register"
                className="inline-flex items-center gap-2 text-xs font-semibold text-emerald-400 hover:text-emerald-300 transition-colors"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Create another workspace</span>
              </Link>

              <Link
                to="/dashboard"
                className="text-xs text-slate-500 hover:text-slate-300 transition-colors"
              >
                Switch to Personal OS
              </Link>
            </div>
          </div>
        )}

        {/* Security & Multi-Tenancy Guarantee */}
        <div className="mt-8 flex items-center justify-center gap-2 text-xs text-slate-500">
          <ShieldCheck className="w-4 h-4 text-emerald-500/70" />
          <span>Multi-tenant tenant isolation • Cryptographically verified identity</span>
        </div>
      </motion.div>
    </div>
  );
};
