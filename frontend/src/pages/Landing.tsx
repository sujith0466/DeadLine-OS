import React, { useState, useEffect } from 'react';
import { useSearchParams, useLocation } from 'react-router-dom';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import { LandingNavigation } from '../components/Landing/LandingNavigation';
import { HeroSection } from '../components/Landing/HeroSection';
import { TrustedMetrics } from '../components/Landing/TrustedMetrics';
import { ProductShowcase } from '../components/Landing/ProductShowcase';
import { InteractiveWorkflow } from '../components/Landing/InteractiveWorkflow';
import { HowItThinks } from '../components/Landing/HowItThinks';
import { ModeSpecificShowcase } from '../components/Landing/ModeSpecificShowcase';
import { CustomerConfidenceSection } from '../components/Landing/CustomerConfidenceSection';
import { FAQSection } from '../components/Landing/FAQSection';
import { CTASection } from '../components/Landing/CTASection';
import { LandingFooter } from '../components/Landing/LandingFooter';
import { Background } from '../components/Landing/Background';
import { ProductModeSwitcher, type ProductMode } from '../components/Landing/ProductModeSwitcher';

const STORAGE_KEY = 'deadlineos-landing-mode';

export const Landing: React.FC = () => {
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const shouldReduceMotion = useReducedMotion();

  // Mode state with query parameter, location state, and localStorage persistence
  const [mode, setMode] = useState<ProductMode>(() => {
    const urlMode = searchParams.get('mode');
    if (urlMode === 'personal' || urlMode === 'business') {
      return urlMode;
    }
    const stateMode = (location.state as any)?.mode;
    if (stateMode === 'personal' || stateMode === 'business') {
      return stateMode;
    }
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved === 'personal' || saved === 'business') {
        return saved;
      }
    } catch {
      // In case localStorage is blocked or restricted
    }
    return 'personal';
  });

  // Track visibility of the primary hero switcher
  const [isPrimaryVisible, setIsPrimaryVisible] = useState(true);

  // Sync mode if query parameters or location state update
  useEffect(() => {
    const urlMode = searchParams.get('mode');
    if (urlMode === 'personal' || urlMode === 'business') {
      setMode(urlMode);
      try {
        localStorage.setItem(STORAGE_KEY, urlMode);
      } catch {}
    } else {
      const stateMode = (location.state as any)?.mode;
      if (stateMode === 'personal' || stateMode === 'business') {
        setMode(stateMode);
        try {
          localStorage.setItem(STORAGE_KEY, stateMode);
        } catch {}
      }
    }
  }, [searchParams, location.state]);

  const handleModeChange = (newMode: ProductMode) => {
    setMode(newMode);
    try {
      localStorage.setItem(STORAGE_KEY, newMode);
    } catch {
      // Ignore storage errors
    }
  };

  useEffect(() => {
    const primaryEl = document.getElementById('primary-mode-switcher');
    if (!primaryEl) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsPrimaryVisible(entry.isIntersecting);
      },
      {
        threshold: 0.05,
        rootMargin: '-30px 0px 0px 0px',
      }
    );

    observer.observe(primaryEl);

    return () => {
      observer.disconnect();
    };
  }, []);

  return (
    <div className="bg-[#020617] min-h-screen text-gray-50 font-sans selection:bg-indigo-500/30 relative">
      <Background />
      <LandingNavigation mode={mode} />

      <main>
        <HeroSection mode={mode} onModeChange={handleModeChange} />
        <TrustedMetrics mode={mode} />
        <ProductShowcase mode={mode} />
        <InteractiveWorkflow mode={mode} />
        <HowItThinks mode={mode} />
        <ModeSpecificShowcase mode={mode} />
        <CustomerConfidenceSection mode={mode} />
        <FAQSection mode={mode} />
        <CTASection mode={mode} />
      </main>

      {/* Floating Vertical Mode Switcher (Visible only when primary switcher is scrolled out of viewport) */}
      <AnimatePresence>
        {!isPrimaryVisible && (
          <motion.div
            initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, x: 20, scale: 0.94 }}
            animate={shouldReduceMotion ? { opacity: 1 } : { opacity: 1, x: 0, scale: 1 }}
            exit={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, x: 20, scale: 0.94 }}
            transition={shouldReduceMotion ? { duration: 0 } : { duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
            className="fixed right-3 sm:right-6 top-1/2 -translate-y-1/2 z-40"
          >
            <ProductModeSwitcher
              activeMode={mode}
              onModeChange={handleModeChange}
              variant="floating"
            />
          </motion.div>
        )}
      </AnimatePresence>

      <LandingFooter mode={mode} />
    </div>
  );
};
