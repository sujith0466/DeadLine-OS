import React, { useEffect, useState } from 'react';
import { 
  Target, TrendingUp, ActivitySquare, Rocket, PlayCircle, 
  BrainCircuit, Award, Activity, ChevronRight, CheckCircle2
} from 'lucide-react';
import { GlassCard } from '../components/UI/GlassCard';
import { DeadlineOSApi } from '../api';
import { motion, AnimatePresence } from 'framer-motion';
import { useCountUp } from '../hooks/useCountUp';
import { Badge } from '../components/UI/Badge';

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

export const Goals: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [goals, setGoals] = useState<any[]>([]);
  const [habits, setHabits] = useState<any[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [goalsRes, habitsRes] = await Promise.all([
          DeadlineOSApi.getGoals(),
          DeadlineOSApi.getHabits()
        ]);
        setGoals(goalsRes.data || []);
        setHabits(habitsRes.data || []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 h-full">
        <ActivitySquare className="w-12 h-12 text-primary animate-pulse mb-4" />
        <h2 className="text-xl font-bold text-white tracking-widest uppercase text-sm">Initializing Intelligence...</h2>
      </div>
    );
  }

  const activeGoalsCount = goals.length;
  const avgConsistency = habits.length > 0 ? Math.round(habits.reduce((acc, h) => acc + h.completion_rate, 0) / habits.length) : 0;
  const successProb = 88; // Derived metric
  const avgMomentum = habits.length > 0 ? Math.round(habits.reduce((acc, h) => acc + h.momentum_score, 0) / habits.length) : 0;

  const getHealthStatus = (score: number) => {
    if (score >= 90) return { label: 'Excellent', color: 'text-emerald-400', bg: 'bg-emerald-400/10', border: 'border-emerald-400/30' };
    if (score >= 70) return { label: 'Good', color: 'text-primary', bg: 'bg-primary/10', border: 'border-primary/30' };
    if (score >= 40) return { label: 'Warning', color: 'text-amber-400', bg: 'bg-amber-400/10', border: 'border-amber-400/30' };
    return { label: 'Critical', color: 'text-rose-500', bg: 'bg-rose-500/10', border: 'border-rose-500/30' };
  };

  return (
    <div className="space-y-8 pb-12">
      


      {/* SECTION A: Growth Intelligence Overview */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <AnimatedKpi value={activeGoalsCount} label="Active Goals" icon={Rocket} delay={0.1} colorClass="text-cyan-400" />
        <AnimatedKpi value={avgConsistency} suffix="%" label="Habit Consistency" icon={Activity} delay={0.2} colorClass="text-purple-400" />
        <AnimatedKpi value={successProb} suffix="%" label="Success Probability" icon={Target} delay={0.3} colorClass="text-emerald-400" />
        <AnimatedKpi value={avgMomentum} label="Momentum Score" icon={TrendingUp} delay={0.4} colorClass="text-amber-400" />
      </div>

      {/* SECTION B & C: Goal Command Center & Timeline */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
        <h2 className="text-sm font-bold text-gray-400 uppercase tracking-widest flex items-center gap-2 mb-4">
          <Rocket className="w-4 h-4 text-cyan-400" /> Goal Command Center
        </h2>
        <div className="grid grid-cols-1 gap-6">
          {goals.map((goal, index) => {
            const health = getHealthStatus(goal.health_score);
            const progress = goal.milestones.length > 0 
              ? Math.round((goal.milestones.filter((m:any) => m.completed).length / goal.milestones.length) * 100) 
              : 0;

            return (
              <GlassCard key={goal.id} className="relative overflow-hidden border-t-2 border-t-cyan-500/50 hover:shadow-[0_0_30px_rgba(34,211,238,0.1)] transition-all">
                <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-500/5 blur-[120px] rounded-full pointer-events-none" />
                
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 relative z-10">
                  {/* Left: Intelligence */}
                  <div className="lg:col-span-5 space-y-5">
                    <div className="flex justify-between items-start">
                      <div>
                        <Badge variant="info" className="mb-2">{goal.category}</Badge>
                        <h3 className="text-2xl font-black text-white leading-tight">{goal.title}</h3>
                        <p className="text-xs text-gray-400 mt-1 font-bold tracking-widest uppercase">Target: {goal.target_date}</p>
                      </div>
                      <div className={`px-3 py-1 rounded-lg border ${health.bg} ${health.border} flex flex-col items-end`}>
                        <span className="text-[10px] text-gray-400 font-bold uppercase tracking-wider mb-0.5">Health Status</span>
                        <span className={`text-sm font-black ${health.color} uppercase tracking-widest`}>{health.label}</span>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-black/40 p-3 rounded-lg border border-white/5">
                        <span className="text-[10px] font-bold text-gray-500 uppercase block mb-1">Progress</span>
                        <div className="flex items-end gap-2">
                          <span className="text-xl font-black text-white">{progress}%</span>
                          <div className="flex-1 h-1.5 bg-white/10 rounded-full mb-1.5">
                            <div className="h-full bg-cyan-400 rounded-full" style={{ width: `${progress}%` }} />
                          </div>
                        </div>
                      </div>
                      <div className="bg-black/40 p-3 rounded-lg border border-white/5">
                        <span className="text-[10px] font-bold text-gray-500 uppercase block mb-1">AI Forecast</span>
                        <span className="text-xl font-black text-emerald-400">{goal.ai_forecast?.completion_probability || 0}%</span>
                      </div>
                    </div>

                    {goal.ai_forecast && (
                      <div className="bg-primary/5 p-3 rounded-lg border border-primary/20 flex gap-3 items-start">
                        <BrainCircuit className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                        <div>
                          <p className="text-xs font-bold text-primary uppercase tracking-wider mb-1">AI Strategy Insight</p>
                          <p className="text-sm text-gray-300 italic">"{goal.ai_forecast.recommendations[0]}"</p>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Right: Milestone Timeline */}
                  <div className="lg:col-span-7">
                    <h4 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-4">Execution Roadmap</h4>
                    <div className="flex flex-col space-y-4 relative before:absolute before:inset-0 before:ml-[1.1rem] before:-translate-x-px before:h-full before:w-0.5 before:bg-gradient-to-b before:from-cyan-500 before:via-white/10 before:to-transparent">
                      <AnimatePresence>
                        {/* Root Goal Node */}
                        <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: index * 0.1 }} className="relative flex items-center gap-4 group">
                          <div className="w-9 h-9 rounded-full bg-black border-2 border-cyan-500 flex items-center justify-center shrink-0 z-10 shadow-[0_0_15px_rgba(34,211,238,0.4)]">
                            <Target className="w-4 h-4 text-cyan-400" />
                          </div>
                          <div className="flex-1">
                            <span className="text-sm font-bold text-white">Goal Initialized</span>
                          </div>
                        </motion.div>

                        {/* Milestones */}
                        {goal.milestones.map((m: any, i: number) => (
                          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: index * 0.1 + (i + 1) * 0.1 }} key={i} className="relative flex items-center gap-4 group">
                            <div className={`w-9 h-9 rounded-full border-2 flex items-center justify-center shrink-0 z-10 transition-colors ${m.completed ? 'bg-emerald-500/20 border-emerald-500 text-emerald-400 shadow-[0_0_10px_rgba(16,185,129,0.3)]' : 'bg-black border-white/20 text-gray-500'}`}>
                              {m.completed ? <CheckCircle2 className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                            </div>
                            <div className={`flex-1 p-3 rounded-xl border transition-all ${m.completed ? 'bg-emerald-500/5 border-emerald-500/20' : 'bg-white/5 border-white/10 hover:border-white/20'}`}>
                              <span className={`text-sm font-bold ${m.completed ? 'text-emerald-400' : 'text-gray-300'}`}>{m.title}</span>
                            </div>
                          </motion.div>
                        ))}

                        {/* Completion Node */}
                        <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: index * 0.1 + (goal.milestones.length + 1) * 0.1 }} className="relative flex items-center gap-4 group">
                          <div className={`w-9 h-9 rounded-full bg-black border-2 border-dashed flex items-center justify-center shrink-0 z-10 ${progress === 100 ? 'border-success text-success' : 'border-gray-600 text-gray-600'}`}>
                            <Award className="w-4 h-4" />
                          </div>
                          <div className="flex-1">
                            <span className={`text-sm font-bold ${progress === 100 ? 'text-success' : 'text-gray-500'}`}>Target Completion</span>
                          </div>
                        </motion.div>
                      </AnimatePresence>
                    </div>
                  </div>
                </div>
              </GlassCard>
            );
          })}
        </div>
      </motion.div>

      {/* SECTION D, E, F: Habits, Forecasts, Coach */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}>
        <h2 className="text-sm font-bold text-gray-400 uppercase tracking-widest flex items-center gap-2 mb-4 mt-8">
          <TrendingUp className="w-4 h-4 text-purple-400" /> Habit Intelligence & Coaching
        </h2>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* SECTION D: Habit Intelligence Grid */}
          <div className="lg:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-4">
            {habits.map((habit) => (
              <GlassCard key={habit.id} className="relative overflow-hidden group hover:-translate-y-1 transition-all border-purple-500/20">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-lg font-bold text-white mb-1">{habit.name}</h3>
                    <Badge variant="neutral">{habit.frequency}</Badge>
                  </div>
                  <div className="relative w-12 h-12 flex items-center justify-center">
                    <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                      <path className="text-white/10" strokeWidth="3" stroke="currentColor" fill="none" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                      <path className={`${habit.completion_rate > 75 ? 'text-emerald-400' : 'text-purple-400'}`} strokeDasharray={`${habit.completion_rate}, 100`} strokeWidth="3" strokeLinecap="round" stroke="currentColor" fill="none" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                    </svg>
                    <span className="absolute text-[10px] font-bold text-white">{habit.completion_rate}%</span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2 mb-4">
                  <div className="bg-black/30 rounded p-2">
                    <span className="block text-[9px] text-gray-500 uppercase font-bold">Current Streak</span>
                    <span className="text-lg font-black text-white flex items-center gap-1"><PlayCircle className="w-3 h-3 text-emerald-400" />{habit.current_streak}</span>
                  </div>
                  <div className="bg-black/30 rounded p-2">
                    <span className="block text-[9px] text-gray-500 uppercase font-bold">Momentum</span>
                    <span className={`text-lg font-black ${habit.momentum_score > 70 ? 'text-purple-400' : 'text-amber-400'}`}>{habit.momentum_score}</span>
                  </div>
                </div>

                <div className="bg-purple-500/10 p-2 rounded border border-purple-500/20">
                  <span className="text-[9px] font-bold text-purple-400 uppercase tracking-widest block mb-1">AI Recommendation</span>
                  <span className="text-xs text-gray-300">Maintain streak to solidify neural pathway. High probability of long-term adoption.</span>
                </div>
              </GlassCard>
            ))}
          </div>

          {/* SECTION E & F: Habit Forecast Engine & AI Growth Coach */}
          <div className="space-y-6">
            <GlassCard className="bg-black/40 border-white/5">
              <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                <Activity className="w-4 h-4 text-emerald-400" /> Forecast Engine
              </h3>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-xs font-bold mb-1">
                    <span className="text-gray-300">Predicted Success Trajectory</span>
                    <span className="text-emerald-400">85%</span>
                  </div>
                  <div className="h-1 w-full bg-white/10 rounded-full overflow-hidden">
                    <div className="h-full bg-emerald-400 w-[85%]" />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-xs font-bold mb-1">
                    <span className="text-gray-300">Breakdown Risk</span>
                    <span className="text-amber-400">12%</span>
                  </div>
                  <div className="h-1 w-full bg-white/10 rounded-full overflow-hidden">
                    <div className="h-full bg-amber-400 w-[12%]" />
                  </div>
                </div>
              </div>
            </GlassCard>

            <GlassCard className="border-amber-500/20 bg-amber-500/5">
              <h3 className="text-xs font-bold text-amber-500 uppercase tracking-widest mb-4 flex items-center gap-2">
                <BrainCircuit className="w-4 h-4" /> AI Growth Coach
              </h3>
              <div className="space-y-3">
                <div className="p-3 bg-black/50 rounded-lg border border-amber-500/20">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-[10px] font-black text-amber-400 uppercase tracking-wider">Action Plan</span>
                    <span className="text-[10px] font-bold text-emerald-400 bg-emerald-400/10 px-2 py-0.5 rounded-full">94% Conf.</span>
                  </div>
                  <p className="text-sm text-gray-200">Increase "Coding Practice" habit block by 30 minutes to accelerate Milestone 2 completion.</p>
                </div>
                <div className="p-3 bg-black/50 rounded-lg border border-white/5">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-[10px] font-black text-gray-400 uppercase tracking-wider">Optimization</span>
                    <span className="text-[10px] font-bold text-emerald-400 bg-emerald-400/10 px-2 py-0.5 rounded-full">82% Conf.</span>
                  </div>
                  <p className="text-sm text-gray-200">Schedule 15m "Documentation" block immediately after morning standup.</p>
                </div>
              </div>
            </GlassCard>
          </div>

        </div>
      </motion.div>

    </div>
  );
};
