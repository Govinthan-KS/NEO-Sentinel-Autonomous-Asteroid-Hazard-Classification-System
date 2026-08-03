import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { useAuth } from '@/context/AuthContext';
import { Menu, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
export function Navbar() {
  const location = useLocation();
  const { user } = useAuth();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // Close mobile menu on route change
  useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [location.pathname]);

  // Lock body scroll when mobile menu is open
  useEffect(() => {
    if (isMobileMenuOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isMobileMenuOpen]);

  return (
    <>
    <nav className="sticky top-0 z-50 flex items-center justify-between px-6 md:px-10 py-4 bg-[rgba(8,12,22,0.55)] backdrop-blur-[18px] border-b border-[rgba(150,190,255,0.12)]">
      <Link to="/" className="flex items-center gap-2.5 z-50">
        <svg width="26" height="26" viewBox="0 0 40 40">
          <circle cx="20" cy="20" r="16" fill="none" stroke="var(--primary)" strokeWidth="1.6" strokeDasharray="4 3" opacity="0.85" />
          <ellipse cx="20" cy="20" rx="16" ry="6.5" fill="none" stroke="var(--accent-lime)" strokeWidth="1.3" opacity="0.7" transform="rotate(-24 20 20)" />
          <circle cx="33.2" cy="12.6" r="2.5" fill="var(--primary-bright)" />
        </svg>
        <span className="font-bold text-base tracking-wide text-text-primary hidden sm:inline-block">
          NEO<span className="text-muted">-</span>SENTINEL
        </span>
      </Link>
      
      {/* Desktop Navigation */}
      <div className="hidden md:flex items-center gap-9">
        <Link 
          to="/" 
          className={cn("text-sm font-semibold transition-colors hover:text-primary-bright", location.pathname === "/" ? "text-text-primary" : "text-muted-secondary")}
        >
          Home
        </Link>
        <Link 
          to="/about" 
          className={cn("text-sm font-semibold transition-colors hover:text-primary-bright", location.pathname === "/about" ? "text-text-primary" : "text-muted-secondary")}
        >
          About
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
        <div className="w-[1px] h-4 bg-slate-800/80 mx-2" />
        {user ? (
          <Link to="/profile" className="flex items-center gap-2 group">
            <div className="relative w-8 h-8 rounded-full overflow-hidden border-2 border-slate-700/50 group-hover:border-primary/50 transition-colors bg-slate-800 flex items-center justify-center">
              {user.user_metadata?.avatar_url ? (
                <img 
                  src={user.user_metadata.avatar_url} 
                  alt="Profile" 
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = 'none';
                    e.currentTarget.parentElement?.querySelector('.fallback-text')?.classList.remove('hidden');
                  }}
                />
              ) : null}
              <span className={`fallback-text ${user.user_metadata?.avatar_url ? 'hidden' : ''} text-xs font-bold text-slate-300`}>
                {user.user_metadata?.full_name ? 
                  user.user_metadata.full_name.split(' ').map((n: string) => n[0]).join('').toUpperCase().substring(0, 2) 
                  : '?'}
              </span>
            </div>
          </Link>
        ) : (
          <Link 
            to="/login"
            className="text-sm font-semibold text-slate-300 hover:text-white transition-colors"
          >
            Login
          </Link>
        )}
      </div>

      {/* Mobile Menu Toggle */}
      <button 
        className="md:hidden flex items-center justify-center p-2 text-[#c7d3ee] hover:text-white transition-colors z-50"
        onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
      >
        {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
      </button>
    </nav>

    {/* Mobile Overlay Menu */}
    <AnimatePresence>
      {isMobileMenuOpen && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.2 }}
          className="fixed inset-0 z-40 bg-[rgba(5,7,13,0.95)] backdrop-blur-md flex flex-col items-center justify-center pt-20 pb-10 px-6 overflow-y-auto"
        >
          <div className="flex flex-col items-center gap-8 w-full max-w-sm">
            <Link 
              to="/" 
              className={cn("text-2xl font-bold transition-colors w-full text-center py-3 rounded-xl", location.pathname === "/" ? "bg-[rgba(150,190,255,0.1)] text-text-primary" : "text-muted-secondary")}
            >
              Home
            </Link>
            <Link 
              to="/about" 
              className={cn("text-2xl font-bold transition-colors w-full text-center py-3 rounded-xl", location.pathname === "/about" ? "bg-[rgba(150,190,255,0.1)] text-text-primary" : "text-muted-secondary")}
            >
              About
            </Link>
            <Link 
              to="/predict" 
              className={cn("text-2xl font-bold transition-colors w-full text-center py-3 rounded-xl", location.pathname === "/predict" ? "bg-[rgba(150,190,255,0.1)] text-text-primary" : "text-muted-secondary")}
            >
              Predict
            </Link>
            <Link 
              to="/dashboard" 
              className={cn("text-2xl font-bold transition-colors w-full text-center py-3 rounded-xl", location.pathname === "/dashboard" ? "bg-[rgba(150,190,255,0.1)] text-text-primary" : "text-muted-secondary")}
            >
              Dashboard
            </Link>
            
            <div className="w-full h-[1px] bg-slate-800/80 my-2" />
            
            {user ? (
              <Link to="/profile" className="flex items-center justify-center gap-3 w-full py-3 bg-[rgba(163,230,53,0.1)] border border-[rgba(163,230,53,0.2)] rounded-xl">
                <div className="relative w-8 h-8 rounded-full overflow-hidden border border-primary/50 bg-slate-800 flex items-center justify-center">
                  {user.user_metadata?.avatar_url ? (
                    <img 
                      src={user.user_metadata.avatar_url} 
                      alt="Profile" 
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        (e.target as HTMLImageElement).style.display = 'none';
                        e.currentTarget.parentElement?.querySelector('.fallback-text')?.classList.remove('hidden');
                      }}
                    />
                  ) : null}
                  <span className={`fallback-text ${user.user_metadata?.avatar_url ? 'hidden' : ''} text-xs font-bold text-slate-300`}>
                    {user.user_metadata?.full_name ? 
                      user.user_metadata.full_name.split(' ').map((n: string) => n[0]).join('').toUpperCase().substring(0, 2) 
                      : '?'}
                  </span>
                </div>
                <span className="font-bold text-accent-lime">My Profile</span>
              </Link>
            ) : (
              <Link 
                to="/login"
                className="w-full py-4 text-center rounded-xl bg-gradient-to-r from-primary to-primary-bright text-[#05070d] font-bold text-lg"
              >
                Login
              </Link>
            )}
            
            <a 
              href="https://github.com/Govinthan-KS/NEO-Sentinel-Autonomous-Asteroid-Hazard-Classification-System" 
              target="_blank" 
              rel="noreferrer"
              className="mt-6 text-sm font-mono text-muted hover:text-primary transition-colors"
            >
              View on GitHub ↗
            </a>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
    </>
  );
}
