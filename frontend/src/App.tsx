import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import { Layout } from './components/Layout/Layout';
import { ErrorBoundary } from './components/ErrorBoundary';
import { PageReveal } from './components/UI/PageReveal';
import { AnimatePresence } from 'framer-motion';
import { GlobalErrorToast } from './components/GlobalErrorToast';

import { Landing } from './pages/Landing';
import { Dashboard } from './pages/Dashboard';
import { Planner } from './pages/Planner';
import { Rescue } from './pages/Rescue';
import { DigitalTwin } from './pages/DigitalTwin';
import { Vision } from './pages/Vision';
import { CommandCenter } from './pages/CommandCenter';
import { Analytics } from './pages/Analytics';
import { Calendar } from './pages/Calendar';
import { Interventions } from './pages/Interventions';
import { Goals } from './pages/Goals';
import { DocumentIntelligence } from './pages/DocumentIntelligence';
import { VoiceCopilot } from './pages/VoiceCopilot';

const AnimatedRoutes = () => {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/" element={<PageReveal><Landing /></PageReveal>} />
        
        <Route element={<Layout />}>
          <Route path="/dashboard" element={<PageReveal><Dashboard /></PageReveal>} />
          <Route path="/planner" element={<PageReveal><Planner /></PageReveal>} />
          <Route path="/rescue" element={<PageReveal><Rescue /></PageReveal>} />
          <Route path="/digital-twin" element={<PageReveal><DigitalTwin /></PageReveal>} />
          <Route path="/vision" element={<PageReveal><Vision /></PageReveal>} />
          <Route path="/command-center" element={<PageReveal><CommandCenter /></PageReveal>} />
          <Route path="/analytics" element={<PageReveal><Analytics /></PageReveal>} />
          <Route path="/calendar" element={<PageReveal><Calendar /></PageReveal>} />
          <Route path="/interventions" element={<PageReveal><Interventions /></PageReveal>} />
          <Route path="/goals" element={<PageReveal><Goals /></PageReveal>} />
          <Route path="/documents" element={<PageReveal><DocumentIntelligence /></PageReveal>} />
          <Route path="/voice" element={<PageReveal><VoiceCopilot /></PageReveal>} />
        </Route>
      </Routes>
    </AnimatePresence>
  );
};

function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <AnimatedRoutes />
        <GlobalErrorToast />
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;
