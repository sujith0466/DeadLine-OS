import React, { useState } from 'react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import {
  Sun,
  Zap,
  Coffee,
  Users,
  Moon,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Sparkles,
  Layers,
  FileCheck,
  DollarSign,
  TrendingUp,
  ShieldAlert,
} from 'lucide-react';
import type { ProductMode } from './ProductModeSwitcher';

interface ModeSpecificShowcaseProps {
  mode: ProductMode;
}

export const ModeSpecificShowcase: React.FC<ModeSpecificShowcaseProps> = ({ mode }) => {
  const isPersonal = mode === 'personal';
  const shouldReduceMotion = useReducedMotion();
  const [selectedTimeSlot, setSelectedTimeSlot] = useState<number>(1);
  const [showComparison, setShowComparison] = useState<'with' | 'without'>('with');

  const personalDayTimeline = [
    {
      time: '07:30',
      period: 'MORNING GENESIS',
      title: 'Daily Brief & Energy Calibration',
      icon: Sun,
      energy: 'Rising (78%)',
      status: 'Synthesis Active',
      desc: 'DeadlineOS analyzes your sleep rhythm, upcoming deadlines, and calendar invitations to compose an optimized day before your feet hit the floor.',
      without: 'Wake up to 47 unread emails and a frantic mental scramble over what to work on first.',
      with: 'Clear morning brief delivered with exactly 3 high-leverage priorities aligned to your biological energy peak.',
      agent: 'Morning Brief Engine',
    },
    {
      time: '09:00',
      period: 'CIRCADIAN PEAK',
      title: 'Protected 2.5h Deep Work Block',
      icon: Zap,
      energy: 'Peak Energy (96%)',
      status: 'Distraction Shield ON',
      desc: 'Automatic focus shield silences non-urgent interruptions and protects high-leverage cognitive work during your natural biological peak.',
      without: 'Scattered attention across 6 Slack channels, impromptu syncs, and zero deep execution progress.',
      with: '2.5 hours of uninterrupted deep flow on architecture specs with real-time focus analytics.',
      agent: 'Command Center Orchestrator',
    },
    {
      time: '13:30',
      period: 'COGNITIVE REBALANCE',
      title: 'Restorative Buffer & Smart Rescheduling',
      icon: Coffee,
      energy: 'Midday Dip (52%)',
      status: 'Buffer Injected',
      desc: 'When an unexpected meeting overruns, your Digital Twin recalibrates afternoon priorities instantly without broken streaks or guilt.',
      without: 'Guilt spirals as a delayed lunch throws off the entire afternoon schedule, leading to abandoned tasks.',
      with: '45m restorative break injected; non-essential tasks automatically shifted to tomorrow morning focus block.',
      agent: 'Rescue & Recovery Center',
    },
    {
      time: '15:30',
      period: 'COLLABORATIVE WINDOW',
      title: 'Social & Synchronous Alignment',
      icon: Users,
      energy: 'Steady (74%)',
      status: 'Team Sync Mode',
      desc: 'Meetings and collaborative discussions are grouped together during your social energy window, keeping deep work blocks sacred.',
      without: 'Fragmented 15-minute Swiss-cheese calendar gaps where no meaningful work can possibly occur.',
      with: 'Consolidated meeting block with contextual talking points pre-loaded from ongoing project goals.',
      agent: 'Autonomous Planner',
    },
    {
      time: '19:00',
      period: 'EVENING SYNTHESIS',
      title: 'Reflection & Next Baseline Calibrated',
      icon: Moon,
      energy: 'Restorative (65%)',
      status: 'Reflection Logged',
      desc: 'Evening reflection synthesizes completed milestones, measures momentum score (+4.8%), and pre-sets tomorrow’s baseline.',
      without: 'Going to sleep with lingering anxiety about forgotten deadlines and open loops.',
      with: '100% peace of mind with all tasks captured, reviewed, and scheduled for the next cycle.',
      agent: 'Reflection & Synthesis Agent',
    },
  ];

  const businessDayTimeline = [
    {
      time: '08:30',
      period: 'INBOUND CAPTURE',
      title: 'Multimodal Ingestion Stream',
      icon: Layers,
      energy: 'Stream Active',
      status: 'OCR Extraction',
      desc: 'Invoices, receipts, and contract terms arriving via email and WhatsApp are parsed and structured in real-time.',
      without: 'Lost attachments in disorganized inboxes and manual data entry errors across spreadsheets.',
      with: 'Invoices instantly extracted into structured draft records awaiting one-click verification.',
      agent: 'Multimodal Staging Parser',
    },
    {
      time: '10:30',
      period: 'STAGING GATEWAY',
      title: 'Side-by-Side Human Verification',
      icon: FileCheck,
      energy: 'Verification Gateway',
      status: '1-Click Approval',
      desc: 'CFO conducts rapid side-by-side visual audits before any transaction touches the authoritative general ledger.',
      without: 'Unverified automated AI writes directly into accounting books, risking audits and hallucinations.',
      with: 'Strict barrier protection: AI never touches the general ledger without explicit human confirmation.',
      agent: 'Verification Barrier Engine',
    },
    {
      time: '12:30',
      period: 'FINANCIAL TRUTH',
      title: 'Double-Entry Recording & Allocation',
      icon: DollarSign,
      energy: 'Balanced State',
      status: 'Zero Rounding Drift',
      desc: 'Exact decimal math posts debits and credits with immutable audit logs and automated partner allocation.',
      without: 'Accumulated rounding discrepancies, unbalanced suspense accounts, and broken financial reports.',
      with: 'Authoritative double-entry integrity with verified mathematical certainty on every rupee.',
      agent: 'Double-Entry Ledger Core',
    },
    {
      time: '14:30',
      period: 'RUNWAY REALITY',
      title: 'Real-Time Burn Dynamics & Horizon',
      icon: TrendingUp,
      energy: 'Horizon Safe',
      status: '94 Days Runway',
      desc: 'Live group balances and burn velocity curves provide leadership with unshakeable visibility into cash runway.',
      without: 'Waiting 30 days for month-end close to find out the company’s actual cash position.',
      with: 'Continuous real-time calculation of exact runway horizon and flagged overdue risks.',
      agent: 'Cash Reality & Runway Engine',
    },
    {
      time: '17:00',
      period: 'OPERATIONS DISPATCH',
      title: 'Automated Collection & Reconciliation',
      icon: ShieldAlert,
      energy: 'Escalation Ready',
      status: 'Audit Logged',
      desc: 'Multi-stage reminders dispatched via WhatsApp/Email and recurring retainers generated without double-billing.',
      without: 'Awkward manual collection chasing and forgotten retainer invoice generation.',
      with: 'Automated 1-click payment escalation with complete audit history and instant reconciliation.',
      agent: 'Receivable Recovery Engine',
    },
  ];

  const timeline = isPersonal ? personalDayTimeline : businessDayTimeline;
  const activeSlot = timeline[selectedTimeSlot % timeline.length];
  const SlotIcon = activeSlot.icon;

  return (
    <section className="py-28 bg-[#080A0F] relative overflow-hidden border-t border-white/5">
      {/* Subtle background glow */}
      <div className={`absolute top-1/3 -right-48 w-[500px] h-[500px] rounded-full blur-[140px] pointer-events-none opacity-15 ${isPersonal ? 'bg-purple-600' : 'bg-teal-600'}`} />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">

        {/* Editorial Section Introduction */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono font-bold tracking-wider uppercase mb-4 ${
            isPersonal ? 'bg-indigo-500/10 border border-indigo-500/20 text-indigo-400' : 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400'
          }`}>
            <Sparkles className="w-3.5 h-3.5" />
            <span>{isPersonal ? 'HUMAN OUTCOME & LIVING RHYTHM' : 'ENTERPRISE OPERATIONAL CERTAINTY'}</span>
          </div>

          <h2 className="text-4xl md:text-5xl lg:text-6xl font-black tracking-tight text-white mb-6">
            {isPersonal ? (
              <>
                Built Around How You{' '}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-pink-300 to-indigo-400">
                  Actually Live.
                </span>
              </>
            ) : (
              <>
                Engineered for How Enterprises{' '}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-teal-400 via-emerald-300 to-cyan-400">
                  Actually Operate.
                </span>
              </>
            )}
          </h2>

          <p className="text-base md:text-lg text-gray-400 leading-relaxed font-normal">
            {isPersonal
              ? 'See how DeadlineOS orchestrates your day around circadian biological focus peaks, adapts to unexpected disruptions, and preserves your momentum without burnout.'
              : 'See how DeadlineOS streamlines high-stakes commercial operations, provides real-time runway visibility, and accelerates cash recovery with complete mathematical certainty.'}
          </p>
        </div>

        {/* The Living Day Rhythm Simulator (Interactive Master Surface) */}
        <div className="p-6 md:p-10 rounded-3xl bg-[#0D0F18]/95 border border-white/10 shadow-[0_20px_60px_rgba(0,0,0,0.7)]">

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">

            {/* Left Column: Interactive Hour Stepper & Narrative */}
            <div className="lg:col-span-5 flex flex-col justify-between h-full space-y-6">
              <div>
                <div className="flex items-center justify-between mb-4">
                  <span className="text-xs font-mono font-bold text-gray-400 uppercase tracking-wider">
                    {isPersonal ? 'DAILY OPERATING RHYTHM' : 'COMMERCIAL TIMELINE FLOW'}
                  </span>
                  <span className="text-[11px] font-mono text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                    Interactive Timeline
                  </span>
                </div>

                {/* Horizontal / Vertical Time Selector Pills */}
                <div className="grid grid-cols-5 gap-1.5 p-1 rounded-xl bg-black/50 border border-white/10 mb-6">
                  {timeline.map((slot, idx) => {
                    const isSelected = (selectedTimeSlot % timeline.length) === idx;
                    return (
                      <button
                        key={slot.time}
                        onClick={() => setSelectedTimeSlot(idx)}
                        className={`p-2 rounded-lg text-center transition-all cursor-pointer outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 ${
                          isSelected
                            ? 'bg-white text-slate-950 font-bold shadow-md'
                            : 'text-gray-400 hover:text-white hover:bg-white/5'
                        }`}
                      >
                        <div className="text-xs font-mono font-bold">{slot.time}</div>
                        <div className="text-[9px] truncate opacity-80">{slot.period.split(' ')[0]}</div>
                      </button>
                    );
                  })}
                </div>

                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded ${isPersonal ? 'bg-indigo-500/20 text-indigo-300' : 'bg-emerald-500/20 text-emerald-300'}`}>
                      {activeSlot.time} • {activeSlot.period}
                    </span>
                    <span className="text-[10px] font-mono text-gray-400">
                      {activeSlot.energy}
                    </span>
                  </div>

                  <h3 className="text-2xl font-black text-white">
                    {activeSlot.title}
                  </h3>

                  <p className="text-sm text-gray-300 leading-relaxed font-normal">
                    {activeSlot.desc}
                  </p>
                </div>
              </div>

              {/* Comparison Mode Toggle */}
              <div className="pt-4 border-t border-white/10">
                <div className="flex items-center gap-2 text-xs font-semibold mb-2">
                  <span className="text-gray-400">Compare Realities:</span>
                  <div className="flex rounded-lg bg-black/60 p-0.5 border border-white/10 text-[11px]">
                    <button
                      onClick={() => setShowComparison('with')}
                      className={`px-2.5 py-1 rounded-md transition-all cursor-pointer ${
                        showComparison === 'with'
                          ? isPersonal ? 'bg-indigo-600 text-white font-bold' : 'bg-emerald-600 text-white font-bold'
                          : 'text-gray-400 hover:text-white'
                      }`}
                    >
                      With DeadlineOS
                    </button>
                    <button
                      onClick={() => setShowComparison('without')}
                      className={`px-2.5 py-1 rounded-md transition-all cursor-pointer ${
                        showComparison === 'without' ? 'bg-rose-900/80 text-rose-200 font-bold' : 'text-gray-400 hover:text-white'
                      }`}
                    >
                      Without
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column: Dynamic Reality Comparison Surface */}
            <div className="lg:col-span-7">
              <AnimatePresence mode="wait">
                <motion.div
                  key={`${mode}-${selectedTimeSlot}-${showComparison}`}
                  initial={{ opacity: 0, scale: 0.98 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.98 }}
                  transition={shouldReduceMotion ? { duration: 0 } : { duration: 0.3 }}
                  className={`rounded-2xl p-6 border shadow-inner ${
                    showComparison === 'with'
                      ? 'bg-black/60 border-white/10'
                      : 'bg-rose-950/20 border-rose-500/20'
                  }`}
                >
                  <div className="flex items-center justify-between text-xs pb-3 border-b border-white/10 mb-4">
                    <div className="flex items-center gap-2">
                      <SlotIcon className={`w-4 h-4 ${showComparison === 'with' ? isPersonal ? 'text-indigo-400' : 'text-emerald-400' : 'text-rose-400'}`} />
                      <span className="font-bold text-white uppercase tracking-wider">
                        {showComparison === 'with' ? 'OPTIMIZED OPERATING OUTCOME' : 'UNCOORDINATED MANUAL FRICTION'}
                      </span>
                    </div>
                    <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded ${
                      showComparison === 'with'
                        ? isPersonal ? 'bg-indigo-500/10 text-indigo-300 border border-indigo-500/20' : 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'
                        : 'bg-rose-500/10 text-rose-300 border border-rose-500/20'
                    }`}>
                      {showComparison === 'with' ? activeSlot.status : 'High Cognitive Drag'}
                    </span>
                  </div>

                  {/* Reality Outcome Content */}
                  <div className="space-y-4">
                    <div className={`p-4 rounded-xl border text-sm leading-relaxed ${
                      showComparison === 'with'
                        ? isPersonal ? 'bg-indigo-500/10 border-indigo-500/20 text-indigo-100' : 'bg-emerald-500/10 border-emerald-500/20 text-emerald-100'
                        : 'bg-rose-950/30 border-rose-500/30 text-rose-200'
                    }`}>
                      <div className="flex items-start gap-3">
                        {showComparison === 'with' ? (
                          <CheckCircle2 className={`w-5 h-5 shrink-0 mt-0.5 ${isPersonal ? 'text-indigo-400' : 'text-emerald-400'}`} />
                        ) : (
                          <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5 text-rose-400" />
                        )}
                        <div>
                          <div className="font-bold text-white mb-1">
                            {showComparison === 'with' ? 'Seamless Daily Realization' : 'Chaotic Schedule Breakdown'}
                          </div>
                          <p className="text-xs md:text-sm font-normal">
                            {showComparison === 'with' ? activeSlot.with : activeSlot.without}
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Operational Proof Metric Footer */}
                    <div className="p-3 rounded-xl bg-black/40 border border-white/5 flex items-center justify-between text-xs text-gray-400">
                      <span className="flex items-center gap-1.5">
                        <Clock className="w-3.5 h-3.5 text-gray-500" />
                        <span>Governed by: <strong className="text-gray-200">{activeSlot.agent}</strong></span>
                      </span>
                      <span className="font-mono text-emerald-400 font-semibold">
                        {showComparison === 'with' ? '100% Flow Protected' : 'Friction Escalating'}
                      </span>
                    </div>
                  </div>
                </motion.div>
              </AnimatePresence>
            </div>

          </div>
        </div>

      </div>
    </section>
  );
};
