import React, { useState, useEffect } from 'react';
import apiClient from '../../api/client';
import {
  FlaskConical,
  Sprout,
  Droplets,
  Calendar,
  Layers,
  PlusCircle,
  FileDown,
  Info,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  ChevronRight,
  TrendingDown,
  Activity
} from 'lucide-react';

const GreenGramExperimentCard = ({ farmId, farmName }) => {
  const [experiments, setExperiments] = useState([]);
  const [activeExp, setActiveExp] = useState(null);
  const [hierarchy, setHierarchy] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Observation modal state
  const [showObsModal, setShowObsModal] = useState(false);
  const [obsSubmitting, setObsSubmitting] = useState(false);
  const [obsSuccess, setObsSuccess] = useState(null);
  const [selectedPlotId, setSelectedPlotId] = useState('');
  const [selectedPlantId, setSelectedPlantId] = useState('');
  const [obsParam, setObsParam] = useState('plant_height');
  const [obsVal, setObsVal] = useState('');
  const [obsUnit, setObsUnit] = useState('cm');
  const [obsNotes, setObsNotes] = useState('');

  useEffect(() => {
    fetchExperiments();
  }, []);

  const fetchExperiments = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await apiClient.get('/api/experiments');
      const exps = res.data || [];
      setExperiments(exps);

      if (exps.length > 0) {
        const firstExp = exps[0];
        setActiveExp(firstExp);
        await loadExperimentDetails(firstExp.id);
      }
    } catch (err) {
      console.error('Failed to load experiments:', err);
      setError('Unable to load experimental trials.');
    } finally {
      setLoading(false);
    }
  };

  const loadExperimentDetails = async (expId) => {
    try {
      const [hRes, cRes] = await Promise.all([
        apiClient.get(`/api/experiments/${expId}`),
        apiClient.get(`/api/experiments/${expId}/comparison`).catch(() => ({ data: null })),
      ]);
      setHierarchy(hRes.data);
      if (cRes && cRes.data && !cRes.data.error) {
        setComparison(cRes.data);
      } else {
        setComparison(null);
      }
    } catch (err) {
      console.error('Failed to load experiment details:', err);
    }
  };

  const handleSelectExperiment = async (exp) => {
    setActiveExp(exp);
    await loadExperimentDetails(exp.id);
  };

  const handleCreateDefaultTrial = async () => {
    try {
      setLoading(true);
      const payload = {
        name: `Green Gram Trial ${new Date().toLocaleDateString('en-GB')}`,
        crop: "Green Gram (Moong)",
        variety: "Pusa Vishal",
        pots_per_group: 3,
        plants_per_pot: 5,
        location: farmName || "Controlled Pot Trial"
      };
      await apiClient.post('/api/experiments', payload);
      await fetchExperiments();
    } catch (err) {
      alert('Failed to initialize trial: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleRecordObservation = async (e) => {
    e.preventDefault();
    if (!activeExp || !selectedPlotId || !obsVal) {
      alert('Please fill in required fields.');
      return;
    }
    try {
      setObsSubmitting(true);
      const payload = {
        plot_id: parseInt(selectedPlotId),
        plant_id: selectedPlantId ? parseInt(selectedPlantId) : null,
        parameter: obsParam,
        value_numeric: parseFloat(obsVal),
        unit: obsUnit,
        notes: obsNotes,
      };
      await apiClient.post(`/api/experiments/${activeExp.id}/observations`, payload);
      setObsSuccess('Measurement successfully logged!');
      setObsVal('');
      setObsNotes('');
      setTimeout(() => {
        setObsSuccess(null);
        setShowObsModal(false);
        loadExperimentDetails(activeExp.id);
      }, 1200);
    } catch (err) {
      alert('Failed to record observation: ' + (err.response?.data?.detail || err.message));
    } finally {
      setObsSubmitting(false);
    }
  };

  const handleExportCSV = (type) => {
    if (!activeExp) return;
    const url = `/api/experiments/${activeExp.id}/export/${type}`;
    window.open(url, '_blank');
  };

  if (loading && !activeExp) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm flex items-center justify-center h-48">
        <RefreshCw className="w-6 h-6 animate-spin text-emerald-600" />
        <span className="ml-2 text-slate-600 font-medium">Loading experiment records...</span>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 border-b border-slate-100 pb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center font-bold">
            <FlaskConical className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-bold text-slate-800">
                Green Gram Controlled Experiment Engine V1
              </h3>
              <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-emerald-100 text-emerald-800">
                Prompt 6
              </span>
            </div>
            <p className="text-xs text-slate-500">
              Multi-replicate scientific trial • Terravyn Guided vs Conventional Control
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {experiments.length === 0 ? (
            <button
              onClick={handleCreateDefaultTrial}
              className="px-3 py-1.5 bg-emerald-700 hover:bg-emerald-800 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition"
            >
              <PlusCircle className="w-4 h-4" /> Initialize New Trial
            </button>
          ) : (
            <>
              <button
                onClick={() => setShowObsModal(true)}
                className="px-3 py-1.5 bg-emerald-700 hover:bg-emerald-800 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition"
              >
                <PlusCircle className="w-4 h-4" /> Log Observation
              </button>
              <button
                onClick={() => handleExportCSV('observations')}
                title="Download full observation dataset in CSV format"
                className="px-3 py-1.5 border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-medium flex items-center gap-1.5 transition"
              >
                <FileDown className="w-4 h-4 text-slate-500" /> Export CSV
              </button>
            </>
          )}
        </div>
      </div>

      {/* Safety Notice & Calibration Convention */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-xs text-amber-900 flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
          <div>
            <strong>Strict Observation Mode:</strong> Autonomous irrigation pump actuation based on experimental results is strictly prohibited. Operating in recommendation and manual confirmation mode.
          </div>
        </div>
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-xs text-blue-900 flex items-start gap-2">
          <Info className="w-4 h-4 text-blue-700 shrink-0 mt-0.5" />
          <div>
            <strong>Capacitive Hardware Standard:</strong> ADC 4095 represents Air / Dry (0% moisture). Submerged saturation is ~1400 ADC. Direction: <code className="bg-blue-100 px-1 py-0.5 rounded">4095_DRY_0_WET</code>.
          </div>
        </div>
      </div>

      {/* Active Trial Selector & Summary */}
      {experiments.length > 0 && activeExp && (
        <div className="space-y-4">
          <div className="bg-slate-50 p-3 rounded-lg border border-slate-200 flex flex-wrap items-center justify-between gap-3 text-xs">
            <div className="flex items-center gap-3">
              <span className="font-semibold text-slate-700">Trial:</span>
              <span className="font-bold text-slate-900">{activeExp.name}</span>
              <span className="text-slate-400">|</span>
              <span className="text-slate-600">Variety: <strong>{activeExp.variety || 'Pusa Vishal'}</strong></span>
              <span className="text-slate-400">|</span>
              <span className="text-slate-600">Status: <strong className="text-emerald-700">{activeExp.status}</strong></span>
            </div>
            {hierarchy && hierarchy.baseline && (
              <div className="text-slate-500">
                Soil: <strong className="text-slate-700">{hierarchy.baseline.soil_type || 'Sandy Loam'}</strong> (pH {hierarchy.baseline.soil_ph || 7.2}) • Spacing: {hierarchy.baseline.spacing_cm || '30x10 cm'}
              </div>
            )}
          </div>

          {/* Comparative Analytics Card */}
          {comparison && comparison.observed_differences && (
            <div className="border border-emerald-200 bg-emerald-50/40 rounded-xl p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Activity className="w-4 h-4 text-emerald-700" />
                  <h4 className="font-bold text-sm text-slate-800">
                    Comparative Cohort Performance
                  </h4>
                </div>
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800">
                  Observed Differences
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-sm">
                  <span className="text-[11px] text-slate-500 uppercase tracking-wider block mb-1">Water Used (Terravyn)</span>
                  <span className="text-base font-bold text-emerald-800">
                    {comparison.terravyn_cohort?.total_water_liters ?? 0} L
                  </span>
                  <span className="text-[11px] text-slate-400 block mt-0.5">
                    {comparison.terravyn_cohort?.irrigation_event_count ?? 0} irrigations
                  </span>
                </div>

                <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-sm">
                  <span className="text-[11px] text-slate-500 uppercase tracking-wider block mb-1">Water Used (Control)</span>
                  <span className="text-base font-bold text-slate-800">
                    {comparison.control_cohort?.total_water_liters ?? 0} L
                  </span>
                  <span className="text-[11px] text-slate-400 block mt-0.5">
                    {comparison.control_cohort?.irrigation_event_count ?? 0} irrigations
                  </span>
                </div>

                <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-sm">
                  <span className="text-[11px] text-slate-500 uppercase tracking-wider block mb-1">Water Saved</span>
                  <span className="text-base font-bold text-teal-700 flex items-center justify-center gap-0.5">
                    {comparison.observed_differences.water_saved_percentage !== null
                      ? `${comparison.observed_differences.water_saved_percentage}%`
                      : '—'}
                  </span>
                  <span className="text-[11px] text-slate-400 block mt-0.5">
                    {comparison.observed_differences.water_saved_liters !== null
                      ? `${comparison.observed_differences.water_saved_liters} L net`
                      : 'Equiv.'}
                  </span>
                </div>

                <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-sm">
                  <span className="text-[11px] text-slate-500 uppercase tracking-wider block mb-1">Mean Plant Height</span>
                  <span className="text-base font-bold text-slate-800">
                    {comparison.terravyn_cohort?.avg_height_cm ?? '—'} cm
                  </span>
                  <span className="text-[11px] text-emerald-600 block mt-0.5">
                    vs {comparison.control_cohort?.avg_height_cm ?? '—'} cm Control
                  </span>
                </div>
              </div>

              <div className="text-[11px] text-slate-500 italic bg-white/70 p-2 rounded border border-slate-200/60">
                ⚠️ <strong>Scientific Disclaimer:</strong> {comparison.scientific_disclaimer}
              </div>
            </div>
          )}

          {/* Replicate Hierarchy: Terravyn vs Control Pots */}
          {hierarchy && hierarchy.groups && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {hierarchy.groups.map((group) => (
                <div
                  key={group.id}
                  className={`border rounded-xl p-4 space-y-3 ${
                    group.type === 'TERRAVYN'
                      ? 'border-emerald-200 bg-emerald-50/20'
                      : 'border-slate-200 bg-slate-50/40'
                  }`}
                >
                  <div className="flex justify-between items-center">
                    <div>
                      <h4 className="font-bold text-slate-800 text-sm flex items-center gap-1.5">
                        <Sprout className={`w-4 h-4 ${group.type === 'TERRAVYN' ? 'text-emerald-700' : 'text-slate-500'}`} />
                        {group.name}
                      </h4>
                      <p className="text-xs text-slate-500">{group.description}</p>
                    </div>
                    <span
                      className={`text-xs px-2 py-0.5 rounded font-semibold ${
                        group.type === 'TERRAVYN'
                          ? 'bg-emerald-100 text-emerald-800'
                          : 'bg-slate-200 text-slate-700'
                      }`}
                    >
                      {group.type}
                    </span>
                  </div>

                  <div className="space-y-2">
                    {group.plots.map((plot) => (
                      <div
                        key={plot.id}
                        className="bg-white p-3 rounded-lg border border-slate-200 shadow-xs flex justify-between items-center text-xs"
                      >
                        <div>
                          <span className="font-semibold text-slate-800">{plot.name}</span>
                          <span className="text-slate-400 mx-1.5">•</span>
                          <span className="text-slate-500">{plot.plants.length} plant units</span>
                        </div>
                        <div className="flex gap-1 flex-wrap max-w-[200px] justify-end">
                          {plot.plants.map((plant) => (
                            <span
                              key={plant.id}
                              title={`Plant ${plant.plant_tag} (${plant.status})`}
                              className="px-1.5 py-0.5 rounded text-[10px] bg-slate-100 text-slate-600 font-mono"
                            >
                              {plant.plant_tag.split('-').slice(1).join('-')}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Observation Modal */}
      {showObsModal && hierarchy && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-xl shadow-xl border border-slate-200 max-w-md w-full p-6 space-y-4">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h4 className="font-bold text-slate-800 text-base">Record Phenotypic Measurement</h4>
              <button
                onClick={() => setShowObsModal(false)}
                className="text-slate-400 hover:text-slate-600 font-bold"
              >
                ✕
              </button>
            </div>

            {obsSuccess && (
              <div className="p-3 bg-green-50 text-green-800 rounded-lg text-xs flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-green-600 shrink-0" />
                {obsSuccess}
              </div>
            )}

            <form onSubmit={handleRecordObservation} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-600 font-medium mb-1">Target Pot / Plot *</label>
                <select
                  value={selectedPlotId}
                  onChange={(e) => {
                    setSelectedPlotId(e.target.value);
                    setSelectedPlantId('');
                  }}
                  required
                  className="w-full border border-slate-300 rounded-lg p-2 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                >
                  <option value="">-- Select Pot/Plot --</option>
                  {hierarchy.groups?.flatMap((g) =>
                    g.plots.map((p) => (
                      <option key={p.id} value={p.id}>
                        {g.name} — {p.name}
                      </option>
                    ))
                  )}
                </select>
              </div>

              <div>
                <label className="block text-slate-600 font-medium mb-1">Plant Tag (Optional for individual plant)</label>
                <select
                  value={selectedPlantId}
                  onChange={(e) => setSelectedPlantId(e.target.value)}
                  className="w-full border border-slate-300 rounded-lg p-2 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                >
                  <option value="">-- Whole Pot / Plot Aggregation --</option>
                  {hierarchy.groups
                    ?.flatMap((g) => g.plots)
                    .find((p) => p.id === parseInt(selectedPlotId))
                    ?.plants.map((pl) => (
                      <option key={pl.id} value={pl.id}>
                        {pl.plant_tag} ({pl.status})
                      </option>
                    ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-600 font-medium mb-1">Parameter *</label>
                  <select
                    value={obsParam}
                    onChange={(e) => {
                      setObsParam(e.target.value);
                      if (e.target.value === 'plant_height') setObsUnit('cm');
                      else if (e.target.value.includes('count')) setObsUnit('count');
                      else if (e.target.value === 'wilting_index') setObsUnit('score 0-3');
                    }}
                    className="w-full border border-slate-300 rounded-lg p-2 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                  >
                    <option value="plant_height">Plant Height</option>
                    <option value="leaf_count">Leaf Count</option>
                    <option value="flower_count">Flower Count</option>
                    <option value="pod_count">Pod Count</option>
                    <option value="wilting_index">Wilting Index (0-3)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-600 font-medium mb-1">Measured Value *</label>
                  <div className="flex gap-1">
                    <input
                      type="number"
                      step="0.1"
                      required
                      placeholder="e.g. 24.5"
                      value={obsVal}
                      onChange={(e) => setObsVal(e.target.value)}
                      className="w-full border border-slate-300 rounded-lg p-2 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                    />
                    <span className="p-2 bg-slate-100 border border-slate-300 rounded-lg text-slate-600 font-mono text-[11px]">
                      {obsUnit}
                    </span>
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-slate-600 font-medium mb-1">Agronomic Notes</label>
                <textarea
                  rows="2"
                  placeholder="e.g. Normal green foliage, no pest damage"
                  value={obsNotes}
                  onChange={(e) => setObsNotes(e.target.value)}
                  className="w-full border border-slate-300 rounded-lg p-2 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowObsModal(false)}
                  className="px-3 py-1.5 border border-slate-200 text-slate-600 rounded-lg hover:bg-slate-50 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={obsSubmitting}
                  className="px-4 py-1.5 bg-emerald-700 hover:bg-emerald-800 text-white font-semibold rounded-lg transition disabled:opacity-50"
                >
                  {obsSubmitting ? 'Saving...' : 'Save Observation'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default GreenGramExperimentCard;
