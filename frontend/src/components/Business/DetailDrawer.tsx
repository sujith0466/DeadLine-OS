import React, { useEffect, useRef } from 'react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import { X } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { StatusBadge } from './StatusBadge';
import type { BusinessStatusType } from './StatusBadge';

export interface DetailDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  status?: BusinessStatusType;
  icon?: LucideIcon;
  width?: 'sm' | 'md' | 'lg' | 'xl';
  children: React.ReactNode;
  footer?: React.ReactNode;
  className?: string;
}

export const DetailDrawer: React.FC<DetailDrawerProps> = ({
  isOpen,
  onClose,
  title,
  subtitle,
  status,
  icon: Icon,
  width = 'md',
  children,
  footer,
  className = '',
}) => {
  const shouldReduceMotion = useReducedMotion();
  const drawerRef = useRef<HTMLDivElement>(null);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  const widthClasses = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-3xl',
  }[width];

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 overflow-hidden">
          {/* Backdrop Blur & Overlay */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={onClose}
            aria-hidden="true"
            className="fixed inset-0 bg-black/70 backdrop-blur-sm"
          />

          <div className="fixed inset-y-0 right-0 max-w-full flex pl-0 sm:pl-10">
            {/* Drawer Surface */}
            <motion.div
              ref={drawerRef}
              role="dialog"
              aria-modal="true"
              aria-labelledby="drawer-title"
              tabIndex={-1}
              initial={shouldReduceMotion ? undefined : { x: '100%' }}
              animate={{ x: 0 }}
              exit={shouldReduceMotion ? undefined : { x: '100%' }}
              transition={{ type: 'spring', damping: 30, stiffness: 300 }}
              className={`w-screen ${widthClasses} bg-[#0B0F19] border-l border-slate-800 shadow-2xl shadow-black flex flex-col justify-between overflow-hidden outline-none ${className}`}
            >
              {/* Drawer Header */}
              <div className="px-6 py-5 border-b border-slate-800/80 bg-slate-900/40 flex items-start justify-between gap-4">
                <div className="flex items-start gap-3">
                  {Icon && (
                    <div className="p-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 mt-0.5">
                      <Icon className="w-5 h-5" />
                    </div>
                  )}
                  <div>
                    <div className="flex items-center gap-2.5 flex-wrap">
                      <h2
                        id="drawer-title"
                        className="text-lg font-bold text-slate-100 tracking-tight"
                      >
                        {title}
                      </h2>
                      {status && <StatusBadge status={status} size="sm" />}
                    </div>
                    {subtitle && (
                      <p className="text-xs text-slate-400 mt-0.5 leading-relaxed">
                        {subtitle}
                      </p>
                    )}
                  </div>
                </div>

                <button
                  onClick={onClose}
                  aria-label="Close drawer"
                  className="p-1.5 rounded-xl bg-slate-800/60 hover:bg-slate-800 text-slate-400 hover:text-white transition-colors flex-shrink-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/50"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Drawer Body */}
              <div className="flex-1 overflow-y-auto p-6 space-y-6 text-sm text-slate-300">
                {children}
              </div>

              {/* Drawer Footer Actions */}
              {footer && (
                <div className="px-6 py-4 border-t border-slate-800/80 bg-slate-900/40 flex items-center justify-end gap-3 flex-shrink-0">
                  {footer}
                </div>
              )}
            </motion.div>
          </div>
        </div>
      )}
    </AnimatePresence>
  );
};
