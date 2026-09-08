import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, Cpu, Wifi, Hash, QrCode, Calendar, ShieldCheck, 
  User, Phone, Mail, MapPin, PowerOff, ShieldAlert, FileDown 
} from 'lucide-react';
import axios from 'axios';

const DeviceDetails = () => {
  const { deviceUid } = useParams();
  const navigate = useNavigate();
  const [deviceData, setDeviceData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);

  const fetchDetails = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`/api/admin/devices/${deviceUid}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setDeviceData(response.data);
    } catch (err) {
      console.error("Failed to fetch device details:", err);
      setError("Device not found or error loading details.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetails();
  }, [deviceUid]);

  const handleToggleActive = async () => {
    if (!deviceData) return;
    const isCurrentlyActive = deviceData.device?.is_active !== false; // handle null as true
    const endpoint = isCurrentlyActive ? 'disable' : 'activate';
    
    if (!window.confirm(`Are you sure you want to ${endpoint} this device?`)) return;
    
    setActionLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.put(`/api/admin/devices/${deviceUid}/${endpoint}`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      await fetchDetails();
    } catch (err) {
      alert("Failed to update device status");
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-20">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand"></div>
      </div>
    );
  }

  if (error || !deviceData) {
    return (
      <div className="bg-red-50 text-red-600 p-6 rounded-2xl border border-red-100 flex flex-col items-center justify-center text-center">
        <ShieldAlert size={48} className="mb-4 opacity-50" />
        <h2 className="text-xl font-bold mb-2">Error Loading Device</h2>
        <p className="mb-6">{error}</p>
        <button onClick={() => navigate('/admin/devices')} className="bg-white dark:bg-slate-900 px-6 py-2 rounded-xl text-slate-700 dark:text-slate-200 font-medium border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:bg-slate-950 transition-colors">
          Back to Devices
        </button>
      </div>
    );
  }

  const { device, timeline } = deviceData;
  const isAssigned = !!device?.farmer;
  const isActive = device?.is_active !== false;

  return (
    <div className="space-y-6">
      {/* Header & Actions */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div className="flex items-center gap-4">
          <button onClick={() => navigate('/admin/devices')} className="p-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-300 rounded-xl hover:bg-slate-50 dark:bg-slate-950 transition-colors">
            <ArrowLeft size={20} />
          </button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">{device?.device_uid}</h1>
              {!isActive ? (
                <span className="px-3 py-1 bg-red-100 text-red-700 text-xs font-bold rounded-full uppercase tracking-wide">Disabled</span>
              ) : (
                <span className="px-3 py-1 bg-emerald-100 text-emerald-700 text-xs font-bold rounded-full uppercase tracking-wide">Active</span>
              )}
            </div>
            <p className="text-slate-500 dark:text-slate-400 mt-1 flex items-center gap-2">
              <Hash size={14} /> MAC: <span className="font-mono">{device?.mac_address}</span>
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-3 w-full md:w-auto">
          {device?.qr_code_path && (
            <a 
              href={`/api/admin/devices/${device?.device_uid}/download-qr`}
              className="flex-1 md:flex-none flex justify-center items-center gap-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 px-4 py-2.5 rounded-xl text-slate-700 dark:text-slate-200 font-medium hover:bg-slate-50 dark:bg-slate-950 transition-colors shadow-sm"
            >
              <FileDown size={18} /> Download QR
            </a>
          )}
          <button 
            onClick={handleToggleActive}
            disabled={actionLoading}
            className={`flex-1 md:flex-none flex justify-center items-center gap-2 px-4 py-2.5 rounded-xl font-medium transition-colors shadow-sm ${
              isActive 
                ? 'bg-red-50 text-red-600 border border-red-200 hover:bg-red-100' 
                : 'bg-emerald-50 text-emerald-600 border border-emerald-200 hover:bg-emerald-100'
            }`}
          >
            <PowerOff size={18} /> {isActive ? 'Disable Device' : 'Activate Device'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Hardware Information Panel */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-100 dark:border-slate-800/50 p-6 shadow-sm">
            <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100 mb-6 flex items-center gap-2">
              <Cpu className="text-brand" /> Hardware Information
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-y-6 gap-x-8">
              <div>
                <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Registration Status</p>
                <div className="font-medium text-slate-800 dark:text-slate-100 flex items-center gap-2">
                  <ShieldCheck size={16} className="text-emerald-500" />
                  {device?.registration_status}
                </div>
              </div>
              
              <div>
                <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Product Category</p>
                <div className="font-medium text-slate-800 dark:text-slate-100">
                  {device?.product_category_name === "TERRAVYN Other" ? device?.custom_category : (device?.product_category_name || 'N/A')}
                </div>
              </div>

              <div>
                <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Manufactured At</p>
                <div className="font-medium text-slate-800 dark:text-slate-100">
                  {device?.manufactured_at ? new Date(device.manufactured_at).toLocaleDateString() : 'N/A'}
                </div>
              </div>
              
              <div>
                <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Firmware / Hardware</p>
                <div className="font-medium text-slate-800 dark:text-slate-100">
                  {device?.firmware_version || 'Unknown'} / {device?.hardware_version || 'Unknown'}
                </div>
              </div>

              <div>
                <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Last Heartbeat</p>
                <div className="font-medium text-slate-800 dark:text-slate-100 flex items-center gap-2">
                  <Wifi size={16} className={device?.last_heartbeat ? "text-emerald-500" : "text-slate-300"} />
                  {device?.last_heartbeat ? new Date(device?.last_heartbeat).toLocaleString() : 'Never'}
                </div>
              </div>

              {device?.manufacturing_notes && (
                <div className="md:col-span-2">
                  <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Manufacturing Notes</p>
                  <div className="font-medium text-slate-800 dark:text-slate-100 text-sm bg-slate-50 dark:bg-slate-800/50 p-3 rounded-lg">
                    {device.manufacturing_notes}
                  </div>
                </div>
              )}
            </div>
          </div>
          
          {/* Security Credentials */}
          <div className="bg-slate-900 rounded-2xl border border-slate-800 p-6 shadow-sm text-white">
            <h3 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
              <ShieldCheck className="text-brand" /> Provisioning Credentials
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/50">
                <p className="text-xs text-slate-400 font-medium mb-1 uppercase tracking-wider">Activation Code</p>
                <p className="font-mono text-lg text-emerald-400 tracking-widest">{device?.activation_code}</p>
              </div>
              
              <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/50">
                <p className="text-xs text-slate-400 font-medium mb-1 uppercase tracking-wider">Secret Code</p>
                <p className="font-mono text-sm text-slate-300 truncate" title={device?.secret_code}>{device?.secret_code}</p>
              </div>
            </div>
          </div>
          
          {/* Telemetry Snapshot */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-100 dark:border-slate-800/50 p-6 shadow-sm">
            <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100 mb-6 flex items-center gap-2">
              <Wifi className="text-brand" /> Latest Telemetry Snapshot
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-slate-50 dark:bg-slate-800/50 p-4 rounded-xl border border-slate-100 dark:border-slate-700/50">
                <p className="text-xs text-slate-500 dark:text-slate-400 font-medium uppercase tracking-wider mb-1">Temperature</p>
                <p className="font-bold text-lg text-slate-800 dark:text-slate-100">{device?.last_temperature != null ? `${device.last_temperature} °C` : '--'}</p>
              </div>
              <div className="bg-slate-50 dark:bg-slate-800/50 p-4 rounded-xl border border-slate-100 dark:border-slate-700/50">
                <p className="text-xs text-slate-500 dark:text-slate-400 font-medium uppercase tracking-wider mb-1">Humidity</p>
                <p className="font-bold text-lg text-slate-800 dark:text-slate-100">{device?.last_humidity != null ? `${device.last_humidity} %` : '--'}</p>
              </div>
              <div className="bg-slate-50 dark:bg-slate-800/50 p-4 rounded-xl border border-slate-100 dark:border-slate-700/50">
                <p className="text-xs text-slate-500 dark:text-slate-400 font-medium uppercase tracking-wider mb-1">Soil Moisture</p>
                <p className="font-bold text-lg text-slate-800 dark:text-slate-100">{device?.last_soil_moisture != null ? `${device.last_soil_moisture} %` : '--'}</p>
              </div>
              <div className="bg-slate-50 dark:bg-slate-800/50 p-4 rounded-xl border border-slate-100 dark:border-slate-700/50">
                <p className="text-xs text-slate-500 dark:text-slate-400 font-medium uppercase tracking-wider mb-1">RSSI</p>
                <p className="font-bold text-lg text-slate-800 dark:text-slate-100">{device?.last_rssi != null ? `${device.last_rssi} dBm` : '--'}</p>
              </div>
            </div>
            <p className="text-xs text-slate-500 mt-4 text-right">
              Last Seen: {device?.last_seen ? new Date(device.last_seen).toLocaleString() : 'Never'}
            </p>
          </div>
        </div>

        {/* Farmer Information Panel */}
        <div className="space-y-6">
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-100 dark:border-slate-800/50 p-6 shadow-sm h-full">
            <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100 mb-6 flex items-center gap-2">
              <User className="text-brand" /> Assignment Details
            </h3>
            
            {isAssigned ? (
              <div className="space-y-6">
                <div className="flex items-center justify-between pb-6 border-b border-slate-100 dark:border-slate-800/50">
                  <div>
                    <p className="text-xs text-slate-500 dark:text-slate-400 font-medium uppercase tracking-wider mb-1">Status</p>
                    <p className="font-bold text-emerald-600 bg-emerald-50 px-3 py-1 rounded-full inline-block text-sm">Assigned</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-slate-500 dark:text-slate-400 font-medium uppercase tracking-wider mb-1">Date</p>
                    <p className="font-medium text-slate-800 dark:text-slate-100 text-sm">{new Date(device?.assigned_at).toLocaleDateString()}</p>
                  </div>
                </div>
                
                <div className="space-y-4">
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-full bg-brand/10 flex items-center justify-center text-brand font-bold shrink-0">
                      {device?.farmer?.name ? device?.farmer?.name.charAt(0).toUpperCase() : '?'}
                    </div>
                    <div>
                      <p className="text-xs text-slate-500 dark:text-slate-400 font-medium uppercase tracking-wider mb-0.5">Farmer Name</p>
                      <p className="font-bold text-slate-800 dark:text-slate-100">{device?.farmer?.name || 'Unknown'}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-slate-50 dark:bg-slate-950 flex items-center justify-center text-slate-400 shrink-0">
                      <Phone size={18} />
                    </div>
                    <div>
                      <p className="text-xs text-slate-500 dark:text-slate-400 font-medium uppercase tracking-wider mb-0.5">Phone Number</p>
                      <p className="font-medium text-slate-800 dark:text-slate-100">{device?.farmer?.phone}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-slate-50 dark:bg-slate-950 flex items-center justify-center text-slate-400 shrink-0">
                      <Mail size={18} />
                    </div>
                    <div className="overflow-hidden">
                      <p className="text-xs text-slate-500 dark:text-slate-400 font-medium uppercase tracking-wider mb-0.5">Email</p>
                      <p className="font-medium text-slate-800 dark:text-slate-100 truncate">{device?.farmer?.email}</p>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-12 px-4 bg-slate-50 dark:bg-slate-950 rounded-xl border border-dashed border-slate-200 dark:border-slate-800 h-[calc(100%-3rem)] flex flex-col justify-center">
                <div className="w-16 h-16 bg-white dark:bg-slate-900 shadow-sm border border-slate-100 dark:border-slate-800/50 rounded-full flex items-center justify-center mx-auto mb-4">
                  <User className="text-slate-400 w-8 h-8" />
                </div>
                <h4 className="text-base font-bold text-slate-800 dark:text-slate-100 mb-2">Unassigned Device</h4>
                <p className="text-sm text-slate-500 dark:text-slate-400 mb-6">This device is provisioned but hasn't been assigned to a farmer yet.</p>
                <button 
                  onClick={() => navigate('/admin/devices')}
                  className="text-sm font-medium text-brand hover:text-brand-dark"
                >
                  Assign from Devices List &rarr;
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DeviceDetails;
