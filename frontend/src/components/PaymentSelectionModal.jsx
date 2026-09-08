import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, CreditCard, Banknote, CheckCircle2, ChevronLeft, ArrowRight } from 'lucide-react';

const PaymentSelectionModal = ({ isOpen, onClose, onBack, onSubmit, customerDetails }) => {
  const [selectedMethod, setSelectedMethod] = useState('');

  // Load from local storage
  useEffect(() => {
    if (isOpen) {
      const saved = localStorage.getItem('terravyn_payment_method');
      if (saved) {
        setSelectedMethod(saved);
      }
    }
  }, [isOpen]);

  // Save to local storage on change
  useEffect(() => {
    if (isOpen && selectedMethod) {
      localStorage.setItem('terravyn_payment_method', selectedMethod);
    }
  }, [selectedMethod, isOpen]);

  // Handle ESC
  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [isOpen, onClose]);

  const handleSubmit = () => {
    if (!selectedMethod) return;
    onSubmit({ paymentMethod: selectedMethod, customerDetails });
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-0 md:p-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm"
            onClick={onClose}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="bg-white/90 backdrop-blur-xl w-full h-full md:h-auto md:max-w-3xl md:rounded-[32px] shadow-2xl flex flex-col relative z-10 overflow-hidden border border-white/20"
            role="dialog"
            aria-modal="true"
            aria-labelledby="payment-modal-title"
          >
            {/* Header */}
            <div className="flex justify-between items-center p-6 md:px-8 border-b border-slate-100 bg-white/80 sticky top-0 z-20">
              <div>
                <h2 id="payment-modal-title" className="text-2xl font-bold text-slate-900">Choose Payment Method</h2>
                <p className="text-sm text-slate-500 mt-1">Select your preferred payment option to complete your order.</p>
              </div>
              <button
                onClick={onClose}
                className="p-2 hover:bg-slate-100 rounded-full transition-colors"
                aria-label="Close"
              >
                <X className="w-6 h-6 text-slate-500" />
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6 md:px-8 custom-scrollbar">
              <div className="grid md:grid-cols-2 gap-6">
                {/* Option 1: ONLINE */}
                <button
                  type="button"
                  onClick={() => setSelectedMethod('ONLINE')}
                  className={`text-left p-6 rounded-3xl border-2 transition-all duration-300 relative overflow-hidden group flex flex-col h-full ${
                    selectedMethod === 'ONLINE'
                      ? 'border-brand bg-brand/5 shadow-xl shadow-brand/10 scale-[1.02]'
                      : 'border-slate-200 bg-white hover:border-brand/40 hover:shadow-lg'
                  }`}
                >
                  {selectedMethod === 'ONLINE' && (
                    <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} className="absolute top-4 right-4 text-brand bg-white rounded-full">
                      <CheckCircle2 className="w-8 h-8 drop-shadow-sm" />
                    </motion.div>
                  )}
                  <div className={`w-16 h-16 rounded-2xl flex items-center justify-center mb-6 transition-colors shadow-sm ${
                    selectedMethod === 'ONLINE' ? 'bg-brand text-white shadow-brand/30' : 'bg-slate-50 text-slate-500 border border-slate-100 group-hover:bg-brand/10 group-hover:text-brand'
                  }`}>
                    <CreditCard className="w-8 h-8" />
                  </div>
                  <h3 className="text-2xl font-bold text-slate-900 mb-2">Pay Now</h3>
                  <p className="text-slate-600 mb-8 text-sm leading-relaxed">Pay securely online using Razorpay.</p>
                  
                  <ul className="space-y-3 mb-8 flex-1">
                    <li className="flex items-start gap-3 text-sm text-slate-700 font-medium">
                      <CheckCircle2 className="w-5 h-5 text-brand flex-shrink-0" /> Instant Confirmation
                    </li>
                    <li className="flex items-start gap-3 text-sm text-slate-700 font-medium">
                      <CheckCircle2 className="w-5 h-5 text-brand flex-shrink-0" /> Secure Payments
                    </li>
                    <li className="flex items-start gap-3 text-sm text-slate-700 font-medium">
                      <CheckCircle2 className="w-5 h-5 text-brand flex-shrink-0" /> Multiple Payment Methods
                    </li>
                  </ul>

                  <div className={`w-full py-4 rounded-xl font-bold flex items-center justify-center gap-2 transition-all mt-auto ${
                    selectedMethod === 'ONLINE' ? 'bg-brand text-white shadow-md' : 'bg-slate-50 text-slate-400 group-hover:bg-slate-100'
                  }`}>
                    Proceed to Pay
                    <ArrowRight className="w-5 h-5" />
                  </div>
                </button>

                {/* Option 2: COD */}
                <button
                  type="button"
                  onClick={() => setSelectedMethod('COD')}
                  className={`text-left p-6 rounded-3xl border-2 transition-all duration-300 relative overflow-hidden group flex flex-col h-full ${
                    selectedMethod === 'COD'
                      ? 'border-brand bg-brand/5 shadow-xl shadow-brand/10 scale-[1.02]'
                      : 'border-slate-200 bg-white hover:border-brand/40 hover:shadow-lg'
                  }`}
                >
                  {selectedMethod === 'COD' && (
                    <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} className="absolute top-4 right-4 text-brand bg-white rounded-full">
                      <CheckCircle2 className="w-8 h-8 drop-shadow-sm" />
                    </motion.div>
                  )}
                  <div className={`w-16 h-16 rounded-2xl flex items-center justify-center mb-6 transition-colors shadow-sm ${
                    selectedMethod === 'COD' ? 'bg-brand text-white shadow-brand/30' : 'bg-slate-50 text-slate-500 border border-slate-100 group-hover:bg-brand/10 group-hover:text-brand'
                  }`}>
                    <Banknote className="w-8 h-8" />
                  </div>
                  <h3 className="text-2xl font-bold text-slate-900 mb-2">Cash on Delivery</h3>
                  <p className="text-slate-600 mb-8 text-sm leading-relaxed">Pay when your TERRAVYN device is delivered.</p>
                  
                  <ul className="space-y-3 mb-8 flex-1">
                    <li className="flex items-start gap-3 text-sm text-slate-700 font-medium">
                      <CheckCircle2 className="w-5 h-5 text-brand flex-shrink-0" /> No Online Payment Required
                    </li>
                    <li className="flex items-start gap-3 text-sm text-slate-700 font-medium">
                      <CheckCircle2 className="w-5 h-5 text-brand flex-shrink-0" /> Pay at Delivery
                    </li>
                    <li className="flex items-start gap-3 text-sm text-slate-700 font-medium">
                      <CheckCircle2 className="w-5 h-5 text-brand flex-shrink-0" /> Easy Checkout
                    </li>
                  </ul>

                  <div className={`w-full py-4 rounded-xl font-bold flex items-center justify-center gap-2 transition-all mt-auto ${
                    selectedMethod === 'COD' ? 'bg-brand text-white shadow-md' : 'bg-slate-50 text-slate-400 group-hover:bg-slate-100'
                  }`}>
                    Place Order
                    <ArrowRight className="w-5 h-5" />
                  </div>
                </button>
              </div>
            </div>

            {/* Footer */}
            <div className="p-6 md:px-8 border-t border-slate-100 bg-white/80 sticky bottom-0 z-20 flex justify-between items-center">
              <button
                onClick={onBack}
                className="px-6 py-3.5 text-slate-600 hover:text-slate-900 font-bold flex items-center gap-2 transition-colors rounded-xl hover:bg-slate-100"
              >
                <ChevronLeft className="w-5 h-5" /> Back
              </button>
              <button
                onClick={handleSubmit}
                disabled={!selectedMethod}
                className="w-full md:w-auto px-10 py-3.5 bg-brand hover:bg-brand-dark text-white font-bold rounded-xl shadow-lg shadow-brand/20 transition-all hover:-translate-y-0.5 disabled:opacity-50 disabled:hover:translate-y-0 disabled:shadow-none text-lg"
              >
                {selectedMethod === 'ONLINE' ? 'Proceed to Pay' : selectedMethod === 'COD' ? 'Place Order' : 'Continue'}
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

export default PaymentSelectionModal;
