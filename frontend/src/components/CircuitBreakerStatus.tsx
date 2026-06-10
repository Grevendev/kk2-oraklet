import React, { useState, useEffect } from 'react';

export const CircuitBreakerStatus: React.FC = () => {
  const [status, setStatus] = useState<{
    isOpen: boolean;
    message: string;
    retryAfter: number;
    initialRetryAfter: number; // Sparar startvärdet för att kunna räkna ut procent till progress baren
  } | null>(null);

  useEffect(() => {
    const handleTriggered = (event: Event) => {
      const customEvent = event as CustomEvent;
      const retry = customEvent.detail.retryAfter || 10;
      setStatus({
        isOpen: true,
        message: customEvent.detail.message || 'Systemets säkring har löst ut (Circuit Breaker OPEN).',
        retryAfter: retry,
        initialRetryAfter: retry
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

  // Om allt är grönt (stängt), visar vi en diskret, lyxig och stabil systemstatus istället för ingenting alls!
  if (!status || status.retryAfter <= 0) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '12px 16px',
        background: 'rgba(16, 185, 129, 0.03)', // Extremt dämpad grön glöd
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

  // Räkna ut hur många procent av återhämtningen som återstår
  const progressPercent = (status.retryAfter / status.initialRetryAfter) * 100;

  // SYSTEM TRIPPAT: Visar den lyxiga, strömlinjeformade kris-indikatorn
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      gap: '12px',
      padding: '16px',
      background: 'rgba(239, 68, 68, 0.04)', // Lyxig mörkröd transparent botten
      border: '1px solid rgba(239, 68, 68, 0.25)', // Tydlig men mjuk röd glöd-kant
      borderRadius: '12px',
      boxShadow: '0 4px 24px rgba(239, 68, 68, 0.05)'
    }}>

      {/* Övre raden: Meddelande och pulserande status */}
      <div style={{
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'space-between',
        gap: '16px',
        flexWrap: 'wrap'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {/* Pulserande röd varningslampa */}
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

        {/* Monospace Countdown */}
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

      {/* Undre raden: Förklarande text */}
      <p style={{ color: '#94a3b8', fontSize: '13px', margin: 0, lineHeight: '1.5' }}>
        Tjänsten har tillfälligt brutit strömmen till AI-kedjan för att förhindra kaskadfel och skydda CPU-resurser. Automatisk återanslutning pågår.
      </p>

      {/* Premium Framstegsindikator (Progress bar) */}
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
          transition: 'width 1s linear' // Ger en mjuk, rullande nedräkningseffekt i animationen
        }} />
      </div>
    </div>
  );
};