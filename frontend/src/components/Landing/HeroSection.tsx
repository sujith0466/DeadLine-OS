import React from 'react';
import { motion } from 'framer-motion';
import { ChevronRight, Cpu } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { SystemPreview } from './SystemPreview';

export const HeroSection: React.FC = () => {
  const navigate = useNavigate();

  return (
    <section className="relative pt-32 pb-20 lg:pt-48 lg:pb-32 px-6 max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-[1fr_1.15fr] items-center gap-16 lg:gap-24 z-10">
      
      {/* LEFT: Text Content */}
      <div className="flex-1 text-center lg:text-left">
        
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1, ease: "easeOut" }}
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/10 border border-primary/20 text-sm text-primary font-medium mb-6"
        >
          <Cpu className="w-4 h-4" />
          <span>AI Chief-of-Staff</span>
        </motion.div>
        
        <h1 className="text-5xl sm:text-6xl lg:text-7xl font-black tracking-tight leading-tight mb-6 text-white flex flex-col">
          <motion.span initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.2, ease: "easeOut" }}>Plan.</motion.span>
          <motion.span initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.3, ease: "easeOut" }}>Predict.</motion.span>
          <motion.span initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.4, ease: "easeOut" }} className="gradient-text">Prevent Failure.</motion.span>
        </h1>
        
        <motion.p 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.6, ease: "easeOut" }}
          className="text-lg md:text-xl text-gray-400 mb-14 max-w-xl mx-auto lg:mx-0 leading-relaxed"
        >
          DeadlineOS is an AI Productivity Operating System that continuously plans, forecasts, adapts and intervenes before deadlines are missed.
        </motion.p>
        
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.7, ease: "easeOut" }}
          className="flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-5"
        >
          <motion.button 
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => navigate('/dashboard')} 
            className="group relative inline-flex items-center justify-center px-8 py-4 text-lg font-bold text-white bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl transition-all duration-300 shadow-[0_0_40px_rgba(79,70,229,0.4)] hover:shadow-[0_0_60px_rgba(79,70,229,0.7)] overflow-hidden w-full sm:w-auto border border-white/10"
          >
            {/* Occasional shine sweep */}
            <motion.div 
              animate={{ x: ['-200%', '200%'] }}
              transition={{ repeat: Infinity, duration: 2, ease: "linear", repeatDelay: 4 }}
              className="absolute inset-0 w-1/2 bg-gradient-to-r from-transparent via-white/30 to-transparent skew-x-12 z-10"
            />
            <span className="relative flex items-center z-20">
              Initialize DeadlineOS <ChevronRight className="w-5 h-5 ml-1 group-hover:translate-x-1 transition-transform" />
            </span>
          </motion.button>
          
          <motion.button 
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => {
              const el = document.getElementById('features');
              if (el) {
                const y = el.getBoundingClientRect().top + window.scrollY - 80;
                window.scrollTo({ top: y, behavior: 'smooth' });
              }
            }} 
            className="group relative inline-flex items-center justify-center px-8 py-4 text-lg font-bold text-white bg-white/5 border border-white/20 hover:bg-white/10 hover:border-indigo-500/50 rounded-xl backdrop-blur-md transition-all duration-300 hover:shadow-[0_0_30px_rgba(99,102,241,0.2)] w-full sm:w-auto overflow-hidden"
          >
            <div className="absolute inset-0 w-full h-full bg-gradient-to-r from-transparent via-white/5 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700 ease-in-out" />
            <span className="relative z-10">View AI Architecture</span>
          </motion.button>
        </motion.div>
      </div>

      {/* RIGHT: Visual Preview */}
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.8, delay: 0.9, ease: "easeOut" }}
        className="w-full ml-auto flex justify-end"
      >
        <SystemPreview />
      </motion.div>
      
    </section>
  );
};
