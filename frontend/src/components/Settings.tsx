// src/components/Settings.tsx
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '../context/ThemeContext';

export const Settings: React.FC = () => {
  const [expanded, setExpanded] = useState(false);
  const { theme, toggleTheme } = useTheme();

  return (
    <div style={{
      borderTop: '1px solid var(--border-color)',
      marginTop: '16px',
      paddingTop: '12px'
    }}>
      {/* Inställningar Huvudknapp */}
      <motion.button
        onClick={() => setExpanded(!expanded)}
        whileHover={{ scale: 1.02, background: 'rgba(255,255,255,0.02)' }}
        whileTap={{ scale: 0.98 }}
        style={{
          width: '100%',
          padding: '10px 12px',
          background: 'transparent',
          border: 'none',
          borderRadius: '8px',
          color: 'var(--text-main)',
          fontSize: '13px',
          fontWeight: 500,
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          outline: 'none'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span>⚙️</span> Inställningar
        </div>
        <motion.span
          animate={{ rotate: expanded ? 90 : 0 }}
          transition={{ type: 'spring', stiffness: 200 }}
          style={{ fontSize: '11px', opacity: 0.5 }}
        >
          ▶
        </motion.span>
      </motion.button>

      {/* Expanderbar panel med inställningsval */}
      <AnimatePresence initial={false}>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 300, damping: 25 }}
            style={{ overflow: 'hidden' }}
          >
            <div style={{ padding: '12px 12px 4px 12px', display: 'flex', flexDirection: 'column', gap: '14px' }}>

              {/* Rad för Dark / Light Mode Switch */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 500 }}>
                  App-tema ({theme === 'dark' ? 'Mörkt' : 'Ljust'})
                </span>

                {/* Lyxig iOS/Cyber-style Switch */}
                <div
                  onClick={toggleTheme}
                  style={{
                    width: '44px',
                    height: '24px',
                    background: theme === 'dark' ? '#38bdf8' : '#cbd5e1',
                    borderRadius: '12px',
                    padding: '2px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: theme === 'dark' ? 'flex-end' : 'flex-start',
                    boxShadow: 'inset 0 1px 3px rgba(0,0,0,0.2)',
                    transition: 'background-color 0.2s ease'
                  }}
                >
                  <motion.div
                    layout
                    transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                    style={{
                      width: '20px',
                      height: '20px',
                      borderRadius: '50%',
                      background: '#ffffff',
                      boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '11px'
                    }}
                  >
                    {theme === 'dark' ? '🌙' : '☀️'}
                  </motion.div>
                </div>
              </div>

              {/* Exempel på framtida inställningsval */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', opacity: 0.4 }}>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Ljudinställningar</span>
                <span style={{ fontSize: '11px', fontFamily: 'monospace' }}>OFF</span>
              </div>

            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};