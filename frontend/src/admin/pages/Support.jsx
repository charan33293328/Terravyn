import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Search, Filter, HelpCircle, AlertCircle, Clock, CheckCircle2,
  MoreVertical, Eye, Download, LayoutGrid
} from 'lucide-react';
import apiClient from '../../api/client';

const StatCard = ({ title, value, icon: Icon, colorClass }) => (
  <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-100 dark:border-slate-800/50 shadow-sm flex items-center gap-4">
    <div className={`p-4 rounded-xl ${colorClass}`}>
      <Icon size={24} />
    </div>
    <div>
      <p className="text-sm font-medium text-slate-500 dark:text-slate-400 mb-1">{title}</p>
      <h3 className="text-2xl font-bold text-slate-900 dark:text-white">{value}</h3>
    </div>
  </div>
);

const PriorityBadge = ({ priority }) => {
  const styles = {
    LOW: 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200',
    NORMAL: 'bg-blue-100 text-blue-700',
    HIGH: 'bg-amber-100 text-amber-700',
    CRITICAL: 'bg-red-100 text-red-700'
  };
  return (
    <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${styles[priority] || styles.NORMAL}`}>
      {priority}
    </span>
  );
};

const StatusBadge = ({ status }) => {
  const styles = {
    OPEN: 'bg-emerald-100 text-emerald-700',
    IN_PROGRESS: 'bg-blue-100 text-blue-700',
    WAITING_FOR_CUSTOMER: 'bg-amber-100 text-amber-700',
    RESOLVED: 'bg-purple-100 text-purple-700',
    CLOSED: 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200'
  };
  return (
    <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${styles[status] || styles.OPEN}`}>
      {status.replace(/_/g, ' ')}
    </span>
  );
};

