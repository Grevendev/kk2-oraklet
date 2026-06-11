import React from 'react';

interface SkeletonLoaderProps {
  variant?: 'default' | 'dashboard-stats' | 'ai-chat';
}

export const SkeletonLoader: React.FC<SkeletonLoaderProps> = ({ variant = 'default' }) => {
  const injectStyle = (
    <style>{`
      @keyframes pulse {
        0% { opacity: 0.3; }
        50% { opacity: 0.7; }
        100% { opacity: 0.3; }
      }
      .pulse-element {
        animation: pulse 1.6s infinite ease-in-out;
      }
    `}</style>
  );

  if (variant === 'ai-chat') {
    return (
      <div className="pulse-element" style={{
        background: 'rgba(255, 255, 255, 0.01)',
        border: '1px solid rgba(255, 255, 255, 0.03)',
        borderRadius: '12px',
        padding: '16px',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
        marginBottom: '20px'
      }}>
        {injectStyle}

        {/* Användarens fråga (Platshållare) */}
        <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
          <div style={{ height: '14px', width: '45px', background: 'rgba(56, 189, 248, 0.2)', borderRadius: '4px' }} />
          <div style={{ height: '14px', width: '40%', background: 'rgba(226, 232, 240, 0.05)', borderRadius: '4px' }} />
        </div>

        {/* Oraklets svar (Grönaktig pulserande box) */}
        <div style={{
          background: 'rgba(16, 185, 129, 0.02)',
          padding: '14px',
          borderRadius: '10px',
          border: '1px solid rgba(16, 185, 129, 0.05)',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px'
        }}>
          <div style={{ height: '14px', width: '60px', background: 'rgba(16, 185, 129, 0.2)', borderRadius: '4px' }} />
          <div style={{ height: '12px', width: '90%', background: 'rgba(16, 185, 129, 0.04)', borderRadius: '4px' }} />
          <div style={{ height: '12px', width: '75%', background: 'rgba(16, 185, 129, 0.04)', borderRadius: '4px' }} />
        </div>

        {/* Kedjans interna resonemang (Mörk streckad box) */}
        <div style={{
          background: '#020617',
          border: '1px dashed rgba(255, 255, 255, 0.03)',
          padding: '12px',
          borderRadius: '8px',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px'
        }}>
          <div style={{ height: '10px', width: '150px', background: 'rgba(71, 85, 105, 0.2)', borderRadius: '4px' }} />
          <div style={{ height: '10px', width: '85%', background: 'rgba(255, 255, 255, 0.02)', borderRadius: '4px' }} />
        </div>
      </div>
    );
  }

  if (variant === 'dashboard-stats') {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', width: '100%' }}>
        {injectStyle}
        <div style={{
          background: '#020617',
          border: '1px solid rgba(255, 255, 255, 0.04)',
          borderRadius: '12px',
          padding: '20px 16px',
          boxShadow: '0 4px 20px rgba(0,0,0,0.2)',
          height: '270px',
          boxSizing: 'border-box',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between'
        }}>
          <div className="pulse-element" style={{ height: '10px', width: '180px', background: 'rgba(255,255,255,0.04)', borderRadius: '4px' }} />
          <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-around', height: '180px', padding: '0 10px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
            <div className="pulse-element" style={{ height: '60%', width: '30px', background: 'rgba(56, 189, 248, 0.05)', borderRadius: '4px 4px 0 0' }} />
            <div className="pulse-element" style={{ height: '40%', width: '30px', background: 'rgba(71, 85, 105, 0.05)', borderRadius: '4px 4px 0 0' }} />
            <div className="pulse-element" style={{ height: '85%', width: '30px', background: 'rgba(168, 85, 247, 0.05)', borderRadius: '4px 4px 0 0' }} />
            <div className="pulse-element" style={{ height: '45%', width: '30px', background: 'rgba(56, 189, 248, 0.05)', borderRadius: '4px 4px 0 0' }} />
            <div className="pulse-element" style={{ height: '70%', width: '30px', background: 'rgba(71, 85, 105, 0.05)', borderRadius: '4px 4px 0 0' }} />
            <div className="pulse-element" style={{ height: '30%', width: '30px', background: 'rgba(168, 85, 247, 0.05)', borderRadius: '4px 4px 0 0' }} />
          </div>
        </div>

        <div style={{
          background: '#020617',
          border: '1px solid rgba(255, 255, 255, 0.04)',
          borderRadius: '12px',
          overflow: 'hidden',
          height: '140px'
        }}>
          <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '10px 16px', borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
            <div className="pulse-element" style={{ height: '10px', width: '140px', background: 'rgba(255,255,255,0.04)', borderRadius: '4px' }} />
          </div>
          <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div className="pulse-element" style={{ height: '12px', width: '85%', background: 'rgba(52, 211, 153, 0.04)', borderRadius: '4px' }} />
            <div className="pulse-element" style={{ height: '12px', width: '60%', background: 'rgba(52, 211, 153, 0.04)', borderRadius: '4px' }} />
            <div className="pulse-element" style={{ height: '12px', width: '75%', background: 'rgba(52, 211, 153, 0.04)', borderRadius: '4px' }} />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      gap: '12px',
      padding: '16px',
      background: 'rgba(255, 255, 255, 0.02)',
      borderRadius: '12px',
      border: '1px solid rgba(255, 255, 255, 0.05)'
    }}>
      {injectStyle}
      <div className="pulse-element" style={{ height: '20px', width: '40%', background: 'rgba(255,255,255,0.05)', borderRadius: '4px' }} />
      <div className="pulse-element" style={{ height: '150px', width: '100%', background: 'rgba(255,255,255,0.05)', borderRadius: '8px' }} />
    </div>
  );
};