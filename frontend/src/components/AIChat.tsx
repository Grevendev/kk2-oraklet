import React, { useState } from 'react';
import { dataApi } from '../api/endpoints';
import { AIResponse } from '../types';
import { SkeletonLoader } from './SkeletonLoader';
import { useToast } from '../context/ToastContext';
import { motion, AnimatePresence } from 'framer-motion';

export const AIChat: React.FC = () => {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [chatHistory, setChatHistory] = useState<AIResponse[]>([]);

  const { showToast } = useToast();

  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const result = await dataApi.askAI(question);
      setChatHistory(prev => [result, ...prev]);
      setQuestion('');
      showToast('Svar genererat från Oraklet.', 'success');
    } catch (err: unknown) {
      const error = err as { response?: { data?: { message?: string; }; }; };
      const backendMessage = error.response?.data?.message || 'Kunde inte kommunicera med Oraklet.';
      setError(backendMessage);
      showToast(backendMessage, 'error');
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
          color: 'var(--text-main)' // Global variabel
        }}>
          3. Query Engine Interactivity
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '13px', lineHeight: '1.5', margin: 0 }}>
          Ställ frågor om ditt uppladdade dataset. AI-kedjan exekveras med strikt
          <span style={{ color: 'var(--success)', fontFamily: 'monospace' }}> PromptBuilder </span>
          och
          <span style={{ color: 'var(--success)', fontFamily: 'monospace' }}> ResponseParser</span>-validering.
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
            background: 'var(--bg-app)',
            border: '1px solid var(--border-color)',
            color: 'var(--text-main)',
            fontSize: '14px',
            outline: 'none',
            transition: 'all 0.2s ease',
            boxShadow: 'inset 0 2px 4px rgba(0, 0, 0, 0.1)'
          }}
        />
        <motion.button
          type="submit"
          disabled={loading}
          whileHover={loading ? {} : { scale: 1.02 }}
          whileTap={loading ? {} : { scale: 0.98 }}
          style={{
            padding: '12px 24px',
            background: loading ? 'var(--text-disabled)' : 'var(--primary)',
            color: '#fff',
            fontWeight: 600,
            fontSize: '14px',
            border: 'none',
            borderRadius: '10px',
            cursor: loading ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s ease'
          }}
        >
          {loading ? 'Tänker...' : 'Fråga'}
        </motion.button>
      </form>

      {/* Pipeline Felhantering */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, height: 0, y: -10 }}
            animate={{ opacity: 1, height: 'auto', y: 0 }}
            exit={{ opacity: 0, height: 0, y: -10 }}
            style={{ overflow: 'hidden' }}
          >
            <div style={{
              marginBottom: '20px',
              padding: '14px 16px',
              background: 'rgba(239, 68, 68, 0.1)',
              color: 'var(--error)',
              border: '1px solid var(--error)',
              borderRadius: '10px',
              fontSize: '13px'
            }}>
              <strong>⚠️ Pipeline-avbrott:</strong> {error}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Chatthistorik-ström */}
      <div className="custom-scrollbar" style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '20px',
        maxHeight: '450px',
        overflowY: 'auto',
        paddingRight: '4px'
      }}>
        <AnimatePresence mode="popLayout">
          {loading && (
            <motion.div
              key="loader"
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0 }}
            >
              <SkeletonLoader variant="ai-chat" />
            </motion.div>
          )}

          {chatHistory.map((chat, idx) => (
            <motion.div
              key={chat.question + idx}
              layout
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              style={{
                background: 'var(--bg-card)',
                border: '1px solid var(--border-color)',
                borderRadius: '12px',
                padding: '16px',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px'
              }}
            >
              <div style={{ fontSize: '14px', color: 'var(--text-muted)', display: 'flex', gap: '6px' }}>
                <span style={{ color: 'var(--primary)', fontWeight: 'bold' }}>Fråga:</span>
                <span style={{ color: 'var(--text-main)' }}>{chat.question}</span>
              </div>

              <div style={{
                color: 'var(--text-main)',
                background: 'rgba(16, 185, 129, 0.05)',
                padding: '14px',
                borderRadius: '10px',
                border: '1px solid var(--border-color)',
                fontSize: '14px',
                lineHeight: '1.6'
              }}>
                <span style={{ color: 'var(--success)', fontWeight: 700, marginRight: '6px' }}>🔮 Svar:</span>
                {chat.answer}
              </div>

              {chat.reasoning && (
                <div style={{
                  fontSize: '12px',
                  color: 'var(--text-muted)',
                  background: 'var(--bg-app)',
                  border: '1px dashed var(--border-color)',
                  padding: '12px',
                  borderRadius: '8px'
                }}>
                  <div style={{ fontFamily: 'monospace', fontSize: '11px', textTransform: 'uppercase', marginBottom: '6px' }}>
                    🧠 chain_of_thought_telemetry
                  </div>
                  <span style={{ fontStyle: 'italic' }}>{chat.reasoning}</span>
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
};