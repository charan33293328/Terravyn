import React, { useState, useEffect } from 'react';
import { 
  Server, Users, ShoppingBag, IndianRupee, HelpCircle, Activity, 
  ArrowRight, AlertCircle, ShieldCheck, Box, RefreshCw
} from 'lucide-react';
import { Link } from 'react-router-dom';
import apiClient from '../../api/client';

const MetricCard = ({ title, value, subtext, icon: Icon, colorClass }) => (
  <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-800/50 flex items-center gap-5 hover:shadow-md transition-all group cursor-default">
    <div className={`p-4 rounded-xl ${colorClass} group-hover:scale-110 transition-transform`}>
      <Icon size={24} />
    </div>
    <div className="overflow-hidden flex-1">
      <p className="text-xs font-bold text-slate-400 uppercase tracking-wider truncate">{title}</p>
      <p className="text-2xl font-black text-slate-900 dark:text-white mt-1 truncate" title={value}>{value !== undefined ? value : '-'}</p>
      {subtext && <p className="text-[10px] font-semibold text-slate-400 mt-1 truncate">{subtext}</p>}
    </div>
  </div>
);

const SectionCard = ({ title, icon: Icon, children, colorClass, manageLink }) => (
  <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-800/50 p-5 flex flex-col h-full">
    <h3 className="font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2 text-sm mb-4">
      <div className={`p-1.5 rounded-lg ${colorClass}`}>
        <Icon size={16} />
      </div>
      {title}
    </h3>
    <div className="flex-1 space-y-3">
      {children}
    </div>
    {manageLink && (
      <div className="mt-4 pt-4 border-t border-slate-50">
        <Link to={manageLink} className="text-xs font-bold text-brand hover:text-brand-dark flex items-center gap-1">
          Manage <ArrowRight size={14} />
        </Link>
      </div>
    )}
  </div>
);

