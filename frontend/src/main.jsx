import { StrictMode, Suspense } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App.jsx';
import './i18n';
import { ThemeProvider } from './context/ThemeContext';
import ErrorBoundary from './components/ErrorBoundary';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ErrorBoundary>
      <Suspense fallback={<div className="flex min-h-screen items-center justify-center text-brand font-bold text-xl">Loading TERRAVYN...</div>}>
        <ThemeProvider>
          <App />
        </ThemeProvider>
      </Suspense>
    </ErrorBoundary>
  </StrictMode>,
)
