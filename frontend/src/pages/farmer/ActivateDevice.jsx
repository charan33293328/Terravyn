import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Scanner } from '@yudiel/react-qr-scanner';
import { CheckCircle, XCircle, Camera, Edit3, Loader2, AlertCircle, PlusCircle } from 'lucide-react';
import apiClient from '../../api/client';

const ActivateDevice = () => {
  const navigate = useNavigate();
  
  const [step, setStep] = useState('SCAN'); // 'SCAN', 'FORM', 'SUCCESS'
  const [activationMethod, setActivationMethod] = useState('QR'); // 'QR' or 'MANUAL'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Scanned Data
  const [uid, setUid] = useState('');
  const [code, setCode] = useState('');
  
  // Metadata Data
  const [deviceName, setDeviceName] = useState('');
  const [farmId, setFarmId] = useState('');
  const [location, setLocation] = useState('');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  
  // Farms State
  const [farms, setFarms] = useState([]);
  const [isCreatingFarm, setIsCreatingFarm] = useState(false);
  const [newFarmName, setNewFarmName] = useState('');
  const [creatingFarm, setCreatingFarm] = useState(false);
  
  // Scanner State
  const [cameraError, setCameraError] = useState(false);

  useEffect(() => {
    fetchFarms();
  }, []);

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

  const handleScan = (detectedCodes) => {
    if (detectedCodes && detectedCodes.length > 0 && step === 'SCAN') {
      const result = detectedCodes[0].rawValue;
      console.log("QR Detected:", result);
      
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
          console.log("QR Payload Parsed");
          setUid(parsedUid);
          setCode(parsedCode);
          setActivationMethod('QR');
          setStep('FORM');
          setError('');
        } else {
          setError('Invalid TERRAVYN QR Code. Please scan again.');
        }
      } catch (e) {
        setError('Invalid TERRAVYN QR Code. Please scan again.');
      }
    }
  };

  const switchToManual = () => {
    setActivationMethod('MANUAL');
    setStep('FORM');
    setError('');
    setCameraError(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (loading) return;
    
    if (!uid || !code || !deviceName || !farmId) {
      setError('Please fill in all required fields.');
      return;
    }

    setLoading(true);
    setError('');

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
    } catch (err) {
      setError(err.response?.data?.detail || 'Activation failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (step === 'SUCCESS') {
    return (
      <div className="max-w-2xl mx-auto p-6 mt-12 text-center bg-white rounded-xl shadow-sm border border-slate-200">
        <CheckCircle className="w-16 h-16 text-emerald-500 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-slate-800 mb-2">🎉 Device Linked Successfully</h2>
        <p className="text-slate-600 mb-8">Your TERRAVYN device is now connected to your account.</p>
        <div className="flex justify-center gap-4">
          <button 
            onClick={() => navigate('/farmer/devices')}
            className="px-6 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition"
          >
            View Devices
          </button>
          <button 
            onClick={() => navigate('/farmer/dashboard')}
            className="px-6 py-2 bg-brand text-white rounded-lg hover:bg-brand/90 transition"
          >
            Go to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-xl mx-auto p-6 mt-8">
      <h1 className="text-2xl font-bold text-slate-800 mb-2">Claim New Device</h1>
      <p className="text-slate-500 mb-8">Scan your device QR code to link it to your farm.</p>

      {error && (
        <div className="mb-6 p-4 bg-red-50 text-red-600 rounded-lg flex items-start gap-3">
          <XCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <p>{error}</p>
        </div>
      )}

      {step === 'SCAN' && (
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          {cameraError && (
            <div className="mb-6 p-4 bg-orange-50 text-orange-700 rounded-lg flex items-start gap-3">
              <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold mb-1">Camera access is required to scan the QR code.</p>
                <p className="text-sm">Please enable camera permissions or use Manual Activation instead.</p>
              </div>
            </div>
          )}
          
          <h3 className="font-semibold text-lg mb-4 text-center">Scan QR Code</h3>
          <div className="rounded-xl overflow-hidden aspect-square border-2 border-dashed border-slate-300 max-w-sm mx-auto bg-slate-50 relative">
            <Scanner 
              onScan={handleScan}
              onError={(err) => {
                console.error("Scanner Error:", err);
                setCameraError(true);
              }}
              constraints={{ facingMode: 'environment' }}
            />
          </div>
          <p className="text-center text-sm text-slate-500 mt-4">Point your camera at the QR code on your device or packaging.</p>
          
          <div className="mt-8 text-center border-t border-slate-100 pt-6">
            <p className="text-sm text-slate-500 mb-2">Having trouble scanning?</p>
            <button 
              onClick={switchToManual}
              className="text-brand font-medium hover:underline flex items-center justify-center gap-2 mx-auto"
            >
              <Edit3 className="w-4 h-4" />
              Enter Device Details Manually
            </button>
          </div>
        </div>
      )}

      {step === 'FORM' && (
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm relative">
          <button 
            onClick={() => { setStep('SCAN'); setError(''); }}
            className="absolute top-4 right-4 text-sm text-slate-500 hover:text-slate-800"
          >
            Cancel
          </button>
          
          <h3 className="font-semibold text-lg mb-6">Device Details</h3>
          
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 bg-slate-50 p-4 rounded-lg border border-slate-200">
              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Device UID</label>
                <input 
                  type="text" 
                  value={uid}
                  onChange={e => setUid(e.target.value)}
                  readOnly={activationMethod === 'QR'}
                  className={`w-full px-3 py-2 border rounded-md text-sm ${activationMethod === 'QR' ? 'bg-slate-100 border-slate-200 text-slate-600 focus:outline-none' : 'bg-white border-slate-300 focus:ring-brand focus:border-brand'}`}
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
                  className={`w-full px-3 py-2 border rounded-md text-sm ${activationMethod === 'QR' ? 'bg-slate-100 border-slate-200 text-slate-600 focus:outline-none' : 'bg-white border-slate-300 focus:ring-brand focus:border-brand'}`}
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
                    + Add New Farm
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
                <p className="text-xs text-orange-600 mt-1">No farms available. Please add a new farm.</p>
              )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Installation Location</label>
                <input 
                  type="text" 
                  value={location}
                  onChange={e => setLocation(e.target.value)}
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-brand focus:border-brand"
                  placeholder="e.g. Near Water Tank"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Installation Date</label>
                <input 
                  type="date" 
                  value={date}
                  onChange={e => setDate(e.target.value)}
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-brand focus:border-brand"
                />
              </div>
            </div>

            <div className="pt-4 border-t border-slate-100">
              <button 
                type="submit"
                disabled={loading || !uid || !code || !deviceName || !farmId}
                className="w-full py-3 px-4 bg-brand text-white rounded-lg font-medium flex justify-center items-center gap-2 hover:bg-brand/90 disabled:opacity-50 transition"
              >
                {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Link Device'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};

export default ActivateDevice;
