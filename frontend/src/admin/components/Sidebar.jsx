import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, Server, ShoppingBag, Users, HelpCircle, 
  BarChart3, Globe, Settings, Droplets, X, FileText, Tag, Cpu, ShieldCheck
} from 'lucide-react';

const Sidebar = ({ isOpen, setIsOpen }) => {
  const navItems = [
    { name: 'Dashboard', icon: LayoutDashboard, path: '/admin' },
    { name: 'Devices', icon: Server, path: '/admin/devices' },
    { name: 'Manufacturing', icon: Cpu, path: '/admin/devices/manufacture' },
    { name: 'Farmers', icon: Users, path: '/admin/users' },
    { name: 'Products', icon: Tag, path: '/admin/products' },
    { name: 'Orders', icon: ShoppingBag, path: '/admin/orders' },
    { name: 'Support', icon: HelpCircle, path: '/admin/support' },
    { name: 'Analytics', icon: BarChart3, path: '/admin/analytics' },
    { name: 'Validation & Calibration', icon: ShieldCheck, path: '/admin/calibration' },
    { name: 'Content Management', icon: FileText, path: '/admin/cms' },
    { name: 'Settings', icon: Settings, path: '/admin/settings' },
  ];

  return (
    <>
      {/* Mobile Overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-slate-900/50 z-20 lg:hidden backdrop-blur-sm transition-opacity"
          onClick={() => setIsOpen(false)}
        />
      )}
      
      {/* Sidebar Container */}
      <div className={`fixed inset-y-0 left-0 w-64 bg-slate-900 text-slate-300 transform transition-transform duration-300 ease-in-out z-30 shadow-2xl lg:translate-x-0 ${isOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        
        {/* Brand Header */}
        <div className="h-16 flex items-center justify-between px-6 bg-slate-950 border-b border-slate-800">
          <div className="flex items-center gap-2 text-white font-black text-xl tracking-tight">
            <Droplets className="text-brand w-6 h-6" /> TERRAVYN
          </div>
          <button className="lg:hidden text-slate-400 hover:text-white transition-colors" onClick={() => setIsOpen(false)}>
            <X size={20} />
          </button>
        </div>
        
        {/* Navigation */}
        <div className="px-4 py-6 overflow-y-auto h-[calc(100vh-4rem)] custom-scrollbar">
          <div className="text-[10px] font-black text-slate-500 dark:text-slate-400 uppercase tracking-[0.2em] mb-4 px-2">Control Center</div>
          <nav className="space-y-1.5">
            {navItems.map((item) => (
              <NavLink
                key={item.name}
                to={item.path}
                end={item.path === '/admin'}
                onClick={() => setIsOpen(false)}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-bold transition-all duration-200 ${
                    isActive
                      ? 'bg-brand text-white shadow-md shadow-brand/20 translate-x-1'
                      : 'hover:bg-slate-800 hover:text-white text-slate-400'
                  }`
                }
              >
                <item.icon className={`w-5 h-5 ${item.path === '/admin' ? '' : 'opacity-80'}`} />
                {item.name}
              </NavLink>
            ))}
          </nav>
        </div>
      </div>
    </>
  );
};

export default Sidebar;
