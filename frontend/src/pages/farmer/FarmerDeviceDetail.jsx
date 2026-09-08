import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { 
  ArrowLeft, Edit3, MapPin, Activity, Cpu, Wifi, WifiOff, 
  Droplets, ThermometerSun, AlertTriangle, Clock, RefreshCw, Save, X, Power, CloudRain,
  CheckCircle, ShieldCheck, Copy, Check
} from 'lucide-react';
import apiClient from '../../api/client';
import DeviceModeControl from '../../components/DeviceModeControl';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';

dayjs.extend(relativeTime);

const FarmerDeviceDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [device, setDevice] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Connectivity status: active when device is connected with the website
  const isConnected = device?.connectivity_status === 'ONLINE' || device?.status?.toLowerCase() === 'online';

  // Modals state
  const [showRenameModal, setShowRenameModal] = useState(false);
  const [newName, setNewName] = useState('');
  
  const [showFarmModal, setShowFarmModal] = useState(false);
  const [farms, setFarms] = useState([]);
  const [selectedFarmId, setSelectedFarmId] = useState('');

  // Wi-Fi Provisioning state
  const [showWifiModal, setShowWifiModal] = useState(false);
  const [wifiSetupStep, setWifiSetupStep] = useState('CONFIRM'); // 'CONFIRM', 'IN_PROGRESS', 'SUCCESS'
  const [wifiLoading, setWifiLoading] = useState(false);
  const [wifiApName, setWifiApName] = useState('TERRAVYN-XXXXXX');
  const [copiedAp, setCopiedAp] = useState(false);
  const [wifiElapsedTime, setWifiElapsedTime] = useState(0);

  useEffect(() => {
    if (searchParams.get('action') === 'wifi' && isConnected && !showWifiModal) {
      handleOpenWifiModal();
    }
  }, [searchParams, isConnected]);

  useEffect(() => {
    fetchDeviceDetail();
    fetchFarms();
    
    // Poll telemetry every 10 seconds
    const interval = setInterval(() => {
      fetchDeviceDetail(false);
    }, 10000);
    
    return () => clearInterval(interval);
  }, [id]);

  const fetchDeviceDetail = async (showLoader = true) => {
    if (showLoader) setLoading(true);
    try {
      const res = await apiClient.get(`/farmer/devices/${id}`);
      setDevice(res.data);
      setNewName(res.data.device_name || '');
      setSelectedFarmId(res.data.farm_id || '');
    } catch (err) {
      console.error("Failed to fetch device detail", err);
      setError("Device not found or access denied.");
    } finally {
      if (showLoader) setLoading(false);
    }
  };

  const fetchFarms = async () => {
    try {
      const res = await apiClient.get('/farmer/farms');
      setFarms(res.data);
    } catch (err) {
      console.error("Failed to fetch farms", err);
    }
  };

  const handleRename = async () => {
    if (!newName.trim()) return;
    try {
      await apiClient.put(`/farmer/devices/${id}/rename`, { device_name: newName });
      setShowRenameModal(false);
      fetchDeviceDetail(false);
    } catch (err) {
      alert("Failed to rename device");
    }
  };

  const handleAssignFarm = async () => {
    try {
      await apiClient.put(`/farmer/devices/${id}/farm`, { farm_id: selectedFarmId ? parseInt(selectedFarmId) : null });
      setShowFarmModal(false);
      fetchDeviceDetail(false);
    } catch (err) {
      alert("Failed to assign farm");
    }
  };

  const handleOpenWifiModal = () => {
    if (!isConnected) {
      alert("This device is currently offline. It must be connected to the website to change Wi-Fi.");
      return;
    }
    let ap = 'TERRAVYN-XXXXXX';
    if (device?.chip_id && device.chip_id !== 'N/A') {
      const clean = device.chip_id.replace(/[:-]/g, '').toUpperCase();
      ap = `TERRAVYN-${clean.slice(-6)}`;
    } else if (device?.mac_address && device.mac_address !== 'N/A') {
      const clean = device.mac_address.replace(/[:-]/g, '').toUpperCase();
      ap = `TERRAVYN-${clean.slice(-6)}`;
    }
    setWifiApName(ap);
    setWifiSetupStep('CONFIRM');
    setShowWifiModal(true);
  };

  const handleStartWifiSetup = async () => {
    setWifiLoading(true);
    try {
      const res = await apiClient.post(`/farmer/devices/${id}/wifi-provisioning`, {});
      if (res.data.ap_name) {
        setWifiApName(res.data.ap_name);
      }
      setWifiSetupStep('IN_PROGRESS');
      fetchDeviceDetail(false);
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to initiate Wi-Fi setup. Please try again.");
    } finally {
      setWifiLoading(false);
    }
  };

  // Polling effect while Wi-Fi provisioning is in progress
  useEffect(() => {
    let pollInterval = null;
    let timerInterval = null;

    if (wifiSetupStep === 'IN_PROGRESS') {
      setWifiElapsedTime(0);

      timerInterval = setInterval(() => {
        setWifiElapsedTime(prev => prev + 1);
      }, 1000);

      pollInterval = setInterval(async () => {
        try {
          const res = await apiClient.get(`/farmer/devices/${id}`);
          setDevice(res.data);
          // If the device reconnected and is ONLINE
          if (res.data.connectivity_status === 'ONLINE' && res.data.wifi_provisioning_requested === false) {
            setWifiSetupStep('SUCCESS');
            clearInterval(pollInterval);
            clearInterval(timerInterval);
          }
        } catch (e) {
          console.error("Polling error:", e);
        }
      }, 3000);
    }

    return () => {
      if (pollInterval) clearInterval(pollInterval);
      if (timerInterval) clearInterval(timerInterval);
    };
  }, [wifiSetupStep, id]);

  const getStatusBadge = (status) => {
    switch (status) {
      case 'READY_FOR_SALE': return <span className="px-2.5 py-1 bg-blue-100 text-blue-700 rounded text-sm font-medium">Ready</span>;
      case 'ASSIGNED': return <span className="px-2.5 py-1 bg-emerald-100 text-emerald-700 rounded text-sm font-medium">Assigned</span>;
      case 'MAINTENANCE': return <span className="px-2.5 py-1 bg-orange-100 text-orange-700 rounded text-sm font-medium">Maintenance</span>;
      case 'DECOMMISSIONED': return <span className="px-2.5 py-1 bg-red-100 text-red-700 rounded text-sm font-medium">Decommissioned</span>;
      default: return <span className="px-2.5 py-1 bg-slate-100 text-slate-700 rounded text-sm font-medium">{status || 'UNKNOWN'}</span>;
    }
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto p-6 space-y-6">
        <div className="flex items-center gap-4">
          <div className="h-10 w-10 bg-slate-100 rounded-lg animate-pulse" />
          <div className="space-y-2">
            <div className="h-6 w-48 bg-slate-100 rounded animate-pulse" />
            <div className="h-4 w-32 bg-slate-100 rounded animate-pulse" />
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="h-64 bg-slate-100 rounded-xl animate-pulse col-span-2" />
          <div className="h-64 bg-slate-100 rounded-xl animate-pulse" />
        </div>
      </div>
    );
  }

  if (error || !device) {
    return (
      <div className="max-w-xl mx-auto my-12 p-8 bg-white rounded-xl border border-slate-200 text-center space-y-4">
        <AlertTriangle className="w-12 h-12 text-amber-500 mx-auto" />
        <h2 className="text-xl font-bold text-slate-800">Device Error</h2>
        <p className="text-slate-600">{error || "Device information could not be retrieved."}</p>
        <button 
          onClick={() => navigate('/farmer/devices')}
          className="px-4 py-2 bg-brand text-white rounded-lg hover:bg-brand/90 transition inline-flex items-center gap-2"
        >
          <ArrowLeft className="w-4 h-4" /> Back to My Devices
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <button 
            onClick={() => navigate('/farmer/devices')}
            className="p-2 border border-slate-200 rounded-lg hover:bg-slate-50 transition text-slate-600"
            title="Back to devices"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-3">
              {device.device_name || 'Unnamed Device'}
              {device.connectivity_status === 'ONLINE' ? (
                <span className="flex items-center gap-1.5 text-emerald-600 bg-emerald-50 px-2 py-1 rounded text-xs font-semibold uppercase tracking-wider">
                  <Wifi className="w-3.5 h-3.5" /> Online
                </span>
              ) : (
                <span className="flex items-center gap-1.5 text-red-600 bg-red-50 px-2 py-1 rounded text-xs font-semibold uppercase tracking-wider">
                  <WifiOff className="w-3.5 h-3.5" /> Offline
                </span>
              )}
            </h1>
            <p className="text-slate-500 font-mono mt-1">{device.device_uid}</p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <button 
            onClick={handleOpenWifiModal}
            disabled={!isConnected}
            className={`px-4 py-2 rounded-lg transition flex items-center gap-2 font-medium shadow-sm ${
              isConnected 
                ? 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 hover:border-brand/40 cursor-pointer' 
                : 'bg-slate-100 border border-slate-200 text-slate-400 cursor-not-allowed opacity-60 shadow-none hover:bg-slate-100'
            }`}
            title={isConnected ? "Change Wi-Fi network for this device" : "Device must be connected to the website to change Wi-Fi"}
          >
            {isConnected ? (
              <Wifi className="w-4 h-4 text-brand" />
            ) : (
              <WifiOff className="w-4 h-4 text-slate-400" />
            )}
            Change Wi-Fi
          </button>
          <button 
            onClick={() => setShowRenameModal(true)}
            className="px-4 py-2 bg-white border border-slate-200 text-slate-700 rounded-lg hover:bg-slate-50 transition flex items-center gap-2 font-medium"
          >
            <Edit3 className="w-4 h-4" /> Rename
          </button>
          <button 
            onClick={() => setShowFarmModal(true)}
            className="px-4 py-2 bg-brand text-white rounded-lg hover:bg-brand/90 transition flex items-center gap-2 font-medium"
          >
            <MapPin className="w-4 h-4" /> Assign Farm
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column */}
        <div className="lg:col-span-2 space-y-6">
          {/* Overview & Info */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="p-5 border-b border-slate-100 bg-slate-50">
              <h3 className="font-semibold text-slate-800 flex items-center gap-2">
                <Cpu className="w-5 h-5 text-brand" /> Device Information
              </h3>
            </div>
            <div className="p-5 grid grid-cols-1 sm:grid-cols-2 gap-y-6 gap-x-8">
              <div>
                <p className="text-sm text-slate-500 mb-1">Product Category</p>
                <p className="font-medium text-slate-800">{device.product_category_name || 'N/A'}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500 mb-1">Device Status</p>
                <div className="mt-1">{getStatusBadge(device.device_status)}</div>
              </div>
              <div>
                <p className="text-sm text-slate-500 mb-1">MAC Address</p>
                <p className="font-medium text-slate-800 font-mono">{device.mac_address || 'N/A'}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500 mb-1">Chip ID</p>
                <p className="font-medium text-slate-800 font-mono">{device.chip_id || 'N/A'}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500 mb-1">Firmware Version</p>
                <p className="font-medium text-slate-800">{device.firmware_version || 'N/A'}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500 mb-1">Irrigation Mode</p>
                <div className="pt-0.5">
                  <DeviceModeControl
                    device={{ id: device.id, irrigation_mode: device.irrigation_mode, last_mode_change: device.last_mode_change }}
                    compact={true}
                    onModeChange={() => fetchDeviceDetail(false)}
                  />
                </div>
              </div>
              <div>
                <p className="text-sm text-slate-500 mb-1">Pump Status</p>
                <p className="font-medium text-slate-800">{device.pump_status ? 'ON' : 'OFF'}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500 mb-1">Weather Prediction</p>
                <p className="font-medium text-slate-800 truncate">{device.weather_prediction || 'N/A'}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500 mb-1">Device Uptime</p>
                <p className="font-medium text-slate-800">
                  {device.uptime_seconds ? `${Math.floor(device.uptime_seconds/3600)}h ${Math.floor((device.uptime_seconds%3600)/60)}m` : 'N/A'}
                </p>
              </div>
              <div>
                <p className="text-sm text-slate-500 mb-1">Last Seen</p>
                <p className="font-medium text-slate-800">
                  {device.last_heartbeat ? dayjs(device.last_heartbeat).fromNow() : 'N/A'}
                </p>
              </div>
              <div>
                <p className="text-sm text-slate-500 mb-1">Signal Quality</p>
                <p className="font-medium text-slate-800">{device.signal_quality || 'N/A'}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500 mb-1">RSSI (Strength)</p>
                <p className="font-medium text-slate-800 flex items-center gap-2">
                  <Activity className="w-4 h-4 text-emerald-500" /> 
                  {device.rssi ? `${device.rssi} dBm` : 'N/A'}
                </p>
              </div>
            </div>
          </div>

          {/* Weather Information */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="p-5 border-b border-slate-100 bg-slate-50 flex justify-between items-center">
              <h3 className="font-semibold text-slate-800 flex items-center gap-2">
                <ThermometerSun className="w-5 h-5 text-brand" /> Weather Information
              </h3>
              {device.telemetry?.recorded_at && (
                <span className="text-xs text-slate-500">
                  Last updated {dayjs(device.telemetry.recorded_at).fromNow()}
                </span>
              )}
            </div>
            <div className="p-5 grid grid-cols-1 sm:grid-cols-5 gap-4">
              <div className="bg-orange-50 p-4 rounded-lg border border-orange-100 text-center">
                <ThermometerSun className="w-6 h-6 text-orange-500 mx-auto mb-2" />
                <p className="text-sm text-orange-600 font-medium">Temp</p>
                <p className="text-2xl font-bold text-orange-700">{device.temperature ?? device.telemetry?.temperature ?? '--'}°C</p>
              </div>
              <div className="bg-cyan-50 p-4 rounded-lg border border-cyan-100 text-center">
                <Droplets className="w-6 h-6 text-cyan-500 mx-auto mb-2" />
                <p className="text-sm text-cyan-600 font-medium">Humidity</p>
                <p className="text-2xl font-bold text-cyan-700">{device.humidity ?? device.telemetry?.humidity ?? '--'}%</p>
              </div>
              <div className="bg-slate-50 p-4 rounded-lg border border-slate-200 text-center">
                <Activity className="w-6 h-6 text-slate-500 mx-auto mb-2" />
                <p className="text-sm text-slate-600 font-medium">Pressure</p>
                <p className="text-2xl font-bold text-slate-700">{device.telemetry?.pressure ?? '--'} hPa</p>
                <span className="text-xs font-medium text-slate-500">{device.telemetry?.pressure_trend ? device.telemetry.pressure_trend.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) : '--'}</span>
              </div>
              <div className="bg-indigo-50 p-4 rounded-lg border border-indigo-100 text-center">
                <CloudRain className="w-6 h-6 text-indigo-500 mx-auto mb-2" />
                <p className="text-sm text-indigo-600 font-medium">Prediction</p>
                <p className="text-lg font-bold text-indigo-700 leading-tight flex items-center justify-center h-8">{device.telemetry?.weather_prediction || device.weather_prediction || '--'}</p>
              </div>
              {device.rain_detected || device.telemetry?.rain_detected ? (
                <div className="bg-blue-50 p-4 rounded-lg border border-blue-100 text-center flex flex-col justify-center items-center">
                  <div className="text-3xl mb-1">🌧️</div>
                  <p className="text-lg font-bold text-blue-700">Raining</p>
                </div>
              ) : (
                <div className="bg-emerald-50 p-4 rounded-lg border border-emerald-100 text-center flex flex-col justify-center items-center">
                  <div className="text-3xl mb-1">☀️</div>
                  <p className="text-lg font-bold text-emerald-700">No Rain</p>
                </div>
              )}
            </div>
          </div>

          {/* Rain Irrigation Alert */}
          {device.status === 'ONLINE' && device.rain_detected && (
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 flex items-start gap-3">
              <div className="text-2xl mt-0.5">🌧️</div>
              <div>
                <h4 className="font-semibold text-blue-800">Irrigation paused due to rainfall.</h4>
                <p className="text-sm text-blue-600 mt-1">Automatic irrigation is suspended while rain is detected.</p>
              </div>
            </div>
          )}

          {/* Telemetry Snapshot */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="p-5 border-b border-slate-100 bg-slate-50 flex justify-between items-center">
              <h3 className="font-semibold text-slate-800 flex items-center gap-2">
                <Activity className="w-5 h-5 text-brand" /> Telemetry Snapshot
              </h3>
              {device.telemetry?.recorded_at && (
                <span className="text-xs text-slate-500">
                  Last updated {dayjs(device.telemetry.recorded_at).fromNow()}
                </span>
              )}
            </div>
            {device.telemetry ? (
              <div className="p-5 grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="bg-blue-50 p-4 rounded-lg border border-blue-100 text-center">
                  <Droplets className="w-6 h-6 text-blue-500 mx-auto mb-2" />
                  <p className="text-sm text-blue-600 font-medium">Soil Moisture</p>
                  <p className="text-2xl font-bold text-blue-700">{device.telemetry.soil_moisture ?? '--'}%</p>
                </div>
                <div className="bg-emerald-50 p-4 rounded-lg border border-emerald-100 text-center">
                  <Power className="w-6 h-6 text-emerald-500 mx-auto mb-2" />
                  <p className="text-sm text-emerald-600 font-medium">Pump Status</p>
                  <p className="text-2xl font-bold text-emerald-700">{device.telemetry.pump_status ?? device.pump_status ? 'ON' : 'OFF'}</p>
                </div>
                <div className="bg-red-50 p-4 rounded-lg border border-red-100 text-center">
                  <AlertTriangle className="w-6 h-6 text-red-500 mx-auto mb-2" />
                  <p className="text-sm text-red-600 font-medium">Obstacle</p>
                  <p className="text-2xl font-bold text-red-700">{device.telemetry.obstacle_detected ? 'DETECTED' : 'CLEAR'}</p>
                </div>
              </div>
            ) : (
              <div className="p-12 text-center text-slate-500">
                <Activity className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                <p>No telemetry data available yet.</p>
              </div>
            )}
          </div>
        </div>

        {/* Right Column */}
        <div className="space-y-6">
          {/* Connection & Wi-Fi Settings */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="p-5 border-b border-slate-100 bg-slate-50 flex justify-between items-center">
              <h3 className="font-semibold text-slate-800 flex items-center gap-2">
                <Wifi className="w-5 h-5 text-brand" /> Connection & Wi-Fi
              </h3>
              <span className={`px-2 py-0.5 rounded text-xs font-semibold uppercase tracking-wider flex items-center gap-1.5 ${
                device.connectivity_status === 'ONLINE' ? 'bg-emerald-50 text-emerald-700 border border-emerald-100' : 'bg-red-50 text-red-700 border border-red-100'
              }`}>
                {device.connectivity_status === 'ONLINE' ? <Wifi className="w-3.5 h-3.5" /> : <WifiOff className="w-3.5 h-3.5" />}
                {device.connectivity_status}
              </span>
            </div>
            <div className="p-5 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-slate-500 mb-1">Signal Quality</p>
                  <p className="font-semibold text-slate-800 text-sm">{device.signal_quality || 'Good'}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 mb-1">Signal Strength</p>
                  <p className="font-semibold text-slate-800 text-sm">{device.rssi ? `${device.rssi} dBm` : 'N/A'}</p>
                </div>
              </div>

              {device.wifi_provisioning_requested && (
                <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-center gap-2 text-xs text-amber-800">
                  <RefreshCw className="w-4 h-4 animate-spin shrink-0 text-amber-600" />
                  <span>Wi-Fi setup command pending device pickup.</span>
                </div>
              )}

              <div className="border-t border-slate-100 pt-3">
                <p className="text-xs text-slate-500 mb-3 leading-relaxed">
                  Need to change your router or update the Wi-Fi credentials for this device?
                </p>
                <button
                  onClick={handleOpenWifiModal}
                  disabled={!isConnected}
                  className={`w-full py-2.5 px-4 rounded-lg text-sm font-medium transition flex items-center justify-center gap-2 shadow-sm ${
                    isConnected
                      ? 'bg-slate-900 hover:bg-slate-800 text-white cursor-pointer'
                      : 'bg-slate-100 text-slate-400 border border-slate-200 cursor-not-allowed opacity-60 shadow-none'
                  }`}
                  title={isConnected ? "Change Wi-Fi network for this device" : "Device must be connected to the website to change Wi-Fi"}
                >
                  {isConnected ? (
                    <Wifi className="w-4 h-4 text-emerald-400" />
                  ) : (
                    <WifiOff className="w-4 h-4 text-slate-400" />
                  )}
                  Change Wi-Fi
                </button>
                {isConnected ? (
                  <p className="text-[11px] text-emerald-600 mt-2 flex items-center justify-center gap-1.5 font-medium">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                    Device connected — ready for Wi-Fi change
                  </p>
                ) : (
                  <div className="mt-2.5 p-2.5 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-2 text-xs text-amber-800">
                    <WifiOff className="w-4 h-4 shrink-0 text-amber-600 mt-0.5" />
                    <span>Device is currently offline. Connect the device to the website to change Wi-Fi.</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Farm Assignment */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="p-5 border-b border-slate-100 bg-slate-50">
              <h3 className="font-semibold text-slate-800 flex items-center gap-2">
                <MapPin className="w-5 h-5 text-brand" /> Farm Assignment
              </h3>
            </div>
            <div className="p-5 space-y-4">
              {device.farm_id ? (
                <>
                  <div>
                    <p className="text-sm text-slate-500 mb-1">Assigned Farm</p>
                    <p className="font-medium text-slate-800">{device.farm_name}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500 mb-1">Crop Type</p>
                    <p className="font-medium text-slate-800">{device.crop_type || 'N/A'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500 mb-1">Assignment Date</p>
                    <p className="font-medium text-slate-800">
                      {device.assigned_at ? dayjs(device.assigned_at).format('MMM D, YYYY') : 'N/A'}
                    </p>
                  </div>
                  <button 
                    onClick={() => setShowFarmModal(true)}
                    className="w-full mt-2 py-2 text-sm font-medium text-brand bg-brand/5 rounded-lg hover:bg-brand/10 transition"
                  >
                    Reassign Farm
                  </button>
                </>
              ) : (
                <div className="text-center py-4">
                  <p className="text-slate-500 mb-4">This device is not assigned to any farm.</p>
                  <button 
                    onClick={() => setShowFarmModal(true)}
                    className="px-4 py-2 bg-brand text-white rounded-lg hover:bg-brand/90 transition inline-flex items-center gap-2"
                  >
                    <MapPin className="w-4 h-4" /> Assign Farm
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Recent Alerts */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="p-5 border-b border-slate-100 bg-slate-50">
              <h3 className="font-semibold text-slate-800 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-red-500" /> Recent Alerts
              </h3>
            </div>
            <div className="p-0">
              {device.alerts?.length > 0 ? (
                <ul className="divide-y divide-slate-100">
                  {device.alerts.map(alert => (
                    <li key={alert.id} className="p-4 hover:bg-slate-50 transition">
                      <div className="flex justify-between items-start mb-1">
                        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                          alert.severity === 'critical' ? 'bg-red-100 text-red-700' :
                          alert.severity === 'warning' ? 'bg-orange-100 text-orange-700' :
                          'bg-blue-100 text-blue-700'
                        }`}>
                          {alert.severity.toUpperCase()}
                        </span>
                        <span className="text-xs text-slate-400">{dayjs(alert.generated_time).fromNow()}</span>
                      </div>
                      <p className="text-sm font-medium text-slate-800">{alert.title}</p>
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="p-8 text-center text-slate-500 text-sm">
                  <CheckCircle className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
                  No recent alerts. Device is healthy.
                </div>
              )}
            </div>
          </div>

          {/* Activity Timeline */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="p-5 border-b border-slate-100 bg-slate-50">
              <h3 className="font-semibold text-slate-800 flex items-center gap-2">
                <Clock className="w-5 h-5 text-brand" /> Activity Timeline
              </h3>
            </div>
            <div className="p-5">
              {device.activities?.length > 0 ? (
                <div className="relative border-l-2 border-slate-200 ml-3 space-y-6">
                  {device.activities.map((activity, idx) => (
                    <div key={idx} className="relative pl-6">
                      <div className="absolute -left-1.5 top-1 w-3 h-3 bg-brand rounded-full ring-4 ring-white"></div>
                      <p className="text-xs text-slate-400 mb-1">{dayjs(activity.timestamp).format('MMM D, YYYY h:mm A')}</p>
                      <p className="text-sm font-medium text-slate-800">{activity.description}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-500 text-center">No recent activity found.</p>
              )}
            </div>
          </div>
        </div>

      </div>

      {/* Rename Modal */}
      {showRenameModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 duration-200">
            <div className="p-5 border-b border-slate-100 flex justify-between items-center">
              <h3 className="font-bold text-lg text-slate-800">Rename Device</h3>
              <button onClick={() => setShowRenameModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6">
              <label className="block text-sm font-medium text-slate-700 mb-2">Device Name</label>
              <input 
                type="text" 
                maxLength={50}
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand/20 focus:border-brand"
                placeholder="e.g. Rice Field Sensor A"
              />
              <p className="text-xs text-slate-500 mt-2 text-right">{newName.length}/50</p>
            </div>
            <div className="p-4 border-t border-slate-100 bg-slate-50 flex justify-end gap-3">
              <button onClick={() => setShowRenameModal(false)} className="px-4 py-2 text-slate-600 hover:bg-slate-200 rounded-lg transition font-medium">Cancel</button>
              <button onClick={handleRename} disabled={!newName.trim()} className="px-4 py-2 bg-brand text-white rounded-lg hover:bg-brand/90 transition font-medium disabled:opacity-50 flex items-center gap-2">
                <Save className="w-4 h-4" /> Save
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Assign Farm Modal */}
      {showFarmModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 duration-200">
            <div className="p-5 border-b border-slate-100 flex justify-between items-center">
              <h3 className="font-bold text-lg text-slate-800">Assign Farm</h3>
              <button onClick={() => setShowFarmModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6">
              <label className="block text-sm font-medium text-slate-700 mb-2">Select Farm</label>
              <select 
                value={selectedFarmId}
                onChange={(e) => setSelectedFarmId(e.target.value)}
                className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand/20 focus:border-brand"
              >
                <option value="">-- Remove Farm Assignment --</option>
                {farms.map(farm => (
                  <option key={farm.id} value={farm.id}>{farm.name} - {farm.location}</option>
                ))}
              </select>
            </div>
            <div className="p-4 border-t border-slate-100 bg-slate-50 flex justify-end gap-3">
              <button onClick={() => setShowFarmModal(false)} className="px-4 py-2 text-slate-600 hover:bg-slate-200 rounded-lg transition font-medium">Cancel</button>
              <button onClick={handleAssignFarm} className="px-4 py-2 bg-brand text-white rounded-lg hover:bg-brand/90 transition font-medium flex items-center gap-2">
                <Save className="w-4 h-4" /> Save Assignment
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Change Wi-Fi Modal */}
      {showWifiModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg overflow-hidden animate-in fade-in zoom-in-95 duration-200">
            {/* Modal Header */}
            <div className="p-5 border-b border-slate-100 bg-slate-50/80 flex justify-between items-center">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-lg bg-brand/10 text-brand flex items-center justify-center">
                  <Wifi className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-lg text-slate-900 leading-tight">Change Device Wi-Fi</h3>
                  <p className="text-xs text-slate-500 font-mono">{device?.device_uid}</p>
                </div>
              </div>
              <button 
                onClick={() => {
                  setShowWifiModal(false);
                  fetchDeviceDetail(false);
                }} 
                className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-100 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            {wifiSetupStep === 'CONFIRM' && (
              <div className="p-6 space-y-4">
                <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5 shrink-0" />
                  <div className="text-sm text-amber-900 space-y-1">
                    <p className="font-semibold">Temporary Disconnection</p>
                    <p className="text-amber-800 text-xs leading-relaxed">
                      This will temporarily disconnect the TERRAVYN device from its current Wi-Fi network so it can connect to your new network.
                    </p>
                  </div>
                </div>

                <p className="text-sm text-slate-600 leading-relaxed">
                  After starting setup, connect your phone to the temporary <strong>{wifiApName}</strong> Wi-Fi network and enter your new Wi-Fi details directly on the TERRAVYN setup page.
                </p>

                <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-start gap-3">
                  <ShieldCheck className="w-5 h-5 text-emerald-600 mt-0.5 shrink-0" />
                  <div className="text-xs text-emerald-900 space-y-0.5">
                    <p className="font-semibold">Security & Privacy Guarantee</p>
                    <p className="text-emerald-800 leading-relaxed">
                      Your Wi-Fi password is entered directly into the device and is never sent to or stored by TERRAVYN.
                    </p>
                  </div>
                </div>

                <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
                  <button
                    onClick={() => setShowWifiModal(false)}
                    className="px-4 py-2 border border-slate-200 text-slate-700 hover:bg-slate-50 rounded-lg text-sm font-medium transition"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleStartWifiSetup}
                    disabled={wifiLoading}
                    className="px-5 py-2.5 bg-brand text-white hover:bg-brand-dark rounded-lg text-sm font-medium transition flex items-center gap-2 shadow-sm disabled:opacity-50"
                  >
                    {wifiLoading ? (
                      <><RefreshCw className="w-4 h-4 animate-spin" /> Starting...</>
                    ) : (
                      <><Wifi className="w-4 h-4" /> Start Wi-Fi Setup</>
                    )}
                  </button>
                </div>
              </div>
            )}

            {wifiSetupStep === 'IN_PROGRESS' && (
              <div className="p-6 space-y-5 max-h-[80vh] overflow-y-auto">
                {/* Active status indicator */}
                <div className="p-3.5 bg-blue-50 border border-blue-200 rounded-xl flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="relative flex h-3 w-3">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-3 w-3 bg-blue-600"></span>
                    </div>
                    <div>
                      <p className="text-xs font-bold text-blue-900">Wi-Fi Setup in Progress</p>
                      <p className="text-[11px] text-blue-700">The device may appear offline while changing networks.</p>
                    </div>
                  </div>
                  <span className="text-xs font-mono font-semibold text-blue-700 bg-white px-2 py-0.5 rounded border border-blue-100 shadow-2xs">
                    {Math.floor(wifiElapsedTime / 60)}:{String(wifiElapsedTime % 60).padStart(2, '0')}
                  </span>
                </div>

                {/* Step-by-Step Instructions */}
                <div className="space-y-3.5 text-slate-700 text-xs sm:text-sm">
                  <div className="flex items-start gap-3">
                    <span className="w-6 h-6 rounded-full bg-slate-100 text-slate-700 text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">1</span>
                    <p className="leading-snug">
                      <strong className="text-slate-900">Request Sent:</strong> Wi-Fi setup request sent to your TERRAVYN device.
                    </p>
                  </div>

                  <div className="flex items-start gap-3">
                    <span className="w-6 h-6 rounded-full bg-slate-100 text-slate-700 text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">2</span>
                    <p className="leading-snug">
                      <strong className="text-slate-900">Wait for Device:</strong> Wait a few seconds for the device to enter Wi-Fi setup mode.
                    </p>
                  </div>

                  <div className="flex items-start gap-3">
                    <span className="w-6 h-6 rounded-full bg-slate-100 text-slate-700 text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">3</span>
                    <p className="leading-snug">
                      <strong className="text-slate-900">Open Phone Wi-Fi:</strong> On your phone or laptop, open Wi-Fi settings.
                    </p>
                  </div>

                  <div className="flex items-start gap-3">
                    <span className="w-6 h-6 rounded-full bg-brand text-white text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">4</span>
                    <div className="flex-1">
                      <p className="leading-snug">
                        <strong className="text-slate-900">Connect to:</strong>
                      </p>
                      <div className="mt-1.5 p-2.5 bg-slate-50 border border-slate-200 rounded-lg flex items-center justify-between">
                        <span className="font-mono font-bold text-slate-900 text-sm tracking-wide">{wifiApName}</span>
                        <button
                          onClick={() => {
                            navigator.clipboard.writeText(wifiApName);
                            setCopiedAp(true);
                            setTimeout(() => setCopiedAp(false), 2000);
                          }}
                          className="text-xs font-medium text-slate-600 hover:text-brand flex items-center gap-1 bg-white px-2 py-1 rounded border border-slate-200 shadow-2xs"
                        >
                          {copiedAp ? <><Check className="w-3.5 h-3.5 text-emerald-600" /> Copied</> : <><Copy className="w-3.5 h-3.5" /> Copy</>}
                        </button>
                      </div>
                      <p className="text-[11px] text-slate-400 mt-1">
                        *(The exact network name will appear in your phone's available Wi-Fi list)*
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <span className="w-6 h-6 rounded-full bg-slate-100 text-slate-700 text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">5</span>
                    <p className="leading-snug">
                      <strong className="text-slate-900">Configure Credentials:</strong> The TERRAVYN setup page will allow you to enter the new Wi-Fi network details directly into the device. (If the page doesn't open automatically, visit <span className="font-mono bg-slate-100 px-1 py-0.5 rounded text-slate-800">192.168.4.1</span>).
                    </p>
                  </div>

                  <div className="flex items-start gap-3">
                    <span className="w-6 h-6 rounded-full bg-slate-100 text-slate-700 text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">6</span>
                    <p className="leading-snug">
                      <strong className="text-slate-900">Reconnect:</strong> After saving the new Wi-Fi details, the device will restart and reconnect to TERRAVYN.
                    </p>
                  </div>
                </div>

                {/* Waiting indicator */}
                <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 flex items-center gap-3">
                  <RefreshCw className="w-4 h-4 text-brand animate-spin shrink-0" />
                  <div className="text-xs">
                    <p className="font-semibold text-slate-800">Waiting for TERRAVYN to reconnect...</p>
                    <p className="text-slate-500">This page will automatically detect when the device is back online.</p>
                  </div>
                </div>

                {/* Extended wait helper */}
                {wifiElapsedTime > 120 && (
                  <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800 space-y-1">
                    <p className="font-semibold">TERRAVYN has not reconnected yet.</p>
                    <p className="text-amber-700 leading-relaxed">
                      Make sure the device has power, that your phone connected to the temporary setup network, and that the new Wi-Fi network name and password were typed correctly.
                    </p>
                  </div>
                )}

                <div className="flex justify-end pt-3 border-t border-slate-100">
                  <button
                    onClick={() => {
                      setShowWifiModal(false);
                      fetchDeviceDetail(false);
                    }}
                    className="px-4 py-2 border border-slate-200 text-slate-700 hover:bg-slate-50 rounded-lg text-sm font-medium transition"
                  >
                    Close Setup Window
                  </button>
                </div>
              </div>
            )}

            {wifiSetupStep === 'SUCCESS' && (
              <div className="p-8 text-center space-y-4">
                <div className="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto shadow-sm">
                  <CheckCircle className="w-10 h-10" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-slate-900">Wi-Fi Changed Successfully!</h3>
                  <p className="text-sm text-slate-600 mt-1.5 max-w-sm mx-auto">
                    TERRAVYN is back online and transmitting telemetry on your new network.
                  </p>
                </div>
                <div className="pt-3">
                  <button
                    onClick={() => {
                      setShowWifiModal(false);
                      fetchDeviceDetail(true);
                    }}
                    className="px-6 py-2.5 bg-brand text-white hover:bg-brand-dark rounded-lg text-sm font-medium transition shadow-sm"
                  >
                    Done
                  </button>
                </div>
              </div>
            )}

          </div>
        </div>
      )}

    </div>
  );
};

export default FarmerDeviceDetail;
