import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Package, MapPin, CreditCard, Truck, Download, AlertCircle, CheckCircle2, Clock } from 'lucide-react';
import apiClient from '../../api/client';
import dayjs from 'dayjs';

const FarmerOrderDetail = () => {
  const { id } = useParams();
  const [order, setOrder] = useState(null);
  const [tracking, setTracking] = useState(null);
  const [loading, setLoading] = useState(true);
  
  const [returnReason, setReturnReason] = useState('');
  const [returnStatus, setReturnStatus] = useState(null); // idle, loading, success, error
  const [returnError, setReturnError] = useState('');

  useEffect(() => {
    fetchOrderDetails();
  }, [id]);

  const fetchOrderDetails = async () => {
    try {
      setLoading(true);
      const [orderRes, trackingRes] = await Promise.all([
        apiClient.get(`/farmer/orders/${id}`),
        apiClient.get(`/farmer/orders/${id}/tracking`)
      ]);
      setOrder(orderRes.data);
      setTracking(trackingRes.data);
    } catch (error) {
      console.error('Error fetching order details:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadInvoice = async () => {
    try {
      const response = await apiClient.get(`/farmer/orders/${id}/invoice`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `invoice_${id}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Error downloading invoice:', error);
      alert('Failed to download invoice. Please try again later.');
    }
  };

  const handleReturnRequest = async (e) => {
    e.preventDefault();
    if (!returnReason.trim()) return;
    
    try {
      setReturnStatus('loading');
      await apiClient.post(`/farmer/orders/${id}/return`, { reason: returnReason });
      setReturnStatus('success');
      fetchOrderDetails(); // Refresh order details to show the new return request
    } catch (error) {
      setReturnStatus('error');
      setReturnError(error.response?.data?.detail || 'Failed to submit return request.');
    }
  };

  if (loading) {
    return (
      <div className="p-4 md:p-8 space-y-6 max-w-5xl mx-auto flex justify-center items-center h-64">
        <div className="flex flex-col items-center">
          <div className="w-8 h-8 border-4 border-brand border-t-transparent rounded-full animate-spin"></div>
          <p className="mt-4 text-slate-500">Loading order details...</p>
        </div>
      </div>
    );
  }

  if (!order) {
    return (
      <div className="p-4 md:p-8 space-y-6 max-w-5xl mx-auto">
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-slate-800">Order Not Found</h2>
          <p className="text-slate-500 mt-2 mb-6">The order you are looking for does not exist or you do not have permission to view it.</p>
          <Link to="/farmer/orders" className="bg-brand text-white px-6 py-2 rounded-lg font-medium">
            Back to Orders
          </Link>
        </div>
      </div>
    );
  }

  const isDelivered = order.order_status?.toUpperCase() === 'DELIVERED';
  const hasReturnRequest = order.return_requests && order.return_requests.length > 0;
  const returnWindowValid = dayjs().diff(dayjs(order.updated_at), 'day') <= 7;

  return (
    <div className="p-4 md:p-8 space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div className="flex items-center gap-4">
          <Link to="/farmer/orders" className="p-2 hover:bg-slate-100 rounded-lg text-slate-500 transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
              Order {order.order_id}
            </h1>
            <p className="text-slate-500 mt-1">Placed on {dayjs(order.created_at).format('MMM D, YYYY at h:mm A')}</p>
          </div>
        </div>
        
        <div className="flex gap-3">
          <button 
            onClick={handleDownloadInvoice}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 text-slate-700 rounded-lg text-sm font-medium hover:bg-slate-50 transition-colors shadow-sm"
          >
            <Download className="w-4 h-4" /> Invoice
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column - Order Items & Tracking */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Tracking Timeline */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
            <h2 className="text-lg font-bold text-slate-800 mb-6 flex items-center gap-2">
              <Truck className="w-5 h-5 text-brand" /> Tracking Status
            </h2>
            
            {tracking?.timeline ? (
              <div className="relative">
                <div className="absolute left-4 top-2 bottom-2 w-0.5 bg-slate-100"></div>
                <div className="space-y-6">
                  {tracking.timeline.map((step, index) => (
                    <div key={index} className="relative flex gap-4">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center relative z-10 ${
                        step.current ? 'bg-brand text-white shadow-md shadow-brand/20 ring-4 ring-brand/10' :
                        step.completed ? 'bg-emerald-500 text-white' :
                        'bg-slate-100 text-slate-400'
                      }`}>
                        {step.completed && !step.current ? <CheckCircle2 className="w-5 h-5" /> : 
                         step.current ? <Clock className="w-5 h-5 animate-pulse" /> :
                         <div className="w-2.5 h-2.5 rounded-full bg-slate-300"></div>}
                      </div>
                      <div className="pt-1">
                        <p className={`font-medium ${step.completed ? 'text-slate-800' : 'text-slate-400'}`}>
                          {step.status}
                        </p>
                        {step.timestamp && (
                          <p className="text-sm text-slate-500 mt-0.5">
                            {dayjs(step.timestamp).format('MMM D, YYYY • h:mm A')}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-slate-500">Tracking information is not available.</p>
            )}
            
            {(tracking?.tracking_number || tracking?.courier_partner) && (
              <div className="mt-6 pt-6 border-t border-slate-100 bg-slate-50/50 rounded-xl p-4 flex flex-col sm:flex-row justify-between gap-4">
                <div>
                  <p className="text-xs text-slate-500 font-medium uppercase tracking-wider mb-1">Courier Partner</p>
                  <p className="font-medium text-slate-800">{tracking.courier_partner || 'Pending Allocation'}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 font-medium uppercase tracking-wider mb-1">Tracking Number</p>
                  <p className="font-medium text-slate-800 font-mono">{tracking.tracking_number || 'Awaiting Generation'}</p>
                </div>
                {tracking.tracking_url && (
                  <div className="flex items-center">
                    <a 
                      href={tracking.tracking_url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-brand font-medium text-sm flex items-center gap-1 hover:underline"
                    >
                      Track Shipment <ArrowUpRight className="w-4 h-4" />
                    </a>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Order Items */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="p-6 border-b border-slate-200">
              <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                <Package className="w-5 h-5 text-brand" /> Items ({order.items?.length || 0})
              </h2>
            </div>
            
            <div className="divide-y divide-slate-100">
              {order.items?.map((item) => (
                <div key={item.id} className="p-6 flex flex-col sm:flex-row gap-4 sm:items-center justify-between hover:bg-slate-50 transition-colors">
                  <div className="flex items-center gap-4">
                    <div className="w-16 h-16 bg-slate-100 rounded-xl flex items-center justify-center flex-shrink-0">
                      <Package className="w-8 h-8 text-slate-400" />
                    </div>
                    <div>
                      <h4 className="font-bold text-slate-800">{item.product_name}</h4>
                      <p className="text-sm text-slate-500 mt-1">Qty: {item.quantity}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-slate-800 text-lg">₹{item.subtotal.toLocaleString()}</p>
                    <p className="text-xs text-slate-500 mt-1">₹{item.unit_price.toLocaleString()} each</p>
                  </div>
                </div>
              ))}
            </div>
            
            <div className="p-6 bg-slate-50 border-t border-slate-200">
              <div className="space-y-3">
                <div className="flex justify-between text-slate-600">
                  <span>Subtotal</span>
                  <span className="font-medium">₹{order.items?.reduce((acc, item) => acc + item.subtotal, 0).toLocaleString() || 0}</span>
                </div>
                <div className="flex justify-between text-slate-600">
                  <span>Tax (GST)</span>
                  <span className="font-medium">₹{order.tax_amount.toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-slate-600">
                  <span>Shipping</span>
                  <span className="font-medium">₹{order.shipping_amount.toLocaleString()}</span>
                </div>
                <div className="pt-4 border-t border-slate-200 flex justify-between">
                  <span className="font-bold text-slate-800 text-lg">Total</span>
                  <span className="font-bold text-brand text-xl">₹{order.total_amount.toLocaleString()}</span>
                </div>
              </div>
            </div>
          </div>
          
        </div>
        
        {/* Right Column - Details & Return */}
        <div className="space-y-6">
          
          {/* Shipping Details */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
            <h3 className="font-bold text-slate-800 mb-4 flex items-center gap-2">
              <MapPin className="w-5 h-5 text-slate-400" /> Shipping Address
            </h3>
            <div className="text-slate-600 text-sm space-y-1 bg-slate-50 p-4 rounded-xl">
              <p className="font-medium text-slate-800 text-base mb-2">{order.customer_name}</p>
              <p>{order.address}</p>
              <p>{order.city}, {order.district}</p>
              <p>{order.state} - {order.pincode}</p>
              <div className="pt-3 mt-3 border-t border-slate-200">
                <p>Phone: {order.phone_number}</p>
                <p className="truncate">Email: {order.email}</p>
              </div>
            </div>
          </div>
          
          {/* Payment Details */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
            <h3 className="font-bold text-slate-800 mb-4 flex items-center gap-2">
              <CreditCard className="w-5 h-5 text-slate-400" /> Payment Info
            </h3>
            <div className="space-y-4 bg-slate-50 p-4 rounded-xl">
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-500">Method</span>
                <span className="font-medium text-slate-800">{order.payment_method}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-500">Status</span>
                <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                  order.payment_status === 'SUCCESS' ? 'bg-emerald-100 text-emerald-700' :
                  order.payment_status === 'PENDING' ? 'bg-yellow-100 text-yellow-700' :
                  'bg-red-100 text-red-700'
                }`}>
                  {order.payment_status}
                </span>
              </div>
              {order.invoice_number && (
                <div className="flex justify-between items-center pt-3 border-t border-slate-200">
                  <span className="text-sm text-slate-500">Invoice</span>
                  <span className="font-mono text-xs font-medium text-slate-800">{order.invoice_number}</span>
                </div>
              )}
            </div>
          </div>

          {/* Return Request Widget */}
          {hasReturnRequest ? (
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
              <h3 className="font-bold text-slate-800 mb-4 flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-slate-400" /> Return Request
              </h3>
              <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-bold text-yellow-800">Status: {order.return_requests[0].status}</span>
                  <span className="text-xs text-yellow-600">{dayjs(order.return_requests[0].requested_at).format('MMM D, YYYY')}</span>
                </div>
                <p className="text-sm text-yellow-700 mt-2 italic">"{order.return_requests[0].reason}"</p>
                {order.return_requests[0].resolution_notes && (
                  <div className="mt-3 pt-3 border-t border-yellow-200/50">
                    <p className="text-xs font-bold text-yellow-800 uppercase">Resolution</p>
                    <p className="text-sm text-yellow-700 mt-1">{order.return_requests[0].resolution_notes}</p>
                  </div>
                )}
              </div>
            </div>
          ) : isDelivered && returnWindowValid ? (
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
              <h3 className="font-bold text-slate-800 mb-2 flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-slate-400" /> Request Return
              </h3>
              <p className="text-sm text-slate-500 mb-4">
                You have 7 days from delivery to request a return.
              </p>
              
              {returnStatus === 'success' ? (
                <div className="bg-emerald-50 text-emerald-700 p-4 rounded-xl text-sm font-medium flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5" /> Return request submitted successfully.
                </div>
              ) : (
                <form onSubmit={handleReturnRequest} className="space-y-4">
                  {returnStatus === 'error' && (
                    <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm">
                      {returnError}
                    </div>
                  )}
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Reason for Return</label>
                    <textarea 
                      required
                      rows={3}
                      value={returnReason}
                      onChange={(e) => setReturnReason(e.target.value)}
                      className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand/20 focus:border-brand resize-none"
                      placeholder="Please explain why you want to return this order..."
                    ></textarea>
                  </div>
                  <button 
                    type="submit" 
                    disabled={returnStatus === 'loading' || !returnReason.trim()}
                    className="w-full py-2.5 bg-slate-800 hover:bg-slate-900 text-white rounded-xl text-sm font-medium transition-colors disabled:opacity-50"
                  >
                    {returnStatus === 'loading' ? 'Submitting...' : 'Submit Return Request'}
                  </button>
                </form>
              )}
            </div>
          ) : isDelivered && !returnWindowValid ? (
             <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
               <div className="text-center">
                 <AlertCircle className="w-10 h-10 text-slate-300 mx-auto mb-2" />
                 <p className="text-sm text-slate-500">Return window has expired for this order.</p>
               </div>
             </div>
          ) : null}
          
        </div>
      </div>
    </div>
  );
};

export default FarmerOrderDetail;
