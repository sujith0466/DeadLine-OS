import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, ShieldAlert, Users, RefreshCw, Building2, CheckCircle2 } from 'lucide-react';
import type { ProductMode } from './ProductModeSwitcher';

interface ModeSpecificShowcaseProps {
  mode: ProductMode;
}

export const ModeSpecificShowcase: React.FC<ModeSpecificShowcaseProps> = ({ mode }) => {
  const isPersonal = mode === 'personal';

  const personalShowcases = [
    {
      icon: Activity,
      tag: 'PREDICTIVE MODELING',
      title: 'Digital Twin Trajectory Simulation',
      desc: "See how today's choices change tomorrow. Your Digital Twin runs predictive variations of your week to identify cognitive fatigue and deadline collisions before they happen.",
      highlight: '94% Schedule Realization',
    },
    {
      icon: ShieldAlert,
      tag: 'MOMENTUM RECOVERY',
      title: 'Predictive Rescue Center',
      desc: 'When the plan breaks, DeadlineOS helps you recover. Injects restorative windows, recalibrates deadlines, and preserves habit streaks without guilt.',
      highlight: 'Zero-Guilt Recovery',
    },
    {
      icon: Users,
      tag: 'COORDINATED AGENTS',
      title: 'Autonomous Agent Ecosystem',
      desc: 'Your day adapts as reality changes. Specialized AI agents for planning, reflection, voice capture, and rescue coordinate continuously to protect your flow.',
      highlight: 'Continuous Optimization',
    },
  ];

  const businessShowcases = [
    {
      icon: ShieldAlert,
      tag: 'CASH & COLLECTIONS',
      title: 'Receivable Recovery & Collection Rescue',
      desc: 'Know what is owed. Know what needs attention. Automated multi-stage escalation delivers 1-click WhatsApp and email payment reminders with full audit provenance.',
      highlight: 'Accelerates Cash Collection',
    },
    {
      icon: RefreshCw,
      tag: 'RECURRING OPERATIONS',
      title: 'Automated Obligations Engine',
      desc: 'Recurring retainers and subscriptions keep moving without becoming recurring problems. Generates invoices and matches payments with zero double-billing risk.',
      highlight: '100% Idempotent Execution',
    },
    {
      icon: Building2,
      tag: 'MULTI-ENTITY CONTROL',
      title: 'Consolidated Group Operations',
      desc: 'One clear operational view across all companies, divisions, and subsidiaries you operate, with automatic identification and elimination of inter-company transfers.',
      highlight: 'Group-Level Cash Reality',
    },
  ];

  const items = isPersonal ? personalShowcases : businessShowcases;

  return (
    <section className="py-28 bg-[#07080A] relative border-t border-white/5">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <span className={`text-xs font-mono font-bold tracking-widest uppercase ${isPersonal ? 'text-indigo-400' : 'text-emerald-400'}`}>
            {isPersonal ? 'DEEP PERSONAL CAPABILITIES' : 'OPERATIONAL EXCELLENCE'}
          </span>
          <h2 className="text-3xl md:text-4xl font-black text-white mt-2">
            {isPersonal ? 'Engineered for High-Agency Individuals' : 'Built for Rigorous Commercial Operations'}
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <AnimatePresence mode="wait">
            {items.map((item, idx) => {
              const Icon = item.icon;
              return (
                <motion.div
                  key={`${mode}-${idx}`}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: idx * 0.1 }}
                  className="p-8 rounded-2xl bg-white/[0.02] border border-white/10 hover:border-white/20 transition-all flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between mb-6">
                      <div className={`p-3 rounded-xl ${isPersonal ? 'bg-indigo-500/10 text-indigo-400' : 'bg-emerald-500/10 text-emerald-400'}`}>
                        <Icon className="w-6 h-6" />
                      </div>
                      <span className="text-[10px] font-mono font-bold tracking-wider px-2.5 py-1 rounded bg-white/5 text-gray-400">
                        {item.tag}
                      </span>
                    </div>

                    <h3 className="text-xl font-bold text-white mb-3">{item.title}</h3>
                    <p className="text-sm text-gray-400 leading-relaxed mb-6">{item.desc}</p>
                  </div>

                  <div className="pt-4 border-t border-white/10 flex items-center justify-between text-xs">
                    <span className="font-semibold text-white">{item.highlight}</span>
                    <CheckCircle2 className={`w-4 h-4 ${isPersonal ? 'text-indigo-400' : 'text-emerald-400'}`} />
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      </div>
    </section>
  );
};
