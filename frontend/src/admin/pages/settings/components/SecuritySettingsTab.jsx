import React, { useState, useEffect } from 'react';
import { Save } from 'lucide-react';
import api from '../../../../api/client';

const SecuritySettingsTab = () => {
  const [data, setData] = useState({
    session_timeout_duration: 3600,
    password_complexity_requirements: 'High',
    minimum_password_length: 8,
    maximum_login_attempts: 5,
    account_lockout_duration: 900,
    require_two_factor_auth: false
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const res = await api.get('/admin/settings/security');
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
      const intFields = ['session_timeout_duration', 'minimum_password_length', 'maximum_login_attempts', 'account_lockout_duration'];
      intFields.forEach(f => { if (payload[f] === null) payload[f] = 0; else payload[f] = parseInt(payload[f]); });
      await api.put('/admin/settings/security', payload);
      alert("Security settings saved.");
    } catch (err) {
      console.error(err);
      alert("Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setData({ ...data, [e.target.name]: e.target.type === 'number' ? Number(value) : value });
  };

  if (loading) return <div className="animate-pulse h-96 bg-slate-50 dark:bg-slate-950 rounded-2xl" />;

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">Security Settings</h2>
          <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">Manage password policies, sessions, and multi-factor authentication.</p>
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
          <h3 className="text-sm font-black text-slate-900 dark:text-white uppercase tracking-wide mb-4 pb-2 border-b border-slate-100 dark:border-slate-800/50">Passwords</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Minimum Password Length</label>
              <input type="number" name="minimum_password_length" value={data.minimum_password_length || 8} onChange={handleChange} className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50" />
            </div>
            <div>
              <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Complexity Requirements</label>
              <select name="password_complexity_requirements" value={data.password_complexity_requirements || 'High'} onChange={handleChange} className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50">
                <option value="Low">Low (Alphanumeric)</option>
                <option value="Medium">Medium (Upper, Lower, Number)</option>
                <option value="High">High (Upper, Lower, Number, Special)</option>
              </select>
            </div>
          </div>
        </section>

        <section>
          <h3 className="text-sm font-black text-slate-900 dark:text-white uppercase tracking-wide mb-4 pb-2 border-b border-slate-100 dark:border-slate-800/50">Session & Lockout</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Session Timeout (seconds)</label>
              <input type="number" name="session_timeout_duration" value={data.session_timeout_duration || 0} onChange={handleChange} className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50" />
            </div>
            <div>
              <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Maximum Login Attempts</label>
              <input type="number" name="maximum_login_attempts" value={data.maximum_login_attempts || 5} onChange={handleChange} className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50" />
            </div>
            <div>
              <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Account Lockout Duration (seconds)</label>
              <input type="number" name="account_lockout_duration" value={data.account_lockout_duration || 900} onChange={handleChange} className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50" />
            </div>
          </div>
        </section>

        <section>
          <h3 className="text-sm font-black text-slate-900 dark:text-white uppercase tracking-wide mb-4 pb-2 border-b border-slate-100 dark:border-slate-800/50">Multi-Factor Authentication</h3>
          <div className="flex items-center justify-between bg-slate-50 dark:bg-slate-950 p-4 rounded-xl border border-slate-100 dark:border-slate-800/50 w-full md:w-1/2">
            <div>
              <h4 className="font-bold text-slate-900 dark:text-white text-sm">Require 2FA</h4>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Enforce 2FA for all administrative accounts.</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer ml-4 shrink-0">
              <input type="checkbox" name="require_two_factor_auth" checked={data.require_two_factor_auth || false} onChange={handleChange} className="sr-only peer" />
              <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white dark:bg-slate-900 after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-brand"></div>
            </label>
          </div>
        </section>
      </form>
    </div>
  );
};

export default SecuritySettingsTab;
