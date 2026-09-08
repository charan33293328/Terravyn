import React, { useState, useEffect } from 'react';
import { Activity, Shield, Settings, Server, Users } from 'lucide-react';
import api from '../../../../api/client';

const AuditLogsTab = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLogs();
  }, []);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const res = await api.get('/admin/audit-logs');
      setLogs(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="animate-pulse h-96 bg-slate-50 dark:bg-slate-950 rounded-2xl" />;

  const getIconForResource = (resource) => {
    if (resource.includes('Role') || resource.includes('User')) return Users;
    if (resource.includes('Security')) return Shield;
    if (resource.includes('System') || resource.includes('Backup')) return Server;
    if (resource.includes('Settings')) return Settings;
    return Activity;
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">Audit Logs</h2>
          <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">Review chronological records of administrative actions.</p>
        </div>
      </div>

      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-100 dark:border-slate-800/50 overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50 dark:bg-slate-950 border-b border-slate-100 dark:border-slate-800/50">
              <th className="py-4 px-6 text-xs font-black text-slate-400 uppercase tracking-wider">Action</th>
              <th className="py-4 px-6 text-xs font-black text-slate-400 uppercase tracking-wider">Admin</th>
              <th className="py-4 px-6 text-xs font-black text-slate-400 uppercase tracking-wider">Resource</th>
              <th className="py-4 px-6 text-xs font-black text-slate-400 uppercase tracking-wider">IP Address</th>
              <th className="py-4 px-6 text-xs font-black text-slate-400 uppercase tracking-wider text-right">Timestamp</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800/50">
            {logs.map(log => {
              const Icon = getIconForResource(log.resource);
              return (
                <tr key={log.id} className="hover:bg-slate-50 dark:bg-slate-950/50 transition-colors">
                  <td className="py-4 px-6">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 flex items-center justify-center shrink-0">
                        <Icon size={14} />
                      </div>
                      <p className="text-sm font-bold text-slate-900 dark:text-white">{log.action}</p>
                    </div>
                  </td>
                  <td className="py-4 px-6 text-sm text-slate-600 dark:text-slate-300 font-medium">{log.admin_name}</td>
                  <td className="py-4 px-6">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-wider bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                      {log.resource}
                    </span>
                  </td>
                  <td className="py-4 px-6 text-sm text-slate-500 dark:text-slate-400 font-mono text-xs">{log.ip_address}</td>
                  <td className="py-4 px-6 text-right text-sm text-slate-500 dark:text-slate-400">{new Date(log.timestamp).toLocaleString()}</td>
                </tr>
              );
            })}
            {logs.length === 0 && (
              <tr>
                <td colSpan="5" className="py-12 text-center text-slate-500 dark:text-slate-400 text-sm">No audit logs found.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AuditLogsTab;
