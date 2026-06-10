import React from 'react';

export const OracleBrandIdentity: React.FC = () => {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '12px',
      userSelect: 'none'
    }}>
      {/* Abstrakt Monolit / Kvant-ikon */}
      <div style={{
        position: 'relative',
        width: '28px',
        height: '28px',
        background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
        borderRadius: '8px',
        transform: 'rotate(45deg)',
        boxShadow: '0 0 16px rgba(16, 185, 129, 0.25)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        {/* Inre glödande kärna */}
        <div style={{
          width: '10px',
          height: '10px',
          background: '#020617',
          borderRadius: '3px',
          transform: 'rotate(-45deg)'
        }} />
      </div>

      {/* Premium Typografi */}
      <div style={{ display: 'flex', flexDirection: 'column', lineHeight: '1' }}>
        <span style={{
          fontSize: '18px',
          fontWeight: 800,
          letterSpacing: '0.08em',
          color: '#f8fafc',
          fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
        }}>
          ORACLE<span style={{ color: '#10b981' }}>.</span>CORE
        </span>
        <span style={{
          fontSize: '9px',
          fontFamily: 'monospace',
          color: '#475569',
          letterSpacing: '0.18em',
          marginTop: '3px',
          textTransform: 'uppercase'
        }}>
          Neural Ingestion v1.0
        </span>
      </div>
    </div>
  );
};