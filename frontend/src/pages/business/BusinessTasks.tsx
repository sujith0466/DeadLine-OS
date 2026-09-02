import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  CheckSquare,
  Plus,
  Search,
  Calendar,
  User as UserIcon,
  MapPin,
  Package,
  Trash2,
  Bell,
  Zap,
  CheckCircle2,
  RefreshCw,
  ArrowRight,
} from 'lucide-react';
import { api } from '../../api';
import { useBusinessAuth } from '../../context/BusinessAuthContext';
import { useAuth } from '../../context/AuthContext';
import { BusinessPageHeader } from '../../components/Business/BusinessPageHeader';
import { OperationsSubNav } from '../../components/Business/OperationsSubNav';
import { BusinessDataTable } from '../../components/Business/BusinessDataTable';
import type { ColumnDef } from '../../components/Business/BusinessDataTable';
import { DetailDrawer } from '../../components/Business/DetailDrawer';
import { StatusBadge } from '../../components/Business/StatusBadge';

export interface TaskItem extends Record<string, any> {
  id: string;
  workspace_id: string;
  title: string;
  description?: string | null;
  assignee_member_id?: string | null;
  assignee_name?: string | null;
  assignee_email?: string | null;
  created_by_user_id: string;
  creator_name?: string | null;
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';
  status: 'TODO' | 'IN_PROGRESS' | 'BLOCKED' | 'DONE' | 'CANCELLED';
  due_date?: string | null;
  is_overdue: boolean;
  entity_id?: string | null;
  entity_name?: string | null;
  location_id?: string | null;
  location_name?: string | null;
  product_id?: string | null;
  product_name?: string | null;
  category: string;
  notes?: string | null;
  completed_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface OperationalAlertItem {
  id: string;
  workspace_id: string;
  alert_type: string;
  severity: 'CRITICAL' | 'WARNING' | 'INFO';
  status: 'ACTIVE' | 'ACKNOWLEDGED' | 'RESOLVED' | 'DISMISSED';
  title: string;
  description?: string | null;
  entity_type: string;
  entity_id: string;
  dedup_fingerprint: string;
  cooldown_until?: string | null;
  recommended_action?: string | null;
  generated_task_id?: string | null;
  acknowledged_at?: string | null;
  resolved_at?: string | null;
  created_at: string;
}

export const BusinessTasks: React.FC = () => {
  const { activeWorkspace, role } = useBusinessAuth();
  const { user } = useAuth();

  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [alerts, setAlerts] = useState<OperationalAlertItem[]>([]);
  const [activeTab, setActiveTab] = useState<'TASKS' | 'ALERTS'>('TASKS');
  const [evaluatingAlerts, setEvaluatingAlerts] = useState<boolean>(false);
  const [selectedAlertForTask, setSelectedAlertForTask] = useState<OperationalAlertItem | null>(null);
  const [alertTaskAssignee, setAlertTaskAssignee] = useState<string>('');

  const [members, setMembers] = useState<any[]>([]);
  const [locations, setLocations] = useState<any[]>([]);
  const [products, setProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [priorityFilter, setPriorityFilter] = useState<string>('ALL');
  const [assigneeFilter, setAssigneeFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Modals & Drawers
  const [isCreateModalOpen, setIsCreateModalOpen] = useState<boolean>(false);
  const [selectedTask, setSelectedTask] = useState<TaskItem | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState<boolean>(false);

  // Form State
  const [formTitle, setFormTitle] = useState<string>('');
  const [formDescription, setFormDescription] = useState<string>('');
  const [formPriority, setFormPriority] = useState<string>('MEDIUM');
  const [formCategory, setFormCategory] = useState<string>('GENERAL');
  const [formAssigneeId, setFormAssigneeId] = useState<string>('');
  const [formLocationId, setFormLocationId] = useState<string>('');
  const [formProductId, setFormProductId] = useState<string>('');
  const [formDueDate, setFormDueDate] = useState<string>('');
  const [formNotes, setFormNotes] = useState<string>('');
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const canCreate = ['OWNER', 'ADMIN', 'MEMBER'].includes(role || '');
  const canDelete = ['OWNER', 'ADMIN'].includes(role || '');

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [tasksRes, membersRes, locsRes, prodsRes, alertsRes] = await Promise.all([
        api.listBusinessTasks(),
        api.listWorkspaceMembers(),
        api.listLocations(),
        api.listProducts(),
        api.listOperationalAlerts(),
      ]);

      setTasks(tasksRes.data?.tasks || []);
      setMembers(membersRes.data?.members || membersRes.data || []);
      setLocations(locsRes.data?.locations || []);
      setProducts(prodsRes.data?.products || []);
      setAlerts(alertsRes.data?.alerts || []);
    } catch (err: any) {
      console.error('Failed to load business task data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (activeWorkspace) {
      fetchData();
    }
  }, [activeWorkspace, fetchData]);

  const filteredTasks = useMemo(() => {
    return tasks.filter((t) => {
      if (statusFilter !== 'ALL' && t.status !== statusFilter) return false;
      if (priorityFilter !== 'ALL' && t.priority !== priorityFilter) return false;
      if (assigneeFilter === 'ME') {
        const currentMember = members.find((m) => m.user_id === user?.id);
        if (t.assignee_member_id !== currentMember?.id) return false;
      } else if (assigneeFilter === 'UNASSIGNED') {
        if (t.assignee_member_id) return false;
      } else if (assigneeFilter !== 'ALL') {
        if (t.assignee_member_id !== assigneeFilter) return false;
      }

      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const titleMatch = t.title.toLowerCase().includes(q);
        const descMatch = (t.description || '').toLowerCase().includes(q);
        const assigneeMatch = (t.assignee_name || '').toLowerCase().includes(q);
        const entityMatch = (t.entity_name || '').toLowerCase().includes(q);
        if (!titleMatch && !descMatch && !assigneeMatch && !entityMatch) return false;
      }

      return true;
    });
  }, [tasks, statusFilter, priorityFilter, assigneeFilter, searchQuery, members, user]);

