import React, { useState, useEffect } from 'react';
import { Tag, Search, Edit2, AlertCircle, Plus, Eye, Archive, Trash2, Copy } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../../api/client';

const ProductCatalog = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const navigate = useNavigate();

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

  const handleStatusChange = async (id, status) => {
    if (!window.confirm(`Are you sure you want to change the status to ${status}?`)) return;
    try {
      await api.put(`/admin/products/${id}/publish?status=${status}`);
      fetchProducts();
    } catch (err) {
      console.error("Failed to change status", err);
      alert("Failed to change status");
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to permanently delete this product? This action cannot be undone.")) return;
    try {
      await api.delete(`/admin/products/${id}`);
      fetchProducts();
    } catch (err) {
      console.error("Failed to delete product", err);
      alert("Failed to delete product");
    }
  };

  const filteredProducts = products.filter(p => 
    p.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
    p.sku.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-fade-in">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-white dark:bg-slate-900 p-6 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-800/50">
        <div>
          <h1 className="text-2xl font-black text-slate-800 dark:text-slate-100 tracking-tight flex items-center gap-2">
            <Tag className="text-brand w-7 h-7" />
            Product Catalog
          </h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">Manage multiple products, pricing, and visibility</p>
        </div>
        <button 
          onClick={() => navigate('/admin/products/new')}
          className="bg-brand text-white px-5 py-2.5 rounded-xl font-bold flex items-center gap-2 hover:bg-brand-dark transition-colors shadow-sm"
        >
          <Plus size={20} />
          Add Product
        </button>
      </div>

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

      <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-800/50 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 dark:bg-slate-950/50 border-b border-slate-100 dark:border-slate-800/50 text-sm font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                <th className="px-6 py-4">Product</th>
                <th className="px-6 py-4">Category</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4">Pricing</th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/50">
              {loading ? (
                <tr>
                  <td colSpan="5" className="px-6 py-12 text-center text-slate-500 dark:text-slate-400">
                    <div className="animate-pulse flex flex-col items-center">
                      <div className="h-8 w-8 border-4 border-brand border-t-transparent rounded-full animate-spin mb-4"></div>
                      <p>Loading products...</p>
                    </div>
                  </td>
                </tr>
              ) : filteredProducts.length === 0 ? (
                <tr>
                  <td colSpan="5" className="px-6 py-12 text-center text-slate-500 dark:text-slate-400 flex flex-col items-center">
                    <AlertCircle className="w-12 h-12 text-slate-300 mb-3" />
                    <p className="text-lg font-medium text-slate-600 dark:text-slate-300">No products found</p>
                  </td>
                </tr>
              ) : (
                filteredProducts.map((product) => (
                  <tr key={product.id} className="hover:bg-slate-50 dark:bg-slate-950/80 transition-colors group">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-lg bg-slate-100 dark:bg-slate-800 overflow-hidden border border-slate-200 dark:border-slate-800 shrink-0">
                          {product.primary_image ? (
                            <img src={product.primary_image} alt={product.name} className="w-full h-full object-cover" />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center text-slate-400 font-bold bg-slate-100 dark:bg-slate-800">
                              {product.name.charAt(0)}
                            </div>
                          )}
                        </div>
                        <div>
                          <p className="font-bold text-slate-800 dark:text-slate-100">{product.name}</p>
                          <p className="text-xs text-slate-500 dark:text-slate-400 font-mono mt-0.5">{product.sku}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-sm text-slate-600 dark:text-slate-300">{product.category || 'Uncategorized'}</span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex flex-col gap-1 items-start">
                        <span className={`text-xs font-bold px-2 py-1 rounded-md ${
                          product.status === 'PUBLISHED' ? 'bg-green-100 text-green-700' : 
                          product.status === 'ARCHIVED' ? 'bg-slate-200 text-slate-600 dark:text-slate-300' : 'bg-orange-100 text-orange-700'
                        }`}>
                          {product.status}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <span className="text-lg font-bold text-slate-800 dark:text-slate-100">₹{product.current_price.toLocaleString()}</span>
                        {product.mrp > product.current_price && (
                          <span className="text-xs text-slate-400 line-through">₹{product.mrp.toLocaleString()}</span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => window.open(`/products/${product.slug}`, '_blank')}
                          className="p-2 text-slate-400 hover:text-brand hover:bg-brand/10 rounded-lg transition-colors tooltip-trigger"
                          title="View on Website"
                        >
                          <Eye size={18} />
                        </button>
                        
                        <button
                          onClick={() => navigate(`/admin/products/${product.id}`)}
                          className="p-2 text-slate-400 hover:text-brand hover:bg-brand/10 rounded-lg transition-colors tooltip-trigger"
                          title="Edit Product"
                        >
                          <Edit2 size={18} />
                        </button>

                        {product.status !== 'PUBLISHED' && (
                          <button
                            onClick={() => handleStatusChange(product.id, 'PUBLISHED')}
                            className="p-2 text-slate-400 hover:text-green-600 hover:bg-green-50 rounded-lg transition-colors tooltip-trigger"
                            title="Publish"
                          >
                            <span className="font-bold text-xs">PUB</span>
                          </button>
                        )}
                        
                        {product.status === 'PUBLISHED' && (
                          <button
                            onClick={() => handleStatusChange(product.id, 'DRAFT')}
                            className="p-2 text-slate-400 hover:text-orange-600 hover:bg-orange-50 rounded-lg transition-colors tooltip-trigger"
                            title="Unpublish (Draft)"
                          >
                            <Archive size={18} />
                          </button>
                        )}
                        
                        <button
                          onClick={() => handleDelete(product.id)}
                          className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors tooltip-trigger"
                          title="Delete"
                        >
                          <Trash2 size={18} />
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
    </div>
  );
};

export default ProductCatalog;
