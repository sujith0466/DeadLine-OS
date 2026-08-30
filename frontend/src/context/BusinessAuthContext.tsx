import React, { createContext, useContext, useEffect, useState, useCallback, useMemo } from 'react';
import { useAuth } from './AuthContext';
import { api } from '../api';

export type BusinessRole = 'OWNER' | 'ADMIN' | 'MEMBER' | 'ACCOUNTANT' | 'VIEWER';

export interface BusinessWorkspace {
  id: string;
  name: string;
  legal_name?: string | null;
  tax_identifier?: string | null;
  base_currency: string;
  timezone: string;
  status: 'ACTIVE' | 'SUSPENDED' | 'ARCHIVED';
  member_role?: BusinessRole;
  member_status?: 'ACTIVE' | 'SUSPENDED' | 'INVITED';
  created_at?: string;
  updated_at?: string;
}

export interface BusinessMember {
  id: string;
  workspace_id: string;
  user_id: string;
  role: BusinessRole;
  status: 'ACTIVE' | 'SUSPENDED' | 'INVITED';
  created_at?: string;
  updated_at?: string;
}

export interface BusinessAuthContextType {
  workspaces: BusinessWorkspace[];
  activeWorkspace: BusinessWorkspace | null;
  currentMember: BusinessMember | null;
  role: BusinessRole | null;
  permissions: string[];
  loading: boolean;
  error: string | null;

  refreshWorkspaces: () => Promise<void>;
  selectWorkspace: (workspaceId: string) => Promise<void>;
  createWorkspace: (data: {
    name: string;
    legal_name?: string;
    tax_identifier?: string;
    base_currency?: string;
    timezone?: string;
  }) => Promise<BusinessWorkspace>;
  clearWorkspace: () => void;

  hasPermission: (permission: string) => boolean;
  hasAnyPermission: (permissions: string[]) => boolean;
  hasAllPermissions: (permissions: string[]) => boolean;

  isBusinessMember: boolean;
  isWorkspaceActive: boolean;
  isSuspended: boolean;
}

const BusinessAuthContext = createContext<BusinessAuthContextType | undefined>(undefined);

const WORKSPACE_STORAGE_KEY = 'active_workspace_id';
const NAMESPACED_STORAGE_KEY = 'deadlineos_business_active_workspace_id';

