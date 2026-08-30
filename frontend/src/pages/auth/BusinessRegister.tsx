import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import { Building2, ArrowRight, Lock, Mail, User, ShieldCheck, AlertCircle, CheckCircle2, XCircle, Sparkles, Globe, DollarSign, FileText, ArrowLeft, Eye, EyeOff, Check, Dot, ChevronDown } from 'lucide-react';
import { supabase } from '../../lib/supabase';
import { useAuth } from '../../context/AuthContext';
import { useBusinessAuth } from '../../context/BusinessAuthContext';

export const BusinessRegister: React.FC = () => {
  const navigate = useNavigate();
  const shouldReduceMotion = useReducedMotion();
  const [searchParams] = useSearchParams();
  const { user } = useAuth();
  const { createWorkspace, refreshWorkspaces } = useBusinessAuth();

  const rawNext = searchParams.get('next');
  const safeNext = (rawNext && rawNext.startsWith('/') && !rawNext.startsWith('//') && !rawNext.includes('\\')) ? rawNext : null;

  // Form State: Always start at Step 1 (Account details)
  const [step, setStep] = useState<'account' | 'workspace' | 'verification'>('account');
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  
  // Workspace Onboarding State
  const [workspaceName, setWorkspaceName] = useState('');
  const [legalName, setLegalName] = useState('');
  const [taxIdentifier, setTaxIdentifier] = useState('');
  const [baseCurrency, setBaseCurrency] = useState('INR');
  const [timezone, setTimezone] = useState('Asia/Kolkata');

  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Authoritative email verification check from Supabase identity
  const isEmailVerified = Boolean(
    user?.email_confirmed_at ||
    (user as any)?.confirmed_at ||
    (user?.app_metadata && user.app_metadata.provider && user.app_metadata.provider !== 'email')
  );

  // Prefill existing Supabase identity details when user is authenticated
  useEffect(() => {
    if (user) {
      if (user.email && !email) {
        setEmail(user.email);
      }
      const metaName = (user.user_metadata?.full_name || user.user_metadata?.name || '') as string;
      if (metaName && !fullName) {
        setFullName(metaName);
      }
    }
  }, [user, email, fullName]);

  // If safeNext exists, navigate accordingly
  useEffect(() => {
    if (user && safeNext) {
      navigate(safeNext);
    }
  }, [user, safeNext, navigate]);

  // 5-tier password strength model
  const evaluatePasswordStrength = (pass: string) => {
    if (!pass) return { score: 0, label: '', color: 'bg-slate-800', textColor: 'text-slate-500' };

    const hasMinLength = pass.length >= 8;
    const hasLower = /[a-z]/.test(pass);
    const hasUpper = /[A-Z]/.test(pass);
    const hasNumber = /[0-9]/.test(pass);
    const hasSpecial = /[^A-Za-z0-9]/.test(pass);

    const criteriaCount = [hasLower, hasUpper, hasNumber, hasSpecial].filter(Boolean).length;

    if (!hasMinLength || criteriaCount <= 1) {
      return { score: 1, label: 'Weak', color: 'bg-rose-500', textColor: 'text-rose-400' };
    }
    if (hasMinLength && criteriaCount === 2) {
      return { score: 2, label: 'Fair', color: 'bg-amber-400', textColor: 'text-amber-400' };
    }
    if (hasMinLength && (criteriaCount === 3 || (criteriaCount === 4 && pass.length < 10))) {
      return { score: 3, label: 'Strong', color: 'bg-emerald-400', textColor: 'text-emerald-400' };
    }
    if (hasMinLength && criteriaCount === 4 && pass.length >= 10) {
      return { score: 4, label: 'Very Strong', color: 'bg-emerald-300', textColor: 'text-emerald-300' };
    }

    return { score: 2, label: 'Fair', color: 'bg-amber-400', textColor: 'text-amber-400' };
  };

  const strength = evaluatePasswordStrength(password);
  const passwordsMatch = password && confirmPassword ? password === confirmPassword : null;

  const handleAccountSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    // SCENARIO A: Existing authenticated user
    if (user) {
      if (!fullName.trim()) {
        setErrorMessage('Please provide your Administrator Full Name.');
        return;
      }
      // Non-blocking metadata sync if full_name was entered or updated
      try {
        if (fullName.trim() !== (user.user_metadata?.full_name || user.user_metadata?.name)) {
          await supabase.auth.updateUser({
            data: { full_name: fullName.trim() },
          });
        }
      } catch {
        // Continue seamlessly to workspace details
      }
      // Advance to Step 2 (Workspace Details) without creating duplicate identity or calling signUp
      setStep('workspace');
      return;
    }

    // SCENARIO B: New unauthenticated user
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
      navigate('/business/dashboard');
    } catch (err: any) {
      setErrorMessage(err?.response?.data?.error?.message || err?.message || 'Failed to create business workspace.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#030712] flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden selection:bg-emerald-500/30 font-sans [perspective:1200px]">
      {/* Enterprise Ambient Glows */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[520px] bg-gradient-to-tr from-emerald-500/15 via-cyan-500/10 to-transparent rounded-full blur-[150px] pointer-events-none transform-gpu" />
      <div className="absolute bottom-10 right-1/4 w-[450px] h-[450px] bg-teal-500/8 rounded-full blur-[130px] pointer-events-none transform-gpu" />
      <div className="absolute top-10 right-10 w-[320px] h-[320px] bg-emerald-500/8 rounded-full blur-[110px] pointer-events-none transform-gpu" />

      {/* Enterprise Grid */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#10b98108_1px,transparent_1px),linear-gradient(to_bottom,#10b98108_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_65%_55%_at_50%_40%,#000_70%,transparent_100%)] pointer-events-none" />

      <div className="sm:mx-auto sm:w-full sm:max-w-xl relative z-10">
        {/* Brand Badge */}
        <motion.div
          initial={shouldReduceMotion ? false : { opacity: 0, y: -16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="flex flex-col items-center mb-6"
        >
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-gradient-to-r from-emerald-500/10 via-teal-500/10 to-emerald-500/10 border border-emerald-500/25 text-emerald-300 text-xs font-semibold tracking-wider uppercase backdrop-blur-md shadow-inner shadow-emerald-500/10">
            <Building2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>Business OS • Organization Onboarding</span>
          </div>

          <div className="mt-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 p-[1px] shadow-lg shadow-emerald-500/25 flex items-center justify-center">
              <div className="w-full h-full bg-slate-950 rounded-[15px] flex items-center justify-center shadow-inner">
                <Sparkles className="w-5 h-5 text-emerald-400" />
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
            {step === 'workspace' ? 'Configure Your Workspace' : step === 'verification' ? 'Verify Work Email' : 'Register Organization'}
          </h1>
          <p className="mt-2 text-sm text-slate-400 leading-relaxed max-w-md mx-auto">
            {step === 'workspace'
              ? 'Establish authoritative commercial operations, base currency, and ledger parameters'
              : step === 'verification'
              ? 'We sent a secure activation link to your email to confirm your administrator identity'
              : 'Empower your commercial enterprise with deterministic clarity and verified multi-tenant security'}
          </p>
        </motion.div>
      </div>

      {/* Main Form Container with 3D Depth */}
      <motion.div
        initial={shouldReduceMotion ? false : { opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        whileHover={shouldReduceMotion ? undefined : { y: -2, transition: { duration: 0.2 } }}
        transition={{ duration: 0.45, delay: 0.14 }}
        className="mt-8 sm:mx-auto sm:w-full sm:max-w-xl relative z-10"
      >
        <div className="bg-slate-900/70 backdrop-blur-2xl border border-slate-800/90 py-8 px-6 sm:px-10 shadow-[0_20px_60px_-15px_rgba(0,0,0,0.7),0_0_40px_rgba(16,185,129,0.08)] rounded-3xl relative overflow-hidden transition-all duration-300">
          {/* Top Edge Ambient Highlight */}
          <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-emerald-500/50 to-transparent" />

          {/* Stepper Header */}
          {step !== 'verification' && (
            <div className="flex items-center justify-between mb-8 pb-4 border-b border-slate-800/80">
              <div className={`flex items-center gap-2.5 text-xs font-semibold ${step === 'account' ? 'text-emerald-400' : 'text-slate-400'}`}>
                <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold transition-all shadow-sm ${
                  step === 'account' ? 'bg-emerald-400 text-slate-950 shadow-emerald-500/30' : 'bg-slate-800 text-emerald-400 border border-emerald-500/30'
                }`}>
                  {step === 'workspace' ? <CheckCircle2 className="w-4 h-4" /> : '1'}
                </span>
                <span>Administrator Account</span>
              </div>

              <div className="flex-1 max-w-[60px] h-0.5 mx-3 bg-slate-800 relative overflow-hidden rounded-full">
                <div className={`h-full bg-emerald-400 transition-all duration-500 ${step === 'workspace' ? 'w-full' : 'w-0'}`} />
              </div>

              <div className={`flex items-center gap-2.5 text-xs font-semibold ${step === 'workspace' ? 'text-emerald-400' : 'text-slate-500'}`}>
                <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                  step === 'workspace' ? 'bg-emerald-400 text-slate-950 shadow-emerald-500/30 shadow-sm' : 'bg-slate-800/80 text-slate-400 border border-slate-700'
                }`}>
                  2
                </span>
                <span>Workspace Details</span>
              </div>
            </div>
          )}

          {/* Error Banner */}
          <AnimatePresence mode="wait">
            {errorMessage && (
              <motion.div
                initial={shouldReduceMotion ? false : { opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mb-5 rounded-xl bg-rose-500/10 border border-rose-500/25 p-3.5 flex items-start gap-2.5 text-rose-300 text-xs sm:text-sm overflow-hidden shadow-sm"
                role="alert"
              >
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-400" />
                <span className="leading-snug">{errorMessage}</span>
              </motion.div>
            )}
          </AnimatePresence>

          {/* STEP 1: Account Registration */}
          {step === 'account' && (
            <form className="space-y-4" onSubmit={handleAccountSubmit} noValidate>
              {/* Informational Message for Existing Authenticated User */}
              {user && (
                <motion.div
                  initial={shouldReduceMotion ? false : { opacity: 0, y: -4 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mb-5 rounded-2xl bg-emerald-500/10 border border-emerald-500/25 p-4 flex items-start gap-3 text-emerald-300 text-xs sm:text-sm shadow-inner"
                >
                  <ShieldCheck className="w-5 h-5 shrink-0 text-emerald-400 mt-0.5" />
                  <div className="space-y-1">
                    <p className="font-bold text-white tracking-wide">
                      Existing DeadlineOS account detected
                    </p>
                    <p className="text-slate-300 text-xs leading-relaxed">
                      Your Personal OS account is already connected. Complete your Business Workspace setup using this identity.
                      {isEmailVerified && (
                        <span className="block text-emerald-400 font-semibold mt-1">
                          Your account is already verified.
                        </span>
                      )}
                    </p>
                  </div>
                </motion.div>
              )}

              <div>
                <label htmlFor="full-name" className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                  Administrator Full Name
                </label>
                <div className="relative rounded-xl shadow-sm group">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500 group-focus-within:text-emerald-400 transition-colors">
                    <User className="h-4.5 w-4.5" />
                  </div>
                  <input
                    id="full-name"
                    type="text"
                    required
                    autoComplete="name"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Alex Morgan"
                    className="block w-full pl-10 pr-3.5 py-3 bg-slate-950/70 border border-slate-700/80 rounded-xl text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all shadow-inner"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="business-reg-email" className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                  Work Email Address
                </label>
                <div className="relative rounded-xl shadow-sm group">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500 group-focus-within:text-emerald-400 transition-colors">
                    <Mail className="h-4.5 w-4.5" />
                  </div>
                  <input
                    id="business-reg-email"
                    type="email"
                    required
                    autoComplete="email"
                    value={user ? (user.email || email) : email}
                    onChange={(e) => setEmail(e.target.value)}
                    readOnly={Boolean(user)}
                    placeholder="alex@enterprise.com"
                    className={`block w-full pl-10 pr-3.5 py-3 border rounded-xl text-slate-100 placeholder-slate-500 text-sm focus:outline-none transition-all shadow-inner ${
                      user
                        ? 'bg-slate-900/80 border-slate-700/60 text-slate-300 cursor-not-allowed'
                        : 'bg-slate-950/70 border-slate-700/80 focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500'
                    }`}
                  />
                </div>
              </div>

              {/* Password Section: Rendered for new users, secured notice for existing authenticated users */}
              {!user ? (
                <>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {/* Password Field with Independent Toggle */}
                    <div>
                      <label htmlFor="business-reg-password" className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                        Password (8+ chars)
                      </label>
                      <div className="relative rounded-xl shadow-sm group">
                        <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500 group-focus-within:text-emerald-400 transition-colors">
                          <Lock className="h-4.5 w-4.5" />
                        </div>
                        <input
                          id="business-reg-password"
                          type={showPassword ? 'text' : 'password'}
                          required
                          autoComplete="new-password"
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

                    {/* Confirm Password Field with Independent Toggle */}
                    <div>
                      <label htmlFor="business-reg-confirm" className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                        Confirm Password
                      </label>
                      <div className="relative rounded-xl shadow-sm group">
                        <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500 group-focus-within:text-emerald-400 transition-colors">
                          <Lock className="h-4.5 w-4.5" />
                        </div>
                        <input
                          id="business-reg-confirm"
                          type={showConfirmPassword ? 'text' : 'password'}
                          required
                          autoComplete="new-password"
                          value={confirmPassword}
                          onChange={(e) => setConfirmPassword(e.target.value)}
                          placeholder="••••••••••••"
                          className={`block w-full pl-10 pr-11 py-3 bg-slate-950/70 border rounded-xl text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50 transition-all shadow-inner ${
                            passwordsMatch === false ? 'border-rose-500/80 focus:border-rose-500' : passwordsMatch === true ? 'border-emerald-500/80 focus:border-emerald-500' : 'border-slate-700/80 focus:border-emerald-500'
                          }`}
                        />
                        <button
                          type="button"
                          onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                          className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-200 transition-colors cursor-pointer focus:outline-none focus:text-emerald-400"
                          aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
                          title={showConfirmPassword ? 'Hide password' : 'Show password'}
                        >
                          {showConfirmPassword ? <EyeOff className="h-4.5 w-4.5" /> : <Eye className="h-4.5 w-4.5" />}
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Password Strength Indicator & Match Indicators */}
                  {(password || confirmPassword) && (
                    <div className="space-y-2 pt-1">
                      {password && (
                        <AnimatePresence mode="wait">
                          <motion.div
                            initial={shouldReduceMotion ? false : { opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                            className="space-y-1.5 overflow-hidden"
                          >
                            <div className="flex items-center justify-between gap-3">
                              <div className="flex gap-1.5 w-full max-w-[140px]">
                                {[1, 2, 3, 4].map((stepIdx) => (
                                  <div
                                    key={stepIdx}
                                    className={`h-1.5 flex-1 rounded-full transition-all duration-300 ${
                                      strength.score >= stepIdx ? strength.color : 'bg-slate-800'
                                    }`}
                                  />
                                ))}
                              </div>
                              <span className={`text-[11px] font-bold tracking-wider uppercase ${strength.textColor}`}>
                                {strength.label}
                              </span>
                            </div>

                            {/* Subtle Criteria Verification Pills */}
                            <div className="flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-slate-500 pt-0.5">
                              <span className={`flex items-center gap-1 transition-colors ${password.length >= 8 ? 'text-emerald-400 font-medium' : ''}`}>
                                {password.length >= 8 ? <Check className="w-3 h-3" /> : <Dot className="w-3 h-3" />} 8+ chars
                              </span>
                              <span className={`flex items-center gap-1 transition-colors ${/[A-Z]/.test(password) ? 'text-emerald-400 font-medium' : ''}`}>
                                {/[A-Z]/.test(password) ? <Check className="w-3 h-3" /> : <Dot className="w-3 h-3" />} Uppercase
                              </span>
                              <span className={`flex items-center gap-1 transition-colors ${/[0-9]/.test(password) ? 'text-emerald-400 font-medium' : ''}`}>
                                {/[0-9]/.test(password) ? <Check className="w-3 h-3" /> : <Dot className="w-3 h-3" />} Number
                              </span>
                              <span className={`flex items-center gap-1 transition-colors ${/[^A-Za-z0-9]/.test(password) ? 'text-emerald-400 font-medium' : ''}`}>
                                {/[^A-Za-z0-9]/.test(password) ? <Check className="w-3 h-3" /> : <Dot className="w-3 h-3" />} Symbol
                              </span>
                            </div>
                          </motion.div>
                        </AnimatePresence>
                      )}

                      {confirmPassword && (
                        <div className="flex items-center gap-1.5">
                          {passwordsMatch ? (
                            <>
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                              <span className="text-xs text-emerald-400 font-medium">Passwords match</span>
                            </>
                          ) : (
                            <>
                              <XCircle className="w-3.5 h-3.5 text-rose-400 shrink-0" />
                              <span className="text-xs text-rose-400 font-medium">Passwords do not match</span>
                            </>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </>
              ) : (
                <div className="rounded-xl bg-slate-950/60 border border-slate-800/80 p-3.5 flex items-center justify-between text-xs text-slate-400">
                  <div className="flex items-center gap-2">
                    <Lock className="w-4 h-4 text-emerald-400/80" />
                    <span>Password secured via active DeadlineOS session</span>
                  </div>
                  <span className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider">Connected</span>
                </div>
              )}

              <div className="pt-3">
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full flex justify-center items-center gap-2 py-3 px-4 rounded-xl shadow-lg shadow-emerald-500/20 text-sm font-bold text-slate-950 bg-gradient-to-r from-emerald-400 via-teal-300 to-emerald-400 hover:from-emerald-300 hover:to-teal-200 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 focus:ring-offset-slate-900 transition-all cursor-pointer active:scale-[0.99] group"
                >
                  {loading ? (
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                      <span>{user ? 'Proceeding to Workspace Setup...' : 'Creating Administrator Account...'}</span>
                    </div>
                  ) : (
                    <>
                      <span>Continue to Workspace Setup</span>
                      <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                    </>
                  )}
                </button>
              </div>
            </form>
          )}

          {/* STEP 2: Workspace Setup */}
          {step === 'workspace' && (
            <form className="space-y-4" onSubmit={handleWorkspaceSubmit} noValidate>
              <div>
                <label htmlFor="ws-name" className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                  Company / Organization Name *
                </label>
                <div className="relative rounded-xl shadow-sm group">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500 group-focus-within:text-emerald-400 transition-colors">
                    <Building2 className="h-4.5 w-4.5" />
                  </div>
                  <input
                    id="ws-name"
                    type="text"
                    required
                    value={workspaceName}
                    onChange={(e) => setWorkspaceName(e.target.value)}
                    placeholder="Starlight Ventures Ltd"
                    className="block w-full pl-10 pr-3.5 py-3 bg-slate-950/70 border border-slate-700/80 rounded-xl text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all shadow-inner"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="legal-name" className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                    Legal Entity Name <span className="text-slate-500 font-normal">(Optional)</span>
                  </label>
                  <div className="relative rounded-xl shadow-sm group">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500 group-focus-within:text-emerald-400 transition-colors">
                      <FileText className="h-4.5 w-4.5" />
                    </div>
                    <input
                      id="legal-name"
                      type="text"
                      value={legalName}
                      onChange={(e) => setLegalName(e.target.value)}
                      placeholder="Starlight Ventures Pvt Ltd"
                      className="block w-full pl-10 pr-3.5 py-3 bg-slate-950/70 border border-slate-700/80 rounded-xl text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all shadow-inner"
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="tax-id" className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                    Tax ID / GSTIN / EIN <span className="text-slate-500 font-normal">(Optional)</span>
                  </label>
                  <input
                    id="tax-id"
                    type="text"
                    value={taxIdentifier}
                    onChange={(e) => setTaxIdentifier(e.target.value)}
                    placeholder="29AAAAA0000A1Z5"
                    className="block w-full px-3.5 py-3 bg-slate-950/70 border border-slate-700/80 rounded-xl text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all shadow-inner"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="base-currency" className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                    Base Currency
                  </label>
                  <div className="relative rounded-xl shadow-sm group">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500 group-focus-within:text-emerald-400 transition-colors">
                      <DollarSign className="h-4.5 w-4.5" />
                    </div>
                    <select
                      id="base-currency"
                      value={baseCurrency}
                      onChange={(e) => setBaseCurrency(e.target.value)}
                      style={{ colorScheme: 'dark' }}
                      className="block w-full pl-10 pr-10 py-3 bg-slate-950/70 border border-slate-700/80 rounded-xl text-slate-100 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 hover:border-slate-600 transition-all shadow-inner appearance-none cursor-pointer"
                    >
                      <option value="INR" className="bg-slate-900 text-slate-100 py-1.5">INR (₹) - Indian Rupee</option>
                      <option value="USD" className="bg-slate-900 text-slate-100 py-1.5">USD ($) - US Dollar</option>
                      <option value="EUR" className="bg-slate-900 text-slate-100 py-1.5">EUR (€) - Euro</option>
                      <option value="GBP" className="bg-slate-900 text-slate-100 py-1.5">GBP (£) - British Pound</option>
                    </select>
                    <div className="absolute inset-y-0 right-0 pr-3.5 flex items-center pointer-events-none text-slate-400 group-focus-within:text-emerald-400 transition-colors">
                      <ChevronDown className="h-4 w-4" />
                    </div>
                  </div>
                </div>

                <div>
                  <label htmlFor="ws-timezone" className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                    Operating Timezone
                  </label>
                  <div className="relative rounded-xl shadow-sm group">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500 group-focus-within:text-emerald-400 transition-colors">
                      <Globe className="h-4.5 w-4.5" />
                    </div>
                    <select
                      id="ws-timezone"
                      value={timezone}
                      onChange={(e) => setTimezone(e.target.value)}
                      style={{ colorScheme: 'dark' }}
                      className="block w-full pl-10 pr-10 py-3 bg-slate-950/70 border border-slate-700/80 rounded-xl text-slate-100 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 hover:border-slate-600 transition-all shadow-inner appearance-none cursor-pointer"
                    >
                      <option value="Asia/Kolkata" className="bg-slate-900 text-slate-100 py-1.5">Asia/Kolkata (IST)</option>
                      <option value="America/New_York" className="bg-slate-900 text-slate-100 py-1.5">America/New_York (EST)</option>
                      <option value="America/Los_Angeles" className="bg-slate-900 text-slate-100 py-1.5">America/Los_Angeles (PST)</option>
                      <option value="Europe/London" className="bg-slate-900 text-slate-100 py-1.5">Europe/London (GMT)</option>
                      <option value="Europe/Berlin" className="bg-slate-900 text-slate-100 py-1.5">Europe/Berlin (CET)</option>
                      <option value="Asia/Singapore" className="bg-slate-900 text-slate-100 py-1.5">Asia/Singapore (SGT)</option>
                      <option value="Asia/Dubai" className="bg-slate-900 text-slate-100 py-1.5">Asia/Dubai (GST)</option>
                    </select>
                    <div className="absolute inset-y-0 right-0 pr-3.5 flex items-center pointer-events-none text-slate-400 group-focus-within:text-emerald-400 transition-colors">
                      <ChevronDown className="h-4 w-4" />
                    </div>
                  </div>
                </div>
              </div>

              <div className="pt-3 space-y-2">
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full flex justify-center items-center gap-2 py-3 px-4 rounded-xl shadow-lg shadow-emerald-500/20 text-sm font-bold text-slate-950 bg-gradient-to-r from-emerald-400 via-teal-300 to-emerald-400 hover:from-emerald-300 hover:to-teal-200 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 focus:ring-offset-slate-900 transition-all cursor-pointer active:scale-[0.99] group"
                >
                  {loading ? (
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                      <span>Provisioning Organization & Ledger...</span>
                    </div>
                  ) : (
                    <>
                      <span>Launch Business Workspace</span>
                      <Sparkles className="w-4 h-4 group-hover:rotate-12 transition-transform" />
                    </>
                  )}
                </button>

                <button
                  type="button"
                  onClick={() => setStep('account')}
                  disabled={loading}
                  className="w-full flex justify-center items-center gap-1.5 py-2 px-4 text-xs font-semibold text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
                >
                  <ArrowLeft className="w-3.5 h-3.5" /> Back to Account Details
                </button>
              </div>
            </form>
          )}

          {/* STEP 3: Verification Notice */}
          {step === 'verification' && (
            <div className="text-center py-6 space-y-4">
              <div className="w-14 h-14 rounded-2xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center mx-auto border border-emerald-500/20 shadow-inner">
                <CheckCircle2 className="w-7 h-7" />
              </div>
              <h3 className="text-xl font-bold text-white">Check Your Work Inbox</h3>
              <p className="text-sm text-slate-400 leading-relaxed max-w-sm mx-auto">
                We've sent an activation link to <span className="text-slate-100 font-semibold">{email}</span>. Please click the link to confirm your administrator credentials and launch workspace setup.
              </p>
              <div className="pt-3">
                <Link
                  to="/business/login"
                  className="inline-flex items-center gap-2 text-sm font-semibold text-emerald-400 hover:text-emerald-300 transition-colors"
                >
                  <ArrowLeft className="w-4 h-4" /> Return to Enterprise Sign In
                </Link>
              </div>
            </div>
          )}

          {/* Divider & Navigation Links */}
          <div className="mt-6 pt-5 border-t border-slate-800/80 text-center space-y-2.5">
            <p className="text-xs text-slate-400">
              Already have an organization?{' '}
              <Link to="/business/login" className="font-semibold text-emerald-400 hover:text-emerald-300 transition-colors">
                Sign In to Business OS
              </Link>
            </p>
            <p className="text-xs text-slate-500">
              Looking for individual productivity?{' '}
              <Link to="/register" className="font-semibold text-indigo-400 hover:text-indigo-300 transition-colors">
                Register Personal Account
              </Link>
            </p>
          </div>
        </div>

        {/* Assurance */}
        <div className="mt-6 flex items-center justify-center gap-2 text-xs text-slate-500">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400/80" />
          <span>Atomic transactional onboarding • Automatic OWNER provisioning</span>
        </div>
      </motion.div>
    </div>
  );
};
