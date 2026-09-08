import React from 'react';
import { ShieldAlert, AlertTriangle, XCircle } from 'lucide-react';
import { motion } from 'framer-motion';

const ErrorState = ({ type = '403', title, message, actionText, onAction }) => {
  const getIcon = () => {
    switch(type) {
      case '403': return <ShieldAlert size={64} className="text-red-500" />;
      case '404': return <XCircle size={64} className="text-amber-500" />;
      default: return <AlertTriangle size={64} className="text-red-500" />;
    }
  };

  const defaultTitle = type === '403' ? 'Access Denied' : 'Something went wrong';
  const defaultMessage = type === '403' 
    ? "You don't have the necessary administrative privileges to view this page."
    : "An unexpected error occurred while loading this module.";

  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center p-8 text-center">
      <motion.div 
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="w-32 h-32 bg-white dark:bg-slate-900 rounded-full shadow-sm border border-slate-100 dark:border-slate-800/50 flex items-center justify-center mb-6 relative"
      >
        <div className="absolute inset-0 bg-red-50 rounded-full animate-ping opacity-20"></div>
        {getIcon()}
      </motion.div>
      <h2 className="text-2xl font-black text-slate-900 dark:text-white tracking-tight mb-2">
        {title || defaultTitle}
      </h2>
      <p className="text-slate-500 dark:text-slate-400 max-w-md mb-8">
        {message || defaultMessage}
      </p>
      {onAction && (
        <button 
          onClick={onAction}
          className="bg-brand text-white px-6 py-2.5 rounded-xl font-bold shadow-sm hover:bg-brand-dark hover:shadow transition-all"
        >
          {actionText || 'Go Back'}
        </button>
      )}
    </div>
  );
};

export default ErrorState;
