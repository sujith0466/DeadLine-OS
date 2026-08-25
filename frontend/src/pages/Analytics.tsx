import React, { useEffect, useState, useRef } from 'react';
import {
  TrendingUp, BrainCircuit, ActivitySquare, Cpu, Bot, Mic, Image,
  FileText, Target, Sun, Moon, Flame, Sparkles, RefreshCw, BarChart2
} from 'lucide-react';
import { motion } from 'framer-motion';
import { GlassCard } from '../components/UI/GlassCard';
import { DeadlineOSApi } from '../api';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

export const Analytics: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [interpreting, setInterpreting] = useState(false);

  // Phase 7 Analytics State
  const [morningBrief, setMorningBrief] = useState<any>(null);
  const [eveningReflection, setEveningReflection] = useState<any>(null);
  const [dailyScore, setDailyScore] = useState<any>(null);
  const [habitHealth, setHabitHealth] = useState<any>(null);
  const [goalProgress, setGoalProgress] = useState<any>(null);
  const [trends, setTrends] = useState<any>(null);
  const [aiInterpretation, setAiInterpretation] = useState<any>(null);

  // Agent Grid State
  const [voiceAgent, setVoiceAgent] = useState<any>(null);
  const [visionAgent, setVisionAgent] = useState<any>(null);
  const [docsAgent, setDocsAgent] = useState<any>(null);

  const [activeDays, setActiveDays] = useState<number>(14);
  const fetched = useRef(false);

  const loadData = async (days: number) => {
    try {
      const [
        mbRes, erRes, dsRes, hhRes, gpRes, trRes, voRes, viRes, docRes
      ] = await Promise.all([
        DeadlineOSApi.getMorningBrief().catch(() => ({ data: null })),
        DeadlineOSApi.getEveningReflection().catch(() => ({ data: null })),
        DeadlineOSApi.getDailyScore().catch(() => ({ data: null })),
        DeadlineOSApi.getHabitHealth().catch(() => ({ data: null })),
        DeadlineOSApi.getGoalProgress().catch(() => ({ data: null })),
        DeadlineOSApi.getTrendsAnalytics(days).catch(() => ({ data: null })),
        DeadlineOSApi.getAnalyticsVoice().catch(() => ({ data: null })),
        DeadlineOSApi.getAnalyticsVision().catch(() => ({ data: null })),
        DeadlineOSApi.getAnalyticsDocuments().catch(() => ({ data: null })),
      ]);

      setMorningBrief(mbRes?.data);
      setEveningReflection(erRes?.data);
      setDailyScore(dsRes?.data);
      setHabitHealth(hhRes?.data);
      setGoalProgress(gpRes?.data);
      setTrends(trRes?.data);

      setVoiceAgent(voRes?.data);
      setVisionAgent(viRes?.data);
      setDocsAgent(docRes?.data);
    } catch (err) {
      console.error("Failed to load analytics suite", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (fetched.current) return;
    fetched.current = true;
    loadData(activeDays);
  }, []);

  const handleGenerateAIInterpretation = async () => {
    setInterpreting(true);
    try {
      const res = await DeadlineOSApi.interpretAnalytics(activeDays);
      if (res?.data) {
        setAiInterpretation(res.data);
      }
    } catch (err) {
      console.error("Failed to generate AI analytics interpretation", err);
    } finally {
      setInterpreting(false);
    }
  };

  const getGradeBadge = (grade: string) => {
    switch (grade) {
      case 'EXCELLENT':
      case 'OPTIMAL':
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
      case 'STRONG':
      case 'BUILDING':
        return 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30';
      case 'FAIR':
      case 'STABLE':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      default:
        return 'bg-rose-500/20 text-rose-400 border-rose-500/30';
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 h-full">
        <ActivitySquare className="w-12 h-12 text-primary animate-pulse mb-4" />
        <h2 className="text-xl font-bold text-white">Initializing Execution Observatory...</h2>
        <p className="text-gray-400 mt-2">Aggregating deterministic runtime metrics & execution telemetry</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 pb-12">
      {/* HEADER & CONTROLS */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/10 pb-6">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight flex items-center gap-3">
            <BarChart2 className="w-7 h-7 text-primary" /> Execution Intelligence & Analytics
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Explainable performance telemetry, daily briefings, habit velocity, and grounded AI insights.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex bg-black/40 border border-white/10 rounded-lg p-1">
            {[7, 14, 30, 90].map((d) => (
              <button
                key={d}
                onClick={() => {
                  setActiveDays(d);
                  loadData(d);
                }}
                className={`px-3 py-1 text-xs font-bold rounded-md transition-all ${
                  activeDays === d ? 'bg-primary text-black' : 'text-gray-400 hover:text-white'
                }`}
              >
                {d}D
              </button>
            ))}
          </div>

          <button
            onClick={handleGenerateAIInterpretation}
            disabled={interpreting}
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-primary/80 to-secondary/80 hover:from-primary hover:to-secondary text-black font-bold text-xs rounded-lg transition-all shadow-lg disabled:opacity-50"
          >
            {interpreting ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Sparkles className="w-4 h-4" />
            )}
            {interpreting ? 'Synthesizing...' : 'AI Execution Analysis'}
          </button>
        </div>
      </div>

      {/* AI INTERPRETATION BANNER */}
      {aiInterpretation && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <GlassCard className="p-6 border border-primary/30 bg-primary/5 relative overflow-hidden">
            <div className="flex items-start justify-between gap-4 mb-4">
              <div>
                <span className="text-[10px] font-black uppercase tracking-widest text-primary flex items-center gap-1.5 mb-1">
                  <BrainCircuit className="w-3.5 h-3.5" /> AI Interpretation ({aiInterpretation._provider || 'Advisory'})
                </span>
                <h2 className="text-xl font-bold text-white">{aiInterpretation.headline}</h2>
              </div>
              <span className="text-xs font-bold px-2.5 py-1 bg-white/10 rounded border border-white/10 text-gray-300">
                Confidence {aiInterpretation.confidence_score || 95}%
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div className="bg-black/30 p-4 rounded-xl border border-white/5">
                <p className="text-xs font-bold text-primary mb-2 uppercase tracking-wider">Key Insights</p>
                <ul className="text-xs text-gray-300 space-y-1.5 list-disc list-inside">
                  {aiInterpretation.key_insights?.map((item: string, idx: number) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ul>
              </div>
              <div className="bg-black/30 p-4 rounded-xl border border-white/5">
                <p className="text-xs font-bold text-emerald-400 mb-2 uppercase tracking-wider">Observed Strengths</p>
                <ul className="text-xs text-gray-300 space-y-1.5 list-disc list-inside">
                  {aiInterpretation.strengths?.map((item: string, idx: number) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ul>
              </div>
              <div className="bg-black/30 p-4 rounded-xl border border-white/5">
                <p className="text-xs font-bold text-amber-400 mb-2 uppercase tracking-wider">Focus Adjustments</p>
                <ul className="text-xs text-gray-300 space-y-1.5 list-disc list-inside">
                  {aiInterpretation.growth_areas?.map((item: string, idx: number) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="bg-primary/10 border border-primary/20 p-3 rounded-lg flex items-center justify-between">
              <span className="text-xs font-semibold text-primary">
                Actionable Takeaway: <strong className="text-white">{aiInterpretation.actionable_takeaway}</strong>
              </span>
            </div>
          </GlassCard>
        </motion.div>
      )}

      {/* ROW 1: DAILY SCORE & BRIEFINGS */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Daily Score Card */}
        {dailyScore && (
          <GlassCard className="p-6 border-l-4 border-l-primary flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-bold uppercase tracking-widest text-gray-400">Daily Execution Score</span>
                <span className={`text-xs font-black px-2.5 py-0.5 rounded border ${getGradeBadge(dailyScore.grade)}`}>
                  {dailyScore.grade}
                </span>
              </div>

              <div className="flex items-baseline gap-3 mb-6">
                <span className="text-5xl font-black text-white">{dailyScore.score}</span>
                <span className="text-sm font-bold text-gray-400">/ 100</span>
              </div>

              <div className="space-y-3 mb-4">
                <div className="flex justify-between text-xs">
                  <span className="text-gray-400">Completion Rate (35%)</span>
                  <span className="text-white font-bold">{dailyScore.components?.completion_rate?.score}%</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-gray-400">Schedule Adherence (25%)</span>
                  <span className="text-white font-bold">{dailyScore.components?.schedule_adherence?.score}%</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-gray-400">Focus Depth (20%)</span>
                  <span className="text-white font-bold">{dailyScore.components?.focus_depth?.score}%</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-gray-400">Recovery Discipline (10%)</span>
                  <span className="text-white font-bold">{dailyScore.components?.recovery_discipline?.score}%</span>
                </div>
              </div>
            </div>

            <p className="text-[11px] text-gray-400 italic border-t border-white/10 pt-3">
              {dailyScore.explanation?.[0] || 'Deterministic multi-factor score.'}
            </p>
          </GlassCard>
        )}

        {/* Morning Brief Card */}
        {morningBrief && (
          <GlassCard className="p-6 border-l-4 border-l-amber-400 flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <Sun className="w-5 h-5 text-amber-400" />
                <h3 className="text-sm font-bold uppercase tracking-wider text-white">Morning Briefing</h3>
              </div>

              <div className="grid grid-cols-2 gap-3 mb-4">
                <div className="bg-black/30 p-3 rounded-lg border border-white/5">
                  <p className="text-[10px] text-gray-400 uppercase font-bold">Planned Today</p>
                  <p className="text-2xl font-black text-white">{morningBrief.planned_activities_count}</p>
                </div>
                <div className="bg-black/30 p-3 rounded-lg border border-white/5">
                  <p className="text-[10px] text-gray-400 uppercase font-bold">High Priority</p>
                  <p className="text-2xl font-black text-amber-400">{morningBrief.high_priority_count}</p>
                </div>
                <div className="bg-black/30 p-3 rounded-lg border border-white/5">
                  <p className="text-[10px] text-gray-400 uppercase font-bold">Pending Workload</p>
                  <p className="text-xl font-black text-white">{morningBrief.total_pending_workload_hours}h</p>
                </div>
                <div className="bg-black/30 p-3 rounded-lg border border-white/5">
                  <p className="text-[10px] text-gray-400 uppercase font-bold">Overdue Risks</p>
                  <p className={`text-xl font-black ${morningBrief.overdue_tasks_count > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                    {morningBrief.overdue_tasks_count}
                  </p>
                </div>
              </div>
            </div>

            <div className="border-t border-white/10 pt-3">
              <p className="text-xs text-gray-300">
                {morningBrief.narrative_highlights?.[0] || 'Ready for today’s commitments.'}
              </p>
            </div>
          </GlassCard>
        )}

        {/* Evening Reflection Card */}
        {eveningReflection && (
          <GlassCard className="p-6 border-l-4 border-l-indigo-400 flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <Moon className="w-5 h-5 text-indigo-400" />
                <h3 className="text-sm font-bold uppercase tracking-wider text-white">Evening Reflection</h3>
              </div>

              <div className="grid grid-cols-2 gap-3 mb-4">
                <div className="bg-black/30 p-3 rounded-lg border border-white/5">
                  <p className="text-[10px] text-gray-400 uppercase font-bold">Focus Time</p>
                  <p className="text-2xl font-black text-white">{eveningReflection.total_focus_duration_minutes}m</p>
                </div>
                <div className="bg-black/30 p-3 rounded-lg border border-white/5">
                  <p className="text-[10px] text-gray-400 uppercase font-bold">Adherence</p>
                  <p className="text-2xl font-black text-indigo-400">{eveningReflection.schedule_adherence_pct}%</p>
                </div>
                <div className="bg-black/30 p-3 rounded-lg border border-white/5">
                  <p className="text-[10px] text-gray-400 uppercase font-bold">Completed</p>
                  <p className="text-xl font-black text-emerald-400">{eveningReflection.completed_activities_count}</p>
                </div>
                <div className="bg-black/30 p-3 rounded-lg border border-white/5">
                  <p className="text-[10px] text-gray-400 uppercase font-bold">Skipped / Defer</p>
                  <p className="text-xl font-black text-amber-400">{eveningReflection.skipped_activities_count}</p>
                </div>
              </div>
            </div>

            <div className="border-t border-white/10 pt-3">
              <p className="text-xs text-gray-300">
                {eveningReflection.narrative_highlights?.[0] || 'Solid execution summary.'}
              </p>
            </div>
          </GlassCard>
        )}
      </div>

      {/* ROW 2: MULTI-DAY TRENDS CHART */}
      {trends?.daily_trends && (
        <GlassCard className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <TrendingUp className="w-5 h-5 text-emerald-400" />
              <h2 className="text-lg font-bold text-white">
                Execution Momentum & Focus Trends ({activeDays} Days)
              </h2>
            </div>
            <div className="flex items-center gap-4 text-xs">
              <span className="text-gray-400">
                Avg Focus: <strong className="text-white">{trends.avg_daily_focus_hours}h/day</strong>
              </span>
              <span className="text-gray-400">
                Completion Rate: <strong className="text-emerald-400">{trends.overall_completion_rate_pct}%</strong>
              </span>
            </div>
          </div>

          <div className="h-[280px] w-full" style={{ width: '100%', height: '280px' }}>
            <ResponsiveContainer width="99%" height="100%">
              <AreaChart data={trends.daily_trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorCompRate" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorFocusHr" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis dataKey="date" stroke="rgba(255,255,255,0.3)" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis stroke="rgba(255,255,255,0.3)" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.95)', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px' }}
                  itemStyle={{ color: '#fff' }}
                />
                <Legend iconType="circle" />
                <Area type="monotone" dataKey="completion_rate_pct" name="Completion Rate (%)" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#colorCompRate)" />
                <Area type="monotone" dataKey="focus_hours" name="Focus Duration (Hours)" stroke="#0ea5e9" strokeWidth={2} fillOpacity={1} fill="url(#colorFocusHr)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>
      )}

      {/* ROW 3: HABIT HEALTH & GOAL ADVANCEMENT */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Habit Health Grid */}
        {habitHealth && (
          <GlassCard className="p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Flame className="w-5 h-5 text-amber-500" />
                <h3 className="text-base font-bold text-white">Habit Health & Momentum</h3>
              </div>
              <span className={`text-xs font-bold px-2.5 py-0.5 rounded border ${getGradeBadge(habitHealth.overall_grade)}`}>
                Score: {habitHealth.overall_health_score}/100
              </span>
            </div>

            {habitHealth.habits?.length > 0 ? (
              <div className="space-y-3">
                {habitHealth.habits.slice(0, 4).map((h: any) => (
                  <div key={h.habit_id} className="bg-black/30 p-3 rounded-lg border border-white/5 flex items-center justify-between">
                    <div>
                      <p className="text-sm font-bold text-white">{h.name}</p>
                      <p className="text-xs text-gray-400">
                        {h.frequency} • {h.consistency_percentage}% Consistency • Streak: {h.current_streak}d
                      </p>
                    </div>
                    <div className="text-right">
                      <span className="text-sm font-black text-primary">{h.health_score}</span>
                      <span className="text-[10px] text-gray-400 block">{h.trend}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-gray-400 py-6 text-center">No active habits configured.</p>
            )}
          </GlassCard>
        )}

        {/* Goal Trajectory Intelligence */}
        {goalProgress && (
          <GlassCard className="p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Target className="w-5 h-5 text-primary" />
                <h3 className="text-base font-bold text-white">Goal Advancement Trajectory</h3>
              </div>
              <span className="text-xs font-bold text-gray-400">
                Avg Progress: <strong className="text-white">{goalProgress.overall_completion_rate_pct}%</strong>
              </span>
            </div>

            {goalProgress.goals?.length > 0 ? (
              <div className="space-y-3">
                {goalProgress.goals.slice(0, 4).map((g: any) => (
                  <div key={g.goal_id} className="bg-black/30 p-3 rounded-lg border border-white/5 space-y-2">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-bold text-white">{g.title}</p>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                        g.risk_level === 'ON_TRACK' || g.risk_level === 'COMPLETED' ? 'text-emerald-400 bg-emerald-500/10' : 'text-rose-400 bg-rose-500/10'
                      }`}>
                        {g.risk_level}
                      </span>
                    </div>
                    <div className="w-full bg-black/40 h-2 rounded-full overflow-hidden">
                      <div className="h-full bg-primary" style={{ width: `${g.progress_percentage}%` }}></div>
                    </div>
                    <div className="flex justify-between text-[11px] text-gray-400">
                      <span>Milestones: {g.completed_milestones}/{g.total_milestones}</span>
                      <span>Target: {g.target_date || 'No target date'}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-gray-400 py-6 text-center">No active goals configured.</p>
            )}
          </GlassCard>
        )}
      </div>

      {/* ROW 4: AGENT INTELLIGENCE GRID */}
      <div className="space-y-4">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <Cpu className="w-5 h-5 text-secondary" /> Agent Intelligence Grid
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {voiceAgent && (
            <GlassCard className="p-4 border-l-2 border-l-primary/50">
              <div className="flex items-center gap-2 mb-2 border-b border-white/10 pb-2">
                <Mic className="w-4 h-4 text-primary" />
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">Voice Copilot</h3>
              </div>
              <p className="text-xs text-gray-400">Executions: <strong className="text-white">{voiceAgent.total_executions || 0}</strong></p>
              <p className="text-xs text-gray-400">Success Rate: <strong className="text-emerald-400">{voiceAgent.success_rate || 100}%</strong></p>
            </GlassCard>
          )}

          {visionAgent && (
            <GlassCard className="p-4 border-l-2 border-l-secondary/50">
              <div className="flex items-center gap-2 mb-2 border-b border-white/10 pb-2">
                <Image className="w-4 h-4 text-secondary" />
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">Vision Agent</h3>
              </div>
              <p className="text-xs text-gray-400">Executions: <strong className="text-white">{visionAgent.total_executions || 0}</strong></p>
              <p className="text-xs text-gray-400">Success Rate: <strong className="text-emerald-400">{visionAgent.success_rate || 100}%</strong></p>
            </GlassCard>
          )}

          {docsAgent && (
            <GlassCard className="p-4 border-l-2 border-l-emerald-500/50">
              <div className="flex items-center gap-2 mb-2 border-b border-white/10 pb-2">
                <FileText className="w-4 h-4 text-emerald-400" />
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">Document Intel</h3>
              </div>
              <p className="text-xs text-gray-400">Executions: <strong className="text-white">{docsAgent.total_executions || 0}</strong></p>
              <p className="text-xs text-gray-400">Success Rate: <strong className="text-emerald-400">{docsAgent.success_rate || 100}%</strong></p>
            </GlassCard>
          )}

          <GlassCard className="p-4 border-l-2 border-l-gray-500 opacity-80">
            <div className="flex items-center gap-2 mb-2 border-b border-white/10 pb-2">
              <Bot className="w-4 h-4 text-gray-400" />
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">Scheduler & Recovery</h3>
            </div>
            <p className="text-xs text-gray-400">Automatic rescheduling and streak protection active.</p>
          </GlassCard>
        </div>
      </div>
    </div>
  );
};
