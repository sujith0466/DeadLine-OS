import React, { useState } from 'react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import {
  HelpCircle,
  Sparkles,
  CheckCircle2,
  ArrowRight,
  Shield,
  Activity,
  Layers,
  Cpu,
  RefreshCw,
} from 'lucide-react';
import type { ProductMode } from './ProductModeSwitcher';

interface FAQSectionProps {
  mode?: ProductMode;
}

export const FAQSection: React.FC<FAQSectionProps> = ({ mode = 'personal' }) => {
  const [selectedFaqIndex, setSelectedFaqIndex] = useState<number>(0);
  const isPersonal = mode === 'personal';
  const shouldReduceMotion = useReducedMotion();

  const personalFaqs = [
    {
      num: '01',
      category: 'OPERATING ENVIRONMENT',
      icon: Activity,
      question: 'What makes DeadlineOS different from traditional task managers?',
      answer: 'Traditional task managers are passive buckets that wait for you to do all the heavy lifting. DeadlineOS is an active cognitive operating environment. It continuously models your biological focus windows, forecasts weekly collision risks, injects restorative recovery buffers before fatigue sets in, and self-calibrates daily baselines through closed-loop reflection.',
      microVisual: 'Autonomous Closed-Loop vs Passive Task List',
      status: 'Active Operating System',
    },
    {
      num: '02',
      category: 'PREDICTIVE SIMULATION',
      icon: RefreshCw,
      question: 'How does Digital Twin trajectory simulation work?',
      answer: 'Your Digital Twin runs multi-path simulations of your upcoming week across historical task completion rates, circadian capacity curves, and fixed calendar commitments. It identifies cognitive friction spikes and deadline collisions days in advance, allowing you to choose the lowest-friction path before you commit.',
      microVisual: '3 Weekly Trajectories Evaluated • Low-Friction Path Selected',
      status: 'Predictive Modeling Online',
    },
    {
      num: '03',
      category: 'INTELLIGENCE ARCHITECTURE',
      icon: Cpu,
      question: 'When and how is AI intelligence invoked?',
      answer: 'High-agency AI reasoning models are invoked strictly for complex semantic operations — such as multimodal document parsing, voice-note task extraction, and goal-to-habit decomposition. Meanwhile, local deterministic engines enforce hard calendar bounds, invariant rules, and circadian recovery limits with zero latency.',
      microVisual: 'Semantic AI Reasoning + Deterministic Calendar Engine',
      status: 'Hybrid Orchestration Active',
    },
    {
      num: '04',
      category: 'PRIVACY & SECURITY',
      icon: Shield,
      question: 'Is my personal schedule and reflection data secure?',
      answer: 'Yes. All personal goals, habit logs, voice transcripts, and daily reflections are stored within isolated account vaults with strict cryptographic scoping. We never sell your personal context, monetize your schedule, or train public foundation models on your private reflections.',
      microVisual: 'Cryptographically Isolated Vault • Zero Telemetry Selling',
      status: 'Strict Account Isolation',
    },
  ];

  const businessFaqs = [
    {
      num: '01',
      category: 'FINANCIAL INTEGRITY',
      icon: CheckCircle2,
      question: 'How does DeadlineOS guarantee financial truth?',
      answer: 'Business OS enforces classical double-entry accounting principles with exact decimal math. AI never writes directly to the authoritative financial general ledger; all extracted documents, invoices, and bank records pass through a mandatory side-by-side human review barrier before posting.',
      microVisual: 'Balanced Debits/Credits • 1-Click Human Staging Barrier',
      status: 'Exact Decimal Arithmetic',
    },
    {
      num: '02',
      category: 'GROUP CONSOLIDATION',
      icon: Layers,
      question: 'Can I manage multiple commercial entities or subsidiaries?',
      answer: 'Yes. DeadlineOS provides commercial multi-entity group consolidation with automatic detection and elimination of inter-company transfers. Leadership receives a unified group-level cash reality across all legal entities, currencies, and subsidiary bank feeds in real-time.',
      microVisual: 'Inter-Company Transfer Elimination • Unified Group Cash',
      status: 'Multi-Entity Core Active',
    },
    {
      num: '03',
      category: 'COLLECTIONS & ESCALATION',
      icon: RefreshCw,
      question: 'How does the Overdue Collection Rescue engine operate?',
      answer: 'The Collection Rescue Engine continuously monitors invoice aging buckets (1-30d, 30d+) and coordinates staged, multi-channel payment reminders via WhatsApp and Email. Every dispatched reminder, customer view, and payment link click retains complete timestamped audit history.',
      microVisual: 'Staged 1-Click WhatsApp & Email Escalation • Full Audit Log',
      status: 'Automated DSO Recovery',
    },
    {
      num: '04',
      category: 'WORKSPACE ISOLATION',
      icon: Shield,
      question: 'Is there any cross-tenant data leakage between business workspaces?',
      answer: 'Zero. Business workspaces enforce rigorous multi-tenant scoping boundaries. Team members only access the financial operations, entities, and approval privileges explicitly permitted by their assigned role, ensuring complete institutional isolation.',
      microVisual: 'Row-Level Multi-Tenant Scoping • Role-Based Access Control',
      status: 'Strict Tenant Boundaries',
    },
  ];

  const faqs = isPersonal ? personalFaqs : businessFaqs;
  const activeFaq = faqs[selectedFaqIndex % faqs.length];
  const FaqIcon = activeFaq.icon;

  return (
    <section id="faq" className="py-28 bg-[#08090C] relative overflow-hidden border-t border-white/5">
      {/* Background glow */}
      <div className={`absolute bottom-0 left-1/3 w-[600px] h-[400px] rounded-full blur-[160px] pointer-events-none opacity-10 ${isPersonal ? 'bg-purple-600' : 'bg-cyan-600'}`} />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">

        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono font-bold tracking-wider uppercase mb-4 ${
            isPersonal ? 'bg-indigo-500/10 border border-indigo-500/20 text-indigo-400' : 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400'
          }`}>
            <HelpCircle className="w-3.5 h-3.5" />
            <span>{isPersonal ? 'INTELLIGENCE, EXPLAINED • CLARITY & ANSWERS' : 'COMMERCIAL ARCHITECTURE & CLARITY'}</span>
          </div>

          <h2 className="text-4xl md:text-5xl lg:text-6xl font-black tracking-tight text-white mb-6">
            Questions are part of{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-indigo-300 to-purple-400">
              the system.
            </span>
          </h2>

          <p className="text-base md:text-lg text-gray-400 leading-relaxed font-normal">
            {isPersonal
              ? 'Understand how DeadlineOS reasons, balances circadian schedules, protects your private context, and keeps you in complete authority.'
              : 'Understand how DeadlineOS enforces double-entry financial certainty, consolidates multi-entity operations, and ensures strict tenant isolation.'}
          </p>
        </div>

        {/* Interactive Editorial Knowledge & Answer Viewport */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch">

          {/* Left Column: Interactive Question Navigator */}
          <div className="lg:col-span-5 flex flex-col justify-between space-y-3">
            <div className="text-xs font-mono font-bold text-gray-400 uppercase tracking-wider mb-1 flex items-center justify-between">
              <span>EXPLORE QUESTIONS</span>
              <span className="text-[11px] font-mono text-gray-500">4 Answers</span>
            </div>

            {faqs.map((faq, idx) => {
              const isSelected = (selectedFaqIndex % faqs.length) === idx;

              return (
                <button
                  key={faq.num}
                  onClick={() => setSelectedFaqIndex(idx)}
                  className={`relative p-4 rounded-2xl text-left transition-all duration-200 cursor-pointer outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 border ${
                    isSelected
                      ? 'bg-white/[0.08] border-white/20 shadow-xl text-white'
                      : 'bg-white/[0.02] border-white/5 text-gray-400 hover:text-gray-200 hover:bg-white/[0.04]'
                  }`}
                >
                  {isSelected && (
                    <motion.div
                      layoutId="active-faq-question-pill"
                      transition={shouldReduceMotion ? { duration: 0 } : { type: 'spring', stiffness: 500, damping: 35 }}
                      className="absolute inset-0 rounded-2xl bg-white/[0.04] border border-white/25 shadow-[0_0_20px_rgba(255,255,255,0.06)]"
                    />
                  )}
                  <div className="flex items-center justify-between mb-1.5 relative z-10">
                    <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-white/5 text-gray-300">
                      {faq.num}
                    </span>
                    <span className="text-[10px] font-mono text-gray-500">{faq.category}</span>
                  </div>
                  <div className="text-sm font-bold text-white relative z-10 leading-snug">
                    {faq.question}
                  </div>
                </button>
              );
            })}
          </div>

          {/* Right Column: Large Answer Viewport (Product Surface) */}
          <div className="lg:col-span-7">
            <AnimatePresence mode="wait">
              <motion.div
                key={`${mode}-${activeFaq.num}`}
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                transition={shouldReduceMotion ? { duration: 0 } : { duration: 0.35 }}
                className="h-full p-6 md:p-8 rounded-3xl bg-[#0D0F18]/95 border border-white/10 shadow-[0_20px_60px_rgba(0,0,0,0.7)] flex flex-col justify-between relative overflow-hidden"
              >
                {/* Subtle radial accent glow */}
                <div className={`absolute top-0 right-0 w-80 h-80 rounded-full blur-3xl opacity-15 pointer-events-none ${isPersonal ? 'bg-indigo-500' : 'bg-emerald-500'}`} />

                <div>
                  <div className="flex items-center justify-between pb-4 border-b border-white/10 mb-6">
                    <div className="flex items-center gap-2">
                      <FaqIcon className={`w-4 h-4 ${isPersonal ? 'text-indigo-400' : 'text-emerald-400'}`} />
                      <span className="text-xs font-mono font-bold text-white uppercase tracking-wider">
                        {activeFaq.category} • ANSWER {activeFaq.num}
                      </span>
                    </div>
                    <div className={`flex items-center gap-1.5 text-[11px] font-mono font-bold px-2.5 py-1 rounded-full ${
                      isPersonal ? 'bg-indigo-500/10 border border-indigo-500/20 text-indigo-300' : 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-300'
                    }`}>
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                      <span>{activeFaq.status}</span>
                    </div>
                  </div>

                  <h3 className="text-xl md:text-2xl font-black text-white mb-4 leading-snug">
                    {activeFaq.question}
                  </h3>

                  <p className="text-sm md:text-base text-gray-300 leading-relaxed font-normal mb-8">
                    {activeFaq.answer}
                  </p>
                </div>

                {/* Micro Visual Signature Proof Box */}
                <div className="p-4 rounded-2xl bg-black/60 border border-white/10 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2 text-white font-semibold">
                    <Sparkles className={`w-4 h-4 ${isPersonal ? 'text-indigo-400' : 'text-emerald-400'}`} />
                    <span>{activeFaq.microVisual}</span>
                  </div>
                  <button
                    onClick={() => setSelectedFaqIndex((prev) => (prev + 1) % faqs.length)}
                    className="text-gray-400 hover:text-white flex items-center gap-1 text-[11px] font-mono cursor-pointer transition-colors"
                  >
                    Next Question <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>

              </motion.div>
            </AnimatePresence>
          </div>

        </div>

      </div>
    </section>
  );
};
