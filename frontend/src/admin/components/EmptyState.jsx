import React from 'react';
import { PackageOpen, FileSearch } from 'lucide-react';
import { motion } from 'framer-motion';

const EmptyState = ({ icon: Icon = PackageOpen, title = "No data available yet", description, action }) => {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center">
      <motion.div 
        initial={{ y: 10, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="w-24 h-24 bg-brand/5 text-brand/50 rounded-full flex items-center justify-center mb-6"
      >
        <Icon size={40} />
      </motion.div>
      <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-1">{title}</h3>
      {description && <p className="text-sm text-slate-500 dark:text-slate-400 max-w-sm mb-6">{description}</p>}
      {action && (
        <div className="mt-2">
          {action}
        </div>
      )}
    </div>
  );
};

export default EmptyState;
