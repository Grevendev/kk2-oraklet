import React, { useState } from 'react';
import { dataApi } from '../api/endpoints';
import { UploadResponse } from '../types';

interface DataUploaderProps {
  onUploadSuccess: (data: UploadResponse) => void;
}

export const DataUploader: React.FC<DataUploaderProps> = ({ onUploadSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Nytt state för att hålla reda på den framgångsrikt uppladdade filen
  const [uploadedFile, setUploadedFile] = useState<{ name: string; size: number; } | null>(null);

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    await uploadFile(file);
  };

  const uploadFile = async (file: File) => {
    setLoading(true);
    setError(null);

    try {
      const response = await dataApi.upload(file);
      // Spara filens metadata vid framgång för det nya UI-läget
      setUploadedFile({ name: file.name, size: file.size });
      onUploadSuccess(response);
    } catch (err: any) {
      if (err.response?.data?.message) {
        setError(err.response.data.message);
      } else if (err.message) {
        setError(err.message);
      } else {
        setError('Anslutningsfel mot valideringsklustret eller oväntat valideringsfel.');
      }
    } finally {
      setLoading(false);
    }
  };

  // Funktion för att nollställa uppladdningsvyn och tillåta en ny fil
  const handleClearFile = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation(); // Förhindrar att filväljaren öppnas när man klickar på krysset
    setUploadedFile(null);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Titel & Beskrivning */}
      <div style={{ marginBottom: '20px' }}>
        <h2 style={{
          marginTop: 0,
          fontSize: '20px',
          fontWeight: 600,
          letterSpacing: '-0.02em',
          color: '#f8fafc'
        }}>
          1. Data Ingestion Stream
        </h2>
        <p style={{ color: '#64748b', fontSize: '13px', lineHeight: '1.5', margin: 0 }}>
          Stöder <span style={{ fontFamily: 'monospace', color: '#a855f7' }}>.csv</span> och <span style={{ fontFamily: 'monospace', color: '#a855f7' }}>.parquet</span>. Systemet kör automatisk schema- och semantisk driftkontroll.
        </p>
      </div>

      {/* Premium Dropzone Labellager */}
      <label
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '40px 20px',
          background: loading
            ? '#0f172a'
            : uploadedFile
              ? 'rgba(52, 211, 153, 0.02)'
              : 'rgba(255, 255, 255, 0.01)',
          border: loading
            ? '2px dashed rgba(168, 85, 247, 0.2)'
            : uploadedFile
              ? '2px solid rgba(52, 211, 153, 0.3)'
              : '2px dashed rgba(255, 255, 255, 0.1)',
          borderRadius: '12px',
          cursor: loading ? 'not-allowed' : uploadedFile ? 'default' : 'pointer',
          transition: 'all 0.2s ease',
          boxShadow: uploadedFile ? '0 4px 20px rgba(52, 211, 153, 0.03)' : 'inset 0 2px 4px rgba(0, 0, 0, 0.4)'
        }}
        onMouseEnter={(e) => {
          if (!loading && !uploadedFile) {
            e.currentTarget.style.borderColor = 'rgba(168, 85, 247, 0.4)';
            e.currentTarget.style.background = 'rgba(168, 85, 247, 0.02)';
          }
        }}
        onMouseLeave={(e) => {
          if (!loading && !uploadedFile) {
            e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.1)';
            e.currentTarget.style.background = 'rgba(255, 255, 255, 0.01)';
          }
        }}
      >
        {/* Det osynliga fil-inputet */}
        <input
          type="file"
          accept=".csv,.parquet"
          onChange={handleFileChange}
          disabled={loading || !!uploadedFile}
          style={{ display: 'none' }}
        />

        {/* Dynamiskt UI-innehåll baserat på status: LOADING -> UPLOADED -> DEFAULT */}
        {loading ? (
          <div style={{ textAlign: 'center' }}>
            <div style={{
              fontSize: '24px',
              marginBottom: '12px',
              animation: 'pulse 1.5s infinite ease-in-out'
            }}>
              ⚙️
            </div>
            <div style={{ fontSize: '14px', fontWeight: 600, color: '#a855f7', marginBottom: '4px' }}>
              Kör defensiv datavalidering...
            </div>
            <div style={{ fontSize: '12px', color: '#475569', fontFamily: 'monospace' }}>
              PARSING_SCHEMA_MATRICES
            </div>
          </div>
        ) : uploadedFile ? (
          /* DET NYA FINARE LÄGET NÄR EN FIL ÄR UPPLADDAD */
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '16px',
            background: '#020617',
            border: '1px solid rgba(255, 255, 255, 0.05)',
            padding: '14px 20px',
            borderRadius: '10px',
            maxWidth: '450px',
            width: '100%',
            boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
            cursor: 'default'
          }}>
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: '8px',
              background: 'rgba(52, 211, 153, 0.1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '18px'
            }}>
              📊
            </div>

            <div style={{ flex: 1, minWidth: 0, textAlign: 'left' }}>
              <div style={{
                color: '#34d399',
                fontSize: '13px',
                fontWeight: 600,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap'
              }}>
                {uploadedFile.name}
              </div>
              <div style={{ color: '#475569', fontSize: '11px', fontFamily: 'monospace', marginTop: '2px' }}>
                {(uploadedFile.size / (1024 * 1024)).toFixed(2)} MB // READY_FOR_INGESTION
              </div>
            </div>

            <button
              onClick={handleClearFile}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#64748b',
                cursor: 'pointer',
                fontSize: '16px',
                padding: '4px 8px',
                borderRadius: '6px',
                transition: 'all 0.2s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = '#ef4444';
                e.currentTarget.style.background = 'rgba(239, 68, 68, 0.07)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = '#64748b';
                e.currentTarget.style.background = 'transparent';
              }}
            >
              ✕
            </button>
          </div>
        ) : (
          /* UTGÅNGSLÄGET (Helt orört från din originalkod) */
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '28px', marginBottom: '12px', opacity: 0.7 }}>
              📁
            </div>
            <div style={{ fontSize: '14px', fontWeight: 600, color: '#e2e8f0', marginBottom: '4px' }}>
              Välj eller släpp din datafil här
            </div>
            <div style={{ fontSize: '12px', color: '#64748b' }}>
              Klicka för att bläddra på din hårddisk
            </div>
          </div>
        )}
      </label>

      {/* Sofistikerat Injusteringsfel */}
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
          <strong>⚠️ Injusteringsfel:</strong> {error}
        </div>
      )}
    </div>
  );
};