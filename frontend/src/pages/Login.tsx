import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { Globe } from 'lucide-react';
import { GlassCard } from '@/components/ui/GlassCard';
import { AnimatedBackground } from '@/components/layout/AnimatedBackground';
import { Navbar } from '@/components/layout/Navbar';
import { Footer } from '@/components/layout/Footer';

export const Login: React.FC = () => {
  const { user, loading, signInWithGoogle } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!loading && user) {
      navigate('/dashboard', { replace: true });
    }
  }, [user, loading, navigate]);

  return (
    <div className="relative min-h-screen flex flex-col">
      <AnimatedBackground />
      <Navbar />

      <main className="flex-grow relative z-10 flex items-center justify-center py-11 px-10">
        <div className="w-full max-w-md relative">
          <GlassCard className="p-8 flex flex-col items-center text-center">
            
            <div className="w-16 h-16 rounded-2xl bg-[rgba(163,230,53,0.08)] border border-[rgba(163,230,53,0.3)] flex items-center justify-center mb-6 shadow-[0_0_30px_rgba(163,230,53,0.1)]">
              <svg width="32" height="32" viewBox="0 0 40 40">
                <circle cx="20" cy="20" r="16" fill="none" stroke="var(--primary)" strokeWidth="1.6" strokeDasharray="4 3" opacity="0.85" />
                <ellipse cx="20" cy="20" rx="16" ry="6.5" fill="none" stroke="var(--accent-lime)" strokeWidth="1.3" opacity="0.7" transform="rotate(-24 20 20)" />
                <circle cx="33.2" cy="12.6" r="2.5" fill="var(--primary-bright)" />
              </svg>
            </div>

          <h1 className="text-3xl font-bold text-slate-100 mb-2">NEO-Sentinel</h1>
          <p className="text-slate-400 mb-8 max-w-[280px]">
            Sign in to access telemetry dashboards and ML prediction models.
          </p>

          <button
            onClick={signInWithGoogle}
            disabled={loading}
            className="w-full py-3 px-4 bg-white hover:bg-slate-50 text-slate-900 rounded-xl font-medium transition-all duration-200 flex items-center justify-center gap-3 shadow-lg hover:shadow-xl hover:-translate-y-0.5 disabled:opacity-70 disabled:hover:translate-y-0 disabled:cursor-not-allowed"
          >
            <Globe className="w-5 h-5 text-[#4285F4]" />
            Continue with Google
          </button>
          
          <p className="mt-6 text-sm text-slate-500">
            By signing in, you agree to our <a href="/terms" className="text-cyan-400/80 hover:text-cyan-300 transition-colors">Terms of Service</a>.
          </p>

        </GlassCard>
        </div>
      </main>
      
      <Footer />
    </div>
  );
};
