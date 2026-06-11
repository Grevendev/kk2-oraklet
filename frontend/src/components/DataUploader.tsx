import React, { useState, useRef } from 'react';
import { dataApi } from '../api/endpoints';
import { UploadResponse } from '../types';
import { SkeletonLoader } from './SkeletonLoader';

interface DataUploaderProps {
  onUploadSuccess: (data: UploadResponse) => void;
  onFileReset: () => void;
}

export const DataUploader: React.FC<DataUploaderProps> = ({ onUploadSuccess, onFileReset }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadedFile, setUploadedFile] = useState<{ name: string; size: number; } | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

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
      setUploadedFile({ name: file.name, size: file.size });
      onUploadSuccess(response);
    } catch (err: unknown) {
      const error = err as { response?: { data?: { message?: string; }; }; message?: string; };

      if (error.response?.data?.message) {
        setError(error.response.data.message);
      } else if (error.message) {
        setError(error.message);
      } else {
        setError('Anslutningsfel mot valideringsklustret eller oväntat valideringsfel.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleClearFile = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    setUploadedFile(null);
    onFileReset();

    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
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
          padding: loading ? '10px' : '40px 20px', // Krymper paddingen något under loading för att matcha skelettets storlek perfekt
          background: loading
            ? 'transparent'
            : uploadedFile
              ? 'rgba(52, 211, 153, 0.02)'
              : 'rgba(255, 255, 255, 0.01)',
          border: loading
            ? '1px solid transparent'
            : uploadedFile
              ? '2px solid rgba(52, 211, 153, 0.3)'
              : '2px dashed rgba(255, 255, 255, 0.1)',
          borderRadius: '12px',
          cursor: loading ? 'not-allowed' : uploadedFile ? 'default' : 'pointer',
          transition: 'all 0.2s ease',
          boxShadow: uploadedFile ? '0 4px 20px rgba(52, 211, 153, 0.03)' : loading ? 'none' : 'inset 0 2px 4px rgba(0, 0, 0, 0.4)',
          width: '100%',
          boxSizing: 'border-box'
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
          ref={fileInputRef}
          type="file"
          accept=".csv,.parquet"
          onChange={handleFileChange}
          disabled={loading || !!uploadedFile}
          style={{ display: 'none' }}
        />

        {/* Dynamiskt UI-innehåll baserat på status: LOADING -> UPLOADED -> DEFAULT */}
        {loading ? (
          // Injekterar den pulserande rutan för filanalys
          <SkeletonLoader variant="uploader-progress" />
        ) : uploadedFile ? (
          /* DET FINARE LÄGET NÄR EN FIL ÄR UPPLADDAD */
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
            boxSizing: 'border-box',
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
          /* UTGÅNGSLÄGET */
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