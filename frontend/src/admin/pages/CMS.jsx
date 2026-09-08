import React, { useState } from 'react';
import { LayoutDashboard, Home, HelpCircle, FileText, Shield, Image } from 'lucide-react';
import CMSDashboard from './cms/CMSDashboard';
import LandingPageEditor from './cms/LandingPageEditor';
import FAQManager from './cms/FAQManager';
import BlogManager from './cms/BlogManager';
import LegalPages from './cms/LegalPages';
import MediaLibrary from './cms/MediaLibrary';

const CMS = () => {
  const [activeTab, setActiveTab] = useState('dashboard');

  const tabs = [
    { id: 'dashboard', name: 'Dashboard', icon: LayoutDashboard },
    { id: 'landing', name: 'Landing Page', icon: Home },
    { id: 'faq', name: 'FAQs', icon: HelpCircle },
    { id: 'blog', name: 'Blog / News', icon: FileText },
    { id: 'legal', name: 'Legal Pages', icon: Shield },
    { id: 'media', name: 'Media Library', icon: Image },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-black tracking-tight text-slate-900 dark:text-white">Content Management</h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">Manage website content, FAQs, articles, and media</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 p-1.5 bg-slate-100 dark:bg-slate-800/50 rounded-2xl w-fit overflow-x-auto border border-slate-200 dark:border-slate-800">
        {tabs.map(tab => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-bold text-sm transition-all duration-200 ${
                isActive 
                  ? 'bg-white dark:bg-slate-900 text-brand shadow-sm ring-1 ring-slate-900/5' 
                  : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:text-slate-200 hover:bg-slate-200/50'
              }`}
            >
              <Icon size={18} />
              {tab.name}
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      <div className="mt-6">
        {activeTab === 'dashboard' && <CMSDashboard setActiveTab={setActiveTab} />}
        {activeTab === 'landing' && <LandingPageEditor />}
        {activeTab === 'faq' && <FAQManager />}
        {activeTab === 'blog' && <BlogManager />}
        {activeTab === 'legal' && <LegalPages />}
        {activeTab === 'media' && <MediaLibrary />}
      </div>
    </div>
  );
};

export default CMS;
