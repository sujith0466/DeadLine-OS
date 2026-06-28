import React, { useEffect, useState } from 'react';
import { 
  format, startOfMonth, endOfMonth, startOfWeek, endOfWeek, 
  eachDayOfInterval, isSameMonth, isSameDay, addMonths, subMonths, 
  addDays, addWeeks, subWeeks, isToday
} from 'date-fns';
import { 
  ShieldAlert, Target, ActivitySquare, BatteryCharging, 
  CheckCircle2, AlertTriangle, CalendarDays, ChevronLeft, ChevronRight, X
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

export const Calendar: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [events, setEvents] = useState<any[]>([]);
  const [intelligence, setIntelligence] = useState<any>(null);
  const [analytics, setAnalytics] = useState<any>(null);
  
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [view, setView] = useState<'month' | 'week'>('month');

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [evRes, intRes, anRes] = await Promise.all([
          DeadlineOSApi.getCalendarEvents(),
          DeadlineOSApi.getCalendarIntelligence(),
          DeadlineOSApi.getAnalyticsOverview()
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
      } catch (err) {
        console.error("Failed to load calendar", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const changeDate = (direction: 'prev' | 'next' | 'today') => {
    if (direction === 'today') {
      setCurrentDate(new Date());
    } else if (view === 'month') {
      setCurrentDate(prev => direction === 'next' ? addMonths(prev, 1) : subMonths(prev, 1));
    } else {
      setCurrentDate(prev => direction === 'next' ? addWeeks(prev, 1) : subWeeks(prev, 1));
    }
  };

  const getDayEvents = (date: Date) => {
    return events.filter(e => isSameDay(e.start, date));
  };

  // Render Month Grid
  const renderMonthView = () => {
    const monthStart = startOfMonth(currentDate);
    const monthEnd = endOfMonth(monthStart);
    const startDate = startOfWeek(monthStart);
    const endDate = endOfWeek(monthEnd);

    const days = eachDayOfInterval({ start: startDate, end: endDate });

    return (
      <div className="grid grid-cols-7 gap-px bg-white/10 rounded-lg overflow-hidden border border-white/10">
        {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(d => (
          <div key={d} className="bg-[#0B1120] p-2 text-center text-[10px] font-bold text-gray-400 uppercase tracking-widest">
            {d}
          </div>
        ))}
        {days.map((day, i) => {
          const dayEvents = getDayEvents(day);
          const tasks = dayEvents.filter(e => e.type === 'task').length;
          const deadlines = dayEvents.filter(e => e.type === 'deadline').length;
          const goals = dayEvents.filter(e => e.type === 'goal').length;
          const meetings = dayEvents.filter(e => e.type === 'meeting').length;
          const alerts = dayEvents.filter(e => e.risk_level === 'High').length;
          
          const isCurrentMonth = isSameMonth(day, monthStart);
          const isSelected = selectedDate && isSameDay(day, selectedDate);
          
          return (
            <div 
              key={i} 
              onClick={() => setSelectedDate(day)}
              className={`bg-[#020617] min-h-[100px] p-2 cursor-pointer transition-colors hover:bg-white/5 border-t border-r border-white/5 relative group
                ${!isCurrentMonth ? 'opacity-40' : ''}
                ${isSelected ? 'ring-2 ring-inset ring-sky-500 bg-sky-500/10' : ''}
                ${isToday(day) ? 'bg-indigo-500/10' : ''}
              `}
            >
              <div className="flex justify-between items-start">
                <span className={`text-sm font-bold ${isToday(day) ? 'text-indigo-400 bg-indigo-500/20 px-2 rounded' : 'text-gray-300'}`}>
                  {format(day, 'd')}
                </span>
                {alerts > 0 && <AlertTriangle className="w-3 h-3 text-rose-500" />}
              </div>
              
              <div className="mt-2 space-y-1">
                {deadlines > 0 && <div className="text-[10px] font-bold text-rose-400 bg-rose-500/10 px-1.5 py-0.5 rounded flex justify-between"><span>⚠ Deadlines</span><span>{deadlines}</span></div>}
                {tasks > 0 && <div className="text-[10px] font-bold text-sky-400 bg-sky-500/10 px-1.5 py-0.5 rounded flex justify-between"><span>📝 Tasks</span><span>{tasks}</span></div>}
                {meetings > 0 && <div className="text-[10px] font-bold text-purple-400 bg-purple-500/10 px-1.5 py-0.5 rounded flex justify-between"><span>📅 Meetings</span><span>{meetings}</span></div>}
                {goals > 0 && <div className="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded flex justify-between"><span>🎯 Goals</span><span>{goals}</span></div>}
              </div>
            </div>
          )
        })}
      </div>
    );
  };

  const renderWeekView = () => {
    const startDate = startOfWeek(currentDate);
    const days = Array.from({length: 7}).map((_, i) => addDays(startDate, i));
    const hours = Array.from({length: 15}).map((_, i) => i + 8); // 8 AM to 10 PM

    return (
      <div className="flex flex-col bg-[#020617] rounded-lg border border-white/10 overflow-hidden h-[600px] overflow-y-auto">
        <div className="grid grid-cols-8 sticky top-0 z-20 bg-[#0B1120] border-b border-white/10 shadow-lg">
          <div className="p-3 border-r border-white/10"></div>
          {days.map(d => (
            <div key={d.toString()} onClick={() => setSelectedDate(d)} className={`p-3 text-center cursor-pointer hover:bg-white/5 border-r border-white/10 ${isToday(d) ? 'bg-indigo-500/20' : ''}`}>
              <div className="text-[10px] uppercase text-gray-400 font-bold">{format(d, 'EEE')}</div>
              <div className={`text-lg font-black ${isToday(d) ? 'text-indigo-400' : 'text-gray-200'}`}>{format(d, 'd')}</div>
            </div>
          ))}
        </div>
        <div className="relative">
          {hours.map(h => (
            <div key={h} className="grid grid-cols-8 border-b border-white/5 h-16 group">
              <div className="p-2 text-[10px] font-bold text-gray-500 text-right pr-4 border-r border-white/10">
                {h}:00
              </div>
              {days.map(d => (
                <div key={d.toString()} className="border-r border-white/5 hover:bg-white/5 transition-colors relative">
                  {getDayEvents(d).map(e => {
                     const evHour = e.start.getHours();
                     const evMin = e.start.getMinutes();
                     if (evHour === h) {
                        return (
                          <div key={e.id} className="absolute inset-x-1 p-1 text-[9px] rounded font-bold overflow-hidden"
                               style={{ 
                                 top: `${(evMin/60)*100}%`, 
                                 height: '90%', 
                                 background: e.type==='deadline' ? 'rgba(244,63,94,0.2)' : e.type==='meeting'?'rgba(168,85,247,0.2)':'rgba(56,189,248,0.2)',
                                 borderLeft: `2px solid ${e.type==='deadline'?'#f43f5e':e.type==='meeting'?'#a855f7':'#38bdf8'}`,
                                 color: '#fff',
                                 zIndex: 10
                               }}>
                            {format(e.start, 'h:mm')} - {e.title}
                          </div>
                        )
                     }
                     return null;
                  })}
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
    );
  };

  const selectedDayEvents = selectedDate ? getDayEvents(selectedDate) : [];
  const morningEvents = selectedDayEvents.filter(e => e.start.getHours() < 12);
  const afternoonEvents = selectedDayEvents.filter(e => e.start.getHours() >= 12 && e.start.getHours() < 17);
  const eveningEvents = selectedDayEvents.filter(e => e.start.getHours() >= 17);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 h-screen w-full relative z-10">
        <ActivitySquare className="w-16 h-16 text-sky-500 animate-pulse mb-4" />
        <h2 className="text-2xl font-black text-white">Aggregating Productivity Matrix...</h2>
      </div>
    );
  }

  return (
    <div className="w-full max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 py-6 relative z-10 space-y-6">
      
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-sky-400 to-indigo-500 flex items-center gap-3">
            <CalendarDays className="w-8 h-8 text-sky-400" /> AI Productivity Calendar
          </h1>
          <p className="text-gray-400 font-medium">Your central execution dashboard powered by Local Intelligence V3.</p>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="flex bg-black/40 rounded-lg p-1 border border-white/10">
            <button onClick={() => setView('month')} className={`px-4 py-1.5 text-xs font-bold rounded-md transition-colors ${view === 'month' ? 'bg-sky-500/20 text-sky-400' : 'text-gray-400 hover:text-white'}`}>Month</button>
            <button onClick={() => setView('week')} className={`px-4 py-1.5 text-xs font-bold rounded-md transition-colors ${view === 'week' ? 'bg-sky-500/20 text-sky-400' : 'text-gray-400 hover:text-white'}`}>Week</button>
          </div>
          
          <div className="flex items-center gap-2 bg-black/40 rounded-lg p-1 border border-white/10">
            <button onClick={() => changeDate('prev')} className="p-1 hover:bg-white/10 rounded"><ChevronLeft className="w-5 h-5"/></button>
            <button onClick={() => changeDate('today')} className="px-3 text-xs font-bold hover:text-sky-400">Today</button>
            <button onClick={() => changeDate('next')} className="p-1 hover:bg-white/10 rounded"><ChevronRight className="w-5 h-5"/></button>
          </div>
          
          <div className="text-xl font-black min-w-[150px] text-right text-white">
            {format(currentDate, view === 'month' ? 'MMMM yyyy' : 'MMM yyyy')}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <AnimatedKpi value={events.length} label="Total Workload" icon={ActivitySquare} delay={0.1} colorClass="text-sky-400" />
        <AnimatedKpi value={intelligence?.schedule_confidence || 85} suffix="%" label="Schedule Confidence" icon={CheckCircle2} delay={0.2} colorClass="text-emerald-400" />
        <AnimatedKpi value={analytics?.productivity_score || 0} label="Focus Score" icon={Target} delay={0.3} colorClass="text-purple-400" />
        <AnimatedKpi value={intelligence?.remaining_hours || 0} suffix="h" label="Capacity Available" icon={BatteryCharging} delay={0.4} colorClass="text-indigo-400" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 relative">
        <div className={`transition-all duration-300 ${selectedDate ? 'lg:col-span-8' : 'lg:col-span-12'}`}>
          {view === 'month' ? renderMonthView() : renderWeekView()}
        </div>
        
        {/* Day Planner Side Panel */}
        <AnimatePresence>
          {selectedDate && (
            <motion.div 
              initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 20 }}
              className="lg:col-span-4 h-full"
            >
              <GlassCard className="h-full min-h-[600px] border-t-4 border-t-sky-500 relative flex flex-col">
                <button onClick={() => setSelectedDate(null)} className="absolute top-4 right-4 p-1 rounded hover:bg-white/10">
                  <X className="w-5 h-5 text-gray-400" />
                </button>
                
                <div className="mb-6">
                  <h3 className="text-2xl font-black text-white">{format(selectedDate, 'EEEE')}</h3>
                  <p className="text-sky-400 font-bold">{format(selectedDate, 'MMMM d, yyyy')}</p>
                </div>
                
                <div className="flex-1 overflow-y-auto space-y-6 pr-2">
                  
                  {/* AI Recommendations */}
                  {selectedDayEvents.some(e => e.risk_level === 'High') && (
                    <div className="bg-rose-500/10 border border-rose-500/20 rounded-lg p-3">
                      <h4 className="text-xs font-bold text-rose-400 uppercase tracking-widest mb-2 flex items-center gap-2">
                        <ShieldAlert className="w-4 h-4"/> Critical Deadlines Today
                      </h4>
                      <p className="text-xs text-rose-200">The Intelligence Engine detects high-risk deadlines. Prioritize deep work immediately.</p>
                    </div>
                  )}

                  <div className="space-y-4">
                    <h4 className="text-[10px] font-bold text-gray-500 uppercase tracking-widest border-b border-white/10 pb-1">Morning</h4>
                    {morningEvents.length > 0 ? morningEvents.map(e => (
                      <div key={e.id} className="bg-black/40 border border-white/5 p-3 rounded-lg flex items-start gap-3">
                         <span className="text-xs font-bold text-gray-400 w-12 pt-0.5">{format(e.start, 'h:mm')}</span>
                         <div>
                           <p className="text-sm font-bold text-white">{e.title}</p>
                           <Badge className="mt-1" variant={e.type==='deadline'?'danger':e.type==='goal'?'success':'info'}>{e.type}</Badge>
                         </div>
                      </div>
                    )) : <p className="text-xs text-gray-500 italic">No morning items.</p>}
                  </div>
                  
                  <div className="space-y-4">
                    <h4 className="text-[10px] font-bold text-gray-500 uppercase tracking-widest border-b border-white/10 pb-1">Afternoon</h4>
                    {afternoonEvents.length > 0 ? afternoonEvents.map(e => (
                      <div key={e.id} className="bg-black/40 border border-white/5 p-3 rounded-lg flex items-start gap-3">
                         <span className="text-xs font-bold text-gray-400 w-12 pt-0.5">{format(e.start, 'h:mm')}</span>
                         <div>
                           <p className="text-sm font-bold text-white">{e.title}</p>
                           <Badge className="mt-1" variant={e.type==='deadline'?'danger':e.type==='goal'?'success':'info'}>{e.type}</Badge>
                         </div>
                      </div>
                    )) : <p className="text-xs text-gray-500 italic">No afternoon items.</p>}
                  </div>
                  
                  <div className="space-y-4">
                    <h4 className="text-[10px] font-bold text-gray-500 uppercase tracking-widest border-b border-white/10 pb-1">Evening</h4>
                    {eveningEvents.length > 0 ? eveningEvents.map(e => (
                      <div key={e.id} className="bg-black/40 border border-white/5 p-3 rounded-lg flex items-start gap-3">
                         <span className="text-xs font-bold text-gray-400 w-12 pt-0.5">{format(e.start, 'h:mm')}</span>
                         <div>
                           <p className="text-sm font-bold text-white">{e.title}</p>
                           <Badge className="mt-1" variant={e.type==='deadline'?'danger':e.type==='goal'?'success':'info'}>{e.type}</Badge>
                         </div>
                      </div>
                    )) : <p className="text-xs text-gray-500 italic">No evening items.</p>}
                  </div>

                </div>
              </GlassCard>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};
