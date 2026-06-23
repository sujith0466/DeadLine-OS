import React from 'react';
import { motion } from 'framer-motion';
import { X, Check } from 'lucide-react';
import { GlassCard } from '../UI/GlassCard';

export const WhyDeadlineOS: React.FC = () => {
  const traditional = [
    "Track Tasks manually",
    "Reactive to missed deadlines",
    "Manual scheduling and planning",
    "No awareness of future risk",
    "Single-player checklists"
  ];

  const deadlineos = [
    "Predicts Failure mathematically",
    "Creates Recovery Plans autonomously",
    "Simulates Future Outcomes instantly",
    "Continuously Monitors Risk 24/7",
    "Multi-Agent Intelligence acting as your Chief-of-Staff"
  ];

  return (
    <section id="why-deadlineos" className="py-32 relative z-10 bg-black/20">
      <div className="max-w-6xl mx-auto px-6">
        
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-black text-white mb-6">Why DeadlineOS?</h2>
          <p className="text-gray-400 text-lg max-w-2xl mx-auto">
            Traditional tools tell you what you failed to do. DeadlineOS prevents you from failing in the first place.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          
          {/* Traditional Card */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <GlassCard className="p-8 border-rose-500/20 bg-gradient-to-b from-rose-500/5 to-transparent h-full">
              <h3 className="text-2xl font-bold text-gray-300 mb-8 flex items-center gap-3">
                <X className="w-6 h-6 text-rose-500" />
                Traditional Productivity Apps
              </h3>
              <ul className="space-y-6">
                {traditional.map((item, i) => (
                  <li key={i} className="flex items-start gap-3 text-gray-400">
                    <div className="mt-1 flex-shrink-0 w-1.5 h-1.5 rounded-full bg-rose-500/50" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </GlassCard>
          </motion.div>

          {/* DeadlineOS Card */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <GlassCard className="p-8 border-primary/40 bg-gradient-to-b from-primary/10 to-transparent shadow-[0_0_50px_rgba(56,189,248,0.1)] h-full relative overflow-hidden">
              <div className="absolute top-0 right-0 w-64 h-64 bg-primary/10 rounded-full blur-3xl" />
              
              <h3 className="text-2xl font-bold text-white mb-8 flex items-center gap-3 relative z-10">
                <Check className="w-6 h-6 text-primary" />
                DeadlineOS
              </h3>
              <ul className="space-y-6 relative z-10">
                {deadlineos.map((item, i) => (
                  <li key={i} className="flex items-start gap-3 text-gray-200 font-medium">
                    <Check className="mt-0.5 flex-shrink-0 w-5 h-5 text-primary" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </GlassCard>
          </motion.div>

        </div>

      </div>
    </section>
  );
};
