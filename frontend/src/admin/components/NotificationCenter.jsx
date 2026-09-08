import React, { useState, useRef, useEffect } from 'react';
import { Bell, ShoppingBag, Server, HelpCircle, Activity } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import apiClient from '../../api/client';

const NotificationCenter = () => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const fetchNotifications = async () => {
    try {
      const res = await apiClient.get('/admin/notifications?limit=20');
      if (Array.isArray(res.data)) {
        setNotifications(res.data);
        setUnreadCount(res.data.filter(n => !n.is_read).length);
      } else {
        setNotifications([]);
        setUnreadCount(0);
      }
    } catch (err) {
      console.error("Failed to fetch notifications", err);
    }
  };

  useEffect(() => {
    fetchNotifications();
    // Poll every 30 seconds
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, []);

  const markAsRead = async (id) => {
    try {
      await apiClient.put(`/admin/notifications/${id}/read`, {});
      fetchNotifications();
    } catch (err) {
      console.error("Failed to mark notification as read", err);
    }
  };

  const getIconAndColor = (type) => {
    if (type === 'ORDER') return { icon: ShoppingBag, color: 'text-emerald-500 bg-emerald-50' };
    if (type === 'ALERT') return { icon: Server, color: 'text-red-500 bg-red-50' };
    if (type === 'SYSTEM') return { icon: Activity, color: 'text-blue-500 bg-blue-50' };
    return { icon: Bell, color: 'text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-950' };
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="relative text-slate-400 hover:text-brand transition-colors p-2 rounded-full hover:bg-slate-50 dark:bg-slate-950"
      >
        <Bell className="w-5 h-5" />
        {unreadCount > 0 && (
          <span className="absolute top-1 right-1 w-2.5 h-2.5 bg-red-500 rounded-full border-2 border-white"></span>
        )}
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="absolute right-0 mt-2 w-80 bg-white dark:bg-slate-900/80 backdrop-blur-xl rounded-2xl shadow-xl border border-white/20 z-50 overflow-hidden ring-1 ring-slate-900/5"
          >
            <div className="px-4 py-3 border-b border-slate-100 dark:border-slate-800/50 flex justify-between items-center bg-white dark:bg-slate-900">
              <h3 className="font-bold text-slate-900 dark:text-white text-sm">Notifications</h3>
            </div>
            
            <div className="max-h-[400px] overflow-y-auto">
              {!Array.isArray(notifications) || notifications.length === 0 ? (
                <div className="p-4 text-center text-slate-500 dark:text-slate-400 text-sm">
                  No notifications
                </div>
              ) : (
                notifications.map((notif) => {
                  const { icon: Icon, color } = getIconAndColor(notif.type);
                  return (
                    <div 
                      key={notif.id} 
                      className={`p-4 border-b border-slate-50 flex gap-3 hover:bg-slate-50 dark:bg-slate-950/50 transition-colors cursor-pointer ${notif.is_read ? 'opacity-60' : ''}`}
                      onClick={() => !notif.is_read && markAsRead(notif.id)}
                    >
                      <div className={`p-2 rounded-xl h-fit ${color}`}>
                        <Icon size={16} />
                      </div>
                      <div className="flex-1">
                        <p className="text-sm text-slate-700 dark:text-slate-200 font-medium leading-tight mb-1">{notif.message}</p>
                        <span className="text-xs font-semibold text-slate-400">{new Date(notif.created_at).toLocaleString()}</span>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
            
            <div className="p-2 bg-slate-50 dark:bg-slate-950 border-t border-slate-100 dark:border-slate-800/50 text-center">
              <button className="text-xs font-bold text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:text-slate-200 transition-colors">
                View All History
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default NotificationCenter;
