import React, { useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { FocusSession } from '../FocusSession/FocusSession';
import { Sidebar } from './Sidebar';
import { Navbar } from './Navbar';
import { AppBackground } from './AppBackground';

export const Layout: React.FC = () => {
  useEffect(() => {
    try {
      localStorage.setItem('deadlineos-landing-mode', 'personal');
    } catch {}
  }, []);
  return (
    <div className="flex min-h-screen relative overflow-hidden bg-[#020617] text-white font-sans selection:bg-primary/30">
      <AppBackground />
      <Sidebar />
      <div className="flex-1 ml-64 flex flex-col min-h-screen z-10 relative">
        <Navbar />
        <main className="flex-1 p-8 overflow-y-auto">
          <Outlet />
          <FocusSession />
        </main>
      </div>
    </div>
  );
};
