import React, { useState, useEffect } from 'react';
import apiClient from '../../api/client';
import { 
  Brain, Droplets, Clock, CheckCircle2, AlertTriangle, 
  RefreshCw, Sprout, CloudRain, Sparkles, ShieldAlert, 
  Info, Edit3, Check, X, BookOpen, ChevronDown, ChevronUp, ExternalLink, Sliders
} from 'lucide-react';
import dayjs from 'dayjs';
import KnowledgeExplorerModal from '../knowledge/KnowledgeExplorerModal';

const STAGES = [
  "Sowing",
  "Germination",
  "Seedling",
  "Vegetative",
  "Flowering",
  "Pod Formation",
  "Pod Filling",
  "Maturity / Harvest"
];

const TerravynDecisionCard = ({ farms = [], initialFarmId = null }) => {
  const [selectedFarmId, setSelectedFarmId] = useState(initialFarmId);
  const [decisionData, setDecisionData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [evaluating, setEvaluating] = useState(false);
  const [error, setError] = useState(null);
  const [showOverrideModal, setShowOverrideModal] = useState(false);
  const [selectedOverrideStage, setSelectedOverrideStage] = useState('');
  const [savingStage, setSavingStage] = useState(false);
  const [showEvidence, setShowEvidence] = useState(false);
  const [showKnowledgeModal, setShowKnowledgeModal] = useState(false);

  useEffect(() => {
    if (!selectedFarmId && farms && farms.length > 0) {
      setSelectedFarmId(farms[0].id);
    }
  }, [farms, selectedFarmId]);

  useEffect(() => {
    if (selectedFarmId) {
      fetchDecision(selectedFarmId);
    }
  }, [selectedFarmId]);

  const fetchDecision = async (farmId, forceEvaluate = false) => {
    try {
      if (forceEvaluate) {
        setEvaluating(true);
      } else {
        setLoading(true);
      }
      setError(null);

      const url = forceEvaluate
        ? `/farmer/farms/${farmId}/decision/evaluate`
        : `/farmer/farms/${farmId}/decision`;

      const res = forceEvaluate
        ? await apiClient.post(url)
        : await apiClient.get(url);

      setDecisionData(res.data);
      setSelectedOverrideStage(res.data.growth_stage);
    } catch (err) {
      console.error("Failed to fetch decision:", err);
      setError(err.response?.data?.detail || "Unable to compute decision recommendation.");
    } finally {
      setLoading(false);
      setEvaluating(false);
    }
  };

  const handleStageOverride = async (stage) => {
    try {
      setSavingStage(true);
      await apiClient.post(`/farmer/farms/${selectedFarmId}/stage-override`, {
        stage: stage || null
      });
      setShowOverrideModal(false);
      fetchDecision(selectedFarmId, true);
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to update growth stage");
    } finally {
      setSavingStage(false);
    }
  };

  const getDecisionBadge = (decision) => {
    switch (decision?.toUpperCase()) {
      case 'IRRIGATE':
        return {
          bg: 'bg-amber-500 text-white',
          border: 'border-amber-400',
          text: 'IRRIGATE',
          sub: 'Moisture deficit detected',
          icon: <Droplets className="w-5 h-5" />
        };
      case 'WAIT':
        return {
          bg: 'bg-blue-600 text-white',
          border: 'border-blue-500',
          text: 'WAIT',
          sub: 'Rain forecast or cooldown active',
          icon: <Clock className="w-5 h-5" />
        };
      case 'MONITOR':
        return {
          bg: 'bg-emerald-600 text-white',
          border: 'border-emerald-500',
          text: 'MONITOR',
          sub: 'Moisture level satisfactory',
          icon: <CheckCircle2 className="w-5 h-5" />
        };
      case 'ALERT':
      default:
        return {
          bg: 'bg-rose-600 text-white',
          border: 'border-rose-500',
          text: 'ALERT',
          sub: 'Sensor anomaly or offline',
          icon: <AlertTriangle className="w-5 h-5" />
        };
    }
  };

  if (!farms || farms.length === 0) return null;

  const badge = getDecisionBadge(decisionData?.decision);

  return (
    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 dark:border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Brain className="w-6 h-6 text-brand" />
            <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100">
              Terravyn Decision Engine
            </h2>
            <span className="text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded-full bg-brand/10 text-brand border border-brand/20">
              {decisionData?.engine_version || 'green-gram-irrigation-v1'}
            </span>
            {decisionData?.factors?.calibration_info?.calibrated && (
              <span className="text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700 dark:bg-indigo-900/50 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800 flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3 text-indigo-600 dark:text-indigo-400" />
                Field Calibrated (v{decisionData.factors.calibration_info.version})
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Deterministic multi-factor agronomic reasoning (Crop • Soil • ESP32 Sensor • Weather)
          </p>
        </div>

        <div className="flex items-center gap-3">
          {farms.length > 1 && (
            <select
              value={selectedFarmId || ''}
              onChange={(e) => setSelectedFarmId(parseInt(e.target.value))}
              className="text-sm px-3 py-1.5 border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 rounded-lg text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand"
            >
              {farms.map((f) => (
                <option key={f.id} value={f.id}>
                  {f.name} {f.plot_type && f.plot_type !== 'STANDARD' ? `[${f.plot_type}]` : ''}
                </option>
              ))}
            </select>
          )}

          <button
            onClick={() => fetchDecision(selectedFarmId, true)}
            disabled={evaluating || loading}
            className="p-2 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300 transition disabled:opacity-40"
            title="Re-evaluate decision now"
          >
            <RefreshCw className={`w-4 h-4 ${evaluating ? 'animate-spin text-brand' : ''}`} />
          </button>
        </div>
      </div>

      {loading && (
        <div className="py-12 flex flex-col items-center justify-center space-y-3">
          <div className="w-8 h-8 border-3 border-brand border-t-transparent rounded-full animate-spin"></div>
          <p className="text-sm text-slate-500">Evaluating agronomic decision factors...</p>
        </div>
      )}

      {error && !loading && (
        <div className="bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 rounded-xl p-4 flex items-center gap-3 text-red-700 dark:text-red-300 text-xs">
          <ShieldAlert className="w-5 h-5 shrink-0 text-red-500" />
          <span>{error}</span>
        </div>
      )}

      {!loading && decisionData && (
        <div className="space-y-6">
          {/* Research Intelligence Advisory Notification */}
          {decisionData?.factors?.research_intelligence?.research_triggered && (
            <div className="flex items-center justify-between p-3 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-xs text-emerald-800 dark:text-emerald-300 animate-fadeIn">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
                <span className="font-medium">Terravyn acquired relevant agricultural research from approved institutions for this situation.</span>
              </div>
              <button
                type="button"
                onClick={() => setShowEvidence(true)}
                className="text-[11px] font-bold text-emerald-700 dark:text-emerald-400 hover:underline flex items-center gap-1 shrink-0 ml-2"
              >
                <span>View Evidence</span>
                <ChevronDown className="w-3 h-3" />
              </button>
            </div>
          )}

          {/* Field Calibration Advisory Banner */}
          {decisionData?.factors?.calibration_info?.calibrated && (
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-3.5 rounded-xl bg-indigo-50/80 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-800/80 text-xs text-indigo-950 dark:text-indigo-200 animate-fadeIn shadow-xs">
              <div className="flex items-center gap-2.5">
                <div className="p-1.5 rounded-lg bg-indigo-100 dark:bg-indigo-900/60 text-indigo-700 dark:text-indigo-300">
                  <Sliders className="w-4 h-4" />
                </div>
                <div>
                  <span className="font-bold text-indigo-900 dark:text-indigo-100">
                    Field-Calibrated (v{decisionData.factors.calibration_info.version}):
                  </span>{' '}
                  <span className="text-slate-600 dark:text-slate-300">
                    Calibrated to this field's {decisionData.factors.soil_type || 'soil'} behavior for {decisionData.growth_stage} stage.
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-2 self-start sm:self-auto shrink-0">
                {decisionData.factors.calibration_info.hysteresis_delta != null && (
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-indigo-100 dark:bg-indigo-900/80 text-indigo-800 dark:text-indigo-200 border border-indigo-200/60 dark:border-indigo-700/50">
                    Hysteresis: +{decisionData.factors.calibration_info.hysteresis_delta}%
                  </span>
                )}
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md bg-indigo-600 text-white">
                  Active
                </span>
              </div>
            </div>
          )}

          {/* Main Decision Banner */}
          <div className="flex flex-col md:flex-row items-stretch gap-4">
            {/* Primary Recommendation Badge */}
            <div className={`flex-1 ${badge.bg} rounded-2xl p-5 shadow-sm flex flex-col justify-between`}>
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold tracking-wider uppercase text-white/90">
                  Irrigation Recommendation
                </span>
                <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-white/20 text-white">
                  {decisionData.confidence}% Confidence
                </span>
              </div>
              <div className="my-3 flex items-center gap-3">
                <div className="p-3 bg-white/20 rounded-xl">
                  {badge.icon}
                </div>
                <div>
                  <h3 className="text-3xl font-black tracking-tight">{badge.text}</h3>
                  <p className="text-xs text-white/90 font-medium">{badge.sub}</p>
                </div>
              </div>
              <div className="text-[11px] text-white/80 border-t border-white/20 pt-2 flex items-center justify-between">
                <span>Evaluated: {dayjs(decisionData.generated_at).format('hh:mm A')}</span>
                <span>Plot: {decisionData.plot_type}</span>
              </div>
            </div>

            {/* Crop Stage & Variety Card */}
            <div className="bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 rounded-2xl p-5 flex flex-col justify-between md:w-80">
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                    <Sprout className="w-3.5 h-3.5 text-emerald-600" /> Crop Profile
                  </span>
                  <button
                    onClick={() => setShowOverrideModal(true)}
                    className="text-[11px] text-brand hover:underline font-medium flex items-center gap-1"
                  >
                    <Edit3 className="w-3 h-3" /> Adjust Stage
                  </button>
                </div>

                <div className="mt-2.5">
                  <h4 className="font-bold text-slate-800 dark:text-slate-100 text-base">
                    {decisionData.crop}
                  </h4>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Variety: {decisionData.variety || 'IPM 02-03'}
                  </p>
                </div>

                <div className="mt-3 flex items-center gap-2">
                  <span className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-emerald-100 dark:bg-emerald-900/50 text-emerald-800 dark:text-emerald-200">
                    Stage: {decisionData.growth_stage}
                  </span>
                  {decisionData.growth_stage_manual && (
                    <span className="text-[10px] bg-amber-100 text-amber-800 px-1.5 py-0.5 rounded font-medium">
                      Manual
                    </span>
                  )}
                </div>
              </div>

              <p className="text-[11px] text-slate-400 mt-3 pt-2 border-t border-slate-200 dark:border-slate-700">
                Stage dictates water stress vulnerability and threshold offset.
              </p>
            </div>
          </div>

          {/* Key Evaluation Factors Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 rounded-xl p-3">
              <span className="text-[11px] text-slate-500 dark:text-slate-400 flex items-center gap-1">
                <Droplets className="w-3 h-3 text-cyan-500" /> Soil Moisture
              </span>
              <p className="text-base font-bold text-slate-800 dark:text-slate-100 mt-1">
                {decisionData.factors.soil_moisture != null ? `${decisionData.factors.soil_moisture}%` : 'N/A'}
              </p>
              <p className="text-[10px] text-slate-400 mt-0.5">
                Target: &gt;{decisionData.factors.effective_threshold != null ? `${decisionData.factors.effective_threshold}%` : '40%'}
              </p>
              {decisionData.factors.calibration_info?.calibrated && (
                <span className="inline-block mt-1 text-[9px] font-bold px-1.5 py-0.5 rounded bg-indigo-100 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300">
                  Field-Calibrated v{decisionData.factors.calibration_info.version}
                </span>
              )}
            </div>

            <div className="bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 rounded-xl p-3">
              <span className="text-[11px] text-slate-500 dark:text-slate-400 flex items-center gap-1">
                <CloudRain className="w-3 h-3 text-blue-500" /> Rain 24h
              </span>
              <p className="text-base font-bold text-slate-800 dark:text-slate-100 mt-1">
                {decisionData.factors.rainfall_forecast_24h != null ? `${decisionData.factors.rainfall_forecast_24h} mm` : '0 mm'}
              </p>
              <p className="text-[10px] text-slate-400 mt-0.5">
                Prob: {decisionData.factors.rainfall_probability_24h != null ? `${decisionData.factors.rainfall_probability_24h}%` : '0%'}
              </p>
            </div>

            <div className="bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 rounded-xl p-3">
              <span className="text-[11px] text-slate-500 dark:text-slate-400 flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-amber-500" /> Daily ET₀
              </span>
              <p className="text-base font-bold text-slate-800 dark:text-slate-100 mt-1">
                {decisionData.factors.et0 != null ? `${decisionData.factors.et0.toFixed(1)} mm` : 'N/A'}
              </p>
              <p className="text-[10px] text-slate-400 mt-0.5">
                Atmospheric demand
              </p>
            </div>

            <div className="bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 rounded-xl p-3">
              <span className="text-[11px] text-slate-500 dark:text-slate-400 flex items-center gap-1">
                <Clock className="w-3 h-3 text-indigo-500" /> Redistribution
              </span>
              <p className="text-base font-bold text-slate-800 dark:text-slate-100 mt-1">
                {decisionData.factors.hours_since_last_irrigation != null 
                  ? `${decisionData.factors.hours_since_last_irrigation.toFixed(1)}h ago` 
                  : 'Ready'}
              </p>
              <p className="text-[10px] text-slate-400 mt-0.5">
                2h Soak Cooldown
              </p>
            </div>
          </div>

          {/* Explainable Reasoning ("Why?") */}
          <div className="bg-blue-50/50 dark:bg-slate-800/40 border border-blue-100 dark:border-slate-700/60 rounded-xl p-4 space-y-2">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                <Info className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" /> Why this recommendation?
              </h4>
              <button
                type="button"
                onClick={() => setShowEvidence(!showEvidence)}
                className="text-[11px] text-brand hover:underline font-semibold flex items-center gap-1"
              >
                <BookOpen className="w-3 h-3" />
                <span>{showEvidence ? 'Hide Citations' : 'View Scientific Evidence'}</span>
                {showEvidence ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              </button>
            </div>

            <ul className="space-y-1.5 pt-1">
              {decisionData.reasons.map((r, i) => (
                <li key={i} className="text-xs text-slate-700 dark:text-slate-300 flex items-start gap-2">
                  <span className="text-brand font-bold shrink-0 mt-0.5">•</span>
                  <span>{r}</span>
                </li>
              ))}
            </ul>

            {/* Expandable Scientific Evidence & Citations */}
            {showEvidence && (
              <div className="mt-3 pt-3 border-t border-blue-100 dark:border-slate-700/60 space-y-3 animate-fadeIn">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                    Scientific Evidence & Rule Provenance
                  </span>
                  <button
                    type="button"
                    onClick={() => setShowKnowledgeModal(true)}
                    className="text-[11px] text-emerald-600 dark:text-emerald-400 hover:underline flex items-center gap-1 font-semibold"
                  >
                    <span>Knowledge Base Explorer</span>
                    <ExternalLink className="w-3 h-3" />
                  </button>
                </div>

                {/* Evidence items */}
                {decisionData.evidence && decisionData.evidence.length > 0 && (
                  <div className="space-y-2">
                    {decisionData.evidence.map((ev, idx) => (
                      <div key={idx} className="p-2.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-[11px] space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="font-mono font-bold text-slate-800 dark:text-slate-200">
                            {ev.rule_id || ev.parameter}
                          </span>
                          <span className={`px-1.5 py-0.2 text-[9px] font-bold rounded ${
                            ev.status === 'EXPERIMENTAL'
                              ? 'bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300'
                              : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300'
                          }`}>
                            {ev.status}
                          </span>
                        </div>
                        {ev.description && (
                          <p className="text-slate-600 dark:text-slate-400">{ev.description}</p>
                        )}
                        {ev.note && (
                          <p className="text-amber-600 dark:text-amber-400 font-medium italic">{ev.note}</p>
                        )}
                        <span className="text-[10px] text-slate-400 block pt-0.5">Source: {ev.source}</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Citations List */}
                {decisionData.citations && decisionData.citations.length > 0 && (
                  <div className="space-y-2 pt-1">
                    <span className="text-[10px] uppercase font-bold text-slate-400 block">Authoritative Citations & Research Provenance</span>
                    {decisionData.citations.map((c, idx) => (
                      <div key={idx} className="text-[10px] text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-800/60 p-2.5 rounded-lg border border-slate-100 dark:border-slate-800 space-y-1">
                        <div className="flex items-center justify-between gap-2">
                          <strong className="text-slate-700 dark:text-slate-200">{c.title}</strong>
                          {c.source_tier != null && (
                            <span className={`shrink-0 px-1.5 py-0.5 text-[9px] font-bold rounded ${
                              c.source_tier === 1 
                                ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300' 
                                : c.source_tier === 2 
                                ? 'bg-purple-100 text-purple-700 dark:bg-purple-950 dark:text-purple-300'
                                : 'bg-slate-100 text-slate-600'
                            }`}>
                              Tier {c.source_tier} {c.source_tier === 1 ? '(Govt/ICAR/FAO)' : c.source_tier === 2 ? '(Scientific Journal)' : ''}
                            </span>
                          )}
                        </div>
                        <div className="text-[10px] text-slate-500">
                          {c.organization} {c.publication_year ? `(${c.publication_year})` : ''}
                        </div>
                        {c.url && (
                          <a
                            href={c.url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-[9px] text-brand hover:underline inline-flex items-center gap-0.5 pt-0.5 font-medium"
                          >
                            <span>Open Provenance Source</span>
                            <ExternalLink className="w-2.5 h-2.5" />
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Recommended Action Callout */}
          <div className="bg-slate-50 dark:bg-slate-800/70 border-l-4 border-brand p-3.5 rounded-r-xl">
            <p className="text-xs font-semibold text-slate-800 dark:text-slate-100">
              Action Required:
            </p>
            <p className="text-xs text-slate-600 dark:text-slate-300 mt-0.5 leading-relaxed">
              {decisionData.recommended_action}
            </p>
          </div>

          {/* Safety & Non-Intervention Disclaimer */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between text-[11px] text-slate-500 dark:text-slate-400 border-t border-slate-100 dark:border-slate-800 pt-3 gap-2">
            <span className="italic">
              * Non-interfering Advisory: The physical relay/pump remains under your device's AUTO/MANUAL control.
            </span>
            <span className="text-[10px] px-2 py-0.5 rounded bg-amber-50 dark:bg-amber-950/50 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
              Preliminary Agronomic Model
            </span>
          </div>
        </div>
      )}

      {/* Full Scientific Knowledge Base Explorer Modal */}
      <KnowledgeExplorerModal
        isOpen={showKnowledgeModal}
        onClose={() => setShowKnowledgeModal(false)}
      />

      {/* Growth Stage Manual Override Modal */}
      {showOverrideModal && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200 dark:border-slate-800 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <h3 className="font-bold text-slate-800 dark:text-slate-100 text-base">
                Adjust Crop Growth Stage
              </h3>
              <button 
                onClick={() => setShowOverrideModal(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-slate-500">
              Actual crop development can vary due to temperature and sowing conditions. Select the current visible growth stage in the field:
            </p>

            <div className="space-y-2 max-h-60 overflow-y-auto">
              {STAGES.map((s) => (
                <label
                  key={s}
                  className={`flex items-center justify-between p-3 rounded-xl border text-xs cursor-pointer transition ${
                    selectedOverrideStage === s
                      ? 'border-brand bg-brand/5 font-semibold text-brand'
                      : 'border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300'
                  }`}
                >
                  <span>{s}</span>
                  <input
                    type="radio"
                    name="growth_stage"
                    checked={selectedOverrideStage === s}
                    onChange={() => setSelectedOverrideStage(s)}
                    className="accent-brand"
                  />
                </label>
              ))}
            </div>

            <div className="flex items-center justify-between pt-3 border-t border-slate-100 dark:border-slate-800">
              <button
                type="button"
                onClick={() => handleStageOverride(null)}
                disabled={savingStage}
                className="text-xs text-slate-500 hover:text-slate-700 underline"
              >
                Reset to Auto Calendar
              </button>

              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setShowOverrideModal(false)}
                  className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => handleStageOverride(selectedOverrideStage)}
                  disabled={savingStage}
                  className="px-4 py-1.5 text-xs bg-brand text-white font-semibold rounded-lg hover:bg-brand/90 transition flex items-center gap-1.5"
                >
                  {savingStage ? 'Saving...' : <><Check className="w-3.5 h-3.5" /> Save Stage</>}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TerravynDecisionCard;
