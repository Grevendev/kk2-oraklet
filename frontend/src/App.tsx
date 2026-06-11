import { useState, useEffect } from 'react';
import { DataUploader } from './components/DataUploader';
import { StatsDashboard } from './components/StatsDashboard';
import { AIChat } from './components/AIChat';
import { CircuitBreakerStatus } from './components/CircuitBreakerStatus';
import { UploadResponse, ChatSession } from './types';
import { OracleBrandIdentity } from './components/OracleBrandIdentity';
import { Sidebar } from './components/Sidebar';

export default function App() {
  const [currentDataset, setCurrentDataset] = useState<UploadResponse | null>(null);

  const [sessions, setSessions] = useState<ChatSession[]>(() => {
    const saved = localStorage.getItem('oraklet_sessions');
    return saved ? JSON.parse(saved) : [];
  });
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);

  useEffect(() => {
    localStorage.setItem('oraklet_sessions', JSON.stringify(sessions));
  }, [sessions]);

  const handleNewSession = (title: string) => {
    const newSession: ChatSession = {
      id: String(Date.now()),
      title: title || 'Odefinierad analys',
      createdAt: new Date().toLocaleDateString('sv-SE')
    };
    setSessions((prev) => [newSession, ...prev]);
    setCurrentSessionId(newSession.id);
  };

  return (
    <div style={{
      display: 'flex',
      width: '100%', // Ändrat från 100vw till 100% för att förhindra horisontell scroll
      height: '100vh',
      background: '#090d16',
      overflowX: 'hidden' // Blockerar all sido-förflyttning helt
    }}>

      {/* ─── INJICERAD CSS FÖR RESPONSIVITET OCH GÖMDA SCROLLISTER ─── */}
      <style>{`
        /* Göm webbläsarens yttre standard-scrollbar helt från fönsterkanten */
        html, body {
          margin: 0;
          padding: 0;
          width: 100%;
          height: 100vh;
          overflow: hidden;
        }

        /* Dölj scrollbar helt för vänstersidan (Sidebar) */
        .hide-scrollbar {
          scrollbar-width: none; /* Firefox */
          -ms-overflow-style: none; /* IE/Edge */
        }
        .hide-scrollbar::-webkit-scrollbar {
          display: none; /* Chrome, Safari, Opera */
        }

        /* Tunn, lyxig scrollbar för högersidan (Huvudinnehållet) */
        .custom-scrollbar {
          scrollbar-width: thin;
          scrollbar-color: rgba(255, 255, 255, 0.05) transparent;
        }
        .custom-scrollbar::-webkit-scrollbar {
          width: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.04);
          border-radius: 10px;
        }
        .custom-scrollbar:hover::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.12);
        }
      `}</style>

      {/* VÄNSTER SIDA: Minnesdashboard */}
      <Sidebar
        sessions={sessions}
        currentSessionId={currentSessionId}
        onSelectSession={(id) => setCurrentSessionId(id)}
        onNewChat={() => handleNewSession('Ny odefinierad session')}
        onClearHistory={() => {
          setSessions([]);
          setCurrentSessionId(null);
        }}
      />

      {/* HÖGER SIDA: Huvud-Dashboard (Helt responsiv flexbox) */}
      <div className="custom-scrollbar" style={{
        flex: 1,
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
        color: '#f8fafc',
        padding: '40px 20px', // Något mindre padding för bättre responsivitet på mindre skärmar
        letterSpacing: '-0.01em',
        overflowY: 'auto',
        overflowX: 'hidden', // Säkerställer att inte heller innehållet trycker ut sidan i sidled
        boxSizing: 'border-box'
      }}>
        <div style={{ maxWidth: '1100px', margin: '0 auto', width: '100%' }}>

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
            <div style={{ flex: '1 1 300px' }}>
              <div style={{ margin: '10px 0 20px 0' }}>
                <OracleBrandIdentity />
              </div>
              <p style={{
                fontSize: '14px',
                color: '#64748b',
                fontWeight: 500,
                margin: 0,
                textTransform: 'uppercase',
                letterSpacing: '0.05em'
              }}>
                Enterprise-Grade Data & AI Processing Platform
              </p>
            </div>

            <div style={{ minWidth: '240px', flex: '0 1 auto' }}>
              <CircuitBreakerStatus />
            </div>
          </header>

          {/* Dashboard Layout Grid */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '32px', width: '100%' }}>

            {/* Sektion 1: Ingestering */}
            <section style={{
              background: '#0f172a',
              borderRadius: '16px',
              border: '1px solid rgba(255, 255, 255, 0.05)',
              padding: '24px',
              boxShadow: '0 4px 30px rgba(0, 0, 0, 0.2)',
              boxSizing: 'border-box'
            }}>
              <DataUploader
                onUploadSuccess={(data) => {
                  setCurrentDataset(data);
                  handleNewSession(`Dataset monterat (${data.columns.length} kolumner)`);
                }}
                onFileReset={() => setCurrentDataset(null)}
              />
            </section>

            {/* Sektion 2: Status över aktivt dataset */}
            {currentDataset && (
              <section style={{
                background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
                padding: '24px',
                borderRadius: '16px',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                boxShadow: '0 10px 40px rgba(0,0,0,0.3)',
                display: 'flex',
                flexDirection: 'column',
                gap: '16px',
                boxSizing: 'border-box'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981', boxShadow: '0 0 12px #10b981' }} />
                  <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 600, color: '#f1f5f9', letterSpacing: '-0.01em' }}>
                    Active Dataset Mounted
                  </h3>
                </div>

                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
                  gap: '16px',
                  fontSize: '14px'
                }}>
                  <div>
                    <div style={{ color: '#64748b', marginBottom: '4px' }}>Total Records:</div>
                    <div style={{ fontWeight: 600, color: '#e2e8f0' }}>{currentDataset.rows.toLocaleString()} rader</div>
                  </div>

                  <div>
                    <div style={{ color: '#64748b', marginBottom: '8px' }}>Schema Columns:</div>
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
                </div>
              </section>
            )}

            {/* Sektion 3 & 4: Delad grid med flexibel brytpunkt */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', // Justerad minmax från 450px till 320px för mycket bättre mobil/smal-skärms-responsivitet
              gap: '32px',
              width: '100%'
            }}>
              <section style={{
                background: '#0f172a',
                borderRadius: '16px',
                border: '1px solid rgba(255, 255, 255, 0.05)',
                padding: '24px',
                boxShadow: '0 4px 30px rgba(0, 0, 0, 0.2)',
                boxSizing: 'border-box'
              }}>
                <StatsDashboard />
              </section>

              <section style={{
                background: '#0f172a',
                borderRadius: '16px',
                border: '1px solid rgba(255, 255, 255, 0.05)',
                padding: '24px',
                boxShadow: '0 4px 30px rgba(0, 0, 0, 0.2)',
                boxSizing: 'border-box'
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

    </div>
  );
}