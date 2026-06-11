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

  // Tillstånd för chattsessioner, laddas dynamiskt från localStorage om det finns
  const [sessions, setSessions] = useState<ChatSession[]>(() => {
    const saved = localStorage.getItem('oraklet_sessions');
    return saved ? JSON.parse(saved) : [];
  });
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);

  // Spara sessioner automatiskt i webbläsarens minne när de ändras
  useEffect(() => {
    localStorage.setItem('oraklet_sessions', JSON.stringify(sessions));
  }, [sessions]);

  // Funktion för att registrera en ny aktivitet/körning i historiken
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
    <div style={{ display: 'flex', width: '100vw', height: '100vh', background: '#090d16', overflow: 'hidden' }}>

      {/* VÄNSTER SIDA: Din huvudsakliga Dashboard */}
      <div style={{
        flex: 1,
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
        color: '#f8fafc',
        padding: '60px 40px',
        letterSpacing: '-0.01em',
        overflowY: 'auto'
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
              <div style={{ margin: '10px 0 20px 0' }}>
                <OracleBrandIdentity />
              </div>
              <p style={{
                fontSize: '15px',
                color: '#64748b',
                fontWeight: 500,
                margin: 0,
                textTransform: 'uppercase',
                letterSpacing: '0.05em'
              }}>
                Enterprise-Grade Data & AI Processing Platform
              </p>
            </div>

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
              <DataUploader
                onUploadSuccess={(data) => {
                  setCurrentDataset(data);
                  // Skapa en rad i minnesdashboarden automatiskt vid lyckad uppladdning!
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

            {/* Sektion 3 & 4: Delad layout */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))',
              gap: '32px'
            }}>
              <section style={{
                background: '#0f172a',
                borderRadius: '16px',
                border: '1px solid rgba(255, 255, 255, 0.05)',
                padding: '24px',
                boxShadow: '0 4px 30px rgba(0, 0, 0, 0.2)'
              }}>
                <StatsDashboard />
              </section>

              <section style={{
                background: '#0f172a',
                borderRadius: '16px',
                border: '1px solid rgba(255, 255, 255, 0.05)',
                padding: '24px',
                boxShadow: '0 4px 30px rgba(0, 0, 0, 0.2)'
              }}>
                {/* Vi kan skicka med en callback om du vill lägga till sessioner direkt inifrån chatten */}
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

      {/* HÖGER SIDA: Minnesdashboard (Sidebar) */}
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

    </div>
  );
}