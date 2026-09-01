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

export const BusinessTasks: React.FC = () => {
  const { activeWorkspace, role } = useBusinessAuth();
  const { user } = useAuth();

  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [members, setMembers] = useState<any[]>([]);
  const [locations, setLocations] = useState<any[]>([]);
  const [products, setProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [priorityFilter, setPriorityFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Modals & Drawers
  const [selectedTask, setSelectedTask] = useState<TaskItem | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState<boolean>(false);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState<boolean>(false);

  // Create Form State
  const [formTitle, setFormTitle] = useState('');
  const [formDescription, setFormDescription] = useState('');
  const [formPriority, setFormPriority] = useState('MEDIUM');
  const [formCategory, setFormCategory] = useState('GENERAL');
  const [formAssigneeId, setFormAssigneeId] = useState('');
  const [formLocationId, setFormLocationId] = useState('');
  const [formProductId, setFormProductId] = useState('');
  const [formDueDate, setFormDueDate] = useState('');
  const [formNotes, setFormNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const canCreate = role === 'OWNER' || role === 'ADMIN' || role === 'MEMBER';
  const canDelete = role === 'OWNER' || role === 'ADMIN';

  const fetchData = useCallback(async () => {
    if (!activeWorkspace) return;
    setLoading(true);
    try {
      const [tasksRes, membersRes, locsRes, prodsRes] = await Promise.allSettled([
        api.listBusinessTasks(),
        api.listWorkspaceMembers(),
        api.listLocations(),
        api.listProducts(),
      ]);

      if (tasksRes.status === 'fulfilled' && tasksRes.value?.data?.tasks) {
        setTasks(tasksRes.value.data.tasks);
      } else {
        setTasks([]);
      }

      if (membersRes.status === 'fulfilled' && membersRes.value?.data?.members) {
        setMembers(membersRes.value.data.members);
      }
      if (locsRes.status === 'fulfilled' && locsRes.value?.data?.locations) {
        setLocations(locsRes.value.data.locations);
      }
      if (prodsRes.status === 'fulfilled' && prodsRes.value?.data?.products) {
        setProducts(prodsRes.value.data.products);
      }
    } catch (err: any) {
      console.error('Failed to load task records', err);
    } finally {
      setLoading(false);
    }
  }, [activeWorkspace]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Derived metrics
  const totalCount = tasks.length;
  const todoCount = tasks.filter(t => t.status === 'TODO').length;
  const inProgressCount = tasks.filter(t => t.status === 'IN_PROGRESS').length;
  const blockedCount = tasks.filter(t => t.status === 'BLOCKED').length;
  const overdueCount = tasks.filter(t => t.is_overdue).length;
  const doneCount = tasks.filter(t => t.status === 'DONE').length;

  // Filtered tasks
  const filteredTasks = useMemo(() => {
    return tasks.filter(task => {
      if (statusFilter === 'MY_TASKS') {
        const myMember = members.find(m => m.user_id === user?.id);
        if (!myMember || task.assignee_member_id !== myMember.id) return false;
      } else if (statusFilter === 'OVERDUE') {
        if (!task.is_overdue) return false;
      } else if (statusFilter !== 'ALL' && task.status !== statusFilter) {
        return false;
      }

      if (priorityFilter !== 'ALL' && task.priority !== priorityFilter) {
        return false;
      }

      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        const matchTitle = task.title.toLowerCase().includes(query);
        const matchDesc = task.description?.toLowerCase().includes(query);
        const matchAssignee = task.assignee_name?.toLowerCase().includes(query);
        const matchLocation = task.location_name?.toLowerCase().includes(query);
        if (!matchTitle && !matchDesc && !matchAssignee && !matchLocation) return false;
      }

      return true;
    });
  }, [tasks, statusFilter, priorityFilter, searchQuery, members, user]);

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formTitle.trim()) {
      setFormError('Task title is required.');
      return;
    }

    setIsSubmitting(true);
    setFormError(null);
    try {
      await api.createBusinessTask({
        title: formTitle.trim(),
        description: formDescription.trim() || undefined,
        priority: formPriority,
        category: formCategory,
        assignee_member_id: formAssigneeId || undefined,
        location_id: formLocationId || undefined,
        product_id: formProductId || undefined,
        due_date: formDueDate ? new Date(formDueDate).toISOString() : undefined,
        notes: formNotes.trim() || undefined,
      });
      setIsCreateModalOpen(false);
      // Reset form
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

  const columns: ColumnDef<TaskItem>[] = [
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
          <span className={`px-2 py-0.5 rounded text-[10px] font-bold tracking-wider border ${colorMap[task.priority] || colorMap.MEDIUM}`}>
            {task.priority}
          </span>
        );
      },
    },
    {
      key: 'title',
      header: 'Task Title & Context',
      render: (task: TaskItem) => (
        <div className="flex flex-col">
          <span className="font-semibold text-slate-100">{task.title}</span>
          <div className="flex items-center gap-2 text-xs text-slate-400 mt-0.5">
            <span className="bg-slate-800 px-1.5 py-0.5 rounded text-[10px] uppercase font-mono">{task.category}</span>
            {task.location_name && (
              <span className="flex items-center gap-1 text-slate-400">
                <MapPin className="w-3 h-3 text-slate-500" />
                {task.location_name}
              </span>
            )}
            {task.product_name && (
              <span className="flex items-center gap-1 text-slate-400">
                <Package className="w-3 h-3 text-slate-500" />
                {task.product_name}
              </span>
            )}
          </div>
        </div>
      ),
    },
    {
      key: 'assignee',
      header: 'Assignee',
      render: (task: TaskItem) => (
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-bold text-slate-300">
            {task.assignee_name ? task.assignee_name.charAt(0).toUpperCase() : <UserIcon className="w-3 h-3 text-slate-500" />}
          </div>
          <span className="text-xs text-slate-300 font-medium">
            {task.assignee_name || <span className="text-slate-500 italic">Unassigned</span>}
          </span>
        </div>
      ),
    },
    {
      key: 'due_date',
      header: 'Due Date',
      render: (task: TaskItem) => {
        if (!task.due_date) return <span className="text-xs text-slate-500">No deadline</span>;
        const due = new Date(task.due_date);
        return (
          <div className="flex items-center gap-1.5">
            <Calendar className={`w-3.5 h-3.5 ${task.is_overdue ? 'text-rose-400' : 'text-slate-400'}`} />
            <span className={`text-xs font-mono ${task.is_overdue ? 'text-rose-400 font-semibold' : 'text-slate-300'}`}>
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
          className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
        >
          Details
        </button>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <BusinessPageHeader
        title="Business Tasks & Work Allocation"
        description="Assign, track, and manage operational execution across facilities and team members."
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

      {/* Filter Tabs & Search */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3 p-2 rounded-2xl bg-slate-900/60 border border-slate-800/80">
        <div className="flex items-center gap-1 overflow-x-auto no-scrollbar w-full md:w-auto">
          {[
            { id: 'ALL', label: 'All Tasks' },
            { id: 'MY_TASKS', label: 'My Tasks' },
            { id: 'TODO', label: 'To Do' },
            { id: 'IN_PROGRESS', label: 'In Progress' },
            { id: 'BLOCKED', label: 'Blocked' },
            { id: 'OVERDUE', label: 'Overdue' },
            { id: 'DONE', label: 'Done' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setStatusFilter(tab.id)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all cursor-pointer ${
                statusFilter === tab.id
                  ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.03]'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2 w-full md:w-auto">
          <div className="relative flex-1 md:w-56">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search tasks..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-950/80 border border-slate-800 rounded-xl pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500/50"
            />
          </div>

          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="bg-slate-950/80 border border-slate-800 rounded-xl px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-emerald-500/50"
          >
            <option value="ALL">All Priorities</option>
            <option value="URGENT">Urgent</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>
        </div>
      </div>

      {/* Main Table */}
      <BusinessDataTable
        data={filteredTasks}
        columns={columns}
        keyExtractor={(task) => task.id}
        loading={loading}
        emptyTitle="No Tasks Found"
        emptyDescription={
          statusFilter !== 'ALL' || searchQuery
            ? 'No tasks match the active filter criteria.'
            : 'Create your first operational task to allocate work to team members.'
        }
        emptyActionLabel={canCreate && statusFilter === 'ALL' && !searchQuery ? 'Create First Task' : undefined}
        onEmptyAction={canCreate ? () => setIsCreateModalOpen(true) : undefined}
        onRowClick={(task) => {
          setSelectedTask(task);
          setIsDrawerOpen(true);
        }}
      />

      {/* Detail & Workflow Drawer */}
      <DetailDrawer
        isOpen={isDrawerOpen && !!selectedTask}
        onClose={() => {
          setIsDrawerOpen(false);
          setSelectedTask(null);
        }}
        title="Task Details & Lifecycle"
      >
        {selectedTask && (
          <div className="space-y-6">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="px-2 py-0.5 rounded text-[10px] font-bold border border-slate-700 bg-slate-800 text-slate-300 uppercase">
                  {selectedTask.priority}
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-400 uppercase">
                  {selectedTask.category}
                </span>
              </div>
              <h3 className="text-lg font-bold text-white">{selectedTask.title}</h3>
              {selectedTask.description && (
                <p className="text-xs text-slate-300 mt-2 leading-relaxed whitespace-pre-wrap">
                  {selectedTask.description}
                </p>
              )}
            </div>

            {/* Lifecycle Transition Actions */}
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
              <span className="text-xs font-semibold text-slate-300 block">Status Transition</span>
              <div className="flex flex-wrap gap-2">
                {selectedTask.status !== 'IN_PROGRESS' && (
                  <button
                    onClick={() => handleStatusChange(selectedTask, 'IN_PROGRESS')}
                    className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 hover:bg-indigo-600/30 transition-colors"
                  >
                    Start Working (In Progress)
                  </button>
                )}
                {selectedTask.status !== 'DONE' && (
                  <button
                    onClick={() => handleStatusChange(selectedTask, 'DONE')}
                    className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-emerald-600/20 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-600/30 transition-colors"
                  >
                    Mark as Done
                  </button>
                )}
                {selectedTask.status !== 'BLOCKED' && selectedTask.status !== 'DONE' && (
                  <button
                    onClick={() => handleStatusChange(selectedTask, 'BLOCKED')}
                    className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-amber-600/20 text-amber-300 border border-amber-500/30 hover:bg-amber-600/30 transition-colors"
                  >
                    Mark Blocked
                  </button>
                )}
                {selectedTask.status !== 'CANCELLED' && selectedTask.status !== 'DONE' && (
                  <button
                    onClick={() => handleStatusChange(selectedTask, 'CANCELLED')}
                    className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-rose-600/20 text-rose-300 border border-rose-500/30 hover:bg-rose-600/30 transition-colors"
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
                className="text-slate-400 hover:text-slate-200 text-xs"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateTask} className="p-4 space-y-4 text-xs">
              {formError && (
                <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 font-semibold">
                  {formError}
                </div>
              )}

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Title *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Receive raw material shipment from Supplier A"
                  value={formTitle}
                  onChange={(e) => setFormTitle(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500/50"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Description</label>
                <textarea
                  rows={3}
                  placeholder="Detailed task instructions..."
                  value={formDescription}
                  onChange={(e) => setFormDescription(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500/50"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Priority</label>
                  <select
                    value={formPriority}
                    onChange={(e) => setFormPriority(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-emerald-500/50"
                  >
                    <option value="LOW">Low</option>
                    <option value="MEDIUM">Medium</option>
                    <option value="HIGH">High</option>
                    <option value="URGENT">Urgent</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Category</label>
                  <select
                    value={formCategory}
                    onChange={(e) => setFormCategory(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-emerald-500/50"
                  >
                    <option value="GENERAL">General</option>
                    <option value="INVENTORY">Inventory</option>
                    <option value="PROCUREMENT">Procurement</option>
                    <option value="FACILITY">Facility</option>
                    <option value="AUDIT">Audit</option>
                    <option value="MAINTENANCE">Maintenance</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Assignee</label>
                  <select
                    value={formAssigneeId}
                    onChange={(e) => setFormAssigneeId(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-emerald-500/50"
                  >
                    <option value="">Unassigned</option>
                    {members.map((m) => (
                      <option key={m.id} value={m.id}>
                        {m.user?.full_name || m.user?.email} ({m.role})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Due Date</label>
                  <input
                    type="datetime-local"
                    value={formDueDate}
                    onChange={(e) => setFormDueDate(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-emerald-500/50"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Location</label>
                  <select
                    value={formLocationId}
                    onChange={(e) => setFormLocationId(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-emerald-500/50"
                  >
                    <option value="">All Locations</option>
                    {locations.map((loc) => (
                      <option key={loc.id} value={loc.id}>
                        {loc.name} ({loc.location_type})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Linked SKU</label>
                  <select
                    value={formProductId}
                    onChange={(e) => setFormProductId(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-emerald-500/50"
                  >
                    <option value="">None</option>
                    {products.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.sku} - {p.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsCreateModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-slate-400 hover:text-slate-200 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold disabled:opacity-50"
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
