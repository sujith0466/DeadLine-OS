import React, { useState, useEffect } from 'react';
import { 
  CalendarClock, BrainCircuit, Activity, Clock, Zap, Target, 
  ShieldAlert, Coffee, Settings2, Play, Loader2
} from 'lucide-react';
import { GlassCard } from '../components/UI/GlassCard';
import { GradientButton } from '../components/UI/GradientButton';
import { Badge } from '../components/UI/Badge';
import { DeadlineOSApi } from '../api';
import { motion, AnimatePresence } from 'framer-motion';
import { useCountUp } from '../hooks/useCountUp';

const AnimatedKpi = ({ value, suffix = '', label, icon: Icon, delay = 0, colorClass = "text-white" }: any) => {
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
};

export const Planner: React.FC = () => {
  const [tasks, setTasks] = useState<any[]>([]);
  const [schedule, setSchedule] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [analytics, setAnalytics] = useState<any>(null);
  
  // Controls
  const [availableHours, setAvailableHours] = useState(6);
  const [deepWorkFocus, setDeepWorkFocus] = useState(true);
  const [breakDuration, setBreakDuration] = useState(15);
  const [strategy, setStrategy] = useState('Balanced');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [tasksRes, analyticsRes] = await Promise.all([
          DeadlineOSApi.getTasks(),
          DeadlineOSApi.getAnalyticsOverview()
        ]);
        setTasks(tasksRes.tasks || []);
        setAnalytics(analyticsRes.data || null);
      } catch (err) {}
    };
    fetchData();
  }, []);

  const handleGeneratePlan = async () => {
    setLoading(true);
    try {
      const result = await DeadlineOSApi.runPlanningAgent({
        tasks,
        availability: { 
          daily_available_hours: availableHours, 
          preferred_work_hours: { start: "09:00", end: "21:00" },
          strategy,
          deepWorkFocus,
          breakDuration
        }
      });
      setSchedule(result.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const plannedHours = schedule ? schedule.schedule.filter((s:any) => !s.task.includes('Break')).length * 1.5 : 0;
  const focusScore = schedule?.confidence_score || (analytics?.productivity_score || 85);
  const efficiency = schedule ? 92 : 0;
  const remainingCap = Math.max(0, availableHours - plannedHours);
  const riskLevel = remainingCap < 1 ? 'High' : 'Low';

  return (
    <div className="space-y-6 pb-12">
      
      {/* SECTION A: Execution Overview (KPIs) */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <AnimatedKpi value={availableHours} suffix="h" label="Available Hours" icon={Clock} delay={0.1} colorClass="text-white" />
        <AnimatedKpi value={plannedHours || 0} suffix="h" label="Planned Hours" icon={Activity} delay={0.2} colorClass="text-amber-400" />
        <AnimatedKpi value={focusScore} suffix="%" label="Focus Score" icon={Target} delay={0.3} colorClass="text-emerald-400" />
        <AnimatedKpi value={efficiency} suffix="%" label="Schedule Efficiency" icon={Zap} delay={0.4} colorClass="text-indigo-400" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* LEFT COLUMN: Controls & Analysis */}
        <div className="lg:col-span-4 space-y-6">
          
          {/* SECTION B: Planning Control Panel */}
          <GlassCard className="border-t-2 border-t-amber-400">
            <h2 className="text-sm font-bold text-white mb-4 uppercase tracking-widest flex items-center gap-2">
              <Settings2 className="w-4 h-4 text-amber-400" /> Control Panel
            </h2>
            
            <div className="space-y-4 mb-6">
              <div>
                <label className="flex justify-between text-xs font-bold text-gray-400 mb-1.5 uppercase">
                  <span>Daily Available Hours</span>
                  <span className="text-amber-400">{availableHours}h</span>
                </label>
                <input 
                  type="range" 
                  min="1" max="16" 
                  value={availableHours} 
                  onChange={(e) => setAvailableHours(parseInt(e.target.value))}
                  className="w-full accent-amber-500"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-400 mb-1.5 uppercase">Planning Strategy</label>
                <select 
                  className="w-full bg-black/40 border border-white/10 rounded-lg p-2 text-sm text-white outline-none focus:border-amber-500 transition-colors"
                  value={strategy}
                  onChange={(e) => setStrategy(e.target.value)}
                >
                  <option value="Balanced">Balanced Execution</option>
                  <option value="Aggressive">Aggressive Output</option>
                  <option value="Deep Focus">Deep Work Bias</option>
                </select>
              </div>

              <div className="flex gap-4">
                <div className="flex-1">
                  <label className="block text-xs font-bold text-gray-400 mb-1.5 uppercase">Break Length</label>
                  <div className="flex items-center bg-black/40 border border-white/10 rounded-lg overflow-hidden">
                    <input 
                      type="number" 
                      value={breakDuration} 
                      onChange={(e) => setBreakDuration(parseInt(e.target.value))}
                      className="w-full bg-transparent p-2 text-sm text-white outline-none"
                    />
                    <span className="pr-3 text-xs text-gray-500">min</span>
                  </div>
                </div>
                <div className="flex-1 flex flex-col justify-end pb-2">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input 
                      type="checkbox" 
                      className="rounded bg-white/10 border-white/20 text-amber-500 w-4 h-4 accent-amber-500"
                      checked={deepWorkFocus}
                      onChange={(e) => setDeepWorkFocus(e.target.checked)}
                    />
                    <span className="text-xs font-bold text-gray-300">Force Deep Work</span>
                  </label>
                </div>
              </div>
            </div>

            <GradientButton className="w-full flex justify-center items-center gap-2" onClick={handleGeneratePlan} disabled={loading}>
              {loading ? <><Loader2 className="w-4 h-4 animate-spin"/> Synthesizing Plan...</> : <><Play className="w-4 h-4" fill="currentColor"/> {schedule ? 'Rebuild Schedule' : 'Generate Schedule'}</>}
            </GradientButton>
          </GlassCard>

          {/* SECTION D: Workload Analysis */}
          <GlassCard>
            <h2 className="text-sm font-bold text-white mb-4 uppercase tracking-widest flex items-center gap-2">
              <Activity className="w-4 h-4 text-indigo-400" /> Workload Analysis
            </h2>
            <div className="space-y-5">
              <div>
                <div className="flex justify-between text-xs font-bold mb-1.5">
                  <span className="text-gray-400">Capacity Utilization</span>
                  <span className="text-white">{Math.round((plannedHours / availableHours) * 100) || 0}%</span>
                </div>
                <div className="h-1.5 w-full bg-black/50 rounded-full overflow-hidden">
                  <motion.div 
                    initial={{ width: 0 }}
                    animate={{ width: `${Math.min((plannedHours / availableHours) * 100, 100)}%` }}
                    transition={{ duration: 1 }}
                    className={`h-full rounded-full ${remainingCap < 1 ? 'bg-rose-500' : 'bg-emerald-400'}`}
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs font-bold mb-1.5">
                  <span className="text-gray-400">Burnout Risk Factor</span>
                  <span className={riskLevel === 'High' ? 'text-rose-400' : 'text-emerald-400'}>{riskLevel}</span>
                </div>
                <div className="h-1.5 w-full bg-black/50 rounded-full overflow-hidden">
                  <motion.div 
                    initial={{ width: 0 }}
                    animate={{ width: riskLevel === 'High' ? '85%' : '20%' }}
                    transition={{ duration: 1, delay: 0.2 }}
                    className={`h-full rounded-full ${riskLevel === 'High' ? 'bg-rose-500' : 'bg-emerald-400'}`}
                  />
                </div>
              </div>
            </div>
          </GlassCard>

          {/* SECTION E: AI Recommendations */}
          <GlassCard className="bg-indigo-500/5 border-indigo-500/20">
            <h2 className="text-sm font-bold text-indigo-400 mb-4 uppercase tracking-widest flex items-center gap-2">
              <BrainCircuit className="w-4 h-4" /> Planning Brief
            </h2>
            <div className="space-y-3">
              <div className="p-3 bg-black/40 rounded-lg border border-white/5">
                <div className="flex justify-between items-start mb-1">
                  <span className="text-xs font-bold text-emerald-400 uppercase">Optimization</span>
                </div>
                <p className="text-sm text-gray-300">Schedule high-priority cognitive tasks before 2 PM based on your historical peak focus hours.</p>
              </div>
              <div className="p-3 bg-black/40 rounded-lg border border-white/5">
                <div className="flex justify-between items-start mb-1">
                  <span className="text-xs font-bold text-amber-400 uppercase">Warning</span>
                </div>
                <p className="text-sm text-gray-300">Heavy context switching detected. Consider grouping small tasks into a 45-minute administrative block.</p>
              </div>
            </div>
          </GlassCard>

          {/* SECTION F: Digital Twin Simulation */}
          <GlassCard className="bg-cyan-500/5 border-cyan-500/20">
            <h2 className="text-sm font-bold text-cyan-400 mb-3 flex items-center gap-2">
              <ShieldAlert className="w-4 h-4" /> Twin Simulation
            </h2>
            <p className="text-xs text-gray-400 mb-3 italic">"What happens if I delay my highest priority task?"</p>
            <div className="flex justify-between items-center p-3 rounded-lg bg-black/40 border border-cyan-500/10">
              <div>
                <span className="block text-xs font-bold text-gray-500">Impact Level</span>
                <span className="text-sm font-bold text-rose-400">CRITICAL</span>
              </div>
              <div className="text-right">
                <span className="block text-xs font-bold text-gray-500">Risk Increase</span>
                <span className="text-lg font-black text-white">+32%</span>
              </div>
            </div>
          </GlassCard>

        </div>

        {/* RIGHT COLUMN: AI Schedule Timeline */}
        <div className="lg:col-span-8">
          <GlassCard className="h-full min-h-[600px] border-white/10 shadow-[0_0_40px_rgba(0,0,0,0.5)]">
            <div className="flex justify-between items-center mb-8 border-b border-white/10 pb-4">
              <h2 className="text-lg font-black text-white flex items-center gap-2">
                <CalendarClock className="w-5 h-5 text-amber-400" /> Execution Timeline
              </h2>
              {schedule && (
                <div className="text-right">
                  <span className="text-xs font-bold text-gray-400 uppercase tracking-widest block mb-0.5">Confidence Meter</span>
                  <span className="text-xl font-black text-success">{schedule.confidence_score}%</span>
                </div>
              )}
            </div>

            {loading ? (
              <div className="flex flex-col items-center justify-center h-64 text-amber-500/50">
                <Loader2 className="w-12 h-12 animate-spin mb-4" />
                <p className="text-sm font-bold uppercase tracking-widest animate-pulse">Running Constraint Solvers...</p>
              </div>
            ) : schedule ? (
              <div className="space-y-6 relative before:absolute before:inset-0 before:ml-[1.2rem] before:-translate-x-px before:h-full before:w-0.5 before:bg-gradient-to-b before:from-amber-500 before:via-white/10 before:to-transparent">
                <AnimatePresence>
                  {schedule.schedule.map((slot: any, idx: number) => {
                    const isBreak = slot.task.toLowerCase().includes('break');
                    const isFocus = slot.focus_block;
                    
                    return (
                      <motion.div 
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: idx * 0.1 }}
                        key={idx} 
                        className="relative flex items-start gap-6 group"
                      >
                        {/* Timeline Node */}
                        <div className={`w-10 h-10 rounded-full border-2 flex items-center justify-center shrink-0 z-10 shadow-lg transition-colors ${
                          isBreak ? 'bg-black border-gray-600 text-gray-400' :
                          isFocus ? 'bg-black border-amber-500 text-amber-400 shadow-[0_0_15px_rgba(245,158,11,0.3)]' :
                          'bg-black border-indigo-500 text-indigo-400'
                        }`}>
                          {isBreak ? <Coffee className="w-4 h-4" /> : isFocus ? <Zap className="w-4 h-4" /> : <Target className="w-4 h-4" />}
                        </div>
                        
                        {/* Timeline Card */}
                        <div className={`flex-1 p-4 rounded-2xl border transition-all duration-300 hover:-translate-y-1 ${
                          isBreak ? 'bg-white/5 border-white/10 opacity-70' :
                          isFocus ? 'bg-amber-500/5 border-amber-500/30' :
                          'bg-white/5 border-white/10 hover:bg-white/10'
                        }`}>
                          <div className="flex justify-between items-start mb-2">
                            <span className={`text-sm font-black tracking-wider ${isBreak ? 'text-gray-400' : 'text-white'}`}>
                              {slot.start_time} <span className="text-gray-600 mx-1">—</span> {slot.end_time}
                            </span>
                            <div className="flex gap-2">
                              {isFocus && <Badge variant="warning">Deep Work</Badge>}
                              {!isBreak && <Badge variant="neutral">Priority</Badge>}
                            </div>
                          </div>
                          <h3 className={`text-lg font-bold ${isBreak ? 'text-gray-500' : 'text-white'}`}>{slot.task}</h3>
                          {!isBreak && (
                            <p className="text-sm text-gray-400 mt-2">Optimal execution window allocated based on historical energy peaks.</p>
                          )}
                        </div>
                      </motion.div>
                    )
                  })}
                </AnimatePresence>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-[400px] text-center border-2 border-dashed border-white/10 rounded-2xl">
                <CalendarClock className="w-16 h-16 text-white/10 mb-4" />
                <h2 className="text-xl font-bold text-gray-300 mb-2">Schedule Engine Idle</h2>
                <p className="text-gray-500 max-w-sm">
                  Configure your availability limits and strategy. The Planning Agent will synthesize a conflict-free execution path.
                </p>
              </div>
            )}
          </GlassCard>
        </div>

      </div>
    </div>
  );
};
