import { motion } from 'framer-motion';

export function ArchitectureVisual() {
  return (
    <div className="relative w-full rounded-[24px] border border-[rgba(150,190,255,0.1)] bg-[rgba(8,12,22,0.7)] backdrop-blur-xl p-10 overflow-hidden shadow-[0_0_80px_rgba(0,0,0,0.6)]">
      <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-[rgba(150,190,255,0.4)] to-transparent"></div>
      
      {/* CI/CD Orchestration Layer (Top) */}
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="w-full mb-10 pb-6 border-b border-dashed border-[rgba(150,190,255,0.2)] flex flex-col items-center"
      >
        <span className="text-xs uppercase tracking-[0.2em] text-muted-secondary font-semibold mb-4">Orchestration Layer</span>
        <div className="px-8 py-3 rounded-xl border border-[rgba(150,190,255,0.3)] bg-[rgba(150,190,255,0.05)] shadow-[0_0_20px_rgba(150,190,255,0.1)]">
          <span className="font-semibold text-text-primary">GitHub Actions CI/CD</span>
        </div>
      </motion.div>

      {/* Main Architecture Columns */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative z-10">
        
        {/* Column 1: Data Engineering */}
        <motion.div 
          initial={{ opacity: 0, x: -20 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.1 }}
          className="flex flex-col gap-4"
        >
          <span className="text-xs uppercase tracking-[0.1em] text-primary font-semibold mb-2 text-center">Data Pipeline</span>
          <Node title="NASA NeoWs API" subtitle="Upstream Telemetry" type="source" />
          <ArrowDown />
          <Node title="Great Expectations" subtitle="Data Validation" type="compute" />
          <ArrowDown />
          <Node title="DVC / DagsHub" subtitle="Versioning Storage" type="storage" />
        </motion.div>

        {/* Column 2: MLOps Training */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.2 }}
          className="flex flex-col gap-4"
        >
          <span className="text-xs uppercase tracking-[0.1em] text-accent-lime font-semibold mb-2 text-center">MLOps Pipeline</span>
          <Node title="Model Training" subtitle="Ensemble Pipeline" type="compute" />
          <ArrowDown />
          <Node title="Promotion Guardrails" subtitle="Metrics Thresholds" type="compute" />
          <ArrowDown />
          <Node title="MLflow Registry" subtitle="@champion assignment" type="storage" />
        </motion.div>

        {/* Column 3: Serving & UI */}
        <motion.div 
          initial={{ opacity: 0, x: 20 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.3 }}
          className="flex flex-col gap-4"
        >
          <span className="text-xs uppercase tracking-[0.1em] text-primary-bright font-semibold mb-2 text-center">Serving & UI</span>
          <Node title="FastAPI Serving" subtitle="SHAP + Isolation Forest" type="serving" />
          <ArrowDown />
          <Node title="Supabase Postgres" subtitle="Metrics Logging" type="storage" />
          <ArrowDown />
          <Node title="React Frontend" subtitle="Live Dashboard" type="serving" />
        </motion.div>

      </div>
    </div>
  );
}

// Helper components
function Node({ title, subtitle, type }: { title: string, subtitle: string, type: 'source' | 'compute' | 'storage' | 'serving' }) {
  const colorClass = 
    type === 'source' ? 'text-primary border-primary bg-primary/10 shadow-[0_0_15px_rgba(90,200,250,0.15)]' :
    type === 'compute' ? 'text-accent-lime border-accent-lime bg-accent-lime/10 shadow-[0_0_15px_rgba(163,230,53,0.15)]' :
    type === 'serving' ? 'text-primary-bright border-primary-bright bg-primary-bright/10 shadow-[0_0_15px_rgba(143,224,255,0.15)]' :
    'text-anomaly-amber border-anomaly-amber bg-anomaly-amber/10 shadow-[0_0_15px_rgba(255,180,84,0.15)]';

  return (
    <div className={`flex flex-col items-center justify-center p-4 rounded-xl border text-center h-24 ${colorClass}`}>
      <div className="font-semibold text-sm text-text-primary leading-tight mb-1">{title}</div>
      <div className="font-mono text-[10px] opacity-80 uppercase tracking-wider">{subtitle}</div>
    </div>
  );
}

function ArrowDown() {
  return (
    <div className="flex justify-center text-muted/50 my-[-8px]">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <line x1="12" y1="4" x2="12" y2="20"></line>
        <polyline points="19 13 12 20 5 13"></polyline>
      </svg>
    </div>
  );
}
