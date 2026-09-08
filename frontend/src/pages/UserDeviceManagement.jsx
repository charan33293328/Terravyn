import React, { useState, useEffect } from 'react';
import { Plus, Edit2, Cpu, CheckCircle, XCircle, AlertCircle, Edit3, Loader2 } from 'lucide-react';
import { Scanner } from '@yudiel/react-qr-scanner';
import apiClient from '../api/client';
import { useNavigate } from 'react-router-dom';

const UserDeviceManagement = () => {
  const navigate = useNavigate();
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Claiming Modal state
  const [showClaimModal, setShowClaimModal] = useState(false);
  const [step, setStep] = useState('SCAN'); // 'SCAN', 'FORM', 'SUCCESS'
  const [activationMethod, setActivationMethod] = useState('QR'); // 'QR' or 'MANUAL'
  const [claimError, setClaimError] = useState('');
  const [submitLoading, setSubmitLoading] = useState(false);
  const [cameraError, setCameraError] = useState(false);

  // Form Data
  const [uid, setUid] = useState('');
  const [code, setCode] = useState('');
  const [deviceName, setDeviceName] = useState('');
  const [farmId, setFarmId] = useState('');
  const [location, setLocation] = useState('');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);

  // Farms Data
  const [farms, setFarms] = useState([]);
  const [isCreatingFarm, setIsCreatingFarm] = useState(false);
  const [newFarmName, setNewFarmName] = useState('');
  const [creatingFarm, setCreatingFarm] = useState(false);

  useEffect(() => {
    fetchDevices(false);
    fetchFarms();
    
    const interval = setInterval(() => {
      fetchDevices(true);
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const fetchDevices = async (isPolling = false) => {
    if (!isPolling) setLoading(true);
    try {
      const res = await apiClient.get('/user/devices');
      setDevices(res.data);
    } catch (err) {
      console.error("Failed to fetch user devices", err);
    } finally {
      if (!isPolling) setLoading(false);
    }
  };

  const formatLastSeen = (timestamp) => {
    if (!timestamp) return 'Never Connected';
    const seconds = Math.floor((new Date() - new Date(timestamp + 'Z')) / 1000); // ensure UTC parsing if needed, but ISO should have Z
    // if timestamp doesn't have Z, we enforce it
    const dateStr = timestamp.endsWith('Z') ? timestamp : timestamp + 'Z';
    const secs = Math.floor((new Date() - new Date(dateStr)) / 1000);
    const diff = secs >= 0 ? secs : 0;
    
    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)} minutes ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)} hours ago`;
    return `${Math.floor(diff / 86400)} days ago`;
  };

  const fetchFarms = async () => {
    try {
      const res = await apiClient.get('/farmer/farms');
      setFarms(res.data);
      if (res.data.length > 0) {
        setFarmId(res.data[0].id.toString());
      }
    } catch (err) {
      console.error("Failed to fetch farms", err);
    }
  };

  const openClaimModal = () => {
    setShowClaimModal(true);
    setStep('SCAN');
    setActivationMethod('QR');
    setClaimError('');
    setUid('');
    setCode('');
    setDeviceName('');
    setLocation('');
    setDate(new Date().toISOString().split('T')[0]);
    if (farms.length > 0) {
      setFarmId(farms[0].id.toString());
    } else {
      setFarmId('');
    }
    setIsCreatingFarm(false);
  };

  const closeClaimModal = () => {
    setShowClaimModal(false);
  };

  const handleScan = (detectedCodes) => {
    if (detectedCodes && detectedCodes.length > 0 && step === 'SCAN') {
      const result = detectedCodes[0].rawValue;
      
      let parsedUid = null;
      let parsedCode = null;

      try {
        if (result.trim().startsWith('{')) {
          const payload = JSON.parse(result);
          parsedUid = payload.device_uid;
          parsedCode = payload.activation_code;
        } else if (result.includes('UID:') && result.includes('CODE:')) {
          const parts = result.split('|');
          parts.forEach(part => {
            if (part.startsWith('UID:')) parsedUid = part.substring(4);
            if (part.startsWith('CODE:')) parsedCode = part.substring(5);
          });
        }
        
        if (parsedUid && parsedCode) {
          setUid(parsedUid);
          setCode(parsedCode);
          setActivationMethod('QR');
          setStep('FORM');
          setClaimError('');
        } else {
          setClaimError('Invalid TERRAVYN QR Code. Please scan again.');
        }
      } catch (e) {
        setClaimError('Invalid TERRAVYN QR Code. Please scan again.');
      }
    }
  };

  const switchToManual = () => {
    setActivationMethod('MANUAL');
    setStep('FORM');
    setClaimError('');
    setCameraError(false);
  };

  const handleCreateFarm = async (e) => {
    e.preventDefault();
    if (!newFarmName.trim()) return;
    setCreatingFarm(true);
    try {
      const res = await apiClient.post('/farmer/farms', { name: newFarmName });
      setFarms([...farms, res.data]);
      setFarmId(res.data.id.toString());
      setIsCreatingFarm(false);
      setNewFarmName('');
    } catch (err) {
      console.error("Failed to create farm", err);
    } finally {
      setCreatingFarm(false);
    }
  };

  const handleClaimSubmit = async (e) => {
    e.preventDefault();
    if (submitLoading) return;
    
    if (!uid || !code || !deviceName || !farmId) {
      setClaimError('Please fill in all required fields.');
      return;
    }

    setSubmitLoading(true);
    setClaimError('');

    try {
      await apiClient.post('/farmer/devices/link', {
        device_uid: uid,
        activation_code: code,
        device_name: deviceName,
        farm_id: parseInt(farmId),
        installation_location: location,
        installation_date: new Date(date).toISOString(),
        activation_method: activationMethod
      });
      setStep('SUCCESS');
      fetchDevices();
    } catch (err) {
      setClaimError(err.response?.data?.detail || 'Activation failed. Please try again.');
    } finally {
      setSubmitLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-slate-800">My Devices</h2>
          <p className="text-slate-500">Manage your claimed smart hardware and sensors.</p>
        </div>
        <button 
          onClick={openClaimModal}
          className="flex items-center gap-2 px-4 py-2 bg-brand text-white rounded-lg shadow-sm hover:bg-brand-dark transition-colors font-medium text-sm"
        >
          <Plus className="w-4 h-4"/> Claim New Device
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <table className="min-w-full divide-y divide-slate-200">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Device Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Farm Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Connectivity Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Last Seen</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-slate-200">
            {loading && devices.length === 0 ? (
              <tr><td colSpan="5" className="px-6 py-4 text-center text-slate-500">Loading devices...</td></tr>
            ) : devices.length === 0 ? (
              <tr><td colSpan="5" className="px-6 py-4 text-center text-slate-500">You haven't claimed any devices yet.</td></tr>
            ) : devices.map(device => (
              <tr key={device.id}>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center">
                      <Cpu className="w-4 h-4 text-slate-600" />
                    </div>
                    <div>
                      <span className="block text-sm font-medium text-slate-900">{device.name || 'Unnamed Device'}</span>
                      <span className="block text-xs font-mono text-slate-500">{device.device_uid}</span>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">{device.farm_name || 'Unassigned'}</td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${device.connectivity_status === 'ONLINE' ? 'bg-emerald-100 text-emerald-800' : device.connectivity_status === 'OFFLINE' ? 'bg-red-100 text-red-800' : 'bg-slate-100 text-slate-800'}`}>
                    {device.connectivity_status}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
                  {formatLastSeen(device.last_heartbeat)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <button className="text-brand hover:text-brand-dark mr-3"><Edit2 className="w-4 h-4" /></button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showClaimModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 overflow-y-auto">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg overflow-hidden flex flex-col max-h-[90vh]">
            
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50 shrink-0">
              <h3 className="text-lg font-bold text-slate-800">
                {step === 'SCAN' && 'Scan QR Code'}
                {step === 'FORM' && 'Device Details'}
                {step === 'SUCCESS' && 'Success'}
              </h3>
              <button 
                onClick={closeClaimModal}
                className="text-slate-400 hover:text-slate-600"
              >
                <XCircle className="w-6 h-6" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto flex-1">
              
              {claimError && (
                <div className="mb-6 p-4 bg-red-50 text-red-600 rounded-lg flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
                  <p className="text-sm">{claimError}</p>
                </div>
              )}

              {step === 'SCAN' && (
                <div>
                  {cameraError && (
                    <div className="mb-4 p-3 bg-orange-50 text-orange-700 text-sm rounded-lg flex items-start gap-2">
                      <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                      <p>Camera access required. Enable permissions or enter manually.</p>
                    </div>
                  )}
                  
                  <div className="rounded-xl overflow-hidden aspect-square border-2 border-dashed border-slate-300 max-w-xs mx-auto bg-slate-50 relative">
                    <Scanner 
                      onScan={handleScan}
                      onError={(err) => {
                        console.error("Scanner Error:", err);
                        setCameraError(true);
                      }}
                      constraints={{ facingMode: 'environment' }}
                    />
                  </div>
                  <p className="text-center text-sm text-slate-500 mt-4">Point your camera at the QR code on your device.</p>
                  
                  <div className="mt-8 text-center border-t border-slate-100 pt-6">
                    <button 
                      onClick={switchToManual}
                      className="text-brand font-medium text-sm hover:underline flex items-center justify-center gap-2 mx-auto"
                    >
                      <Edit3 className="w-4 h-4" />
                      Having trouble scanning? Enter Device Details Manually
                    </button>
                  </div>
                </div>
              )}

              {step === 'FORM' && (
                <form onSubmit={handleClaimSubmit} className="space-y-5">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 bg-slate-50 p-4 rounded-lg border border-slate-200">
                    <div>
                      <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Device UID</label>
                      <input 
                        type="text" 
                        value={uid}
                        onChange={e => setUid(e.target.value)}
                        readOnly={activationMethod === 'QR'}
                        className={`w-full px-3 py-2 border rounded-md text-sm ${activationMethod === 'QR' ? 'bg-slate-100 border-slate-200 text-slate-600 focus:outline-none cursor-not-allowed' : 'bg-white border-slate-300 focus:ring-brand focus:border-brand'}`}
                        placeholder="TRV-DEV-..."
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Activation Code</label>
                      <input 
                        type="text" 
                        value={code}
                        onChange={e => setCode(e.target.value)}
                        readOnly={activationMethod === 'QR'}
                        className={`w-full px-3 py-2 border rounded-md text-sm ${activationMethod === 'QR' ? 'bg-slate-100 border-slate-200 text-slate-600 focus:outline-none cursor-not-allowed' : 'bg-white border-slate-300 focus:ring-brand focus:border-brand'}`}
                        placeholder="e.g. AU5H3Y8S"
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Device Name <span className="text-red-500">*</span></label>
                    <input 
                      type="text" 
                      value={deviceName}
                      onChange={e => setDeviceName(e.target.value)}
                      maxLength={50}
                      className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-brand focus:border-brand"
                      placeholder="e.g. North Field Sensor"
                      required
                    />
                  </div>

                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <label className="block text-sm font-medium text-slate-700">Farm Selection <span className="text-red-500">*</span></label>
                      {!isCreatingFarm && (
                        <button type="button" onClick={() => setIsCreatingFarm(true)} className="text-xs text-brand font-medium hover:underline">
                          + Create Farm
                        </button>
                      )}
                    </div>
                    
                    {isCreatingFarm ? (
                      <div className="flex gap-2 mb-2">
                        <input 
                          type="text"
                          value={newFarmName}
                          onChange={e => setNewFarmName(e.target.value)}
                          placeholder="Enter new farm name"
                          className="flex-1 px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-brand focus:border-brand"
                        />
                        <button 
                          type="button"
                          onClick={handleCreateFarm}
                          disabled={creatingFarm || !newFarmName.trim()}
                          className="px-4 py-2 bg-slate-800 text-white text-sm font-medium rounded-lg hover:bg-slate-700 disabled:opacity-50"
                        >
                          Save
                        </button>
                        <button 
                          type="button"
                          onClick={() => { setIsCreatingFarm(false); setNewFarmName(''); }}
                          className="px-3 py-2 text-slate-500 hover:text-slate-700 text-sm"
                        >
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <select 
                        value={farmId}
                        onChange={e => setFarmId(e.target.value)}
                        className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-brand focus:border-brand"
                        required
                      >
                        <option value="" disabled>Select a farm</option>
                        {farms.map(f => (
                          <option key={f.id} value={f.id}>{f.name}</option>
                        ))}
                      </select>
                    )}
                    {farms.length === 0 && !isCreatingFarm && (
                      <p className="text-xs text-orange-600 mt-1">No farms found. Please create your first farm.</p>
                    )}
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Installation Location</label>
                      <input 
                        type="text" 
                        value={location}
                        onChange={e => setLocation(e.target.value)}
                        className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-brand focus:border-brand text-sm"
                        placeholder="e.g. Near Water Tank"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Installation Date</label>
                      <input 
                        type="date" 
                        value={date}
                        onChange={e => setDate(e.target.value)}
                        className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-brand focus:border-brand text-sm"
                      />
                    </div>
                  </div>

                  <div className="pt-6 border-t border-slate-100 flex gap-3">
                    <button 
                      type="button" 
                      onClick={() => setStep('SCAN')} 
                      className="px-4 py-2 text-sm font-medium text-slate-700 bg-slate-100 rounded-lg hover:bg-slate-200"
                    >
                      Back to Scanner
                    </button>
                    <button 
                      type="submit"
                      disabled={submitLoading || !uid || !code || !deviceName || !farmId}
                      className="flex-1 py-2 px-4 bg-brand text-white rounded-lg font-medium flex justify-center items-center gap-2 hover:bg-brand/90 disabled:opacity-50 transition"
                    >
                      {submitLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Link Device'}
                    </button>
                  </div>
                </form>
              )}

              {step === 'SUCCESS' && (
                <div className="text-center py-6">
                  <CheckCircle className="w-16 h-16 text-emerald-500 mx-auto mb-4" />
                  <h2 className="text-2xl font-bold text-slate-800 mb-2">🎉 Device Linked Successfully</h2>
                  <p className="text-slate-600 mb-8">Your TERRAVYN device is now connected to your account.</p>
                  <div className="flex justify-center gap-4">
                    <button 
                      onClick={closeClaimModal}
                      className="px-6 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition font-medium"
                    >
                      View Device
                    </button>
                    <button 
                      onClick={() => navigate('/dashboard')}
                      className="px-6 py-2 bg-brand text-white rounded-lg hover:bg-brand/90 transition font-medium"
                    >
                      Go to Dashboard
                    </button>
                  </div>
                </div>
              )}

            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserDeviceManagement;
