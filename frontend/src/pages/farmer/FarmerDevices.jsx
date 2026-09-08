import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  PlusCircle, Activity, Wifi, WifiOff, MapPin, Search, Filter, 
  Download, MoreVertical, ChevronLeft, ChevronRight, CheckCircle, 
  AlertTriangle, Settings, Eye
} from 'lucide-react';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import apiClient from '../../api/client';
import DeviceModeControl from '../../components/DeviceModeControl';

dayjs.extend(relativeTime);

const FarmerDevices = () => {
  const navigate = useNavigate();
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [totalDevices, setTotalDevices] = useState(0);
  const [showExportMenu, setShowExportMenu] = useState(false);
  
  // Filters & Pagination
  const [search, setSearch] = useState('');
  const [connectionStatus, setConnectionStatus] = useState('ALL');
  const [deviceStatus, setDeviceStatus] = useState('ALL');
  const [farmId, setFarmId] = useState('');
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(10);
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');
  
  // Metadata for filters
  const [farms, setFarms] = useState([]);

  useEffect(() => {
    fetchFarms();
  }, []);

  useEffect(() => {
    fetchDevices();
  }, [search, connectionStatus, deviceStatus, farmId, page, limit, sortBy, sortOrder]);

  const fetchFarms = async () => {
    try {
      const res = await apiClient.get('/farmer/farms');
      setFarms(Array.isArray(res.data) ? res.data : []);
    } catch (err) {
      console.error("Failed to fetch farms", err);
    }
  };

  const fetchDevices = async () => {
    setLoading(true);
    try {
      const skip = (page - 1) * limit;
      let url = `/farmer/devices?skip=${skip}&limit=${limit}&sort_by=${sortBy}&sort_order=${sortOrder}`;
      if (search) url += `&search=${encodeURIComponent(search)}`;
      if (connectionStatus !== 'ALL') url += `&connection_status=${connectionStatus}`;
      if (deviceStatus !== 'ALL') url += `&device_status=${deviceStatus}`;
      if (farmId) url += `&farm_id=${farmId}`;

      const res = await apiClient.get(url);
      setDevices(res.data?.devices || []);
      setTotalDevices(res.data?.total || 0);
    } catch (err) {
      console.error("Failed to fetch devices", err);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format) => {
    setShowExportMenu(false);
    try {
      let url = `/farmer/devices/export?format=${format}`;
      if (search) url += `&search=${encodeURIComponent(search)}`;
      if (connectionStatus !== 'ALL') url += `&connection_status=${connectionStatus}`;
      if (deviceStatus !== 'ALL') url += `&device_status=${deviceStatus}`;
      if (farmId) url += `&farm_id=${farmId}`;

      const res = await apiClient.get(url, { responseType: 'blob' });
      
      const blob = new Blob([res.data], { 
        type: format === 'csv' ? 'text/csv' : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
      });
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      
      const timestamp = dayjs().format('YYYYMMDD_HHmmss');
      link.download = `terravyn_devices_${timestamp}.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error('Export failed:', error);
      alert('Failed to export devices');
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'READY_FOR_SALE': return <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-medium">Ready</span>;
      case 'ASSIGNED': return <span className="px-2 py-1 bg-emerald-100 text-emerald-700 rounded text-xs font-medium">Assigned</span>;
      case 'MAINTENANCE': return <span className="px-2 py-1 bg-orange-100 text-orange-700 rounded text-xs font-medium">Maintenance</span>;
      case 'DECOMMISSIONED': return <span className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs font-medium">Decommissioned</span>;
      default: return <span className="px-2 py-1 bg-slate-100 text-slate-700 rounded text-xs font-medium">{status}</span>;
    }
  };

  const totalPages = Math.ceil(totalDevices / limit);

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:justify-between md:items-start gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">My Devices</h1>
          <p className="text-slate-500">View and manage all TERRAVYN devices linked to your account.</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <button 
              onClick={() => setShowExportMenu(!showExportMenu)}
              className="px-4 py-2 bg-white border border-slate-200 text-slate-700 rounded-lg hover:bg-slate-50 transition flex items-center gap-2"
            >
              <Download className="w-4 h-4" />
              Export
            </button>
            {showExportMenu && (
              <div className="absolute right-0 mt-2 w-32 bg-white rounded-lg shadow-lg border border-slate-100 z-10">
                <button 
                  onClick={() => handleExport('csv')} 
                  className="w-full text-left px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 rounded-t-lg"
                >
                  Export CSV
                </button>
                <button 
                  onClick={() => handleExport('xlsx')} 
                  className="w-full text-left px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 rounded-b-lg"
                >
                  Export Excel
                </button>
              </div>
            )}
          </div>
          <button 
            onClick={() => navigate('/farmer/activate-device')}
            className="px-4 py-2 bg-brand text-white rounded-lg hover:bg-brand/90 transition flex items-center gap-2 shadow-sm"
          >
            <PlusCircle className="w-5 h-5" />
            Activate Device
          </button>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input 
              type="text" 
              placeholder="Search by device name or UID..." 
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand/20 focus:border-brand"
            />
          </div>
          <div className="flex flex-wrap gap-3">
            <select 
              value={connectionStatus} 
              onChange={(e) => setConnectionStatus(e.target.value)}
              className="px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand/20 focus:border-brand bg-white"
            >
              <option value="ALL">All Connection Status</option>
              <option value="ONLINE">Online</option>
              <option value="OFFLINE">Offline</option>
            </select>
            
            <select 
              value={deviceStatus} 
              onChange={(e) => setDeviceStatus(e.target.value)}
              className="px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand/20 focus:border-brand bg-white"
            >
              <option value="ALL">All Device Status</option>
              <option value="ASSIGNED">Assigned</option>
              <option value="READY_FOR_SALE">Ready for Sale</option>
              <option value="MAINTENANCE">Maintenance</option>
              <option value="DECOMMISSIONED">Decommissioned</option>
            </select>

            <select 
              value={farmId} 
              onChange={(e) => setFarmId(e.target.value)}
              className="px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand/20 focus:border-brand bg-white"
            >
              <option value="">All Farms</option>
              {farms.map(f => (
                <option key={f.id} value={f.id}>{f.name}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Device List */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-medium">
              <tr>
                <th className="px-6 py-4">Device</th>
                <th className="px-6 py-4">Farm</th>
                <th className="px-6 py-4">Connection</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4">Mode</th>
                <th className="px-6 py-4">Last Seen</th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan="7" className="px-6 py-12 text-center text-slate-500">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand mx-auto mb-4"></div>
                    Loading devices...
                  </td>
                </tr>
              ) : devices.length === 0 ? (
                <tr>
                  <td colSpan="7" className="px-6 py-12 text-center text-slate-500">
                    <Activity className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                    <p className="text-lg font-medium text-slate-700">No devices found</p>
                    <p>Try adjusting your filters or search query.</p>
                  </td>
                </tr>
              ) : (
                devices.map(device => (
                  <tr key={device.id} className="hover:bg-slate-50/50 transition">
                    <td className="px-6 py-4">
                      <div className="flex flex-col gap-1">
                        <span className="font-semibold text-slate-800">{device.device_name || 'Unnamed Device'}</span>
                        <span className="text-xs font-mono text-slate-500">{device.device_uid}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <MapPin className="w-4 h-4 text-slate-400" />
                        <span className="text-slate-600">{device.farm_name || 'Unassigned'}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        {device.connectivity_status === 'ONLINE' ? (
                          <div className="flex items-center gap-1.5 text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full text-xs font-medium">
                            <Wifi className="w-3.5 h-3.5" />
                            Online
                          </div>
                        ) : (
                          <div className="flex items-center gap-1.5 text-slate-600 bg-slate-100 px-2.5 py-1 rounded-full text-xs font-medium">
                            <WifiOff className="w-3.5 h-3.5" />
                            Offline
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      {getStatusBadge(device.device_status)}
                    </td>
                    <td className="px-6 py-4">
                      <DeviceModeControl 
                        device={device} 
                        compact={true} 
                        onModeChange={(updated) => {
                          setDevices(devices.map(d => d.id === updated.id ? { ...d, irrigation_mode: updated.irrigation_mode, last_mode_change: updated.last_mode_change } : d));
                        }} 
                      />
                    </td>
                    <td className="px-6 py-4 text-slate-500 text-sm">
                      {device.last_heartbeat ? dayjs(device.last_heartbeat).fromNow() : 'Never'}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <button 
                          onClick={() => {
                            if (device.connectivity_status === 'ONLINE' || device.status === 'online') {
                              navigate(`/farmer/devices/${device.id}?action=wifi`);
                            }
                          }}
                          disabled={!(device.connectivity_status === 'ONLINE' || device.status === 'online')}
                          className={`p-2 rounded-lg transition ${
                            (device.connectivity_status === 'ONLINE' || device.status === 'online')
                              ? 'text-slate-500 hover:text-brand hover:bg-brand/10 cursor-pointer'
                              : 'text-slate-300 cursor-not-allowed opacity-40'
                          }`}
                          title={
                            (device.connectivity_status === 'ONLINE' || device.status === 'online')
                              ? "Change Wi-Fi (Device Connected)"
                              : "Device must be connected to the website to change Wi-Fi"
                          }
                        >
                          <Wifi className="w-4 h-4" />
                        </button>
                        <button 
                          onClick={() => navigate(`/farmer/devices/${device.id}`)}
                          className="p-2 text-slate-400 hover:text-brand hover:bg-brand/5 rounded-lg transition"
                          title="View Details"
                        >
                          <Eye className="w-5 h-5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        
        {/* Pagination */}
        {!loading && devices.length > 0 && (
          <div className="p-4 border-t border-slate-200 flex items-center justify-between text-sm text-slate-500 bg-slate-50">
            <div>
              Showing {((page - 1) * limit) + 1} to {Math.min(page * limit, totalDevices)} of {totalDevices} devices
            </div>
            <div className="flex items-center gap-2">
              <button 
                disabled={page === 1}
                onClick={() => setPage(p => Math.max(1, p - 1))}
                className="p-1.5 rounded-lg border border-slate-200 hover:bg-white disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="font-medium px-2">Page {page} of {totalPages}</span>
              <button 
                disabled={page === totalPages || totalPages === 0}
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                className="p-1.5 rounded-lg border border-slate-200 hover:bg-white disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default FarmerDevices;
