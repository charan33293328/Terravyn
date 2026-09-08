import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import apiClient from '../../api/client';
import { ArrowLeft, Save, AlertCircle, MapPin, Compass } from 'lucide-react';

const FarmForm = () => {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEdit = !!id;

  const [loading, setLoading] = useState(isEdit);
  const [submitting, setSubmitting] = useState(false);
  const [locating, setLocating] = useState(false);
  const [error, setError] = useState(null);

  const [formData, setFormData] = useState({
    name: '',
    crop_type: '',
    crop_variety: '',
    sowing_date: '',
    soil_type: '',
    area: '',
    area_unit: 'Acres',
    description: '',
    status: 'ACTIVE',
    expected_harvest_date: '',
    latitude: '',
    longitude: '',
    plot_type: 'STANDARD',
    experiment_active: false,
    village: '',
    district: '',
    state: '',
    country: 'India'
  });

  const cropTypes = ['Rice', 'Wheat', 'Green Gram (Moong)', 'Black Gram (Urad)', 'Cotton', 'Maize', 'Sugarcane', 'Groundnut', 'Tomato', 'Chili', 'Banana', 'Mango', 'Other'];
  const soilTypes = ['Sandy Loam', 'Clay Loam', 'Black Soil (Regur)', 'Red Sandy Soil', 'Alluvial Soil', 'Silt Loam', 'Saline / Alkaline'];
  const statuses = ['ACTIVE', 'INACTIVE', 'HARVESTED', 'UNDER_PREPARATION'];

  useEffect(() => {
    if (isEdit) {
      fetchFarmDetails();
    }
  }, [id]);

  const fetchFarmDetails = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get(`/farmer/farms/${id}`);
      const data = res.data;
      setFormData({
        name: data.name || '',
        crop_type: data.crop_type || '',
        crop_variety: data.crop_variety || '',
        sowing_date: data.sowing_date ? data.sowing_date.split('T')[0] : '',
        soil_type: data.soil_type || '',
        area: data.area || '',
        area_unit: data.area_unit || 'Acres',
        description: data.description || '',
        status: data.status || 'ACTIVE',
        expected_harvest_date: data.expected_harvest_date ? data.expected_harvest_date.split('T')[0] : '',
        latitude: data.latitude != null ? data.latitude : '',
        longitude: data.longitude != null ? data.longitude : '',
        plot_type: data.plot_type || 'STANDARD',
        experiment_active: data.experiment_active || false,
        village: data.village || '',
        district: data.district || '',
        state: data.state || '',
        country: data.country || 'India'
      });
    } catch (err) {
      setError('Failed to fetch farm details');
    } finally {
      setLoading(false);
    }
  };

  const detectLocation = () => {
    if (!navigator.geolocation) {
      alert("Geolocation is not supported by your browser");
      return;
    }
    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setFormData(prev => ({
          ...prev,
          latitude: pos.coords.latitude.toFixed(6),
          longitude: pos.coords.longitude.toFixed(6)
        }));
        setLocating(false);
      },
      (err) => {
        alert(`Unable to retrieve GPS location: ${err.message}`);
        setLocating(false);
      },
      { timeout: 10000, enableHighAccuracy: true }
    );
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({ 
      ...prev, 
      [name]: type === 'checkbox' ? checked : value 
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    if (!formData.name) {
      setError('Farm Name is required');
      return;
    }

    try {
      setSubmitting(true);
      const payload = {
        ...formData,
        area: formData.area ? parseFloat(formData.area) : null,
        latitude: formData.latitude !== '' && formData.latitude !== null && !isNaN(parseFloat(formData.latitude)) ? parseFloat(formData.latitude) : null,
        longitude: formData.longitude !== '' && formData.longitude !== null && !isNaN(parseFloat(formData.longitude)) ? parseFloat(formData.longitude) : null,
        expected_harvest_date: formData.expected_harvest_date ? new Date(formData.expected_harvest_date).toISOString() : null,
        sowing_date: formData.sowing_date ? new Date(formData.sowing_date).toISOString() : null,
        crop_variety: formData.crop_variety || null,
        soil_type: formData.soil_type || null,
        plot_type: formData.plot_type || 'STANDARD',
        experiment_active: Boolean(formData.experiment_active)
      };

      if (isEdit) {
        await apiClient.put(`/farmer/farms/${id}`, payload);
      } else {
        await apiClient.post(`/farmer/farms`, payload);
      }
      navigate('/farmer/farms');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save farm');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand"></div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <button 
        onClick={() => navigate('/farmer/farms')}
        className="flex items-center gap-2 text-slate-500 hover:text-slate-800 mb-6 transition"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Farms
      </button>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="p-6 border-b border-slate-200">
          <h1 className="text-2xl font-bold text-slate-800">{isEdit ? 'Edit Farm' : 'Create New Farm'}</h1>
          <p className="text-slate-500">{isEdit ? 'Update your farm information below.' : 'Add a new farm to manage devices and monitoring.'}</p>
        </div>

        {error && (
          <div className="m-6 p-4 bg-red-50 text-red-700 rounded-lg flex items-center gap-2">
            <AlertCircle className="w-5 h-5" />
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2 md:col-span-2">
              <label className="block text-sm font-medium text-slate-700">Farm Name *</label>
              <input 
                type="text" 
                name="name" 
                value={formData.name} 
                onChange={handleChange} 
                className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-brand focus:border-brand"
                placeholder="e.g. North Block Field"
                required
              />
            </div>

            <div className="space-y-2">
              <label className="block text-sm font-medium text-slate-700">Crop Type</label>
              <select 
                name="crop_type" 
                value={formData.crop_type} 
                onChange={handleChange}
                className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-brand focus:border-brand"
              >
                <option value="">Select Crop...</option>
                {cropTypes.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>

            <div className="space-y-2">
              <label className="block text-sm font-medium text-slate-700">Crop Variety</label>
              <input 
                type="text" 
                name="crop_variety" 
                value={formData.crop_variety} 
                onChange={handleChange} 
                className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-brand focus:border-brand"
                placeholder="e.g. IPM 02-03, SML 668"
              />
            </div>

            <div className="space-y-2">
              <label className="block text-sm font-medium text-slate-700">Sowing Date</label>
              <input 
                type="date" 
                name="sowing_date" 
                value={formData.sowing_date} 
                onChange={handleChange} 
                className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-brand focus:border-brand"
              />
            </div>

            <div className="space-y-2">
              <label className="block text-sm font-medium text-slate-700">Expected Harvest Date</label>
              <input 
                type="date" 
                name="expected_harvest_date" 
                value={formData.expected_harvest_date} 
                onChange={handleChange} 
                className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-brand focus:border-brand"
              />
            </div>

            <div className="space-y-2">
              <label className="block text-sm font-medium text-slate-700">Soil Type</label>
              <select 
                name="soil_type" 
                value={formData.soil_type} 
                onChange={handleChange}
                className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-brand focus:border-brand"
              >
                <option value="">Select Soil Type...</option>
                {soilTypes.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>

            <div className="space-y-2">
              <label className="block text-sm font-medium text-slate-700">Status</label>
              <select 
                name="status" 
                value={formData.status} 
                onChange={handleChange}
                className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-brand focus:border-brand"
              >
                {statuses.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>

            <div className="space-y-2 md:col-span-2">
              <label className="block text-sm font-medium text-slate-700">Area</label>
              <div className="flex gap-2">
                <input 
                  type="number" 
                  step="0.01"
                  name="area" 
                  value={formData.area} 
                  onChange={handleChange} 
                  className="w-2/3 px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-brand focus:border-brand"
                  placeholder="e.g. 5.5"
                />
                <select 
                  name="area_unit" 
                  value={formData.area_unit} 
                  onChange={handleChange}
                  className="w-1/3 px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-brand focus:border-brand"
                >
                  <option value="Acres">Acres</option>
                  <option value="Hectares">Hectares</option>
                  <option value="Sq Meters">Sq Meters</option>
                </select>
              </div>
            </div>

            <div className="space-y-2">
              <label className="block text-sm font-medium text-slate-700">Plot Type (Experimentation)</label>
              <select 
                name="plot_type" 
                value={formData.plot_type} 
                onChange={handleChange}
                className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-brand focus:border-brand text-sm"
              >
                <option value="STANDARD">Standard Production Field</option>
                <option value="TERRAVYN">Terravyn Recommended Plot (Experimental)</option>
                <option value="CONTROL">Control Plot (Farmer Standard Practice)</option>
              </select>
            </div>

            <div className="space-y-2 flex flex-col justify-center">
              <label className="flex items-center gap-2 text-sm font-medium text-slate-700 cursor-pointer pt-6">
                <input 
                  type="checkbox"
                  name="experiment_active"
                  checked={formData.experiment_active}
                  onChange={handleChange}
                  className="w-4 h-4 text-brand rounded focus:ring-brand accent-brand"
                />
                <span>Enable Green Gram Experiment Tracking</span>
              </label>
              <p className="text-[11px] text-slate-400">Records plant responses & water usage for agronomic comparison.</p>
            </div>
          </div>

          <div className="border-t border-slate-200 pt-6 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-medium text-slate-800">Field Location & GPS</h3>
                <p className="text-xs text-slate-500">Accurate coordinates power meteorological forecasts and reference evapotranspiration (ET₀).</p>
              </div>
              <button
                type="button"
                onClick={detectLocation}
                disabled={locating}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-brand/10 text-brand text-xs font-semibold rounded-lg hover:bg-brand/20 transition disabled:opacity-50"
              >
                <Compass className={`w-3.5 h-3.5 ${locating ? 'animate-spin' : ''}`} />
                {locating ? 'Detecting...' : 'Detect GPS Location'}
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 bg-slate-50 p-4 rounded-xl border border-slate-200">
              <div className="space-y-2">
                <label className="block text-sm font-medium text-slate-700 flex items-center gap-1">
                  <MapPin className="w-3.5 h-3.5 text-brand" /> Latitude (°N)
                </label>
                <input 
                  type="number" 
                  step="any"
                  name="latitude" 
                  value={formData.latitude} 
                  onChange={handleChange} 
                  className="w-full px-4 py-2 bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-brand focus:border-brand text-sm"
                  placeholder="e.g. 17.3850"
                />
              </div>

              <div className="space-y-2">
                <label className="block text-sm font-medium text-slate-700 flex items-center gap-1">
                  <MapPin className="w-3.5 h-3.5 text-brand" /> Longitude (°E)
                </label>
                <input 
                  type="number" 
                  step="any"
                  name="longitude" 
                  value={formData.longitude} 
                  onChange={handleChange} 
                  className="w-full px-4 py-2 bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-brand focus:border-brand text-sm"
                  placeholder="e.g. 78.4867"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
              <div className="space-y-2">
                <label className="block text-sm font-medium text-slate-700">Village / Region</label>
                <input 
                  type="text" 
                  name="village" 
                  value={formData.village} 
                  onChange={handleChange} 
                  className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-brand focus:border-brand"
                />
              </div>
              <div className="space-y-2">
                <label className="block text-sm font-medium text-slate-700">District</label>
                <input 
                  type="text" 
                  name="district" 
                  value={formData.district} 
                  onChange={handleChange} 
                  className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-brand focus:border-brand"
                />
              </div>
              <div className="space-y-2">
                <label className="block text-sm font-medium text-slate-700">State</label>
                <input 
                  type="text" 
                  name="state" 
                  value={formData.state} 
                  onChange={handleChange} 
                  className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-brand focus:border-brand"
                />
              </div>
              <div className="space-y-2">
                <label className="block text-sm font-medium text-slate-700">Country</label>
                <input 
                  type="text" 
                  name="country" 
                  value={formData.country} 
                  onChange={handleChange} 
                  className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-brand focus:border-brand"
                />
              </div>
            </div>
          </div>

          <div className="border-t border-slate-200 pt-6">
            <div className="space-y-2">
              <label className="block text-sm font-medium text-slate-700">Additional Description</label>
              <textarea 
                name="description" 
                value={formData.description} 
                onChange={handleChange} 
                rows="3"
                className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-brand focus:border-brand"
                placeholder="Notes about soil type, irrigation setup, etc."
              ></textarea>
            </div>
          </div>

          <div className="pt-4 flex justify-end gap-3 border-t border-slate-200 mt-6">
            <button 
              type="button" 
              onClick={() => navigate('/farmer/farms')}
              className="px-6 py-2 border border-slate-200 text-slate-700 rounded-lg hover:bg-slate-50 transition"
              disabled={submitting}
            >
              Cancel
            </button>
            <button 
              type="submit" 
              className="px-6 py-2 bg-brand text-white rounded-lg hover:bg-brand/90 transition flex items-center gap-2"
              disabled={submitting}
            >
              {submitting ? 'Saving...' : <><Save className="w-5 h-5" /> Save Farm</>}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default FarmForm;
