import { useEffect, useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Navbar } from '@/components/layout/Navbar';
import { Footer } from '@/components/layout/Footer';
import { AnimatedBackground } from '@/components/layout/AnimatedBackground';
import { GlassCard } from '@/components/ui/GlassCard';
import { PaginationControls } from '@/components/ui/PaginationControls';
import { ExportMenu } from '@/components/ui/ExportMenu';
import { Select } from '@/components/ui/Select';
import { Switch } from '@/components/ui/Switch';
import { NumberInput } from '@/components/ui/NumberInput';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';

export function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [champion, setChampion] = useState<any>(null);
  const [summary, setSummary] = useState<any>(null);
  const [leaderboard, setLeaderboard] = useState<any[]>([]);
  const [recent, setRecent] = useState<any[]>([]);
  const [trends, setTrends] = useState<any[]>([]);

  // Leaderboard Filters & Pagination
  const [lbSearch, setLbSearch] = useState('');
  const [lbMinRoc, setLbMinRoc] = useState<number | ''>('');
  const [lbPromotedOnly, setLbPromotedOnly] = useState(false);
  const [lbPage, setLbPage] = useState(1);
  const [lbRows, setLbRows] = useState(10);

  // Recent Predictions Filters & Pagination
  const [recVerdict, setRecVerdict] = useState('ALL');
  const [recAnomaly, setRecAnomaly] = useState('ALL');
  const [recMinConf, setRecMinConf] = useState<number | ''>('');
  const [recPage, setRecPage] = useState(1);
  const [recRows, setRecRows] = useState(10);

  useEffect(() => {
    let mounted = true;
    const fetchData = async () => {
      try {
        const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:7860';
        const [champRes, leadRes, sumRes, recRes, trendRes] = await Promise.all([
          fetch(`${baseUrl}/dashboard/champion`),
          fetch(`${baseUrl}/dashboard/leaderboard`),
          fetch(`${baseUrl}/dashboard/summary`),
          fetch(`${baseUrl}/dashboard/recent?limit=50`), // Kept at 50 as requested
          fetch(`${baseUrl}/dashboard/trends`)
        ]);

        if (!champRes.ok) throw new Error('Failed to load champion data');

        const [champData, leadData, sumData, recData, trendData] = await Promise.all([
          champRes.json(),
          leadRes.json(),
          sumRes.json(),
          recRes.json(),
          trendRes.json()
        ]);

        if (mounted) {
          setChampion(champData);
          setLeaderboard(leadData);
          setSummary(sumData);
          setRecent(recData);
          setTrends(trendData);
          setLoading(false);
        }
      } catch (err: any) {
        if (mounted) {
          setError(err.message || 'Error loading dashboard data');
          setLoading(false);
        }
      }
    };

    fetchData();
    return () => { mounted = false; };
  }, []);

  // Leaderboard Logic
  const filteredLeaderboard = useMemo(() => {
    const q = lbSearch.toLowerCase();
    
    // Inject champion into the leaderboard array if it's missing (backend might limit rows)
    let fullList = [...leaderboard];
    if (champion && !fullList.find(r => r.run_id === champion.run_id)) {
      fullList.push({
        ...champion,
        display_name: champion.model_name || champion.run_name || 'Champion',
        run_date: champion.trained_date || new Date().toISOString(),
        is_champion: true
      });
    }

    // Explicitly mark the champion in case the array data lacks the flag
    const lbWithChamp = fullList.map(item => ({
      ...item,
      is_champion: item.is_champion || (champion && item.run_id === champion.run_id)
    }));

    const filtered = lbWithChamp.filter(item => {
      const matchText = item.display_name?.toLowerCase().includes(q) || item.run_id?.toLowerCase().includes(q);
      const matchRoc = lbMinRoc === '' || (item.roc_auc != null && item.roc_auc >= Number(lbMinRoc));
      const matchPromoted = !lbPromotedOnly || item.is_champion;
      return matchText && matchRoc && matchPromoted;
    });
    // Sort champion first
    return filtered.sort((a, b) => (b.is_champion ? 1 : 0) - (a.is_champion ? 1 : 0));
  }, [leaderboard, champion, lbSearch, lbMinRoc, lbPromotedOnly]);

  const paginatedLeaderboard = useMemo(() => {
    const start = (lbPage - 1) * lbRows;
    return filteredLeaderboard.slice(start, start + lbRows);
  }, [filteredLeaderboard, lbPage, lbRows]);

  const lbColumns = [
    { header: 'Model Name', key: 'display_name' },
    { header: 'Run ID', key: 'run_id' },
    { header: 'Run Date', key: 'run_date' },
    { header: 'Recall', key: 'recall' },
    { header: 'Precision', key: 'precision' },
    { header: 'F1', key: 'f1' },
    { header: 'ROC-AUC', key: 'roc_auc' },
    { header: 'Champion', key: 'is_champion' }
  ];

  // Recent Predictions Logic
  const filteredRecent = useMemo(() => {
    return recent.filter(item => {
      let matchVerdict = true;
      if (recVerdict === 'HAZARD') matchVerdict = item.is_hazardous === true;
      if (recVerdict === 'SAFE') matchVerdict = item.is_hazardous === false;

      let matchAnomaly = true;
      if (recAnomaly === 'YES') matchAnomaly = item.is_anomaly === true;
      if (recAnomaly === 'NO') matchAnomaly = item.is_anomaly === false;

      const matchConf = recMinConf === '' || (item.confidence != null && (item.confidence * 100) >= Number(recMinConf));
      
      return matchVerdict && matchAnomaly && matchConf;
    });
  }, [recent, recVerdict, recAnomaly, recMinConf]);

  const paginatedRecent = useMemo(() => {
    const start = (recPage - 1) * recRows;
    return filteredRecent.slice(start, start + recRows);
  }, [filteredRecent, recPage, recRows]);

  const recColumns = [
    { header: 'Timestamp', key: 'timestamp' },
    { header: 'Hazardous', key: 'is_hazardous' },
    { header: 'Confidence', key: 'confidence' },
    { header: 'Anomaly', key: 'is_anomaly' },
    { header: 'Velocity (km/h)', key: 'relative_velocity_kmph' },
    { header: 'Miss Distance (km)', key: 'miss_distance_km' }
  ];

  // Reset pagination when search changes
  useEffect(() => setLbPage(1), [lbSearch, lbMinRoc, lbPromotedOnly]);
  useEffect(() => setRecPage(1), [recVerdict, recAnomaly, recMinConf]);

  return (
    <div className="relative min-h-screen flex flex-col">
      <AnimatedBackground />
      <Navbar />

      <main className="flex-grow relative z-10 max-w-[1320px] mx-auto w-full px-10 py-11 pb-[100px] flex flex-col gap-6">
        <div>
          <div className="font-mono text-[11px] tracking-[0.14em] text-[#c7d3ee] uppercase mb-1.5">Operations</div>
          <h1 className="text-[28px] font-bold m-0 text-[#eef3ff]">Live Dashboard</h1>
        </div>

        {error && (
          <GlassCard className="p-6 border-hazard-red/50 bg-hazard-red/10 text-hazard-red">
            <h3 className="font-bold mb-1">Dashboard Error</h3>
            <p className="text-sm opacity-90">{error}</p>
          </GlassCard>
        )}

        {loading && !error && (
          <div className="flex flex-col items-center justify-center h-[50vh] gap-6">
            <div className="relative flex items-center justify-center w-24 h-24">
              <motion.div 
                className="absolute inset-0 rounded-full border border-[rgba(90,200,250,0.2)] shadow-[0_0_30px_rgba(90,200,250,0.1)_inset]"
                animate={{ scale: [0.8, 1.2, 0.8], opacity: [0.5, 1, 0.5] }}
                transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
              />
              <motion.div 
                className="absolute inset-2 rounded-full border-2 border-t-primary border-r-transparent border-b-accent-lime border-l-transparent opacity-80"
                animate={{ rotate: 360 }}
                transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
              />
              <motion.div 
                className="absolute inset-4 rounded-full border-2 border-t-transparent border-r-accent-lime border-b-transparent border-l-primary opacity-60"
                animate={{ rotate: -360 }}
                transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
              />
              <div className="w-2 h-2 rounded-full bg-primary shadow-[0_0_10px_var(--primary)] animate-ping" />
            </div>
            <div className="font-mono text-sm tracking-widest uppercase text-[#c7d3ee] animate-pulse">Syncing Telemetry...</div>
          </div>
        )}

        {!loading && !error && (
          <>
            {/* Telemetry Stat Cards */}
            <motion.div 
              className="grid grid-cols-4 gap-4"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
            >
              <GlassCard className="p-5.5 px-6 py-5 border-[rgba(150,190,255,0.16)]">
                <div className="text-[11px] text-[#c7d3ee] tracking-[0.06em] uppercase mb-2">Predictions Served</div>
                <div className="font-mono text-[26px] font-semibold text-text-primary">
                  {summary?.total_predictions?.toLocaleString() ?? 0}
                </div>
              </GlassCard>
              <GlassCard className="p-5.5 px-6 py-5 border-[rgba(150,190,255,0.16)]">
                <div className="text-[11px] text-[#c7d3ee] tracking-[0.06em] uppercase mb-2">Hazard Rate</div>
                <div className="font-mono text-[26px] font-semibold text-hazard-red">
                  {summary?.hazard_rate != null ? (summary.hazard_rate * 100).toFixed(1) : 0}%
                </div>
                <div className="text-[12px] text-[#8fa3c8] mt-1.5">Across recent data</div>
              </GlassCard>
              <GlassCard className="p-5.5 px-6 py-5 border-[rgba(150,190,255,0.16)]">
                <div className="text-[11px] text-[#c7d3ee] tracking-[0.06em] uppercase mb-2">Anomaly Rate</div>
                <div className="font-mono text-[26px] font-semibold text-anomaly-amber">
                  {summary?.anomaly_rate != null ? (summary.anomaly_rate * 100).toFixed(1) : 0}%
                </div>
                <div className="text-[12px] text-[#8fa3c8] mt-1.5">Across recent data</div>
              </GlassCard>
              <GlassCard className="p-5.5 px-6 py-5 border-[rgba(150,190,255,0.16)]">
                <div className="text-[11px] text-[#c7d3ee] tracking-[0.06em] uppercase mb-2">Active Pipeline</div>
                <div className="font-mono text-[14px] font-semibold text-primary-bright truncate mt-1">
                  {summary?.current_model_run_id ? summary.current_model_run_id.substring(0, 8) : 'N/A'}
                </div>
                <div className="text-[12px] text-[#8fa3c8] mt-1.5">Current run hash</div>
              </GlassCard>
            </motion.div>

            {/* Champion Status Card */}
            {champion && (
              <motion.div 
                className="p-7 rounded-[20px] bg-gradient-to-br from-[rgba(90,200,250,0.1)] to-[rgba(163,230,53,0.05)] border border-[rgba(150,190,255,0.2)] shadow-[0_0_40px_rgba(90,200,250,0.06)]"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: 0.1 }}
              >
                <div className="flex items-center justify-between flex-wrap gap-5">
                  <div className="flex items-center gap-4">
                    <div className="w-[46px] h-[46px] rounded-xl bg-[rgba(163,230,53,0.14)] border border-[rgba(163,230,53,0.4)] flex items-center justify-center shrink-0">
                      <svg width="22" height="22" viewBox="0 0 22 22"><path d="M11 1l3 6 6.5 1-4.7 4.6 1.1 6.5L11 16l-5.9 3.1 1.1-6.5L1.5 8l6.5-1z" fill="var(--accent-bright)"/></svg>
                    </div>
                    <div>
                      <div className="text-[11px] tracking-[0.1em] text-accent-lime uppercase mb-1">Champion Model</div>
                      <div className="font-mono text-lg font-semibold text-text-primary">
                        {champion.run_name || champion.model_name || 'Unknown'}
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-7">
                    <div>
                      <div className="text-[11px] text-[#c7d3ee] mb-1">Recall</div>
                      <div className="font-mono text-[17px] font-semibold text-primary-bright">
                        {champion.recall != null ? champion.recall.toFixed(4) : 'N/A'}
                      </div>
                    </div>
                    <div>
                      <div className="text-[11px] text-[#c7d3ee] mb-1">F1</div>
                      <div className="font-mono text-[17px] font-semibold text-primary-bright">
                        {champion.f1 != null ? champion.f1.toFixed(4) : 'N/A'}
                      </div>
                    </div>
                    <div>
                      <div className="text-[11px] text-[#c7d3ee] mb-1">ROC-AUC</div>
                      <div className="font-mono text-[17px] font-semibold text-primary-bright">
                        {champion.roc_auc != null ? champion.roc_auc.toFixed(4) : 'N/A'}
                      </div>
                    </div>
                  </div>
                </div>
                <div className="flex gap-3.5 mt-5 flex-wrap">
                  <div className="flex items-center gap-2 px-3.5 py-2 rounded-full bg-[rgba(150,190,255,0.08)] border border-[rgba(150,190,255,0.18)] text-xs text-[#c7d3ee]">
                    Trained <span className="font-mono text-[#eef3ff]">{champion.days_since_trained ?? 0}d ago</span>
                    {champion.trained_date ? ` · ${new Date(champion.trained_date).toLocaleDateString()}` : ''}
                  </div>
                  <div className="flex items-center gap-2 px-3.5 py-2 rounded-full bg-[rgba(255,180,84,0.08)] border border-[rgba(255,180,84,0.3)] text-xs text-[#eef3ff]">
                    <span className="w-1.5 h-1.5 rounded-full bg-anomaly-amber"></span>
                    Last challenged <span className="font-mono">{champion.days_since_last_challenge ?? 0}d ago</span> · pipeline actively trying to beat it
                  </div>
                </div>
              </motion.div>
            )}

            {/* Trends Chart */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.2 }}
            >
              <GlassCard className="p-7">
                <h3 className="text-base font-bold m-0 mb-6 text-[#eef3ff]">Predictions Over Time</h3>
                {trends.length === 0 ? (
                  <div className="h-[300px] flex items-center justify-center text-[#c7d3ee] font-mono text-sm border border-dashed border-[rgba(150,190,255,0.2)] rounded-xl">
                    No trend data available.
                  </div>
                ) : (
                  <div className="h-[300px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={trends} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(150,190,255,0.1)" vertical={false} />
                        <XAxis 
                          dataKey="date" 
                          stroke="#5c6f94" 
                          fontSize={11} 
                          tickMargin={10} 
                          tickFormatter={(val) => {
                            const d = new Date(val);
                            return isNaN(d.getTime()) ? val : `${d.getMonth()+1}/${d.getDate()}`;
                          }}
                        />
                        <YAxis stroke="#5c6f94" fontSize={11} tickMargin={10} width={40} />
                        <Tooltip 
                          contentStyle={{ backgroundColor: 'rgba(8,12,22,0.9)', border: '1px solid rgba(150,190,255,0.2)', borderRadius: '8px' }}
                          itemStyle={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '12px' }}
                          labelStyle={{ color: '#8fa3c8', fontSize: '12px', marginBottom: '4px' }}
                        />
                        <Legend iconType="circle" wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
                        <Line type="monotone" dataKey="total" name="Total Predictions" stroke="var(--primary)" strokeWidth={2} dot={false} />
                        <Line type="monotone" dataKey="hazardous" name="Hazardous" stroke="var(--hazard-red)" strokeWidth={2} dot={false} />
                        <Line type="monotone" dataKey="anomalies" name="Anomalies" stroke="var(--anomaly-amber)" strokeWidth={2} dot={false} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </GlassCard>
            </motion.div>

            {/* Leaderboard Table */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.3 }}
            >
              <GlassCard className="p-7 overflow-hidden flex flex-col">
                <div className="flex items-center justify-between mb-5">
                  <h3 className="text-base font-bold m-0 text-[#eef3ff]">Model Leaderboard</h3>
                  <ExportMenu 
                    data={filteredLeaderboard} 
                    columns={lbColumns} 
                    filename="leaderboard_export" 
                    title="Model Leaderboard Export" 
                  />
                </div>

                {/* Leaderboard Filters */}
                <div className="flex flex-wrap gap-4 mb-5 p-4 rounded-xl bg-[rgba(150,190,255,0.03)] border border-[rgba(150,190,255,0.1)] items-end">
                  <div className="flex flex-col gap-1.5">
                    <span className="text-[10px] uppercase tracking-wider text-[#5c6f94] font-semibold">Search Name</span>
                    <input 
                      type="text" 
                      placeholder="e.g. baseline" 
                      value={lbSearch}
                      onChange={e => setLbSearch(e.target.value)}
                      className="bg-[rgba(12,16,28,0.6)] backdrop-blur-md border border-[rgba(150,190,255,0.2)] rounded-lg px-3.5 py-2 text-[13px] text-[#eef3ff] font-mono focus:border-primary-bright outline-none w-56 shadow-inner transition-colors hover:border-[rgba(90,200,250,0.5)] placeholder:text-[#5c6f94]"
                    />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <span className="text-[10px] uppercase tracking-wider text-[#5c6f94] font-semibold">Min ROC-AUC</span>
                    <NumberInput 
                      step={0.01}
                      placeholder="0.00" 
                      value={lbMinRoc}
                      onChange={setLbMinRoc}
                      className="w-36"
                    />
                  </div>
                  <div className="flex items-center h-[36px] px-2 gap-2 cursor-pointer mb-0.5">
                    <Switch 
                      checked={lbPromotedOnly}
                      onChange={setLbPromotedOnly}
                      label="Champion Only"
                    />
                  </div>
                </div>

                {filteredLeaderboard.length === 0 ? (
                  <div className="p-6 text-center text-[#c7d3ee] font-mono text-sm border border-dashed border-[rgba(150,190,255,0.2)] rounded-xl">
                    No models found matching criteria.
                  </div>
                ) : (
                  <div className="overflow-x-auto w-full">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="border-b border-[rgba(150,190,255,0.15)]">
                          <th className="p-2.5 text-[11px] text-[#c7d3ee] tracking-[0.06em] uppercase">Model</th>
                          <th className="p-2.5 text-[11px] text-[#c7d3ee] tracking-[0.06em] uppercase">Run Date</th>
                          <th className="p-2.5 text-[11px] text-[#c7d3ee] tracking-[0.06em] uppercase text-right">Recall</th>
                          <th className="p-2.5 text-[11px] text-[#c7d3ee] tracking-[0.06em] uppercase text-right">Precision</th>
                          <th className="p-2.5 text-[11px] text-[#c7d3ee] tracking-[0.06em] uppercase text-right">F1</th>
                          <th className="p-2.5 text-[11px] text-[#c7d3ee] tracking-[0.06em] uppercase text-right">ROC-AUC</th>
                          <th className="p-2.5 text-[11px] text-[#c7d3ee] tracking-[0.06em] uppercase text-center">Promoted</th>
                        </tr>
                      </thead>
                      <tbody>
                        {paginatedLeaderboard.map((row) => (
                          <tr key={row.run_id} className="border-b border-[rgba(150,190,255,0.06)] hover:bg-[rgba(150,190,255,0.03)] transition-colors">
                            <td className="p-2.5 text-[13px] font-semibold text-[#eef3ff]">
                              {row.display_name}
                              <div className="font-mono text-[11px] text-[#c7d3ee] font-normal mt-0.5">{row.run_id.substring(0, 8)}</div>
                            </td>
                            <td className="p-2.5 font-mono text-xs text-[#c7d3ee]">
                              {new Date(row.run_date).toLocaleDateString()}
                            </td>
                            <td className="p-2.5 font-mono text-[13px] text-right text-[#eef3ff]">{row.recall?.toFixed(4) ?? '-'}</td>
                            <td className="p-2.5 font-mono text-[13px] text-right text-[#eef3ff]">{row.precision?.toFixed(4) ?? '-'}</td>
                            <td className="p-2.5 font-mono text-[13px] text-right text-[#eef3ff]">{row.f1?.toFixed(4) ?? '-'}</td>
                            <td className="p-2.5 font-mono text-[13px] text-right text-[#eef3ff]">{row.roc_auc?.toFixed(4) ?? '-'}</td>
                            <td className="p-2.5 text-center">
                              {row.is_champion ? (
                                <span className="inline-block px-2.5 py-[3px] rounded-full bg-[rgba(163,230,53,0.14)] border border-[rgba(163,230,53,0.4)] text-accent-bright text-[11px] font-mono">CHAMPION</span>
                              ) : (
                                <span className="text-[11px] text-[#5c6f94]">—</span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
                {filteredLeaderboard.length > 0 && (
                  <PaginationControls 
                    totalRows={filteredLeaderboard.length} 
                    rowsPerPage={lbRows} 
                    currentPage={lbPage} 
                    onPageChange={setLbPage} 
                    onRowsPerPageChange={(v) => { setLbRows(v); setLbPage(1); }} 
                  />
                )}
              </GlassCard>
            </motion.div>

            {/* Recent Predictions Table */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.4 }}
            >
              <GlassCard className="p-7 overflow-hidden flex flex-col">
                <div className="flex items-center justify-between mb-5">
                  <h3 className="text-base font-bold m-0 text-[#eef3ff]">Recent Predictions</h3>
                  <ExportMenu 
                    data={filteredRecent} 
                    columns={recColumns} 
                    filename="predictions_export" 
                    title="Telemetry Predictions Export" 
                  />
                </div>

                {/* Recent Predictions Filters */}
                <div className="flex flex-wrap gap-4 mb-5 p-4 rounded-xl bg-[rgba(150,190,255,0.03)] border border-[rgba(150,190,255,0.1)] items-end">
                  <div className="flex flex-col gap-1.5 z-20">
                    <span className="text-[10px] uppercase tracking-wider text-[#5c6f94] font-semibold">Verdict</span>
                    <Select 
                      value={recVerdict} 
                      onChange={setRecVerdict}
                      options={[
                        { label: 'All', value: 'ALL' },
                        { label: 'Hazard', value: 'HAZARD' },
                        { label: 'Safe', value: 'SAFE' }
                      ]}
                      className="w-36"
                    />
                  </div>
                  <div className="flex flex-col gap-1.5 z-10">
                    <span className="text-[10px] uppercase tracking-wider text-[#5c6f94] font-semibold">Anomaly</span>
                    <Select 
                      value={recAnomaly} 
                      onChange={setRecAnomaly}
                      options={[
                        { label: 'All', value: 'ALL' },
                        { label: 'Yes', value: 'YES' },
                        { label: 'No', value: 'NO' }
                      ]}
                      className="w-36"
                    />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <span className="text-[10px] uppercase tracking-wider text-[#5c6f94] font-semibold">Min Confidence (%)</span>
                    <NumberInput 
                      step={1}
                      placeholder="0" 
                      value={recMinConf}
                      onChange={setRecMinConf}
                      className="w-44"
                    />
                  </div>
                </div>

                {filteredRecent.length === 0 ? (
                  <div className="p-6 text-center text-[#c7d3ee] font-mono text-sm border border-dashed border-[rgba(150,190,255,0.2)] rounded-xl">
                    No predictions found matching filters.
                  </div>
                ) : (
                  <div className="overflow-x-auto w-full">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="border-b border-[rgba(150,190,255,0.15)]">
                          <th className="p-2.5 text-[11px] text-[#c7d3ee] tracking-[0.06em] uppercase">Timestamp</th>
                          <th className="p-2.5 text-[11px] text-[#c7d3ee] tracking-[0.06em] uppercase">Diam Avg</th>
                          <th className="p-2.5 text-[11px] text-[#c7d3ee] tracking-[0.06em] uppercase text-right">Vel (km/h)</th>
                          <th className="p-2.5 text-[11px] text-[#c7d3ee] tracking-[0.06em] uppercase text-right">Miss (km)</th>
                          <th className="p-2.5 text-[11px] text-[#c7d3ee] tracking-[0.06em] uppercase text-center">Verdict</th>
                          <th className="p-2.5 text-[11px] text-[#c7d3ee] tracking-[0.06em] uppercase text-right">Conf</th>
                          <th className="p-2.5 text-[11px] text-[#c7d3ee] tracking-[0.06em] uppercase text-center">Anomaly</th>
                        </tr>
                      </thead>
                      <tbody>
                        {paginatedRecent.map((row, idx) => (
                          <tr key={idx} className="border-b border-[rgba(150,190,255,0.06)] hover:bg-[rgba(150,190,255,0.03)] transition-colors">
                            <td className="p-2.5 font-mono text-[11px] text-[#c7d3ee] whitespace-nowrap">
                              {new Date(row.timestamp).toLocaleString()}
                            </td>
                            <td className="p-2.5 font-mono text-[12px] text-[#eef3ff]">
                              {row.estimated_diameter_min_km && row.estimated_diameter_max_km
                                ? ((row.estimated_diameter_min_km + row.estimated_diameter_max_km) / 2).toFixed(3)
                                : '-'}
                            </td>
                            <td className="p-2.5 font-mono text-[12px] text-right text-[#eef3ff]">{row.relative_velocity_kmph?.toLocaleString(undefined, { maximumFractionDigits: 0 }) ?? '-'}</td>
                            <td className="p-2.5 font-mono text-[12px] text-right text-[#eef3ff]">{row.miss_distance_km?.toLocaleString(undefined, { maximumFractionDigits: 0 }) ?? '-'}</td>
                            <td className="p-2.5 text-center">
                              {row.is_hazardous ? (
                                <span className="text-hazard-red text-[12px] font-bold">HAZARD</span>
                              ) : (
                                <span className="text-accent-lime text-[12px] font-bold">SAFE</span>
                              )}
                            </td>
                            <td className="p-2.5 font-mono text-[12px] text-right text-[#eef3ff]">
                              {row.confidence != null ? (row.confidence * 100).toFixed(1) + '%' : '-'}
                            </td>
                            <td className="p-2.5 text-center">
                              {row.is_anomaly ? (
                                <span className="text-anomaly-amber text-[12px] font-bold">YES</span>
                              ) : (
                                <span className="text-[#5c6f94] text-[12px]">—</span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
                {filteredRecent.length > 0 && (
                  <PaginationControls 
                    totalRows={filteredRecent.length} 
                    rowsPerPage={recRows} 
                    currentPage={recPage} 
                    onPageChange={setRecPage} 
                    onRowsPerPageChange={(v) => { setRecRows(v); setRecPage(1); }} 
                  />
                )}
              </GlassCard>
            </motion.div>
            
          </>
        )}
      </main>

      <Footer />
    </div>
  );
}
