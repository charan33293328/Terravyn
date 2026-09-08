from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

# Media Asset
class MediaAssetBase(BaseModel):
    file_name: str
    file_type: str
    file_size: int

class MediaAssetCreate(MediaAssetBase):
    file_path: str

class MediaAssetResponse(MediaAssetBase):
    id: int
    file_path: str
    uploaded_by: Optional[int] = None
    uploaded_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# FAQ
class FAQBase(BaseModel):
    question: str
    answer: str
    category: Optional[str] = None
    display_order: int = 0
    status: str = "PUBLISHED"
    translations: Optional[Dict[str, Any]] = None

class FAQCreate(FAQBase):
    pass

class FAQUpdate(FAQBase):
    pass

class FAQResponse(FAQBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# BlogPost
class BlogPostBase(BaseModel):
    title: str
    slug: str
    featured_image: Optional[str] = None
    content: str
    tags: Optional[List[str]] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    status: str = "DRAFT"
    publish_date: Optional[datetime] = None
    translations: Optional[Dict[str, Any]] = None

class BlogPostCreate(BlogPostBase):
    pass

class BlogPostUpdate(BlogPostBase):
    pass

class BlogPostResponse(BlogPostBase):
    id: int
    author_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# CMS Page
class CMSPageBase(BaseModel):
    page_identifier: str
    content_data: Dict[str, Any]
    status: str = "PUBLISHED"

class CMSPageCreate(CMSPageBase):
    pass

class CMSPageUpdate(BaseModel):
    content_data: Dict[str, Any]
    status: Optional[str] = None

class CMSPageResponse(CMSPageBase):
    id: int
    updated_by: Optional[int] = None
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Content Revision
class ContentRevisionResponse(BaseModel):
    id: int
    entity_type: str
    entity_id: int
    editor_id: Optional[int] = None
    change_summary: Optional[str] = None
    version_number: int
    snapshot_data: Dict[str, Any]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
