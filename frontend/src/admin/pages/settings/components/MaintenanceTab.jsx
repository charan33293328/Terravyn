import React, { useState, useEffect } from 'react';
import { Save, AlertTriangle } from 'lucide-react';
import api from '../../../../api/client';

const MaintenanceTab = () => {
  const [data, setData] = useState({
    is_active: false,
    message: '',
    start_time: '',
    end_time: '',
    whitelist_ips: []
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const res = await api.get('/admin/maintenance');
      setData({
        ...res.data,
        start_time: res.data.start_time ? new Date(res.data.start_time).toISOString().slice(0, 16) : '',
        end_time: res.data.end_time ? new Date(res.data.end_time).toISOString().slice(0, 16) : ''
      });
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
      if (!payload.start_time) payload.start_time = null;
      if (!payload.end_time) payload.end_time = null;

      await api.post('/admin/maintenance', payload);
      alert("Maintenance schedule updated.");
    } catch (err) {
      console.error(err);
      alert("Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (e) => {
    setData({ ...data, [e.target.name]: e.target.type === 'checkbox' ? e.target.checked : e.target.value });
  };

  if (loading) return <div className="animate-pulse h-96 bg-slate-50 dark:bg-slate-950 rounded-2xl" />;

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">Maintenance Mode</h2>
          <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">Suspend customer-facing services during system upgrades.</p>
        </div>
        <button 
          onClick={handleSave}
          disabled={saving}
          className={`${data.is_active ? 'bg-red-500 hover:bg-red-600' : 'bg-brand hover:bg-brand-dark'} text-white px-6 py-2.5 rounded-xl font-bold text-sm transition-colors flex items-center gap-2 disabled:opacity-50`}
        >
          {saving ? 'Saving...' : <><Save size={18} /> {data.is_active ? 'Apply Maintenance' : 'Save Schedule'}</>}
        </button>
      </div>

      <div className={`mb-8 p-4 rounded-xl border ${data.is_active ? 'bg-red-50 border-red-200' : 'bg-amber-50 border-amber-200'} flex items-start gap-4`}>
        <div className={`mt-0.5 ${data.is_active ? 'text-red-500' : 'text-amber-500'}`}>
          <AlertTriangle size={24} />
        </div>
        <div>
          <h3 className={`font-bold ${data.is_active ? 'text-red-900' : 'text-amber-900'}`}>
            {data.is_active ? 'Maintenance Mode is currently ACTIVE.' : 'Caution: Maintenance Mode'}
          </h3>
          <p className={`text-sm mt-1 ${data.is_active ? 'text-red-700' : 'text-amber-700'}`}>
            When active, customers will see a 503 Service Unavailable page with your custom message. Admin users will still have access to the dashboard.
          </p>
        </div>
      </div>

      <form onSubmit={handleSave} className="space-y-8">
        <section>
          <div className="flex items-center justify-between bg-slate-50 dark:bg-slate-950 p-6 rounded-2xl border border-slate-100 dark:border-slate-800/50">
            <div>
              <h4 className="font-bold text-slate-900 dark:text-white text-lg">Enable Maintenance Mode</h4>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Immediately suspend services or schedule for later if times are provided.</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer ml-4 shrink-0">
              <input type="checkbox" name="is_active" checked={data.is_active} onChange={handleChange} className="sr-only peer" />
              <div className="w-14 h-7 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white dark:bg-slate-900 after:border-slate-300 after:border after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-red-500"></div>
            </label>
          </div>
        </section>

        <section className={`${!data.is_active ? 'opacity-50 pointer-events-none' : ''} space-y-6 transition-opacity duration-200`}>
          <div>
            <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Public Maintenance Message</label>
            <textarea 
              name="message" 
              value={data.message || ''} 
              onChange={handleChange} 
              rows={3}
              placeholder="We are currently undergoing scheduled maintenance. Please check back soon."
              className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-red-500/50" 
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Scheduled Start Time (Optional)</label>
              <input type="datetime-local" name="start_time" value={data.start_time || ''} onChange={handleChange} className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-red-500/50" />
            </div>
            <div>
              <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Scheduled End Time (Optional)</label>
              <input type="datetime-local" name="end_time" value={data.end_time || ''} onChange={handleChange} className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-red-500/50" />
            </div>
          </div>
        </section>
      </form>
    </div>
  );
};

export default MaintenanceTab;
