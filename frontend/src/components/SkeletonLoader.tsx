import React from 'react';

export const SkeletonLoader: React.FC = () => (
  <div style={{
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
    padding: '16px',
    background: 'rgba(255, 255, 255, 0.02)',
    borderRadius: '12px',
    border: '1px solid rgba(255, 255, 255, 0.05)'
  }}>
    <div style={{ height: '20px', width: '40%', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', animation: 'pulse 1.5s infinite' }} />
    <div style={{ height: '150px', width: '100%', background: 'rgba(255,255,255,0.05)', borderRadius: '8px', animation: 'pulse 1.5s infinite' }} />

    <style>{`
      @keyframes pulse {
        0% { opacity: 0.4; }
        50% { opacity: 0.8; }
        100% { opacity: 0.4; }
      }
    `}</style>
  </div>
);