const StatRow = ({ label, value }) => (
  <div className="flex items-center justify-between">
    <span className="text-sm font-medium text-slate-500 dark:text-slate-400">{label}</span>
    <span className="text-sm font-black text-slate-800 dark:text-slate-100">{value !== undefined ? value : '-'}</span>
  </div>
);

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [revenue, setRevenue] = useState({});
  const [orders, setOrders] = useState({});
  const [products, setProducts] = useState({});
  const [customers, setCustomers] = useState({});
  const [devices, setDevices] = useState({});
  const [support, setSupport] = useState({});
  const [verifications, setVerifications] = useState({});
  const [alerts, setAlerts] = useState([]);
  const [activities, setActivities] = useState([]);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.get('/admin/dashboard/summary');
      const data = response.data;

      setRevenue(data.revenue);
      setOrders(data.orders);
      setProducts(data.products);
      setCustomers(data.customers);
      setDevices(data.devices);
      setSupport(data.support);
      setVerifications(data.verifications);
      setAlerts(data.alerts);
      setActivities(data.activities);
    } catch (err) {
      console.error("Error fetching dashboard stats", err);
      setError("Failed to load dashboard data. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96 space-y-4">
        <div className="w-10 h-10 border-4 border-brand border-t-transparent rounded-full animate-spin"></div>
        <p className="text-slate-500 dark:text-slate-400 font-medium animate-pulse">Loading dashboard insights...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-rose-50 border border-rose-200 text-rose-700 p-6 rounded-2xl text-center">
        <AlertCircle className="mx-auto mb-2" size={32} />
        <h3 className="font-bold mb-1">Dashboard Error</h3>
        <p className="text-sm">{error}</p>
        <button onClick={fetchDashboardData} className="mt-4 px-4 py-2 bg-rose-600 text-white rounded-lg text-sm font-bold hover:bg-rose-700 transition-colors">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-8 pb-12">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-black text-slate-900 dark:text-white">Operations Center</h1>
        <button 
          onClick={fetchDashboardData} 
          className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg text-sm font-bold text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:bg-slate-950 transition-colors shadow-sm"
        >
          <RefreshCw size={16} /> Refresh
        </button>
      </div>

      {/* 1. TOP KPI SECTION: Revenue & Orders Overview */}
      <section>
        <h2 className="text-sm font-black text-slate-900 dark:text-white uppercase tracking-widest mb-4">Business KPIs</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard title="Revenue (Today)" value={`₹${revenue.revenue_today?.toLocaleString() || 0}`} subtext="Paid/Successful only" icon={IndianRupee} colorClass="bg-green-50 text-green-600 border border-green-100" />
          <MetricCard title="Revenue (Month)" value={`₹${revenue.revenue_this_month?.toLocaleString() || 0}`} subtext="Paid/Successful only" icon={IndianRupee} colorClass="bg-green-50 text-green-600 border border-green-100" />
          <MetricCard title="New Orders (Today)" value={orders.new_orders_today} subtext="Placed today" icon={ShoppingBag} colorClass="bg-amber-50 text-amber-600 border border-amber-100" />
          <MetricCard title="Pending Orders" value={orders.pending_orders} subtext="Awaiting processing" icon={Activity} colorClass="bg-rose-50 text-rose-600 border border-rose-100" />
        </div>
      </section>

      {/* 2. ATTENTION REQUIRED (Operational Alerts) */}
      {alerts.length > 0 && (
        <section>
          <h2 className="text-sm font-black text-rose-600 uppercase tracking-widest mb-4 flex items-center gap-2">
            <AlertCircle size={18} /> Attention Required
          </h2>
          <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-rose-100 overflow-hidden">
            {alerts.map((alert, i) => (
              <Link key={i} to={alert.link} className={`block p-4 border-l-4 border-rose-500 hover:bg-rose-50 transition-colors ${i > 0 ? 'border-t border-slate-100 dark:border-slate-800/50' : ''}`}>
                <div className="flex items-center justify-between">
                  <span className="font-medium text-slate-800 dark:text-slate-100">{alert.message}</span>
                  <ArrowRight size={16} className="text-rose-400" />
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* 3. OPERATIONAL SECTIONS */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        
        <SectionCard title="Orders Overview" icon={ShoppingBag} colorClass="bg-amber-100 text-amber-600" manageLink="/admin/orders">
          <StatRow label="Processing Orders" value={orders.processing_orders} />
          <StatRow label="Delivered Orders" value={orders.delivered_orders} />
          <StatRow label="Cancelled Orders" value={orders.cancelled_orders} />
        </SectionCard>

        <SectionCard title="Device Operations" icon={Server} colorClass="bg-blue-100 text-blue-600" manageLink="/admin/devices">
          <StatRow label="Registered Devices" value={devices.registered_devices} />
          <StatRow label="Provisioned Devices" value={devices.provisioned_devices} />
          <StatRow label="Assigned Devices" value={devices.assigned_devices} />
          <StatRow label="Online Devices" value={devices.online_devices} />
          <StatRow label="Offline Devices" value={devices.offline_devices} />
          <StatRow label="Awaiting Provisioning" value={devices.devices_awaiting_provisioning} />
        </SectionCard>

        <SectionCard title="Customer Insights" icon={Users} colorClass="bg-purple-100 text-purple-600" manageLink="/admin/customers">
          <StatRow label="New Customers (Month)" value={customers.new_customers_this_month} />
          <StatRow label="Active Customers" value={customers.active_customers} />
          <StatRow label="Customers with Devices" value={customers.customers_with_devices} />
          <StatRow label="Repeat Customers" value={customers.repeat_customers} />
        </SectionCard>

        <SectionCard title="Support Overview" icon={HelpCircle} colorClass="bg-rose-100 text-rose-600" manageLink="/admin/support">
          <StatRow label="Open Tickets" value={support.open_tickets} />
          <StatRow label="High Priority" value={support.high_priority_tickets} />
          <StatRow label="Awaiting Customer" value={support.tickets_awaiting_customer_response} />
          <StatRow label="Resolved Today" value={support.resolved_tickets_today} />
        </SectionCard>

        <SectionCard title="Identity Verification" icon={ShieldCheck} colorClass="bg-emerald-100 text-emerald-600" manageLink="/admin/orders">
          <StatRow label="Pending Reviews" value={verifications.pending_aadhaar_reviews} />
          <StatRow label="Approved" value={verifications.approved_verifications} />
          <StatRow label="Rejected" value={verifications.rejected_verifications} />
          <StatRow label="Addt. Info Requested" value={verifications.additional_information_requested} />
        </SectionCard>

        <SectionCard title="Product Performance" icon={Box} colorClass="bg-indigo-100 text-indigo-600" manageLink="/admin/products">
          <StatRow label="Published Products" value={products.published_products} />
          <StatRow label="Draft Products" value={products.draft_products} />
          <div className="pt-2">
            <span className="text-xs font-bold text-slate-400 uppercase">Top Sellers</span>
            {products.top_selling_products?.length > 0 ? (
              <ul className="mt-1 space-y-1">
                {products.top_selling_products.map((p, i) => (
                  <li key={i} className="text-sm flex justify-between">
                    <span className="truncate pr-2 text-slate-700 dark:text-slate-200">{p.name}</span>
                    <span className="font-bold text-slate-900 dark:text-white">{p.total_sold}</span>
                  </li>
                ))}
              </ul>
            ) : <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">No sales yet</p>}
          </div>
        </SectionCard>

      </div>

      {/* 4. RECENT ACTIVITY FEED */}
      <section>
        <h2 className="text-sm font-black text-slate-900 dark:text-white uppercase tracking-widest mb-4">Recent Activity</h2>
        <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-800/50 overflow-hidden">
          {activities.length > 0 ? (
            <div className="divide-y divide-slate-50">
              {activities.map((act, i) => {
                const date = new Date(act.timestamp);
                const timeString = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                const dateString = date.toLocaleDateString();
                
                return (
                  <div key={i} className="flex items-center gap-4 p-4 hover:bg-slate-50 dark:bg-slate-950 transition-colors">
                    <div className="w-2 h-2 rounded-full bg-brand flex-shrink-0"></div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-slate-800 dark:text-slate-100">{act.message}</p>
                      <p className="text-xs text-slate-400 mt-0.5">{dateString} at {timeString}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
             <div className="p-8 text-center text-slate-500 dark:text-slate-400 text-sm">No recent activities found.</div>
          )}
        </div>
      </section>

    </div>
  );
};

export default Dashboard;
