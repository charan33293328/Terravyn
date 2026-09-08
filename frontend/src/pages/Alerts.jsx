import React, { useState, useEffect } from 'react';
import { AlertCircle, CheckCircle, Info, AlertTriangle } from 'lucide-react';
import apiClient from '../api/client';

const Alerts = () => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const res = await apiClient.get('/alerts/');
        setAlerts(res.data);
      } catch (err) {
        console.error("Failed to fetch alerts", err);
      } finally {
        setLoading(false);
      }
    };
    fetchAlerts();
  }, []);

  const getIcon = (severity) => {
    switch(severity) {
      case 'critical': return <AlertCircle className="w-5 h-5 text-red-500" />;
      case 'warning': return <AlertTriangle className="w-5 h-5 text-orange-500" />;
      case 'info': return <Info className="w-5 h-5 text-blue-500" />;
      default: return <Info className="w-5 h-5 text-slate-500" />;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-slate-800">Alerts & Notifications</h2>
          <p className="text-slate-500">System monitoring and critical event logging.</p>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-slate-500">Loading alerts...</div>
        ) : alerts.length === 0 ? (
          <div className="p-8 text-center text-slate-500">No alerts found. Everything is running smoothly!</div>
        ) : (
          <ul className="divide-y divide-slate-200">
            {alerts.map((alert) => (
              <li key={alert.id} className="p-4 hover:bg-slate-50 transition-colors flex gap-4 items-start">
                <div className="mt-1">{getIcon(alert.severity)}</div>
                <div className="flex-1">
                  <div className="flex justify-between">
                    <p className="text-sm font-bold text-slate-800">{alert.type}</p>
                    <p className="text-xs text-slate-500">{new Date(alert.timestamp).toLocaleString()}</p>
                  </div>
                  <p className="text-sm text-slate-600 mt-1">{alert.message}</p>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default Alerts;
