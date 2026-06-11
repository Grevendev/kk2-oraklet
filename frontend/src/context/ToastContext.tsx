import React, { createContext, useContext, useState, useCallback } from 'react';

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

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast måste användas inom en ToastProvider');
  }
  return context;
};

export const ToastProvider: React.FC<{ children: React.ReactNode; }> = ({ children }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const showToast = useCallback((message: string, type: ToastType = 'info') => {
    const id = Math.random().toString(36).substring(2, 9);

    setToasts((prev) => [...prev, { id, message, type }]);

    // Ta bort toasten automatiskt efter 4 sekunder
    setTimeout(() => {
      setToasts((prev) => prev.filter((toast) => toast.id !== id));
    }, 4000);
  }, []);

  // Stilkonfigurationer baserat på din premium-palett
  const getToastStyles = (type: ToastType) => {
    switch (type) {
      case 'success':
        return {
          background: 'rgba(16, 185, 129, 0.08)', // Väldigt dämpad grön
          border: '1px solid rgba(16, 185, 129, 0.3)',
          color: '#a7f3d0',
          boxShadow: '0 8px 32px rgba(16, 185, 129, 0.08)',
          glowColor: '#10b981',
          tag: 'SUCCESS'
        };
      case 'error':
        return {
          background: 'rgba(239, 68, 68, 0.08)', // Väldigt dämpad röd
          border: '1px solid rgba(239, 68, 68, 0.3)',
          color: '#fca5a5',
          boxShadow: '0 8px 32px rgba(239, 68, 68, 0.08)',
          glowColor: '#ef4444',
          tag: 'CRITICAL'
        };
      case 'info':
      default:
        return {
          background: 'rgba(56, 189, 248, 0.06)', // Väldigt dämpad neonblå
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

      {/* Toast Container - Stackar notifieringar i nedre högra hörnet */}
      <div style={{
        position: 'fixed',
        bottom: '24px',
        right: '24px',
        zIndex: 9999,
        display: 'flex',
        flexDirection: 'column',
        gap: '10px',
        pointerEvents: 'none' // Hindrar inte klick på bakomliggande element när de tonar ut
      }}>
        {toasts.map((toast) => {
          const styles = getToastStyles(toast.type);

          return (
            <div
              key={toast.id}
              style={{
                pointerEvents: 'auto', // Aktiverar klick igen för själva toasten om man vill stänga den
                display: 'flex',
                flexDirection: 'column',
                gap: '6px',
                width: '320px',
                padding: '14px 16px',
                background: styles.background,
                backdropFilter: 'blur(12px)', // Lyxig glas-effekt mot bakgrunden
                border: styles.border,
                borderRadius: '10px',
                color: styles.color,
                boxShadow: styles.boxShadow,
                fontFamily: 'sans-serif',
                fontSize: '13px',
                lineHeight: '1.4',
                animation: 'toastFadeIn 0.25s cubic-bezier(0.16, 1, 0.3, 1) forwards',
                transition: 'all 0.2s ease'
              }}
            >
              {/* Övre raden: Telemetri-etikett och statuslampa */}
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

              {/* Meddelandetext */}
              <div style={{ color: '#e2e8f0', fontWeight: 500 }}>
                {toast.message}
              </div>
            </div>
          );
        })}
      </div>

      {/* Global injicering av keyframe-animationer för mjuk infasning */}
      <style>{`
        @keyframes toastFadeIn {
          from {
            opacity: 0;
            transform: translateY(12px) scale(0.98);
          }
          to {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }
      `}</style>
    </ToastContext.Provider>
  );
};