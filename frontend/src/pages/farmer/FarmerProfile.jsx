import React, { useState } from 'react';
import { UserCircle, Shield, Bell, Settings, Activity } from 'lucide-react';
import PersonalInfoTab from '../../components/profile/PersonalInfoTab';
import SecuritySettingsTab from '../../components/profile/SecuritySettingsTab';
import NotificationPreferencesTab from '../../components/profile/NotificationPreferencesTab';
import AccountSettingsTab from '../../components/profile/AccountSettingsTab';
import ActivityHistoryTab from '../../components/profile/ActivityHistoryTab';

export default function FarmerProfile() {
  const [activeTab, setActiveTab] = useState('personal');

  const tabs = [
    { id: 'personal', name: 'Personal Information', icon: UserCircle },
    { id: 'security', name: 'Security Settings', icon: Shield },
    { id: 'notifications', name: 'Notification Preferences', icon: Bell },
    { id: 'account', name: 'Account Settings', icon: Settings },
    { id: 'activity', name: 'Activity History', icon: Activity },
  ];

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">My Profile</h1>
        <p className="text-slate-500 mt-1">Manage your personal information, security settings, and account preferences.</p>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden flex flex-col md:flex-row min-h-[600px]">
        {/* Sidebar Tabs */}
        <div className="w-full md:w-64 bg-slate-50 border-r border-slate-200 p-4 shrink-0">
          <nav className="space-y-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors ${
                  activeTab === tab.id
                    ? 'bg-emerald-50 text-emerald-700'
                    : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                }`}
              >
                <tab.icon className={`h-5 w-5 ${activeTab === tab.id ? 'text-emerald-600' : 'text-slate-400'}`} />
                {tab.name}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="flex-1 p-6 lg:p-8">
          {activeTab === 'personal' && <PersonalInfoTab />}
          {activeTab === 'security' && <SecuritySettingsTab />}
          {activeTab === 'notifications' && <NotificationPreferencesTab />}
          {activeTab === 'account' && <AccountSettingsTab />}
          {activeTab === 'activity' && <ActivityHistoryTab />}
        </div>
      </div>
    </div>
  );
}
