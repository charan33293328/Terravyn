import React, { useState, useEffect } from 'react';
import { Plus, Edit2, Trash2, X, Check, Eye } from 'lucide-react';
import api from '../../../api/client';
import TiptapEditor from '../../components/TiptapEditor';

const BlogManager = () => {
  const [blogs, setBlogs] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Editor State
  const [isEditing, setIsEditing] = useState(false);
  const [currentBlog, setCurrentBlog] = useState(null);
  
  // Form State
  const [title, setTitle] = useState('');
  const [slug, setSlug] = useState('');
  const [content, setContent] = useState('');
  const [featuredImage, setFeaturedImage] = useState('');
  const [status, setStatus] = useState('DRAFT');

  useEffect(() => {
    fetchBlogs();
  }, []);

  const fetchBlogs = async () => {
    try {
      setLoading(true);
      const res = await api.get('/admin/cms/blog');
      setBlogs(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    try {
      const payload = { title, slug, content, featured_image: featuredImage, status };
      if (currentBlog) {
        await api.put(`/admin/cms/blog/${currentBlog.id}`, payload);
      } else {
        await api.post('/admin/cms/blog', payload);
      }
      setIsEditing(false);
      fetchBlogs();
    } catch (err) {
      console.error(err);
      alert("Failed to save article");
    }
  };

  const openEditor = (blog = null) => {
    if (blog) {
      setCurrentBlog(blog);
      setTitle(blog.title);
      setSlug(blog.slug);
      setContent(blog.content);
      setFeaturedImage(blog.featured_image || '');
      setStatus(blog.status);
    } else {
      setCurrentBlog(null);
      setTitle('');
      setSlug('');
      setContent('');
      setFeaturedImage('');
      setStatus('DRAFT');
    }
    setIsEditing(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this article?")) return;
    try {
      await api.delete(`/admin/cms/blog/${id}`);
      fetchBlogs();
    } catch (err) {
      console.error(err);
    }
  };

  // Generate slug from title
  useEffect(() => {
    if (!currentBlog && title) {
      setSlug(title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)+/g, ''));
    }
  }, [title, currentBlog]);

  if (isEditing) {
    return (
      <div className="bg-white dark:bg-slate-900 rounded-3xl p-8 border border-slate-100 dark:border-slate-800/50 shadow-sm">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white">{currentBlog ? 'Edit Article' : 'New Article'}</h2>
          </div>
          <div className="flex items-center gap-3">
            <button 
              onClick={() => setIsEditing(false)}
              className="px-4 py-2 rounded-xl font-bold text-sm text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:bg-slate-800 transition-colors"
            >
              Cancel
            </button>
            <button 
              onClick={handleSave}
              className="bg-brand text-white px-6 py-2 rounded-xl font-bold text-sm hover:bg-brand-dark transition-colors flex items-center gap-2"
            >
              <Check size={18} /> Save Article
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-6">
            <div>
              <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Article Title</label>
              <input 
                type="text" 
                value={title} 
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Enter an engaging title..."
                className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-lg font-bold focus:outline-none focus:ring-2 focus:ring-brand/50 focus:border-brand transition-all"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Content</label>
              <TiptapEditor value={content} onChange={setContent} />
            </div>
          </div>

          <div className="space-y-6">
            <div className="bg-slate-50 dark:bg-slate-950 p-6 rounded-2xl border border-slate-200 dark:border-slate-800">
              <h3 className="font-bold text-slate-900 dark:text-white mb-4">Publishing Settings</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">URL Slug</label>
                  <input 
                    type="text" 
                    value={slug} 
                    onChange={(e) => setSlug(e.target.value)}
                    className="w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Status</label>
                  <select 
                    value={status} 
                    onChange={(e) => setStatus(e.target.value)}
                    className="w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50"
                  >
                    <option value="DRAFT">Draft</option>
                    <option value="PUBLISHED">Published</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Featured Image URL</label>
                  <input 
                    type="text" 
                    value={featuredImage} 
                    onChange={(e) => setFeaturedImage(e.target.value)}
                    placeholder="/static/media/images/..."
                    className="w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50 mb-2"
                  />
                  {featuredImage && (
                    <img src={featuredImage.startsWith('http') ? featuredImage : `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}${featuredImage}`} alt="Preview" className="w-full h-32 object-cover rounded-xl border border-slate-200 dark:border-slate-800" />
                  )}
                  <p className="text-[10px] text-slate-500 dark:text-slate-400 mt-1">Tip: Upload images via Media Library and copy the URL.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (loading) return <div className="animate-pulse h-64 bg-white dark:bg-slate-900 rounded-3xl" />;

  return (
    <div className="bg-white dark:bg-slate-900 rounded-3xl p-8 border border-slate-100 dark:border-slate-800/50 shadow-sm">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">News & Announcements</h2>
          <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">Manage blog posts, company news, and system updates.</p>
        </div>
        <button 
          onClick={() => openEditor()}
          className="bg-brand text-white px-5 py-2.5 rounded-xl font-bold text-sm hover:bg-brand-dark transition-colors flex items-center gap-2"
        >
          <Plus size={18} /> Create Article
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {blogs.length === 0 ? (
          <div className="col-span-full text-center py-12 text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-950 rounded-2xl border-2 border-dashed border-slate-200 dark:border-slate-800">
            No articles created yet. Start writing!
          </div>
        ) : (
          blogs.map((blog) => (
            <div key={blog.id} className="bg-slate-50 dark:bg-slate-950 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden hover:border-slate-300 transition-colors group">
              {blog.featured_image ? (
                <div className="aspect-video bg-slate-200 relative">
                  <img src={blog.featured_image.startsWith('http') ? blog.featured_image : `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}${blog.featured_image}`} alt={blog.title} className="w-full h-full object-cover" />
                </div>
              ) : (
                <div className="aspect-video bg-slate-200 flex items-center justify-center">
                  <Eye size={32} className="text-slate-400" />
                </div>
              )}
              
              <div className="p-5">
                <div className="flex items-center justify-between mb-2">
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${blog.status === 'PUBLISHED' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>
                    {blog.status}
                  </span>
                  <span className="text-[10px] font-medium text-slate-500 dark:text-slate-400">
                    {new Date(blog.created_at).toLocaleDateString()}
                  </span>
                </div>
                <h3 className="font-bold text-slate-900 dark:text-white line-clamp-2 mb-4 h-12" title={blog.title}>{blog.title}</h3>
                
                <div className="flex items-center justify-between pt-4 border-t border-slate-200 dark:border-slate-800">
                  <button onClick={() => openEditor(blog)} className="text-sm font-bold text-brand hover:text-brand-dark flex items-center gap-1">
                    <Edit2 size={14} /> Edit
                  </button>
                  <button onClick={() => handleDelete(blog.id)} className="text-sm font-bold text-slate-400 hover:text-red-500 flex items-center gap-1">
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default BlogManager;
