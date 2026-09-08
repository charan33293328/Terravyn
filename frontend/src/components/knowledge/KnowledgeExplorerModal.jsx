import React, { useState, useEffect } from 'react';
import apiClient from '../../api/client';
import { 
  BookOpen, Sprout, Droplets, Thermometer, ShieldAlert, 
  Bug, FlaskConical, ExternalLink, X, CheckCircle2, AlertTriangle, 
  Layers, Info, Award
} from 'lucide-react';

const KnowledgeExplorerModal = ({ isOpen, onClose, initialTab = 'overview' }) => {
  const [activeTab, setActiveTab] = useState(initialTab);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [profile, setProfile] = useState(null);
  const [varieties, setVarieties] = useState([]);
  const [stages, setStages] = useState([]);
  const [rules, setRules] = useState([]);
  const [nutrients, setNutrients] = useState(null);
  const [diseases, setDiseases] = useState({});
  const [pests, setPests] = useState({});
  const [sources, setSources] = useState({});

  useEffect(() => {
    if (isOpen) {
      fetchKnowledgeData();
    }
  }, [isOpen]);

  const fetchKnowledgeData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [
        profileRes,
        varietiesRes,
        stagesRes,
        rulesRes,
        nutrientsRes,
        diseasesRes,
        pestsRes,
        sourcesRes
      ] = await Promise.all([
        apiClient.get('/farmer/knowledge/green-gram/profile'),
        apiClient.get('/farmer/knowledge/green-gram/varieties'),
        apiClient.get('/farmer/knowledge/green-gram/stages'),
        apiClient.get('/farmer/knowledge/green-gram/irrigation-rules'),
        apiClient.get('/farmer/knowledge/green-gram/nutrients'),
        apiClient.get('/farmer/knowledge/green-gram/diseases'),
        apiClient.get('/farmer/knowledge/green-gram/pests'),
        apiClient.get('/farmer/knowledge/green-gram/sources')
      ]);

      setProfile(profileRes.data);
      setVarieties(varietiesRes.data);
      setStages(stagesRes.data);
      setRules(rulesRes.data);
      setNutrients(nutrientsRes.data);
      setDiseases(diseasesRes.data);
      setPests(pestsRes.data);
      setSources(sourcesRes.data);
    } catch (err) {
      console.error("Failed to load knowledge base:", err);
      setError("Failed to load agricultural knowledge base records.");
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-3 sm:p-6 animate-fadeIn">
      <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-5xl w-full max-h-[92vh] flex flex-col shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-emerald-500/10 text-emerald-600 rounded-xl border border-emerald-500/20">
              <BookOpen className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100">
                  Terravyn Green Gram Knowledge Base
                </h2>
                <span className="px-2 py-0.5 text-[10px] font-bold bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 rounded-full uppercase tracking-wider">
                  V1.0 ICAR / SAU Grounded
                </span>
              </div>
              <p className="text-xs text-slate-500">
                Scientifically traceable pulse agronomy for <span className="italic font-medium">Vigna radiata</span>
              </p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center gap-1 px-6 border-b border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/20 overflow-x-auto scrollbar-none">
          {[
            { id: 'overview', label: 'Overview', icon: <Sprout className="w-4 h-4" /> },
            { id: 'varieties', label: 'Varieties', icon: <Award className="w-4 h-4" /> },
            { id: 'stages', label: 'Growth Stages', icon: <Layers className="w-4 h-4" /> },
            { id: 'irrigation', label: 'Water & Irrigation', icon: <Droplets className="w-4 h-4" /> },
            { id: 'nutrients', label: 'Nutrients & Chlorosis', icon: <FlaskConical className="w-4 h-4" /> },
            { id: 'protection', label: 'Diseases & Pests', icon: <ShieldAlert className="w-4 h-4" /> },
            { id: 'sources', label: 'Citations & Sources', icon: <BookOpen className="w-4 h-4" /> }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 text-xs font-semibold whitespace-nowrap border-b-2 transition ${
                activeTab === tab.id
                  ? 'border-emerald-500 text-emerald-600 dark:text-emerald-400 bg-white dark:bg-slate-900 rounded-t-lg'
                  : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-300'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {loading && (
            <div className="flex items-center justify-center py-20 text-slate-400 gap-3">
              <div className="w-5 h-5 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
              <span className="text-sm">Retrieving agricultural research records...</span>
            </div>
          )}

          {error && (
            <div className="p-4 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 rounded-xl text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              {error}
            </div>
          )}

          {!loading && !error && (
            <>
              {/* TAB 1: OVERVIEW */}
              {activeTab === 'overview' && profile && (
                <div className="space-y-6 animate-fadeIn">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 space-y-1.5">
                      <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">Botanical Name</span>
                      <p className="text-base font-bold text-slate-800 dark:text-slate-100 italic">{profile.crop}</p>
                      <p className="text-xs text-slate-500 font-medium">Family: {profile.family}</p>
                    </div>

                    <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 space-y-1.5">
                      <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">Crop Classification</span>
                      <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">{profile.classification}</p>
                      <p className="text-xs text-slate-500">Duration: {profile.duration_range_days[0]}–{profile.duration_range_days[1]} Days</p>
                    </div>

                    <div className="p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900/50 space-y-1.5">
                      <span className="text-[11px] uppercase tracking-wider text-emerald-600 font-semibold">Biological N-Fixation</span>
                      <p className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
                        {profile.symbiotic_fixation.approx_n_fixed_kg_ha[0]}–{profile.symbiotic_fixation.approx_n_fixed_kg_ha[1]} kg N/ha
                      </p>
                      <p className="text-xs text-slate-500">
                        Enriches soil by +{profile.symbiotic_fixation.residual_soil_n_benefit_kg_ha[0]}–{profile.symbiotic_fixation.residual_soil_n_benefit_kg_ha[1]} kg residual N/ha
                      </p>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200">Cultivation Windows Across India</h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                      {profile.seasons.map((s, idx) => (
                        <div key={idx} className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-1">
                          <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400">{s.season}</span>
                          <p className="text-xs text-slate-600 dark:text-slate-400">{s.sowing_window}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="p-4 rounded-xl bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-900 text-xs text-slate-600 dark:text-slate-300 space-y-2">
                    <div className="flex items-center gap-2 font-bold text-blue-800 dark:text-blue-300">
                      <Info className="w-4 h-4" />
                      Scientific Grounding & Policy
                    </div>
                    <p>
                      This knowledge base enforces evidence-based agronomy sourced directly from <strong>ICAR-IIPR (Indian Institute of Pulses Research)</strong>, 
                      <strong>State Agricultural Universities (TNAU, ANGRAU, CCS HAU, PAU)</strong>, and <strong>FAO-56</strong>. 
                      In-situ capacitance sensor thresholds are explicitly labeled <em>EXPERIMENTAL</em> until calibrated with local soil samples.
                    </p>
                  </div>
                </div>
              )}

              {/* TAB 2: VARIETIES */}
              {activeTab === 'varieties' && (
                <div className="space-y-4 animate-fadeIn">
                  <div className="flex items-center justify-between text-xs text-slate-500">
                    <span>{varieties.length} Certified Indian Green Gram Varieties Cataloged</span>
                    <span>Source: ICAR-IIPR Varietal Directory</span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {varieties.map(v => (
                      <div key={v.name} className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30 space-y-3">
                        <div className="flex items-start justify-between">
                          <div>
                            <h4 className="text-base font-bold text-slate-900 dark:text-slate-100">{v.name}</h4>
                            <p className="text-xs text-slate-500">{v.developer_institution}</p>
                          </div>
                          <span className="px-2 py-1 text-[11px] font-bold bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 rounded-lg">
                            {v.duration_days} Days
                          </span>
                        </div>

                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div className="p-2 bg-white dark:bg-slate-900 rounded-lg border border-slate-100 dark:border-slate-800">
                            <span className="text-[10px] text-slate-400 block font-semibold">Yield Potential</span>
                            <span className="font-bold text-slate-700 dark:text-slate-300">{v.yield_potential_q_ha} q/ha</span>
                          </div>
                          <div className="p-2 bg-white dark:bg-slate-900 rounded-lg border border-slate-100 dark:border-slate-800">
                            <span className="text-[10px] text-slate-400 block font-semibold">Seasons</span>
                            <span className="font-bold text-slate-700 dark:text-slate-300">{v.suitable_seasons.join(', ')}</span>
                          </div>
                        </div>

                        <div className="space-y-1">
                          <span className="text-[10px] uppercase font-bold text-slate-400">Disease Reactions</span>
                          <div className="flex flex-wrap gap-1.5">
                            {Object.entries(v.disease_resistance).map(([dis, reaction]) => (
                              <span key={dis} className="px-2 py-0.5 text-[10px] rounded bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-medium">
                                {dis}: <strong className="text-emerald-600 dark:text-emerald-400">{reaction}</strong>
                              </span>
                            ))}
                          </div>
                        </div>

                        <div className="text-[11px] text-slate-500 border-t border-slate-200 dark:border-slate-800 pt-2 flex items-center justify-between">
                          <span>Status: <strong>{v.status}</strong></span>
                          <span className="text-slate-400 truncate max-w-[200px]">{v.source.title}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* TAB 3: GROWTH STAGES */}
              {activeTab === 'stages' && (
                <div className="space-y-4 animate-fadeIn">
                  <p className="text-xs text-slate-500">
                    10 distinct physiological stages aligned with FAO-56 crop coefficient ($K_c$) and ICAR-IIPR moisture sensitivity.
                  </p>

                  <div className="space-y-3">
                    {stages.map((stg, idx) => (
                      <div key={stg.stage_id} className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-emerald-300 transition space-y-2">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <span className="w-6 h-6 rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-600 text-xs font-bold flex items-center justify-center">
                              {idx + 1}
                            </span>
                            <div>
                              <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100">{stg.stage_name}</h4>
                              <span className="text-[11px] text-slate-400">DAS: {stg.standard_das_range[0]}–{stg.standard_das_range[1]}</span>
                            </div>
                          </div>

                          <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 text-[10px] font-bold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded">
                              FAO Kc: {stg.crop_coefficient_kc.toFixed(2)}
                            </span>
                            <span className={`px-2 py-0.5 text-[10px] font-bold rounded ${
                              stg.water_sensitivity === 'CRITICAL' ? 'bg-rose-100 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300' :
                              stg.water_sensitivity === 'DETRIMENTAL' ? 'bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300' :
                              'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300'
                            }`}>
                              Water: {stg.water_sensitivity}
                            </span>
                          </div>
                        </div>

                        <p className="text-xs text-slate-600 dark:text-slate-400">
                          {stg.physiological_description}
                        </p>

                        <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800 text-[11px] space-y-1">
                          <div><strong className="text-slate-700 dark:text-slate-300">Management:</strong> {stg.management_advisory}</div>
                          <div><strong className="text-slate-700 dark:text-slate-300">Nutrients:</strong> {stg.nutrient_priority}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* TAB 4: WATER & IRRIGATION */}
              {activeTab === 'irrigation' && (
                <div className="space-y-6 animate-fadeIn">
                  <div className="p-4 rounded-xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900 text-xs text-amber-800 dark:text-amber-300 space-y-1">
                    <div className="flex items-center gap-2 font-bold">
                      <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                      Waterlogging Hypoxia Warning (ICAR-CRIDA / IIPR)
                    </div>
                    <p>
                      Green Gram roots and Rhizobial nodules are <strong>extremely vulnerable to standing water</strong>. 
                      Submergence for more than 24 hours causes irreversible tap root rot and 25–40% yield collapse. Continuous drainage channels are mandatory.
                    </p>
                  </div>

                  <div className="space-y-3">
                    <div className="flex items-center justify-between text-xs text-slate-500 font-semibold">
                      <span>Scientific Irrigation Rules Repository</span>
                      <span>Validated Agronomy vs Experimental Telemetry</span>
                    </div>

                    <div className="space-y-2.5">
                      {rules.map(r => (
                        <div key={r.rule_id} className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="font-mono text-xs font-bold text-slate-700 dark:text-slate-300">{r.rule_id}</span>
                            <span className={`px-2 py-0.5 text-[10px] font-bold rounded ${
                              r.is_experimental 
                                ? 'bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300'
                                : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300'
                            }`}>
                              {r.status} {r.is_experimental ? '(CALIBRATION REQ.)' : ''}
                            </span>
                          </div>

                          <div className="text-xs">
                            <strong className="text-slate-800 dark:text-slate-200">Condition:</strong> {r.condition}
                          </div>
                          <div className="text-xs text-slate-600 dark:text-slate-400">
                            <strong>Rationale:</strong> {r.scientific_rationale}
                          </div>

                          <div className="pt-2 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[11px] text-slate-400">
                            <span>Stage: {r.growth_stage}</span>
                            <span>Source: {r.source?.title || 'Terravyn Agro'}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 5: NUTRIENTS & CHLOROSIS */}
              {activeTab === 'nutrients' && nutrients && (
                <div className="space-y-6 animate-fadeIn">
                  <div className="p-4 rounded-xl bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-900 text-xs text-blue-900 dark:text-blue-300 space-y-1">
                    <div className="flex items-center gap-2 font-bold">
                      <FlaskConical className="w-4 h-4" />
                      Anti-Simplistic Diagnostic Advisory
                    </div>
                    <p>
                      Terravyn does not automatically diagnose yellow leaves as Nitrogen deficiency. Yellowing can stem from 
                      waterlogging hypoxia, lime-induced iron chlorosis (pH &gt; 7.8), sulfur deficiency, or MYMV virus. Lab soil testing is required before corrective fertilizer application.
                    </p>
                  </div>

                  <div className="space-y-3">
                    <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200">Nutrient Requirements & Management</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {Object.entries(nutrients.nutrients || {}).map(([sym, n]) => (
                        <div key={sym} className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-1.5">
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-bold text-slate-800 dark:text-slate-100">{n.nutrient_name} ({sym})</span>
                            <span className="text-xs font-semibold text-emerald-600">{n.recommended_dose_kg_ha}</span>
                          </div>
                          <p className="text-xs text-slate-600 dark:text-slate-400">{n.physiological_role}</p>
                          <div className="p-2 rounded bg-slate-50 dark:bg-slate-800 text-[11px] space-y-0.5">
                            <div><strong className="text-slate-700 dark:text-slate-300">Timing:</strong> {n.application_timing}</div>
                            <div><strong className="text-slate-700 dark:text-slate-300">Symptoms:</strong> {n.deficiency_symptoms}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30 space-y-2">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-300">Validated Foliar Technologies to Arrest Flower Drop</h4>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                      <div className="p-3 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 space-y-1">
                        <strong className="text-slate-800 dark:text-slate-200">2% DAP Spray (ICAR-IIPR)</strong>
                        <p className="text-slate-500">First spray at early flowering (30 DAS) and second at early podding (45 DAS) provides targeted N & P directly to floral sinks.</p>
                      </div>
                      <div className="p-3 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 space-y-1">
                        <strong className="text-slate-800 dark:text-slate-200">TNAU Pulse Wonder (1% Spray)</strong>
                        <p className="text-slate-500">Reduces flower drop by 20–25% and improves pod setting percentage (TNAU Agritech standard).</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 6: DISEASES & PESTS */}
              {activeTab === 'protection' && (
                <div className="space-y-6 animate-fadeIn">
                  <div className="space-y-3">
                    <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200">Major Green Gram Diseases (India)</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {Object.entries(diseases).map(([key, d]) => (
                        <div key={d.disease_id} className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-bold text-slate-800 dark:text-slate-100">{d.common_name}</span>
                            <span className="px-1.5 py-0.5 text-[10px] bg-slate-100 dark:bg-slate-800 text-slate-600 rounded font-medium">{d.pathogen_type}</span>
                          </div>
                          <p className="text-[11px] text-slate-500 italic">{d.causal_organism}</p>
                          <p className="text-xs text-slate-600 dark:text-slate-400"><strong>Symptoms:</strong> {d.early_symptoms}</p>
                          <div className="p-2 rounded bg-slate-50 dark:bg-slate-800 text-[11px] space-y-0.5">
                            <div><strong>Weather Triggers:</strong> {d.favorable_weather?.conditions || 'Warm humid conditions'}</div>
                            <div><strong>IPM Action:</strong> {d.ipm_management?.[0] || 'Scout and rogue out early.'}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-3">
                    <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200">Major Insect Pests & Economic Threshold Levels (ETL)</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {Object.entries(pests).map(([key, p]) => (
                        <div key={p.pest_id} className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-bold text-slate-800 dark:text-slate-100">{p.common_name}</span>
                            <span className="text-[10px] text-slate-400 italic">{p.scientific_name}</span>
                          </div>
                          <div className="p-2 rounded bg-rose-50 dark:bg-rose-950/30 text-rose-800 dark:text-rose-300 text-[11px]">
                            <strong>ETL:</strong> {p.economic_threshold_level_etl}
                          </div>
                          <p className="text-xs text-slate-600 dark:text-slate-400"><strong>Damage:</strong> {p.symptoms_of_damage}</p>
                          <p className="text-[11px] text-slate-500"><strong>Monitoring:</strong> {p.monitoring_method}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 7: CITATIONS & SOURCES */}
              {activeTab === 'sources' && (
                <div className="space-y-4 animate-fadeIn">
                  <div className="text-xs text-slate-500">
                    Master catalog of authoritative Indian agricultural institutions and research publications grounding Terravyn.
                  </div>

                  <div className="space-y-3">
                    {Object.entries(sources).map(([srcId, s]) => (
                      <div key={srcId} className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-1.5">
                        <div className="flex items-start justify-between">
                          <div>
                            <span className="font-mono text-xs font-bold text-emerald-600 dark:text-emerald-400 block">{s.source_id}</span>
                            <h4 className="text-sm font-bold text-slate-800 dark:text-slate-100">{s.title}</h4>
                          </div>
                          {s.publication_year && (
                            <span className="px-2 py-0.5 text-xs bg-slate-100 dark:bg-slate-800 rounded font-semibold text-slate-600">
                              {s.publication_year}
                            </span>
                          )}
                        </div>

                        <p className="text-xs text-slate-600 dark:text-slate-400">
                          <strong>Organization:</strong> {s.organization}
                        </p>
                        {s.notes && (
                          <p className="text-[11px] text-slate-500">{s.notes}</p>
                        )}
                        {s.url && (
                          <a 
                            href={s.url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-[11px] text-brand hover:underline pt-1"
                          >
                            <span>Access Reference</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-3 border-t border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30 text-xs text-slate-400">
          <span>Terravyn Agronomic Engine V1 • Strictly Advisory Mode</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-slate-800 dark:bg-slate-700 text-white rounded-lg text-xs font-medium hover:bg-slate-700"
          >
            Close Explorer
          </button>
        </div>

      </div>
    </div>
  );
};

export default KnowledgeExplorerModal;
