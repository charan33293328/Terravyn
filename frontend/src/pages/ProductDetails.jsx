import React, { useState, useEffect } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { Leaf, CheckCircle2, ChevronRight, ArrowLeft, ShoppingCart, Plus, Minus } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useCart } from '../context/CartContext';
import axios from 'axios';
import LanguageSelector from '../components/LanguageSelector';
import CustomerDetailsModal from '../components/CustomerDetailsModal';
import PaymentSelectionModal from '../components/PaymentSelectionModal';
import SuccessModal from '../components/SuccessModal';
import { fetchPublicSettings } from '../api/publicCms';

const ProductDetails = () => {
  const { slug } = useParams();
  const { t } = useTranslation();
  const navigate = useNavigate();
  
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [settings, setSettings] = useState(null);
  
  const [mainImage, setMainImage] = useState('');
  const [isCustomerModalOpen, setIsCustomerModalOpen] = useState(false);
  const [isPaymentModalOpen, setIsPaymentModalOpen] = useState(false);
  const [customerData, setCustomerData] = useState(null);
  const [toastMessage, setToastMessage] = useState('');
  const [isSuccessModalOpen, setIsSuccessModalOpen] = useState(false);
  const [completedOrderData, setCompletedOrderData] = useState(null);
  
  const [quantity, setQuantity] = useState(1);
  const { addToCart, getCartCount } = useCart();

  const handleAddToCart = () => {
    addToCart(product, quantity);
    setToastMessage(`${quantity} item(s) added to cart`);
    setTimeout(() => setToastMessage(''), 3000);
  };

  const incrementQuantity = () => {
    // Arbitrary max 10, or could be bounded by stock later
    if (quantity < 10) setQuantity(prev => prev + 1);
  };

  const decrementQuantity = () => {
    if (quantity > 1) setQuantity(prev => prev - 1);
  };

  useEffect(() => {
    async function loadData() {
      const s = await fetchPublicSettings();
      setSettings(s);
      
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'https://terravyn-backend.onrender.com';
      try {
        const res = await axios.get(`${baseUrl}/api/public/products/${slug}`);
        const p = res.data;
        setProduct(p);
        if (p.images && p.images.length > 0) {
          setMainImage(p.images[0].image_url);
        } else if (p.primary_image) {
          setMainImage(p.primary_image);
        }
      } catch (err) {
        console.error("Failed to fetch product:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [slug]);

  const platformName = settings?.platform_name || 'TERRAVYN';
  const companyName = settings?.company_name || 'TERRAVYN Pvt Ltd';

  const handlePurchase = () => {
    setIsCustomerModalOpen(true);
  };

  const handleCustomerSubmit = (data) => {
    setCustomerData(data);
    setIsCustomerModalOpen(false);
    setIsPaymentModalOpen(true);
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
    setIsPaymentModalOpen(false);
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'https://terravyn-backend.onrender.com';

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
        const payload = { ...paymentInfo, productId: product.id, quantity };
        const createOrderRes = await axios.post(`${baseUrl}/api/orders/create-order`, payload);
        const orderData = createOrderRes.data;
        
        const options = {
          key: razorpayKey,
          amount: orderData.total_amount * 100, // paise
          currency: 'INR',
          name: platformName,
          description: product.name,
          image: mainImage,
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
                setIsSuccessModalOpen(true);
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
          theme: {
            color: '#16a34a'
          }
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
        const payload = { ...paymentInfo, productId: product.id, quantity };
        const createOrderRes = await axios.post(`${baseUrl}/api/orders/place-cod-order`, payload);
        const orderData = createOrderRes.data;
        
        setCompletedOrderData({
          order_id: orderData.order_id,
          payment_method: 'COD'
        });
        setIsSuccessModalOpen(true);
      } catch(err) {
        setToastMessage(err.response?.data?.detail || err.message || 'Failed to place COD order.');
      }
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand"></div>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center">
        <h2 className="text-2xl font-bold mb-4">Product Not Found</h2>
        <Link to="/pricing" className="text-brand font-bold hover:underline">Return to Products</Link>
      </div>
    );
  }

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
              <span className="font-bold text-xl tracking-tight text-slate-800">{platformName}</span>
            </Link>
            <div className="hidden md:flex items-center gap-8">
              <Link to="/pricing" className="text-sm font-bold text-slate-600 hover:text-brand transition-colors"><ArrowLeft size={16} className="inline mr-1"/> Back to Products</Link>
            </div>
            <div className="flex items-center gap-4">
              <LanguageSelector />
              <Link to="/login" className="text-sm font-medium text-slate-700 hover:text-brand transition-colors">{t('nav.login')}</Link>
              <Link to="/cart" className="relative cursor-pointer hover:opacity-80 transition-opacity">
                <ShoppingCart className="w-6 h-6 text-slate-700" />
                {getCartCount() > 0 && (
                  <span className="absolute -top-1.5 -right-1.5 bg-brand text-white text-[10px] font-bold w-4 h-4 rounded-full flex items-center justify-center">
                    {getCartCount()}
                  </span>
                )}
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <main className="pt-32 pb-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-12 lg:gap-20">
            
            {/* Left Column (Images) */}
            <div className="order-1">
              <div className="lg:sticky lg:top-32">
                <div className="w-full aspect-[4/3] rounded-[32px] overflow-hidden bg-white shadow-xl border-4 border-white relative mb-6">
                  {mainImage ? (
                    <img src={mainImage} className="w-full h-full object-cover" alt={product.name} />
                  ) : (
                    <div className="absolute inset-0 bg-slate-50 flex items-center justify-center">
                      <Leaf className="w-24 h-24 text-slate-200" />
                    </div>
                  )}
                </div>

                {product.images && product.images.length > 0 && (
                  <div className="flex gap-4 overflow-x-auto pb-4">
                    {product.images.map((img, index) => (
                      <button 
                        key={index}
                        onClick={() => setMainImage(img.image_url)}
                        className={`flex-shrink-0 w-24 h-24 rounded-2xl overflow-hidden bg-white border-4 transition-all duration-300 ${mainImage === img.image_url ? 'border-brand shadow-lg scale-105' : 'border-transparent hover:border-brand/30 hover:scale-105'}`}
                      >
                        <img src={img.image_url} className="w-full h-full object-cover" alt="Thumbnail" />
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
            
            {/* Right Column (Details) */}
            <div className="order-2 flex flex-col space-y-8">
              <div>
                <div className="flex items-center gap-3 mb-3">
                  <span className="text-sm font-bold text-brand bg-brand/10 px-3 py-1 rounded-full uppercase tracking-wider">{product.category || 'System'}</span>
                  <span className="text-xs text-slate-400 font-mono">SKU: {product.sku}</span>
                </div>
                <h1 className="text-4xl lg:text-5xl font-extrabold text-slate-900 tracking-tight mb-4">
                  {product.name}
                </h1>
                {product.tagline && (
                  <p className="text-xl text-brand font-medium tracking-wide mb-6">
                    {product.tagline}
                  </p>
                )}
                <p className="text-lg text-slate-600 leading-relaxed whitespace-pre-line">
                  {product.full_description || product.short_description}
                </p>
              </div>

              {/* Pricing & Checkout Card */}
              <div className="bg-white rounded-3xl p-8 shadow-xl border border-slate-100 relative overflow-hidden">
                <div className="absolute top-0 right-0 w-32 h-32 bg-brand/5 rounded-bl-full -mr-8 -mt-8"></div>
                
                <div className="flex justify-between items-end mb-8 relative z-10">
                  <div>
                    <p className="text-sm text-slate-500 font-medium uppercase tracking-wider mb-2">Total Price</p>
                    <div className="flex items-baseline gap-3">
                      <span className="text-5xl font-extrabold text-slate-900">₹{product.current_price.toLocaleString()}</span>
                      {product.discount_percentage > 0 && (
                        <div className="flex flex-col">
                          <span className="text-sm text-slate-400 line-through">₹{product.mrp.toLocaleString()}</span>
                          <span className="text-xs font-bold text-orange-500 bg-orange-50 px-2 py-0.5 rounded mt-0.5">
                            {product.discount_percentage}% OFF
                          </span>
                        </div>
                      )}
                    </div>
                    {product.tax_percentage > 0 && <p className="text-sm text-slate-500 mt-2 font-medium">+{product.tax_percentage}% GST will be added at checkout</p>}
                  </div>
                  <div className="flex flex-col items-end gap-2">
                    {product.stock_status === 'IN_STOCK' ? (
                      <div className="flex items-center gap-2 bg-green-50 text-brand px-4 py-2 rounded-full border border-green-200">
                        <span className="relative flex h-3 w-3">
                          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand opacity-75"></span>
                          <span className="relative inline-flex rounded-full h-3 w-3 bg-brand"></span>
                        </span>
                        <span className="font-bold text-sm tracking-wide">In Stock</span>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2 bg-red-50 text-red-600 px-4 py-2 rounded-full border border-red-200">
                        <span className="font-bold text-sm tracking-wide">Out of Stock</span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="mb-6 flex items-center justify-between">
                  <span className="text-sm font-bold text-slate-700">Quantity</span>
                  <div className="flex items-center border border-slate-200 rounded-lg bg-white overflow-hidden shadow-sm">
                    <button 
                      onClick={decrementQuantity}
                      disabled={quantity <= 1 || product.stock_status !== 'IN_STOCK'}
                      className="px-3 py-2 text-slate-500 hover:bg-slate-50 hover:text-brand disabled:opacity-50 transition-colors"
                    >
                      <Minus size={18} />
                    </button>
                    <div className="w-12 text-center font-bold text-slate-800 border-x border-slate-200 py-2">
                      {quantity}
                    </div>
                    <button 
                      onClick={incrementQuantity}
                      disabled={quantity >= 10 || product.stock_status !== 'IN_STOCK'}
                      className="px-3 py-2 text-slate-500 hover:bg-slate-50 hover:text-brand disabled:opacity-50 transition-colors"
                    >
                      <Plus size={18} />
                    </button>
                  </div>
                </div>

                <div className="flex flex-col sm:flex-row gap-3">
                  <button 
                    onClick={handleAddToCart}
                    disabled={product.stock_status !== 'IN_STOCK'}
                    className="flex-1 py-4 bg-white border-2 border-brand text-brand hover:bg-brand/5 disabled:border-slate-300 disabled:text-slate-400 disabled:bg-slate-50 disabled:cursor-not-allowed font-bold rounded-2xl shadow-sm transition-all flex items-center justify-center gap-2"
                  >
                    <ShoppingCart size={20} />
                    Add to Cart
                  </button>

                  <button 
                    onClick={handlePurchase}
                    disabled={product.stock_status !== 'IN_STOCK'}
                    className="flex-1 py-4 bg-brand hover:bg-brand-dark disabled:bg-slate-300 disabled:cursor-not-allowed text-white font-bold rounded-2xl shadow-lg transition-all flex items-center justify-center gap-2"
                  >
                    Buy Now
                    <ChevronRight size={20} />
                  </button>
                </div>
              </div>

              {/* Features & Specs */}
              {((product.features && product.features.length > 0) || (product.specifications && product.specifications.length > 0)) && (
                <div className="grid sm:grid-cols-2 gap-8 pt-8 border-t border-slate-200">
                  {product.features && product.features.length > 0 && (
                    <div>
                      <h3 className="text-xl font-bold text-slate-900 mb-6 flex items-center gap-2">
                        <Leaf className="w-5 h-5 text-brand" />
                        Key Features
                      </h3>
                      <ul className="space-y-3">
                        {product.features.map((feat, index) => (
                          <li key={index} className="flex items-start gap-3">
                            <CheckCircle2 className="w-5 h-5 text-brand flex-shrink-0 mt-0.5" />
                            <span className="text-slate-700">{feat.feature}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {product.specifications && product.specifications.length > 0 && (
                    <div>
                      <h3 className="text-xl font-bold text-slate-900 mb-6 flex items-center gap-2">
                        Technical Specs
                      </h3>
                      <div className="bg-white rounded-2xl border border-slate-100 overflow-hidden shadow-sm">
                        <table className="w-full text-sm">
                          <tbody className="divide-y divide-slate-100">
                            {product.specifications.map((spec, index) => (
                              <tr key={index} className={index % 2 === 0 ? 'bg-slate-50/50' : 'bg-white'}>
                                <td className="py-3 px-4 font-bold text-slate-700 w-1/3">{spec.key}</td>
                                <td className="py-3 px-4 text-slate-600">{spec.value}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              )}

            </div>
          </div>
        </div>
      </main>

      <footer className="bg-slate-900 py-12 text-center text-slate-400 border-t border-slate-800 mt-12">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex justify-center items-center gap-2 mb-6">
            <Leaf className="w-5 h-5 text-brand" />
            <span className="font-bold text-lg text-white">{platformName}</span>
          </div>
          <p>&copy; {new Date().getFullYear()} {companyName}. {t('footer.rights')}</p>
        </div>
      </footer>

      <CustomerDetailsModal 
        isOpen={isCustomerModalOpen} 
        onClose={() => setIsCustomerModalOpen(false)} 
        onSubmit={handleCustomerSubmit} 
      />

      <PaymentSelectionModal
        isOpen={isPaymentModalOpen}
        onClose={() => setIsPaymentModalOpen(false)}
        onBack={() => {setIsPaymentModalOpen(false); setIsCustomerModalOpen(true);}}
        onSubmit={handlePaymentSubmit}
        customerDetails={customerData}
      />

      <SuccessModal
        isOpen={isSuccessModalOpen}
        onClose={() => setIsSuccessModalOpen(false)}
        orderDetails={completedOrderData}
      />

      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-[200] bg-slate-900 text-white px-6 py-4 rounded-xl shadow-2xl flex items-center gap-3">
          <CheckCircle2 className="w-6 h-6 text-brand" />
          <span className="font-medium">{toastMessage}</span>
        </div>
      )}
    </div>
  );
};

export default ProductDetails;