export const BusinessAuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, loading: authLoading } = useAuth();

  const [workspaces, setWorkspaces] = useState<BusinessWorkspace[]>([]);
  const [activeWorkspace, setActiveWorkspace] = useState<BusinessWorkspace | null>(null);
  const [currentMember, setCurrentMember] = useState<BusinessMember | null>(null);
  const [role, setRole] = useState<BusinessRole | null>(null);
  const [permissions, setPermissions] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Helper to persist active workspace ID in localStorage
  const persistWorkspaceId = useCallback((id: string | null) => {
    if (id) {
      localStorage.setItem(WORKSPACE_STORAGE_KEY, id);
      localStorage.setItem(NAMESPACED_STORAGE_KEY, id);
    } else {
      localStorage.removeItem(WORKSPACE_STORAGE_KEY);
      localStorage.removeItem(NAMESPACED_STORAGE_KEY);
    }
  }, []);

  // Helper to get stored workspace ID
  const getStoredWorkspaceId = useCallback((): string | null => {
    return localStorage.getItem(NAMESPACED_STORAGE_KEY) || localStorage.getItem(WORKSPACE_STORAGE_KEY) || null;
  }, []);

  // Hydrate active workspace permissions and member details from server
  const hydrateWorkspaceDetails = useCallback(async (workspace: BusinessWorkspace) => {
    try {
      // Ensure the storage key matches this workspace
      persistWorkspaceId(workspace.id);

      const res = await api.getCurrentWorkspace();
      if (res && res.data) {
        if (res.data.permissions) {
          setPermissions(res.data.permissions);
        }
        if (res.data.member) {
          setCurrentMember(res.data.member);
          setRole(res.data.member.role as BusinessRole);
        } else if (workspace.member_role) {
          setRole(workspace.member_role);
        }
      }
    } catch (err: any) {
      // If 403 or suspended, clear active workspace state safely
      if (err.response?.status === 403 || err.response?.status === 401) {
        setActiveWorkspace(null);
        setCurrentMember(null);
        setRole(null);
        setPermissions([]);
        persistWorkspaceId(null);
        setError("Workspace access denied or membership suspended.");
      }
    }
  }, [persistWorkspaceId]);

  // Discover user's active workspaces
  const refreshWorkspaces = useCallback(async () => {
    if (!user) {
      setWorkspaces([]);
      setActiveWorkspace(null);
      setCurrentMember(null);
      setRole(null);
      setPermissions([]);
      setLoading(false);
      setError(null);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const res = await api.listWorkspaces();
      const userWorkspaces: BusinessWorkspace[] = res?.data?.workspaces || [];
      setWorkspaces(userWorkspaces);

      if (userWorkspaces.length === 0) {
        setActiveWorkspace(null);
        setCurrentMember(null);
        setRole(null);
        setPermissions([]);
        persistWorkspaceId(null);
        setLoading(false);
        return;
      }

      // Check stored workspace ID
      const storedId = getStoredWorkspaceId();
      const storedMatch = storedId
        ? userWorkspaces.find(w => w.id === storedId && w.status === 'ACTIVE' && w.member_status === 'ACTIVE')
        : null;

      if (storedMatch) {
        setActiveWorkspace(storedMatch);
        setRole(storedMatch.member_role || null);
        await hydrateWorkspaceDetails(storedMatch);
      } else {
        // Fall back to first active workspace
        const firstActive = userWorkspaces.find(w => w.status === 'ACTIVE' && w.member_status === 'ACTIVE');
        if (firstActive) {
          setActiveWorkspace(firstActive);
          setRole(firstActive.member_role || null);
          await hydrateWorkspaceDetails(firstActive);
        } else {
          setActiveWorkspace(null);
          setCurrentMember(null);
          setRole(null);
          setPermissions([]);
          persistWorkspaceId(null);
        }
      }
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || err?.message || 'Failed to discover workspaces.');
    } finally {
      setLoading(false);
    }
  }, [user, getStoredWorkspaceId, hydrateWorkspaceDetails, persistWorkspaceId]);

  // Initial hydration when user identity changes
  useEffect(() => {
    if (authLoading) return;
    refreshWorkspaces();
  }, [user, authLoading, refreshWorkspaces]);

  // Select an active workspace
  const selectWorkspace = useCallback(async (workspaceId: string) => {
    const target = workspaces.find(w => w.id === workspaceId);
    if (!target) {
      throw new Error(`Workspace with ID ${workspaceId} not found in user memberships.`);
    }

    if (target.status !== 'ACTIVE' || target.member_status !== 'ACTIVE') {
      throw new Error(`Cannot select suspended or inactive workspace.`);
    }

    setActiveWorkspace(target);
    setRole(target.member_role || null);
    persistWorkspaceId(target.id);
    await hydrateWorkspaceDetails(target);
  }, [workspaces, persistWorkspaceId, hydrateWorkspaceDetails]);

  // Create a new workspace and select it atomically
  const createWorkspace = useCallback(async (data: {
    name: string;
    legal_name?: string;
    tax_identifier?: string;
    base_currency?: string;
    timezone?: string;
  }): Promise<BusinessWorkspace> => {
    setError(null);
    const res = await api.createWorkspace(data);
    const createdWorkspace: BusinessWorkspace = res.data.workspace;
    createdWorkspace.member_role = 'OWNER';
    createdWorkspace.member_status = 'ACTIVE';

    setWorkspaces(prev => [...prev, createdWorkspace]);
    setActiveWorkspace(createdWorkspace);
    setRole('OWNER');
    persistWorkspaceId(createdWorkspace.id);
    await hydrateWorkspaceDetails(createdWorkspace);
    return createdWorkspace;
  }, [persistWorkspaceId, hydrateWorkspaceDetails]);

  // Clear workspace context
  const clearWorkspace = useCallback(() => {
    setActiveWorkspace(null);
    setCurrentMember(null);
    setRole(null);
    setPermissions([]);
    persistWorkspaceId(null);
  }, [persistWorkspaceId]);

  // Permission Evaluation Helpers
  const hasPermission = useCallback((permission: string): boolean => {
    return permissions.includes(permission);
  }, [permissions]);

  const hasAnyPermission = useCallback((reqPermissions: string[]): boolean => {
    return reqPermissions.some(p => permissions.includes(p));
  }, [permissions]);

  const hasAllPermissions = useCallback((reqPermissions: string[]): boolean => {
    return reqPermissions.every(p => permissions.includes(p));
  }, [permissions]);

  const isBusinessMember = useMemo(() => workspaces.length > 0, [workspaces]);
  const isWorkspaceActive = useMemo(() => activeWorkspace?.status === 'ACTIVE' && activeWorkspace?.member_status === 'ACTIVE', [activeWorkspace]);
  const isSuspended = useMemo(() => activeWorkspace?.status === 'SUSPENDED' || activeWorkspace?.member_status === 'SUSPENDED', [activeWorkspace]);

  const value = useMemo<BusinessAuthContextType>(() => ({
    workspaces,
    activeWorkspace,
    currentMember,
    role,
    permissions,
    loading: authLoading || loading,
    error,
    refreshWorkspaces,
    selectWorkspace,
    createWorkspace,
    clearWorkspace,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    isBusinessMember,
    isWorkspaceActive,
    isSuspended,
  }), [
    workspaces,
    activeWorkspace,
    currentMember,
    role,
    permissions,
    authLoading,
    loading,
    error,
    refreshWorkspaces,
    selectWorkspace,
    createWorkspace,
    clearWorkspace,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    isBusinessMember,
    isWorkspaceActive,
    isSuspended,
  ]);

  return (
    <BusinessAuthContext.Provider value={value}>
      {children}
    </BusinessAuthContext.Provider>
  );
};

export const useBusinessAuth = (): BusinessAuthContextType => {
  const context = useContext(BusinessAuthContext);
  if (context === undefined) {
    throw new Error('useBusinessAuth must be used within a BusinessAuthProvider');
  }
  return context;
};
