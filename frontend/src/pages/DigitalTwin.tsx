import React, { useState, useEffect } from 'react';
import { 
  Zap, Activity, GitBranch, Target, ShieldAlert, Cpu,
  AlertTriangle, ArrowRight, Box, Loader2, Play
} from 'lucide-react';
import { GlassCard } from '../components/UI/GlassCard';
import { GradientButton } from '../components/UI/GradientButton';
import { DeadlineOSApi } from '../api';
import { motion, AnimatePresence } from 'framer-motion';
import { useCountUp } from '../hooks/useCountUp';

const AnimatedKpi = React.memo(({ value, suffix = '', label, icon: Icon, delay = 0, colorClass = "text-white" }: any) => {
  const isNumber = typeof value === 'number';
  const count = useCountUp(isNumber ? value : 0, 1.5);
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.5, ease: "easeOut" }}
    >
      <GlassCard className="p-4 flex flex-col hover:-translate-y-1 transition-transform duration-300">
        <div className="flex justify-between items-start mb-2">
          <div className="p-1.5 rounded-lg bg-white/5 border border-white/10">
            <Icon className="w-4 h-4 text-gray-400" />
          </div>
        </div>
        <div>
          <div className={`text-2xl font-black mb-1 tracking-tight ${colorClass}`}>
            {isNumber ? <span ref={count.ref}>{count.value}</span> : <span>{value}</span>}
            {suffix}
          </div>
          <p className="text-[10px] text-gray-400 uppercase tracking-wider font-semibold">{label}</p>
        </div>
      </GlassCard>
    </motion.div>
  );
});

