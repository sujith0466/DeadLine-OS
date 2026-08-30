import React from 'react';
import { ShieldCheck, CheckCircle2 } from 'lucide-react';
import type { ProductMode } from './ProductModeSwitcher';

interface TrustSecuritySectionProps {
  mode: ProductMode;
}

export const TrustSecuritySection: React.FC<TrustSecuritySectionProps> = ({ mode: _mode }) => {

  return (
    <section className="py-24 bg-[#0A0A0B] relative border-t border-white/5">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="p-8 md:p-12 rounded-3xl bg-gradient-to-br from-slate-900/60 via-slate-900/30 to-black/60 border border-white/10 relative overflow-hidden">
          <div className="relative z-10 grid grid-cols-1 lg:grid-cols-3 gap-8 items-center">
            
            <div className="lg:col-span-2">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold mb-4">
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>Verified Monolithic Production Baseline</span>
              </div>
              <h2 className="text-3xl md:text-4xl font-black text-white mb-4">
                222 / 222 Passing Backend Tests
              </h2>
              <p className="text-sm md:text-base text-gray-400 leading-relaxed mb-6">
                DeadlineOS enforces rigorous production guarantees: 162 Personal OS tests protect core personal workflows, while 60 Business OS tests guarantee multi-tenant security, double-entry ledger arithmetic, and zero Personal OS database contamination.
              </p>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
                <div className="p-3 rounded-xl bg-black/40 border border-white/5">
                  <div className="text-gray-400">Personal OS</div>
                  <div className="text-sm font-bold text-white mt-0.5">162 / 162 Passed</div>
                </div>
                <div className="p-3 rounded-xl bg-black/40 border border-white/5">
                  <div className="text-gray-400">Business OS (B1-B8)</div>
                  <div className="text-sm font-bold text-white mt-0.5">60 / 60 Passed</div>
                </div>
                <div className="p-3 rounded-xl bg-black/40 border border-white/5">
                  <div className="text-gray-400">RBAC Enforcement</div>
                  <div className="text-sm font-bold text-emerald-400 mt-0.5">5-Tier Strict</div>
                </div>
                <div className="p-3 rounded-xl bg-black/40 border border-white/5">
                  <div className="text-gray-400">Personal Contamination</div>
                  <div className="text-sm font-bold text-emerald-400 mt-0.5">0% (Strict)</div>
                </div>
              </div>
            </div>

            <div className="space-y-3 bg-black/50 p-6 rounded-2xl border border-white/5">
              <div className="text-xs font-mono text-gray-400 font-bold uppercase tracking-wider mb-2">
                PRODUCTION INVARIANTS
              </div>
              <div className="flex items-center gap-2.5 text-xs text-gray-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Deterministic Decimal Arithmetic</span>
              </div>
              <div className="flex items-center gap-2.5 text-xs text-gray-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Sanitized 500 Error Responses</span>
              </div>
              <div className="flex items-center gap-2.5 text-xs text-gray-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Read-Only Business Health Probes</span>
              </div>
              <div className="flex items-center gap-2.5 text-xs text-gray-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Supabase Storage Audit Logs</span>
              </div>
              <div className="flex items-center gap-2.5 text-xs text-gray-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Zero Bypass Grounded Copilot</span>
              </div>
            </div>

          </div>
        </div>
      </div>
    </section>
  );
};
