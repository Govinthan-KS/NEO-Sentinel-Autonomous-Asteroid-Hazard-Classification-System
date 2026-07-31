import { memo } from 'react';
import { bgImage } from '@/assets/bgImage';

export const AnimatedBackground = memo(function AnimatedBackground() {
  return (
    <div className="fixed inset-0 overflow-hidden z-0 pointer-events-none bg-[#0a0715]">
      
      {/* Background Image with Slow Pan/Zoom */}
      <div 
        className="absolute inset-[-10%] bg-cover bg-center animate-[slowPan_60s_ease-in-out_infinite_alternate]"
        style={{
          backgroundImage: `url(${bgImage})`,
          opacity: 0.6
        }}
      ></div>

      {/* Dark Gradient Overlay to ensure text readability */}
      <div className="absolute inset-0 bg-gradient-to-b from-[#0a0715]/80 via-[#0a0715]/40 to-[#0a0715]/90 mix-blend-multiply"></div>
      <div className="absolute inset-0 bg-gradient-to-t from-[#05070d] via-transparent to-transparent"></div>

      <style>{`
        @keyframes slowPan {
          0% { transform: scale(1) translate(0, 0); }
          100% { transform: scale(1.1) translate(-2%, 2%); }
        }
      `}</style>
    </div>
  );
});
