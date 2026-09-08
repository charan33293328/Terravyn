import React, { useState, useEffect } from 'react';
import { ShoppingBag, Search, Filter, Download, Eye, Clock, CheckCircle2, XCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import apiClient from '../../api/client';

const Orders = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [paymentFilter, setPaymentFilter] = useState('');
  const [stats, setStats] = useState({ total: 0, pending: 0, delivered: 0 });

  const fetchOrders = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const params = { limit: 100 };
      if (search) params.search = search;
      if (statusFilter) params.status = statusFilter;
      if (paymentFilter) params.payment_status = paymentFilter;

      const res = await apiClient.get('/admin/orders', { params });
      
      const items = res.data.items || [];
      setOrders(items);
      
      // Basic stats calculation for top cards based on fetched items
      const pending = items.filter(o => ['PENDING', 'PROCESSING'].includes(o.order_status)).length;
      const delivered = items.filter(o => o.order_status === 'DELIVERED').length;
      setStats({ total: res.data.total || 0, pending, delivered });

    } catch (err) {
      console.error("Failed to fetch orders", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, [search, statusFilter, paymentFilter]);

  const handleExport = async () => {
    try {
      const token = localStorage.getItem('token');
      const params = {};
      if (search) params.search = search;
      if (statusFilter) params.status = statusFilter;
      if (paymentFilter) params.payment_status = paymentFilter;

      const res = await apiClient.get('/admin/orders/export', {
        params,
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'terravyn_orders.xlsx');
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
    } catch (err) {
      console.error("Failed to export orders", err);
      alert("Failed to export. Please make sure openpyxl and pandas are installed in the backend.");
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'PENDING': return <span className="px-2.5 py-1 bg-amber-100 text-amber-700 rounded-full text-xs font-bold">PENDING</span>;
      case 'PROCESSING': return <span className="px-2.5 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-bold">PROCESSING</span>;
      case 'SHIPPED': return <span className="px-2.5 py-1 bg-indigo-100 text-indigo-700 rounded-full text-xs font-bold">SHIPPED</span>;
      case 'DELIVERED': return <span className="px-2.5 py-1 bg-emerald-100 text-emerald-700 rounded-full text-xs font-bold">DELIVERED</span>;
      case 'CANCELLED': return <span className="px-2.5 py-1 bg-red-100 text-red-700 rounded-full text-xs font-bold">CANCELLED</span>;
      default: return <span className="px-2.5 py-1 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 rounded-full text-xs font-bold">{status}</span>;
    }
  };

  const getPaymentBadge = (status) => {
    if (['SUCCESS', 'PAID'].includes(status)) return <span className="px-2 py-1 bg-emerald-50 text-emerald-600 rounded text-xs font-bold flex items-center gap-1"><CheckCircle2 size={12} /> PAID</span>;
    if (status === 'COD_PENDING') return <span className="px-2 py-1 bg-amber-50 text-amber-600 rounded text-xs font-bold flex items-center gap-1"><Clock size={12} /> COD PENDING</span>;
    if (status === 'COD_COLLECTED') return <span className="px-2 py-1 bg-blue-50 text-blue-600 rounded text-xs font-bold flex items-center gap-1"><CheckCircle2 size={12} /> COD COLLECTED</span>;
    if (status === 'FAILED') return <span className="px-2 py-1 bg-red-50 text-red-600 rounded text-xs font-bold flex items-center gap-1"><XCircle size={12} /> FAILED</span>;
    return <span className="px-2 py-1 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 rounded text-xs font-bold">{status}</span>;
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Header section */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 dark:text-white tracking-tight flex items-center gap-3">
            <ShoppingBag className="text-brand" size={28} />
            Order Management
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 font-medium mt-1">Manage customer orders, track shipments, and process payments.</p>
        </div>
        <div className="flex gap-3 w-full sm:w-auto">
          <button 
            onClick={handleExport}
            className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-4 py-2.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-200 rounded-xl font-bold hover:bg-slate-50 dark:bg-slate-950 hover:text-brand transition-colors shadow-sm"
          >
            <Download size={18} />
            Export Excel
          </button>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 flex items-center gap-4">
          <div className="p-3 bg-blue-50 text-blue-600 rounded-xl"><ShoppingBag size={24} /></div>
          <div>
            <p className="text-sm font-bold text-slate-500 dark:text-slate-400">Total Orders</p>
            <p className="text-2xl font-black text-slate-900 dark:text-white">{stats.total}</p>
          </div>
        </div>
        <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 flex items-center gap-4">
          <div className="p-3 bg-amber-50 text-amber-600 rounded-xl"><Clock size={24} /></div>
          <div>
            <p className="text-sm font-bold text-slate-500 dark:text-slate-400">Pending & Processing</p>
            <p className="text-2xl font-black text-slate-900 dark:text-white">{stats.pending}</p>
          </div>
        </div>
        <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 flex items-center gap-4">
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-xl"><CheckCircle2 size={24} /></div>
          <div>
            <p className="text-sm font-bold text-slate-500 dark:text-slate-400">Delivered</p>
            <p className="text-2xl font-black text-slate-900 dark:text-white">{stats.delivered}</p>
          </div>
        </div>
      </div>

      {/* Filters row */}
      <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="relative w-full md:w-96">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
          <input 
            type="text"
            placeholder="Search by Order ID, Name, Email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand/50 focus:border-brand font-medium text-sm transition-all"
          />
        </div>
        
        <div className="flex w-full md:w-auto gap-3">
          <div className="relative flex-1 md:w-48">
            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
            <select 
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full pl-9 pr-4 py-2.5 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand/50 font-semibold text-sm appearance-none cursor-pointer"
            >
              <option value="">All Statuses</option>
              <option value="PENDING">Pending</option>
              <option value="PROCESSING">Processing</option>
              <option value="SHIPPED">Shipped</option>
              <option value="DELIVERED">Delivered</option>
              <option value="CANCELLED">Cancelled</option>
            </select>
          </div>
          
          <div className="relative flex-1 md:w-48">
            <select 
              value={paymentFilter}
              onChange={(e) => setPaymentFilter(e.target.value)}
              className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand/50 font-semibold text-sm appearance-none cursor-pointer"
            >
              <option value="">All Payments</option>
              <option value="SUCCESS">Online Paid</option>
              <option value="COD_PENDING">COD Pending</option>
              <option value="COD_COLLECTED">COD Collected</option>
              <option value="FAILED">Failed</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Table */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden">
        <div className="overflow-x-auto custom-scrollbar">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 dark:bg-slate-950 border-b border-slate-200 dark:border-slate-800 text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400 font-bold">
                <th className="p-4 pl-6">Order ID</th>
                <th className="p-4">Date</th>
                <th className="p-4">Customer</th>
                <th className="p-4">Amount</th>
                <th className="p-4">Payment</th>
                <th className="p-4">Status</th>
                <th className="p-4 pr-6 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/50">
              {loading ? (
                <tr>
                  <td colSpan="7" className="p-8 text-center text-slate-500 dark:text-slate-400 font-medium">
                    <div className="flex justify-center mb-2"><div className="animate-spin rounded-full h-6 w-6 border-b-2 border-brand"></div></div>
                    Loading orders...
                  </td>
                </tr>
              ) : orders.length === 0 ? (
                <tr>
                  <td colSpan="7" className="p-8 text-center text-slate-500 dark:text-slate-400 font-medium">No orders found matching your filters.</td>
                </tr>
              ) : (
                orders.map((order) => (
                  <tr key={order.id} className="hover:bg-slate-50 dark:bg-slate-950/50 transition-colors">
                    <td className="p-4 pl-6">
                      <div className="font-bold text-slate-900 dark:text-white text-sm">{order.order_id}</div>
                      {order.invoice_number && <div className="text-xs text-slate-400 mt-0.5">{order.invoice_number}</div>}
                    </td>
                    <td className="p-4">
                      <div className="text-sm font-medium text-slate-700 dark:text-slate-200">{new Date(order.created_at).toLocaleDateString()}</div>
                      <div className="text-xs text-slate-400">{new Date(order.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</div>
                    </td>
                    <td className="p-4">
                      <div className="text-sm font-bold text-slate-900 dark:text-white">{order.customer_name}</div>
                      <div className="text-xs text-slate-500 dark:text-slate-400">{order.phone_number}</div>
                    </td>
                    <td className="p-4">
                      <div className="text-sm font-black text-slate-900 dark:text-white">₹{order?.total_amount?.toLocaleString() || 0}</div>
                      <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mt-1">{order.payment_method}</div>
                    </td>
                    <td className="p-4">{getPaymentBadge(order.payment_status)}</td>
                    <td className="p-4">{getStatusBadge(order.order_status)}</td>
                    <td className="p-4 pr-6 text-right">
                      <Link 
                        to={`/admin/orders/${order.order_id}`}
                        className="inline-flex items-center justify-center p-2 text-slate-400 hover:text-brand hover:bg-brand/10 rounded-xl transition-colors"
                        title="View Details"
                      >
                        <Eye size={20} />
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Orders;
