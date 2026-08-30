import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ShieldCheck, CheckCircle2, UserCheck, Building } from 'lucide-react';
import type { ProductMode } from './ProductModeSwitcher';

interface CustomerConfidenceSectionProps {
  mode: ProductMode;
}

export const CustomerConfidenceSection: React.FC<CustomerConfidenceSectionProps> = ({ mode }) => {
  const isPersonal = mode === 'personal';

  const personalGuarantees = [
    {
      title: 'Private by Design',
      desc: 'Your goals, habits, thoughts, and reflections remain strictly isolated to your private account. We never monetize or sell your context.',
    },
    {
      title: 'Adaptive, Not Punitive',
      desc: 'When life disrupts your plan, DeadlineOS adjusts your timeline without broken streaks or judgment, keeping your momentum compounding.',
    },
    {
      title: 'Cognitive Pacing',
      desc: 'Intelligent planning respects real circadian limits, balancing ambition with adequate recovery intervals.',
    },
    {
      title: 'Deliberate Automation',
      desc: 'Background agents handle tedious task rescheduling and daily synthesis so you can focus entirely on deep execution.',
    },
  ];

  const businessGuarantees = [
    {
      title: 'Authoritative Financial Truth',
      desc: 'Every balance and invoice calculation traces directly to confirmed transaction records with exact decimal math.',
    },
    {
      title: 'Complete Audit Provenance',
      desc: 'Every allocation, invoice adjustment, and automated reminder maintains an immutable historical audit log.',
    },
    {
      title: 'Human Verification Where It Matters',
      desc: 'Inbound documents pass through a side-by-side staging review barrier before touching authoritative records.',
    },
    {
      title: 'Strict Workspace Isolation',
      desc: 'Rigorous multi-tenant boundaries ensure corporate financial records remain completely segregated across clients and entities.',
    },
  ];

  const guarantees = isPersonal ? personalGuarantees : businessGuarantees;

  return (
    <section className="py-24 bg-[#0A0A0B] relative border-t border-white/5">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="p-8 md:p-12 rounded-3xl bg-gradient-to-br from-slate-900/60 via-slate-900/30 to-black/60 border border-white/10 relative overflow-hidden">
          <div className="relative z-10 grid grid-cols-1 lg:grid-cols-3 gap-8 items-center">
            
            <div className="lg:col-span-2">
              <div
                className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold mb-4 ${
                  isPersonal
                    ? 'bg-indigo-500/10 border border-indigo-500/20 text-indigo-400'
                    : 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400'
                }`}
              >
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>{isPersonal ? 'Personal Trust & Privacy' : 'Enterprise Operational Reliability'}</span>
              </div>
              
              <AnimatePresence mode="wait">
                <motion.div
                  key={mode}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.3 }}
                >
                  <h2 className="text-3xl md:text-4xl font-black text-white mb-4">
                    {isPersonal
                      ? 'Built Around Your Life, Not Another Task List.'
                      : 'Operational Clarity Without Losing Control.'}
                  </h2>
                  <p className="text-sm md:text-base text-gray-400 leading-relaxed mb-6">
                    {isPersonal
                      ? 'DeadlineOS is engineered to be an active, supportive operating partner. Your private context stays yours, and your schedules adapt to the reality of daily life.'
                      : 'DeadlineOS gives leadership and operations teams deterministic financial truth, verifiable audit trails, and automated workflows that never compromise control.'}
                  </p>
                </motion.div>
              </AnimatePresence>
            </div>

            <div className="space-y-3 bg-black/50 p-6 rounded-2xl border border-white/5">
              <div className="text-xs font-mono text-gray-400 font-bold uppercase tracking-wider mb-2 flex items-center justify-between">
                <span>{isPersonal ? 'CORE COMMITMENTS' : 'OPERATIONAL STANDARDS'}</span>
                {isPersonal ? <UserCheck className="w-4 h-4 text-indigo-400" /> : <Building className="w-4 h-4 text-emerald-400" />}
              </div>

              {guarantees.map((item, idx) => (
                <div key={idx} className="flex items-start gap-2.5 text-xs text-gray-300">
                  <CheckCircle2 className={`w-4 h-4 shrink-0 mt-0.5 ${isPersonal ? 'text-indigo-400' : 'text-emerald-400'}`} />
                  <div>
                    <span className="font-semibold text-white">{item.title}:</span>{' '}
                    <span className="text-gray-400">{item.desc}</span>
                  </div>
                </div>
              ))}
            </div>

          </div>
        </div>
      </div>
    </section>
  );
};
