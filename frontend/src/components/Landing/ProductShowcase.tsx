import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Calendar,
  Target,
  Activity,
  ShieldAlert,
  Terminal,
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
} from 'lucide-react';
import type { ProductMode } from './ProductModeSwitcher';

interface ProductShowcaseProps {
  mode: ProductMode;
}

export const ProductShowcase: React.FC<ProductShowcaseProps> = ({ mode }) => {
  const isPersonal = mode === 'personal';

  const personalFeatures = [
    {
      icon: Calendar,
      title: 'Plan Around Your Actual Life',
      description: 'Autonomous scheduling that dynamically aligns deep work with your circadian energy windows and real calendar limits.',
      color: 'from-blue-400 to-indigo-500',
    },
    {
      icon: Target,
      title: 'Turn Intentions into Momentum',
      description: 'Break massive ambitions into achievable daily habits with deterministic progress tracking.',
      color: 'from-emerald-400 to-teal-500',
    },
    {
      icon: Activity,
      title: 'Simulate What Comes Next',
      description: 'Your Digital Twin models upcoming weekly friction and flags burnout risks before you commit to a plan.',
      color: 'from-purple-400 to-pink-500',
    },
    {
      icon: ShieldAlert,
      title: 'Recover Before Slips Become Failures',
      description: 'When momentum drops, the Rescue Center immediately restructures priorities and protects your streaks.',
      color: 'from-orange-400 to-red-500',
    },
    {
      icon: Terminal,
      title: 'Command Center Orchestration',
      description: 'Execute multi-step daily operations and timeline reorganizations using effortless natural language.',
      color: 'from-gray-400 to-slate-500',
    },
    {
      icon: FileText,
      title: 'Instant Document Ingestion',
      description: 'Transform course syllabi, project briefs, and meeting notes into structured action plans automatically.',
      color: 'from-amber-400 to-orange-500',
    },
    {
      icon: Mic,
      title: 'Voice Thought Capture',
      description: 'Capture stream-of-consciousness reflections and tasks hands-free while walking, commuting, or exercising.',
      color: 'from-cyan-400 to-blue-500',
    },
    {
      icon: Camera,
      title: 'Vision Intelligence',
      description: 'Convert handwritten whiteboard sketches and journal pages into executable digital timelines.',
      color: 'from-rose-400 to-pink-500',
    },
  ];

  const businessFeatures = [
    {
      icon: Layers,
      title: 'Turn Inbound Chaos into Structured Records',
      description: 'Multimodal document ingestion with side-by-side human staging review before anything touches financial records.',
      color: 'from-cyan-400 to-blue-500',
    },
    {
      icon: DollarSign,
      title: 'Keep Financial Truth Deterministic',
      description: 'Immutable transaction logs, exact decimal arithmetic, and automated invoice payment allocations.',
      color: 'from-emerald-400 to-teal-500',
    },
    {
      icon: TrendingUp,
      title: 'See Where the Business Stands',
      description: 'Real-time cash reality calculations and burn velocity curves give you unshakeable runway visibility.',
      color: 'from-blue-400 to-indigo-500',
    },
    {
      icon: ShieldAlert,
      title: 'Recover Overdue Receivables',
      description: 'Intelligent multi-stage collection workflows deliver 1-click WhatsApp and email reminders to accelerate cashflow.',
      color: 'from-rose-400 to-red-500',
    },
    {
      icon: RefreshCw,
      title: 'Automate Recurring Obligations',
      description: 'Recurring retainer billing, subscription renewals, and vendor obligations execute reliably without double-billing.',
      color: 'from-purple-400 to-indigo-500',
    },
    {
      icon: Building,
      title: 'Operate Across Multiple Entities',
      description: 'Consolidated financial views across multiple legal entities with automatic elimination of inter-company transfers.',
      color: 'from-amber-400 to-orange-500',
    },
    {
      icon: Cpu,
      title: 'Grounded Business Copilot',
      description: 'Financial intelligence that queries authoritative ledger state directly, avoiding AI guesswork or hallucinations.',
      color: 'from-indigo-400 to-purple-500',
    },
    {
      icon: Lock,
      title: 'Strict Workspace Boundaries',
      description: 'Enterprise tenant isolation, role-based member permissions, and read-only diagnostic health monitoring.',
      color: 'from-emerald-400 to-cyan-500',
    },
  ];

  const features = isPersonal ? personalFeatures : businessFeatures;

  return (
    <section id="features" className="py-32 bg-[#0A0A0B] relative overflow-hidden">
      {/* Ambient background glows */}
      <div className="absolute top-1/4 -right-1/4 w-[500px] h-[500px] bg-indigo-500/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-1/4 -left-1/4 w-[500px] h-[500px] bg-purple-500/10 rounded-full blur-[120px] pointer-events-none" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
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
                    A Complete Unified <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">Personal Ecosystem</span>
                  </>
                ) : (
                  <>
                    Complete Operational <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">Commercial Control</span>
                  </>
                )}
              </h2>
              <p className="text-lg text-gray-400">
                {isPersonal
                  ? 'DeadlineOS combines intelligent scheduling, predictive recovery, and digital twin simulations into a single calm, autonomous operating environment.'
                  : 'Engineered for operational clarity. Unified financial truth, automated collections, recurring cycles, and multi-entity intelligence in one coherent system.'}
              </p>
            </motion.div>
          </AnimatePresence>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <AnimatePresence mode="wait">
            {features.map((feature, idx) => {
              const Icon = feature.icon;
              return (
                <motion.div
                  key={`${mode}-${idx}`}
                  initial={{ opacity: 0, y: 25 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: '-50px' }}
                  transition={{ duration: 0.45, delay: idx * 0.05 }}
                  className="group relative p-6 rounded-2xl bg-white/[0.02] border border-white/10 hover:bg-white/[0.04] transition-all hover:-translate-y-1 overflow-hidden"
                >
                  <div className={`absolute inset-0 bg-gradient-to-br ${feature.color} opacity-0 group-hover:opacity-[0.04] transition-opacity duration-500`} />
                  <div className="relative z-10">
                    <div
                      className={`w-12 h-12 rounded-xl bg-gradient-to-br ${feature.color} flex items-center justify-center text-white mb-6 shadow-lg shadow-black/20 group-hover:scale-110 transition-transform duration-300`}
                    >
                      <Icon className="w-6 h-6" />
                    </div>
                    <h3 className="text-xl font-bold text-white mb-3 group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-white group-hover:to-gray-300 transition-all">
                      {feature.title}
                    </h3>
                    <p className="text-sm text-gray-400 leading-relaxed font-normal">{feature.description}</p>
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
