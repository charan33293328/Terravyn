import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Leaf, ChevronRight, CheckCircle2, Menu, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import LanguageSelector from '../components/LanguageSelector';
import { fetchPublicSettings } from '../api/publicCms';

const Pricing = () => {
  const { t } = useTranslation();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [settings, setSettings] = useState(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    async function loadData() {
      const s = await fetchPublicSettings();
      setSettings(s);
      
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'https://terravyn-backend.onrender.com';
      try {
        const res = await axios.get(`${baseUrl}/api/public/products`);
        setProducts(res.data || []);
      } catch (err) {
        console.error("Failed to fetch products:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const platformName = settings?.platform_name || 'TERRAVYN';
  const companyName = settings?.company_name || 'TERRAVYN Pvt Ltd';

  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900 animate-fade-in">
      <nav className="fixed w-full bg-white/90 backdrop-blur-md z-50 border-b border-slate-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-20">
            <Link to="/" className="flex items-center gap-2" onClick={() => setMobileMenuOpen(false)}>
              <div className="w-10 h-10 bg-brand rounded-xl flex items-center justify-center shadow-lg shadow-brand/20">
                <Leaf className="w-6 h-6 text-white" />
              </div>
              <span className="font-bold text-xl tracking-tight text-slate-800">{platformName}</span>
            </Link>
            
            {/* Desktop Links */}
            <div className="hidden md:flex items-center gap-8">
              <Link to="/#home" className="text-sm font-medium text-slate-600 hover:text-brand transition-colors">{t('nav.home')}</Link>
              <Link to="/#features" className="text-sm font-medium text-slate-600 hover:text-brand transition-colors">{t('nav.features')}</Link>
              <Link to="/#how-it-works" className="text-sm font-medium text-slate-600 hover:text-brand transition-colors">{t('nav.howItWorks')}</Link>
              <Link to="/pricing" className="text-sm font-bold text-brand transition-colors">{t('nav.pricing')}</Link>
            </div>

            {/* Desktop & Mobile Actions */}
            <div className="flex items-center gap-3">
              <LanguageSelector />
              
              <div className="hidden sm:flex items-center gap-3">
                <Link to="/login" className="text-sm font-medium text-slate-700 hover:text-brand transition-colors px-2 py-1">{t('nav.login')}</Link>
                <Link to="/signup" className="px-4 py-2 bg-brand text-white text-sm font-medium rounded-lg shadow-md shadow-brand/20 hover:bg-brand-dark transition-all hover:-translate-y-0.5 whitespace-nowrap">
                  {t('nav.getStarted')}
                </Link>
              </div>

              {/* Hamburger Button */}
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="md:hidden p-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors"
                aria-label="Toggle navigation menu"
              >
                {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Navigation Drawer */}
        <AnimatePresence>
          {mobileMenuOpen && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="md:hidden bg-white border-b border-slate-200 overflow-hidden shadow-xl"
            >
              <div className="px-4 py-6 space-y-4">
                <div className="flex flex-col space-y-3">
                  <Link
                    to="/#home"
                    onClick={() => setMobileMenuOpen(false)}
                    className="px-3 py-2 text-base font-semibold text-slate-700 hover:bg-slate-50 hover:text-brand rounded-lg transition-colors"
                  >
                    {t('nav.home')}
                  </Link>
                  <Link
                    to="/#features"
                    onClick={() => setMobileMenuOpen(false)}
                    className="px-3 py-2 text-base font-semibold text-slate-700 hover:bg-slate-50 hover:text-brand rounded-lg transition-colors"
                  >
                    {t('nav.features')}
                  </Link>
                  <Link
                    to="/#how-it-works"
                    onClick={() => setMobileMenuOpen(false)}
                    className="px-3 py-2 text-base font-semibold text-slate-700 hover:bg-slate-50 hover:text-brand rounded-lg transition-colors"
                  >
                    {t('nav.howItWorks')}
                  </Link>
                  <Link
                    to="/pricing"
                    onClick={() => setMobileMenuOpen(false)}
                    className="px-3 py-2 text-base font-bold text-brand bg-brand/5 rounded-lg transition-colors"
                  >
                    {t('nav.pricing')}
                  </Link>
                </div>

                <div className="pt-4 border-t border-slate-100 flex flex-col gap-3">
                  <Link
                    to="/login"
                    onClick={() => setMobileMenuOpen(false)}
                    className="w-full text-center py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-100 rounded-xl border border-slate-200 transition-colors"
                  >
                    {t('nav.login')}
                  </Link>
                  <Link
                    to="/signup"
                    onClick={() => setMobileMenuOpen(false)}
                    className="w-full text-center py-3 bg-brand text-white text-sm font-bold rounded-xl shadow-md shadow-brand/20 hover:bg-brand-dark transition-colors"
                  >
                    {t('nav.getStarted')}
                  </Link>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </nav>

      <main className="pt-28 sm:pt-32 pb-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center mb-12 sm:mb-16">
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-slate-900 tracking-tight mb-3 sm:mb-4">
            Our Products
          </h1>
          <p className="text-base sm:text-xl text-slate-600 max-w-2xl mx-auto px-2">
            Explore our range of smart agriculture solutions designed to optimize your farm.
          </p>
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {loading ? (
            <div className="flex justify-center items-center py-20">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand"></div>
            </div>
          ) : products.length === 0 ? (
            <div className="text-center py-20 bg-white rounded-3xl shadow-sm border border-slate-100 p-6">
              <h2 className="text-2xl font-bold text-slate-800 mb-2">No products available</h2>
              <p className="text-slate-500">Please check back later.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8">
              {products.map(product => (
                <div key={product.id} className="bg-white rounded-3xl shadow-sm border border-slate-100 overflow-hidden hover:shadow-xl transition-all duration-300 group flex flex-col">
                  <div className="aspect-[4/3] bg-slate-50 relative overflow-hidden">
                    {product.primary_image ? (
                      <img src={product.primary_image} alt={product.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                    ) : (
                      <div className="flex items-center justify-center w-full h-full text-slate-300">
                        <Leaf size={64} />
                      </div>
                    )}
                    {product.discount_percentage > 0 && (
                      <div className="absolute top-4 right-4 bg-orange-500 text-white text-xs font-bold px-3 py-1.5 rounded-full shadow-md">
                        {product.discount_percentage}% OFF
                      </div>
                    )}
                  </div>
                  
                  <div className="p-6 sm:p-8 flex flex-col flex-1">
                    <div className="text-xs font-bold text-brand uppercase tracking-wider mb-2">{product.category || 'System'}</div>
                    <h3 className="text-xl sm:text-2xl font-bold text-slate-900 mb-2 line-clamp-2">{product.name}</h3>
                    <p className="text-slate-600 mb-6 text-sm sm:text-base line-clamp-3">{product.short_description || product.tagline}</p>
                    
                    <div className="mt-auto pt-6 border-t border-slate-100">
                      <div className="flex items-end justify-between mb-6">
                        <div>
                          <p className="text-xs sm:text-sm text-slate-500 font-medium mb-1">Price</p>
                          <div className="flex items-baseline gap-2">
                            <span className="text-2xl sm:text-3xl font-extrabold text-slate-900">₹{product.current_price.toLocaleString()}</span>
                            {product.mrp > product.current_price && (
                              <span className="text-xs sm:text-sm text-slate-400 line-through">₹{product.mrp.toLocaleString()}</span>
                            )}
                          </div>
                        </div>
                      </div>
                      
                      <Link 
                        to={`/products/${product.slug}`}
                        className="w-full py-3 sm:py-3.5 bg-brand/10 text-brand font-bold text-sm sm:text-base rounded-xl hover:bg-brand hover:text-white transition-colors flex items-center justify-center gap-2"
                      >
                        View Details
                        <ChevronRight size={18} />
                      </Link>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>


      <footer className="bg-slate-900 py-12 text-center text-slate-400 border-t border-slate-800">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex justify-center items-center gap-2 mb-6 opacity-80 hover:opacity-100 transition-opacity">
            <Leaf className="w-5 h-5 text-brand" />
            <span className="font-bold text-lg text-white tracking-wide">{platformName}</span>
          </div>
          <p>&copy; {new Date().getFullYear()} {companyName}. {t('footer.rights')}</p>
        </div>
      </footer>
    </div>
  );
};

export default Pricing;
