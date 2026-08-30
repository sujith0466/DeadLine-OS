import React, { useState } from 'react';
import { usePageMeta } from '../../hooks/usePageMeta';
import { useNavigate, Link } from 'react-router-dom';
import { supabase } from '../../lib/supabase';
import { Lock, Mail, ArrowRight, ShieldCheck, Zap, Eye, EyeOff, Sparkles, CheckCircle2 } from 'lucide-react';
import { motion, useReducedMotion } from 'framer-motion';
import { useAuth } from '../../context/AuthContext';
import { useDemoLogin } from '../../hooks/useDemoLogin';

export const Login: React.FC = () => {
  usePageMeta('Login');
  const shouldReduceMotion = useReducedMotion();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const navigate = useNavigate();
  const { user } = useAuth();
  const { handleDemoLogin, loading: demoLoading, error: demoError } = useDemoLogin();
  const isLoading = loading || demoLoading;
  const displayError = error || demoError;

  React.useEffect(() => {
    if (user) {
      navigate('/dashboard');
    }
  }, [user, navigate]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    const { error } = await supabase.auth.signInWithPassword({
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
    <div className="min-h-screen bg-[#020617] flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden selection:bg-indigo-500/30 font-sans [perspective:1200px]">
      {/* Layered 3D Ambient Lighting */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[520px] bg-gradient-to-tr from-indigo-600/18 via-violet-600/12 to-transparent rounded-full blur-[150px] pointer-events-none transform-gpu" />
      <div className="absolute bottom-10 right-1/4 w-[450px] h-[450px] bg-indigo-500/8 rounded-full blur-[130px] pointer-events-none transform-gpu" />
      <div className="absolute top-10 left-10 w-[320px] h-[320px] bg-purple-500/8 rounded-full blur-[110px] pointer-events-none transform-gpu" />

      {/* Subtle Precision Structural Grid */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#3341550a_1px,transparent_1px),linear-gradient(to_bottom,#3341550a_1px,transparent_1px)] bg-[size:3.5rem_3.5rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_40%,#000_70%,transparent_100%)] pointer-events-none" />

      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10">
        {/* Mode Badge & Brand Anchor */}
        <motion.div
          initial={shouldReduceMotion ? false : { opacity: 0, y: -16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="flex flex-col items-center mb-6"
        >
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-gradient-to-r from-indigo-500/10 via-purple-500/10 to-indigo-500/10 border border-indigo-500/25 text-indigo-300 text-xs font-semibold tracking-wider uppercase backdrop-blur-md shadow-inner shadow-indigo-500/10">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            <span>Personal OS • Individual Portal</span>
          </div>

          <div className="mt-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 p-[1px] shadow-lg shadow-indigo-500/25 flex items-center justify-center">
              <div className="w-full h-full bg-slate-950 rounded-[15px] flex items-center justify-center shadow-inner">
                <ShieldCheck className="w-5 h-5 text-indigo-400" />
              </div>
            </div>
            <div className="text-left">
              <span className="text-xl font-extrabold tracking-tight text-white">Deadline<span className="text-indigo-400">OS</span></span>
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
            Welcome Back
          </h1>
          <p className="mt-2 text-sm text-slate-400 leading-relaxed max-w-sm mx-auto">
            Sign in to access your deterministic personal dashboard and circadian focus stream
          </p>
        </motion.div>
      </div>

      {/* Main Form Card with Realistic 3D Depth */}
      <motion.div
        initial={shouldReduceMotion ? false : { opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        whileHover={shouldReduceMotion ? undefined : { y: -2, transition: { duration: 0.2 } }}
        transition={{ duration: 0.45, delay: 0.14 }}
        className="mt-8 sm:mx-auto sm:w-full sm:max-w-md relative z-10"
      >
        <div className="bg-slate-900/70 backdrop-blur-2xl border border-slate-800/90 py-8 px-6 sm:px-10 shadow-[0_20px_60px_-15px_rgba(0,0,0,0.7),0_0_40px_rgba(99,102,241,0.08)] rounded-3xl relative overflow-hidden transition-all duration-300">
          {/* Top Specular Edge Highlight */}
          <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-indigo-500/50 to-transparent" />

          <form className="space-y-4.5" onSubmit={handleLogin} noValidate>
            {/* Error Banner */}
            {displayError && (
              <motion.div
                initial={shouldReduceMotion ? false : { opacity: 0, y: -6 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-rose-500/10 border border-rose-500/25 text-rose-300 text-xs sm:text-sm p-3.5 rounded-xl flex items-start gap-2.5 shadow-sm"
                role="alert"
              >
                <div className="w-4 h-4 rounded-full bg-rose-500/20 text-rose-400 flex items-center justify-center shrink-0 mt-0.5 font-bold text-[11px]">!</div>
                <span className="leading-snug">{displayError}</span>
              </motion.div>
            )}

            {/* Email Field */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                Email Address
              </label>
              <div className="relative rounded-xl shadow-sm group">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500 group-focus-within:text-indigo-400 transition-colors">
                  <Mail className="h-4.5 w-4.5" />
                </div>
                <input
                  type="email"
                  required
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="block w-full pl-10 pr-3.5 py-3 border border-slate-700/80 rounded-xl bg-slate-950/70 text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all shadow-inner"
                  placeholder="you@example.com"
                />
              </div>
            </div>

            {/* Password Field with Eye Toggle */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
                  Password
                </label>
              </div>
              <div className="relative rounded-xl shadow-sm group">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500 group-focus-within:text-indigo-400 transition-colors">
                  <Lock className="h-4.5 w-4.5" />
                </div>
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="block w-full pl-10 pr-11 py-3 border border-slate-700/80 rounded-xl bg-slate-950/70 text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all shadow-inner"
                  placeholder="••••••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-200 transition-colors focus:outline-none focus:text-indigo-400"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                  title={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="h-4.5 w-4.5" /> : <Eye className="h-4.5 w-4.5" />}
                </button>
              </div>
            </div>

            {/* Submit CTA */}
            <div className="pt-2">
              <button
                type="submit"
                disabled={isLoading}
                className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl shadow-lg shadow-indigo-600/25 text-sm font-bold text-white bg-gradient-to-r from-indigo-600 via-indigo-500 to-purple-600 hover:from-indigo-500 hover:to-purple-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 focus:ring-offset-slate-900 disabled:opacity-50 disabled:cursor-not-allowed transition-all active:scale-[0.99] cursor-pointer group"
              >
                {loading ? (
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>Authenticating Personal OS...</span>
                  </div>
                ) : (
                  <>
                    <span>Sign In to Personal OS</span>
                    <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                  </>
                )}
              </button>
            </div>
          </form>

          {/* Demo Account Quick Access */}
          <div className="mt-6 pt-5 border-t border-slate-800/80">
            <button
              onClick={handleDemoLogin}
              type="button"
              disabled={isLoading}
              className="w-full flex items-center justify-center gap-2 py-2.5 px-4 border border-slate-700/80 rounded-xl shadow-sm text-xs sm:text-sm font-semibold text-slate-200 bg-slate-800/70 hover:bg-slate-750 hover:border-slate-600 focus:outline-none focus:ring-2 focus:ring-slate-500 focus:ring-offset-slate-900 transition-all disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer active:scale-[0.99]"
            >
              <Zap className="w-4 h-4 text-amber-400 shrink-0" />
              <span>{demoLoading ? 'Launching Demo Session...' : 'Instant Explore (Demo Account)'}</span>
            </button>
          </div>

          {/* Navigation Links */}
          <div className="mt-6 text-center space-y-2.5">
            <p className="text-xs text-slate-400">
              Don't have an account?{' '}
              <Link to="/register" className="font-semibold text-indigo-400 hover:text-indigo-300 transition-colors">
                Create Personal Account
              </Link>
            </p>
            <p className="text-xs text-slate-500">
              Need commercial workspace access?{' '}
              <Link to="/business/login" className="font-semibold text-emerald-400 hover:text-emerald-300 transition-colors">
                Switch to Business OS
              </Link>
            </p>
          </div>
        </div>

        {/* Privacy & Assurance */}
        <div className="mt-6 flex items-center justify-center gap-2 text-xs text-slate-500">
          <CheckCircle2 className="w-3.5 h-3.5 text-indigo-400/80" />
          <span>Local-first privacy • Cryptographically verified session</span>
        </div>
      </motion.div>
    </div>
  );
};
