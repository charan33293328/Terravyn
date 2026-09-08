import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  ArrowLeft, MessageSquare, ShieldAlert, CheckCircle2, Lock, Unlock, Send, PenTool,
  Clock, Download, Info, Settings, Paperclip
} from 'lucide-react';
import apiClient from '../../api/client';

const TicketDetails = () => {
  const { id } = useParams();
  const [ticket, setTicket] = useState(null);
  const [customerInfo, setCustomerInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  
  const [replyText, setReplyText] = useState('');
  const [internalNote, setInternalNote] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    fetchTicket();
  }, [id]);

  const fetchTicket = async () => {
    try {
      const res = await apiClient.get(`/admin/support/tickets/${id}`);
      setTicket(res.data);
      
      if (res.data.customer_id) {
        const custRes = await apiClient.get(`/admin/customers/${res.data.customer_id}`);
        setCustomerInfo(custRes.data);
      }
    } catch (err) {
      console.error("Failed to fetch ticket or customer", err);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (newStatus) => {
    try {
      await apiClient.put(`/admin/support/tickets/${id}/status?status=${newStatus}`);
      fetchTicket();
    } catch (err) {
      alert("Failed to update status");
    }
  };

  const handlePriorityChange = async (newPriority) => {
    try {
      await apiClient.put(`/admin/support/tickets/${id}/priority?priority=${newPriority}`);
      fetchTicket();
    } catch (err) {
      alert("Failed to update priority");
    }
  };

  const submitReply = async (e) => {
    e.preventDefault();
    if (!replyText.trim()) return;
    setIsSubmitting(true);
    try {
      await apiClient.post(`/admin/support/tickets/${id}/reply`, { message: replyText });
      setReplyText('');
      fetchTicket();
    } catch (err) {
      alert("Failed to send reply");
    } finally {
      setIsSubmitting(false);
    }
  };

  const submitNote = async (e) => {
    e.preventDefault();
    if (!internalNote.trim()) return;
    setIsSubmitting(true);
    try {
      await apiClient.post(`/admin/support/tickets/${id}/notes`, { note: internalNote });
      setInternalNote('');
      fetchTicket();
    } catch (err) {
      alert("Failed to add note");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-slate-500 dark:text-slate-400 animate-pulse">Loading ticket details...</div>;
  }

  if (!ticket) return <div className="p-8 text-center text-red-500">Ticket not found.</div>;

  const allInteractions = [
    { type: 'INITIAL', date: ticket.created_at, message: ticket.description, sender_type: 'CUSTOMER' },
    ...ticket.messages.map(m => ({ ...m, type: 'MESSAGE', date: m.created_at })),
    ...ticket.internal_notes.map(n => ({ ...n, type: 'NOTE', date: n.created_at, sender_type: 'ADMIN_NOTE' }))
  ].sort((a, b) => new Date(a.date) - new Date(b.date));

  return (
    <div className="space-y-6">
      {/* Header Actions */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div className="flex items-center gap-4">
          <Link to="/admin/support" className="p-2 hover:bg-slate-100 dark:bg-slate-800 rounded-xl transition-colors">
            <ArrowLeft className="w-5 h-5 text-slate-500 dark:text-slate-400" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-3">
              {ticket.subject}
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1 flex gap-2">
              <span className="font-mono text-brand font-bold bg-brand/10 px-2 rounded">{ticket.ticket_number}</span>
              • Created on {new Date(ticket.created_at).toLocaleDateString()}
            </p>
          </div>
        </div>
        
        <div className="flex gap-2">
          {ticket.status !== 'CLOSED' ? (
            <button 
              onClick={() => { if(window.confirm("Close this ticket?")) handleStatusChange('CLOSED') }}
              className="px-4 py-2 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 font-medium rounded-xl hover:bg-slate-200 transition flex items-center gap-2"
            >
              <Lock size={16} /> Close Ticket
            </button>
          ) : (
            <button 
              onClick={() => handleStatusChange('IN_PROGRESS')}
              className="px-4 py-2 bg-emerald-100 text-emerald-700 font-medium rounded-xl hover:bg-emerald-200 transition flex items-center gap-2"
            >
              <Unlock size={16} /> Reopen Ticket
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Pane - Metadata & Customer */}
        <div className="lg:col-span-1 space-y-6">
          
          <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-800/50">
            <h3 className="font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
              <Settings size={18} className="text-slate-400" /> Ticket Properties
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase">Status</label>
                <select 
                  value={ticket.status} 
                  onChange={(e) => handleStatusChange(e.target.value)}
                  className="w-full mt-1 bg-slate-50 dark:bg-slate-950 border-none rounded-xl py-2 px-3 font-medium text-slate-700 dark:text-slate-200 focus:ring-2 focus:ring-brand"
                >
                  <option value="OPEN">Open</option>
                  <option value="IN_PROGRESS">In Progress</option>
                  <option value="WAITING_FOR_CUSTOMER">Waiting For Customer</option>
                  <option value="RESOLVED">Resolved</option>
                  <option value="CLOSED">Closed</option>
                </select>
              </div>
              
              <div>
                <label className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase">Priority</label>
                <select 
                  value={ticket.priority} 
                  onChange={(e) => handlePriorityChange(e.target.value)}
                  className="w-full mt-1 bg-slate-50 dark:bg-slate-950 border-none rounded-xl py-2 px-3 font-medium text-slate-700 dark:text-slate-200 focus:ring-2 focus:ring-brand"
                >
                  <option value="LOW">Low</option>
                  <option value="NORMAL">Normal</option>
                  <option value="HIGH">High</option>
                  <option value="CRITICAL">Critical</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase">Category</label>
                <p className="font-medium text-slate-900 dark:text-white mt-1">{ticket.category}</p>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-800/50">
            <h3 className="font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
              <Info size={18} className="text-slate-400" /> Customer Information
            </h3>
            <div className="space-y-3">
              <div>
                <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Name</p>
                <Link to={`/admin/customers/${ticket.customer_id}`} className="font-semibold text-brand hover:underline">{ticket.customer_name}</Link>
              </div>
              <div>
                <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Email Address</p>
                <p className="font-semibold text-slate-900 dark:text-white">{ticket.customer_email || 'N/A'}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Phone Number</p>
                <p className="font-semibold text-slate-900 dark:text-white">{ticket.customer_phone || 'N/A'}</p>
              </div>
            </div>
            
            {customerInfo && (
              <>
                <div className="mt-6 pt-6 border-t border-slate-100 dark:border-slate-800/50">
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Devices ({customerInfo.device_ownership?.length || 0})</h4>
                  {customerInfo.device_ownership?.map(dev => (
                    <div key={dev.device_uid} className="flex justify-between items-center bg-slate-50 dark:bg-slate-950 p-2 rounded-lg text-sm mb-2">
                      <span className="font-mono text-slate-700 dark:text-slate-200">{dev.device_uid}</span>
                      <span className={`w-2 h-2 rounded-full ${dev.status === 'ONLINE' ? 'bg-emerald-500' : 'bg-slate-400'}`}></span>
                    </div>
                  ))}
                </div>
                
                <div className="mt-4">
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Recent Orders</h4>
                  {customerInfo.order_history?.slice(0, 3).map(ord => (
                    <div key={ord.order_id} className="flex flex-col bg-slate-50 dark:bg-slate-950 p-2 rounded-lg text-sm mb-2">
                      <Link to={`/admin/orders/${ord.order_id}`} className="font-semibold text-brand hover:underline">#{ord.order_id}</Link>
                      <div className="flex justify-between text-xs mt-1 text-slate-500 dark:text-slate-400">
                        <span>Inv: {ord.invoice_number || 'N/A'}</span>
                        <span className="font-bold text-slate-700 dark:text-slate-200">{ord.order_status}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>

        </div>

        {/* Right Pane - Conversation */}
        <div className="lg:col-span-2 bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-800/50 flex flex-col min-h-[600px]">
          <div className="p-5 border-b border-slate-100 dark:border-slate-800/50 font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <MessageSquare size={18} className="text-slate-400" /> Conversation Timeline
          </div>
          
          <div className="flex-1 p-5 overflow-y-auto space-y-6 bg-slate-50 dark:bg-slate-950/50">
            {allInteractions.map((item, idx) => {
              const isCustomer = item.sender_type === 'CUSTOMER';
              const isNote = item.sender_type === 'ADMIN_NOTE';
              
              if (isNote) {
                return (
                  <div key={idx} className="flex justify-center my-4">
                    <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 max-w-lg w-full text-sm">
                      <div className="flex items-center gap-2 text-amber-700 font-bold mb-1">
                        <PenTool size={14} /> Internal Note
                        <span className="text-xs font-normal opacity-70 ml-auto">
                          {new Date(item.date).toLocaleString()}
                        </span>
                      </div>
                      <p className="text-amber-900 whitespace-pre-wrap">{item.note}</p>
                    </div>
                  </div>
                );
              }
              
              return (
                <div key={idx} className={`flex ${isCustomer ? 'justify-start' : 'justify-end'}`}>
                  <div className={`max-w-[80%] rounded-2xl p-4 ${
                    isCustomer ? 'bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-tl-sm' : 'bg-brand text-white rounded-tr-sm shadow-sm'
                  }`}>
                    <div className={`text-xs font-bold mb-2 flex items-center gap-2 ${isCustomer ? 'text-slate-500 dark:text-slate-400' : 'text-emerald-100'}`}>
                      {isCustomer ? ticket.customer_name : 'Support Team'}
                      <span className={`text-[10px] font-normal ${isCustomer ? 'text-slate-400' : 'text-emerald-200'}`}>
                        {new Date(item.date).toLocaleString()}
                      </span>
                    </div>
                    <p className={`whitespace-pre-wrap ${isCustomer ? 'text-slate-700 dark:text-slate-200' : 'text-white'}`}>
                      {item.message}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="p-5 border-t border-slate-100 dark:border-slate-800/50 bg-white dark:bg-slate-900 rounded-b-2xl">
            {ticket.status === 'CLOSED' ? (
              <div className="text-center py-4 text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-950 rounded-xl">
                This ticket is closed. Reopen to continue the conversation.
              </div>
            ) : (
              <div className="space-y-4">
                <form onSubmit={submitReply} className="relative">
                  <textarea 
                    value={replyText}
                    onChange={(e) => setReplyText(e.target.value)}
                    placeholder="Type your reply to the customer here..."
                    className="w-full border-slate-200 dark:border-slate-800 rounded-xl focus:ring-brand focus:border-brand p-4 pr-16 min-h-[100px] resize-y"
                    disabled={isSubmitting}
                  />
                  <button 
                    type="submit"
                    disabled={isSubmitting || !replyText.trim()}
                    className="absolute bottom-4 right-4 p-2 bg-brand text-white rounded-lg hover:bg-emerald-600 disabled:opacity-50 transition"
                  >
                    <Send size={18} />
                  </button>
                </form>
                
                <form onSubmit={submitNote} className="flex gap-2">
                  <input 
                    type="text" 
                    value={internalNote}
                    onChange={(e) => setInternalNote(e.target.value)}
                    placeholder="Add an internal note (visible only to admins)..."
                    className="flex-1 bg-amber-50/50 border border-amber-200 placeholder-amber-400 rounded-xl px-4 py-2 focus:ring-amber-400 focus:border-amber-400 text-sm"
                    disabled={isSubmitting}
                  />
                  <button 
                    type="submit"
                    disabled={isSubmitting || !internalNote.trim()}
                    className="px-4 py-2 bg-amber-100 text-amber-700 font-bold text-sm rounded-xl hover:bg-amber-200 disabled:opacity-50 transition"
                  >
                    Save Note
                  </button>
                </form>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TicketDetails;
