import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../../api/client';
import { 
  PlusCircle, MapPin, Search, Filter, 
  Download, MoreVertical, ChevronLeft, ChevronRight, 
  Leaf, Trees, CheckCircle, AlertTriangle 
} from 'lucide-react';
import dayjs from 'dayjs';

const FarmManagement = () => {
  const navigate = useNavigate();
  const [farms, setFarms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showExportMenu, setShowExportMenu] = useState(false);
  
  // Filters & Pagination
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [cropFilter, setCropFilter] = useState('ALL');
  const [sortField, setSortField] = useState('created_at');
  const [sortDesc, setSortDesc] = useState(true);
  const [page, setPage] = useState(1);
  const limit = 10;

  useEffect(() => {
    fetchFarms();
  }, [search, statusFilter, cropFilter, sortField, sortDesc, page]);

  const fetchFarms = async () => {
    try {
      setLoading(true);
      let url = `/farmer/farms?limit=${limit}&offset=${(page - 1) * limit}&sort_by=${sortField}&sort_desc=${sortDesc}`;
      if (search) url += `&search=${search}`;
      if (statusFilter !== 'ALL') url += `&status=${statusFilter}`;
      if (cropFilter !== 'ALL') url += `&crop_type=${cropFilter}`;

      const res = await apiClient.get(url);
      setFarms(res.data);
    } catch (error) {
      console.error('Failed to fetch farms:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format) => {
    setShowExportMenu(false);
    try {
      let url = `/farmer/farms/export?format=${format}`;
      if (search) url += `&search=${search}`;
      if (statusFilter !== 'ALL') url += `&status=${statusFilter}`;
      if (cropFilter !== 'ALL') url += `&crop_type=${cropFilter}`;

      const res = await apiClient.get(url, { responseType: 'blob' });
      
      const blob = new Blob([res.data], { 
        type: format === 'csv' ? 'text/csv' : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
      });
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      
      const timestamp = dayjs().format('YYYYMMDD_HHmmss');
      link.download = `terravyn_farms_${timestamp}.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error('Export failed:', error);
      alert('Failed to export farms');
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'ACTIVE': return <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-medium">Active</span>;
      case 'INACTIVE': return <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs font-medium">Inactive</span>;
      case 'HARVESTED': return <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-medium">Harvested</span>;
      case 'UNDER_PREPARATION': return <span className="px-2 py-1 bg-orange-100 text-orange-700 rounded text-xs font-medium">Under Preparation</span>;
      default: return <span className="px-2 py-1 bg-slate-100 text-slate-700 rounded text-xs font-medium">{status}</span>;
    }
  };

  const cropTypes = ['Rice', 'Wheat', 'Cotton', 'Maize', 'Sugarcane', 'Groundnut', 'Tomato', 'Chili', 'Banana', 'Mango', 'Other'];

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:justify-between md:items-start gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Farm Management</h1>
          <p className="text-slate-500">Manage your farms, organize devices, and monitor agricultural operations efficiently.</p>
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
            onClick={() => navigate('/farmer/farms/new')}
            className="px-4 py-2 bg-brand text-white rounded-lg hover:bg-brand/90 transition flex items-center gap-2 shadow-sm"
          >
            <PlusCircle className="w-5 h-5" />
            Add New Farm
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
              placeholder="Search by farm name, location..." 
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand/50"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5 text-slate-400" />
            <select 
              value={statusFilter} 
              onChange={(e) => setStatusFilter(e.target.value)}
              className="border border-slate-200 rounded-lg px-3 py-2 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand/50"
            >
              <option value="ALL">All Statuses</option>
              <option value="ACTIVE">Active</option>
              <option value="INACTIVE">Inactive</option>
              <option value="HARVESTED">Harvested</option>
              <option value="UNDER_PREPARATION">Under Preparation</option>
            </select>
            <select 
              value={cropFilter} 
              onChange={(e) => setCropFilter(e.target.value)}
              className="border border-slate-200 rounded-lg px-3 py-2 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand/50"
            >
              <option value="ALL">All Crops</option>
              {cropTypes.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
            <select 
              value={`${sortField}-${sortDesc}`}
              onChange={(e) => {
                const [field, desc] = e.target.value.split('-');
                setSortField(field);
                setSortDesc(desc === 'true');
              }}
              className="border border-slate-200 rounded-lg px-3 py-2 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand/50"
            >
              <option value="created_at-true">Newest First</option>
              <option value="created_at-false">Oldest First</option>
              <option value="name-false">Name (A-Z)</option>
              <option value="name-true">Name (Z-A)</option>
              <option value="area-true">Largest Area</option>
            </select>
          </div>
        </div>
      </div>

      {/* Farms Grid */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand"></div>
        </div>
      ) : farms.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
          <div className="w-16 h-16 bg-brand/10 text-brand rounded-full flex items-center justify-center mx-auto mb-4">
            <Trees className="w-8 h-8" />
          </div>
          <h3 className="text-xl font-bold text-slate-800 mb-2">No farms added yet</h3>
          <p className="text-slate-500 mb-6 max-w-md mx-auto">Create your first farm to organize your TERRAVYN devices and begin precision farming.</p>
          <button 
            onClick={() => navigate('/farmer/farms/new')}
            className="px-6 py-2 bg-brand text-white rounded-lg hover:bg-brand/90 transition"
          >
            Add New Farm
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {farms.map((farm) => (
            <div key={farm.id} className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm hover:shadow-md transition">
              <div className="p-5 border-b border-slate-100 flex justify-between items-start">
                <div>
                  <h3 className="text-lg font-bold text-slate-800 truncate">{farm.name}</h3>
                  <div className="flex items-center gap-1 text-sm text-slate-500 mt-1">
                    <MapPin className="w-3 h-3" />
                    <span>{[farm.village, farm.district, farm.state].filter(Boolean).join(', ') || 'No location set'}</span>
                  </div>
                </div>
                {getStatusBadge(farm.status)}
              </div>
              <div className="p-5 bg-slate-50/50 space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs text-slate-500 mb-1">Crop Type</p>
                    <p className="font-medium text-slate-800 flex items-center gap-1">
                      <Leaf className="w-4 h-4 text-brand" />
                      {farm.crop_type || 'N/A'}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-500 mb-1">Total Area</p>
                    <p className="font-medium text-slate-800">
                      {farm.area ? `${farm.area} ${farm.area_unit}` : 'N/A'}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-500 mb-1">Linked Devices</p>
                    <p className="font-medium text-slate-800">{farm.device_count || 0}</p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-500 mb-1">Created Date</p>
                    <p className="font-medium text-slate-800">{dayjs(farm.created_at).format('MMM D, YYYY')}</p>
                  </div>
                </div>
              </div>
              <div className="p-4 border-t border-slate-100 flex gap-2">
                <button 
                  onClick={() => navigate(`/farmer/farms/${farm.id}`)}
                  className="flex-1 px-4 py-2 bg-brand/10 text-brand rounded-lg hover:bg-brand/20 transition text-sm font-medium"
                >
                  View Details
                </button>
                <button 
                  onClick={() => navigate(`/farmer/farms/${farm.id}/edit`)}
                  className="flex-1 px-4 py-2 border border-slate-200 text-slate-700 rounded-lg hover:bg-slate-50 transition text-sm font-medium"
                >
                  Edit Farm
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {farms.length > 0 && (
        <div className="flex items-center justify-between border-t border-slate-200 pt-4 mt-6">
          <p className="text-sm text-slate-500">
            Showing page {page}
          </p>
          <div className="flex gap-2">
            <button 
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="p-2 border border-slate-200 rounded-lg hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <button 
              onClick={() => setPage(p => p + 1)}
              disabled={farms.length < limit}
              className="p-2 border border-slate-200 rounded-lg hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default FarmManagement;
