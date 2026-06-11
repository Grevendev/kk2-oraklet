import React, { useState, useEffect } from 'react';
import { useToast } from '../context/ToastContext';
import { motion, AnimatePresence } from 'framer-motion';

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
    <motion.div layout transition={{ type: 'spring', stiffness: 300, damping: 30 }}>
      <AnimatePresence mode="wait">
        {isOnline ? (
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
              background: 'var(--bg-card)',
              border: '1px solid var(--border-color)',
              borderRadius: '12px',
              fontSize: '13px',
              boxSizing: 'border-box'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <motion.span
                animate={{ opacity: [0.5, 1, 0.5], scale: [0.95, 1.05, 0.95] }}
                transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
                style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  background: 'var(--success)',
                  boxShadow: '0 0 8px var(--success)'
                }}
              />
              <span style={{ color: 'var(--text-muted)', fontWeight: 500 }}>AI Pipeline Security Layer</span>
            </div>
            <span style={{ fontFamily: 'monospace', fontSize: '11px', color: 'var(--success)', fontWeight: 600 }}>
              STATUS // CLOSED // ONLINE
            </span>
          </motion.div>
        ) : (
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
              background: 'var(--bg-card)',
              border: '1px solid var(--error)',
              borderRadius: '12px',
              boxSizing: 'border-box'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '16px', flexWrap: 'wrap' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <motion.span
                  animate={{ opacity: [0.4, 1, 0.4], scale: [0.9, 1.1, 0.9] }}
                  transition={{ repeat: Infinity, duration: 1.2, ease: "easeInOut" }}
                  style={{
                    width: '10px',
                    height: '10px',
                    borderRadius: '50%',
                    background: 'var(--error)',
                    boxShadow: '0 0 12px var(--error)',
                    display: 'inline-block'
                  }}
                />
                <span style={{ color: 'var(--error)', fontSize: '13px', fontWeight: 600, lineHeight: '1.4' }}>
                  {status.message}
                </span>
              </div>
              <motion.div
                layoutId="retry-badge"
                style={{
                  fontFamily: 'monospace',
                  fontSize: '11px',
                  color: 'var(--error)',
                  background: 'rgba(239, 68, 68, 0.1)',
                  padding: '2px 8px',
                  borderRadius: '4px',
                  fontWeight: 600
                }}
              >
                ISOLATED // RETRY_IN_{status.retryAfter}S
              </motion.div>
            </div>

            <p style={{ color: 'var(--text-muted)', fontSize: '13px', margin: 0, lineHeight: '1.5' }}>
              Tjänsten har tillfälligt brutit strömmen till AI-kedjan för att skydda systemresurser.
            </p>

            <div style={{ width: '100%', height: '4px', background: 'var(--bg-app)', borderRadius: '2px', overflow: 'hidden', marginTop: '4px' }}>
              <motion.div
                initial={{ width: '100%' }}
                animate={{ width: `${progressPercent}%` }}
                transition={{ duration: 1, ease: 'linear' }}
                style={{ height: '100%', background: 'var(--error)', borderRadius: '2px' }}
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};