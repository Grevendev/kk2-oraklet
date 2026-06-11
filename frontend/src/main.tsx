// src/main.tsx
import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.tsx';
import { ThemeProvider } from './context/ThemeContext'; // <-- Importera här
import './index.css'; // <-- Säkerställ att din CSS laddas här

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ThemeProvider>
      <App />
    </ThemeProvider>
  </React.StrictMode>,
);