export interface ColumnMetrics {
  mean: number;
  min: number;
  max: number;
  std?: number; // Valfria extrafält
  [key: string]: number | undefined;
}

export interface UploadResponse {
  rows: number;
  columns: string[];
  dtypes: Record<string, string>;
}

export interface StatsResponse {
  stats: Record<string, ColumnMetrics>;
}

export interface AIResponse {
  question: string;
  answer: string;
  reasoning: string;
  stats_used: Record<string, any>;
}

export interface ErrorResponse {
  error_type: string;
  message: string;
  details?: Record<string, any>;
}

// Hjälp-interface för att hålla koll på Circuit Breaker i UI:t
export interface CircuitBreakerState {
  isOpen: boolean;
  retryAfter: number;
  message: string;
}