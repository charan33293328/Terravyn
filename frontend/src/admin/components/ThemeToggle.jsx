import React from 'react';
import { Moon, Sun } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';

const ThemeToggle = () => {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      aria-label="Toggle theme"
      className="p-2 text-slate-500 dark:text-slate-400 hover:text-brand transition-colors rounded-full hover:bg-slate-50 dark:bg-slate-950 dark:hover:bg-slate-800"
    >
      {theme === 'dark' ? (
        <Sun size={20} className="text-amber-500" />
      ) : (
        <Moon size={20} />
      )}
    </button>
  );
};

export default ThemeToggle;
