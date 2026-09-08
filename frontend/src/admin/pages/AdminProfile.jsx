import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { motion } from 'framer-motion';
import { Save, Lock, User, Mail, Phone, Hash, Calendar, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../../api/axios';
import { useAuth } from '../../context/AuthContext';

// Schemas for validation
const profileSchema = z.object({
  full_name: z.string().min(2, 'Name must be at least 2 characters'),
  username: z.string().min(3, 'Username must be at least 3 characters'),
  email: z.string().email('Invalid email address'),
  phone_number: z.string().min(10, 'Phone number must be at least 10 characters'),
});

const passwordSchema = z.object({
  current_password: z.string().min(1, 'Current password is required'),
  new_password: z.string().min(8, 'New password must be at least 8 characters'),
  confirm_password: z.string().min(8, 'Confirm password must be at least 8 characters'),
}).refine((data) => data.new_password === data.confirm_password, {
  message: "Passwords don't match",
  path: ["confirm_password"],
});

const AdminProfile = () => {
  const { user, setUser } = useAuth();
  const [isUpdatingProfile, setIsUpdatingProfile] = useState(false);
  const [isUpdatingPassword, setIsUpdatingPassword] = useState(false);

  const profileForm = useForm({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      full_name: '',
      username: '',
      email: '',
      phone_number: '',
    }
  });

  const passwordForm = useForm({
    resolver: zodResolver(passwordSchema),
    defaultValues: {
      current_password: '',
      new_password: '',
      confirm_password: '',
    }
  });

  // Populate profile form when user data is available
  useEffect(() => {
    if (user) {
      profileForm.reset({
        full_name: user.full_name || '',
        username: user.username || '',
        email: user.email || '',
        phone_number: user.phone_number || '',
      });
    }
  }, [user, profileForm]);

  const onProfileSubmit = async (data) => {
    setIsUpdatingProfile(true);
    try {
      const response = await api.put('/admin/profile', data);
      setUser(response.data); // Update global state
      toast.success('Profile updated successfully');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update profile');
    } finally {
      setIsUpdatingProfile(false);
    }
  };

  const onPasswordSubmit = async (data) => {
    setIsUpdatingPassword(true);
    try {
      await api.put('/admin/profile/change-password', data);
      toast.success('Password changed successfully');
      passwordForm.reset();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to change password');
    } finally {
      setIsUpdatingPassword(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (!user) return <div className="flex justify-center py-20"><Loader2 className="animate-spin text-brand" size={40} /></div>;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="mb-8">
        <h1 className="text-2xl font-black text-slate-900 dark:text-white tracking-tight dark:text-white">Admin Profile</h1>
        <p className="text-slate-500 dark:text-slate-400 mt-1 dark:text-slate-400">Manage your administrative account details and security settings.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column: Avatar & Read-Only Details */}
        <div className="lg:col-span-1 space-y-6">
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 p-6 flex flex-col items-center text-center dark:bg-slate-900 dark:border-slate-800"
          >
            <div className="w-32 h-32 bg-brand/10 rounded-full flex items-center justify-center text-brand font-bold text-4xl mb-4 border-4 border-white shadow-md dark:border-slate-800">
              {user.full_name?.charAt(0) || 'A'}
            </div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">{user.full_name}</h2>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-brand/10 text-brand rounded-full text-xs font-bold uppercase mt-2">
              {user.role?.replace('_', ' ')}
            </div>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 p-6 dark:bg-slate-900 dark:border-slate-800"
          >
            <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider mb-4 flex items-center gap-2 dark:text-white">
              <Calendar size={16} className="text-slate-400" /> Account Info
            </h3>
            <div className="space-y-4">
              <div>
                <p className="text-xs text-slate-500 dark:text-slate-400 font-medium mb-1 dark:text-slate-400">Account Created</p>
                <p className="text-sm text-slate-900 dark:text-white font-medium dark:text-slate-200">{formatDate(user.created_at)}</p>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Right Column: Forms */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Profile Form */}
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden dark:bg-slate-900 dark:border-slate-800"
          >
            <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-800/50 bg-slate-50 dark:bg-slate-950 flex items-center gap-3 dark:bg-slate-800/50 dark:border-slate-800">
              <User size={20} className="text-brand" />
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">Personal Information</h2>
            </div>
            <div className="p-6">
              <form onSubmit={profileForm.handleSubmit(onProfileSubmit)} className="space-y-5">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <div className="space-y-1.5">
                    <label className="text-sm font-bold text-slate-700 dark:text-slate-300">Full Name</label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                        <User size={18} />
                      </div>
                      <input 
                        type="text" 
                        {...profileForm.register('full_name')}
                        className="w-full pl-10 pr-3 py-2.5 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl focus:ring-2 focus:ring-brand/20 focus:border-brand transition-all dark:bg-slate-800 dark:border-slate-700 dark:text-white"
                        placeholder="John Doe"
                      />
                    </div>
                    {profileForm.formState.errors.full_name && (
                      <p className="text-red-500 text-xs font-medium">{profileForm.formState.errors.full_name.message}</p>
                    )}
                  </div>
                  
                  <div className="space-y-1.5">
                    <label className="text-sm font-bold text-slate-700 dark:text-slate-300">Username</label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                        <Hash size={18} />
                      </div>
                      <input 
                        type="text" 
                        {...profileForm.register('username')}
                        className="w-full pl-10 pr-3 py-2.5 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl focus:ring-2 focus:ring-brand/20 focus:border-brand transition-all dark:bg-slate-800 dark:border-slate-700 dark:text-white"
                        placeholder="johndoe123"
                      />
                    </div>
                    {profileForm.formState.errors.username && (
                      <p className="text-red-500 text-xs font-medium">{profileForm.formState.errors.username.message}</p>
                    )}
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-sm font-bold text-slate-700 dark:text-slate-300">Email Address</label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                        <Mail size={18} />
                      </div>
                      <input 
                        type="email" 
                        {...profileForm.register('email')}
                        className="w-full pl-10 pr-3 py-2.5 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl focus:ring-2 focus:ring-brand/20 focus:border-brand transition-all dark:bg-slate-800 dark:border-slate-700 dark:text-white"
                        placeholder="admin@terravyn.com"
                      />
                    </div>
                    {profileForm.formState.errors.email && (
                      <p className="text-red-500 text-xs font-medium">{profileForm.formState.errors.email.message}</p>
                    )}
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-sm font-bold text-slate-700 dark:text-slate-300">Phone Number</label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                        <Phone size={18} />
                      </div>
                      <input 
                        type="text" 
                        {...profileForm.register('phone_number')}
                        className="w-full pl-10 pr-3 py-2.5 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl focus:ring-2 focus:ring-brand/20 focus:border-brand transition-all dark:bg-slate-800 dark:border-slate-700 dark:text-white"
                        placeholder="+91 9876543210"
                      />
                    </div>
                    {profileForm.formState.errors.phone_number && (
                      <p className="text-red-500 text-xs font-medium">{profileForm.formState.errors.phone_number.message}</p>
                    )}
                  </div>
                </div>
                
                <div className="flex justify-end pt-2 border-t border-slate-100 dark:border-slate-800">
                  <button 
                    type="submit" 
                    disabled={isUpdatingProfile}
                    className="flex items-center gap-2 bg-brand text-white px-5 py-2.5 rounded-xl font-bold hover:bg-brand-dark transition-colors disabled:opacity-70"
                  >
                    {isUpdatingProfile ? <Loader2 size={18} className="animate-spin" /> : <Save size={18} />}
                    Save Changes
                  </button>
                </div>
              </form>
            </div>
          </motion.div>

          {/* Password Form */}
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden dark:bg-slate-900 dark:border-slate-800"
          >
            <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-800/50 bg-slate-50 dark:bg-slate-950 flex items-center gap-3 dark:bg-slate-800/50 dark:border-slate-800">
              <Lock size={20} className="text-brand" />
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">Change Password</h2>
            </div>
            <div className="p-6">
              <form onSubmit={passwordForm.handleSubmit(onPasswordSubmit)} className="space-y-5">
                <div className="space-y-1.5 max-w-md">
                  <label className="text-sm font-bold text-slate-700 dark:text-slate-300">Current Password</label>
                  <input 
                    type="password" 
                    {...passwordForm.register('current_password')}
                    className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl focus:ring-2 focus:ring-brand/20 focus:border-brand transition-all dark:bg-slate-800 dark:border-slate-700 dark:text-white"
                  />
                  {passwordForm.formState.errors.current_password && (
                    <p className="text-red-500 text-xs font-medium">{passwordForm.formState.errors.current_password.message}</p>
                  )}
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <div className="space-y-1.5">
                    <label className="text-sm font-bold text-slate-700 dark:text-slate-300">New Password</label>
                    <input 
                      type="password" 
                      {...passwordForm.register('new_password')}
                      className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl focus:ring-2 focus:ring-brand/20 focus:border-brand transition-all dark:bg-slate-800 dark:border-slate-700 dark:text-white"
                    />
                    {passwordForm.formState.errors.new_password && (
                      <p className="text-red-500 text-xs font-medium">{passwordForm.formState.errors.new_password.message}</p>
                    )}
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-sm font-bold text-slate-700 dark:text-slate-300">Confirm New Password</label>
                    <input 
                      type="password" 
                      {...passwordForm.register('confirm_password')}
                      className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl focus:ring-2 focus:ring-brand/20 focus:border-brand transition-all dark:bg-slate-800 dark:border-slate-700 dark:text-white"
                    />
                    {passwordForm.formState.errors.confirm_password && (
                      <p className="text-red-500 text-xs font-medium">{passwordForm.formState.errors.confirm_password.message}</p>
                    )}
                  </div>
                </div>
                
                <div className="flex justify-end pt-2 border-t border-slate-100 dark:border-slate-800">
                  <button 
                    type="submit" 
                    disabled={isUpdatingPassword}
                    className="flex items-center gap-2 bg-slate-900 text-white px-5 py-2.5 rounded-xl font-bold hover:bg-slate-800 transition-colors disabled:opacity-70 dark:bg-brand dark:hover:bg-brand-dark"
                  >
                    {isUpdatingPassword ? <Loader2 size={18} className="animate-spin" /> : <Lock size={18} />}
                    Update Password
                  </button>
                </div>
              </form>
            </div>
          </motion.div>

        </div>
      </div>
    </div>
  );
};

export default AdminProfile;
