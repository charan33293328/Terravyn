import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Search, Filter, Download, Eye,
  CheckCircle2, XCircle, ShoppingBag, Smartphone, Users
} from 'lucide-react';
import apiClient from '../../api/client';

const Farmers = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('ALL');

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get('/admin/customers');
      setUsers(Array.isArray(res.data) ? res.data : []);
    } catch (err) {
      console.error('Failed to fetch users:', err);
      setUsers([]);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      const res = await apiClient.get('/admin/customers/export', { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'Farmers_Export.xlsx');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Export failed:', err);
    }
  };

  const filteredUsers = (users || []).filter(user => {
    const q = search.toLowerCase();
    const matchesSearch =
      (user.full_name || '').toLowerCase().includes(q) ||
      (user.email || '').toLowerCase().includes(q) ||
      (user.phone_number || '').includes(search);

    let matchesFilter = true;
    if (filter === 'ACTIVE') matchesFilter = user.is_active === true;
    if (filter === 'INACTIVE') matchesFilter = user.is_active === false;
    if (filter === 'WITH_DEVICES') matchesFilter = user.total_devices > 0;
    if (filter === 'WITH_ORDERS') matchesFilter = user.total_orders > 0;

    return matchesSearch && matchesFilter;
  });

  return (
    <div className="space-y-6">

      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center justify-between">
        <div className="flex flex-col sm:flex-row gap-3 flex-1">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Search by name, email, or phone..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl focus:ring-2 focus:ring-brand focus:border-brand text-sm"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter className="text-slate-400 w-4 h-4" />
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-2.5 text-sm focus:ring-brand focus:border-brand"
            >
              <option value="ALL">All Farmers</option>
              <option value="ACTIVE">Active</option>
              <option value="INACTIVE">Inactive</option>
              <option value="WITH_DEVICES">With Devices</option>
              <option value="WITH_ORDERS">With Orders</option>
            </select>
          </div>
        </div>
        <button
          onClick={handleExport}
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-200 font-medium rounded-xl hover:bg-slate-50 dark:bg-slate-950 transition-colors shadow-sm"
        >
          <Download size={16} />
          Export Excel
        </button>
      </div>

      {/* Table */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 dark:bg-slate-950 border-b border-slate-200 dark:border-slate-800 text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400">
                <th className="px-6 py-4 font-semibold">Farmer</th>
                <th className="px-6 py-4 font-semibold">Contact</th>
                <th className="px-6 py-4 font-semibold text-center">Status</th>
                <th className="px-6 py-4 font-semibold text-center">
                  <div className="flex items-center justify-center gap-1">
                    <ShoppingBag size={13} /> Orders
                  </div>
                </th>
                <th className="px-6 py-4 font-semibold text-center">
                  <div className="flex items-center justify-center gap-1">
                    <Smartphone size={13} /> Devices
                  </div>
                </th>
                <th className="px-6 py-4 font-semibold">Registered</th>
                <th className="px-6 py-4 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/50">
              {loading ? (
                <tr>
                  <td colSpan="7" className="px-6 py-14 text-center text-slate-500 dark:text-slate-400">
                    <div className="animate-spin w-8 h-8 border-4 border-brand border-t-transparent rounded-full mx-auto mb-3" />
                    Loading farmers...
                  </td>
                </tr>
              ) : filteredUsers.length === 0 ? (
                <tr>
                  <td colSpan="7" className="px-6 py-16 text-center text-slate-400">
                    <Users className="w-10 h-10 mx-auto mb-3 opacity-30" />
                    <p className="font-medium text-slate-500 dark:text-slate-400">No farmers found</p>
                    <p className="text-xs mt-1">Farmers appear here once they create an account on the app.</p>
                  </td>
                </tr>
              ) : (
                filteredUsers.map((user) => (
                  <tr key={user.id} className="hover:bg-slate-50 dark:bg-slate-950 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-full bg-brand/10 flex items-center justify-center text-brand font-bold text-sm shrink-0">
                          {(user.full_name || 'U').charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <div className="font-semibold text-slate-900 dark:text-white">{user.full_name || 'Unknown'}</div>
                          <div className="text-xs text-slate-400 font-mono">ID: {user.id}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-slate-800 dark:text-slate-100">{user.email}</div>
                      <div className="text-xs text-slate-400 mt-0.5">{user.phone_number || 'N/A'}</div>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
                        user.is_active
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                          : 'bg-red-50 text-red-700 border-red-200'
                      }`}>
                        {user.is_active ? <CheckCircle2 size={12} /> : <XCircle size={12} />}
                        {user.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <div className="inline-flex items-center justify-center bg-amber-50 text-amber-700 w-8 h-8 rounded-lg font-bold text-sm">
                        {user.total_orders || 0}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <div className="inline-flex items-center justify-center bg-blue-50 text-blue-700 w-8 h-8 rounded-lg font-bold text-sm">
                        {user.total_devices || 0}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-slate-700 dark:text-slate-200">
                        {user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link
                        to={`/admin/users/${user.id}`}
                        className="inline-flex items-center justify-center p-2 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-brand hover:text-white rounded-lg transition-colors"
                        title="View Details"
                      >
                        <Eye size={16} />
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Footer summary */}
        {!loading && filteredUsers.length > 0 && (
          <div className="px-6 py-3 bg-slate-50 dark:bg-slate-950 border-t border-slate-100 dark:border-slate-800/50 text-xs text-slate-500 dark:text-slate-400">
            Showing {filteredUsers.length} of {users.length} registered farmers
          </div>
        )}
      </div>
    </div>
  );
};

export default Farmers;
