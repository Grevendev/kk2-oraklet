import React, { useState } from 'react';
import { ChatSession } from '../types';
import { SkeletonLoader } from './SkeletonLoader';
import { useToast } from '../context/ToastContext';
import { motion, AnimatePresence } from 'framer-motion';
import { Settings } from './Settings';

interface SidebarProps {
  sessions: ChatSession[];
  currentSessionId: string | null;
  onSelectSession: (id: string) => void;
  onNewChat: () => void;
  onClearHistory: () => void;
  loading?: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  sessions,
  currentSessionId,
  onSelectSession,
  onNewChat,
  onClearHistory,
  loading = false
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [isOpen, setIsOpen] = useState(true);
  const { showToast } = useToast();

  const filteredSessions = sessions.filter(session =>
    session.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handlePurgeHistory = () => {
    onClearHistory();
    showToast('Sessionshistoriken har raderats och rensats permanent.', 'error');
  };

  return (
    <AnimatePresence mode="wait">
      {!isOpen ? (
        <motion.button
          key="open-btn"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          whileHover={{ scale: 1.05, borderColor: 'var(--accent)' }}
          whileTap={{ scale: 0.95 }}
          onClick={() => setIsOpen(true)}
          style={{
            position: 'fixed',
            left: '20px',
            top: '20px',
            zIndex: 50,
            background: 'var(--bg-sidebar)',
            color: 'var(--accent)',
            border: '1px solid var(--accent)',
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
        </motion.button>
      ) : (
        <motion.div
          key="sidebar-panel"
          initial={{ width: 0, opacity: 0, minWidth: 0 }}
          animate={{ width: '280px', opacity: 1, minWidth: '280px' }}
          exit={{ width: 0, opacity: 0, minWidth: 0 }}
          transition={{ type: 'spring', stiffness: 300, damping: 30 }}
          style={{
            height: '100vh',
            background: 'var(--bg-sidebar)',
            borderRight: '1px solid var(--border-color)',
            display: 'flex',
            flexDirection: 'column',
            padding: '20px',
            boxShadow: '4px 0 30px rgba(0,0,0,0.4)',
            boxSizing: 'border-box',
            overflow: 'hidden'
          }}
        >
          {/* Top Kontroller */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
            <span style={{ fontSize: '11px', fontFamily: 'monospace', color: 'var(--text-muted)', letterSpacing: '0.05em', fontWeight: 600 }}>
              MEMORY_DASHBOARD
            </span>
            <motion.button
              whileHover={{ scale: 1.2, color: 'var(--error)' }}
              onClick={() => setIsOpen(false)}
              style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '16px' }}
              title="Göm panel"
            >
              ✕
            </motion.button>
          </div>

          {/* Ny session knapp */}
          <motion.button
            whileHover={loading ? {} : { scale: 1.02, background: 'var(--bg-accent-light)', borderColor: 'var(--accent)' }}
            whileTap={loading ? {} : { scale: 0.98 }}
            onClick={onNewChat}
            disabled={loading}
            style={{
              width: '100%',
              padding: '12px',
              marginBottom: '16px',
              background: 'transparent',
              color: 'var(--accent)',
              border: '1px dashed var(--accent)',
              borderRadius: '8px',
              fontWeight: 600,
              fontSize: '13px',
              cursor: loading ? 'not-allowed' : 'pointer',
              transition: 'opacity 0.2s',
              opacity: loading ? 0.5 : 1
            }}
          >
            + Ny session
          </motion.button>

          {/* Sökfält */}
          {!loading && (
            <input
              type="text"
              placeholder="Sök i tidigare tasks..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                width: '100%',
                padding: '10px 12px',
                marginBottom: '24px',
                background: 'var(--bg-app)',
                border: '1px solid var(--border-color)',
                borderRadius: '8px',
                color: 'var(--text-main)',
                fontSize: '13px',
                outline: 'none',
                boxSizing: 'border-box'
              }}
            />
          )}

          {/* Lista med sessioner */}
          <div
            className="hide-scrollbar"
            style={{
              flex: 1,
              overflowY: 'auto',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px',
            }}
          >
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 700, marginBottom: '6px', letterSpacing: '0.03em' }}>
              SENASTE AKTIVITETER
            </div>

            {loading ? (
              <SkeletonLoader variant="sidebar-items" />
            ) : filteredSessions.length === 0 ? (
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontStyle: 'italic', padding: '10px' }}>
                {searchTerm ? 'Inga matchande sessioner hittades' : 'Ingen historik lagrad ännu'}
              </div>
            ) : (
              <AnimatePresence>
                {filteredSessions.map((session) => {
                  const isActive = session.id === currentSessionId;
                  return (
                    <motion.div
                      key={session.id}
                      layout
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, x: -10 }}
                      whileHover={{ x: 4, background: 'var(--bg-accent-light)', color: 'var(--text-main)' }}
                      onClick={() => onSelectSession(session.id)}
                      style={{
                        padding: '12px',
                        borderRadius: '8px',
                        background: isActive ? 'var(--bg-accent-light)' : 'transparent',
                        color: isActive ? 'var(--text-main)' : 'var(--text-muted)',
                        fontSize: '13px',
                        fontWeight: isActive ? 600 : 400,
                        cursor: 'pointer',
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        border: isActive ? '1px solid var(--border-color)' : '1px solid transparent',
                        boxSizing: 'border-box'
                      }}
                    >
                      {session.title}
                    </motion.div>
                  );
                })}
              </AnimatePresence>
            )}
          </div>

          <Settings />

          {/* Rensa-knapp */}
          {!loading && sessions.length > 0 && (
            <motion.button
              whileHover={{ opacity: 1, x: 2 }}
              onClick={handlePurgeHistory}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--error)',
                fontSize: '11px',
                cursor: 'pointer',
                textAlign: 'left',
                padding: '10px 0 0 4px',
                opacity: 0.6,
                fontFamily: 'monospace'
              }}
            >
              // PURGE_ALL_HISTORY
            </motion.button>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  );
};