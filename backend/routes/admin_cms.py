import os
import shutil
import uuid
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from database.connection import get_db
from models.domain import User, RoleEnum, CMSPage, FAQ, BlogPost, MediaAsset, ContentRevision
from auth.security import get_current_user
from schemas.cms import (
    CMSPageCreate, CMSPageUpdate, CMSPageResponse,
    FAQCreate, FAQUpdate, FAQResponse,
    BlogPostCreate, BlogPostUpdate, BlogPostResponse,
    MediaAssetResponse
)

# Ensure directories exist
MEDIA_BASE = "static/media"
for folder in ["images", "videos", "documents", "thumbnails", "blog"]:
    os.makedirs(os.path.join(MEDIA_BASE, folder), exist_ok=True)

router = APIRouter(prefix="/api/admin/cms", tags=["Admin CMS"])

def check_admin(user: User):
    if user.role not in [RoleEnum.super_admin, RoleEnum.admin]:
        raise HTTPException(status_code=403, detail="Not enough privileges")

def create_revision(db: Session, entity_type: str, entity_id: int, editor_id: int, snapshot: dict, summary: str = None):
    # Get latest version number
    latest = db.query(ContentRevision).filter(
        ContentRevision.entity_type == entity_type,
        ContentRevision.entity_id == entity_id
    ).order_by(ContentRevision.version_number.desc()).first()
    
    version = 1 if not latest else latest.version_number + 1
    
    rev = ContentRevision(
        entity_type=entity_type,
        entity_id=entity_id,
        editor_id=editor_id,
        change_summary=summary,
        version_number=version,
        snapshot_data=snapshot
    )
    db.add(rev)
    db.commit()

# --- PAGES API ---

@router.get("/pages", response_model=List[CMSPageResponse])
def get_pages(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    return db.query(CMSPage).all()

@router.get("/pages/{page_identifier}", response_model=CMSPageResponse)
def get_page(page_identifier: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    page = db.query(CMSPage).filter(CMSPage.page_identifier == page_identifier).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return page

@router.post("/pages", response_model=CMSPageResponse)
def create_page(page_in: CMSPageCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    
    # Check exists
    if db.query(CMSPage).filter(CMSPage.page_identifier == page_in.page_identifier).first():
        raise HTTPException(status_code=400, detail="Page identifier already exists")
        
    page = CMSPage(
        page_identifier=page_in.page_identifier,
        content_data=page_in.content_data,
        status=page_in.status,
        updated_by=current_user.id
    )
    db.add(page)
    db.commit()
    db.refresh(page)
    
    create_revision(db, "CMSPage", page.id, current_user.id, page_in.content_data, "Initial creation")
    return page

@router.put("/pages/{id}", response_model=CMSPageResponse)
def update_page(id: int, page_in: CMSPageUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    page = db.query(CMSPage).filter(CMSPage.id == id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
        
    page.content_data = page_in.content_data
    if page_in.status:
        page.status = page_in.status
    page.updated_by = current_user.id
    db.commit()
    db.refresh(page)
    
    create_revision(db, "CMSPage", page.id, current_user.id, page_in.content_data, "Update page content")
    return page

# --- FAQS API ---

@router.get("/faqs", response_model=List[FAQResponse])
def get_faqs(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    return db.query(FAQ).order_by(FAQ.display_order.asc()).all()

@router.post("/faqs", response_model=FAQResponse)
def create_faq(faq_in: FAQCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    faq = FAQ(**faq_in.model_dump())
    db.add(faq)
    db.commit()
    db.refresh(faq)
    return faq

@router.put("/faqs/{id}", response_model=FAQResponse)
def update_faq(id: int, faq_in: FAQUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    faq = db.query(FAQ).filter(FAQ.id == id).first()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")
        
    for k, v in faq_in.model_dump(exclude_unset=True).items():
        setattr(faq, k, v)
        
    db.commit()
    db.refresh(faq)
    return faq

@router.delete("/faqs/{id}")
def delete_faq(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    faq = db.query(FAQ).filter(FAQ.id == id).first()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")
    db.delete(faq)
    db.commit()
    return {"message": "Deleted"}

# --- BLOG API ---

@router.get("/blog", response_model=List[BlogPostResponse])
def get_blogs(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    return db.query(BlogPost).order_by(BlogPost.created_at.desc()).all()

@router.post("/blog", response_model=BlogPostResponse)
def create_blog(blog_in: BlogPostCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    blog = BlogPost(**blog_in.model_dump(), author_id=current_user.id)
    db.add(blog)
    db.commit()
    db.refresh(blog)
    return blog

@router.put("/blog/{id}", response_model=BlogPostResponse)
def update_blog(id: int, blog_in: BlogPostUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    blog = db.query(BlogPost).filter(BlogPost.id == id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog post not found")
        
    for k, v in blog_in.model_dump(exclude_unset=True).items():
        setattr(blog, k, v)
        
    db.commit()
    db.refresh(blog)
    return blog

@router.delete("/blog/{id}")
def delete_blog(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    blog = db.query(BlogPost).filter(BlogPost.id == id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog post not found")
    db.delete(blog)
    db.commit()
    return {"message": "Deleted"}

# --- MEDIA API ---

@router.get("/media", response_model=List[MediaAssetResponse])
def get_media(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    return db.query(MediaAsset).order_by(MediaAsset.uploaded_at.desc()).all()

@router.post("/media", response_model=MediaAssetResponse)
async def upload_media(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    check_admin(current_user)
    
    # Determine folder based on content type
    folder = "documents"
    if file.content_type.startswith("image/"):
        folder = "images"
    elif file.content_type.startswith("video/"):
        folder = "videos"
        
    # Generate unique filename
    ext = os.path.splitext(file.filename)[1]
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(MEDIA_BASE, folder, unique_name)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    file_size = os.path.getsize(file_path)
    
    # URL path for frontend
    url_path = f"/static/media/{folder}/{unique_name}"
    
    asset = MediaAsset(
        file_name=file.filename,
        file_path=url_path,
        file_type=file.content_type,
        file_size=file_size,
        uploaded_by=current_user.id
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    
    return asset

@router.delete("/media/{id}")
def delete_media(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    asset = db.query(MediaAsset).filter(MediaAsset.id == id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Media not found")
        
    # Delete from filesystem
    fs_path = asset.file_path.lstrip("/") # remove leading slash
    if os.path.exists(fs_path):
        os.remove(fs_path)
        
    db.delete(asset)
    db.commit()
    return {"message": "Deleted"}
