import React, { useState, useEffect } from 'react';
import apiClient from '../../api/client';
import {
  Brain, ShieldCheck, ShieldAlert, AlertTriangle, CheckCircle2, Clock,
  Droplets, Power, RefreshCw, Play, Settings, Sliders, ChevronDown, ChevronUp,
  Info, ExternalLink, Activity
} from 'lucide-react';
import dayjs from 'dayjs';

const IrrigationIntelligencePanel = ({ farmId, farmName }) => {
  const [state, setState] = useState(null);
  const [history, setHistory] = useState(null);
  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);
  const [dryRunning, setDryRunning] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const [error, setError] = useState(null);
  const [actionSuccess, setActionSuccess] = useState(null);

  useEffect(() => {
    if (farmId) {
      fetchState();
      fetchHistory();
    }
  }, [farmId]);

  const fetchState = async () => {
    try {
      setError(null);
      const res = await apiClient.get(`/irrigation/intelligence/${farmId}`);
      setState(res.data);
    } catch (err) {
      console.error('Failed to load intelligence state:', err);
      setError(err.response?.data?.detail || 'Unable to load irrigation intelligence state.');
    } finally {
      setLoading(false);
    }
  };

  const fetchHistory = async () => {
    try {
      const res = await apiClient.get(`/irrigation/history/${farmId}?limit=5`);
      setHistory(res.data);
    } catch (err) {
      console.error('Failed to load irrigation history:', err);
    }
  };

  const handleEvaluate = async (autoDispatch = false) => {
    try {
      setEvaluating(true);
      setError(null);
      setActionSuccess(null);
      const res = await apiClient.post(`/irrigation/evaluate/${farmId}?auto_dispatch=${autoDispatch}`);
      setActionSuccess('Evaluation completed successfully.');
      fetchState();
      fetchHistory();
    } catch (err) {
      console.error('Evaluation failed:', err);
      setError(err.response?.data?.detail || 'Evaluation failed.');
    } finally {
      setEvaluating(false);
    }
  };

  const handleDryRun = async () => {
    try {
      setDryRunning(true);
      setError(null);
      setActionSuccess(null);
      const res = await apiClient.post(`/irrigation/dry-run/${farmId}`);
      setActionSuccess('Dry-run simulation completed. Zero physical pump actuation occurred.');
      fetchState();
      fetchHistory();
    } catch (err) {
      console.error('Dry-run failed:', err);
      setError(err.response?.data?.detail || 'Dry-run failed.');
    } finally {
      setDryRunning(false);
    }
  };

  const handleAssistedExecute = async () => {
    if (!state?.latest_authorization || state.latest_authorization.status !== 'AUTHORIZED') {
      alert('Cannot execute: Action is not currently authorized.');
      return;
    }

    if (!window.confirm('Confirm execution of assisted irrigation for configured duration?')) {
      return;
    }

    try {
      setExecuting(true);
      setError(null);
      const res = await apiClient.post(`/irrigation/execute/${state.latest_authorization.id || 1}`);
      setActionSuccess(`Command dispatched: ${res.data.command_id} (${res.data.duration_seconds}s)`);
      fetchState();
      fetchHistory();
    } catch (err) {
      console.error('Assisted execution failed:', err);
      setError(err.response?.data?.detail || 'Failed to dispatch assisted irrigation.');
    } finally {
      setExecuting(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm flex items-center justify-center py-12">
        <div className="flex items-center gap-3 text-slate-500 text-sm">
          <RefreshCw className="w-5 h-5 animate-spin text-brand" />
          <span>Loading Production Irrigation Intelligence...</span>
        </div>
      </div>
    );
  }

  const isManualMode = state?.device?.irrigation_mode === 'MANUAL';
  const isPumpRunning = Boolean(state?.device?.pump_status);
  const isOnline = state?.device?.status === 'ONLINE';

  const getAuthBadge = (status) => {
    switch (status) {
      case 'AUTHORIZED':
        return {
          bg: 'bg-emerald-500 text-white',
          border: 'border-emerald-400',
          text: 'AUTHORIZED',
          icon: <ShieldCheck className="w-4 h-4" />
        };
      case 'DEFERRED':
        return {
          bg: 'bg-amber-500 text-white',
          border: 'border-amber-400',
          text: 'DEFERRED (COOLDOWN)',
          icon: <Clock className="w-4 h-4" />
        };
      case 'BLOCKED':
      default:
        return {
          bg: 'bg-rose-600 text-white',
          border: 'border-rose-500',
          text: 'BLOCKED',
          icon: <ShieldAlert className="w-4 h-4" />
        };
    }
  };

  const authBadge = getAuthBadge(state?.latest_authorization?.status);

  return (
    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 dark:border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Brain className="w-6 h-6 text-brand" />
            <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100">
              Production Irrigation Intelligence
            </h2>
            <span className="text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700 dark:bg-indigo-900/50 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
              V1.0 Safe Control
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Two-Layer Architecture: Agricultural Intelligence (Layer A) + Execution Safety Authorization (Layer B)
          </p>
        </div>

        {/* Status Pills */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Hardware Mode */}
          <span className={`text-[11px] font-bold px-2.5 py-1 rounded-lg border flex items-center gap-1.5 ${
            isManualMode 
              ? 'bg-amber-50 text-amber-800 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300' 
              : 'bg-blue-50 text-blue-800 border-blue-200 dark:bg-blue-950/40 dark:text-blue-300'
          }`}>
            <span className={`w-2 h-2 rounded-full ${isManualMode ? 'bg-amber-500' : 'bg-blue-500'}`}></span>
            Mode: {state?.device?.irrigation_mode || 'AUTO'}
          </span>

          {/* Deployment Mode */}
          <span className="text-[11px] font-bold px-2.5 py-1 rounded-lg bg-purple-50 text-purple-800 border border-purple-200 dark:bg-purple-950/40 dark:text-purple-300">
            {state?.intelligence_mode || 'SHADOW'} MODE
          </span>

          {/* Pump Status */}
          <span className={`text-[11px] font-bold px-2.5 py-1 rounded-lg border flex items-center gap-1.5 ${
            isPumpRunning 
              ? 'bg-emerald-500 text-white border-emerald-600 animate-pulse' 
              : 'bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300'
          }`}>
            <Power className="w-3.5 h-3.5" />
            Pump: {isPumpRunning ? 'RUNNING' : 'IDLE'}
          </span>
        </div>
      </div>

      {/* Alerts / Success Feedback */}
      {error && (
        <div className="bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 rounded-xl p-3.5 flex items-center gap-2 text-rose-800 dark:text-rose-300 text-xs">
          <ShieldAlert className="w-4 h-4 shrink-0 text-rose-600" />
          <span>{error}</span>
        </div>
      )}

      {actionSuccess && (
        <div className="bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 rounded-xl p-3.5 flex items-center gap-2 text-emerald-800 dark:text-emerald-300 text-xs">
          <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
          <span>{actionSuccess}</span>
        </div>
      )}

      {/* Manual Mode Warning Banner */}
      {isManualMode && (
        <div className="p-3.5 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 text-xs text-amber-900 dark:text-amber-200 flex items-start gap-2.5">
          <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold">Manual Mode Override Active:</span> Automatic irrigation execution is strictly disabled. The physical switch on the TERRAVYN device or manual dashboard switch controls the pump.
          </div>
        </div>
      )}

      {/* Dual Layer Decision Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Layer A: Agricultural Need */}
        <div className="p-5 rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700/80 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
              <Brain className="w-4 h-4 text-brand" /> Layer A: Agricultural Need
            </span>
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200">
              Confidence: {state?.latest_decision?.confidence || 0}%
            </span>
          </div>

          <div className="flex items-center gap-3 pt-1">
            <div className={`px-3.5 py-2 rounded-xl font-black text-lg ${
              state?.latest_decision?.decision === 'IRRIGATE'
                ? 'bg-amber-500 text-white'
                : state?.latest_decision?.decision === 'WAIT'
                ? 'bg-blue-600 text-white'
                : 'bg-emerald-600 text-white'
            }`}>
              {state?.latest_decision?.decision || 'MONITOR'}
            </div>
            <div className="text-xs text-slate-600 dark:text-slate-300">
              <p className="font-medium">
                {state?.latest_decision?.decision === 'IRRIGATE' ? 'Crop requires water replenishment.' : 'No immediate irrigation required.'}
              </p>
              <p className="text-[11px] text-slate-400">
                Evaluated: {state?.latest_decision?.timestamp ? dayjs(state.latest_decision.timestamp).format('hh:mm A') : 'N/A'}
              </p>
            </div>
          </div>

          {state?.latest_decision?.reasons && state.latest_decision.reasons.length > 0 && (
            <ul className="text-xs text-slate-600 dark:text-slate-300 space-y-1 pt-2 border-t border-slate-200 dark:border-slate-700">
              {state.latest_decision.reasons.slice(0, 2).map((r, i) => (
                <li key={i} className="flex items-start gap-1.5">
                  <span className="text-brand font-bold">•</span>
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Layer B: Execution Safety & Authorization */}
        <div className="p-5 rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700/80 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-emerald-600" /> Layer B: Execution Safety
            </span>
            <div className={`px-2.5 py-1 rounded-lg text-xs font-bold flex items-center gap-1 ${authBadge.bg}`}>
              {authBadge.icon}
              <span>{authBadge.text}</span>
            </div>
          </div>

          <div className="pt-1 text-xs text-slate-700 dark:text-slate-300">
            <p className="font-semibold text-slate-800 dark:text-slate-100 mb-1">
              Safety Reason:
            </p>
            <p className="text-xs text-slate-600 dark:text-slate-400 bg-white dark:bg-slate-900 p-2.5 rounded-lg border border-slate-200 dark:border-slate-800">
              {state?.latest_authorization?.reason || 'Awaiting evaluation.'}
            </p>
          </div>

          {/* Active Calibration Badge */}
          {state?.active_calibration && (
            <div className="text-[11px] text-indigo-700 dark:text-indigo-300 bg-indigo-50/80 dark:bg-indigo-950/40 p-2 rounded-lg border border-indigo-200 dark:border-indigo-800 flex items-center justify-between">
              <span className="font-semibold">
                Calibrated Trigger: {state.active_calibration.value}%
              </span>
              <span>
                Hysteresis: +{state.active_calibration.hysteresis_delta}%
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Action Buttons Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
        <div className="flex items-center gap-2">
          <button
            onClick={() => handleEvaluate(false)}
            disabled={evaluating || dryRunning || executing}
            className="px-3.5 py-2 text-xs font-bold rounded-xl border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-200 flex items-center gap-1.5 transition disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${evaluating ? 'animate-spin text-brand' : ''}`} />
            <span>{evaluating ? 'Evaluating...' : 'Re-Evaluate Both Layers'}</span>
          </button>

          <button
            onClick={handleDryRun}
            disabled={evaluating || dryRunning || executing}
            className="px-3.5 py-2 text-xs font-bold rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-800 dark:text-slate-200 flex items-center gap-1.5 transition disabled:opacity-50"
            title="Simulate decision and safety pipeline with zero pump actuation"
          >
            <Play className={`w-3.5 h-3.5 ${dryRunning ? 'animate-spin text-amber-500' : ''}`} />
            <span>{dryRunning ? 'Simulating...' : 'Dry Run (Simulate)'}</span>
          </button>
        </div>

        {/* Assisted Mode Execution Button */}
        {state?.intelligence_mode === 'ASSISTED' && state?.latest_authorization?.status === 'AUTHORIZED' && (
          <button
            onClick={handleAssistedExecute}
            disabled={executing || isManualMode}
            className="px-4 py-2 text-xs font-bold rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm flex items-center gap-1.5 transition disabled:opacity-50"
          >
            <Power className="w-3.5 h-3.5" />
            <span>{executing ? 'Dispatching...' : 'Approve & Execute (Assisted)'}</span>
          </button>
        )}
      </div>

      {/* Expandable Execution Audit Trail */}
      {history && (history.authorizations?.length > 0 || history.commands?.length > 0) && (
        <div className="pt-2 border-t border-slate-100 dark:border-slate-800">
          <button
            type="button"
            onClick={() => setShowDetails(!showDetails)}
            className="text-xs font-semibold text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 flex items-center gap-1"
          >
            <span>{showDetails ? 'Hide Execution Audit Log' : 'View Recent Execution Audit Log'}</span>
            {showDetails ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>

          {showDetails && (
            <div className="mt-3 space-y-2 animate-fadeIn">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">Recent Commands & Dispatches</span>
              {history.commands.map((cmd) => (
                <div key={cmd.id} className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 text-xs flex items-center justify-between">
                  <div>
                    <span className="font-mono font-bold text-slate-800 dark:text-slate-200 mr-2">{cmd.command_id}</span>
                    <span className="text-slate-500">Duration: {cmd.duration_seconds}s</span>
                    <span className="text-slate-400 text-[10px] ml-2">({dayjs(cmd.created_at).format('hh:mm A')})</span>
                  </div>
                  <span className={`px-2 py-0.5 text-[10px] font-bold rounded ${
                    cmd.status === 'EXECUTED' || cmd.status === 'SIMULATED'
                      ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200'
                      : cmd.status === 'SENT' || cmd.status === 'ACKNOWLEDGED'
                      ? 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-200'
                      : 'bg-slate-100 text-slate-700'
                  }`}>
                    {cmd.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default IrrigationIntelligencePanel;
