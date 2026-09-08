import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  LifeBuoy, 
  MessageSquare, 
  Clock, 
  CheckCircle2, 
  AlertCircle, 
  Search,
  Filter,
  Plus,
  ChevronRight,
  BookOpen
} from 'lucide-react';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import client from '../../api/client';

dayjs.extend(relativeTime);

export default function SupportCenter() {
  const navigate = useNavigate();
  const [summary, setSummary] = useState(null);
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState('All');
  const [priorityFilter, setPriorityFilter] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  
  // Pagination
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const fetchSummary = async () => {
    try {
      const response = await client.get('/farmer/support/summary');
      setSummary(response.data);
    } catch (err) {
      console.error('Failed to fetch summary:', err);
    }
  };

  const fetchTickets = async () => {
    try {
      setLoading(true);
      const params = {
        page,
        page_size: 10,
        status: statusFilter !== 'All' ? statusFilter : undefined,
        priority: priorityFilter !== 'All' ? priorityFilter : undefined,
        search: searchQuery || undefined
      };
      
      const response = await client.get('/farmer/support/tickets', { params });
      setTickets(response.data.tickets);
      setTotalPages(response.data.total_pages);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch tickets:', err);
      setError('Failed to load support tickets. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, []);

  useEffect(() => {
    fetchTickets();
  }, [page, statusFilter, priorityFilter, searchQuery]);

  const getStatusBadge = (status) => {
    const styles = {
      'OPEN': 'bg-blue-100 text-blue-800',
      'IN_PROGRESS': 'bg-orange-100 text-orange-800',
      'AWAITING_FARMER_RESPONSE': 'bg-purple-100 text-purple-800',
      'RESOLVED': 'bg-green-100 text-green-800',
      'CLOSED': 'bg-gray-100 text-gray-800'
    };
    const labels = {
      'OPEN': 'Open',
      'IN_PROGRESS': 'In Progress',
      'AWAITING_FARMER_RESPONSE': 'Action Required',
      'RESOLVED': 'Resolved',
      'CLOSED': 'Closed'
    };
    return (
      <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[status] || styles['OPEN']}`}>
        {labels[status] || status}
      </span>
    );
  };

  const getPriorityBadge = (priority) => {
    const styles = {
      'LOW': 'bg-blue-50 text-blue-700 border border-blue-200',
      'MEDIUM': 'bg-yellow-50 text-yellow-700 border border-yellow-200',
      'HIGH': 'bg-orange-50 text-orange-700 border border-orange-200',
      'CRITICAL': 'bg-red-50 text-red-700 border border-red-200'
    };
    return (
      <span className={`px-2 py-0.5 rounded text-xs font-medium ${styles[priority] || styles['LOW']}`}>
        {priority}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Support Center</h1>
          <p className="text-gray-500 text-sm mt-1">
            Need assistance? Create support tickets, track their progress, and connect with the TERRAVYN support team.
          </p>
        </div>
        <button
          onClick={() => navigate('/farmer/support/new')}
          className="inline-flex items-center px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded-lg shadow-sm transition-colors"
        >
          <Plus className="w-4 h-4 mr-2" />
          Create Support Ticket
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex items-center space-x-4">
          <div className="p-3 bg-blue-50 rounded-lg text-blue-600">
            <LifeBuoy className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm font-medium text-gray-500">Total Tickets</p>
            <h3 className="text-2xl font-bold text-gray-900">{summary?.total_tickets || 0}</h3>
          </div>
        </div>
        
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex items-center space-x-4">
          <div className="p-3 bg-orange-50 rounded-lg text-orange-600">
            <Clock className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm font-medium text-gray-500">Open Tickets</p>
            <h3 className="text-2xl font-bold text-gray-900">{summary?.open_tickets || 0}</h3>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex items-center space-x-4">
          <div className="p-3 bg-green-50 rounded-lg text-green-600">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm font-medium text-gray-500">Resolved</p>
            <h3 className="text-2xl font-bold text-gray-900">{summary?.resolved_tickets || 0}</h3>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex items-center space-x-4">
          <div className="p-3 bg-gray-50 rounded-lg text-gray-600">
            <MessageSquare className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm font-medium text-gray-500">Closed</p>
            <h3 className="text-2xl font-bold text-gray-900">{summary?.closed_tickets || 0}</h3>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Main Content - Ticket List */}
        <div className="lg:col-span-2 space-y-4">
          
          {/* Controls */}
          <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search ticket number, subject..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm"
              />
            </div>
            <div className="flex gap-2">
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm bg-white"
              >
                <option value="All">All Statuses</option>
                <option value="OPEN">Open</option>
                <option value="IN_PROGRESS">In Progress</option>
                <option value="AWAITING_FARMER_RESPONSE">Action Required</option>
                <option value="RESOLVED">Resolved</option>
                <option value="CLOSED">Closed</option>
              </select>
              <select
                value={priorityFilter}
                onChange={(e) => setPriorityFilter(e.target.value)}
                className="px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm bg-white"
              >
                <option value="All">All Priorities</option>
                <option value="LOW">Low</option>
                <option value="MEDIUM">Medium</option>
                <option value="HIGH">High</option>
                <option value="CRITICAL">Critical</option>
              </select>
            </div>
          </div>

          {/* Ticket List */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            {loading ? (
              <div className="p-8 text-center text-gray-500">Loading tickets...</div>
            ) : error ? (
              <div className="p-8 text-center text-red-500">{error}</div>
            ) : tickets.length === 0 ? (
              <div className="p-12 text-center flex flex-col items-center">
                <LifeBuoy className="w-12 h-12 text-gray-300 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-1">No support requests yet</h3>
                <p className="text-gray-500 text-sm mb-6 max-w-sm">
                  Need help? Create a support ticket and our team will assist you.
                </p>
                <button
                  onClick={() => navigate('/farmer/support/new')}
                  className="px-4 py-2 bg-green-50 text-green-700 hover:bg-green-100 text-sm font-medium rounded-lg transition-colors"
                >
                  Create Support Ticket
                </button>
              </div>
            ) : (
              <div className="divide-y divide-gray-100">
                {tickets.map((ticket) => (
                  <div 
                    key={ticket.id}
                    onClick={() => navigate(`/farmer/support/${ticket.id}`)}
                    className="p-4 hover:bg-gray-50 cursor-pointer transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-1">
                        <span className="text-xs font-semibold text-gray-500">{ticket.ticket_number}</span>
                        {getStatusBadge(ticket.status)}
                        {getPriorityBadge(ticket.priority)}
                      </div>
                      <h4 className="text-sm font-medium text-gray-900 truncate">{ticket.subject}</h4>
                      <p className="text-xs text-gray-500 mt-1 line-clamp-1">{ticket.description}</p>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-gray-500 sm:text-right">
                      <div className="hidden sm:block">
                        <p className="text-xs">{ticket.category}</p>
                        <p className="text-xs mt-1">Updated {dayjs(ticket.updated_at).fromNow()}</p>
                      </div>
                      <ChevronRight className="w-5 h-5 text-gray-400" />
                    </div>
                  </div>
                ))}
              </div>
            )}
            
            {/* Pagination */}
            {totalPages > 1 && (
              <div className="px-4 py-3 border-t border-gray-100 flex items-center justify-between bg-gray-50">
                <button
                  disabled={page === 1}
                  onClick={() => setPage(p => p - 1)}
                  className="px-3 py-1 text-sm bg-white border border-gray-200 rounded-md disabled:opacity-50"
                >
                  Previous
                </button>
                <span className="text-sm text-gray-600">
                  Page {page} of {totalPages}
                </span>
                <button
                  disabled={page === totalPages}
                  onClick={() => setPage(p => p + 1)}
                  className="px-3 py-1 text-sm bg-white border border-gray-200 rounded-md disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Sidebar - Knowledge Base */}
        <div className="space-y-4">
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
              <BookOpen className="w-5 h-5 mr-2 text-green-600" />
              Self-Help Resources
            </h3>
            <div className="space-y-3">
              {[
                "Frequently Asked Questions",
                "Device Installation Guides",
                "Troubleshooting Sensor Data",
                "How to read Monitoring Charts",
                "Understanding Alerts",
                "Order Tracking Assistance"
              ].map((topic, i) => (
                <a key={i} href="#" className="block p-3 rounded-lg border border-gray-100 hover:border-green-200 hover:bg-green-50 transition-colors group">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700 group-hover:text-green-700">
                      {topic}
                    </span>
                    <ChevronRight className="w-4 h-4 text-gray-400 group-hover:text-green-600" />
                  </div>
                </a>
              ))}
            </div>
            
            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <h4 className="text-sm font-semibold text-blue-900 mb-1 flex items-center">
                <AlertCircle className="w-4 h-4 mr-1" /> Still stuck?
              </h4>
              <p className="text-xs text-blue-800 mb-3">
                If you can't find the answer you're looking for, our support team is ready to help.
              </p>
              <button 
                onClick={() => navigate('/farmer/support/new')}
                className="w-full py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium rounded transition-colors"
              >
                Create a Ticket
              </button>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
