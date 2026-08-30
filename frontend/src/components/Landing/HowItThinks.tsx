import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Cpu, Network, Database, Lock, ShieldCheck, RefreshCw } from 'lucide-react';
import type { ProductMode } from './ProductModeSwitcher';

interface HowItThinksProps {
  mode: ProductMode;
}

export const HowItThinks: React.FC<HowItThinksProps> = ({ mode }) => {
  const isPersonal = mode === 'personal';

  return (
    <section className="py-28 bg-[#0A0A0B] relative overflow-hidden border-t border-white/5">
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
                animate={{ scale: [1, 1.04, 1] }}
                transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
                className="absolute inset-0 m-auto w-36 h-36 rounded-2xl bg-gray-900/90 border border-white/15 shadow-2xl flex flex-col items-center justify-center z-20 backdrop-blur-xl"
              >
                <Cpu className={`w-10 h-10 mb-2 ${isPersonal ? 'text-indigo-400' : 'text-emerald-400'}`} />
                <span className="text-xs font-bold text-gray-200">{isPersonal ? 'Digital Twin Core' : 'Financial Truth Engine'}</span>
                <span className="text-[9px] font-mono text-gray-400">{isPersonal ? 'Simulation V2' : 'Double-Entry (B3)'}</span>
              </motion.div>

              {/* Orbiting Nodes */}
              {[
                { icon: Network, label: isPersonal ? 'Gemini 2.0' : 'Grounded Copilot', delay: 0 },
                { icon: Database, label: isPersonal ? 'Neon DB' : 'Postgres Ledger', delay: -2.5 },
                { icon: Lock, label: isPersonal ? 'Encrypted Auth' : '5-Tier RBAC', delay: -5 },
                { icon: isPersonal ? RefreshCw : ShieldCheck, label: isPersonal ? 'Rescue Agent' : 'Human Staging', delay: -7.5 },
              ].map((node, idx) => (
                <motion.div
                  key={`${mode}-${idx}`}
                  animate={{ rotate: 360 }}
                  transition={{ duration: 24, repeat: Infinity, ease: 'linear', delay: node.delay }}
                  className="absolute inset-0 w-full h-full"
                >
                  <div
                    className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 w-20 h-20 rounded-xl bg-gray-900 border border-white/10 shadow-xl flex flex-col items-center justify-center z-30"
                    style={{ transform: 'rotate(-360deg)' }}
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
                  {isPersonal ? 'Hybrid AI Architecture' : 'Zero-Bypass Deterministic Intelligence'}
                </div>

                <h2 className="text-3xl md:text-4xl font-black text-white mb-6 leading-tight">
                  {isPersonal
                    ? 'Intelligence That Simulates Before It Commits'
                    : 'AI Advisory with Unyielding Mathematical Truth'}
                </h2>

                <p className="text-base text-gray-400 mb-6 leading-relaxed">
                  {isPersonal
                    ? 'Unlike static to-do lists, DeadlineOS continuously models your energy capacity, habit momentum, and deadline collisions in a sandboxed digital twin simulation.'
                    : 'Business OS strictly separates AI advisory tasks from authoritative financial records. While Gemini assists with document extraction and risk summaries, all financial ledger writes require deterministic math and human staging verification.'}
                </p>

                <div className="space-y-4">
                  {(isPersonal
                    ? [
                        { title: 'Zero Hallucination Scheduling', desc: 'Schedules are locked against real calendar physics and hard deadlines.' },
                        { title: 'Predictive Burnout Detection', desc: 'Monitors cognitive velocity to suggest breaks before fatigue sets in.' },
                        { title: 'Multi-Agent Autonomous Orchestration', desc: 'Planner, Rescue, and Accountability agents coordinate behind the scenes.' },
                      ]
                    : [
                        { title: 'Staging Drawer Verification Barrier', desc: 'No invoice or payment enters the ledger without explicit human confirmation.' },
                        { title: 'Deterministic Decimal Arithmetic', desc: 'Zero floating-point rounding errors on multi-currency financial records.' },
                        { title: 'Grounded Business Copilot', desc: 'AI queries the ledger via structured read-only interfaces without hallucinating cash.' },
                      ]
                  ).map((item, idx) => (
                    <div key={idx} className="flex items-start gap-3 p-3 rounded-xl bg-white/[0.02] border border-white/5">
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
