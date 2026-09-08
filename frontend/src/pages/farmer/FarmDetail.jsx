import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import apiClient from '../../api/client';
import { 
  ArrowLeft, MapPin, Edit, Trash2, Leaf, Calendar, 
  Cpu, Thermometer, Droplets, Activity, Plus
} from 'lucide-react';
import dayjs from 'dayjs';
import FieldWeatherCard from '../../components/weather/FieldWeatherCard';
import TerravynDecisionCard from '../../components/decision/TerravynDecisionCard';
import GreenGramKnowledgeCard from '../../components/knowledge/GreenGramKnowledgeCard';
import GreenGramExperimentCard from '../../components/experiment/GreenGramExperimentCard';
import IrrigationIntelligencePanel from '../../components/irrigation/IrrigationIntelligencePanel';
import LearningDashboardPanel from '../../components/learning/LearningDashboardPanel';

const FarmDetail = () => {
  const navigate = useNavigate();
  const { id } = useParams();
  
  const [farm, setFarm] = useState(null);
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchFarmData();
  }, [id]);

  const fetchFarmData = async () => {
    try {
      setLoading(true);
      const farmRes = await apiClient.get(`/farmer/farms/${id}`);
      setFarm(farmRes.data);

      // Fetch devices for this farm
      const devicesRes = await apiClient.get(`/farmer/devices`);
      const allDevices = Array.isArray(devicesRes.data) ? devicesRes.data : (devicesRes.data.devices || []);
      const farmDevices = allDevices.filter(d => d.farm_id === parseInt(id));
      setDevices(farmDevices);

    } catch (err) {
      setError('Failed to fetch farm details');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (devices.length > 0) {
      alert('Cannot delete farm. Reassign or unlink devices first.');
      return;
    }
    
    if (window.confirm('Are you sure you want to delete this farm? This action cannot be undone.')) {
      try {
        await apiClient.delete(`/farmer/farms/${id}`);
        navigate('/farmer/farms');
      } catch (err) {
        alert(err.response?.data?.detail || 'Failed to delete farm');
      }
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand"></div>
      </div>
    );
  }

  if (error || !farm) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <div className="bg-red-50 text-red-700 p-4 rounded-lg">{error || 'Farm not found'}</div>
        <button onClick={() => navigate('/farmer/farms')} className="mt-4 text-brand font-medium">Back to Farms</button>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button 
          onClick={() => navigate('/farmer/farms')}
          className="p-2 border border-slate-200 rounded-lg hover:bg-slate-50 transition"
        >
          <ArrowLeft className="w-5 h-5 text-slate-600" />
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-slate-800">{farm.name}</h1>
            <span className={`px-2 py-1 text-xs font-medium rounded ${
              farm.status === 'ACTIVE' ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-700'
            }`}>
              {farm.status}
            </span>
          </div>
          <p className="text-slate-500 flex items-center gap-1 mt-1">
            <MapPin className="w-4 h-4" />
            {[farm.village, farm.district, farm.state, farm.country].filter(Boolean).join(', ') || 'Location not specified'}
          </p>
        </div>
        <div className="flex gap-2">
          <button 
            onClick={() => navigate(`/farmer/farms/${id}/edit`)}
            className="px-4 py-2 border border-slate-200 text-slate-700 rounded-lg hover:bg-slate-50 transition flex items-center gap-2"
          >
            <Edit className="w-4 h-4" /> Edit
          </button>
          <button 
            onClick={handleDelete}
            className="px-4 py-2 border border-red-200 text-red-600 rounded-lg hover:bg-red-50 transition flex items-center gap-2"
          >
            <Trash2 className="w-4 h-4" /> Delete
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Details */}
        <div className="space-y-6">
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-6">
            <h3 className="text-lg font-bold text-slate-800 border-b border-slate-100 pb-2">Farm Details</h3>
            
            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <Leaf className="w-5 h-5 text-brand mt-0.5" />
                <div>
                  <p className="text-sm text-slate-500">Crop Type & Variety</p>
                  <p className="font-medium text-slate-800">
                    {farm.crop_type || 'Not specified'} 
                    {farm.crop_variety ? ` (${farm.crop_variety})` : ''}
                  </p>
                  {farm.plot_type && farm.plot_type !== 'STANDARD' && (
                    <span className="inline-block mt-1 px-2 py-0.5 text-[10px] font-bold rounded uppercase tracking-wider bg-brand/10 text-brand border border-brand/20">
                      Experiment Plot: {farm.plot_type}
                    </span>
                  )}
                </div>
              </div>

              {farm.sowing_date && (
                <div className="flex items-start gap-3">
                  <Calendar className="w-5 h-5 text-brand mt-0.5" />
                  <div>
                    <p className="text-sm text-slate-500">Sowing Date</p>
                    <p className="font-medium text-slate-800">
                      {dayjs(farm.sowing_date).format('MMM D, YYYY')}
                    </p>
                  </div>
                </div>
              )}

              {farm.soil_type && (
                <div className="flex items-start gap-3">
                  <Leaf className="w-5 h-5 text-brand mt-0.5" />
                  <div>
                    <p className="text-sm text-slate-500">Soil Type</p>
                    <p className="font-medium text-slate-800">{farm.soil_type}</p>
                  </div>
                </div>
              )}
              
              <div className="flex items-start gap-3">
                <MapPin className="w-5 h-5 text-brand mt-0.5" />
                <div>
                  <p className="text-sm text-slate-500">Field Coordinates (GPS)</p>
                  <p className="font-medium text-slate-800">
                    {farm.latitude != null && farm.longitude != null 
                      ? `${farm.latitude.toFixed(4)}°N, ${farm.longitude.toFixed(4)}°E` 
                      : <span className="text-amber-600 text-xs">Coordinates not set</span>}
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <MapPin className="w-5 h-5 text-brand mt-0.5" />
                <div>
                  <p className="text-sm text-slate-500">Total Area</p>
                  <p className="font-medium text-slate-800">{farm.area ? `${farm.area} ${farm.area_unit}` : 'Not specified'}</p>
                </div>
              </div>
              
              <div className="flex items-start gap-3">
                <Calendar className="w-5 h-5 text-brand mt-0.5" />
                <div>
                  <p className="text-sm text-slate-500">Expected Harvest</p>
                  <p className="font-medium text-slate-800">
                    {farm.expected_harvest_date ? dayjs(farm.expected_harvest_date).format('MMM D, YYYY') : 'Not specified'}
                  </p>
                </div>
              </div>

              {farm.description && (
                <div className="pt-4 border-t border-slate-100">
                  <p className="text-sm text-slate-500 mb-1">Description</p>
                  <p className="text-sm text-slate-700">{farm.description}</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Decisions, Weather & Linked Devices */}
        <div className="lg:col-span-2 space-y-6">
          {/* Terravyn Green Gram Decision Engine Card */}
          <TerravynDecisionCard farms={[farm]} initialFarmId={farm.id} />

          {/* Production Irrigation Intelligence Panel (Prompt 8) */}
          <IrrigationIntelligencePanel farmId={farm.id} farmName={farm.name} />

          {/* Green Gram Crop Profile & Agronomic Knowledge Card */}
          <GreenGramKnowledgeCard farmId={farm.id} farmName={farm.name} />

          {/* Green Gram Controlled Experiment & Replicate Data Engine */}
          <GreenGramExperimentCard farmId={farm.id} farmName={farm.name} />

          {/* Terravyn Closed-Loop Learning & Continuous Improvement Panel (Prompt 9) */}
          <LearningDashboardPanel farmId={farm.id} />

          {/* Farm Weather Forecast Widget */}
          <FieldWeatherCard farms={[farm]} initialFarmId={farm.id} />

          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-lg font-bold text-slate-800">Linked Devices</h3>
              <button 
                onClick={() => navigate('/farmer/devices')}
                className="text-sm text-brand font-medium hover:underline flex items-center gap-1"
              >
                <Plus className="w-4 h-4" /> Link More Devices
              </button>
            </div>

            {devices.length === 0 ? (
              <div className="text-center py-8 bg-slate-50 rounded-lg border border-dashed border-slate-200">
                <Cpu className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                <p className="text-slate-600 font-medium">No devices linked to this farm</p>
                <p className="text-sm text-slate-500 mt-1">Go to My Devices to assign a device to this farm.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {devices.map(device => (
                  <div key={device.device_uid} className="border border-slate-200 rounded-lg p-4 hover:border-brand/30 transition">
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="font-semibold text-slate-800 truncate">{device.name || device.device_uid}</h4>
                      <span className={`w-2 h-2 rounded-full ${device.connection_status === 'ONLINE' ? 'bg-green-500' : 'bg-red-500'} mt-1.5`} title={device.connection_status}></span>
                    </div>
                    <p className="text-xs text-slate-500 font-mono mb-3">{device.device_uid}</p>
                    
                    <div className="grid grid-cols-2 gap-2 mt-4 pt-4 border-t border-slate-100">
                      <div className="flex items-center gap-1.5 text-sm">
                        <Thermometer className="w-4 h-4 text-orange-500" />
                        <span className="text-slate-700">{device.sensor_data?.temperature ? `${device.sensor_data.temperature}°C` : '--'}</span>
                      </div>
                      <div className="flex items-center gap-1.5 text-sm">
                        <Droplets className="w-4 h-4 text-blue-500" />
                        <span className="text-slate-700">{device.sensor_data?.soil_moisture ? `${device.sensor_data.soil_moisture}%` : '--'}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default FarmDetail;
