import React, { useState, useEffect } from 'react';
import { Save } from 'lucide-react';
import api from '../../../../api/client';

const NotificationSettingsTab = () => {
  const [data, setData] = useState({
    new_orders: true,
    new_customer_registrations: true,
    support_tickets: true,
    device_provisioning: true,
    payment_success: true,
    payment_failures: true,
    low_inventory_alerts: true,
    maintenance_notifications: true
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const res = await api.get('/admin/settings/notifications');
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
      await api.put('/admin/settings/notifications', data);
      alert("Notification settings saved.");
    } catch (err) {
      console.error(err);
      alert("Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (e) => {
    setData({ ...data, [e.target.name]: e.target.checked });
  };

  if (loading) return <div className="animate-pulse h-96 bg-slate-50 dark:bg-slate-950 rounded-2xl" />;

  const toggleList = [
    { name: 'new_orders', label: 'New Orders', desc: 'Alert when a new order is placed.' },
    { name: 'new_customer_registrations', label: 'New Customers', desc: 'Alert when a new farmer registers.' },
    { name: 'support_tickets', label: 'Support Tickets', desc: 'Alert when a new support ticket is raised.' },
    { name: 'device_provisioning', label: 'Device Provisioning', desc: 'Alert when a device is successfully activated.' },
    { name: 'payment_success', label: 'Payment Success', desc: 'Alert on successful online payments.' },
    { name: 'payment_failures', label: 'Payment Failures', desc: 'Alert on failed online payments.' },
    { name: 'low_inventory_alerts', label: 'Low Inventory', desc: 'Alert when device stock is running low.' },
    { name: 'maintenance_notifications', label: 'Maintenance Events', desc: 'Alert when maintenance mode starts/ends.' }
  ];

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">Notification Settings</h2>
          <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">Configure which events trigger email alerts to administrators.</p>
        </div>
        <button 
          onClick={handleSave}
          disabled={saving}
          className="bg-brand text-white px-6 py-2.5 rounded-xl font-bold text-sm hover:bg-brand-dark transition-colors flex items-center gap-2 disabled:opacity-50"
        >
          {saving ? 'Saving...' : <><Save size={18} /> Save Changes</>}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {toggleList.map(t => (
          <div key={t.name} className="flex items-start justify-between bg-slate-50 dark:bg-slate-950 p-4 rounded-xl border border-slate-100 dark:border-slate-800/50">
            <div>
              <h4 className="font-bold text-slate-900 dark:text-white text-sm">{t.label}</h4>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{t.desc}</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer ml-4 shrink-0">
              <input type="checkbox" name={t.name} checked={data[t.name] || false} onChange={handleChange} className="sr-only peer" />
              <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white dark:bg-slate-900 after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-brand"></div>
            </label>
          </div>
        ))}
      </div>
    </div>
  );
};

export default NotificationSettingsTab;
