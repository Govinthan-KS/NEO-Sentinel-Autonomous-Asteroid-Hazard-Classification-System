import { Link } from 'react-router-dom';
import { Shield, Activity, Code, ExternalLink } from 'lucide-react';

export function Footer() {
  return (
    <footer className="relative z-10 w-full mt-auto bg-gradient-to-t from-[#05070d] to-transparent pt-20 pb-8 border-t border-[rgba(150,190,255,0.05)]">
      <div className="max-w-[1320px] mx-auto px-10">
        
        {/* Top Section */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-16">
          
          {/* Brand Col */}
          <div className="col-span-1 md:col-span-1">
            <div className="flex items-center gap-3 mb-6">
              <svg width="24" height="24" viewBox="0 0 40 40" fill="none">
                <circle cx="20" cy="20" r="16" stroke="var(--primary)" strokeWidth="1.5" strokeDasharray="4 3" opacity="0.8"/>
                <ellipse cx="20" cy="20" rx="16" ry="6.5" stroke="var(--accent-lime)" strokeWidth="1.5" transform="rotate(-24 20 20)"/>
              </svg>
              <span className="font-bold text-lg tracking-widest text-text-primary">NEO<span className="text-muted-secondary font-light">-</span>SENTINEL</span>
            </div>
            <p className="text-sm text-[#5c6f94] leading-relaxed mb-6">
              Autonomous Planetary Defense System. Leveraging MLflow and a multi-model ensemble (XGBoost, LightGBM, Random Forest) to classify Near-Earth Object telemetry data and identify potential hazards in real-time.
            </p>
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[rgba(163,230,53,0.1)] border border-[rgba(163,230,53,0.2)] w-fit">
              <div className="w-2 h-2 rounded-full bg-accent-lime shadow-[0_0_8px_var(--accent-lime)] animate-pulse"></div>
              <span className="text-accent-lime text-[11px] font-mono font-bold tracking-wider">SYSTEMS NOMINAL</span>
            </div>
          </div>

          {/* Links Col 1 */}
          <div>
            <h4 className="text-white text-[13px] font-bold tracking-[0.15em] uppercase mb-5 flex items-center gap-2">
              <Activity size={14} className="text-primary-bright" />
              Platform
            </h4>
            <ul className="flex flex-col gap-3">
              <li><Link to="/" className="text-[13px] text-[#8fa3c8] hover:text-white transition-colors">Mission Control (Home)</Link></li>
              <li><Link to="/predict" className="text-[13px] text-[#8fa3c8] hover:text-white transition-colors">Run Classification</Link></li>
              <li><Link to="/dashboard" className="text-[13px] text-[#8fa3c8] hover:text-white transition-colors">Global Telemetry Dashboard</Link></li>
              <li><Link to="/dashboard" className="text-[13px] text-[#8fa3c8] hover:text-white transition-colors">Model Leaderboard</Link></li>
            </ul>
          </div>

          {/* Links Col 2 */}
          <div>
            <h4 className="text-white text-[13px] font-bold tracking-[0.15em] uppercase mb-5 flex items-center gap-2">
              <Shield size={14} className="text-primary-bright" />
              Resources
            </h4>
            <ul className="flex flex-col gap-3">
              <li>
                <a href="https://api.nasa.gov/" target="_blank" rel="noreferrer" className="text-[13px] text-[#8fa3c8] hover:text-white transition-colors flex items-center gap-1.5 group">
                  NASA NeoWs API
                  <ExternalLink size={12} className="opacity-40 group-hover:opacity-100 transition-opacity" />
                </a>
              </li>
              <li>
                <a href="https://mlflow.org/" target="_blank" rel="noreferrer" className="text-[13px] text-[#8fa3c8] hover:text-white transition-colors flex items-center gap-1.5 group">
                  MLflow Documentation
                  <ExternalLink size={12} className="opacity-40 group-hover:opacity-100 transition-opacity" />
                </a>
              </li>
              <li>
                <a href="#" className="text-[13px] text-[#8fa3c8] hover:text-white transition-colors flex items-center gap-1.5 group">
                  Architecture Overview
                </a>
              </li>
            </ul>
          </div>

          {/* Links Col 3 */}
          <div>
            <h4 className="text-white text-[13px] font-bold tracking-[0.15em] uppercase mb-5 flex items-center gap-2">
              <Code size={14} className="text-primary-bright" />
              Open Source
            </h4>
            <ul className="flex flex-col gap-3">
              <li>
                <a href="https://github.com/Govinthan-KS/Asteroid-Hazard-Classifier" target="_blank" rel="noreferrer" className="text-[13px] text-[#8fa3c8] hover:text-white transition-colors">
                  Repository
                </a>
              </li>
              <li><a href="#" className="text-[13px] text-[#8fa3c8] hover:text-white transition-colors">Issue Tracker</a></li>
              <li><a href="#" className="text-[13px] text-[#8fa3c8] hover:text-white transition-colors">License (Apache 2.0)</a></li>
            </ul>
          </div>

        </div>

        {/* Bottom Section */}
        <div className="pt-8 border-t border-[rgba(150,190,255,0.08)] flex flex-col md:flex-row justify-between items-center gap-4">
          <span className="font-mono text-[11px] text-[#5c6f94] tracking-wider">
            © {new Date().getFullYear()} NEO-Sentinel Planetary Defense. All Systems Go.
          </span>
          <div className="flex items-center gap-6">
            <span className="font-mono text-[11px] text-[#5c6f94]">v2.4.1 (STABLE)</span>
            <div className="flex gap-4">
              <Link to="/privacy" className="text-[11px] text-[#a5badf] hover:text-[#eef3ff] transition-colors">Privacy Policy</Link>
              <Link to="/terms" className="text-[11px] text-[#a5badf] hover:text-[#eef3ff] transition-colors">Terms of Service</Link>
            </div>
          </div>
        </div>

      </div>
    </footer>
  );
}
