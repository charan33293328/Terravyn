import React, { useState, useEffect } from 'react';
import { Save } from 'lucide-react';
import api from '../../../../api/client';

const EmailSettingsTab = () => {
  const [data, setData] = useState({
    smtp_host: '',
    smtp_port: 587,
    smtp_username: '',
    smtp_password: '',
    has_smtp_password: false,
    encryption_type: 'TLS',
    sender_email: '',
    sender_name: ''
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const res = await api.get('/admin/settings/email');
      setData({ ...res.data, smtp_password: '' });
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
      if (!payload.smtp_password) delete payload.smtp_password;
      
      await api.put('/admin/settings/email', payload);
      alert("Email settings saved.");
      fetchSettings();
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
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">Email (SMTP) Settings</h2>
          <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">Configure SMTP credentials for outgoing platform emails.</p>
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
          <h3 className="text-sm font-black text-slate-900 dark:text-white uppercase tracking-wide mb-4 pb-2 border-b border-slate-100 dark:border-slate-800/50">SMTP Server</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">SMTP Host</label>
              <input type="text" name="smtp_host" value={data.smtp_host || ''} onChange={handleChange} placeholder="smtp.gmail.com" className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50" />
            </div>
            <div>
              <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">SMTP Port</label>
              <input type="number" name="smtp_port" value={data.smtp_port || 587} onChange={handleChange} className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50" />
            </div>
            <div>
              <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">SMTP Username</label>
              <input type="text" name="smtp_username" value={data.smtp_username || ''} onChange={handleChange} className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50" />
            </div>
            <div>
              <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">SMTP Password</label>
              <input type="password" name="smtp_password" value={data.smtp_password || ''} onChange={handleChange} placeholder={data.has_smtp_password ? "•••••••• (Saved)" : "Enter Password"} className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50" />
            </div>
            <div>
              <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Encryption</label>
              <select name="encryption_type" value={data.encryption_type || 'TLS'} onChange={handleChange} className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50">
                <option value="TLS">TLS</option>
                <option value="SSL">SSL</option>
                <option value="None">None</option>
              </select>
            </div>
          </div>
        </section>

        <section>
          <h3 className="text-sm font-black text-slate-900 dark:text-white uppercase tracking-wide mb-4 pb-2 border-b border-slate-100 dark:border-slate-800/50">Sender Details</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Sender Email</label>
              <input type="email" name="sender_email" value={data.sender_email || ''} onChange={handleChange} placeholder="noreply@terravyn.com" className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50" />
            </div>
            <div>
              <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Sender Name</label>
              <input type="text" name="sender_name" value={data.sender_name || ''} onChange={handleChange} placeholder="TERRAVYN Support" className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50" />
            </div>
          </div>
        </section>
      </form>
    </div>
  );
};

export default EmailSettingsTab;
