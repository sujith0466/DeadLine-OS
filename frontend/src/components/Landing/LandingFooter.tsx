import React from 'react';
import { Link } from 'react-router-dom';
import { Brain, ShieldCheck } from 'lucide-react';
import type { ProductMode } from './ProductModeSwitcher';

interface LandingFooterProps {
  mode: ProductMode;
}

export const LandingFooter: React.FC<LandingFooterProps> = ({ mode: _mode }) => {
  return (
    <footer className="bg-[#050608] border-t border-white/5 py-12 text-gray-400 text-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center text-white">
              <Brain className="w-5 h-5" />
            </div>
            <div>
              <span className="text-sm font-bold text-white tracking-tight">DeadlineOS</span>
              <span className="ml-2 px-2 py-0.5 rounded-full bg-white/5 border border-white/10 text-[10px] text-gray-400 font-mono">
                v1.0.0
              </span>
            </div>
          </div>

          <div className="flex items-center gap-6">
            <a href="#features" className="hover:text-white transition-colors">Capabilities</a>
            <a href="#workflow" className="hover:text-white transition-colors">Pipeline</a>
            <a href="#agents" className="hover:text-white transition-colors">Intelligence</a>
            <a href="#faq" className="hover:text-white transition-colors">FAQ</a>
            <Link to="/login" className="hover:text-white transition-colors">Sign In</Link>
          </div>

          <div className="flex items-center gap-2 text-gray-500">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Personal & Enterprise Operating System</span>
          </div>

        </div>

        <div className="mt-8 pt-6 border-t border-white/5 text-center text-gray-600">
          © {new Date().getFullYear()} DeadlineOS Inc. All rights reserved. Precision intelligence for personal momentum and commercial enterprise.
        </div>
      </div>
    </footer>
  );
};
