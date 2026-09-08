import React, { useState, useEffect } from 'react';
import { Save, Image as ImageIcon, Video, Globe2 } from 'lucide-react';
import api from '../../../api/client';

const LANGUAGES = [
  { code: 'en', name: 'English (Default)' },
  { code: 'te', name: 'Telugu' },
  { code: 'hi', name: 'Hindi' },
  { code: 'ta', name: 'Tamil' },
  { code: 'kn', name: 'Kannada' },
  { code: 'mr', name: 'Marathi' },
];

const LandingPageEditor = () => {
  const [activeLang, setActiveLang] = useState('en');
  const [data, setData] = useState({
    en: {
      heroTitle: '', heroSubtitle: '', ctaText: '', ctaUrl: '',
      heroVideo: '', howItWorksTitle: '', howItWorksDesc: '',
      howItWorksVideo: '', howItWorksThumbnail: ''
    }
  });
  const [features, setFeatures] = useState([]);
  
  const [pageId, setPageId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchLandingPage();
  }, []);

  const fetchLandingPage = async () => {
    try {
      setLoading(true);
      const res = await api.get('/admin/cms/pages/landing_page');
      setPageId(res.data.id);
      
      const content = res.data.content_data;
      if (content.translations) setData(content.translations);
      if (content.features) setFeatures(content.features);
      
    } catch (err) {
      if (err.response?.status !== 404) console.error(err);
      // Initialize if missing
      const initData = {};
      LANGUAGES.forEach(l => {
        initData[l.code] = {
          heroTitle: '', heroSubtitle: '', ctaText: '', ctaUrl: '',
          heroVideo: '', howItWorksTitle: '', howItWorksDesc: '',
          howItWorksVideo: '', howItWorksThumbnail: ''
        };
      });
      setData(initData);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      const payload = {
        content_data: { translations: data, features: features },
        status: 'PUBLISHED'
      };

      if (pageId) {
        await api.put(`/admin/cms/pages/${pageId}`, payload);
      } else {
        const res = await api.post('/admin/cms/pages', {
          page_identifier: 'landing_page',
          ...payload
        });
        setPageId(res.data.id);
      }
      alert("Landing page saved successfully!");
    } catch (err) {
      console.error(err);
      alert("Failed to save");
    } finally {
      setSaving(false);
    }
  };

  const updateLangData = (field, value) => {
    setData(prev => ({
      ...prev,
      [activeLang]: {
        ...(prev[activeLang] || {}),
        [field]: value
      }
    }));
  };

  const addFeature = () => {
    setFeatures([...features, { id: Date.now().toString(), icon: '', title: '', description: '', active: true }]);
  };

  const updateFeature = (index, field, value) => {
    const newFeatures = [...features];
    newFeatures[index][field] = value;
    setFeatures(newFeatures);
  };

  const removeFeature = (index) => {
    const newFeatures = [...features];
    newFeatures.splice(index, 1);
    setFeatures(newFeatures);
  };

  const currentData = data[activeLang] || {};

  if (loading) return <div className="animate-pulse h-96 bg-white dark:bg-slate-900 rounded-3xl" />;

  return (
    <div className="bg-white dark:bg-slate-900 rounded-3xl p-8 border border-slate-100 dark:border-slate-800/50 shadow-sm">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Landing Page Editor</h2>
          <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">Manage sections of the public landing page with multi-language support.</p>
        </div>
        <button 
          onClick={handleSave}
          disabled={saving}
          className="bg-brand text-white px-6 py-2.5 rounded-xl font-bold text-sm hover:bg-brand-dark transition-colors flex items-center gap-2"
        >
          {saving ? 'Saving...' : <><Save size={18} /> Save All Changes</>}
        </button>
      </div>

      <div className="flex gap-2 mb-8 overflow-x-auto pb-2 custom-scrollbar">
        {LANGUAGES.map(lang => (
          <button
            key={lang.code}
            onClick={() => setActiveLang(lang.code)}
            className={`px-4 py-2 rounded-xl font-bold text-sm whitespace-nowrap transition-colors flex items-center gap-2 ${
              activeLang === lang.code ? 'bg-slate-900 text-white' : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200'
            }`}
          >
            <Globe2 size={16} /> {lang.name}
          </button>
        ))}
      </div>

      <div className="space-y-12">
        {/* HERO SECTION */}
        <section>
          <h3 className="text-lg font-black text-slate-900 dark:text-white uppercase tracking-wide mb-6 pb-2 border-b border-slate-100 dark:border-slate-800/50">1. Hero Section</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Hero Title</label>
                <input 
                  type="text" value={currentData.heroTitle || ''} onChange={(e) => updateLangData('heroTitle', e.target.value)}
                  className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50"
                  placeholder={activeLang !== 'en' ? `Fallback: ${data.en?.heroTitle}` : ''}
                />
              </div>
              <div>
                <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Hero Subtitle</label>
                <textarea 
                  value={currentData.heroSubtitle || ''} onChange={(e) => updateLangData('heroSubtitle', e.target.value)}
                  className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50 h-24 resize-none"
                  placeholder={activeLang !== 'en' ? `Fallback: ${data.en?.heroSubtitle}` : ''}
                />
              </div>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">CTA Button Text</label>
                <input 
                  type="text" value={currentData.ctaText || ''} onChange={(e) => updateLangData('ctaText', e.target.value)}
                  className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50"
                />
              </div>
              <div>
                <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">CTA URL</label>
                <input 
                  type="text" value={currentData.ctaUrl || ''} onChange={(e) => updateLangData('ctaUrl', e.target.value)}
                  className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50"
                />
              </div>
              <div>
                <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1 flex items-center gap-2"><Video size={16}/> Background Video URL</label>
                <input 
                  type="text" value={currentData.heroVideo || ''} onChange={(e) => updateLangData('heroVideo', e.target.value)}
                  className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50"
                  placeholder="/static/media/videos/hero.mp4"
                />
              </div>
            </div>
          </div>
        </section>

        {/* HOW IT WORKS SECTION */}
        <section>
          <h3 className="text-lg font-black text-slate-900 dark:text-white uppercase tracking-wide mb-6 pb-2 border-b border-slate-100 dark:border-slate-800/50">2. How It Works (Onboarding)</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Section Title</label>
                <input 
                  type="text" value={currentData.howItWorksTitle || ''} onChange={(e) => updateLangData('howItWorksTitle', e.target.value)}
                  className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50"
                />
              </div>
              <div>
                <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Section Description</label>
                <textarea 
                  value={currentData.howItWorksDesc || ''} onChange={(e) => updateLangData('howItWorksDesc', e.target.value)}
                  className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50 h-24 resize-none"
                />
              </div>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1 flex items-center gap-2"><Video size={16}/> {langName(activeLang)} Video URL</label>
                <input 
                  type="text" value={currentData.howItWorksVideo || ''} onChange={(e) => updateLangData('howItWorksVideo', e.target.value)}
                  className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50"
                  placeholder={`/static/media/videos/onboarding-${activeLang}.mp4`}
                />
              </div>
              <div>
                <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1 flex items-center gap-2"><ImageIcon size={16}/> Video Thumbnail URL</label>
                <input 
                  type="text" value={currentData.howItWorksThumbnail || ''} onChange={(e) => updateLangData('howItWorksThumbnail', e.target.value)}
                  className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50"
                />
              </div>
            </div>
          </div>
        </section>

        {/* FEATURES SECTION - only editable in English for simplicity here, or globally applied */}
        {activeLang === 'en' && (
          <section>
            <div className="flex items-center justify-between mb-6 pb-2 border-b border-slate-100 dark:border-slate-800/50">
              <h3 className="text-lg font-black text-slate-900 dark:text-white uppercase tracking-wide">3. Features Cards (Global)</h3>
              <button onClick={addFeature} className="text-sm font-bold text-brand hover:underline">+ Add Feature Card</button>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {features.map((feat, index) => (
                <div key={index} className="bg-slate-50 dark:bg-slate-950 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 relative">
                  <button onClick={() => removeFeature(index)} className="absolute top-4 right-4 text-slate-400 hover:text-red-500">✕</button>
                  <div className="space-y-3 mt-4">
                    <input 
                      type="text" placeholder="Icon Class (e.g. Activity)" value={feat.icon} onChange={(e) => updateFeature(index, 'icon', e.target.value)}
                      className="w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-2 text-sm"
                    />
                    <input 
                      type="text" placeholder="Card Title" value={feat.title} onChange={(e) => updateFeature(index, 'title', e.target.value)}
                      className="w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-2 text-sm font-bold"
                    />
                    <textarea 
                      placeholder="Card Description" value={feat.description} onChange={(e) => updateFeature(index, 'description', e.target.value)}
                      className="w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-2 text-sm resize-none h-20"
                    />
                    <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-200 font-bold">
                      <input type="checkbox" checked={feat.active} onChange={(e) => updateFeature(index, 'active', e.target.checked)} />
                      Active
                    </label>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  );
};

// Helper
const langName = (code) => {
  return LANGUAGES.find(l => l.code === code)?.name || code;
}

export default LandingPageEditor;
