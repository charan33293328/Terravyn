import React, { useState, useEffect } from 'react';
import { X, Search, CheckCircle2, User, Phone, MapPin } from 'lucide-react';
import axios from 'axios';

const AssignFarmerModal = ({ isOpen, onClose, device, onSuccess }) => {
  const [farmers, setFarmers] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [assigning, setAssigning] = useState(false);
  const [selectedFarmer, setSelectedFarmer] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen) {
      fetchFarmers();
    } else {
      // Reset state on close
      setSearchQuery('');
      setSelectedFarmer(null);
      setError(null);
    }
  }, [isOpen, searchQuery]);

  const fetchFarmers = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('/api/admin/farmers', {
        headers: { Authorization: `Bearer ${token}` },
        params: { search: searchQuery, limit: 10 }
      });
      setFarmers(response.data.items);
    } catch (err) {
      console.error("Failed to fetch farmers", err);
    } finally {
      setLoading(false);
    }
  };

  const handleAssign = async () => {
    if (!selectedFarmer || !device) return;
    
    setAssigning(true);
    setError(null);
    
    try {
      const token = localStorage.getItem('token');
      await axios.put(`/api/admin/devices/${device.device_uid}/assign`, {
        farmer_id: selectedFarmer.id
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      onSuccess();
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to assign device");
    } finally {
      setAssigning(false);
    }
  };

  if (!isOpen || !device) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm">
      <div className="bg-white dark:bg-slate-900 rounded-2xl w-full max-w-2xl max-h-[90vh] flex flex-col shadow-2xl">
        <div className="flex-shrink-0 border-b border-slate-100 dark:border-slate-800/50 px-6 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-slate-800 dark:text-slate-100">Assign Device</h2>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Select a farmer to assign {device.device_uid}</p>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-slate-100 dark:bg-slate-800 rounded-lg text-slate-500 dark:text-slate-400 transition-colors">
            <X size={20} />
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {error && (
            <div className="p-4 bg-red-50 text-red-600 rounded-xl text-sm border border-red-100">
              {error}
            </div>
          )}
          
          {/* Search Bar */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Search farmers by name, phone, or village..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-3 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl focus:ring-2 focus:ring-brand focus:border-brand outline-none transition-all"
            />
          </div>

          {/* Farmer List */}
          <div className="space-y-3">
            {loading ? (
              <div className="flex justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand"></div>
              </div>
            ) : farmers.length === 0 ? (
              <div className="text-center py-8 text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-950 rounded-xl border border-dashed border-slate-200 dark:border-slate-800">
                No farmers found matching "{searchQuery}"
              </div>
            ) : (
              farmers.map((farmer) => (
                <div 
                  key={farmer.id}
                  onClick={() => setSelectedFarmer(farmer)}
                  className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
                    selectedFarmer?.id === farmer.id 
                      ? 'border-brand bg-brand/5 shadow-sm' 
                      : 'border-slate-100 dark:border-slate-800/50 hover:border-slate-300 hover:bg-slate-50 dark:bg-slate-950'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-semibold text-slate-800 dark:text-slate-100 flex items-center gap-2">
                        {farmer.full_name}
                        {farmer.status === 'ACTIVE' ? (
                          <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 text-[10px] font-bold uppercase tracking-wide">
                            Active
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 text-[10px] font-bold uppercase tracking-wide">
                            Inactive
                          </span>
                        )}
                      </h4>
                      <div className="flex items-center gap-4 mt-2 text-sm text-slate-500 dark:text-slate-400">
                        <span className="flex items-center gap-1.5"><Phone size={14} /> {farmer.phone}</span>
                        <span className="flex items-center gap-1.5"><MapPin size={14} /> {farmer.village || farmer.address}</span>
                      </div>
                    </div>
                    {selectedFarmer?.id === farmer.id && (
                      <CheckCircle2 className="text-brand w-6 h-6" />
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
        
        <div className="flex-shrink-0 border-t border-slate-100 dark:border-slate-800/50 p-6 flex justify-end gap-3 bg-slate-50 dark:bg-slate-950 rounded-b-2xl">
          <button
            type="button"
            onClick={onClose}
            className="px-6 py-2.5 text-sm font-medium text-slate-600 dark:text-slate-300 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:bg-slate-800 rounded-xl transition-colors"
          >
            Cancel
          </button>
          <button
            type="button"
            disabled={!selectedFarmer || assigning}
            onClick={handleAssign}
            className="px-6 py-2.5 text-sm font-medium text-white bg-brand hover:bg-brand-dark rounded-xl transition-colors shadow-lg shadow-brand/20 disabled:opacity-50 flex items-center gap-2"
          >
            {assigning ? (
              <>
                <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
                Assigning...
              </>
            ) : (
              'Confirm Assignment'
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default AssignFarmerModal;
