import React, { useState, useEffect, useRef } from 'react';
import { Plus, Edit2, Trash2, Cpu, QrCode, Download } from 'lucide-react';
import { QRCodeCanvas } from 'qrcode.react';
import apiClient from '../api/client';

const AdminDeviceManagement = () => {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('all'); // all, claimed, unclaimed
  
  // Modal state
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [generatedDevice, setGeneratedDevice] = useState(null);
  const qrRef = useRef(null);

  useEffect(() => {
    fetchDevices();
  }, [activeTab]);

  const fetchDevices = async () => {
    setLoading(true);
    try {
      let endpoint = '/admin/devices';
      if (activeTab === 'claimed') endpoint = '/admin/devices/claimed';
      if (activeTab === 'unclaimed') endpoint = '/admin/devices/unclaimed';
      
      const res = await apiClient.get(endpoint);
      setDevices(res.data);
    } catch (err) {
      console.error("Failed to fetch devices", err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateDevice = async () => {
    try {
      const res = await apiClient.post('/admin/create-device');
      setGeneratedDevice(res.data);
      fetchDevices();
    } catch (err) {
      console.error("Failed to generate device", err);
    }
  };

  const downloadQRCode = () => {
    if (!qrRef.current) return;
    const canvas = qrRef.current.querySelector('canvas');
    if (canvas) {
      const pngUrl = canvas
        .toDataURL("image/png")
        .replace("image/png", "image/octet-stream");
      let downloadLink = document.createElement("a");
      downloadLink.href = pngUrl;
      downloadLink.download = `QR_${generatedDevice.device_uid}.png`;
      document.body.appendChild(downloadLink);
      downloadLink.click();
      document.body.removeChild(downloadLink);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-slate-800">Admin: Device Management</h2>
          <p className="text-slate-500">Provision new hardware, generate QR codes, and monitor fleet status.</p>
        </div>
        <button 
          onClick={() => {
            setGeneratedDevice(null);
            setShowGenerateModal(true);
          }}
          className="flex items-center gap-2 px-4 py-2 bg-brand text-white rounded-lg shadow-sm hover:bg-brand-dark transition-colors font-medium text-sm"
        >
          <Plus className="w-4 h-4"/> Generate New Device
        </button>
      </div>

      <div className="flex border-b border-slate-200 space-x-8">
        <button 
          className={`pb-4 font-medium text-sm border-b-2 transition-colors ${activeTab === 'all' ? 'border-brand text-brand' : 'border-transparent text-slate-500 hover:text-slate-700'}`}
          onClick={() => setActiveTab('all')}
        >
          All Devices
        </button>
        <button 
          className={`pb-4 font-medium text-sm border-b-2 transition-colors ${activeTab === 'claimed' ? 'border-brand text-brand' : 'border-transparent text-slate-500 hover:text-slate-700'}`}
          onClick={() => setActiveTab('claimed')}
        >
          Claimed
        </button>
        <button 
          className={`pb-4 font-medium text-sm border-b-2 transition-colors ${activeTab === 'unclaimed' ? 'border-brand text-brand' : 'border-transparent text-slate-500 hover:text-slate-700'}`}
          onClick={() => setActiveTab('unclaimed')}
        >
          Unclaimed
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <table className="min-w-full divide-y divide-slate-200">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Device UID</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Activation Code</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Owner ID</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Status</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-slate-200">
            {loading ? (
              <tr><td colSpan="4" className="px-6 py-4 text-center text-slate-500">Loading devices...</td></tr>
            ) : devices.length === 0 ? (
              <tr><td colSpan="4" className="px-6 py-4 text-center text-slate-500">No devices found.</td></tr>
            ) : devices.map(device => (
              <tr key={device.id}>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center">
                      <Cpu className="w-4 h-4 text-slate-600" />
                    </div>
                    <span className="text-sm font-medium text-slate-900 font-mono">{device.device_uid}</span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500 font-mono">
                  {device.activation_code || 'N/A'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
                  {device.owner_id ? `User #${device.owner_id}` : <span className="text-amber-600 font-medium">Unclaimed</span>}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${device.status === 'online' ? 'bg-green-100 text-green-800' : 'bg-slate-100 text-slate-800'}`}>
                    {device.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showGenerateModal && (
        <div className="fixed inset-0 bg-slate-900/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
            <h3 className="text-lg font-bold text-slate-900 mb-4">Generate New IoT Device</h3>
            
            {!generatedDevice ? (
              <div className="space-y-4">
                <p className="text-sm text-slate-600">
                  This will provision a new device identity securely in the database. A unique device UID, activation code, and secret will be generated.
                </p>
                <div className="flex justify-end gap-3 mt-6">
                  <button onClick={() => setShowGenerateModal(false)} className="px-4 py-2 text-sm font-medium text-slate-700 bg-slate-100 rounded-lg hover:bg-slate-200">Cancel</button>
                  <button onClick={handleGenerateDevice} className="px-4 py-2 text-sm font-medium text-white bg-brand rounded-lg hover:bg-brand-dark flex items-center gap-2">
                    <Cpu className="w-4 h-4" /> Provision Hardware
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-6 text-center">
                <div className="bg-green-50 text-green-800 p-3 rounded-lg text-sm font-medium">
                  Device successfully generated and stored!
                </div>
                
                <div className="space-y-2 text-left bg-slate-50 p-4 rounded-lg">
                  <p className="text-sm"><span className="font-semibold text-slate-700">Device UID:</span> <span className="font-mono text-slate-600">{generatedDevice.device_uid}</span></p>
                  <p className="text-sm"><span className="font-semibold text-slate-700">Activation Code:</span> <span className="font-mono text-slate-600">{generatedDevice.activation_code}</span></p>
                  <p className="text-sm"><span className="font-semibold text-slate-700">Secret:</span> <span className="font-mono text-xs text-slate-500 break-all">{generatedDevice.device_secret}</span></p>
                </div>

                <div className="flex flex-col items-center justify-center pt-2" ref={qrRef}>
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Provisioning QR Code</p>
                  <div className="p-2 bg-white border border-slate-200 rounded-xl shadow-sm">
                    <QRCodeCanvas 
                      value={JSON.stringify({
                        uid: generatedDevice.device_uid,
                        code: generatedDevice.activation_code
                      })}
                      size={180}
                      level={"H"}
                    />
                  </div>
                </div>

                <div className="flex justify-center gap-3 mt-6">
                  <button onClick={() => setShowGenerateModal(false)} className="px-4 py-2 text-sm font-medium text-slate-700 bg-slate-100 rounded-lg hover:bg-slate-200">Close</button>
                  <button onClick={downloadQRCode} className="px-4 py-2 text-sm font-medium text-brand bg-brand/10 rounded-lg hover:bg-brand/20 flex items-center gap-2">
                    <Download className="w-4 h-4" /> Download QR
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDeviceManagement;
