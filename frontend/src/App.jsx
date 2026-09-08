import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import TerravynLoader from './components/common/TerravynLoader';
import Layout from './components/Layout';
import Landing from './pages/Landing';
import Dashboard from './pages/Dashboard';
import IrrigationControl from './pages/IrrigationControl';
import Analytics from './pages/Analytics';
import Alerts from './pages/Alerts';
import DeviceManagement from './pages/DeviceManagement';
import Profile from './pages/Profile';
import Login from './pages/Login';
import Signup from './pages/Signup';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import Pricing from './pages/Pricing';
import ProductDetails from './pages/ProductDetails';
import Cart from './pages/Cart';
import CustomerOrders from './pages/customer/CustomerOrders';
import CustomerOrderDetails from './pages/customer/CustomerOrderDetails';
import { AuthProvider, useAuth } from './context/AuthContext';
import { CartProvider } from './context/CartContext';

import ActivateDevice from './pages/farmer/ActivateDevice';
import FarmerDevices from './pages/farmer/FarmerDevices';
import FarmerDeviceDetail from './pages/farmer/FarmerDeviceDetail';
import FarmerDashboard from './pages/farmer/FarmerDashboard';
import FarmManagement from './pages/farmer/FarmManagement';
import FarmForm from './pages/farmer/FarmForm';
import FarmDetail from './pages/farmer/FarmDetail';
import MonitoringCenter from './pages/farmer/MonitoringCenter';
import MonitoringDeviceDetail from './pages/farmer/MonitoringDeviceDetail';
import AlertsCenter from './pages/farmer/AlertsCenter';
import AlertDetail from './pages/farmer/AlertDetail';
import FarmerOrders from './pages/farmer/FarmerOrders';
import FarmerOrderDetail from './pages/farmer/FarmerOrderDetail';
import SupportCenter from './pages/farmer/SupportCenter';
import CreateSupportTicket from './pages/farmer/CreateSupportTicket';
import SupportTicketDetail from './pages/farmer/SupportTicketDetail';
import FarmerProfile from './pages/farmer/FarmerProfile';

// Admin Imports
import AdminLayout from './admin/layouts/AdminLayout';
import ProtectedAdminRoute from './admin/routes/ProtectedAdminRoute';
import AdminDashboard from './admin/pages/Dashboard';
import AdminDevices from './admin/pages/Devices';
import AdminDeviceDetails from './admin/pages/DeviceDetails';
import DeviceManufacturing from './admin/pages/DeviceManufacturing';
import UserDirectory from './admin/pages/UserDirectory';
import FarmerDetails from './admin/pages/FarmerDetails';
import AdminOrders from './admin/pages/Orders';
import AdminOrderDetails from './admin/pages/OrderDetails';
import ProductCatalog from './admin/pages/ProductCatalog';
import ProductEditor from './admin/pages/ProductEditor';

import AdminSupport from './admin/pages/Support';
import AdminTicketDetails from './admin/pages/TicketDetails';
import AdminAnalytics from './admin/pages/Analytics';
import AdminCMS from './admin/pages/CMS';
import AdminSettings from './admin/pages/settings/PlatformSettings';
import AdminProfile from './admin/pages/AdminProfile';
import KnowledgeCalibration from './admin/pages/KnowledgeCalibration';

const ProtectedRoute = () => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand"></div>
    </div>;
  }
  
  return user ? <Outlet /> : <Navigate to="/login" replace />;
};

const PublicOnlyRoute = () => {
  const { user, loading } = useAuth();
  
  if (loading) return null;
  
  if (user) {
    const adminRoles = ['super_admin', 'admin'];
    if (adminRoles.includes(user.role)) {
      return <Navigate to="/admin" replace />;
    }
    return <Navigate to="/farmer/dashboard" replace />;
  }
  
  return <Outlet />;
};

