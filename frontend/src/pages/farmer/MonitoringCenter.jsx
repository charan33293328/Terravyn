import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Activity, Server, Droplets, Thermometer, CloudRain, Search, AlertCircle, RefreshCw, Sun, Moon, CheckCircle, XCircle } from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import apiClient from '../../api/client';
import dayjs from 'dayjs';
import DeviceModeControl from '../../components/DeviceModeControl';

const MonitoringCenter = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [farms, setFarms] = useState([]);
  const [devices, setDevices] = useState([]);

  const [selectedFarm, setSelectedFarm] = useState('');
  const [selectedDevice, setSelectedDevice] = useState('');
  const [timeRange, setTimeRange] = useState('Last 24 Hours');

  const [summary, setSummary] = useState(null);
  const [latestData, setLatestData] = useState([]);
  const [chartData, setChartData] = useState([]);
  const [historyData, setHistoryData] = useState([]);
  const [historyPage, setHistoryPage] = useState(1);
  const [historyPages, setHistoryPages] = useState(1);

  const fetchFarmsAndDevices = async () => {
    try {
      const farmsRes = await apiClient.get('/farmer/farms');
      setFarms(farmsRes.data);
      const devicesRes = await apiClient.get('/farmer/devices');
      const devs = Array.isArray(devicesRes.data) ? devicesRes.data : (devicesRes.data.devices || []);
      setDevices(devs);
    } catch (err) {
      console.error('Failed to load filters', err);
    }
  };

  const fetchMonitoringData = async (isRefresh = false) => {
    try {
      if (!isRefresh) setLoading(true);
      else setRefreshing(true);

      const params = {};
      if (selectedFarm) params.farm_id = selectedFarm;
      if (selectedDevice) params.device_id = selectedDevice;

      const summaryRes = await apiClient.get('/farmer/monitoring/summary', { params });
      setSummary(summaryRes.data);

      const latestRes = await apiClient.get('/farmer/monitoring/latest', { params });
      setLatestData(latestRes.data);

      const chartsRes = await apiClient.get('/farmer/monitoring/charts', {
        params: { ...params, time_range: timeRange }
      });

      // format chart data for recharts
      // we need to pivot data so that recharts can plot multiple lines if needed
      // Actually, if we have just global averages per timestamp, that's fine.
      // But we have metrics.
      const formattedCharts = chartsRes.data;
      setChartData(formattedCharts);

      const historyRes = await apiClient.get('/farmer/monitoring/history', {
        params: { ...params, time_range: timeRange, page: historyPage }
      });
      setHistoryData(historyRes.data.items);
      setHistoryPages(historyRes.data.pages);

    } catch (err) {
      console.error('Failed to load monitoring data', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchFarmsAndDevices();
  }, []);

  useEffect(() => {
    fetchMonitoringData();
    const interval = setInterval(() => {
      fetchMonitoringData(true);
    }, 10000); // 10s polling
    return () => clearInterval(interval);
  }, [selectedFarm, selectedDevice, timeRange, historyPage]);

  // Derived filtered devices based on selected farm
  const filteredDevices = selectedFarm
    ? devices.filter(d => d.farm_id === parseInt(selectedFarm))
    : devices;

  // Chart Rendering Helper
  const renderChart = (metricData, label, color, lineType = "monotone") => {
    if (!metricData || metricData.data.length === 0) return (
      <div className="h-64 flex items-center justify-center bg-slate-50 rounded-xl border border-slate-100 text-slate-400">
        No data for {label}
      </div>
    );

    return (
      <div className="h-64">
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
              type={lineType}
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

  const soilChart = chartData.find(c => c.metric === 'soil_moisture');
  const tempChart = chartData.find(c => c.metric === 'temperature');
  const rainChart = chartData.find(c => c.metric === 'rain_detected');
  const lightChart = chartData.find(c => c.metric === 'dark_detected');
  const obstacleChart = chartData.find(c => c.metric === 'obstacle_detected');

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Activity className="w-6 h-6 text-brand" /> Monitoring Center
          </h1>
          <p className="text-slate-500 mt-1">Monitor your farms and devices in real time</p>
        </div>
        <button
          onClick={() => fetchMonitoringData(true)}
          className="p-2 text-slate-400 hover:text-brand hover:bg-brand/5 rounded-lg transition-colors flex items-center gap-2"
        >
          <RefreshCw className={`w-5 h-5 ${refreshing ? 'animate-spin text-brand' : ''}`} />
          <span className="text-sm font-medium">Refresh</span>
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-wrap gap-4">
        <select
          className="px-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-700 outline-none focus:border-brand focus:ring-1 focus:ring-brand min-w-[200px]"
          value={selectedFarm}
          onChange={(e) => {
            setSelectedFarm(e.target.value);
            setSelectedDevice('');
            setHistoryPage(1);
          }}
        >
          <option value="">All Farms</option>
          {farms.map(f => <option key={f.id} value={f.id}>{f.name}</option>)}
        </select>

        <select
          className="px-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-700 outline-none focus:border-brand focus:ring-1 focus:ring-brand min-w-[200px]"
          value={selectedDevice}
          onChange={(e) => {
            setSelectedDevice(e.target.value);
            setHistoryPage(1);
          }}
        >
          <option value="">All Devices</option>
          {filteredDevices.map(d => <option key={d.id} value={d.id}>{d.name || d.device_uid}</option>)}
        </select>

        <select
          className="px-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-700 outline-none focus:border-brand focus:ring-1 focus:ring-brand min-w-[200px]"
          value={timeRange}
          onChange={(e) => {
            setTimeRange(e.target.value);
            setHistoryPage(1);
          }}
        >
          <option value="Last 1 Hour">Last 1 Hour</option>
          <option value="Last 6 Hours">Last 6 Hours</option>
          <option value="Last 24 Hours">Last 24 Hours</option>
          <option value="Last 7 Days">Last 7 Days</option>
          <option value="Last 30 Days">Last 30 Days</option>
        </select>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand"></div>
        </div>
      ) : (
        <>
          {/* Summary Cards */}
          {summary && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
              <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between hover:shadow-md transition-shadow">
                <div className="min-w-0 flex-1 mr-4">
                  <p className="text-sm text-slate-500 font-medium">Monitored Devices</p>
                  <p className="text-3xl font-bold text-slate-900 mt-2">
                    {summary.online_devices} <span className="text-sm font-normal text-slate-400">/ {summary.total_devices}</span>
                  </p>
                </div>
                <div className="w-12 h-12 bg-blue-50 text-blue-600 rounded-xl flex items-center justify-center shrink-0">
                  <Server className="w-6 h-6" />
                </div>
              </div>

              <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between hover:shadow-md transition-shadow">
                <div className="min-w-0 flex-1 mr-4">
                  <p className="text-sm text-slate-500 font-medium">Avg Soil Moisture</p>
                  <p className="text-3xl font-bold text-slate-900 mt-2">
                    {summary.avg_soil_moisture !== null ? `${summary.avg_soil_moisture}%` : 'N/A'}
                  </p>
                </div>
                <div className="w-12 h-12 bg-emerald-50 text-emerald-600 rounded-xl flex items-center justify-center shrink-0">
                  <Droplets className="w-6 h-6" />
                </div>
              </div>

              <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between hover:shadow-md transition-shadow">
                <div className="min-w-0 flex-1 mr-4">
                  <p className="text-sm text-slate-500 font-medium">Avg Temperature</p>
                  <p className="text-3xl font-bold text-slate-900 mt-2">
                    {summary.avg_temperature !== null ? `${summary.avg_temperature}°C` : 'N/A'}
                  </p>
                </div>
                <div className="w-12 h-12 bg-amber-50 text-amber-600 rounded-xl flex items-center justify-center shrink-0">
                  <Thermometer className="w-6 h-6" />
                </div>
              </div>

              <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between hover:shadow-md transition-shadow">
                <div className="min-w-0 flex-1 mr-4">
                  <p className="text-sm text-slate-500 font-medium">Active Alerts</p>
                  <p className="text-3xl font-bold text-slate-900 mt-2">{summary.active_alerts}</p>
                </div>
                <div className="w-12 h-12 bg-red-50 text-red-600 rounded-xl flex items-center justify-center shrink-0">
                  <AlertCircle className="w-6 h-6" />
                </div>
              </div>

              <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between hover:shadow-md transition-shadow">
                <div className="min-w-0 flex-1 mr-4">
                  <p className="text-sm text-slate-500 font-medium">Ambient Light</p>
                  <p className="text-3xl font-bold text-slate-900 mt-2 capitalize">
                    {latestData[0]?.light_status === 'DAY' ? 'Day' : latestData[0]?.light_status === 'NIGHT' ? 'Night' : 'N/A'}
                  </p>
                </div>
                <div className="w-12 h-12 bg-indigo-50 text-indigo-600 rounded-xl flex items-center justify-center shrink-0">
                  {latestData[0]?.light_status === 'NIGHT' ? <Moon className="w-6 h-6" /> : <Sun className="w-6 h-6" />}
                </div>
              </div>

              <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between hover:shadow-md transition-shadow">
                <div className="min-w-0 flex-1 mr-4">
                  <p className="text-sm text-slate-500 font-medium">Weather Intel</p>
                  <p className="text-2xl font-bold text-slate-900 mt-2 capitalize truncate" title={latestData[0]?.weather_prediction}>
                    {latestData[0]?.rain_detected ? 'Raining' : latestData[0]?.weather_prediction || 'N/A'}
                  </p>
                </div>
                <div className="w-12 h-12 bg-purple-50 text-purple-600 rounded-xl flex items-center justify-center shrink-0">
                  <CloudRain className="w-6 h-6" />
                </div>
              </div>
            </div>
          )}

          {/* Device Sensor Health Section */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <div className="flex justify-between items-center mb-4">
              <div>
                <h3 className="text-lg font-bold text-slate-900">Device Sensor Health</h3>
                <p className="text-xs text-slate-500">Live operational health of hardware sensors</p>
              </div>
              <span className="text-xs font-semibold px-2.5 py-1 bg-brand/10 text-brand rounded-full">
                Active Sensors
              </span>
            </div>
            {latestData.length > 0 && latestData[0]?.sensor_health ? (
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                {Object.entries(latestData[0].sensor_health)
                  .filter(([sensor]) => !['water', 'ultrasonic'].includes(sensor.toLowerCase()))
                  .map(([sensor, status]) => {
                    const sensorNames = {
                      soil: 'Soil Moisture',
                      dht22: 'DHT22 Temp/RH',
                      bmp280: 'BMP280 Baro',
                      rain: 'Rain Sensor',
                      ldr: 'LDR Light',
                      ir: 'IR Obstacle'
                    };
                    const displayName = sensorNames[sensor.toLowerCase()] || sensor.replace('_', ' ').toUpperCase();
                    return (
                      <div key={sensor} className="flex items-center justify-between p-3.5 rounded-xl border border-slate-100 bg-slate-50/80 hover:bg-slate-50 transition-colors">
                        <span className="text-xs sm:text-sm font-semibold text-slate-700">{displayName}</span>
                        <div className="flex items-center gap-1.5 shrink-0 ml-2">
                          {status === 'OK' ? (
                            <><CheckCircle className="w-4 h-4 text-emerald-500 shrink-0" /><span className="text-xs font-bold text-emerald-600">OK</span></>
                          ) : status === 'FAULT' ? (
                            <><XCircle className="w-4 h-4 text-red-500 shrink-0" /><span className="text-xs font-bold text-red-600">FAULT</span></>
                          ) : (
                            <><div className="w-3.5 h-3.5 rounded-full bg-slate-300 shrink-0" /><span className="text-xs font-bold text-slate-500">N/A</span></>
                          )}
                        </div>
                      </div>
                    );
                  })}
              </div>
            ) : (
              <div className="py-6 flex items-center justify-center text-slate-400 text-sm">
                No health data available.
              </div>
            )}
          </div>

          {/* Historical Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
              <h3 className="text-lg font-bold text-slate-900 mb-6">Soil Moisture Trend</h3>
              {renderChart(soilChart, 'Soil Moisture', '#10b981')}
            </div>
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
              <h3 className="text-lg font-bold text-slate-900 mb-6">Temperature Trend</h3>
              {renderChart(tempChart, 'Temperature', '#f59e0b')}
            </div>
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
              <h3 className="text-lg font-bold text-slate-900 mb-6">Humidity Trend</h3>
              {renderChart(chartData.find(c => c.metric === 'humidity'), 'Humidity', '#06b6d4')}
            </div>
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
              <h3 className="text-lg font-bold text-slate-900 mb-6">Rainfall History</h3>
              {renderChart(rainChart, 'Rain Detected (1=Yes, 0=No)', '#3b82f6', 'step')}
            </div>
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
              <h3 className="text-lg font-bold text-slate-900 mb-6">Ambient Light History</h3>
              {renderChart(lightChart, 'Dark Detected (1=Night, 0=Day)', '#6366f1', 'step')}
            </div>
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
              <h3 className="text-lg font-bold text-slate-900 mb-6">Obstacle Detection History</h3>
              {renderChart(obstacleChart, 'Obstacle Detected (1=Yes, 0=No)', '#ef4444', 'step')}
            </div>
          </div>

          {/* Live Device Telemetry */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="p-6 border-b border-slate-200 flex justify-between items-center">
              <h3 className="text-lg font-bold text-slate-900">Live Device Monitoring</h3>
            </div>

            {latestData.length === 0 ? (
              <div className="p-12 text-center text-slate-500">
                <Server className="w-12 h-12 mx-auto text-slate-300 mb-4" />
                <p className="font-medium text-slate-900">No monitoring data available</p>
                <p className="mt-1">Telemetry will appear once devices begin transmitting.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm text-slate-600">
                  <thead className="bg-slate-50 text-slate-500 font-medium">
                    <tr>
                      <th className="px-6 py-4">Device</th>
                      <th className="px-6 py-4">Farm</th>
                      <th className="px-6 py-4">Moisture</th>
                      <th className="px-6 py-4">Temp</th>
                      <th className="px-6 py-4">Humidity</th>
                      <th className="px-6 py-4">Atmos Temp</th>
                      <th className="px-6 py-4">Pressure</th>
                      <th className="px-6 py-4">Rain</th>
                      <th className="px-6 py-4">Light</th>
                      <th className="px-6 py-4">Obstacle</th>
                      <th className="px-6 py-4">Pump</th>
                      <th className="px-6 py-4">Signal</th>
                      <th className="px-6 py-4">Status</th>
                      <th className="px-6 py-4">Mode</th>
                      <th className="px-6 py-4">Last Update</th>
                      <th className="px-6 py-4"></th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {latestData.map(d => (
                      <tr key={d.device_id} className="hover:bg-slate-50 transition-colors">
                        <td className="px-6 py-4">
                          <div className="font-medium text-slate-900">{d.device_name}</div>
                          <div className="text-xs text-slate-500">{d.device_uid}</div>
                        </td>
                        <td className="px-6 py-4">{d.farm_name || 'Unassigned'}</td>
                        <td className="px-6 py-4 font-medium text-emerald-600">
                          {d.soil_moisture !== null ? `${d.soil_moisture}%` : '-'}
                        </td>
                        <td className="px-6 py-4 font-medium text-amber-600">
                          {d.temperature !== null ? `${d.temperature}°C` : '-'}
                        </td>
                        <td className="px-6 py-4 font-medium text-cyan-600">
                          {d.humidity !== null ? `${d.humidity}%` : '-'}
                        </td>
                        <td className="px-6 py-4 font-medium text-red-600">
                          {d.bmp_temperature !== null ? `${d.bmp_temperature}°C` : '-'}
                        </td>
                        <td className="px-6 py-4 font-medium text-teal-600">
                          {d.pressure !== null ? `${d.pressure} hPa` : '-'}
                        </td>
                        <td className="px-6 py-4 font-medium text-blue-600">
                          {d.rain_detected ? 'Yes' : 'No'}
                        </td>
                        <td className="px-6 py-4 font-medium text-indigo-600 capitalize">
                          {d.light_status ? (d.light_status === 'DAY' ? 'Day ☀' : 'Night 🌙') : '-'}
                        </td>
                        <td className="px-6 py-4 font-medium text-red-600">
                          {d.obstacle_detected ? 'Yes' : 'No'}
                        </td>
                        <td className="px-6 py-4 font-medium text-emerald-600">
                          {d.pump_status ? 'ON' : 'OFF'}
                        </td>
                        <td className="px-6 py-4 font-medium text-slate-600">
                          {d.signal_quality || '-'}
                        </td>
                        <td className="px-6 py-4">
                          <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${d.connection_status?.toUpperCase() === 'ONLINE' ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-600'
                            }`}>
                            <span className="capitalize">{d.connection_status?.toLowerCase() || 'Unknown'}</span>
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <DeviceModeControl
                            device={{ id: d.device_id, irrigation_mode: d.irrigation_mode, last_mode_change: d.last_mode_change }}
                            compact={true}
                            onModeChange={() => fetchMonitoringData(true)}
                          />
                        </td>
                        <td className="px-6 py-4">
                          {d.recorded_at ? dayjs(d.recorded_at).fromNow() : 'Never'}
                        </td>
                        <td className="px-6 py-4 text-right">
                          <button
                            onClick={() => navigate(`/farmer/monitoring/devices/${d.device_id}`)}
                            className="text-brand font-medium hover:text-brand-dark transition-colors"
                          >
                            View Details
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* History Data */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="p-6 border-b border-slate-200 flex justify-between items-center">
              <h3 className="text-lg font-bold text-slate-900">Telemetry History</h3>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-600">
                <thead className="bg-slate-50 text-slate-500 font-medium">
                  <tr>
                    <th className="px-6 py-4">Timestamp</th>
                    <th className="px-6 py-4">Device</th>
                    <th className="px-6 py-4">Moisture</th>
                    <th className="px-6 py-4">Temp</th>
                    <th className="px-6 py-4">Humidity</th>
                    <th className="px-6 py-4">Atmos Temp</th>
                    <th className="px-6 py-4">Pressure</th>
                    <th className="px-6 py-4">Pump</th>
                    <th className="px-6 py-4">Weather Pred</th>
                    <th className="px-6 py-4">Rain</th>
                    <th className="px-6 py-4">Light</th>
                    <th className="px-6 py-4">Obstacle</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {historyData.map((row, idx) => (
                    <tr key={idx} className="hover:bg-slate-50">
                      <td className="px-6 py-4">{dayjs(row.timestamp).format('MMM D, YYYY HH:mm:ss')}</td>
                      <td className="px-6 py-4">{row.device}</td>
                      <td className="px-6 py-4">{row.soil_moisture !== null ? `${row.soil_moisture}%` : '-'}</td>
                      <td className="px-6 py-4">{row.temperature !== null ? `${row.temperature}°C` : '-'}</td>
                      <td className="px-6 py-4">{row.humidity !== null ? `${row.humidity}%` : '-'}</td>
                      <td className="px-6 py-4">{row.bmp_temperature !== null ? `${row.bmp_temperature}°C` : '-'}</td>
                      <td className="px-6 py-4">{row.pressure !== null ? `${row.pressure} hPa` : '-'}</td>
                      <td className="px-6 py-4">{row.pump_status ? 'ON' : 'OFF'}</td>
                      <td className="px-6 py-4">{row.weather_prediction || '-'}</td>
                      <td className="px-6 py-4">{row.rain_detected ? 'Yes' : 'No'}</td>
                      <td className="px-6 py-4 capitalize">{row.light_status || '-'}</td>
                      <td className="px-6 py-4">{row.obstacle_detected ? 'Yes' : 'No'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {historyPages > 1 && (
              <div className="p-4 border-t border-slate-200 flex justify-end gap-2">
                <button
                  disabled={historyPage === 1}
                  onClick={() => setHistoryPage(p => p - 1)}
                  className="px-3 py-1 bg-slate-100 text-slate-600 rounded-lg hover:bg-slate-200 disabled:opacity-50"
                >
                  Prev
                </button>
                <span className="px-3 py-1 text-slate-600 font-medium">
                  Page {historyPage} of {historyPages}
                </span>
                <button
                  disabled={historyPage === historyPages}
                  onClick={() => setHistoryPage(p => p + 1)}
                  className="px-3 py-1 bg-slate-100 text-slate-600 rounded-lg hover:bg-slate-200 disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default MonitoringCenter;
