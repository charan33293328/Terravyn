import React, { useState, useEffect } from 'react';
import { Save } from 'lucide-react';
import api from '../../../../api/client';

const DeviceSettingsTab = () => {
  const [data, setData] = useState({
    heartbeat_timeout_threshold: 300,
    provision_polling_interval: 60,
    default_firmware_version: '',
    device_offline_alert_duration: 3600,
    qr_code_expiration_period: 86400,
    activation_code_expiration_period: 3600
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const res = await api.get('/admin/settings/devices');
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
      const intFields = ['heartbeat_timeout_threshold', 'provision_polling_interval', 'device_offline_alert_duration', 'qr_code_expiration_period', 'activation_code_expiration_period'];
      intFields.forEach(f => { if (payload[f] === null) payload[f] = 0; else payload[f] = parseInt(payload[f]); });
      await api.put('/admin/settings/devices', payload);
      alert("Device defaults saved.");
    } catch (err) {
      console.error(err);
      alert("Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (e) => {
    setData({ ...data, [e.target.name]: Number(e.target.value) || e.target.value });
  };

  if (loading) return <div className="animate-pulse h-96 bg-slate-50 dark:bg-slate-950 rounded-2xl" />;

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">Device Defaults</h2>
          <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">Global timeouts, polling intervals, and device behavior.</p>
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
          <h3 className="text-sm font-black text-slate-900 dark:text-white uppercase tracking-wide mb-4 pb-2 border-b border-slate-100 dark:border-slate-800/50">Connectivity</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Heartbeat Timeout (seconds)</label>
              <input type="number" name="heartbeat_timeout_threshold" value={data.heartbeat_timeout_threshold || 0} onChange={handleChange} className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50" />
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Time without heartbeat before marking device as OFFLINE.</p>
            </div>
            <div>
              <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Device Offline Alert (seconds)</label>
              <input type="number" name="device_offline_alert_duration" value={data.device_offline_alert_duration || 0} onChange={handleChange} className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50" />
            </div>
            <div>
              <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Provision Polling Interval (seconds)</label>
              <input type="number" name="provision_polling_interval" value={data.provision_polling_interval || 0} onChange={handleChange} className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50" />
            </div>
          </div>
        </section>

        <section>
          <h3 className="text-sm font-black text-slate-900 dark:text-white uppercase tracking-wide mb-4 pb-2 border-b border-slate-100 dark:border-slate-800/50">Provisioning Tokens</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">QR Code Expiration (seconds)</label>
              <input type="number" name="qr_code_expiration_period" value={data.qr_code_expiration_period || 0} onChange={handleChange} className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50" />
            </div>
            <div>
              <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Activation Code Expiration (seconds)</label>
              <input type="number" name="activation_code_expiration_period" value={data.activation_code_expiration_period || 0} onChange={handleChange} className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50" />
            </div>
          </div>
        </section>

        <section>
          <h3 className="text-sm font-black text-slate-900 dark:text-white uppercase tracking-wide mb-4 pb-2 border-b border-slate-100 dark:border-slate-800/50">Firmware</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Default Firmware Version</label>
              <input type="text" name="default_firmware_version" value={data.default_firmware_version || ''} onChange={handleChange} className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50" />
            </div>
          </div>
        </section>
      </form>
    </div>
  );
};

export default DeviceSettingsTab;
