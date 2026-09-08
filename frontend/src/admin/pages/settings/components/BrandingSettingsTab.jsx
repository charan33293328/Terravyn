import React, { useState, useEffect, useRef } from 'react';
import { Save, Image as ImageIcon, UploadCloud } from 'lucide-react';
import api from '../../../../api/client';

const BrandingSettingsTab = () => {
  const [data, setData] = useState({
    platform_logo: '',
    favicon: '',
    admin_login_logo: '',
    website_footer_logo: '',
    primary_brand_color: '#0f766e',
    secondary_brand_color: '#115e59',
    accent_color: '#14b8a6',
    company_tagline: ''
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const res = await api.get('/admin/settings/branding');
      setData(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    try {
      setSaving(true);
      const payload = { ...data };
      Object.keys(payload).forEach(key => {
        if (payload[key] === '') payload[key] = null;
      });
      await api.put('/admin/settings/branding', payload);
      alert("Branding settings saved.");
    } catch (err) {
      console.error(err);
      alert("Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (e) => {
    setData({ ...data, [e.target.name]: e.target.value });
  };

  if (loading) return <div className="animate-pulse h-96 bg-slate-50 dark:bg-slate-950 rounded-2xl" />;

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">Branding Settings</h2>
          <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">Manage logos, colors, and global aesthetics.</p>
        </div>
        <button 
          onClick={handleSave}
          disabled={saving}
          className="bg-brand text-white px-6 py-2.5 rounded-xl font-bold text-sm hover:bg-brand-dark transition-colors flex items-center gap-2 disabled:opacity-50"
        >
          {saving ? 'Saving...' : <><Save size={18} /> Save Changes</>}
        </button>
      </div>

      <form onSubmit={handleSave} className="space-y-8">
        <section>
          <h3 className="text-sm font-black text-slate-900 dark:text-white uppercase tracking-wide mb-4 pb-2 border-b border-slate-100 dark:border-slate-800/50">Colors</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Primary Color</label>
              <div className="flex items-center gap-3">
                <input type="color" name="primary_brand_color" value={data.primary_brand_color || '#000000'} onChange={handleChange} className="w-10 h-10 rounded cursor-pointer border-0 p-0" />
                <input type="text" name="primary_brand_color" value={data.primary_brand_color || ''} onChange={handleChange} className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50" />
              </div>
            </div>
            <div>
              <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Secondary Color</label>
              <div className="flex items-center gap-3">
                <input type="color" name="secondary_brand_color" value={data.secondary_brand_color || '#000000'} onChange={handleChange} className="w-10 h-10 rounded cursor-pointer border-0 p-0" />
                <input type="text" name="secondary_brand_color" value={data.secondary_brand_color || ''} onChange={handleChange} className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50" />
              </div>
            </div>
            <div>
              <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Accent Color</label>
              <div className="flex items-center gap-3">
                <input type="color" name="accent_color" value={data.accent_color || '#000000'} onChange={handleChange} className="w-10 h-10 rounded cursor-pointer border-0 p-0" />
                <input type="text" name="accent_color" value={data.accent_color || ''} onChange={handleChange} className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50" />
              </div>
            </div>
          </div>
        </section>

        <section>
          <h3 className="text-sm font-black text-slate-900 dark:text-white uppercase tracking-wide mb-4 pb-2 border-b border-slate-100 dark:border-slate-800/50">Logos & Assets</h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">Paste the URL of your uploaded image from the Media Library.</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Main Platform Logo</label>
              <input type="text" name="platform_logo" value={data.platform_logo || ''} onChange={handleChange} placeholder="/static/media/images/logo.png" className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50 mb-2" />
              {data.platform_logo && <img src={`http://127.0.0.1:8000${data.platform_logo}`} alt="Preview" className="h-16 object-contain bg-slate-100 dark:bg-slate-800 p-2 rounded-lg border" />}
            </div>
            <div>
              <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Favicon</label>
              <input type="text" name="favicon" value={data.favicon || ''} onChange={handleChange} placeholder="/static/media/images/favicon.ico" className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50 mb-2" />
            </div>
            <div>
              <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Admin Login Logo</label>
              <input type="text" name="admin_login_logo" value={data.admin_login_logo || ''} onChange={handleChange} className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50" />
            </div>
            <div>
              <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Footer Logo</label>
              <input type="text" name="website_footer_logo" value={data.website_footer_logo || ''} onChange={handleChange} className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50" />
            </div>
          </div>
        </section>

        <section>
          <h3 className="text-sm font-black text-slate-900 dark:text-white uppercase tracking-wide mb-4 pb-2 border-b border-slate-100 dark:border-slate-800/50">Messaging</h3>
          <div>
            <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Company Tagline</label>
            <input type="text" name="company_tagline" value={data.company_tagline || ''} onChange={handleChange} placeholder="Smart Agriculture for a Better Tomorrow" className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50" />
          </div>
        </section>
      </form>
    </div>
  );
};

export default BrandingSettingsTab;
