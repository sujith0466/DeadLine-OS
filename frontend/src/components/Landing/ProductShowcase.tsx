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
      title: 'AI Energy Planner',
      description: 'Autonomous scheduling that dynamically aligns deep work with your circadian energy windows.',
      color: 'from-blue-400 to-indigo-500',
    },
    {
      icon: Target,
      title: 'Goals & Habit Deconstruction',
      description: 'Break complex life ambitions into micro-habits with mathematical success tracking.',
      color: 'from-emerald-400 to-teal-500',
    },
    {
      icon: Activity,
      title: 'Digital Twin Simulations',
      description: 'Simulate your upcoming week before committing to identify cognitive overload risks.',
      color: 'from-purple-400 to-pink-500',
    },
    {
      icon: ShieldAlert,
      title: 'Predictive Rescue Center',
      description: 'Detect momentum friction in real-time and automatically inject restorative workflows.',
      color: 'from-orange-400 to-red-500',
    },
    {
      icon: Terminal,
      title: 'Unified Command Center',
      description: 'Execute multi-agent operations, task reassignments, and daily reviews in natural language.',
      color: 'from-gray-400 to-slate-500',
    },
    {
      icon: FileText,
      title: 'Document Intelligence',
      description: 'Ingest syllabi, briefs, and notes into structured action timelines instantaneously.',
      color: 'from-amber-400 to-orange-500',
    },
    {
      icon: Mic,
      title: 'Voice Copilot',
      description: 'Capture stream-of-consciousness reflections hands-free while on walks or commuting.',
      color: 'from-cyan-400 to-blue-500',
    },
    {
      icon: Camera,
      title: 'Vision Intelligence',
      description: 'Transform handwritten whiteboards and notebook sketches into executable digital plans.',
      color: 'from-rose-400 to-pink-500',
    },
  ];

  const businessFeatures = [
    {
      icon: Layers,
      title: 'Document Capture & Staging',
      description: 'Multimodal ingestion with human-in-the-loop verification before anything touches the ledger.',
      color: 'from-cyan-400 to-blue-500',
    },
    {
      icon: DollarSign,
      title: 'Double-Entry Financial Ledger',
      description: 'Strict immutable transaction logs, precise decimal arithmetic, and automated invoice allocations.',
      color: 'from-emerald-400 to-teal-500',
    },
    {
      icon: TrendingUp,
      title: 'Cash Reality & Runway Days',
      description: 'Real-time deterministic burn calculations and early warning indicators for cash shortfalls.',
      color: 'from-blue-400 to-indigo-500',
    },
    {
      icon: ShieldAlert,
      title: 'Overdue Collection Rescue',
      description: 'Multi-stage collection escalation with automated WhatsApp and email reminders.',
      color: 'from-rose-400 to-red-500',
    },
    {
      icon: RefreshCw,
      title: 'Recurring Obligations Engine',
      description: 'Automated recurring billing cycles with idempotency guarantees and calendar synchronization.',
      color: 'from-purple-400 to-indigo-500',
    },
    {
      icon: Building,
      title: 'Commercial Multi-Entity',
      description: 'Consolidated reporting across multiple legal entities with automatic inter-company eliminations.',
      color: 'from-amber-400 to-orange-500',
    },
    {
      icon: Cpu,
      title: 'Zero-Bypass Business Copilot',
      description: 'Grounded financial reasoning that operates strictly on deterministic ledger state without hallucinations.',
      color: 'from-indigo-400 to-purple-500',
    },
    {
      icon: Lock,
      title: '5-Tier RBAC & Tenant Isolation',
      description: 'Strict workspace isolation, sanitized production error responses, and read-only health probes.',
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
                    Certified Enterprise <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">Commercial Architecture</span>
                  </>
                )}
              </h2>
              <p className="text-lg text-gray-400">
                {isPersonal
                  ? 'DeadlineOS integrates cognitive planning, predictive recovery, and digital twin simulations into a single autonomous personal operating system.'
                  : 'Engineered for operational precision. Certified across B0–B8 with deterministic financial integrity, multi-entity consolidation, and intelligent automation.'}
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
                  transition={{ duration: 0.45, delay: idx * 0.06 }}
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
