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
  // Använder unknown för typsäkerhet - du måste verifiera datan innan användning
  stats_used: Record<string, unknown>;
}

export interface ErrorResponse {
  error_type: string;
  message: string;
  // Använder unknown för att tillåta flexibla detaljer utan att ge upp typsäkerheten
  details?: Record<string, unknown>;
}

// Hjälp-interface för att hålla koll på Circuit Breaker i UI:t
export interface CircuitBreakerState {
  isOpen: boolean;
  retryAfter: number;
  message: string;
}