// src/context/ThemeContext.tsx
import React, { createContext, useContext, useState, useEffect } from 'react';

type Theme = 'light' | 'dark';

interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);
// eslint-disable-next-line react-refresh/only-export-components
export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) throw new Error('useTheme måste användas inom en ThemeProvider');
  return context;
};

export const ThemeProvider: React.FC<{ children: React.ReactNode; }> = ({ children }) => {
  const [theme, setTheme] = useState<Theme>(() => {
    // 1. Kolla om användaren har ett sparat val sedan tidigare
    const savedTheme = localStorage.getItem('app-theme') as Theme | null;
    if (savedTheme) return savedTheme;

    // 2. Annars, kolla operativsystemets inställning
    if (window.matchMedia('(prefers-color-scheme: light)').matches) {
      return 'light';
    }
    return 'dark'; // Default till mörkt läge för premium-looken
  });

  useEffect(() => {
    // Uppdatera localStorage och lägg till/ta bort en klass på <html> för CSS-styling
    localStorage.setItem('app-theme', theme);
    const root = window.document.documentElement;
    if (theme === 'light') {
      root.classList.add('light-mode');
    } else {
      root.classList.remove('light-mode');
    }
  }, [theme]);

  // Lyssna på om användaren ändrar OS-tema live i sina systeminställningar
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: light)');
    const handleChange = (e: MediaQueryListEvent) => {
      if (!localStorage.getItem('app-theme')) {
        setTheme(e.matches ? 'light' : 'dark');
      }
    };
    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  const toggleTheme = () => {
    setTheme(prev => (prev === 'light' ? 'dark' : 'light'));
  };

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};