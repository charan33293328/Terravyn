import React, { useState, useEffect } from 'react';
import apiClient from '../../api/client';
import { 
  Sprout, Droplets, Thermometer, FlaskConical, ShieldAlert, 
  Bug, BookOpen, ExternalLink, ChevronRight, AlertTriangle, 
  CheckCircle2, RefreshCw, Calendar, Sparkles
} from 'lucide-react';
import KnowledgeExplorerModal from './KnowledgeExplorerModal';

const GreenGramKnowledgeCard = ({ farmId = null, farmName = "" }) => {
  const [statusData, setStatusData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [modalInitialTab, setModalInitialTab] = useState('overview');

  useEffect(() => {
    if (farmId) {
      fetchFarmCropStatus(farmId);
    }
  }, [farmId]);

  const fetchFarmCropStatus = async (id) => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.get(`/farmer/farms/${id}/crop-status`);
      setStatusData(res.data);
    } catch (err) {
      console.error("Failed to load crop status:", err);
      setError("Crop profile status currently unavailable.");
    } finally {
      setLoading(false);
    }
  };

  const openExplorer = (tab = 'overview') => {
    setModalInitialTab(tab);
    setShowModal(true);
  };

  if (!farmId) {
    return null;
  }

  return (
    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between bg-slate-50/50 dark:bg-slate-800/30">
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-emerald-500/10 text-emerald-600 rounded-lg border border-emerald-500/20">
            <Sprout className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-bold text-slate-800 dark:text-slate-100 text-sm flex items-center gap-2">
              Green Gram Crop Profile & Status
              <span className="px-1.5 py-0.5 text-[10px] font-bold bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 rounded">
                ICAR-IIPR
              </span>
            </h3>
            <p className="text-[11px] text-slate-400">
              Field agronomic monitoring grounded in authoritative Indian pulse research
            </p>
          </div>
        </div>

        <button
          onClick={() => fetchFarmCropStatus(farmId)}
          disabled={loading}
          className="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition"
          title="Refresh Crop Status"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Body */}
      <div className="p-5 space-y-4">
        {loading && !statusData && (
          <div className="flex items-center justify-center py-8 text-xs text-slate-400 gap-2">
            <div className="w-4 h-4 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
            <span>Evaluating agronomic crop profile...</span>
          </div>
        )}

        {error && (
          <div className="p-3 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900 text-amber-700 dark:text-amber-300 rounded-xl text-xs flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {statusData && (
          <>
            {/* Top Stats Bar */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
              <div className="p-3 bg-slate-50 dark:bg-slate-800/40 rounded-xl border border-slate-100 dark:border-slate-800">
                <span className="text-[10px] uppercase font-bold text-slate-400 block">Variety</span>
                <span className="font-bold text-xs text-slate-800 dark:text-slate-100 truncate block">
                  {statusData.variety || 'Standard Profile'}
                </span>
                <button 
                  onClick={() => openExplorer('varieties')}
                  className="text-[10px] text-brand hover:underline mt-0.5 inline-block font-medium"
                >
                  View traits
                </button>
              </div>

              <div className="p-3 bg-slate-50 dark:bg-slate-800/40 rounded-xl border border-slate-100 dark:border-slate-800">
                <span className="text-[10px] uppercase font-bold text-slate-400 block">Growth Stage</span>
                <span className="font-bold text-xs text-emerald-600 dark:text-emerald-400 truncate block">
                  {statusData.growth_stage}
                </span>
                <span className="text-[10px] text-slate-400">
                  {statusData.days_after_sowing !== null ? `${statusData.days_after_sowing} DAS` : 'Manual Stage'}
                </span>
              </div>

              <div className="p-3 bg-slate-50 dark:bg-slate-800/40 rounded-xl border border-slate-100 dark:border-slate-800">
                <span className="text-[10px] uppercase font-bold text-slate-400 block">Water Sensitivity</span>
                <span className={`font-bold text-xs truncate block ${
                  statusData.water_status?.status === 'DEFICIT' ? 'text-amber-600' : 'text-slate-800 dark:text-slate-100'
                }`}>
                  {statusData.water_sensitivity}
                </span>
                <span className="text-[10px] text-slate-400">
                  FAO Kc: {statusData.crop_coefficient_kc?.toFixed(2)}
                </span>
              </div>

              <div className="p-3 bg-slate-50 dark:bg-slate-800/40 rounded-xl border border-slate-100 dark:border-slate-800">
                <span className="text-[10px] uppercase font-bold text-slate-400 block">Environmental Status</span>
                <span className={`font-bold text-xs truncate block ${
                  statusData.environmental_status?.status === 'OPTIMAL' ? 'text-emerald-600' : 'text-amber-600'
                }`}>
                  {statusData.environmental_status?.status}
                </span>
                <span className="text-[10px] text-slate-400">
                  {statusData.environmental_status?.temperature_c !== null ? `${statusData.environmental_status?.temperature_c?.toFixed(1)}°C` : 'Temp N/A'}
                </span>
              </div>
            </div>

            {/* Diagnostic Row: Nutrients, Diseases, Pests */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {/* Nutrient Advisory */}
              <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                    <FlaskConical className="w-3.5 h-3.5 text-blue-500" />
                    Nutrient Advisory
                  </span>
                  <button 
                    onClick={() => openExplorer('nutrients')}
                    className="text-[10px] text-slate-400 hover:text-brand"
                  >
                    Details &rarr;
                  </button>
                </div>
                <p className="text-[11px] text-slate-600 dark:text-slate-400 line-clamp-2">
                  {statusData.nutrient_advisory?.stage_priority}
                </p>
                <span className="text-[10px] text-slate-400 block italic">
                  * Requires lab soil test before chemical application
                </span>
              </div>

              {/* Disease Risk */}
              <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                    <ShieldAlert className="w-3.5 h-3.5 text-rose-500" />
                    Disease Risk Watch
                  </span>
                  <button 
                    onClick={() => openExplorer('protection')}
                    className="text-[10px] text-slate-400 hover:text-brand"
                  >
                    IPM &rarr;
                  </button>
                </div>
                {statusData.disease_risks && statusData.disease_risks.length > 0 ? (
                  <div className="space-y-1">
                    {statusData.disease_risks.slice(0, 2).map((d, i) => (
                      <div key={i} className="text-[11px] text-slate-700 dark:text-slate-300 flex items-center justify-between">
                        <span className="truncate">{d.disease_name}</span>
                        <span className="px-1 text-[9px] bg-rose-100 dark:bg-rose-950 text-rose-600 rounded font-semibold">
                          {d.risk_level}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-[11px] text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" />
                    No active disease warnings for current stage.
                  </p>
                )}
              </div>

              {/* Pest Risk */}
              <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                    <Bug className="w-3.5 h-3.5 text-amber-500" />
                    Pest Monitoring Watch
                  </span>
                  <button 
                    onClick={() => openExplorer('protection')}
                    className="text-[10px] text-slate-400 hover:text-brand"
                  >
                    ETL &rarr;
                  </button>
                </div>
                {statusData.pest_risks && statusData.pest_risks.length > 0 ? (
                  <div className="space-y-1">
                    {statusData.pest_risks.slice(0, 2).map((p, i) => (
                      <div key={i} className="text-[11px] text-slate-700 dark:text-slate-300 flex items-center justify-between">
                        <span className="truncate">{p.pest_name}</span>
                        <span className="text-[10px] text-slate-400">{p.monitoring?.split(';')?.[0]?.substring(0, 18)}...</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-[11px] text-slate-400">Scout weekly during early morning.</p>
                )}
              </div>
            </div>

            {/* Scientific Action Bar */}
            <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-emerald-600" />
                <span className="text-xs text-slate-600 dark:text-slate-300 font-medium">
                  Authoritative agricultural research available for this field
                </span>
              </div>
              <button
                onClick={() => openExplorer('overview')}
                className="px-3 py-1 bg-white dark:bg-slate-900 hover:bg-slate-100 dark:hover:bg-slate-800 text-brand border border-slate-200 dark:border-slate-700 rounded-lg text-xs font-semibold flex items-center gap-1 transition"
              >
                <span>Explore Knowledge Base</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </>
        )}
      </div>

      {/* Interactive Modal */}
      <KnowledgeExplorerModal 
        isOpen={showModal} 
        onClose={() => setShowModal(false)}
        initialTab={modalInitialTab}
      />
    </div>
  );
};

export default GreenGramKnowledgeCard;
