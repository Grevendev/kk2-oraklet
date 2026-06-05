import apiClient from './client';
import { UploadResponse, StatsResponse, AIResponse } from '../types';

export const dataApi = {
  // 1. POST /data/upload - Laddar upp CSV eller Parquet
  upload: async (file: File): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const { data } = await apiClient.post<UploadResponse>('/data/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return data;
  },

  // 2. GET /data/stats - Hämtar beskrivande statistik (Stödjer ETag via Axios automatiskt)
  getStats: async (): Promise<StatsResponse> => {
    const { data } = await apiClient.get<StatsResponse>('/data/stats');
    return data;
  },

  // 3. POST /ai/ask - Standard AI-fråga (icke-streamad)
  askAI: async (question: string): Promise<AIResponse> => {
    const { data } = await apiClient.post<AIResponse>('/ai/ask', { question });
    return data;
  }
};