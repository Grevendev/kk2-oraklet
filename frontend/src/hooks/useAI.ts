import { useState } from 'react';
import { AIResponse, CircuitBreakerState } from '../types';

const API_BASE = 'http://127.0.0.1:8000';

export const useAI = () => {
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [chatHistory, setChatHistory] = useState<AIResponse[]>([]);

  // Initiera med din egen CircuitBreakerState-typ
  const [circuitBreaker, setCircuitBreaker] = useState<CircuitBreakerState>({
    isOpen: false,
    retryAfter: 0,
    message: ''
  });

  const askOraklet = async (question: string) => {
    if (!question.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/ai/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question }),
      });

      // Vid 503 sätter vi din CircuitBreakerState i UI:t
      if (response.status === 503) {
        setCircuitBreaker({
          isOpen: true,
          retryAfter: 10, // Sekunder innan den försöker igen, eller från headers om du har det
          message: 'Oraklets Circuit Breaker har löst ut på grund av fel i AI-kedjan!'
        });
        throw new Error('Service Unavailable: Kretsbrytaren är öppen.');
      }

      if (!response.ok) {
        const errData = await response.json().catch(() => ({ message: 'Kunde inte hämta svar' }));
        throw new Error(errData.message || `Ett fel uppstod (Status: ${response.status})`);
      }

      // Om anropet lyckas, stäng brytaren i UI:t
      setCircuitBreaker({ isOpen: false, retryAfter: 0, message: '' });

      const data: AIResponse = await response.json();
      setChatHistory((prev) => [...prev, data]);
      return data;
    } catch (err: any) {
      setError(err.message || 'Ett fel uppstod vid AI-anropet.');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const clearHistory = () => setChatHistory([]);

  return {
    loading,
    error,
    chatHistory,
    circuitBreaker, // Gör den tillgänglig för din CircuitBreakerStatus.tsx-komponent!
    askOraklet,
    clearHistory
  };
};