  // Metrics
  const totalCount = tasks.length;
  const todoCount = tasks.filter((t) => t.status === 'TODO').length;
  const inProgressCount = tasks.filter((t) => t.status === 'IN_PROGRESS').length;
  const blockedCount = tasks.filter((t) => t.status === 'BLOCKED').length;
  const overdueCount = tasks.filter((t) => t.is_overdue).length;
  const doneCount = tasks.filter((t) => t.status === 'DONE').length;
  const activeAlertsCount = alerts.filter((a) => a.status === 'ACTIVE' || a.status === 'ACKNOWLEDGED').length;

  const handleEvaluateSignals = async () => {
    try {
      setEvaluatingAlerts(true);
      await api.evaluateOperationalAlerts();
      await fetchData();
    } catch (err: any) {
      alert(err.response?.data?.message || err.message || 'Signal evaluation failed');
    } finally {
      setEvaluatingAlerts(false);
    }
  };

  const handleAcknowledgeAlert = async (alertId: string) => {
    try {
      await api.acknowledgeOperationalAlert(alertId);
      await fetchData();
    } catch (err: any) {
      alert(err.response?.data?.message || err.message || 'Failed to acknowledge alert');
    }
  };

  const handleResolveAlert = async (alertId: string) => {
    try {
      await api.resolveOperationalAlert(alertId, 'Resolved via Operations Hub');
      await fetchData();
    } catch (err: any) {
      alert(err.response?.data?.message || err.message || 'Failed to resolve alert');
    }
  };

  const handleDismissAlert = async (alertId: string) => {
    try {
      await api.dismissOperationalAlert(alertId);
      await fetchData();
    } catch (err: any) {
      alert(err.response?.data?.message || err.message || 'Failed to dismiss alert');
    }
  };

