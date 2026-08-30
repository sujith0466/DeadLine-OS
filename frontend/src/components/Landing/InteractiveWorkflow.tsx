import React, { useState } from 'react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import {
  Mic,
  Calendar,
  Zap,
  ShieldAlert,
  Sparkles,
  ArrowRight,
  CheckCircle2,
  RefreshCw,
  Layers,
  DollarSign,
  TrendingUp,
  FileCheck,
  RotateCw,
} from 'lucide-react';
import type { ProductMode } from './ProductModeSwitcher';

interface InteractiveWorkflowProps {
  mode: ProductMode;
}

export const InteractiveWorkflow: React.FC<InteractiveWorkflowProps> = ({ mode }) => {
  const isPersonal = mode === 'personal';
  const shouldReduceMotion = useReducedMotion();
  const [activeStageIndex, setActiveStageIndex] = useState<number>(0);

  const personalLifecycle = [
    {
      num: '01',
      title: 'Multimodal Capture',
      stage: 'INPUT INGESTION',
      icon: Mic,
      tagline: 'Raw Chaos Ingested',
      summary: 'Drop raw voice memos, whiteboard photos, PDF syllabi, or quick thoughts into the system with zero manual tagging.',
      input: 'Spoken audio memo: "Need to finish backend auth and review designs before Friday"',
      output: 'Parsed into 2 structured tasks with estimated 90m deep work intervals and priority tags',
      agent: 'Ingestion & Vision Engine',
      metric: '< 2s Parse Latency',
    },
    {
      num: '02',
      title: 'Circadian Planning',
      stage: 'INTELLIGENCE COMPOSITION',
      icon: Calendar,
      tagline: 'Energy-Aware Prioritization',
      summary: 'Autonomous scheduler analyzes your biological focus peaks, calendar conflicts, and deadlines to generate an optimal daily plan.',
      input: 'Upcoming project milestone + 3 conflicting calendar invitations',
      output: 'Protected 09:00 - 11:30 Deep Work block mapped directly to circadian energy peak',
      agent: 'Autonomous Planner Agent',
      metric: '94% Schedule Realization',
    },
    {
      num: '03',
      title: 'Protected Execution',
      stage: 'FOCUSED FLOW',
      icon: Zap,
      tagline: 'Distraction-Free Momentum',
      summary: 'Enter deep execution mode with real-time focus analytics, automated notification suppression, and progressive goal tracking.',
      input: 'Active Deep Work Session: System Architecture Refactoring',
      output: '2h 15m uninterrupted focus recorded; 3 non-urgent alerts batched for recovery window',
      agent: 'Command Center Orchestrator',
      metric: '0 Distractions In-Flow',
    },
    {
      num: '04',
      title: 'Predictive Recovery',
      stage: 'MOMENTUM RESCUE',
      icon: ShieldAlert,
      tagline: 'Zero-Guilt Recalibration',
      summary: 'When fatigue is detected or a meeting overruns, your Digital Twin recalibrates remaining tasks into realistic restorative buffers.',
      input: 'Energy dip detected at 14:30; 1 task slipping behind schedule',
      output: 'Task rescheduled to Friday morning focus window; 45m restorative break injected',
      agent: 'Rescue & Digital Twin Agent',
      metric: 'Streak Preserved 100%',
    },
    {
      num: '05',
      title: 'Compounding Reflection',
      stage: 'SYSTEM EVOLUTION',
      icon: Sparkles,
      tagline: 'Daily Baseline Calibration',
      summary: 'Evening reflection synthesizes daily output, logs wins, and recalibrates tomorrow’s capacity model so you start ahead.',
      input: 'Daily execution summary: 4 tasks completed, 1 rescheduled, 88% momentum score',
      output: 'Tomorrow’s starting baseline updated with +4.2% velocity adjustment and prioritized morning brief',
      agent: 'Reflection & Synthesis Agent',
      metric: 'Self-Calibrating Loop',
    },
  ];

  const businessLifecycle = [
    {
      num: '01',
      title: 'Inbound Signal Stream',
      stage: 'RAW DOCUMENT INGESTION',
      icon: Layers,
      tagline: 'Multi-Source Capture',
      summary: 'Upload invoices, vendor receipts, bank feeds, or spoken contract terms into the centralized processing gateway.',
      input: 'Incoming PDF invoice: "INV-2026-104 from Acme Global ($18,500)"',
      output: 'OCR extracted: Vendor ID, Line Items, Tax Rate, Payment Terms, Due Date',
      agent: 'Multimodal Staging Parser',
      metric: '100% Extracted Metadata',
    },
    {
      num: '02',
      title: 'Human Staging Barrier',
      stage: 'VERIFICATION GATEWAY',
      icon: FileCheck,
      tagline: 'Human-in-the-Loop Review',
      summary: 'Review side-by-side extracted drafts with one-click verification before any data is recorded to the authoritative ledger.',
      input: 'Extracted draft vs Original PDF side-by-side review interface',
      output: '1-Click CFO Approval confirmed; transaction unlocked for ledger write',
      agent: 'Verification Barrier Engine',
      metric: 'Zero Unauthorized Writes',
    },
    {
      num: '03',
      title: 'Double-Entry Recording',
      stage: 'FINANCIAL TRUTH',
      icon: DollarSign,
      tagline: 'Immutable Ledger Journal',
      summary: 'Exact decimal math and balanced debits/credits are written into the immutable ledger with full historical audit logs.',
      input: 'Approved Invoice INV-2026-104 ($18,500.00)',
      output: 'Dr. Accounts Receivable $18,500.00 / Cr. Revenue $18,500.00 recorded',
      agent: 'Double-Entry Ledger Core',
      metric: 'Exact Decimal Arithmetic',
    },
    {
      num: '04',
      title: 'Cash & Runway Reality',
      stage: 'RUNWAY VISIBILITY',
      icon: TrendingUp,
      tagline: 'Real-Time Burn Dynamics',
      summary: 'Computes real-time verified cash balances, live burn velocity, and exact runway days, flagging overdue receivables.',
      input: 'Ledger Balances ($1.45M) + Daily Operating Burn ($15.4k/day)',
      output: 'Runway calculated at 94 Days Safe; 1 invoice flagged for stage-2 collection escalation',
      agent: 'Cash Reality & Runway Engine',
      metric: '94 Days Runway Horizon',
    },
    {
      num: '05',
      title: 'Automated Operations',
      stage: 'COLLECTION & RECONCILIATION',
      icon: RefreshCw,
      tagline: 'Autonomous Execution',
      summary: 'Dispatches staged 1-click collection reminders via WhatsApp/Email and reconciles recurring retainer billings idempotently.',
      input: '14-day overdue invoice for Apex Media ($12,500.00)',
      output: 'Multi-channel reminder sent with audit trail; customer paid via 1-click link',
      agent: 'Receivable Recovery Engine',
      metric: '3x Faster DSO Recovery',
    },
  ];

  const stages = isPersonal ? personalLifecycle : businessLifecycle;
  const activeStage = stages[activeStageIndex % stages.length];
  const Icon = activeStage.icon;

  return (
    <section id="workflow" className="py-28 bg-[#07080B] relative overflow-hidden border-t border-white/5">
      {/* Background ambient radial gradients */}
      <div className={`absolute top-1/2 -left-48 w-96 h-96 rounded-full blur-[140px] pointer-events-none opacity-20 ${isPersonal ? 'bg-indigo-600' : 'bg-emerald-600'}`} />
      <div className={`absolute bottom-0 right-0 w-96 h-96 rounded-full blur-[140px] pointer-events-none opacity-15 ${isPersonal ? 'bg-purple-600' : 'bg-cyan-600'}`} />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">

        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono font-bold tracking-wider uppercase mb-4 ${
            isPersonal ? 'bg-indigo-500/10 border border-indigo-500/20 text-indigo-400' : 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400'
          }`}>
            <RotateCw className="w-3.5 h-3.5" />
            <span>{isPersonal ? 'CONTINUOUS EXECUTION LIFECYCLE' : 'CLOSED-LOOP OPERATIONAL PIPELINE'}</span>
          </div>

          <h2 className="text-4xl md:text-5xl lg:text-6xl font-black tracking-tight text-white mb-6">
            {isPersonal ? (
              <>
                How Momentum is{' '}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-indigo-300 to-purple-400">
                  Generated & Compounded.
                </span>
              </>
            ) : (
              <>
                How Operations Turn into{' '}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400">
                  Unshakeable Truth.
                </span>
              </>
            )}
          </h2>

          <p className="text-base md:text-lg text-gray-400 leading-relaxed font-normal">
            {isPersonal
              ? 'DeadlineOS runs a closed-loop intelligence engine that observes reality, schedules around circadian limits, executes deep work, prevents burnout, and self-calibrates every single day.'
              : 'A deterministic pipeline that bridges raw business inputs through human staging, double-entry ledgers, live runway tracking, and automated collection execution.'}
          </p>
        </div>

        {/* Interactive Lifecycle Pathway Navigation (5 Connected Nodes) */}
        <div className="mb-10">
          <div className="flex flex-wrap md:flex-nowrap items-center justify-between gap-2 p-2 rounded-2xl bg-[#0D0F17]/95 border border-white/10 shadow-2xl backdrop-blur-2xl">
            {stages.map((stage, idx) => {
              const isSelected = (activeStageIndex % stages.length) === idx;
              const StageIcon = stage.icon;

              return (
                <button
                  key={stage.num}
                  onClick={() => setActiveStageIndex(idx)}
                  className={`flex-1 min-w-[140px] relative p-3 rounded-xl text-left transition-all duration-200 cursor-pointer outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 ${
                    isSelected ? 'bg-white/10 text-white shadow-lg border border-white/15' : 'text-gray-400 hover:text-gray-200 hover:bg-white/[0.03]'
                  }`}
                >
                  {isSelected && (
                    <motion.div
                      layoutId="active-lifecycle-pill"
                      transition={shouldReduceMotion ? { duration: 0 } : { type: 'spring', stiffness: 500, damping: 35 }}
                      className="absolute inset-0 rounded-xl bg-white/[0.08] border border-white/20 shadow-[0_0_15px_rgba(255,255,255,0.08)]"
                    />
                  )}
                  <div className="flex items-center justify-between mb-1.5 relative z-10">
                    <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-white/5 text-gray-300">
                      {stage.num}
                    </span>
                    <StageIcon className={`w-3.5 h-3.5 ${isSelected ? isPersonal ? 'text-indigo-400' : 'text-emerald-400' : 'text-gray-500'}`} />
                  </div>
                  <div className="text-xs font-bold text-white relative z-10 truncate">{stage.title}</div>
                  <div className="text-[10px] text-gray-500 relative z-10 truncate mt-0.5">{stage.stage}</div>
                </button>
              );
            })}
          </div>
        </div>

        {/* The Living Lifecycle Canvas & Deep Stage Inspector */}
        <AnimatePresence mode="wait">
          <motion.div
            key={`${mode}-${activeStage.num}`}
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -15 }}
            transition={shouldReduceMotion ? { duration: 0 } : { duration: 0.35 }}
            className="p-6 md:p-10 rounded-3xl bg-[#0C0E15]/95 border border-white/10 shadow-[0_20px_60px_rgba(0,0,0,0.7)] relative overflow-hidden"
          >
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">

              {/* Left Column: Stage Detail & Operational Logic */}
              <div className="lg:col-span-5 flex flex-col justify-between h-full">
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <span className={`text-[11px] font-mono font-bold px-2.5 py-1 rounded bg-white/5 ${isPersonal ? 'text-indigo-400 border border-indigo-500/20' : 'text-emerald-400 border border-emerald-500/20'}`}>
                      STAGE {activeStage.num} OF 05
                    </span>
                    <span className="text-[11px] font-mono text-gray-400 bg-black/40 px-2 py-0.5 rounded border border-white/5">
                      {activeStage.tagline}
                    </span>
                  </div>

                  <h3 className="text-2xl md:text-3xl font-black text-white mb-3">
                    {activeStage.title}
                  </h3>

                  <p className="text-sm md:text-base text-gray-300 leading-relaxed mb-6 font-normal">
                    {activeStage.summary}
                  </p>
                </div>

                <div className="pt-4 border-t border-white/10 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className={`w-4 h-4 ${isPersonal ? 'text-indigo-400' : 'text-emerald-400'}`} />
                    <span className="font-semibold text-white">Agent: {activeStage.agent}</span>
                  </div>
                  <span className="font-mono text-gray-400">{activeStage.metric}</span>
                </div>
              </div>

              {/* Right Column: Interactive Signal Flow Simulator */}
              <div className="lg:col-span-7">
                <div className="rounded-2xl bg-black/60 border border-white/10 p-5 md:p-6 shadow-inner space-y-4">
                  <div className="flex items-center justify-between text-xs pb-3 border-b border-white/10">
                    <div className="flex items-center gap-2">
                      <Icon className={`w-4 h-4 ${isPersonal ? 'text-indigo-400' : 'text-emerald-400'}`} />
                      <span className="font-bold text-white uppercase tracking-wider">LIVE CLOSED-LOOP ARTIFACT TRANSFORMATION</span>
                    </div>
                    <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                      STEP {activeStage.num} ACTIVE
                    </span>
                  </div>

                  {/* Input Signal State */}
                  <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/5">
                    <div className="text-[10px] font-mono text-gray-500 uppercase mb-1">Incoming Real-World Input Signal</div>
                    <div className="text-xs text-gray-300 font-medium">{activeStage.input}</div>
                  </div>

                  {/* Flow Connector Line */}
                  <div className="flex items-center justify-center gap-2 text-gray-600 text-xs py-0.5">
                    <div className="h-px bg-white/10 flex-1" />
                    <span className="font-mono text-[10px] text-gray-400 uppercase">Automated AI Synthesis & Orchestration</span>
                    <div className="h-px bg-white/10 flex-1" />
                  </div>

                  {/* Output Generated Action */}
                  <div className={`p-3.5 rounded-xl border ${isPersonal ? 'bg-indigo-500/10 border-indigo-500/25 text-indigo-200' : 'bg-emerald-500/10 border-emerald-500/25 text-emerald-200'}`}>
                    <div className={`text-[10px] font-mono font-bold uppercase mb-1 ${isPersonal ? 'text-indigo-400' : 'text-emerald-400'}`}>Generated Execution State & Artifact</div>
                    <div className="text-xs font-semibold text-white">{activeStage.output}</div>
                  </div>

                  {/* Next Step Compounding Cycle Indicator */}
                  <div className="pt-2 flex items-center justify-between text-[11px] text-gray-500">
                    <span className="flex items-center gap-1.5">
                      <RefreshCw className="w-3 h-3 text-gray-400" />
                      <span>Compounds directly into Step {((activeStageIndex + 1) % stages.length) + 1}: {stages[(activeStageIndex + 1) % stages.length].title}</span>
                    </span>
                    <button
                      onClick={() => setActiveStageIndex((prev) => (prev + 1) % stages.length)}
                      className="text-xs font-semibold text-white hover:text-indigo-400 flex items-center gap-1 cursor-pointer transition-colors"
                    >
                      Next Step <ArrowRight className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              </div>

            </div>
          </motion.div>
        </AnimatePresence>

      </div>
    </section>
  );
};
