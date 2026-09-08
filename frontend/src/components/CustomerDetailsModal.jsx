import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { motion, AnimatePresence } from 'framer-motion';
import { X, CheckCircle2, Upload, FileText, File, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react';
import axios from 'axios';

const schema = z.object({
  name: z.string().min(3, { message: 'Name must be at least 3 characters' }),
  phone: z.string().regex(/^[6-9]\d{9}$/, { message: 'Enter a valid 10-digit Indian mobile number' }),
  email: z.string().email({ message: 'Enter a valid email address' }),
  address: z.string().min(1, { message: 'House / Flat is required' }),
  street: z.string().min(1, { message: 'Street / Area is required' }),
  city: z.string().min(1, { message: 'Village / City is required' }),
  district: z.string().min(1, { message: 'District is required' }),
  state: z.string().min(1, { message: 'State is required' }),
  pincode: z.string().regex(/^\d{6}$/, { message: 'PIN code must be exactly 6 digits' }),
  landmark: z.string().optional(),
  aadhaar_number: z.string().regex(/^\d{12}$/, { message: 'Aadhaar must be exactly 12 digits' }),
  aadhaar_document_path: z.string().min(1, { message: 'Please upload your Aadhaar document' }),
  consent_accepted: z.boolean().refine(val => val === true, { message: 'You must provide consent' })
});

const InputField = ({ label, name, register, error, isValid, ...rest }) => (
  <div className="flex flex-col gap-1">
    <label className="text-sm font-medium text-slate-700">{label}</label>
    <div className="relative">
      <input
        {...register(name)}
        {...rest}
        className={`w-full px-4 py-2.5 rounded-xl border ${
          error ? 'border-red-500 focus:ring-red-500' : 
          isValid ? 'border-green-500 focus:ring-green-500' : 
          'border-slate-200 focus:ring-brand'
        } focus:outline-none focus:ring-2 focus:border-transparent transition-all bg-slate-50`}
      />
      {isValid && !error && (
        <CheckCircle2 className="w-5 h-5 text-green-500 absolute right-3 top-1/2 -translate-y-1/2" />
      )}
    </div>
    {error && <span className="text-xs text-red-500 mt-1">{error.message}</span>}
  </div>
);

const CustomerDetailsModal = ({ isOpen, onClose, onSubmit }) => {
  const {
    register,
    handleSubmit,
    formState: { errors, isValid, touchedFields },
    reset,
    watch,
    setValue,
    trigger
  } = useForm({
    resolver: zodResolver(schema),
    mode: 'onChange',
    defaultValues: {
      name: '',
      phone: '',
      email: '',
      address: '',
      street: '',
      city: '',
      district: '',
      state: '',
      pincode: '',
      landmark: '',
      aadhaar_number: '',
      aadhaar_document_path: '',
      consent_accepted: false
    }
  });

  const [step, setStep] = useState(1);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [accordionOpen, setAccordionOpen] = useState(false);
  const [passwordAccordionOpen, setPasswordAccordionOpen] = useState(false);
  const [passwordPromptOpen, setPasswordPromptOpen] = useState(false);
  const [pdfPassword, setPdfPassword] = useState('');
  const [pendingFile, setPendingFile] = useState(null);

  // Format Aadhaar Number nicely (XXXX XXXX XXXX)
  const formatAadhaar = (val) => {
    const numbers = val.replace(/\D/g, '');
    const matches = numbers.match(/(\d{1,4})/g);
    return matches ? matches.join(' ') : '';
  };

  // Load from local storage
  useEffect(() => {
    if (isOpen) {
      setStep(1);
      setUploading(false);
      setUploadProgress(0);
      setUploadedFile(null);
      setAccordionOpen(false);
      setPasswordAccordionOpen(false);
      setPasswordPromptOpen(false);
      setPdfPassword('');
      setPendingFile(null);

      const saved = localStorage.getItem('terravyn_checkout_customer');
      if (saved) {
        try {
          const parsed = JSON.parse(saved);
          reset(parsed);
        } catch (e) {
          console.error(e);
        }
      }
    }
  }, [isOpen, reset]);

  // Save to local storage on change
  const currentValues = watch();
  useEffect(() => {
    if (isOpen) {
      localStorage.setItem('terravyn_checkout_customer', JSON.stringify(currentValues));
    }
  }, [currentValues, isOpen]);

  // Handle ESC
  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [isOpen, onClose]);

  const handleFormSubmit = (data) => {
    if (step !== 2) return;
    onSubmit(data);
  };

  const handleKeyDown = (e) => {
    // If pressing Enter inside an input field
    if (e.key === 'Enter' && e.target.tagName !== 'TEXTAREA' && e.target.tagName !== 'BUTTON') {
      e.preventDefault();
      if (step === 1) {
        handleNextStep();
      } else if (step === 2) {
        // Just trigger standard form submit
        handleSubmit(handleFormSubmit)();
      }
    }
  };

  const handleNextStep = async () => {
    const isStep1Valid = await trigger(['name', 'phone', 'email', 'address', 'street', 'city', 'district', 'state', 'pincode']);
    if (isStep1Valid) {
      setStep(2);
    } else {
      setTimeout(() => {
        const firstErrorElement = document.querySelector('.border-red-500');
        if (firstErrorElement) {
          firstErrorElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }, 50);
    }
  };

  const submitFile = async (file, password = null) => {
    setUploading(true);
    setUploadProgress(0);
    const formData = new FormData();
    formData.append('file', file);
    if (password) {
      formData.append('password', password);
    }

    try {
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'https://terravyn-backend.onrender.com';
      const res = await axios.post(`${baseUrl}/api/uploads/identity-document`, formData, {
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(percentCompleted);
        }
      });
      
      const { document_path } = res.data;
      reset({ ...currentValues, aadhaar_document_path: document_path });
      setUploadedFile(file.name);
      setPasswordPromptOpen(false);
      setPendingFile(null);
      setPdfPassword('');
    } catch (err) {
      if (err.response?.status === 423 || err.response?.data?.detail === "ENCRYPTED_PDF") {
        setPendingFile(file);
        setPasswordPromptOpen(true);
        return;
      }
      console.error("Upload error details:", err.response?.data || err.message || err);
      const backendMessage = err.response?.data?.detail || "Unable to save document.";
      alert(backendMessage);
    } finally {
      setUploading(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (file.size > 10 * 1024 * 1024) {
      alert("File size exceeds 10 MB limit.");
      return;
    }
    
    const allowed = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png'];
    if (!allowed.includes(file.type)) {
      alert("Unsupported file type. Please upload a PDF, JPG, or PNG.");
      return;
    }

    await submitFile(file);
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
            className="bg-white w-full h-full md:h-auto md:max-w-2xl md:max-h-[90vh] md:rounded-[32px] shadow-2xl flex flex-col relative z-10 overflow-hidden"
            role="dialog"
            aria-modal="true"
            aria-labelledby="modal-title"
          >
            {/* Header */}
            <div className="flex justify-between items-center p-6 md:px-8 border-b border-slate-100 bg-white sticky top-0 z-20">
              <div>
                <h2 id="modal-title" className="text-2xl font-bold text-slate-900">Complete Your Order</h2>
                <p className="text-sm text-slate-500 mt-1">Please provide your details to continue.</p>
              </div>
              <button
                onClick={onClose}
                className="p-2 hover:bg-slate-100 rounded-full transition-colors"
                aria-label="Close"
              >
                <X className="w-6 h-6 text-slate-500" />
              </button>
            </div>

            {/* Form */}
            <div className="flex-1 overflow-y-auto p-6 md:px-8 custom-scrollbar">
              <form id="customer-details-form" onSubmit={handleSubmit(handleFormSubmit)} onKeyDown={handleKeyDown} className="space-y-6">
                
                {step === 1 && (
                  <>
                    <div className="space-y-4">
                      <h3 className="text-lg font-bold text-slate-800 pb-2 border-b border-slate-100">Personal Information</h3>
                      <div className="grid md:grid-cols-2 gap-4">
                        <InputField label="Full Name *" name="name" register={register} error={errors.name} isValid={touchedFields.name && !errors.name} placeholder="John Doe" />
                        <InputField label="Phone Number *" name="phone" register={register} error={errors.phone} isValid={touchedFields.phone && !errors.phone} placeholder="9876543210" />
                      </div>
                      <InputField label="Email Address *" name="email" register={register} error={errors.email} isValid={touchedFields.email && !errors.email} placeholder="john@example.com" type="email" />
                    </div>

                    <div className="space-y-4">
                      <h3 className="text-lg font-bold text-slate-800 pb-2 border-b border-slate-100 mt-6">Shipping Address</h3>
                      <InputField label="House / Flat Number *" name="address" register={register} error={errors.address} isValid={touchedFields.address && !errors.address} placeholder="Flat 101, building name" />
                      <InputField label="Street / Area *" name="street" register={register} error={errors.street} isValid={touchedFields.street && !errors.street} placeholder="Main Street" />
                      
                      <div className="grid md:grid-cols-2 gap-4">
                        <InputField label="Village / City *" name="city" register={register} error={errors.city} isValid={touchedFields.city && !errors.city} placeholder="City Name" />
                        <InputField label="District *" name="district" register={register} error={errors.district} isValid={touchedFields.district && !errors.district} placeholder="District Name" />
                      </div>
                      
                      <div className="grid md:grid-cols-2 gap-4">
                        <InputField label="State *" name="state" register={register} error={errors.state} isValid={touchedFields.state && !errors.state} placeholder="State Name" />
                        <InputField label="PIN Code *" name="pincode" register={register} error={errors.pincode} isValid={touchedFields.pincode && !errors.pincode} placeholder="123456" />
                      </div>

                      <InputField label="Landmark (Optional)" name="landmark" register={register} error={errors.landmark} isValid={touchedFields.landmark && !errors.landmark} placeholder="Near hospital" />
                    </div>
                  </>
                )}

                {step === 2 && (
                  <div className="space-y-6 animate-fade-in">
                    <h3 className="text-lg font-bold text-slate-800 pb-2 border-b border-slate-100">Identity Verification</h3>
                    
                    <div className="space-y-1">
                      <label className="text-sm font-medium text-slate-700">Aadhaar Number *</label>
                      <input
                        type="text"
                        placeholder="XXXX XXXX XXXX"
                        maxLength="14"
                        value={formatAadhaar(currentValues.aadhaar_number || '')}
                        onChange={(e) => setValue('aadhaar_number', e.target.value.replace(/\s/g, ''), { shouldValidate: true, shouldTouch: true })}
                        className={`w-full px-4 py-2.5 rounded-xl border ${
                          errors.aadhaar_number ? 'border-red-500 focus:ring-red-500' : 'border-slate-200 focus:ring-brand'
                        } focus:outline-none focus:ring-2 focus:border-transparent transition-all bg-slate-50 tracking-widest text-lg font-mono`}
                      />
                      {errors.aadhaar_number && <span className="text-xs text-red-500">{errors.aadhaar_number.message}</span>}
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-medium text-slate-700">Upload Aadhaar Card *</label>
                      <p className="text-xs text-slate-500">Allowed: PDF, JPG, PNG (Max 10MB)</p>
                      
                      <label className="relative flex flex-col items-center justify-center w-full h-32 border-2 border-slate-300 border-dashed rounded-xl cursor-pointer bg-slate-50 hover:bg-slate-100 transition-colors">
                        <div className="flex flex-col items-center justify-center pt-5 pb-6">
                          {uploading ? (
                            <div className="flex flex-col items-center">
                              <div className="w-8 h-8 border-4 border-brand border-t-transparent rounded-full animate-spin mb-2"></div>
                              <p className="text-sm text-brand font-bold">{uploadProgress}% Uploaded</p>
                            </div>
                          ) : uploadedFile ? (
                            <div className="flex flex-col items-center text-green-600">
                              <FileText className="w-8 h-8 mb-2" />
                              <p className="text-sm font-bold">{uploadedFile}</p>
                              <p className="text-xs text-slate-500 mt-1">Click to replace</p>
                            </div>
                          ) : (
                            <>
                              <Upload className="w-8 h-8 mb-2 text-slate-400" />
                              <p className="mb-2 text-sm text-slate-500 font-semibold">Click to upload document</p>
                            </>
                          )}
                        </div>
                        <input type="file" className="hidden" accept=".pdf,.jpg,.jpeg,.png" onChange={handleFileUpload} disabled={uploading} />
                      </label>
                      {errors.aadhaar_document_path && <span className="text-xs text-red-500">{errors.aadhaar_document_path.message}</span>}
                    </div>

                    <div className="space-y-2">
                      <div className="border border-slate-200 rounded-xl overflow-hidden bg-white">
                        <button 
                          type="button" 
                          onClick={() => setAccordionOpen(!accordionOpen)} 
                          className="w-full flex items-center justify-between p-4 bg-slate-50 hover:bg-slate-100 transition-colors"
                        >
                          <span className="font-semibold text-slate-700 text-sm flex items-center gap-2">
                            <AlertCircle className="w-4 h-4 text-brand" />
                            Why do we ask for your Aadhaar card?
                          </span>
                          {accordionOpen ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
                        </button>
                        <AnimatePresence>
                          {accordionOpen && (
                            <motion.div initial={{ height: 0 }} animate={{ height: 'auto' }} exit={{ height: 0 }} className="overflow-hidden">
                              <div className="p-4 text-sm text-slate-600 bg-white border-t border-slate-100 leading-relaxed">
                                We require identity verification documents to facilitate the SIM card registration process associated with your TERRAVYN device. The SIM card enables connectivity features used by the device. Your information will be handled securely and used only for the purposes permitted under applicable laws and regulations.
                              </div>
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </div>

                      <div className="border border-slate-200 rounded-xl overflow-hidden bg-white">
                        <button 
                          type="button" 
                          onClick={() => setPasswordAccordionOpen(!passwordAccordionOpen)} 
                          className="w-full flex items-center justify-between p-4 bg-slate-50 hover:bg-slate-100 transition-colors"
                        >
                          <span className="font-semibold text-slate-700 text-sm flex items-center gap-2">
                            <AlertCircle className="w-4 h-4 text-brand" />
                            Why am I being asked for my Aadhaar PDF password?
                          </span>
                          {passwordAccordionOpen ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
                        </button>
                        <AnimatePresence>
                          {passwordAccordionOpen && (
                            <motion.div initial={{ height: 0 }} animate={{ height: 'auto' }} exit={{ height: 0 }} className="overflow-hidden">
                              <div className="p-4 text-sm text-slate-600 bg-white border-t border-slate-100 leading-relaxed">
                                Some Aadhaar PDFs downloaded from UIDAI are protected with a password. To enable our verification team to securely review your submitted document, we may ask for this password. The password is used only during document processing and is not stored permanently.
                              </div>
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </div>
                    </div>

                    <div className="flex items-start gap-3 mt-4 bg-slate-50 p-4 rounded-xl border border-slate-100">
                      <input 
                        type="checkbox" 
                        id="consent" 
                        {...register('consent_accepted')}
                        className="mt-1 w-4 h-4 rounded border-slate-300 text-brand focus:ring-brand"
                      />
                      <label htmlFor="consent" className="text-xs text-slate-600 leading-relaxed">
                        I confirm that the information and documents provided are accurate, and I consent to their use for the device connectivity verification process in accordance with applicable laws and TERRAVYN's <a href="/privacy" className="text-brand hover:underline">Privacy Policy</a>.
                      </label>
                    </div>
                    {errors.consent_accepted && <span className="text-xs text-red-500 ml-7">{errors.consent_accepted.message}</span>}
                  </div>
                )}
              </form>
            </div>

            {/* Footer */}
            <div className="p-6 md:px-8 border-t border-slate-100 bg-slate-50 sticky bottom-0 z-20 flex justify-between items-center">
              {step === 2 ? (
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  className="px-6 py-3.5 text-slate-600 font-bold rounded-xl hover:bg-slate-200 transition-colors"
                >
                  Back
                </button>
              ) : (
                <div />
              )}

              {step === 1 ? (
                <button
                  key="btn-continue"
                  type="button"
                  onClick={handleNextStep}
                  className="w-full md:w-auto px-8 py-3.5 bg-brand hover:bg-brand-dark text-white font-bold rounded-xl shadow-lg shadow-brand/20 transition-all hover:-translate-y-0.5"
                >
                  Continue to Verification
                </button>
              ) : (
                <button
                  key="btn-submit"
                  type="submit"
                  form="customer-details-form"
                  disabled={!isValid || !currentValues.aadhaar_document_path || !currentValues.consent_accepted || uploading}
                  className="w-full md:w-auto px-8 py-3.5 bg-brand hover:bg-brand-dark text-white font-bold rounded-xl shadow-lg shadow-brand/20 transition-all hover:-translate-y-0.5 disabled:opacity-50 disabled:hover:translate-y-0 disabled:shadow-none flex items-center gap-2 justify-center"
                >
                  Proceed to Payment
                </button>
              )}
            </div>
          </motion.div>
        </div>
      )}
      
      {/* Password Prompt Modal */}
      {passwordPromptOpen && (
        <div className="fixed inset-0 z-[110] flex items-center justify-center p-4">
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
            className="bg-white w-full max-w-md rounded-2xl shadow-2xl relative z-10 p-6"
          >
            <h3 className="text-xl font-bold text-slate-900 mb-2">Password-Protected Aadhaar PDF Detected</h3>
            <p className="text-sm text-slate-600 mb-6">
              Your Aadhaar PDF is protected with a password. Please enter the PDF password so that we can securely process your document for identity verification.
            </p>
            
            <div className="space-y-4">
              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-slate-700">PDF Password</label>
                <input
                  type="password"
                  value={pdfPassword}
                  onChange={(e) => setPdfPassword(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:ring-brand focus:border-brand bg-slate-50"
                  placeholder="Enter password..."
                />
              </div>
              
              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setPasswordPromptOpen(false);
                    setPendingFile(null);
                    setPdfPassword('');
                  }}
                  className="px-4 py-2 text-slate-600 font-medium hover:bg-slate-100 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => submitFile(pendingFile, pdfPassword)}
                  disabled={uploading || !pdfPassword}
                  className="px-6 py-2 bg-brand hover:bg-brand-dark text-white font-bold rounded-lg transition-colors disabled:opacity-50"
                >
                  {uploading ? 'Verifying...' : 'Verify and Continue'}
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

export default CustomerDetailsModal;
