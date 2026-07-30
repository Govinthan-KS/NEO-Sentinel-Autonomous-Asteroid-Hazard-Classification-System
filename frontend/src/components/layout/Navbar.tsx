import { Link, useLocation } from 'react-router-dom';
import { cn } from '@/lib/utils';

export function Navbar() {
  const location = useLocation();

  return (
    <nav className="sticky top-0 z-50 flex items-center justify-between px-10 py-4 bg-[rgba(8,12,22,0.55)] backdrop-blur-[18px] border-b border-[rgba(150,190,255,0.12)]">
      <Link to="/" className="flex items-center gap-2.5">
        <svg width="26" height="26" viewBox="0 0 40 40">
          <circle cx="20" cy="20" r="16" fill="none" stroke="var(--primary)" strokeWidth="1.6" strokeDasharray="4 3" opacity="0.85" />
          <ellipse cx="20" cy="20" rx="16" ry="6.5" fill="none" stroke="var(--accent-lime)" strokeWidth="1.3" opacity="0.7" transform="rotate(-24 20 20)" />
          <circle cx="33.2" cy="12.6" r="2.5" fill="var(--primary-bright)" />
        </svg>
        <span className="font-bold text-base tracking-wide text-text-primary">
          NEO<span className="text-muted">-</span>SENTINEL
        </span>
      </Link>
      <div className="flex items-center gap-9">
        <Link 
          to="/" 
          className={cn("text-sm font-semibold transition-colors hover:text-primary-bright", location.pathname === "/" ? "text-text-primary" : "text-muted-secondary")}
        >
          Home
        </Link>
        <Link 
          to="/predict" 
          className={cn("text-sm font-semibold transition-colors hover:text-primary-bright", location.pathname === "/predict" ? "text-text-primary" : "text-muted-secondary")}
        >
          Predict
        </Link>
        <Link 
          to="/dashboard" 
          className={cn("text-sm font-semibold transition-colors hover:text-primary-bright", location.pathname === "/dashboard" ? "text-text-primary" : "text-muted-secondary")}
        >
          Dashboard
        </Link>
        <a 
          href="https://github.com/Govinthan-KS/NEO-Sentinel-Autonomous-Asteroid-Hazard-Classification-System" 
          target="_blank" 
          rel="noreferrer"
          className="text-[13px] font-mono text-muted hover:text-primary transition-colors"
        >
          GitHub ↗
        </a>
      </div>
    </nav>
  );
}
