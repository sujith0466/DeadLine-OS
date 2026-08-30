import React, { useEffect, useRef } from 'react';
import { motion, useInView, useSpring, useTransform, useReducedMotion } from 'framer-motion';
import type { ProductMode } from './ProductModeSwitcher';

const AnimatedCounter: React.FC<{ value: number; duration?: number }> = ({ value, duration = 2 }) => {
  const shouldReduceMotion = useReducedMotion();
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, margin: '-80px' });
  const spring = useSpring(shouldReduceMotion ? value : 0, { duration: shouldReduceMotion ? 0 : duration * 1000, bounce: 0 });
  const displayValue = useTransform(spring, (current) => Math.floor(current).toLocaleString());

  useEffect(() => {
    if (shouldReduceMotion) {
      spring.set(value);
      return;
    }
    if (inView) {
      spring.set(value);
    }
  }, [inView, spring, value, shouldReduceMotion]);

  if (shouldReduceMotion) {
    return <span>{value.toLocaleString()}</span>;
  }

  return <motion.span ref={ref}>{displayValue}</motion.span>;
};

interface TrustedMetricsProps {
  mode: ProductMode;
}

export const TrustedMetrics: React.FC<TrustedMetricsProps> = ({ mode }) => {
  const isPersonal = mode === 'personal';

  const metrics = isPersonal
    ? [
        { label: 'Autonomous AI Modules', value: 8, suffix: '+' },
        { label: 'Coordinated Agents', value: 6, suffix: '' },
        { label: 'Twin Trajectories Simulated', value: 24500, suffix: '+' },
        { label: 'Goals & Habits Realized', value: 12000, suffix: '+' },
      ]
    : [
        { label: 'Operational Workflows', value: 100, suffix: '% Automated' },
        { label: 'Average Cash Runway Visibility', value: 94, suffix: ' Days' },
        { label: 'Receivable Collection Speed', value: 3, suffix: 'x Faster' },
        { label: 'Group Entities Consolidated', value: 100, suffix: '% Live' },
      ];

  return (
    <section className="py-20 bg-[#0A0A0B] relative border-t border-white/5">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {metrics.map((metric, idx) => (
            <motion.div
              key={`${mode}-${idx}`}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-60px' }}
              transition={{ duration: 0.5, delay: idx * 0.08 }}
              className="flex flex-col items-center justify-center p-6 rounded-2xl bg-white/[0.02] border border-white/5 backdrop-blur-sm transition-colors hover:border-white/10"
            >
              <div
                className={`text-3xl md:text-4xl lg:text-5xl font-black mb-2 text-transparent bg-clip-text bg-gradient-to-br ${
                  isPersonal ? 'from-indigo-400 to-purple-400' : 'from-emerald-400 to-cyan-400'
                }`}
              >
                <AnimatedCounter value={metric.value} />
                <span className="text-xl md:text-2xl font-bold ml-0.5">{metric.suffix}</span>
              </div>
              <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider text-center">
                {metric.label}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};
