// src/components/StatsDashboard.tsx
import React, { useState, useMemo } from 'react';
import { dataApi } from '../api/endpoints';
import { StatsResponse } from '../types';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, CartesianGrid } from 'recharts';
import { SkeletonLoader } from './SkeletonLoader';
import { useToast } from '../context/ToastContext';

export const StatsDashboard: React.FC = () => {
  const [statsData, setStatsData] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { showToast } = useToast();

  const fetchStats = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await dataApi.getStats();
      setStatsData(data);
      showToast('Analys slutförd: Statistisk matris genererad via ETag-cache.', 'success');
    } catch (err: unknown) {
      const error = err as { response?: { data?: { message?: string; }; }; };
      const backendMessage = error.response?.data?.message || 'Kunde inte hämta statistik. Har du laddat upp ett dataset?';
      setError(backendMessage);
      showToast(backendMessage, 'error');
    } finally {
      setLoading(false);
    }
  };

  const chartData = useMemo(() => {
    const rawStats = statsData?.stats || {};
    return Object.entries(rawStats)
      .filter(([, metrics]) => metrics && typeof metrics.mean === 'number')
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
          color: 'var(--text-main)'
        }}>
          2. Dataset Analytics
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '13px', lineHeight: '1.5', margin: 0 }}>
          Hämtar aggregerad data. Denna vy drar nytta av backendens <span style={{ fontFamily: 'monospace', color: 'var(--accent)', background: 'var(--bg-accent-light)', padding: '1px 5px', borderRadius: '4px' }}>ETag-caching</span>.
        </p>
      </div>

      {/* Interaktionsknapp */}
      <button
        onClick={fetchStats}
        disabled={loading}
        style={{
          width: '100%',
          padding: '12px 20px',
          background: loading ? 'var(--bg-card)' : 'var(--bg-app)',
          color: 'var(--accent)',
          fontWeight: 600,
          fontSize: '14px',
          border: '1px solid var(--accent)',
          borderRadius: '10px',
          cursor: loading ? 'not-allowed' : 'pointer',
          transition: 'all 0.2s ease',
          boxShadow: loading ? 'none' : '0 4px 12px var(--shadow-glow)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          gap: '8px',
          marginBottom: '20px'
        }}
      >
        {loading ? (
          <>
            <span style={{ display: 'inline-block', animation: 'spin 1s linear infinite' }}>⏳</span>
            Analyserar matriser...
          </>
        ) : 'Exekvera statistisk profilering'}
      </button>

      {/* Felhantering */}
      {error && (
        <div style={{
          padding: '14px 16px',
          background: 'rgba(239, 68, 68, 0.1)',
          color: 'var(--error)',
          border: '1px solid var(--error)',
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
            background: 'var(--bg-card)',
            border: '1px solid var(--border-color)',
            borderRadius: '12px',
            padding: '20px 16px 10px 16px'
          }}>
            <div style={{ fontSize: '11px', fontFamily: 'monospace', color: 'var(--text-muted)', letterSpacing: '0.05em', textTransform: 'uppercase', marginBottom: '16px' }}>
              VISUAL_METRIC_MATRIX // DISTRIBUTION
            </div>

            <div style={{ width: '100%', height: 240 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" vertical={false} />
                  <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={12} tickLine={false} />
                  <YAxis stroke="var(--text-muted)" fontSize={12} tickLine={false} />
                  <Tooltip
                    contentStyle={{ background: 'var(--bg-sidebar)', border: '1px solid var(--border-color)', borderRadius: '8px', color: 'var(--text-main)' }}
                    itemStyle={{ fontSize: '13px' }}
                    labelStyle={{ fontSize: '13px', fontWeight: 'bold', color: 'var(--accent)', marginBottom: '4px' }}
                  />
                  <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
                  <Bar dataKey="Medelvärde" fill="var(--accent)" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="Min" fill="var(--text-muted)" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="Max" fill="var(--secondary)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Data-output */}
          <div style={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border-color)',
            borderRadius: '12px',
            overflow: 'hidden'
          }}>
            <div style={{
              background: 'var(--bg-accent-light)',
              padding: '10px 16px',
              borderBottom: '1px solid var(--border-color)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <span style={{
                fontSize: '11px',
                fontFamily: 'monospace',
                color: 'var(--text-muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.05em'
              }}>
                OUTPUT_BUFFER // JSON_MATRIX
              </span>
            </div>

            <div style={{ padding: '16px', overflowX: 'auto', maxHeight: '180px' }}>
              <pre style={{
                fontFamily: '"Fira Code", monospace',
                fontSize: '12px',
                margin: 0,
                color: 'var(--success)',
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