const App = () => {
  const [showLoader, setShowLoader] = useState(true);

  return (
    <AuthProvider>
      <CartProvider>
        <BrowserRouter>
          <>
            {showLoader && <TerravynLoader onComplete={() => setShowLoader(false)} />}
            <Routes>
              {/* Open Pages (Accessible to everyone) */}
              <Route path="/pricing" element={<Pricing />} />
              <Route path="/products/:slug" element={<ProductDetails />} />
              <Route path="/cart" element={<Cart />} />

              {/* Public Pages (Redirect if logged in) */}
              <Route element={<PublicOnlyRoute />}>
                <Route path="/" element={<Landing />} />
                <Route path="/login" element={<Login />} />
                <Route path="/signup" element={<Signup />} />
                <Route path="/forgot-password" element={<ForgotPassword />} />
                <Route path="/reset-password" element={<ResetPassword />} />
              </Route>
              
              {/* Protected Pages (User) */}
              <Route element={<ProtectedRoute />}>
                <Route element={<Layout />}>
                  <Route path="/farmer/dashboard" element={<FarmerDashboard />} />
                  <Route path="/irrigation" element={<IrrigationControl />} />
                  <Route path="/analytics" element={<Analytics />} />
                  <Route path="/alerts" element={<Alerts />} />
                  <Route path="/farmer/devices" element={<FarmerDevices />} />
                  <Route path="/farmer/devices/:id" element={<FarmerDeviceDetail />} />
                  <Route path="/farmer/activate-device" element={<ActivateDevice />} />
                  
                  {/* Farm Management Routes */}
                  <Route path="/farmer/farms" element={<FarmManagement />} />
                  <Route path="/farmer/farms/new" element={<FarmForm />} />
                  <Route path="/farmer/farms/:id" element={<FarmDetail />} />
                  <Route path="/farmer/farms/:id/edit" element={<FarmForm />} />
                  
                  {/* Monitoring Center Routes */}
                  <Route path="/farmer/monitoring" element={<MonitoringCenter />} />
                  <Route path="/farmer/monitoring/devices/:id" element={<MonitoringDeviceDetail />} />
                  
                  {/* Alerts Center Routes */}
                  <Route path="/farmer/alerts" element={<AlertsCenter />} />
                  <Route path="/farmer/alerts/:id" element={<AlertDetail />} />
                  
                  {/* Farmer Orders Routes */}
                  <Route path="/farmer/orders" element={<FarmerOrders />} />
                  <Route path="/farmer/orders/:id" element={<FarmerOrderDetail />} />
                  
                  {/* Support Center Routes */}
                  <Route path="/farmer/support" element={<SupportCenter />} />
                  <Route path="/farmer/support/new" element={<CreateSupportTicket />} />
                  <Route path="/farmer/support/:ticketId" element={<SupportTicketDetail />} />
                  
                  {/* Profile Route */}
                  <Route path="/farmer/profile" element={<FarmerProfile />} />
                  
                  <Route path="/profile" element={<Profile />} />
                  
                  {/* Customer Order Routes */}
                  <Route path="/orders" element={<CustomerOrders />} />
                  <Route path="/orders/:orderId" element={<CustomerOrderDetails />} />
                </Route>
              </Route>

              {/* New Admin Panel (Business Operations) */}
              <Route element={<ProtectedAdminRoute />}>
                <Route element={<AdminLayout />}>
                  <Route path="/admin" element={<AdminDashboard />} />
                  <Route path="/admin/devices" element={<AdminDevices />} />
                  <Route path="/admin/devices/manufacture" element={<DeviceManufacturing />} />
                  <Route path="/admin/devices/:deviceUid" element={<AdminDeviceDetails />} />
                  <Route path="/admin/users" element={<UserDirectory />} />
                  <Route path="/admin/users/:id" element={<FarmerDetails />} />
                  {/* Redirect legacy routes to unified directory */}
                  <Route path="/admin/farmers" element={<Navigate to="/admin/users" replace />} />
                  <Route path="/admin/customers" element={<Navigate to="/admin/users" replace />} />
                  
                  <Route path="/admin/orders" element={<AdminOrders />} />
                  <Route path="/admin/orders/:id" element={<AdminOrderDetails />} />
                  <Route path="/admin/products" element={<ProductCatalog />} />
                  <Route path="/admin/products/:id" element={<ProductEditor />} />
                  <Route path="/admin/customers/:id" element={<Navigate to="/admin/users" replace />} />
                  <Route path="/admin/support" element={<AdminSupport />} />
                  <Route path="/admin/support/:id" element={<AdminTicketDetails />} />
                  <Route path="/admin/analytics" element={<AdminAnalytics />} />
                  <Route path="/admin/calibration" element={<KnowledgeCalibration />} />
                  <Route path="/admin/cms" element={<AdminCMS />} />
                  <Route path="/admin/settings" element={<AdminSettings />} />
                  <Route path="/admin/profile" element={<AdminProfile />} />
                </Route>
              </Route>

            </Routes>
          </>
        </BrowserRouter>
      </CartProvider>
    </AuthProvider>
  );
};

export default App;
