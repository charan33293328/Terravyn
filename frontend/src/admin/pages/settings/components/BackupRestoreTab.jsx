import React, { useState, useEffect } from 'react';
import { Database, Download, Trash2, HardDrive, RefreshCw } from 'lucide-react';
import api from '../../../../api/client';

const BackupRestoreTab = () => {
  const [backups, setBackups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    fetchBackups();
  }, []);

  const fetchBackups = async () => {
    try {
      setLoading(true);
      const res = await api.get('/admin/backups');
      setBackups(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateBackup = async () => {
    try {
      setCreating(true);
      await api.post('/admin/backups');
      // Polling or waiting to refresh
      setTimeout(fetchBackups, 3000);
    } catch (err) {
      console.error(err);
      alert(err.response?.data?.detail || "Failed to initiate backup");
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this backup?")) return;
    try {
      await api.delete(`/admin/backups/${id}`);
      fetchBackups();
    } catch (err) {
      console.error(err);
      alert("Failed to delete backup");
    }
  };

  const formatBytes = (bytes, decimals = 2) => {
    if (!+bytes) return '0 Bytes'
    const k = 1024
    const dm = decimals < 0 ? 0 : decimals
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`
  }

  if (loading) return <div className="animate-pulse h-96 bg-slate-50 dark:bg-slate-950 rounded-2xl" />;

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">Backup & Restore</h2>
          <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">Manage database snapshots and disaster recovery.</p>
        </div>
        <div className="flex gap-3">
          <button onClick={fetchBackups} className="bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 px-4 py-2.5 rounded-xl font-bold text-sm hover:bg-slate-200 transition-colors flex items-center gap-2">
            <RefreshCw size={18} /> Refresh
          </button>
          <button 
            onClick={handleCreateBackup}
            disabled={creating}
            className="bg-brand text-white px-6 py-2.5 rounded-xl font-bold text-sm hover:bg-brand-dark transition-colors flex items-center gap-2 disabled:opacity-50"
          >
            {creating ? 'Processing...' : <><Database size={18} /> Create Backup</>}
          </button>
        </div>
      </div>

      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-100 dark:border-slate-800/50 overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50 dark:bg-slate-950 border-b border-slate-100 dark:border-slate-800/50">
              <th className="py-4 px-6 text-xs font-black text-slate-400 uppercase tracking-wider">File Name</th>
              <th className="py-4 px-6 text-xs font-black text-slate-400 uppercase tracking-wider">Date Created</th>
              <th className="py-4 px-6 text-xs font-black text-slate-400 uppercase tracking-wider">Size</th>
              <th className="py-4 px-6 text-xs font-black text-slate-400 uppercase tracking-wider">Status</th>
              <th className="py-4 px-6 text-xs font-black text-slate-400 uppercase tracking-wider text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800/50">
            {backups.map(b => (
              <tr key={b.id} className="hover:bg-slate-50 dark:bg-slate-950/50 transition-colors">
                <td className="py-4 px-6">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-brand/10 text-brand flex items-center justify-center shrink-0">
                      <HardDrive size={18} />
                    </div>
                    <div>
                      <p className="text-sm font-bold text-slate-900 dark:text-white">{b.file_name}</p>
                      <p className="text-xs text-slate-500 dark:text-slate-400">By {b.creator_name}</p>
                    </div>
                  </div>
                </td>
                <td className="py-4 px-6 text-sm text-slate-600 dark:text-slate-300">{new Date(b.created_at).toLocaleString()}</td>
                <td className="py-4 px-6 text-sm text-slate-600 dark:text-slate-300 font-medium">{formatBytes(b.file_size)}</td>
                <td className="py-4 px-6">
                  <span className={`inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-bold border ${
                    b.status === 'COMPLETED' ? 'bg-emerald-50 text-emerald-700 border-emerald-100' :
                    b.status === 'IN_PROGRESS' ? 'bg-blue-50 text-blue-700 border-blue-100' :
                    'bg-red-50 text-red-700 border-red-100'
                  }`}>
                    {b.status}
                  </span>
                </td>
                <td className="py-4 px-6 text-right">
                  <div className="flex justify-end gap-2">
                    <button className="w-8 h-8 rounded-lg flex items-center justify-center text-slate-400 hover:text-brand hover:bg-brand/10 transition-colors" title="Download">
                      <Download size={16} />
                    </button>
                    <button onClick={() => handleDelete(b.id)} className="w-8 h-8 rounded-lg flex items-center justify-center text-slate-400 hover:text-red-500 hover:bg-red-50 transition-colors" title="Delete">
                      <Trash2 size={16} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {backups.length === 0 && (
              <tr>
                <td colSpan="5" className="py-12 text-center text-slate-500 dark:text-slate-400 text-sm">No backups found.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default BackupRestoreTab;
