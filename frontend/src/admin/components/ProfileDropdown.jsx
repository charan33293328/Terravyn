import React, { useState, useRef, useEffect } from 'react';
import { User, LogOut } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

const ProfileDropdown = ({ user }) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/');
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-3 hover:bg-slate-50 dark:bg-slate-950 p-1.5 pr-3 rounded-full transition-colors border border-transparent hover:border-slate-100 dark:border-slate-800/50"
      >
        <div className="hidden md:block text-right">
          <div className="text-sm font-bold text-slate-900 dark:text-white leading-tight">{user?.full_name || 'Administrator'}</div>
          <div className="text-xs text-brand font-medium uppercase">{user?.role?.replace('_', ' ')}</div>
        </div>
        <div className="w-9 h-9 bg-brand/10 rounded-full flex items-center justify-center text-brand font-bold border border-brand/20 shadow-sm">
          {user?.full_name?.charAt(0) || 'A'}
        </div>
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="absolute right-0 mt-2 w-56 bg-white dark:bg-slate-900/90 backdrop-blur-xl rounded-2xl shadow-xl border border-white/20 z-50 overflow-hidden ring-1 ring-slate-900/5"
          >
            <div className="p-4 border-b border-slate-100 dark:border-slate-800/50 bg-white dark:bg-slate-900">
              <p className="text-sm font-bold text-slate-900 dark:text-white">{user?.full_name}</p>
              <p className="text-xs text-slate-500 dark:text-slate-400 truncate">{user?.email}</p>
            </div>
            
            <div className="p-2 space-y-1">
              <button 
                onClick={() => {
                  setIsOpen(false);
                  navigate('/admin/profile');
                }}
                className="flex items-center gap-2 w-full px-3 py-2 text-sm text-slate-600 dark:text-slate-300 hover:text-brand hover:bg-brand/5 rounded-xl transition-colors font-medium"
              >
                <User size={16} /> Edit Profile
              </button>
            </div>
            
            <div className="p-2 border-t border-slate-100 dark:border-slate-800/50 bg-slate-50 dark:bg-slate-950">
              <button 
                onClick={handleLogout}
                className="flex items-center gap-2 w-full px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-xl transition-colors font-medium"
              >
                <LogOut size={16} /> Sign out
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ProfileDropdown;
