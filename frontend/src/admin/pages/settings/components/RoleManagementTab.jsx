import React, { useState, useEffect } from 'react';
import { Plus, Edit2, Trash2, Users, ShieldCheck } from 'lucide-react';
import api from '../../../../api/client';

const RoleManagementTab = () => {
  const [roles, setRoles] = useState([]);
  const [permissions, setPermissions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [rolesRes, permsRes] = await Promise.all([
        api.get('/admin/roles'),
        api.get('/admin/permissions')
      ]);
      setRoles(rolesRes.data);
      setPermissions(permsRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this role?")) return;
    try {
      await api.delete(`/admin/roles/${id}`);
      fetchData();
    } catch (err) {
      console.error(err);
      alert(err.response?.data?.detail || "Failed to delete role");
    }
  };

  if (loading) return <div className="animate-pulse h-96 bg-slate-50 dark:bg-slate-950 rounded-2xl" />;

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">Roles & Permissions</h2>
          <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">Manage administrative roles and configure granular access.</p>
        </div>
        <button className="bg-brand text-white px-4 py-2.5 rounded-xl font-bold text-sm hover:bg-brand-dark transition-colors flex items-center gap-2">
          <Plus size={18} /> New Role
        </button>
      </div>

      <div className="space-y-4">
        {roles.map(role => (
          <div key={role.id} className="bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800/50 rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="font-bold text-lg text-slate-900 dark:text-white">{role.name}</h3>
                  {role.is_system && (
                    <span className="px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-wider bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">System</span>
                  )}
                </div>
                <p className="text-sm text-slate-500 dark:text-slate-400">{role.description}</p>
              </div>
              <div className="flex items-center gap-2">
                <button className="w-8 h-8 rounded-lg flex items-center justify-center text-slate-400 hover:text-brand hover:bg-brand/10 transition-colors">
                  <Edit2 size={16} />
                </button>
                {!role.is_system && (
                  <button onClick={() => handleDelete(role.id)} className="w-8 h-8 rounded-lg flex items-center justify-center text-slate-400 hover:text-red-500 hover:bg-red-50 transition-colors">
                    <Trash2 size={16} />
                  </button>
                )}
              </div>
            </div>

            <div className="mt-6">
              <h4 className="text-xs font-black text-slate-400 uppercase tracking-wider mb-3">Assigned Permissions</h4>
              <div className="flex flex-wrap gap-2">
                {role.permissions?.length > 0 ? (
                  role.permissions.map(p => (
                    <span key={p.id} className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-700 text-xs font-medium border border-emerald-100">
                      <ShieldCheck size={12} />
                      {p.name}
                    </span>
                  ))
                ) : (
                  <span className="text-xs text-slate-400 italic">No permissions assigned</span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default RoleManagementTab;
