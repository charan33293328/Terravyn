import React from 'react';
import EmptyState from '../components/EmptyState';
import { Settings } from 'lucide-react';

const SettingsPage = () => {
  return (
    <div className="bg-white dark:bg-slate-900 rounded-3xl p-8 shadow-sm border border-slate-100 dark:border-slate-800/50 min-h-[60vh] flex items-center justify-center">
      <EmptyState icon={Settings} title="System Settings" description="TERRAVYN business configurations will be implemented here." />
    </div>
  );
};

export default SettingsPage;
