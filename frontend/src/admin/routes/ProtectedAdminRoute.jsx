import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import ErrorState from '../components/ErrorState';

const ProtectedAdminRoute = () => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand"></div>
      </div>
    );
  }
  
  // If not logged in at all, go to login
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  
  // Checking role for RBAC
  const adminRoles = ['super_admin', 'admin'];
  if (!adminRoles.includes(user.role)) {
    // Return 403 Forbidden Error State
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex items-center justify-center">
        <ErrorState 
          type="403" 
          title="Access Denied" 
          message="You do not have the required administrative privileges to view the Control Center."
          actionText="Return to Dashboard"
          onAction={() => window.location.href = '/dashboard'}
        />
      </div>
    );
  }
  
  return <Outlet />;
};

export default ProtectedAdminRoute;
