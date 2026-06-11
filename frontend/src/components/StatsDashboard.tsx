import React, { useState, useMemo } from 'react';
import { dataApi } from '../api/endpoints';
import { StatsResponse } from '../types';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, CartesianGrid } from 'recharts';
import { SkeletonLoader } from './SkeletonLoader';
import { useToast } from '../context/ToastContext'; // 1. Importera global toast-hook

export const StatsDashboard: React.FC = () => {
  const [statsData, setStatsData] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { showToast } = useToast(); // 2. Initiera toasten

  const fetchStats = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await dataApi.getStats();
      setStatsData(data);

      // 3. Skjut en premium framgångs-toast
      showToast('Analys slutförd: Statistisk matris genererad via ETag-cache.', 'success');
    } catch (err: unknown) {
      const error = err as { response?: { data?: { message?: string; }; }; };
      const backendMessage = error.response?.data?.message || 'Kunde inte hämta statistik. Har du laddat upp ett dataset?';

      setError(backendMessage);

      // 4. Skjut en toast för anslutnings- eller valideringsfelet
      showToast(backendMessage, 'error');
    } finally {
      setLoading(false);
    }
  };

  // --- STRUKTURTRANSFORMATION (100% FRONTEND) ---
  const chartData = useMemo(() => {
    const rawStats = statsData?.stats || {};

    return Object.entries(rawStats)
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      .filter(([_key, metrics]) => metrics && typeof metrics.mean === 'number')
      .map(([columnName, metrics]) => ({
        name: columnName,
        "Medelvärde": Number(metrics.mean.toFixed(2)),
        "Min": Number(metrics.min.toFixed(2)),
        "Max": Number(metrics.max.toFixed(2))
      }));
  }, [statsData]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header-sektion */}
      <div style={{ marginBottom: '20px' }}>
        <h2 style={{
          marginTop: 0,
          fontSize: '20px',
          fontWeight: 600,
          letterSpacing: '-0.02em',
          color: '#f8fafc'
        }}>
          2. Dataset Analytics
        </h2>
        <p style={{ color: '#64748b', fontSize: '13px', lineHeight: '1.5', margin: 0 }}>
          Hämtar aggregerad data. Denna vy drar nytta av backendens <span style={{ fontFamily: 'monospace', color: '#38bdf8', background: 'rgba(56, 189, 248, 0.1)', padding: '1px 5px', borderRadius: '4px' }}>ETag-caching</span>.
        </p>
      </div>

      {/* Interaktionsknapp */}
      <button
        onClick={fetchStats}
        disabled={loading}
        style={{
          width: '100%',
          padding: '12px 20px',
          background: loading ? '#1e293b' : 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
          color: loading ? '#94a3b8' : '#38bdf8',
          fontWeight: 600,
          fontSize: '14px',
          border: loading ? '1px solid rgba(255, 255, 255, 0.05)' : '1px solid rgba(56, 189, 248, 0.2)',
          borderRadius: '10px',
          cursor: loading ? 'not-allowed' : 'pointer',
          transition: 'all 0.2s ease',
          boxShadow: loading ? 'none' : '0 4px 12px rgba(56, 189, 248, 0.05)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          gap: '8px',
          marginBottom: '20px'
        }}
        onMouseEnter={(e) => {
          if (!loading) {
            e.currentTarget.style.border = '1px solid rgba(56, 189, 248, 0.4)';
            e.currentTarget.style.boxShadow = '0 4px 20px rgba(56, 189, 248, 0.12)';
          }
        }}
        onMouseLeave={(e) => {
          if (!loading) {
            e.currentTarget.style.border = '1px solid rgba(56, 189, 248, 0.2)';
            e.currentTarget.style.boxShadow = '0 4px 12px rgba(56, 189, 248, 0.05)';
          }
        }}
      >
        {loading ? (
          <>
            <span style={{ display: 'inline-block', animation: 'spin 1s linear infinite' }}>⏳</span>
            Anlyserar matriser...
          </>
        ) : 'Exekvera statistisk profilering'}
      </button>

      {/* Felhantering */}
      {error && (
        <div style={{
          padding: '14px 16px',
          background: 'rgba(239, 68, 68, 0.07)',
          color: '#fca5a5',
          border: '1px solid rgba(239, 68, 68, 0.2)',
          borderRadius: '10px',
          fontSize: '13px',
          lineHeight: '1.5',
          marginBottom: '20px'
        }}>
          ⚠️ {error}
        </div>
      )}

      {loading && <SkeletonLoader variant="dashboard-stats" />}

      {!loading && statsData && chartData.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>

          {/* VISUAL DIAGRAM SEKTION */}
          <div style={{
            background: '#020617',
            border: '1px solid rgba(255, 255, 255, 0.04)',
            borderRadius: '12px',
            padding: '20px 16px 10px 16px',
            boxShadow: '0 4px 20px rgba(0,0,0,0.2)'
          }}>
            <div style={{ fontSize: '11px', fontFamily: 'monospace', color: '#475569', letterSpacing: '0.05em', textTransform: 'uppercase', marginBottom: '16px' }}>
              VISUAL_METRIC_MATRIX // DISTRIBUTION
            </div>

            <div style={{ width: '100%', height: 240 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" vertical={false} />
                  <XAxis dataKey="name" stroke="#475569" fontSize={12} tickLine={false} />
                  <YAxis stroke="#475569" fontSize={12} tickLine={false} />
                  <Tooltip
                    contentStyle={{ background: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: '#f8fafc' }}
                    itemStyle={{ fontSize: '13px' }}
                    labelStyle={{ fontSize: '13px', fontWeight: 'bold', color: '#38bdf8', marginBottom: '4px' }}
                  />
                  <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
                  <Bar dataKey="Medelvärde" fill="#38bdf8" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="Min" fill="#475569" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="Max" fill="#a855f7" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Data-output */}
          <div style={{
            background: '#020617',
            border: '1px solid rgba(255, 255, 255, 0.04)',
            borderRadius: '12px',
            overflow: 'hidden',
            boxShadow: 'inset 0 2px 8px rgba(0, 0, 0, 0.8)'
          }}>
            <div style={{
              background: 'rgba(255, 255, 255, 0.02)',
              padding: '10px 16px',
              borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <span style={{
                fontSize: '11px',
                fontFamily: 'monospace',
                color: '#475569',
                textTransform: 'uppercase',
                letterSpacing: '0.05em'
              }}>
                OUTPUT_BUFFER // JSON_MATRIX
              </span>
              <div style={{ display: 'flex', gap: '6px' }}>
                <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#38bdf8' }} />
                <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#475569' }} />
              </div>
            </div>

            <div style={{ padding: '16px', overflowX: 'auto', maxHeight: '180px' }}>
              <pre style={{
                fontFamily: '"Fira Code", "Courier New", Courier, monospace',
                fontSize: '12px',
                margin: 0,
                color: '#34d399',
                lineHeight: '1.6'
              }}>
                {JSON.stringify(statsData?.stats, null, 2)}
              </pre>
            </div>
          </div>

        </div>
      )}
    </div>
  );
};