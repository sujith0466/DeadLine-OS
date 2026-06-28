import React, { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { DeadlineOSApi } from '../api';
import { useAuth } from './AuthContext';

interface SettingsState {
  profile: any;
  appearance: any;
  notifications: any;
  planner: any;
  ai: any;
  security: any;
}

interface SettingsContextProps {
  settings: SettingsState;
  loading: boolean;
  refreshSettings: () => Promise<void>;
  updateSection: (section: string, data: any) => Promise<void>;
}

const SettingsContext = createContext<SettingsContextProps | undefined>(undefined);

const getInitialSettings = (): SettingsState => {
  try {
    const cached = localStorage.getItem('deadlineos_settings');
    if (cached) return JSON.parse(cached);
  } catch (e) {}
  return {
    profile: {},
    appearance: {},
    notifications: {},
    planner: {},
    ai: {},
    security: {}
  };
};

export const SettingsProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { session } = useAuth();
  const [loading, setLoading] = useState(true);
  const [settings, setSettings] = useState<SettingsState>(getInitialSettings);

  const refreshSettings = async () => {
    if (!session) return;
    try {
      setLoading(true);
      const [profile, appearance, notifications, planner, ai, security] = await Promise.all([
        DeadlineOSApi.getProfile().catch(() => ({})),
        DeadlineOSApi.getSettings('appearance').catch(() => ({})),
        DeadlineOSApi.getSettings('notifications').catch(() => ({})),
        DeadlineOSApi.getSettings('planner').catch(() => ({})),
        DeadlineOSApi.getSettings('ai').catch(() => ({})),
        DeadlineOSApi.getSettings('security').catch(() => ({}))
      ]);
      
      const newSettings = {
        profile: profile || {},
        appearance: appearance || {},
        notifications: notifications || {},
        planner: planner || {},
        ai: ai || {},
        security: security || {}
      };
      setSettings(newSettings);
      localStorage.setItem('deadlineos_settings', JSON.stringify(newSettings));
    } catch (err) {
      console.error("Failed to load settings", err);
    } finally {
      setLoading(false);
    }
  };

  const updateSection = async (section: string, data: any) => {
    // Optimistic update
    setSettings(prev => {
      const updated = {
        ...prev,
        [section]: { ...prev[section as keyof SettingsState], ...data }
      };
      localStorage.setItem('deadlineos_settings', JSON.stringify(updated));
      return updated;
    });
    
    try {
      if (section === 'profile') {
        await DeadlineOSApi.updateProfile(data);
      } else {
        await DeadlineOSApi.updateSettings(section, data);
      }
    } catch (err) {
      // Revert on fail
      await refreshSettings();
      throw err;
    }
  };

  useEffect(() => {
    if (session) {
      refreshSettings();
    }
  }, [session]);

  // Sync DOM with Appearance Settings
  useEffect(() => {
    const root = document.documentElement;
    const appearance = settings.appearance || {};

    // Theme logic
    const theme = appearance.theme || 'system';
    const isDark = theme === 'dark' || (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
    
    if (isDark) {
      root.classList.add('dark');
      root.classList.remove('light');
    } else {
      root.classList.add('light');
      root.classList.remove('dark');
    }

    // Accent Color
    root.setAttribute('data-accent', appearance.accent_color || 'indigo');

    // Compact Mode
    if (appearance.compact_mode) {
      root.classList.add('compact-mode');
    } else {
      root.classList.remove('compact-mode');
    }

    // Reduced Motion
    if (appearance.reduced_motion) {
      root.classList.add('reduced-motion');
    } else {
      root.classList.remove('reduced-motion');
    }
  }, [settings.appearance]);

  return (
    <SettingsContext.Provider value={{ settings, loading, refreshSettings, updateSection }}>
      {children}
    </SettingsContext.Provider>
  );
};

export const useSettings = () => {
  const context = useContext(SettingsContext);
  if (!context) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
};
