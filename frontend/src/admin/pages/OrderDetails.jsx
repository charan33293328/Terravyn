import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import apiClient from '../../api/client';
import { 
  ArrowLeft, ShoppingBag, User, MapPin, CreditCard, Download, 
  CheckCircle2, Clock, XCircle, FileText, Send, Copy, Box, ShieldCheck, Eye, EyeOff
} from 'lucide-react';

const OrderDetails = () => {
  const { id } = useParams();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [statusUpdate, setStatusUpdate] = useState('');
  const [identityStatus, setIdentityStatus] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);

  useEffect(() => {
    fetchOrderDetails();
  }, [id]);

  const fetchOrderDetails = async () => {
    try {
      const res = await apiClient.get(`/admin/orders/${id}`);
      setOrder(res.data);
      setStatusUpdate(res.data.order_status);
      if (res.data.identity) {
        setIdentityStatus(res.data.identity.status);
      }
    } catch (err) {
      console.error("Failed to fetch order", err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateStatus = async () => {
    if (statusUpdate === order.order_status) return;
    if (!window.confirm(`Are you sure you want to update status to ${statusUpdate}?`)) return;
    
    setIsUpdating(true);
    try {
      await apiClient.put(`/admin/orders/${id}/status`, { order_status: statusUpdate });
      fetchOrderDetails();
    } catch (err) {
      console.error("Failed to update status", err);
      alert("Failed to update order status.");
    } finally {
      setIsUpdating(false);
    }
  };

  const handleMarkCODCollected = async () => {
    if (!window.confirm("Mark COD as collected? This will set payment status to SUCCESS.")) return;
    setIsUpdating(true);
    try {
      await apiClient.put(`/admin/orders/${id}/payment-status`, { payment_status: 'SUCCESS' });
      fetchOrderDetails();
    } catch (err) {
      console.error("Failed to update payment status", err);
      alert("Failed to update payment status.");
    } finally {
      setIsUpdating(false);
    }
  };

  const handleUpdateIdentityStatus = async () => {
    if (!order.identity || identityStatus === order.identity.status) return;
    if (!window.confirm(`Are you sure you want to update identity verification to ${identityStatus}?`)) return;
    
    setIsUpdating(true);
    try {
      await apiClient.put(`/admin/orders/${id}/identity-verification`, { status: identityStatus });
      fetchOrderDetails();
    } catch (err) {
      console.error("Failed to update identity status", err);
      alert("Failed to update identity status.");
    } finally {
      setIsUpdating(false);
    }
  };

  const handleViewDocument = () => {
    try {
      const token = localStorage.getItem('token');
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'https://terravyn-backend.onrender.com';
      window.open(`${baseUrl}/api/admin/orders/${id}/aadhaar-document?token=${token}`, '_blank');
    } catch (err) {
      console.error("Failed to open document", err);
      alert("Failed to open document.");
    }
  };

  const handleDownloadInvoice = async () => {
    try {
      const res = await apiClient.get(`/invoices/${id}/download`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Invoice_${id}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error("Failed to download invoice", err);
      alert("Failed to download invoice.");
    }
  };

  const handleCancelOrder = async () => {
    if(!window.confirm("Are you sure you want to cancel this order?")) return;
    setIsUpdating(true);
    try {
      await apiClient.post(`/admin/orders/${id}/cancel`, {});
      fetchOrderDetails();
    } catch (err) {
      console.error("Failed to cancel order", err);
      alert("Failed to cancel order.");
    } finally {
      setIsUpdating(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    // Could add a toast here
  };

  const getStatusColor = (status) => {
    const colors = {
      'PENDING': 'bg-amber-100 text-amber-800 border-amber-200',
      'PROCESSING': 'bg-blue-100 text-blue-800 border-blue-200',
      'PACKED': 'bg-indigo-100 text-indigo-800 border-indigo-200',
      'SHIPPED': 'bg-purple-100 text-purple-800 border-purple-200',
      'OUT_FOR_DELIVERY': 'bg-fuchsia-100 text-fuchsia-800 border-fuchsia-200',
      'DELIVERED': 'bg-emerald-100 text-emerald-800 border-emerald-200',
      'CANCELLED': 'bg-red-100 text-red-800 border-red-200',
      'RETURNED': 'bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-100 border-slate-200 dark:border-slate-800',
      'SUCCESS': 'bg-emerald-100 text-emerald-800 border-emerald-200',
      'FAILED': 'bg-red-100 text-red-800 border-red-200'
    };
    return colors[status] || 'bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-100 border-slate-200 dark:border-slate-800';
  };

  if (loading) {
    return (
      <div className="p-8 max-w-6xl mx-auto animate-pulse">
        <div className="h-8 bg-slate-200 rounded w-1/4 mb-8"></div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className="h-48 bg-slate-200 rounded-2xl"></div>
            <div className="h-64 bg-slate-200 rounded-2xl"></div>
          </div>
          <div className="space-y-6">
            <div className="h-48 bg-slate-200 rounded-2xl"></div>
            <div className="h-64 bg-slate-200 rounded-2xl"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!order) {
    return (
      <div className="p-8 max-w-6xl mx-auto text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-100 text-red-500 mb-4">
          <XCircle size={32} />
        </div>
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">Order not found</h2>
        <p className="text-slate-500 dark:text-slate-400 mb-6">The order you are looking for does not exist or has been removed.</p>
        <Link to="/admin/orders" className="text-brand font-medium hover:underline inline-flex items-center gap-2">
          <ArrowLeft size={16} /> Back to Orders
        </Link>
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div className="flex items-center gap-4">
          <Link to="/admin/orders" className="p-2 hover:bg-slate-100 dark:bg-slate-800 rounded-xl transition-colors">
            <ArrowLeft className="w-5 h-5 text-slate-500 dark:text-slate-400" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-3">
              Order {order.order_id}
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${getStatusColor(order.order_status)}`}>
                {order.order_status}
              </span>
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1 flex items-center gap-2">
              <Clock className="w-4 h-4" />
              Placed on {new Date(order.timestamps.created_at).toLocaleString()}
            </p>
          </div>
        </div>
        
        <div className="flex flex-wrap gap-3">
          <button onClick={handleDownloadInvoice} className="inline-flex items-center gap-2 px-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-700 dark:text-slate-200 font-medium hover:bg-slate-50 dark:bg-slate-950 transition-colors shadow-sm">
            <Download size={18} /> Invoice
          </button>
          {order.order_status !== 'CANCELLED' && (
            <button onClick={handleCancelOrder} disabled={isUpdating} className="inline-flex items-center gap-2 px-4 py-2 bg-white dark:bg-slate-900 border border-red-200 rounded-xl text-red-600 font-medium hover:bg-red-50 transition-colors shadow-sm disabled:opacity-50">
              <XCircle size={18} /> Cancel Order
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Products Section */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden">
            <div className="p-5 border-b border-slate-100 dark:border-slate-800/50 flex items-center gap-3">
              <div className="p-2 bg-brand/10 text-brand rounded-lg">
                <Box size={20} />
              </div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">Product Information</h2>
            </div>
            <div className="p-5">
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead>
                    <tr className="border-b border-slate-100 dark:border-slate-800/50 text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400">
                      <th className="pb-3 font-semibold">Product</th>
                      <th className="pb-3 font-semibold text-center">Price</th>
                      <th className="pb-3 font-semibold text-center">Qty</th>
                      <th className="pb-3 font-semibold text-right">Total</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-50">
                    <tr>
                      <td className="py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-12 h-12 bg-slate-100 dark:bg-slate-800 rounded-lg flex items-center justify-center text-slate-400">
                            <ShoppingBag size={24} />
                          </div>
                          <span className="font-medium text-slate-900 dark:text-white">{order.product.name}</span>
                        </div>
                      </td>
                      <td className="py-4 text-center text-slate-600 dark:text-slate-300">₹{order.product.unit_price.toLocaleString()}</td>
                      <td className="py-4 text-center font-medium text-slate-900 dark:text-white">{order.product.quantity}</td>
                      <td className="py-4 text-right font-bold text-slate-900 dark:text-white">₹{order.product.subtotal.toLocaleString()}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Pricing Breakdown Section */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden">
            <div className="p-5 border-b border-slate-100 dark:border-slate-800/50 flex items-center gap-3">
              <div className="p-2 bg-emerald-50 text-emerald-600 rounded-lg">
                <FileText size={20} />
              </div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">Pricing Breakdown</h2>
            </div>
            <div className="p-5 space-y-3">
              <div className="flex justify-between text-slate-600 dark:text-slate-300">
                <span>Subtotal</span>
                <span className="font-medium">₹{order.pricing.subtotal || order.product.subtotal.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-slate-600 dark:text-slate-300">
                <span>Tax Amount</span>
                <span className="font-medium">₹{order.pricing.tax.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-slate-600 dark:text-slate-300 pb-3 border-b border-slate-100 dark:border-slate-800/50">
                <span>Shipping Charges</span>
                <span className="font-medium">₹{order.pricing.shipping.toLocaleString()}</span>
              </div>
              <div className="flex justify-between items-center pt-2">
                <span className="text-lg font-bold text-slate-900 dark:text-white">Total Amount</span>
                <span className="text-2xl font-black text-brand">₹{order.pricing.total.toLocaleString()}</span>
              </div>
            </div>
          </div>

          {/* Update Status Section */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden">
            <div className="p-5 border-b border-slate-100 dark:border-slate-800/50 flex items-center gap-3">
              <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
                <Send size={20} />
              </div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">Update Order Status</h2>
            </div>
            <div className="p-5 flex flex-col sm:flex-row gap-4">
              <select 
                value={statusUpdate}
                onChange={(e) => setStatusUpdate(e.target.value)}
                className="flex-1 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white text-sm rounded-xl focus:ring-brand focus:border-brand p-3"
              >
                <option value="PLACED">PLACED</option>
                <option value="PROCESSING">PROCESSING</option>
                <option value="PACKED">PACKED</option>
                <option value="SHIPPED">SHIPPED</option>
                <option value="OUT_FOR_DELIVERY">OUT FOR DELIVERY</option>
                <option value="DELIVERED">DELIVERED</option>
                <option value="CANCELLED">CANCELLED</option>
                <option value="RETURNED">RETURNED</option>
              </select>
              <button 
                onClick={handleUpdateStatus}
                disabled={isUpdating || statusUpdate === order.order_status}
                className="bg-brand hover:bg-brand-600 text-white font-bold py-3 px-6 rounded-xl transition-colors disabled:opacity-50 whitespace-nowrap"
              >
                {isUpdating ? 'Saving...' : 'Update Status'}
              </button>
            </div>
          </div>
          
        </div>

        {/* Right Column */}
        <div className="space-y-6">
          
          {/* Customer Info Section */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden">
            <div className="p-5 border-b border-slate-100 dark:border-slate-800/50 flex items-center gap-3">
              <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
                <User size={20} />
              </div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">Customer</h2>
            </div>
            <div className="p-5 space-y-4">
              <div>
                <p className="text-sm font-medium text-slate-500 dark:text-slate-400 mb-1">Name</p>
                <p className="font-semibold text-slate-900 dark:text-white">{order.customer.name}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-slate-500 dark:text-slate-400 mb-1">Email Address</p>
                <a href={`mailto:${order.customer.email}`} className="font-semibold text-brand hover:underline">{order.customer.email}</a>
              </div>
              <div>
                <p className="text-sm font-medium text-slate-500 dark:text-slate-400 mb-1">Phone Number</p>
                <div className="flex items-center gap-2">
                  <p className="font-semibold text-slate-900 dark:text-white">{order.customer.phone}</p>
                  <button onClick={() => copyToClipboard(order.customer.phone)} className="text-slate-400 hover:text-brand" title="Copy Phone Number">
                    <Copy size={14} />
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Identity Verification Section */}
          {order.identity && (
            <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden">
              <div className="p-5 border-b border-slate-100 dark:border-slate-800/50 flex items-center gap-3">
                <div className="p-2 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 rounded-lg">
                  <ShieldCheck size={20} />
                </div>
                <h2 className="text-lg font-bold text-slate-900 dark:text-white">Identity Verification</h2>
              </div>
              <div className="p-5 space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-slate-500 dark:text-slate-400">Aadhaar Status</span>
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${
                    order.identity.status === 'APPROVED' ? 'bg-emerald-100 text-emerald-800 border-emerald-200' :
                    order.identity.status === 'REJECTED' ? 'bg-red-100 text-red-800 border-red-200' :
                    'bg-amber-100 text-amber-800 border-amber-200'
                  }`}>
                    {order.identity.status}
                  </span>
                </div>
                
                {order.identity.aadhaar_number_masked && (
                  <div>
                    <span className="text-sm font-medium text-slate-500 dark:text-slate-400 mb-1 block">Aadhaar Number</span>
                    <span className="font-mono text-slate-900 dark:text-white font-semibold">{order.identity.aadhaar_number_masked}</span>
                  </div>
                )}

                {order.identity.aadhaar_document_path && (
                  <button 
                    onClick={handleViewDocument}
                    className="w-full mt-2 inline-flex items-center justify-center gap-2 px-4 py-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-700 dark:text-slate-200 font-medium rounded-xl transition-colors"
                  >
                    <Eye size={18} /> View Identity Document
                  </button>
                )}

                <div className="pt-4 border-t border-slate-100 dark:border-slate-800/50">
                  <span className="text-xs font-medium text-slate-500 dark:text-slate-400 block mb-2">Update Verification Status</span>
                  <div className="flex gap-2">
                    <select 
                      value={identityStatus}
                      onChange={(e) => setIdentityStatus(e.target.value)}
                      className="flex-1 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white text-sm rounded-xl focus:ring-brand focus:border-brand p-2"
                    >
                      <option value="PENDING">PENDING</option>
                      <option value="APPROVED">APPROVE</option>
                      <option value="REJECTED">REJECT</option>
                    </select>
                    <button 
                      onClick={handleUpdateIdentityStatus}
                      disabled={isUpdating || identityStatus === order.identity.status}
                      className="bg-brand hover:bg-brand-600 text-white px-4 py-2 rounded-xl transition-colors disabled:opacity-50 text-sm font-bold"
                    >
                      Save
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Shipping Address Section */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden">
            <div className="p-5 border-b border-slate-100 dark:border-slate-800/50 flex items-center gap-3">
              <div className="p-2 bg-orange-50 text-orange-600 rounded-lg">
                <MapPin size={20} />
              </div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">Shipping Address</h2>
            </div>
            <div className="p-5 space-y-1">
              <p className="text-slate-700 dark:text-slate-200 leading-relaxed">{order.shipping_address.address}</p>
              <p className="text-slate-700 dark:text-slate-200 leading-relaxed">{order.shipping_address.city}, {order.shipping_address.district}</p>
              <p className="text-slate-700 dark:text-slate-200 leading-relaxed">{order.shipping_address.state} - <span className="font-semibold text-slate-900 dark:text-white">{order.shipping_address.pincode}</span></p>
            </div>
          </div>

          {/* Payment Section */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden">
            <div className="p-5 border-b border-slate-100 dark:border-slate-800/50 flex items-center gap-3">
              <div className="p-2 bg-purple-50 text-purple-600 rounded-lg">
                <CreditCard size={20} />
              </div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">Payment Details</h2>
            </div>
            <div className="p-5 space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-slate-500 dark:text-slate-400 font-medium">Method</span>
                <span className="font-bold text-slate-900 dark:text-white">{order.payment.method}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-500 dark:text-slate-400 font-medium">Status</span>
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${getStatusColor(order.payment.status)}`}>
                  {order.payment.status}
                </span>
              </div>

              {order.payment.method === 'RAZORPAY' && (
                <div className="pt-3 border-t border-slate-100 dark:border-slate-800/50 space-y-3">
                  <div>
                    <span className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider block mb-1">Razorpay Order ID</span>
                    <span className="text-sm font-mono text-slate-800 dark:text-slate-100 bg-slate-50 dark:bg-slate-950 px-2 py-1 rounded">{order.payment.razorpay_order_id || 'N/A'}</span>
                  </div>
                  <div>
                    <span className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider block mb-1">Razorpay Payment ID</span>
                    <span className="text-sm font-mono text-slate-800 dark:text-slate-100 bg-slate-50 dark:bg-slate-950 px-2 py-1 rounded">{order.payment.razorpay_payment_id || 'N/A'}</span>
                  </div>
                </div>
              )}

              {order.payment.method === 'COD' && (
                <div className="pt-3 border-t border-slate-100 dark:border-slate-800/50">
                  <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-amber-800 text-sm">
                    <strong>Payment to be collected upon delivery.</strong>
                  </div>
                  {order.payment.status !== 'SUCCESS' && order.order_status !== 'CANCELLED' && (
                    <button 
                      onClick={handleMarkCODCollected}
                      disabled={isUpdating}
                      className="mt-4 w-full bg-emerald-500 hover:bg-emerald-600 text-white font-bold py-2.5 rounded-xl transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                    >
                      <CheckCircle2 size={18} /> Mark COD as Collected
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};

export default OrderDetails;
