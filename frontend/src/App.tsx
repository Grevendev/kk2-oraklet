import React, { useState } from 'react';
import { DataUploader } from './components/DataUploader';
import { StatsDashboard } from './components/StatsDashboard';
import { AIChat } from './components/AIChat';
import { CircuitBreakerStatus } from './components/CircuitBreakerStatus';
import { UploadResponse } from './types';

export default function App() {
  const [currentDataset, setCurrentDataset] = useState<UploadResponse | null>(null);

  return (
    <div style={{
      fontFamily: 'system-ui, -apple-system, sans-serif',
      background: '#0d9ea1',
      minHeight: '100vh',
      color: '#193370',
      padding: '40px 20px'
    }}>
      <div style={{ maxWidth: '1000px', margin: '0 auto' }}>

        {/* Header */}
        <header style={{ marginBottom: '40px', borderBottom: '1px solid #022553', paddingBottom: '20px' }}>
          <h1 style={{ fontSize: '32px', fontWeight: 800, margin: '0 0 8px 0', color: '#022553' }}>
            Oraklet
          </h1>
          <p style={{ fontSize: '25px', color: '#022553', margin: 0 }}>
            Enterprise-Grade Data & AI Processing Platform
          </p>
        </header>

        {/* Global System Alerts (Circuit Breaker) */}
        <CircuitBreakerStatus />

        {/* Grid Layout för kontrollpanelen */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '24px' }}>

          {/* Sektion 1: Ingestering */}
          <section>
            <DataUploader onUploadSuccess={(data) => setCurrentDataset(data)} />
          </section>

          {/* Sektion 2: Status över aktivt dataset */}
          {currentDataset && (
            <section style={{
              background: '#fff',
              padding: '20px',
              borderRadius: '8px',
              border: '1px solid #e2e8f0',
              marginBottom: '20px'
            }}>
              <h3 style={{ marginTop: 0, color: '#0f172a' }}>Aktivt Dataset Inläst</h3>
              <div style={{ display: 'flex', gap: '40px', fontSize: '14px' }}>
                <div><strong>Rader:</strong> {currentDataset.rows}</div>
                <div><strong>Kolumner:</strong> {currentDataset.columns.join(', ')}</div>
              </div>
            </section>
          )}

          {/* Sektion 3: Statistik & Analys */}
          <section>
            <StatsDashboard />
          </section>

          {/* Sektion 4: AI Pipeline Interaktion */}
          <section>
            <AIChat />
          </section>

        </div>

        {/* Footer */}
        <footer style={{ marginTop: '60px', textAlign: 'center', fontSize: '12px', color: '#94a3b8' }}>
          Oraklet Backend & Frontend Integration Layer • Full Fault-Tolerance Mode
        </footer>

      </div>
    </div>
  );
}