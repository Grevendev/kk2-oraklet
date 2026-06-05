import React, { useState, useEffect } from 'react';

export const CircuitBreakerStatus: React.FC = () => {
  const [status, setStatus] = useState<{ isOpen: boolean; message: string; retryAfter: number; } | null>(null);

  useEffect(() => {
    const handleTriggered = (event: Event) => {
      const customEvent = event as CustomEvent;
      setStatus({
        isOpen: true,
        message: customEvent.detail.message || 'Systemets säkring har löst ut (Circuit Breaker OPEN).',
        retryAfter: customEvent.detail.retryAfter
      });
    };

    window.addEventListener('circuit-breaker-triggered', handleTriggered);
    return () => window.removeEventListener('circuit-breaker-triggered', handleTriggered);
  }, []);

  // Räkna ner timern varje sekund om den är öppen
  useEffect(() => {
    if (!status || status.retryAfter <= 0) return;

    const timer = setTimeout(() => {
      setStatus(prev => prev ? { ...prev, retryAfter: prev.retryAfter - 1 } : null);
    }, 1000);

    return () => clearTimeout(timer);
  }, [status]);

  if (!status || status.retryAfter <= 0) return null;

  return (
    <div style={{
      padding: '15px',
      background: '#fff7ed',
      border: '1px solid #ea580c',
      color: '#c2410c',
      borderRadius: '8px',
      marginBottom: '20px',
      fontSize: '14px'
    }}>
      <strong>⚠️ {status.message}</strong>
      <br />
      Tjänsten är tillfälligt isolerad för att skydda systemet. Försök igen om <strong>{status.retryAfter}</strong> sekunder.
    </div>
  );
};