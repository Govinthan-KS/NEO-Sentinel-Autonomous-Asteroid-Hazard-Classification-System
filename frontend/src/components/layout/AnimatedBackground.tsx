import { memo, useEffect, useRef } from 'react';
import { bgImage } from '@/assets/bgImage';

export const AnimatedBackground = memo(function AnimatedBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    
    // Create layered stars for a 3D parallax effect
    const layers = [
      { speed: 0.1, size: 0.8, count: 100, stars: [] as any[] }, // Distant
      { speed: 0.3, size: 1.2, count: 60, stars: [] as any[] },  // Mid
      { speed: 0.8, size: 2.0, count: 30, stars: [] as any[] }   // Close
    ];

    const initStars = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      
      const screenArea = canvas.width * canvas.height;
      const densityMultiplier = screenArea / (1920 * 1080); // Adjust star count by screen size

      layers.forEach(layer => {
        layer.stars = [];
        const numStars = Math.floor(layer.count * densityMultiplier);
        for (let i = 0; i < numStars; i++) {
          layer.stars.push({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            opacity: Math.random() * 0.6 + 0.2,
            pulse: Math.random() * 0.02,
            pulseDir: Math.random() > 0.5 ? 1 : -1
          });
        }
      });
    };

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      layers.forEach(layer => {
        layer.stars.forEach(star => {
          // Twinkle effect
          star.opacity += star.pulse * star.pulseDir;
          if (star.opacity > 0.9 || star.opacity < 0.1) star.pulseDir *= -1;

          ctx.fillStyle = `rgba(255, 255, 255, ${star.opacity})`;
          ctx.beginPath();
          ctx.arc(star.x, star.y, layer.size, 0, Math.PI * 2);
          ctx.fill();

          // Movement
          star.y -= layer.speed;
          star.x -= layer.speed * 0.2; // Slight diagonal movement

          // Wrap around edges
          if (star.y < 0) {
            star.y = canvas.height;
            star.x = Math.random() * canvas.width;
          }
          if (star.x < 0) {
            star.x = canvas.width;
            star.y = Math.random() * canvas.height;
          }
        });
      });

      animationFrameId = requestAnimationFrame(draw);
    };

    window.addEventListener('resize', initStars);
    initStars();
    draw();

    return () => {
      window.removeEventListener('resize', initStars);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <div className="fixed inset-0 overflow-hidden z-0 pointer-events-none bg-[#02040a]">
      
      {/* Nebula / Space Dust Background */}
      <div 
        className="absolute inset-[-10%] bg-cover bg-center animate-[slowPan_60s_ease-in-out_infinite_alternate]"
        style={{
          backgroundImage: `url(${bgImage})`,
          opacity: 0.6
        }}
      ></div>

      {/* Realistic Starfield Canvas */}
      <canvas 
        ref={canvasRef} 
        className="absolute inset-0 w-full h-full mix-blend-screen opacity-80"
      />

      {/* Dark Gradient Overlay to ensure text readability */}
      <div className="absolute inset-0 bg-gradient-to-b from-[#0a0715]/80 via-[#0a0715]/40 to-[#0a0715]/90 mix-blend-multiply"></div>
      <div className="absolute inset-0 bg-gradient-to-t from-[#05070d] via-transparent to-transparent"></div>

      <style>{`
        @keyframes slowPan {
          0% { transform: scale(1) translate(0, 0); }
          100% { transform: scale(1.15) translate(-3%, 3%); }
        }
      `}</style>
    </div>
  );
});
