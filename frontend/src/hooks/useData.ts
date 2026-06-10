import { useState } from 'react';
import { UploadResponse, StatsResponse } from '../types';

const API_BASE = 'http://127.0.0.1:8000';

export const useData = () => {
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [metaData, setMetaData] = useState<UploadResponse | null>(null);
  const [statsData, setStatsData] = useState<StatsResponse | null>(null);

  const uploadCSV = async (file: File) => {
    setLoading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_BASE}/data/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({ message: 'Uppladdning misslyckades' }));
        throw new Error(errData.message || `Status: ${response.status}`);
      }

      const data: UploadResponse = await response.json();
      setMetaData(data);

      // Hämta automatiskt statistik efter lyckad uppladdning
      await fetchStats();

      return data;
    } catch (err: any) {
      setError(err.message || 'Ett oväntat fel uppstod vid uppladdning.');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_BASE}/data/stats`);
      if (!response.ok) {
        if (response.status === 404) return;
        throw new Error('Kunde inte hämta statistik');
      }
      const data: StatsResponse = await response.json();
      setStatsData(data);
    } catch (err: any) {
      console.error("Fel vid hämtning av statistik:", err);
    }
  };

  return {
    loading,
    error,
    metaData,
    statsData, // Innehåller objektet { stats: { ... } } enligt din index.ts
    uploadCSV,
    fetchStats
  };
};