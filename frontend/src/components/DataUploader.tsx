import React, { useState, useRef } from 'react';
import { dataApi } from '../api/endpoints';
import { UploadResponse } from '../types';
import { SkeletonLoader } from './SkeletonLoader';
import { useToast } from '../context/ToastContext';
import { motion, AnimatePresence } from 'framer-motion';

interface DataUploaderProps {
  onUploadSuccess: (data: UploadResponse) => void;
  onFileReset: () => void;
}

export const DataUploader: React.FC<DataUploaderProps> = ({ onUploadSuccess, onFileReset }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadedFile, setUploadedFile] = useState<{ name: string; size: number; } | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const { showToast } = useToast();

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
      showToast(`Injustering lyckades: ${file.name} monterad.`, 'success');
    } catch (err: unknown) {
      const error = err as { response?: { data?: { message?: string; }; }; message?: string; };
      let backendMessage = 'Anslutningsfel mot valideringsklustret eller oväntat valideringsfel.';

      if (error.response?.data?.message) {
        backendMessage = error.response.data.message;
      } else if (error.message) {
        backendMessage = error.message;
      }

      setError(backendMessage);
      showToast(backendMessage, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleClearFile = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    setUploadedFile(null);
    onFileReset();
    showToast('Datasetet har avmonterats.', 'info');

    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (!loading && !uploadedFile) setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    if (loading || uploadedFile) return;

    const file = e.dataTransfer.files?.[0];
    if (file && (file.name.endsWith('.csv') || file.name.endsWith('.parquet'))) {
      await uploadFile(file);
    } else if (file) {
      showToast('Ogiltigt filformat. Endast .csv och .parquet stöds.', 'error');
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
          color: 'var(--text-main)'
        }}>
          1. Data Ingestion Stream
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '13px', lineHeight: '1.5', margin: 0 }}>
          Stöder <span style={{ fontFamily: 'monospace', color: 'var(--accent)' }}>.csv</span> och <span style={{ fontFamily: 'monospace', color: 'var(--accent)' }}>.parquet</span>. Systemet kör automatisk schema- och semantisk driftkontroll.
        </p>
      </div>

      {/* Premium Dropzone */}
      <motion.label
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        animate={{
          scale: isDragging ? 1.015 : 1,
          backgroundColor: loading
            ? 'transparent'
            : uploadedFile
              ? 'var(--bg-card)'
              : isDragging
                ? 'var(--bg-accent-light)'
                : 'transparent',
          borderColor: loading
            ? 'var(--border-color)'
            : uploadedFile
              ? 'var(--success)'
              : isDragging
                ? 'var(--accent)'
                : 'var(--border-color)',
          borderStyle: uploadedFile || isDragging ? 'solid' : 'dashed'
        }}
        transition={{ type: 'spring', stiffness: 400, damping: 25 }}
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: loading ? '10px' : '40px 20px',
          borderWidth: '2px',
          borderRadius: '12px',
          cursor: loading ? 'not-allowed' : uploadedFile ? 'default' : 'pointer',
          width: '100%',
          boxSizing: 'border-box'
        }}
        whileHover={(!loading && !uploadedFile) ? { borderColor: 'var(--accent)', backgroundColor: 'var(--bg-accent-light)' } : {}}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.parquet"
          onChange={handleFileChange}
          disabled={loading || !!uploadedFile}
          style={{ display: 'none' }}
        />

        <AnimatePresence mode="wait">
          {loading ? (
            <motion.div
              key="loading"
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -5 }}
              style={{ width: '100%' }}
            >
              <SkeletonLoader variant="uploader-progress" />
            </motion.div>
          ) : uploadedFile ? (
            <motion.div
              key="uploaded"
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: -10 }}
              transition={{ type: 'spring', stiffness: 350, damping: 25 }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '16px',
                background: 'var(--bg-app)',
                border: '1px solid var(--border-color)',
                padding: '14px 20px',
                borderRadius: '10px',
                maxWidth: '450px',
                width: '100%',
                boxSizing: 'border-box'
              }}
            >
              <div style={{
                width: '36px',
                height: '36px',
                borderRadius: '8px',
                background: 'var(--bg-accent-light)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '18px'
              }}>
                📊
              </div>

              <div style={{ flex: 1, minWidth: 0, textAlign: 'left' }}>
                <div style={{
                  color: 'var(--success)',
                  fontSize: '13px',
                  fontWeight: 600,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap'
                }}>
                  {uploadedFile.name}
                </div>
                <div style={{ color: 'var(--text-muted)', fontSize: '11px', fontFamily: 'monospace', marginTop: '2px' }}>
                  {(uploadedFile.size / (1024 * 1024)).toFixed(2)} MB // READY_FOR_INGESTION
                </div>
              </div>

              <motion.button
                onClick={handleClearFile}
                whileHover={{ scale: 1.1, color: 'var(--error)' }}
                whileTap={{ scale: 0.9 }}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-muted)',
                  cursor: 'pointer',
                  fontSize: '16px',
                  padding: '4px 8px',
                  borderRadius: '6px'
                }}
              >
                ✕
              </motion.button>
            </motion.div>
          ) : (
            <motion.div
              key="default"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              style={{ textAlign: 'center' }}
            >
              <motion.div
                animate={isDragging ? { y: -4, scale: 1.1, color: 'var(--accent)' } : { y: 0, scale: 1, color: 'var(--text-main)' }}
                style={{ fontSize: '28px', marginBottom: '12px', opacity: 0.7 }}
              >
                {isDragging ? '🚀' : '📁'}
              </motion.div>
              <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '4px' }}>
                {isDragging ? 'Släpp filen för att starta ingestion' : 'Välj eller släpp din datafil här'}
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                Klicka för att bläddra på din hårddisk
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.label>

      {/* Felhantering */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, height: 0, marginTop: 0 }}
            animate={{ opacity: 1, height: 'auto', marginTop: 20 }}
            exit={{ opacity: 0, height: 0, marginTop: 0 }}
            style={{ overflow: 'hidden' }}
          >
            <div style={{
              padding: '14px 16px',
              background: 'rgba(239, 68, 68, 0.1)',
              color: 'var(--error)',
              border: '1px solid var(--error)',
              borderRadius: '10px',
              fontSize: '13px',
              lineHeight: '1.5'
            }}>
              <strong>⚠️ Injusteringsfel:</strong> {error}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};