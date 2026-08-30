import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown } from 'lucide-react';
import type { ProductMode } from './ProductModeSwitcher';

interface FAQSectionProps {
  mode?: ProductMode;
}

export const FAQSection: React.FC<FAQSectionProps> = ({ mode = 'personal' }) => {
  const [openIndex, setOpenIndex] = useState<number | null>(0);
  const isPersonal = mode === 'personal';

  const personalFaqs = [
    {
      question: 'How is DeadlineOS different from Notion or Todoist?',
      answer: 'Those are passive capture tools that wait for you to do the work. DeadlineOS is an active operating system with autonomous agents that forecast burnout, dynamically balance energy windows, and inject rescue workflows when momentum drops.',
    },
    {
      question: 'How does the Digital Twin simulation work?',
      answer: 'The Digital Twin runs Monte Carlo simulations of your upcoming week across circadian capacity, task estimates, and hard deadlines. It flags cognitive overload and low-energy collisions before you commit.',
    },
    {
      question: 'When is Google Gemini AI invoked?',
      answer: 'Gemini serves as a high-level semantic reasoning engine for goal breakdown, document parsing, and rescue strategy synthesis. The local engine enforces scheduling bounds and deterministic calendar limits.',
    },
    {
      question: 'Is my personal data encrypted and secure?',
      answer: 'Yes. All personal goals, habits, notes, and task timelines are stored securely with strict row-level workspace scoping and end-to-end encryption.',
    },
  ];

  const businessFaqs = [
    {
      question: 'How does DeadlineOS guarantee financial truth?',
      answer: 'Business OS enforces strict double-entry ledger arithmetic with exact decimal precision. AI never writes directly to the financial ledger; all documents and invoices pass through a human-in-the-loop staging review barrier.',
    },
    {
      question: 'Can I manage multiple commercial entities or subsidiaries?',
      answer: 'Yes. DeadlineOS provides multi-entity group consolidation with automatic detection and elimination of inter-company transfers, delivering unified group-level cash reality across all your organizations.',
    },
    {
      question: 'How does the Overdue Collection Rescue engine operate?',
      answer: 'The Collection Rescue Engine tracks invoice aging buckets and coordinates 1-click multi-channel payment reminders via WhatsApp and Email while maintaining a complete, auditable activity record.',
    },
    {
      question: 'Is there any data leakage between Business workspaces and Personal OS?',
      answer: 'None. Business workspaces are designed with strict access boundaries so team members only interact with the business data and permissions authorized for their role, keeping personal and commercial workspaces entirely isolated.',
    },
  ];

  const faqs = isPersonal ? personalFaqs : businessFaqs;

  return (
    <section id="faq" className="py-24 bg-[#0A0A0B] relative border-t border-white/5">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-black text-white">
            Frequently Asked Questions
          </h2>
          <p className="text-sm text-gray-400 mt-3">
            {isPersonal
              ? 'Everything you need to know about the Personal Operating System.'
              : 'Everything you need to know about Business OS enterprise operations.'}
          </p>
        </div>

        <div className="space-y-4">
          <AnimatePresence mode="wait">
            {faqs.map((faq, idx) => (
              <motion.div
                key={`${mode}-${idx}`}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.05 * idx }}
                className="border border-white/10 rounded-2xl bg-white/[0.02] overflow-hidden transition-colors hover:border-white/20"
              >
                <button
                  onClick={() => setOpenIndex(openIndex === idx ? null : idx)}
                  className="w-full px-6 py-4 flex items-center justify-between text-left outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 focus-visible:ring-offset-2 focus-visible:ring-offset-[#0A0A0B] rounded-2xl transition-all cursor-pointer"
                >
                  <span className="font-bold text-white text-sm md:text-base">{faq.question}</span>
                  <ChevronDown
                    className={`w-5 h-5 text-gray-400 transition-transform duration-200 ${
                      openIndex === idx ? 'rotate-180' : ''
                    }`}
                  />
                </button>
                <AnimatePresence>
                  {openIndex === idx && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.25 }}
                      className="overflow-hidden"
                    >
                      <div className="px-6 pb-5 pt-1 text-sm text-gray-400 leading-relaxed border-t border-white/5">
                        {faq.answer}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </div>
    </section>
  );
};
