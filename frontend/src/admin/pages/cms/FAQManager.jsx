import React, { useState, useEffect } from 'react';
import { Plus, GripVertical, Edit2, Trash2, Globe, Check, X } from 'lucide-react';
import api from '../../../api/client';

const FAQManager = () => {
  const [faqs, setFaqs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [currentFaq, setCurrentFaq] = useState(null);

  // Form State
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [category, setCategory] = useState('');
  const [status, setStatus] = useState('PUBLISHED');

  useEffect(() => {
    fetchFaqs();
  }, []);

  const fetchFaqs = async () => {
    try {
      setLoading(true);
      const res = await api.get('/admin/cms/faqs');
      setFaqs(res.data.sort((a, b) => a.display_order - b.display_order));
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    try {
      if (currentFaq) {
        await api.put(`/admin/cms/faqs/${currentFaq.id}`, {
          question, answer, category, status
        });
      } else {
        await api.post('/admin/cms/faqs', {
          question, answer, category, status, display_order: faqs.length
        });
      }
      setShowModal(false);
      fetchFaqs();
    } catch (err) {
      console.error(err);
    }
  };

  const openModal = (faq = null) => {
    if (faq) {
      setCurrentFaq(faq);
      setQuestion(faq.question);
      setAnswer(faq.answer);
      setCategory(faq.category || '');
      setStatus(faq.status);
    } else {
      setCurrentFaq(null);
      setQuestion('');
      setAnswer('');
      setCategory('');
      setStatus('PUBLISHED');
    }
    setShowModal(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this FAQ?")) return;
    try {
      await api.delete(`/admin/cms/faqs/${id}`);
      fetchFaqs();
    } catch (err) {
      console.error(err);
    }
  };

  // Drag and Drop
  const [draggedItem, setDraggedItem] = useState(null);

  const handleDragStart = (e, index) => {
    setDraggedItem(index);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e, index) => {
    e.preventDefault();
    if (draggedItem === null || draggedItem === index) return;
    
    const newFaqs = [...faqs];
    const item = newFaqs[draggedItem];
    newFaqs.splice(draggedItem, 1);
    newFaqs.splice(index, 0, item);
    
    setDraggedItem(index);
    setFaqs(newFaqs);
  };

  const handleDragEnd = async () => {
    setDraggedItem(null);
    // Save new order to backend
    try {
      await Promise.all(
        faqs.map((faq, idx) => 
          api.put(`/admin/cms/faqs/${faq.id}`, { display_order: idx })
        )
      );
    } catch (err) {
      console.error("Failed to save reorder", err);
    }
  };

  if (loading) return <div className="animate-pulse h-64 bg-white dark:bg-slate-900 rounded-3xl" />;

  return (
    <div className="bg-white dark:bg-slate-900 rounded-3xl p-8 border border-slate-100 dark:border-slate-800/50 shadow-sm">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">FAQ Management</h2>
          <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">Drag and drop to reorder frequently asked questions.</p>
        </div>
        <button 
          onClick={() => openModal()}
          className="bg-brand text-white px-5 py-2.5 rounded-xl font-bold text-sm hover:bg-brand-dark transition-colors flex items-center gap-2"
        >
          <Plus size={18} /> Add FAQ
        </button>
      </div>

      <div className="space-y-3">
        {faqs.length === 0 ? (
          <div className="text-center py-12 text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-950 rounded-2xl border-2 border-dashed border-slate-200 dark:border-slate-800">
            No FAQs created yet.
          </div>
        ) : (
          faqs.map((faq, index) => (
            <div 
              key={faq.id}
              draggable
              onDragStart={(e) => handleDragStart(e, index)}
              onDragOver={(e) => handleDragOver(e, index)}
              onDragEnd={handleDragEnd}
              className={`flex items-start gap-4 p-4 rounded-2xl border bg-white dark:bg-slate-900 cursor-move transition-colors ${draggedItem === index ? 'border-brand shadow-lg ring-2 ring-brand/20' : 'border-slate-200 dark:border-slate-800 hover:border-slate-300'}`}
            >
              <div className="text-slate-400 mt-1 cursor-grab active:cursor-grabbing">
                <GripVertical size={20} />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-3">
                  <h4 className="font-bold text-slate-900 dark:text-white">{faq.question}</h4>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${faq.status === 'PUBLISHED' ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300'}`}>
                    {faq.status}
                  </span>
                  {faq.category && (
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">
                      {faq.category}
                    </span>
                  )}
                </div>
                <p className="text-sm text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">{faq.answer}</p>
              </div>
              <div className="flex items-center gap-2">
                <button onClick={() => openModal(faq)} className="p-2 text-slate-400 hover:text-brand hover:bg-brand/10 rounded-lg transition-colors">
                  <Edit2 size={16} />
                </button>
                <button onClick={() => handleDelete(faq.id)} className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors">
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-slate-900 rounded-3xl p-8 w-full max-w-2xl shadow-2xl relative">
            <button onClick={() => setShowModal(false)} className="absolute top-6 right-6 text-slate-400 hover:text-slate-600 dark:text-slate-300">
              <X size={24} />
            </button>
            <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-6">{currentFaq ? 'Edit FAQ' : 'Add FAQ'}</h3>
            
            <form onSubmit={handleSave} className="space-y-4">
              <div>
                <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Question</label>
                <input 
                  type="text" 
                  value={question} 
                  onChange={(e) => setQuestion(e.target.value)}
                  className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50 focus:border-brand transition-all"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Answer</label>
                <textarea 
                  value={answer} 
                  onChange={(e) => setAnswer(e.target.value)}
                  className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50 focus:border-brand transition-all h-32 resize-none"
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Category</label>
                  <input 
                    type="text" 
                    value={category} 
                    onChange={(e) => setCategory(e.target.value)}
                    placeholder="e.g. Payments, Devices"
                    className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50 focus:border-brand transition-all"
                  />
                </div>
                <div>
                  <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Status</label>
                  <select 
                    value={status} 
                    onChange={(e) => setStatus(e.target.value)}
                    className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50 focus:border-brand transition-all"
                  >
                    <option value="PUBLISHED">Published</option>
                    <option value="DRAFT">Draft</option>
                  </select>
                </div>
              </div>
              <div className="flex justify-end pt-4">
                <button type="submit" className="bg-brand text-white px-6 py-3 rounded-xl font-bold hover:bg-brand-dark transition-colors">
                  Save FAQ
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default FAQManager;
