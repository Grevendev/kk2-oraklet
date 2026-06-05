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
    <div style={{ padding: '20px', border: '1px solid #ccc', borderRadius: '8px', background: '#fff' }}>
      <h2 style={{ marginTop: 0, color: '#333' }}>3. Fråga Oraklet</h2>
      <p style={{ color: '#666', fontSize: '14px' }}>Ställ frågor om ditt uppladdade dataset. AI-kedjan körs med strikt PromptBuilder- och ResponseParser-validering.</p>

      <form onSubmit={handleAsk} style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="T.ex. Vad är medelvärdet för kolumn X?"
          disabled={loading}
          style={{ flex: 1, padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}
        />
        <button
          type="submit"
          disabled={loading}
          style={{ padding: '8px 16px', background: '#10b981', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
        >
          {loading ? 'Tänker...' : 'Fråga'}
        </button>
      </form>

      {error && (
        <div style={{ padding: '10px', background: '#fee2e2', color: '#991b1b', borderRadius: '4px', marginBottom: '15px', fontSize: '14px' }}>
          <strong>Fel från AI-Pipeline:</strong> {error}
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
        {chatHistory.map((chat, index) => (
          <div key={index} style={{ borderBottom: '1px style #e4e4e7', paddingBottom: '15px' }}>
            <div style={{ fontWeight: 'bold', color: '#1f2937' }}>Fråga: {chat.question}</div>

            <div style={{ marginTop: '5px', color: '#047857', background: '#f0fdf4', padding: '10px', borderRadius: '4px' }}>
              <strong>Svar:</strong> {chat.answer}
            </div>

            {chat.reasoning && (
              <div style={{ marginTop: '5px', fontSize: '12px', color: '#6b7280', fontStyle: 'italic', background: '#f8fafc', padding: '8px', borderRadius: '4px' }}>
                <strong>Kedjans interna resonemang (Chain-of-Thought):</strong> {chat.reasoning}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};