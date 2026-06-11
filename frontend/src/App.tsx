import { useState, useEffect } from 'react';
import { DataUploader } from './components/DataUploader';
import { StatsDashboard } from './components/StatsDashboard';
import { AIChat } from './components/AIChat';
import { CircuitBreakerStatus } from './components/CircuitBreakerStatus';
import { UploadResponse, ChatSession } from './types';
import { OracleBrandIdentity } from './components/OracleBrandIdentity';
import { Sidebar } from './components/Sidebar';
import { ToastProvider } from './context/ToastContext';
import { ThemeProvider } from './context/ThemeContext'; // Importera den nya ThemeProvidern

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
    <ThemeProvider>
      <ToastProvider>
        <div style={{
          display: 'flex',
          width: '100%',
          height: '100vh',
          background: 'var(--bg-app)', // Använder centralt tema
          overflowX: 'hidden',
          transition: 'background-color 0.3s ease'
        }}>

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

          {/* HÖGER SIDA: Huvud-Dashboard */}
          <div className="custom-scrollbar" style={{
            flex: 1,
            fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
            color: 'var(--text-main)', // Använder centralt tema
            padding: '40px 20px',
            letterSpacing: '-0.01em',
            overflowY: 'auto',
            overflowX: 'hidden',
            boxSizing: 'border-box',
            transition: 'color 0.3s ease'
          }}>
            <div style={{ maxWidth: '1100px', margin: '0 auto', width: '100%' }}>

              {/* Premium Header */}
              <header style={{
                marginBottom: '48px',
                borderBottom: '1px solid var(--border-color)', // Använder centralt tema
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
                    color: 'var(--text-muted)', // Använder centralt tema
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
                  background: 'var(--bg-card)', // Använder centralt tema
                  borderRadius: '16px',
                  border: '1px solid var(--border-color)',
                  padding: '24px',
                  boxShadow: '0 4px 30px rgba(0, 0, 0, 0.1)',
                  boxSizing: 'border-box',
                  transition: 'background-color 0.3s ease, border-color 0.3s ease'
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
                    background: 'var(--bg-card)', // Använder centralt tema
                    padding: '24px',
                    borderRadius: '16px',
                    border: '1px solid var(--border-color)',
                    boxShadow: '0 10px 40px rgba(0,0,0,0.1)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '16px',
                    boxSizing: 'border-box',
                    transition: 'background-color 0.3s ease, border-color 0.3s ease'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <div style={{
                        width: '8px',
                        height: '8px',
                        borderRadius: '50%',
                        background: 'var(--success)',
                        boxShadow: '0 0 12px var(--success)'
                      }} />
                      <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 600, color: 'var(--text-main)', letterSpacing: '-0.01em' }}>
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
                        <div style={{ color: 'var(--text-muted)', marginBottom: '4px' }}>Total Records:</div>
                        <div style={{ fontWeight: 600, color: 'var(--text-main)' }}>{currentDataset.rows.toLocaleString()} rader</div>
                      </div>

                      <div>
                        <div style={{ color: 'var(--text-muted)', marginBottom: '8px' }}>Schema Columns:</div>
                        <div style={{
                          display: 'flex',
                          flexWrap: 'wrap',
                          gap: '6px',
                          fontFamily: 'monospace',
                          fontSize: '12px'
                        }}>
                          {currentDataset.columns.map((col, idx) => (
                            <span key={idx} style={{
                              background: 'rgba(255,255,255,0.03)',
                              padding: '2px 8px',
                              borderRadius: '4px',
                              border: '1px solid var(--border-color)',
                              color: 'var(--text-muted)'
                            }}>
                              {col}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </section>
                )}

                {/* Sektion 3 & 4: Delad grid */}
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
                  gap: '32px',
                  width: '100%'
                }}>
                  <section style={{
                    background: 'var(--bg-card)', // Använder centralt tema
                    borderRadius: '16px',
                    border: '1px solid var(--border-color)',
                    padding: '24px',
                    boxShadow: '0 4px 30px rgba(0, 0, 0, 0.1)',
                    boxSizing: 'border-box',
                    transition: 'background-color 0.3s ease, border-color 0.3s ease'
                  }}>
                    <StatsDashboard />
                  </section>

                  <section style={{
                    background: 'var(--bg-card)', // Använder centralt tema
                    borderRadius: '16px',
                    border: '1px solid var(--border-color)',
                    padding: '24px',
                    boxShadow: '0 4px 30px rgba(0, 0, 0, 0.1)',
                    boxSizing: 'border-box',
                    transition: 'background-color 0.3s ease, border-color 0.3s ease'
                  }}>
                    <AIChat />
                  </section>
                </div>

              </div>

              {/* Modern Minimalist Footer */}
              <footer style={{
                marginTop: '80px',
                borderTop: '1px solid var(--border-color)',
                paddingTop: '24px',
                textAlign: 'center',
                fontSize: '12px',
                color: 'var(--text-muted)',
                fontFamily: 'monospace'
              }}>
                ORAKLET CORE // INTEGRATION LAYER // ACCELERATED INFERENCE MODE
              </footer>

            </div>
          </div>

        </div>
      </ToastProvider>
    </ThemeProvider>
  );
}