import { motion } from 'framer-motion';

export function RadarSweep() {
  return (
    <div className="relative w-full aspect-square max-w-[600px] flex items-center justify-center">
      {/* Outer Glow */}
      <div className="absolute inset-0 rounded-full bg-[radial-gradient(circle,rgba(90,200,250,0.1),transparent_70%)] blur-[30px]" />
      
      {/* Radar Rings */}
      <div className="absolute inset-4 rounded-full border border-[rgba(90,200,250,0.4)] shadow-[0_0_20px_rgba(90,200,250,0.1)_inset]" />
      <div className="absolute inset-16 rounded-full border border-[rgba(163,230,53,0.3)] shadow-[0_0_20px_rgba(163,230,53,0.1)_inset]" />
      <div className="absolute inset-[110px] rounded-full border border-dashed border-[rgba(150,190,255,0.4)]" />
      <div className="absolute inset-[160px] rounded-full border border-[rgba(90,200,250,0.5)] shadow-[0_0_15px_rgba(90,200,250,0.2)]" />
      
      {/* Center Node */}
      <div className="absolute w-4 h-4 rounded-full bg-primary shadow-[0_0_20px_var(--primary)]" />
      <div className="absolute w-4 h-4 rounded-full bg-primary animate-ping opacity-50" />

      {/* Sweeping Beam */}
      <motion.div
        className="absolute inset-4 rounded-full origin-center overflow-hidden"
        animate={{ rotate: 360 }}
        transition={{ duration: 6, repeat: Infinity, ease: 'linear' }}
      >
        <div 
          className="absolute inset-0"
          style={{
            background: 'conic-gradient(from 0deg, transparent 0%, transparent 70%, rgba(90,200,250,0.15) 90%, rgba(90,200,250,0.9) 100%)'
          }}
        />
        <div className="absolute top-0 left-1/2 w-[3px] h-1/2 bg-primary shadow-[0_0_20px_5px_rgba(90,200,250,0.8)] -ml-[1.5px]" />
      </motion.div>

      {/* Asteroid Blips */}
      <motion.div
        className="absolute w-3 h-3 rounded-full bg-hazard-red shadow-[0_0_15px_var(--hazard-red)]"
        style={{ top: '25%', right: '25%' }}
        animate={{ opacity: [0, 1, 0] }}
        transition={{ duration: 6, repeat: Infinity, delay: 0.5, times: [0, 0.1, 1] }}
      />
      <motion.div
        className="absolute w-2 h-2 rounded-full bg-primary-bright shadow-[0_0_10px_var(--primary-bright)]"
        style={{ bottom: '35%', left: '20%' }}
        animate={{ opacity: [0, 1, 0] }}
        transition={{ duration: 6, repeat: Infinity, delay: 3.5, times: [0, 0.1, 1] }}
      />
      <motion.div
        className="absolute w-2.5 h-2.5 rounded-full bg-accent-lime shadow-[0_0_12px_var(--accent-lime)]"
        style={{ bottom: '25%', right: '35%' }}
        animate={{ opacity: [0, 1, 0] }}
        transition={{ duration: 6, repeat: Infinity, delay: 2, times: [0, 0.1, 1] }}
      />
    </div>
  );
}
