import React, { useState, useEffect } from 'react';
import { X, Save, AlertTriangle } from 'lucide-react';
import api from '../../api/client';

const UpdatePriceModal = ({ isOpen, onClose, product, onUpdate }) => {
  const [sellingPrice, setSellingPrice] = useState('');
  const [mrp, setMrp] = useState('');
  const [reason, setReason] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (product) {
      setSellingPrice(product.current_price || '');
      setMrp(product.mrp || '');
      setReason('');
      setError('');
    }
  }, [product, isOpen]);

  if (!isOpen || !product) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    const sp = parseFloat(sellingPrice);
    const m = parseFloat(mrp);

    if (isNaN(sp) || isNaN(m)) {
      setError('Please enter valid numbers for prices.');
      return;
    }

    if (sp <= 0) {
      setError('Selling Price must be greater than 0.');
      return;
    }

    if (m < sp) {
      setError('MRP cannot be less than the Selling Price.');
      return;
    }

    if (!reason.trim()) {
      setError('A reason for the price change is required.');
      return;
    }

    setLoading(true);
    try {
      await api.put(`/admin/products/${product.id}/price`, {
        current_price: sp,
        mrp: m,
        reason: reason.trim()
      });
      onUpdate();
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update price');
    } finally {
      setLoading(false);
    }
  };

  const discount = mrp && sellingPrice && parseFloat(mrp) > 0 
    ? (((parseFloat(mrp) - parseFloat(sellingPrice)) / parseFloat(mrp)) * 100).toFixed(2)
    : 0;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm" onClick={onClose} />
      
      <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-xl w-full max-w-lg relative z-10 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-800/50 flex justify-between items-center bg-slate-50 dark:bg-slate-950">
          <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100">Update Product Price</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 dark:text-slate-300 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {error && (
            <div className="p-3 bg-red-50 text-red-700 rounded-lg flex items-start gap-2 text-sm border border-red-100">
              <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-200 mb-1">Product Name</label>
            <input 
              type="text" 
              value={product.name} 
              disabled 
              className="w-full px-4 py-2 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg text-slate-500 dark:text-slate-400 cursor-not-allowed"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-200 mb-1">Selling Price (₹)</label>
              <input 
                type="number" 
                min="1"
                step="0.01"
                value={sellingPrice}
                onChange={(e) => setSellingPrice(e.target.value)}
                className="w-full px-4 py-2 border border-slate-200 dark:border-slate-800 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand/20 focus:border-brand"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-200 mb-1">Original MRP (₹)</label>
              <input 
                type="number" 
                min="1"
                step="0.01"
                value={mrp}
                onChange={(e) => setMrp(e.target.value)}
                className="w-full px-4 py-2 border border-slate-200 dark:border-slate-800 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand/20 focus:border-brand"
                required
              />
            </div>
          </div>

          <div className="flex justify-between items-center p-3 bg-slate-50 dark:bg-slate-950 rounded-lg border border-slate-100 dark:border-slate-800/50">
            <span className="text-sm text-slate-500 dark:text-slate-400">Calculated Discount</span>
            <span className="font-bold text-brand">{discount}% OFF</span>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-200 mb-1">Reason for Price Change</label>
            <textarea 
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="e.g. Festival Season Sale, Base Price Increase"
              className="w-full px-4 py-2 border border-slate-200 dark:border-slate-800 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand/20 focus:border-brand h-24 resize-none"
              required
            />
          </div>

          <div className="pt-2 flex justify-end gap-3">
            <button 
              type="button" 
              onClick={onClose}
              className="px-4 py-2 text-slate-600 dark:text-slate-300 font-medium hover:bg-slate-100 dark:bg-slate-800 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button 
              type="submit" 
              disabled={loading}
              className="px-6 py-2 bg-brand text-white font-medium rounded-lg hover:bg-brand-dark transition-colors shadow-md shadow-brand/20 flex items-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed"
            >
              <Save className="w-4 h-4" />
              {loading ? 'Saving...' : 'Confirm Update'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default UpdatePriceModal;
