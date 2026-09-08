import React, { Component } from 'react';
import { Users, AlertTriangle } from 'lucide-react';
import Farmers from './Farmers';

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  componentDidCatch(error, info) {
    console.error('UserDirectory crashed:', error, info);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <AlertTriangle className="w-12 h-12 text-amber-400 mb-4" />
          <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100 mb-2">Something went wrong</h3>
          <p className="text-sm text-slate-500 dark:text-slate-400 max-w-sm mb-4">
            {this.state.error?.message || 'An unexpected error occurred.'}
          </p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="px-4 py-2 bg-brand text-white rounded-xl text-sm font-medium hover:bg-brand-dark transition-colors"
          >
            Try Again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

const UserDirectory = () => {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
          <Users className="text-brand w-7 h-7" />
          Farmers
        </h1>
        <p className="text-slate-500 dark:text-slate-400 mt-1">
          Manage registered farmers who have an account on the TERRAVYN platform.
        </p>
      </div>

      <ErrorBoundary>
        <Farmers />
      </ErrorBoundary>
    </div>
  );
};

export default UserDirectory;
