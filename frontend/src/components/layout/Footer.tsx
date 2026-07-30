import { Link } from 'react-router-dom';

export function Footer() {
  return (
    <footer className="border-t border-[rgba(150,190,255,0.1)] px-10 py-7 flex justify-between items-center max-w-[1240px] mx-auto w-full">
      <span className="font-mono text-xs text-muted">© 2026 NEO-Sentinel · Planetary Defense Tooling</span>
      <div className="flex gap-6">
        <Link to="/predict" className="text-[13px] text-muted-secondary hover:text-primary-bright transition-colors">Predict</Link>
        <Link to="/dashboard" className="text-[13px] text-muted-secondary hover:text-primary-bright transition-colors">Dashboard</Link>
      </div>
    </footer>
  );
}
