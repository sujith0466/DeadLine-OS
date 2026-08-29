import React, { useState, useEffect } from 'react';
import { api } from '../../api';
import { Building2, ChevronDown, Plus, Check } from 'lucide-react';

interface Workspace {
  id: string;
  name: string;
  legal_name?: string;
  member_role: string;
  status: string;
}

export const WorkspaceSwitcher: React.FC = () => {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [activeWorkspaceId, setActiveWorkspaceId] = useState<string | null>(
    localStorage.getItem('active_workspace_id')
  );
  const [isOpen, setIsOpen] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [newWsName, setNewWsName] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    loadWorkspaces();
  }, []);

  const loadWorkspaces = async () => {
    try {
      const res = await api.listWorkspaces();
      if (res.status === 'success' && res.data?.workspaces) {
        const list: Workspace[] = res.data.workspaces;
        setWorkspaces(list);
        if (list.length > 0 && (!activeWorkspaceId || !list.find(w => w.id === activeWorkspaceId))) {
          selectWorkspace(list[0].id);
        }
      }
    } catch (err) {
      console.error('Failed to load workspaces:', err);
    }
  };

  const selectWorkspace = (id: string) => {
    setActiveWorkspaceId(id);
    localStorage.setItem('active_workspace_id', id);
    window.dispatchEvent(new CustomEvent('deadline_workspace_changed', { detail: id }));
    setIsOpen(false);
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newWsName.trim()) return;

    setIsLoading(true);
    try {
      const res = await api.createWorkspace({ name: newWsName.trim() });
      if (res.status === 'success' && res.data?.workspace) {
        setNewWsName('');
        setIsCreating(false);
        await loadWorkspaces();
        selectWorkspace(res.data.workspace.id);
      }
    } catch (err) {
      console.error('Failed to create workspace:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const activeWs = workspaces.find(w => w.id === activeWorkspaceId);

  return (
    <div className="relative inline-block text-left">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 text-sm font-medium text-white transition-colors"
      >
        <Building2 className="w-4 h-4 text-emerald-400" />
        <span className="truncate max-w-[140px]">
          {activeWs ? activeWs.name : 'Select Workspace'}
        </span>
        <ChevronDown className="w-3.5 h-3.5 text-zinc-400" />
      </button>

      {isOpen && (
        <div className="absolute left-0 mt-2 w-56 rounded-xl bg-zinc-900/95 border border-white/10 shadow-2xl backdrop-blur-xl z-50 p-1.5">
          <div className="text-xs font-semibold uppercase tracking-wider text-zinc-400 px-2.5 py-1.5">
            Workspaces
          </div>

          <div className="max-h-48 overflow-y-auto space-y-0.5">
            {workspaces.map(ws => (
              <button
                key={ws.id}
                onClick={() => selectWorkspace(ws.id)}
                className={`w-full flex items-center justify-between px-2.5 py-2 rounded-lg text-xs transition-colors ${
                  ws.id === activeWorkspaceId
                    ? 'bg-emerald-500/10 text-emerald-300 font-medium'
                    : 'text-zinc-300 hover:bg-white/5'
                }`}
              >
                <div className="truncate text-left">
                  <div>{ws.name}</div>
                  <div className="text-[10px] text-zinc-500 capitalize">{ws.member_role.toLowerCase()}</div>
                </div>
                {ws.id === activeWorkspaceId && <Check className="w-3.5 h-3.5 text-emerald-400" />}
              </button>
            ))}
          </div>

          <div className="border-t border-white/5 mt-1.5 pt-1.5">
            {isCreating ? (
              <form onSubmit={handleCreate} className="p-1 space-y-1.5">
                <input
                  type="text"
                  placeholder="Workspace Name"
                  value={newWsName}
                  onChange={e => setNewWsName(e.target.value)}
                  className="w-full px-2 py-1 text-xs rounded bg-white/5 border border-white/10 text-white placeholder-zinc-500 focus:outline-none focus:border-emerald-500"
                  autoFocus
                />
                <div className="flex gap-1">
                  <button
                    type="submit"
                    disabled={isLoading || !newWsName.trim()}
                    className="flex-1 px-2 py-1 text-xs bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-black font-semibold rounded"
                  >
                    {isLoading ? 'Creating...' : 'Create'}
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsCreating(false)}
                    className="px-2 py-1 text-xs text-zinc-400 hover:text-white"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            ) : (
              <button
                onClick={() => setIsCreating(true)}
                className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs text-zinc-400 hover:text-white hover:bg-white/5 transition-colors"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>New Workspace</span>
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
