import React, { useState, useEffect } from 'react';
import { 
  LifeBuoy, AlertTriangle, ShieldAlert, AlertOctagon, Activity, 
  Box, Cpu, Target, RefreshCw,
  Loader2, Zap, BrainCircuit
} from 'lucide-react';
import { GlassCard } from '../components/UI/GlassCard';
import { GradientButton } from '../components/UI/GradientButton';
import { Badge } from '../components/UI/Badge';
import { DeadlineOSApi } from '../api';
import { motion, AnimatePresence } from 'framer-motion';
import { useCountUp } from '../hooks/useCountUp';

const AnimatedKpi = ({ value, suffix = '', label, icon: Icon, delay = 0, colorClass = "text-white", borderClass = "border-white/10" }: any) => {
  const isNumber = typeof value === 'number';
  const count = useCountUp(isNumber ? value : 0, 1.5);
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.5, ease: "easeOut" }}
    >
      <GlassCard className={`p-4 flex flex-col hover:-translate-y-1 transition-transform duration-300 ${borderClass}`}>
        <div className="flex justify-between items-start mb-2">
          <div className="p-1.5 rounded-lg bg-black/40 border border-white/5">
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
};

export const Rescue: React.FC = () => {
  const [tasks, setTasks] = useState<any[]>([]);
  const [analytics, setAnalytics] = useState<any>(null);
  const [rescuePlan, setRescuePlan] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [detecting, setDetecting] = useState(false);

  // Computed state
  const atRiskTasks = tasks.filter(t => t.priority_score > 80);
  const criticalCount = atRiskTasks.length;
  
  // Dummy values for visual simulation since backend doesn't provide these directly yet
  const overloadCount = tasks.length > 5 ? Math.floor(tasks.length / 3) : 0;
  const failureCount = criticalCount > 0 ? 1 : 0;



  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        const [tasksRes, analyticsRes] = await Promise.all([
          DeadlineOSApi.getTasks(),
          DeadlineOSApi.getAnalyticsOverview()
        ]);
        setTasks(tasksRes.tasks || []);
        setAnalytics(analyticsRes.data || null);
      } catch (err) {}
    };
    fetchInitialData();
  }, []);

  const handleDetectRisks = () => {
    setDetecting(true);
    setTimeout(() => setDetecting(false), 1500); // Simulate detection scan
  };

  const handleRescue = async () => {
    setLoading(true);
    try {
      const result = await DeadlineOSApi.runRescueAgent({
        tasks,
        availability: { daily_available_hours: 4 }
      });
      setRescuePlan(result.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 pb-12">
      


      {/* 3. Executive Risk Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <AnimatedKpi value={criticalCount} label="Critical Risks" icon={AlertOctagon} delay={0.1} colorClass={criticalCount > 0 ? "text-rose-500" : "text-gray-300"} borderClass={criticalCount > 0 ? "border-rose-500/30" : ""} />
        <AnimatedKpi value={rescuePlan ? rescuePlan.success_probability : (analytics?.deadline_success_rate || 0)} suffix="%" label="Recovery Probability" icon={Target} delay={0.2} colorClass="text-emerald-400" />
        <AnimatedKpi value={94} suffix="%" label="Intervention Score" icon={Zap} delay={0.3} colorClass="text-amber-400" />
        <AnimatedKpi value={rescuePlan ? 98 : 0} suffix="%" label="Rescue Confidence" icon={ShieldAlert} delay={0.4} colorClass="text-purple-400" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* LEFT COLUMN */}
        <div className="lg:col-span-4 space-y-6">
          
          {/* Threat Detection Panel */}
          <GlassCard className="border-t-2 border-t-rose-500">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-sm font-bold text-white uppercase tracking-widest flex items-center gap-2">
                <Activity className="w-4 h-4 text-rose-500" /> Threat Detection
              </h3>
              <button 
                onClick={handleDetectRisks}
                className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-gray-300 transition-colors"
                title="Run Deep Scan"
              >
                <RefreshCw className={`w-4 h-4 ${detecting ? 'animate-spin text-rose-500' : ''}`} />
              </button>
            </div>

            <div className="space-y-3 mb-6">
              <div className="flex justify-between items-center p-3 rounded-lg bg-black/40 border border-white/5">
                <span className="text-sm font-medium text-gray-300">Overdue Tasks</span>
                <Badge variant={failureCount > 0 ? 'danger' : 'success'}>{failureCount}</Badge>
              </div>
              <div className="flex justify-between items-center p-3 rounded-lg bg-black/40 border border-rose-500/10">
                <span className="text-sm font-medium text-gray-300">At-Risk Tasks</span>
                <Badge variant={criticalCount > 0 ? 'warning' : 'neutral'}>{criticalCount}</Badge>
              </div>
              <div className="flex justify-between items-center p-3 rounded-lg bg-black/40 border border-white/5">
                <span className="text-sm font-medium text-gray-300">High Workload Tasks</span>
                <Badge variant="info">{overloadCount}</Badge>
              </div>
              <div className="flex justify-between items-center p-3 rounded-lg bg-black/40 border border-white/5">
                <span className="text-sm font-medium text-gray-300">Predicted Failures</span>
                <Badge variant={criticalCount > 2 ? 'danger' : 'neutral'}>{criticalCount > 2 ? 1 : 0}</Badge>
              </div>
            </div>

            <GradientButton 
              variant="danger" 
              className="w-full flex justify-center items-center gap-2" 
              onClick={handleRescue} 
              disabled={loading || criticalCount === 0}
            >
              {loading ? <><Loader2 className="w-4 h-4 animate-spin"/> Simulating Recovery...</> : <><LifeBuoy className="w-4 h-4" /> Deploy Rescue Agent</>}
            </GradientButton>
            {criticalCount === 0 && <p className="text-center text-xs text-emerald-400 mt-2 font-bold">No active threats detected.</p>}
          </GlassCard>

          {/* AI Interventions */}
          <GlassCard className="bg-orange-500/5 border-orange-500/20">
            <h3 className="text-sm font-bold text-orange-400 mb-4 uppercase tracking-widest flex items-center gap-2">
              <Zap className="w-4 h-4" /> Recommended Interventions
            </h3>
            <div className="space-y-3">
              <div className="p-3 bg-black/40 rounded-lg border border-rose-500/20 border-l-4 border-l-rose-500">
                <div className="flex justify-between items-center mb-1">
                  <span className="text-[10px] font-black text-rose-500 uppercase tracking-wider">High Priority</span>
                  <span className="text-[10px] font-bold text-emerald-400 bg-emerald-400/10 px-2 py-0.5 rounded-full">98% Conf.</span>
                </div>
                <p className="text-sm text-gray-200">Re-allocate 2 hours from low-priority tasks to unblock critical path.</p>
              </div>
              <div className="p-3 bg-black/40 rounded-lg border border-amber-500/20 border-l-4 border-l-amber-500">
                <div className="flex justify-between items-center mb-1">
                  <span className="text-[10px] font-black text-amber-500 uppercase tracking-wider">Medium Priority</span>
                  <span className="text-[10px] font-bold text-emerald-400 bg-emerald-400/10 px-2 py-0.5 rounded-full">85% Conf.</span>
                </div>
                <p className="text-sm text-gray-200">Reduce parallel active workstreams to maximize single-task velocity.</p>
              </div>
            </div>
          </GlassCard>

          {/* Live Agent Activity */}
          <GlassCard>
            <h3 className="text-sm font-bold text-gray-400 mb-4 uppercase tracking-widest flex items-center gap-2">
              <Cpu className="w-4 h-4" /> Live Orchestration
            </h3>
            <div className="space-y-2">
              <div className="flex justify-between items-center p-2 rounded bg-white/5">
                <span className="text-xs font-bold text-rose-400">Rescue Agent</span>
                <Badge variant={loading ? 'info' : rescuePlan ? 'success' : 'neutral'}>
                  {loading ? 'Running' : rescuePlan ? 'Complete' : 'Idle'}
                </Badge>
              </div>
              <div className="flex justify-between items-center p-2 rounded bg-white/5">
                <span className="text-xs font-bold text-cyan-400">Digital Twin</span>
                <Badge variant={loading ? 'info' : 'success'}>{loading ? 'Running' : 'Complete'}</Badge>
              </div>
              <div className="flex justify-between items-center p-2 rounded bg-white/5">
                <span className="text-xs font-bold text-indigo-400">Intervention Engine</span>
                <Badge variant={loading ? 'warning' : 'neutral'}>{loading ? 'Standby' : 'Idle'}</Badge>
              </div>
            </div>
          </GlassCard>

        </div>

        {/* RIGHT COLUMN */}
        <div className="lg:col-span-8 space-y-6">
          
          {/* Risk Analysis & Twin Simulation Hero */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <GlassCard className="relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-rose-500/10 to-transparent pointer-events-none" />
              <h3 className="text-sm font-bold text-white mb-6 uppercase tracking-widest flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-500" /> Risk Analysis Center
              </h3>
              
              <div className="mb-6">
                <p className="text-xs text-gray-400 uppercase font-bold mb-1">Assessed Risk Level</p>
                <div className="flex items-end gap-3">
                  <span className={`text-4xl font-black ${criticalCount > 2 ? 'text-rose-500' : criticalCount > 0 ? 'text-amber-500' : 'text-emerald-500'}`}>
                    {criticalCount > 2 ? 'HIGH' : criticalCount > 0 ? 'MEDIUM' : 'LOW'}
                  </span>
                </div>
              </div>

              <div className="space-y-4">
                <p className="text-xs text-gray-400 uppercase font-bold">Severity Factors</p>
                <div>
                  <div className="flex justify-between text-xs font-bold mb-1">
                    <span className="text-gray-300">Schedule Compression</span>
                    <span className="text-rose-400">85%</span>
                  </div>
                  <div className="h-1.5 w-full bg-black/50 rounded-full overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-rose-600 to-rose-400 w-[85%]" />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-xs font-bold mb-1">
                    <span className="text-gray-300">Context Switching Overhead</span>
                    <span className="text-orange-400">60%</span>
                  </div>
                  <div className="h-1.5 w-full bg-black/50 rounded-full overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-orange-600 to-orange-400 w-[60%]" />
                  </div>
                </div>
              </div>
            </GlassCard>

            <GlassCard className="relative overflow-hidden border-cyan-500/20 bg-cyan-500/5">
              <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/10 to-transparent pointer-events-none" />
              <h3 className="text-sm font-bold text-cyan-400 mb-6 uppercase tracking-widest flex items-center gap-2">
                <Box className="w-4 h-4" /> Twin Rescue Simulation
              </h3>
              <p className="text-sm text-gray-300 mb-4 font-medium italic">"What happens if no recovery action is taken?"</p>
              
              <div className="space-y-3">
                <div className="flex justify-between items-center p-3 rounded-lg bg-black/40 border border-white/5">
                  <span className="text-sm font-bold text-emerald-400">Current Success Prob.</span>
                  <span className="text-lg font-black text-white">{analytics?.deadline_success_rate || 88}%</span>
                </div>
                <div className="flex justify-between items-center p-3 rounded-lg bg-black/40 border border-rose-500/20">
                  <span className="text-sm font-bold text-rose-400">Predicted Success Prob.</span>
                  <span className="text-lg font-black text-white">{Math.max(0, (analytics?.deadline_success_rate || 88) - 25)}%</span>
                </div>
                <div className="flex justify-between items-center pt-2">
                  <div>
                    <span className="block text-[10px] font-bold text-gray-500 uppercase">Risk Delta</span>
                    <span className="text-xl font-black text-rose-500">+25%</span>
                  </div>
                  <div className="text-right">
                    <span className="block text-[10px] font-bold text-gray-500 uppercase">Projected Failure</span>
                    <span className="text-xl font-black text-rose-500">HIGH</span>
                  </div>
                </div>
              </div>
            </GlassCard>
          </div>

          {/* Emergency Recovery Timeline (HERO) */}
          <GlassCard className="min-h-[400px] border-purple-500/20 shadow-[0_0_30px_rgba(168,85,247,0.1)] relative overflow-hidden">
            <div className="absolute top-0 right-0 w-64 h-64 bg-purple-500/10 blur-[100px] rounded-full pointer-events-none" />
            <h3 className="text-xl font-black text-white mb-6 flex items-center gap-2">
              <BrainCircuit className="w-6 h-6 text-purple-400" /> Emergency Recovery Timeline
            </h3>

            {loading ? (
              <div className="flex flex-col items-center justify-center h-64 text-purple-400">
                <Loader2 className="w-12 h-12 animate-spin mb-4" />
                <p className="text-sm font-bold uppercase tracking-widest animate-pulse">Synthesizing Recovery Protocol...</p>
              </div>
            ) : rescuePlan ? (
              <div>
                <p className="text-gray-300 mb-8 text-sm font-medium leading-relaxed bg-black/20 p-4 rounded-xl border border-white/5">
                  {rescuePlan.reasoning}
                </p>
                <div className="space-y-6 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px before:h-full before:w-0.5 before:bg-gradient-to-b before:from-purple-500 before:via-white/10 before:to-transparent">
                  <AnimatePresence>
                    {rescuePlan.recovery_plan.map((step: any, i: number) => (
                      <motion.div 
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.15 }}
                        key={i} 
                        className="relative flex items-center gap-6 group"
                      >
                        <div className="w-10 h-10 rounded-full bg-black border-2 border-purple-500 flex items-center justify-center shrink-0 z-10 shadow-[0_0_15px_rgba(168,85,247,0.4)]">
                          <span className="text-purple-400 font-black text-sm">{i + 1}</span>
                        </div>
                        <div className="flex-1 p-4 rounded-xl bg-white/5 border border-white/10 group-hover:bg-purple-500/10 group-hover:border-purple-500/30 transition-all duration-300">
                          <div className="flex justify-between items-start">
                            <h4 className="text-lg font-bold text-white mb-1">{step.action}</h4>
                            <Badge variant="warning">Critical Path</Badge>
                          </div>
                          <p className="text-sm text-gray-400">Execute this directive immediately to stabilize the schedule and prevent downstream failure.</p>
                        </div>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-64 text-center border-2 border-dashed border-white/10 rounded-2xl">
                <LifeBuoy className="w-16 h-16 text-white/10 mb-4" />
                <h2 className="text-xl font-bold text-gray-300 mb-2">No Active Protocol</h2>
                <p className="text-gray-500 max-w-sm">
                  System stable. Deploy the Rescue Agent if execution falls behind.
                </p>
              </div>
            )}
          </GlassCard>

        </div>
      </div>
    </div>
  );
};
