import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import apiClient from '../../api/client';
import { 
  Cpu, Wifi, WifiOff, Map, Bell, Package, Activity, 
  Plus, Monitor, LifeBuoy, ArrowRight, ShieldAlert,
  CheckCircle2, AlertTriangle, Info, Clock, Thermometer, Droplets, CloudRain, Sun, Moon
} from 'lucide-react';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import DeviceModeControl from '../../components/DeviceModeControl';
import FieldWeatherCard from '../../components/weather/FieldWeatherCard';
import TerravynDecisionCard from '../../components/decision/TerravynDecisionCard';
import GreenGramKnowledgeCard from '../../components/knowledge/GreenGramKnowledgeCard';

dayjs.extend(relativeTime);

const FarmerDashboard = () => {
  const { user } = useAuth();
  
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState(null);
  const [devices, setDevices] = useState([]);
  const [farms, setFarms] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [activities, setActivities] = useState([]);
  const [latestTelemetry, setLatestTelemetry] = useState([]);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [
          summaryRes, devicesRes, farmsRes, alertsRes, activitiesRes, telemetryRes
        ] = await Promise.all([
          apiClient.get('/farmer/dashboard/summary'),
          apiClient.get('/farmer/dashboard/devices'),
          apiClient.get('/farmer/dashboard/farms'),
          apiClient.get('/farmer/dashboard/alerts'),
          apiClient.get('/farmer/dashboard/activities'),
          apiClient.get('/farmer/monitoring/latest')
        ]);
        
        setSummary(summaryRes.data);
        setDevices(devicesRes.data);
        setFarms(farmsRes.data);
        setAlerts(alertsRes.data);
        setActivities(activitiesRes.data);
        setLatestTelemetry(telemetryRes.data);
      } catch (err) {
        console.error("Failed to fetch dashboard data:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchDashboardData();

    const interval = setInterval(async () => {
      try {
        const res = await apiClient.get('/farmer/monitoring/latest');
        setLatestTelemetry(res.data);
      } catch (err) {
        console.error("Failed to refresh telemetry:", err);
      }
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good Morning';
    if (hour < 18) return 'Good Afternoon';
    return 'Good Evening';
  };

  const getAlertIcon = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical': return <ShieldAlert className="text-red-500 w-5 h-5" />;
      case 'warning': return <AlertTriangle className="text-yellow-500 w-5 h-5" />;
      default: return <Info className="text-blue-500 w-5 h-5" />;
    }
  };

  const getActivityIcon = (type) => {
    switch(type) {
      case 'device': return <Cpu className="w-4 h-4 text-brand" />;
      case 'farm': return <Map className="w-4 h-4 text-emerald-500" />;
      case 'order': return <Package className="w-4 h-4 text-blue-500" />;
      case 'support': return <LifeBuoy className="w-4 h-4 text-purple-500" />;
      default: return <Activity className="w-4 h-4 text-slate-500" />;
    }
  };

  if (loading) {
    return (
      <div className="p-4 md:p-8 space-y-6">
        <div className="h-16 w-1/3 bg-slate-200 dark:bg-slate-800 rounded-xl animate-pulse"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-32 bg-slate-200 dark:bg-slate-800 rounded-2xl animate-pulse"></div>
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 h-64 bg-slate-200 dark:bg-slate-800 rounded-2xl animate-pulse"></div>
          <div className="h-64 bg-slate-200 dark:bg-slate-800 rounded-2xl animate-pulse"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 md:p-8 space-y-8 max-w-7xl mx-auto">
      
      {/* Header Section */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            {getGreeting()}, {user?.first_name || user?.username} <span className="animate-wave">👋</span>
          </h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            Welcome back to TERRAVYN. Here's what's happening on your farms today.
          </p>
        </div>
        <div className="flex gap-2">
          <Link to="/farmer/activate-device" className="bg-brand hover:bg-brand-dark text-white px-4 py-2 rounded-xl text-sm font-medium transition-colors flex items-center gap-2">
            <Plus size={16} /> Activate Device
          </Link>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <StatCard icon={<Cpu />} label="Total Devices" value={summary?.total_devices || 0} color="bg-blue-50 text-blue-600 border-blue-100" />
        <StatCard icon={<Wifi />} label="Online Devices" value={summary?.online_devices || 0} color="bg-emerald-50 text-emerald-600 border-emerald-100" />
        <StatCard icon={<WifiOff />} label="Offline Devices" value={summary?.offline_devices || 0} color="bg-red-50 text-red-600 border-red-100" />
        <StatCard icon={<Map />} label="Total Farms" value={summary?.total_farms || 0} color="bg-emerald-50 text-emerald-600 border-emerald-100" />
        <StatCard icon={<Bell />} label="Active Alerts" value={summary?.active_alerts || 0} color="bg-yellow-50 text-yellow-600 border-yellow-100" />
        <StatCard icon={<Package />} label="Pending Orders" value={summary?.pending_orders || 0} color="bg-purple-50 text-purple-600 border-purple-100" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Devices & Farms */}
        <div className="lg:col-span-2 space-y-6">
          {/* Terravyn Green Gram Decision Engine Card */}
          <TerravynDecisionCard farms={farms} />

          {/* Green Gram Crop Profile & Agronomic Knowledge Card */}
          {farms && farms.length > 0 && (
            <GreenGramKnowledgeCard farmId={farms[0]?.id} farmName={farms[0]?.name} />
          )}

          {/* Field Weather & Evapotranspiration Card */}
          <FieldWeatherCard farms={farms} />
          
          {/* In-Situ Sensor Telemetry */}
          {latestTelemetry.length > 0 && (
            <div className="space-y-4 mb-6">
              <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm flex items-center justify-between">
                <div>
                  <p className="text-slate-500 dark:text-slate-400 text-sm font-medium mb-1">Weather Intelligence</p>
                  <div className="flex items-end gap-3 mb-1">
                    <span className="text-xl font-bold text-slate-800 dark:text-slate-100">
                      {latestTelemetry[0]?.weather_prediction || 'Gathering data...'}
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-4 text-sm text-slate-500 dark:text-slate-400">
                    <span>Pressure: {latestTelemetry[0]?.pressure != null ? `${latestTelemetry[0].pressure} hPa` : 'N/A'}</span>
                    <span>•</span>
                    <span>Trend: {latestTelemetry[0]?.pressure_trend ? latestTelemetry[0].pressure_trend.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) : '---'}</span>
                  </div>
                </div>
                <CloudRain className="w-12 h-12 text-brand opacity-20" />
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3.5">
                <MiniStatCard 
                  icon={<Droplets className="w-5 h-5" />} 
                  label="Soil Moisture" 
                  value={latestTelemetry[0]?.soil_moisture != null ? `${latestTelemetry[0].soil_moisture}%` : 'N/A'} 
                  color="bg-emerald-50 text-emerald-600 border-emerald-100" 
                />
                <MiniStatCard 
                  icon={<Thermometer className="w-5 h-5" />} 
                  label="Air Temp" 
                  value={latestTelemetry[0]?.temperature != null ? `${latestTelemetry[0].temperature}°C` : 'N/A'} 
                  color="bg-orange-50 text-orange-600 border-orange-100" 
                />
                <MiniStatCard 
                  icon={<Droplets className="w-5 h-5" />} 
                  label="Humidity" 
                  value={latestTelemetry[0]?.humidity != null ? `${latestTelemetry[0].humidity}%` : 'N/A'} 
                  color="bg-cyan-50 text-cyan-600 border-cyan-100" 
                />
                <MiniStatCard 
                  icon={<CloudRain className="w-5 h-5" />} 
                  label="Rain" 
                  value={latestTelemetry[0]?.rain_detected ? 'Yes' : 'No'} 
                  color={latestTelemetry[0]?.rain_detected ? 'bg-blue-50 text-blue-600 border-blue-100' : 'bg-emerald-50 text-emerald-600 border-emerald-100'} 
                />
                <MiniStatCard 
                  icon={latestTelemetry[0]?.light_status === 'NIGHT' ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />} 
                  label="Light" 
                  value={latestTelemetry[0]?.light_status === 'DAY' ? 'Day' : latestTelemetry[0]?.light_status === 'NIGHT' ? 'Night' : 'N/A'} 
                  color={latestTelemetry[0]?.light_status === 'NIGHT' ? 'bg-indigo-50 text-indigo-600 border-indigo-100' : 'bg-amber-50 text-amber-600 border-amber-100'} 
                />
                <MiniStatCard 
                  icon={<ShieldAlert className="w-5 h-5" />} 
                  label="Obstacle" 
                  value={latestTelemetry[0]?.obstacle_detected ? 'Detected' : 'Clear'} 
                  color={latestTelemetry[0]?.obstacle_detected ? 'bg-red-50 text-red-600 border-red-100' : 'bg-emerald-50 text-emerald-600 border-emerald-100'} 
                />
              </div>
            </div>
          )}

          {/* Device Overview Widget */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
                <Cpu className="text-brand w-5 h-5" /> My Devices
              </h2>
              <Link to="/farmer/devices" className="text-sm font-medium text-brand hover:text-brand-dark flex items-center gap-1">
                View All <ArrowRight size={16} />
              </Link>
            </div>
            
            {devices.length === 0 ? (
              <div className="text-center py-8">
                <div className="mx-auto w-16 h-16 bg-slate-50 dark:bg-slate-800 rounded-full flex items-center justify-center mb-4 text-slate-400">
                  <Cpu size={24} />
                </div>
                <h3 className="text-slate-700 dark:text-slate-300 font-medium mb-1">No devices activated yet.</h3>
                <p className="text-sm text-slate-500 mb-4">Activate your first TERRAVYN device to begin monitoring your farm.</p>
                <Link to="/farmer/activate-device" className="inline-block bg-brand text-white px-4 py-2 rounded-lg text-sm font-medium">
                  Activate Device
                </Link>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-slate-50 dark:bg-slate-800/50 text-slate-500 dark:text-slate-400">
                    <tr>
                      <th className="px-4 py-3 rounded-tl-lg font-medium">Device Name</th>
                      <th className="px-4 py-3 font-medium">UID</th>
                      <th className="px-4 py-3 font-medium">Farm</th>
                      <th className="px-4 py-3 font-medium">Status</th>
                      <th className="px-4 py-3 font-medium">Mode</th>
                      <th className="px-4 py-3 rounded-tr-lg font-medium">Last Seen</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800/50">
                    {devices.map((device) => (
                      <tr key={device.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition-colors">
                        <td className="px-4 py-4 font-medium text-slate-800 dark:text-slate-200">{device.device_name || 'Unnamed Device'}</td>
                        <td className="px-4 py-4 text-slate-500 font-mono text-xs">{device.device_uid}</td>
                        <td className="px-4 py-4 text-slate-500">{device.farm_name}</td>
                        <td className="px-4 py-4">
                          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
                            device.connection_status?.toUpperCase() === 'ONLINE' ? 'bg-emerald-50 text-emerald-700 border-emerald-100' :
                            device.connection_status?.toUpperCase() === 'OFFLINE' ? 'bg-red-50 text-red-700 border-red-100' :
                            'bg-yellow-50 text-yellow-700 border-yellow-100'
                          }`}>
                            <span className={`w-1.5 h-1.5 rounded-full ${
                              device.connection_status?.toUpperCase() === 'ONLINE' ? 'bg-emerald-500' :
                              device.connection_status?.toUpperCase() === 'OFFLINE' ? 'bg-red-500' : 'bg-yellow-500'
                            }`}></span>
                            <span className="capitalize">{device.connection_status?.toLowerCase() || 'Unknown'}</span>
                          </span>
                        </td>
                        <td className="px-4 py-4">
                          <DeviceModeControl 
                            device={device} 
                            compact={true} 
                            onModeChange={(updated) => {
                              setDevices(devices.map(d => d.id === updated.id ? { ...d, irrigation_mode: updated.irrigation_mode, last_mode_change: updated.last_mode_change } : d));
                            }} 
                          />
                        </td>
                        <td className="px-4 py-4 text-slate-500">
                          {device.last_seen ? dayjs(device.last_seen).fromNow() : 'Never'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Farm Overview Widget */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
                <Map className="text-brand w-5 h-5" /> My Farms
              </h2>
              <Link to="/farmer/farms" className="text-sm font-medium text-brand hover:text-brand-dark flex items-center gap-1">
                View All <ArrowRight size={16} />
              </Link>
            </div>

            {farms.length === 0 ? (
              <div className="text-center py-8">
                <div className="mx-auto w-16 h-16 bg-slate-50 dark:bg-slate-800 rounded-full flex items-center justify-center mb-4 text-slate-400">
                  <Map size={24} />
                </div>
                <h3 className="text-slate-700 dark:text-slate-300 font-medium mb-1">No farms added yet.</h3>
                <p className="text-sm text-slate-500 mb-4">Create your first farm to organize your devices.</p>
                <Link to="/farmer/farms/new" className="inline-block bg-brand text-white px-4 py-2 rounded-lg text-sm font-medium">
                  Add Farm
                </Link>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {farms.map((farm) => (
                  <div key={farm.id} className="border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30 p-4 rounded-xl h-full flex flex-col justify-between">
                    <div>
                      <h3 className="font-bold text-slate-800 dark:text-slate-200 mb-2 truncate">{farm.name}</h3>
                      <div className="space-y-1 text-sm text-slate-500 dark:text-slate-400">
                        <p>Crop: <span className="font-medium text-slate-700 dark:text-slate-300">{farm.crop_type}</span></p>
                        <p>Area: <span className="font-medium text-slate-700 dark:text-slate-300">{farm.area} acres</span></p>
                        <p>Devices: <span className="font-medium text-slate-700 dark:text-slate-300">{farm.number_of_devices}</span></p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
          
        </div>

        {/* Right Column: Alerts & Activity & Quick Actions */}
        <div className="space-y-6">
          
          {/* Quick Actions */}
          <div className="bg-gradient-to-br from-brand/10 to-brand/5 dark:from-brand/20 dark:to-transparent rounded-2xl border border-brand/20 p-6 shadow-sm">
            <h2 className="text-lg font-bold text-brand-dark dark:text-brand-light mb-4 flex items-center gap-2">
              ⚡ Quick Actions
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 gap-2">
              <QuickActionLink to="/farmer/activate-device" icon={<Plus size={18} />} label="Activate New Device" />
              <QuickActionLink to="/farmer/devices" icon={<Cpu size={18} />} label="View My Devices" />
              <QuickActionLink to="/farmer/farms/new" icon={<Map size={18} />} label="Add New Farm" />
              <QuickActionLink to="/farmer/monitoring" icon={<Monitor size={18} />} label="Monitoring Center" />
              <QuickActionLink to="/farmer/support" icon={<LifeBuoy size={18} />} label="Support Center" />
            </div>
          </div>

          {/* Recent Alerts Widget */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
                <Bell className="text-brand w-5 h-5" /> Recent Alerts
              </h2>
              <Link to="/farmer/alerts" className="text-sm font-medium text-brand hover:text-brand-dark">
                View All
              </Link>
            </div>

            {alerts.length === 0 ? (
              <div className="text-center py-6 text-slate-500">
                <CheckCircle2 className="w-10 h-10 mx-auto text-emerald-400 mb-2" />
                <p className="font-medium text-slate-700 dark:text-slate-300">You're all caught up.</p>
                <p className="text-sm">No active alerts at the moment.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {alerts.map((alert) => (
                  <div key={alert.id} className="flex gap-3 items-start p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-700/50">
                    <div className="mt-0.5">{getAlertIcon(alert.severity)}</div>
                    <div>
                      <h4 className="font-medium text-sm text-slate-800 dark:text-slate-200">{alert.title}</h4>
                      <p className="text-xs text-slate-500 mt-0.5">{alert.device_name}</p>
                      <p className="text-[10px] text-slate-400 flex items-center gap-1 mt-1">
                        <Clock size={10} /> {dayjs(alert.generated_time).fromNow()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Recent Activity Timeline */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm">
            <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 mb-6 flex items-center gap-2">
              <Activity className="text-brand w-5 h-5" /> Recent Activity
            </h2>

            {activities.length === 0 ? (
              <p className="text-sm text-slate-500 text-center py-4">No recent activities found.</p>
            ) : (
              <div className="relative border-l border-slate-200 dark:border-slate-800 ml-3 space-y-6 pb-2">
                {activities.map((activity, idx) => (
                  <div key={idx} className="relative pl-6">
                    <span className="absolute -left-3 top-0.5 flex items-center justify-center w-6 h-6 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-full shadow-sm">
                      {getActivityIcon(activity.type)}
                    </span>
                    <p className="text-sm font-medium text-slate-700 dark:text-slate-300">{activity.description}</p>
                    <time className="block text-xs text-slate-400 mt-1">{dayjs(activity.timestamp).format('MMM D, YYYY h:mm A')}</time>
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

// Helper Components
const StatCard = ({ icon, label, value, color }) => (
  <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm flex items-center gap-4 h-full">
    <div className={`w-12 h-12 rounded-xl flex items-center justify-center border ${color}`}>
      {icon}
    </div>
    <div>
      <p className="text-sm font-medium text-slate-500 dark:text-slate-400">{label}</p>
      <p className="text-2xl font-bold text-slate-900 dark:text-white">{value}</p>
    </div>
  </div>
);

const MiniStatCard = ({ icon, label, value, color }) => (
  <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-3 shadow-sm flex flex-col items-center justify-center text-center gap-1 h-full">
    <div className={`w-10 h-10 rounded-lg flex items-center justify-center border ${color}`}>
      {icon}
    </div>
    <div>
      <p className="text-xs font-medium text-slate-500 dark:text-slate-400">{label}</p>
      <p className="text-lg font-bold text-slate-900 dark:text-white">{value}</p>
    </div>
  </div>
);

const QuickActionLink = ({ to, icon, label }) => (
  <Link 
    to={to} 
    className="flex items-center gap-3 p-3 rounded-xl bg-white/60 dark:bg-slate-900/60 hover:bg-white dark:hover:bg-slate-900 border border-transparent hover:border-brand/20 transition-all text-slate-700 dark:text-slate-200 font-medium text-sm"
  >
    <div className="text-brand">{icon}</div>
    {label}
  </Link>
);

export default FarmerDashboard;
