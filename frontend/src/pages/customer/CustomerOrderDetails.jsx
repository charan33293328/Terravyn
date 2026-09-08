import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, CheckCircle2, Circle, Truck, FileText, Download 
} from 'lucide-react';
import { toast } from 'react-hot-toast';

const CustomerOrderDetails = () => {
  const { orderId } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchOrderDetails = async () => {
      try {
        const token = localStorage.getItem('token');
        const baseUrl = import.meta.env.VITE_API_BASE_URL || 'https://terravyn-backend.onrender.com';
        const res = await fetch(`${baseUrl}/api/user/orders/${orderId}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        if (res.ok) {
          setData(await res.json());
        } else if (res.status === 404) {
          toast.error("Order not found");
          navigate('/orders');
        }
      } catch (err) {
        console.error(err);
        toast.error("Failed to load order details");
      } finally {
        setLoading(false);
      }
    };
    fetchOrderDetails();
  }, [orderId, navigate]);

  if (loading) return <div className="p-8 text-center text-slate-500">Loading order details...</div>;
  if (!data) return null;

  const { order, invoice } = data;

  const steps = [
    { key: 'PENDING', label: 'Order Placed' },
    { key: 'PROCESSING', label: 'Processing' },
    { key: 'SHIPPED', label: 'Shipped' },
    { key: 'DELIVERED', label: 'Delivered' }
  ];

  const getStepStatus = (stepKey) => {
    if (order.order_status === 'CANCELLED') return 'cancelled';
    const currentIndex = steps.findIndex(s => s.key === order.order_status);
    const stepIndex = steps.findIndex(s => s.key === stepKey);
    
    if (stepIndex < currentIndex) return 'completed';
    if (stepIndex === currentIndex) return 'current';
    return 'pending';
  };

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div className="flex items-center gap-4 mb-2">
        <button onClick={() => navigate('/orders')} className="p-2 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-full transition-colors">
          <ArrowLeft size={20} />
        </button>
        <h1 className="text-3xl font-extrabold text-slate-900">Order #{order.order_id}</h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Timeline (Left 2/3) */}
        <div className="md:col-span-2 space-y-6">
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <h3 className="font-bold text-slate-900 mb-6">Tracking Timeline</h3>
            
            {order.order_status === 'CANCELLED' ? (
              <div className="p-4 bg-red-50 text-red-700 rounded-lg border border-red-100 font-medium">
                This order has been cancelled.
              </div>
            ) : (
              <div className="space-y-6 pl-2">
                {steps.map((step, idx) => {
                  const status = getStepStatus(step.key);
                  const isLast = idx === steps.length - 1;
                  return (
                    <div key={step.key} className="relative flex gap-4">
                      {/* Line connector */}
                      {!isLast && (
                        <div className={`absolute left-[11px] top-7 w-[2px] h-full ${status === 'completed' ? 'bg-brand' : 'bg-slate-100'}`}></div>
                      )}
                      
                      <div className="relative z-10 mt-1">
                        {status === 'completed' ? (
                          <div className="w-6 h-6 bg-brand text-white rounded-full flex items-center justify-center">
                            <CheckCircle2 size={16} />
                          </div>
                        ) : status === 'current' ? (
                          <div className="w-6 h-6 border-4 border-brand bg-white rounded-full"></div>
                        ) : (
                          <div className="w-6 h-6 text-slate-300 bg-white"><Circle size={24} /></div>
                        )}
                      </div>
                      
                      <div className={`pb-6 ${status === 'pending' ? 'text-slate-400' : 'text-slate-900'}`}>
                        <p className="font-bold">{step.label}</p>
                        {step.key === 'PENDING' && status !== 'pending' && <p className="text-sm text-slate-500">{new Date(order.created_at).toLocaleString()}</p>}
                        
                        {step.key === 'SHIPPED' && (status === 'completed' || status === 'current') && order.courier_name && (
                          <div className="mt-2 p-3 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-700">
                            <p><strong>Courier:</strong> {order.courier_name}</p>
                            <p><strong>Tracking No:</strong> {order.tracking_number}</p>
                            {order.tracking_url && (
                              <a href={order.tracking_url} target="_blank" rel="noreferrer" className="text-brand hover:underline mt-1 inline-block">
                                Track Package &rarr;
                              </a>
                            )}
                          </div>
                        )}
                        
                        {step.key === 'DELIVERED' && status === 'pending' && order.estimated_delivery_date && (
                          <p className="text-sm text-slate-500 mt-1">Expected by {new Date(order.estimated_delivery_date).toLocaleDateString()}</p>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Info (Right 1/3) */}
        <div className="space-y-6">
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 space-y-4">
            <h3 className="font-bold text-slate-900 border-b border-slate-100 pb-2">Order Summary</h3>
            <div className="text-sm space-y-2">
              <div className="flex justify-between">
                <span className="text-slate-500">Item</span>
                <span className="font-medium">{order.product_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Quantity</span>
                <span className="font-medium">{order.quantity}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Payment</span>
                <span className="font-medium">{order.payment_method} ({order.payment_status})</span>
              </div>
            </div>
            <div className="flex justify-between text-lg font-bold text-slate-900 pt-3 border-t border-slate-100">
              <span>Total</span>
              <span>₹{order.total_amount.toLocaleString()}</span>
            </div>
          </div>

          {invoice && (
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 space-y-3">
              <h3 className="font-bold text-slate-900 flex items-center gap-2"><FileText size={18} className="text-brand"/> Invoice</h3>
              <p className="text-sm text-slate-500 mb-3">{invoice.invoice_number}</p>
              
              <button 
                onClick={() => {
                  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'https://terravyn-backend.onrender.com';
                  window.open(`${baseUrl}/api/invoices/${order.order_id}/view`, '_blank');
                }}
                className="w-full py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium rounded-lg transition-colors text-sm flex items-center justify-center gap-2"
              >
                <FileText size={16} /> View Online
              </button>
              
              <button 
                onClick={() => {
                  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'https://terravyn-backend.onrender.com';
                  window.open(`${baseUrl}/api/invoices/${order.order_id}/download`, '_blank');
                }}
                className="w-full py-2 bg-brand/10 hover:bg-brand/20 text-brand font-medium rounded-lg transition-colors text-sm flex items-center justify-center gap-2"
              >
                <Download size={16} /> Download PDF
              </button>
            </div>
          )}
          
          <div className="bg-slate-50 rounded-xl border border-slate-200 p-4 text-center">
            <p className="text-sm text-slate-600 mb-2">Need help with your order?</p>
            <a href="mailto:support@terravyn.com" className="text-brand font-bold text-sm hover:underline">Contact Support</a>
          </div>
        </div>

      </div>
    </div>
  );
};

export default CustomerOrderDetails;
