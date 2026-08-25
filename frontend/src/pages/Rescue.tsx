import React, { useState, useEffect } from 'react';
import { usePageMeta } from '../hooks/usePageMeta';
import { 
  LifeBuoy, AlertTriangle, ShieldAlert, Activity, 
  RefreshCw, Loader2, CheckCircle, Flame, SkipForward, Palmtree
} from 'lucide-react';
import { GlassCard } from '../components/UI/GlassCard';
import { GradientButton } from '../components/UI/GradientButton';
import { Badge } from '../components/UI/Badge';
import { DeadlineOSApi } from '../api';
import { motion, AnimatePresence } from 'framer-motion';
import { useSync } from '../hooks/useSync';

export const Rescue: React.FC = () => {
  usePageMeta('Recovery Center');
  const [recoverable, setRecoverable] = useState<any>({ missed: [], interrupted: [], overdue: [], skipped: [] });
  const [strategies, setStrategies] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [vacationStatus, setVacationStatus] = useState<any>(null);
  const [emergencyStatus, setEmergencyStatus] = useState<any>(null);

  const fetchRecoveryData = async () => {
    try {
      const [itemsRes, stratRes, vacRes, emRes] = await Promise.all([
        DeadlineOSApi.getRecoveryItems(),
        DeadlineOSApi.getSmartRecoveryRecommendations(),
        DeadlineOSApi.getVacationStatus(),
        DeadlineOSApi.getEmergencyStatus()
      ]);
      setRecoverable(itemsRes.data || { missed: [], interrupted: [], overdue: [], skipped: [] });
      setStrategies(stratRes.data?.strategies || []);
      setVacationStatus(vacRes.data);
      setEmergencyStatus(emRes.data);
    } catch (e) { }
  };

  useEffect(() => {
    fetchRecoveryData();
  }, []);

  useSync(['THREAT_DETECTED', 'RESCUE_EXECUTED', 'PLANNER_UPDATED'], fetchRecoveryData);

  const handleExecuteAction = async (action: string, entityId: string, entityType: string, scheduleId?: string, params?: any) => {
    setActionLoading(entityId);
    try {
      await DeadlineOSApi.executeRecoveryAction({
        action,
        entity_id: entityId,
        entity_type: entityType,
        schedule_id: scheduleId,
        params
      });
      await fetchRecoveryData();
    } catch (e) {
    } finally {
      setActionLoading(null);
    }
  };

  const handleExecuteStrategy = async (strategy: any) => {
    setLoading(true);
    try {
      for (const act of strategy.actions) {
        await DeadlineOSApi.executeRecoveryAction({
          action: act.action,
          entity_id: act.entity_id,
          entity_type: act.entity_type || 'TASK',
          schedule_id: act.schedule_id,
          params: act
        });
      }
      await fetchRecoveryData();
    } catch (e) {
    } finally {
      setLoading(false);
    }
  };

  const handleToggleEmergency = async () => {
    setLoading(true);
    try {
      if (emergencyStatus?.is_active) {
        await DeadlineOSApi.deactivateEmergencyMode();
      } else {
        await DeadlineOSApi.activateEmergencyMode({ reason: 'User triggered from Recovery Center', auto_skip_non_critical: true });
      }
      await fetchRecoveryData();
    } catch (e) {
    } finally {
      setLoading(false);
    }
  };

  const totalThreats = (recoverable.missed?.length || 0) + (recoverable.interrupted?.length || 0) + (recoverable.overdue?.length || 0);

  return (
    <div className="space-y-6 pb-12">
      {/* Top Banner */}
      <GlassCard className={`relative overflow-hidden ${totalThreats > 0 ? 'border-rose-500/50' : 'border-emerald-500/50'}`}>
        <div className={`absolute inset-0 opacity-10 pointer-events-none ${totalThreats > 0 ? 'bg-rose-500' : 'bg-emerald-500'}`} />
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl font-black text-white mb-1 flex items-center gap-3">
              {totalThreats > 0 ? <AlertTriangle className="text-rose-500 w-7 h-7"/> : <CheckCircle className="text-emerald-500 w-7 h-7"/>}
              {totalThreats > 0 ? 'Schedule Disruption Detected' : 'Schedule on Track'}
            </h2>
            <p className="text-gray-400 text-sm font-medium">
              {totalThreats > 0 
                ? `${totalThreats} activities require recovery (missed, interrupted, or overdue).` 
                : 'All scheduled workflows are healthy.'}
            </p>
          </div>
          
          <div className="flex items-center gap-3">
            {vacationStatus?.is_active_today && (
              <div className="flex items-center gap-1.5 px-3 py-1.5 bg-cyan-500/20 border border-cyan-500/30 rounded-lg text-cyan-300 text-xs font-semibold">
                <Palmtree className="w-4 h-4" />
                Vacation Active
              </div>
            )}

            <GradientButton 
              variant={emergencyStatus?.is_active ? 'danger' : 'secondary'}
              onClick={handleToggleEmergency}
              disabled={loading}
              className="flex items-center gap-2 text-xs"
            >
              <Flame className="w-4 h-4" />
              {emergencyStatus?.is_active ? 'Exit Emergency Mode' : 'Emergency Mode'}
            </GradientButton>

            <GradientButton 
              variant="primary"
              onClick={fetchRecoveryData}
              disabled={loading}
              className="flex items-center gap-2 text-xs"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin"/> : <RefreshCw className="w-4 h-4" />}
              Refresh
            </GradientButton>
          </div>
        </div>
      </GlassCard>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Recoverable Activities */}
        <div className="space-y-6 lg:col-span-1">
          <GlassCard>
            <h3 className="text-xs font-bold text-gray-300 uppercase tracking-wider mb-4 flex items-center gap-2">
              <Activity className="w-4 h-4 text-rose-400" /> Disrupted Activities
            </h3>
            
            <div className="space-y-3">
              {totalThreats === 0 ? (
                <p className="text-xs text-gray-500 text-center py-6">No disrupted activities found.</p>
              ) : (
                <>
                  {/* Missed Slots */}
                  {recoverable.missed?.map((m: any) => (
                    <div key={m.id} className="p-3 bg-black/40 rounded-xl border border-rose-500/20 space-y-2">
                      <div className="flex justify-between items-start">
                        <span className="text-[10px] font-bold text-rose-400 uppercase">MISSED SLOT</span>
                        <Badge variant="danger">High</Badge>
                      </div>
                      <p className="text-xs font-semibold text-gray-200">{m.task_title || m.entity_id}</p>
                      <div className="flex items-center gap-2 pt-1">
                        <button
                          onClick={() => handleExecuteAction('SKIP', m.entity_id, m.entity_type || 'TASK', m.id)}
                          disabled={actionLoading === m.entity_id}
                          className="px-2 py-1 bg-white/10 hover:bg-white/20 text-gray-300 rounded text-[10px] font-semibold flex items-center gap-1"
                        >
                          <SkipForward className="w-3 h-3" /> Skip Today
                        </button>
                      </div>
                    </div>
                  ))}

                  {/* Overdue Tasks */}
                  {recoverable.overdue?.map((o: any) => (
                    <div key={o.id} className="p-3 bg-black/40 rounded-xl border border-amber-500/20 space-y-2">
                      <div className="flex justify-between items-start">
                        <span className="text-[10px] font-bold text-amber-400 uppercase">OVERDUE</span>
                        <Badge variant="warning">Priority {o.priority_score}</Badge>
                      </div>
                      <p className="text-xs font-semibold text-gray-200">{o.title}</p>
                      <div className="flex items-center gap-2 pt-1">
                        <button
                          onClick={() => handleExecuteAction('COMPLETE', o.id, 'TASK')}
                          disabled={actionLoading === o.id}
                          className="px-2 py-1 bg-primary text-black rounded text-[10px] font-bold hover:bg-primary/90"
                        >
                          Mark Complete
                        </button>
                        <button
                          onClick={() => handleExecuteAction('SKIP', o.id, 'TASK')}
                          disabled={actionLoading === o.id}
                          className="px-2 py-1 bg-white/10 hover:bg-white/20 text-gray-300 rounded text-[10px] font-semibold flex items-center gap-1"
                        >
                          <SkipForward className="w-3 h-3" /> Skip Today
                        </button>
                      </div>
                    </div>
                  ))}
                </>
              )}
            </div>
          </GlassCard>
        </div>

        {/* Right: Smart Recovery Strategies */}
        <div className="lg:col-span-2 space-y-6">
          <GlassCard className="h-full">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-4 flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-cyan-400" /> Deterministic Smart Recovery
            </h3>
            
            {strategies.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-64 text-center border-2 border-dashed border-white/10 rounded-2xl">
                <LifeBuoy className="w-12 h-12 text-white/10 mb-3" />
                <p className="text-xs text-gray-400 max-w-sm">
                  No recovery intervention needed. All schedules are within capacity limits.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <AnimatePresence>
                  {strategies.map((strat, i) => (
                    <motion.div 
                      key={strat.name}
                      initial={{ opacity: 0, y: 15 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.1 }}
                      className="p-4 rounded-xl bg-black/40 border border-white/10 hover:border-cyan-500/50 transition-colors flex flex-col justify-between"
                    >
                      <div className="space-y-2">
                        <div className="flex justify-between items-center">
                          <h4 className="text-sm font-bold text-white">{strat.name}</h4>
                          <Badge variant="success">{strat.success_prob}% Safe</Badge>
                        </div>
                        <p className="text-xs text-gray-400">{strat.impact}</p>
                        <div className="p-2 bg-white/5 rounded text-[11px] text-gray-300 font-mono">
                          {strat.rationale}
                        </div>
                      </div>

                      <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between">
                        <span className="text-[10px] text-gray-500">{strat.actions?.length || 0} automated actions</span>
                        <GradientButton 
                          variant="primary" 
                          className="text-xs px-3 py-1.5" 
                          onClick={() => handleExecuteStrategy(strat)} 
                          disabled={loading}
                        >
                          Apply Strategy
                        </GradientButton>
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            )}
          </GlassCard>
        </div>
      </div>
    </div>
  );
};
