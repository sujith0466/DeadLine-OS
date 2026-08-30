import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import { Building2, ArrowRight, Lock, Mail, Eye, EyeOff, AlertCircle, ShieldCheck, Briefcase } from 'lucide-react';
import { supabase } from '../../lib/supabase';
import { useAuth } from '../../context/AuthContext';
import { useBusinessAuth } from '../../context/BusinessAuthContext';

export const BusinessLogin: React.FC = () => {
  const navigate = useNavigate();
  const shouldReduceMotion = useReducedMotion();
  const [searchParams] = useSearchParams();
  const { user, loading: authLoading } = useAuth();
  const { workspaces, refreshWorkspaces, selectWorkspace, loading: bizLoading } = useBusinessAuth();

  const rawNext = searchParams.get('next');
  const safeNext = (rawNext && rawNext.startsWith('/') && !rawNext.startsWith('//') && !rawNext.includes('\\')) ? rawNext : null;

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Ref to prevent premature routing from useEffect during active form submission
  const isSubmitting = useRef(false);

  // If already authenticated with Supabase on mount/entry, evaluate Business workspaces after discovery completes
  useEffect(() => {
    if (!authLoading && user && !bizLoading && !isSubmitting.current) {
      if (safeNext) {
        navigate(safeNext);
      } else if (workspaces.length === 0) {
        navigate('/business/register');
      } else if (workspaces.length === 1 && workspaces[0].status === 'ACTIVE') {
        selectWorkspace(workspaces[0].id).then(() => {
          navigate('/business/dashboard');
        });
      } else if (workspaces.length > 1) {
        navigate('/business/select');
      }
    }
  }, [user, authLoading, workspaces, bizLoading, navigate, selectWorkspace, safeNext]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    const cleanEmail = email.trim().toLowerCase();
    if (!cleanEmail || !password) {
      setErrorMessage('Please enter both your work email and password.');
      return;
    }

    try {
      setLoading(true);
      isSubmitting.current = true;

      const { data, error: signInError } = await supabase.auth.signInWithPassword({
        email: cleanEmail,
        password,
      });

      if (signInError) {
        isSubmitting.current = false;
        if (signInError.message.toLowerCase().includes('invalid login credentials')) {
          setErrorMessage('Invalid commercial credentials. Please verify your email and password.');
        } else if (signInError.message.toLowerCase().includes('email not confirmed')) {
          setErrorMessage('Please verify your work email address before accessing Business OS.');
        } else {
          setErrorMessage(signInError.message || 'Authentication failed. Please try again.');
        }
        setLoading(false);
        return;
      }

      if (data?.user) {
        // Trigger authoritative workspace discovery and WAIT for server result
        try {
          const freshWorkspaces = await refreshWorkspaces();

          if (safeNext) {
            navigate(safeNext);
          } else if (!freshWorkspaces || freshWorkspaces.length === 0) {
            // Scenario B: Legitimate 0 Business workspaces -> BusinessRegister Step 1
            navigate('/business/register');
          } else if (freshWorkspaces.length === 1 && freshWorkspaces[0].status === 'ACTIVE') {
            // Scenario A: Exactly 1 active workspace -> select and navigate to dashboard
            await selectWorkspace(freshWorkspaces[0].id);
            navigate('/business/dashboard');
          } else {
            // Scenario C: Multiple workspaces -> select workspace screen
            navigate('/business/select');
          }
        } catch (discoverErr: any) {
          isSubmitting.current = false;
          setErrorMessage(discoverErr?.response?.data?.error?.message || discoverErr?.message || 'Failed to discover business workspaces. Please try again.');
          setLoading(false);
        }
      }
    } catch (err: any) {
      isSubmitting.current = false;
      setErrorMessage(err?.message || 'An unexpected error occurred during business sign in.');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#030712] flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden selection:bg-emerald-500/30 font-sans [perspective:1200px]">
      {/* Enterprise Ambient Lighting & Glows */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[520px] bg-gradient-to-tr from-emerald-500/15 via-teal-500/10 to-transparent rounded-full blur-[150px] pointer-events-none transform-gpu" />
      <div className="absolute bottom-10 right-1/4 w-[450px] h-[450px] bg-emerald-500/8 rounded-full blur-[130px] pointer-events-none transform-gpu" />
      <div className="absolute top-10 left-10 w-[320px] h-[320px] bg-cyan-500/8 rounded-full blur-[110px] pointer-events-none transform-gpu" />

      {/* Enterprise Precision Grid */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#10b98108_1px,transparent_1px),linear-gradient(to_bottom,#10b98108_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_65%_55%_at_50%_40%,#000_70%,transparent_100%)] pointer-events-none" />

      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10">
        {/* Brand Badge & Commercial Anchor */}
        <motion.div
          initial={shouldReduceMotion ? false : { opacity: 0, y: -16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="flex flex-col items-center mb-6"
        >
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-gradient-to-r from-emerald-500/10 via-teal-500/10 to-emerald-500/10 border border-emerald-500/25 text-emerald-300 text-xs font-semibold tracking-wider uppercase backdrop-blur-md shadow-inner shadow-emerald-500/10">
            <Building2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>Business OS • Commercial Portal</span>
          </div>

          <div className="mt-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 p-[1px] shadow-lg shadow-emerald-500/25 flex items-center justify-center">
              <div className="w-full h-full bg-slate-950 rounded-[15px] flex items-center justify-center shadow-inner">
                <Briefcase className="w-5 h-5 text-emerald-400" />
              </div>
            </div>
            <div className="text-left">
              <span className="text-xl font-extrabold tracking-tight text-white">Deadline<span className="text-emerald-400">OS</span></span>
            </div>
          </div>
        </motion.div>

        {/* Title */}
        <motion.div
          initial={shouldReduceMotion ? false : { opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.08 }}
          className="text-center"
        >
          <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-white">
            Enterprise Sign In
          </h1>
          <p className="mt-2 text-sm text-slate-400 leading-relaxed max-w-sm mx-auto">
            Access your organization's financial cockpit, automated operations, and verified ledger
          </p>
        </motion.div>
      </div>

      {/* Main Form Card with 3D Depth */}
      <motion.div
        initial={shouldReduceMotion ? false : { opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        whileHover={shouldReduceMotion ? undefined : { y: -2, transition: { duration: 0.2 } }}
        transition={{ duration: 0.45, delay: 0.14 }}
        className="mt-8 sm:mx-auto sm:w-full sm:max-w-md relative z-10"
      >
        <div className="bg-slate-900/70 backdrop-blur-2xl border border-slate-800/90 py-8 px-6 sm:px-10 shadow-[0_20px_60px_-15px_rgba(0,0,0,0.7),0_0_40px_rgba(16,185,129,0.08)] rounded-3xl relative overflow-hidden transition-all duration-300">
          {/* Top Edge Ambient Highlight */}
          <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-emerald-500/50 to-transparent" />

          <form className="space-y-4.5" onSubmit={handleSubmit} noValidate>
            {/* Error Banner */}
            <AnimatePresence mode="wait">
              {errorMessage && (
                <motion.div
                  initial={shouldReduceMotion ? false : { opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="rounded-xl bg-rose-500/10 border border-rose-500/25 p-3.5 flex items-start gap-2.5 text-rose-300 text-xs sm:text-sm overflow-hidden shadow-sm"
                  role="alert"
                >
                  <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-400" />
                  <span className="leading-snug">{errorMessage}</span>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Email Input */}
            <div>
              <label htmlFor="business-email" className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                Work Email Address
              </label>
              <div className="relative rounded-xl shadow-sm group">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500 group-focus-within:text-emerald-400 transition-colors">
                  <Mail className="h-4.5 w-4.5" />
                </div>
                <input
                  id="business-email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@company.com"
                  className="block w-full pl-10 pr-3.5 py-3 bg-slate-950/70 border border-slate-700/80 rounded-xl text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all shadow-inner"
                />
              </div>
            </div>

            {/* Password Input with Eye Toggle */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label htmlFor="business-password" className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
                  Password
                </label>
              </div>
              <div className="relative rounded-xl shadow-sm group">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500 group-focus-within:text-emerald-400 transition-colors">
                  <Lock className="h-4.5 w-4.5" />
                </div>
                <input
                  id="business-password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="block w-full pl-10 pr-11 py-3 bg-slate-950/70 border border-slate-700/80 rounded-xl text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all shadow-inner"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-200 transition-colors cursor-pointer focus:outline-none focus:text-emerald-400"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                  title={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="h-4.5 w-4.5" /> : <Eye className="h-4.5 w-4.5" />}
                </button>
              </div>
            </div>

            {/* Submit Button */}
            <div className="pt-2">
              <button
                type="submit"
                disabled={loading || authLoading}
                className="w-full flex justify-center items-center gap-2 py-3 px-4 rounded-xl shadow-lg shadow-emerald-500/20 text-sm font-bold text-slate-950 bg-gradient-to-r from-emerald-400 via-teal-300 to-emerald-400 hover:from-emerald-300 hover:to-teal-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500 focus:ring-offset-slate-900 transition-all disabled:opacity-60 disabled:cursor-not-allowed cursor-pointer active:scale-[0.99] group"
              >
                {loading ? (
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                    <span>Authenticating Workspace...</span>
                  </div>
                ) : (
                  <>
                    <span>Enter Business OS</span>
                    <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                  </>
                )}
              </button>
            </div>
          </form>

          {/* Divider & Navigation Links */}
          <div className="mt-6 pt-5 border-t border-slate-800/80 text-center space-y-2.5">
            <p className="text-xs text-slate-400">
              New organization?{' '}
              <Link to="/business/register" className="font-semibold text-emerald-400 hover:text-emerald-300 transition-colors">
                Create a Business Workspace
              </Link>
            </p>
            <p className="text-xs text-slate-500">
              Looking for individual productivity?{' '}
              <Link to="/login" className="font-semibold text-indigo-400 hover:text-indigo-300 transition-colors">
                Switch to Personal OS
              </Link>
            </p>
          </div>
        </div>

        {/* Security Assurance Badge */}
        <div className="mt-6 flex items-center justify-center gap-2 text-xs text-slate-500">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400/80" />
          <span>Multi-tenant encrypted isolation • Server-verified RBAC</span>
        </div>
      </motion.div>
    </div>
  );
};
