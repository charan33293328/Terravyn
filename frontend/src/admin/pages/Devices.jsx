import React, { useState, useEffect } from 'react';
import { Search, Plus, Filter, QrCode, Server, Trash2, Edit, ChevronLeft, ChevronRight, Activity, Zap, CheckCircle2 } from 'lucide-react';
import { Link } from 'react-router-dom';
import apiClient from '../../api/client';
import AssignFarmerModal from '../components/AssignFarmerModal';

const Devices = () => {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creating, setCreating] = useState(false);
  const [createSuccess, setCreateSuccess] = useState(null);

  const [isAssignModalOpen, setIsAssignModalOpen] = useState(false);
  const [deviceToAssign, setDeviceToAssign] = useState(null);

  const limit = 10;

  const fetchDevices = async () => {
    setLoading(true);
    try {
      const skip = (page - 1) * limit;
      let url = `/admin/devices/?skip=${skip}&limit=${limit}`;
      if (search) url += `&search=${search}`;
      if (statusFilter) url += `&device_status=${statusFilter}`;
      
      const response = await apiClient.get(url);
      setDevices(response.data.items);
      setTotal(response.data.total);
    } catch (error) {
      console.error("Failed to fetch devices", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDevices();
    const interval = setInterval(() => {
      fetchDevices();
    }, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [page, search, statusFilter]);

  const handleProvisionDevice = async (macAddress) => {
    setCreating(true);
    try {
      await apiClient.post(`/admin/devices/${macAddress}/provision`);
      fetchDevices();
    } catch (error) {
      console.error("Failed to provision device", error);
      alert(error.response?.data?.detail || "Failed to provision device");
    } finally {
      setCreating(false);
    }
  };

  const handleDownloadQR = async (deviceUid) => {
    try {
      const res = await apiClient.get(`/admin/devices/${deviceUid}/download-qr`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${deviceUid}.png`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);
      alert("QR code downloaded successfully.");
    } catch (err) {
      if (err.response?.status === 404) {
        alert("Device not found.");
      } else {
        alert("Unable to download QR code.");
      }
    }
  };

  const handleDeleteDevice = async (identifier) => {
    if (!window.confirm("CRITICAL: Are you absolutely sure you want to permanently delete this device? This cannot be undone.")) return;
    try {
      await apiClient.delete(`/admin/devices/${identifier}`);
      fetchDevices();
    } catch (error) {
      alert("Failed to delete device. You might not have Super Admin permissions.");
    }
  };



  const isOnline = (lastHeartbeat) => {
    if (!lastHeartbeat) return false;
    // Ensure the UTC timestamp from the backend is parsed correctly by adding 'Z' if missing
    const heartbeatStr = lastHeartbeat.endsWith('Z') ? lastHeartbeat : lastHeartbeat + 'Z';
    const diff = (new Date() - new Date(heartbeatStr)) / 1000;
    return diff <= 60;
  };

  const counts = {
    ready: devices.filter(d => d.device_status === 'READY_FOR_SALE').length,
    assigned: devices.filter(d => d.device_status === 'ASSIGNED').length,
    active: devices.filter(d => d.device_status === 'ACTIVE').length,
    inactive: devices.filter(d => ['INACTIVE', 'MAINTENANCE'].includes(d.device_status)).length,
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'ACTIVE': return 'bg-emerald-100 text-emerald-700';
      case 'INACTIVE': return 'bg-rose-100 text-rose-700';
      case 'MAINTENANCE': return 'bg-amber-100 text-amber-700';
      case 'ASSIGNED': return 'bg-indigo-100 text-indigo-700';
      default: return 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200';
    }
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <div className="space-y-6">
      
      {/* HEADER & ACTIONS */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white dark:bg-slate-900 p-5 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-800/50">
        <div>
          <h1 className="text-xl font-black text-slate-900 dark:text-white">Device Fleet</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 font-medium">Manage and provision {total} IoT devices</p>
        </div>
        <div className="flex gap-3">
          <button onClick={() => fetchDevices()} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-300 px-4 py-2 rounded-xl font-bold text-sm transition-colors hover:bg-slate-50 dark:bg-slate-950">
            Refresh
          </button>
        </div>
      </div>

      {/* COUNTERS */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-800/50 flex flex-col items-center justify-center">
          <span className="text-3xl font-black text-amber-500">{counts.ready}</span>
          <span className="text-xs font-bold text-slate-400 uppercase tracking-widest mt-1">Ready for Sale</span>
        </div>
        <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-800/50 flex flex-col items-center justify-center">
          <span className="text-3xl font-black text-blue-500">{counts.assigned}</span>
          <span className="text-xs font-bold text-slate-400 uppercase tracking-widest mt-1">Assigned</span>
        </div>
        <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-800/50 flex flex-col items-center justify-center">
          <span className="text-3xl font-black text-emerald-500">{counts.active}</span>
          <span className="text-xs font-bold text-slate-400 uppercase tracking-widest mt-1">Active</span>
        </div>
        <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-800/50 flex flex-col items-center justify-center">
          <span className="text-3xl font-black text-rose-500">{counts.inactive}</span>
          <span className="text-xs font-bold text-slate-400 uppercase tracking-widest mt-1">Inactive</span>
        </div>
      </div>

      {/* FILTERS */}
      <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-800/50 flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
          <input 
            type="text" 
            placeholder="Search UID, Activation Code, MAC or Farmer..." 
            className="w-full pl-10 pr-4 py-2 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl text-sm focus:ring-2 focus:ring-brand/20 focus:border-brand outline-none transition-all"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="text-slate-400" size={18} />
          <select 
            className="bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl text-sm px-4 py-2 focus:ring-2 focus:ring-brand/20 focus:border-brand outline-none"
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          >
            <option value="">All Statuses</option>
            <option value="READY_FOR_SALE">Ready For Sale</option>
            <option value="ASSIGNED">Assigned</option>
            <option value="ACTIVE">Active</option>
            <option value="MAINTENANCE">Maintenance</option>
            <option value="INACTIVE">Inactive</option>
          </select>
        </div>
      </div>

      {/* TABLE */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-800/50 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 dark:bg-slate-950/50 border-b border-slate-100 dark:border-slate-800/50">
                <th className="px-6 py-4 text-xs font-black text-slate-500 dark:text-slate-400 uppercase tracking-widest">Device UID / MAC</th>
                <th className="px-6 py-4 text-xs font-black text-slate-500 dark:text-slate-400 uppercase tracking-widest">Product & FW</th>
                <th className="px-6 py-4 text-xs font-black text-slate-500 dark:text-slate-400 uppercase tracking-widest">Status</th>
                <th className="px-6 py-4 text-xs font-black text-slate-500 dark:text-slate-400 uppercase tracking-widest">Last Seen</th>
                <th className="px-6 py-4 text-xs font-black text-slate-500 dark:text-slate-400 uppercase tracking-widest text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/50">
              {loading ? (
                <tr><td colSpan="7" className="p-8 text-center text-slate-400">Loading devices...</td></tr>
              ) : devices.length === 0 ? (
                <tr>
                  <td colSpan="7" className="p-12">
                    <div className="text-center bg-slate-50 dark:bg-slate-950 py-12 rounded-xl border border-dashed border-slate-200 dark:border-slate-800 max-w-lg mx-auto">
                      <Server className="mx-auto text-slate-300 mb-4" size={48} />
                      <h3 className="text-lg font-bold text-slate-700 dark:text-slate-200">No ESP32 devices have registered yet.</h3>
                      <p className="text-slate-500 dark:text-slate-400 mt-2 text-sm px-6">
                        Power on your real ESP32 hardware and ensure it connects to the Admin WiFi to automatically register in this list.
                      </p>
                    </div>
                  </td>
                </tr>
              ) : (
                devices.map(device => (
                  <tr key={device.id} className="hover:bg-slate-50 dark:bg-slate-950/50 transition-colors group">
                    <td className="px-6 py-4">
                      <div className="font-bold text-slate-900 dark:text-white text-sm">{device.device_uid || 'Unprovisioned'}</div>
                      <div className="text-xs font-mono text-slate-500 mt-1">{device.mac_address || '---'}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-slate-800 dark:text-slate-200">{device.product_category_name || 'N/A'}</div>
                      <div className="text-xs text-slate-500 mt-1">FW: {device.firmware_version || '---'} | Chip: {device.chip_id || '---'}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex flex-col gap-1 items-start">
                        <span className={`px-2.5 py-1 text-[10px] font-black uppercase tracking-widest rounded-full ${getStatusColor(device.device_status)}`}>
                          {device.device_status ? device.device_status.replace(/_/g, ' ') : 'UNKNOWN'}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2.5 py-1 text-[10px] font-black uppercase tracking-widest rounded-full ${isOnline(device.last_heartbeat) ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'}`}>
                        {isOnline(device.last_heartbeat) ? 'ONLINE' : 'OFFLINE'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right flex items-center justify-end gap-2 flex-wrap">
                      
                      {device.device_uid && (
                        <button onClick={() => handleDownloadQR(device.device_uid)} className="px-3 py-1.5 bg-slate-800 text-white rounded-lg text-xs font-bold hover:bg-slate-900 transition-all">Download QR</button>
                      )}
                      
                      {device.device_status === 'READY_FOR_SALE' && (
                        <button onClick={() => { setDeviceToAssign(device); setIsAssignModalOpen(true); }} className="px-3 py-1.5 bg-brand text-white border border-brand-dark rounded-lg text-xs font-bold hover:bg-brand-dark transition-all">Assign Farmer</button>
                      )}

                      {device.device_uid && (
                        <Link to={`/admin/devices/${device.device_uid}`} className="px-3 py-1.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg text-xs font-bold text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:text-white transition-all">View Details</Link>
                      )}

                      <button onClick={() => handleDeleteDevice(device.device_uid || device.mac_address)} className="px-3 py-1.5 bg-rose-50 border border-rose-200 text-rose-600 rounded-lg text-xs font-bold hover:bg-rose-100 transition-all">Delete</button>

                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        
        {/* PAGINATION */}
        {!loading && totalPages > 1 && (
          <div className="px-6 py-4 border-t border-slate-100 dark:border-slate-800/50 flex items-center justify-between">
            <span className="text-sm text-slate-500 dark:text-slate-400 font-medium">
              Showing {((page - 1) * limit) + 1} to {Math.min(page * limit, total)} of {total} entries
            </span>
            <div className="flex gap-2">
              <button 
                disabled={page === 1}
                onClick={() => setPage(p => p - 1)}
                className="p-1.5 rounded-lg border border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 disabled:opacity-50 hover:bg-slate-50 dark:bg-slate-950"
              >
                <ChevronLeft size={18} />
              </button>
              <button 
                disabled={page === totalPages}
                onClick={() => setPage(p => p + 1)}
                className="p-1.5 rounded-lg border border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 disabled:opacity-50 hover:bg-slate-50 dark:bg-slate-950"
              >
                <ChevronRight size={18} />
              </button>
            </div>
          </div>
        )}
      </div>

      <AssignFarmerModal
        isOpen={isAssignModalOpen}
        onClose={() => setIsAssignModalOpen(false)}
        device={deviceToAssign}
        onSuccess={() => {
          fetchDevices();
        }}
      />
    </div>
  );
};

export default Devices;
