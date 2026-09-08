import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Leaf, Lock, Mail, User, Phone, CheckCircle, AlertCircle, ChevronRight, ChevronLeft, Eye, EyeOff, Check, X } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import api from '../api/axios';

const Signup = () => {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    full_name: '',
    username: '',
    email: '',
    phone_number: '',
    password: '',
    confirm_password: '',
    role: 'user'
  });
  
  const [otps, setOtps] = useState({
    email: '',
    phone: ''
  });

  const [touched, setTouched] = useState({});
  const [fieldErrors, setFieldErrors] = useState({});
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [status, setStatus] = useState({
    isUsernameAvailable: null,
    isCheckingUsername: false,
    isEmailVerified: false,
    isPhoneVerified: false,
    emailOtpSent: false,
    phoneOtpSent: false,
    emailResends: 0,
    phoneResends: 0
  });

  const [timers, setTimers] = useState({
    email: 0,
    phone: 0
  });

  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { register, login } = useAuth();
  const navigate = useNavigate();

  // Timer effects
  useEffect(() => {
    let emailInterval;
    if (timers.email > 0) {
      emailInterval = setInterval(() => {
        setTimers(prev => ({ ...prev, email: prev.email - 1 }));
      }, 1000);
    }
    return () => clearInterval(emailInterval);
  }, [timers.email]);

  useEffect(() => {
    let phoneInterval;
    if (timers.phone > 0) {
      phoneInterval = setInterval(() => {
        setTimers(prev => ({ ...prev, phone: prev.phone - 1 }));
      }, 1000);
    }
    return () => clearInterval(phoneInterval);
  }, [timers.phone]);

  // Validation functions
  const validateFullName = (name) => {
    const trimmed = (name || '').trim();
    if (!trimmed) return 'Full name is required.';
    if (trimmed.length < 3) return 'Full name must be at least 3 characters.';
    if (trimmed.length > 100) return 'Full name cannot exceed 100 characters.';
    if (!/^[a-zA-Z\s.'-]+$/.test(trimmed)) return 'Full name can only contain letters, spaces, hyphens, and dots.';
    return '';
  };

  const validateUsername = (uname) => {
    const trimmed = (uname || '').trim();
    if (!trimmed) return 'Username is required.';
    if (trimmed.length < 4) return 'Username must be at least 4 characters.';
    if (trimmed.length > 30) return 'Username cannot exceed 30 characters.';
    if (!/^[a-zA-Z0-9_]+$/.test(trimmed)) return 'Username can only contain letters, numbers, and underscores.';
    return '';
  };

  const validateEmail = (mail) => {
    const trimmed = (mail || '').trim();
    if (!trimmed) return 'Email address is required.';
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    if (!emailRegex.test(trimmed)) return 'Please enter a valid email address (e.g. name@example.com).';
    return '';
  };

  const validatePhone = (phone) => {
    const trimmed = (phone || '').trim();
    if (!trimmed) return 'Phone number is required.';
    if (!/^\d+$/.test(trimmed)) return 'Phone number must contain numbers only.';
    if (trimmed.length !== 10) return 'Phone number must be exactly 10 digits.';
    if (!/^[6-9]\d{9}$/.test(trimmed)) return 'Enter a valid 10-digit Indian mobile number (starting with 6, 7, 8, or 9).';
    return '';
  };

  const validateOtp = (otpVal) => {
    const trimmed = (otpVal || '').trim();
    if (!trimmed) return 'OTP is required.';
    if (!/^\d{6}$/.test(trimmed)) return 'OTP must be a 6-digit number.';
    return '';
  };

  const validatePasswordRules = (pass) => {
    const p = pass || '';
    return {
      hasLength: p.length >= 8,
      hasUpper: /[A-Z]/.test(p),
      hasLower: /[a-z]/.test(p),
      hasNumber: /[0-9]/.test(p),
      hasSpecial: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]+/.test(p),
      isValid: p.length >= 8 && /[A-Z]/.test(p) && /[a-z]/.test(p) && /[0-9]/.test(p) && /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]+/.test(p)
    };
  };

  const validateConfirmPassword = (confirmPass, pass) => {
    if (!confirmPass) return 'Please confirm your password.';
    if (confirmPass !== pass) return 'Passwords do not match.';
    return '';
  };

  const handleBlur = (field) => {
    setTouched(prev => ({ ...prev, [field]: true }));
    let err = '';
    if (field === 'full_name') err = validateFullName(formData.full_name);
    else if (field === 'username') err = validateUsername(formData.username);
    else if (field === 'email') err = validateEmail(formData.email);
    else if (field === 'phone_number') err = validatePhone(formData.phone_number);
    else if (field === 'password') {
      const rules = validatePasswordRules(formData.password);
      if (!rules.isValid) err = 'Password does not satisfy all security criteria.';
    }
    else if (field === 'confirm_password') err = validateConfirmPassword(formData.confirm_password, formData.password);
    else if (field === 'email_otp') err = validateOtp(otps.email);
    else if (field === 'phone_otp') err = validateOtp(otps.phone);

    setFieldErrors(prev => ({ ...prev, [field]: err }));
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // Reset specific status if field changes
    if (name === 'username') {
      setStatus(prev => ({ ...prev, isUsernameAvailable: null }));
    }

    if (touched[name]) {
      let err = '';
      if (name === 'full_name') err = validateFullName(value);
      else if (name === 'username') err = validateUsername(value);
      else if (name === 'email') err = validateEmail(value);
      else if (name === 'phone_number') err = validatePhone(value);
      else if (name === 'password') {
        const rules = validatePasswordRules(value);
        if (!rules.isValid) err = 'Password does not satisfy all security criteria.';
        if (touched.confirm_password && formData.confirm_password) {
          setFieldErrors(prev => ({ ...prev, confirm_password: validateConfirmPassword(formData.confirm_password, value) }));
        }
      }
      else if (name === 'confirm_password') err = validateConfirmPassword(value, formData.password);

      setFieldErrors(prev => ({ ...prev, [name]: err }));
    }
  };

  const handleOtpChange = (e) => {
    const { name, value } = e.target;
    setOtps(prev => ({ ...prev, [name]: value }));
    const otpKey = `${name}_otp`;
    if (touched[otpKey]) {
      setFieldErrors(prev => ({ ...prev, [otpKey]: validateOtp(value) }));
    }
  };

  const checkUsername = async () => {
    const unameErr = validateUsername(formData.username);
    if (unameErr) {
      setFieldErrors(prev => ({ ...prev, username: unameErr }));
      return;
    }
    setStatus(prev => ({ ...prev, isCheckingUsername: true }));
    try {
      const res = await api.post('/auth/check-username', { username: formData.username.trim() });
      setStatus(prev => ({ ...prev, isUsernameAvailable: res.data.available, isCheckingUsername: false }));
      if (!res.data.available) {
        setFieldErrors(prev => ({ ...prev, username: 'This username is already taken.' }));
      } else {
        setFieldErrors(prev => ({ ...prev, username: '' }));
      }
    } catch (err) {
      setStatus(prev => ({ ...prev, isCheckingUsername: false }));
      console.error(err);
    }
  };

  const sendEmailOtp = async () => {
    setError('');
    const nameErr = validateFullName(formData.full_name);
    const unameErr = validateUsername(formData.username);
    const emailErr = validateEmail(formData.email);

    setTouched(prev => ({ ...prev, full_name: true, username: true, email: true }));
    setFieldErrors(prev => ({ ...prev, full_name: nameErr, username: unameErr, email: emailErr }));

    if (nameErr || unameErr || emailErr) {
      setError(nameErr || unameErr || emailErr);
      return;
    }

    if (status.isUsernameAvailable === false) {
      setError('Username is already taken. Please choose another username.');
      return;
    }
    if (status.emailResends >= 3) {
      setError('Maximum email resends reached. Please try again later.');
      return;
    }
    setLoading(true);
    try {
      await api.post('/auth/send-email-otp', {
        email: formData.email.trim(),
        full_name: formData.full_name.trim(),
        username: formData.username.trim()
      });
      setStatus(prev => ({ 
        ...prev, 
        emailOtpSent: true,
        emailResends: prev.emailOtpSent ? prev.emailResends + 1 : prev.emailResends
      }));
      setTimers(prev => ({ ...prev, email: 60 }));
      setSuccess('Verification OTP sent to your email.');
      setTimeout(() => setSuccess(''), 4000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send Email OTP.');
    } finally {
      setLoading(false);
    }
  };

  const verifyEmailOtp = async () => {
    setError('');
    const otpErr = validateOtp(otps.email);
    setTouched(prev => ({ ...prev, email_otp: true }));
    setFieldErrors(prev => ({ ...prev, email_otp: otpErr }));
    if (otpErr) {
      setError(otpErr);
      return;
    }

    setLoading(true);
    try {
      await api.post('/auth/verify-email-otp', {
        email: formData.email.trim(),
        otp: otps.email.trim()
      });
      setStatus(prev => ({ ...prev, isEmailVerified: true }));
      setSuccess('Email verified successfully.');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid or expired OTP.');
    } finally {
      setLoading(false);
    }
  };

  const sendPhoneOtp = async () => {
    setError('');
    const phoneErr = validatePhone(formData.phone_number);
    setTouched(prev => ({ ...prev, phone_number: true }));
    setFieldErrors(prev => ({ ...prev, phone_number: phoneErr }));
    if (phoneErr) {
      setError(phoneErr);
      return;
    }

    if (status.phoneResends >= 3) {
      setError('Maximum SMS resends reached. Please try again later.');
      return;
    }
    setLoading(true);
    try {
      const formattedPhone = `+91${formData.phone_number.trim()}`;
      await api.post('/auth/send-phone-otp', {
        phone_number: formattedPhone
      });
      setStatus(prev => ({ 
        ...prev, 
        phoneOtpSent: true,
        phoneResends: prev.phoneOtpSent ? prev.phoneResends + 1 : prev.phoneResends
      }));
      setTimers(prev => ({ ...prev, phone: 60 }));
      setSuccess('SMS OTP sent successfully.');
      setTimeout(() => setSuccess(''), 4000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send SMS OTP.');
    } finally {
      setLoading(false);
    }
  };

  const verifyPhoneOtp = async () => {
    setError('');
    const otpErr = validateOtp(otps.phone);
    setTouched(prev => ({ ...prev, phone_otp: true }));
    setFieldErrors(prev => ({ ...prev, phone_otp: otpErr }));
    if (otpErr) {
      setError(otpErr);
      return;
    }

    setLoading(true);
    try {
      const formattedPhone = `+91${formData.phone_number.trim()}`;
      await api.post('/auth/verify-phone-otp', {
        phone_number: formattedPhone,
        otp: otps.phone.trim()
      });
      setStatus(prev => ({ ...prev, isPhoneVerified: true }));
      setSuccess('Phone number verified successfully.');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid or expired OTP.');
    } finally {
      setLoading(false);
    }
  };

  const passRules = validatePasswordRules(formData.password);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    if (step === 1 && status.isEmailVerified) {
      setStep(2);
      return;
    }
    if (step === 2 && status.isPhoneVerified) {
      setStep(3);
      return;
    }
    if (step === 3) {
      const confirmErr = validateConfirmPassword(formData.confirm_password, formData.password);

      setTouched(prev => ({ ...prev, password: true, confirm_password: true }));
      setFieldErrors(prev => ({
        ...prev,
        password: !passRules.isValid ? 'Password must satisfy all security requirements.' : '',
        confirm_password: confirmErr
      }));

      if (!passRules.isValid) {
        setError('Please satisfy all password security requirements.');
        return;
      }
      if (confirmErr) {
        setError(confirmErr);
        return;
      }
      
      setLoading(true);
      try {
        const payload = {
          full_name: formData.full_name.trim(),
          username: formData.username.trim(),
          email: formData.email.trim(),
          password: formData.password,
          role: formData.role || 'user',
          phone_number: `+91${formData.phone_number.trim()}`
        };
        await register(payload);
        setSuccess('Account created successfully! Logging you in...');
        await login(formData.email.trim(), formData.password);
        navigate('/farmer/dashboard');
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to register. Please try again.');
      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="flex justify-center">
          <div className="w-16 h-16 bg-brand rounded-2xl flex items-center justify-center shadow-lg shadow-brand/20">
            <Leaf className="w-8 h-8 text-white" />
          </div>
        </div>
        <h2 className="mt-6 text-center text-3xl font-extrabold text-slate-900">
          Create an account
        </h2>
        <p className="mt-2 text-center text-sm text-slate-600">
          Step {step} of 3 • {step === 1 ? 'Personal Details & Email' : step === 2 ? 'Phone Verification' : 'Secure Password'}
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow-sm sm:rounded-xl sm:px-10 border border-slate-200 relative overflow-hidden">
          
          {/* Progress Bar */}
          <div className="absolute top-0 left-0 w-full h-1 bg-slate-100">
            <div 
              className="h-full bg-brand transition-all duration-500 ease-in-out" 
              style={{ width: `${(step / 3) * 100}%` }}
            ></div>
          </div>

          <form className="space-y-6 mt-4" onSubmit={handleSubmit}>
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg text-sm flex items-start">
                <AlertCircle className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}
            {success && (
              <div className="bg-green-50 border border-green-200 text-green-600 px-4 py-3 rounded-lg text-sm flex items-start">
                <CheckCircle className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />
                <span>{success}</span>
              </div>
            )}
            
            {/* STEP 1: Personal Info & Email */}
            {step === 1 && (
              <div className="space-y-4 animate-in fade-in slide-in-from-right-4 duration-300">
                {/* Full Name */}
                <div>
                  <label className="block text-sm font-medium text-slate-700">Full Name</label>
                  <div className="mt-1 relative rounded-md shadow-sm">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <User className="h-5 w-5 text-slate-400" />
                    </div>
                    <input
                      type="text"
                      name="full_name"
                      required
                      disabled={status.isEmailVerified}
                      onBlur={() => handleBlur('full_name')}
                      className={`block w-full pl-10 pr-10 sm:text-sm rounded-lg py-2.5 border transition-colors disabled:bg-slate-50 disabled:text-slate-500 ${
                        touched.full_name && fieldErrors.full_name
                          ? 'border-red-300 focus:border-red-500 focus:ring-red-500 bg-red-50/10'
                          : touched.full_name && !fieldErrors.full_name && formData.full_name
                          ? 'border-emerald-400 focus:border-emerald-500 focus:ring-emerald-500'
                          : 'border-slate-300 focus:ring-brand focus:border-brand'
                      }`}
                      placeholder="e.g. Ramesh Kumar"
                      value={formData.full_name}
                      onChange={handleChange}
                    />
                    {touched.full_name && !fieldErrors.full_name && formData.full_name && (
                      <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                        <CheckCircle className="h-4 w-4 text-emerald-500" />
                      </div>
                    )}
                  </div>
                  {touched.full_name && fieldErrors.full_name && (
                    <p className="mt-1.5 text-xs text-red-600 flex items-center gap-1">
                      <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                      <span>{fieldErrors.full_name}</span>
                    </p>
                  )}
                </div>

                {/* Username */}
                <div>
                  <label className="block text-sm font-medium text-slate-700">Username</label>
                  <div className="mt-1 relative rounded-md shadow-sm">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <User className="h-5 w-5 text-slate-400" />
                    </div>
                    <input
                      type="text"
                      name="username"
                      required
                      disabled={status.isEmailVerified}
                      onBlur={() => {
                        handleBlur('username');
                        if (formData.username.trim().length >= 4) {
                          checkUsername();
                        }
                      }}
                      className={`block w-full pl-10 pr-10 sm:text-sm rounded-lg py-2.5 border transition-colors disabled:bg-slate-50 disabled:text-slate-500 ${
                        touched.username && fieldErrors.username
                          ? 'border-red-300 focus:border-red-500 focus:ring-red-500 bg-red-50/10'
                          : status.isUsernameAvailable === true
                          ? 'border-emerald-400 focus:border-emerald-500 focus:ring-emerald-500'
                          : 'border-slate-300 focus:ring-brand focus:border-brand'
                      }`}
                      placeholder="e.g. ramesh_k"
                      value={formData.username}
                      onChange={handleChange}
                    />
                    <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                      {status.isCheckingUsername && (
                        <div className="animate-spin rounded-full h-4 w-4 border-2 border-brand border-t-transparent"></div>
                      )}
                      {!status.isCheckingUsername && status.isUsernameAvailable === true && (
                        <CheckCircle className="h-4 w-4 text-emerald-500" />
                      )}
                      {!status.isCheckingUsername && status.isUsernameAvailable === false && (
                        <AlertCircle className="h-4 w-4 text-red-500" />
                      )}
                    </div>
                  </div>
                  {touched.username && fieldErrors.username ? (
                    <p className="mt-1.5 text-xs text-red-600 flex items-center gap-1">
                      <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                      <span>{fieldErrors.username}</span>
                    </p>
                  ) : status.isUsernameAvailable === true ? (
                    <p className="mt-1.5 text-xs text-emerald-600 flex items-center gap-1">
                      <CheckCircle className="w-3.5 h-3.5 shrink-0" />
                      <span>Username is available!</span>
                    </p>
                  ) : (
                    <p className="mt-1 text-xs text-slate-500">
                      4-30 alphanumeric characters or underscores.
                    </p>
                  )}
                </div>

                {/* Email address */}
                <div>
                  <label className="block text-sm font-medium text-slate-700">Email Address</label>
                  <div className="mt-1 relative rounded-md shadow-sm">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <Mail className="h-5 w-5 text-slate-400" />
                    </div>
                    <input
                      type="email"
                      name="email"
                      required
                      disabled={status.isEmailVerified}
                      onBlur={() => handleBlur('email')}
                      className={`block w-full pl-10 pr-10 sm:text-sm rounded-lg py-2.5 border transition-colors disabled:bg-slate-50 disabled:text-slate-500 ${
                        touched.email && fieldErrors.email
                          ? 'border-red-300 focus:border-red-500 focus:ring-red-500 bg-red-50/10'
                          : status.isEmailVerified
                          ? 'border-emerald-400 bg-emerald-50/20'
                          : 'border-slate-300 focus:ring-brand focus:border-brand'
                      }`}
                      placeholder="e.g. ramesh@example.com"
                      value={formData.email}
                      onChange={handleChange}
                    />
                    {status.isEmailVerified && (
                      <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                        <CheckCircle className="h-4 w-4 text-emerald-500" />
                      </div>
                    )}
                  </div>
                  {touched.email && fieldErrors.email ? (
                    <p className="mt-1.5 text-xs text-red-600 flex items-center gap-1">
                      <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                      <span>{fieldErrors.email}</span>
                    </p>
                  ) : status.isEmailVerified ? (
                    <p className="mt-1.5 text-xs text-emerald-600 flex items-center gap-1">
                      <CheckCircle className="w-3.5 h-3.5 shrink-0" />
                      <span>Email address verified</span>
                    </p>
                  ) : null}
                </div>

                {!status.isEmailVerified && (
                  <div className="pt-2">
                    {!status.emailOtpSent ? (
                      <button
                        type="button"
                        onClick={sendEmailOtp}
                        disabled={loading || status.isUsernameAvailable === false}
                        className="w-full flex justify-center py-2.5 px-4 border border-brand text-brand hover:bg-brand hover:text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                      >
                        {loading ? 'Sending Verification Code...' : 'Send Email Verification Code'}
                      </button>
                    ) : (
                      <div className="space-y-3 p-4 bg-slate-50 rounded-lg border border-slate-200">
                        <label className="block text-sm font-medium text-slate-700">Enter 6-digit Email OTP</label>
                        <input
                          type="text"
                          name="email"
                          maxLength={6}
                          value={otps.email}
                          onBlur={() => handleBlur('email_otp')}
                          onChange={handleOtpChange}
                          className={`focus:ring-brand focus:border-brand block w-full sm:text-sm rounded-lg py-2.5 border text-center tracking-widest font-mono text-lg ${
                            touched.email_otp && fieldErrors.email_otp ? 'border-red-300 bg-red-50/20' : 'border-slate-300 bg-white'
                          }`}
                          placeholder="••••••"
                        />
                        {touched.email_otp && fieldErrors.email_otp && (
                          <p className="text-xs text-red-600 flex items-center gap-1">
                            <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                            <span>{fieldErrors.email_otp}</span>
                          </p>
                        )}
                        <div className="flex space-x-2">
                          <button
                            type="button"
                            onClick={verifyEmailOtp}
                            disabled={loading || otps.email.trim().length !== 6}
                            className="flex-1 py-2.5 bg-brand text-white rounded-lg text-sm font-medium hover:bg-brand-dark transition-colors disabled:opacity-50"
                          >
                            {loading ? 'Verifying...' : 'Verify Email'}
                          </button>
                          <button
                            type="button"
                            onClick={sendEmailOtp}
                            disabled={timers.email > 0 || loading || status.emailResends >= 3}
                            className="px-4 py-2.5 bg-white border border-slate-300 text-slate-700 rounded-lg text-sm font-medium hover:bg-slate-50 transition-colors disabled:opacity-50"
                          >
                            {timers.email > 0 ? `Resend (${timers.email}s)` : 'Resend'}
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                )}
                
                {status.isEmailVerified && (
                  <div className="pt-2 flex justify-end">
                    <button
                      type="submit"
                      className="w-full flex items-center justify-center gap-2 py-2.5 px-6 bg-brand text-white rounded-lg text-sm font-medium hover:bg-brand-dark transition-colors shadow-sm"
                    >
                      <span>Proceed to Phone Verification</span>
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* STEP 2: Phone Number */}
            {step === 2 && (
              <div className="space-y-4 animate-in fade-in slide-in-from-right-4 duration-300">
                <button 
                  type="button" 
                  onClick={() => setStep(1)}
                  className="flex items-center text-sm text-slate-500 hover:text-slate-800 mb-2"
                >
                  <ChevronLeft className="w-4 h-4 mr-1" /> Back to Personal Details
                </button>
                
                <div>
                  <label className="block text-sm font-medium text-slate-700">Mobile Phone Number</label>
                  <div className="mt-1 relative rounded-md shadow-sm flex">
                    <span className="inline-flex items-center px-3 rounded-l-md border border-r-0 border-slate-300 bg-slate-50 text-slate-600 font-medium sm:text-sm">
                      🇮🇳 +91
                    </span>
                    <input
                      type="tel"
                      name="phone_number"
                      required
                      disabled={status.isPhoneVerified}
                      maxLength={10}
                      onBlur={() => handleBlur('phone_number')}
                      className={`flex-1 block w-full rounded-none rounded-r-md sm:text-sm py-2.5 border pl-3 transition-colors disabled:bg-slate-50 disabled:text-slate-500 ${
                        touched.phone_number && fieldErrors.phone_number
                          ? 'border-red-300 focus:border-red-500 focus:ring-red-500 bg-red-50/10'
                          : status.isPhoneVerified
                          ? 'border-emerald-400 bg-emerald-50/20'
                          : 'border-slate-300 focus:ring-brand focus:border-brand'
                      }`}
                      placeholder="9876543210"
                      value={formData.phone_number}
                      onChange={handleChange}
                    />
                  </div>
                  {touched.phone_number && fieldErrors.phone_number ? (
                    <p className="mt-1.5 text-xs text-red-600 flex items-center gap-1">
                      <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                      <span>{fieldErrors.phone_number}</span>
                    </p>
                  ) : status.isPhoneVerified ? (
                    <p className="mt-1.5 text-xs text-emerald-600 flex items-center gap-1">
                      <CheckCircle className="w-3.5 h-3.5 shrink-0" />
                      <span>Phone number verified</span>
                    </p>
                  ) : (
                    <p className="mt-1 text-xs text-slate-500">Enter a 10-digit Indian mobile number for OTP authentication.</p>
                  )}
                </div>

                {!status.isPhoneVerified && (
                  <div className="pt-2">
                    {!status.phoneOtpSent ? (
                      <button
                        type="button"
                        onClick={sendPhoneOtp}
                        disabled={loading || formData.phone_number.trim().length !== 10}
                        className="w-full flex justify-center py-2.5 px-4 border border-brand text-brand hover:bg-brand hover:text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                      >
                        {loading ? 'Sending SMS Code...' : 'Send SMS Verification Code'}
                      </button>
                    ) : (
                      <div className="space-y-3 p-4 bg-slate-50 rounded-lg border border-slate-200">
                        <label className="block text-sm font-medium text-slate-700">Enter 6-digit SMS OTP</label>
                        <input
                          type="text"
                          name="phone"
                          maxLength={6}
                          value={otps.phone}
                          onBlur={() => handleBlur('phone_otp')}
                          onChange={handleOtpChange}
                          className={`focus:ring-brand focus:border-brand block w-full sm:text-sm rounded-lg py-2.5 border text-center tracking-widest font-mono text-lg ${
                            touched.phone_otp && fieldErrors.phone_otp ? 'border-red-300 bg-red-50/20' : 'border-slate-300 bg-white'
                          }`}
                          placeholder="••••••"
                        />
                        {touched.phone_otp && fieldErrors.phone_otp && (
                          <p className="text-xs text-red-600 flex items-center gap-1">
                            <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                            <span>{fieldErrors.phone_otp}</span>
                          </p>
                        )}
                        <div className="flex space-x-2">
                          <button
                            type="button"
                            onClick={verifyPhoneOtp}
                            disabled={loading || otps.phone.trim().length !== 6}
                            className="flex-1 py-2.5 bg-brand text-white rounded-lg text-sm font-medium hover:bg-brand-dark transition-colors disabled:opacity-50"
                          >
                            {loading ? 'Verifying...' : 'Verify Phone'}
                          </button>
                          <button
                            type="button"
                            onClick={sendPhoneOtp}
                            disabled={timers.phone > 0 || loading || status.phoneResends >= 3}
                            className="px-4 py-2.5 bg-white border border-slate-300 text-slate-700 rounded-lg text-sm font-medium hover:bg-slate-50 transition-colors disabled:opacity-50"
                          >
                            {timers.phone > 0 ? `Resend (${timers.phone}s)` : 'Resend'}
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {status.isPhoneVerified && (
                  <div className="pt-2 flex justify-end">
                    <button
                      type="submit"
                      className="w-full flex items-center justify-center gap-2 py-2.5 px-6 bg-brand text-white rounded-lg text-sm font-medium hover:bg-brand-dark transition-colors shadow-sm"
                    >
                      <span>Proceed to Set Password</span>
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* STEP 3: Password */}
            {step === 3 && (
              <div className="space-y-4 animate-in fade-in slide-in-from-right-4 duration-300">
                <button 
                  type="button" 
                  onClick={() => setStep(2)}
                  className="flex items-center text-sm text-slate-500 hover:text-slate-800 mb-2"
                >
                  <ChevronLeft className="w-4 h-4 mr-1" /> Back to Phone Verification
                </button>
                
                {/* Password Field */}
                <div>
                  <label className="block text-sm font-medium text-slate-700">Create Password</label>
                  <div className="mt-1 relative rounded-md shadow-sm">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <Lock className="h-5 w-5 text-slate-400" />
                    </div>
                    <input
                      type={showPassword ? 'text' : 'password'}
                      name="password"
                      required
                      autoFocus
                      onBlur={() => handleBlur('password')}
                      className={`block w-full pl-10 pr-10 sm:text-sm rounded-lg py-2.5 border transition-colors ${
                        touched.password && fieldErrors.password
                          ? 'border-red-300 focus:border-red-500 focus:ring-red-500 bg-red-50/10'
                          : passRules.isValid
                          ? 'border-emerald-400 focus:border-emerald-500 focus:ring-emerald-500'
                          : 'border-slate-300 focus:ring-brand focus:border-brand'
                      }`}
                      placeholder="••••••••"
                      value={formData.password}
                      onChange={handleChange}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600"
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                  
                  {/* Password Checklist Criteria */}
                  <div className="mt-2.5 p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs space-y-1.5">
                    <p className="font-semibold text-slate-700 mb-1">Password must meet the following:</p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                      <div className={`flex items-center gap-1.5 ${passRules.hasLength ? 'text-emerald-600 font-medium' : 'text-slate-500'}`}>
                        {passRules.hasLength ? <Check className="w-3.5 h-3.5 text-emerald-500 shrink-0" /> : <X className="w-3.5 h-3.5 text-slate-400 shrink-0" />}
                        <span>Min 8 characters</span>
                      </div>
                      <div className={`flex items-center gap-1.5 ${passRules.hasUpper ? 'text-emerald-600 font-medium' : 'text-slate-500'}`}>
                        {passRules.hasUpper ? <Check className="w-3.5 h-3.5 text-emerald-500 shrink-0" /> : <X className="w-3.5 h-3.5 text-slate-400 shrink-0" />}
                        <span>1 uppercase letter</span>
                      </div>
                      <div className={`flex items-center gap-1.5 ${passRules.hasLower ? 'text-emerald-600 font-medium' : 'text-slate-500'}`}>
                        {passRules.hasLower ? <Check className="w-3.5 h-3.5 text-emerald-500 shrink-0" /> : <X className="w-3.5 h-3.5 text-slate-400 shrink-0" />}
                        <span>1 lowercase letter</span>
                      </div>
                      <div className={`flex items-center gap-1.5 ${passRules.hasNumber ? 'text-emerald-600 font-medium' : 'text-slate-500'}`}>
                        {passRules.hasNumber ? <Check className="w-3.5 h-3.5 text-emerald-500 shrink-0" /> : <X className="w-3.5 h-3.5 text-slate-400 shrink-0" />}
                        <span>1 number</span>
                      </div>
                      <div className={`flex items-center gap-1.5 ${passRules.hasSpecial ? 'text-emerald-600 font-medium' : 'text-slate-500'}`}>
                        {passRules.hasSpecial ? <Check className="w-3.5 h-3.5 text-emerald-500 shrink-0" /> : <X className="w-3.5 h-3.5 text-slate-400 shrink-0" />}
                        <span>1 special symbol</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Confirm Password Field */}
                <div>
                  <label className="block text-sm font-medium text-slate-700">Confirm Password</label>
                  <div className="mt-1 relative rounded-md shadow-sm">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <Lock className="h-5 w-5 text-slate-400" />
                    </div>
                    <input
                      type={showConfirmPassword ? 'text' : 'password'}
                      name="confirm_password"
                      required
                      onBlur={() => handleBlur('confirm_password')}
                      className={`block w-full pl-10 pr-10 sm:text-sm rounded-lg py-2.5 border transition-colors ${
                        touched.confirm_password && fieldErrors.confirm_password
                          ? 'border-red-300 focus:border-red-500 focus:ring-red-500 bg-red-50/10'
                          : touched.confirm_password && !fieldErrors.confirm_password && formData.confirm_password
                          ? 'border-emerald-400 focus:border-emerald-500 focus:ring-emerald-500'
                          : 'border-slate-300 focus:ring-brand focus:border-brand'
                      }`}
                      placeholder="••••••••"
                      value={formData.confirm_password}
                      onChange={handleChange}
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600"
                    >
                      {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                  {touched.confirm_password && fieldErrors.confirm_password ? (
                    <p className="mt-1.5 text-xs text-red-600 flex items-center gap-1">
                      <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                      <span>{fieldErrors.confirm_password}</span>
                    </p>
                  ) : touched.confirm_password && !fieldErrors.confirm_password && formData.confirm_password ? (
                    <p className="mt-1.5 text-xs text-emerald-600 flex items-center gap-1">
                      <CheckCircle className="w-3.5 h-3.5 shrink-0" />
                      <span>Passwords match</span>
                    </p>
                  ) : null}
                </div>

                <div className="pt-4">
                  <button
                    type="submit"
                    disabled={loading || !passRules.isValid || formData.password !== formData.confirm_password}
                    className="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-brand hover:bg-brand-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand transition-colors disabled:opacity-50"
                  >
                    {loading ? 'Creating account...' : 'Create Account'}
                  </button>
                </div>
              </div>
            )}
          </form>
          
          <div className="mt-6 text-center text-sm text-slate-600">
            Already have an account?{' '}
            <Link to="/login" className="font-medium text-brand hover:text-brand-dark transition-colors">
              Sign in
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Signup;

