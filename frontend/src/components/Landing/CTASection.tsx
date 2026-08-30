import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ChevronRight, Play } from 'lucide-react';
import { useDemoLogin } from '../../hooks/useDemoLogin';
import type { ProductMode } from './ProductModeSwitcher';

interface CTASectionProps {
  mode: ProductMode;
}

export const CTASection: React.FC<CTASectionProps> = ({ mode }) => {
  const { handleDemoLogin, loading: demoLoading } = useDemoLogin();
  const isPersonal = mode === 'personal';

  return (
    <section className="py-28 bg-[#0A0A0B] relative overflow-hidden border-t border-white/5">
      <div
        className={`absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full blur-[140px] pointer-events-none transition-colors duration-700 ${
          isPersonal ? 'bg-indigo-500/10' : 'bg-emerald-500/10'
        }`}
      />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center">
        <AnimatePresence mode="wait">
          <motion.div
            key={mode}
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -15 }}
            transition={{ duration: 0.35 }}
            className="max-w-3xl mx-auto"
          >
            <h2 className="text-4xl md:text-5xl lg:text-6xl font-black tracking-tight text-white mb-6">
              {isPersonal ? (
                <>
                  Build a system that moves your <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">life forward.</span>
                </>
              ) : (
                <>
                  Operate your enterprise with <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">clarity and control.</span>
                </>
              )}
            </h2>

            <p className="text-lg text-gray-400 mb-10 leading-relaxed font-medium">
              {isPersonal
                ? 'Join high-agency individuals using DeadlineOS to orchestrate goals, conquer daily deadlines, and eliminate burnout.'
                : 'Empower your organization with authoritative financial truth, automated collections, and multi-entity intelligence.'}
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                to="/register"
                className="w-full sm:w-auto flex items-center justify-center gap-2 px-8 py-4 bg-white text-gray-900 rounded-full font-bold text-lg hover:bg-gray-100 transition-all shadow-[0_0_40px_rgba(255,255,255,0.1)] hover:scale-105"
              >
                Get Started
                <ChevronRight className="w-5 h-5" />
              </Link>
              <button
                onClick={handleDemoLogin}
                disabled={demoLoading}
                className="w-full sm:w-auto flex items-center justify-center gap-2 px-8 py-4 bg-white/5 border border-white/10 text-white rounded-full font-bold text-lg backdrop-blur-xl hover:bg-white/10 transition-all disabled:opacity-60 cursor-pointer"
              >
                <Play className="w-5 h-5 fill-current opacity-80" />
                {demoLoading ? 'Launching...' : 'Watch Demo'}
              </button>
            </div>
          </motion.div>
        </AnimatePresence>
      </div>
    </section>
  );
};
