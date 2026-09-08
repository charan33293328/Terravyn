import React from 'react';
import { useAuth } from '../context/AuthContext';
import AdminDeviceManagement from './AdminDeviceManagement';
import UserDeviceManagement from './UserDeviceManagement';

const DeviceManagement = () => {
  const { user, loading } = useAuth();

  if (loading || !user) {
    return <div className="p-6 text-slate-500">Loading...</div>;
  }

  if (user.role === 'admin') {
    return <AdminDeviceManagement />;
  }

  return <UserDeviceManagement />;
};

export default DeviceManagement;
