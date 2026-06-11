import React, { createContext, useContext, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion'; // Importera Framer Motion

type ToastType = 'success' | 'error' | 'info';

interface Toast {
  id: string;
  message: string;
  type: ToastType;
}

interface ToastContextType {
  showToast: (message: string, type?: ToastType) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);
// eslint-disable-next-line react-refresh/only-export-components
export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) throw new Error('useToast måste användas inom en ToastProvider');
  return context;
};

export const ToastProvider: React.FC<{ children: React.ReactNode; }> = ({ children }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const showToast = useCallback((message: string, type: ToastType = 'info') => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, message, type }]);

    setTimeout(() => {
      setToasts((prev) => prev.filter((toast) => toast.id !== id));
    }, 4000);
  }, []);

  const getToastStyles = (type: ToastType) => {
    switch (type) {
      case 'success':
        return {
          background: 'rgba(16, 185, 129, 0.08)',
          border: '1px solid rgba(16, 185, 129, 0.3)',
          color: '#a7f3d0',
          boxShadow: '0 8px 32px rgba(16, 185, 129, 0.08)',
          glowColor: '#10b981',
          tag: 'SUCCESS'
        };
      case 'error':
        return {
          background: 'rgba(239, 68, 68, 0.08)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          color: '#fca5a5',
          boxShadow: '0 8px 32px rgba(239, 68, 68, 0.08)',
          glowColor: '#ef4444',
          tag: 'CRITICAL'
        };
      case 'info':
      default:
        return {
          background: 'rgba(56, 189, 248, 0.06)',
          border: '1px solid rgba(56, 189, 248, 0.25)',
          color: '#e0f2fe',
          boxShadow: '0 8px 32px rgba(56, 189, 248, 0.06)',
          glowColor: '#38bdf8',
          tag: 'TELEMETRY'
        };
    }
  };

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}

      <div style={{
        position: 'fixed',
        bottom: '24px',
        right: '24px',
        zIndex: 9999,
        display: 'flex',
        flexDirection: 'column',
        gap: '10px',
        pointerEvents: 'none'
      }}>
        {/* AnimatePresence krävs för att animera element som tas bort från DOM:en */}
        <AnimatePresence mode="popLayout">
          {toasts.map((toast) => {
            const styles = getToastStyles(toast.type);

            return (
              <motion.div
                key={toast.id}
                layout // Gör att elementen nedanför flyttar sig glidande när ett element tas bort
                initial={{ opacity: 0, y: 20, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -10, scale: 0.95 }}
                transition={{
                  type: 'spring',
                  stiffness: 350,
                  damping: 30
                }}
                style={{
                  pointerEvents: 'auto',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px',
                  width: '320px',
                  padding: '14px 16px',
                  background: styles.background,
                  backdropFilter: 'blur(12px)',
                  border: styles.border,
                  borderRadius: '10px',
                  color: styles.color,
                  boxShadow: styles.boxShadow,
                  fontFamily: 'sans-serif',
                  fontSize: '13px',
                  lineHeight: '1.4'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{
                      width: '6px',
                      height: '6px',
                      borderRadius: '50%',
                      background: styles.glowColor,
                      boxShadow: `0 0 6px ${styles.glowColor}`
                    }} />
                    <span style={{
                      fontFamily: 'monospace',
                      fontSize: '10px',
                      fontWeight: 700,
                      color: styles.glowColor,
                      letterSpacing: '0.05em'
                    }}>
                      SYSTEM // {styles.tag}
                    </span>
                  </div>

                  <button
                    onClick={() => setToasts((prev) => prev.filter((t) => t.id !== toast.id))}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: styles.color,
                      cursor: 'pointer',
                      fontSize: '11px',
                      opacity: 0.4,
                      padding: 0
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.opacity = '1')}
                    onMouseLeave={(e) => (e.currentTarget.style.opacity = '0.4')}
                  >
                    ✕
                  </button>
                </div>

                <div style={{ color: '#e2e8f0', fontWeight: 500 }}>
                  {toast.message}
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
};