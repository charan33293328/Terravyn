import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Leaf, Lock, User as UserIcon, Mail, ArrowRight, ArrowLeft, Eye, EyeOff } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const Login = () => {
  const [step, setStep] = useState(1);
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const validateIdentifier = (value) => {
    const trimmed = value.trim();
    if (!trimmed) {
      return { valid: false, message: 'Please enter your username or email address.' };
    }

    if (trimmed.includes('@')) {
      const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
      if (!emailRegex.test(trimmed)) {
        return { valid: false, message: 'Please enter a valid email address (e.g., name@example.com).' };
      }
      return { valid: true, type: 'email' };
    } else {
      const usernameRegex = /^[a-zA-Z0-9_.-]{3,30}$/;
      if (trimmed.length < 3) {
        return { valid: false, message: 'Username must be at least 3 characters long.' };
      }
      if (!usernameRegex.test(trimmed)) {
        return { valid: false, message: 'Username can only contain letters, numbers, underscores, hyphens, and dots.' };
      }
      return { valid: true, type: 'username' };
    }
  };

  const handleNext = (e) => {
    e?.preventDefault();
    setError('');
    const validation = validateIdentifier(identifier);
    if (!validation.valid) {
      setError(validation.message);
      return;
    }
    setStep(2);
  };

  const handleBack = () => {
    setError('');
    setStep(1);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    const validation = validateIdentifier(identifier);
    if (!validation.valid) {
      setError(validation.message);
      setStep(1);
      return;
    }

    if (!password) {
      setError('Password is required.');
      return;
    }

    setLoading(true);
    
    try {
      const user = await login(identifier.trim(), password);
      const adminRoles = ['super_admin', 'admin', 'operations_manager'];
      
      if (adminRoles.includes(user.role)) {
        navigate('/admin/dashboard');
      } else if (user.role === 'support_agent') {
        navigate('/admin/support');
      } else {
        navigate('/farmer/dashboard');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid username/email or password.');
    } finally {
      setLoading(false);
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
          Welcome Back
        </h2>
        <p className="mt-2 text-center text-sm text-slate-600">
          Or{' '}
          <Link to="/signup" className="font-medium text-brand hover:text-brand-dark transition-colors">
            create a new platform account
          </Link>
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow-sm sm:rounded-xl sm:px-10 border border-slate-200">
          {step === 1 ? (
            <form className="space-y-6" onSubmit={handleNext}>
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg text-sm">
                  {error}
                </div>
              )}
              
              <div>
                <label className="block text-sm font-medium text-slate-700">
                  Username or Email Address
                </label>
                <div className="mt-1 relative rounded-md shadow-sm">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    {identifier.includes('@') ? (
                      <Mail className="h-5 w-5 text-slate-400" />
                    ) : (
                      <UserIcon className="h-5 w-5 text-slate-400" />
                    )}
                  </div>
                  <input
                    type="text"
                    required
                    autoFocus
                    className="focus:ring-brand focus:border-brand block w-full pl-10 sm:text-sm border-slate-300 rounded-lg py-2.5 border"
                    placeholder="Enter your username or email address"
                    value={identifier}
                    onChange={(e) => {
                      setIdentifier(e.target.value);
                      if (error) setError('');
                    }}
                  />
                </div>
                <p className="mt-1.5 text-xs text-slate-500">
                  Enter your registered username or email format to continue.
                </p>
              </div>

              <div className="space-y-3">
                <button
                  type="submit"
                  className="w-full flex justify-center items-center gap-2 py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-brand hover:bg-brand-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand transition-colors"
                >
                  <span>Continue</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
                
                <button
                  type="button"
                  onClick={() => navigate('/')}
                  className="w-full flex justify-center py-2.5 px-4 border border-slate-300 rounded-lg shadow-sm text-sm font-medium text-slate-700 bg-white hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand transition-colors"
                >
                  Back to Landing Page
                </button>
              </div>
              
              <div className="mt-6 text-center text-sm text-slate-600">
                Don't have an account?{' '}
                <Link to="/signup" className="font-medium text-brand hover:text-brand-dark">
                  Create Account
                </Link>
              </div>
            </form>
          ) : (
            <form className="space-y-6" onSubmit={handleSubmit}>
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg text-sm">
                  {error}
                </div>
              )}

              {/* Verified Identifier Badge */}
              <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 flex items-center justify-between">
                <div className="flex items-center space-x-3 overflow-hidden">
                  <div className="w-8 h-8 rounded-full bg-brand/10 text-brand flex items-center justify-center shrink-0">
                    {identifier.includes('@') ? (
                      <Mail className="w-4 h-4" />
                    ) : (
                      <UserIcon className="w-4 h-4" />
                    )}
                  </div>
                  <div className="truncate">
                    <p className="text-xs text-slate-500 font-medium">Signing in as</p>
                    <p className="text-sm font-semibold text-slate-800 truncate">{identifier.trim()}</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={handleBack}
                  className="text-xs font-semibold text-brand hover:text-brand-dark px-2.5 py-1 rounded hover:bg-brand/5 transition-colors shrink-0 ml-2"
                >
                  Change
                </button>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700">Password</label>
                <div className="mt-1 relative rounded-md shadow-sm">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Lock className="h-5 w-5 text-slate-400" />
                  </div>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    autoFocus
                    className="focus:ring-brand focus:border-brand block w-full pl-10 pr-10 sm:text-sm border-slate-300 rounded-lg py-2.5 border"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => {
                      setPassword(e.target.value);
                      if (error) setError('');
                    }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600"
                  >
                    {showPassword ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <input
                    id="show-password"
                    type="checkbox"
                    className="h-4 w-4 text-brand focus:ring-brand border-slate-300 rounded"
                    checked={showPassword}
                    onChange={(e) => setShowPassword(e.target.checked)}
                  />
                  <label htmlFor="show-password" className="ml-2 block text-sm text-slate-900 cursor-pointer">
                    Show Password
                  </label>
                </div>

                <div className="text-sm">
                  <Link to="/forgot-password" className="font-medium text-brand hover:text-brand-dark transition-colors">
                    Forgot Password?
                  </Link>
                </div>
              </div>

              <div className="space-y-3">
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-brand hover:bg-brand-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand transition-colors disabled:opacity-70"
                >
                  {loading ? 'Signing in...' : 'Sign In'}
                </button>
                
                <button
                  type="button"
                  onClick={handleBack}
                  className="w-full flex items-center justify-center gap-2 py-2.5 px-4 border border-slate-300 rounded-lg shadow-sm text-sm font-medium text-slate-700 bg-white hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand transition-colors"
                >
                  <ArrowLeft className="w-4 h-4" />
                  <span>Use another account</span>
                </button>
              </div>
              
              <div className="mt-6 text-center text-sm text-slate-600">
                Don't have an account?{' '}
                <Link to="/signup" className="font-medium text-brand hover:text-brand-dark">
                  Create Account
                </Link>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default Login;

