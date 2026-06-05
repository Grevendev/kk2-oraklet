import React, { useState } from 'react';
import { dataApi } from '../api/endpoints';
import { UploadResponse } from '../types';

interface DataUploaderProps {
  onUploadSuccess: (data: UploadResponse) => void;
}

export const DataUploader: React.FC<DataUploaderProps> = ({ onUploadSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setError(null);

    try {
      const response = await dataApi.upload(file);
      onUploadSuccess(response);
    } catch (err: any) {
      // Här fångar vi upp dina anpassade felmeddelanden från FastAPI
      const backendMessage = err.response?.data?.message || 'Ett oväntat fel uppstod vid valideringen.';
      setError(backendMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px', border: '1px solid #ccc', borderRadius: '8px', background: '#fff', marginBottom: '20px' }}>
      <h2 style={{ marginTop: 0, color: '#333' }}>1. Ladda upp dataset</h2>
      <p style={{ color: '#666', fontSize: '14px' }}>Stöder `.csv` och `.parquet`. Systemet kör automatisk schema- och semantisk driftkontroll.</p>

      <input
        type="file"
        accept=".csv,.parquet"
        onChange={handleFileChange}
        disabled={loading}
        style={{ marginTop: '10px' }}
      />

      {loading && <p style={{ color: '#0070f3' }}>Kör defensiv datavalidering...</p>}

      {error && (
        <div style={{ marginTop: '15px', padding: '10px', background: '#fee2e2', color: '#991b1b', borderRadius: '4px', fontSize: '14px' }}>
          <strong>Injusteringsfel:</strong> {error}
        </div>
      )}
    </div>
  );
};