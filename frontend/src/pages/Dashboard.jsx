import React, { useState, useEffect } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Droplets, Thermometer, Wind, CloudRain, Sun, Activity, Settings2, Wifi, Cpu } from 'lucide-react';
import { useDeviceWebSocket } from '../hooks/useDeviceWebSocket';
import apiClient from '../api/client';

const Dashboard = () => {
  const [devices, setDevices] = useState([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState(null);
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [loadingDevices, setLoadingDevices] = useState(true);

  useEffect(() => {
    const fetchDevices = async (isPolling = false) => {
      if (!isPolling) setLoadingDevices(true);
      try {
        const res = await apiClient.get('/user/devices');
        setDevices(res.data);
        if (res.data.length > 0) {
          // Keep the current selected device, just update its data
          setSelectedDeviceId(prevId => {
            const currentId = prevId || res.data[0].id;
            setSelectedDevice(res.data.find(d => d.id === currentId));
            return currentId;
          });
        }
      } catch (err) {
        console.error("Failed to fetch devices", err);
      } finally {
        if (!isPolling) setLoadingDevices(false);
      }
    };
    
    fetchDevices(false);
    
    const interval = setInterval(() => {
      fetchDevices(true);
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const { sensorData, deviceStatus } = useDeviceWebSocket(selectedDeviceId);
  const [chartData, setChartData] = useState([]);

  useEffect(() => {
    // Fetch historical data on mount if we have a selected device
    const fetchHistory = async () => {
      if (!selectedDeviceId) return;
      try {
        const res = await apiClient.get(`/device/history?device_id=${selectedDeviceId}&days=1`);
        // Format historical data
        const historyData = res.data.map(item => {
          const date = new Date(item.created_at);
          const timeStr = `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
          return { time: timeStr, value: item.soil_moisture };
        });
        
        // Take the last 20 points to fit the chart nicely
        if (historyData.length > 20) {
          setChartData(historyData.slice(historyData.length - 20));
        } else {
          setChartData(historyData);
        }
      } catch (err) {
        console.error("Failed to fetch history", err);
      }
    };
    fetchHistory();
  }, [selectedDeviceId]);

  useEffect(() => {
    if (sensorData) {
      // Append new live data to chart history, keep last 20 points
      const now = new Date();
      const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
      
      setChartData(prev => {
        const newData = [...prev, { time: timeStr, value: sensorData.soil_moisture }];
        if (newData.length > 20) return newData.slice(newData.length - 20);
        return newData;
      });
    }
  }, [sensorData]);

  if (loadingDevices) {
    return <div className="p-6 text-slate-500">Loading Dashboard...</div>;
  }

  if (devices.length === 0) {
    return (
      <div className="p-12 text-center bg-white rounded-xl border border-slate-200 shadow-sm">
        <h3 className="text-xl font-bold text-slate-800 mb-2">No devices activated yet.</h3>
        <p className="text-slate-500 mb-6">Activate your TERRAVYN device to begin monitoring your farm.</p>
        <button 
          onClick={() => window.location.href = '/farmer/activate-device'}
          className="px-6 py-2 bg-brand text-white rounded-lg hover:bg-brand/90 transition inline-flex items-center gap-2"
        >
          <Activity className="w-5 h-5" />
          Activate Device
        </button>
      </div>
    );
  }

  if (!sensorData) {
    return (
      <div className="p-12 text-center bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col items-center justify-center min-h-[400px]">
        <Activity className="w-12 h-12 text-slate-300 mb-4" />
        <h3 className="text-xl font-bold text-slate-800 mb-2">No Data Available</h3>
        <p className="text-slate-500">Waiting for {selectedDevice?.name || selectedDevice?.device_uid} to send its first sensor reading.</p>
      </div>
    );
  }

  const currentData = sensorData;
  const derivedStatus = selectedDevice?.connectivity_status === 'ONLINE' ? 'online' : 'offline';
  const statusColor = derivedStatus === 'online' ? 'text-emerald-500' : 'text-red-500';
  const statusBg = derivedStatus === 'online' ? 'bg-emerald-50' : 'bg-red-50';

  const totalDevices = devices.length;
  const onlineDevices = devices.filter(d => d.connectivity_status === 'ONLINE').length;
  const offlineDevices = devices.filter(d => d.connectivity_status === 'OFFLINE' || d.connectivity_status === 'UNKNOWN').length;

  return (
    <div className="space-y-6">
      {/* Fleet Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-sm text-slate-500 font-medium">Total Devices</p>
            <p className="text-2xl font-bold text-slate-800 mt-1">{totalDevices}</p>
          </div>
          <div className="p-3 bg-blue-50 text-blue-600 rounded-lg">
            <Cpu className="w-6 h-6" />
          </div>
        </div>
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-sm text-slate-500 font-medium">Online Devices</p>
            <p className="text-2xl font-bold text-slate-800 mt-1">{onlineDevices}</p>
          </div>
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
            <Wifi className="w-6 h-6" />
          </div>
        </div>
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-sm text-slate-500 font-medium">Offline Devices</p>
            <p className="text-2xl font-bold text-slate-800 mt-1">{offlineDevices}</p>
          </div>
          <div className="p-3 bg-red-50 text-red-600 rounded-lg">
            <Activity className="w-6 h-6 opacity-50" />
          </div>
        </div>
      </div>

      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-3">
            Operational Dashboard
            {derivedStatus === 'online' && (
              <span className="flex h-3 w-3 relative">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
              </span>
            )}
          </h2>
          <p className="text-slate-500">Real-time agricultural intelligence for {selectedDevice?.name || selectedDevice?.device_uid}</p>
        </div>
        
        {devices.length > 1 && (
          <div className="flex gap-3">
            <select 
              value={selectedDeviceId} 
              onChange={(e) => {
                const id = parseInt(e.target.value);
                setSelectedDeviceId(id);
                setSelectedDevice(devices.find(d => d.id === id));
                setChartData([]); // Reset chart on switch
              }}
              className="px-4 py-2 bg-white border border-slate-200 text-slate-700 rounded-lg shadow-sm focus:ring-brand focus:border-brand"
            >
              {devices.map(d => (
                <option key={d.id} value={d.id}>{d.name || d.device_uid}</option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
        <KPICard icon={Droplets} label="Soil Moisture" value={`${currentData.soil_moisture?.toFixed(1) || 0}%`} status={currentData.soil_moisture > 40 ? "optimal" : "low"} />
        <KPICard icon={Thermometer} label="Temperature" value={`${currentData.temperature?.toFixed(1) || 0}°C`} status="optimal" />
        <KPICard icon={Wind} label="Humidity" value={`${currentData.humidity?.toFixed(1) || 0}%`} status="normal" />
        <KPICard icon={CloudRain} label="Rain Status" value={currentData.rain_status ? "Raining" : "Clear"} />
        <KPICard icon={Sun} label="Light" value={`${Math.round(currentData.light_intensity || 0)} lux`} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Soil Moisture Chart */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex justify-between items-center mb-6">
            <h3 className="font-semibold text-slate-800">Live Soil Moisture</h3>
            <span className="text-xs font-medium bg-brand/10 text-brand px-2 py-1 rounded">Live Stream</span>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorMoistureLive" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0A7D40" stopOpacity={0.2}/>
                    <stop offset="95%" stopColor="#0A7D40" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="time" axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 12}} />
                <YAxis domain={[0, 100]} axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 12}} />
                <Tooltip isAnimationActive={false} />
                <Area isAnimationActive={false} type="monotone" dataKey="value" stroke="#0A7D40" strokeWidth={3} fillOpacity={1} fill="url(#colorMoistureLive)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Operational Parameters & Identity */}
        <div className="flex flex-col gap-6">
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex-1">
            <h3 className="font-semibold text-slate-800 mb-4">Operational Parameters</h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <ParameterCard icon={Activity} label="Pump Status" value={currentData.pump_status ? "Active" : "Idle"} statusColor={currentData.pump_status ? "text-green-500" : "text-slate-500"} bg={currentData.pump_status ? "bg-green-50" : "bg-slate-50"} />
              <ParameterCard icon={Settings2} label="Irrigation Mode" value={currentData.mode_status === 'auto' ? "Auto" : "Manual"} statusColor={currentData.mode_status === 'auto' ? "text-blue-500" : "text-orange-500"} bg={currentData.mode_status === 'auto' ? "bg-blue-50" : "bg-orange-50"} />
              <ParameterCard icon={Wifi} label="Connectivity" value={selectedDevice?.connectivity_status || 'UNKNOWN'} statusColor={statusColor} bg={statusBg} />
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <h3 className="font-semibold text-slate-800 mb-4">Hardware Identity</h3>
            <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
              <div>
                <p className="text-sm text-slate-500 mb-1">Device ID</p>
                <p className="font-bold text-slate-800">{selectedDevice?.device_uid} (ID: {selectedDevice?.id})</p>
              </div>
              <div className="text-right">
                <p className="text-sm text-slate-500 mb-1">Firmware</p>
                <p className="font-medium text-slate-700">{selectedDevice?.firmware_version || 'Unknown'}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Helper Components
const KPICard = ({ icon: Icon, label, value, status }) => (
  <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm transition-shadow duration-300 transform hover:scale-[1.02]">
    <div className="flex justify-between items-start mb-2">
      <div className="p-2 bg-brand/10 text-brand rounded-lg">
        <Icon className="w-5 h-5" />
      </div>
      {status && <span className="text-xs font-medium text-slate-500 capitalize">{status}</span>}
    </div>
    <p className="text-sm text-slate-500 font-medium transition-colors">{label}</p>
    <p className="text-2xl font-bold text-slate-800 mt-1 transition-all">{value}</p>
  </div>
);

const ParameterCard = ({ icon: Icon, label, value, statusColor, bg }) => (
  <div className={`p-4 rounded-lg flex items-center gap-4 transition-colors duration-300 ${bg}`}>
    <div className={`p-2 bg-white rounded-lg shadow-sm transition-colors ${statusColor}`}>
      <Icon className="w-5 h-5" />
    </div>
    <div>
      <p className="text-xs text-slate-500 font-medium">{label}</p>
      <p className={`font-bold transition-colors ${statusColor}`}>{value}</p>
    </div>
  </div>
);

export default Dashboard;
