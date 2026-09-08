import React, { useState, useEffect, useRef } from 'react';
import { Camera, CheckCircle2, Info, ArrowRight, Loader2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import client from '../../api/client';
import dayjs from 'dayjs';

export default function PersonalInfoTab() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  
  const [profile, setProfile] = useState(null);
  const [fullName, setFullName] = useState('');
  const [username, setUsername] = useState('');
  const [photoFile, setPhotoFile] = useState(null);
  const [photoPreview, setPhotoPreview] = useState(null);
  
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      setLoading(true);
      const res = await client.get('/farmer/profile');
      setProfile(res.data);
      setFullName(res.data.full_name || '');
      setUsername(res.data.username || '');
      if (res.data.profile_photo) {
        const baseUrl = import.meta.env.VITE_API_BASE_URL || 'https://terravyn-backend.onrender.com';
        setPhotoPreview(res.data.profile_photo.startsWith('http') ? res.data.profile_photo : `${baseUrl}${res.data.profile_photo}`);
      }
    } catch (err) {
      setError('Failed to load profile information.');
    } finally {
      setLoading(false);
    }
  };

  const handlePhotoChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        setError('Image exceeds 5MB limit.');
        return;
      }
      setPhotoFile(file);
      setPhotoPreview(URL.createObjectURL(file));
      setError(null);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(false);
    
    try {
      const formData = new FormData();
      if (fullName !== profile.full_name) formData.append('full_name', fullName);
      if (username !== profile.username) formData.append('username', username);
      if (photoFile) formData.append('profile_photo', photoFile);
      
      const res = await client.put('/farmer/profile', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      setProfile(res.data);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update profile.');
    } finally {
      setSaving(false);
    }
  };

  const navigateToSupport = (subject) => {
    navigate(`/farmer/support/new?category=Account Issue&subject=${encodeURIComponent(subject)}`);
  };

  if (loading) {
    return <div className="flex justify-center items-center h-64"><Loader2 className="w-8 h-8 animate-spin text-emerald-600" /></div>;
  }

  return (
    <div className="max-w-2xl">
      <h2 className="text-xl font-bold text-slate-900 mb-6">Personal Information</h2>
      
      {error && <div className="bg-red-50 text-red-600 p-4 rounded-lg mb-6">{error}</div>}
      {success && <div className="bg-emerald-50 text-emerald-600 p-4 rounded-lg mb-6 flex items-center gap-2"><CheckCircle2 className="w-5 h-5"/> Profile updated successfully!</div>}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Profile Photo */}
        <div className="flex items-center gap-6">
          <div className="relative">
            <div className="w-24 h-24 rounded-full bg-slate-200 border-4 border-white shadow-sm overflow-hidden flex items-center justify-center">
              {photoPreview ? (
                <img src={photoPreview} alt="Profile" className="w-full h-full object-cover" />
              ) : (
                <span className="text-3xl font-bold text-slate-400">{fullName.charAt(0)}</span>
              )}
            </div>
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="absolute bottom-0 right-0 p-1.5 bg-white rounded-full border border-slate-200 shadow-sm text-slate-600 hover:text-emerald-600 transition-colors"
            >
              <Camera className="w-4 h-4" />
            </button>
            <input 
              type="file" 
              ref={fileInputRef} 
              className="hidden" 
              accept=".jpg,.jpeg,.png,.webp" 
              onChange={handlePhotoChange}
            />
          </div>
          <div>
            <h3 className="text-sm font-medium text-slate-900">Profile Photo</h3>
            <p className="text-xs text-slate-500 mt-1">JPEG, PNG, WEBP. Max 5MB.</p>
          </div>
        </div>

        {/* Name and Username */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Full Name</label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full px-4 py-2 bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-2 bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
              placeholder="e.g. farmer_john"
            />
          </div>
        </div>

        {/* Email Address */}
        <div className="pt-4 border-t border-slate-200">
          <label className="block text-sm font-medium text-slate-700 mb-1 flex items-center gap-2">
            Email Address
            <div className="group relative cursor-pointer">
              <Info className="w-4 h-4 text-slate-400" />
              <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 hidden group-hover:block w-64 bg-slate-800 text-white text-xs p-2 rounded shadow-lg z-10 text-center">
                For security reasons, email address changes cannot be performed from the Farmer Panel. Please contact TERRAVYN Support for assistance.
              </div>
            </div>
          </label>
          <div className="flex items-center gap-3">
            <input
              type="email"
              value={profile?.email || ''}
              readOnly
              className="flex-1 px-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-600 cursor-not-allowed"
            />
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-50 text-emerald-700 text-sm font-medium whitespace-nowrap">
              <CheckCircle2 className="w-4 h-4" />
              Verified
            </span>
          </div>
          <div className="mt-2 text-sm text-slate-500 flex items-center gap-2">
            Need to update your email? 
            <button type="button" onClick={() => navigateToSupport('Request for Email Address Update')} className="text-emerald-600 font-medium hover:underline inline-flex items-center gap-1">
              Contact Support <ArrowRight className="w-3 h-3" />
            </button>
          </div>
        </div>

        {/* Phone Number */}
        <div className="pt-4 border-t border-slate-200">
          <label className="block text-sm font-medium text-slate-700 mb-1 flex items-center gap-2">
            Phone Number
            <div className="group relative cursor-pointer">
              <Info className="w-4 h-4 text-slate-400" />
              <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 hidden group-hover:block w-64 bg-slate-800 text-white text-xs p-2 rounded shadow-lg z-10 text-center">
                For security reasons, phone number changes cannot be performed from the Farmer Panel. Please contact TERRAVYN Support for assistance.
              </div>
            </div>
          </label>
          <div className="flex items-center gap-3">
            <input
              type="text"
              value={profile?.phone || ''}
              readOnly
              className="flex-1 px-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-600 cursor-not-allowed"
            />
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-50 text-emerald-700 text-sm font-medium whitespace-nowrap">
              <CheckCircle2 className="w-4 h-4" />
              Verified
            </span>
          </div>
          <div className="mt-2 text-sm text-slate-500 flex items-center gap-2">
            Need to update your phone number? 
            <button type="button" onClick={() => navigateToSupport('Request for Phone Number Update')} className="text-emerald-600 font-medium hover:underline inline-flex items-center gap-1">
              Contact Support <ArrowRight className="w-3 h-3" />
            </button>
          </div>
        </div>

        {/* Read Only Meta */}
        <div className="grid grid-cols-2 gap-6 pt-4 border-t border-slate-200">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Farmer ID</label>
            <input type="text" value={profile?.id || ''} readOnly className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-600" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Date Joined</label>
            <input type="text" value={profile ? dayjs(profile.created_at).format('DD MMM YYYY') : ''} readOnly className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-600" />
          </div>
        </div>

        {/* Submit */}
        <div className="pt-6 border-t border-slate-200 flex justify-end">
          <button
            type="submit"
            disabled={saving}
            className="px-6 py-2 bg-emerald-600 text-white font-medium rounded-lg hover:bg-emerald-700 transition-colors disabled:bg-emerald-400 flex items-center gap-2"
          >
            {saving && <Loader2 className="w-4 h-4 animate-spin" />}
            Save Changes
          </button>
        </div>
      </form>
    </div>
  );
}
