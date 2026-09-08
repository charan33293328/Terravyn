import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  Send, 
  Paperclip, 
  X, 
  Download, 
  FileText, 
  Image as ImageIcon,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import client from '../../api/client';

dayjs.extend(relativeTime);

export default function SupportTicketDetail() {
  const { ticketId } = useParams();
  const navigate = useNavigate();
  const [ticket, setTicket] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Reply State
  const [replyMessage, setReplyMessage] = useState('');
  const [replyFiles, setReplyFiles] = useState([]);
  const [replying, setReplying] = useState(false);
  const [closing, setClosing] = useState(false);
  
  const messagesEndRef = useRef(null);

  const fetchTicket = async () => {
    try {
      const response = await client.get(`/farmer/support/tickets/${ticketId}`);
      setTicket(response.data);
      setError(null);
    } catch (err) {
      console.error(err);
      setError("Failed to load ticket details.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTicket();
  }, [ticketId]);

  useEffect(() => {
    // Scroll to bottom of messages
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [ticket?.messages]);

  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files);
    if (replyFiles.length + selectedFiles.length > 5) {
      alert("Maximum 5 files allowed.");
      return;
    }
    setReplyFiles([...replyFiles, ...selectedFiles]);
  };

  const removeFile = (index) => {
    setReplyFiles(replyFiles.filter((_, i) => i !== index));
  };

  const handleReplySubmit = async (e) => {
    e.preventDefault();
    if (!replyMessage.trim() && replyFiles.length === 0) return;
    
    setReplying(true);
    const formData = new FormData();
    formData.append('message', replyMessage);
    
    replyFiles.forEach(f => formData.append('files', f));

    try {
      await client.post(`/farmer/support/tickets/${ticketId}/reply`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setReplyMessage('');
      setReplyFiles([]);
      await fetchTicket(); // Refresh ticket
    } catch (err) {
      console.error(err);
      alert(err.response?.data?.detail || "Failed to send reply.");
    } finally {
      setReplying(false);
    }
  };

  const handleCloseTicket = async () => {
    if (!window.confirm("Are you sure you want to close this ticket?")) return;
    
    setClosing(true);
    try {
      await client.put(`/farmer/support/tickets/${ticketId}/close`);
      await fetchTicket();
    } catch (err) {
      console.error(err);
      alert(err.response?.data?.detail || "Failed to close ticket.");
    } finally {
      setClosing(false);
    }
  };

  const downloadAttachment = async (attachmentId, fileName, mimeType) => {
    try {
      const response = await client.get(`/farmer/support/attachments/${attachmentId}`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data], { type: mimeType }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', fileName);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
    } catch (err) {
      console.error("Failed to download attachment", err);
      alert("Failed to download attachment.");
    }
  };

  if (loading) return <div className="p-8 text-center">Loading ticket...</div>;
  if (error) return <div className="p-8 text-center text-red-500">{error}</div>;
  if (!ticket) return null;

  const canReply = ['OPEN', 'IN_PROGRESS', 'AWAITING_FARMER_RESPONSE'].includes(ticket.status);
  const canClose = ['RESOLVED', 'AWAITING_FARMER_RESPONSE'].includes(ticket.status);

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
      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${styles[status] || styles['OPEN']}`}>
        {labels[status] || status}
      </span>
    );
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6 h-full flex flex-col">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-4 rounded-xl shadow-sm border border-gray-100">
        <div className="flex items-center space-x-4">
          <button 
            onClick={() => navigate('/farmer/support')}
            className="p-2 hover:bg-gray-100 rounded-lg text-gray-600 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-xl font-bold text-gray-900">{ticket.ticket_number}</h1>
              {getStatusBadge(ticket.status)}
            </div>
            <p className="text-sm text-gray-500">{ticket.subject}</p>
          </div>
        </div>
        
        {canClose && (
          <button
            onClick={handleCloseTicket}
            disabled={closing}
            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm font-medium rounded-lg transition-colors flex items-center"
          >
            {closing ? 'Closing...' : 'Close Ticket'}
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 min-h-0">
        
        {/* Left Column - Conversation */}
        <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-gray-100 flex flex-col h-[calc(100vh-12rem)]">
          
          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {ticket.messages.filter(m => !m.is_internal).map((msg) => (
              <div key={msg.id} className={`flex ${msg.sender_type === 'FARMER' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] rounded-2xl p-4 ${
                  msg.sender_type === 'FARMER' 
                    ? 'bg-green-50 text-green-900 rounded-br-none border border-green-100' 
                    : 'bg-gray-50 text-gray-900 rounded-bl-none border border-gray-200'
                }`}>
                  <div className="flex items-center justify-between gap-4 mb-2">
                    <span className="text-xs font-bold text-gray-700">
                      {msg.sender_type === 'FARMER' ? 'You' : 'TERRAVYN Support'}
                    </span>
                    <span className="text-[10px] text-gray-500">
                      {dayjs(msg.created_at).format('MMM D, YYYY h:mm A')}
                    </span>
                  </div>
                  
                  <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.message}</p>
                  
                  {/* Attachments */}
                  {msg.attachments && msg.attachments.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-black/5 space-y-2">
                      <p className="text-xs font-semibold text-gray-600">Attachments:</p>
                      <div className="flex flex-wrap gap-2">
                        {msg.attachments.map(att => (
                          <button
                            key={att.id}
                            onClick={() => downloadAttachment(att.id, att.file_name, att.mime_type)}
                            className="flex items-center gap-2 px-3 py-1.5 bg-white bg-opacity-60 hover:bg-opacity-100 border border-black/10 rounded-lg text-xs transition-colors"
                          >
                            {att.mime_type.startsWith('image/') ? <ImageIcon className="w-4 h-4 text-blue-500" /> : <FileText className="w-4 h-4 text-red-500" />}
                            <span className="truncate max-w-[150px]">{att.file_name}</span>
                            <Download className="w-3 h-3 text-gray-400 ml-1" />
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Reply Box */}
          {canReply ? (
            <div className="border-t border-gray-100 p-4 bg-gray-50 rounded-b-xl">
              {replyFiles.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-3 px-2">
                  {replyFiles.map((file, idx) => (
                    <div key={idx} className="flex items-center gap-1 bg-white border border-gray-200 rounded-md px-2 py-1 text-xs">
                      <span className="truncate max-w-[100px]">{file.name}</span>
                      <button onClick={() => removeFile(idx)} className="text-gray-400 hover:text-red-500"><X className="w-3 h-3" /></button>
                    </div>
                  ))}
                </div>
              )}
              <form onSubmit={handleReplySubmit} className="flex items-end gap-2">
                <div className="flex-1 bg-white border border-gray-300 rounded-xl overflow-hidden focus-within:ring-2 focus-within:ring-green-500 focus-within:border-transparent transition-all">
                  <textarea
                    value={replyMessage}
                    onChange={(e) => setReplyMessage(e.target.value)}
                    placeholder="Type your reply..."
                    className="w-full px-4 py-3 resize-none outline-none text-sm max-h-32 min-h-[50px]"
                    rows={replyMessage.split('\n').length > 1 ? Math.min(replyMessage.split('\n').length, 4) : 1}
                  />
                  <div className="flex justify-between items-center px-3 py-2 bg-gray-50 border-t border-gray-100">
                    <div className="flex items-center gap-2">
                      <input
                        type="file"
                        multiple
                        id="reply-file"
                        className="hidden"
                        accept="image/jpeg,image/png,application/pdf"
                        onChange={handleFileChange}
                        disabled={replyFiles.length >= 5}
                      />
                      <label htmlFor="reply-file" className={`p-1.5 rounded-md hover:bg-gray-200 text-gray-500 transition-colors cursor-pointer ${replyFiles.length >= 5 ? 'opacity-50 cursor-not-allowed' : ''}`}>
                        <Paperclip className="w-4 h-4" />
                      </label>
                      <span className="text-[10px] text-gray-400">Max 5 files (JPG, PNG, PDF)</span>
                    </div>
                  </div>
                </div>
                <button
                  type="submit"
                  disabled={replying || (!replyMessage.trim() && replyFiles.length === 0)}
                  className="p-3.5 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white rounded-xl shadow-sm transition-colors flex-shrink-0"
                >
                  <Send className="w-5 h-5" />
                </button>
              </form>
            </div>
          ) : (
            <div className="border-t border-gray-100 p-4 bg-gray-50 rounded-b-xl text-center">
              <p className="text-sm text-gray-500">This ticket is {ticket.status.toLowerCase().replace('_', ' ')}. You cannot reply to it.</p>
            </div>
          )}
        </div>

        {/* Right Column - Metadata */}
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 space-y-6">
            <h3 className="font-bold text-gray-900 border-b border-gray-100 pb-2">Ticket Details</h3>
            
            <div className="space-y-4">
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Category</p>
                <p className="text-sm text-gray-900 mt-1">{ticket.category}</p>
              </div>
              
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Priority</p>
                <p className="text-sm text-gray-900 mt-1">{ticket.priority}</p>
              </div>

              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Created</p>
                <p className="text-sm text-gray-900 mt-1">{dayjs(ticket.created_at).format('MMM D, YYYY h:mm A')}</p>
              </div>

              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Last Updated</p>
                <p className="text-sm text-gray-900 mt-1">{dayjs(ticket.updated_at).fromNow()}</p>
              </div>
            </div>
          </div>

          {/* Related Items */}
          {(ticket.device_id || ticket.farm_id || ticket.order_id) && (
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 space-y-4">
              <h3 className="font-bold text-gray-900 border-b border-gray-100 pb-2">Related Items</h3>
              
              {ticket.device_id && (
                <div>
                  <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Device</p>
                  <button 
                    onClick={() => navigate('/farmer/monitoring')}
                    className="text-sm text-blue-600 hover:text-blue-800 hover:underline mt-1"
                  >
                    View Device Context
                  </button>
                </div>
              )}

              {ticket.farm_id && (
                <div>
                  <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Farm</p>
                  <button 
                    onClick={() => navigate('/farmer/dashboard')}
                    className="text-sm text-blue-600 hover:text-blue-800 hover:underline mt-1"
                  >
                    View Farm Details
                  </button>
                </div>
              )}

              {ticket.order_id && (
                <div>
                  <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Order</p>
                  <button 
                    onClick={() => navigate(`/farmer/orders/${ticket.order_id}`)}
                    className="text-sm text-blue-600 hover:text-blue-800 hover:underline mt-1"
                  >
                    Order #{ticket.order_id}
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
        
      </div>
    </div>
  );
}