export const DigitalTwin: React.FC = () => {
  const [scenario, setScenario] = useState({ action: 'delay_task', task: 'React Assignment', delay_days: 1 });
  const [simulation, setSimulation] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [analytics, setAnalytics] = useState<any>(null);

  useEffect(() => {
    DeadlineOSApi.getAnalyticsOverview().then(res => setAnalytics(res.data));
  }, []);

  const handleSimulate = async () => {
    setLoading(true);
    setSimulation(null);
    try {
      const res = await DeadlineOSApi.runDigitalTwin({ scenario });
      setSimulation(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const applyPreset = React.useCallback((action: string, task: string, delay: number) => {
    setScenario({ action, task, delay_days: delay });
  }, []);

  return (
    <div className="space-y-8 pb-12">
      
      {/* SECTION A: Twin Intelligence KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <AnimatedKpi value={analytics?.deadline_success_rate || 88} suffix="%" label="Success Probability" icon={Target} delay={0.1} colorClass="text-emerald-400" />
        <AnimatedKpi value={analytics?.future_risk_forecast || 'Low'} label="Future Risk" icon={ShieldAlert} delay={0.2} colorClass="text-cyan-400" />
        <AnimatedKpi value={82} suffix="%" label="Schedule Stability" icon={Activity} delay={0.3} colorClass="text-white" />
        <AnimatedKpi value={94} suffix="%" label="Prediction Confidence" icon={Cpu} delay={0.4} colorClass="text-purple-400" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* LEFT COLUMN: Scenario Builder */}
        <div className="lg:col-span-4 space-y-6">
          <GlassCard className="border-t-2 border-t-emerald-500">
            <h2 className="text-sm font-bold text-white mb-4 uppercase tracking-widest flex items-center gap-2">
              <Box className="w-4 h-4 text-emerald-400" /> Scenario Builder
            </h2>
            
            <div className="space-y-4 mb-6">
              <div>
                <label className="block text-xs font-bold text-gray-400 mb-1.5 uppercase">Simulation Vector</label>
                <select 
                  className="w-full bg-black/40 border border-white/10 rounded-lg p-2 text-sm text-white outline-none focus:border-emerald-500 transition-colors"
                  value={scenario.action}
                  onChange={(e) => setScenario({...scenario, action: e.target.value})}
                >
                  <option value="DELAY_TASK" className="bg-slate-900 text-white">Delay Task</option>
                  <option value="SKIP_TASK" className="bg-slate-900 text-white">Skip Task</option>
                  <option value="ADD_TASK" className="bg-slate-900 text-white">Add New Task</option>
                  <option value="INCREASE_WORKLOAD" className="bg-slate-900 text-white">Increase Workload</option>
                  <option value="REDUCE_HOURS" className="bg-slate-900 text-white">Reduce Available Hours</option>
                  <option value="MOVE_DEADLINE" className="bg-slate-900 text-white">Shift Deadlines</option>
                </select>
              </div>
              
              <div>
                <label className="block text-xs font-bold text-gray-400 mb-1.5 uppercase">Target Parameter</label>
                <input 
                  type="text" 
                  className="w-full bg-black/40 border border-white/10 rounded-lg p-2 text-sm text-white outline-none focus:border-emerald-500 transition-colors"
                  value={scenario.task}
                  onChange={(e) => setScenario({...scenario, task: e.target.value})}
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-400 mb-1.5 uppercase">Multiplier / Delta</label>
                <input 
                  type="number" 
                  className="w-full bg-black/40 border border-white/10 rounded-lg p-2 text-sm text-white outline-none focus:border-emerald-500 transition-colors"
                  value={scenario.delay_days}
                  onChange={(e) => setScenario({...scenario, delay_days: Number(e.target.value)})}
                />
              </div>
            </div>

            <GradientButton className="w-full flex justify-center items-center gap-2" onClick={handleSimulate} disabled={loading}>
              {loading ? <><Loader2 className="w-4 h-4 animate-spin"/> Executing Simulation...</> : <><Play className="w-4 h-4" fill="currentColor"/> Inject Scenario</>}
            </GradientButton>
          </GlassCard>

          {/* Preset Simulation Cards */}
          <GlassCard className="bg-cyan-500/5 border-cyan-500/20">
            <h2 className="text-xs font-bold text-cyan-400 mb-3 uppercase tracking-widest flex items-center gap-2">
              <Zap className="w-4 h-4" /> Quick Presets
            </h2>
            <div className="space-y-2">
              <button onClick={() => applyPreset('DELAY_TASK', 'Critical Path', 1)} className="w-full text-left p-2 rounded-lg bg-black/40 border border-white/5 hover:border-cyan-500/50 hover:bg-cyan-500/10 transition-colors text-sm text-white flex justify-between items-center group">
                Delay Critical Task <ArrowRight className="w-3 h-3 text-cyan-400 opacity-0 group-hover:opacity-100 transition-opacity" />
              </button>
              <button onClick={() => applyPreset('REDUCE_HOURS', 'Daily Schedule', 4)} className="w-full text-left p-2 rounded-lg bg-black/40 border border-white/5 hover:border-cyan-500/50 hover:bg-cyan-500/10 transition-colors text-sm text-white flex justify-between items-center group">
                Miss One Day <ArrowRight className="w-3 h-3 text-cyan-400 opacity-0 group-hover:opacity-100 transition-opacity" />
              </button>
              <button onClick={() => applyPreset('INCREASE_WORKLOAD', 'Deep Work', 2)} className="w-full text-left p-2 rounded-lg bg-black/40 border border-white/5 hover:border-emerald-500/50 hover:bg-emerald-500/10 transition-colors text-sm text-white flex justify-between items-center group">
                Increase Deep Work <ArrowRight className="w-3 h-3 text-emerald-400 opacity-0 group-hover:opacity-100 transition-opacity" />
              </button>
            </div>
          </GlassCard>
        </div>

        {/* RIGHT COLUMN: Results & Dashboards */}
        <div className="lg:col-span-8 space-y-6">
          {simulation ? (
            <AnimatePresence>
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
                
                {/* SECTION C: Scenario Impact Dashboard (Current vs Projected) */}
                <GlassCard className="relative overflow-hidden border-rose-500/30">
                  <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/5 to-rose-500/10 pointer-events-none" />
                  <h3 className="text-sm font-bold text-white mb-6 uppercase tracking-widest flex items-center gap-2">
                    <Activity className="w-4 h-4 text-rose-400" /> Scenario Impact Delta
                  </h3>
                  
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    {/* Success Rate */}
                    <div className="p-3 bg-black/40 rounded-xl border border-white/5">
                      <p className="text-[10px] text-gray-500 font-bold uppercase mb-2">Success Rate</p>
                      <div className="flex items-center justify-between">
                        <span className="text-xl font-black text-emerald-400">{simulation?.current_state?.success_probability || analytics?.deadline_success_rate || 88}%</span>
                        <ArrowRight className="w-4 h-4 text-gray-600 mx-2" />
                        <span className="text-xl font-black text-rose-500">{simulation?.projected_state?.success_probability || 0}%</span>
                      </div>
                    </div>
                    {/* Risk Level */}
                    <div className="p-3 bg-black/40 rounded-xl border border-white/5">
                      <p className="text-[10px] text-gray-500 font-bold uppercase mb-2">Risk Level</p>
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-black text-emerald-400">CURRENT</span>
                        <ArrowRight className="w-4 h-4 text-gray-600 mx-1" />
                        <span className="text-sm font-black text-rose-500">{simulation?.projected_state?.risk_level || 'Unknown'}</span>
                      </div>
                    </div>
                    {/* Stability */}
                    <div className="p-3 bg-black/40 rounded-xl border border-white/5">
                      <p className="text-[10px] text-gray-500 font-bold uppercase mb-2">Stability</p>
                      <div className="flex items-center justify-between">
                        <span className="text-xl font-black text-emerald-400">82%</span>
                        <ArrowRight className="w-4 h-4 text-gray-600 mx-2" />
                        <span className="text-xl font-black text-rose-500">{simulation?.schedule_stability || 0}%</span>
                      </div>
                    </div>
                    {/* Risk Score */}
                    <div className="p-3 bg-black/40 rounded-xl border border-white/5">
                      <p className="text-[10px] text-gray-500 font-bold uppercase mb-2">Risk Score</p>
                      <div className="flex items-center justify-between">
                        <span className="text-xl font-black text-emerald-400">{simulation?.current_state?.risk_score || 0}</span>
                        <ArrowRight className="w-4 h-4 text-gray-600 mx-2" />
                        <span className="text-xl font-black text-rose-500">{simulation?.projected_state?.risk_score || 0}</span>
                      </div>
                    </div>
                  </div>
                </GlassCard>

                {/* SECTION D: Cascade Effect Visualization */}
                <GlassCard className="bg-black/20">
                  <h3 className="text-sm font-bold text-white mb-6 uppercase tracking-widest flex items-center gap-2">
                    <GitBranch className="w-4 h-4 text-cyan-400" /> Cascade Effect Simulation
                  </h3>
                  <div className="flex flex-col md:flex-row items-center justify-between gap-2 overflow-x-auto pb-4 hide-scrollbar">
                    {simulation?.cascade?.map((node: any, idx: number) => (
                      <React.Fragment key={idx}>
                        <motion.div 
                          initial={{ scale: 0.8, opacity: 0 }} 
                          animate={{ scale: 1, opacity: 1 }} 
                          transition={{ delay: idx * 0.2 }}
                          className="flex-shrink-0 w-40 p-3 rounded-xl border border-cyan-500/20 bg-cyan-500/5 text-center shadow-[0_0_15px_rgba(34,211,238,0.1)] relative"
                        >
                          <span className="block text-[10px] font-black text-cyan-400 uppercase tracking-widest mb-1">{node.step}</span>
                          <p className="text-xs text-white">{node.desc}</p>
                        </motion.div>
                        {idx < simulation?.cascade?.length - 1 && (
                          <motion.div 
                            initial={{ opacity: 0 }} 
                            animate={{ opacity: 1 }} 
                            transition={{ delay: idx * 0.2 + 0.1 }}
                            className="hidden md:block w-8 h-0.5 bg-gradient-to-r from-cyan-500 to-transparent relative"
                          >
                            <div className="absolute right-0 -top-1 w-0 h-0 border-t-4 border-t-transparent border-b-4 border-b-transparent border-l-4 border-l-cyan-500" />
                          </motion.div>
                        )}
                        {idx < simulation?.cascade?.length - 1 && (
                          <div className="block md:hidden h-4 w-0.5 bg-cyan-500 my-1" />
                        )}
                      </React.Fragment>
                    ))}
                  </div>
                </GlassCard>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* SECTION E: Future Timeline Simulation */}
                  <GlassCard>
                    <h3 className="text-xs font-bold text-gray-400 mb-4 uppercase tracking-widest flex items-center gap-2">
                      <Activity className="w-4 h-4 text-purple-400" /> Future Timeline Trajectory
                    </h3>
                    <div className="space-y-4 relative before:absolute before:inset-0 before:ml-2.5 before:-translate-x-px before:h-full before:w-0.5 before:bg-white/10">
                      {['Today', 'Tomorrow', '3 Days', '1 Week', 'Final Outcome'].map((day, idx) => (
                        <div key={idx} className="relative flex items-center gap-4">
                          <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center bg-black z-10 ${idx === 4 ? 'border-rose-500 shadow-[0_0_10px_rgba(244,63,94,0.5)]' : 'border-purple-500'}`}>
                            {idx === 4 && <AlertTriangle className="w-3 h-3 text-rose-500" />}
                          </div>
                          <div className="flex-1 bg-white/5 p-2 rounded-lg border border-white/5">
                            <span className="text-[10px] font-bold text-gray-400 uppercase">{day}</span>
                            <p className="text-xs text-white">{idx === 4 ? 'Failure state established.' : 'Constraint tightening.'}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </GlassCard>

                  {/* SECTION F: Twin Recommendations */}
                  <GlassCard className="bg-primary/5 border-primary/20">
                    <h3 className="text-xs font-bold text-primary mb-4 uppercase tracking-widest flex items-center gap-2">
                      <Target className="w-4 h-4" /> AI Strategy Directive
                    </h3>
                    <div className="space-y-3">
                      {simulation?.recommendations?.map((rec: any, idx: number) => (
                        <div key={idx} className="p-3 bg-black/40 rounded-lg border border-primary/20">
                          <div className="flex justify-between items-center mb-1">
                            <span className="text-[10px] font-black text-primary uppercase tracking-wider">AI Insight</span>
                            <span className="text-[10px] font-bold text-emerald-400 bg-emerald-400/10 px-2 py-0.5 rounded-full">{rec.confidence}% Conf.</span>
                          </div>
                          <p className="text-sm text-gray-200">{rec.action}</p>
                        </div>
                      ))}
                    </div>
                  </GlassCard>
                </div>

              </motion.div>
            </AnimatePresence>
          ) : (
            <GlassCard className="h-full min-h-[500px] flex flex-col items-center justify-center text-center py-20 border-2 border-dashed border-white/10">
              {loading ? (
                <div className="flex flex-col items-center">
                  <Loader2 className="w-12 h-12 text-emerald-500 animate-spin mb-4" />
                  <p className="text-sm font-bold uppercase tracking-widest text-emerald-400 animate-pulse">Running Physics Engine...</p>
                </div>
              ) : (
                <div className="flex flex-col items-center">
                  <Box className="w-16 h-16 text-white/10 mb-4" />
                  <h2 className="text-xl font-bold text-gray-300 mb-2">Laboratory Offline</h2>
                  <p className="text-gray-500 max-w-sm">
                    Configure a scenario vector or load a preset to visualize potential future cascades.
                  </p>
                </div>
              )}
            </GlassCard>
          )}
        </div>
      </div>
    </div>
  );
};
