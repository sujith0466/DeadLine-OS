import React, { useState } from 'react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import {
  Activity,
  ShieldAlert,
  Terminal,
  Target,
  FileText,
  Mic,
  Camera,
  Layers,
  DollarSign,
  TrendingUp,
  RefreshCw,
  Cpu,
  Lock,
  Building,
  CheckCircle2,
  ArrowRight,
  Brain,
  Zap,
} from 'lucide-react';
import type { ProductMode } from './ProductModeSwitcher';

interface ProductShowcaseProps {
  mode: ProductMode;
}

export const ProductShowcase: React.FC<ProductShowcaseProps> = ({ mode }) => {
  const isPersonal = mode === 'personal';
  const shouldReduceMotion = useReducedMotion();
  const [activeTab, setActiveTab] = useState<number>(0);
  const [selectedTrajectory, setSelectedTrajectory] = useState<number>(0);

  // Reset active tab when switching mode
  const currentTab = activeTab;

  const personalCoreCapabilities = [
    {
      id: 'digital-twin',
      title: 'Digital Twin Trajectory Engine',
      eyebrow: 'PREDICTIVE COGNITION',
      icon: Activity,
      tag: 'Simulates Weekly Friction',
      desc: 'Models upcoming cognitive fatigue, calendar collisions, and energy dips across multiple simulated weekly timelines before you commit.',
      accent: 'from-blue-500 to-indigo-500',
      badge: '94% Schedule Realization',
    },
    {
      id: 'recovery-center',
      title: 'Predictive Recovery Center',
      eyebrow: 'MOMENTUM RESCUE',
      icon: ShieldAlert,
      tag: 'Zero-Guilt Recalibration',
      desc: 'Detects slipping streaks and cognitive velocity drops early, restructuring remaining tasks into realistic restorative recovery windows.',
      accent: 'from-purple-500 to-pink-500',
      badge: 'Streak Protection Active',
    },
    {
      id: 'command-center',
      title: 'Circadian Command Center',
      eyebrow: 'AUTONOMOUS ORCHESTRATION',
      icon: Terminal,
      tag: 'Energy-Aware Execution',
      desc: 'Orchestrates daily deep work blocks around circadian biological focus peaks and hard deadlines using high-agency autonomous intelligence.',
      accent: 'from-indigo-500 to-cyan-500',
      badge: 'Real-Time Flow Protection',
    },
    {
      id: 'momentum-engine',
      title: 'Intention-to-Momentum Engine',
      eyebrow: 'DETERMINISTIC PROGRESS',
      icon: Target,
      tag: 'Ambitious Goals → Daily Habits',
      desc: 'Breaks major quarterly intentions into deterministic daily habits and measurable milestones with structured accountability.',
      accent: 'from-emerald-500 to-teal-500',
      badge: 'Compounding Daily Wins',
    },
  ];

  const businessCoreCapabilities = [
    {
      id: 'staging-barrier',
      title: 'Human Staging Barrier',
      eyebrow: 'MULTIMODAL INGESTION',
      icon: Layers,
      tag: 'OCR Extraction + Human Review',
      desc: 'Transforms invoices, receipts, and contracts into structured draft records with a mandatory side-by-side human review barrier.',
      accent: 'from-cyan-500 to-blue-500',
      badge: '100% Staged Verification',
    },
    {
      id: 'double-entry-ledger',
      title: 'Authoritative Double-Entry Ledger',
      eyebrow: 'FINANCIAL TRUTH',
      icon: DollarSign,
      tag: 'Immutable Transaction Logs',
      desc: 'Maintains exact decimal math and balanced debits/credits. AI never writes directly to the authoritative ledger without explicit confirmation.',
      accent: 'from-emerald-500 to-teal-500',
      badge: 'Exact Decimal Arithmetic',
    },
    {
      id: 'runway-velocity',
      title: 'Cash Reality & Runway Velocity',
      eyebrow: 'RUNWAY VISIBILITY',
      icon: TrendingUp,
      tag: 'Real-Time Burn Dynamics',
      desc: 'Calculates verified cash positions and burn velocity curves to give leadership unshakeable runway horizon visibility.',
      accent: 'from-blue-500 to-indigo-500',
      badge: '94 Days Runway Safe',
    },
    {
      id: 'collection-rescue',
      title: 'Receivable Recovery Engine',
      eyebrow: 'COLLECTION ESCALATION',
      icon: ShieldAlert,
      tag: 'Automated 1-Click Reminders',
      desc: 'Tracks aging buckets (1-30d, 30d+) and coordinates staged WhatsApp/Email payment reminders with complete audit trails.',
      accent: 'from-rose-500 to-amber-500',
      badge: '3x Faster DSO Recovery',
    },
  ];

  const coreCapabilities = isPersonal ? personalCoreCapabilities : businessCoreCapabilities;
  const activeCapability = coreCapabilities[currentTab % coreCapabilities.length];

  const personalSupportingSubsystems = [
    {
      icon: FileText,
      title: 'Document Intelligence',
      desc: 'Parses course syllabi, project briefs, and technical specs into structured action timelines.',
      tag: 'Multimodal Ingestion',
    },
    {
      icon: Mic,
      title: 'Voice Thought Capture',
      desc: 'Captures stream-of-consciousness audio thoughts and extracts actionable tasks hands-free.',
      tag: 'Audio Transcription',
    },
    {
      icon: Camera,
      title: 'Vision Intelligence',
      desc: 'Converts whiteboard sketches, physical journal notes, and diagrams into structured schedules.',
      tag: 'Visual OCR',
    },
    {
      icon: Brain,
      title: 'Autonomous Multi-Agent Hub',
      desc: 'Planner, Rescue, Reflection, and Accountability agents coordinate continuously in the background.',
      tag: 'Agent Swarm',
    },
  ];

  const businessSupportingSubsystems = [
    {
      icon: RefreshCw,
      title: 'Recurring Obligations Engine',
      desc: 'Automates retainer billings, vendor renewals, and subscription cycles without double-billing risk.',
      tag: 'Idempotent Automation',
    },
    {
      icon: Building,
      title: 'Multi-Entity Group Consolidation',
      desc: 'Unified operational view across legal entities with automatic elimination of inter-company transfers.',
      tag: 'Group Consolidation',
    },
    {
      icon: Cpu,
      title: 'Grounded Ledger Copilot',
      desc: 'AI financial intelligence queries authoritative ledger records directly, avoiding hallucinations.',
      tag: 'Deterministic AI',
    },
    {
      icon: Lock,
      title: 'Enterprise Workspace Boundaries',
      desc: 'Multi-tenant isolation, role-based member permissions, and diagnostic health monitoring.',
      tag: 'Tenant Isolation',
    },
  ];

  const supportingSubsystems = isPersonal ? personalSupportingSubsystems : businessSupportingSubsystems;

  return (
    <section id="features" className="py-28 bg-[#08090C] relative overflow-hidden border-t border-white/5">
      {/* Ambient background glows */}
      <div
        className={`absolute top-1/4 -right-1/4 w-[600px] h-[600px] rounded-full blur-[140px] pointer-events-none transition-colors duration-700 ${
          isPersonal ? 'bg-indigo-500/10' : 'bg-emerald-500/10'
        }`}
      />
      <div
        className={`absolute bottom-1/4 -left-1/4 w-[600px] h-[600px] rounded-full blur-[140px] pointer-events-none transition-colors duration-700 ${
          isPersonal ? 'bg-purple-500/10' : 'bg-cyan-500/10'
        }`}
      />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">

        {/* 1. SYSTEM INTRODUCTION */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <motion.div
            key={mode}
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35 }}
          >
            <div
              className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono font-bold tracking-wider uppercase mb-4 ${
                isPersonal
                  ? 'bg-indigo-500/10 border border-indigo-500/20 text-indigo-400'
                  : 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400'
              }`}
            >
              <Zap className="w-3.5 h-3.5" />
              <span>{isPersonal ? 'INTERCONNECTED OPERATING SYSTEM' : 'COMMERCIAL OPERATING ECOSYSTEM'}</span>
            </div>

            <h2 className="text-4xl md:text-5xl lg:text-6xl font-black tracking-tight text-white mb-6">
              {isPersonal ? (
                <>
                  Everything your life needs,{' '}
                  <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-purple-300 to-pink-400">
                    working as one system.
                  </span>
                </>
              ) : (
                <>
                  Precision commercial truth,{' '}
                  <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400">
                    working as one system.
                  </span>
                </>
              )}
            </h2>

            <p className="text-base md:text-lg text-gray-400 leading-relaxed font-normal">
              {isPersonal
                ? 'DeadlineOS integrates cognitive scheduling, digital twin trajectory modeling, automated recovery, and multi-agent coordination into a single living product surface.'
                : 'DeadlineOS unifies multimodal staging, double-entry financial truth, real-time runway velocity, and automated collection rescue into one coherent operating environment.'}
            </p>
          </motion.div>
        </div>

        {/* 2. INTERACTIVE CAPABILITY ECOSYSTEM SELECTOR */}
        <div className="mb-8 flex justify-center">
          <div
            role="tablist"
            aria-label="Core Operating Capabilities"
            className="grid grid-cols-2 md:grid-cols-4 gap-2 p-1.5 rounded-2xl bg-[#0F1117]/90 border border-white/10 shadow-2xl backdrop-blur-2xl max-w-4xl w-full"
          >
            {coreCapabilities.map((cap, idx) => {
              const isSelected = (currentTab % coreCapabilities.length) === idx;
              const Icon = cap.icon;

              return (
                <button
                  key={cap.id}
                  role="tab"
                  id={`capability-tab-${cap.id}`}
                  aria-selected={isSelected}
                  tabIndex={isSelected ? 0 : -1}
                  onClick={() => setActiveTab(idx)}
                  className={`relative z-10 flex items-center justify-center gap-2 px-4 py-3 rounded-xl text-xs md:text-sm font-semibold transition-all duration-200 outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 cursor-pointer ${
                    isSelected ? 'text-slate-950 font-bold shadow-md' : 'text-gray-400 hover:text-white hover:bg-white/[0.03]'
                  }`}
                >
                  {isSelected && (
                    <motion.div
                      layoutId="active-showcase-tab-pill"
                      transition={shouldReduceMotion ? { duration: 0 } : { type: 'spring', stiffness: 500, damping: 35 }}
                      className="absolute inset-0 rounded-xl bg-white shadow-[0_2px_12px_rgba(255,255,255,0.25)]"
                    />
                  )}
                  <Icon className={`relative z-10 w-4 h-4 shrink-0 ${isSelected ? 'text-slate-950' : isPersonal ? 'text-indigo-400' : 'text-emerald-400'}`} />
                  <span className="relative z-10 truncate text-left">{cap.title.split(' ')[0]} {cap.title.split(' ')[1]}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* 3. PRIMARY LIVING CAPABILITY EXPERIENCE (BENTO HERO STAGE) */}
        <div className="mb-12">
          <AnimatePresence mode="wait">
            <motion.div
              key={`${mode}-${activeCapability.id}`}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={shouldReduceMotion ? { duration: 0 } : { duration: 0.35 }}
              className="p-6 md:p-10 rounded-3xl bg-[#0D0F16]/95 border border-white/10 shadow-[0_20px_60px_rgba(0,0,0,0.7)] relative overflow-hidden"
            >
              {/* Radial glow tailored to mode */}
              <div className={`absolute top-0 right-0 w-96 h-96 rounded-full blur-3xl opacity-20 pointer-events-none bg-gradient-to-br ${activeCapability.accent}`} />

              <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center relative z-10">

                {/* Left Column: Capability Narrative & Metadata */}
                <div className="lg:col-span-5 flex flex-col justify-between h-full">
                  <div>
                    <div className="flex items-center gap-2 mb-3">
                      <span className={`text-[11px] font-mono font-bold tracking-wider uppercase px-2.5 py-1 rounded-md bg-white/5 ${isPersonal ? 'text-indigo-400 border border-indigo-500/20' : 'text-emerald-400 border border-emerald-500/20'}`}>
                        {activeCapability.eyebrow}
                      </span>
                      <span className="text-[11px] font-mono text-gray-400 bg-black/40 px-2 py-0.5 rounded border border-white/5">
                        {activeCapability.tag}
                      </span>
                    </div>

                    <h3 className="text-2xl md:text-3xl font-black text-white mb-3">
                      {activeCapability.title}
                    </h3>

                    <p className="text-sm md:text-base text-gray-300 leading-relaxed mb-6 font-normal">
                      {activeCapability.desc}
                    </p>
                  </div>

                  {/* Interconnected System Proof points */}
                  <div className="pt-4 border-t border-white/10 flex items-center justify-between">
                    <div className="flex items-center gap-2 text-xs font-semibold text-white">
                      <CheckCircle2 className={`w-4 h-4 ${isPersonal ? 'text-indigo-400' : 'text-emerald-400'}`} />
                      <span>{activeCapability.badge}</span>
                    </div>
                    <span className="text-[11px] font-mono text-gray-500 uppercase">Live Subsystem</span>
                  </div>
                </div>

                {/* Right Column: Miniature Interactive Product Surface */}
                <div className="lg:col-span-7">
                  <div className="rounded-2xl bg-black/60 border border-white/10 p-5 md:p-6 shadow-inner relative overflow-hidden">

                    {/* PERSONAL CAPABILITY MINIATURE INTERFACES */}
                    {isPersonal && activeCapability.id === 'digital-twin' && (
                      <div className="space-y-4">
                        <div className="flex justify-between items-center text-xs pb-3 border-b border-white/10">
                          <div className="flex items-center gap-2">
                            <Activity className="w-4 h-4 text-indigo-400" />
                            <span className="font-bold text-white">TRAJECTORY SIMULATION VIEWER</span>
                          </div>
                          <span className="font-mono text-[10px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                            3 VARIATIONS EVALUATED
                          </span>
                        </div>

                        {/* Trajectory Path Buttons */}
                        <div className="grid grid-cols-3 gap-2 text-xs">
                          {[
                            { name: 'Balanced Realization', risk: 'Low Friction (12%)', score: '94% Success' },
                            { name: 'Aggressive Sprint', risk: 'High Collision (68%)', score: '71% Realized' },
                            { name: 'Restorative Buffer', risk: 'Zero Fatigue (4%)', score: '98% Realized' },
                          ].map((traj, idx) => (
                            <button
                              key={idx}
                              onClick={() => setSelectedTrajectory(idx)}
                              className={`p-2.5 rounded-xl text-left border transition-all cursor-pointer ${
                                selectedTrajectory === idx
                                  ? 'bg-indigo-500/15 border-indigo-500/40 text-white'
                                  : 'bg-white/[0.02] border-white/5 text-gray-400 hover:border-white/20'
                              }`}
                            >
                              <div className="font-bold text-[11px] truncate">{traj.name}</div>
                              <div className="text-[10px] text-indigo-300 mt-1">{traj.score}</div>
                              <div className="text-[9px] text-gray-500 mt-0.5">{traj.risk}</div>
                            </button>
                          ))}
                        </div>

                        {/* Animated Trajectory Curve Bar Graph */}
                        <div className="bg-black/50 p-4 rounded-xl border border-white/5">
                          <div className="flex justify-between text-[11px] text-gray-400 mb-2">
                            <span>Predicted Circadian Energy & Focus Allocation</span>
                            <span className="font-mono text-indigo-400">Optimal Workload Curve</span>
                          </div>
                          <div className="h-16 flex items-end justify-between gap-2 pt-2">
                            {[65, 80, 85, 90, 75, 50, 95].map((val, idx) => {
                              const dynamicHeight = selectedTrajectory === 1 ? Math.min(100, val + 20) : selectedTrajectory === 2 ? Math.max(30, val - 15) : val;
                              return (
                                <div key={idx} className="flex-1 flex flex-col items-center gap-1 h-full justify-end">
                                  <motion.div
                                    initial={shouldReduceMotion ? false : { height: '0%' }}
                                    animate={{ height: `${dynamicHeight}%` }}
                                    transition={{ duration: 0.4, delay: idx * 0.04 }}
                                    className="w-full bg-gradient-to-t from-indigo-600 via-purple-500 to-indigo-400 rounded-sm"
                                  />
                                  <span className="text-[9px] font-mono text-gray-500">D{idx + 1}</span>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      </div>
                    )}

                    {isPersonal && activeCapability.id === 'recovery-center' && (
                      <div className="space-y-4">
                        <div className="flex justify-between items-center text-xs pb-3 border-b border-white/10">
                          <div className="flex items-center gap-2">
                            <ShieldAlert className="w-4 h-4 text-purple-400" />
                            <span className="font-bold text-white">PREDICTIVE MOMENTUM RESCUE</span>
                          </div>
                          <span className="font-mono text-[10px] text-purple-300 bg-purple-500/10 px-2 py-0.5 rounded border border-purple-500/20">
                            ZERO-GUILT INTERVENTION
                          </span>
                        </div>

                        <div className="p-3.5 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-between">
                          <div>
                            <div className="text-xs font-bold text-white">Cognitive Fatigue Spike Detected</div>
                            <div className="text-[11px] text-purple-300 mt-0.5">Thursday 14:00 – High calendar collision density</div>
                          </div>
                          <span className="px-2.5 py-1 rounded bg-purple-500/20 text-purple-300 text-[10px] font-mono font-bold">
                            Buffer Injected
                          </span>
                        </div>

                        <div className="space-y-2">
                          <div className="flex justify-between text-xs text-gray-300">
                            <span>Momentum Preservation Score</span>
                            <span className="font-mono font-bold text-white">88%</span>
                          </div>
                          <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden">
                            <motion.div
                              initial={shouldReduceMotion ? false : { width: 0 }}
                              animate={{ width: '88%' }}
                              transition={{ duration: 0.8 }}
                              className="h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full"
                            />
                          </div>
                        </div>

                        <div className="p-3 rounded-xl bg-black/40 border border-white/5 text-[11px] text-gray-300 flex items-center justify-between">
                          <span>Action: 2 non-critical tasks rescheduled to Friday focus peak</span>
                          <span className="text-emerald-400 font-semibold flex items-center gap-1">
                            <CheckCircle2 className="w-3 h-3" /> Streak Protected
                          </span>
                        </div>
                      </div>
                    )}

                    {isPersonal && activeCapability.id === 'command-center' && (
                      <div className="space-y-3">
                        <div className="flex justify-between items-center text-xs pb-3 border-b border-white/10">
                          <div className="flex items-center gap-2">
                            <Terminal className="w-4 h-4 text-cyan-400" />
                            <span className="font-bold text-white">CIRCADIAN TIMELINE EXECUTION</span>
                          </div>
                          <span className="font-mono text-[10px] text-cyan-300 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20">
                            ORCHESTRATION ACTIVE
                          </span>
                        </div>

                        <div className="space-y-2 text-xs">
                          <div className="p-2.5 rounded-lg bg-indigo-500/15 border border-indigo-500/30 flex justify-between items-center">
                            <div className="flex items-center gap-2">
                              <span className="font-mono text-[10px] text-indigo-300">08:30 - 11:00</span>
                              <span className="font-bold text-white">Deep Work: Architecture System</span>
                            </div>
                            <span className="text-[10px] font-mono text-indigo-400 font-bold">Circadian Peak</span>
                          </div>

                          <div className="p-2.5 rounded-lg bg-white/5 border border-white/5 flex justify-between items-center">
                            <div className="flex items-center gap-2">
                              <span className="font-mono text-[10px] text-gray-400">11:30 - 12:30</span>
                              <span className="text-gray-300">System Alignment & Sync</span>
                            </div>
                            <span className="text-[10px] font-mono text-gray-400">Collaborative</span>
                          </div>

                          <div className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex justify-between items-center">
                            <div className="flex items-center gap-2">
                              <span className="font-mono text-[10px] text-emerald-400">14:00 - 16:00</span>
                              <span className="font-bold text-white">Core Implementation Block</span>
                            </div>
                            <span className="text-[10px] font-mono text-emerald-400 font-bold">High Velocity</span>
                          </div>
                        </div>
                      </div>
                    )}

                    {isPersonal && activeCapability.id === 'momentum-engine' && (
                      <div className="space-y-4">
                        <div className="flex justify-between items-center text-xs pb-3 border-b border-white/10">
                          <div className="flex items-center gap-2">
                            <Target className="w-4 h-4 text-emerald-400" />
                            <span className="font-bold text-white">GOALS & HABITS COMPACTION</span>
                          </div>
                          <span className="font-mono text-[10px] text-emerald-300 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                            14-DAY ACTIVE STREAK
                          </span>
                        </div>

                        <div className="p-3.5 rounded-xl bg-slate-900/80 border border-white/5 space-y-2">
                          <div className="flex justify-between text-xs">
                            <span className="font-bold text-white">Goal: Launch Autonomous Agent System</span>
                            <span className="font-mono text-emerald-400 font-bold">88% Completed</span>
                          </div>
                          <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden">
                            <motion.div
                              initial={shouldReduceMotion ? false : { width: 0 }}
                              animate={{ width: '88%' }}
                              transition={{ duration: 0.8 }}
                              className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 rounded-full"
                            />
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-2 text-[11px]">
                          <div className="p-2.5 rounded-lg bg-black/40 border border-white/5">
                            <div className="text-gray-400">Daily Habit</div>
                            <div className="font-bold text-white mt-0.5">90m Focused Deep Work</div>
                          </div>
                          <div className="p-2.5 rounded-lg bg-black/40 border border-white/5">
                            <div className="text-gray-400">Compounding Rate</div>
                            <div className="font-bold text-emerald-400 mt-0.5">+4.2% Weekly Velocity</div>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* BUSINESS CAPABILITY MINIATURE INTERFACES */}
                    {!isPersonal && activeCapability.id === 'staging-barrier' && (
                      <div className="space-y-4">
                        <div className="flex justify-between items-center text-xs pb-3 border-b border-white/10">
                          <div className="flex items-center gap-2">
                            <Layers className="w-4 h-4 text-cyan-400" />
                            <span className="font-bold text-white">DOCUMENT STAGING & EXTRACTION REVIEW</span>
                          </div>
                          <span className="font-mono text-[10px] text-cyan-300 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20">
                            HUMAN-IN-THE-LOOP
                          </span>
                        </div>

                        <div className="grid grid-cols-2 gap-3 text-xs">
                          <div className="p-3 rounded-xl bg-black/40 border border-white/5 space-y-1.5">
                            <div className="text-[10px] font-mono text-gray-400">RAW INBOUND SOURCE</div>
                            <div className="font-bold text-white">INV-2026-104.pdf</div>
                            <div className="text-[10px] text-gray-400">Vendor: Apex Tech Global</div>
                            <div className="text-[10px] font-mono text-emerald-400 font-bold">Total: ₹185,000</div>
                          </div>

                          <div className="p-3 rounded-xl bg-cyan-500/10 border border-cyan-500/20 space-y-1.5">
                            <div className="text-[10px] font-mono text-cyan-300">EXTRACTED DRAFT STATE</div>
                            <div className="font-bold text-white">Staged for Ledger Write</div>
                            <div className="text-[10px] text-gray-300">GST: 18% Verified (₹28,220)</div>
                            <div className="text-[10px] text-emerald-400 font-bold flex items-center gap-1">
                              <CheckCircle2 className="w-3 h-3" /> Ready for Approval
                            </div>
                          </div>
                        </div>

                        <div className="p-2.5 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-[11px] text-emerald-300 flex items-center justify-between">
                          <span>Barrier Protection: AI never writes directly to ledger without confirmation</span>
                          <span className="font-mono font-bold">1-Click Approve</span>
                        </div>
                      </div>
                    )}

                    {!isPersonal && activeCapability.id === 'double-entry-ledger' && (
                      <div className="space-y-4">
                        <div className="flex justify-between items-center text-xs pb-3 border-b border-white/10">
                          <div className="flex items-center gap-2">
                            <DollarSign className="w-4 h-4 text-emerald-400" />
                            <span className="font-bold text-white">DOUBLE-ENTRY JOURNAL INTEGRITY</span>
                          </div>
                          <span className="font-mono text-[10px] text-emerald-300 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                            BALANCED STATE: 100%
                          </span>
                        </div>

                        <div className="space-y-2 text-xs">
                          <div className="p-2.5 rounded-lg bg-black/40 border border-white/5 flex justify-between items-center font-mono">
                            <span className="text-gray-300">Dr. Accounts Receivable (Apex Media)</span>
                            <span className="font-bold text-emerald-400">₹125,000.00</span>
                          </div>
                          <div className="p-2.5 rounded-lg bg-black/40 border border-white/5 flex justify-between items-center font-mono">
                            <span className="text-gray-300">Cr. Professional Services Revenue</span>
                            <span className="font-bold text-white">₹125,000.00</span>
                          </div>
                        </div>

                        <div className="pt-2 border-t border-white/10 flex justify-between text-[11px] text-gray-400">
                          <span>Deterministic Decimal Arithmetic</span>
                          <span className="text-emerald-400 font-semibold">Zero Rounding Drift</span>
                        </div>
                      </div>
                    )}

                    {!isPersonal && activeCapability.id === 'runway-velocity' && (
                      <div className="space-y-4">
                        <div className="flex justify-between items-center text-xs pb-3 border-b border-white/10">
                          <div className="flex items-center gap-2">
                            <TrendingUp className="w-4 h-4 text-blue-400" />
                            <span className="font-bold text-white">CASH REALITY & RUNWAY HORIZON</span>
                          </div>
                          <span className="font-mono text-[10px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                            RUNWAY: 94 DAYS SAFE
                          </span>
                        </div>

                        <div className="grid grid-cols-2 gap-3 text-xs">
                          <div className="p-3 rounded-xl bg-black/40 border border-white/5">
                            <div className="text-gray-400 text-[10px]">Confirmed Group Balance</div>
                            <div className="text-xl font-bold text-white mt-1">₹1,450,000</div>
                          </div>
                          <div className="p-3 rounded-xl bg-black/40 border border-white/5">
                            <div className="text-gray-400 text-[10px]">Daily Burn Velocity</div>
                            <div className="text-xl font-bold text-blue-400 mt-1">₹15,400 / day</div>
                          </div>
                        </div>

                        {/* Runway Bar Projection */}
                        <div className="bg-black/50 p-3 rounded-xl border border-white/5">
                          <div className="flex justify-between text-[10px] text-gray-400 mb-1.5">
                            <span>Horizon Projections (30d • 60d • 90d+)</span>
                            <span className="text-emerald-400 font-mono">Runway Buffer: &gt;3 Months</span>
                          </div>
                          <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden">
                            <motion.div
                              initial={shouldReduceMotion ? false : { width: 0 }}
                              animate={{ width: '94%' }}
                              transition={{ duration: 0.8 }}
                              className="h-full bg-gradient-to-r from-blue-500 via-emerald-400 to-cyan-400 rounded-full"
                            />
                          </div>
                        </div>
                      </div>
                    )}

                    {!isPersonal && activeCapability.id === 'collection-rescue' && (
                      <div className="space-y-4">
                        <div className="flex justify-between items-center text-xs pb-3 border-b border-white/10">
                          <div className="flex items-center gap-2">
                            <ShieldAlert className="w-4 h-4 text-rose-400" />
                            <span className="font-bold text-white">COLLECTION RESCUE & ESCALATION</span>
                          </div>
                          <span className="font-mono text-[10px] text-rose-300 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20">
                            14D OVERDUE DETECTED
                          </span>
                        </div>

                        <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 flex justify-between items-center">
                          <div>
                            <div className="text-xs font-bold text-white">Apex Media Corp • INV-2026-088</div>
                            <div className="text-[10px] text-rose-300">Aging: 14 Days Overdue • ₹125,000</div>
                          </div>
                          <span className="px-2.5 py-1 rounded bg-rose-500/20 text-rose-300 text-[10px] font-mono font-bold">
                            Stage 2 Reminder
                          </span>
                        </div>

                        <div className="p-3 rounded-xl bg-black/40 border border-white/5 text-[11px] text-gray-300 flex items-center justify-between">
                          <span>Multi-Channel Dispatch: WhatsApp + Automated Email</span>
                          <span className="text-emerald-400 font-semibold flex items-center gap-1">
                            <CheckCircle2 className="w-3 h-3" /> Audit Logged
                          </span>
                        </div>
                      </div>
                    )}

                  </div>
                </div>

              </div>
            </motion.div>
          </AnimatePresence>
        </div>

        {/* 4. SUPPORTING SUBSYSTEMS BENTO GRID */}
        <div>
          <div className="flex items-center justify-between mb-6">
            <h4 className="text-xs font-mono font-bold tracking-widest text-gray-400 uppercase">
              {isPersonal ? 'SUPPORTING MULTIMODAL & AGENT SUBSYSTEMS' : 'ENTERPRISE INFRASTRUCTURE & INTEGRATION LAYERS'}
            </h4>
            <span className="text-[11px] text-gray-500 font-mono">4 Interconnected Modules</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
            {supportingSubsystems.map((sub, idx) => {
              const Icon = sub.icon;
              return (
                <motion.div
                  key={`${mode}-sub-${idx}`}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={shouldReduceMotion ? { duration: 0 } : { duration: 0.4, delay: idx * 0.06 }}
                  className="group p-5 rounded-2xl bg-white/[0.02] border border-white/10 hover:border-white/20 hover:bg-white/[0.04] transition-all flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <div className={`p-2.5 rounded-xl ${isPersonal ? 'bg-indigo-500/10 text-indigo-400' : 'bg-emerald-500/10 text-emerald-400'} group-hover:scale-105 transition-transform`}>
                        <Icon className="w-5 h-5" />
                      </div>
                      <span className="text-[10px] font-mono text-gray-500 bg-white/5 px-2 py-0.5 rounded">
                        {sub.tag}
                      </span>
                    </div>

                    <h5 className="text-base font-bold text-white mb-1.5 group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-white group-hover:to-gray-300">
                      {sub.title}
                    </h5>

                    <p className="text-xs text-gray-400 leading-relaxed font-normal">
                      {sub.desc}
                    </p>
                  </div>

                  <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between text-[11px] text-gray-500">
                    <span>Active Subsystem</span>
                    <ArrowRight className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition-all text-gray-300" />
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>

      </div>
    </section>
  );
};
