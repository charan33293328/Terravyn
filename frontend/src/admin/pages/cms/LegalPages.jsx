import React, { useState, useEffect } from 'react';
import { Shield, Check } from 'lucide-react';
import api from '../../../api/client';
import TiptapEditor from '../../components/TiptapEditor';

const PAGES = [
  { id: 'privacy_policy', title: 'Privacy Policy' },
  { id: 'terms_conditions', title: 'Terms & Conditions' },
  { id: 'refund_policy', title: 'Refund Policy' },
  { id: 'shipping_policy', title: 'Shipping Policy' },
  { id: 'cookie_policy', title: 'Cookie Policy' },
];

const LegalPages = () => {
  const [activePage, setActivePage] = useState(PAGES[0].id);
  const [content, setContent] = useState('');
  const [pageId, setPageId] = useState(null);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPage(activePage);
  }, [activePage]);

  const fetchPage = async (identifier) => {
    try {
      setLoading(true);
      const res = await api.get(`/admin/cms/pages/${identifier}`);
      setContent(res.data.content_data.html || '');
      setPageId(res.data.id);
    } catch (err) {
      if (err.response?.status === 404) {
        // Doesn't exist yet
        setContent('');
        setPageId(null);
      } else {
        console.error(err);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      const payload = {
        content_data: { html: content },
        status: 'PUBLISHED'
      };

      if (pageId) {
        await api.put(`/admin/cms/pages/${pageId}`, payload);
      } else {
        const res = await api.post('/admin/cms/pages', {
          page_identifier: activePage,
          ...payload
        });
        setPageId(res.data.id);
      }
      // Show short success notification
      const btn = document.getElementById('save-btn');
      const originalText = btn.innerHTML;
      btn.innerHTML = 'Saved Successfully!';
      setTimeout(() => btn.innerHTML = originalText, 2000);
    } catch (err) {
      console.error(err);
      alert("Failed to save legal page");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="bg-white dark:bg-slate-900 rounded-3xl p-8 border border-slate-100 dark:border-slate-800/50 shadow-sm flex flex-col md:flex-row gap-8">
      {/* Sidebar navigation */}
      <div className="w-full md:w-64 shrink-0 border-r border-slate-100 dark:border-slate-800/50 pr-4">
        <h2 className="text-sm font-black text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
          <Shield size={16} /> Legal Documents
        </h2>
        <nav className="space-y-1">
          {PAGES.map(p => (
            <button
              key={p.id}
              onClick={() => setActivePage(p.id)}
              className={`w-full text-left px-4 py-3 rounded-xl font-bold text-sm transition-colors ${
                activePage === p.id 
                  ? 'bg-slate-900 text-white' 
                  : 'text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:bg-slate-950 hover:text-slate-900 dark:text-white'
              }`}
            >
              {p.title}
            </button>
          ))}
        </nav>
      </div>

      {/* Editor Area */}
      <div className="flex-1 max-w-4xl">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            {PAGES.find(p => p.id === activePage)?.title}
          </h1>
          <button 
            id="save-btn"
            onClick={handleSave}
            disabled={saving || loading}
            className="bg-brand text-white px-6 py-2.5 rounded-xl font-bold text-sm hover:bg-brand-dark transition-colors flex items-center gap-2 disabled:opacity-50"
          >
            {saving ? 'Saving...' : <><Check size={18} /> Save Changes</>}
          </button>
        </div>

        {loading ? (
          <div className="animate-pulse h-[400px] bg-slate-50 dark:bg-slate-950 rounded-2xl" />
        ) : (
          <TiptapEditor value={content} onChange={setContent} />
        )}
      </div>
    </div>
  );
};

export default LegalPages;
