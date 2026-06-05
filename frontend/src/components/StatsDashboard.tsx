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
    <div style={{ padding: '20px', border: '1px solid #ccc', borderRadius: '8px', background: '#fff', marginBottom: '20px' }}>
      <h2 style={{ marginTop: 0, color: '#333' }}>2. Dataset-statistik</h2>
      <p style={{ color: '#666', fontSize: '14px' }}>Hämtar aggregerad data. Denna vy drar nytta av backendens ETag-caching.</p>

      <button
        onClick={fetchStats}
        disabled={loading}
        style={{
          padding: '8px 16px',
          background: '#0070f3',
          color: '#fff',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer'
        }}
      >
        {loading ? 'Hämtar...' : 'Läs in / Uppdatera statistik'}
      </button>

      {error && (
        <div style={{ marginTop: '15px', padding: '10px', background: '#fee2e2', color: '#991b1b', borderRadius: '4px', fontSize: '14px' }}>
          {error}
        </div>
      )}

      {statsData && (
        <div style={{ marginTop: '15px', background: '#f4f4f5', padding: '15px', borderRadius: '4px', overflowX: 'auto' }}>
          <h4 style={{ marginTop: 0 }}>Genererad JSON-statistik:</h4>
          <pre style={{ fontSize: '12px', margin: 0 }}>{JSON.stringify(statsData.stats, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};