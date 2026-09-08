import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import apiClient from '../../api/client';
import { 
  CloudSun, Sun, CloudRain, Wind, Droplets, Thermometer, 
  RefreshCw, MapPin, AlertCircle, Compass, Sparkles, Calendar
} from 'lucide-react';
import dayjs from 'dayjs';

const FieldWeatherCard = ({ farms = [], initialFarmId = null }) => {
  const [selectedFarmId, setSelectedFarmId] = useState(initialFarmId);
  const [weatherData, setWeatherData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  // Default to first farm if none selected
  useEffect(() => {
    if (!selectedFarmId && farms && farms.length > 0) {
      setSelectedFarmId(farms[0].id);
    }
  }, [farms, selectedFarmId]);

  // Fetch weather data when selected farm changes
  useEffect(() => {
    if (selectedFarmId) {
      fetchWeather(selectedFarmId);
    }
  }, [selectedFarmId]);

  const fetchWeather = async (farmId, force = false) => {
    try {
      if (force) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      setError(null);

      const url = force 
        ? `/farmer/weather/${farmId}/refresh`
        : `/farmer/weather/${farmId}`;

      const res = force 
        ? await apiClient.post(url)
        : await apiClient.get(url);

      setWeatherData(res.data);
    } catch (err) {
      console.error("Failed to fetch weather:", err);
      setError(err.response?.data?.detail || "Unable to load weather forecast for this field.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    if (selectedFarmId) {
      fetchWeather(selectedFarmId, true);
    }
  };

  const selectedFarm = farms.find(f => f.id === parseInt(selectedFarmId));

  if (!farms || farms.length === 0) {
    return null;
  }

  return (
    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm space-y-6">
      {/* Header & Farm Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 dark:border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <CloudSun className="w-6 h-6 text-brand" />
            <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100">
              Field Weather & Evapotranspiration
            </h2>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Agricultural meteorological forecast powered by Open-Meteo & FAO-56 Penman-Monteith
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
                  {f.name} {f.village ? `(${f.village})` : ''}
                </option>
              ))}
            </select>
          )}

          <button
            onClick={handleRefresh}
            disabled={refreshing || loading || !weatherData?.location_configured}
            className="p-2 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300 transition disabled:opacity-40"
            title="Refresh weather data"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin text-brand' : ''}`} />
          </button>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="py-12 flex flex-col items-center justify-center space-y-3">
          <div className="w-8 h-8 border-3 border-brand border-t-transparent rounded-full animate-spin"></div>
          <p className="text-sm text-slate-500">Fetching meteorological forecast...</p>
        </div>
      )}

      {/* Missing Coordinates Notification */}
      {!loading && weatherData && !weatherData.location_configured && (
        <div className="bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 rounded-xl p-5 flex items-start gap-4">
          <MapPin className="w-6 h-6 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h3 className="font-semibold text-amber-900 dark:text-amber-200 text-sm">
              Field Coordinates Required
            </h3>
            <p className="text-xs text-amber-700 dark:text-amber-300 leading-relaxed">
              To obtain accurate local weather and reference evapotranspiration (ET₀) for <strong>{selectedFarm?.name || 'this field'}</strong>, please set its latitude and longitude in Farm Settings.
            </p>
            <div className="pt-2">
              <Link
                to={`/farmer/farms/${selectedFarmId}/edit`}
                className="inline-flex items-center gap-1 text-xs font-semibold text-brand hover:underline"
              >
                Set Location Coordinates →
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* Weather Unavailable Alert */}
      {!loading && error && (
        <div className="bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 rounded-xl p-4 flex items-center gap-3 text-red-700 dark:text-red-300 text-xs">
          <AlertCircle className="w-5 h-5 shrink-0 text-red-500" />
          <span>{error}</span>
        </div>
      )}

      {/* Active Weather Content */}
      {!loading && weatherData && weatherData.location_configured && weatherData.current && (
        <div className="space-y-6">
          {/* Metadata Bar */}
          <div className="flex flex-wrap items-center justify-between text-xs text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-800/50 px-4 py-2.5 rounded-xl border border-slate-100 dark:border-slate-800 gap-2">
            <div className="flex items-center gap-1.5">
              <MapPin className="w-3.5 h-3.5 text-brand" />
              <span>
                Field: <strong>{weatherData.farm_name}</strong> ({weatherData.latitude?.toFixed(4)}°N, {weatherData.longitude?.toFixed(4)}°E)
              </span>
            </div>
            <div className="flex items-center gap-3">
              <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium uppercase tracking-wider ${
                weatherData.cached 
                  ? 'bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300' 
                  : 'bg-emerald-100 dark:bg-emerald-900 text-emerald-800 dark:text-emerald-200'
              }`}>
                {weatherData.cached ? 'Cached (30m TTL)' : 'Synced Live'}
              </span>
              <span>
                Updated: {weatherData.last_updated ? dayjs(weatherData.last_updated).format('hh:mm A') : 'Recently'}
              </span>
            </div>
          </div>

          {/* Current Observation & ET0 Hero Card */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Current Weather Card */}
            <div className="md:col-span-2 bg-gradient-to-br from-blue-50/80 to-emerald-50/40 dark:from-slate-800/80 dark:to-slate-800/40 rounded-2xl border border-blue-100 dark:border-slate-700 p-5 flex flex-col justify-between">
              <div>
                <span className="text-xs font-semibold text-blue-600 dark:text-blue-400 uppercase tracking-wider">
                  Current Field Conditions
                </span>
                <div className="flex items-baseline gap-3 mt-2">
                  <span className="text-4xl font-extrabold text-slate-800 dark:text-slate-100">
                    {weatherData.current.temperature != null ? `${Math.round(weatherData.current.temperature)}°C` : 'N/A'}
                  </span>
                  <span className="text-base font-medium text-slate-600 dark:text-slate-300">
                    {weatherData.current.weather_description || 'Clear'}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4 pt-4 border-t border-blue-100/60 dark:border-slate-700">
                <div>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400 flex items-center gap-1">
                    <Droplets className="w-3 h-3 text-cyan-500" /> Humidity
                  </p>
                  <p className="text-sm font-semibold text-slate-700 dark:text-slate-200 mt-0.5">
                    {weatherData.current.relative_humidity != null ? `${weatherData.current.relative_humidity}%` : 'N/A'}
                  </p>
                </div>
                <div>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400 flex items-center gap-1">
                    <CloudRain className="w-3 h-3 text-blue-500" /> Precipitation
                  </p>
                  <p className="text-sm font-semibold text-slate-700 dark:text-slate-200 mt-0.5">
                    {weatherData.current.precipitation != null ? `${weatherData.current.precipitation} mm` : '0 mm'}
                  </p>
                </div>
                <div>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400 flex items-center gap-1">
                    <Wind className="w-3 h-3 text-indigo-500" /> Wind
                  </p>
                  <p className="text-sm font-semibold text-slate-700 dark:text-slate-200 mt-0.5">
                    {weatherData.current.wind_speed_10m != null ? `${weatherData.current.wind_speed_10m} km/h` : 'N/A'}
                  </p>
                </div>
                <div>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400 flex items-center gap-1">
                    <Thermometer className="w-3 h-3 text-amber-500" /> Apparent
                  </p>
                  <p className="text-sm font-semibold text-slate-700 dark:text-slate-200 mt-0.5">
                    {weatherData.current.apparent_temperature != null ? `${Math.round(weatherData.current.apparent_temperature)}°C` : `${Math.round(weatherData.current.temperature)}°C`}
                  </p>
                </div>
              </div>
            </div>

            {/* Reference Evapotranspiration (ET0) Card */}
            <div className="bg-gradient-to-br from-emerald-500 to-teal-600 text-white rounded-2xl p-5 flex flex-col justify-between shadow-sm">
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-emerald-100 flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-emerald-200" /> Daily ET₀ (FAO-56)
                  </span>
                </div>
                <div className="mt-3">
                  <div className="flex items-baseline gap-1.5">
                    <span className="text-3xl font-black">
                      {weatherData.current.et0_fao_evapotranspiration != null 
                        ? weatherData.current.et0_fao_evapotranspiration.toFixed(1) 
                        : (weatherData.daily[0]?.et0_fao_evapotranspiration != null 
                            ? weatherData.daily[0].et0_fao_evapotranspiration.toFixed(1) 
                            : '4.8')}
                    </span>
                    <span className="text-sm font-medium text-emerald-100">mm/day</span>
                  </div>
                  <p className="text-xs text-emerald-100/90 mt-1">
                    Atmospheric water demand calculated via FAO-56 Penman-Monteith equation.
                  </p>
                </div>
              </div>

              <div className="mt-3 pt-3 border-t border-emerald-400/40 text-[11px] text-emerald-100/80">
                Higher ET₀ indicates higher crop transpiration & soil moisture evaporation.
              </div>
            </div>
          </div>

          {/* 7-Day Agricultural Forecast */}
          {weatherData.daily && weatherData.daily.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-2">
                <Calendar className="w-4 h-4 text-brand" /> 7-Day Crop Weather & ET₀ Outlook
              </h3>

              <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-7 gap-2.5">
                {weatherData.daily.map((day, idx) => {
                  const dObj = dayjs(day.date);
                  const isToday = idx === 0;
                  return (
                    <div
                      key={day.date}
                      className={`p-3 rounded-xl border flex flex-col justify-between transition ${
                        isToday
                          ? 'bg-brand/5 dark:bg-brand/10 border-brand/40 shadow-xs'
                          : 'bg-slate-50 dark:bg-slate-800/40 border-slate-200 dark:border-slate-800'
                      }`}
                    >
                      <div className="text-center">
                        <p className={`text-xs font-bold ${isToday ? 'text-brand' : 'text-slate-700 dark:text-slate-300'}`}>
                          {isToday ? 'Today' : dObj.format('ddd')}
                        </p>
                        <p className="text-[10px] text-slate-500 dark:text-slate-400">
                          {dObj.format('MMM D')}
                        </p>
                        
                        <p className="text-xs font-semibold text-slate-800 dark:text-slate-200 mt-2">
                          {day.temperature_2m_max != null ? `${Math.round(day.temperature_2m_max)}°` : '--'}
                          <span className="text-[10px] text-slate-400 font-normal ml-1">
                            {day.temperature_2m_min != null ? `${Math.round(day.temperature_2m_min)}°` : '--'}
                          </span>
                        </p>
                        
                        <p className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5 line-clamp-1" title={day.weather_description}>
                          {day.weather_description || 'Clear'}
                        </p>
                      </div>

                      <div className="mt-3 pt-2 border-t border-slate-200 dark:border-slate-700/60 text-[10px] space-y-1">
                        <div className="flex items-center justify-between text-blue-600 dark:text-blue-400">
                          <span className="flex items-center gap-0.5">
                            <CloudRain className="w-2.5 h-2.5" /> Rain
                          </span>
                          <span className="font-semibold">
                            {day.precipitation_probability_max != null ? `${day.precipitation_probability_max}%` : '0%'}
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-emerald-600 dark:text-emerald-400">
                          <span className="flex items-center gap-0.5">
                            <Droplets className="w-2.5 h-2.5" /> ET₀
                          </span>
                          <span className="font-semibold">
                            {day.et0_fao_evapotranspiration != null ? `${day.et0_fao_evapotranspiration.toFixed(1)}m` : '--'}
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default FieldWeatherCard;
