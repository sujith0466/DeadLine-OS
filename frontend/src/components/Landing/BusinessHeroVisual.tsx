import React from 'react';
import { DollarSign, Layers, ShieldCheck, ArrowUpRight, TrendingUp, RefreshCw, CheckCircle2 } from 'lucide-react';

export const BusinessHeroVisual: React.FC = () => {
  return (
    <div className="w-full relative" aria-hidden="true">
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-emerald-500/10 to-transparent blur-3xl" />
      <div className="relative aspect-[21/10] md:aspect-[21/9] rounded-2xl border border-white/10 bg-[#0B0C10]/90 backdrop-blur-2xl shadow-[0_0_100px_rgba(0,0,0,0.8)] flex flex-col overflow-hidden">
        
        {/* Window Controls & Summary Bar */}
        <div className="h-10 border-b border-white/5 flex items-center justify-between px-4 bg-white/5 gap-2 w-full shrink-0">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500/80" />
            <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
            <div className="w-3 h-3 rounded-full bg-green-500/80" />
            <span className="ml-2 font-mono text-xs text-gray-400 font-bold tracking-widest hidden sm:inline">
              DEADLINE BUSINESS OS — OPERATIONAL VIEW
            </span>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-[10px] text-emerald-400 font-semibold">
              <ShieldCheck className="w-3 h-3" />
              <span>RUNWAY: 94 DAYS</span>
            </div>
            <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-[10px] text-indigo-400 font-semibold hidden md:flex">
              <Layers className="w-3 h-3" />
              <span>3 CONSOLIDATED ENTITIES</span>
            </div>
          </div>
        </div>

        {/* Dashboard Content */}
        <div className="flex-1 flex gap-4 p-4 h-full relative overflow-hidden text-left">
          
          {/* Left Column: Receivables & Collection Rescue */}
          <div className="w-1/3 flex flex-col gap-3">
            <div className="bg-white/5 border border-white/5 rounded-xl p-3.5 flex flex-col gap-2.5">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold text-gray-400 tracking-wider uppercase">COLLECTION RESCUE</span>
                <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
              </div>

              {/* Overdue Item */}
              <div className="bg-rose-500/10 border border-rose-500/20 rounded-lg p-2.5">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="text-xs font-bold text-white">INV-2026-088</div>
                    <div className="text-[10px] text-rose-300">Apex Media Corp • 14d Overdue</div>
                  </div>
                  <span className="text-xs font-mono font-bold text-rose-400">₹125,000</span>
                </div>
                <div className="mt-2 flex items-center justify-between text-[9px] text-gray-400 pt-1.5 border-t border-rose-500/20">
                  <span className="text-emerald-400 flex items-center gap-1">
                    <CheckCircle2 className="w-2.5 h-2.5" /> 1-Click Reminder Sent
                  </span>
                  <span>WhatsApp + Email</span>
                </div>
              </div>

              {/* Current Receivable */}
              <div className="bg-slate-900/60 border border-white/5 rounded-lg p-2.5">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="text-xs font-bold text-white">INV-2026-092</div>
                    <div className="text-[10px] text-slate-400">Nexus Labs • Due in 3d</div>
                  </div>
                  <span className="text-xs font-mono font-bold text-emerald-400">₹480,000</span>
                </div>
              </div>
            </div>

            {/* Aging Buckets Mini Card */}
            <div className="bg-white/5 border border-white/5 rounded-xl p-3 flex-1 flex flex-col justify-between">
              <div className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">RECEIVABLE AGING</div>
              <div className="grid grid-cols-3 gap-1.5 text-center mt-1">
                <div className="bg-black/30 p-1.5 rounded border border-white/5">
                  <div className="text-[9px] text-gray-400">Current</div>
                  <div className="text-xs font-bold text-white mt-0.5">₹840k</div>
                </div>
                <div className="bg-black/30 p-1.5 rounded border border-white/5">
                  <div className="text-[9px] text-amber-400">1-30d</div>
                  <div className="text-xs font-bold text-amber-400 mt-0.5">₹125k</div>
                </div>
                <div className="bg-black/30 p-1.5 rounded border border-white/5">
                  <div className="text-[9px] text-rose-400">30d+</div>
                  <div className="text-xs font-bold text-rose-400 mt-0.5">₹45k</div>
                </div>
              </div>
            </div>
          </div>

          {/* Middle Column: Cash Reality & Runway Velocity */}
          <div className="w-1/3 flex flex-col gap-3">
            {/* Cash Position Card */}
            <div className="bg-gradient-to-br from-emerald-500/10 via-slate-900/40 to-indigo-500/10 border border-emerald-500/20 rounded-xl p-4 flex flex-col justify-between relative overflow-hidden flex-1">
              <div>
                <div className="flex items-center justify-between text-xs text-gray-400">
                  <span>Confirmed Cash Reality</span>
                  <DollarSign className="w-4 h-4 text-emerald-400" />
                </div>
                <div className="text-2xl font-black text-white mt-1 tracking-tight">₹1,450,000</div>
                <div className="flex items-center gap-1 text-[10px] text-emerald-400 mt-1">
                  <ArrowUpRight className="w-3 h-3" />
                  <span>+₹185,000 net cashflow this cycle</span>
                </div>
              </div>

              {/* Runway Curve Visualization */}
              <div className="my-2 h-14 w-full bg-black/40 rounded-lg p-2 flex items-end justify-between gap-1 border border-white/5">
                {[45, 52, 48, 65, 58, 72, 85, 94].map((val, idx) => (
                  <div key={idx} className="flex-1 flex flex-col items-center gap-1 h-full justify-end">
                    <div 
                      style={{ height: `${(val / 94) * 100}%` }}
                      className="w-full bg-gradient-to-t from-emerald-600 to-emerald-400 rounded-sm"
                    />
                  </div>
                ))}
              </div>

              <div className="flex justify-between items-center text-[10px] text-gray-400 pt-1 border-t border-white/5">
                <span>Burn Velocity: ₹15,400/day</span>
                <span className="font-semibold text-emerald-400">Verified Ledger State</span>
              </div>
            </div>

            {/* Cash Alert State */}
            <div className="bg-white/5 border border-white/5 rounded-xl p-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-emerald-400" />
                <div>
                  <div className="text-xs font-bold text-white">Cash Risk Status</div>
                  <div className="text-[9px] text-gray-400">Runway Safe (&gt;90 Days)</div>
                </div>
              </div>
              <span className="px-2 py-0.5 bg-emerald-500/20 text-emerald-400 text-[10px] font-bold rounded">NORMAL</span>
            </div>
          </div>

          {/* Right Column: Recurring Automation & Multi-Entity Group */}
          <div className="w-1/3 flex flex-col gap-3">
            {/* Multi-Entity Group Consolidation */}
            <div className="bg-white/5 border border-white/5 rounded-xl p-3.5">
              <div className="flex items-center justify-between text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-2">
                <span>GROUP CONSOLIDATION</span>
                <Layers className="w-3.5 h-3.5 text-indigo-400" />
              </div>
              
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs text-gray-300">
                  <span>Mumbai HQ Entity</span>
                  <span className="font-mono font-bold text-white">₹920,000</span>
                </div>
                <div className="flex justify-between text-xs text-gray-300">
                  <span>Bangalore Division</span>
                  <span className="font-mono font-bold text-white">₹380,000</span>
                </div>
                <div className="flex justify-between text-xs text-gray-300">
                  <span>US Branch (Delaware)</span>
                  <span className="font-mono font-bold text-white">₹225,000</span>
                </div>
              </div>

              <div className="mt-2.5 pt-2 border-t border-white/10 flex justify-between items-center text-[10px]">
                <span className="text-gray-400">Inter-Entity Eliminated</span>
                <span className="text-amber-400 font-mono font-bold">-₹75,000</span>
              </div>
            </div>

            {/* Recurring Automation Engine */}
            <div className="flex-1 bg-black/40 border border-white/5 rounded-xl p-3.5 flex flex-col justify-between relative overflow-hidden">
              <div className="flex items-center justify-between text-[10px] font-bold text-gray-500 tracking-wider">
                <span>AUTOMATION RUNNER</span>
                <RefreshCw className="w-3 h-3 text-indigo-400" />
              </div>

              <div className="space-y-2 my-2">
                <div className="flex items-center gap-2 text-[10px] text-gray-300">
                  <span className="w-1.5 h-1.5 rounded-full bg-indigo-400" />
                  <span className="truncate">Auto-generated retainer invoice</span>
                </div>
                <div className="flex items-center gap-2 text-[10px] text-gray-300">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                  <span className="truncate">Reconciled payment: Stripe #TX-9021</span>
                </div>
                <div className="flex items-center gap-2 text-[10px] text-gray-300">
                  <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
                  <span className="truncate">Copilot ledger grounding verified</span>
                </div>
              </div>

              <div className="text-[9px] font-mono text-indigo-300/80 pt-1 border-t border-white/5 flex justify-between">
                <span>Idempotency: Guaranteed</span>
                <span>Audit: 100% Clean</span>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};
