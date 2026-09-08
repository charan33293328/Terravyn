import React, { useState, useEffect } from 'react';
import { Settings, Cpu, HardDrive, QrCode, Tag, CheckCircle2, AlertCircle, Download, FileText } from 'lucide-react';
import apiClient from '../../api/client';

const DeviceManufacturing = () => {
  const [formData, setFormData] = useState({
    mac_address: '',
    chip_id: '',
    product_category_id: '',
    product_category_name: '',
    custom_category: '',
    device_name: '',
    firmware_version: '1.0.0',
    hardware_version: 'REV-A',
    manufacturing_notes: ''
  });
  
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(null);

  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await apiClient.get('/admin/devices/categories');
        setCategories(response.data);
        
        // Find default category
        const defaultCat = response.data.find(c => c.name === "TERRAVYN Multi-Sensor Agriculture Device");
        if (defaultCat) {
          setFormData(prev => ({
            ...prev,
            product_category_id: defaultCat.id,
            product_category_name: defaultCat.name
          }));
        } else if (response.data.length > 0) {
          setFormData(prev => ({
            ...prev,
            product_category_id: response.data[0].id,
            product_category_name: response.data[0].name
          }));
        }
      } catch (err) {
        console.error("Failed to load categories", err);
      }
    };
    fetchCategories();
  }, []);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleCategoryChange = (e) => {
    const selectedId = parseInt(e.target.value);
    const selectedCat = categories.find(c => c.id === selectedId);
    setFormData(prev => ({
      ...prev,
      product_category_id: selectedId,
      product_category_name: selectedCat ? selectedCat.name : '',
      custom_category: selectedCat && selectedCat.name !== "TERRAVYN Other" ? '' : prev.custom_category
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess(null);
    setLoading(true);

    const macRegex = /^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$/;
    if (!macRegex.test(formData.mac_address)) {
      setError("Invalid MAC Address format. Please use XX:XX:XX:XX:XX:XX");
      setLoading(false);
      return;
    }
    
    if (formData.product_category_name === "TERRAVYN Other" && !formData.custom_category.trim()) {
      setError("Custom Product Category is required when 'TERRAVYN Other' is selected.");
      setLoading(false);
      return;
    }

    try {
      const response = await apiClient.post('/admin/devices/manufacture', formData);
      setSuccess(response.data);
      // Reset form but keep categories and versions
      setFormData(prev => ({
        ...prev,
        mac_address: '',
        chip_id: '',
        device_name: '',
        manufacturing_notes: '',
        custom_category: prev.product_category_name === "TERRAVYN Other" ? '' : prev.custom_category
      }));
    } catch (err) {
      setError(err.response?.data?.detail || "An error occurred during manufacturing registration.");
    } finally {
      setLoading(false);
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
    } catch (err) {
      alert("Unable to download QR code.");
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Device Manufacturing</h1>
        <p className="text-sm text-gray-500">Register new TERRAVYN hardware before packaging.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
            <Settings className="w-5 h-5 mr-2 text-indigo-600" />
            Hardware Identity
          </h2>
          
          {error && (
            <div className="mb-4 bg-red-50 border border-red-200 text-red-600 p-3 rounded-lg flex items-center text-sm">
              <AlertCircle className="w-4 h-4 mr-2" />
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">MAC Address *</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Tag className="h-4 w-4 text-gray-400" />
                  </div>
                  <input
                    type="text"
                    name="mac_address"
                    value={formData.mac_address}
                    onChange={handleInputChange}
                    placeholder="AA:BB:CC:DD:EE:FF"
                    className="pl-10 block w-full rounded-md border-gray-300 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm border p-2"
                    required
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Chip ID *</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Cpu className="h-4 w-4 text-gray-400" />
                  </div>
                  <input
                    type="text"
                    name="chip_id"
                    value={formData.chip_id}
                    onChange={handleInputChange}
                    placeholder="e.g. 7458c82c34c"
                    className="pl-10 block w-full rounded-md border-gray-300 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm border p-2"
                    required
                  />
                </div>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Product Category *</label>
              <select
                name="product_category_id"
                value={formData.product_category_id}
                onChange={handleCategoryChange}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm border p-2 bg-white"
                required
              >
                {categories.map(cat => (
                  <option key={cat.id} value={cat.id}>{cat.name}</option>
                ))}
              </select>
            </div>
            
            {formData.product_category_name === "TERRAVYN Other" && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Custom Product Category *</label>
                <input
                  type="text"
                  name="custom_category"
                  value={formData.custom_category}
                  onChange={handleInputChange}
                  placeholder="Enter custom category"
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm border p-2"
                  required
                />
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Firmware Version</label>
                <input
                  type="text"
                  name="firmware_version"
                  value={formData.firmware_version}
                  onChange={handleInputChange}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm border p-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Hardware Version</label>
                <input
                  type="text"
                  name="hardware_version"
                  value={formData.hardware_version}
                  onChange={handleInputChange}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm border p-2"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Optional Device Name</label>
              <input
                type="text"
                name="device_name"
                value={formData.device_name}
                onChange={handleInputChange}
                placeholder="e.g. Prototype Beta 1"
                className="block w-full rounded-md border-gray-300 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm border p-2"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Manufacturing Notes</label>
              <textarea
                name="manufacturing_notes"
                value={formData.manufacturing_notes}
                onChange={handleInputChange}
                rows="3"
                placeholder="Any special notes or observations during QC..."
                className="block w-full rounded-md border-gray-300 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm border p-2"
              />
            </div>

            <div className="pt-4 border-t border-gray-200">
              <button
                type="submit"
                disabled={loading}
                className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-400"
              >
                {loading ? 'Registering...' : 'Register New Device'}
              </button>
            </div>
          </form>
        </div>

        <div>
          {success ? (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 flex flex-col items-center text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
                <CheckCircle2 className="w-8 h-8 text-green-600" />
              </div>
              <h2 className="text-xl font-bold text-gray-800 mb-2">Device Successfully Registered</h2>
              <p className="text-gray-500 mb-6">Identity generated and saved to database.</p>
              
              <div className="bg-gray-50 rounded-lg p-4 w-full mb-6">
                <div className="grid grid-cols-2 gap-4 text-left text-sm">
                  <div>
                    <span className="block text-gray-500">Device UID</span>
                    <span className="font-mono font-medium text-gray-900">{success.device_uid}</span>
                  </div>
                  <div>
                    <span className="block text-gray-500">Activation Code</span>
                    <span className="font-mono font-medium text-gray-900">{success.activation_code}</span>
                  </div>
                  <div>
                    <span className="block text-gray-500">MAC Address</span>
                    <span className="font-mono font-medium text-gray-900">{success.mac_address}</span>
                  </div>
                  <div>
                    <span className="block text-gray-500">Status</span>
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      READY FOR SALE
                    </span>
                  </div>
                </div>
              </div>
              
              <div className="border border-gray-200 rounded-lg p-4 w-full bg-white flex flex-col items-center">
                <div className="mb-4">
                  <QrCode className="w-24 h-24 text-gray-800" />
                  <p className="text-xs text-gray-500 mt-2">QR Code Generated</p>
                </div>
                
                <div className="flex space-x-3 w-full">
                  <button 
                    onClick={() => handleDownloadQR(success.device_uid)}
                    className="flex-1 flex justify-center items-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                  >
                    <Download className="w-4 h-4 mr-2" /> Download PNG
                  </button>
                  <button 
                    className="flex-1 flex justify-center items-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                  >
                    <FileText className="w-4 h-4 mr-2" /> Print PDF
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-gray-50 rounded-lg border border-dashed border-gray-300 p-12 flex flex-col items-center justify-center h-full text-center">
              <HardDrive className="w-16 h-16 text-gray-300 mb-4" />
              <h3 className="text-lg font-medium text-gray-700 mb-2">Awaiting Device Information</h3>
              <p className="text-gray-500 text-sm max-w-md">
                Enter the MAC Address and Chip ID from the ESP32 serial output. The system will generate the secure identity and QR code needed for packaging.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DeviceManufacturing;
