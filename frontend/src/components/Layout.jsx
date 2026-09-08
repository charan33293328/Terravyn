import React, { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Server, Droplets, Bell, BarChart3, UserCircle, Settings, HelpCircle, LogOut, Trees, Activity, Package } from 'lucide-react';
import { motion } from 'framer-motion';

const Sidebar = () => {
  const navItems = [
    { name: 'Dashboard', icon: LayoutDashboard, path: '/farmer/dashboard' },
    { name: 'Farm Management', icon: Trees, path: '/farmer/farms' },
    { name: 'My Devices', icon: Server, path: '/farmer/devices' },
    { name: 'Monitoring Center', icon: Activity, path: '/farmer/monitoring' },
    { name: 'Alerts Center', icon: Bell, path: '/farmer/alerts' },
    { name: 'Orders', icon: Package, path: '/farmer/orders' },
    { name: 'Support Center', icon: HelpCircle, path: '/farmer/support' },
    { name: 'Profile', icon: UserCircle, path: '/farmer/profile' },
  ];

  return (
    <div className="w-64 bg-white h-screen border-r border-slate-200 flex flex-col fixed left-0 top-0 z-50">
      <div className="p-6">
        <h1 className="text-2xl font-bold text-brand flex items-center gap-2">
          <Droplets className="w-6 h-6" /> TERRAVYN
        </h1>
        <p className="text-xs text-slate-500 mt-1">Smart Ag Systems</p>
      </div>
      
      <nav className="flex-1 px-4 space-y-2 mt-4 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink
            key={item.name}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-brand text-white'
                  : 'text-slate-600 hover:bg-slate-50 hover:text-brand'
              }`
            }
          >
            <item.icon className="w-5 h-5" />
            {item.name}
          </NavLink>
        ))}
      </nav>


    </div>
  );
};

const Header = () => {
  const navigate = useNavigate();
  const [profileOpen, setProfileOpen] = useState(false);

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/');
  };

  return (
    <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-8 sticky top-0 z-10">
      <div className="flex-1 max-w-xl">
        <div className="relative">
          <input
            type="text"
            placeholder="Search parameters or field sensors..."
            className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand/20 focus:border-brand transition-all"
          />
          <svg className="w-5 h-5 text-slate-400 absolute left-3 top-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
      </div>
      <div className="flex items-center gap-4">
        <button 
          onClick={() => navigate('/farmer/alerts')}
          className="text-slate-400 hover:text-slate-600 transition-colors"
        >
          <Bell className="w-5 h-5" />
        </button>
        <div className="relative">
          <button 
            onClick={() => setProfileOpen(!profileOpen)}
            className="w-8 h-8 bg-brand/10 rounded-full flex items-center justify-center text-brand font-bold text-sm focus:outline-none"
          >
            A
          </button>
          
          {profileOpen && (
            <div className="absolute right-0 mt-2 w-48 bg-white border border-slate-200 rounded-lg shadow-lg py-1 z-50">
              <button 
                onClick={() => {
                  setProfileOpen(false);
                  navigate('/farmer/profile');
                }}
                className="flex items-center gap-2 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 w-full text-left transition-colors"
              >
                <UserCircle className="w-4 h-4" /> Profile
              </button>
              <button 
                onClick={() => {
                  setProfileOpen(false);
                  navigate('/farmer/support');
                }}
                className="flex items-center gap-2 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 w-full text-left transition-colors"
              >
                <HelpCircle className="w-4 h-4" /> Support
              </button>
              <div className="border-t border-slate-100 my-1"></div>
              <button 
                onClick={handleLogout}
                className="flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 w-full text-left transition-colors"
              >
                <LogOut className="w-4 h-4" /> Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

const Layout = () => {
  return (
    <div className="flex min-h-screen bg-[#f8fafc]">
      <Sidebar />
      <div className="flex-1 ml-64 flex flex-col min-h-screen min-w-0">
        <Header />
        <main className="flex-1 p-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
          >
            <Outlet />
          </motion.div>
        </main>
      </div>
    </div>
  );
};

export default Layout;
