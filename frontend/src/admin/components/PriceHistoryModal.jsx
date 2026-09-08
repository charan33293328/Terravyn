import React, { useState, useEffect } from 'react';
import { X, Clock, ArrowRight, TrendingDown, TrendingUp } from 'lucide-react';
import api from '../../api/client';

const PriceHistoryModal = ({ isOpen, onClose, product }) => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isOpen && product) {
      fetchHistory();
    }
  }, [isOpen, product]);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/admin/products/${product.id}/price-history`);
      setHistory(res.data);
    } catch (err) {
      console.error("Failed to fetch price history", err);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen || !product) return null;

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
      year: 'numeric', month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm" onClick={onClose} />
      
      <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-xl w-full max-w-2xl relative z-10 overflow-hidden flex flex-col max-h-[80vh]">
        <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-800/50 flex justify-between items-center bg-slate-50 dark:bg-slate-950 shrink-0">
          <div>
            <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100">Price History</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400">{product.name} ({product.sku})</p>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 dark:text-slate-300 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto custom-scrollbar">
          {loading ? (
            <div className="flex justify-center items-center h-40">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand"></div>
            </div>
          ) : history.length === 0 ? (
            <div className="text-center py-10 text-slate-500 dark:text-slate-400 flex flex-col items-center">
              <Clock className="w-10 h-10 mb-2 opacity-20" />
              <p>No price history found.</p>
            </div>
          ) : (
            <div className="space-y-6 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-slate-200 before:to-transparent">
              {history.map((record, index) => {
                const isIncrease = record.new_price > record.old_price;
                const isInitial = record.old_price === 0;
                
                return (
                  <div key={record.id} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                    {/* Timeline dot */}
                    <div className="flex items-center justify-center w-10 h-10 rounded-full border-4 border-white bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 shadow-sm z-10">
                      {isInitial ? <Clock size={16} /> : isIncrease ? <TrendingUp size={16} className="text-orange-500" /> : <TrendingDown size={16} className="text-brand" />}
                    </div>
                    
                    {/* Card */}
                    <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">{formatDate(record.effective_from)}</span>
                        {!record.effective_until && (
                          <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs font-bold rounded-full">Current</span>
                        )}
                      </div>
                      
                      {!isInitial ? (
                        <div className="flex items-center gap-3 mb-3">
                          <div className="text-slate-500 dark:text-slate-400 line-through text-sm">₹{record.old_price.toLocaleString()}</div>
                          <ArrowRight size={14} className="text-slate-300" />
                          <div className={`font-bold text-lg ${isIncrease ? 'text-orange-600' : 'text-brand'}`}>₹{record.new_price.toLocaleString()}</div>
                        </div>
                      ) : (
                        <div className="mb-3">
                          <span className="text-xs text-slate-500 dark:text-slate-400 block mb-1">Initial Price</span>
                          <div className="font-bold text-lg text-slate-800 dark:text-slate-100">₹{record.new_price.toLocaleString()}</div>
                        </div>
                      )}
                      
                      <div className="text-sm text-slate-600 dark:text-slate-300 bg-slate-50 dark:bg-slate-950 p-2 rounded border border-slate-100 dark:border-slate-800/50">
                        <span className="font-medium">Reason: </span>
                        {record.reason || "Not specified"}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PriceHistoryModal;