  const handleSynthesizeTask = async () => {
    if (!selectedAlertForTask) return;
    try {
      await api.createTaskFromOperationalAlert(selectedAlertForTask.id, {
        assignee_member_id: alertTaskAssignee || undefined
      });
      setSelectedAlertForTask(null);
      setAlertTaskAssignee('');
      await fetchData();
    } catch (err: any) {
      alert(err.response?.data?.message || err.message || 'Failed to synthesize task');
    }
  };

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formTitle.trim()) {
      setFormError('Task title is required.');
      return;
    }

    try {
      setIsSubmitting(true);
      setFormError(null);

      await api.createBusinessTask({
        title: formTitle.trim(),
        description: formDescription.trim() || undefined,
        priority: formPriority,
        category: formCategory,
        assignee_member_id: formAssigneeId || undefined,
        location_id: formLocationId || undefined,
        product_id: formProductId || undefined,
        due_date: formDueDate || undefined,
        notes: formNotes.trim() || undefined,
      });

      setIsCreateModalOpen(false);
      setFormTitle('');
      setFormDescription('');
      setFormPriority('MEDIUM');
      setFormCategory('GENERAL');
      setFormAssigneeId('');
      setFormLocationId('');
      setFormProductId('');
      setFormDueDate('');
      setFormNotes('');
      fetchData();
    } catch (err: any) {
      setFormError(err?.message || 'Failed to create task.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleStatusChange = async (task: TaskItem, newStatus: string) => {
    try {
      await api.transitionBusinessTaskStatus(task.id, newStatus);
      fetchData();
      if (selectedTask && selectedTask.id === task.id) {
        setSelectedTask({ ...selectedTask, status: newStatus as any });
      }
    } catch (err: any) {
      alert(err?.message || 'Failed to transition task status.');
    }
  };

  const handleAssignChange = async (task: TaskItem, newAssigneeId: string) => {
    try {
      await api.assignBusinessTask(task.id, newAssigneeId || null);
      fetchData();
      if (selectedTask && selectedTask.id === task.id) {
        const found = members.find(m => m.id === newAssigneeId);
        setSelectedTask({
          ...selectedTask,
          assignee_member_id: newAssigneeId || null,
          assignee_name: found?.user?.full_name || found?.user?.email || null,
        });
      }
    } catch (err: any) {
      alert(err?.message || 'Failed to assign task.');
    }
  };

  const handleDeleteTask = async (taskId: string) => {
    if (!window.confirm('Are you sure you want to delete this task?')) return;
    try {
      await api.deleteBusinessTask(taskId);
      setIsDrawerOpen(false);
      setSelectedTask(null);
      fetchData();
    } catch (err: any) {
      alert(err?.message || 'Failed to delete task.');
    }
  };

  const columns: ColumnDef<any>[] = [
    {
      key: 'priority',
      header: 'Priority',
      render: (task: TaskItem) => {
        const colorMap: Record<string, string> = {
          URGENT: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
          HIGH: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
          MEDIUM: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30',
          LOW: 'bg-slate-500/10 text-slate-400 border-slate-500/30',
        };
        return (
          <span className={`px-2 py-0.5 rounded-full text-[11px] font-bold border ${colorMap[task.priority] || colorMap.MEDIUM}`}>
            {task.priority}
          </span>
        );
      },
    },
    {
      key: 'title',
      header: 'Task & Context',
      render: (task: TaskItem) => (
        <div className="space-y-1">
          <div className="font-semibold text-slate-100 flex items-center gap-2">
            <span>{task.title}</span>
            {task.category && task.category !== 'GENERAL' && (
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 uppercase font-mono">
                {task.category}
              </span>
            )}
          </div>
          {task.description && (
            <div className="text-xs text-slate-400 line-clamp-1">{task.description}</div>
          )}
          <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-500">
            {task.location_name && (
              <span className="flex items-center gap-1">
                <MapPin className="w-3 h-3 text-slate-400" />
                {task.location_name}
              </span>
            )}
            {task.product_name && (
              <span className="flex items-center gap-1">
                <Package className="w-3 h-3 text-slate-400" />
                {task.product_name}
              </span>
            )}
          </div>
        </div>
      ),
    },
    {
      key: 'assignee_name',
      header: 'Assignee',
      render: (task: TaskItem) => (
        <div className="flex items-center gap-2 text-xs">
          <div className="w-6 h-6 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-400">
            <UserIcon className="w-3 h-3" />
          </div>
          <div>
            <div className="font-medium text-slate-200">
              {task.assignee_name || <span className="text-slate-500 italic">Unassigned</span>}
            </div>
            {task.assignee_email && (
              <div className="text-[10px] text-slate-500">{task.assignee_email}</div>
            )}
          </div>
        </div>
      ),
    },
    {
      key: 'due_date',
      header: 'Due Date',
      render: (task: TaskItem) => {
        if (!task.due_date) return <span className="text-xs text-slate-500">—</span>;
        const due = new Date(task.due_date);
        return (
          <div className="flex items-center gap-1.5 text-xs">
            <Calendar className={`w-3.5 h-3.5 ${task.is_overdue ? 'text-rose-400' : 'text-slate-400'}`} />
            <span className={task.is_overdue ? 'text-rose-400 font-semibold' : 'text-slate-300'}>
              {due.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })}
            </span>
            {task.is_overdue && (
              <span className="px-1.5 py-0.2 rounded bg-rose-500/20 text-rose-300 text-[10px] font-bold">OVERDUE</span>
            )}
          </div>
        );
      },
    },
    {
      key: 'status',
      header: 'Status',
      render: (task: TaskItem) => (
        <StatusBadge status={task.status} />
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (task: TaskItem) => (
        <button
          onClick={(e) => {
            e.stopPropagation();
            setSelectedTask(task);
            setIsDrawerOpen(true);
          }}
          className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors cursor-pointer"
        >
          Details
        </button>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <BusinessPageHeader
        title="Business Tasks & Operations Control"
        description="Assign, track, and manage operational execution and automated signal alerting across facilities."
        primaryAction={
          canCreate
            ? {
                label: 'Create Task',
                onClick: () => setIsCreateModalOpen(true),
                icon: Plus,
                variant: 'primary',
              }
            : undefined
        }
      />

      <OperationsSubNav />

      {/* Tabs Switcher: Tasks Queue vs Operational Alerts */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setActiveTab('TASKS')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              activeTab === 'TASKS'
                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                : 'text-slate-400 hover:text-slate-200 bg-slate-900/40 border border-transparent'
            }`}
          >
            <CheckSquare className="w-4 h-4" />
            <span>Tasks Queue ({tasks.length})</span>
          </button>
          <button
            onClick={() => setActiveTab('ALERTS')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              activeTab === 'ALERTS'
                ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                : 'text-slate-400 hover:text-slate-200 bg-slate-900/40 border border-transparent'
            }`}
          >
            <Bell className="w-4 h-4" />
            <span>Operational Alerts</span>
            {activeAlertsCount > 0 && (
              <span className="px-1.5 py-0.5 rounded-full bg-rose-500 text-white text-[10px] font-extrabold animate-pulse">
                {activeAlertsCount}
              </span>
            )}
          </button>
        </div>

        {activeTab === 'ALERTS' && (
          <button
            onClick={handleEvaluateSignals}
            disabled={evaluatingAlerts}
            className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition-all disabled:opacity-50 cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${evaluatingAlerts ? 'animate-spin' : ''}`} />
            <span>{evaluatingAlerts ? 'Evaluating...' : 'Evaluate Signals'}</span>
          </button>
        )}
      </div>

      {activeTab === 'TASKS' && (
        <>
          {/* Metrics Bar */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="p-3.5 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-md">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Total Tasks</span>
              <div className="text-xl font-bold text-slate-100 mt-1">{totalCount}</div>
            </div>
            <div className="p-3.5 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-md">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">To Do</span>
              <div className="text-xl font-bold text-slate-300 mt-1">{todoCount}</div>
            </div>
            <div className="p-3.5 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-md">
              <span className="text-[11px] font-semibold text-indigo-400 uppercase tracking-wider">In Progress</span>
              <div className="text-xl font-bold text-indigo-300 mt-1">{inProgressCount}</div>
            </div>
            <div className="p-3.5 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-md">
              <span className="text-[11px] font-semibold text-amber-400 uppercase tracking-wider">Blocked</span>
              <div className="text-xl font-bold text-amber-300 mt-1">{blockedCount}</div>
            </div>
            <div className="p-3.5 rounded-2xl bg-slate-900/60 border border-rose-500/30 bg-rose-500/5 backdrop-blur-md">
              <span className="text-[11px] font-semibold text-rose-400 uppercase tracking-wider">Overdue</span>
              <div className="text-xl font-bold text-rose-400 mt-1">{overdueCount}</div>
            </div>
            <div className="p-3.5 rounded-2xl bg-slate-900/60 border border-emerald-500/30 bg-emerald-500/5 backdrop-blur-md">
              <span className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider">Completed</span>
              <div className="text-xl font-bold text-emerald-400 mt-1">{doneCount}</div>
            </div>
          </div>

          {/* Filter Bar */}
          <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-md flex flex-wrap items-center justify-between gap-4">
            <div className="flex flex-wrap items-center gap-3">
              <div className="relative min-w-[240px]">
                <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Search tasks, descriptions..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full bg-slate-950/60 border border-slate-800 rounded-xl pl-10 pr-4 py-2 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-emerald-500/50"
                />
              </div>

              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="bg-slate-950/60 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500/50"
              >
                <option value="ALL">All Statuses</option>
                <option value="TODO">To Do</option>
                <option value="IN_PROGRESS">In Progress</option>
                <option value="BLOCKED">Blocked</option>
                <option value="DONE">Done</option>
                <option value="CANCELLED">Cancelled</option>
              </select>

              <select
                value={priorityFilter}
                onChange={(e) => setPriorityFilter(e.target.value)}
                className="bg-slate-950/60 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500/50"
              >
                <option value="ALL">All Priorities</option>
                <option value="URGENT">Urgent</option>
                <option value="HIGH">High</option>
                <option value="MEDIUM">Medium</option>
                <option value="LOW">Low</option>
              </select>

              <select
                value={assigneeFilter}
                onChange={(e) => setAssigneeFilter(e.target.value)}
                className="bg-slate-950/60 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500/50"
              >
                <option value="ALL">All Assignees</option>
                <option value="ME">Assigned to Me</option>
                <option value="UNASSIGNED">Unassigned</option>
                {members.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.user?.full_name || m.user?.email || m.id}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Tasks Table */}
          <BusinessDataTable
            columns={columns}
            data={filteredTasks}
            keyExtractor={(task) => task.id}
            loading={loading}
            emptyTitle="No business tasks found"
            emptyDescription="Create a task or change filter criteria."
            onRowClick={(task: any) => {
              setSelectedTask(task);
              setIsDrawerOpen(true);
            }}
          />
        </>
      )}

      {activeTab === 'ALERTS' && (
        <div className="space-y-4">
          {alerts.length === 0 ? (
            <div className="p-8 rounded-2xl bg-slate-900/40 border border-slate-800 text-center space-y-3">
              <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto" />
              <div className="text-sm font-bold text-slate-200">No Active Operational Alerts</div>
              <div className="text-xs text-slate-400">All inventory levels, delivery dates, and supplier quality metrics are nominal.</div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {alerts.map((alert) => {
                const severityColors = {
                  CRITICAL: 'bg-rose-500/10 border-rose-500/40 text-rose-400',
                  WARNING: 'bg-amber-500/10 border-amber-500/40 text-amber-400',
                  INFO: 'bg-blue-500/10 border-blue-500/40 text-blue-400',
                };

                return (
                  <div
                    key={alert.id}
                    className={`p-4 rounded-2xl border backdrop-blur-md space-y-3 ${
                      severityColors[alert.severity] || severityColors.WARNING
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="px-2 py-0.5 rounded text-[10px] font-extrabold uppercase bg-slate-950/60 border border-current">
                            {alert.severity}
                          </span>
                          <span className="text-[11px] font-mono text-slate-400 uppercase">
                            {alert.alert_type}
                          </span>
                          <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            alert.status === 'ACTIVE' ? 'bg-rose-500/20 text-rose-300' :
                            alert.status === 'ACKNOWLEDGED' ? 'bg-amber-500/20 text-amber-300' : 'bg-emerald-500/20 text-emerald-300'
                          }`}>
                            {alert.status}
                          </span>
                        </div>
                        <h4 className="text-sm font-bold text-slate-100">{alert.title}</h4>
                      </div>
                    </div>

                    <p className="text-xs text-slate-300 leading-relaxed">
                      {alert.description}
                    </p>

                    {alert.recommended_action && (
                      <div className="text-[11px] text-slate-400 flex items-center gap-1.5 pt-1 border-t border-slate-800/40">
                        <Zap className="w-3.5 h-3.5 text-amber-400" />
                        <span>Recommended Action: <strong className="text-slate-200">{alert.recommended_action}</strong></span>
                      </div>
                    )}

                    <div className="flex items-center justify-between pt-2 border-t border-slate-800/40 text-xs">
                      <div className="flex items-center gap-2">
                        {alert.status === 'ACTIVE' && (
                          <button
                            onClick={() => handleAcknowledgeAlert(alert.id)}
                            className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-[11px] font-semibold transition-colors cursor-pointer"
                          >
                            Acknowledge
                          </button>
                        )}
                        {alert.status !== 'RESOLVED' && alert.status !== 'DISMISSED' && (
                          <button
                            onClick={() => handleResolveAlert(alert.id)}
                            className="px-2.5 py-1 rounded-lg bg-emerald-600/20 border border-emerald-500/30 text-emerald-300 hover:bg-emerald-600/30 text-[11px] font-semibold transition-colors cursor-pointer"
                          >
                            Resolve
                          </button>
                        )}
                        {alert.status !== 'RESOLVED' && alert.status !== 'DISMISSED' && (
                          <button
                            onClick={() => handleDismissAlert(alert.id)}
                            className="px-2 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 text-[11px] font-semibold transition-colors cursor-pointer"
                          >
                            Dismiss
                          </button>
                        )}
                      </div>

                      {!alert.generated_task_id ? (
                        <button
                          onClick={() => setSelectedAlertForTask(alert)}
                          className="flex items-center gap-1 px-3 py-1 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-[11px] transition-colors cursor-pointer"
                        >
                          <span>Convert to Task</span>
                          <ArrowRight className="w-3 h-3" />
                        </button>
                      ) : (
                        <span className="text-[11px] text-emerald-400 font-bold flex items-center gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>Task Generated</span>
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Convert Alert to Task Modal */}
      {selectedAlertForTask && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between p-4 border-b border-slate-800">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Zap className="w-4 h-4 text-amber-400" />
                <span>Synthesize Task from Alert</span>
              </h3>
              <button
                onClick={() => setSelectedAlertForTask(null)}
                className="text-slate-400 hover:text-slate-200 text-xs cursor-pointer"
              >
                ✕
              </button>
            </div>
            <div className="p-4 space-y-4 text-xs">
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1">
                <div className="font-bold text-slate-100">{selectedAlertForTask.title}</div>
                <div className="text-slate-400">{selectedAlertForTask.description}</div>
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Assign To Team Member (Optional)</label>
                <select
                  value={alertTaskAssignee}
                  onChange={(e) => setAlertTaskAssignee(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500/50"
                >
                  <option value="">Unassigned (Queue)</option>
                  {members.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.user?.full_name || m.user?.email || m.id} ({m.role})
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  onClick={() => setSelectedAlertForTask(null)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-bold transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSynthesizeTask}
                  className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition-colors cursor-pointer"
                >
                  Generate Task
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Task Detail Drawer */}
      <DetailDrawer
        isOpen={isDrawerOpen}
        onClose={() => {
          setIsDrawerOpen(false);
          setSelectedTask(null);
        }}
        title={selectedTask?.title || 'Task Details'}
        subtitle={selectedTask ? `ID: ${selectedTask.id}` : undefined}
      >
        {selectedTask && (
          <div className="space-y-6">
            {/* Status & Priority */}
            <div className="flex items-center justify-between">
              <StatusBadge status={selectedTask.status} />
              <span className="px-2.5 py-1 rounded-full text-xs font-bold border bg-slate-800 text-slate-300 border-slate-700">
                Priority: {selectedTask.priority}
              </span>
            </div>

            {/* Description */}
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-400">Description</label>
              <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-200 whitespace-pre-wrap leading-relaxed">
                {selectedTask.description || <span className="text-slate-500 italic">No description provided.</span>}
              </div>
            </div>

            {/* Quick Status Actions */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-400">Update Status</label>
              <div className="flex flex-wrap gap-2">
                {selectedTask.status !== 'IN_PROGRESS' && selectedTask.status !== 'DONE' && (
                  <button
                    onClick={() => handleStatusChange(selectedTask, 'IN_PROGRESS')}
                    className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 hover:bg-indigo-600/30 transition-colors cursor-pointer"
                  >
                    Start Working
                  </button>
                )}
                {selectedTask.status !== 'DONE' && (
                  <button
                    onClick={() => handleStatusChange(selectedTask, 'DONE')}
                    className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-emerald-600/20 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-600/30 transition-colors cursor-pointer"
                  >
                    Mark as Done
                  </button>
                )}
                {selectedTask.status !== 'BLOCKED' && selectedTask.status !== 'DONE' && (
                  <button
                    onClick={() => handleStatusChange(selectedTask, 'BLOCKED')}
                    className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-amber-600/20 text-amber-300 border border-amber-500/30 hover:bg-amber-600/30 transition-colors cursor-pointer"
                  >
                    Mark Blocked
                  </button>
                )}
                {selectedTask.status !== 'CANCELLED' && selectedTask.status !== 'DONE' && (
                  <button
                    onClick={() => handleStatusChange(selectedTask, 'CANCELLED')}
                    className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-rose-600/20 text-rose-300 border border-rose-500/30 hover:bg-rose-600/30 transition-colors cursor-pointer"
                  >
                    Cancel Task
                  </button>
                )}
              </div>
            </div>

            {/* Assignment Box */}
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
              <label className="text-xs font-semibold text-slate-300 block">Assignee</label>
              <select
                value={selectedTask.assignee_member_id || ''}
                onChange={(e) => handleAssignChange(selectedTask, e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500/50"
              >
                <option value="">Unassigned</option>
                {members.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.user?.full_name || m.user?.email || m.id} ({m.role})
                  </option>
                ))}
              </select>
            </div>

            {/* Context & Metadata */}
            <div className="space-y-2 text-xs">
              <div className="flex justify-between py-1.5 border-b border-slate-800/60">
                <span className="text-slate-400">Due Date</span>
                <span className={`font-mono ${selectedTask.is_overdue ? 'text-rose-400 font-bold' : 'text-slate-200'}`}>
                  {selectedTask.due_date ? new Date(selectedTask.due_date).toLocaleString() : 'None'}
                </span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-800/60">
                <span className="text-slate-400">Location</span>
                <span className="text-slate-200">{selectedTask.location_name || 'All Facilities'}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-800/60">
                <span className="text-slate-400">Linked SKU</span>
                <span className="text-slate-200">{selectedTask.product_name || 'None'}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-800/60">
                <span className="text-slate-400">Created By</span>
                <span className="text-slate-200">{selectedTask.creator_name || 'System'}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-800/60">
                <span className="text-slate-400">Created At</span>
                <span className="text-slate-400 font-mono">{new Date(selectedTask.created_at).toLocaleString()}</span>
              </div>
            </div>

            {/* Danger Zone */}
            {canDelete && (
              <div className="pt-4 border-t border-slate-800">
                <button
                  onClick={() => handleDeleteTask(selectedTask.id)}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/30 hover:bg-rose-500/20 text-xs font-bold transition-all cursor-pointer"
                >
                  <Trash2 className="w-4 h-4" />
                  <span>Delete Task</span>
                </button>
              </div>
            )}
          </div>
        )}
      </DetailDrawer>

      {/* Create Task Modal */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="w-full max-w-lg bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between p-4 border-b border-slate-800">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <CheckSquare className="w-4 h-4 text-emerald-400" />
                <span>Create Business Task</span>
              </h3>
              <button
                onClick={() => setIsCreateModalOpen(false)}
                className="text-slate-400 hover:text-slate-200 text-xs cursor-pointer"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateTask} className="p-4 space-y-4">
              {formError && (
                <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs">
                  {formError}
                </div>
              )}

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-300">
                  Task Title <span className="text-rose-400">*</span>
                </label>
                <input
                  type="text"
                  placeholder="e.g. Conduct physical inventory count for Bay A"
                  value={formTitle}
                  onChange={(e) => setFormTitle(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500/50"
                  required
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-300">Description</label>
                <textarea
                  rows={3}
                  placeholder="Provide instructions or operational details..."
                  value={formDescription}
                  onChange={(e) => setFormDescription(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500/50 resize-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-300">Priority</label>
                  <select
                    value={formPriority}
                    onChange={(e) => setFormPriority(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500/50"
                  >
                    <option value="LOW">Low</option>
                    <option value="MEDIUM">Medium</option>
                    <option value="HIGH">High</option>
                    <option value="URGENT">Urgent</option>
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-300">Category</label>
                  <select
                    value={formCategory}
                    onChange={(e) => setFormCategory(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500/50"
                  >
                    <option value="GENERAL">General</option>
                    <option value="INVENTORY">Inventory</option>
                    <option value="PROCUREMENT">Procurement</option>
                    <option value="MAINTENANCE">Maintenance</option>
                    <option value="DISPATCH">Dispatch</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-300">Assignee</label>
                  <select
                    value={formAssigneeId}
                    onChange={(e) => setFormAssigneeId(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500/50"
                  >
                    <option value="">Unassigned</option>
                    {members.map((m) => (
                      <option key={m.id} value={m.id}>
                        {m.user?.full_name || m.user?.email || m.id}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-300">Due Date</label>
                  <input
                    type="datetime-local"
                    value={formDueDate}
                    onChange={(e) => setFormDueDate(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500/50"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-300">Location</label>
                  <select
                    value={formLocationId}
                    onChange={(e) => setFormLocationId(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500/50"
                  >
                    <option value="">None / All Facilities</option>
                    {locations.map((l) => (
                      <option key={l.id} value={l.id}>
                        {l.name} ({l.location_type})
                      </option>
                    ))}
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-300">Linked SKU / Product</label>
                  <select
                    value={formProductId}
                    onChange={(e) => setFormProductId(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500/50"
                  >
                    <option value="">None</option>
                    {products.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name} ({p.sku})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsCreateModalOpen(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-bold transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow-lg shadow-emerald-500/20 transition-all disabled:opacity-50 cursor-pointer"
                >
                  {isSubmitting ? 'Creating...' : 'Create Task'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
