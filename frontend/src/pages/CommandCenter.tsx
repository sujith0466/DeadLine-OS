import React, { useState, useEffect } from 'react';
import { 
  Network, Upload, FileText, Mic, CheckCircle2, Loader2, 
  Cpu, Activity, AlertOctagon, Box,
  Play
} from 'lucide-react';
import { GlassCard } from '../components/UI/GlassCard';
import { GradientButton } from '../components/UI/GradientButton';
import { Badge } from '../components/UI/Badge';
import { DeadlineOSApi } from '../api';
import { motion } from 'framer-motion';



export const CommandCenter: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [feed, setFeed] = useState<any[]>([]);
  const [analytics, setAnalytics] = useState<any>(null);
  const [trace, setTrace] = useState<any[]>([]);

  // Orchestration Graph Nodes
  const MAS_NODES = [
    'Vision Agent',
    'Priority Agent',
    'Planning Agent',
    'Accountability Agent',
    'Coach Agent',
    'Rescue Agent',
    'Digital Twin',
    'Intervention Engine',
    'Calendar'
  ];

  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        const analyticsRes = await DeadlineOSApi.getAnalyticsOverview();
        setAnalytics(analyticsRes.data || {
          productivity_score: 0, deadline_success_rate: 0, current_risk_level: "Low", future_risk_forecast: "Low", ai_confidence_score: 0
        });
      } catch (err) {}
    };
    fetchInitialData();
  }, []);

  useEffect(() => {
    const fetchFeed = async () => {
      try {
        const res = await DeadlineOSApi.getOrchestrationFeed();
        if (res.feed) setFeed(res.feed);
      } catch (err) {}
    };
    fetchFeed();
    const interval = setInterval(fetchFeed, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleRunPipeline = async () => {
    if (!file) return;
    setLoading(true);
    setTrace([]); // Reset trace
    try {
      const payload = file;
      const res = await DeadlineOSApi.runOrchestrationPipeline(payload);
      if (res.trace) {
        setTrace(res.trace);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getAgentColor = (agentName: string) => {
    const name = agentName.toLowerCase();
    if (name.includes('vision')) return 'text-purple-400 bg-purple-400/10 border-purple-400/20';
    if (name.includes('priority')) return 'text-rose-400 bg-rose-400/10 border-rose-400/20';
    if (name.includes('planning')) return 'text-amber-400 bg-amber-400/10 border-amber-400/20';
    if (name.includes('accountability')) return 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20';
    if (name.includes('coach')) return 'text-blue-400 bg-blue-400/10 border-blue-400/20';
    if (name.includes('rescue')) return 'text-red-500 bg-red-500/10 border-red-500/20';
    if (name.includes('twin')) return 'text-cyan-400 bg-cyan-400/10 border-cyan-400/20';
    if (name.includes('reflection')) return 'text-indigo-400 bg-indigo-400/10 border-indigo-400/20';
    if (name.includes('goal')) return 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20';
    if (name.includes('document')) return 'text-orange-400 bg-orange-400/10 border-orange-400/20';
    if (name.includes('voice')) return 'text-violet-400 bg-violet-400/10 border-violet-400/20';
    if (name.includes('intervention')) return 'text-rose-500 bg-rose-500/10 border-rose-500/20';
    if (name.includes('calendar')) return 'text-blue-500 bg-blue-500/10 border-blue-500/20';
    return 'text-gray-400 bg-gray-400/10 border-gray-400/20';
  };

  const getNodeStatus = (nodeName: string) => {
    const traceEvent = trace.find((t: any) => t.agent.toLowerCase().includes(nodeName.toLowerCase().replace(' agent', '')));
    if (traceEvent) {
      if (traceEvent.status === 'success') return 'Complete';
      if (traceEvent.status === 'warning') return 'Warning';
    }
    if (loading) {
      // Very basic logic: if loading, and it's not complete, it's either running or idle waiting.
      // We'll mark the first one without trace as Running, others Idle.
      const nodeIndex = MAS_NODES.indexOf(nodeName);
      const lastCompletedIndex = MAS_NODES.findIndex(n => !trace.find((t: any) => t.agent.toLowerCase().includes(n.toLowerCase().replace(' agent', ''))));
      if (nodeIndex === lastCompletedIndex) return 'Running';
      return 'Idle';
    }
    return 'Idle';
  };

  return (
    <div className="space-y-6 pb-12">
      

      {/* 3-COLUMN LAYOUT */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* LEFT COLUMN: Inputs & Controls */}
        <div className="space-y-6">
          <GlassCard className="border-dashed border-2 border-white/20">
            <h3 className="text-sm font-bold text-white mb-4 uppercase tracking-widest flex items-center gap-2">
              <Activity className="w-4 h-4 text-primary" /> Input Vectors
            </h3>
            
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-white/5 rounded-xl border border-white/10 hover:bg-white/10 transition-colors cursor-pointer relative overflow-hidden group">
                <input 
                  type="file" 
                  id="img-upload" 
                  className="absolute inset-0 opacity-0 cursor-pointer" 
                  accept="image/*"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                />
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-primary/20 rounded-lg"><Upload className="w-4 h-4 text-primary" /></div>
                  <div>
                    <p className="text-sm font-bold text-white group-hover:text-primary transition-colors">Upload Image</p>
                    <p className="text-xs text-gray-500">{file ? file.name : 'Timetables, Screenshots'}</p>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between p-3 bg-white/5 rounded-xl border border-white/10 hover:bg-white/10 transition-colors cursor-pointer relative overflow-hidden group opacity-60">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-amber-500/20 rounded-lg"><FileText className="w-4 h-4 text-amber-500" /></div>
                  <div>
                    <p className="text-sm font-bold text-white group-hover:text-amber-400 transition-colors">Upload Document</p>
                    <p className="text-xs text-gray-500">PDFs, Syllabi (Soon)</p>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between p-3 bg-white/5 rounded-xl border border-white/10 hover:bg-white/10 transition-colors cursor-pointer relative overflow-hidden group opacity-60">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-purple-500/20 rounded-lg"><Mic className="w-4 h-4 text-purple-500" /></div>
                  <div>
                    <p className="text-sm font-bold text-white group-hover:text-purple-400 transition-colors">Voice Command</p>
                    <p className="text-xs text-gray-500">Tap to speak (Soon)</p>
                  </div>
                </div>
              </div>
            </div>

            <GradientButton 
              className="w-full mt-6 flex justify-center items-center gap-2" 
              onClick={handleRunPipeline} 
              disabled={!file || loading}
            >
              {loading ? <><Loader2 className="w-4 h-4 animate-spin"/> Orchestrating...</> : <><Play className="w-4 h-4" fill="currentColor"/> Deploy MAS Pipeline</>}
            </GradientButton>
          </GlassCard>
        </div>

        {/* CENTER COLUMN: Orchestration Graph */}
        <div className="space-y-6">
          <GlassCard className="h-full">
            <h3 className="text-sm font-bold text-white mb-6 uppercase tracking-widest flex items-center gap-2">
              <Network className="w-4 h-4 text-indigo-400" /> Orchestration Graph
            </h3>
            <div className="relative">
              {/* Connecting line */}
              <div className="absolute left-6 top-6 bottom-6 w-0.5 bg-white/10" />
              
              <div className="space-y-4">
                {MAS_NODES.map((node) => {
                  const status = getNodeStatus(node);
                  const isActive = status === 'Running';
                  const isComplete = status === 'Complete';
                  const isWarning = status === 'Warning';
                  
                  let badgeVariant: any = 'neutral';
                  let iconColor = 'text-gray-500 bg-gray-500/10 border-gray-500/20';
                  
                  if (isActive) {
                    badgeVariant = 'info';
                    iconColor = 'text-primary bg-primary/20 border-primary/40 shadow-[0_0_15px_rgba(56,189,248,0.5)]';
                  } else if (isComplete) {
                    badgeVariant = 'success';
                    iconColor = 'text-emerald-400 bg-emerald-400/20 border-emerald-400/40 shadow-[0_0_10px_rgba(52,211,153,0.3)]';
                  } else if (isWarning) {
                    badgeVariant = 'warning';
                    iconColor = 'text-amber-400 bg-amber-400/20 border-amber-400/40 shadow-[0_0_10px_rgba(251,191,36,0.3)]';
                  }

                  return (
                    <div key={node} className="relative flex items-center gap-4 group">
                      <div className={`w-12 h-12 rounded-full border-2 flex items-center justify-center z-10 transition-all duration-300 ${iconColor}`}>
                        {isComplete ? <CheckCircle2 className="w-5 h-5" /> : 
                         isActive ? <Loader2 className="w-5 h-5 animate-spin" /> : 
                         isWarning ? <AlertOctagon className="w-5 h-5" /> :
                         <Cpu className="w-5 h-5" />}
                      </div>
                      <div className={`flex-1 p-3 rounded-xl border transition-all duration-300 ${isActive ? 'bg-primary/5 border-primary/30' : 'bg-white/5 border-white/10'}`}>
                        <div className="flex justify-between items-center">
                          <span className={`text-sm font-bold ${isActive ? 'text-white' : 'text-gray-300'}`}>{node}</span>
                          <Badge variant={badgeVariant} className={isActive ? 'animate-pulse' : ''}>{status}</Badge>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          </GlassCard>
        </div>

        {/* RIGHT COLUMN: Live Feeds & Interventions */}
        <div className="space-y-6">
          
          {/* Live Intelligence Feed */}
          <GlassCard className="flex flex-col h-[400px]">
            <h3 className="text-sm font-bold text-white mb-4 uppercase tracking-widest flex items-center gap-2 shrink-0">
              <Activity className="w-4 h-4 text-emerald-400" /> Live Intelligence Feed
            </h3>
            <div className="flex-1 overflow-y-auto space-y-3 pr-2 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
              {feed.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-gray-500">
                  <Activity className="w-8 h-8 mb-2 opacity-50" />
                  <p className="text-sm">Awaiting Events</p>
                </div>
              ) : (
                feed.map((event, i) => {
                  const colors = getAgentColor(event.agent);
                  return (
                    <motion.div 
                      key={event.id || i}
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="p-3 bg-white/5 border border-white/10 rounded-lg"
                    >
                      <div className="flex justify-between items-center mb-1">
                        <span className={`text-xs font-bold ${colors.split(' ')[0]}`}>{event.agent}</span>
                        <span className="text-[10px] text-gray-500">{new Date(event.timestamp).toLocaleTimeString()}</span>
                      </div>
                      <p className="text-xs text-gray-300 leading-snug">{event.action}</p>
                    </motion.div>
                  )
                })
              )}
            </div>
          </GlassCard>

          {/* Digital Twin Forecast */}
          <GlassCard className="border-cyan-500/20 bg-cyan-500/5">
            <h3 className="text-sm font-bold text-cyan-400 mb-3 flex items-center gap-2">
              <Box className="w-4 h-4" /> Twin Forecast Risk
            </h3>
            <div className="flex items-center gap-4">
              <div className="flex-1 bg-black/40 p-3 rounded-lg border border-cyan-500/20">
                <p className="text-xs text-gray-400 mb-1">Projected Risk Factor</p>
                <div className="flex items-end gap-2">
                  <span className="text-2xl font-black text-white">{analytics?.future_risk_forecast === 'High' ? '85%' : '12%'}</span>
                  {analytics?.future_risk_forecast === 'High' ? 
                    <span className="text-xs text-rose-400 mb-1 font-bold">CRITICAL</span> : 
                    <span className="text-xs text-emerald-400 mb-1 font-bold">NOMINAL</span>
                  }
                </div>
              </div>
            </div>
            {analytics?.future_risk_forecast === 'High' && (
              <p className="text-xs text-rose-400 mt-3 font-medium">Warning: Severe bottleneck projected in the next 48 hours based on current velocity.</p>
            )}
          </GlassCard>

          {/* Live Interventions */}
          <GlassCard className="border-rose-500/20 bg-rose-500/5">
            <h3 className="text-sm font-bold text-rose-500 mb-3 flex items-center gap-2">
              <AlertOctagon className="w-4 h-4" /> Live Interventions
            </h3>
            {analytics?.future_risk_forecast === 'High' ? (
              <div className="p-3 bg-black/40 rounded-lg border border-rose-500/20">
                <p className="text-xs font-bold text-rose-400 uppercase mb-1">Action Required</p>
                <p className="text-sm text-white">System predicts a 85% chance of missing the next milestone. Reallocation of calendar blocks recommended immediately.</p>
              </div>
            ) : (
              <div className="p-3 bg-black/40 rounded-lg border border-white/5 text-center">
                <p className="text-sm text-emerald-400 font-medium">No active interventions required.</p>
              </div>
            )}
          </GlassCard>

        </div>
      </div>
    </div>
  );
};
