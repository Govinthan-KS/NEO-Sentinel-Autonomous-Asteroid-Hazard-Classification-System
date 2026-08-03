
import { Link } from 'react-router-dom';
import { Navbar } from '@/components/layout/Navbar';
import { Footer } from '@/components/layout/Footer';
import { AnimatedBackground } from '@/components/layout/AnimatedBackground';
import { RadarSweep } from '@/components/ui/RadarSweep';

import { GlassCard } from '@/components/ui/GlassCard';
import { SiNasa, SiMlflow, SiDvc, SiFastapi, SiReact } from 'react-icons/si';

export function Home() {

  return (
    <div className="relative min-h-screen flex flex-col">
      <AnimatedBackground />
      <Navbar />

      <main className="flex-grow relative z-10">
        {/* Hero Section */}
        <section className="max-w-[1240px] mx-auto px-6 md:px-10 pt-10 md:pt-[50px] pb-12 md:pb-[80px] grid grid-cols-1 md:grid-cols-[1.15fr_0.85fr] gap-10 md:gap-[60px] items-center">
          <div>
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[rgba(163,230,53,0.08)] border border-[rgba(163,230,53,0.28)] font-mono text-[11px] tracking-[0.1em] text-accent-bright mb-6">
              <span className="w-1.5 h-1.5 rounded-full bg-accent-bright shadow-[0_0_8px_var(--accent-lime)]"></span>
              SYSTEM OPERATIONAL
            </div>
            <h1 className="text-4xl md:text-[52px] leading-[1.15] md:leading-[1.08] font-bold tracking-tight mb-5">
              Real-time hazard classification for near-Earth objects.
            </h1>
            <p className="text-[17px] leading-[1.65] text-text-secondary max-w-[520px] mb-9">
              NEO-Sentinel combines a multi-model ensemble with explainable AI and anomaly detection to flag Potentially Hazardous Asteroids — with the reasoning behind every call, not just a verdict.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 mb-11">
              <Link to="/predict" className="min-h-[44px] justify-center group relative inline-flex items-center gap-2.5 px-7 py-3.5 rounded-full bg-gradient-to-r from-primary to-accent-lime p-[1px] shadow-[0_0_20px_rgba(163,230,53,0.15)] hover:shadow-[0_0_30px_rgba(163,230,53,0.3)] transition-all overflow-hidden">
                <span className="absolute inset-0 bg-background rounded-full transition-colors group-hover:bg-transparent"></span>
                <span className="relative z-10 flex items-center gap-2 text-text-primary font-semibold text-[15px] group-hover:text-[#05070d] transition-colors">
                  Classify an Asteroid
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="group-hover:translate-x-1 transition-transform">
                    <line x1="5" y1="12" x2="19" y2="12"></line>
                    <polyline points="12 5 19 12 12 19"></polyline>
                  </svg>
                </span>
              </Link>
              <Link to="/dashboard" className="min-h-[44px] justify-center inline-flex items-center px-7 py-3.5 rounded-full border border-[rgba(150,190,255,0.2)] text-[#eef3ff] font-semibold text-[15px] bg-[rgba(150,190,255,0.03)] hover:bg-[rgba(150,190,255,0.08)] hover:border-[rgba(150,190,255,0.4)] transition-all shadow-[0_0_15px_rgba(150,190,255,0.0)] hover:shadow-[0_0_20px_rgba(150,190,255,0.15)]">
                View Live Dashboard
              </Link>
            </div>
            
            {/* Tech Stack / Powered By Section */}
            <div className="mt-8 flex flex-col gap-3">
              <div className="text-[11px] text-muted tracking-[0.1em] uppercase font-semibold">
                Powered By
              </div>
              <div className="flex flex-wrap gap-3">
                <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md bg-[rgba(255,255,255,0.03)] border border-[rgba(255,255,255,0.08)] text-text-secondary text-xs font-mono transition-colors hover:text-[#eef3ff] hover:bg-[rgba(255,255,255,0.05)]">
                  <SiNasa className="text-[14px]" /> NASA NeoWs API
                </span>
                <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md bg-[rgba(255,255,255,0.03)] border border-[rgba(255,255,255,0.08)] text-text-secondary text-xs font-mono transition-colors hover:text-[#eef3ff] hover:bg-[rgba(255,255,255,0.05)]">
                  <SiMlflow className="text-[14px]" /> MLflow
                </span>
                <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md bg-[rgba(255,255,255,0.03)] border border-[rgba(255,255,255,0.08)] text-text-secondary text-xs font-mono transition-colors hover:text-[#eef3ff] hover:bg-[rgba(255,255,255,0.05)]">
                  <SiDvc className="text-[14px]" /> DVC
                </span>
                <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md bg-[rgba(255,255,255,0.03)] border border-[rgba(255,255,255,0.08)] text-text-secondary text-xs font-mono transition-colors hover:text-[#eef3ff] hover:bg-[rgba(255,255,255,0.05)]">
                  <SiFastapi className="text-[14px]" /> FastAPI
                </span>
                <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md bg-[rgba(255,255,255,0.03)] border border-[rgba(255,255,255,0.08)] text-text-secondary text-xs font-mono transition-colors hover:text-[#eef3ff] hover:bg-[rgba(255,255,255,0.05)]">
                  <SiReact className="text-[14px]" /> React
                </span>
              </div>
            </div>
          </div>

          <div className="relative w-full">
            <RadarSweep />
          </div>
        </section>

        {/* Project Overview */}
        <section className="max-w-[1240px] mx-auto px-6 md:px-10 py-10 pb-16 md:pb-[90px]">
          <div className="flex items-baseline justify-between mb-9">
            <h2 className="text-[26px] font-bold m-0">What it does</h2>
            <span className="inline-block px-3 py-1 rounded-full bg-[rgba(150,190,255,0.1)] border border-[rgba(150,190,255,0.25)] text-[#eef3ff] font-mono text-xs tracking-[0.08em]">ML · XAI · ANOMALY DETECTION</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-[22px]">
            <GlassCard className="p-7">
              <svg width="30" height="30" viewBox="0 0 30 30" className="mb-4"><rect x="3" y="16" width="5" height="11" fill="var(--primary)" opacity="0.85"/><rect x="12" y="9" width="5" height="18" fill="var(--primary)"/><rect x="21" y="3" width="5" height="24" fill="var(--primary-bright)"/></svg>
              <h3 className="text-[17px] font-bold mb-2.5">Multi-Model Ensemble</h3>
              <p className="text-[14px] leading-[1.6] text-text-secondary m-0">XGBoost, LightGBM and Random Forest candidates are trained continuously; the strongest performer is promoted to champion.</p>
            </GlassCard>
            <GlassCard className="p-7">
              <svg width="30" height="30" viewBox="0 0 30 30" className="mb-4"><rect x="2" y="13" width="10" height="4" fill="var(--hazard-red)"/><rect x="13" y="13" width="7" height="4" fill="var(--accent-lime)"/><rect x="21" y="13" width="6" height="4" fill="var(--accent-lime)" opacity="0.6"/></svg>
              <h3 className="text-[17px] font-bold mb-2.5">Explainable by Design</h3>
              <p className="text-[14px] leading-[1.6] text-text-secondary m-0">Every verdict ships with a SHAP breakdown — signed, per-feature contributions showing exactly what pushed the call.</p>
            </GlassCard>
            <GlassCard className="p-7">
              <svg width="30" height="30" viewBox="0 0 30 30" className="mb-4"><circle cx="7" cy="20" r="2.4" fill="var(--primary)"/><circle cx="13" cy="16" r="2.4" fill="var(--primary)"/><circle cx="19" cy="21" r="2.4" fill="var(--primary)"/><circle cx="25" cy="6" r="3.2" fill="none" stroke="var(--hazard-red)" strokeWidth="1.6"/></svg>
              <h3 className="text-[17px] font-bold mb-2.5">Anomaly Detection</h3>
              <p className="text-[14px] leading-[1.6] text-text-secondary m-0">A parallel outlier model flags objects that don't resemble the training distribution — a second, independent signal.</p>
            </GlassCard>
          </div>
        </section>

        {/* Architecture CTA */}
        <section className="max-w-[1240px] mx-auto px-6 md:px-10 pb-16 md:pb-[100px] flex justify-center">
          <Link to="/about" className="group relative flex items-center justify-center gap-3 px-8 py-4 bg-[rgba(150,190,255,0.05)] border border-[rgba(150,190,255,0.2)] rounded-full hover:bg-[rgba(150,190,255,0.1)] transition-all">
            <span className="font-mono text-sm tracking-widest text-[#eef3ff] uppercase font-semibold">View Full Architecture</span>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-primary-bright group-hover:translate-x-1 transition-transform">
              <line x1="5" y1="12" x2="19" y2="12"></line>
              <polyline points="12 5 19 12 12 19"></polyline>
            </svg>
          </Link>
        </section>

        {/* Research Paper Citation */}
        <section className="max-w-[1240px] mx-auto px-6 md:px-10 pb-16 md:pb-[110px]">
          <h2 className="text-[26px] font-bold m-0 mb-2">Built on peer-reviewed research</h2>
          <p className="text-sm text-muted m-0 mb-8">This system extends a published academic study into a production MLOps pipeline.</p>
          <div className="grid grid-cols-1 md:grid-cols-[1.1fr_0.9fr] gap-6">
            <div className="p-8 rounded-[20px] bg-gradient-to-br from-[rgba(90,200,250,0.09)] to-[rgba(163,230,53,0.05)] border border-[rgba(150,190,255,0.2)] backdrop-blur-md shadow-[0_0_40px_rgba(90,200,250,0.06)]">
              <div className="font-mono text-[11px] tracking-[0.12em] text-primary-bright uppercase mb-3.5">Source paper</div>
              <p className="text-[19px] leading-[1.5] font-semibold m-0 mb-4 text-text-primary">"A Multi-Model Approach Using XAI and Anomaly Detection to Predict Asteroid Hazards"</p>
              <div className="font-mono text-[13px] text-text-secondary leading-[1.8]">
                Mondal et al. · arXiv preprint · March 2025
              </div>
              <p className="text-sm leading-[1.65] text-muted-secondary mt-5">Introduced a multi-model classification approach paired with SHAP-based explainability and unsupervised anomaly detection for identifying potentially hazardous asteroids.</p>
            </div>
            
            <div className="p-8 rounded-[20px] bg-[rgba(120,170,255,0.05)] border border-[rgba(150,190,255,0.12)]">
              <div className="font-mono text-[11px] tracking-[0.12em] text-accent-lime uppercase mb-4">What we extended</div>
              {[
                'Champion/challenger promotion pipeline with automated retraining',
                'Live leaderboard tracking recall, precision, F1 and ROC-AUC per run',
                'Anomaly scoring served alongside every hazard prediction',
                'Interactive operational dashboard for real-time inference telemetry and insights'
              ].map((item, i) => (
                <div key={i} className="flex gap-3 items-start mb-4">
                  <svg width="16" height="16" viewBox="0 0 16 16" className="shrink-0 mt-0.5">
                    <circle cx="8" cy="8" r="7.5" fill="none" stroke="var(--accent-lime)" strokeWidth="1.2"/>
                    <path d="M5 8l2 2 4-4.5" fill="none" stroke="var(--accent-lime)" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                  <p className="text-sm leading-[1.55] text-[#c7d3ee] m-0">{item}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

      </main>

      <Footer />
    </div>
  );
}
