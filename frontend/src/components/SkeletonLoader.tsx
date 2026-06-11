// src/components/SkeletonLoader.tsx
import React from 'react';

interface SkeletonLoaderProps {
  variant?: 'default' | 'dashboard-stats' | 'ai-chat' | 'sidebar-items' | 'uploader-progress';
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

  // Variant 1: Sidomeny/Historik
  if (variant === 'sidebar-items') {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', width: '100%' }}>
        {injectStyle}
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="pulse-element" style={{
            height: '38px',
            width: '100%',
            background: 'var(--bg-accent-light)',
            border: '1px solid var(--border-color)',
            borderRadius: '8px',
            padding: '0 12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            boxSizing: 'border-box'
          }}>
            <div style={{ height: '10px', width: '65%', background: 'var(--border-color)', borderRadius: '3px' }} />
            <div style={{ height: '8px', width: '20%', background: 'var(--border-color)', borderRadius: '2px' }} />
          </div>
        ))}
      </div>
    );
  }

  // Variant 2: Uploader progress
  if (variant === 'uploader-progress') {
    return (
      <div className="pulse-element" style={{
        background: 'var(--bg-card)',
        padding: '24px',
        borderRadius: '16px',
        border: '1px solid var(--border-color)',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
        width: '100%',
        boxSizing: 'border-box'
      }}>
        {injectStyle}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--text-muted)' }} />
          <div style={{ height: '12px', width: '160px', background: 'var(--border-color)', borderRadius: '4px' }} />
        </div>
        <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
          <div style={{ height: '14px', width: '100px', background: 'var(--border-color)', borderRadius: '4px' }} />
          <div style={{ display: 'flex', gap: '6px' }}>
            <div style={{ height: '20px', width: '50px', background: 'var(--border-color)', borderRadius: '4px' }} />
            <div style={{ height: '20px', width: '60px', background: 'var(--border-color)', borderRadius: '4px' }} />
          </div>
        </div>
      </div>
    );
  }

  // Variant 3: AI Chat
  if (variant === 'ai-chat') {
    return (
      <div className="pulse-element" style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border-color)',
        borderRadius: '12px',
        padding: '16px',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
        marginBottom: '20px'
      }}>
        {injectStyle}
        <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
          <div style={{ height: '14px', width: '45px', background: 'var(--accent)', borderRadius: '4px' }} />
          <div style={{ height: '14px', width: '40%', background: 'var(--border-color)', borderRadius: '4px' }} />
        </div>
        <div style={{
          background: 'var(--bg-accent-light)',
          padding: '14px',
          borderRadius: '10px',
          border: '1px solid var(--border-color)',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px'
        }}>
          <div style={{ height: '14px', width: '60px', background: 'var(--accent)', borderRadius: '4px' }} />
          <div style={{ height: '12px', width: '90%', background: 'var(--border-color)', borderRadius: '4px' }} />
          <div style={{ height: '12px', width: '75%', background: 'var(--border-color)', borderRadius: '4px' }} />
        </div>
      </div>
    );
  }

  // Variant 4: Dashboard stats
  if (variant === 'dashboard-stats') {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', width: '100%' }}>
        {injectStyle}
        <div style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-color)',
          borderRadius: '12px',
          padding: '20px 16px',
          height: '270px',
          boxSizing: 'border-box',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between'
        }}>
          <div className="pulse-element" style={{ height: '10px', width: '180px', background: 'var(--border-color)', borderRadius: '4px' }} />
          <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-around', height: '180px', padding: '0 10px', borderBottom: '1px solid var(--border-color)' }}>
            {[60, 40, 85, 45, 70, 30].map((h, i) => (
              <div key={i} className="pulse-element" style={{ height: `${h}%`, width: '30px', background: 'var(--accent)', borderRadius: '4px 4px 0 0', opacity: 0.2 }} />
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Default
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      gap: '12px',
      padding: '16px',
      background: 'var(--bg-card)',
      borderRadius: '12px',
      border: '1px solid var(--border-color)'
    }}>
      {injectStyle}
      <div className="pulse-element" style={{ height: '20px', width: '40%', background: 'var(--border-color)', borderRadius: '4px' }} />
      <div className="pulse-element" style={{ height: '150px', width: '100%', background: 'var(--border-color)', borderRadius: '8px' }} />
    </div>
  );
};