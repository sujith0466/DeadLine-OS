import React, { Suspense } from 'react';
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import { isSupabaseConfigured } from './lib/supabase';
import { Layout } from './components/Layout/Layout';
import { ErrorBoundary } from './components/ErrorBoundary';
import { PageReveal } from './components/UI/PageReveal';
import { AnimatePresence } from 'framer-motion';
import { GlobalErrorToast } from './components/GlobalErrorToast';
import { AuthProvider } from './context/AuthContext';
import { SettingsProvider } from './context/SettingsContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Login } from './pages/auth/Login';
import { Register } from './pages/auth/Register';

const Landing = React.lazy(() => import('./pages/Landing').then(m => ({ default: m.Landing })));
const Dashboard = React.lazy(() => import('./pages/Dashboard').then(m => ({ default: m.Dashboard })));
const Planner = React.lazy(() => import('./pages/Planner').then(m => ({ default: m.Planner })));
const Rescue = React.lazy(() => import('./pages/Rescue').then(m => ({ default: m.Rescue })));
const DigitalTwin = React.lazy(() => import('./pages/DigitalTwin').then(m => ({ default: m.DigitalTwin })));
const Vision = React.lazy(() => import('./pages/Vision').then(m => ({ default: m.Vision })));
const CommandCenter = React.lazy(() => import('./pages/CommandCenter').then(m => ({ default: m.CommandCenter })));
const Analytics = React.lazy(() => import('./pages/Analytics').then(m => ({ default: m.Analytics })));
const Calendar = React.lazy(() => import('./pages/Calendar').then(m => ({ default: m.Calendar })));
const Goals = React.lazy(() => import('./pages/Goals').then(m => ({ default: m.Goals })));
const DocumentIntelligence = React.lazy(() => import('./pages/DocumentIntelligence').then(m => ({ default: m.DocumentIntelligence })));
const VoiceCopilot = React.lazy(() => import('./pages/VoiceCopilot').then(m => ({ default: m.VoiceCopilot })));
const SettingsLayout = React.lazy(() => import('./pages/Settings/SettingsLayout').then(m => ({ default: m.SettingsLayout })));
const ProfileSettings = React.lazy(() => import('./pages/Settings/ProfileSettings').then(m => ({ default: m.ProfileSettings })));
const AppearanceSettings = React.lazy(() => import('./pages/Settings/AppearanceSettings').then(m => ({ default: m.AppearanceSettings })));
const NotificationSettings = React.lazy(() => import('./pages/Settings/NotificationSettings').then(m => ({ default: m.NotificationSettings })));
const PlannerSettings = React.lazy(() => import('./pages/Settings/PlannerSettings').then(m => ({ default: m.PlannerSettings })));
const AISettings = React.lazy(() => import('./pages/Settings/AISettings').then(m => ({ default: m.AISettings })));
const SecuritySettings = React.lazy(() => import('./pages/Settings/SecuritySettings').then(m => ({ default: m.SecuritySettings })));
const SessionsSettings = React.lazy(() => import('./pages/Settings/SessionsSettings').then(m => ({ default: m.SessionsSettings })));
const ConnectedAccountsSettings = React.lazy(() => import('./pages/Settings/ConnectedAccountsSettings').then(m => ({ default: m.ConnectedAccountsSettings })));
const DataManagementSettings = React.lazy(() => import('./pages/Settings/DataManagementSettings').then(m => ({ default: m.DataManagementSettings })));
const DeleteAccountSettings = React.lazy(() => import('./pages/Settings/DeleteAccountSettings').then(m => ({ default: m.DeleteAccountSettings })));
const AboutSettings = React.lazy(() => import('./pages/Settings/AboutSettings').then(m => ({ default: m.AboutSettings })));

