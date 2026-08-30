import React from 'react';
import { motion } from 'framer-motion';
import { User, Building2 } from 'lucide-react';

export type ProductMode = 'personal' | 'business';

interface ProductModeSwitcherProps {
  activeMode: ProductMode;
  onModeChange: (mode: ProductMode) => void;
}

export const ProductModeSwitcher: React.FC<ProductModeSwitcherProps> = ({
  activeMode,
  onModeChange,
}) => {
  const modes: { id: ProductMode; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
    { id: 'personal', label: 'Personal', icon: User },
    { id: 'business', label: 'Business', icon: Building2 },
  ];

  const handleKeyDown = (e: React.KeyboardEvent, index: number) => {
    if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
      e.preventDefault();
      const nextIndex = index === 0 ? 1 : 0;
      onModeChange(modes[nextIndex].id);
    }
  };

  return (
    <div className="flex justify-center mb-8 w-full">
      <div
        role="tablist"
        aria-label="Product operating mode selection"
        className="relative inline-flex items-center p-1 rounded-full bg-slate-900/90 border border-white/10 shadow-2xl backdrop-blur-xl transition-all hover:border-white/20"
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
              className={`relative z-10 flex items-center gap-2 px-6 py-2.5 text-xs md:text-sm font-semibold rounded-full transition-colors duration-200 outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 ${
                isSelected ? 'text-slate-950 font-bold' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {isSelected && (
                <motion.div
                  layoutId="active-product-mode-pill"
                  transition={{ type: 'spring', stiffness: 500, damping: 35 }}
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
