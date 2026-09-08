import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft, User, Phone, Mail, MapPin, ShoppingBag,
  Smartphone, Activity, CheckCircle2, XCircle, Power, PowerOff,
  Calendar, Ticket, Package, Clock
} from 'lucide-react';
import apiClient from '../../api/client';

const statusColors = {
  DELIVERED: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  SHIPPED: 'bg-blue-50 text-blue-700 border-blue-200',
  PROCESSING: 'bg-amber-50 text-amber-700 border-amber-200',
  PENDING: 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-800',
  CANCELLED: 'bg-red-50 text-red-700 border-red-200',
};

const FarmerDetails = () => {
  const { id } = useParams();
  const [farmer, setFarmer] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isUpdating, setIsUpdating] = useState(false);

  useEffect(() => {
    fetchDetails();
  }, [id]);

  const fetchDetails = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get(`/admin/customers/${id}`);
      setFarmer(res.data);
    } catch (err) {
      console.error('Failed to fetch farmer details:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleStatus = async () => {
    if (!farmer) return;
    setIsUpdating(true);
    try {
      const action = farmer.is_active ? 'disable' : 'activate';
      await apiClient.put(`/admin/customers/${id}/${action}`);
      setFarmer(prev => ({ ...prev, is_active: !prev.is_active }));
    } catch (err) {
      console.error('Failed to update status:', err);
      alert('Failed to update status. Please try again.');
    } finally {
      setIsUpdating(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-32">
        <div className="animate-spin w-10 h-10 border-4 border-brand border-t-transparent rounded-full" />
      </div>
    );
  }

  if (!farmer) {
    return (
      <div className="flex flex-col items-center justify-center py-32 text-center">
        <User className="w-12 h-12 text-slate-300 mb-4" />
        <h2 className="text-lg font-bold text-slate-700 dark:text-slate-200">Farmer not found</h2>
        <Link to="/admin/users" className="mt-4 text-brand text-sm font-medium hover:underline flex items-center gap-1">
          <ArrowLeft size={14} /> Back to Farmers
        </Link>
      </div>
    );
  }

  const info = farmer.personal_information || {};

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link
            to="/admin/users"
            className="p-2 hover:bg-slate-100 dark:bg-slate-800 rounded-xl transition-colors text-slate-500 dark:text-slate-400"
          >
            <ArrowLeft size={20} />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">{info.full_name || 'Unknown'}</h1>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">Farmer #{id}</p>
          </div>
        </div>

        <button
          onClick={toggleStatus}
          disabled={isUpdating}
          className={`inline-flex items-center gap-2 px-4 py-2.5 rounded-xl font-medium text-sm transition-colors disabled:opacity-60 ${
            farmer.is_active
              ? 'bg-red-50 text-red-600 border border-red-200 hover:bg-red-100'
              : 'bg-emerald-50 text-emerald-600 border border-emerald-200 hover:bg-emerald-100'
          }`}
        >
          {farmer.is_active ? <PowerOff size={16} /> : <Power size={16} />}
          {isUpdating ? 'Updating...' : farmer.is_active ? 'Deactivate Account' : 'Activate Account'}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column */}
        <div className="space-y-6">
          {/* Profile Card */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm p-6">
            <div className="flex flex-col items-center text-center mb-6">
              <div className="w-20 h-20 rounded-full bg-brand/10 flex items-center justify-center text-brand font-bold text-3xl mb-3">
                {(info.full_name || 'U').charAt(0).toUpperCase()}
              </div>
              <h2 className="font-bold text-slate-900 dark:text-white text-lg">{info.full_name || 'Unknown'}</h2>
              <span className={`mt-2 inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border ${
                farmer.is_active
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                  : 'bg-red-50 text-red-700 border-red-200'
              }`}>
                {farmer.is_active ? <CheckCircle2 size={12} /> : <XCircle size={12} />}
                {farmer.is_active ? 'Active' : 'Inactive'}
              </span>
            </div>

            <div className="space-y-3">
              <div className="flex items-start gap-3">
                <Mail className="w-4 h-4 text-slate-400 mt-0.5 shrink-0" />
                <span className="text-sm text-slate-700 dark:text-slate-200 break-all">{info.email || 'N/A'}</span>
              </div>
              <div className="flex items-start gap-3">
                <Phone className="w-4 h-4 text-slate-400 mt-0.5 shrink-0" />
                <span className="text-sm text-slate-700 dark:text-slate-200">{info.phone_number || 'N/A'}</span>
              </div>
              {info.address && info.address !== 'N/A' && (
                <div className="flex items-start gap-3">
                  <MapPin className="w-4 h-4 text-slate-400 mt-0.5 shrink-0" />
                  <span className="text-sm text-slate-700 dark:text-slate-200">{info.address}</span>
                </div>
              )}
            </div>
          </div>

          {/* Activity Summary */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm p-6">
            <h3 className="font-bold text-slate-800 dark:text-slate-100 mb-4 flex items-center gap-2">
              <Activity size={16} className="text-brand" /> Activity Summary
            </h3>
            <div className="grid grid-cols-3 gap-3">
              <div className="bg-amber-50 rounded-xl p-3 text-center border border-amber-100">
                <p className="text-2xl font-bold text-amber-700">{(farmer.order_history || []).length}</p>
                <p className="text-xs text-amber-600 mt-1">Orders</p>
              </div>
              <div className="bg-blue-50 rounded-xl p-3 text-center border border-blue-100">
                <p className="text-2xl font-bold text-blue-700">{(farmer.device_ownership || []).length}</p>
                <p className="text-xs text-blue-600 mt-1">Devices</p>
              </div>
              <div className="bg-purple-50 rounded-xl p-3 text-center border border-purple-100">
                <p className="text-2xl font-bold text-purple-700">{farmer.activity_information?.total_support_tickets || 0}</p>
                <p className="text-xs text-purple-600 mt-1">Tickets</p>
              </div>
            </div>
            <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800/50 flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
              <Calendar size={13} />
              Registered: {farmer.activity_information?.registration_date
                ? new Date(farmer.activity_information.registration_date).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
                : 'N/A'}
            </div>
          </div>
        </div>

        {/* Right Column */}
        <div className="lg:col-span-2 space-y-6">
          {/* Order History */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-800/50 flex items-center gap-2">
              <ShoppingBag size={16} className="text-brand" />
              <h3 className="font-bold text-slate-800 dark:text-slate-100">Order History</h3>
              <span className="ml-auto text-xs font-medium bg-slate-100 dark:bg-slate-800 px-2.5 py-1 rounded-full text-slate-600 dark:text-slate-300">
                {(farmer.order_history || []).length} orders
              </span>
            </div>
            {(farmer.order_history || []).length === 0 ? (
              <div className="px-6 py-10 text-center text-slate-400">
                <Package className="w-8 h-8 mx-auto mb-2 opacity-30" />
                <p className="text-sm">No orders placed yet.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="bg-slate-50 dark:bg-slate-950 text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400 border-b border-slate-100 dark:border-slate-800/50">
                      <th className="px-6 py-3 font-semibold">Order ID</th>
                      <th className="px-6 py-3 font-semibold">Date</th>
                      <th className="px-6 py-3 font-semibold text-center">Status</th>
                      <th className="px-6 py-3 font-semibold text-right">Amount</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-50">
                    {(farmer.order_history || []).map(order => (
                      <tr key={order.order_id} className="hover:bg-slate-50 dark:bg-slate-950 transition-colors">
                        <td className="px-6 py-3">
                          <Link
                            to={`/admin/orders/${order.order_id}`}
                            className="font-mono text-brand hover:underline text-xs font-medium"
                          >
                            {order.order_id}
                          </Link>
                        </td>
                        <td className="px-6 py-3 text-slate-600 dark:text-slate-300">
                          <div className="flex items-center gap-1.5">
                            <Clock size={12} className="text-slate-400" />
                            {order.created_at ? new Date(order.created_at).toLocaleDateString() : 'N/A'}
                          </div>
                        </td>
                        <td className="px-6 py-3 text-center">
                          <span className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-medium border ${statusColors[order.order_status] || 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-800'}`}>
                            {order.order_status || 'N/A'}
                          </span>
                        </td>
                        <td className="px-6 py-3 text-right font-semibold text-slate-800 dark:text-slate-100">
                          ₹{order.total_amount?.toLocaleString('en-IN') || '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Devices */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-800/50 flex items-center gap-2">
              <Smartphone size={16} className="text-brand" />
              <h3 className="font-bold text-slate-800 dark:text-slate-100">Devices</h3>
              <span className="ml-auto text-xs font-medium bg-slate-100 dark:bg-slate-800 px-2.5 py-1 rounded-full text-slate-600 dark:text-slate-300">
                {(farmer.device_ownership || []).length} devices
              </span>
            </div>
            {(farmer.device_ownership || []).length === 0 ? (
              <div className="px-6 py-10 text-center text-slate-400">
                <Smartphone className="w-8 h-8 mx-auto mb-2 opacity-30" />
                <p className="text-sm">No devices assigned yet.</p>
              </div>
            ) : (
              <div className="divide-y divide-slate-50">
                {(farmer.device_ownership || []).map((device, i) => (
                  <div key={i} className="px-6 py-3 flex items-center justify-between hover:bg-slate-50 dark:bg-slate-950">
                    <div>
                      <p className="font-mono text-sm font-semibold text-slate-800 dark:text-slate-100">{device.device_uid || 'N/A'}</p>
                      {device.claimed_at && (
                        <p className="text-xs text-slate-400 mt-0.5">
                          Claimed: {new Date(device.claimed_at).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                    <span className={`px-2.5 py-1 rounded-full text-xs font-medium border ${
                      device.is_active
                        ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                        : 'bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 border-slate-200 dark:border-slate-800'
                    }`}>
                      {device.status || 'Unknown'}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default FarmerDetails;
