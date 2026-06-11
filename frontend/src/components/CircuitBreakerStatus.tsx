import React, { useState, useEffect } from 'react';
import { useToast } from '../context/ToastContext';
import { motion, AnimatePresence } from 'framer-motion'; // Importera Framer Motion

export const CircuitBreakerStatus: React.FC = () => {
  const [status, setStatus] = useState<{
    isOpen: boolean;
    message: string;
    retryAfter: number;
    initialRetryAfter: number;
  } | null>(null);

  const { showToast } = useToast();

  useEffect(() => {
    const handleTriggered = (event: Event) => {
      const customEvent = event as CustomEvent;
      const retry = customEvent.detail.retryAfter || 10;
      const triggerMessage = customEvent.detail.message || 'Systemets säkring har löst ut (Circuit Breaker OPEN).';

      setStatus({
        isOpen: true,
        message: triggerMessage,
        retryAfter: retry,
        initialRetryAfter: retry
      });

      showToast(`Kritisk incident: AI-säkringen har löst ut. Pipeline isolerad.`, 'error');
    };

    window.addEventListener('circuit-breaker-triggered', handleTriggered);
    return () => window.removeEventListener('circuit-breaker-triggered', handleTriggered);
  }, [showToast]);

  // Räkna ner timern varje sekund om den är öppen
  useEffect(() => {
    if (!status || status.retryAfter <= 0) return;

    const timer = setTimeout(() => {
      setStatus(prev => {
        if (!prev) return null;

        const nextRetry = prev.retryAfter - 1;

        if (nextRetry <= 0) {
          showToast('AI Pipeline Security Layer har återställts. Systemet är ONLINE.', 'success');
        }

        return { ...prev, retryAfter: nextRetry };
      });
    }, 1000);

    return () => clearTimeout(timer);
  }, [status, showToast]);

  const isOnline = !status || status.retryAfter <= 0;
  const progressPercent = status ? (status.retryAfter / status.initialRetryAfter) * 100 : 0;

  return (
    // motion.div med layout ser till att omgivande element flyttar sig mjukt vid storleksförändring
    <motion.div layout transition={{ type: 'spring', stiffness: 300, damping: 30 }}>
      <AnimatePresence mode="wait">
        {isOnline ? (
          /* ================= ONLINE / CLOSED LÄGE ================= */
          <motion.div
            key="online-status"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '12px 16px',
              background: 'rgba(16, 185, 129, 0.03)',
              border: '1px solid rgba(16, 185, 129, 0.15)',
              borderRadius: '12px',
              fontSize: '13px',
              boxSizing: 'border-box'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              {/* Pulserande grön LED-glöd */}
              <motion.span
                animate={{ opacity: [0.5, 1, 0.5], scale: [0.95, 1.05, 0.95] }}
                transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
                style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  background: '#10b981',
                  boxShadow: '0 0 8px #10b981'
                }}
              />
              <span style={{ color: '#94a3b8', fontWeight: 500 }}>AI Pipeline Security Layer</span>
            </div>
            <span style={{ fontFamily: 'monospace', fontSize: '11px', color: '#10b981', fontWeight: 600 }}>
              STATUS // CLOSED // ONLINE
            </span>
          </motion.div>
        ) : (
          /* ================= ISOLERAT / TRIPPAT LÄGE ================= */
          <motion.div
            key="isolated-status"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '12px',
              padding: '16px',
              background: 'rgba(239, 68, 68, 0.04)',
              border: '1px solid rgba(239, 68, 68, 0.25)',
              borderRadius: '12px',
              boxShadow: '0 4px 24px rgba(239, 68, 68, 0.05)',
              boxSizing: 'border-box'
            }}
          >
            <div style={{
              display: 'flex',
              alignItems: 'flex-start',
              justifyContent: 'space-between',
              gap: '16px',
              flexWrap: 'wrap'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                {/* Intensivt pulserande röd varnings-LED */}
                <motion.span
                  animate={{ opacity: [0.4, 1, 0.4], scale: [0.9, 1.1, 0.9] }}
                  transition={{ repeat: Infinity, duration: 1.2, ease: "easeInOut" }}
                  style={{
                    width: '10px',
                    height: '10px',
                    borderRadius: '50%',
                    background: '#ef4444',
                    boxShadow: '0 0 12px #ef4444',
                    display: 'inline-block'
                  }}
                />
                <span style={{ color: '#fca5a5', fontSize: '13px', fontWeight: 600, lineHeight: '1.4' }}>
                  {status.message}
                </span>
              </div>

              {/* Nedräkningstext med en mjuk layout-fjäder för sifferbyten */}
              <motion.div
                layoutId="retry-badge"
                style={{
                  fontFamily: '"Fira Code", "Courier New", monospace',
                  fontSize: '11px',
                  color: '#ef4444',
                  background: 'rgba(239, 68, 68, 0.1)',
                  padding: '2px 8px',
                  borderRadius: '4px',
                  fontWeight: 600,
                  letterSpacing: '0.02em'
                }}
              >
                ISOLATED // RETRY_IN_{status.retryAfter}S
              </motion.div>
            </div>

            <p style={{ color: '#94a3b8', fontSize: '13px', margin: 0, lineHeight: '1.5' }}>
              Tjänsten har tillfälligt brutit strömmen till AI-kedjan för att förhindra kaskadfel och skydda CPU-resurser. Automatisk återanslutning pågår.
            </p>

            {/* Progress bar behållare */}
            <div style={{
              width: '100%',
              height: '4px',
              background: 'rgba(255, 255, 255, 0.03)',
              borderRadius: '2px',
              overflow: 'hidden',
              marginTop: '4px'
            }}>
              {/* Progress bar fyllning styrd via Framer Motion för helt ryckfri interpolation */}
              <motion.div
                initial={{ width: '100%' }}
                animate={{ width: `${progressPercent}%` }}
                transition={{ duration: 1, ease: 'linear' }}
                style={{
                  height: '100%',
                  background: 'linear-gradient(to right, #ef4444, #f43f5e)',
                  borderRadius: '2px'
                }}
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};