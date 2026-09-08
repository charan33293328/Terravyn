import React, { useState } from 'react';
import { User, Mail, Lock } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import apiClient from '../api/client';

const Profile = () => {
  const { user, logout } = useAuth();
  const [formData, setFormData] = useState({
    full_name: user?.full_name || '',
    password: ''
  });
  const [message, setMessage] = useState({ type: '', text: '' });
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setMessage({ type: '', text: '' });
    
    try {
      const updatePayload = { full_name: formData.full_name };
      if (formData.password) {
        updatePayload.password = formData.password;
      }
      await apiClient.put('/auth/profile', updatePayload);
      setMessage({ type: 'success', text: 'Profile updated successfully!' });
      setFormData({...formData, password: ''});
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to update profile.' });
    } finally {
      setSaving(false);
    }
  };

  if (!user) return null;

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-800">User Profile</h2>
        <p className="text-slate-500">Manage your account settings and preferences.</p>
      </div>

      <div className="bg-white p-8 rounded-xl shadow-sm border border-slate-200">
        <form onSubmit={handleSubmit} className="space-y-6">
          {message.text && (
            <div className={`p-4 rounded-lg text-sm ${message.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
              {message.text}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-slate-700">Full Name</label>
            <div className="mt-1 relative rounded-md shadow-sm">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <User className="h-5 w-5 text-slate-400" />
              </div>
              <input
                type="text"
                className="focus:ring-brand focus:border-brand block w-full pl-10 sm:text-sm border-slate-300 rounded-lg py-2 border"
                value={formData.full_name}
                onChange={(e) => setFormData({...formData, full_name: e.target.value})}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700">Email Address (Read Only)</label>
            <div className="mt-1 relative rounded-md shadow-sm">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Mail className="h-5 w-5 text-slate-400" />
              </div>
              <input
                type="email"
                disabled
                className="bg-slate-50 block w-full pl-10 sm:text-sm border-slate-300 rounded-lg py-2 border text-slate-500 cursor-not-allowed"
                value={user.email}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700">New Password</label>
            <div className="mt-1 relative rounded-md shadow-sm">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Lock className="h-5 w-5 text-slate-400" />
              </div>
              <input
                type="password"
                placeholder="Leave blank to keep current password"
                className="focus:ring-brand focus:border-brand block w-full pl-10 sm:text-sm border-slate-300 rounded-lg py-2 border"
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
              />
            </div>
          </div>

          <div className="flex justify-between pt-4">
            <button
              type="button"
              onClick={logout}
              className="px-4 py-2 text-sm font-medium text-red-600 bg-red-50 hover:bg-red-100 rounded-lg transition-colors"
            >
              Sign Out
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-6 py-2 text-sm font-medium text-white bg-brand hover:bg-brand-dark rounded-lg shadow-sm transition-colors disabled:opacity-70"
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Profile;
