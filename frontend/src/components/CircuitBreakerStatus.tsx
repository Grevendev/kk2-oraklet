import React, { useState, useEffect } from 'react';
import { useToast } from '../context/ToastContext'; // 1. Importera global toast-hook

export const CircuitBreakerStatus: React.FC = () => {
  const [status, setStatus] = useState<{
    isOpen: boolean;
    message: string;
    retryAfter: number;
    initialRetryAfter: number;
  } | null>(null);

  const { showToast } = useToast(); // 2. Initiera toasten

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

      // 3. Skjut en omedelbar röd varningstoast när kaskadskyddet aktiveras
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

        // 4. PRECIS när timern slår om till noll (och komponenten blir grön), skjut en framgångstoast!
        if (nextRetry <= 0) {
          showToast('AI Pipeline Security Layer har återställts. Systemet är ONLINE.', 'success');
        }

        return { ...prev, retryAfter: nextRetry };
      });
    }, 1000);

    return () => clearTimeout(timer);
  }, [status, showToast]);

  if (!status || status.retryAfter <= 0) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '12px 16px',
        background: 'rgba(16, 185, 129, 0.03)',
        border: '1px solid rgba(16, 185, 129, 0.15)',
        borderRadius: '12px',
        fontSize: '13px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            background: '#10b981',
            boxShadow: '0 0 8px #10b981'
          }} />
          <span style={{ color: '#94a3b8', fontWeight: 500 }}>AI Pipeline Security Layer</span>
        </div>
        <span style={{ fontFamily: 'monospace', fontSize: '11px', color: '#10b981', fontWeight: 600 }}>
          STATUS // CLOSED // ONLINE
        </span>
      </div>
    );
  }

  const progressPercent = (status.retryAfter / status.initialRetryAfter) * 100;

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      gap: '12px',
      padding: '16px',
      background: 'rgba(239, 68, 68, 0.04)',
      border: '1px solid rgba(239, 68, 68, 0.25)',
      borderRadius: '12px',
      boxShadow: '0 4px 24px rgba(239, 68, 68, 0.05)'
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'space-between',
        gap: '16px',
        flexWrap: 'wrap'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{
            width: '10px',
            height: '10px',
            borderRadius: '50%',
            background: '#ef4444',
            boxShadow: '0 0 12px #ef4444',
            display: 'inline-block'
          }} />
          <span style={{ color: '#fca5a5', fontSize: '13px', fontWeight: 600, lineHeight: '1.4' }}>
            {status.message}
          </span>
        </div>

        <div style={{
          fontFamily: '"Fira Code", "Courier New", monospace',
          fontSize: '11px',
          color: '#ef4444',
          background: 'rgba(239, 68, 68, 0.1)',
          padding: '2px 8px',
          borderRadius: '4px',
          fontWeight: 600,
          letterSpacing: '0.02em'
        }}>
          ISOLATED // RETRY_IN_{status.retryAfter}S
        </div>
      </div>

      <p style={{ color: '#94a3b8', fontSize: '13px', margin: 0, lineHeight: '1.5' }}>
        Tjänsten har tillfälligt brutit strömmen till AI-kedjan för att förhindra kaskadfel och skydda CPU-resurser. Automatisk återanslutning pågår.
      </p>

      <div style={{
        width: '100%',
        height: '4px',
        background: 'rgba(255, 255, 255, 0.03)',
        borderRadius: '2px',
        overflow: 'hidden',
        marginTop: '4px'
      }}>
        <div style={{
          width: `${progressPercent}%`,
          height: '100%',
          background: 'linear-gradient(to right, #ef4444, #f43f5e)',
          borderRadius: '2px',
          transition: 'width 1s linear'
        }} />
      </div>
    </div>
  );
};