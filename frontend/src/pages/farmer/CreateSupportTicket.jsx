import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, UploadCloud, X, AlertCircle, CheckCircle2 } from 'lucide-react';
import client from '../../api/client';

export default function CreateSupportTicket() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  
  // Form State
  const [subject, setSubject] = useState('');
  const [category, setCategory] = useState('General Inquiry');
  const [priority, setPriority] = useState('NORMAL');
  const [description, setDescription] = useState('');
  
  // Relations
  const [devices, setDevices] = useState([]);
  const [farms, setFarms] = useState([]);
  const [orders, setOrders] = useState([]);
  
  const [selectedDevice, setSelectedDevice] = useState('');
  const [selectedFarm, setSelectedFarm] = useState('');
  const [selectedOrder, setSelectedOrder] = useState('');
  
  // Files
  const [files, setFiles] = useState([]);

  useEffect(() => {
    const fetchRelations = async () => {
      try {
        const [devRes, farmRes, orderRes] = await Promise.all([
          client.get('/farmer/devices'),
          client.get('/farmer/farms'),
          client.get('/farmer/orders')
        ]);
        setDevices(devRes.data.devices || []);
        setFarms(farmRes.data || []);
        setOrders(orderRes.data.items || []);
      } catch (err) {
        console.error("Failed to fetch relational data", err);
      }
    };
    fetchRelations();
  }, []);

  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files);
    if (files.length + selectedFiles.length > 5) {
      setError("You can only upload a maximum of 5 files.");
      return;
    }
    
    const validFiles = [];
    const allowedTypes = ['image/jpeg', 'image/png', 'application/pdf'];
    const maxSize = 10 * 1024 * 1024; // 10MB
    
    for (let f of selectedFiles) {
      if (!allowedTypes.includes(f.type)) {
        setError(`File ${f.name} is not a supported format (JPG, PNG, PDF only).`);
        continue;
      }
      if (f.size > maxSize) {
        setError(`File ${f.name} exceeds the 10MB limit.`);
        continue;
      }
      validFiles.push(f);
    }
    
    if (validFiles.length > 0) {
      setFiles([...files, ...validFiles]);
      setError(null);
    }
  };

  const removeFile = (index) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!subject || !description) {
      setError("Subject and Description are required.");
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('subject', subject);
    formData.append('description', description);
    formData.append('category', category);
    formData.append('priority', priority);
    
    if (selectedDevice) formData.append('device_id', selectedDevice);
    if (selectedFarm) formData.append('farm_id', selectedFarm);
    if (selectedOrder) formData.append('order_id', selectedOrder);
    
    files.forEach(f => {
      formData.append('files', f);
    });

    try {
      const response = await client.post('/farmer/support/tickets', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      setSuccess(true);
      setTimeout(() => {
        navigate(`/farmer/support/${response.data.id}`);
      }, 1500);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || "Failed to create support ticket. Please try again.");
      setLoading(false);
    }
  };

  const categories = [
    "Device Activation Issue",
    "Device Connectivity Issue",
    "Sensor Data Issue",
    "Monitoring Center Issue",
    "Alert Issue",
    "Order Issue",
    "Return / Refund Issue",
    "Billing Issue",
    "Account Issue",
    "Feature Request",
    "General Inquiry",
    "Other"
  ];

  if (success) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
          <CheckCircle2 className="w-8 h-8 text-green-600" />
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Ticket Created Successfully!</h2>
        <p className="text-gray-500 max-w-md">
          Your support request has been submitted. Our team will review it and get back to you shortly. You are being redirected to the ticket...
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center space-x-4">
        <button 
          onClick={() => navigate('/farmer/support')}
          className="p-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 text-gray-600 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Create Support Ticket</h1>
          <p className="text-sm text-gray-500">Provide details about your issue so we can help you faster.</p>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl flex items-start">
          <AlertCircle className="w-5 h-5 text-red-600 mr-3 mt-0.5 flex-shrink-0" />
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="p-6 space-y-6">
          
          {/* Basic Info */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 border-b pb-2">Ticket Information</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Subject <span className="text-red-500">*</span></label>
                <input
                  type="text"
                  required
                  value={subject}
                  onChange={e => setSubject(e.target.value)}
                  placeholder="Brief summary of the issue"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Category <span className="text-red-500">*</span></label>
                <select
                  value={category}
                  onChange={e => setCategory(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm bg-white"
                >
                  {categories.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
                <select
                  value={priority}
                  onChange={e => setPriority(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm bg-white"
                >
                  <option value="LOW">Low</option>
                  <option value="NORMAL">Medium</option>
                  <option value="HIGH">High</option>
                  <option value="CRITICAL">Critical</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Description <span className="text-red-500">*</span></label>
              <textarea
                required
                rows="5"
                value={description}
                onChange={e => setDescription(e.target.value)}
                placeholder="Please describe your issue in detail. Include any error messages or steps to reproduce the problem."
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm resize-none"
              ></textarea>
            </div>
          </div>

          {/* Relations */}
          <div className="space-y-4 pt-4 border-t border-gray-100">
            <h3 className="text-lg font-semibold text-gray-900 border-b pb-2">Related Items (Optional)</h3>
            <p className="text-xs text-gray-500 -mt-2">Link this ticket to specific items to help us resolve it faster.</p>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Related Device</label>
                <select
                  value={selectedDevice}
                  onChange={e => setSelectedDevice(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm bg-white"
                >
                  <option value="">None</option>
                  {devices.map(d => <option key={d.id} value={d.id}>{d.name || d.device_uid}</option>)}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Related Farm</label>
                <select
                  value={selectedFarm}
                  onChange={e => setSelectedFarm(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm bg-white"
                >
                  <option value="">None</option>
                  {farms.map(f => <option key={f.id} value={f.id}>{f.name}</option>)}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Related Order</label>
                <select
                  value={selectedOrder}
                  onChange={e => setSelectedOrder(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm bg-white"
                >
                  <option value="">None</option>
                  {orders.map(o => <option key={o.order_id} value={o.order_id}>{o.order_id}</option>)}
                </select>
              </div>
            </div>
          </div>

          {/* Attachments */}
          <div className="space-y-4 pt-4 border-t border-gray-100">
            <div className="flex justify-between items-center border-b pb-2">
              <h3 className="text-lg font-semibold text-gray-900">Attachments</h3>
              <span className="text-xs text-gray-500">{files.length} / 5 files</span>
            </div>
            
            <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:bg-gray-50 transition-colors">
              <input
                type="file"
                multiple
                accept="image/jpeg,image/png,application/pdf"
                onChange={handleFileChange}
                className="hidden"
                id="file-upload"
                disabled={files.length >= 5}
              />
              <label htmlFor="file-upload" className={`cursor-pointer flex flex-col items-center ${files.length >= 5 ? 'opacity-50 cursor-not-allowed' : ''}`}>
                <UploadCloud className="w-10 h-10 text-green-500 mb-3" />
                <span className="text-sm font-medium text-gray-900">Click to upload or drag and drop</span>
                <span className="text-xs text-gray-500 mt-1">JPG, PNG or PDF (max. 10MB)</span>
              </label>
            </div>

            {files.length > 0 && (
              <div className="space-y-2 mt-4">
                {files.map((file, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200">
                    <div className="flex items-center min-w-0">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">{file.name}</p>
                        <p className="text-xs text-gray-500">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => removeFile(idx)}
                      className="p-1 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
          
        </div>
        
        <div className="p-6 bg-gray-50 border-t border-gray-100 flex justify-end gap-3">
          <button
            type="button"
            onClick={() => navigate('/farmer/support')}
            className="px-6 py-2 border border-gray-300 bg-white text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50 transition-colors"
            disabled={loading}
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 flex items-center"
          >
            {loading ? 'Submitting...' : 'Submit Ticket'}
          </button>
        </div>
      </form>
    </div>
  );
}
