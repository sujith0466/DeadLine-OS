import React, { useState, useEffect, useRef } from 'react';
import { motion, useInView, useSpring, useTransform, useReducedMotion } from 'framer-motion';
import {
  Activity,
  Cpu,
  TrendingUp,
  Sparkles,
  ShieldCheck,
  Zap,
  Layers,
  CheckCircle2,
} from 'lucide-react';
import type { ProductMode } from './ProductModeSwitcher';

const AnimatedTelemetryCounter: React.FC<{ value: number; duration?: number; suffix?: string }> = ({
  value,
  duration = 1.8,
  suffix = '',
}) => {
  const shouldReduceMotion = useReducedMotion();
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, margin: '-40px' });
  const spring = useSpring(shouldReduceMotion ? value : 0, {
    duration: shouldReduceMotion ? 0 : duration * 1000,
    bounce: 0,
  });
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
    return (
      <span>
        {value.toLocaleString()}
        {suffix}
      </span>
    );
  }

  return (
    <span ref={ref} className="tabular-nums">
      <motion.span>{displayValue}</motion.span>
      {suffix && <span className="ml-0.5">{suffix}</span>}
    </span>
  );
};

interface TrustedMetricsProps {
  mode: ProductMode;
}

export const TrustedMetrics: React.FC<TrustedMetricsProps> = ({ mode }) => {
  const isPersonal = mode === 'personal';
  const shouldReduceMotion = useReducedMotion();
  const [hoveredNode, setHoveredNode] = useState<number | null>(null);

  const personalMetrics = [
    {
      id: 'modules',
      category: 'SYSTEM CAPABILITY',
      value: 8,
      prefix: '',
      suffix: '+',
      label: 'Autonomous AI Modules',
      status: 'Active Matrix',
      desc: 'Multimodal Ingestion & Core Runtimes',
      icon: Cpu,
      telemetry: '08/08 Core Systems Active',
      pathSvg: 'M2 12h4l3-8 4 16 3-8h6',
    },
    {
      id: 'agents',
      category: 'AGENT SWARM',
      value: 6,
      prefix: '',
      suffix: '',
      label: 'Coordinated Agents',
      status: 'Synchronized',
      desc: 'Real-time Dispatch & Reflection',
      icon: Activity,
      telemetry: 'Continuous Multi-Agent Sync',
      pathSvg: 'M3 12a9 9 0 1 0 18 0 9 9 0 0 0-18 0',
    },
    {
      id: 'simulations',
      category: 'PREDICTIVE MODELING',
      value: 24500,
      prefix: '',
      suffix: '+',
      label: 'Twin Trajectories Simulated',
      status: 'Monte Carlo Safe',
      desc: 'Circadian Friction & Collision Avoidance',
      icon: TrendingUp,
      telemetry: '94% Schedule Realization',
      pathSvg: 'M3 17l6-6 4 4 8-8',
    },
    {
      id: 'outcomes',
      category: 'REALIZED IMPACT',
      value: 12000,
      prefix: '',
      suffix: '+',
      label: 'Goals & Habits Realized',
      status: 'Compounding',
      desc: 'Zero-Guilt Daily Realization',
      icon: Sparkles,
      telemetry: '+4.8% Weekly Velocity',
      pathSvg: 'M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z',
    },
  ];

  const businessMetrics = [
    {
      id: 'ops',
      category: 'COMMERCIAL CAPABILITY',
      value: 24,
      prefix: '',
      suffix: '+',
      label: 'Automated Operations Active',
      status: 'Deterministic',
      desc: 'Double-Entry Invoicing & Allocations',
      icon: Layers,
      telemetry: 'Exact Decimal Precision',
      pathSvg: 'M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5',
    },
    {
      id: 'runway',
      category: 'FINANCIAL VISIBILITY',
      value: 94,
      prefix: '',
      suffix: ' Days',
      label: 'Cash Runway Horizon',
      status: 'Real-Time Safe',
      desc: 'Live Group Balances & Burn Velocity',
      icon: ShieldCheck,
      telemetry: 'Real-Time Burn Dynamics',
      pathSvg: 'M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z',
    },
    {
      id: 'recovery',
      category: 'RECOVERY VELOCITY',
      value: 3,
      prefix: '',
      suffix: 'x Faster',
      label: 'Receivable Collection Speed',
      status: '1-Click Escalation',
      desc: 'Automated DSO WhatsApp & Email Links',
      icon: Zap,
      telemetry: 'Staged Audit Provenance',
      pathSvg: 'M13 2L3 14h9l-1 8 10-12h-9l1-8z',
    },
    {
      id: 'consolidation',
      category: 'GROUP REALITY',
      value: 100,
      prefix: '',
      suffix: '% Live',
      label: 'Unified Group Consolidation',
      status: 'Zero Contamination',
      desc: 'Multi-Entity Inter-Company Elimination',
      icon: CheckCircle2,
      telemetry: 'Verified Group Cash Truth',
      pathSvg: 'M22 11.08V12a10 10 0 1 1-5.93-9.14M22 4L12 14.01l-3-3',
    },
  ];

  const metrics = isPersonal ? personalMetrics : businessMetrics;

  return (
    <section
      id="metrics"
      aria-label="Operating Intelligence and Metrics"
      className="py-20 bg-[#07080B] relative overflow-hidden border-t border-white/5"
    >
      {/* Background ambient radial glow */}
      <div
        className={`absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[350px] rounded-full blur-[160px] pointer-events-none opacity-15 ${
          isPersonal ? 'bg-indigo-600' : 'bg-emerald-600'
        }`}
      />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">

        {/* System Pulse Control Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-8 pb-6 border-b border-white/10 gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span
                className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold uppercase tracking-wider ${
                  isPersonal
                    ? 'bg-indigo-500/10 border border-indigo-500/25 text-indigo-400'
                    : 'bg-emerald-500/10 border border-emerald-500/25 text-emerald-400'
                }`}
              >
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                <span>LIVE SYSTEM PULSE • CONTINUOUS OPERATING INTELLIGENCE</span>
              </span>
            </div>
            <h2 className="text-2xl md:text-3xl font-black text-white tracking-tight">
              {isPersonal ? 'One Interconnected Cognitive System.' : 'One Unified Commercial Operating Core.'}
            </h2>
          </div>
        </div>

        {/* Central Unified Telemetry Surface */}
        <div className="relative rounded-3xl bg-[#0B0D14]/95 border border-white/10 shadow-[0_20px_60px_rgba(0,0,0,0.7)] backdrop-blur-2xl p-4 md:p-6 lg:p-8 overflow-hidden">

          {/* Subtle connecting telemetry rail across desktop */}
          <div className="hidden lg:block absolute top-1/2 left-8 right-8 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent pointer-events-none -translate-y-1/2" />

          {/* 4 Connected Telemetry Metric Nodes */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6 relative z-10">
            {metrics.map((item, idx) => {
              const Icon = item.icon;
              const isHovered = hoveredNode === idx;

              return (
                <motion.div
                  key={`${mode}-${item.id}`}
                  initial={shouldReduceMotion ? false : { opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: '-40px' }}
                  transition={
                    shouldReduceMotion
                      ? { duration: 0 }
                      : { duration: 0.45, delay: idx * 0.08, ease: [0.21, 0.47, 0.32, 0.98] }
                  }
                  onMouseEnter={() => setHoveredNode(idx)}
                  onMouseLeave={() => setHoveredNode(null)}
                  className={`group relative p-6 rounded-2xl border transition-all duration-300 flex flex-col justify-between cursor-default outline-none focus-within:ring-2 focus-within:ring-indigo-400 ${
                    isHovered
                      ? 'bg-white/[0.06] border-white/25 shadow-2xl translate-y-[-2px]'
                      : 'bg-white/[0.02] border-white/5 hover:border-white/15'
                  }`}
                >
                  {/* Subtle top indicator bar */}
                  <div
                    className={`absolute top-0 left-6 right-6 h-[2px] rounded-full transition-opacity duration-300 ${
                      isHovered
                        ? isPersonal
                          ? 'bg-gradient-to-r from-indigo-500 via-purple-400 to-pink-400 opacity-100'
                          : 'bg-gradient-to-r from-emerald-500 via-teal-400 to-cyan-400 opacity-100'
                        : 'opacity-0'
                    }`}
                  />

                  {/* Header: Category & Icon */}
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <span className="text-[10px] font-mono font-bold tracking-wider uppercase text-gray-400 group-hover:text-gray-300 transition-colors">
                        {item.category}
                      </span>
                      <div
                        className={`p-2 rounded-xl border transition-colors ${
                          isHovered
                            ? isPersonal
                              ? 'bg-indigo-500/20 border-indigo-500/30 text-indigo-300'
                              : 'bg-emerald-500/20 border-emerald-500/30 text-emerald-300'
                            : 'bg-white/5 border-white/10 text-gray-400'
                        }`}
                      >
                        <Icon className="w-4 h-4" />
                      </div>
                    </div>

                    {/* Metric Counter Value */}
                    <div
                      className={`text-3xl md:text-4xl lg:text-5xl font-black tracking-tight mb-2 text-transparent bg-clip-text bg-gradient-to-r ${
                        isPersonal
                          ? 'from-white via-indigo-100 to-indigo-300'
                          : 'from-white via-emerald-100 to-teal-300'
                      }`}
                    >
                      <AnimatedTelemetryCounter
                        value={item.value}
                        suffix={item.suffix}
                        duration={1.8 + idx * 0.2}
                      />
                    </div>

                    {/* Metric Label */}
                    <h3 className="text-sm font-bold text-white mb-1.5 leading-snug">
                      {item.label}
                    </h3>

                    {/* Supporting Description */}
                    <p className="text-xs text-gray-400 leading-relaxed font-normal mb-4">
                      {item.desc}
                    </p>
                  </div>

                  {/* Footer: Live Telemetry Status Pill */}
                  <div className="pt-3 border-t border-white/5 flex items-center justify-between text-[11px] font-mono">
                    <span className="text-gray-500 truncate max-w-[140px]">{item.telemetry}</span>
                    <span
                      className={`flex items-center gap-1 font-semibold ${
                        isPersonal ? 'text-indigo-400' : 'text-emerald-400'
                      }`}
                    >
                      <span className="w-1.5 h-1.5 rounded-full bg-current" />
                      <span>{item.status}</span>
                    </span>
                  </div>
                </motion.div>
              );
            })}
          </div>

          {/* Bottom Telemetry Baseline Metadata */}
          <div className="mt-6 pt-4 border-t border-white/5 flex flex-wrap items-center justify-between text-xs text-gray-400 font-mono gap-2">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400/80" />
              <span>Orchestration Layer: Fully Coordinated</span>
            </div>
            <div className="flex items-center gap-4 text-[11px] text-gray-400">
              <span>Telemetry Invariant: Verified</span>
              <span>•</span>
              <span>Deterministic Execution Engine</span>
            </div>
          </div>

        </div>

      </div>
    </section>
  );
};
