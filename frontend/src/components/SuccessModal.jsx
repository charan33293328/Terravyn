import React, { useEffect, useState } from 'react';
import { CheckCircle2, Download, ExternalLink, X, FileText } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const SuccessModal = ({ isOpen, onClose, orderDetails }) => {
  const [invoice, setInvoice] = useState(null);
  const [loading, setLoading] = useState(true);

  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  useEffect(() => {
    if (isOpen && orderDetails?.order_id) {
      // Fetch invoice details
      fetch(`${baseUrl}/api/invoices/${orderDetails.order_id}`)
        .then(res => res.json())
        .then(data => {
          setInvoice(data);
          setLoading(false);
        })
        .catch(err => {
          console.error("Failed to fetch invoice", err);
          setLoading(false);
        });
    }
  }, [isOpen, orderDetails, baseUrl]);

  if (!isOpen) return null;

  const handleDownload = () => {
    window.open(`${baseUrl}/api/invoices/${orderDetails.order_id}/download`, '_blank');
  };

  const handleView = () => {
    window.open(`${baseUrl}/api/invoices/${orderDetails.order_id}/view`, '_blank');
  };

  const isOnline = orderDetails?.payment_method === 'ONLINE';

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 sm:p-0">
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm"
        />
        
        <motion.div 
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          className="relative w-full max-w-lg bg-white rounded-3xl shadow-2xl overflow-hidden flex flex-col"
        >
          {/* Header */}
          <div className="bg-green-50 px-8 py-10 text-center relative border-b border-green-100">
            <button 
              onClick={onClose}
              className="absolute top-4 right-4 p-2 text-slate-400 hover:text-slate-600 bg-white rounded-full shadow-sm hover:shadow transition-all"
            >
              <X className="w-5 h-5" />
            </button>
            <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6 shadow-inner">
              <CheckCircle2 className="w-10 h-10 text-brand" />
            </div>
            <h2 className="text-3xl font-extrabold text-slate-900 mb-2">
              {isOnline ? "Payment Successful" : "Order Placed Successfully"}
            </h2>
            <p className="text-green-700 font-medium text-lg">
              Thank you for choosing TERRAVYN!
            </p>
          </div>

          {/* Body */}
          <div className="px-8 py-8 flex flex-col gap-6">
            <div className="bg-slate-50 rounded-2xl p-6 border border-slate-100 space-y-4">
              <div className="flex justify-between items-center pb-4 border-b border-slate-200">
                <span className="text-slate-500 font-medium">Order ID</span>
                <span className="text-slate-900 font-bold tracking-wide">{orderDetails.order_id}</span>
              </div>
              
              <div className="flex justify-between items-center pb-4 border-b border-slate-200">
                <span className="text-slate-500 font-medium">Payment Status</span>
                {isOnline ? (
                  <span className="px-3 py-1 bg-green-100 text-green-700 text-sm font-bold rounded-full">
                    PAID
                  </span>
                ) : (
                  <span className="px-3 py-1 bg-orange-100 text-orange-700 text-sm font-bold rounded-full">
                    PAYMENT PENDING
                  </span>
                )}
              </div>

              {!loading && invoice && (
                <div className="flex justify-between items-center">
                  <span className="text-slate-500 font-medium">Invoice Number</span>
                  <span className="text-brand font-bold">{invoice.invoice_number}</span>
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex flex-col sm:flex-row gap-4 mt-2">
              <button
                onClick={handleDownload}
                disabled={loading || !invoice}
                className="flex-1 flex items-center justify-center gap-2 bg-brand hover:bg-brand-dark text-white py-3.5 rounded-xl font-bold shadow-md hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Download className="w-5 h-5" />
                Download Invoice
              </button>
              <button
                onClick={handleView}
                disabled={loading || !invoice}
                className="flex-1 flex items-center justify-center gap-2 bg-white border-2 border-slate-200 hover:border-brand text-slate-700 hover:text-brand py-3.5 rounded-xl font-bold shadow-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <FileText className="w-5 h-5" />
                View Invoice
              </button>
            </div>
            
            <p className="text-center text-sm text-slate-500 mt-2">
              A confirmation email with the invoice has been sent to your email address.
            </p>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};

export default SuccessModal;
