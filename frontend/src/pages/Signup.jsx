import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Leaf, Lock, Mail, User, Phone, CheckCircle, AlertCircle, ChevronRight, ChevronLeft } from 'lucide-react';
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

  const [status, setStatus] = useState({
    isUsernameAvailable: null,
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

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    // Reset specific status if field changes
    if (e.target.name === 'username') {
      setStatus(prev => ({ ...prev, isUsernameAvailable: null }));
    }
  };

  const handleOtpChange = (e) => {
    setOtps({ ...otps, [e.target.name]: e.target.value });
  };

  const checkUsername = async () => {
    if (formData.username.length < 4) return;
    try {
      const res = await api.post('/auth/check-username', { username: formData.username });
      setStatus(prev => ({ ...prev, isUsernameAvailable: res.data.available }));
    } catch (err) {
      console.error(err);
    }
  };

  const sendEmailOtp = async () => {
    setError('');
    if (!formData.email || !formData.full_name || !formData.username) {
      setError('Please fill in all details first.');
      return;
    }
    if (status.isUsernameAvailable === false) {
      setError('Username is already taken.');
      return;
    }
    if (status.emailResends >= 3) {
      setError('Maximum email resends reached. Please try again later.');
      return;
    }
    setLoading(true);
    try {
      const response = await api.post('/auth/send-email-otp', {
        email: formData.email,
        full_name: formData.full_name,
        username: formData.username
      });
      setStatus(prev => ({ 
        ...prev, 
        emailOtpSent: true,
        emailResends: prev.emailOtpSent ? prev.emailResends + 1 : prev.emailResends
      }));
      setTimers(prev => ({ ...prev, email: 60 }));
      setSuccess('Email OTP sent successfully.');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send Email OTP.');
    } finally {
      setLoading(false);
    }
  };

  const verifyEmailOtp = async () => {
    setError('');
    setLoading(true);
    try {
      await api.post('/auth/verify-email-otp', {
        email: formData.email,
        otp: otps.email
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
    if (!formData.phone_number || formData.phone_number.length !== 10) {
      setError('Please enter a valid 10-digit Indian mobile number.');
      return;
    }
    if (status.phoneResends >= 3) {
      setError('Maximum SMS resends reached. Please try again later.');
      return;
    }
    setLoading(true);
    try {
      const formattedPhone = `+91${formData.phone_number}`;
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
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send SMS OTP.');
    } finally {
      setLoading(false);
    }
  };

  const verifyPhoneOtp = async () => {
    setError('');
    setLoading(true);
    try {
      const formattedPhone = `+91${formData.phone_number}`;
      await api.post('/auth/verify-phone-otp', {
        phone_number: formattedPhone,
        otp: otps.phone
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

  const validatePassword = () => {
    const p = formData.password;
    if (p.length < 8) return "Password must be at least 8 characters long.";
    if (!/[A-Z]/.test(p)) return "Password must contain an uppercase letter.";
    if (!/[a-z]/.test(p)) return "Password must contain a lowercase letter.";
    if (!/[0-9]/.test(p)) return "Password must contain a number.";
    if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]+/.test(p)) return "Password must contain a special character.";
    if (p !== formData.confirm_password) return "Passwords do not match.";
    return null;
  };

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
      const passErr = validatePassword();
      if (passErr) {
        setError(passErr);
        return;
      }
      
      setLoading(true);
      try {
        const payload = {
          ...formData,
          phone_number: `+91${formData.phone_number}`
        };
        await register(payload);
        setSuccess('Account created successfully.');
        await login(formData.email, formData.password);
        navigate('/customer/dashboard');
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to register. Please try again.');
      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
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
          Step {step} of 3
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
                      minLength={3}
                      maxLength={100}
                      className="focus:ring-brand focus:border-brand block w-full pl-10 sm:text-sm border-slate-300 rounded-lg py-2 border disabled:bg-slate-50 disabled:text-slate-500"
                      placeholder="John Doe"
                      value={formData.full_name}
                      onChange={handleChange}
                    />
                  </div>
                </div>

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
                      pattern="[a-zA-Z0-9_]+"
                      minLength={4}
                      maxLength={30}
                      onBlur={checkUsername}
                      className="focus:ring-brand focus:border-brand block w-full pl-10 pr-10 sm:text-sm border-slate-300 rounded-lg py-2 border disabled:bg-slate-50 disabled:text-slate-500"
                      placeholder="johndoe123"
                      value={formData.username}
                      onChange={handleChange}
                    />
                    <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                      {status.isUsernameAvailable === true && <CheckCircle className="h-4 w-4 text-green-500" />}
                      {status.isUsernameAvailable === false && <AlertCircle className="h-4 w-4 text-red-500" />}
                    </div>
                  </div>
                  {status.isUsernameAvailable === false && (
                    <p className="mt-1 text-xs text-red-500">Username already taken.</p>
                  )}
                  {status.isUsernameAvailable === true && (
                    <p className="mt-1 text-xs text-green-500">Username available.</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700">Email address</label>
                  <div className="mt-1 relative rounded-md shadow-sm">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <Mail className="h-5 w-5 text-slate-400" />
                    </div>
                    <input
                      type="email"
                      name="email"
                      required
                      disabled={status.isEmailVerified}
                      className="focus:ring-brand focus:border-brand block w-full pl-10 sm:text-sm border-slate-300 rounded-lg py-2 border disabled:bg-slate-50 disabled:text-slate-500"
                      placeholder="john@example.com"
                      value={formData.email}
                      onChange={handleChange}
                    />
                  </div>
                </div>

                {!status.isEmailVerified && (
                  <div className="pt-2">
                    {!status.emailOtpSent ? (
                      <button
                        type="button"
                        onClick={sendEmailOtp}
                        disabled={loading || status.isUsernameAvailable === false}
                        className="w-full flex justify-center py-2 px-4 border border-brand text-brand hover:bg-brand hover:text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                      >
                        {loading ? 'Sending...' : 'Send Email OTP'}
                      </button>
                    ) : (
                      <div className="space-y-3 p-4 bg-slate-50 rounded-lg border border-slate-200">
                        <label className="block text-sm font-medium text-slate-700">Enter 6-digit OTP</label>
                        <input
                          type="text"
                          name="email"
                          maxLength={6}
                          value={otps.email}
                          onChange={handleOtpChange}
                          className="focus:ring-brand focus:border-brand block w-full sm:text-sm border-slate-300 rounded-lg py-2 border text-center tracking-widest font-mono"
                          placeholder="------"
                        />
                        <div className="flex space-x-2">
                          <button
                            type="button"
                            onClick={verifyEmailOtp}
                            disabled={loading || otps.email.length !== 6}
                            className="flex-1 py-2 bg-brand text-white rounded-lg text-sm font-medium hover:bg-brand-dark transition-colors disabled:opacity-50"
                          >
                            Verify Email
                          </button>
                          <button
                            type="button"
                            onClick={sendEmailOtp}
                            disabled={timers.email > 0 || loading || status.emailResends >= 3}
                            className="px-4 py-2 bg-white border border-slate-300 text-slate-700 rounded-lg text-sm font-medium hover:bg-slate-50 transition-colors disabled:opacity-50"
                          >
                            {timers.email > 0 ? `Resend in ${timers.email}s` : 'Resend'}
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
                      className="flex items-center py-2 px-6 bg-brand text-white rounded-lg text-sm font-medium hover:bg-brand-dark transition-colors"
                    >
                      Next <ChevronRight className="ml-1 w-4 h-4" />
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
                  className="flex items-center text-sm text-slate-500 hover:text-slate-800 mb-4"
                >
                  <ChevronLeft className="w-4 h-4 mr-1" /> Back
                </button>
                
                <div>
                  <label className="block text-sm font-medium text-slate-700">Phone Number</label>
                  <div className="mt-1 relative rounded-md shadow-sm flex">
                    <span className="inline-flex items-center px-3 rounded-l-md border border-r-0 border-slate-300 bg-slate-50 text-slate-500 sm:text-sm">
                      +91
                    </span>
                    <input
                      type="tel"
                      name="phone_number"
                      required
                      disabled={status.isPhoneVerified}
                      pattern="[0-9]{10}"
                      maxLength={10}
                      className="focus:ring-brand focus:border-brand flex-1 block w-full rounded-none rounded-r-md sm:text-sm border-slate-300 py-2 border pl-3 disabled:bg-slate-50 disabled:text-slate-500"
                      placeholder="9876543210"
                      value={formData.phone_number}
                      onChange={handleChange}
                    />
                  </div>
                  <p className="mt-1 text-xs text-slate-500">Indian mobile numbers only.</p>
                </div>

                {!status.isPhoneVerified && (
                  <div className="pt-2">
                    {!status.phoneOtpSent ? (
                      <button
                        type="button"
                        onClick={sendPhoneOtp}
                        disabled={loading || formData.phone_number.length !== 10}
                        className="w-full flex justify-center py-2 px-4 border border-brand text-brand hover:bg-brand hover:text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                      >
                        {loading ? 'Sending...' : 'Send SMS OTP'}
                      </button>
                    ) : (
                      <div className="space-y-3 p-4 bg-slate-50 rounded-lg border border-slate-200">
                        <label className="block text-sm font-medium text-slate-700">Enter 6-digit OTP</label>
                        <input
                          type="text"
                          name="phone"
                          maxLength={6}
                          value={otps.phone}
                          onChange={handleOtpChange}
                          className="focus:ring-brand focus:border-brand block w-full sm:text-sm border-slate-300 rounded-lg py-2 border text-center tracking-widest font-mono"
                          placeholder="------"
                        />
                        <div className="flex space-x-2">
                          <button
                            type="button"
                            onClick={verifyPhoneOtp}
                            disabled={loading || otps.phone.length !== 6}
                            className="flex-1 py-2 bg-brand text-white rounded-lg text-sm font-medium hover:bg-brand-dark transition-colors disabled:opacity-50"
                          >
                            Verify Phone
                          </button>
                          <button
                            type="button"
                            onClick={sendPhoneOtp}
                            disabled={timers.phone > 0 || loading || status.phoneResends >= 3}
                            className="px-4 py-2 bg-white border border-slate-300 text-slate-700 rounded-lg text-sm font-medium hover:bg-slate-50 transition-colors disabled:opacity-50"
                          >
                            {timers.phone > 0 ? `Resend in ${timers.phone}s` : 'Resend'}
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
                      className="flex items-center py-2 px-6 bg-brand text-white rounded-lg text-sm font-medium hover:bg-brand-dark transition-colors"
                    >
                      Next <ChevronRight className="ml-1 w-4 h-4" />
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
                  className="flex items-center text-sm text-slate-500 hover:text-slate-800 mb-4"
                >
                  <ChevronLeft className="w-4 h-4 mr-1" /> Back
                </button>
                
                <div>
                  <label className="block text-sm font-medium text-slate-700">Password</label>
                  <div className="mt-1 relative rounded-md shadow-sm">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <Lock className="h-5 w-5 text-slate-400" />
                    </div>
                    <input
                      type="password"
                      name="password"
                      required
                      className="focus:ring-brand focus:border-brand block w-full pl-10 sm:text-sm border-slate-300 rounded-lg py-2 border"
                      placeholder="••••••••"
                      value={formData.password}
                      onChange={handleChange}
                    />
                  </div>
                  <ul className="mt-2 text-xs text-slate-500 space-y-1 list-disc pl-4">
                    <li className={formData.password.length >= 8 ? 'text-green-600' : ''}>Min 8 characters</li>
                    <li className={/[A-Z]/.test(formData.password) ? 'text-green-600' : ''}>1 uppercase letter</li>
                    <li className={/[a-z]/.test(formData.password) ? 'text-green-600' : ''}>1 lowercase letter</li>
                    <li className={/[0-9]/.test(formData.password) ? 'text-green-600' : ''}>1 number</li>
                    <li className={/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]+/.test(formData.password) ? 'text-green-600' : ''}>1 special character</li>
                  </ul>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700">Confirm Password</label>
                  <div className="mt-1 relative rounded-md shadow-sm">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <Lock className="h-5 w-5 text-slate-400" />
                    </div>
                    <input
                      type="password"
                      name="confirm_password"
                      required
                      className="focus:ring-brand focus:border-brand block w-full pl-10 sm:text-sm border-slate-300 rounded-lg py-2 border"
                      placeholder="••••••••"
                      value={formData.confirm_password}
                      onChange={handleChange}
                    />
                  </div>
                </div>

                <div className="pt-4">
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-brand hover:bg-brand-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand transition-colors disabled:opacity-70"
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
