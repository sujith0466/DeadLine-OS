import React, { useState, useEffect, useCallback } from 'react';
import {
  Users,
  UserPlus,
  ShieldCheck,
  Mail,
  X,
} from 'lucide-react';
import { api } from '../../api';
import { useBusinessAuth } from '../../context/BusinessAuthContext';
import type { BusinessMember, BusinessRole } from '../../context/BusinessAuthContext';
import { BusinessPageHeader } from '../../components/Business/BusinessPageHeader';
import { ExecutiveMetricCard } from '../../components/Business/ExecutiveMetricCard';
import { StatusBadge } from '../../components/Business/StatusBadge';
import { BusinessDataTable } from '../../components/Business/BusinessDataTable';
import type { ColumnDef } from '../../components/Business/BusinessDataTable';
import { DetailDrawer } from '../../components/Business/DetailDrawer';
import { BusinessLoadingState } from '../../components/Business/BusinessLoadingState';
import { BusinessErrorState } from '../../components/Business/BusinessErrorState';
import { GovernanceSubNav } from '../../components/Business/GovernanceSubNav';

interface MemberRecord extends BusinessMember, Record<string, any> {}

interface WorkspaceInvitationRecord extends Record<string, any> {
  id: string;
  workspace_id: string;
  email: string;
  role: string;
  status: 'PENDING' | 'ACCEPTED' | 'REVOKED' | 'EXPIRED';
  expires_at: string;
  created_at: string;
}

