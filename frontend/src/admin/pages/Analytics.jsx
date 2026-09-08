import React, { useState, useEffect } from 'react';
import { 
  BarChart3, RefreshCw, Calendar, ArrowUpRight, ArrowDownRight,
  Monitor, ShoppingBag, Users, HelpCircle, Activity
} from 'lucide-react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts';
import apiClient from '../../api/client';

const COLORS = ['#10b981', '#f59e0b', '#3b82f6', '#ef4444', '#8b5cf6'];

const StatCard = ({ title, value, subtext, icon: Icon, colorClass, trend }) => (
  <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-100 dark:border-slate-800/50 shadow-sm flex flex-col justify-between">
    <div className="flex justify-between items-start mb-4">
      <div className={`p-3 rounded-xl ${colorClass}`}>
        <Icon size={20} />
      </div>
      {trend && (
        <span className={`flex items-center text-xs font-bold ${trend > 0 ? 'text-emerald-500' : 'text-red-500'}`}>
          {trend > 0 ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
          {Math.abs(trend)}%
        </span>
      )}
    </div>
    <div>
      <h3 className="text-3xl font-bold text-slate-900 dark:text-white">{value}</h3>
      <p className="text-sm font-medium text-slate-500 dark:text-slate-400 mt-1">{title}</p>
      {subtext && <p className="text-xs text-slate-400 mt-1">{subtext}</p>}
    </div>
  </div>
);

const ChartContainer = ({ title, children }) => (
  <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-100 dark:border-slate-800/50 shadow-sm flex flex-col h-[400px]">
    <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-6">{title}</h3>
    <div className="flex-1 w-full h-full relative">
      {children}
    </div>
  </div>
);

const ActivityFeedItem = ({ event }) => {
  const getIcon = (type) => {
    switch(type) {
      case 'ORDER': return <ShoppingBag size={14} className="text-blue-500" />;
      case 'DEVICE': return <Monitor size={14} className="text-emerald-500" />;
      case 'SUPPORT': return <HelpCircle size={14} className="text-amber-500" />;
      case 'USER': return <Users size={14} className="text-purple-500" />;
      default: return <Activity size={14} className="text-slate-500 dark:text-slate-400" />;
    }
  };

  return (
    <div className="flex gap-4 relative">
      <div className="w-8 h-8 rounded-full bg-slate-50 dark:bg-slate-950 flex items-center justify-center shrink-0 border border-slate-100 dark:border-slate-800/50 z-10 relative">
        {getIcon(event.type)}
      </div>
      <div className="flex-1 pb-6 border-l border-slate-100 dark:border-slate-800/50 -ml-8 pl-12 last:border-transparent last:pb-0">
        <p className="text-sm text-slate-700 dark:text-slate-200 font-medium">{event.message}</p>
        <div className="flex items-center gap-2 mt-1">
          <span className="text-xs text-slate-400 font-medium">
            {new Date(event.created_at).toLocaleString()}
          </span>
          {event.reference_id && (
            <span className="text-[10px] font-mono bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded text-slate-500 dark:text-slate-400 uppercase">
              {event.reference_id}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

const Analytics = () => {
  const [dateRange, setDateRange] = useState('30d');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  
  const [overview, setOverview] = useState(null);
  const [devices, setDevices] = useState(null);
  const [orders, setOrders] = useState(null);
  const [customers, setCustomers] = useState(null);
  const [support, setSupport] = useState(null);
  
  const [ordersChart, setOrdersChart] = useState([]);
  const [revenueChart, setRevenueChart] = useState([]);
  const [supportDist, setSupportDist] = useState([]);
  const [activity, setActivity] = useState([]);

  useEffect(() => {
    fetchData();
  }, [dateRange]);

  const fetchData = async () => {
    setLoading(true);
    setError(false);
    try {
      const p = { time_range: dateRange };
      const [
        oRes, dRes, ordRes, cRes, sRes, 
        ordChartRes, revChartRes, supDistRes, actRes
      ] = await Promise.all([
        apiClient.get('/admin/analytics/overview'),
        apiClient.get('/admin/analytics/devices'),
        apiClient.get('/admin/analytics/orders'),
        apiClient.get('/admin/analytics/customers'),
        apiClient.get('/admin/analytics/support'),
        apiClient.get('/admin/analytics/charts/orders_trend', { params: p }),
        apiClient.get('/admin/analytics/charts/revenue_trend', { params: p }),
        apiClient.get('/admin/analytics/charts/support_distribution', { params: p }),
        apiClient.get('/admin/analytics/activity', { params: { limit: 15 } })
      ]);
      
      setOverview(oRes.data);
      setDevices(dRes.data);
      setOrders(ordRes.data);
      setCustomers(cRes.data);
      setSupport(sRes.data);
      setOrdersChart(ordChartRes.data);
      setRevenueChart(revChartRes.data);
      setSupportDist(supDistRes.data);
      setActivity(actRes.data);
    } catch (err) {
      console.error("Failed to fetch analytics", err);
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  const deviceDistData = devices ? [
    { name: 'Online', value: devices.online },
    { name: 'Offline', value: devices.offline }
  ] : [];

  const deviceProvData = devices ? [
    { name: 'Provisioned', value: devices.provisioned },
    { name: 'Unprovisioned', value: devices.unprovisioned }
  ] : [];

  return (
    <div className="space-y-8 pb-12">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Analytics Dashboard</h1>
          <p className="text-slate-500 dark:text-slate-400">Real-time business intelligence and operational metrics.</p>
        </div>
        
        <div className="flex items-center gap-3">
          <div className="relative">
            <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <select 
              value={dateRange} 
              onChange={(e) => setDateRange(e.target.value)}
              className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl py-2 pl-9 pr-8 font-medium text-sm text-slate-700 dark:text-slate-200 shadow-sm focus:ring-2 focus:ring-brand"
            >
              <option value="today">Today</option>
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
              <option value="90d">Last 90 Days</option>
            </select>
          </div>
          <button 
            onClick={fetchData}
            disabled={loading}
            className="p-2.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-500 dark:text-slate-400 hover:text-brand hover:border-brand/30 shadow-sm transition-colors disabled:opacity-50"
          >
            <RefreshCw size={18} className={loading ? "animate-spin" : ""} />
          </button>
        </div>
      </div>

      {loading ? (
        <div className="p-12 text-center">
          <RefreshCw className="w-8 h-8 text-brand animate-spin mx-auto mb-4" />
          <p className="text-slate-500 dark:text-slate-400 font-medium">Crunching analytics data...</p>
        </div>
      ) : error || !overview || !devices || !customers || !support ? (
        <div className="p-12 text-center bg-white dark:bg-slate-900 rounded-2xl border border-red-100 shadow-sm">
          <Activity className="w-12 h-12 text-red-300 mx-auto mb-4" />
          <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-2">Unable to load analytics</h3>
          <p className="text-slate-500 dark:text-slate-400 mb-6">There was a problem connecting to the analytics engine. Make sure the backend server has been restarted.</p>
          <button 
            onClick={fetchData}
            className="px-6 py-2 bg-brand text-white rounded-xl font-bold hover:bg-emerald-600 transition shadow-sm"
          >
            Try Again
          </button>
        </div>
      ) : (
        <>
          {/* Main KPI Row */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard 
              title="Total Revenue" 
              value={`₹${overview.total_revenue.toLocaleString()}`}
              subtext="From delivered orders"
              icon={ShoppingBag} 
              colorClass="bg-blue-100 text-blue-600" 
            />
            <StatCard 
              title="Active Devices" 
              value={devices.online.toLocaleString()}
              subtext={`Out of ${devices.total} total devices`}
              icon={Monitor} 
              colorClass="bg-emerald-100 text-emerald-600" 
            />
            <StatCard 
              title="Total Customers" 
              value={customers.total.toLocaleString()}
              subtext={`${customers.with_devices} own devices`}
              icon={Users} 
              colorClass="bg-purple-100 text-purple-600" 
            />
            <StatCard 
              title="Open Tickets" 
              value={support.open.toLocaleString()}
              subtext={`${support.critical} critical priority`}
              icon={HelpCircle} 
              colorClass="bg-amber-100 text-amber-600" 
            />
          </div>

          {/* Charts Row 1 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ChartContainer title="Revenue Trend">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={revenueChart} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="date" tick={{fontSize: 12, fill: '#64748b'}} tickLine={false} axisLine={false} tickFormatter={(val) => val.split('-').slice(1).join('/')} />
                  <YAxis tick={{fontSize: 12, fill: '#64748b'}} tickLine={false} axisLine={false} tickFormatter={(val) => `₹${val}`} />
                  <RechartsTooltip 
                    contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                    formatter={(value) => [`₹${value}`, 'Revenue']}
                  />
                  <Line type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={3} dot={false} activeDot={{ r: 6, fill: '#3b82f6', stroke: '#fff', strokeWidth: 2 }} />
                </LineChart>
              </ResponsiveContainer>
            </ChartContainer>

            <ChartContainer title="Orders Trend">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={ordersChart} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="date" tick={{fontSize: 12, fill: '#64748b'}} tickLine={false} axisLine={false} tickFormatter={(val) => val.split('-').slice(1).join('/')} />
                  <YAxis tick={{fontSize: 12, fill: '#64748b'}} tickLine={false} axisLine={false} />
                  <RechartsTooltip 
                    contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                    formatter={(value) => [value, 'Orders']}
                  />
                  <Line type="monotone" dataKey="value" stroke="#10b981" strokeWidth={3} dot={false} activeDot={{ r: 6, fill: '#10b981', stroke: '#fff', strokeWidth: 2 }} />
                </LineChart>
              </ResponsiveContainer>
            </ChartContainer>
          </div>

          {/* Detailed Stats Row */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            {/* Device Stats column */}
            <div className="space-y-4">
              <h3 className="font-bold text-slate-900 dark:text-white text-lg">Device Distribution</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-100 dark:border-slate-800/50 shadow-sm text-center">
                  <p className="text-2xl font-bold text-emerald-500">{devices.online}</p>
                  <p className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider mt-1">Online</p>
                </div>
                <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-100 dark:border-slate-800/50 shadow-sm text-center">
                  <p className="text-2xl font-bold text-slate-400">{devices.offline}</p>
                  <p className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider mt-1">Offline</p>
                </div>
                <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-100 dark:border-slate-800/50 shadow-sm text-center">
                  <p className="text-2xl font-bold text-blue-500">{devices.provisioned}</p>
                  <p className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider mt-1">Provisioned</p>
                </div>
                <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-100 dark:border-slate-800/50 shadow-sm text-center">
                  <p className="text-2xl font-bold text-amber-500">{devices.unprovisioned}</p>
                  <p className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider mt-1">Unprovisioned</p>
                </div>
              </div>

              <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-100 dark:border-slate-800/50 shadow-sm h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={deviceProvData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {deviceProvData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <RechartsTooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                    <Legend verticalAlign="bottom" height={36} iconType="circle" />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Order/Support breakdown */}
            <div className="space-y-4">
              <h3 className="font-bold text-slate-900 dark:text-white text-lg">Support Categories</h3>
              <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-100 dark:border-slate-800/50 shadow-sm h-[380px]">
                {supportDist.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={supportDist}
                        cx="50%"
                        cy="50%"
                        outerRadius={90}
                        dataKey="value"
                        label={({name, percent}) => `${name} ${(percent * 100).toFixed(0)}%`}
                        labelLine={false}
                      >
                        {supportDist.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <RechartsTooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-full flex flex-col items-center justify-center text-slate-400">
                    <HelpCircle size={48} className="mb-4 opacity-50" />
                    <p>No support tickets in this range.</p>
                  </div>
                )}
              </div>
            </div>

            {/* Recent Activity */}
            <div className="space-y-4">
              <h3 className="font-bold text-slate-900 dark:text-white text-lg flex items-center gap-2">
                <Activity size={20} className="text-brand" /> Recent Activity
              </h3>
              <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-100 dark:border-slate-800/50 shadow-sm h-[380px] overflow-y-auto">
                {activity.length > 0 ? (
                  activity.map((item) => (
                    <ActivityFeedItem key={item.id} event={item} />
                  ))
                ) : (
                  <div className="h-full flex flex-col items-center justify-center text-slate-400">
                    <p>No recent activity found.</p>
                  </div>
                )}
              </div>
            </div>

          </div>
        </>
      )}
    </div>
  );
};

export default Analytics;
