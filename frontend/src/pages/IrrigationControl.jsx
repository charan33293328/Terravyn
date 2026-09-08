import React, { useState, useEffect } from 'react';
import { Power, Settings, Droplets } from 'lucide-react';
import { useDeviceWebSocket } from '../hooks/useDeviceWebSocket';
import apiClient from '../api/client';
import IrrigationIntelligencePanel from '../components/irrigation/IrrigationIntelligencePanel';

const IrrigationControl = () => {
  const [activeDevice, setActiveDevice] = useState(null);
  const deviceId = activeDevice?.id || 15;
  const { sensorData, deviceStatus, sendCommand } = useDeviceWebSocket(deviceId);
  
  // Local state to bridge the gap between user action and websocket response
  const [isAuto, setIsAuto] = useState(true);
  const [pumpOn, setPumpOn] = useState(false);
  const [debugData, setDebugData] = useState(null);

  // Fetch active user device on mount
  useEffect(() => {
    const fetchUserDevice = async () => {
      try {
        const res = await apiClient.get('/farmer/devices');
        const devices = res.data?.devices || [];
        if (devices.length > 0) {
          const dev = devices[0];
          setActiveDevice(dev);
          const initialMode = (dev.irrigation_mode || 'AUTO').toUpperCase();
          setIsAuto(initialMode === 'AUTO');
          fetchDebugConfig(dev.mac_address);
        } else {
          const altRes = await apiClient.get('/devices/');
          if (altRes.data && altRes.data.length > 0) {
            const dev = altRes.data[0];
            setActiveDevice(dev);
            const initialMode = (dev.irrigation_mode || 'AUTO').toUpperCase();
            setIsAuto(initialMode === 'AUTO');
            fetchDebugConfig(dev.mac_address);
          }
        }
      } catch (err) {
        console.error("Failed to load active device:", err);
      }
    };
    fetchUserDevice();
  }, []);

  useEffect(() => {
    if (sensorData) {
      if (sensorData.irrigation_mode) {
        setIsAuto(sensorData.irrigation_mode.toUpperCase() === 'AUTO');
      }
      if (sensorData.pump_status !== undefined) {
        setPumpOn(Boolean(sensorData.pump_status));
      }
    }
  }, [sensorData]);

  const handleModeChange = async (mode) => {
    const targetMode = mode.toUpperCase();
    console.log(`Changing irrigation mode to ${targetMode}`);
    const previousAuto = isAuto;
    setIsAuto(targetMode === 'AUTO');

    const targetDeviceId = activeDevice?.id || 15;
    try {
      const payload = { device_id: targetDeviceId, irrigation_mode: targetMode };
      console.log("[Frontend] Request Payload:", payload);
      const res = await apiClient.post('/devices/mode', payload);
      console.log("[Frontend] Response Data:", res.data);
      if (res.data?.irrigation_mode) {
        const confirmedMode = res.data.irrigation_mode.toUpperCase();
        setIsAuto(confirmedMode === 'AUTO');
        setActiveDevice(prev => prev ? { ...prev, irrigation_mode: confirmedMode } : null);
      }
      fetchDebugConfig(activeDevice?.mac_address);
    } catch (err) {
      console.error("Mode control failed", err);
      setIsAuto(previousAuto);
      alert("Failed to update irrigation mode. Please try again.");
    }
  };

  const fetchDebugConfig = async (mac) => {
    try {
      const targetMac = mac || activeDevice?.mac_address || 'B0:CB:D8:CA:28:18';
      const res = await apiClient.get(`/devices/config/${targetMac}`);
      setDebugData(res.data);
    } catch(err) {
      console.error("Failed to fetch debug config:", err);
    }
  };

  const isOnline = deviceStatus === 'online';

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
             Irrigation Control
             {isOnline ? (
               <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block ml-2"></span>
             ) : (
               <span className="w-2 h-2 rounded-full bg-red-500 inline-block ml-2"></span>
             )}
          </h2>
          <p className="text-slate-500">Precision water management for North Sector Orchards.</p>
        </div>
        <div className="bg-slate-100 p-1 rounded-lg flex">
          <button 
            onClick={() => handleModeChange('auto')}
            className={`px-6 py-2 rounded-md font-medium text-sm transition-colors duration-300 ${isAuto ? 'bg-brand text-white shadow-sm' : 'text-slate-600 hover:text-slate-800'}`}
          >
            Auto Mode
          </button>
          <button 
            onClick={() => handleModeChange('manual')}
            className={`px-6 py-2 rounded-md font-medium text-sm transition-colors duration-300 ${!isAuto ? 'bg-brand text-white shadow-sm' : 'text-slate-600 hover:text-slate-800'}`}
          >
            Manual Mode
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6">
        <div className="bg-white p-8 rounded-xl border border-slate-200 shadow-sm flex flex-col items-center justify-center min-h-[400px]">
          <div className="w-full flex justify-between items-start mb-12">
             <div className="flex items-center gap-2">
                <Settings className="text-slate-400 w-5 h-5"/>
                <span className="font-semibold text-slate-700">Main Pump Station 01</span>
             </div>
             <span className={`text-sm font-medium flex items-center gap-1 ${isOnline ? 'text-green-600' : 'text-red-500'}`}>
                <span className={`w-2 h-2 rounded-full ${isOnline ? 'bg-green-500' : 'bg-red-500'}`}></span> 
                {isOnline ? 'System Operational' : 'Offline'}
             </span>
          </div>

          <div 
            className={`w-48 h-48 rounded-full border-8 flex flex-col items-center justify-center transition-all duration-300 ${
              !isOnline ? 'border-slate-100 bg-slate-50 text-slate-400' :
              pumpOn ? 'border-brand/20 bg-brand text-white shadow-lg shadow-brand/30' : 
              'border-slate-100 bg-white text-slate-600'
            }`}
          >
            <Power className="w-12 h-12 mb-2" />
            <span className="text-xl font-bold">{pumpOn ? 'ON' : 'OFF'}</span>
          </div>
          
          <div className="mt-8 text-center max-w-sm px-4">
            {isAuto ? (
              <p className="text-sm text-slate-600 font-medium bg-blue-50 p-3 rounded-lg border border-blue-100">
                The TERRAVYN device automatically manages irrigation.
              </p>
            ) : (
              <p className="text-sm text-amber-700 font-medium bg-amber-50 p-3 rounded-lg border border-amber-100">
                Automatic irrigation is disabled. Use the physical switch on the TERRAVYN device to operate the pump.
              </p>
            )}
            {!isOnline && <p className="mt-3 text-sm text-red-500 font-semibold">Cannot connect to device. Showing last known status.</p>}
          </div>

          <div className="w-full max-w-2xl grid grid-cols-3 gap-4 mt-12 pt-8 border-t border-slate-100 text-center">
            <div>
              <p className="text-xs text-slate-500 font-medium mb-1">SOIL MOISTURE</p>
              <p className="text-lg font-bold text-slate-800">{sensorData?.soil_moisture != null ? `${parseFloat(sensorData.soil_moisture).toFixed(1)}%` : 'N/A'}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500 font-medium mb-1">TEMPERATURE</p>
              <p className="text-lg font-bold text-slate-800">{sensorData?.temperature != null ? `${parseFloat(sensorData.temperature).toFixed(1)}°C` : 'N/A'}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500 font-medium mb-1">HUMIDITY</p>
              <p className="text-lg font-bold text-slate-800">{sensorData?.humidity != null ? `${parseFloat(sensorData.humidity).toFixed(1)}%` : 'N/A'}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Production Irrigation Intelligence Panel (Prompt 8) */}
      <IrrigationIntelligencePanel farmId={activeDevice?.farm_id || 1} farmName={activeDevice?.name || "North Sector Farm"} />

      {/* Developer Debug Panel */}
      <div className="bg-slate-900 text-green-400 p-6 rounded-xl font-mono text-sm shadow-lg mt-8">
         <h3 className="text-white font-bold mb-4 border-b border-slate-700 pb-2">Developer Debug Panel</h3>
         <div className="grid grid-cols-2 gap-4">
            <div>
              <p><span className="text-slate-400">Frontend isAuto:</span> {isAuto.toString()}</p>
              <p><span className="text-slate-400">Frontend pumpOn:</span> {pumpOn.toString()}</p>
            </div>
            <div>
              <p className="text-slate-400 mb-1">Latest /api/devices/config Response:</p>
              <pre className="bg-slate-950 p-3 rounded border border-slate-800 text-xs overflow-x-auto">
                {debugData ? JSON.stringify(debugData, null, 2) : 'Loading...'}
              </pre>
            </div>
         </div>
      </div>
    </div>
  );
};

export default IrrigationControl;
