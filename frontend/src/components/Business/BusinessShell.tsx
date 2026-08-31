import React, { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { motion, useReducedMotion } from 'framer-motion';
import { BusinessHeader } from './BusinessHeader';
import { CaptureModal } from './CaptureModal';
import { BusinessCopilotModal } from './BusinessCopilotModal';
import { AccountantExportModal } from './AccountantExportModal';

export interface BusinessShellProps {
  children?: React.ReactNode;
}

export const BusinessShell: React.FC<BusinessShellProps> = ({ children }) => {
  const shouldReduceMotion = useReducedMotion();

  const [isCaptureOpen, setIsCaptureOpen] = useState(false);
  const [isCopilotOpen, setIsCopilotOpen] = useState(false);
  const [isExportOpen, setIsExportOpen] = useState(false);

  // Global Keyboard Shortcuts (Cmd+K / Ctrl+K for Copilot, Cmd+B / Ctrl+B for Capture)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setIsCopilotOpen(prev => !prev);
      }
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'b' && !e.shiftKey) {
        e.preventDefault();
        setIsCaptureOpen(prev => !prev);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <div className="min-h-screen bg-[#030712] text-slate-100 flex flex-col relative overflow-x-hidden font-sans selection:bg-emerald-500/30 selection:text-emerald-200">
      {/* Enterprise Ambient Lighting & Glows */}
      <div className="fixed top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[350px] bg-gradient-to-b from-emerald-500/10 via-teal-500/5 to-transparent rounded-full blur-[140px] pointer-events-none transform-gpu z-0" />
      <div className="fixed bottom-0 right-10 w-[500px] h-[500px] bg-emerald-500/5 rounded-full blur-[150px] pointer-events-none transform-gpu z-0" />

      {/* Enterprise Precision Hairline Grid */}
      <div className="fixed inset-0 bg-[linear-gradient(to_right,#10b98105_1px,transparent_1px),linear-gradient(to_bottom,#10b98105_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_75%_65%_at_50%_35%,#000_70%,transparent_100%)] pointer-events-none z-0" />

      {/* Persistent Executive Header */}
      <BusinessHeader
        onOpenCopilot={() => setIsCopilotOpen(true)}
        onOpenExport={() => setIsExportOpen(true)}
      />

      {/* Main Full-Width Executive Content Surface */}
      <motion.main
        initial={shouldReduceMotion ? false : { opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25, ease: 'easeOut' }}
        className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 relative z-10"
      >
        {children || <Outlet />}
      </motion.main>

      {/* Global Business OS Modals */}
      <CaptureModal
        isOpen={isCaptureOpen}
        onClose={() => setIsCaptureOpen(false)}
        onSuccess={() => {
          setIsCaptureOpen(false);
          window.dispatchEvent(new CustomEvent('deadline_staging_updated'));
        }}
      />

      <BusinessCopilotModal
        isOpen={isCopilotOpen}
        onClose={() => setIsCopilotOpen(false)}
      />

      <AccountantExportModal
        isOpen={isExportOpen}
        onClose={() => setIsExportOpen(false)}
      />
    </div>
  );
};
