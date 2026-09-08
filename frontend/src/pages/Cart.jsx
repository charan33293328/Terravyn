import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ShoppingCart, ArrowLeft, Trash2, Plus, Minus, Leaf } from 'lucide-react';
import { useCart } from '../context/CartContext';
import LanguageSelector from '../components/LanguageSelector';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import CustomerDetailsModal from '../components/CustomerDetailsModal';
import PaymentSelectionModal from '../components/PaymentSelectionModal';
import SuccessModal from '../components/SuccessModal';

const CheckoutStep = {
  IDLE: 'IDLE',
  CUSTOMER_DETAILS: 'CUSTOMER_DETAILS',
  PAYMENT_SELECTION: 'PAYMENT_SELECTION',
  ORDER_CONFIRMATION: 'ORDER_CONFIRMATION'
};

const Cart = () => {
  const { cartItems, updateQuantity, removeFromCart, getCartCount, clearCart } = useCart();
  const navigate = useNavigate();
  const { t } = useTranslation();

  const [toastMessage, setToastMessage] = React.useState('');
  const [checkoutStep, setCheckoutStep] = React.useState(CheckoutStep.IDLE);
  const [customerData, setCustomerData] = React.useState(null);
  const [completedOrderData, setCompletedOrderData] = React.useState(null);

  const totalAmount = cartItems.reduce((sum, item) => sum + (item.price * item.quantity), 0);

  const handleCheckout = () => {
    if (cartItems.length > 0) {
      setCheckoutStep(CheckoutStep.CUSTOMER_DETAILS);
    }
  };

  const handleCustomerSubmit = (data) => {
    setCustomerData(data);
    console.trace('PAYMENT_SELECTION CALLED'); setCheckoutStep(CheckoutStep.PAYMENT_SELECTION);
  };

  const loadRazorpayScript = () => {
    return new Promise((resolve) => {
      if (window.Razorpay) {
        resolve(true);
        return;
      }
      const script = document.createElement('script');
      script.src = 'https://checkout.razorpay.com/v1/checkout.js';
      script.onload = () => resolve(true);
      script.onerror = () => resolve(false);
      document.body.appendChild(script);
    });
  };

  const handlePaymentSubmit = async (paymentInfo) => {
    // Keep it open until successful or handled otherwise, 
    // or we can close it, but usually we just transition state
    setCheckoutStep(CheckoutStep.IDLE);
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'https://terravyn-backend.onrender.com';
    const itemsPayload = cartItems.map(i => ({ productId: i.product_id, quantity: i.quantity }));

    if (paymentInfo.paymentMethod === 'ONLINE') {
      setToastMessage('Redirecting to secure payment gateway...');
      const res = await loadRazorpayScript();
      if (!res) {
        setToastMessage('Unable to load payment gateway. Please try again.');
        return;
      }

      const razorpayKey = import.meta.env.VITE_RAZORPAY_KEY_ID;
      if (!razorpayKey) {
        setToastMessage('Payment gateway configuration error.');
        return;
      }

      try {
        const payload = { ...paymentInfo, items: itemsPayload };
        const createOrderRes = await axios.post(`${baseUrl}/api/orders/create-order`, payload);
        const orderData = createOrderRes.data;
        
        const options = {
          key: razorpayKey,
          amount: orderData.total_amount * 100, // paise
          currency: 'INR',
          name: 'TERRAVYN',
          description: 'Cart Checkout',
          order_id: orderData.razorpay_order_id,
          handler: async function (response) {
            try {
              const verifyRes = await axios.post(`${baseUrl}/api/orders/verify-payment`, {
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_order_id: response.razorpay_order_id,
                razorpay_signature: response.razorpay_signature
              });
              
              if (verifyRes.data.status === 'success') {
                setCompletedOrderData({
                  order_id: verifyRes.data.order_id,
                  payment_method: 'ONLINE'
                });
                clearCart();
                setCheckoutStep(CheckoutStep.ORDER_CONFIRMATION);
              } else {
                setToastMessage('Payment Verification Failed: ' + (verifyRes.data.detail || 'Unknown error'));
              }
            } catch (err) {
              setToastMessage(err.response?.data?.detail || 'Payment Verification Failed!');
            }
          },
          prefill: {
            name: paymentInfo.customerDetails.name,
            email: paymentInfo.customerDetails.email,
            contact: paymentInfo.customerDetails.phone
          },
          theme: { color: '#16a34a' }
        };

        const rzp = new window.Razorpay(options);
        rzp.on('payment.failed', function (response){
          setToastMessage(`Payment Failed: ${response.error.description || 'Please try again.'}`);
        });
        rzp.open();

      } catch (err) {
        setToastMessage(err.response?.data?.detail || err.message || 'Payment processing error.');
      }
    } else {
      setToastMessage('Preparing your order...');
      try {
        const payload = { ...paymentInfo, items: itemsPayload };
        const createOrderRes = await axios.post(`${baseUrl}/api/orders/place-cod-order`, payload);
        const orderData = createOrderRes.data;
        
        setCompletedOrderData({
          order_id: orderData.order_id,
          payment_method: 'COD'
        });
        clearCart();
        setCheckoutStep(CheckoutStep.ORDER_CONFIRMATION);
      } catch(err) {
        setToastMessage(err.response?.data?.detail || err.message || 'Failed to place COD order.');
      }
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900 animate-fade-in">
      {/* Navbar */}
      <nav className="fixed w-full bg-white/80 backdrop-blur-md z-50 border-b border-slate-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-20">
            <Link to="/" className="flex items-center gap-2">
              <div className="w-10 h-10 bg-brand rounded-xl flex items-center justify-center shadow-lg shadow-brand/20">
                <Leaf className="w-6 h-6 text-white" />
              </div>
              <span className="font-bold text-xl tracking-tight text-slate-800">TERRAVYN</span>
            </Link>
            <div className="flex items-center gap-4">
              <LanguageSelector />
              <Link to="/pricing" className="text-sm font-bold text-slate-600 hover:text-brand transition-colors">Continue Shopping</Link>
            </div>
          </div>
        </div>
      </nav>

      <main className="pt-32 pb-24 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-3 mb-8">
          <button onClick={() => navigate(-1)} className="p-2 text-slate-500 hover:text-brand hover:bg-brand/10 rounded-xl transition-colors">
            <ArrowLeft size={24} />
          </button>
          <h1 className="text-3xl font-black text-slate-800 flex items-center gap-3">
            <ShoppingCart className="text-brand w-8 h-8" />
            Your Shopping Cart
          </h1>
        </div>

        {cartItems.length === 0 ? (
          <div className="bg-white rounded-3xl p-12 text-center shadow-sm border border-slate-100 flex flex-col items-center">
            <div className="w-24 h-24 bg-slate-50 rounded-full flex items-center justify-center mb-6">
              <ShoppingCart className="w-12 h-12 text-slate-300" />
            </div>
            <h2 className="text-2xl font-bold text-slate-800 mb-2">Your cart is empty</h2>
            <p className="text-slate-500 mb-8 max-w-md mx-auto">Looks like you haven't added any TERRAVYN products to your cart yet.</p>
            <Link to="/pricing" className="bg-brand text-white px-8 py-4 rounded-xl font-bold shadow-lg shadow-brand/20 hover:bg-brand-dark transition-colors inline-flex items-center gap-2">
              Browse Products
            </Link>
          </div>
        ) : (
          <div className="grid lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 space-y-4">
              {cartItems.map((item) => (
                <div key={item.product_id} className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100 flex flex-col sm:flex-row items-center gap-6 relative group">
                  <button 
                    onClick={() => removeFromCart(item.product_id)}
                    className="absolute top-4 right-4 p-2 text-slate-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                  >
                    <Trash2 size={20} />
                  </button>
                  
                  <div className="w-32 h-32 bg-slate-50 rounded-xl flex-shrink-0 border border-slate-100 overflow-hidden">
                    {item.image ? (
                      <img src={item.image} alt={item.name} className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center"><Leaf className="text-slate-200 w-12 h-12" /></div>
                    )}
                  </div>
                  
                  <div className="flex-1 text-center sm:text-left">
                    <h3 className="font-bold text-lg text-slate-800 mb-1 pr-8">{item.name}</h3>
                    <p className="text-brand font-black text-xl mb-4">₹{item.price.toLocaleString()}</p>
                    
                    <div className="flex items-center justify-center sm:justify-start gap-4">
                      <div className="flex items-center border border-slate-200 rounded-lg bg-white overflow-hidden shadow-sm">
                        <button 
                          onClick={() => updateQuantity(item.product_id, item.quantity - 1)}
                          className="px-3 py-2 text-slate-500 hover:bg-slate-50 hover:text-brand transition-colors"
                        >
                          <Minus size={16} />
                        </button>
                        <div className="w-12 text-center font-bold text-slate-800 border-x border-slate-200 py-2 text-sm">
                          {item.quantity}
                        </div>
                        <button 
                          onClick={() => updateQuantity(item.product_id, item.quantity + 1)}
                          className="px-3 py-2 text-slate-500 hover:bg-slate-50 hover:text-brand transition-colors"
                        >
                          <Plus size={16} />
                        </button>
                      </div>
                      
                      <div className="text-sm font-bold text-slate-500">
                        Subtotal: <span className="text-slate-800">₹{(item.price * item.quantity).toLocaleString()}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
              
              <div className="flex justify-between items-center px-2 py-4">
                <button onClick={clearCart} className="text-sm font-bold text-slate-500 hover:text-red-500 flex items-center gap-2">
                  <Trash2 size={16} /> Clear Cart
                </button>
              </div>
            </div>
            
            <div>
              <div className="bg-white rounded-3xl p-8 shadow-xl border border-slate-100 sticky top-32">
                <h3 className="text-xl font-bold text-slate-800 mb-6 pb-4 border-b border-slate-100">Order Summary</h3>
                
                <div className="space-y-4 mb-6">
                  <div className="flex justify-between text-slate-600">
                    <span>Items ({getCartCount()})</span>
                    <span className="font-medium">₹{totalAmount.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-slate-600">
                    <span>Tax & Shipping</span>
                    <span className="text-sm italic">Calculated at checkout</span>
                  </div>
                </div>
                
                <div className="border-t border-slate-100 pt-6 mb-8">
                  <div className="flex justify-between items-end">
                    <span className="font-bold text-slate-800">Estimated Total</span>
                    <span className="text-3xl font-black text-slate-900">₹{totalAmount.toLocaleString()}</span>
                  </div>
                </div>
                
                <button 
                  onClick={handleCheckout}
                  className="w-full py-4 bg-brand hover:bg-brand-dark text-white font-bold rounded-2xl shadow-lg transition-all"
                >
                  Proceed to Checkout
                </button>
                <p className="text-xs text-center text-slate-400 mt-4">Secure checkout powered by Razorpay</p>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Modals & Toasts */}
      <CustomerDetailsModal
        isOpen={checkoutStep === CheckoutStep.CUSTOMER_DETAILS}
        onClose={() => setCheckoutStep(CheckoutStep.IDLE)}
        onSubmit={handleCustomerSubmit}
      />

      <PaymentSelectionModal
        isOpen={checkoutStep === CheckoutStep.PAYMENT_SELECTION}
        onClose={() => setCheckoutStep(CheckoutStep.IDLE)}
        customerData={customerData}
        onSubmit={handlePaymentSubmit}
      />

      <SuccessModal
        isOpen={checkoutStep === CheckoutStep.ORDER_CONFIRMATION}
        orderData={completedOrderData}
        onClose={() => {
          setCheckoutStep(CheckoutStep.IDLE);
          navigate('/');
        }}
      />

      {toastMessage && (
        <div className="fixed bottom-4 right-4 bg-slate-800 text-white px-6 py-3 rounded-xl shadow-lg animate-fade-in z-50 flex items-center gap-2">
          {toastMessage.includes('Failed') ? (
            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
          ) : (
            <div className="w-2 h-2 bg-brand rounded-full animate-pulse"></div>
          )}
          {toastMessage}
        </div>
      )}

    </div>
  );
};

export default Cart;

