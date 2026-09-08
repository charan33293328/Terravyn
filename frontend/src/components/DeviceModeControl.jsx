import React, { useState, useEffect } from 'react';
import { Settings, RefreshCw, CheckCircle2 } from 'lucide-react';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import apiClient from '../api/client';

dayjs.extend(relativeTime);

const DeviceModeControl = ({ device, onModeChange, compact = false }) => {
  const [mode, setMode] = useState((device?.irrigation_mode || 'AUTO').toUpperCase());
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(device?.last_mode_change);

  useEffect(() => {
    if (device?.irrigation_mode) {
      setMode(device.irrigation_mode.toUpperCase());
    }
    if (device?.last_mode_change) {
      setLastUpdated(device.last_mode_change);
    }
  }, [device?.irrigation_mode, device?.last_mode_change]);

  const handleToggle = async () => {
    if (!device?.id) return;
    
    const newMode = mode === 'AUTO' ? 'MANUAL' : 'AUTO';
    console.log(`Changing irrigation mode to ${newMode}`);
    setLoading(true);
    setSuccess(false);

    try {
      const res = await apiClient.put(`/devices/${device.id}/mode`, {
        irrigation_mode: newMode
      });
      setMode(newMode);
      setLastUpdated(res.data.last_mode_change || new Date().toISOString());
      setSuccess(true);
      
      if (onModeChange) {
        onModeChange(res.data);
      }

      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      console.error("Failed to update device mode:", err);
      alert("Failed to update operation mode. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const content = (
    <>
      {!compact && (
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Settings className="w-4 h-4 text-slate-500" />
            <h4 className="text-sm font-bold text-slate-800 dark:text-slate-200">Operation Mode</h4>
          </div>
          
          {success && (
            <span className="flex items-center gap-1 text-xs font-medium text-emerald-600 dark:text-emerald-400 animate-in fade-in zoom-in">
              <CheckCircle2 className="w-3 h-3" /> Saved
            </span>
          )}
        </div>
      )}

      <div className={`flex items-center justify-between ${compact ? 'gap-4' : ''}`}>
        <div className="flex flex-col">
          <span className="text-sm font-medium text-slate-900 dark:text-white flex items-center gap-2">
            {mode} Mode
            {compact && success && <CheckCircle2 className="w-3 h-3 text-emerald-500" />}
          </span>
          <span className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 whitespace-nowrap">
            {lastUpdated ? `Changed ${dayjs(lastUpdated).fromNow()}` : 'Never'}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span className={`text-xs font-medium ${mode === 'MANUAL' ? 'text-slate-900 dark:text-white' : 'text-slate-400'}`}>MANUAL</span>
          <button
            onClick={handleToggle}
            disabled={loading}
            className={`relative inline-flex h-7 w-12 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2 ${
              mode === 'AUTO' ? 'bg-brand' : 'bg-slate-400'
            } ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
            role="switch"
            aria-checked={mode === 'AUTO'}
          >
            <span
              aria-hidden="true"
              className={`pointer-events-none inline-block h-6 w-6 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                mode === 'AUTO' ? 'translate-x-5' : 'translate-x-0'
              } flex items-center justify-center`}
            >
              {loading && <RefreshCw className="w-3 h-3 text-slate-400 animate-spin" />}
            </span>
          </button>
          <span className={`text-xs font-medium ${mode === 'AUTO' ? 'text-brand' : 'text-slate-400'}`}>AUTO</span>
        </div>
      </div>
    </>
  );

  if (compact) {
    return <div>{content}</div>;
  }

  return (
    <div className="bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-700/50 p-4 min-w-[250px]">
      {content}
    </div>
  );
};

export default DeviceModeControl;
