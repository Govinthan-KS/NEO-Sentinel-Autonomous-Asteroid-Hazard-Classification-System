import { useState } from 'react';
import { Navbar } from '@/components/layout/Navbar';
import { Footer } from '@/components/layout/Footer';
import { AnimatedBackground } from '@/components/layout/AnimatedBackground';
import { GlassCard } from '@/components/ui/GlassCard';
import { AnimatedGauge } from '@/components/ui/AnimatedGauge';
import { ShapBars, type ShapFeature } from '@/components/ui/ShapBars';
import { NumberInput } from '@/components/ui/NumberInput';
import { showSuccessToast, showInfoToast, showWarningToast, handleApiError } from '@/utils/toast';
import { useAuth } from '@/context/AuthContext';

interface TelemetryForm {
  absolute_magnitude_h: number;
  estimated_diameter_min_km: number;
  estimated_diameter_max_km: number;
  relative_velocity_kmph: number;
  miss_distance_km: number;
  orbiting_body: string;
}

const PRESETS = [
  { label: 'Benign small NEO', values: { absolute_magnitude_h: 24.1, estimated_diameter_min_km: 0.02, estimated_diameter_max_km: 0.045, relative_velocity_kmph: 18500, miss_distance_km: 42000000, orbiting_body: 'Earth' } },
  { label: 'Borderline case', values: { absolute_magnitude_h: 19.8, estimated_diameter_min_km: 0.28, estimated_diameter_max_km: 0.63, relative_velocity_kmph: 41200, miss_distance_km: 4200000, orbiting_body: 'Earth' } },
  { label: 'Apophis-like', values: { absolute_magnitude_h: 16.9, estimated_diameter_min_km: 0.31, estimated_diameter_max_km: 0.68, relative_velocity_kmph: 30700, miss_distance_km: 380000, orbiting_body: 'Earth' } },
  { label: 'Chicxulub scale', values: { absolute_magnitude_h: 14.5, estimated_diameter_min_km: 10.0, estimated_diameter_max_km: 12.0, relative_velocity_kmph: 72000, miss_distance_km: 50000, orbiting_body: 'Earth' } },
  { label: 'High velocity rock', values: { absolute_magnitude_h: 22.0, estimated_diameter_min_km: 0.1, estimated_diameter_max_km: 0.2, relative_velocity_kmph: 150000, miss_distance_km: 10000000, orbiting_body: 'Earth' } },
  { label: 'Deep space flyby', values: { absolute_magnitude_h: 26.0, estimated_diameter_min_km: 0.01, estimated_diameter_max_km: 0.03, relative_velocity_kmph: 5000, miss_distance_km: 150000000, orbiting_body: 'Earth' } },
];

