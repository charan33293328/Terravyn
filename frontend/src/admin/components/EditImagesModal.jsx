import React, { useState, useEffect, useRef } from 'react';
import { X, Upload, Image as ImageIcon, Trash2, GripVertical, CheckCircle2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../../api/client';

const EditImagesModal = ({ isOpen, onClose, product, onUpdate }) => {
  const [images, setImages] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (product) {
      setImages(product.images || []);
    }
  }, [product]);

  if (!isOpen || !product) return null;

  const handleFileChange = async (e) => {
    const files = Array.from(e.target.files);
    if (!files.length) return;

    setIsUploading(true);
    const newImages = [...images];

    try {
      for (const file of files) {
        const formData = new FormData();
        formData.append('file', file);
        
        const res = await api.post('/uploads/product-image', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        
        if (res.data.image_path) {
          newImages.push(res.data.image_path);
        }
      }
      setImages(newImages);
    } catch (err) {
      console.error('Failed to upload images:', err);
      alert('Failed to upload some images. Please try again.');
    } finally {
      setIsUploading(false);
      // reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const removeImage = (indexToRemove) => {
    setImages(images.filter((_, idx) => idx !== indexToRemove));
  };

  const moveImage = (index, direction) => {
    if (direction === 'up' && index > 0) {
      const newImages = [...images];
      [newImages[index - 1], newImages[index]] = [newImages[index], newImages[index - 1]];
      setImages(newImages);
    } else if (direction === 'down' && index < images.length - 1) {
      const newImages = [...images];
      [newImages[index + 1], newImages[index]] = [newImages[index], newImages[index + 1]];
      setImages(newImages);
    }
  };

  const handleSave = async () => {
    try {
      setIsSaving(true);
      await api.put(`/admin/products/${product.id}`, {
        images: images
      });
      onUpdate();
      onClose();
    } catch (err) {
      console.error('Failed to update product images:', err);
      alert('Failed to save changes.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm">
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-white dark:bg-slate-900 rounded-2xl shadow-xl w-full max-w-2xl overflow-hidden flex flex-col max-h-[90vh]"
      >
        <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-800/50 flex justify-between items-center bg-slate-50 dark:bg-slate-950">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-brand/10 flex items-center justify-center">
              <ImageIcon className="text-brand w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100">Manage Images</h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 font-mono">{product.sku}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 text-slate-400 hover:text-slate-600 dark:text-slate-300 hover:bg-slate-200 rounded-full transition-colors">
            <X size={20} />
          </button>
        </div>

        <div className="p-6 flex-1 overflow-y-auto">
          <div className="mb-6">
            <input 
              type="file" 
              ref={fileInputRef} 
              className="hidden" 
              multiple 
              accept="image/jpeg, image/png, image/webp" 
              onChange={handleFileChange}
            />
            <div 
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-xl p-8 text-center cursor-pointer hover:bg-slate-50 dark:bg-slate-950 hover:border-brand/50 transition-colors"
            >
              <Upload className="w-8 h-8 text-slate-400 mx-auto mb-3" />
              <p className="font-medium text-slate-700 dark:text-slate-200">Click to upload new images</p>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Supports JPG, PNG, WEBP</p>
            </div>
          </div>

          <div className="space-y-3">
            <h3 className="font-bold text-slate-800 dark:text-slate-100 text-sm">Gallery Images ({images.length})</h3>
            {images.length === 0 ? (
              <div className="bg-amber-50 border border-amber-100 rounded-lg p-4 text-amber-800 text-sm">
                No custom images uploaded. Default placeholder images will be shown on the pricing page.
              </div>
            ) : (
              <div className="space-y-3">
                <AnimatePresence>
                  {images.map((img, index) => (
                    <motion.div 
                      key={`${img}-${index}`}
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="flex items-center gap-4 p-3 bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-100 dark:border-slate-800/50 group"
                    >
                      <div className="flex flex-col gap-1 text-slate-400">
                        <button 
                          onClick={() => moveImage(index, 'up')}
                          disabled={index === 0}
                          className="hover:text-brand disabled:opacity-30 disabled:hover:text-slate-400"
                        >
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m18 15-6-6-6 6"/></svg>
                        </button>
                        <button 
                          onClick={() => moveImage(index, 'down')}
                          disabled={index === images.length - 1}
                          className="hover:text-brand disabled:opacity-30 disabled:hover:text-slate-400"
                        >
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m6 9 6 6 6-6"/></svg>
                        </button>
                      </div>
                      
                      <div className="w-16 h-16 rounded-lg overflow-hidden bg-slate-200 shrink-0 border border-slate-200 dark:border-slate-800">
                        <img src={img} alt="Product preview" className="w-full h-full object-cover" />
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-slate-700 dark:text-slate-200 truncate">{img.split('/').pop()}</p>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                          {index === 0 ? <span className="text-brand font-medium">Main Image</span> : `Image ${index + 1}`}
                        </p>
                      </div>
                      
                      <button 
                        onClick={() => removeImage(index)}
                        className="p-2 text-red-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                      >
                        <Trash2 size={18} />
                      </button>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            )}
          </div>
        </div>

        <div className="px-6 py-4 bg-slate-50 dark:bg-slate-950 border-t border-slate-100 dark:border-slate-800/50 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-5 py-2.5 text-sm font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-200 rounded-xl transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving || isUploading}
            className="px-5 py-2.5 text-sm font-bold bg-brand text-white hover:bg-brand-dark rounded-xl shadow-md transition-colors flex items-center gap-2 disabled:opacity-70"
          >
            {isSaving ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <CheckCircle2 size={18} />
                Save Changes
              </>
            )}
          </button>
        </div>
      </motion.div>
    </div>
  );
};

export default EditImagesModal;
