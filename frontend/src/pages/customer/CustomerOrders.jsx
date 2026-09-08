import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Package, ChevronRight, FileText } from 'lucide-react';
import { toast } from 'react-hot-toast';

const CustomerOrders = () => {
  const navigate = useNavigate();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOrders();
  }, []);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  };

  const fetchOrders = async () => {
    try {
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'https://terravyn-backend.onrender.com';
      const res = await fetch(`${baseUrl}/api/user/orders`, {
        headers: getAuthHeaders()
      });
      if (res.ok) {
        setOrders(await res.json());
      } else {
        toast.error('Failed to load orders');
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    const styles = {
      PENDING: 'bg-yellow-100 text-yellow-800',
      PROCESSING: 'bg-blue-100 text-blue-800',
      SHIPPED: 'bg-indigo-100 text-indigo-800',
      DELIVERED: 'bg-green-100 text-green-800',
      CANCELLED: 'bg-red-100 text-red-800'
    };
    return styles[status] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <h1 className="text-3xl font-extrabold text-slate-900">My Orders</h1>
      
      {loading ? (
        <div className="text-center p-8 text-slate-500">Loading your orders...</div>
      ) : orders.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-12 text-center">
          <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4 text-slate-400">
            <Package size={24} />
          </div>
          <h3 className="text-lg font-bold text-slate-900 mb-2">No orders found</h3>
          <p className="text-slate-500 mb-6">You haven't placed any orders with TERRAVYN yet.</p>
          <button 
            onClick={() => navigate('/#pricing')}
            className="px-6 py-2 bg-brand text-white rounded-lg font-bold hover:bg-brand-dark transition-colors"
          >
            Shop Now
          </button>
        </div>
      ) : (
        <div className="grid gap-4">
          {orders.map(order => (
            <div 
              key={order.order_id} 
              className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex flex-col md:flex-row md:items-center justify-between gap-4 transition-all hover:shadow-md cursor-pointer"
              onClick={() => navigate(`/orders/${order.order_id}`)}
            >
              <div className="flex gap-4 items-center">
                <div className="p-4 bg-slate-50 rounded-lg border border-slate-100 text-slate-400">
                  <Package size={24} />
                </div>
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-bold text-slate-900">{order.order_id}</span>
                    <span className={`px-2 py-0.5 text-[10px] font-bold rounded-full ${getStatusColor(order.order_status)}`}>
                      {order.order_status}
                    </span>
                  </div>
                  <p className="text-sm text-slate-500 mb-1">{new Date(order.created_at).toLocaleDateString()}</p>
                  <p className="text-sm font-medium text-slate-700">{order.product_name} x{order.quantity}</p>
                </div>
              </div>
              
              <div className="flex items-center gap-4 border-t md:border-t-0 md:border-l border-slate-100 pt-4 md:pt-0 md:pl-6">
                <div className="text-right">
                  <p className="text-xs text-slate-500">Total Amount</p>
                  <p className="font-bold text-lg text-slate-900">₹{order.total_amount.toLocaleString()}</p>
                </div>
                <div className="p-2 text-slate-400">
                  <ChevronRight size={20} />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default CustomerOrders;
