import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Package, Search, Filter, Eye, Download, Calendar, Truck, AlertCircle, ArrowUpRight } from 'lucide-react';
import apiClient from '../../api/client';
import dayjs from 'dayjs';

const FarmerOrders = () => {
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState(null);
  const [orders, setOrders] = useState([]);
  const [total, setTotal] = useState(0);
  
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [search, setSearch] = useState('');
  
  useEffect(() => {
    fetchData();
  }, [page, statusFilter]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [summaryRes, ordersRes] = await Promise.all([
        apiClient.get('/farmer/orders/summary'),
        apiClient.get(`/farmer/orders?page=${page}&status=${statusFilter}&search=${search}`)
      ]);
      setSummary(summaryRes.data);
      setOrders(ordersRes.data.items);
      setTotal(ordersRes.data.total);
    } catch (error) {
      console.error('Error fetching orders:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    fetchData();
  };

  const getStatusColor = (status) => {
    switch (status?.toUpperCase()) {
      case 'DELIVERED': return 'bg-emerald-50 text-emerald-600 border-emerald-200';
      case 'PENDING': return 'bg-yellow-50 text-yellow-600 border-yellow-200';
      case 'PROCESSING': return 'bg-blue-50 text-blue-600 border-blue-200';
      case 'SHIPPED': return 'bg-indigo-50 text-indigo-600 border-indigo-200';
      case 'RETURNED': return 'bg-red-50 text-red-600 border-red-200';
      case 'CANCELLED': return 'bg-slate-50 text-slate-600 border-slate-200';
      default: return 'bg-slate-50 text-slate-600 border-slate-200';
    }
  };

  return (
    <div className="p-4 md:p-8 space-y-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
          <Package className="text-brand w-6 h-6" /> My Orders
        </h1>
        <p className="text-slate-500 mt-1">Track and manage all your TERRAVYN purchases from one place.</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 bg-blue-50 rounded-xl flex items-center justify-center text-blue-500">
            <Package />
          </div>
          <div>
            <p className="text-sm text-slate-500 font-medium">Total Orders</p>
            <h3 className="text-2xl font-bold text-slate-800">{summary?.total_orders || 0}</h3>
          </div>
        </div>
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 bg-yellow-50 rounded-xl flex items-center justify-center text-yellow-500">
            <Truck />
          </div>
          <div>
            <p className="text-sm text-slate-500 font-medium">Active Orders</p>
            <h3 className="text-2xl font-bold text-slate-800">{summary?.active_orders || 0}</h3>
          </div>
        </div>
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 bg-emerald-50 rounded-xl flex items-center justify-center text-emerald-500">
            <Calendar />
          </div>
          <div>
            <p className="text-sm text-slate-500 font-medium">Delivered</p>
            <h3 className="text-2xl font-bold text-slate-800">{summary?.delivered_orders || 0}</h3>
          </div>
        </div>
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 bg-red-50 rounded-xl flex items-center justify-center text-red-500">
            <AlertCircle />
          </div>
          <div>
            <p className="text-sm text-slate-500 font-medium">Returned</p>
            <h3 className="text-2xl font-bold text-slate-800">{summary?.returned_orders || 0}</h3>
          </div>
        </div>
      </div>

      {/* Orders List */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm">
        <div className="p-6 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand/20"
            >
              <option value="ALL">All Status</option>
              <option value="PENDING">Pending</option>
              <option value="PROCESSING">Processing</option>
              <option value="SHIPPED">Shipped</option>
              <option value="DELIVERED">Delivered</option>
              <option value="RETURNED">Returned</option>
            </select>
          </div>
          
          <form onSubmit={handleSearch} className="relative w-full sm:w-64">
            <input
              type="text"
              placeholder="Search orders..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand/20 focus:border-brand"
            />
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          </form>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-500">
              <tr>
                <th className="px-6 py-4 font-medium">Order ID</th>
                <th className="px-6 py-4 font-medium">Date</th>
                <th className="px-6 py-4 font-medium">Items</th>
                <th className="px-6 py-4 font-medium">Total Amount</th>
                <th className="px-6 py-4 font-medium">Status</th>
                <th className="px-6 py-4 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan="6" className="px-6 py-8 text-center text-slate-500">
                    <div className="flex justify-center mb-2">
                      <div className="w-6 h-6 border-2 border-brand border-t-transparent rounded-full animate-spin"></div>
                    </div>
                    Loading orders...
                  </td>
                </tr>
              ) : orders.length === 0 ? (
                <tr>
                  <td colSpan="6" className="px-6 py-8 text-center text-slate-500">
                    No orders found.
                  </td>
                </tr>
              ) : (
                orders.map((order) => (
                  <tr key={order.order_id} className="hover:bg-slate-50/50">
                    <td className="px-6 py-4 font-medium text-slate-800">
                      {order.order_id}
                    </td>
                    <td className="px-6 py-4 text-slate-600">
                      {dayjs(order.created_at).format('MMM D, YYYY')}
                    </td>
                    <td className="px-6 py-4 text-slate-600">
                      {order.items?.length || 0} items
                    </td>
                    <td className="px-6 py-4 font-medium text-slate-800">
                      ₹{order.total_amount.toLocaleString()}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border ${getStatusColor(order.order_status)}`}>
                        {order.order_status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link
                        to={`/farmer/orders/${order.order_id}`}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-brand hover:bg-brand/5 rounded-lg transition-colors"
                      >
                        <Eye className="w-4 h-4" /> View
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        
        {/* Pagination */}
        {total > 10 && (
          <div className="p-4 border-t border-slate-200 flex items-center justify-between">
            <span className="text-sm text-slate-500">
              Showing {((page - 1) * 10) + 1} to {Math.min(page * 10, total)} of {total} orders
            </span>
            <div className="flex gap-2">
              <button 
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1.5 border border-slate-200 rounded-lg text-sm font-medium text-slate-600 disabled:opacity-50"
              >
                Previous
              </button>
              <button 
                onClick={() => setPage(p => p + 1)}
                disabled={page * 10 >= total}
                className="px-3 py-1.5 border border-slate-200 rounded-lg text-sm font-medium text-slate-600 disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default FarmerOrders;
