import React from 'react';
import { Background } from '../components/Landing/Background';
import { Navbar } from '../components/Landing/Navbar';
import { HeroSection } from '../components/Landing/HeroSection';
import { MetricsSection } from '../components/Landing/MetricsSection';
import { FeatureGrid } from '../components/Landing/FeatureGrid';
import { AgentEcosystem } from '../components/Landing/AgentEcosystem';
import { WorkflowTimeline } from '../components/Landing/WorkflowTimeline';
import { WhyDeadlineOS } from '../components/Landing/WhyDeadlineOS';
import { FinalCTA } from '../components/Landing/FinalCTA';
import { Footer } from '../components/Landing/Footer';

export const Landing: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col relative overflow-hidden bg-[#020617] selection:bg-primary/30 text-white font-sans">
      <Background />
      <Navbar />
      
      <main className="flex-1 flex flex-col w-full z-10">
        <HeroSection />
        <MetricsSection />
        <FeatureGrid />
        <AgentEcosystem />
        <WorkflowTimeline />
        <WhyDeadlineOS />
        <FinalCTA />
      </main>
      
      <Footer />
    </div>
  );
};

