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
  fiscal_year_start_month?: number | null;
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

  refreshWorkspaces: () => Promise<BusinessWorkspace[]>;
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
const WORKSPACE_CACHE_KEY = 'deadlineos_business_workspace_cache';

interface CachedWorkspaceSnapshot {
  userId?: string | null;
  workspaces: BusinessWorkspace[];
  activeWorkspace: BusinessWorkspace | null;
  currentMember: BusinessMember | null;
  role: BusinessRole | null;
  permissions: string[];
  savedAt: number;
}

const getCachedSnapshot = (): CachedWorkspaceSnapshot | null => {
  try {
    const raw = localStorage.getItem(WORKSPACE_CACHE_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
};

const saveCachedSnapshot = (snapshot: CachedWorkspaceSnapshot | null) => {
  try {
    if (snapshot) {
      localStorage.setItem(WORKSPACE_CACHE_KEY, JSON.stringify(snapshot));
    } else {
      localStorage.removeItem(WORKSPACE_CACHE_KEY);
    }
  } catch {
    // Storage write safety
  }
};

export const BusinessAuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, loading: authLoading } = useAuth();

  // Synchronously restore cached snapshot if available and active
  const cached = useMemo(() => getCachedSnapshot(), []);
  const initialActive = cached?.activeWorkspace ?? null;
  const hasValidCachedContext = Boolean(
    initialActive &&
    initialActive.status === 'ACTIVE' &&
    initialActive.member_status === 'ACTIVE'
  );

  const [workspaces, setWorkspaces] = useState<BusinessWorkspace[]>(() => cached?.workspaces || []);
  const [activeWorkspace, setActiveWorkspace] = useState<BusinessWorkspace | null>(() => initialActive);
  const [currentMember, setCurrentMember] = useState<BusinessMember | null>(() => cached?.currentMember || null);
  const [role, setRole] = useState<BusinessRole | null>(() => cached?.role || null);
  const [permissions, setPermissions] = useState<string[]>(() => cached?.permissions || []);

  // If valid cached workspace context already exists, do not block UI with a loading state on startup/reload
  const [loading, setLoading] = useState<boolean>(() => !hasValidCachedContext);
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
  const hydrateWorkspaceDetails = useCallback(async (workspace: BusinessWorkspace): Promise<{ member: BusinessMember | null; perms: string[] }> => {
    try {
      persistWorkspaceId(workspace.id);

      const res = await api.getCurrentWorkspace();
      let fetchedMember: BusinessMember | null = null;
      let fetchedPerms: string[] = [];

      if (res && res.data) {
        if (res.data.permissions) {
          fetchedPerms = res.data.permissions;
          setPermissions(res.data.permissions);
        }
        if (res.data.member) {
          fetchedMember = res.data.member;
          setCurrentMember(res.data.member);
          setRole(res.data.member.role as BusinessRole);
        } else if (workspace.member_role) {
          setRole(workspace.member_role);
        }
      }
      return { member: fetchedMember, perms: fetchedPerms };
    } catch (err: any) {
      // If 403 or suspended, clear active workspace state safely
      if (err.response?.status === 403 || err.response?.status === 401) {
        setActiveWorkspace(null);
        setCurrentMember(null);
        setRole(null);
        setPermissions([]);
        persistWorkspaceId(null);
        saveCachedSnapshot(null);
        setError("Workspace access denied or membership suspended.");
      }
      return { member: null, perms: [] };
    }
  }, [persistWorkspaceId]);

  // Discover user's active workspaces (with optional silent background revalidation mode)
  const refreshWorkspaces = useCallback(async (isSilent: boolean = false): Promise<BusinessWorkspace[]> => {
    if (!user) {
      setWorkspaces([]);
      setActiveWorkspace(null);
      setCurrentMember(null);
      setRole(null);
      setPermissions([]);
      saveCachedSnapshot(null);
      setLoading(false);
      setError(null);
      return [];
    }

    try {
      if (!isSilent) {
        setLoading(true);
      }
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
        saveCachedSnapshot(null);
        setLoading(false);
        return [];
      }

      // Check stored workspace ID
      const storedId = getStoredWorkspaceId();
      const storedMatch = storedId
        ? userWorkspaces.find(w => w.id === storedId && w.status === 'ACTIVE' && w.member_status === 'ACTIVE')
        : null;

      let selectedWs: BusinessWorkspace | null = null;

      if (storedMatch) {
        selectedWs = storedMatch;
      } else {
        // Fall back to first active workspace
        const firstActive = userWorkspaces.find(w => w.status === 'ACTIVE' && w.member_status === 'ACTIVE');
        if (firstActive) {
          selectedWs = firstActive;
        }
      }

      if (selectedWs) {
        setActiveWorkspace(selectedWs);
        setRole(selectedWs.member_role || null);
        const { member, perms } = await hydrateWorkspaceDetails(selectedWs);

        saveCachedSnapshot({
          userId: user.id,
          workspaces: userWorkspaces,
          activeWorkspace: selectedWs,
          currentMember: member,
          role: (member?.role as BusinessRole) || selectedWs.member_role || null,
          permissions: perms,
          savedAt: Date.now(),
        });
      } else {
        setActiveWorkspace(null);
        setCurrentMember(null);
        setRole(null);
        setPermissions([]);
        persistWorkspaceId(null);
        saveCachedSnapshot(null);
      }

      return userWorkspaces;
    } catch (err: any) {
      const errMsg = err?.response?.data?.error?.message || err?.message || 'Failed to discover workspaces.';
      setError(errMsg);
      if (err.response?.status === 401 || err.response?.status === 403) {
        setActiveWorkspace(null);
        setCurrentMember(null);
        setRole(null);
        setPermissions([]);
        persistWorkspaceId(null);
        saveCachedSnapshot(null);
      }
      if (!isSilent) {
        throw err;
      }
      return [];
    } finally {
      setLoading(false);
    }
  }, [user, getStoredWorkspaceId, hydrateWorkspaceDetails, persistWorkspaceId]);

  // Initial hydration when user identity changes
  useEffect(() => {
    if (authLoading) return;

    if (!user) {
      setWorkspaces([]);
      setActiveWorkspace(null);
      setCurrentMember(null);
      setRole(null);
      setPermissions([]);
      saveCachedSnapshot(null);
      setLoading(false);
      return;
    }

    const cachedSnapshot = getCachedSnapshot();
    const canSilentRevalidate = Boolean(
      cachedSnapshot &&
      cachedSnapshot.userId === user.id &&
      cachedSnapshot.activeWorkspace &&
      cachedSnapshot.activeWorkspace.status === 'ACTIVE' &&
      cachedSnapshot.activeWorkspace.member_status === 'ACTIVE'
    );

    // If safe cached context exists for this user, revalidate in background without blocking UI
    refreshWorkspaces(canSilentRevalidate).catch(() => {});
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
    const { member, perms } = await hydrateWorkspaceDetails(target);

    saveCachedSnapshot({
      userId: user?.id || null,
      workspaces,
      activeWorkspace: target,
      currentMember: member,
      role: (member?.role as BusinessRole) || target.member_role || null,
      permissions: perms,
      savedAt: Date.now(),
    });
  }, [workspaces, user, persistWorkspaceId, hydrateWorkspaceDetails]);

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

    const updatedWorkspaces = [...workspaces, createdWorkspace];
    setWorkspaces(updatedWorkspaces);
    setActiveWorkspace(createdWorkspace);
    setRole('OWNER');
    persistWorkspaceId(createdWorkspace.id);
    const { member, perms } = await hydrateWorkspaceDetails(createdWorkspace);

    saveCachedSnapshot({
      userId: user?.id || null,
      workspaces: updatedWorkspaces,
      activeWorkspace: createdWorkspace,
      currentMember: member,
      role: 'OWNER',
      permissions: perms,
      savedAt: Date.now(),
    });

    return createdWorkspace;
  }, [workspaces, user, persistWorkspaceId, hydrateWorkspaceDetails]);

  // Clear workspace context
  const clearWorkspace = useCallback(() => {
    setActiveWorkspace(null);
    setCurrentMember(null);
    setRole(null);
    setPermissions([]);
    persistWorkspaceId(null);
    saveCachedSnapshot(null);
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
