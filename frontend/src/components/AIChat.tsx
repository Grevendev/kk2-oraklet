import React, { useState } from 'react';
import { dataApi } from '../api/endpoints';
import { AIResponse } from '../types';

export const AIChat: React.FC = () => {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [chatHistory, setChatHistory] = useState<AIResponse[]>([]);

  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const result = await dataApi.askAI(question);
      setChatHistory(prev => [result, ...prev]);
      setQuestion('');
    } catch (err: any) {
      const backendMessage = err.response?.data?.message || 'Kunde inte kommunicera med Oraklet.';
      setError(backendMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header-sektion */}
      <div style={{ marginBottom: '20px' }}>
        <h2 style={{
          marginTop: 0,
          fontSize: '20px',
          fontWeight: 600,
          letterSpacing: '-0.02em',
          color: '#f8fafc'
        }}>
          3. Query Engine Interactivity
        </h2>
        <p style={{ color: '#64748b', fontSize: '13px', lineHeight: '1.5', margin: 0 }}>
          Ställ frågor om ditt uppladdade dataset. AI-kedjan exekveras med strikt <span style={{ color: '#10b981', fontFamily: 'monospace' }}>PromptBuilder</span> och <span style={{ color: '#10b981', fontFamily: 'monospace' }}>ResponseParser</span>-validering.
        </p>
      </div>

      {/* Sök/Frågeformulär */}
      <form onSubmit={handleAsk} style={{ display: 'flex', gap: '12px', marginBottom: '24px' }}>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="T.ex. Berätta om datasetet..."
          disabled={loading}
          style={{
            flex: 1,
            padding: '12px 16px',
            borderRadius: '10px',
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            color: '#f8fafc',
            fontSize: '14px',
            outline: 'none',
            transition: 'all 0.2s ease',
            boxShadow: 'inset 0 2px 4px rgba(0, 0, 0, 0.2)'
          }}
          onFocus={(e) => {
            e.currentTarget.style.borderColor = 'rgba(16, 185, 129, 0.3)';
            e.currentTarget.style.boxShadow = '0 0 10px rgba(16, 185, 129, 0.05), inset 0 2px 4px rgba(0, 0, 0, 0.2)';
          }}
          onBlur={(e) => {
            e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.08)';
          }}
        />
        <button
          type="submit"
          disabled={loading}
          style={{
            padding: '12px 24px',
            background: loading ? '#1e293b' : 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
            color: '#fff',
            fontWeight: 600,
            fontSize: '14px',
            border: 'none',
            borderRadius: '10px',
            cursor: loading ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s ease',
            boxShadow: loading ? 'none' : '0 4px 12px rgba(16, 185, 129, 0.2)'
          }}
          onMouseEnter={(e) => {
            if (!loading) e.currentTarget.style.boxShadow = '0 4px 20px rgba(16, 185, 129, 0.4)';
          }}
          onMouseLeave={(e) => {
            if (!loading) e.currentTarget.style.boxShadow = '0 4px 12px rgba(16, 185, 129, 0.2)';
          }}
        >
          {loading ? 'Tänker...' : 'Fråga'}
        </button>
      </form>

      {/* Pipeline Felhantering */}
      {error && (
        <div style={{
          marginBottom: '20px',
          padding: '14px 16px',
          background: 'rgba(239, 68, 68, 0.07)',
          color: '#fca5a5',
          border: '1px solid rgba(239, 68, 68, 0.2)',
          borderRadius: '10px',
          fontSize: '13px'
        }}>
          <strong>⚠️ Pipeline-avbrott:</strong> {error}
        </div>
      )}

      {/* Chatthistorik-ström */}
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '20px',
        maxHeight: '450px',
        overflowY: 'auto',
        paddingRight: '4px'
      }}>
        {chatHistory.map((chat, idx) => (
          <div key={idx} style={{
            background: 'rgba(255, 255, 255, 0.01)',
            border: '1px solid rgba(255, 255, 255, 0.03)',
            borderRadius: '12px',
            padding: '16px',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px'
          }}>
            {/* Användarens fråga */}
            <div style={{ fontSize: '14px', color: '#94a3b8', display: 'flex', gap: '6px' }}>
              <span style={{ color: '#38bdf8', fontWeight: 'bold' }}>Fråga:</span>
              <span style={{ color: '#e2e8f0', fontWeight: 500 }}>{chat.question}</span>
            </div>

            {/* Oraklets svar */}
            <div style={{
              color: '#ecfdf5',
              background: 'rgba(16, 185, 129, 0.03)',
              padding: '14px',
              borderRadius: '10px',
              border: '1px solid rgba(16, 185, 129, 0.1)',
              fontSize: '14px',
              lineHeight: '1.6'
            }}>
              <span style={{ color: '#10b981', fontWeight: 700, marginRight: '6px' }}>🔮 Svar:</span>
              {chat.answer}
            </div>

            {/* Kedjans interna resonemang (Chain-of-Thought) */}
            {chat.reasoning && (
              <div style={{
                fontSize: '12px',
                color: '#64748b',
                background: '#020617',
                border: '1px dashed rgba(255, 255, 255, 0.05)',
                padding: '12px',
                borderRadius: '8px',
                lineHeight: '1.5'
              }}>
                <div style={{
                  fontFamily: 'monospace',
                  color: '#475569',
                  fontSize: '11px',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  marginBottom: '6px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}>
                  🧠 chain_of_thought_telemetry
                </div>
                <span style={{ fontStyle: 'italic' }}>{chat.reasoning}</span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};