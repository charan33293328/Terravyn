import React, { useState, useEffect } from 'react';
import apiClient from '../../api/client';
import {
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Layers,
  Scale,
  RotateCcw,
  Eye,
  Sliders,
  Sparkles,
  Info,
  Check,
  XCircle,
  HelpCircle,
  TrendingUp,
  Activity
} from 'lucide-react';

const KnowledgeCalibration = () => {
  const [activeTab, setActiveTab] = useState('calibrations'); // 'calibrations' | 'validations' | 'outcomes'
  const [calibrations, setCalibrations] = useState([]);
  const [validationRecords, setValidationRecords] = useState([]);
  const [outcomeData, setOutcomeData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionSuccess, setActionSuccess] = useState(null);

  // Comparison modal
  const [selectedCalibration, setSelectedCalibration] = useState(null);
  const [comparisonData, setComparisonData] = useState(null);
  const [loadingComparison, setLoadingComparison] = useState(false);

  useEffect(() => {
    fetchData();
  }, [activeTab]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      if (activeTab === 'calibrations') {
        const res = await apiClient.get('/api/validation/calibrations');
        setCalibrations(res.data || []);
      } else if (activeTab === 'validations') {
        const res = await apiClient.get('/api/validation/records');
        setValidationRecords(res.data || []);
      } else if (activeTab === 'outcomes') {
        const res = await apiClient.get('/api/validation/decisions/outcomes');
        setOutcomeData(res.data || null);
      }
    } catch (err) {
      console.error('Failed to load validation/calibration data:', err);
      setError('Unable to load records. Please check API connection.');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenComparison = async (cal) => {
    setSelectedCalibration(cal);
    setLoadingComparison(true);
    try {
      const res = await apiClient.get(`/api/validation/calibrations/${cal.id}/comparison`);
      setComparisonData(res.data);
    } catch (err) {
      alert('Failed to load comparison: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoadingComparison(false);
    }
  };

  const handleEnableShadow = async (calId) => {
    try {
      await apiClient.post(`/api/validation/calibrations/${calId}/shadow`);
      setActionSuccess('Shadow mode enabled. Decisions will be evaluated in parallel without pump actuation.');
      setTimeout(() => setActionSuccess(null), 3000);
      fetchData();
    } catch (err) {
      alert('Failed to enable shadow mode: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleActivate = async (calId) => {
    if (!window.confirm('Are you sure you want to activate this calibration version for production decisions?')) return;
    try {
      await apiClient.post(`/api/validation/calibrations/${calId}/activate`);
      setActionSuccess('Calibration activated successfully. It is now active for field decision evaluation.');
      setTimeout(() => setActionSuccess(null), 3000);
      if (selectedCalibration) setSelectedCalibration(null);
      fetchData();
    } catch (err) {
      alert('Failed to activate calibration: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleRollback = async (calId) => {
    if (!window.confirm('Rollback to previous configuration version?')) return;
    try {
      await apiClient.post(`/api/validation/calibrations/${calId}/rollback`);
      setActionSuccess('Rollback successful. Previous configuration version is now active.');
      setTimeout(() => setActionSuccess(null), 3000);
      fetchData();
    } catch (err) {
      alert('Rollback failed: ' + (err.response?.data?.detail || err.message));
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'ACTIVE':
        return <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 flex items-center gap-1 w-fit"><CheckCircle2 className="w-3 h-3" /> ACTIVE</span>;
      case 'SHADOW':
        return <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-purple-100 text-purple-800 flex items-center gap-1 w-fit"><Eye className="w-3 h-3" /> SHADOW</span>;
      case 'EXPERIMENTAL':
        return <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-amber-100 text-amber-800 flex items-center gap-1 w-fit"><Scale className="w-3 h-3" /> EXPERIMENTAL</span>;
      case 'SUPERSEDED':
        return <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-slate-100 text-slate-600 flex items-center gap-1 w-fit"><RotateCcw className="w-3 h-3" /> SUPERSEDED</span>;
      case 'VALIDATED':
        return <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-blue-100 text-blue-800 flex items-center gap-1 w-fit"><ShieldCheck className="w-3 h-3" /> VALIDATED</span>;
      case 'PROVISIONAL':
        return <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-teal-100 text-teal-800 flex items-center gap-1 w-fit"><Sparkles className="w-3 h-3" /> PROVISIONAL</span>;
      case 'REJECTED':
        return <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-rose-100 text-rose-800 flex items-center gap-1 w-fit"><XCircle className="w-3 h-3" /> REJECTED</span>;
      default:
        return <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-700">{status}</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2">
              <ShieldCheck className="w-7 h-7 text-emerald-600" />
              Knowledge Validation & Calibration Engine V1
            </h1>
            <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
              Prompt 7
            </span>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Deterministic validation pathways, scoped field calibrations, range trigger zones, hysteresis, and shadow mode.
          </p>
        </div>

        {/* Safety Indicator */}
        <div className="bg-amber-50 border border-amber-200 px-3 py-2 rounded-lg text-xs text-amber-900 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-700 shrink-0" />
          <span>
            <strong>Hardware Actuation Guard:</strong> Candidate calibrations do NOT trigger pumps until explicitly approved and activated.
          </span>
        </div>
      </div>

      {actionSuccess && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          {actionSuccess}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 border-b border-slate-200">
        <button
          onClick={() => setActiveTab('calibrations')}
          className={`px-4 py-2.5 text-sm font-bold border-b-2 transition flex items-center gap-2 ${
            activeTab === 'calibrations'
              ? 'border-emerald-600 text-emerald-700'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Sliders className="w-4 h-4" /> Field Calibrations ({calibrations.length})
        </button>
        <button
          onClick={() => setActiveTab('validations')}
          className={`px-4 py-2.5 text-sm font-bold border-b-2 transition flex items-center gap-2 ${
            activeTab === 'validations'
              ? 'border-emerald-600 text-emerald-700'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <ShieldCheck className="w-4 h-4" /> Validation Records ({validationRecords.length})
        </button>
        <button
          onClick={() => setActiveTab('outcomes')}
          className={`px-4 py-2.5 text-sm font-bold border-b-2 transition flex items-center gap-2 ${
            activeTab === 'outcomes'
              ? 'border-emerald-600 text-emerald-700'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Activity className="w-4 h-4" /> Decision Outcomes & Audit
        </button>
      </div>

      {loading ? (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center text-slate-500 flex items-center justify-center gap-2">
          <RefreshCw className="w-5 h-5 animate-spin text-emerald-600" /> Loading records...
        </div>
      ) : error ? (
        <div className="bg-rose-50 border border-rose-200 text-rose-700 p-4 rounded-xl text-sm">
          {error}
        </div>
      ) : (
        <>
          {/* TAB 1: FIELD CALIBRATIONS */}
          {activeTab === 'calibrations' && (
            <div className="space-y-4">
              {calibrations.length === 0 ? (
                <div className="bg-white rounded-xl border border-dashed border-slate-200 p-12 text-center text-slate-500">
                  <Sliders className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                  <p className="font-semibold text-slate-700">No field calibrations recorded yet.</p>
                  <p className="text-xs text-slate-500 mt-1">Calibrations are generated from verified trial observations or researcher input.</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 gap-4">
                  {calibrations.map((cal) => (
                    <div
                      key={cal.id}
                      className={`bg-white rounded-xl border p-5 shadow-xs transition space-y-3 ${
                        cal.status === 'ACTIVE'
                          ? 'border-emerald-300 ring-1 ring-emerald-300'
                          : cal.status === 'SHADOW'
                          ? 'border-purple-200 bg-purple-50/10'
                          : 'border-slate-200'
                      }`}
                    >
                      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
                        <div className="flex items-center gap-3">
                          {getStatusBadge(cal.status)}
                          <h3 className="font-bold text-slate-900 text-base">
                            {cal.parameter} (v{cal.version})
                          </h3>
                          <span className="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-mono">
                            Scope: {cal.scope}
                          </span>
                        </div>

                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleOpenComparison(cal)}
                            className="px-3 py-1.5 border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-semibold flex items-center gap-1 transition"
                          >
                            <Scale className="w-3.5 h-3.5 text-slate-500" /> Compare
                          </button>

                          {cal.status === 'EXPERIMENTAL' && (
                            <button
                              onClick={() => handleEnableShadow(cal.id)}
                              className="px-3 py-1.5 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-xs font-semibold flex items-center gap-1 transition"
                            >
                              <Eye className="w-3.5 h-3.5" /> Enable Shadow
                            </button>
                          )}

                          {(cal.status === 'SHADOW' || cal.status === 'EXPERIMENTAL') && (
                            <button
                              onClick={() => handleActivate(cal.id)}
                              className="px-3 py-1.5 bg-emerald-700 hover:bg-emerald-800 text-white rounded-lg text-xs font-semibold flex items-center gap-1 transition"
                            >
                              <Check className="w-3.5 h-3.5" /> Activate Version
                            </button>
                          )}

                          {cal.status === 'ACTIVE' && (
                            <button
                              onClick={() => handleRollback(cal.id)}
                              title="Revert to previous approved configuration"
                              className="px-3 py-1.5 border border-amber-300 hover:bg-amber-50 text-amber-800 rounded-lg text-xs font-semibold flex items-center gap-1 transition"
                            >
                              <RotateCcw className="w-3.5 h-3.5 text-amber-600" /> Rollback
                            </button>
                          )}
                        </div>
                      </div>

                      {/* Calibration Parameters & Values */}
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-50 p-3 rounded-lg border border-slate-200/60 text-xs">
                        <div>
                          <span className="text-slate-400 block uppercase text-[10px] font-semibold">Growth Stage</span>
                          <span className="font-bold text-slate-800">{cal.growth_stage || 'All Stages'}</span>
                        </div>
                        <div>
                          <span className="text-slate-400 block uppercase text-[10px] font-semibold">Trigger Threshold</span>
                          <span className="font-bold text-emerald-800 text-sm">
                            {cal.value ? `${cal.value}%` : '—'}
                          </span>
                        </div>
                        <div>
                          <span className="text-slate-400 block uppercase text-[10px] font-semibold">Stop Threshold (Hysteresis)</span>
                          <span className="font-bold text-slate-800">
                            {cal.value_range?.stop_threshold ? `${cal.value_range.stop_threshold}%` : `+${cal.hysteresis_delta || 10}%`}
                          </span>
                        </div>
                        <div>
                          <span className="text-slate-400 block uppercase text-[10px] font-semibold">Evidence & Samples</span>
                          <span className="font-bold text-slate-800">
                            {cal.sample_count} observations • Conf: {cal.confidence}%
                          </span>
                        </div>
                      </div>

                      <p className="text-xs text-slate-600 italic">
                        "{cal.rationale || 'No rationale notes recorded.'}"
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 2: VALIDATION RECORDS */}
          {activeTab === 'validations' && (
            <div className="space-y-4">
              {validationRecords.length === 0 ? (
                <div className="bg-white rounded-xl border border-dashed border-slate-200 p-12 text-center text-slate-500">
                  <ShieldCheck className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                  <p className="font-semibold text-slate-700">No validation records executed yet.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {validationRecords.map((rec) => (
                    <div key={rec.id} className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs space-y-2 text-xs">
                      <div className="flex justify-between items-center">
                        <div className="flex items-center gap-2">
                          {getStatusBadge(rec.status)}
                          <span className="font-bold text-slate-900 text-sm">
                            {rec.target_type} #{rec.target_id}
                          </span>
                          <span className="text-slate-400">•</span>
                          <span className="text-slate-600">
                            Confidence: <strong>{rec.confidence}/100 ({rec.confidence_level})</strong>
                          </span>
                        </div>
                        <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-mono text-[11px]">
                          Next: {rec.recommended_next_step}
                        </span>
                      </div>

                      {/* 10 Dimensional Scores Grid */}
                      {rec.dimension_scores && (
                        <div className="grid grid-cols-5 gap-2 bg-slate-50 p-2.5 rounded-lg border border-slate-200/60 text-[11px]">
                          <div>Source: <strong>{rec.dimension_scores.source_quality}</strong></div>
                          <div>Applicability: <strong>{rec.dimension_scores.applicability}</strong></div>
                          <div>Sample Size: <strong>{rec.dimension_scores.sample_size}</strong></div>
                          <div>Measure Quality: <strong>{rec.dimension_scores.measurement_quality}</strong></div>
                          <div>Consistency: <strong>{rec.dimension_scores.consistency}</strong></div>
                        </div>
                      )}

                      {rec.reasons?.length > 0 && (
                        <div className="text-slate-700">
                          <strong className="text-emerald-700">Supporting Reasons:</strong> {rec.reasons.join(' ')}
                        </div>
                      )}

                      {rec.limitations?.length > 0 && (
                        <div className="text-amber-800">
                          <strong>Limitations & Caveats:</strong> {rec.limitations.join(' ')}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 3: DECISION OUTCOMES */}
          {activeTab === 'outcomes' && outcomeData && (
            <div className="space-y-6">
              {/* Summary Stats */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs text-center">
                  <span className="text-xs text-slate-500 uppercase tracking-wider block mb-1">Total Evaluated</span>
                  <span className="text-2xl font-black text-slate-900">{outcomeData.statistics.total_evaluated}</span>
                </div>
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs text-center">
                  <span className="text-xs text-slate-500 uppercase tracking-wider block mb-1">Accuracy Rate</span>
                  <span className="text-2xl font-black text-emerald-700">
                    {outcomeData.statistics.accuracy_rate_pct !== null ? `${outcomeData.statistics.accuracy_rate_pct}%` : 'N/A'}
                  </span>
                </div>
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs text-center">
                  <span className="text-xs text-slate-500 uppercase tracking-wider block mb-1">Correct Decisions</span>
                  <span className="text-2xl font-black text-slate-800">
                    {outcomeData.statistics.correct_wait_count + outcomeData.statistics.correct_irrigation_count}
                  </span>
                </div>
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs text-center">
                  <span className="text-xs text-slate-500 uppercase tracking-wider block mb-1">Missed Irrigations</span>
                  <span className="text-2xl font-black text-rose-700">{outcomeData.statistics.missed_irrigation_count}</span>
                </div>
              </div>

              {/* Recent Outcomes Table */}
              <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
                <div className="px-5 py-3 border-b border-slate-100 font-bold text-sm text-slate-800">
                  Recent Decision Audit Logs
                </div>
                <div className="divide-y divide-slate-100 text-xs">
                  {outcomeData.recent_outcomes?.map((out) => (
                    <div key={out.id} className="p-4 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                            out.classification.includes('CORRECT') ? 'bg-green-100 text-green-800' : 'bg-rose-100 text-rose-800'
                          }`}>
                            {out.classification}
                          </span>
                          <span className="font-semibold text-slate-800">Decision #{out.decision_log_id}</span>
                        </div>
                        <p className="text-slate-500 mt-1">{out.plant_response_summary}</p>
                      </div>
                      <span className="text-slate-400 font-mono text-[11px] shrink-0">
                        {new Date(out.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* Candidate Comparison Modal */}
      {selectedCalibration && comparisonData && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-xl shadow-xl border border-slate-200 max-w-lg w-full p-6 space-y-4">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h3 className="font-bold text-slate-900 text-base flex items-center gap-2">
                <Scale className="w-5 h-5 text-emerald-700" />
                Candidate vs Current Production
              </h3>
              <button
                onClick={() => setSelectedCalibration(null)}
                className="text-slate-400 hover:text-slate-600 font-bold"
              >
                ✕
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-1">
                <span className="text-[10px] text-slate-500 uppercase font-bold block">Current Production</span>
                <span className="text-base font-bold text-slate-800">
                  {comparisonData.current_active.value}%
                </span>
                <span className="text-slate-500 block">Version: {comparisonData.current_active.version}</span>
                <span className="text-slate-500 block">Status: {comparisonData.current_active.status}</span>
              </div>

              <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg space-y-1">
                <span className="text-[10px] text-emerald-800 uppercase font-bold block">Candidate Calibration</span>
                <span className="text-base font-bold text-emerald-900">
                  {comparisonData.candidate.value}%
                </span>
                <span className="text-slate-600 block">Version: {comparisonData.candidate.version}</span>
                <span className="text-slate-600 block">Confidence: {comparisonData.candidate.confidence}%</span>
              </div>
            </div>

            <div className="bg-slate-50 p-3 rounded-lg border border-slate-200 text-xs space-y-1">
              <div>
                <strong>Threshold Difference:</strong> {comparisonData.comparison.threshold_difference > 0 ? `+${comparisonData.comparison.threshold_difference}%` : `${comparisonData.comparison.threshold_difference}%`}
              </div>
              <div>
                <strong>Expected Impact:</strong> {comparisonData.comparison.expected_water_impact}
              </div>
              <div>
                <strong>Risk Assessment:</strong> <span className="font-semibold text-emerald-700">{comparisonData.comparison.risk_assessment}</span>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setSelectedCalibration(null)}
                className="px-4 py-2 border border-slate-200 text-slate-700 rounded-lg text-xs font-semibold hover:bg-slate-50 transition"
              >
                Close
              </button>
              {selectedCalibration.status !== 'ACTIVE' && (
                <button
                  type="button"
                  onClick={() => handleActivate(selectedCalibration.id)}
                  className="px-4 py-2 bg-emerald-700 hover:bg-emerald-800 text-white rounded-lg text-xs font-semibold transition"
                >
                  Activate Version {selectedCalibration.version}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default KnowledgeCalibration;
