import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Server, Activity, Thermometer, Droplets, Bell, MapPin,
  ThermometerSun, Wind, CloudRain, Wifi, Clock, Settings, Power,
  Cloud, BarChart2, CheckCircle, AlertTriangle
} from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import apiClient from '../../api/client';
import dayjs from 'dayjs';

const MonitoringDeviceDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [chartData, setChartData] = useState([]);
  const [timeRange, setTimeRange] = useState('Last 24 Hours');

  const fetchDeviceData = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get(`/farmer/monitoring/devices/${id}`);
      setData(res.data);

      const chartsRes = await apiClient.get('/farmer/monitoring/charts', {
        params: { device_id: id, time_range: timeRange }
      });
      setChartData(chartsRes.data);
    } catch (err) {
      console.error('Failed to load device details', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDeviceData();
  }, [id, timeRange]);

  const renderChart = (metricData, label, color) => {
    if (!metricData || metricData.data.length === 0) return (
      <div className="h-64 flex items-center justify-center bg-slate-50 rounded-xl border border-slate-100 text-slate-400">
        No data for {label}
      </div>
    );

    return (
      <div className="h-64 mt-4">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={metricData.data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
            <XAxis
              dataKey="timestamp"
              tickFormatter={(val) => dayjs(val).format('HH:mm')}
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#64748b', fontSize: 12 }}
              dy={10}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#64748b', fontSize: 12 }}
            />
            <Tooltip
              labelFormatter={(label) => dayjs(label).format('MMM D, YYYY HH:mm')}
              contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
            />
            <Line
              type="monotone"
              dataKey="value"
              stroke={color}
              strokeWidth={3}
              dot={false}
              activeDot={{ r: 6, strokeWidth: 0 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    );
  };

  if (loading && !data) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand"></div>
      </div>
    );
  }

  if (!data) {
    return <div className="text-center py-12 text-slate-500">Failed to load device monitoring data.</div>;
  }

  const { device_info, latest_telemetry, recent_alerts } = data;

  // Find specific charts
  const getChart = (metric) => chartData.find(c => c.metric === metric);

  const formatUptime = (seconds) => {
    if (!seconds) return 'N/A';
    const d = Math.floor(seconds / (3600 * 24));
    const h = Math.floor(seconds % (3600 * 24) / 3600);
    const m = Math.floor(seconds % 3600 / 60);
    if (d > 0) return `${d}d ${h}h`;
    if (h > 0) return `${h}h ${m}m`;
    return `${m}m`;
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <button
        onClick={() => navigate('/farmer/monitoring')}
        className="flex items-center gap-2 text-sm font-medium text-slate-500 hover:text-brand transition-colors mb-4"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Monitoring Center
      </button>

      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-3">
            <Server className="w-6 h-6 text-brand" /> {device_info.name || 'Unnamed Device'}
          </h1>
          <p className="text-slate-500 mt-1 flex items-center gap-2">
            <span className="font-mono text-sm">{device_info.uid}</span>
            <span className="text-slate-300">•</span>
            <span>{device_info.farm_name || 'Unassigned'}</span>
          </p>
        </div>
        <div className="flex flex-col items-end gap-2">
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${device_info.connection_status === 'ONLINE' ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-600'
            }`}>
            {device_info.connection_status}
          </span>
          {latest_telemetry.recorded_at && (
            <span className="text-xs text-slate-500">
              Last updated {dayjs(latest_telemetry.recorded_at).fromNow()}
            </span>
          )}
        </div>
      </div>

      {/* Environmental Intelligence Dashboard (Cards) */}
      <h2 className="text-xl font-bold text-slate-800 mt-8 mb-4 border-b pb-2">Environmental Intelligence</h2>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-5 gap-4">

        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div className="flex items-center gap-2 mb-2 text-slate-500">
            <Droplets className="w-5 h-5 text-blue-500" />
            <span className="text-sm font-medium">Soil Moisture</span>
          </div>
          <p className="text-2xl font-bold text-slate-900">
            {latest_telemetry.soil_moisture !== null ? `${latest_telemetry.soil_moisture}%` : 'N/A'}
          </p>
        </div>

        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div className="flex items-center gap-2 mb-2 text-slate-500">
            <ThermometerSun className="w-5 h-5 text-orange-500" />
            <span className="text-sm font-medium">Ambient Temp</span>
          </div>
          <p className="text-2xl font-bold text-slate-900">
            {latest_telemetry.temperature !== null ? `${latest_telemetry.temperature}°C` : 'N/A'}
          </p>
        </div>

        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div className="flex items-center gap-2 mb-2 text-slate-500">
            <CloudRain className="w-5 h-5 text-cyan-500" />
            <span className="text-sm font-medium">Humidity</span>
          </div>
          <p className="text-2xl font-bold text-slate-900">
            {latest_telemetry.humidity !== null ? `${latest_telemetry.humidity}%` : 'N/A'}
          </p>
        </div>

        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div className="flex items-center gap-2 mb-2 text-slate-500">
            <Thermometer className="w-5 h-5 text-red-500" />
            <span className="text-sm font-medium">Atmos. Temp</span>
          </div>
          <p className="text-2xl font-bold text-slate-900">
            {latest_telemetry.bmp_temperature !== null ? `${latest_telemetry.bmp_temperature}°C` : 'N/A'}
          </p>
        </div>

        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div className="flex items-center gap-2 mb-2 text-slate-500">
            <Wind className="w-5 h-5 text-teal-500" />
            <span className="text-sm font-medium">Pressure</span>
          </div>
          <p className="text-2xl font-bold text-slate-900">
            {latest_telemetry.pressure !== null ? `${latest_telemetry.pressure} hPa` : 'N/A'}
          </p>
        </div>

        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div className="flex items-center gap-2 mb-2 text-slate-500">
            <BarChart2 className="w-5 h-5 text-purple-500" />
            <span className="text-sm font-medium">Est. Altitude</span>
          </div>
          <p className="text-2xl font-bold text-slate-900">
            {latest_telemetry.altitude !== null ? `${latest_telemetry.altitude} m` : 'N/A'}
          </p>
        </div>

        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div className="flex items-center gap-2 mb-2 text-slate-500">
            <Activity className="w-5 h-5 text-slate-500" />
            <span className="text-sm font-medium">Pressure</span>
          </div>
          <p className="text-xl font-bold text-slate-900">
            {latest_telemetry.pressure ? `${latest_telemetry.pressure} hPa` : 'N/A'}
          </p>
          <span className="text-xs text-slate-500 mt-1">Trend: {latest_telemetry.pressure_trend ? latest_telemetry.pressure_trend.replace('_', ' ').replace(/\w/g, l => l.toUpperCase()) : '---'}</span>
        </div>
        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div className="flex items-center gap-2 mb-2 text-slate-500">
            <Cloud className="w-5 h-5 text-sky-500" />
            <span className="text-sm font-medium">Weather Pred.</span>
          </div>
          <p className="text-xl font-bold text-slate-900 truncate">
            {latest_telemetry.weather_prediction || 'N/A'}
          </p>
        </div>

        <div className={`p-4 rounded-xl border shadow-sm flex flex-col justify-between ${latest_telemetry.rain_detected ? 'bg-blue-50 border-blue-200' : 'bg-white border-slate-200'}`}>
          <div className="flex items-center gap-2 mb-2 text-slate-500">
            <CloudRain className="w-5 h-5 text-blue-500" />
            <span className="text-sm font-medium">Rain Detection</span>
          </div>
          <p className={`text-xl font-bold ${latest_telemetry.rain_detected ? 'text-blue-700' : 'text-slate-900'}`}>
            {latest_telemetry.rain_detected === null ? 'N/A' : (latest_telemetry.rain_detected ? 'Raining' : 'Clear')}
          </p>
        </div>

        <div className={`p-4 rounded-xl border shadow-sm flex flex-col justify-between ${latest_telemetry.pump_status ? 'bg-emerald-50 border-emerald-200' : 'bg-white border-slate-200'}`}>
          <div className="flex items-center gap-2 mb-2 text-slate-500">
            <Power className="w-5 h-5 text-emerald-500" />
            <span className="text-sm font-medium">Pump Status</span>
          </div>
          <p className={`text-xl font-bold ${latest_telemetry.pump_status ? 'text-emerald-700' : 'text-slate-900'}`}>
            {latest_telemetry.pump_status === null ? 'N/A' : (latest_telemetry.pump_status ? 'ON' : 'OFF')}
          </p>
        </div>

        <div className={`p-4 rounded-xl border shadow-sm flex flex-col justify-between ${latest_telemetry.obstacle_detected ? 'bg-red-50 border-red-200' : 'bg-white border-slate-200'}`}>
          <div className="flex items-center gap-2 mb-2 text-slate-500">
            <AlertTriangle className={`w-5 h-5 ${latest_telemetry.obstacle_detected ? 'text-red-500' : 'text-slate-500'}`} />
            <span className="text-sm font-medium">Obstacle Detect</span>
          </div>
          <p className={`text-xl font-bold ${latest_telemetry.obstacle_detected ? 'text-red-700' : 'text-slate-900'}`}>
            {latest_telemetry.obstacle_detected === null ? 'N/A' : (latest_telemetry.obstacle_detected ? 'DETECTED' : 'CLEAR')}
          </p>
        </div>

      </div>

      <h2 className="text-xl font-bold text-slate-800 mt-8 mb-4 border-b pb-2">Device Health & Alerts</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

        {/* Device Health / Status */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Settings className="w-5 h-5 text-slate-500" /> System Metrics
            </h3>
            {device_info.connection_status === 'ONLINE' ? (
              <span className="flex items-center gap-1 text-emerald-600 bg-emerald-50 px-2 py-1 rounded text-xs font-bold uppercase">
                <CheckCircle className="w-3.5 h-3.5" /> Healthy
              </span>
            ) : (
              <span className="flex items-center gap-1 text-amber-600 bg-amber-50 px-2 py-1 rounded text-xs font-bold uppercase">
                <AlertTriangle className="w-3.5 h-3.5" /> Needs Attention
              </span>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4 mt-2">
            <div>
              <p className="text-xs text-slate-500 mb-1 flex items-center gap-1"><Settings className="w-3 h-3" /> Irrigation Mode</p>
              <p className="font-semibold text-slate-800">{latest_telemetry.operation_mode || 'MANUAL'}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500 mb-1 flex items-center gap-1"><Wifi className="w-3 h-3" /> WiFi Signal</p>
              <p className="font-semibold text-slate-800">{latest_telemetry.signal_quality || 'N/A'} ({device_info.rssi ? `${device_info.rssi}dBm` : 'N/A'})</p>
            </div>
            <div>
              <p className="text-xs text-slate-500 mb-1 flex items-center gap-1"><Server className="w-3 h-3" /> Firmware Ver.</p>
              <p className="font-semibold text-slate-800">{latest_telemetry.firmware_version || 'N/A'}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500 mb-1 flex items-center gap-1"><Clock className="w-3 h-3" /> Device Uptime</p>
              <p className="font-semibold text-slate-800">{formatUptime(latest_telemetry.uptime_seconds)}</p>
            </div>
          </div>
        </div>

        {/* Recent Alerts */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
          <h3 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
            <Bell className="w-5 h-5 text-amber-500" /> Recent Alerts
          </h3>

          {recent_alerts.length === 0 ? (
            <div className="h-24 flex flex-col items-center justify-center text-slate-500 bg-emerald-50 rounded-xl border border-emerald-100">
              <CheckCircle className="w-6 h-6 text-emerald-400 mb-1" />
              <p className="text-sm font-medium text-emerald-700">No active alerts</p>
            </div>
          ) : (
            <div className="space-y-3 max-h-48 overflow-y-auto pr-2">
              {recent_alerts.map(a => (
                <div key={a.id} className="flex justify-between items-center p-3 rounded-lg border border-slate-100 bg-slate-50">
                  <div>
                    <p className="font-medium text-slate-900 text-sm">{a.title}</p>
                    <p className="text-xs text-slate-500">{dayjs(a.generated_time).fromNow()}</p>
                  </div>
                  <span className={`px-2 py-1 rounded-md text-xs font-medium ${a.severity === 'CRITICAL' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'
                    }`}>
                    {a.severity}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Historical Charts */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div className="flex flex-col sm:flex-row justify-between sm:items-center mb-6 gap-4">
          <h3 className="text-lg font-bold text-slate-900">Historical Trends</h3>
          <select
            className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-700 outline-none focus:border-brand font-medium"
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
          >
            <option value="Last 24 Hours">Last 24 Hours</option>
            <option value="Last 7 Days">Last 7 Days</option>
            <option value="Last 30 Days">Last 30 Days</option>
          </select>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div>
            <h4 className="font-medium text-slate-700 border-b pb-2">Soil Moisture (%)</h4>
            {renderChart(getChart('soil_moisture'), 'Soil Moisture', '#10b981')}
          </div>
          <div>
            <h4 className="font-medium text-slate-700 border-b pb-2">Ambient Temperature (°C)</h4>
            {renderChart(getChart('temperature'), 'Temperature', '#f59e0b')}
          </div>
          <div>
            <h4 className="font-medium text-slate-700 border-b pb-2">Humidity (%)</h4>
            {renderChart(getChart('humidity'), 'Humidity', '#06b6d4')}
          </div>
          <div>
            <h4 className="font-medium text-slate-700 border-b pb-2">Atmospheric Temp (°C)</h4>
            {renderChart(getChart('bmp_temperature'), 'BMP Temperature', '#ef4444')}
          </div>
          <div>
            <h4 className="font-medium text-slate-700 border-b pb-2">Pressure (hPa)</h4>
            {renderChart(getChart('pressure'), 'Pressure', '#14b8a6')}
          </div>
          <div>
            <h4 className="font-medium text-slate-700 border-b pb-2">Altitude (m)</h4>
            {renderChart(getChart('altitude'), 'Altitude', '#8b5cf6')}
          </div>
          <div>
            <h4 className="font-medium text-slate-700 border-b pb-2">WiFi Signal (RSSI)</h4>
            {renderChart(getChart('rssi'), 'RSSI', '#64748b')}
          </div>
          {getChart('obstacle_detected') && getChart('obstacle_detected').data.length > 0 && (
            <div>
              <h4 className="font-medium text-slate-700 border-b pb-2">Obstacle Detected (1=Yes, 0=No)</h4>
              {renderChart(getChart('obstacle_detected'), 'Obstacle Detected', '#ef4444')}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MonitoringDeviceDetail;
