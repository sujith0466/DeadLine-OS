import React, { useState } from 'react';
import { LandingNavigation } from '../components/Landing/LandingNavigation';
import { HeroSection } from '../components/Landing/HeroSection';
import { TrustedMetrics } from '../components/Landing/TrustedMetrics';
import { ProductShowcase } from '../components/Landing/ProductShowcase';
import { InteractiveWorkflow } from '../components/Landing/InteractiveWorkflow';
import { HowItThinks } from '../components/Landing/HowItThinks';
import { ModeSpecificShowcase } from '../components/Landing/ModeSpecificShowcase';
import { TrustSecuritySection } from '../components/Landing/TrustSecuritySection';
import { FAQSection } from '../components/Landing/FAQSection';
import { CTASection } from '../components/Landing/CTASection';
import { LandingFooter } from '../components/Landing/LandingFooter';
import { Background } from '../components/Landing/Background';
import type { ProductMode } from '../components/Landing/ProductModeSwitcher';

export const Landing: React.FC = () => {
  const [mode, setMode] = useState<ProductMode>('personal');

  return (
    <div className="bg-[#020617] min-h-screen text-gray-50 font-sans selection:bg-indigo-500/30 relative">
      <Background />
      <LandingNavigation />
      <main>
        <HeroSection mode={mode} onModeChange={setMode} />
        <TrustedMetrics mode={mode} />
        <ProductShowcase mode={mode} />
        <InteractiveWorkflow mode={mode} />
        <HowItThinks mode={mode} />
        <ModeSpecificShowcase mode={mode} />
        <TrustSecuritySection mode={mode} />
        <FAQSection mode={mode} />
        <CTASection mode={mode} />
      </main>
      <LandingFooter mode={mode} />
    </div>
  );
};
