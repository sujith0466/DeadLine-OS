import React, { useEffect, useState } from 'react';
import { CheckCircle2, ShieldAlert, Zap, ActivitySquare, AlertTriangle, ArrowRight, Play, TestTube, History, GitMerge, Activity } from 'lucide-react';
import { motion } from 'framer-motion';
import { GlassCard } from '../components/UI/GlassCard';
import { GradientButton } from '../components/UI/GradientButton';
import { DeadlineOSApi } from '../api';

export const Interventions: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [interventions, setInterventions] = useState<any[]>([]);
  const [analytics, setAnalytics] = useState<any>(null);
  const [orchestration, setOrchestration] = useState<any[]>([]);
  
  const [simulating, setSimulating] = useState<string | null>(null);
  const [simulationResults, setSimulationResults] = useState<Record<string, any>>({});
  
  const [executing, setExecuting] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      const [intRes, statRes, orchRes] = await Promise.all([
        DeadlineOSApi.getInterventions(),
        DeadlineOSApi.getAnalyticsInterventions(),
        DeadlineOSApi.getOrchestrationFeed().catch(() => ({ data: [] }))
      ]);
      setInterventions(intRes.data);
      setAnalytics(statRes.data);
      setOrchestration(orchRes.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(() => {
        DeadlineOSApi.getOrchestrationFeed().then(r => setOrchestration(r.data || [])).catch(() => {});
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleSimulate = async (id: string) => {
    setSimulating(id);
    try {
      const res = await DeadlineOSApi.simulateIntervention(id);
      setSimulationResults(prev => ({ ...prev, [id]: res.data }));
    } catch (err) {
      console.error(err);
    } finally {
      setSimulating(null);
    }
  };

  const handleExecute = async (id: string) => {
    setExecuting(id);
    try {
      await DeadlineOSApi.executeIntervention(id);
      // Remove from active list
      setInterventions(prev => prev.filter(i => i.id !== id));
      // Refresh analytics & orchestration immediately
      fetchData();
    } catch (err) {
      console.error(err);
    } finally {
      setExecuting(null);
    }
  };

  const runEngine = async () => {
    setLoading(true);
    await DeadlineOSApi.runInterventionEngine();
    await fetchData();
  };

  if (loading && !interventions.length) {
    return (
      <div className="flex flex-col items-center justify-center py-20 h-full">
        <ActivitySquare className="w-12 h-12 text-rose-500 animate-pulse mb-4" />
        <h2 className="text-xl font-bold text-white">Intervention Engine Scanning...</h2>
        <p className="text-gray-400 mt-2">Analyzing twin forecasts and rescue conditions</p>
      </div>
    );
  }

  const getSeverityColor = (severity: string) => {
    if (severity === 'Critical') return 'text-rose-500 border-rose-500/30 bg-rose-500/10';
    if (severity === 'High') return 'text-orange-500 border-orange-500/30 bg-orange-500/10';
    if (severity === 'Medium') return 'text-warning border-warning/30 bg-warning/10';
    return 'text-blue-500 border-blue-500/30 bg-blue-500/10';
  };

  const getIcon = (type: string) => {
    if (type === 'twin_forecast') return <Zap className="w-5 h-5" />;
    if (type === 'rescue' || type === 'calendar_overload' || type === 'workload_overload') return <ShieldAlert className="w-5 h-5" />;
    return <AlertTriangle className="w-5 h-5" />;
  };

  return (
    <div className="space-y-8 pb-12">
      <div className="flex justify-end items-center gap-4">
        <GradientButton onClick={runEngine}>
          Force Engine Sweep
        </GradientButton>
      </div>

      {/* Section A — Executive Risk KPIs */}
      {analytics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
            <GlassCard className="p-4 border-t-4 border-t-blue-500">
              <p className="text-xs font-bold text-gray-400 uppercase tracking-wider">Active Interventions</p>
              <p className="text-3xl font-black text-white mt-1">{interventions.length}</p>
            </GlassCard>
          </motion.div>
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
            <GlassCard className="p-4 border-t-4 border-t-rose-500">
              <p className="text-xs font-bold text-gray-400 uppercase tracking-wider">Critical Risks</p>
              <p className="text-3xl font-black text-rose-500 mt-1">{interventions.filter(i => i.severity === 'Critical').length}</p>
            </GlassCard>
          </motion.div>
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
            <GlassCard className="p-4 border-t-4 border-t-success">
              <p className="text-xs font-bold text-gray-400 uppercase tracking-wider">Interventions Resolved</p>
              <p className="text-3xl font-black text-success mt-1">{analytics.resolved || 0}</p>
            </GlassCard>
          </motion.div>
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}>
            <GlassCard className="p-4 border-t-4 border-t-secondary">
              <p className="text-xs font-bold text-gray-400 uppercase tracking-wider">Resolution Rate</p>
              <p className="text-3xl font-black text-secondary mt-1">{analytics.resolution_rate || 0}%</p>
            </GlassCard>
          </motion.div>
        </div>
      )}

      {/* Main Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Section B/C/D/E — Intervention Intelligence Feed */}
        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-lg font-bold text-white flex items-center gap-2 mb-4">
            <Activity className="w-5 h-5 text-secondary" /> Actionable Intelligence Feed
          </h2>
          
          {interventions.length === 0 ? (
             <GlassCard className="text-center py-12">
               <CheckCircle2 className="w-12 h-12 text-success mx-auto mb-4" />
               <h2 className="text-xl font-bold text-white mb-2">No Active Interventions</h2>
               <p className="text-gray-400">Schedule execution is optimal. Background monitoring active.</p>
             </GlassCard>
          ) : (
            interventions.map((intervention, i) => {
              const sevClasses = getSeverityColor(intervention.severity);
              const sim = simulationResults[intervention.id];
              const isSimulating = simulating === intervention.id;
              const isExecuting = executing === intervention.id;

              return (
                <motion.div key={intervention.id} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.1 }}>
                  <GlassCard className={`border ${sevClasses.split(' ')[1]} ${sevClasses.split(' ')[2]} overflow-hidden`}>
                    
                    {/* Recovery Timeline (Section E) */}
                    <div className="bg-black/20 border-b border-white/5 p-2 flex items-center gap-2 text-[10px] text-gray-400 uppercase font-bold tracking-widest overflow-x-auto whitespace-nowrap">
                       <span className="text-primary flex items-center gap-1"><History className="w-3 h-3"/> Detection</span>
                       <span className="text-gray-600">→</span>
                       <span className={sim ? 'text-primary flex items-center gap-1' : 'flex items-center gap-1'}><TestTube className="w-3 h-3"/> Simulation</span>
                       <span className="text-gray-600">→</span>
                       <span className="text-primary flex items-center gap-1"><GitMerge className="w-3 h-3"/> Recommendation</span>
                       <span className="text-gray-600">→</span>
                       <span className={isExecuting ? 'text-warning flex items-center gap-1 animate-pulse' : 'flex items-center gap-1'}><Play className="w-3 h-3"/> Execution</span>
                    </div>

                    <div className="p-4 flex flex-col xl:flex-row gap-6">
                      {/* Left Column: Metadata */}
                      <div className="w-full xl:w-1/4 space-y-4 border-r border-white/10 pr-4">
                         <div className={`flex items-center gap-2 font-bold uppercase tracking-wider text-xs ${sevClasses.split(' ')[0]}`}>
                            {getIcon(intervention.type)} {intervention.severity} PRIORITY
                         </div>
                         <div>
                           <p className="text-[10px] text-gray-400 font-bold uppercase mb-1">Trigger Source</p>
                           <p className="text-xs text-white bg-black/20 p-2 rounded">{intervention.trigger_source}</p>
                         </div>
                         <div className="flex items-center gap-4">
                           <div>
                             <p className="text-[10px] text-gray-400 font-bold uppercase mb-1">Priority</p>
                             <p className="text-lg font-bold text-white">{intervention.priority_score}</p>
                           </div>
                           <div>
                             <p className="text-[10px] text-gray-400 font-bold uppercase mb-1">AI Confidence</p>
                             <p className="text-lg font-bold text-secondary">{intervention.confidence_score}%</p>
                           </div>
                         </div>
                      </div>

                      {/* Middle Column: The Alert & Recommendation */}
                      <div className="flex-1 space-y-4">
                         <div>
                           <p className="text-xs font-bold text-gray-400 uppercase mb-2">Engine Alert</p>
                           <p className="text-white text-base leading-relaxed">{intervention.message}</p>
                         </div>
                         <div className="bg-background/60 p-4 rounded-xl border border-white/5">
                            <p className="text-xs font-bold text-primary uppercase mb-2 flex items-center gap-2">
                               <ArrowRight className="w-4 h-4" /> Recommended Action
                            </p>
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <p className="text-[10px] text-gray-400 uppercase tracking-widest">Target Task</p>
                                <p className="text-sm font-bold text-white">{intervention.recommended_action.target_task || 'General Action'}</p>
                              </div>
                              <div>
                                <p className="text-[10px] text-gray-400 uppercase tracking-widest">Type</p>
                                <p className="text-sm font-bold text-white">{intervention.recommended_action.action_type}</p>
                              </div>
                            </div>
                         </div>

                         {/* Section C — Intervention Simulation Lab */}
                         {sim && (
                           <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} className="mt-4 border-t border-white/10 pt-4">
                              <p className="text-xs font-bold text-secondary uppercase mb-3 flex items-center gap-2">
                                <TestTube className="w-4 h-4" /> Digital Twin Simulation Results
                              </p>
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                                {/* Success Prob */}
                                <div className="bg-black/20 p-2 rounded border border-white/5 text-center">
                                  <p className="text-[9px] text-gray-400 uppercase tracking-widest mb-1">Success Prob</p>
                                  <div className="flex items-center justify-center gap-2">
                                    <span className="text-sm text-gray-400">{sim.current_state?.success_probability || 0}%</span>
                                    <span className="text-[10px] text-gray-500">→</span>
                                    <span className="text-sm font-bold text-success">{sim.projected_state?.success_probability || sim.success_probability || 0}%</span>
                                  </div>
                                </div>
                                {/* Risk Score */}
                                <div className="bg-black/20 p-2 rounded border border-white/5 text-center">
                                  <p className="text-[9px] text-gray-400 uppercase tracking-widest mb-1">Risk Score</p>
                                  <div className="flex items-center justify-center gap-2">
                                    <span className="text-sm text-gray-400">{sim.current_state?.risk_score || 0}</span>
                                    <span className="text-[10px] text-gray-500">→</span>
                                    <span className="text-sm font-bold text-success">{sim.projected_state?.risk_score || 0}</span>
                                  </div>
                                </div>
                                {/* Capacity */}
                                <div className="bg-black/20 p-2 rounded border border-white/5 text-center">
                                  <p className="text-[9px] text-gray-400 uppercase tracking-widest mb-1">Capacity</p>
                                  <div className="flex items-center justify-center gap-2">
                                    <span className="text-sm font-bold text-primary">{sim.capacity_gain > 0 ? '+' : ''}{sim.capacity_gain} hrs</span>
                                  </div>
                                </div>
                                {/* Stability */}
                                <div className="bg-black/20 p-2 rounded border border-white/5 text-center">
                                  <p className="text-[9px] text-gray-400 uppercase tracking-widest mb-1">Stability</p>
                                  <div className="flex items-center justify-center gap-2">
                                    <span className="text-sm font-bold text-white">{sim.schedule_stability || 'N/A'}</span>
                                  </div>
                                </div>
                              </div>
                           </motion.div>
                         )}

                      </div>

                      {/* Right Column: Execution Console (Section D) */}
                      <div className="w-full xl:w-48 flex flex-col justify-center gap-3">
                         {!sim ? (
                           <button 
                             onClick={() => handleSimulate(intervention.id)}
                             disabled={isSimulating}
                             className="w-full py-2 px-4 bg-primary/20 hover:bg-primary/30 border border-primary/50 text-primary text-sm font-bold rounded-lg transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
                           >
                             {isSimulating ? <ActivitySquare className="w-4 h-4 animate-spin" /> : <TestTube className="w-4 h-4" />}
                             {isSimulating ? 'Simulating...' : 'Run Simulation'}
                           </button>
                         ) : (
                           <button 
                             onClick={() => handleExecute(intervention.id)}
                             disabled={isExecuting}
                             className="w-full py-3 px-4 bg-success/20 hover:bg-success/30 border border-success/50 text-success text-sm font-bold rounded-lg transition-colors flex items-center justify-center gap-2 shadow-[0_0_15px_rgba(16,185,129,0.2)] disabled:opacity-50"
                           >
                             {isExecuting ? <ActivitySquare className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-success" />}
                             {isExecuting ? 'Executing...' : 'Execute Action'}
                           </button>
                         )}
                      </div>
                    </div>
                  </GlassCard>
                </motion.div>
              );
            })
          )}
        </div>

        {/* Section F — Agent Coordination Panel */}
        <div className="space-y-4">
          <h2 className="text-lg font-bold text-white flex items-center gap-2 mb-4">
            <ActivitySquare className="w-5 h-5 text-primary" /> Live Orchestration
          </h2>
          <GlassCard className="h-[600px] overflow-y-auto flex flex-col space-y-3 p-4">
             {orchestration.length === 0 ? (
                <p className="text-sm text-gray-500 text-center py-10">No recent orchestration events.</p>
             ) : (
               orchestration.slice(0, 20).map((event: any, i: number) => (
                 <div key={event.id || i} className="border-l-2 border-primary/50 pl-3 py-1">
                   <div className="flex items-center justify-between mb-1">
                     <span className="text-[10px] font-bold uppercase text-primary tracking-widest">{event.agent}</span>
                     <span className="text-[10px] text-gray-500">
                       {new Date(event.timestamp || new Date()).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'})}
                     </span>
                   </div>
                   <p className="text-sm text-gray-300">{event.action}</p>
                   {event.status === 'success' && <p className="text-[10px] text-success mt-1">SUCCESS</p>}
                   {event.status === 'error' && <p className="text-[10px] text-rose-500 mt-1">FAILED</p>}
                 </div>
               ))
             )}
          </GlassCard>
        </div>

      </div>
    </div>
  );
};
