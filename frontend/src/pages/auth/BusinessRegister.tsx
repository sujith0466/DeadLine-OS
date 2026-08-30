import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Building2, ArrowRight, Lock, Mail, User, ShieldCheck, AlertCircle, CheckCircle2, Sparkles } from 'lucide-react';
import { supabase } from '../../lib/supabase';
import { useAuth } from '../../context/AuthContext';
import { useBusinessAuth } from '../../context/BusinessAuthContext';

export const BusinessRegister: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { createWorkspace, refreshWorkspaces } = useBusinessAuth();

  // Form State
  const [step, setStep] = useState<'account' | 'workspace' | 'verification'>(user ? 'workspace' : 'account');
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  // Workspace Onboarding State
  const [workspaceName, setWorkspaceName] = useState('');
  const [legalName, setLegalName] = useState('');
  const [taxIdentifier, setTaxIdentifier] = useState('');
  const [baseCurrency, setBaseCurrency] = useState('INR');
  const [timezone, setTimezone] = useState('Asia/Kolkata');

  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // If user is already authenticated, skip account step and proceed to workspace creation
  useEffect(() => {
    if (user && step === 'account') {
      setStep('workspace');
    }
  }, [user, step]);

  const handleAccountSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    const cleanEmail = email.trim().toLowerCase();
    if (!fullName.trim() || !cleanEmail || !password) {
      setErrorMessage('Please fill in all required account fields.');
      return;
    }

    if (password.length < 8) {
      setErrorMessage('Password must be at least 8 characters long.');
      return;
    }

    if (password !== confirmPassword) {
      setErrorMessage('Passwords do not match.');
      return;
    }

    try {
      setLoading(true);
      const { data, error: signUpError } = await supabase.auth.signUp({
        email: cleanEmail,
        password,
        options: {
          data: {
            full_name: fullName.trim(),
          },
        },
      });

      if (signUpError) {
        setErrorMessage(signUpError.message || 'Account registration failed.');
        setLoading(false);
        return;
      }

      if (data?.session) {
        // Immediate session active, advance to workspace onboarding
        setStep('workspace');
      } else if (data?.user && !data.session) {
        // Email verification required
        setStep('verification');
      }
    } catch (err: any) {
      setErrorMessage(err?.message || 'An unexpected error occurred.');
    } finally {
      setLoading(false);
    }
  };

  const handleWorkspaceSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!workspaceName.trim()) {
      setErrorMessage('Organization / Workspace Name is required.');
      return;
    }

    try {
      setLoading(true);
      await createWorkspace({
        name: workspaceName.trim(),
        legal_name: legalName.trim() || undefined,
        tax_identifier: taxIdentifier.trim() || undefined,
        base_currency: baseCurrency,
        timezone,
      });

      await refreshWorkspaces();
      navigate('/dashboard'); // or /business/dashboard
    } catch (err: any) {
      setErrorMessage(err?.response?.data?.error?.message || err?.message || 'Failed to create business workspace.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#030712] flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden selection:bg-emerald-500/30">
      {/* Dynamic Background Glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[500px] bg-emerald-500/10 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute bottom-10 right-1/4 w-[400px] h-[400px] bg-cyan-500/5 rounded-full blur-[120px] pointer-events-none" />

      {/* Decorative Grid */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b08_1px,transparent_1px),linear-gradient(to_bottom,#1e293b08_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_40%,#000_70%,transparent_100%)] pointer-events-none" />

      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10">
        {/* Brand Badge */}
        <motion.div
          initial={{ opacity: 0, y: -16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="flex justify-center mb-6"
        >
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold tracking-wider uppercase backdrop-blur-md">
            <Building2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>Business OS • Organization Onboarding</span>
          </div>
        </motion.div>

        {/* Title */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
          className="text-center"
        >
          <h2 className="text-3xl font-black tracking-tight text-white sm:text-4xl">
            {step === 'workspace' ? 'Create Your Workspace' : step === 'verification' ? 'Verify Your Work Email' : 'Register Organization'}
          </h2>
          <p className="mt-2 text-sm text-slate-400">
            {step === 'workspace'
              ? 'Establish authoritative financial operations and multi-tenant ledger'
              : step === 'verification'
              ? 'We sent an activation link to your email to confirm your identity'
              : 'Empower your commercial enterprise with deterministic clarity'}
          </p>
        </motion.div>
      </div>

      {/* Form Container */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, delay: 0.15 }}
        className="mt-8 sm:mx-auto sm:w-full sm:max-w-lg relative z-10 px-4 sm:px-0"
      >
        <div className="bg-slate-900/60 backdrop-blur-xl border border-slate-800/80 py-8 px-6 sm:px-10 shadow-2xl rounded-2xl">
          {/* Step Indicator */}
          {step !== 'verification' && (
            <div className="flex items-center justify-between mb-8 pb-4 border-b border-slate-800/60 text-xs font-semibold">
              <div className={`flex items-center gap-2 ${step === 'account' ? 'text-emerald-400' : 'text-slate-500'}`}>
                <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] ${step === 'account' ? 'bg-emerald-400 text-slate-950 font-bold' : 'bg-slate-800 text-slate-400'}`}>
                  1
                </span>
                <span>Administrator Account</span>
              </div>
              <div className="w-8 h-px bg-slate-800" />
              <div className={`flex items-center gap-2 ${step === 'workspace' ? 'text-emerald-400' : 'text-slate-500'}`}>
                <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] ${step === 'workspace' ? 'bg-emerald-400 text-slate-950 font-bold' : 'bg-slate-800 text-slate-400'}`}>
                  2
                </span>
                <span>Workspace Setup</span>
              </div>
            </div>
          )}

          {/* Error Banner */}
          <AnimatePresence mode="wait">
            {errorMessage && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mb-5 rounded-xl bg-rose-500/10 border border-rose-500/20 p-3.5 flex items-start gap-3 text-rose-400 text-sm overflow-hidden"
                role="alert"
              >
                <AlertCircle className="w-5 h-5 shrink-0 mt-0.5 text-rose-400" />
                <span className="leading-relaxed">{errorMessage}</span>
              </motion.div>
            )}
          </AnimatePresence>

          {/* STEP 1: Account Creation */}
          {step === 'account' && (
            <form className="space-y-4" onSubmit={handleAccountSubmit} noValidate>
              <div>
                <label htmlFor="full-name" className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                  Full Name
                </label>
                <div className="relative rounded-xl shadow-sm">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                    <User className="h-4 w-4" />
                  </div>
                  <input
                    id="full-name"
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Alex Morgan"
                    className="block w-full pl-10 pr-3 py-2.5 bg-slate-950/70 border border-slate-800 rounded-xl text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="business-reg-email" className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                  Work Email
                </label>
                <div className="relative rounded-xl shadow-sm">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                    <Mail className="h-4 w-4" />
                  </div>
                  <input
                    id="business-reg-email"
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="alex@enterprise.com"
                    className="block w-full pl-10 pr-3 py-2.5 bg-slate-950/70 border border-slate-800 rounded-xl text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="business-reg-password" className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                    Password
                  </label>
                  <div className="relative rounded-xl shadow-sm">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                      <Lock className="h-4 w-4" />
                    </div>
                    <input
                      id="business-reg-password"
                      type="password"
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••••••"
                      className="block w-full pl-10 pr-3 py-2.5 bg-slate-950/70 border border-slate-800 rounded-xl text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="business-reg-confirm" className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                    Confirm
                  </label>
                  <div className="relative rounded-xl shadow-sm">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                      <Lock className="h-4 w-4" />
                    </div>
                    <input
                      id="business-reg-confirm"
                      type="password"
                      required
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="••••••••••••"
                      className="block w-full pl-10 pr-3 py-2.5 bg-slate-950/70 border border-slate-800 rounded-xl text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
                    />
                  </div>
                </div>
              </div>

              <div className="pt-3">
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full flex justify-center items-center gap-2 py-3 px-4 border border-transparent rounded-xl shadow-lg shadow-emerald-500/20 text-sm font-bold text-slate-950 bg-emerald-400 hover:bg-emerald-300 focus:outline-none focus:ring-2 focus:ring-emerald-500 transition-all cursor-pointer"
                >
                  {loading ? 'Creating Account...' : 'Continue to Workspace Details'}
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </form>
          )}

          {/* STEP 2: Workspace Onboarding */}
          {step === 'workspace' && (
            <form className="space-y-4" onSubmit={handleWorkspaceSubmit} noValidate>
              <div>
                <label htmlFor="ws-name" className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                  Company / Organization Name *
                </label>
                <div className="relative rounded-xl shadow-sm">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                    <Building2 className="h-4 w-4" />
                  </div>
                  <input
                    id="ws-name"
                    type="text"
                    required
                    value={workspaceName}
                    onChange={(e) => setWorkspaceName(e.target.value)}
                    placeholder="Starlight Ventures Ltd"
                    className="block w-full pl-10 pr-3 py-2.5 bg-slate-950/70 border border-slate-800 rounded-xl text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="legal-name" className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                    Legal Name (Optional)
                  </label>
                  <input
                    id="legal-name"
                    type="text"
                    value={legalName}
                    onChange={(e) => setLegalName(e.target.value)}
                    placeholder="Starlight Ventures Pvt Ltd"
                    className="block w-full px-3.5 py-2.5 bg-slate-950/70 border border-slate-800 rounded-xl text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
                  />
                </div>

                <div>
                  <label htmlFor="tax-id" className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                    Tax ID / GSTIN / EIN
                  </label>
                  <input
                    id="tax-id"
                    type="text"
                    value={taxIdentifier}
                    onChange={(e) => setTaxIdentifier(e.target.value)}
                    placeholder="29AAAAA0000A1Z5"
                    className="block w-full px-3.5 py-2.5 bg-slate-950/70 border border-slate-800 rounded-xl text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="base-currency" className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                    Base Currency
                  </label>
                  <select
                    id="base-currency"
                    value={baseCurrency}
                    onChange={(e) => setBaseCurrency(e.target.value)}
                    className="block w-full px-3.5 py-2.5 bg-slate-950/70 border border-slate-800 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
                  >
                    <option value="INR">INR (₹) - Indian Rupee</option>
                    <option value="USD">USD ($) - US Dollar</option>
                    <option value="EUR">EUR (€) - Euro</option>
                    <option value="GBP">GBP (£) - British Pound</option>
                  </select>
                </div>

                <div>
                  <label htmlFor="ws-timezone" className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                    Operating Timezone
                  </label>
                  <select
                    id="ws-timezone"
                    value={timezone}
                    onChange={(e) => setTimezone(e.target.value)}
                    className="block w-full px-3.5 py-2.5 bg-slate-950/70 border border-slate-800 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
                  >
                    <option value="Asia/Kolkata">Asia/Kolkata (IST)</option>
                    <option value="America/New_York">America/New_York (EST)</option>
                    <option value="America/Los_Angeles">America/Los_Angeles (PST)</option>
                    <option value="Europe/London">Europe/London (GMT)</option>
                    <option value="Europe/Berlin">Europe/Berlin (CET)</option>
                    <option value="Asia/Singapore">Asia/Singapore (SGT)</option>
                    <option value="Asia/Dubai">Asia/Dubai (GST)</option>
                  </select>
                </div>
              </div>

              <div className="pt-3">
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full flex justify-center items-center gap-2 py-3 px-4 border border-transparent rounded-xl shadow-lg shadow-emerald-500/20 text-sm font-bold text-slate-950 bg-emerald-400 hover:bg-emerald-300 focus:outline-none focus:ring-2 focus:ring-emerald-500 transition-all cursor-pointer"
                >
                  {loading ? (
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                      <span>Provisioning Organization...</span>
                    </div>
                  ) : (
                    <>
                      <span>Launch Business Workspace</span>
                      <Sparkles className="w-4 h-4" />
                    </>
                  )}
                </button>
              </div>
            </form>
          )}

          {/* Verification State */}
          {step === 'verification' && (
            <div className="text-center py-6">
              <div className="w-12 h-12 rounded-full bg-emerald-500/10 text-emerald-400 flex items-center justify-center mx-auto mb-4 border border-emerald-500/20">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Check Your Inbox</h3>
              <p className="text-sm text-slate-400 mb-6 leading-relaxed">
                We've sent a verification link to <span className="text-white font-medium">{email}</span>. Click the link in your email to confirm your account and begin workspace setup.
              </p>
              <Link
                to="/business/login"
                className="inline-flex items-center gap-2 text-sm font-semibold text-emerald-400 hover:text-emerald-300"
              >
                Return to Enterprise Sign In <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          )}

          {/* Divider */}
          <div className="mt-8 pt-6 border-t border-slate-800/80 text-center">
            <p className="text-xs text-slate-400">
              Already have an organization?{' '}
              <Link to="/business/login" className="font-semibold text-emerald-400 hover:text-emerald-300 transition-colors">
                Sign In to Business OS
              </Link>
            </p>
            <p className="mt-3 text-xs text-slate-500">
              Looking for individual productivity?{' '}
              <Link to="/register" className="font-semibold text-indigo-400 hover:text-indigo-300 transition-colors">
                Register Personal Account
              </Link>
            </p>
          </div>
        </div>

        {/* Assurance */}
        <div className="mt-6 flex items-center justify-center gap-2 text-xs text-slate-500">
          <ShieldCheck className="w-4 h-4 text-emerald-500/70" />
          <span>Atomic transactional onboarding • Automatic OWNER provisioning</span>
        </div>
      </motion.div>
    </div>
  );
};
