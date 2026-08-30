import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ChevronRight, Play } from 'lucide-react';
import { useDemoLogin } from '../../hooks/useDemoLogin';
import { ProductModeSwitcher, type ProductMode } from './ProductModeSwitcher';
import { PersonalHeroVisual } from './PersonalHeroVisual';
import { BusinessHeroVisual } from './BusinessHeroVisual';
import { ImmersiveSpatial3D } from './ImmersiveSpatial3D';

interface HeroSectionProps {
  mode: ProductMode;
  onModeChange: (mode: ProductMode) => void;
}

export const HeroSection: React.FC<HeroSectionProps> = ({ mode, onModeChange }) => {
  const { handleDemoLogin, loading: demoLoading, error: demoError } = useDemoLogin();
  const isPersonal = mode === 'personal';

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden bg-[#0A0A0B] pt-24 pb-16">
      {/* 3D Immersive Spatial Geometry Background */}
      <ImmersiveSpatial3D mode={mode} />

      <div className="relative z-10 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col items-center text-center">
        
        {/* ChatGPT-Style Centered Product Mode Switcher Row */}
        <ProductModeSwitcher id="primary-mode-switcher" activeMode={mode} onModeChange={onModeChange} variant="hero" />

        {/* Dynamic Mode Headline & Subtitle */}
        <AnimatePresence mode="wait">
          <motion.div
            key={mode}
            id={`panel-${mode}`}
            role="tabpanel"
            aria-labelledby={`tab-${mode}`}
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -15 }}
            transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
            className="flex flex-col items-center text-center max-w-4xl"
          >
            {/* Headline */}
            <h1 className="text-5xl md:text-7xl lg:text-8xl font-black tracking-tighter text-white mb-6">
              Your AI-Powered <br className="hidden md:block" />
              <span
                className={`text-transparent bg-clip-text bg-gradient-to-r transition-all duration-500 ${
                  isPersonal
                    ? 'from-indigo-400 via-purple-400 to-pink-400'
                    : 'from-emerald-400 via-teal-300 to-cyan-400'
                }`}
              >
                {isPersonal ? 'Personal Operating System' : 'Business Operating System'}
              </span>
            </h1>

            {/* Subtitle */}
            <p className="max-w-2xl text-lg md:text-xl text-gray-400 mb-10 font-medium leading-relaxed">
              {isPersonal
                ? 'Transform chaos into momentum. DeadlineOS orchestrates your goals, habits, and deadlines through autonomous intelligence, digital twin simulations, and predictive recovery.'
                : 'Precision intelligence for commercial enterprise. DeadlineOS unifies deterministic cash risk, automated receivables rescue, recurring obligations, and multi-entity consolidation.'}
            </p>
          </motion.div>
        </AnimatePresence>

        {/* CTAs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
          className="flex flex-col sm:flex-row items-center gap-4 mb-16"
        >
          <Link
            to={isPersonal ? "/register" : "/business/register"}
            className="group flex items-center gap-2 px-8 py-4 bg-white text-gray-900 rounded-full font-bold text-lg hover:bg-gray-100 transition-all shadow-[0_0_40px_rgba(255,255,255,0.1)] hover:shadow-[0_0_60px_rgba(255,255,255,0.2)] hover:scale-105"
          >
            Get Started
            <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </Link>
          <button 
            onClick={handleDemoLogin}
            disabled={demoLoading}
            className="group flex items-center gap-2 px-8 py-4 bg-white/5 border border-white/10 text-white rounded-full font-bold text-lg backdrop-blur-xl hover:bg-white/10 transition-all disabled:opacity-60 disabled:cursor-not-allowed"
          >
            <Play className="w-5 h-5 fill-current opacity-80 group-hover:opacity-100 transition-opacity" />
            {demoLoading ? 'Launching...' : 'Watch Demo'}
          </button>
        </motion.div>

        {/* Synchronized Hero Visual Dashboard Mockup */}
        <div className="w-full max-w-5xl relative">
          <AnimatePresence mode="wait">
            <motion.div
              key={mode}
              initial={{ opacity: 0, scale: 0.98, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.98, y: -20 }}
              transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
            >
              {isPersonal ? <PersonalHeroVisual /> : <BusinessHeroVisual />}
            </motion.div>
          </AnimatePresence>
        </div>

      </div>

      {/* Demo error toast */}
      <AnimatePresence>
        {demoError && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="fixed bottom-6 left-1/2 -translate-x-1/2 z-[100] bg-red-900/90 border border-red-500/30 text-red-300 text-sm font-medium px-6 py-3 rounded-2xl shadow-2xl backdrop-blur-xl max-w-md text-center"
          >
            {demoError}
          </motion.div>
        )}
      </AnimatePresence>
    </section>
  );
};
