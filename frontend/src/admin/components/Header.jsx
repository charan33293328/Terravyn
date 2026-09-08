import React from 'react';
import { Menu } from 'lucide-react';
import NotificationCenter from './NotificationCenter';
import ProfileDropdown from './ProfileDropdown';
import ThemeToggle from './ThemeToggle';
import { useAuth } from '../../context/AuthContext';
import { useLocation } from 'react-router-dom';

const Header = ({ onMenuClick }) => {
  const { user } = useAuth();
  const location = useLocation();

  // Simple logic to derive page title from path
  const getPageTitle = () => {
    const path = location.pathname.replace('/admin', '');
    if (!path || path === '/') return 'Dashboard';
    const segment = path.split('/')[1];
    return segment.charAt(0).toUpperCase() + segment.slice(1).replace('-', ' ');
  };

  return (
    <header className="h-16 bg-white dark:bg-slate-900/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 flex items-center justify-between px-4 lg:px-8 sticky top-0 z-10 shadow-sm transition-all">
      <div className="flex items-center gap-4">
        <button onClick={onMenuClick} className="lg:hidden text-slate-500 dark:text-slate-400 hover:text-brand transition-colors p-2 rounded-lg hover:bg-slate-50 dark:bg-slate-950 dark:hover:bg-slate-800">
          <Menu size={24} />
        </button>
        <h1 className="text-xl font-black text-slate-900 dark:text-white hidden sm:block tracking-tight">
          {getPageTitle()}
        </h1>
      </div>
      
      <div className="flex items-center gap-2 sm:gap-6">
        <ThemeToggle />
        <NotificationCenter />
        <div className="w-px h-8 bg-slate-200 dark:bg-slate-700 hidden sm:block"></div>
        <ProfileDropdown user={user} />
      </div>
    </header>
  );
};

export default Header;
