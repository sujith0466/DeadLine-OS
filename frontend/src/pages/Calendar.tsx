import React, { useEffect, useState } from 'react';
import { Calendar as BigCalendar, dateFnsLocalizer } from 'react-big-calendar';
import { format, parse, startOfWeek, getDay, differenceInMinutes, isBefore } from 'date-fns';
import { enUS } from 'date-fns/locale';

import 'react-big-calendar/lib/css/react-big-calendar.css';

import { 
  ShieldAlert, Target, ActivitySquare, 
  Clock, BatteryCharging, BrainCircuit, Activity, 
  Lightbulb, CheckCircle2, TrendingUp, AlertTriangle, CalendarDays
} from 'lucide-react';
import { GlassCard } from '../components/UI/GlassCard';
import { Background } from '../components/Landing/Background';
import { DeadlineOSApi } from '../api';
import { motion } from 'framer-motion';
import { useCountUp } from '../hooks/useCountUp';
import { Badge } from '../components/UI/Badge';

const locales = {
  'en-US': enUS,
};

const localizer = dateFnsLocalizer({
  format,
  parse,
  startOfWeek,
  getDay,
  locales,
});

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

export const Calendar: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [events, setEvents] = useState<any[]>([]);
  const [intelligence, setIntelligence] = useState<any>(null);
  const [analytics, setAnalytics] = useState<any>(null);
  const [heatmap, setHeatmap] = useState<any[]>([]);
  const [tasks, setTasks] = useState<any[]>([]);
  
  const [currentDate, setCurrentDate] = useState(new Date());
  const [currentView, setCurrentView] = useState<any>('week');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [evRes, intRes, anRes, heatRes, tasksRes] = await Promise.all([
          DeadlineOSApi.getCalendarEvents(),
          DeadlineOSApi.getCalendarIntelligence(),
          DeadlineOSApi.getAnalyticsOverview(),
          DeadlineOSApi.getAnalyticsHeatmap(),
          DeadlineOSApi.getTasks()
        ]);
        
        const rawEvents = Array.isArray(evRes?.data) ? evRes.data : Array.isArray(evRes) ? evRes : [];
        const mappedEvents = rawEvents.map((e: any) => ({
          ...e,
          start: new Date(e.start || Date.now()),
          end: new Date(e.end || Date.now())
        }));
        
        setEvents(mappedEvents);
        setIntelligence(intRes?.data || intRes || null);
        setAnalytics(anRes?.data || anRes || null);
        
        const safeHeatmap = Array.isArray(heatRes?.data) ? heatRes.data : Array.isArray(heatRes) ? heatRes : [];
        
        let finalHeatmap = safeHeatmap;
        if (finalHeatmap.length === 0 && mappedEvents.length > 0) {
          const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
          const counts = [0, 1, 2, 3, 4, 5, 6].map(i => ({ name: days[i], focus: 0, admin: 0 }));
          mappedEvents.forEach((e: any) => {
            if (e.start) {
              const dayIdx = new Date(e.start).getDay();
              if (e.type === 'focus_block') {
                counts[dayIdx].focus += 1;
              } else {
                counts[dayIdx].admin += 1;
              }
            }
          });
          finalHeatmap = counts.filter(d => d.name !== 'Sun' && d.name !== 'Sat');
        }
        
        setHeatmap(finalHeatmap);
        
        const safeTasks = Array.isArray(tasksRes?.data) ? tasksRes.data : Array.isArray(tasksRes) ? tasksRes : [];
        setTasks(safeTasks);
      } catch (err) {
        console.error("Failed to load calendar", err);
        setEvents([]);
        setIntelligence(null);
        setAnalytics(null);
        setHeatmap([]);
        setTasks([]);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const eventStyleGetter = (event: any) => {
    let backgroundColor = '#0f172a';
    let border = '1px solid #334155';
    let color = '#f8fafc';

    if (event.type === 'focus_block') {
      backgroundColor = 'rgba(168, 85, 247, 0.2)'; // Purple
      border = '1px solid #a855f7';
      color = '#e9d5ff';
    } else if (event.type === 'rescue_alert') {
      backgroundColor = 'rgba(245, 158, 11, 0.2)'; // Yellow
      border = '1px solid #f59e0b';
      color = '#fde68a';
    } else if (event.type === 'twin_warning') {
      backgroundColor = 'rgba(244, 63, 94, 0.2)'; // Rose
      border = '1px solid #f43f5e';
      color = '#fecdd3';
    } else if (event.risk_level === 'High' || event.risk_level === 'Critical') {
      backgroundColor = 'rgba(239, 68, 68, 0.15)'; // Red
      border = '1px solid #ef4444';
    } else {
      backgroundColor = 'rgba(56, 189, 248, 0.1)'; // Sky
      border = '1px solid #38bdf8';
    }

    return {
      style: {
        backgroundColor,
        border,
        color,
        borderRadius: '6px',
        opacity: 0.9,
        fontWeight: 'bold',
        fontSize: '12px'
      }
    };
  };

  if (loading) {
    return (
      <>
        <Background />
        <div className="flex flex-col items-center justify-center py-20 h-screen w-full">
          <ActivitySquare className="w-16 h-16 text-primary animate-pulse mb-4" />
          <h2 className="text-2xl font-black text-white">Initializing Executive Calendar...</h2>
          <p className="text-gray-400 mt-2">Correlating spatial timelines with digital twin forecasts</p>
        </div>
      </>
    );
  }

  // Derive metrics safely
  let totalScheduledMinutes = 0;
  let focusMinutes = 0;
  const safeEvents = events || [];
  
  safeEvents.forEach(e => {
    if (e.start && e.end) {
      const mins = differenceInMinutes(e.end, e.start);
      totalScheduledMinutes += mins;
      if (e.type === 'focus_block') focusMinutes += mins;
    }
  });
  
  const scheduledHours = Math.round((totalScheduledMinutes / 60) * 10) / 10;
  const focusHours = Math.round((focusMinutes / 60) * 10) / 10;
  
  const availableHours = scheduledHours + (intelligence?.remaining_hours || 0);
  
  const safeTasks = tasks || [];
  const missedTasks = safeTasks.filter(t => t.status !== 'done' && t.deadline && isBefore(new Date(t.deadline), new Date())).length;
  
  const contextSwitchingScore = Math.min(100, safeEvents.length * 8);

  return (
    <>
      <Background />
      <div className="space-y-4 pb-8 w-full max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 py-6 relative z-10">
        
        {/* SECTION 1: Calendar Intelligence KPI Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <AnimatedKpi value={scheduledHours} suffix="h" label="Scheduled Hours" icon={Clock} delay={0.1} colorClass="text-sky-400" />
          <AnimatedKpi value={intelligence?.remaining_hours || 0} suffix="h" label="Remaining Capacity" icon={BatteryCharging} delay={0.2} colorClass="text-emerald-400" />
          <AnimatedKpi value={analytics?.productivity_score || 0} label="Focus Score" icon={Target} delay={0.3} colorClass="text-purple-400" />
          <AnimatedKpi value={intelligence?.schedule_confidence || 0} suffix="%" label="Schedule Confidence" icon={CheckCircle2} delay={0.4} colorClass="text-indigo-400" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          
          {/* LEFT COLUMN: Calendar & Analytics */}
          <div className="lg:col-span-9 space-y-4">
            
            {/* SECTION 2: Executive Calendar View */}
            <GlassCard className="p-4 bg-background/80 h-[650px] border-t-2 border-t-sky-500">
              <style>
                {`
                  .rbc-calendar { font-family: inherit; color: #fff; }
                  .rbc-header { padding: 8px; font-weight: bold; border-bottom: 1px solid rgba(255,255,255,0.1); text-transform: uppercase; font-size: 11px; letter-spacing: 1px;}
                  .rbc-today { background-color: rgba(56, 189, 248, 0.05); }
                  .rbc-off-range-bg { background-color: rgba(0, 0, 0, 0.2); }
                  .rbc-month-view, .rbc-time-view { border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; overflow: hidden; }
                  .rbc-day-bg { border-left: 1px solid rgba(255,255,255,0.1); }
                  .rbc-month-row { border-top: 1px solid rgba(255,255,255,0.1); }
                  .rbc-timeslot-group { border-bottom: 1px solid rgba(255,255,255,0.1); }
                  .rbc-time-content { border-top: 1px solid rgba(255,255,255,0.1); }
                  .rbc-time-header-content { border-left: 1px solid rgba(255,255,255,0.1); }
                  .rbc-toolbar button { color: #fff; border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; margin: 0 2px;}
                  .rbc-toolbar button:hover { background-color: rgba(255,255,255,0.1); }
                  .rbc-toolbar button:active, .rbc-toolbar button.rbc-active { background-color: rgba(56, 189, 248, 0.2); color: #38bdf8; border-color: rgba(56, 189, 248, 0.5);}
                `}
              </style>
              <BigCalendar
                localizer={localizer}
                events={events}
                startAccessor={(event: any) => event.start}
                endAccessor={(event: any) => event.end}
                eventPropGetter={eventStyleGetter}
                date={currentDate}
                onNavigate={(newDate: Date) => setCurrentDate(newDate)}
                view={currentView}
                onView={(newView: any) => setCurrentView(newView)}
                views={['month', 'week', 'day']}
                step={30}
                timeslots={2}
              />
            </GlassCard>

            {/* SECTION 4: Workload Heatmap */}
            <GlassCard className="border-t-2 border-t-purple-500">
               <h3 className="text-xs font-bold text-purple-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                 <Activity className="w-4 h-4" /> Workload Intensity Heatmap
               </h3>
               <div className="flex justify-between items-end h-32 gap-2">
                 {heatmap.length > 0 ? heatmap.map((day: any, i: number) => {
                    const total = day.focus + day.admin;
                    const max = Math.max(...heatmap.map((d: any) => d.focus + d.admin), 10);
                    const height = `${(total / max) * 100}%`;
                    return (
                      <div key={i} className="flex-1 flex flex-col justify-end group">
                        <div className="w-full bg-purple-500/20 rounded-t-sm hover:bg-purple-500/40 transition-all relative" style={{ height }}>
                           <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-black text-white text-[10px] py-1 px-2 rounded opacity-0 group-hover:opacity-100 whitespace-nowrap pointer-events-none transition-opacity">
                             {total} units
                           </div>
                        </div>
                        <p className="text-[10px] text-gray-500 text-center mt-2 uppercase">{day.name}</p>
                      </div>
                    )
                 }) : (
                   <div className="w-full h-full flex items-center justify-center">
                     <p className="text-xs text-gray-500 italic">No heatmap data available.</p>
                   </div>
                 )}
               </div>
            </GlassCard>

          </div>

          {/* RIGHT COLUMN: Dashboards */}
          <div className="lg:col-span-3 space-y-4">
            
            {/* SECTION 8: Digital Twin Calendar Forecast */}
            <GlassCard className="bg-blue-500/5 border-l-4 border-l-blue-500">
               <h3 className="text-xs font-bold text-blue-400 uppercase tracking-widest mb-3 flex items-center gap-2">
                 <BrainCircuit className="w-4 h-4" /> Twin Forecast Projection
               </h3>
               <div className="space-y-3">
                 <div className="flex justify-between items-center bg-black/30 p-2 rounded border border-white/5">
                   <span className="text-xs text-gray-400">Success Probability</span>
                   <span className="text-sm font-bold text-emerald-400">{analytics?.deadline_success_rate || 0}%</span>
                 </div>
                 <div className="flex justify-between items-center bg-black/30 p-2 rounded border border-white/5">
                   <span className="text-xs text-gray-400">Schedule Stability</span>
                   <span className="text-sm font-bold text-blue-400">{intelligence?.schedule_confidence || 0}%</span>
                 </div>
                 <div className="flex justify-between items-center bg-black/30 p-2 rounded border border-white/5">
                   <span className="text-xs text-gray-400">Future Risk</span>
                   <Badge variant={analytics?.future_risk_forecast === 'High' ? 'danger' : 'info'}>{analytics?.future_risk_forecast || 'Low'}</Badge>
                 </div>
               </div>
            </GlassCard>

            {/* SECTION 5: Focus Intelligence */}
            <GlassCard className="border-t-2 border-t-pink-500">
               <h3 className="text-xs font-bold text-pink-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                 <Target className="w-4 h-4" /> Focus Intelligence
               </h3>
               <div className="grid grid-cols-2 gap-3">
                 <div className="bg-black/30 p-3 rounded-lg border border-white/5 text-center">
                    <p className="text-[10px] text-gray-500 uppercase mb-1">Deep Work Util</p>
                    <p className="text-xl font-bold text-pink-400">{focusHours}h</p>
                 </div>
                 <div className="bg-black/30 p-3 rounded-lg border border-white/5 text-center">
                    <p className="text-[10px] text-gray-500 uppercase mb-1">Context Switch</p>
                    <p className="text-xl font-bold text-orange-400">{contextSwitchingScore}</p>
                 </div>
                 <div className="bg-black/30 p-3 rounded-lg border border-white/5 text-center col-span-2">
                    <p className="text-[10px] text-gray-500 uppercase mb-1">Productivity Forecast</p>
                    <div className="flex items-center justify-center gap-2">
                       <TrendingUp className="w-4 h-4 text-emerald-400" />
                       <p className="text-xl font-bold text-emerald-400">{analytics?.productivity_score || 0}%</p>
                    </div>
                 </div>
               </div>
            </GlassCard>

            {/* SECTION 3: Capacity Forecast Panel */}
            <GlassCard className="border-t-2 border-t-emerald-500">
               <h3 className="text-xs font-bold text-emerald-400 uppercase tracking-widest mb-3 flex items-center gap-2">
                 <BatteryCharging className="w-4 h-4" /> Capacity Forecast
               </h3>
               <div className="space-y-3">
                 <div className="flex justify-between text-xs">
                   <span className="text-gray-400">Available vs Planned</span>
                   <span className="text-white font-medium">{availableHours}h / {scheduledHours}h</span>
                 </div>
                 <div className="w-full bg-white/5 rounded-full h-2">
                   <div className="bg-emerald-500 h-2 rounded-full" style={{ width: `${Math.min(100, (scheduledHours / (availableHours || 1)) * 100)}%` }}></div>
                 </div>
                 <div className="flex gap-2 pt-2 border-t border-white/5">
                   <div className="flex-1 bg-black/30 p-2 rounded text-center border border-white/5">
                     <p className="text-[10px] text-gray-500 uppercase mb-1">Overload Risk</p>
                     <p className={`text-sm font-bold ${intelligence?.capacity_percent > 85 ? 'text-rose-400' : 'text-emerald-400'}`}>
                       {intelligence?.capacity_percent > 85 ? 'High' : 'Low'}
                     </p>
                   </div>
                   <div className="flex-1 bg-black/30 p-2 rounded text-center border border-white/5">
                     <p className="text-[10px] text-gray-500 uppercase mb-1">Burnout Risk</p>
                     <p className={`text-sm font-bold ${analytics?.current_risk_level === 'High' ? 'text-rose-400' : 'text-emerald-400'}`}>
                       {analytics?.current_risk_level || 'Low'}
                     </p>
                   </div>
                 </div>
               </div>
            </GlassCard>

            {/* SECTION 6: Calendar Risk Center */}
            <GlassCard className="border-t-2 border-t-rose-500">
               <h3 className="text-xs font-bold text-rose-400 uppercase tracking-widest mb-3 flex items-center gap-2">
                 <ShieldAlert className="w-4 h-4" /> Calendar Risk Center
               </h3>
               <div className="space-y-2">
                 <div className="flex justify-between items-center text-xs bg-black/30 p-2 rounded border border-white/5">
                   <span className="text-gray-400">Missed Deadlines</span>
                   <span className={`font-bold ${missedTasks > 0 ? 'text-rose-500' : 'text-emerald-500'}`}>{missedTasks}</span>
                 </div>
                 <div className="flex justify-between items-center text-xs bg-black/30 p-2 rounded border border-white/5">
                   <span className="text-gray-400">Rescue Triggers</span>
                   <span className="font-bold text-warning">{intelligence?.rescue_overlays?.length || 0}</span>
                 </div>
                 {intelligence?.twin_warnings?.map((w: string, i: number) => (
                    <div key={i} className="flex gap-2 items-start text-xs bg-rose-500/10 p-2 rounded border border-rose-500/20">
                      <AlertTriangle className="w-3 h-3 text-rose-400 shrink-0 mt-0.5" />
                      <span className="text-rose-200">{w}</span>
                    </div>
                 ))}
               </div>
            </GlassCard>

            {/* SECTION 7: AI Recommendations */}
            <GlassCard className="border-t-2 border-t-cyan-500">
               <h3 className="text-xs font-bold text-cyan-400 uppercase tracking-widest mb-3 flex items-center gap-2">
                 <Lightbulb className="w-4 h-4" /> Agent Recommendations
               </h3>
               <div className="space-y-2 text-xs">
                 {intelligence?.insights?.planning?.map((rec: string, i: number) => (
                   <div key={i} className="flex gap-2 p-2 bg-black/30 rounded border border-white/5">
                     <CalendarDays className="w-3 h-3 text-cyan-400 shrink-0 mt-0.5" />
                     <span className="text-gray-300">{rec}</span>
                   </div>
                 ))}
                 {intelligence?.rescue_overlays?.map((rec: string, i: number) => (
                   <div key={`res-${i}`} className="flex gap-2 p-2 bg-warning/10 rounded border border-warning/20">
                     <ShieldAlert className="w-3 h-3 text-warning shrink-0 mt-0.5" />
                     <span className="text-yellow-200">{rec}</span>
                   </div>
                 ))}
               </div>
            </GlassCard>

          </div>

        </div>
      </div>
    </>
  );
};
