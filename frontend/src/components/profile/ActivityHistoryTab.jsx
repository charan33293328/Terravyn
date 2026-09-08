import React, { useState, useEffect } from 'react';
import { Activity, Search, Filter, Loader2, Clock, ChevronLeft, ChevronRight } from 'lucide-react';
import client from '../../api/client';
import dayjs from 'dayjs';

export default function ActivityHistoryTab() {
  const [loading, setLoading] = useState(true);
  const [activities, setActivities] = useState([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  
  const [search, setSearch] = useState('');
  const [activityType, setActivityType] = useState('All');

  const activityTypes = [
    'All',
    'PROFILE_UPDATED',
    'PASSWORD_CHANGED',
    'SESSION_TERMINATED',
    'SESSIONS_TERMINATED',
    'NOTIFICATION_SETTINGS_UPDATED',
    'DATA_EXPORTED',
    'ACCOUNT_DEACTIVATION_REQUESTED'
  ];

  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      fetchActivities();
    }, 300);
    return () => clearTimeout(delayDebounceFn);
  }, [page, search, activityType]);

  const fetchActivities = async () => {
    try {
      setLoading(true);
      const params = { page, page_size: 10 };
      if (search) params.search = search;
      if (activityType !== 'All') params.activity_type = activityType;
      
      const res = await client.get('/farmer/profile/activity', { params });
      setActivities(res.data.items);
      setTotalPages(res.data.total_pages);
      setTotalCount(res.data.total);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handlePrevPage = () => {
    if (page > 1) setPage(page - 1);
  };

  const handleNextPage = () => {
    if (page < totalPages) setPage(page + 1);
  };

  return (
    <div className="max-w-4xl">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-emerald-50 rounded-lg text-emerald-600">
          <Activity className="w-5 h-5" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-slate-900">Activity History</h2>
          <p className="text-sm text-slate-500">Review recent actions and security events on your account.</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <div className="relative flex-1">
          <Search className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search activities..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="w-full pl-10 pr-4 py-2 bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
          />
        </div>
        <div className="relative min-w-[200px]">
          <Filter className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <select
            value={activityType}
            onChange={(e) => { setActivityType(e.target.value); setPage(1); }}
            className="w-full pl-10 pr-4 py-2 bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 appearance-none"
          >
            {activityTypes.map(t => (
              <option key={t} value={t}>{t === 'All' ? 'All Activity Types' : t.replace(/_/g, ' ')}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Activity List */}
      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden relative min-h-[400px]">
        {loading && (
          <div className="absolute inset-0 bg-white/80 z-10 flex items-center justify-center">
            <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
          </div>
        )}

        {activities.length === 0 && !loading ? (
          <div className="p-12 text-center text-slate-500">
            <Activity className="w-12 h-12 mx-auto text-slate-300 mb-3" />
            <p className="text-lg font-medium text-slate-900">No recent account activities found.</p>
            <p>Try adjusting your search or filter.</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {activities.map((activity) => (
              <div key={activity.id} className="p-4 sm:p-6 hover:bg-slate-50 transition-colors flex items-start gap-4">
                <div className="p-2 bg-slate-100 rounded-full text-slate-500 shrink-0 mt-1">
                  <Clock className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 sm:gap-4 mb-1">
                    <span className="font-semibold text-slate-900 truncate">
                      {activity.activity_type.replace(/_/g, ' ')}
                    </span>
                    <span className="text-xs text-slate-500 whitespace-nowrap">
                      {dayjs(activity.created_at).format('MMM DD, YYYY HH:mm A')}
                    </span>
                  </div>
                  <p className="text-sm text-slate-600">{activity.description}</p>
                  {activity.source && (
                    <div className="text-xs text-slate-400 mt-2">Source: {activity.source}</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="px-6 py-4 border-t border-slate-200 bg-slate-50 flex items-center justify-between">
            <span className="text-sm text-slate-500">
              Showing page {page} of {totalPages}
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={handlePrevPage}
                disabled={page === 1}
                className="p-1 rounded bg-white border border-slate-200 text-slate-600 disabled:opacity-50"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <button
                onClick={handleNextPage}
                disabled={page === totalPages}
                className="p-1 rounded bg-white border border-slate-200 text-slate-600 disabled:opacity-50"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
