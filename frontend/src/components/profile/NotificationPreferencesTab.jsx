import React, { useState, useEffect } from 'react';
import { Bell, Loader2, CheckCircle2 } from 'lucide-react';
import client from '../../api/client';

export default function NotificationPreferencesTab() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [prefs, setPrefs] = useState({
    email_notifications: true,
    sms_notifications: true,
    in_app_notifications: true,
    monitoring_alerts: true,
    device_alerts: true,
    order_updates: true,
    support_updates: true,
    security_notifications: true,
    product_announcements: false
  });

  useEffect(() => {
    fetchPrefs();
  }, []);

  const fetchPrefs = async () => {
    try {
      const res = await client.get('/farmer/profile/notifications');
      setPrefs(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = (key) => {
    setPrefs(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setSuccess(false);

    try {
      await client.put('/farmer/profile/notifications', prefs);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="flex justify-center items-center h-64"><Loader2 className="w-8 h-8 animate-spin text-emerald-600" /></div>;
  }

  const ToggleSwitch = ({ label, description, checked, onChange }) => (
    <div className="flex items-center justify-between py-4 border-b border-slate-100 last:border-0">
      <div>
        <div className="font-medium text-slate-900">{label}</div>
        <div className="text-sm text-slate-500">{description}</div>
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={onChange}
        className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-emerald-600 focus:ring-offset-2 ${checked ? 'bg-emerald-600' : 'bg-slate-200'}`}
      >
        <span
          className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${checked ? 'translate-x-5' : 'translate-x-0'}`}
        />
      </button>
    </div>
  );

  return (
    <div className="max-w-3xl">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-emerald-50 rounded-lg text-emerald-600">
          <Bell className="w-5 h-5" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-slate-900">Notification Preferences</h2>
          <p className="text-sm text-slate-500">Choose how and when you want to be notified.</p>
        </div>
      </div>

      {success && <div className="bg-emerald-50 text-emerald-600 p-4 rounded-lg mb-6 flex items-center gap-2"><CheckCircle2 className="w-5 h-5"/> Preferences saved successfully.</div>}

      <form onSubmit={handleSubmit}>
        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden mb-8">
          <div className="bg-slate-50 px-6 py-4 border-b border-slate-200">
            <h3 className="font-semibold text-slate-900">Notification Channels</h3>
          </div>
          <div className="p-6">
            <ToggleSwitch
              label="Email Notifications"
              description="Receive updates via your registered email address."
              checked={prefs.email_notifications}
              onChange={() => handleToggle('email_notifications')}
            />
            <ToggleSwitch
              label="SMS Notifications"
              description="Get critical alerts sent to your phone."
              checked={prefs.sms_notifications}
              onChange={() => handleToggle('sms_notifications')}
            />
            <ToggleSwitch
              label="In-App Notifications"
              description="Show notifications within the TERRAVYN dashboard."
              checked={prefs.in_app_notifications}
              onChange={() => handleToggle('in_app_notifications')}
            />
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden mb-8">
          <div className="bg-slate-50 px-6 py-4 border-b border-slate-200">
            <h3 className="font-semibold text-slate-900">Notification Categories</h3>
          </div>
          <div className="p-6">
            <ToggleSwitch
              label="Monitoring Alerts"
              description="Irrigation schedules, weather warnings, and crop insights."
              checked={prefs.monitoring_alerts}
              onChange={() => handleToggle('monitoring_alerts')}
            />
            <ToggleSwitch
              label="Critical Device Alerts"
              description="Offline devices, low battery, or hardware failures."
              checked={prefs.device_alerts}
              onChange={() => handleToggle('device_alerts')}
            />
            <ToggleSwitch
              label="Order Updates"
              description="Order confirmations, shipping status, and delivery notifications."
              checked={prefs.order_updates}
              onChange={() => handleToggle('order_updates')}
            />
            <ToggleSwitch
              label="Support Ticket Updates"
              description="Replies and status changes on your support requests."
              checked={prefs.support_updates}
              onChange={() => handleToggle('support_updates')}
            />
            <ToggleSwitch
              label="Account Security"
              description="New logins, password changes, and security alerts."
              checked={prefs.security_notifications}
              onChange={() => handleToggle('security_notifications')}
            />
            <ToggleSwitch
              label="Product Announcements"
              description="News about new TERRAVYN features and upcoming products."
              checked={prefs.product_announcements}
              onChange={() => handleToggle('product_announcements')}
            />
          </div>
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={saving}
            className="px-6 py-2 bg-emerald-600 text-white font-medium rounded-lg hover:bg-emerald-700 transition-colors disabled:bg-emerald-400 flex items-center gap-2"
          >
            {saving && <Loader2 className="w-4 h-4 animate-spin" />}
            Save Preferences
          </button>
        </div>
      </form>
    </div>
  );
}
