import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'http://localhost:8000', // Porten där din FastAPI körs
  headers: {
    'Content-Type': 'application/json',
  },
});

// Global interceptor för att hantera fel (t.ex. 503 Circuit Breaker eller 429 Rate Limit)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const status = error.response.status;
      const data = error.response.data;

      if (status === 503) {
        // Din CircuitBreakerMiddleware skickar med "retry_after_seconds"
        const retryAfter = data.retry_after_seconds || 30;
        // Vi kan skicka detta vidare till våra komponenter via ett custom event
        const event = new CustomEvent('circuit-breaker-triggered', {
          detail: { retryAfter, message: data.message }
        });
        window.dispatchEvent(event);
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;