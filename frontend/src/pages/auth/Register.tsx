import React, { useState } from 'react';
import { usePageMeta } from '../../hooks/usePageMeta';
import { useNavigate, Link } from 'react-router-dom';
import { supabase } from '../../lib/supabase';
import { Lock, Mail, ArrowRight, UserPlus, Eye, EyeOff, CheckCircle2, XCircle, Sparkles, ShieldCheck, Check, Dot } from 'lucide-react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';

export const Register: React.FC = () => {
  usePageMeta('Register');
  const shouldReduceMotion = useReducedMotion();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 5-tier password strength model (0=Empty, 1=Weak, 2=Fair, 3=Strong, 4=Very Strong)
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
  const navigate = useNavigate();

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }
    
    const { error } = await supabase.auth.signUp({
      email,
      password,
    });

    if (error) {
      setError(error.message);
      setLoading(false);
    } else {
      navigate('/dashboard');
    }
  };

  return (
    <div className="min-h-screen bg-[#020617] flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden selection:bg-purple-500/30 font-sans [perspective:1200px]">
      {/* Ambient Depth Gradients */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[520px] bg-gradient-to-tr from-purple-600/18 via-indigo-600/12 to-transparent rounded-full blur-[150px] pointer-events-none transform-gpu" />
      <div className="absolute bottom-10 right-1/4 w-[450px] h-[450px] bg-purple-500/8 rounded-full blur-[130px] pointer-events-none transform-gpu" />
      <div className="absolute top-10 right-10 w-[320px] h-[320px] bg-indigo-500/8 rounded-full blur-[110px] pointer-events-none transform-gpu" />

      {/* Subtle Structural Grid Overlay */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#3341550a_1px,transparent_1px),linear-gradient(to_bottom,#3341550a_1px,transparent_1px)] bg-[size:3.5rem_3.5rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_40%,#000_70%,transparent_100%)] pointer-events-none" />

      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10">
        {/* Mode Badge & Brand Anchor */}
        <motion.div
          initial={shouldReduceMotion ? false : { opacity: 0, y: -16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="flex flex-col items-center mb-6"
        >
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-gradient-to-r from-purple-500/10 via-indigo-500/10 to-purple-500/10 border border-purple-500/25 text-purple-300 text-xs font-semibold tracking-wider uppercase backdrop-blur-md shadow-inner shadow-purple-500/10">
            <Sparkles className="w-3.5 h-3.5 text-purple-400" />
            <span>Personal OS • Account Creation</span>
          </div>

          <div className="mt-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-purple-500 to-indigo-600 p-[1px] shadow-lg shadow-purple-500/25 flex items-center justify-center">
              <div className="w-full h-full bg-slate-950 rounded-[15px] flex items-center justify-center shadow-inner">
                <UserPlus className="w-5 h-5 text-purple-400" />
              </div>
            </div>
            <div className="text-left">
              <span className="text-xl font-extrabold tracking-tight text-white">Deadline<span className="text-purple-400">OS</span></span>
            </div>
          </div>
        </motion.div>

        {/* Heading */}
        <motion.div
          initial={shouldReduceMotion ? false : { opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.08 }}
          className="text-center"
        >
          <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-white">
            Create Your Account
          </h1>
          <p className="mt-2 text-sm text-slate-400 leading-relaxed max-w-sm mx-auto">
            Take command of your deadlines with deterministic scheduling and intelligent focus
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
        <div className="bg-slate-900/70 backdrop-blur-2xl border border-slate-800/90 py-8 px-6 sm:px-10 shadow-[0_20px_60px_-15px_rgba(0,0,0,0.7),0_0_40px_rgba(168,85,247,0.08)] rounded-3xl relative overflow-hidden transition-all duration-300">
          {/* Top Specular Edge Highlight */}
          <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-purple-500/50 to-transparent" />

          <form className="space-y-4.5" onSubmit={handleRegister} noValidate>
            {/* Error Banner */}
            {error && (
              <motion.div
                initial={shouldReduceMotion ? false : { opacity: 0, y: -6 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-rose-500/10 border border-rose-500/25 text-rose-300 text-xs sm:text-sm p-3.5 rounded-xl flex items-start gap-2.5 shadow-sm"
                role="alert"
              >
                <div className="w-4 h-4 rounded-full bg-rose-500/20 text-rose-400 flex items-center justify-center shrink-0 mt-0.5 font-bold text-[11px]">!</div>
                <span className="leading-snug">{error}</span>
              </motion.div>
            )}

            {/* Email Field */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                Email Address
              </label>
              <div className="relative rounded-xl shadow-sm group">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500 group-focus-within:text-purple-400 transition-colors">
                  <Mail className="h-4.5 w-4.5" />
                </div>
                <input
                  type="email"
                  required
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="block w-full pl-10 pr-3.5 py-3 border border-slate-700/80 rounded-xl bg-slate-950/70 text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500 transition-all shadow-inner"
                  placeholder="you@example.com"
                />
              </div>
            </div>

            {/* Password Field with Independent Toggle & Strength */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
                  Password
                </label>
              </div>
              <div className="relative rounded-xl shadow-sm group">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500 group-focus-within:text-purple-400 transition-colors">
                  <Lock className="h-4.5 w-4.5" />
                </div>
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  autoComplete="new-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="block w-full pl-10 pr-11 py-3 border border-slate-700/80 rounded-xl bg-slate-950/70 text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500 transition-all shadow-inner"
                  placeholder="••••••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-200 transition-colors focus:outline-none focus:text-purple-400"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                  title={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="h-4.5 w-4.5" /> : <Eye className="h-4.5 w-4.5" />}
                </button>
              </div>

              {/* Password Strength Indicator (Compact & Animated) */}
              <AnimatePresence mode="wait">
                {password && (
                  <motion.div
                    initial={shouldReduceMotion ? false : { opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="mt-2.5 space-y-1.5 overflow-hidden"
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
                )}
              </AnimatePresence>
            </div>

            {/* Confirm Password Field with Independent Toggle */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                Confirm Password
              </label>
              <div className="relative rounded-xl shadow-sm group">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500 group-focus-within:text-purple-400 transition-colors">
                  <Lock className="h-4.5 w-4.5" />
                </div>
                <input
                  type={showConfirmPassword ? 'text' : 'password'}
                  required
                  autoComplete="new-password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className={`block w-full pl-10 pr-11 py-3 border rounded-xl bg-slate-950/70 text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all shadow-inner ${
                    passwordsMatch === false ? 'border-rose-500/80 focus:border-rose-500' : passwordsMatch === true ? 'border-emerald-500/80 focus:border-emerald-500' : 'border-slate-700/80 focus:border-purple-500'
                  }`}
                  placeholder="••••••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-200 transition-colors focus:outline-none focus:text-purple-400"
                  aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
                  title={showConfirmPassword ? 'Hide password' : 'Show password'}
                >
                  {showConfirmPassword ? <EyeOff className="h-4.5 w-4.5" /> : <Eye className="h-4.5 w-4.5" />}
                </button>
              </div>

              {/* Password Match Status Pill */}
              {confirmPassword && (
                <div className="mt-2 flex items-center gap-1.5">
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

            {/* Submit CTA */}
            <div className="pt-2">
              <button
                type="submit"
                disabled={loading}
                className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl shadow-lg shadow-purple-600/25 text-sm font-bold text-white bg-gradient-to-r from-purple-600 via-purple-500 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 focus:ring-offset-slate-900 disabled:opacity-50 disabled:cursor-not-allowed transition-all active:scale-[0.99] cursor-pointer group"
              >
                {loading ? (
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>Creating Account...</span>
                  </div>
                ) : (
                  <>
                    <span>Create Personal Account</span>
                    <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                  </>
                )}
              </button>
            </div>
          </form>

          {/* Navigation Links */}
          <div className="mt-6 text-center space-y-2.5">
            <p className="text-xs text-slate-400">
              Already have an account?{' '}
              <Link to="/login" className="font-semibold text-purple-400 hover:text-purple-300 transition-colors">
                Sign in here
              </Link>
            </p>
            <p className="text-xs text-slate-500">
              Setting up a commercial organization?{' '}
              <Link to="/business/register" className="font-semibold text-emerald-400 hover:text-emerald-300 transition-colors">
                Register Business OS
              </Link>
            </p>
          </div>
        </div>

        {/* Privacy & Assurance */}
        <div className="mt-6 flex items-center justify-center gap-2 text-xs text-slate-500">
          <ShieldCheck className="w-3.5 h-3.5 text-purple-400/80" />
          <span>Encrypted account credentials • Instant onboarding</span>
        </div>
      </motion.div>
    </div>
  );
};
