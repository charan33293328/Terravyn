import React, { useState, useEffect } from 'react';
import { Tag, Search, TrendingDown, Clock, Edit2, AlertCircle, Image as ImageIcon } from 'lucide-react';
import api from '../../api/client';
import UpdatePriceModal from '../components/UpdatePriceModal';
import PriceHistoryModal from '../components/PriceHistoryModal';
import EditImagesModal from '../components/EditImagesModal';

const Products = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  
  // Modal states
  const [selectedProductForPrice, setSelectedProductForPrice] = useState(null);
  const [selectedProductForHistory, setSelectedProductForHistory] = useState(null);
  const [selectedProductForImages, setSelectedProductForImages] = useState(null);

  const fetchProducts = async () => {
    try {
      setLoading(true);
      const res = await api.get('/admin/products');
      setProducts(res.data);
    } catch (err) {
      console.error("Failed to fetch products", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, []);

  const toggleStatus = async (product) => {
    try {
      await api.put(`/admin/products/${product.id}/status?is_active=${!product.is_active}`);
      fetchProducts();
    } catch (err) {
      console.error("Failed to toggle status", err);
    }
  };

  const filteredProducts = products.filter(p => 
    p.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
    p.sku.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-fade-in">
      
      {/* Header section */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-white dark:bg-slate-900 p-6 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-800/50">
        <div>
          <h1 className="text-2xl font-black text-slate-800 dark:text-slate-100 tracking-tight flex items-center gap-2">
            <Tag className="text-brand w-7 h-7" />
            Product Management
          </h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">Manage product catalog, pricing, and view price history</p>
        </div>
      </div>

      {/* Controls */}
      <div className="flex flex-col md:flex-row justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 w-5 h-5" />
          <input
            type="text"
            placeholder="Search products by name or SKU..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-11 pr-4 py-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand/20 focus:border-brand transition-all shadow-sm"
          />
        </div>
      </div>

      {/* Table */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-800/50 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 dark:bg-slate-950/50 border-b border-slate-100 dark:border-slate-800/50 text-sm font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                <th className="px-6 py-4">Product</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4">Pricing</th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/50">
              {loading ? (
                <tr>
                  <td colSpan="4" className="px-6 py-12 text-center text-slate-500 dark:text-slate-400">
                    <div className="animate-pulse flex flex-col items-center">
                      <div className="h-8 w-8 border-4 border-brand border-t-transparent rounded-full animate-spin mb-4"></div>
                      <p>Loading products...</p>
                    </div>
                  </td>
                </tr>
              ) : filteredProducts.length === 0 ? (
                <tr>
                  <td colSpan="4" className="px-6 py-12 text-center text-slate-500 dark:text-slate-400 flex flex-col items-center">
                    <AlertCircle className="w-12 h-12 text-slate-300 mb-3" />
                    <p className="text-lg font-medium text-slate-600 dark:text-slate-300">No products found</p>
                    <p className="text-sm mt-1">Try adjusting your search criteria</p>
                  </td>
                </tr>
              ) : (
                filteredProducts.map((product) => (
                  <tr key={product.id} className="hover:bg-slate-50 dark:bg-slate-950/80 transition-colors group">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-brand/10 flex items-center justify-center text-brand font-bold shrink-0">
                          {product.name.charAt(0)}
                        </div>
                        <div>
                          <p className="font-bold text-slate-800 dark:text-slate-100">{product.name}</p>
                          <p className="text-xs text-slate-500 dark:text-slate-400 font-mono mt-0.5">{product.sku}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <button
                        onClick={() => toggleStatus(product)}
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2 ${
                          product.is_active ? 'bg-brand' : 'bg-slate-200'
                        }`}
                      >
                        <span
                          className={`inline-block h-4 w-4 transform rounded-full bg-white dark:bg-slate-900 transition-transform ${
                            product.is_active ? 'translate-x-6' : 'translate-x-1'
                          }`}
                        />
                      </button>
                      <span className={`ml-3 text-xs font-medium ${product.is_active ? 'text-brand' : 'text-slate-400'}`}>
                        {product.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <span className="text-lg font-bold text-slate-800 dark:text-slate-100">₹{product.current_price.toLocaleString()}</span>
                        {product.discount_percentage > 0 && (
                          <div className="flex flex-col">
                            <span className="text-xs text-slate-400 line-through">₹{product.mrp.toLocaleString()}</span>
                            <span className="text-[10px] font-bold text-orange-500 bg-orange-50 px-1.5 py-0.5 rounded">
                              {product.discount_percentage}% OFF
                            </span>
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => setSelectedProductForImages(product)}
                          className="p-2 text-slate-400 hover:text-brand hover:bg-brand/10 rounded-lg transition-colors tooltip-trigger"
                          title="Manage Images"
                        >
                          <ImageIcon size={18} />
                        </button>
                        <button
                          onClick={() => setSelectedProductForHistory(product)}
                          className="p-2 text-slate-400 hover:text-brand hover:bg-brand/10 rounded-lg transition-colors tooltip-trigger"
                          title="View Price History"
                        >
                          <Clock size={18} />
                        </button>
                        <button
                          onClick={() => setSelectedProductForPrice(product)}
                          className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-brand hover:text-white rounded-lg transition-all font-medium text-sm border border-slate-200 dark:border-slate-800 hover:border-brand"
                        >
                          <Edit2 size={14} /> Update Price
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modals */}
      <UpdatePriceModal 
        isOpen={!!selectedProductForPrice}
        onClose={() => setSelectedProductForPrice(null)}
        product={selectedProductForPrice}
        onUpdate={fetchProducts}
      />

      <PriceHistoryModal
        isOpen={!!selectedProductForHistory}
        onClose={() => setSelectedProductForHistory(null)}
        product={selectedProductForHistory}
      />

      <EditImagesModal
        isOpen={!!selectedProductForImages}
        onClose={() => setSelectedProductForImages(null)}
        product={selectedProductForImages}
        onUpdate={fetchProducts}
      />
      
    </div>
  );
};

export default Products;
