import { motion } from 'framer-motion';

export function ArchitectureFlowchart() {
  const nodes = [
    { id: 'ingest', title: 'Data Ingestion', subtitle: 'NASA NeoWs API', color: 'blue' },
    { id: 'validate', title: 'Data Validation', subtitle: 'Great Expectations', color: 'green' },
    { id: 'version', title: 'Versioning Storage', subtitle: 'DVC / DagsHub', color: 'amber' },
    { id: 'train', title: 'Multi-Model Training', subtitle: 'XGBoost / LightGBM / RF', color: 'green' },
    { id: 'champion', title: 'Promotion Guardrails', subtitle: 'Metrics Thresholds', color: 'green' },
    { id: 'registry', title: 'MLflow Registry', subtitle: '@champion assignment', color: 'amber' },
    { id: 'serve', title: 'FastAPI Serving Layer', subtitle: 'REST API', color: 'blue' },
    { id: 'xai', title: 'Explainability & Anomaly', subtitle: 'SHAP + Isolation Forest', color: 'blue' },
    { id: 'db', title: 'Metrics Logging', subtitle: 'Supabase Postgres', color: 'amber' },
    { id: 'ui', title: 'Live Dashboard', subtitle: 'React Frontend', color: 'blue' },
  ];

  const getColorStyles = (color: string) => {
    switch (color) {
      case 'blue':
        return 'border-[rgba(90,200,250,0.3)] bg-[rgba(90,200,250,0.05)] text-[rgba(90,200,250,1)] shadow-[0_0_15px_rgba(90,200,250,0.1)]';
      case 'green':
        return 'border-[rgba(163,230,53,0.3)] bg-[rgba(163,230,53,0.05)] text-[rgba(163,230,53,1)] shadow-[0_0_15px_rgba(163,230,53,0.1)]';
      case 'amber':
        return 'border-[rgba(251,146,60,0.3)] bg-[rgba(251,146,60,0.05)] text-[rgba(251,146,60,1)] shadow-[0_0_15px_rgba(251,146,60,0.1)]';
      default:
        return 'border-gray-500 bg-gray-500/10 text-gray-300';
    }
  };

  return (
    <div className="relative flex flex-col items-center w-full max-w-2xl py-10">
      
      {/* Background tracking line */}
      <div className="absolute top-10 bottom-10 left-1/2 w-[2px] bg-[rgba(150,190,255,0.05)] -translate-x-1/2 z-0"></div>

      {/* Animated Pulses */}
      <div className="absolute top-10 bottom-10 left-1/2 w-[2px] -translate-x-1/2 z-0 overflow-hidden">
        <motion.div 
          className="w-full h-[150px] bg-gradient-to-b from-transparent via-primary-bright to-transparent opacity-70"
          animate={{ y: ['-100%', '1000%'] }}
          transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
        />
        <motion.div 
          className="w-full h-[100px] bg-gradient-to-b from-transparent via-accent-lime to-transparent opacity-50"
          animate={{ y: ['-100%', '1500%'] }}
          transition={{ duration: 3.5, repeat: Infinity, ease: "linear", delay: 1.5 }}
        />
      </div>

      {/* Flowchart Nodes */}
      <div className="flex flex-col gap-8 w-full z-10">
        {nodes.map((node, i) => (
          <div key={node.id} className="relative flex justify-center w-full">
            {/* Connection Arrow Drop */}
            {i !== 0 && (
              <div className="absolute -top-8 left-1/2 -translate-x-1/2 flex items-center justify-center">
                <svg width="16" height="24" viewBox="0 0 16 24" fill="none">
                  <path d="M8 0L8 20M8 20L4 16M8 20L12 16" stroke="rgba(150,190,255,0.2)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
            )}
            
            <motion.div 
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: i * 0.1 }}
              className={`w-[320px] rounded-xl border p-4 text-center backdrop-blur-md ${getColorStyles(node.color)}`}
            >
              <div className="font-bold text-[15px] text-[#eef3ff] mb-1">{node.title}</div>
              <div className={`font-mono text-[11px] tracking-wider uppercase opacity-90`}>{node.subtitle}</div>
            </motion.div>
          </div>
        ))}
      </div>

    </div>
  );
}
