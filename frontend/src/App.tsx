import React, { useState } from 'react';
import { DataUploader } from './components/DataUploader';
import { StatsDashboard } from './components/StatsDashboard';
import { AIChat } from './components/AIChat';
import { CircuitBreakerStatus } from './components/CircuitBreakerStatus';
import { UploadResponse } from './types';
import { OracleBrandIdentity } from './components/OracleBrandIdentity';
export default function App() {
  const [currentDataset, setCurrentDataset] = useState<UploadResponse | null>(null);

  return (
    <div style={{
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
      background: '#090d16', // Djup, sofistikerad mörk rymdbakgrund
      minHeight: '100vh',
      color: '#f8fafc', // Krispig, vit-grå text för maximal läsbarhet
      padding: '60px 20px',
      letterSpacing: '-0.01em'
    }}>
      <div style={{ maxWidth: '1100px', margin: '0 auto' }}>

        {/* Premium Header */}
        <header style={{
          marginBottom: '48px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
          paddingBottom: '32px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-end',
          flexWrap: 'wrap',
          gap: '20px'
        }}>
          <div>
            {/* Ersatte gamla h1 med en lyxig varumärkesidentitet */}
            <div style={{ margin: '10px 0 20px 0' }}>
              <OracleBrandIdentity />
            </div>
            <p style={{
              fontSize: '15px',
              color: '#64748b', // Mjuk dämpad undertitel
              fontWeight: 500,
              margin: 0,
              textTransform: 'uppercase',
              letterSpacing: '0.05em'
            }}>
              Enterprise-Grade Data & AI Processing Platform
            </p>
          </div>

          {/* Global System Alerts (Circuit Breaker instoppad i headern för renare yta) */}
          <div style={{ minWidth: '240px' }}>
            <CircuitBreakerStatus />
          </div>
        </header>

        {/* Dashboard Layout Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '32px' }}>

          {/* Sektion 1: Ingestering */}
          <section style={{
            background: '#0f172a',
            borderRadius: '16px',
            border: '1px solid rgba(255, 255, 255, 0.05)',
            padding: '24px',
            boxShadow: '0 4px 30px rgba(0, 0, 0, 0.2)'
          }}>
            <DataUploader onUploadSuccess={(data) => setCurrentDataset(data)} />
          </section>

          {/* Sektion 2: Status över aktivt dataset (Visas som ett läckert ID-kort) */}
          {currentDataset && (
            <section style={{
              background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
              padding: '24px',
              borderRadius: '16px',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              boxShadow: '0 10px 40px rgba(0,0,0,0.3)',
              display: 'flex',
              flexDirection: 'column',
              gap: '16px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981', boxShadow: '0 0 12px #10b981' }} />
                <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 600, color: '#f1f5f9', letterSpacing: '-0.01em' }}>
                  Active Dataset Mounted
                </h3>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: '16px', fontSize: '14px' }}>
                <div style={{ color: '#64748b' }}>Total Records:</div>
                <div style={{ fontWeight: 600, color: '#e2e8f0' }}>{currentDataset.rows.toLocaleString()} rader</div>

                <div style={{ color: '#64748b' }}>Schema Columns:</div>
                <div style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: '6px',
                  fontFamily: 'monospace',
                  fontSize: '12px'
                }}>
                  {currentDataset.columns.map((col, idx) => (
                    <span key={idx} style={{
                      background: 'rgba(255,255,255,0.05)',
                      padding: '2px 8px',
                      borderRadius: '4px',
                      border: '1px solid rgba(255,255,255,0.05)',
                      color: '#94a3b8'
                    }}>
                      {col}
                    </span>
                  ))}
                </div>
              </div>
            </section>
          )}

          {/* Sektion 3 & 4: Delad layout om skärmen är stor för maximal dashboard-känsla */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))',
            gap: '32px'
          }}>
            {/* Sektion 3: Statistik & Analys */}
            <section style={{
              background: '#0f172a',
              borderRadius: '16px',
              border: '1px solid rgba(255, 255, 255, 0.05)',
              padding: '24px',
              boxShadow: '0 4px 30px rgba(0, 0, 0, 0.2)'
            }}>
              <StatsDashboard />
            </section>

            {/* Sektion 4: AI Pipeline Interaktion */}
            <section style={{
              background: '#0f172a',
              borderRadius: '16px',
              border: '1px solid rgba(255, 255, 255, 0.05)',
              padding: '24px',
              boxShadow: '0 4px 30px rgba(0, 0, 0, 0.2)'
            }}>
              <AIChat />
            </section>
          </div>

        </div>

        {/* Modern Minimalist Footer */}
        <footer style={{
          marginTop: '80px',
          borderTop: '1px solid rgba(255, 255, 255, 0.04)',
          paddingTop: '24px',
          textAlign: 'center',
          fontSize: '12px',
          color: '#475569',
          fontFamily: 'monospace'
        }}>
          ORAKLET CORE // INTEGRATION LAYER // ACCELERATED INFERENCE MODE
        </footer>

      </div>
    </div>
  );
}