import React, { useState, useEffect, useRef } from 'react';
import { Tag, Save, ArrowLeft, Upload, Trash2, GripVertical, CheckCircle2 } from 'lucide-react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '../../api/client';

const ProductEditor = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const isNew = id === 'new';

  const [loading, setLoading] = useState(!isNew);
  const [saving, setSaving] = useState(false);
  const [generating, setGenerating] = useState(false);
  const fileInputRef = useRef(null);

  const [product, setProduct] = useState({
    name: '',
    slug: '',
    sku: '',
    short_description: '',
    full_description: '',
    category: '',
    tagline: '',
    current_price: 0,
    mrp: 0,
    tax_percentage: 0,
    shipping_charges: 0,
    primary_image: '',
    status: 'DRAFT',
    is_active: true,
    stock_status: 'IN_STOCK',
    images: [],
    specifications: [],
    features: []
  });

  useEffect(() => {
    if (!isNew) {
      fetchProduct();
    }
  }, [id]);

  const fetchProduct = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/public/products`); // Wait, admin products fetch doesn't have ID fetch route?
      // We can use the list and find it or just create a get by ID in admin. Let's use the list for now if no direct API.
      const allRes = await api.get('/admin/products');
      const found = allRes.data.find(p => p.id === parseInt(id));
      if (found) {
        setProduct({
          ...found,
          images: found.images || [],
          specifications: found.specifications || [],
          features: found.features || []
        });
      } else {
        alert("Product not found");
        navigate('/admin/products');
      }
    } catch (err) {
      console.error(err);
      alert("Failed to fetch product details");
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setProduct(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : (type === 'number' ? parseFloat(value) || 0 : value)
    }));
    
    // Auto-generate slug from name if new
    if (isNew && name === 'name') {
      setProduct(prev => ({
        ...prev,
        slug: value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)+/g, '')
      }));
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      
      const payload = { ...product };
      // Calculate discount
      if (payload.mrp > 0 && payload.current_price < payload.mrp) {
        payload.discount_percentage = ((payload.mrp - payload.current_price) / payload.mrp) * 100;
      } else {
        payload.discount_percentage = 0;
      }

      if (isNew) {
        await api.post('/admin/products', payload);
      } else {
        await api.put(`/admin/products/${id}`, payload);
      }
      
      navigate('/admin/products');
    } catch (err) {
      console.error(err);
      alert(err.response?.data?.detail || "Failed to save product");
    } finally {
      setSaving(false);
    }
  };

  const handleGenerateTemplate = async () => {
    if (!product.name || !product.category) {
      alert("Please provide both Product Name and Category to generate a template.");
      return;
    }
    
    try {
      setGenerating(true);
      const res = await api.post('/admin/products/generate-template', {
        name: product.name,
        category: product.category
      });
      
      setProduct(prev => ({
        ...prev,
        ...res.data,
        images: prev.images && prev.images.length > 0 ? prev.images : res.data.images,
        primary_image: prev.primary_image || res.data.primary_image
      }));
      
    } catch (err) {
      console.error(err);
      alert("Failed to generate template.");
    } finally {
      setGenerating(false);
    }
  };

  // Specs
  const addSpec = () => setProduct(prev => ({...prev, specifications: [...prev.specifications, {key: '', value: ''}]}));
  const updateSpec = (idx, field, val) => {
    const newSpecs = [...product.specifications];
    newSpecs[idx][field] = val;
    setProduct(prev => ({...prev, specifications: newSpecs}));
  };
  const removeSpec = (idx) => setProduct(prev => ({...prev, specifications: prev.specifications.filter((_, i) => i !== idx)}));

  // Features
  const addFeature = () => setProduct(prev => ({...prev, features: [...prev.features, {feature: '', display_order: prev.features.length}]}));
  const updateFeature = (idx, val) => {
    const newFeats = [...product.features];
    newFeats[idx].feature = val;
    setProduct(prev => ({...prev, features: newFeats}));
  };
  const removeFeature = (idx) => setProduct(prev => ({...prev, features: prev.features.filter((_, i) => i !== idx)}));

  // Images
  const handleFileUpload = async (e) => {
    const files = Array.from(e.target.files);
    if (!files.length) return;
    
    setSaving(true);
    const newImages = [...product.images];
    
    try {
      for (const file of files) {
        const formData = new FormData();
        formData.append('file', file);
        const res = await api.post('/uploads/product-image', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        if (res.data.image_path) {
          newImages.push({
            image_url: res.data.image_path,
            display_order: newImages.length
          });
        }
      }
      
      setProduct(prev => ({
        ...prev, 
        images: newImages,
        primary_image: prev.primary_image || newImages[0]?.image_url
      }));
    } catch (err) {
      console.error(err);
      alert('Failed to upload image');
    } finally {
      setSaving(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const removeImage = (idx) => {
    const newImages = product.images.filter((_, i) => i !== idx);
    setProduct(prev => ({
      ...prev,
      images: newImages,
      primary_image: prev.primary_image === prev.images[idx].image_url ? (newImages[0]?.image_url || '') : prev.primary_image
    }));
  };

  const setPrimary = (url) => setProduct(prev => ({...prev, primary_image: url}));

  if (loading) return <div className="p-8 text-center text-slate-500 dark:text-slate-400">Loading product data...</div>;

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8 animate-fade-in pb-32">
      
      <div className="flex items-center justify-between bg-white dark:bg-slate-900 p-6 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-800/50 sticky top-4 z-40">
        <div className="flex items-center gap-4">
          <button onClick={() => navigate('/admin/products')} className="p-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 rounded-lg transition-colors text-slate-600 dark:text-slate-300">
            <ArrowLeft size={20} />
          </button>
          <div>
            <h1 className="text-xl font-black text-slate-800 dark:text-slate-100 tracking-tight flex items-center gap-2">
              <Tag className="text-brand w-6 h-6" />
              {isNew ? 'Create New Product' : 'Edit Product'}
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">{product.sku || 'Draft SKU'}</p>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <select 
            name="status"
            value={product.status}
            onChange={handleInputChange}
            className="border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 rounded-lg px-4 py-2 font-medium text-slate-700 dark:text-slate-200 outline-none focus:border-brand"
          >
            <option value="DRAFT">Draft</option>
            <option value="PUBLISHED">Published</option>
            <option value="ARCHIVED">Archived</option>
          </select>
          
          <button 
            onClick={handleSave}
            disabled={saving}
            className="bg-brand text-white px-6 py-2.5 rounded-xl font-bold flex items-center gap-2 hover:bg-brand-dark transition-colors shadow-sm disabled:opacity-70"
          >
            <Save size={18} />
            {saving ? 'Saving...' : 'Save Product'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Main Column */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* General Information */}
          <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl shadow-sm border-2 border-brand/20 relative overflow-hidden">
            {isNew && (
              <div className="absolute top-0 right-0 bg-brand text-white text-xs font-bold px-3 py-1 rounded-bl-lg">
                TERRAVYN Template Engine Active
              </div>
            )}
            <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 mb-4 pb-2 border-b border-slate-100 dark:border-slate-800/50 flex items-center justify-between">
              General Information
            </h2>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2 md:col-span-1">
                  <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Product Name *</label>
                  <input type="text" name="name" value={product.name} onChange={handleInputChange} placeholder="e.g. TERRAVYN Soil Sensor Kit" className="w-full px-4 py-2 border border-slate-200 dark:border-slate-800 rounded-lg focus:ring-2 focus:ring-brand focus:border-transparent outline-none" required />
                </div>
                <div className="col-span-2 md:col-span-1">
                  <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Category *</label>
                  <select name="category" value={product.category} onChange={handleInputChange} className="w-full px-4 py-2 border border-slate-200 dark:border-slate-800 rounded-lg focus:ring-2 focus:ring-brand outline-none" required>
                    <option value="">Select Category...</option>
                    <option value="Smart Agriculture Device">Smart Agriculture Device</option>
                    <option value="Sensor Kit">Sensor Kit</option>
                    <option value="Water Monitoring Device">Water Monitoring Device</option>
                    <option value="Weather Monitoring Device">Weather Monitoring Device</option>
                    <option value="Expansion Module">Expansion Module</option>
                    <option value="Subscription Service">Subscription Service</option>
                  </select>
                </div>
              </div>
              
              {isNew && (
                <div className="bg-brand/5 border border-brand/20 p-4 rounded-xl flex items-center justify-between">
                  <div>
                    <h3 className="font-bold text-brand">Auto-Generate Product Details</h3>
                    <p className="text-sm text-slate-600 dark:text-slate-300">Instantly pre-fill descriptions, features, specifications, and 3D renders based on TERRAVYN templates.</p>
                  </div>
                  <button 
                    onClick={handleGenerateTemplate}
                    disabled={generating}
                    className="bg-brand text-white px-5 py-2 rounded-lg font-bold hover:bg-brand-dark transition-colors shrink-0 flex items-center gap-2"
                  >
                    {generating ? 'Generating...' : 'Generate Details'}
                  </button>
                </div>
              )}
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">SKU *</label>
                  <input type="text" name="sku" value={product.sku} onChange={handleInputChange} className="w-full px-4 py-2 border border-slate-200 dark:border-slate-800 rounded-lg focus:ring-2 focus:ring-brand outline-none" required />
                </div>
                <div>
                  <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">URL Slug *</label>
                  <input type="text" name="slug" value={product.slug} onChange={handleInputChange} className="w-full px-4 py-2 border border-slate-200 dark:border-slate-800 rounded-lg bg-slate-50 dark:bg-slate-950 focus:ring-2 focus:ring-brand outline-none" required />
                </div>
              </div>

              <div>
                <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Tagline</label>
                <input type="text" name="tagline" value={product.tagline} onChange={handleInputChange} className="w-full px-4 py-2 border border-slate-200 dark:border-slate-800 rounded-lg focus:ring-2 focus:ring-brand outline-none" />
              </div>

              <div>
                <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Short Description</label>
                <textarea name="short_description" value={product.short_description} onChange={handleInputChange} rows="2" className="w-full px-4 py-2 border border-slate-200 dark:border-slate-800 rounded-lg focus:ring-2 focus:ring-brand outline-none"></textarea>
              </div>

              <div>
                <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Full Description</label>
                <textarea name="full_description" value={product.full_description} onChange={handleInputChange} rows="5" className="w-full px-4 py-2 border border-slate-200 dark:border-slate-800 rounded-lg focus:ring-2 focus:ring-brand outline-none"></textarea>
              </div>
            </div>
          </div>

          {/* Specifications */}
          <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-800/50">
            <div className="flex justify-between items-center mb-4 pb-2 border-b border-slate-100 dark:border-slate-800/50">
              <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100">Specifications</h2>
              <button onClick={addSpec} className="text-sm font-bold text-brand hover:text-brand-dark">+ Add Row</button>
            </div>
            
            <div className="space-y-3">
              {product.specifications.length === 0 && <p className="text-sm text-slate-500 dark:text-slate-400">No specifications added yet.</p>}
              {product.specifications.map((spec, idx) => (
                <div key={idx} className="flex items-center gap-3">
                  <input type="text" placeholder="Key (e.g. Dimensions)" value={spec.key} onChange={(e) => updateSpec(idx, 'key', e.target.value)} className="flex-1 px-3 py-2 border border-slate-200 dark:border-slate-800 rounded-lg outline-none" />
                  <input type="text" placeholder="Value (e.g. 10x10x5 cm)" value={spec.value} onChange={(e) => updateSpec(idx, 'value', e.target.value)} className="flex-1 px-3 py-2 border border-slate-200 dark:border-slate-800 rounded-lg outline-none" />
                  <button onClick={() => removeSpec(idx)} className="p-2 text-red-400 hover:bg-red-50 rounded-lg"><Trash2 size={18}/></button>
                </div>
              ))}
            </div>
          </div>

          {/* Features */}
          <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-800/50">
            <div className="flex justify-between items-center mb-4 pb-2 border-b border-slate-100 dark:border-slate-800/50">
              <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100">Key Features</h2>
              <button onClick={addFeature} className="text-sm font-bold text-brand hover:text-brand-dark">+ Add Feature</button>
            </div>
            
            <div className="space-y-3">
              {product.features.length === 0 && <p className="text-sm text-slate-500 dark:text-slate-400">No features added yet.</p>}
              {product.features.map((feat, idx) => (
                <div key={idx} className="flex items-center gap-3">
                  <GripVertical className="text-slate-300 cursor-move" size={18} />
                  <input type="text" placeholder="e.g. Real-time Monitoring" value={feat.feature} onChange={(e) => updateFeature(idx, e.target.value)} className="flex-1 px-3 py-2 border border-slate-200 dark:border-slate-800 rounded-lg outline-none" />
                  <button onClick={() => removeFeature(idx)} className="p-2 text-red-400 hover:bg-red-50 rounded-lg"><Trash2 size={18}/></button>
                </div>
              ))}
            </div>
          </div>

        </div>

        {/* Sidebar Column */}
        <div className="space-y-6">
          
          {/* Pricing */}
          <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-800/50">
            <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 mb-4 pb-2 border-b border-slate-100 dark:border-slate-800/50">Pricing</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Selling Price (₹)</label>
                <input type="number" name="current_price" value={product.current_price} onChange={handleInputChange} className="w-full px-4 py-2 border border-slate-200 dark:border-slate-800 rounded-lg outline-none" />
              </div>
              <div>
                <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">MRP (₹)</label>
                <input type="number" name="mrp" value={product.mrp} onChange={handleInputChange} className="w-full px-4 py-2 border border-slate-200 dark:border-slate-800 rounded-lg outline-none" />
              </div>
              
              <div className="grid grid-cols-2 gap-4 border-t border-slate-100 dark:border-slate-800/50 pt-4 mt-2">
                <div>
                  <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Tax (%)</label>
                  <input type="number" name="tax_percentage" value={product.tax_percentage} onChange={handleInputChange} className="w-full px-4 py-2 border border-slate-200 dark:border-slate-800 rounded-lg outline-none" />
                </div>
                <div>
                  <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Shipping (₹)</label>
                  <input type="number" name="shipping_charges" value={product.shipping_charges} onChange={handleInputChange} className="w-full px-4 py-2 border border-slate-200 dark:border-slate-800 rounded-lg outline-none" />
                </div>
              </div>
            </div>
          </div>

          {/* Media */}
          <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-800/50">
            <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 mb-4 pb-2 border-b border-slate-100 dark:border-slate-800/50">Media</h2>
            
            <input type="file" ref={fileInputRef} className="hidden" multiple accept="image/*" onChange={handleFileUpload} />
            <button onClick={() => fileInputRef.current?.click()} className="w-full py-3 border-2 border-dashed border-slate-300 rounded-xl text-slate-500 dark:text-slate-400 font-bold hover:bg-slate-50 dark:bg-slate-950 hover:border-brand hover:text-brand transition-colors flex items-center justify-center gap-2 mb-4">
              <Upload size={18} /> Upload Images
            </button>

            <div className="grid grid-cols-2 gap-3">
              {product.images.map((img, idx) => (
                <div key={idx} className={`relative rounded-lg overflow-hidden border-2 aspect-square group ${product.primary_image === img.image_url ? 'border-brand' : 'border-transparent'}`}>
                  <img src={img.image_url} className="w-full h-full object-cover" />
                  <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col justify-center items-center gap-2">
                    {product.primary_image !== img.image_url && (
                      <button onClick={() => setPrimary(img.image_url)} className="text-white text-xs font-bold bg-slate-800/80 px-2 py-1 rounded">Set Primary</button>
                    )}
                    <button onClick={() => removeImage(idx)} className="text-red-400 bg-white dark:bg-slate-900/10 p-1.5 rounded"><Trash2 size={16} /></button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Availability */}
          <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-800/50">
            <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 mb-4 pb-2 border-b border-slate-100 dark:border-slate-800/50">Availability</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Stock Status</label>
                <select name="stock_status" value={product.stock_status} onChange={handleInputChange} className="w-full px-4 py-2 border border-slate-200 dark:border-slate-800 rounded-lg outline-none bg-white dark:bg-slate-900">
                  <option value="IN_STOCK">In Stock</option>
                  <option value="OUT_OF_STOCK">Out of Stock</option>
                </select>
              </div>
              <label className="flex items-center gap-3 cursor-pointer">
                <input type="checkbox" name="is_active" checked={product.is_active} onChange={handleInputChange} className="w-5 h-5 rounded text-brand border-slate-300 focus:ring-brand" />
                <span className="font-bold text-slate-700 dark:text-slate-200">Product is Active</span>
              </label>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};

export default ProductEditor;