export const BusinessTeam: React.FC = () => {
  const { activeWorkspace, currentMember, hasPermission } = useBusinessAuth();

  const [members, setMembers] = useState<MemberRecord[]>([]);
  const [invitations, setInvitations] = useState<WorkspaceInvitationRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [isInviteModalOpen, setIsInviteModalOpen] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState<BusinessRole>('MEMBER');
  const [inviteLoading, setInviteLoading] = useState(false);
  const [inviteError, setInviteError] = useState<string | null>(null);

  const [selectedMember, setSelectedMember] = useState<MemberRecord | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  const canInvite = hasPermission('members:invite');
  const canManageRoles = hasPermission('members:role_update');
  const canRemove = hasPermission('members:remove');

  const loadData = useCallback(async () => {
    if (!activeWorkspace) return;
    try {
      setLoading(true);
      setError(null);

      const [memRes, invRes] = await Promise.all([
        api.listWorkspaceMembers(),
        api.listWorkspaceInvitations().catch(() => ({ data: { invitations: [] } }))
      ]);

      setMembers(memRes.data?.members || []);
      setInvitations(invRes.data?.invitations || []);
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || err?.message || 'Failed to load team members');
    } finally {
      setLoading(false);
    }
  }, [activeWorkspace]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Escape key handler for invite modal
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isInviteModalOpen) {
        setIsInviteModalOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isInviteModalOpen]);

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteEmail.trim()) return;

    try {
      setInviteLoading(true);
      setInviteError(null);

      await api.inviteWorkspaceMember({
        email: inviteEmail.trim(),
        role: inviteRole,
      });

      setIsInviteModalOpen(false);
      setInviteEmail('');
      setInviteRole('MEMBER');
      loadData();
    } catch (err: any) {
      setInviteError(err?.response?.data?.error?.message || err?.message || 'Failed to send invitation');
    } finally {
      setInviteLoading(false);
    }
  };

  const handleUpdateRole = async (newRole: BusinessRole) => {
    if (!selectedMember) return;
    try {
      setActionLoading(true);
      await api.updateWorkspaceMemberRole(selectedMember.id, newRole);
      loadData();
      setSelectedMember(prev => prev ? { ...prev, role: newRole } : null);
    } catch (err: any) {
      alert(err?.response?.data?.error?.message || 'Failed to update member role');
    } finally {
      setActionLoading(false);
    }
  };

  const handleToggleStatus = async () => {
    if (!selectedMember) return;
    const newStatus = selectedMember.status === 'ACTIVE' ? 'SUSPENDED' : 'ACTIVE';
    try {
      setActionLoading(true);
      await api.updateWorkspaceMemberStatus(selectedMember.id, newStatus);
      loadData();
      setSelectedMember(prev => prev ? { ...prev, status: newStatus } : null);
    } catch (err: any) {
      alert(err?.response?.data?.error?.message || 'Failed to update member status');
    } finally {
      setActionLoading(false);
    }
  };

  const handleRevokeInvitation = async (invitationId: string) => {
    try {
      await api.revokeWorkspaceInvitation(invitationId);
      loadData();
    } catch (err: any) {
      alert(err?.response?.data?.error?.message || 'Failed to revoke invitation');
    }
  };

  const ownersCount = members.filter(m => m.role === 'OWNER').length;
  const activeMembersCount = members.filter(m => m.status === 'ACTIVE').length;
  const pendingInvitesCount = invitations.filter(i => i.status === 'PENDING').length;

  const memberColumns: ColumnDef<MemberRecord>[] = [
    {
      key: 'user',
      header: 'Member / User',
      render: (m) => (
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-xs font-bold text-white shadow-sm">
            {(m.email || 'U').charAt(0).toUpperCase()}
          </div>
          <div>
            <div className="font-semibold text-white flex items-center gap-2">
              <span>{m.email || 'Personnel'}</span>
              {m.id === currentMember?.id && (
                <span className="px-2 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-[10px] text-indigo-400 font-medium">
                  You
                </span>
              )}
            </div>
            <div className="text-[11px] text-slate-500 font-mono">
              Member ID: {m.id.slice(0, 8)}...
            </div>
          </div>
        </div>
      ),
    },
    {
      key: 'role',
      header: 'Assigned RBAC Role',
      render: (m) => (
        <span className={`px-2.5 py-1 rounded-md text-xs font-semibold font-mono ${
          m.role === 'OWNER'
            ? 'bg-purple-500/10 border border-purple-500/20 text-purple-300'
            : m.role === 'ADMIN'
            ? 'bg-indigo-500/10 border border-indigo-500/20 text-indigo-300'
            : m.role === 'ACCOUNTANT'
            ? 'bg-amber-500/10 border border-amber-500/20 text-amber-300'
            : 'bg-slate-800 text-slate-300'
        }`}>
          {m.role}
        </span>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (m) => (
        <StatusBadge
          status={m.status === 'ACTIVE' ? 'ACTIVE' : 'SUSPENDED'}
        />
      ),
    },
    {
      key: 'joined',
      header: 'Joined On',
      render: (m) => (
        <span className="text-xs text-slate-400">
          {m.joined_at ? new Date(m.joined_at).toLocaleDateString() : '—'}
        </span>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (m) => (
        <button
          onClick={(e) => {
            e.stopPropagation();
            setSelectedMember(m);
            setIsDrawerOpen(true);
          }}
          className="text-xs text-indigo-400 hover:text-indigo-300 font-medium px-2.5 py-1 rounded-lg hover:bg-slate-800 transition-colors"
        >
          Manage
        </button>
      ),
    },
  ];

  if (loading && members.length === 0) {
    return (
      <div className="space-y-6">
        <BusinessPageHeader
          title="Team & Access"
          breadcrumbs={[
            { label: 'Governance', href: '/business/team' },
            { label: 'Team & Access' },
          ]}
        />
        <GovernanceSubNav />
        <BusinessLoadingState type="kpi-grid" rows={3} />
        <BusinessLoadingState type="table" rows={6} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <BusinessPageHeader
          title="Team & Access"
          breadcrumbs={[
            { label: 'Governance', href: '/business/team' },
            { label: 'Team & Access' },
          ]}
        />
        <GovernanceSubNav />
        <BusinessErrorState message={error} onRetry={loadData} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <BusinessPageHeader
        title="Team & Access Management"
        breadcrumbs={[
          { label: 'Governance', href: '/business/team' },
          { label: 'Team & Access Management' },
        ]}
        primaryAction={
          canInvite
            ? {
                label: 'Invite Team Member',
                icon: UserPlus,
                onClick: () => setIsInviteModalOpen(true),
              }
            : undefined
        }
      />

      <GovernanceSubNav />

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <ExecutiveMetricCard
          label="Active Workspace Members"
          value={activeMembersCount}
          subtext="Enforced by 5-tier RBAC"
          icon={Users}
          iconColor="text-emerald-400"
        />
        <ExecutiveMetricCard
          label="Workspace Owners"
          value={ownersCount}
          subtext="Cryptographic administrative authority"
          icon={ShieldCheck}
          iconColor="text-purple-400"
        />
        <ExecutiveMetricCard
          label="Pending Invitations"
          value={pendingInvitesCount}
          subtext="Awaiting tenant onboarding"
          icon={Mail}
        />
      </div>

      {/* Members Table */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          <Users className="w-4 h-4 text-indigo-400" />
          <span>Active Workspace Personnel ({members.length})</span>
        </h3>

        <BusinessDataTable
          columns={memberColumns}
          data={members}
          keyExtractor={(m) => m.id}
          onRowClick={(m) => {
            setSelectedMember(m);
            setIsDrawerOpen(true);
          }}
        />
      </div>

      {/* Pending Invitations Section */}
      {invitations.length > 0 && (
        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80 space-y-3">
          <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2">
            <Mail className="w-3.5 h-3.5 text-indigo-400" />
            <span>Pending Outbound Invitations ({invitations.length})</span>
          </h4>

          <div className="divide-y divide-slate-800/60">
            {invitations.map((inv) => (
              <div key={inv.id} className="py-3 flex items-center justify-between">
                <div>
                  <div className="text-sm font-medium text-white">{inv.email}</div>
                  <div className="text-xs text-slate-400 flex items-center gap-2 mt-0.5">
                    <span>Role: <strong className="text-slate-300">{inv.role}</strong></span>
                    <span>•</span>
                    <span>Status: <strong className="text-amber-400">{inv.status}</strong></span>
                  </div>
                </div>

                {canInvite && inv.status === 'PENDING' && (
                  <button
                    onClick={() => handleRevokeInvitation(inv.id)}
                    className="text-xs text-rose-400 hover:text-rose-300 font-medium px-3 py-1.5 rounded-lg hover:bg-rose-500/10 border border-rose-500/20 transition-all"
                  >
                    Revoke
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Member Manage Drawer */}
      <DetailDrawer
        isOpen={isDrawerOpen && Boolean(selectedMember)}
        onClose={() => setIsDrawerOpen(false)}
        title={selectedMember?.email || 'Workspace Member'}
        subtitle="Workspace Access & Role Administration"
      >
        {selectedMember && (
          <div className="space-y-6">
            {/* Status overview */}
            <div className="flex items-center justify-between p-4 rounded-2xl bg-slate-950/60 border border-slate-800">
              <div className="space-y-1">
                <div className="text-xs text-slate-400">Current Role</div>
                <div className="text-sm font-bold text-white font-mono">{selectedMember.role}</div>
              </div>
              <div className="space-y-1 text-right">
                <div className="text-xs text-slate-400">Status</div>
                <StatusBadge
                  status={selectedMember.status === 'ACTIVE' ? 'ACTIVE' : 'SUSPENDED'}
                />
              </div>
            </div>

            {/* Role Modification */}
            {canManageRoles && (
              <div className="space-y-3">
                <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Update Assigned RBAC Role
                </h4>
                <div className="grid grid-cols-2 gap-2">
                  {(['ADMIN', 'ACCOUNTANT', 'MEMBER', 'VIEWER'] as BusinessRole[]).map((r) => (
                    <button
                      key={r}
                      disabled={actionLoading || selectedMember.role === r}
                      onClick={() => handleUpdateRole(r)}
                      className={`p-3 rounded-xl border text-xs font-semibold transition-all text-left ${
                        selectedMember.role === r
                          ? 'bg-indigo-600/20 border-indigo-500/40 text-indigo-300'
                          : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800'
                      }`}
                    >
                      <div className="font-bold">{r}</div>
                      <div className="text-[10px] text-slate-500 mt-0.5">
                        {r === 'ADMIN' ? 'Full operational control' : r === 'ACCOUNTANT' ? 'Ledger & reconciliation' : r === 'MEMBER' ? 'Standard operations' : 'Read-only audit'}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Status Controls */}
            {canRemove && selectedMember.role !== 'OWNER' && (
              <div className="pt-4 border-t border-slate-800 space-y-3">
                <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Membership State
                </h4>
                <button
                  disabled={actionLoading}
                  onClick={handleToggleStatus}
                  className={`w-full py-2.5 rounded-xl text-xs font-semibold transition-all ${
                    selectedMember.status === 'ACTIVE'
                      ? 'bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/20 text-amber-300'
                      : 'bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/20 text-emerald-300'
                  }`}
                >
                  {selectedMember.status === 'ACTIVE' ? 'Suspend Member Access' : 'Re-activate Member Access'}
                </button>
              </div>
            )}
          </div>
        )}
      </DetailDrawer>

      {/* Invite Modal */}
      {isInviteModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="invite-modal-title"
            className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl flex flex-col"
          >
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/40">
              <h3 id="invite-modal-title" className="font-semibold text-white flex items-center gap-2">
                <UserPlus className="w-4 h-4 text-indigo-400" />
                Invite Workspace Member
              </h3>
              <button
                onClick={() => setIsInviteModalOpen(false)}
                aria-label="Close invite modal"
                className="text-slate-400 hover:text-white p-2 rounded-lg hover:bg-slate-800 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/50"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleInvite} className="p-6 space-y-4">
              {inviteError && (
                <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs">
                  {inviteError}
                </div>
              )}

              <div>
                <label className="text-xs font-semibold text-slate-400">Email Address</label>
                <input
                  type="email"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  placeholder="colleague@company.com"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white mt-1 focus:outline-none focus:border-indigo-500"
                  required
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-400">Assigned RBAC Role</label>
                <select
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value as BusinessRole)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white mt-1 focus:outline-none focus:border-indigo-500"
                >
                  <option value="MEMBER">MEMBER — Standard operational access</option>
                  <option value="ADMIN">ADMIN — Management & team controls</option>
                  <option value="ACCOUNTANT">ACCOUNTANT — Financial ledger & audit</option>
                  <option value="VIEWER">VIEWER — Read-only observation</option>
                </select>
              </div>

              <div className="pt-2 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setIsInviteModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={inviteLoading || !inviteEmail.trim()}
                  className="px-5 py-2 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white transition-all shadow-lg shadow-indigo-600/30 disabled:opacity-50"
                >
                  {inviteLoading ? 'Sending...' : 'Send Invitation'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default BusinessTeam;
