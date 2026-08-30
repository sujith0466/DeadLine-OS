import React, { useEffect, useRef } from 'react';
import type { ProductMode } from './ProductModeSwitcher';

interface ImmersiveSpatial3DProps {
  mode: ProductMode;
}

export const ImmersiveSpatial3D: React.FC<ImmersiveSpatial3DProps> = ({ mode }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let width = (canvas.width = canvas.parentElement?.clientWidth || window.innerWidth);
    let height = (canvas.height = canvas.parentElement?.clientHeight || 800);

    const handleResize = () => {
      if (!canvas.parentElement) return;
      width = canvas.width = canvas.parentElement.clientWidth;
      height = canvas.height = canvas.parentElement.clientHeight;
    };

    window.addEventListener('resize', handleResize);

    // Particle nodes for spatial 3D orbit
    const particleCount = mode === 'personal' ? 42 : 54;
    const particles = Array.from({ length: particleCount }, (_, i) => {
      const angle = (i / particleCount) * Math.PI * 2;
      const radius = 120 + Math.random() * 220;
      return {
        x: Math.cos(angle) * radius,
        y: Math.sin(angle) * (radius * 0.4),
        z: (Math.random() - 0.5) * 200,
        speed: 0.003 + Math.random() * 0.005,
        angle,
        radius,
        size: 1.5 + Math.random() * 2.5,
      };
    });

    let rotation = 0;

    const render = () => {
      ctx.clearRect(0, 0, width, height);

      const centerX = width / 2;
      const centerY = height * 0.42;
      rotation += 0.004;

      const isPersonal = mode === 'personal';
      const nodeColor = isPersonal ? 'rgba(129, 140, 248, ' : 'rgba(52, 211, 153, ';
      const lineColor = isPersonal ? 'rgba(99, 102, 241, ' : 'rgba(16, 185, 129, ';

      // Render connecting lines
      for (let i = 0; i < particles.length; i++) {
        const p1 = particles[i];
        const a1 = p1.angle + rotation;
        const x1 = centerX + Math.cos(a1) * p1.radius;
        const y1 = centerY + Math.sin(a1) * (p1.radius * 0.42) + Math.sin(rotation + i) * 15;

        for (let j = i + 1; j < particles.length; j++) {
          const p2 = particles[j];
          const a2 = p2.angle + rotation;
          const x2 = centerX + Math.cos(a2) * p2.radius;
          const y2 = centerY + Math.sin(a2) * (p2.radius * 0.42) + Math.sin(rotation + j) * 15;

          const dist = Math.hypot(x2 - x1, y2 - y1);
          if (dist < 130) {
            const alpha = (1 - dist / 130) * 0.22;
            ctx.strokeStyle = `${lineColor}${alpha})`;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(x1, y1);
            ctx.lineTo(x2, y2);
            ctx.stroke();
          }
        }
      }

      // Render particle nodes
      particles.forEach((p, idx) => {
        const currentAngle = p.angle + rotation;
        const px = centerX + Math.cos(currentAngle) * p.radius;
        const py = centerY + Math.sin(currentAngle) * (p.radius * 0.42) + Math.sin(rotation + idx) * 15;
        const depthAlpha = 0.3 + (Math.sin(currentAngle) + 1) * 0.35;

        ctx.fillStyle = `${nodeColor}${depthAlpha})`;
        ctx.beginPath();
        ctx.arc(px, py, p.size, 0, Math.PI * 2);
        ctx.fill();

        // Glow ring
        ctx.strokeStyle = `${nodeColor}${depthAlpha * 0.3})`;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.arc(px, py, p.size * 2.2, 0, Math.PI * 2);
        ctx.stroke();
      });

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);
    };
  }, [mode]);

  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden z-0" aria-hidden="true">
      {/* 3D Dynamic Spatial Canvas */}
      <canvas ref={canvasRef} className="w-full h-full opacity-60 mix-blend-screen" />

      {/* Fallback Static Spatial Gradients */}
      <div 
        className={`absolute top-1/4 left-1/4 w-96 h-96 rounded-full blur-[140px] mix-blend-screen transition-colors duration-700 ${
          mode === 'personal' ? 'bg-indigo-500/20' : 'bg-emerald-500/20'
        }`} 
      />
      <div 
        className={`absolute bottom-1/4 right-1/4 w-96 h-96 rounded-full blur-[140px] mix-blend-screen transition-colors duration-700 ${
          mode === 'personal' ? 'bg-purple-500/20' : 'bg-cyan-500/20'
        }`} 
      />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full bg-[radial-gradient(ellipse_at_center,rgba(255,255,255,0.02)_0%,transparent_100%)]" />
    </div>
  );
};
