import React, { useState, useEffect, useRef } from 'react';
import { UploadCloud, File, Image as ImageIcon, Film, Trash2, Copy, Check, ExternalLink } from 'lucide-react';
import api from '../../../api/client';

const MediaLibrary = () => {
  const [media, setMedia] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [copiedId, setCopiedId] = useState(null);
  
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetchMedia();
  }, []);

  const fetchMedia = async () => {
    try {
      setLoading(true);
      const res = await api.get('/admin/cms/media');
      setMedia(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      setUploading(true);
      await api.post('/admin/cms/media', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      fetchMedia();
    } catch (err) {
      console.error("Upload failed", err);
      alert("Failed to upload file. Check file size and format.");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this media asset? It might break pages where it's used.")) return;
    try {
      await api.delete(`/admin/cms/media/${id}`);
      fetchMedia();
    } catch (err) {
      console.error(err);
    }
  };

  const handleCopy = (url, id) => {
    // Generate full URL
    const fullUrl = window.location.origin + url;
    navigator.clipboard.writeText(fullUrl);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const formatSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getIcon = (type) => {
    if (type.startsWith('image/')) return ImageIcon;
    if (type.startsWith('video/')) return Film;
    return File;
  };

  return (
    <div className="bg-white dark:bg-slate-900 rounded-3xl p-8 border border-slate-100 dark:border-slate-800/50 shadow-sm">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">Media Library</h2>
          <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">Manage images, videos, and documents used across the site.</p>
        </div>
        <div>
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileUpload} 
            className="hidden" 
            accept="image/*,video/*,.pdf" 
          />
          <button 
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="bg-brand text-white px-5 py-2.5 rounded-xl font-bold text-sm hover:bg-brand-dark transition-colors flex items-center gap-2 disabled:opacity-50"
          >
            {uploading ? (
              <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Uploading...</>
            ) : (
              <><UploadCloud size={18} /> Upload Media</>
            )}
          </button>
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {[1,2,3,4,5].map(i => <div key={i} className="animate-pulse aspect-square bg-slate-100 dark:bg-slate-800 rounded-2xl" />)}
        </div>
      ) : media.length === 0 ? (
        <div className="text-center py-16 px-4 bg-slate-50 dark:bg-slate-950 rounded-2xl border-2 border-dashed border-slate-200 dark:border-slate-800">
          <UploadCloud size={48} className="mx-auto text-slate-300 mb-4" />
          <h3 className="text-lg font-bold text-slate-900 dark:text-white">Drop files here or click Upload</h3>
          <p className="text-slate-500 dark:text-slate-400 mt-2 text-sm">Supports JPG, PNG, MP4, and PDF</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {media.map((asset) => {
            const Icon = getIcon(asset.file_type);
            const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
            const fullUrl = asset.file_path.startsWith('http') ? asset.file_path : `${baseUrl}${asset.file_path}`;
            
            return (
              <div key={asset.id} className="group relative bg-slate-50 dark:bg-slate-950 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden hover:border-brand transition-colors">
                <div className="aspect-square bg-slate-100 dark:bg-slate-800 relative flex items-center justify-center">
                  {isImage ? (
                    <img src={fullUrl} alt={asset.file_name} className="w-full h-full object-cover" />
                  ) : (
                    <Icon size={48} className="text-slate-300" />
                  )}
                  
                  {/* Overlay actions */}
                  <div className="absolute inset-0 bg-slate-900/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                    <button 
                      onClick={() => handleCopy(asset.file_path, asset.id)}
                      className="p-2 bg-white dark:bg-slate-900 rounded-lg hover:bg-brand hover:text-white text-slate-700 dark:text-slate-200 transition-colors"
                      title="Copy URL"
                    >
                      {copiedId === asset.id ? <Check size={18} /> : <Copy size={18} />}
                    </button>
                    <a 
                      href={fullUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="p-2 bg-white dark:bg-slate-900 rounded-lg hover:bg-blue-500 hover:text-white text-slate-700 dark:text-slate-200 transition-colors"
                      title="Open in new tab"
                    >
                      <ExternalLink size={18} />
                    </a>
                    <button 
                      onClick={() => handleDelete(asset.id)}
                      className="p-2 bg-white dark:bg-slate-900 rounded-lg hover:bg-red-500 hover:text-white text-slate-700 dark:text-slate-200 transition-colors"
                      title="Delete"
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>
                </div>
                <div className="p-3">
                  <p className="text-xs font-bold text-slate-700 dark:text-slate-200 truncate" title={asset.file_name}>{asset.file_name}</p>
                  <p className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">{formatSize(asset.file_size)}</p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default MediaLibrary;
