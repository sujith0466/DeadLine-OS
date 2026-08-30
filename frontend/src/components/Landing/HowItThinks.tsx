import React from 'react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import { Cpu, Network, Database, Lock, ShieldCheck, RefreshCw } from 'lucide-react';
import type { ProductMode } from './ProductModeSwitcher';

interface HowItThinksProps {
  mode: ProductMode;
}

export const HowItThinks: React.FC<HowItThinksProps> = ({ mode }) => {
  const isPersonal = mode === 'personal';
  const shouldReduceMotion = useReducedMotion();

  return (
    <section id="agents" className="py-28 bg-[#0A0A0B] relative overflow-hidden border-t border-white/5">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          
          {/* Architecture Visualization */}
          <div className="relative aspect-square md:aspect-[4/3] lg:aspect-square flex items-center justify-center">
            <div
              className={`absolute inset-0 rounded-full blur-[90px] transition-colors duration-700 ${
                isPersonal ? 'bg-indigo-500/10' : 'bg-emerald-500/10'
              }`}
            />
            
            <div className="relative w-full max-w-md aspect-square">
              {/* Central Core */}
              <motion.div 
                animate={shouldReduceMotion ? { scale: 1 } : { scale: [1, 1.04, 1] }}
                transition={shouldReduceMotion ? { duration: 0 } : { duration: 4, repeat: Infinity, ease: 'easeInOut' }}
                className="absolute inset-0 m-auto w-36 h-36 rounded-2xl bg-gray-900/90 border border-white/15 shadow-2xl flex flex-col items-center justify-center z-20 backdrop-blur-xl"
              >
                <Cpu className={`w-10 h-10 mb-2 ${isPersonal ? 'text-indigo-400' : 'text-emerald-400'}`} />
                <span className="text-xs font-bold text-gray-200">{isPersonal ? 'Digital Twin Core' : 'Financial Ledger'}</span>
                <span className="text-[9px] font-mono text-gray-400">{isPersonal ? 'Predictive Pacing' : 'Exact Double-Entry'}</span>
              </motion.div>

              {/* Orbiting Nodes */}
              {[
                { icon: Network, label: isPersonal ? 'Semantic AI' : 'Grounded Copilot', delay: 0 },
                { icon: Database, label: isPersonal ? 'Private Store' : 'Immutable Logs', delay: -2.5 },
                { icon: Lock, label: isPersonal ? 'Encrypted Context' : 'Tenant Boundaries', delay: -5 },
                { icon: isPersonal ? RefreshCw : ShieldCheck, label: isPersonal ? 'Rescue Agent' : 'Human Staging', delay: -7.5 },
              ].map((node, idx) => (
                <motion.div
                  key={`${mode}-${idx}`}
                  animate={shouldReduceMotion ? { rotate: idx * 90 } : { rotate: 360 }}
                  transition={shouldReduceMotion ? { duration: 0 } : { duration: 24, repeat: Infinity, ease: 'linear', delay: node.delay }}
                  className="absolute inset-0 w-full h-full"
                >
                  <div
                    className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 w-20 h-20 rounded-xl bg-gray-900 border border-white/10 shadow-xl flex flex-col items-center justify-center z-30"
                    style={{ transform: shouldReduceMotion ? `rotate(-${idx * 90}deg)` : 'rotate(-360deg)' }}
                  >
                    <node.icon className={`w-5 h-5 mb-1 ${isPersonal ? 'text-purple-400' : 'text-cyan-400'}`} />
                    <span className="text-[9px] font-bold text-gray-300 text-center px-1">{node.label}</span>
                  </div>
                </motion.div>
              ))}

              {/* Orbital Rings */}
              <div className="absolute inset-4 border border-white/5 rounded-full border-dashed" />
              <div className="absolute inset-12 border border-white/5 rounded-full" />
            </div>
          </div>

          {/* Text Content */}
          <div>
            <AnimatePresence mode="wait">
              <motion.div
                key={mode}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.35 }}
              >
                <div
                  className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold mb-6 ${
                    isPersonal
                      ? 'bg-indigo-500/10 border border-indigo-500/20 text-indigo-400'
                      : 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400'
                  }`}
                >
                  {isPersonal ? 'Intelligent Architecture' : 'AI Assistance + Mathematical Truth'}
                </div>

                <h2 className="text-3xl md:text-4xl font-black text-white mb-6 leading-tight">
                  {isPersonal
                    ? 'Intelligence That Simulates Before It Commits'
                    : 'AI Advisory with Authoritative Financial Rigor'}
                </h2>

                <p className="text-base text-gray-400 mb-6 leading-relaxed">
                  {isPersonal
                    ? 'Unlike passive to-do lists, DeadlineOS continuously models your energy capacity, habit momentum, and deadline collisions in a sandboxed digital twin simulation.'
                    : 'Business OS cleanly separates AI intelligence from authoritative financial records. While AI assists with document parsing and risk forecasting, all ledger writes require deterministic math and explicit human confirmation.'}
                </p>

                <div className="space-y-4">
                  {(isPersonal
                    ? [
                        { title: 'Zero-Hallucination Scheduling', desc: 'Schedules adapt to real calendar physics, circadian limits, and hard deadlines.' },
                        { title: 'Predictive Burnout Detection', desc: 'Monitors work velocity to suggest restorative interventions before fatigue takes hold.' },
                        { title: 'Autonomous Multi-Agent Coordination', desc: 'Planner, Rescue, and Accountability agents work behind the scenes.' },
                      ]
                    : [
                        { title: 'Human Verification Barrier', desc: 'No invoice or payment enters the ledger without explicit human confirmation.' },
                        { title: 'Deterministic Decimal Arithmetic', desc: 'Zero floating-point rounding errors across multi-currency records.' },
                        { title: 'Grounded Copilot Reasoning', desc: 'AI queries real ledger state without guessing or hallucinating cash positions.' },
                      ]
                  ).map((item, idx) => (
                    <div key={idx} className="flex items-start gap-3 p-3.5 rounded-xl bg-white/[0.02] border border-white/5">
                      <div className={`p-1.5 rounded-lg mt-0.5 ${isPersonal ? 'bg-indigo-500/10 text-indigo-400' : 'bg-emerald-500/10 text-emerald-400'}`}>
                        <ShieldCheck className="w-4 h-4" />
                      </div>
                      <div>
                        <h4 className="text-sm font-bold text-white">{item.title}</h4>
                        <p className="text-xs text-gray-400 mt-0.5">{item.desc}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            </AnimatePresence>
          </div>

        </div>
      </div>
    </section>
  );
};
