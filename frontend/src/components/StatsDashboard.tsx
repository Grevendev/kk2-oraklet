import React, { useState } from 'react';
import { dataApi } from '../api/endpoints';
import { StatsResponse } from '../types';

export const StatsDashboard: React.FC = () => {
  const [statsData, setStatsData] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await dataApi.getStats();
      setStatsData(data);
    } catch (err: any) {
      const backendMessage = err.response?.data?.message || 'Kunde inte hämta statistik. Har du laddat upp ett dataset?';
      setError(backendMessage);
    } finally {
      setLoading(false);
    }
  };

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
          color: loading ? '#94a3b8' : '#38bdf8', // Neonblå elegant text
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
          gap: '8px'
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
            Anyserar matriser...
          </>
        ) : 'Exekvera statistisk profilering'}
      </button>

      {/* Felhantering (Sofistikerad röd alert box) */}
      {error && (
        <div style={{
          marginTop: '20px',
          padding: '14px 16px',
          background: 'rgba(239, 68, 68, 0.07)',
          color: '#fca5a5',
          border: '1px solid rgba(239, 68, 68, 0.2)',
          borderRadius: '10px',
          fontSize: '13px',
          lineHeight: '1.5'
        }}>
          ⚠️ {error}
        </div>
      )}

      {/* Data-output (Premium mörk IDE/Terminal-look) */}
      {statsData && (
        <div style={{
          marginTop: '20px',
          background: '#020617', // Extremt djupt kolfärgad terminalbakgrund
          border: '1px solid rgba(255, 255, 255, 0.04)',
          borderRadius: '12px',
          overflow: 'hidden',
          boxShadow: 'inset 0 2px 8px rgba(0, 0, 0, 0.8)'
        }}>
          {/* Terminal Top Bar */}
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
              textTransform: 'uppercase', // Fixat! Giltig TypeScript-typ för CSS
              letterSpacing: '0.05em'
            }}>
              OUTPUT_BUFFER // JSON_MATRIX
            </span>
            <div style={{ display: 'flex', gap: '6px' }}>
              <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#38bdf8' }} />
              <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#475569' }} />
            </div>
          </div>

          {/* Kodvisare */}
          <div style={{ padding: '16px', overflowX: 'auto', maxHeight: '350px' }}>
            <pre style={{
              fontFamily: '"Fira Code", "Courier New", Courier, monospace',
              fontSize: '12px',
              margin: 0,
              color: '#34d399', // Matrix-grön elegant syntaxfärg
              lineHeight: '1.6'
            }}>
              {JSON.stringify(statsData.stats, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};