export function Predict() {
  const { session } = useAuth();
  const [form, setForm] = useState<TelemetryForm>(PRESETS[1].values);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Results
  const [prediction, setPrediction] = useState<{
    isHazardous: boolean;
    confidence: number;
    isAnomaly: boolean | null;
    anomalyScore: number | null;
  } | null>(null);
  const [explanations, setExplanations] = useState<ShapFeature[] | null>(null);

  const handleRunClassification = async () => {
    if (loading) {
      showWarningToast('Action in progress', 'Please wait for the current task to finish.');
      return;
    }
    setLoading(true);
    setError(null);
    setPrediction(null);
    setExplanations(null);

    try {
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:7860';
      
      const payload = {
        absolute_magnitude_h: Number(form.absolute_magnitude_h),
        estimated_diameter_min_km: Number(form.estimated_diameter_min_km),
        estimated_diameter_max_km: Number(form.estimated_diameter_max_km),
        relative_velocity_kmph: Number(form.relative_velocity_kmph),
        miss_distance_km: Number(form.miss_distance_km),
        orbiting_body: form.orbiting_body
      };

      const headers: HeadersInit = {
        'Content-Type': 'application/json'
      };
      if (session?.access_token) {
        headers['Authorization'] = `Bearer ${session.access_token}`;
      }

      const [predictRes, explainRes] = await Promise.all([
        fetch(`${baseUrl}/predict`, {
          method: 'POST',
          headers,
          body: JSON.stringify(payload)
        }),
        fetch(`${baseUrl}/explain`, {
          method: 'POST',
          headers,
          body: JSON.stringify(payload)
        })
      ]);

      if (!predictRes.ok || !explainRes.ok) {
        const failedRes = !predictRes.ok ? predictRes : explainRes;
        const errorData = await failedRes.json().catch(() => null);
        
        if (failedRes.status === 422 && errorData?.detail && Array.isArray(errorData.detail)) {
          const issues = errorData.detail.map((err: any) => {
            const field = err.loc[err.loc.length - 1];
            return `${field.replace(/_/g, ' ')} (${err.msg})`;
          }).join(', ');
          throw new Error(`Invalid Input: ${issues}`);
        }
        
        throw new Error(errorData?.message || errorData?.detail || 'Failed to fetch prediction or explanation from backend.');
      }

      const predictData = await predictRes.json();
      const explainData = await explainRes.json();

      setPrediction({
        isHazardous: predictData.is_hazardous,
        confidence: predictData.confidence,
        isAnomaly: predictData.is_anomaly,
        anomalyScore: predictData.anomaly_score
      });

      if (explainData.explanations) {
        setExplanations(
          explainData.explanations.map((e: any) => ({
            name: e.feature_name,
            value: e.shap_contribution
          }))
        );
      }
      showSuccessToast('Classification Complete', 'Prediction and SHAP explanations generated successfully.');
    } catch (err: any) {
      setError(err.message || 'An unknown error occurred.');
      handleApiError(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen flex flex-col">
      <AnimatedBackground />
      <Navbar />

      <main className="flex-grow relative z-10 max-w-[1320px] mx-auto w-full px-6 md:px-10 py-11 pb-[100px]">
        <div className="mb-8">
          <div className="font-mono text-[11px] tracking-[0.14em] text-muted uppercase mb-2">Prediction + Explanation</div>
          <h1 className="text-[30px] font-bold m-0">Classify an Asteroid</h1>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-[400px_1fr] gap-6 items-start">
          
          {/* Telemetry Input Form */}
          <GlassCard className="p-7 lg:sticky lg:top-[100px]">
            <div className="mb-6 p-4 rounded-xl bg-[rgba(163,230,53,0.08)] border border-[rgba(163,230,53,0.3)] shadow-[0_0_20px_rgba(163,230,53,0.05)]">
              <h4 className="text-[#eef3ff] text-[15px] font-bold mb-2 flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-accent-lime shadow-[0_0_8px_var(--accent-lime)]"></span>
                Input Constraints
              </h4>
              <ul className="text-[#c7d3ee] text-[13px] font-mono flex flex-col gap-1.5">
                <li>• Magnitude (H): 0.01 to 49.99</li>
                <li>• Diameter: 0.001 to 1,000 km</li>
                <li>• Velocity: 0 to 300,000 km/h</li>
                <li>• Miss Dist: &ge; 0 km</li>
              </ul>
            </div>

            <div className="text-xs font-semibold text-muted-secondary tracking-[0.06em] uppercase mb-3">Quick scenarios</div>
            <div className="flex gap-2 flex-wrap mb-6">
              {PRESETS.map((p, i) => (
                <button 
                  key={i} 
                  onClick={() => {
                    setForm(p.values);
                    showInfoToast('Preset Loaded', `Loaded values for ${p.label}.`);
                  }}
                  className="min-h-[44px] px-3.5 py-[7px] flex items-center justify-center rounded-full bg-[rgba(150,190,255,0.08)] border border-[rgba(150,190,255,0.22)] text-[#c7d3ee] text-xs font-mono hover:bg-[rgba(150,190,255,0.15)] transition-colors"
                >
                  {p.label}
                </button>
              ))}
            </div>

            <div className="flex flex-col gap-4">
              <label className="flex flex-col gap-1.5">
                <span className="text-xs text-muted-secondary">Absolute Magnitude (H)</span>
                <NumberInput 
                  step={0.1} 
                  value={form.absolute_magnitude_h} 
                  onChange={v => setForm({...form, absolute_magnitude_h: v as number})}
                />
              </label>
              <label className="flex flex-col gap-1.5">
                <span className="text-xs text-muted-secondary">Estimated Diameter Min (km)</span>
                <NumberInput 
                  step={0.001} 
                  value={form.estimated_diameter_min_km} 
                  onChange={v => setForm({...form, estimated_diameter_min_km: v as number})}
                />
              </label>
              <label className="flex flex-col gap-1.5">
                <span className="text-xs text-muted-secondary">Estimated Diameter Max (km)</span>
                <NumberInput 
                  step={0.001} 
                  value={form.estimated_diameter_max_km} 
                  onChange={v => setForm({...form, estimated_diameter_max_km: v as number})}
                />
              </label>
              <label className="flex flex-col gap-1.5">
                <span className="text-xs text-muted-secondary">Relative Velocity (km/h)</span>
                <NumberInput 
                  step={1} 
                  value={form.relative_velocity_kmph} 
                  onChange={v => setForm({...form, relative_velocity_kmph: v as number})}
                />
              </label>
              <label className="flex flex-col gap-1.5">
                <span className="text-xs text-muted-secondary">Miss Distance (km)</span>
                <NumberInput 
                  step={1000} 
                  value={form.miss_distance_km} 
                  onChange={v => setForm({...form, miss_distance_km: v as number})}
                />
              </label>
              <label className="flex flex-col gap-1.5">
                <span className="text-xs text-muted-secondary">Orbiting Body</span>
                <input 
                  type="text" 
                  value={form.orbiting_body}
                  readOnly
                  disabled
                  className="min-h-[44px] bg-[rgba(5,7,13,0.4)] border border-[rgba(150,190,255,0.1)] rounded-lg px-3 py-2 text-[#5c6f94] text-sm font-mono cursor-not-allowed"
                />
              </label>

              <button 
                onClick={handleRunClassification}
                className={`mt-2 min-h-[44px] p-3.5 rounded-xl flex items-center justify-center gap-2 bg-gradient-to-br from-[rgba(90,200,250,0.25)] to-[rgba(163,230,53,0.18)] border border-[rgba(150,190,255,0.4)] shadow-[0_0_24px_rgba(90,200,250,0.15)] text-text-primary font-bold text-sm hover:scale-[1.02] active:scale-[0.98] transition-all ${loading ? 'opacity-50 cursor-wait pointer-events-auto' : ''}`}
              >
                {loading && (
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                )}
                {loading ? 'Running Classification...' : 'Run Classification'}
              </button>
            </div>
          </GlassCard>

          {/* Results Panel */}
          <div className="flex flex-col gap-5">
            {error && (
              <GlassCard className="p-6 border-hazard-red/50 bg-hazard-red/10 text-hazard-red">
                <h3 className="font-bold mb-1">Classification Failed</h3>
                <p className="text-sm opacity-90">{error}</p>
              </GlassCard>
            )}

            {!prediction && !loading && !error && (
              <div className="flex flex-col items-center justify-center h-[420px] rounded-[20px] border border-dashed border-[rgba(150,190,255,0.16)] text-muted gap-3">
                <svg width="36" height="36" viewBox="0 0 40 40"><circle cx="20" cy="20" r="16" fill="none" stroke="currentColor" strokeWidth="1.4" strokeDasharray="4 3" opacity="0.6"/><ellipse cx="20" cy="20" rx="16" ry="6.5" fill="none" stroke="currentColor" strokeWidth="1.2" opacity="0.4" transform="rotate(-24 20 20)"/></svg>
                <span className="font-mono text-[13px]">Awaiting input — run a classification to see the verdict and SHAP breakdown</span>
              </div>
            )}

            {loading && (
              <div className="flex flex-col gap-5 animate-pulse">
                <div className="h-[180px] bg-[rgba(120,170,255,0.06)] rounded-[20px] border border-[rgba(150,190,255,0.14)]" />
                <div className="h-[60px] bg-[rgba(120,170,255,0.06)] rounded-[16px] border border-[rgba(150,190,255,0.14)]" />
                <div className="h-[250px] bg-[rgba(120,170,255,0.06)] rounded-[20px] border border-[rgba(150,190,255,0.14)]" />
              </div>
            )}

            {prediction && !loading && (
              <>
                {/* Verdict Card */}
                <div 
                  className={`p-6 sm:p-[30px] rounded-[20px] border shadow-[0_0_40px_rgba(0,0,0,0.1)] flex flex-col sm:flex-row items-center justify-between gap-6 sm:gap-[30px] text-center sm:text-left transition-colors`}
                  style={{
                    backgroundColor: prediction.isHazardous ? 'rgba(255,84,112,0.09)' : 'rgba(163,230,53,0.07)',
                    borderColor: prediction.isHazardous ? 'rgba(255,84,112,0.35)' : 'rgba(163,230,53,0.3)',
                    boxShadow: prediction.isHazardous ? '0 0 40px rgba(255,84,112,0.12)' : '0 0 40px rgba(163,230,53,0.1)'
                  }}
                >
                  <div>
                    <div 
                      className="font-mono text-[11px] tracking-[0.14em] uppercase mb-2.5"
                      style={{ color: prediction.isHazardous ? 'var(--hazard-red)' : 'var(--accent-lime)' }}
                    >
                      Classification Result
                    </div>
                    <div className="text-[32px] font-bold text-text-primary mb-2">
                      {prediction.isHazardous ? 'POTENTIALLY HAZARDOUS' : 'SAFE!'}
                    </div>
                    <div className="text-sm text-[#c7d3ee]">
                      Confidence <span className="font-mono font-semibold" style={{ color: prediction.isHazardous ? 'var(--hazard-red)' : 'var(--accent-lime)' }}>{Math.round(prediction.confidence * 100)}%</span>
                    </div>
                  </div>
                  <AnimatedGauge 
                    value={prediction.confidence} 
                    size={120} 
                    strokeWidth={10} 
                    color={prediction.isHazardous ? "var(--hazard-red)" : "var(--accent-lime)"}
                  />
                </div>

                {/* Anomaly Card */}
                <div className="px-[26px] py-[22px] rounded-2xl bg-[rgba(120,170,255,0.05)] border border-[rgba(150,190,255,0.12)] flex items-center justify-between">
                  <div className="flex items-center gap-3.5">
                    <span 
                      className="w-2.5 h-2.5 rounded-full"
                      style={{ 
                        backgroundColor: prediction.isAnomaly ? 'var(--anomaly-amber)' : 'var(--primary)',
                        boxShadow: `0 0 10px ${prediction.isAnomaly ? 'var(--anomaly-amber)' : 'var(--primary)'}`
                      }}
                    ></span>
                    <span className="text-sm font-semibold text-text-primary">
                      {prediction.isAnomaly ? 'Anomaly Detected' : 'Nominal Profile'}
                    </span>
                    <span className="text-xs text-[#c7d3ee] hidden sm:inline">
                      — independent outlier signal, separate from the hazard verdict
                    </span>
                  </div>
                  <div className="font-mono text-[13px] text-[#c7d3ee]">
                    {prediction.anomalyScore != null ? (
                      <span className="flex items-center gap-1.5">
                        index <span className="text-white font-bold">{Math.max(0, Math.min(100, (0.5 - prediction.anomalyScore) * 100)).toFixed(1)}%</span>
                      </span>
                    ) : 'N/A'}
                  </div>
                </div>

                {/* SHAP Card */}
                <GlassCard className="p-7">
                  <div className="flex items-baseline justify-between mb-1.5">
                    <h3 className="text-base font-bold m-0 text-[#eef3ff]">SHAP Feature Contributions</h3>
                    <span className="font-mono text-[11px] text-[#c7d3ee]">← toward hazardous · toward safe →</span>
                  </div>
                  <p className="text-[13px] text-[#c7d3ee] m-0 mb-6">
                    Values represent the log-odds impact of each feature. Positive scores drive the model toward a SAFE verdict, while negative scores drive it toward a HAZARDOUS verdict.
                  </p>
                  
                  {explanations && (
                    <ShapBars features={explanations.sort((a, b) => Math.abs(b.value) - Math.abs(a.value))} />
                  )}
                </GlassCard>
              </>
            )}

          </div>
        </div>
      </main>
      
      <Footer />
    </div>
  );
}
