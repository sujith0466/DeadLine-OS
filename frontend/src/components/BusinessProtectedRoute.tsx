import React from 'react';
import { Navigate, Outlet, useLocation, Link } from 'react-router-dom';
import { Building2, ShieldAlert, ArrowRight, RefreshCw } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useBusinessAuth } from '../context/BusinessAuthContext';

interface BusinessProtectedRouteProps {
  requiredPermission?: string;
  children?: React.ReactNode;
}

export const BusinessProtectedRoute: React.FC<BusinessProtectedRouteProps> = ({
  requiredPermission,
  children,
}) => {
  const location = useLocation();
  const { user, loading: authLoading } = useAuth();
  const {
    workspaces,
    activeWorkspace,
    loading: bizLoading,
    hasPermission,
    isSuspended,
    refreshWorkspaces,
  } = useBusinessAuth();

  // STATE 1: Auth & Business Context Hydrating (Prevent premature redirect & flash)
  if ((authLoading || bizLoading) && !activeWorkspace) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-[#020617] text-slate-300">
        <div className="flex flex-col items-center gap-4">
          <div className="relative">
            <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <Building2 className="w-6 h-6 animate-pulse" />
            </div>
            <div className="absolute -inset-1 rounded-2xl bg-emerald-500/20 blur-md -z-10 animate-pulse" />
          </div>
          <div className="text-center">
            <p className="text-sm font-bold text-white tracking-wide">Authorizing Workspace Context...</p>
            <p className="text-xs text-slate-500 mt-1">Verifying cryptographic tenant membership</p>
          </div>
        </div>
      </div>
    );
  }

  // STATE 2: Not Authenticated with Supabase Identity -> Route to Business Login
  if (!user) {
    return <Navigate to="/business/login" state={{ from: location }} replace />;
  }

  // STATE 3: Authenticated but has 0 Business Workspaces -> Route to Business Register/Onboarding
  if (workspaces.length === 0) {
    return <Navigate to="/business/register" replace />;
  }

  // STATE 4: Suspended Membership in Active Workspace
  if (isSuspended || (activeWorkspace && (activeWorkspace.status === 'SUSPENDED' || activeWorkspace.member_status === 'SUSPENDED'))) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-[#020617] p-4 selection:bg-rose-500/30">
        <div className="bg-slate-900/80 backdrop-blur-xl border border-rose-500/30 rounded-2xl p-8 max-w-md w-full text-center shadow-2xl">
          <div className="w-14 h-14 rounded-2xl bg-rose-500/10 text-rose-400 flex items-center justify-center mx-auto mb-4 border border-rose-500/20">
            <ShieldAlert className="w-7 h-7" />
          </div>
          <h2 className="text-xl font-bold text-white mb-2">Workspace Access Suspended</h2>
          <p className="text-sm text-slate-400 mb-6 leading-relaxed">
            Your membership in <strong className="text-white">{activeWorkspace?.name || 'this workspace'}</strong> is currently suspended. Please contact your workspace administrator.
          </p>
          <div className="flex flex-col gap-3">
            <Link
              to="/business/select"
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-sm font-semibold transition-colors"
            >
              <span>Switch Workspace</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
            <button
              onClick={() => refreshWorkspaces()}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 text-xs text-slate-500 hover:text-slate-300 transition-colors cursor-pointer"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Retry Verification</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  // STATE 5: Authenticated but No Workspace Selected -> Route to Workspace Selector
  if (!activeWorkspace) {
    return <Navigate to="/business/select" replace />;
  }

  // STATE 6: Specific Fine-Grained Permission Required but Missing
  if (requiredPermission && !hasPermission(requiredPermission)) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-[#020617] p-4">
        <div className="bg-slate-900/80 backdrop-blur-xl border border-amber-500/30 rounded-2xl p-8 max-w-md w-full text-center shadow-2xl">
          <div className="w-14 h-14 rounded-2xl bg-amber-500/10 text-amber-400 flex items-center justify-center mx-auto mb-4 border border-amber-500/20">
            <ShieldAlert className="w-7 h-7" />
          </div>
          <h2 className="text-xl font-bold text-white mb-2">Insufficient Permissions</h2>
          <p className="text-sm text-slate-400 mb-6 leading-relaxed">
            Your assigned role in <strong className="text-white">{activeWorkspace.name}</strong> does not have the required <code className="text-amber-400 bg-amber-500/10 px-1.5 py-0.5 rounded text-xs">{requiredPermission}</code> privilege.
          </p>
          <Link
            to="/business/select"
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-sm font-semibold transition-colors"
          >
            <span>Return to Workspace Selection</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    );
  }

  // STATE 7: Fully Authorized -> Render Protected Business Children / Outlet
  return children ? <>{children}</> : <Outlet />;
};
