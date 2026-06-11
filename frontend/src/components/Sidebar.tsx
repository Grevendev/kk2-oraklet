import React, { useState } from 'react';
import { ChatSession } from '../types';

interface SidebarProps {
  sessions: ChatSession[];
  currentSessionId: string | null;
  onSelectSession: (id: string) => void;
  onNewChat: () => void;
  onClearHistory: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  sessions,
  currentSessionId,
  onSelectSession,
  onNewChat,
  onClearHistory
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [isOpen, setIsOpen] = useState(true);

  const filteredSessions = sessions.filter(session =>
    session.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        style={{
          position: 'fixed',
          left: '20px', // Justerad till vänster
          top: '20px',
          zIndex: 50,
          background: '#0f172a',
          color: '#38bdf8',
          border: '1px solid rgba(56, 189, 248, 0.2)',
          borderRadius: '8px',
          padding: '10px 14px',
          cursor: 'pointer',
          fontFamily: 'sans-serif',
          fontSize: '13px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          gap: '6px'
        }}
      >
        <span>📁</span> Visa historik
      </button>
    );
  }

  return (
    <div style={{
      width: '300px',
      height: '100vh',
      background: '#050b14',
      borderRight: '1px solid rgba(255, 255, 255, 0.05)', // Ändrat till borderRight
      display: 'flex',
      flexDirection: 'column',
      padding: '20px',
      boxShadow: '4px 0 30px rgba(0,0,0,0.4)', // Kastar skugga åt höger istället
      boxSizing: 'border-box'
    }}>
      {/* Top Kontroller */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <span style={{ fontSize: '11px', fontFamily: 'monospace', color: '#475569', letterSpacing: '0.05em', fontWeight: 600 }}>
          MEMORY_DASHBOARD
        </span>
        <button
          onClick={() => setIsOpen(false)}
          style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', fontSize: '16px' }}
          title="Göm panel"
        >
          ✕
        </button>
      </div>

      {/* Ny session */}
      <button
        onClick={onNewChat}
        style={{
          width: '100%',
          padding: '12px',
          marginBottom: '16px',
          background: 'rgba(56, 189, 248, 0.04)',
          color: '#38bdf8',
          border: '1px dashed rgba(56, 189, 248, 0.25)',
          borderRadius: '8px',
          fontWeight: 600,
          fontSize: '13px',
          cursor: 'pointer',
          transition: 'all 0.2s'
        }}
      >
        + Ny session
      </button>

      {/* Sökfält */}
      <input
        type="text"
        placeholder="Sök i tidigare tasks..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        style={{
          width: '100%',
          padding: '10px 12px',
          marginBottom: '24px',
          background: 'rgba(255, 255, 255, 0.02)',
          border: '1px solid rgba(255, 255, 255, 0.06)',
          borderRadius: '8px',
          color: '#f8fafc',
          fontSize: '13px',
          outline: 'none',
          boxSizing: 'border-box'
        }}
      />

      {/* Lista över sparade händelser med osynlig/tunn scroll */}
      <div
        className="custom-scrollbar"
        style={{
          flex: 1,
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '6px',
        }}
      >
        <div style={{ fontSize: '11px', color: '#475569', fontWeight: 700, marginBottom: '6px', letterSpacing: '0.03em' }}>
          SENASTE AKTIVITETER
        </div>

        {filteredSessions.length === 0 ? (
          <div style={{ fontSize: '12px', color: '#334155', fontStyle: 'italic', padding: '10px' }}>
            Ingen historik lagrad ännu
          </div>
        ) : (
          filteredSessions.map((session) => {
            const isActive = session.id === currentSessionId;
            return (
              <div
                key={session.id}
                onClick={() => onSelectSession(session.id)}
                style={{
                  padding: '12px',
                  borderRadius: '8px',
                  background: isActive ? 'rgba(255, 255, 255, 0.04)' : 'transparent',
                  color: isActive ? '#f8fafc' : '#94a3b8',
                  fontSize: '13px',
                  fontWeight: isActive ? 600 : 400,
                  cursor: 'pointer',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  border: isActive ? '1px solid rgba(255, 255, 255, 0.08)' : '1px solid transparent',
                  boxSizing: 'border-box'
                }}
              >
                {session.title}
              </div>
            );
          })
        )}
      </div>

      {/* Rensa-knapp i botten */}
      {sessions.length > 0 && (
        <button
          onClick={onClearHistory}
          style={{
            background: 'none',
            border: 'none',
            color: '#f43f5e',
            fontSize: '11px',
            cursor: 'pointer',
            textAlign: 'left',
            padding: '10px 0 0 4px',
            opacity: 0.6,
            fontFamily: 'monospace'
          }}
        >
          // PURGE_ALL_HISTORY
        </button>
      )}
    </div>
  );
};