const Support = () => {
  const [stats, setStats] = useState(null);
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');

  useEffect(() => {
    fetchData();
  }, [statusFilter, priorityFilter]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [statsRes, ticketsRes] = await Promise.all([
        apiClient.get('/admin/support/tickets/stats'),
        apiClient.get('/admin/support/tickets', {
          params: {
            status: statusFilter || undefined,
            priority: priorityFilter || undefined,
            search: searchTerm || undefined
          }
        })
      ]);
      setStats(statsRes.data);
      setTickets(ticketsRes.data.items);
    } catch (err) {
      console.error("Failed to fetch support data", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    fetchData();
  };

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Support Center</h1>
          <p className="text-slate-500 dark:text-slate-400">Manage customer inquiries and technical support tickets.</p>
        </div>
      </div>

      {/* Stats Dashboard */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-6 gap-4">
          <StatCard title="Total Tickets" value={stats.total} icon={LayoutGrid} colorClass="bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300" />
          <StatCard title="Open Tickets" value={stats.open} icon={AlertCircle} colorClass="bg-emerald-100 text-emerald-600" />
          <StatCard title="In Progress" value={stats.in_progress} icon={Clock} colorClass="bg-blue-100 text-blue-600" />
          <StatCard title="Resolved" value={stats.resolved} icon={CheckCircle2} colorClass="bg-purple-100 text-purple-600" />
          <StatCard title="High Priority" value={stats.high_priority} icon={AlertCircle} colorClass="bg-red-100 text-red-600" />
          <StatCard title="Created Today" value={stats.created_today} icon={HelpCircle} colorClass="bg-amber-100 text-amber-600" />
        </div>
      )}

      {/* Tickets List Section */}
      <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-100 dark:border-slate-800/50 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-100 dark:border-slate-800/50 space-y-4 sm:space-y-0 sm:flex sm:items-center sm:justify-between">
          <form onSubmit={handleSearch} className="relative w-full sm:max-w-md">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input 
              type="text" 
              placeholder="Search by Ticket ID, Customer, or Subject..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-11 pr-4 py-3 bg-slate-50 dark:bg-slate-950 border-none rounded-xl focus:ring-2 focus:ring-brand"
            />
          </form>
          
          <div className="flex items-center gap-3">
            <select 
              value={statusFilter} 
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-slate-50 dark:bg-slate-950 border-none rounded-xl py-3 px-4 font-medium text-slate-700 dark:text-slate-200 focus:ring-2 focus:ring-brand"
            >
              <option value="">All Statuses</option>
              <option value="OPEN">Open</option>
              <option value="IN_PROGRESS">In Progress</option>
              <option value="WAITING_FOR_CUSTOMER">Waiting For Customer</option>
              <option value="RESOLVED">Resolved</option>
              <option value="CLOSED">Closed</option>
            </select>
            
            <select 
              value={priorityFilter} 
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="bg-slate-50 dark:bg-slate-950 border-none rounded-xl py-3 px-4 font-medium text-slate-700 dark:text-slate-200 focus:ring-2 focus:ring-brand"
            >
              <option value="">All Priorities</option>
              <option value="LOW">Low</option>
              <option value="NORMAL">Normal</option>
              <option value="HIGH">High</option>
              <option value="CRITICAL">Critical</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-slate-50 dark:bg-slate-950 text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400 border-b border-slate-100 dark:border-slate-800/50">
                <th className="px-6 py-4 font-semibold">Ticket Details</th>
                <th className="px-6 py-4 font-semibold">Customer</th>
                <th className="px-6 py-4 font-semibold text-center">Priority</th>
                <th className="px-6 py-4 font-semibold text-center">Status</th>
                <th className="px-6 py-4 font-semibold">Updated</th>
                <th className="px-6 py-4 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/50">
              {loading ? (
                [...Array(5)].map((_, i) => (
                  <tr key={i} className="animate-pulse">
                    <td className="px-6 py-4"><div className="h-4 bg-slate-200 rounded w-3/4"></div></td>
                    <td className="px-6 py-4"><div className="h-4 bg-slate-200 rounded w-1/2"></div></td>
                    <td className="px-6 py-4"><div className="h-4 bg-slate-200 rounded w-16 mx-auto"></div></td>
                    <td className="px-6 py-4"><div className="h-4 bg-slate-200 rounded w-20 mx-auto"></div></td>
                    <td className="px-6 py-4"><div className="h-4 bg-slate-200 rounded w-24"></div></td>
                    <td className="px-6 py-4 text-right"><div className="h-8 bg-slate-200 rounded w-8 ml-auto"></div></td>
                  </tr>
                ))
              ) : tickets.length === 0 ? (
                <tr>
                  <td colSpan="6" className="px-6 py-12 text-center text-slate-500 dark:text-slate-400">
                    <HelpCircle className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                    <p className="text-lg font-medium text-slate-900 dark:text-white">No tickets found</p>
                    <p>Try adjusting your search or filters.</p>
                  </td>
                </tr>
              ) : (
                tickets.map((ticket) => (
                  <tr key={ticket.id} className="hover:bg-slate-50 dark:bg-slate-950 transition-colors group">
                    <td className="px-6 py-4">
                      <div className="flex flex-col">
                        <Link to={`/admin/support/${ticket.id}`} className="font-semibold text-slate-900 dark:text-white hover:text-brand transition-colors">
                          {ticket.subject}
                        </Link>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-xs font-mono font-medium text-brand bg-brand/10 px-2 py-0.5 rounded">
                            {ticket.ticket_number}
                          </span>
                          <span className="text-xs text-slate-500 dark:text-slate-400">{ticket.category}</span>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-slate-900 dark:text-white">{ticket.customer_name}</div>
                      <div className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{ticket.customer_phone}</div>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <PriorityBadge priority={ticket.priority} />
                    </td>
                    <td className="px-6 py-4 text-center">
                      <StatusBadge status={ticket.status} />
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-600 dark:text-slate-300">
                      {new Date(ticket.updated_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link 
                        to={`/admin/support/${ticket.id}`}
                        className="inline-flex items-center justify-center w-8 h-8 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-400 hover:text-brand hover:border-brand/30 transition-all shadow-sm"
                      >
                        <Eye size={16} />
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        
        {/* Simple Pagination Placeholder */}
        {!loading && tickets.length > 0 && (
          <div className="p-4 border-t border-slate-100 dark:border-slate-800/50 flex items-center justify-between text-sm text-slate-500 dark:text-slate-400">
            <span>Showing {tickets.length} tickets</span>
            <div className="flex gap-2">
              <button className="px-3 py-1 border rounded hover:bg-slate-50 dark:bg-slate-950 disabled:opacity-50">Previous</button>
              <button className="px-3 py-1 border rounded hover:bg-slate-50 dark:bg-slate-950 disabled:opacity-50">Next</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Support;
