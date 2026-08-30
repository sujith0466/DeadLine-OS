import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { motion, useReducedMotion } from 'framer-motion';
import { Building2, ShieldCheck, ArrowRight, AlertTriangle, CheckCircle2, UserCheck, Mail, Clock, RefreshCw } from 'lucide-react';
import { api } from '../../api';
import { useAuth } from '../../context/AuthContext';
import { useBusinessAuth, type BusinessRole } from '../../context/BusinessAuthContext';

interface InvitationInfo {
  id: string;
  workspace_id: string;
  workspace_name: string;
  email: string;
  role: BusinessRole;
  status: 'PENDING' | 'ACCEPTED' | 'EXPIRED' | 'REVOKED';
  expires_at?: string | null;
}

export const BusinessInvitationAccept: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const shouldReduceMotion = useReducedMotion();
  const { user } = useAuth();
  const { refreshWorkspaces, selectWorkspace } = useBusinessAuth();

  const token = searchParams.get('token')?.trim() || '';

  const [loading, setLoading] = useState<boolean>(true);
  const [invitation, setInvitation] = useState<InvitationInfo | null>(null);
  const [statusError, setStatusError] = useState<string | null>(null);
  const [accepting, setAccepting] = useState<boolean>(false);
  const [acceptedSuccess, setAcceptedSuccess] = useState<boolean>(false);

  // Validate Invitation Token
  const validateToken = useCallback(async () => {
    if (!token) {
      setLoading(false);
      setStatusError('No invitation token provided. Please check the link from your email.');
      return;
    }

    try {
      setLoading(true);
      setStatusError(null);
      const res = await api.getWorkspaceInvitationInfo(token);
      if (res && res.data) {
        setInvitation(res.data);
      }
    } catch (err: any) {
      const code = err?.response?.data?.error?.code;
      const msg = err?.response?.data?.error?.message;

      if (code === 'INVITATION_NOT_FOUND' || err?.response?.status === 404) {
        setStatusError('Invitation not found or invalid.');
      } else if (code === 'INVITATION_EXPIRED') {
        setStatusError('This invitation has expired. Please ask the administrator for a new invitation.');
      } else if (code === 'INVITATION_REVOKED') {
        setStatusError('This invitation was revoked by the workspace administrator.');
      } else if (code === 'INVITATION_ALREADY_ACCEPTED') {
        setStatusError('This invitation has already been accepted.');
      } else {
        setStatusError(msg || 'Failed to load invitation details. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    validateToken();
  }, [validateToken]);

  // Handle Invitation Acceptance
  const handleAccept = async () => {
    if (!token || accepting || !user) return;

    try {
      setAccepting(true);
      setStatusError(null);

      const res = await api.acceptWorkspaceInvitation(token);
      const targetWorkspaceId = res?.data?.workspace_id || invitation?.workspace_id;

      setAcceptedSuccess(true);
      await refreshWorkspaces();

      if (targetWorkspaceId) {
        try {
          await selectWorkspace(targetWorkspaceId);
        } catch {
          // If auto-select fails, fallback to dashboard
        }
      }

      // Brief pause for UX success visual feedback
      setTimeout(() => {
        navigate('/business/dashboard');
      }, 900);
    } catch (err: any) {
      const msg = err?.response?.data?.error?.message;
      setStatusError(msg || 'Failed to accept invitation. Please try again.');
      setAccepting(false);
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

  // Safe internal return path for authentication redirect (Strict open-redirect defense)
  const safeReturnPath = `/business/invite?token=${encodeURIComponent(token)}`;

  return (
    <div className="min-h-screen bg-[#020617] flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden selection:bg-emerald-500/30">
      {/* Background Glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[500px] bg-emerald-500/10 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute bottom-10 right-1/4 w-[400px] h-[400px] bg-teal-500/5 rounded-full blur-[120px] pointer-events-none" />

      {/* Grid Pattern */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b08_1px,transparent_1px),linear-gradient(to_bottom,#1e293b08_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_40%,#000_70%,transparent_100%)] pointer-events-none" />

      {/* Brand Header */}
      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10 text-center mb-8">
        <motion.div
          initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, y: -16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35 }}
          className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold tracking-wider uppercase backdrop-blur-md mb-4"
        >
          <Building2 className="w-3.5 h-3.5 text-emerald-400" />
          <span>Business OS • Workspace Invitation</span>
        </motion.div>

        <motion.div
          initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, delay: 0.05 }}
        >
          <h1 className="text-3xl font-black tracking-tight text-white sm:text-4xl">
            You're Invited
          </h1>
          <p className="mt-2 text-sm text-slate-400">
            Join your team's commercial operations cockpit on DeadlineOS
          </p>
        </motion.div>
      </div>

      {/* Main Card */}
      <motion.div
        initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.1 }}
        className="sm:mx-auto sm:w-full sm:max-w-md relative z-10 px-4 sm:px-0"
      >
        <div className="bg-slate-900/60 backdrop-blur-xl border border-slate-800/80 py-8 px-6 sm:px-10 shadow-2xl rounded-2xl">
          {/* STATE 1: Loading Skeleton */}
          {loading && (
            <div className="py-6 text-center space-y-4">
              <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 mx-auto animate-pulse">
                <RefreshCw className="w-6 h-6 animate-spin text-emerald-400" />
              </div>
              <div>
                <p className="text-sm font-semibold text-white">Validating Invitation...</p>
                <p className="text-xs text-slate-500 mt-1">Verifying cryptographic token authority</p>
              </div>
            </div>
          )}

          {/* STATE 2: Error Banner / Invalid State */}
          {!loading && statusError && !acceptedSuccess && (
            <div className="text-center py-4">
              <div className="w-12 h-12 rounded-2xl bg-rose-500/10 text-rose-400 flex items-center justify-center mx-auto mb-4 border border-rose-500/20">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <h2 className="text-lg font-bold text-white mb-2">Unable to Join Workspace</h2>
              <p className="text-sm text-slate-400 mb-6 leading-relaxed">
                {statusError}
              </p>
              <div className="flex flex-col gap-3">
                <Link
                  to="/business/login"
                  className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-sm font-semibold transition-colors"
                >
                  <span>Go to Business Sign In</span>
                  <ArrowRight className="w-4 h-4" />
                </Link>
                <Link
                  to="/dashboard"
                  className="text-xs text-slate-500 hover:text-slate-300 transition-colors"
                >
                  Return to Personal OS
                </Link>
              </div>
            </div>
          )}

          {/* STATE 3: Valid Invitation Details */}
          {!loading && !statusError && invitation && (
            <div className="space-y-6">
              {/* Organization Header */}
              <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/80 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400 font-medium">Organization</span>
                  <div className={`px-2.5 py-0.5 rounded-full border text-[11px] font-bold uppercase tracking-wider ${getRoleBadge(invitation.role)}`}>
                    {invitation.role}
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center border border-emerald-500/20 shrink-0">
                    <Building2 className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-white tracking-tight">
                      {invitation.workspace_name}
                    </h3>
                    <p className="text-xs text-slate-400 flex items-center gap-1.5 mt-0.5">
                      <Mail className="w-3 h-3 text-slate-500" />
                      <span>{invitation.email}</span>
                    </p>
                  </div>
                </div>

                {invitation.expires_at && (
                  <div className="pt-2 border-t border-slate-900 flex items-center gap-1.5 text-[11px] text-slate-500">
                    <Clock className="w-3 h-3 text-slate-500" />
                    <span>Expires: {new Date(invitation.expires_at).toLocaleDateString()}</span>
                  </div>
                )}
              </div>

              {/* Authenticated State Actions */}
              {user ? (
                <div className="space-y-3 pt-2">
                  <div className="p-3 rounded-lg bg-emerald-500/5 border border-emerald-500/10 flex items-center gap-2.5 text-xs text-emerald-400">
                    <UserCheck className="w-4 h-4 shrink-0" />
                    <span>Joining as <strong>{user.email}</strong></span>
                  </div>

                  <button
                    onClick={handleAccept}
                    disabled={accepting || acceptedSuccess}
                    className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl font-bold text-sm bg-emerald-400 hover:bg-emerald-300 text-slate-950 shadow-lg shadow-emerald-500/20 transition-all disabled:opacity-60 disabled:cursor-not-allowed cursor-pointer"
                  >
                    {accepting ? (
                      <div className="flex items-center gap-2">
                        <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                        <span>Accepting Membership...</span>
                      </div>
                    ) : acceptedSuccess ? (
                      <div className="flex items-center gap-2 text-slate-950">
                        <CheckCircle2 className="w-4 h-4" />
                        <span>Access Granted! Loading OS...</span>
                      </div>
                    ) : (
                      <>
                        <span>Accept Invitation & Join</span>
                        <ArrowRight className="w-4 h-4" />
                      </>
                    )}
                  </button>
                </div>
              ) : (
                /* Unauthenticated State Actions */
                <div className="space-y-3 pt-2">
                  <p className="text-xs text-slate-400 text-center mb-2">
                    Please sign in or create an account to accept this commercial membership.
                  </p>

                  <Link
                    to={`/business/login?next=${encodeURIComponent(safeReturnPath)}`}
                    className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl font-bold text-sm bg-emerald-400 hover:bg-emerald-300 text-slate-950 shadow-lg shadow-emerald-500/20 transition-all cursor-pointer"
                  >
                    <span>Sign In to Accept</span>
                    <ArrowRight className="w-4 h-4" />
                  </Link>

                  <Link
                    to={`/business/register?next=${encodeURIComponent(safeReturnPath)}`}
                    className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl font-semibold text-xs bg-slate-800 hover:bg-slate-700 text-white transition-colors"
                  >
                    <span>New to DeadlineOS? Create Account</span>
                  </Link>
                </div>
              )}
            </div>
          )}

          {/* Footer Assistance */}
          <div className="mt-8 pt-6 border-t border-slate-800/80 text-center">
            <p className="text-xs text-slate-500">
              Need personal productivity?{' '}
              <Link to="/login" className="font-semibold text-indigo-400 hover:text-indigo-300 transition-colors">
                Personal OS Sign In
              </Link>
            </p>
          </div>
        </div>

        {/* Security Guarantee */}
        <div className="mt-6 flex items-center justify-center gap-2 text-xs text-slate-500">
          <ShieldCheck className="w-4 h-4 text-emerald-500/70" />
          <span>Server-verified invitation token • Multi-tenant RBAC onboarding</span>
        </div>
      </motion.div>
    </div>
  );
};
