import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { User, Building2 } from 'lucide-react';

export type ProductMode = 'personal' | 'business';

interface ProductModeSwitcherProps {
  activeMode: ProductMode;
  onModeChange: (mode: ProductMode) => void;
  variant?: 'hero' | 'floating';
  className?: string;
  id?: string;
}

export const ProductModeSwitcher: React.FC<ProductModeSwitcherProps> = ({
  activeMode,
  onModeChange,
  variant = 'hero',
  className = '',
  id,
}) => {
  const isFloating = variant === 'floating';
  const shouldReduceMotion = useReducedMotion();

  const modes: { id: ProductMode; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
    { id: 'personal', label: 'Personal', icon: User },
    { id: 'business', label: 'Business', icon: Building2 },
  ];

  const handleKeyDown = (e: React.KeyboardEvent, index: number) => {
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown' || e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
      e.preventDefault();
      const nextIndex = index === 0 ? 1 : 0;
      onModeChange(modes[nextIndex].id);
    }
  };

  if (isFloating) {
    return (
      <div className={`flex flex-col items-center ${className}`}>
        <div
          id={id}
          role="tablist"
          aria-label="Operating Environment"
          aria-orientation="vertical"
          className="relative flex flex-col p-1 rounded-2xl bg-[#0D0F14]/95 border border-white/15 shadow-[0_8px_32px_rgba(0,0,0,0.6)] backdrop-blur-2xl transition-all hover:border-white/25"
        >
          {modes.map((mode, index) => {
            const isSelected = activeMode === mode.id;
            const Icon = mode.icon;

            return (
              <button
                key={mode.id}
                role="tab"
                id={`tab-floating-${mode.id}`}
                aria-controls={`panel-${mode.id}`}
                aria-selected={isSelected}
                tabIndex={isSelected ? 0 : -1}
                onClick={() => onModeChange(mode.id)}
                onKeyDown={(e) => handleKeyDown(e, index)}
                title={`Switch to ${mode.label} OS`}
                aria-label={`Switch to ${mode.label} OS`}
                className={`relative z-10 flex flex-col sm:flex-row items-center justify-center gap-1 sm:gap-2 px-3 py-2.5 sm:px-4 sm:py-2 text-xs font-semibold rounded-xl transition-colors duration-200 outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 cursor-pointer ${
                  isSelected ? 'text-slate-950 font-bold' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {isSelected && (
                  <motion.div
                    layoutId="active-product-mode-pill-floating"
                    transition={shouldReduceMotion ? { duration: 0 } : { type: 'spring', stiffness: 500, damping: 35 }}
                    className="absolute inset-0 rounded-xl bg-white shadow-[0_2px_12px_rgba(255,255,255,0.3)]"
                  />
                )}
                <Icon className={`relative z-10 w-4 h-4 ${isSelected ? 'text-slate-950' : 'text-slate-400'}`} />
                <span className="relative z-10 text-[11px] sm:text-xs font-semibold">{mode.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    );
  }

  // Canonical Primary Hero Switcher (Horizontal)
  return (
    <div id={id} className={`flex justify-center mb-8 w-full ${className}`}>
      <div
        role="tablist"
        aria-label="Operating Environment"
        aria-orientation="horizontal"
        className="relative inline-flex items-center p-1 rounded-full bg-[#0D0F14]/90 border border-white/10 shadow-2xl backdrop-blur-xl transition-all hover:border-white/20"
      >
        {modes.map((mode, index) => {
          const isSelected = activeMode === mode.id;
          const Icon = mode.icon;

          return (
            <button
              key={mode.id}
              role="tab"
              id={`tab-${mode.id}`}
              aria-controls={`panel-${mode.id}`}
              aria-selected={isSelected}
              tabIndex={isSelected ? 0 : -1}
              onClick={() => onModeChange(mode.id)}
              onKeyDown={(e) => handleKeyDown(e, index)}
              className={`relative z-10 flex items-center gap-2 px-6 py-2 text-xs md:text-sm font-semibold rounded-full transition-colors duration-200 outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 cursor-pointer ${
                isSelected ? 'text-slate-950 font-bold' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {isSelected && (
                <motion.div
                  layoutId="active-product-mode-pill-hero"
                  transition={shouldReduceMotion ? { duration: 0 } : { type: 'spring', stiffness: 500, damping: 35 }}
                  className="absolute inset-0 rounded-full bg-white shadow-[0_2px_12px_rgba(255,255,255,0.25)]"
                />
              )}
              <span className="relative z-10 flex items-center gap-2">
                <Icon className={`w-3.5 h-3.5 md:w-4 md:h-4 ${isSelected ? 'text-slate-950' : 'text-slate-400'}`} />
                <span>{mode.label}</span>
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
