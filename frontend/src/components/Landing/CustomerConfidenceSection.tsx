import React, { useState } from 'react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import {
  ShieldCheck,
  Lock,
  HeartHandshake,
  UserCheck,
  Zap,
  Building,
  FileCheck,
  Database,
  CheckCircle2,
  Sliders,
  Sparkles,
} from 'lucide-react';
import type { ProductMode } from './ProductModeSwitcher';

interface CustomerConfidenceSectionProps {
  mode: ProductMode;
}

export const CustomerConfidenceSection: React.FC<CustomerConfidenceSectionProps> = ({ mode }) => {
  const isPersonal = mode === 'personal';
  const shouldReduceMotion = useReducedMotion();
  const [selectedPillarIndex, setSelectedPillarIndex] = useState<number>(0);

  const personalPillars = [
    {
      id: 'privacy',
      title: 'Private Context Vault',
      subtitle: 'ZERO CONTEXT LEAKAGE',
      icon: Lock,
      statement: 'Your goals, thoughts, and reflections remain strictly isolated to your account.',
      details: 'We believe your personal aspirations and internal thoughts are sacrosanct. DeadlineOS enforces strict row-level account scoping and cryptographic encryption. We never monetize, sell, or train public models on your private schedule or reflections.',
      proof: 'Strict Row-Level Scoping • Zero Third-Party Monetization',
      badge: 'Protected Vault Active',
    },
    {
      id: 'adaptive',
      title: 'Adaptive, Not Punitive',
      subtitle: 'STREAK RESILIENCE',
      icon: HeartHandshake,
      statement: 'Schedules adapt when life shifts — without guilt, judgment, or broken streaks.',
      details: 'Traditional productivity software shames you with red overdue banners when a meeting overruns. DeadlineOS is built on human resilience: the moment your timeline encounters friction, it intelligently recalculates remaining tasks into realistic restorative buffers.',
      proof: 'Guilt-Free Recalibration • Automatic Restorative Windows',
      badge: 'Resilience Engine Online',
    },
    {
      id: 'human-control',
      title: 'Human Authority & Veto',
      subtitle: 'YOU HOLD THE CONTROLS',
      icon: UserCheck,
      statement: 'AI orchestrates and proposes; you retain ultimate authority over every decision.',
      details: 'You never wake up to an AI rewriting your calendar unprompted. Background agents act as high-agency co-pilots that prepare proposals, stage options, and highlight trade-offs — leaving final execution authority in your hands.',
      proof: 'Explicit Confirmation Gates • Transparent Decision Logic',
      badge: 'Human Authority Enforced',
    },
    {
      id: 'deliberate-automation',
      title: 'Deliberate Automation',
      subtitle: 'COGNITIVE LEVERAGE',
      icon: Zap,
      statement: 'Background intelligence handles tedious synthesis so you can focus on deep flow.',
      details: 'Instead of spending 45 minutes manually dragging calendar blocks and retyping task lists, our autonomous agents coordinate schedule adjustments, brief generation, and daily reflection in the background.',
      proof: 'Zero Manual Calendar Juggling • Compounding Daily Momentum',
      badge: 'Background Synthesis Ready',
    },
  ];

  const businessPillars = [
    {
      id: 'tenant-boundaries',
      title: 'Strict Workspace Isolation',
      subtitle: 'MULTI-TENANT DEFENSE',
      icon: Building,
      statement: 'Corporate financial records and entities remain completely segregated.',
      details: 'Every client workspace, subsidiary division, and corporate ledger runs within strictly enforced multi-tenant boundaries. Role-based permissions guarantee team members only access the financial operations authorized for their role.',
      proof: 'Row-Level Tenant Scoping • Strict Role-Based Access Controls',
      badge: 'Isolation Shield Active',
    },
    {
      id: 'audit-provenance',
      title: 'Complete Audit Provenance',
      subtitle: 'IMMUTABLE ACCOUNTABILITY',
      icon: Database,
      statement: 'Every balance calculation and automated reminder retains full audit history.',
      details: 'Every single payment allocation, invoice state transition, and customer communication creates an immutable, timestamped audit log. You always know exactly who approved an action and when it occurred.',
      proof: 'Cryptographic Audit Trail • Historical State Recovery',
      badge: 'Audit Trail Enforced',
    },
    {
      id: 'staging-gateway',
      title: 'Human Staging Barrier',
      subtitle: 'VERIFICATION GATEWAY',
      icon: FileCheck,
      statement: 'Inbound documents require side-by-side review before touching the general ledger.',
      details: 'AI never writes unconfirmed financial transactions directly to your permanent general ledger. Inbound invoices and receipts are staged into side-by-side review drafts requiring explicit human verification.',
      proof: '1-Click Verification Gateway • Zero Unchecked AI Writes',
      badge: 'Staging Barrier Active',
    },
    {
      id: 'deterministic-truth',
      title: 'Deterministic Accounting Truth',
      subtitle: 'EXACT DECIMAL ARITHMETIC',
      icon: ShieldCheck,
      statement: 'Double-entry ledger integrity with zero rounding drift or hallucinations.',
      details: 'Business OS is grounded in classical double-entry accounting principles with exact decimal math. Financial figures are never estimated or approximated by language models; all cash metrics trace to confirmed records.',
      proof: 'Balanced Debits & Credits • Exact Decimal Precision',
      badge: 'Ledger Invariants Verified',
    },
  ];

  const pillars = isPersonal ? personalPillars : businessPillars;
  const activePillar = pillars[selectedPillarIndex % pillars.length];
  const PillarIcon = activePillar.icon;

  return (
    <section className="py-28 bg-[#07080C] relative overflow-hidden border-t border-white/5">
      {/* Ambient background glow */}
      <div className={`absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[500px] rounded-full blur-[160px] pointer-events-none opacity-10 ${isPersonal ? 'bg-indigo-500' : 'bg-emerald-500'}`} />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">

        {/* Section Editorial Header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono font-bold tracking-wider uppercase mb-4 ${
            isPersonal ? 'bg-indigo-500/10 border border-indigo-500/20 text-indigo-400' : 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400'
          }`}>
            <Sliders className="w-3.5 h-3.5" />
            <span>{isPersonal ? 'THE CONTROL LAYER • ARCHITECTURAL TRUST' : 'ENTERPRISE OPERATIONAL CERTAINTY'}</span>
          </div>

          <h2 className="text-4xl md:text-5xl lg:text-6xl font-black tracking-tight text-white mb-6">
            {isPersonal ? (
              <>
                Intelligence that respects{' '}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-purple-300 to-pink-400">
                  your boundaries.
                </span>
              </>
            ) : (
              <>
                Autonomous operations under{' '}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400">
                  your absolute control.
                </span>
              </>
            )}
          </h2>

          <p className="text-base md:text-lg text-gray-400 leading-relaxed font-normal">
            {isPersonal
              ? 'DeadlineOS gives you high-agency leverage without black-box automation. Your private context stays private, schedules adapt to human biology, and decisions remain entirely yours.'
              : 'Enterprise-grade financial consistency, immutable audit provenance, strict workspace boundaries, and human-in-the-loop review barriers.'}
          </p>
        </div>

        {/* The Living Control & Trust Surface */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch">

          {/* Left Column: Interactive 4-Pillar Control Selector */}
          <div className="lg:col-span-5 flex flex-col justify-between space-y-3">
            <div className="text-xs font-mono font-bold text-gray-400 uppercase tracking-wider mb-1 flex items-center justify-between">
              <span>{isPersonal ? 'CORE TRUST PILLARS' : 'OPERATIONAL STANDARDS'}</span>
              <span className="text-[11px] font-mono text-gray-500">4 Guardrails</span>
            </div>

            {pillars.map((pillar, idx) => {
              const isSelected = (selectedPillarIndex % pillars.length) === idx;
              const Icon = pillar.icon;

              return (
                <button
                  key={pillar.id}
                  onClick={() => setSelectedPillarIndex(idx)}
                  className={`relative p-4 rounded-2xl text-left transition-all duration-200 cursor-pointer outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 border ${
                    isSelected
                      ? 'bg-white/[0.08] border-white/20 shadow-xl text-white'
                      : 'bg-white/[0.02] border-white/5 text-gray-400 hover:text-gray-200 hover:bg-white/[0.04]'
                  }`}
                >
                  {isSelected && (
                    <motion.div
                      layoutId="active-trust-pillar-pill"
                      transition={shouldReduceMotion ? { duration: 0 } : { type: 'spring', stiffness: 500, damping: 35 }}
                      className="absolute inset-0 rounded-2xl bg-white/[0.04] border border-white/25 shadow-[0_0_20px_rgba(255,255,255,0.06)]"
                    />
                  )}
                  <div className="flex items-center justify-between mb-1.5 relative z-10">
                    <div className="flex items-center gap-2.5">
                      <div className={`p-1.5 rounded-lg ${isSelected ? isPersonal ? 'bg-indigo-500/20 text-indigo-300' : 'bg-emerald-500/20 text-emerald-300' : 'bg-white/5 text-gray-500'}`}>
                        <Icon className="w-4 h-4" />
                      </div>
                      <span className="text-sm font-bold text-white">{pillar.title}</span>
                    </div>
                    <span className="text-[10px] font-mono text-gray-500">{pillar.subtitle}</span>
                  </div>
                  <p className="text-xs text-gray-400 leading-relaxed relative z-10 pl-8 font-normal">
                    {pillar.statement}
                  </p>
                </button>
              );
            })}
          </div>

          {/* Right Column: Dynamic Trust Telemetry Viewport */}
          <div className="lg:col-span-7">
            <AnimatePresence mode="wait">
              <motion.div
                key={`${mode}-${activePillar.id}`}
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                transition={shouldReduceMotion ? { duration: 0 } : { duration: 0.35 }}
                className="h-full p-6 md:p-8 rounded-3xl bg-[#0D0F18]/95 border border-white/10 shadow-[0_20px_60px_rgba(0,0,0,0.7)] flex flex-col justify-between relative overflow-hidden"
              >
                {/* Radial accent glow */}
                <div className={`absolute top-0 right-0 w-80 h-80 rounded-full blur-3xl opacity-15 pointer-events-none ${isPersonal ? 'bg-indigo-500' : 'bg-emerald-500'}`} />

                <div>
                  <div className="flex items-center justify-between pb-4 border-b border-white/10 mb-6">
                    <div className="flex items-center gap-2">
                      <PillarIcon className={`w-5 h-5 ${isPersonal ? 'text-indigo-400' : 'text-emerald-400'}`} />
                      <span className="text-xs font-mono font-bold text-white uppercase tracking-wider">
                        {activePillar.title}
                      </span>
                    </div>
                    <div className={`flex items-center gap-1.5 text-[11px] font-mono font-bold px-2.5 py-1 rounded-full ${
                      isPersonal ? 'bg-indigo-500/10 border border-indigo-500/20 text-indigo-300' : 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-300'
                    }`}>
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                      <span>{activePillar.badge}</span>
                    </div>
                  </div>

                  <h3 className="text-xl md:text-2xl font-black text-white mb-4">
                    {activePillar.statement}
                  </h3>

                  <p className="text-sm md:text-base text-gray-300 leading-relaxed font-normal mb-8">
                    {activePillar.details}
                  </p>
                </div>

                {/* Verified Invariant Proof Box */}
                <div className="p-4 rounded-2xl bg-black/60 border border-white/10 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-[10px] font-mono text-gray-400 uppercase tracking-wider">Architectural Invariant Guarantee</span>
                    <span className="text-emerald-400 font-mono text-[10px] flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" /> Guaranteed
                    </span>
                  </div>
                  <div className="text-xs font-semibold text-white flex items-center gap-2">
                    <Sparkles className={`w-3.5 h-3.5 ${isPersonal ? 'text-indigo-400' : 'text-emerald-400'}`} />
                    <span>{activePillar.proof}</span>
                  </div>
                </div>

              </motion.div>
            </AnimatePresence>
          </div>

        </div>

      </div>
    </section>
  );
};
