import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowRight, CheckCircle2 } from 'lucide-react';
import type { ProductMode } from './ProductModeSwitcher';

interface InteractiveWorkflowProps {
  mode: ProductMode;
}

export const InteractiveWorkflow: React.FC<InteractiveWorkflowProps> = ({ mode }) => {
  const isPersonal = mode === 'personal';

  const personalSteps = [
    {
      num: '01',
      title: 'Capture & Ingestion',
      subtitle: 'Multimodal Input',
      desc: 'Drop raw thoughts, voice notes, PDFs, or photos into the Command Center.',
    },
    {
      num: '02',
      title: 'Dynamic Planning',
      subtitle: 'Energy-Aware Schedule',
      desc: 'Autonomous AI schedules tasks around circadian focus windows and real deadlines.',
    },
    {
      num: '03',
      title: 'Execution & Momentum',
      subtitle: 'Cognitive Flow',
      desc: 'Work through structured deep work blocks with real-time focus analytics.',
    },
    {
      num: '04',
      title: 'Predictive Recovery',
      subtitle: 'Burnout Prevention',
      desc: 'Digital Twin simulates trajectory to inject restorative interventions before fatigue sets in.',
    },
    {
      num: '05',
      title: 'Compounding Mastery',
      subtitle: 'Daily Reflection',
      desc: 'Evening reflection synthesizes wins to continuously calibrate tomorrow’s baseline.',
    },
  ];

  const businessSteps = [
    {
      num: '01',
      title: 'Commercial Ingestion',
      subtitle: 'PDF / Audio / OCR',
      desc: 'Upload invoices, vendor receipts, or spoken agreements into the capture drawer.',
    },
    {
      num: '02',
      title: 'Staging & Verification',
      subtitle: 'Human-in-the-Loop Barrier',
      desc: 'Side-by-side verification validates extracted amounts before any ledger modification.',
    },
    {
      num: '03',
      title: 'Deterministic Ledger',
      subtitle: 'Double-Entry Truth',
      desc: 'Strict append-only transaction logs and automatic invoice payment allocations.',
    },
    {
      num: '04',
      title: 'Operational Intelligence',
      subtitle: 'Cash Reality & Risk',
      desc: 'Deterministic burn rates compute Runway Days and trigger collection rescue workflows.',
    },
    {
      num: '05',
      title: 'Automate & Consolidate',
      subtitle: 'Multi-Entity Group',
      desc: 'Recurring obligations execute automatically while inter-company transfers eliminate cleanly.',
    },
  ];

  const steps = isPersonal ? personalSteps : businessSteps;

  return (
    <section id="workflow" className="py-28 bg-[#07080A] relative border-t border-white/5">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-20">
          <AnimatePresence mode="wait">
            <motion.div
              key={mode}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.35 }}
            >
              <h2 className="text-4xl md:text-5xl font-black text-white mb-6">
                {isPersonal ? (
                  <>
                    How <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-400">Momentum</span> is Generated
                  </>
                ) : (
                  <>
                    The Deterministic <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">Financial Pipeline</span>
                  </>
                )}
              </h2>
              <p className="text-lg text-gray-400">
                {isPersonal
                  ? 'A closed-loop execution lifecycle that transforms chaotic ambition into predictable daily achievements.'
                  : 'An unyielding commercial pipeline that bridges raw invoices to verifiable ledger truth and automated collections.'}
              </p>
            </motion.div>
          </AnimatePresence>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 relative">
          {steps.map((step, idx) => (
            <motion.div
              key={`${mode}-${idx}`}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: idx * 0.08 }}
              className="p-5 rounded-2xl bg-white/[0.02] border border-white/10 relative flex flex-col justify-between hover:border-white/20 transition-colors"
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <span className="text-xs font-mono font-bold px-2 py-1 rounded bg-white/5 text-gray-400">{step.num}</span>
                  {idx < steps.length - 1 && (
                    <ArrowRight className="w-4 h-4 text-gray-600 hidden md:block" />
                  )}
                </div>
                <div className="text-xs font-semibold text-indigo-400 mb-1">{step.subtitle}</div>
                <h3 className="text-lg font-bold text-white mb-2">{step.title}</h3>
                <p className="text-xs text-gray-400 leading-relaxed">{step.desc}</p>
              </div>

              <div className="mt-4 pt-3 border-t border-white/5 flex items-center gap-1.5 text-[11px] text-emerald-400">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Deterministic Gate</span>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};
