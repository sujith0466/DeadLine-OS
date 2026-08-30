import React, { useState } from 'react';
import { motion, useScroll, useMotionValueEvent, AnimatePresence } from 'framer-motion';
import { Link } from 'react-router-dom';
import { Brain, Menu, X, LogOut } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { ProductModeSwitcher, type ProductMode } from './ProductModeSwitcher';

interface LandingNavigationProps {
  mode: ProductMode;
  onModeChange: (mode: ProductMode) => void;
}

export const LandingNavigation: React.FC<LandingNavigationProps> = ({ mode, onModeChange }) => {
  const { user, signOut } = useAuth();
  const { scrollY } = useScroll();
  const [hidden, setHidden] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useMotionValueEvent(scrollY, "change", (latest) => {
    const previous = scrollY.getPrevious() ?? 0;
    
    if (latest > 50) {
      setIsScrolled(true);
    } else {
      setIsScrolled(false);
    }

    if (latest > previous && latest > 200) {
      setHidden(true);
    } else {
      setHidden(false);
    }
  });

  const navLinks = [
    { name: 'Features', href: '#features' },
    { name: 'Workflow', href: '#workflow' },
    { name: 'Agents', href: '#agents' },
    { name: 'FAQ', href: '#faq' },
  ];

  return (
    <motion.nav
      variants={{
        visible: { y: 0 },
        hidden: { y: "-100%" },
      }}
      animate={hidden ? "hidden" : "visible"}
      transition={{ duration: 0.35, ease: "easeInOut" }}
      className={`fixed top-0 left-0 right-0 z-50 transition-colors duration-300 ${
        isScrolled
          ? 'bg-[#0B0D13]/85 backdrop-blur-xl border-b border-white/10 shadow-2xl'
          : 'bg-transparent border-transparent'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-20 gap-4">
          {/* Logo */}
          <div className="flex items-center gap-2.5 shrink-0">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center text-white shadow-lg shadow-indigo-500/20">
              <Brain className="w-6 h-6" />
            </div>
            <span className="text-xl font-bold text-white tracking-tight">DeadlineOS</span>
          </div>

          {/* Desktop Navigation Links */}
          <div className="hidden lg:flex items-center space-x-7">
            {navLinks.map((link) => (
              <a
                key={link.name}
                href={link.href}
                className="text-sm font-medium text-gray-300 hover:text-white transition-colors"
              >
                {link.name}
              </a>
            ))}
          </div>

          {/* Persistent Mode Switcher & CTA Actions */}
          <div className="hidden md:flex items-center space-x-4 shrink-0">
            <ProductModeSwitcher
              activeMode={mode}
              onModeChange={onModeChange}
              variant="compact"
              className="mr-1"
            />

            {user ? (
              <div className="flex items-center space-x-3">
                <button
                  onClick={() => signOut()}
                  className="text-sm font-semibold text-gray-300 hover:text-white flex items-center gap-2 transition-colors px-3 py-2 cursor-pointer"
                >
                  <LogOut className="w-4 h-4" /> Logout
                </button>
                <Link
                  to="/dashboard"
                  className="text-sm font-semibold bg-white text-gray-900 hover:bg-gray-100 px-5 py-2.5 rounded-full transition-all shadow-lg shadow-white/10 hover:scale-105"
                >
                  Dashboard
                </Link>
              </div>
            ) : (
              <Link
                to="/login"
                className="text-sm font-semibold bg-white text-gray-900 hover:bg-gray-100 px-5 py-2.5 rounded-full transition-all shadow-lg shadow-white/10 hover:scale-105"
              >
                Login
              </Link>
            )}
          </div>

          {/* Mobile Right Controls: Compact Switcher + Hamburger */}
          <div className="md:hidden flex items-center gap-2">
            <ProductModeSwitcher
              activeMode={mode}
              onModeChange={onModeChange}
              variant="compact"
            />
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 text-gray-300 hover:text-white rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400"
              aria-label={mobileMenuOpen ? 'Close Menu' : 'Open Menu'}
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer Menu */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.25 }}
            className="md:hidden bg-[#0A0C12]/98 backdrop-blur-2xl border-b border-white/10 overflow-hidden"
          >
            <div className="px-5 pt-3 pb-6 space-y-4">
              {/* Mobile Mode Switcher In-Drawer */}
              <div className="pt-1 pb-3 flex justify-center border-b border-white/10">
                <ProductModeSwitcher
                  activeMode={mode}
                  onModeChange={(newMode) => {
                    onModeChange(newMode);
                    setMobileMenuOpen(false);
                  }}
                  variant="hero"
                />
              </div>

              {navLinks.map((link) => (
                <a
                  key={link.name}
                  href={link.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className="block px-3 py-2 text-base font-medium text-gray-300 hover:text-white hover:bg-white/5 rounded-lg transition-colors"
                >
                  {link.name}
                </a>
              ))}

              <div className="pt-4 border-t border-white/10 flex flex-col gap-3">
                <Link
                  to="/login"
                  onClick={() => setMobileMenuOpen(false)}
                  className="w-full text-center text-sm font-medium text-gray-300 hover:text-white py-2"
                >
                  Login
                </Link>
                <Link
                  to="/register"
                  onClick={() => setMobileMenuOpen(false)}
                  className="w-full text-center text-sm font-semibold bg-white text-gray-900 hover:bg-gray-100 py-2.5 rounded-full shadow-lg"
                >
                  Get Started
                </Link>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.nav>
  );
};


