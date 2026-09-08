import React, { useState, useEffect } from 'react';
import apiClient from '../../api/client';
import {
  BrainCircuit, CheckCircle2, AlertTriangle, Clock, RefreshCw,
  TrendingUp, Activity, Play, Eye, GitBranch, ArrowRight, ShieldCheck,
  ChevronDown, ChevronUp, Sparkles, Layers, BookOpen, AlertCircle
} from 'lucide-react';
import dayjs from 'dayjs';

const LearningDashboardPanel = ({ farmId }) => {
  const [summary, setSummary] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [runningCycle, setRunningCycle] = useState(false);
  const [evaluating, setEvaluating] = useState(false);
  const [activeTab, setActiveTab] = useState('summary'); // 'summary' | 'timeline' | 'candidates'
  const [error, setError] = useState(null);
  const [actionSuccess, setActionSuccess] = useState(null);

  useEffect(() => {
    if (farmId) {
      fetchLearningData();
    }
  }, [farmId]);

  const fetchLearningData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [sumRes, timeRes, candRes] = await Promise.all([
        apiClient.get(`/learning/summary/${farmId}?days=30`),
        apiClient.get(`/learning/timeline/${farmId}?limit=25`),
        apiClient.get(`/learning/candidates?farm_id=${farmId}`),
      ]);
      setSummary(sumRes.data);
      setTimeline(timeRes.data);
      setCandidates(candRes.data);
    } catch (err) {
      console.error('Failed to load learning data:', err);
      setError(err.response?.data?.detail || 'Unable to load learning data.');
    } finally {
      setLoading(false);
    }
  };

  const handleRunLearningCycle = async () => {
    try {
      setRunningCycle(true);
      setError(null);
      setActionSuccess(null);
      const res = await apiClient.post(`/learning/run/${farmId}`);
      setActionSuccess('Full closed-loop learning cycle completed.');
      fetchLearningData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to run learning cycle.');
    } finally {
      setRunningCycle(false);
    }
  };

  const handleEvaluateOutcomes = async () => {
    try {
      setEvaluating(true);
      setError(null);
      setActionSuccess(null);
      await apiClient.post(`/learning/evaluate/${farmId}?window=SHORT_TERM`);
      setActionSuccess('Decision outcomes evaluated successfully.');
      fetchLearningData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to evaluate outcomes.');
    } finally {
      setEvaluating(false);
    }
  };

  const handleValidateCandidate = async (candidateId) => {
    try {
      setError(null);
      await apiClient.post(`/learning/candidates/${candidateId}/validate`);
      setActionSuccess(`Candidate #${candidateId} submitted to validation engine.`);
      fetchLearningData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit for validation.');
    }
  };

  const getClassificationBadge = (cls) => {
    switch (cls) {
      case 'CORRECT_IRRIGATION':
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300">Correct Irrigation</span>;
      case 'CORRECT_WAIT':
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300">Correct Wait</span>;
      case 'POSSIBLE_UNNECESSARY_IRRIGATION':
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300">Possible Unnecessary</span>;
      case 'POSSIBLE_MISSED_IRRIGATION':
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-300">Possible Missed</span>;
      case 'EXECUTION_FAILURE':
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300">Execution Failure</span>;
      default:
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300">Insufficient Data</span>;
    }
  };

  const getCandidateTypeBadge = (type) => {
    const colorMap = {
      IRRIGATION_PATTERN: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300',
      SENSOR_PATTERN: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/40 dark:text-indigo-300',
      FORECAST_ERROR: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300',
      KNOWLEDGE_CONFLICT: 'bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300',
      CALIBRATION_PATTERN: 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300',
    };
    const cls = colorMap[type] || 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300';
    return <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${cls}`}>{type?.replace(/_/g, ' ')}</span>;
  };

  if (loading) {
    return (
      <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 p-6 flex items-center justify-center min-h-[220px]">
        <div className="flex flex-col items-center gap-2">
          <RefreshCw className="w-6 h-6 text-emerald-600 animate-spin" />
          <p className="text-sm text-slate-500">Loading Terravyn Continuous Learning Engine...</p>
        </div>
      </div>
    );
  }

  const breakdown = summary?.decisions_summary?.classification_breakdown || {};
  const pipe = summary?.learning_pipeline || {};

  return (
    <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden">
      {/* Header */}
      <div className="p-6 border-b border-slate-100 dark:border-slate-800/60 bg-gradient-to-r from-emerald-50/50 via-teal-50/20 to-transparent dark:from-emerald-950/20 dark:via-teal-950/10 dark:to-transparent">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-emerald-600 text-white shadow-sm shadow-emerald-200 dark:shadow-none">
              <BrainCircuit className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-bold text-slate-900 dark:text-white">Terravyn Learning</h3>
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-900/60 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                  Closed-Loop V1
                </span>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Deterministic decision evaluation, pattern detection & continuous calibration
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleEvaluateOutcomes}
              disabled={evaluating || runningCycle}
              className="px-3 py-1.5 text-xs font-medium rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700/60 transition-colors flex items-center gap-1.5 shadow-sm disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${evaluating ? 'animate-spin' : ''}`} />
              Evaluate Outcomes
            </button>
            <button
              onClick={handleRunLearningCycle}
              disabled={runningCycle || evaluating}
              className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white transition-colors flex items-center gap-1.5 shadow-sm shadow-emerald-200 dark:shadow-none disabled:opacity-50"
            >
              <Sparkles className={`w-3.5 h-3.5 ${runningCycle ? 'animate-spin' : ''}`} />
              Run Full Learning Cycle
            </button>
          </div>
        </div>

        {/* Notifications */}
        {actionSuccess && (
          <div className="mt-3 p-2.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300 text-xs flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
            <span>{actionSuccess}</span>
          </div>
        )}
        {error && (
          <div className="mt-3 p-2.5 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-rose-800 dark:text-rose-300 text-xs flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0 text-rose-600" />
            <span>{error}</span>
          </div>
        )}

        {/* Navigation Tabs */}
        <div className="flex gap-2 mt-4">
          <button
            onClick={() => setActiveTab('summary')}
            className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
              activeTab === 'summary'
                ? 'bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
            }`}
          >
            Performance Overview
          </button>
          <button
            onClick={() => setActiveTab('candidates')}
            className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all flex items-center gap-1.5 ${
              activeTab === 'candidates'
                ? 'bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
            }`}
          >
            Learning Candidates ({candidates.length})
          </button>
          <button
            onClick={() => setActiveTab('timeline')}
            className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all flex items-center gap-1.5 ${
              activeTab === 'timeline'
                ? 'bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
            }`}
          >
            Decision Timeline ({timeline.length})
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="p-6">
        {/* TAB 1: SUMMARY */}
        {activeTab === 'summary' && (
          <div className="space-y-6">
            {/* Top Stat Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200/80 dark:border-slate-700/60">
                <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Total Decisions</span>
                <div className="text-2xl font-bold text-slate-900 dark:text-white mt-1">
                  {summary?.decisions_summary?.total_decisions || 0}
                </div>
                <span className="text-xs text-slate-400 mt-0.5 block">Last 30 days</span>
              </div>

              <div className="p-4 rounded-xl bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-200/80 dark:border-emerald-800/60">
                <span className="text-xs font-medium text-emerald-700 dark:text-emerald-400">Correct Outcomes</span>
                <div className="text-2xl font-bold text-emerald-700 dark:text-emerald-300 mt-1">
                  {(breakdown.CORRECT_IRRIGATION || 0) + (breakdown.CORRECT_WAIT || 0)}
                </div>
                <span className="text-xs text-emerald-600/70 dark:text-emerald-400/60 mt-0.5 block">
                  {breakdown.CORRECT_IRRIGATION || 0} irrigate / {breakdown.CORRECT_WAIT || 0} wait
                </span>
              </div>

              <div className="p-4 rounded-xl bg-amber-50/50 dark:bg-amber-950/20 border border-amber-200/80 dark:border-amber-800/60">
                <span className="text-xs font-medium text-amber-700 dark:text-amber-400">Possible Unnecessary</span>
                <div className="text-2xl font-bold text-amber-700 dark:text-amber-300 mt-1">
                  {breakdown.POSSIBLE_UNNECESSARY_IRRIGATION || 0}
                </div>
                <span className="text-xs text-amber-600/70 dark:text-amber-400/60 mt-0.5 block">Rain observed post-irrigation</span>
              </div>

              <div className="p-4 rounded-xl bg-rose-50/50 dark:bg-rose-950/20 border border-rose-200/80 dark:border-rose-800/60">
                <span className="text-xs font-medium text-rose-700 dark:text-rose-400">Possible Missed</span>
                <div className="text-2xl font-bold text-rose-700 dark:text-rose-300 mt-1">
                  {breakdown.POSSIBLE_MISSED_IRRIGATION || 0}
                </div>
                <span className="text-xs text-rose-600/70 dark:text-rose-400/60 mt-0.5 block">Stress noted after wait</span>
              </div>
            </div>

            {/* Learning Pipeline Overview & Calibration */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-800/20">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3 flex items-center gap-1.5">
                  <GitBranch className="w-3.5 h-3.5 text-emerald-600" />
                  Continuous Improvement Pipeline
                </h4>
                <div className="grid grid-cols-3 gap-2">
                  <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/60 text-center">
                    <span className="text-lg font-bold text-slate-800 dark:text-slate-200">{pipe.experimental || 0}</span>
                    <span className="text-[11px] text-slate-500 block">Experimental</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-purple-50 dark:bg-purple-950/40 text-center">
                    <span className="text-lg font-bold text-purple-700 dark:text-purple-300">{pipe.under_review || 0}</span>
                    <span className="text-[11px] text-purple-600 block">Under Review</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 text-center">
                    <span className="text-lg font-bold text-emerald-700 dark:text-emerald-300">{pipe.validated || 0}</span>
                    <span className="text-[11px] text-emerald-600 block">Validated</span>
                  </div>
                </div>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-3 italic">
                  Note: Candidates do not modify production rules automatically. All changes pass through validation, shadow testing, and explicit activation.
                </p>
              </div>

              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-800/20">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3 flex items-center gap-1.5">
                  <ShieldCheck className="w-3.5 h-3.5 text-blue-600" />
                  Active Field Calibration
                </h4>
                {summary?.active_calibration ? (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium text-slate-600 dark:text-slate-300">Parameter:</span>
                      <span className="text-xs font-mono text-slate-900 dark:text-white">{summary.active_calibration.parameter}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium text-slate-600 dark:text-slate-300">Active Value:</span>
                      <span className="text-xs font-bold text-emerald-600">{summary.active_calibration.value}%</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium text-slate-600 dark:text-slate-300">Version / Scope:</span>
                      <span className="text-xs text-slate-500">v{summary.active_calibration.version} ({summary.active_calibration.scope})</span>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-4">
                    <p className="text-xs text-slate-500">Using standard ICAR-IIPR baseline knowledge thresholds.</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: CANDIDATES */}
        {activeTab === 'candidates' && (
          <div className="space-y-3">
            {candidates.length === 0 ? (
              <div className="text-center py-10">
                <BrainCircuit className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                <p className="text-sm text-slate-600 dark:text-slate-400">No learning candidates detected yet.</p>
                <p className="text-xs text-slate-400 mt-1">Run a full learning cycle to analyze outcomes for repeating patterns.</p>
              </div>
            ) : (
              candidates.map((cand) => (
                <div
                  key={cand.id}
                  className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-800/40 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                >
                  <div className="space-y-1.5 flex-1">
                    <div className="flex items-center gap-2">
                      {getCandidateTypeBadge(cand.candidate_type)}
                      <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                        Status: {cand.status}
                      </span>
                      <span className="text-xs text-slate-400">
                        Confidence: {cand.confidence}%
                      </span>
                    </div>
                    <p className="text-xs text-slate-700 dark:text-slate-300 font-medium">
                      {cand.pattern_description}
                    </p>
                    <div className="flex items-center gap-4 text-[11px] text-slate-400">
                      <span>{cand.event_count} independent events</span>
                      <span>•</span>
                      <span>Quality: {cand.data_quality}</span>
                      <span>•</span>
                      <span>Priority: {cand.priority}</span>
                    </div>
                  </div>

                  {cand.status === 'EXPERIMENTAL' && (
                    <button
                      onClick={() => handleValidateCandidate(cand.id)}
                      className="px-3 py-1.5 text-xs font-medium rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white transition-colors shrink-0"
                    >
                      Submit for Validation
                    </button>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {/* TAB 3: TIMELINE */}
        {activeTab === 'timeline' && (
          <div className="space-y-3">
            {timeline.length === 0 ? (
              <div className="text-center py-10">
                <Clock className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                <p className="text-sm text-slate-600 dark:text-slate-400">No decision outcomes evaluated yet.</p>
              </div>
            ) : (
              <div className="space-y-2">
                {timeline.map((entry) => (
                  <div
                    key={entry.outcome_id}
                    className="p-3.5 rounded-xl border border-slate-200/70 dark:border-slate-800 bg-white dark:bg-slate-800/30 flex items-start justify-between gap-4"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        {getClassificationBadge(entry.classification)}
                        <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
                          {entry.decision} ({entry.actual_action})
                        </span>
                        <span className="text-xs text-slate-400">
                          {dayjs(entry.timestamp).format('MMM D, h:mm A')}
                        </span>
                      </div>
                      <p className="text-xs text-slate-600 dark:text-slate-400">
                        Stage: <span className="font-medium text-slate-700 dark:text-slate-300">{entry.growth_stage}</span> • Pre: {entry.pre_moisture}% • Post: {entry.post_moisture}% {entry.sensor_delta !== null && `(Δ ${entry.sensor_delta > 0 ? '+' : ''}${entry.sensor_delta}%)`}
                      </p>
                      {entry.reasons && entry.reasons.length > 0 && (
                        <p className="text-[11px] text-slate-500 italic">
                          "{entry.reasons[0]}"
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default LearningDashboardPanel;
