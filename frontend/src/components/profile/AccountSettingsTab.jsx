import React, { useState, useEffect } from 'react';
import { Settings, Download, AlertTriangle, Loader2, FileJson, FileText, CheckCircle2 } from 'lucide-react';
import client from '../../api/client';
import dayjs from 'dayjs';

export default function AccountSettingsTab() {
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState(null);
  
  const [exporting, setExporting] = useState(false);
  
  const [showDeactivateModal, setShowDeactivateModal] = useState(false);
  const [deactivatePwd, setDeactivatePwd] = useState('');
  const [deactivateReason, setDeactivateReason] = useState('');
  const [deactivateLoading, setDeactivateLoading] = useState(false);
  const [deactivateError, setDeactivateError] = useState(null);
  const [deactivateSuccess, setDeactivateSuccess] = useState(false);

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const res = await client.get('/farmer/profile');
      setProfile(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format) => {
    setExporting(true);
    try {
      if (format === 'json') {
        const res = await client.get('/farmer/profile/export?format=json');
        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(res.data, null, 2));
        const downloadAnchorNode = document.createElement('a');
        downloadAnchorNode.setAttribute("href", dataStr);
        downloadAnchorNode.setAttribute("download", "terravyn_data_export.json");
        document.body.appendChild(downloadAnchorNode);
        downloadAnchorNode.click();
        downloadAnchorNode.remove();
      } else {
        const res = await client.get('/farmer/profile/export?format=pdf', { responseType: 'blob' });
        const url = window.URL.createObjectURL(new Blob([res.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', 'terravyn_data_export.pdf');
        document.body.appendChild(link);
        link.click();
        link.parentNode.removeChild(link);
      }
    } catch (err) {
      console.error("Export failed", err);
    } finally {
      setExporting(false);
    }
  };

  const handleDeactivate = async (e) => {
    e.preventDefault();
    setDeactivateLoading(true);
    setDeactivateError(null);

    try {
      await client.post('/farmer/profile/deactivate', {
        password: deactivatePwd,
        reason: deactivateReason
      });
      setDeactivateSuccess(true);
      setTimeout(() => {
        // Log out or redirect
        localStorage.removeItem('token');
        window.location.href = '/login';
      }, 3000);
    } catch (err) {
      setDeactivateError(err.response?.data?.detail || "Failed to submit deactivation request.");
      setDeactivateLoading(false);
    }
  };

  if (loading) {
    return <div className="flex justify-center items-center h-64"><Loader2 className="w-8 h-8 animate-spin text-emerald-600" /></div>;
  }

  return (
    <div className="max-w-3xl relative">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-slate-100 rounded-lg text-slate-600">
          <Settings className="w-5 h-5" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-slate-900">Account Settings</h2>
          <p className="text-sm text-slate-500">Manage your account status and download your personal data.</p>
        </div>
      </div>

      {/* Account Status Info */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 mb-8 grid grid-cols-1 md:grid-cols-3 gap-6">
        <div>
          <div className="text-sm text-slate-500 mb-1">Account Status</div>
          <div className="font-semibold text-slate-900 flex items-center gap-2">
            <span className={`w-2.5 h-2.5 rounded-full ${profile?.status === 'ACTIVE' ? 'bg-emerald-500' : 'bg-amber-500'}`}></span>
            {profile?.status}
          </div>
        </div>
        <div>
          <div className="text-sm text-slate-500 mb-1">Membership Type</div>
          <div className="font-semibold text-slate-900">Standard Farmer</div>
        </div>
        <div>
          <div className="text-sm text-slate-500 mb-1">Date Joined</div>
          <div className="font-semibold text-slate-900">{profile ? dayjs(profile.created_at).format('DD MMM YYYY') : ''}</div>
        </div>
      </div>

      {/* Download Data */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 mb-8">
        <div className="flex items-start gap-4 mb-6">
          <div className="p-3 bg-blue-50 text-blue-600 rounded-lg shrink-0">
            <Download className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-slate-900">Download Personal Data</h3>
            <p className="text-sm text-slate-500 mt-1">Export a copy of your personal information, device records, and account history.</p>
          </div>
        </div>
        
        <div className="flex flex-wrap gap-4 ml-14">
          <button
            onClick={() => handleExport('json')}
            disabled={exporting}
            className="px-4 py-2 bg-slate-100 text-slate-700 hover:bg-slate-200 font-medium rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50"
          >
            <FileJson className="w-4 h-4" />
            Download JSON
          </button>
          <button
            onClick={() => handleExport('pdf')}
            disabled={exporting}
            className="px-4 py-2 bg-slate-100 text-slate-700 hover:bg-slate-200 font-medium rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50"
          >
            <FileText className="w-4 h-4" />
            Download PDF
          </button>
        </div>
      </div>

      {/* Deactivate Account */}
      <div className="bg-white border border-red-200 rounded-xl p-6 mb-8">
        <div className="flex items-start gap-4 mb-4">
          <div className="p-3 bg-red-50 text-red-600 rounded-lg shrink-0">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-slate-900">Deactivate Account</h3>
            <p className="text-sm text-slate-500 mt-1">Request to deactivate your account. You will lose access to TERRAVYN services until your account is reactivated.</p>
          </div>
        </div>
        
        <div className="ml-14 mt-4">
          <button
            onClick={() => setShowDeactivateModal(true)}
            className="px-4 py-2 bg-red-50 text-red-600 hover:bg-red-100 font-medium rounded-lg transition-colors border border-red-200"
          >
            Deactivate Account
          </button>
        </div>
      </div>

      {/* Deactivation Modal */}
      {showDeactivateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 m-4">
            {deactivateSuccess ? (
              <div className="text-center py-6">
                <div className="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto mb-4">
                  <CheckCircle2 className="w-8 h-8" />
                </div>
                <h3 className="text-xl font-bold text-slate-900 mb-2">Request Submitted</h3>
                <p className="text-slate-500">Your account deactivation request has been submitted. You will be logged out shortly.</p>
              </div>
            ) : (
              <form onSubmit={handleDeactivate}>
                <h3 className="text-xl font-bold text-slate-900 mb-2">Confirm Deactivation</h3>
                <p className="text-sm text-slate-500 mb-6">Are you sure you want to deactivate your account? This action requires password confirmation.</p>

                {deactivateError && <div className="bg-red-50 text-red-600 text-sm p-3 rounded-lg mb-4">{deactivateError}</div>}

                <div className="space-y-4 mb-6">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Reason for leaving (Optional)</label>
                    <textarea
                      value={deactivateReason}
                      onChange={(e) => setDeactivateReason(e.target.value)}
                      className="w-full px-4 py-2 bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                      rows="2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Confirm Password</label>
                    <input
                      type="password"
                      value={deactivatePwd}
                      onChange={(e) => setDeactivatePwd(e.target.value)}
                      className="w-full px-4 py-2 bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                      required
                    />
                  </div>
                </div>

                <div className="flex items-center justify-end gap-3">
                  <button
                    type="button"
                    onClick={() => setShowDeactivateModal(false)}
                    className="px-4 py-2 text-slate-600 hover:bg-slate-100 font-medium rounded-lg transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={deactivateLoading}
                    className="px-4 py-2 bg-red-600 text-white font-medium rounded-lg hover:bg-red-700 transition-colors flex items-center gap-2 disabled:bg-red-400"
                  >
                    {deactivateLoading && <Loader2 className="w-4 h-4 animate-spin" />}
                    Confirm Deactivation
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
