import React, { useState, useEffect } from 'react';
import { Shield, Key, Loader2, MonitorSmartphone, Globe, LogOut, CheckCircle2 } from 'lucide-react';
import client from '../../api/client';
import dayjs from 'dayjs';

export default function SecuritySettingsTab() {
  const [loading, setLoading] = useState(true);
  const [sessions, setSessions] = useState([]);
  
  // Password State
  const [changingPwd, setChangingPwd] = useState(false);
  const [pwdForm, setPwdForm] = useState({ current_password: '', new_password: '', confirm_password: '' });
  const [pwdError, setPwdError] = useState(null);
  const [pwdSuccess, setPwdSuccess] = useState(false);

  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    try {
      const res = await client.get('/farmer/profile/sessions');
      setSessions(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    setChangingPwd(true);
    setPwdError(null);
    setPwdSuccess(false);

    try {
      await client.put('/farmer/profile/change-password', pwdForm);
      setPwdSuccess(true);
      setPwdForm({ current_password: '', new_password: '', confirm_password: '' });
      setTimeout(() => setPwdSuccess(false), 3000);
    } catch (err) {
      setPwdError(err.response?.data?.detail || 'Failed to change password.');
    } finally {
      setChangingPwd(false);
    }
  };

  const terminateSession = async (sessionId) => {
    try {
      await client.delete(`/farmer/profile/sessions/${sessionId}`);
      fetchSessions();
    } catch (err) {
      console.error(err);
    }
  };

  const terminateAllOther = async () => {
    try {
      await client.delete('/farmer/profile/sessions');
      fetchSessions();
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) {
    return <div className="flex justify-center items-center h-64"><Loader2 className="w-8 h-8 animate-spin text-emerald-600" /></div>;
  }

  return (
    <div className="max-w-3xl">
      <h2 className="text-xl font-bold text-slate-900 mb-6">Security Settings</h2>

      {/* Change Password */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 mb-8">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-emerald-50 rounded-lg text-emerald-600">
            <Key className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-slate-900">Change Password</h3>
            <p className="text-sm text-slate-500">Update your password to keep your account secure.</p>
          </div>
        </div>

        {pwdError && <div className="bg-red-50 text-red-600 p-4 rounded-lg mb-6 text-sm">{pwdError}</div>}
        {pwdSuccess && <div className="bg-emerald-50 text-emerald-600 p-4 rounded-lg mb-6 text-sm flex items-center gap-2"><CheckCircle2 className="w-4 h-4"/> Password updated successfully.</div>}

        <form onSubmit={handlePasswordSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Current Password</label>
            <input
              type="password"
              value={pwdForm.current_password}
              onChange={(e) => setPwdForm({ ...pwdForm, current_password: e.target.value })}
              className="w-full px-4 py-2 bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
              required
            />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">New Password</label>
              <input
                type="password"
                value={pwdForm.new_password}
                onChange={(e) => setPwdForm({ ...pwdForm, new_password: e.target.value })}
                className="w-full px-4 py-2 bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                required
              />
              <p className="text-xs text-slate-500 mt-1">Min 8 characters, with letters and numbers.</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Confirm New Password</label>
              <input
                type="password"
                value={pwdForm.confirm_password}
                onChange={(e) => setPwdForm({ ...pwdForm, confirm_password: e.target.value })}
                className="w-full px-4 py-2 bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                required
              />
            </div>
          </div>
          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={changingPwd}
              className="px-6 py-2 bg-slate-900 text-white font-medium rounded-lg hover:bg-slate-800 transition-colors disabled:bg-slate-400 flex items-center gap-2"
            >
              {changingPwd && <Loader2 className="w-4 h-4 animate-spin" />}
              Update Password
            </button>
          </div>
        </form>
      </div>

      {/* Two-Factor Authentication */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 mb-8 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-slate-100 rounded-lg text-slate-600">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-slate-900">Two-Factor Authentication</h3>
            <p className="text-sm text-slate-500">Add an extra layer of security to your account.</p>
          </div>
        </div>
        <span className="px-3 py-1 bg-slate-100 text-slate-600 text-sm font-medium rounded-full">Coming Soon</span>
      </div>

      {/* Active Sessions */}
      <div className="bg-white border border-slate-200 rounded-xl p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-50 rounded-lg text-blue-600">
              <MonitorSmartphone className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-slate-900">Active Sessions</h3>
              <p className="text-sm text-slate-500">Devices that are currently logged into your account.</p>
            </div>
          </div>
          {sessions.length > 1 && (
            <button 
              onClick={terminateAllOther}
              className="px-4 py-2 text-sm text-red-600 bg-red-50 hover:bg-red-100 rounded-lg font-medium transition-colors"
            >
              Sign out of all other sessions
            </button>
          )}
        </div>

        <div className="space-y-4">
          {sessions.map((session) => (
            <div key={session.session_id} className="flex items-center justify-between p-4 border border-slate-100 bg-slate-50 rounded-lg">
              <div className="flex items-start gap-4">
                <Globe className="w-6 h-6 text-slate-400 mt-1" />
                <div>
                  <div className="font-medium text-slate-900 flex items-center gap-2">
                    {session.ip_address}
                    {session.is_current_session && (
                      <span className="px-2 py-0.5 bg-emerald-100 text-emerald-700 text-xs rounded-full">Current Session</span>
                    )}
                  </div>
                  <div className="text-sm text-slate-500 mt-1">{session.user_agent}</div>
                  <div className="text-xs text-slate-400 mt-1">Last active: {dayjs(session.last_active_at).format('MMM DD, YYYY HH:mm A')}</div>
                </div>
              </div>
              {!session.is_current_session && (
                <button
                  onClick={() => terminateSession(session.session_id)}
                  className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                  title="Sign out of this session"
                >
                  <LogOut className="w-5 h-5" />
                </button>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
