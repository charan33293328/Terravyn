import React, { useState, useEffect } from 'react';
import { Layers, FileText, HelpCircle, Image as ImageIcon, ArrowRight } from 'lucide-react';
import api from '../../../api/client';

const CMSDashboard = ({ setActiveTab }) => {
  const [stats, setStats] = useState({
    pages: 0,
    faqs: 0,
    blogs: 0,
    media: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      setLoading(true);
      // In a real scenario, we might have a dedicated /stats endpoint.
      // Here we fetch all and count for simplicity of the CMS Phase.
      const [pagesRes, faqsRes, blogsRes, mediaRes] = await Promise.all([
        api.get('/admin/cms/pages'),
        api.get('/admin/cms/faqs'),
        api.get('/admin/cms/blog'),
        api.get('/admin/cms/media')
      ]);

      setStats({
        pages: pagesRes.data.length,
        faqs: faqsRes.data.length,
        blogs: blogsRes.data.length,
        media: mediaRes.data.length
      });
    } catch (err) {
      console.error("Error fetching CMS stats:", err);
    } finally {
      setLoading(false);
    }
  };

  const cards = [
    { title: 'Dynamic Pages', count: stats.pages, icon: Layers, color: 'text-blue-500', bg: 'bg-blue-500/10', tab: 'landing' },
    { title: 'Blog Articles', count: stats.blogs, icon: FileText, color: 'text-emerald-500', bg: 'bg-emerald-500/10', tab: 'blog' },
    { title: 'Active FAQs', count: stats.faqs, icon: HelpCircle, color: 'text-purple-500', bg: 'bg-purple-500/10', tab: 'faq' },
    { title: 'Media Assets', count: stats.media, icon: ImageIcon, color: 'text-amber-500', bg: 'bg-amber-500/10', tab: 'media' }
  ];

  if (loading) {
    return <div className="animate-pulse h-64 bg-slate-100 dark:bg-slate-800 rounded-3xl" />;
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {cards.map((card, idx) => (
          <div key={idx} className="bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-100 dark:border-slate-800/50 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden group">
            <div className="flex items-start justify-between relative z-10">
              <div>
                <p className="text-slate-500 dark:text-slate-400 font-medium text-sm">{card.title}</p>
                <h3 className="text-3xl font-black text-slate-900 dark:text-white mt-2">{card.count}</h3>
              </div>
              <div className={`p-3 rounded-2xl ${card.bg} ${card.color}`}>
                <card.icon size={24} />
              </div>
            </div>
            
            <button 
              onClick={() => setActiveTab(card.tab)}
              className="mt-6 flex items-center gap-2 text-sm font-bold text-brand hover:text-brand-dark transition-colors relative z-10"
            >
              Manage {card.title} <ArrowRight size={16} />
            </button>

            <div className={`absolute -bottom-6 -right-6 opacity-5 transform group-hover:scale-110 transition-transform duration-500`}>
              <card.icon size={120} />
            </div>
          </div>
        ))}
      </div>

      <div className="bg-white dark:bg-slate-900 rounded-3xl p-8 border border-slate-100 dark:border-slate-800/50 shadow-sm">
        <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button onClick={() => setActiveTab('blog')} className="p-4 border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-2xl text-slate-500 dark:text-slate-400 hover:border-brand hover:text-brand transition-colors font-bold flex items-center justify-center gap-2">
            + Write New Article
          </button>
          <button onClick={() => setActiveTab('faq')} className="p-4 border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-2xl text-slate-500 dark:text-slate-400 hover:border-brand hover:text-brand transition-colors font-bold flex items-center justify-center gap-2">
            + Add FAQ Item
          </button>
          <button onClick={() => setActiveTab('media')} className="p-4 border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-2xl text-slate-500 dark:text-slate-400 hover:border-brand hover:text-brand transition-colors font-bold flex items-center justify-center gap-2">
            + Upload Media Asset
          </button>
        </div>
      </div>
    </div>
  );
};

export default CMSDashboard;
