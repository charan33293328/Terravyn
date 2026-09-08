import React, { useState } from 'react';
import { Settings, Image as ImageIcon, CreditCard, Mail, Bell, HardDrive, ShieldCheck, Users, Wrench, SaveAll, ClipboardList } from 'lucide-react';

import GeneralSettingsTab from './components/GeneralSettingsTab';
import BrandingSettingsTab from './components/BrandingSettingsTab';
import PaymentSettingsTab from './components/PaymentSettingsTab';
import EmailSettingsTab from './components/EmailSettingsTab';
import NotificationSettingsTab from './components/NotificationSettingsTab';
import DeviceSettingsTab from './components/DeviceSettingsTab';
import SecuritySettingsTab from './components/SecuritySettingsTab';
import RoleManagementTab from './components/RoleManagementTab';
import MaintenanceTab from './components/MaintenanceTab';
import BackupRestoreTab from './components/BackupRestoreTab';
import AuditLogsTab from './components/AuditLogsTab';

const TABS = [
  { id: 'general', name: 'General', icon: Settings },
  { id: 'branding', name: 'Branding', icon: ImageIcon },
  { id: 'payment', name: 'Payment', icon: CreditCard },
  { id: 'email', name: 'Email (SMTP)', icon: Mail },
  { id: 'notifications', name: 'Notifications', icon: Bell },
  { id: 'devices', name: 'Devices', icon: HardDrive },
  { id: 'security', name: 'Security', icon: ShieldCheck },
  { id: 'roles', name: 'Roles & Permissions', icon: Users },
  { id: 'maintenance', name: 'Maintenance Mode', icon: Wrench },
  { id: 'backup', name: 'Backup & Restore', icon: SaveAll },
  { id: 'audit', name: 'Audit Logs', icon: ClipboardList },
];

const PlatformSettings = () => {
  const [activeTab, setActiveTab] = useState('general');

  return (
    <div className="flex flex-col md:flex-row gap-6 h-[calc(100vh-8rem)]">
      
      {/* Sidebar Navigation */}
      <div className="w-full md:w-64 shrink-0 bg-white dark:bg-slate-900 rounded-3xl p-4 border border-slate-100 dark:border-slate-800/50 shadow-sm overflow-y-auto custom-scrollbar">
        <h2 className="text-xs font-black text-slate-400 uppercase tracking-wider mb-4 px-2">Platform Settings</h2>
        <nav className="space-y-1">
          {TABS.map(tab => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl font-bold text-sm transition-colors ${
                  isActive 
                    ? 'bg-slate-900 text-white' 
                    : 'text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:bg-slate-950 hover:text-slate-900 dark:text-white'
                }`}
              >
                <Icon size={18} className={isActive ? 'text-white' : 'text-slate-400'} />
                {tab.name}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 bg-white dark:bg-slate-900 rounded-3xl p-6 md:p-8 border border-slate-100 dark:border-slate-800/50 shadow-sm overflow-y-auto custom-scrollbar">
        {activeTab === 'general' && <GeneralSettingsTab />}
        {activeTab === 'branding' && <BrandingSettingsTab />}
        {activeTab === 'payment' && <PaymentSettingsTab />}
        {activeTab === 'email' && <EmailSettingsTab />}
        {activeTab === 'notifications' && <NotificationSettingsTab />}
        {activeTab === 'devices' && <DeviceSettingsTab />}
        {activeTab === 'security' && <SecuritySettingsTab />}
        {activeTab === 'roles' && <RoleManagementTab />}
        {activeTab === 'maintenance' && <MaintenanceTab />}
        {activeTab === 'backup' && <BackupRestoreTab />}
        {activeTab === 'audit' && <AuditLogsTab />}
      </div>

    </div>
  );
};

export default PlatformSettings;