const AnimatedRoutes = () => {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait">
      <Suspense fallback={<div className="flex h-screen items-center justify-center bg-slate-950 text-indigo-500"><div className="animate-pulse">Loading...</div></div>}>
      <Routes location={location} key={location.pathname}>
        <Route path="/" element={<PageReveal><Landing /></PageReveal>} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        
        <Route element={<ProtectedRoute />}>
          <Route element={<Layout />}>
            <Route path="/dashboard" element={<PageReveal><Dashboard /></PageReveal>} />
          <Route path="/planner" element={<PageReveal><Planner /></PageReveal>} />
          <Route path="/rescue" element={<PageReveal><Rescue /></PageReveal>} />
          <Route path="/digital-twin" element={<PageReveal><DigitalTwin /></PageReveal>} />
          <Route path="/vision" element={<PageReveal><Vision /></PageReveal>} />
          <Route path="/command-center" element={<PageReveal><CommandCenter /></PageReveal>} />
          <Route path="/analytics" element={<PageReveal><Analytics /></PageReveal>} />
          <Route path="/calendar" element={<PageReveal><Calendar /></PageReveal>} />
          <Route path="/goals" element={<PageReveal><Goals /></PageReveal>} />
          <Route path="/documents" element={<PageReveal><DocumentIntelligence /></PageReveal>} />
          <Route path="/voice" element={<PageReveal><VoiceCopilot /></PageReveal>} />
          
          {/* Settings Module */}
          <Route path="/settings" element={<PageReveal><SettingsLayout /></PageReveal>}>
            <Route index element={<ProfileSettings />} />
            <Route path="profile" element={<ProfileSettings />} />
            <Route path="appearance" element={<AppearanceSettings />} />
            <Route path="notifications" element={<NotificationSettings />} />
            <Route path="planner" element={<PlannerSettings />} />
            <Route path="ai" element={<AISettings />} />
            <Route path="security" element={<SecuritySettings />} />
            <Route path="sessions" element={<SessionsSettings />} />
            <Route path="accounts" element={<ConnectedAccountsSettings />} />
            <Route path="data" element={<DataManagementSettings />} />
            <Route path="delete" element={<DeleteAccountSettings />} />
            <Route path="about" element={<AboutSettings />} />
            <Route path="*" element={<ProfileSettings />} />
          </Route>
        </Route>
      </Route>
      </Routes>
      </Suspense>
    </AnimatePresence>
  );
};

function App() {
  const isApiConfigured = Boolean(import.meta.env.VITE_API_BASE_URL);
  
  if (!isSupabaseConfigured || !isApiConfigured) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
        <div className="bg-slate-900/50 border border-slate-800 p-8 rounded-2xl max-w-lg text-center">
          <div className="w-16 h-16 bg-red-500/10 text-red-500 rounded-2xl flex items-center justify-center mx-auto mb-6">
            <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-white mb-4">Configuration Error</h1>
          <p className="text-slate-400 mb-6">
            DeadlineOS requires essential environment variables to handle authentication and API routing. 
            However, required environment variables are missing.
          </p>
          <div className="bg-slate-950 p-4 rounded-xl text-left border border-slate-800 font-mono text-sm mb-6">
            <p className="text-slate-500 mb-2">Please add the following to your frontend/.env file:</p>
            {!isSupabaseConfigured && (
              <>
                <p className="text-indigo-400">VITE_SUPABASE_URL="your-supabase-url"</p>
                <p className="text-indigo-400">VITE_SUPABASE_ANON_KEY="your-anon-key"</p>
              </>
            )}
            {!isApiConfigured && (
              <p className="text-indigo-400">VITE_API_BASE_URL="http://localhost:5000/api"</p>
            )}
          </div>
          <button onClick={() => window.location.reload()} className="bg-indigo-600 hover:bg-indigo-500 text-white px-6 py-2.5 rounded-xl font-medium transition-all">
            Retry Initialization
          </button>
        </div>
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <AuthProvider>
        <SettingsProvider>
          <BrowserRouter>
            <AnimatedRoutes />
            <GlobalErrorToast />
          </BrowserRouter>
        </SettingsProvider>
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
