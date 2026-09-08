import React, { useState, useEffect } from 'react';
import { Save } from 'lucide-react';
import api from '../../../../api/client';

const PaymentSettingsTab = () => {
  const [data, setData] = useState({
    razorpay_key_id: '',
    razorpay_key_secret: '',
    has_razorpay_secret: false,
    enable_razorpay: false,
    enable_cod: true,
    max_cod_order_value: 10000,
    cod_availability_regions: []
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const res = await api.get('/admin/settings/payment');
      setData({ ...res.data, razorpay_key_secret: '' }); // Don't show secret
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
      if (payload.max_cod_order_value === null) payload.max_cod_order_value = 0;
      await api.put('/admin/settings/payment', payload);
      alert("Payment settings saved.");
      fetchSettings(); // Refresh to update has_razorpay_secret
    } catch (err) {
      console.error(err);
      alert("Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setData({ ...data, [e.target.name]: value });
  };

  if (loading) return <div className="animate-pulse h-96 bg-slate-50 dark:bg-slate-950 rounded-2xl" />;

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">Payment Settings</h2>
          <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">Configure payment gateways and offline payment limits.</p>
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
          <div className="flex items-center justify-between mb-4 pb-2 border-b border-slate-100 dark:border-slate-800/50">
            <h3 className="text-sm font-black text-slate-900 dark:text-white uppercase tracking-wide">Razorpay Gateway</h3>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" name="enable_razorpay" checked={data.enable_razorpay} onChange={handleChange} className="sr-only peer" />
              <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white dark:bg-slate-900 after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-brand"></div>
            </label>
          </div>
          
          <div className={`grid grid-cols-1 md:grid-cols-2 gap-6 ${!data.enable_razorpay ? 'opacity-50 pointer-events-none' : ''}`}>
            <div>
              <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Razorpay Key ID</label>
              <input type="text" name="razorpay_key_id" value={data.razorpay_key_id || ''} onChange={handleChange} className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50" />
            </div>
            <div>
              <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Razorpay Key Secret</label>
              <input type="password" name="razorpay_key_secret" value={data.razorpay_key_secret || ''} onChange={handleChange} placeholder={data.has_razorpay_secret ? "•••••••• (Saved)" : "Enter Secret"} className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50" />
            </div>
          </div>
        </section>

        <section>
          <div className="flex items-center justify-between mb-4 pb-2 border-b border-slate-100 dark:border-slate-800/50">
            <h3 className="text-sm font-black text-slate-900 dark:text-white uppercase tracking-wide">Cash on Delivery (COD)</h3>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" name="enable_cod" checked={data.enable_cod} onChange={handleChange} className="sr-only peer" />
              <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white dark:bg-slate-900 after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-brand"></div>
            </label>
          </div>

          <div className={`grid grid-cols-1 gap-6 ${!data.enable_cod ? 'opacity-50 pointer-events-none' : ''}`}>
            <div>
              <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Maximum COD Order Value</label>
              <input type="number" name="max_cod_order_value" value={data.max_cod_order_value || 0} onChange={handleChange} className="w-full md:w-1/2 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50" />
            </div>
          </div>
        </section>
      </form>
    </div>
  );
};

export default PaymentSettingsTab;
