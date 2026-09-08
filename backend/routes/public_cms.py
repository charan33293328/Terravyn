"""
Public CMS API – No authentication required.
Returns only PUBLISHED content. Used by the public-facing website.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database.connection import get_db
from models.domain import CMSPage, FAQ, BlogPost, PlatformSettings

router = APIRouter(prefix="/api/public", tags=["Public CMS"])


def get_lang_fallback(obj_dict: dict, lang: str, fields: list) -> dict:
    """
    For a content_data dict structured as { 'en': {...}, 'te': {...}, ... },
    return the requested lang's fields, falling back to English for missing keys.
    """
    en_data = obj_dict.get("en", {})
    lang_data = obj_dict.get(lang, {}) if lang != "en" else {}

    result = {}
    for f in fields:
        val = lang_data.get(f) or en_data.get(f)
        result[f] = val
    return result


# ─── Homepage / Landing Page ─────────────────────────────────────────────────

@router.get("/cms/homepage")
def get_homepage(
    lang: str = Query("en", max_length=10),
    db: Session = Depends(get_db)
):
    page = db.query(CMSPage).filter(
        CMSPage.page_identifier == "landing_page",
        CMSPage.status == "PUBLISHED"
    ).first()

    if not page or not page.content_data:
        return {"lang": lang, "source": "default", "data": {}}

    content = page.content_data

    # Resolve language with English fallback
    fields = [
        "heroTitle", "heroSubtitle", "ctaText", "ctaUrl", "heroVideo",
        "howItWorksTitle", "howItWorksDesc", "howItWorksVideo", "howItWorksThumbnail"
    ]
    resolved = get_lang_fallback(content, lang, fields)

    # Features are global (not per-language)
    resolved["features"] = content.get("features", [])

    return {
        "lang": lang,
        "source": "cms",
        "updated_at": page.updated_at.isoformat() if page.updated_at else None,
        "data": resolved
    }


# ─── FAQs ────────────────────────────────────────────────────────────────────

@router.get("/cms/faqs")
def get_public_faqs(
    lang: str = Query("en", max_length=10),
    category: str = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(FAQ).filter(FAQ.status == "PUBLISHED")
    if category:
        query = query.filter(FAQ.category == category)
    faqs = query.order_by(FAQ.display_order.asc()).all()

    result = []
    for faq in faqs:
        translations = faq.translations or {}
        lang_data = translations.get(lang, {}) if lang != "en" else {}

        question = lang_data.get("question") or faq.question
        answer = lang_data.get("answer") or faq.answer

        result.append({
            "id": faq.id,
            "question": question,
            "answer": answer,
            "category": faq.category,
            "display_order": faq.display_order
        })

    return result


# ─── Blog Posts ───────────────────────────────────────────────────────────────

@router.get("/cms/blog")
def get_public_blog(
    lang: str = Query("en", max_length=10),
    limit: int = Query(10, ge=1, le=50),
    skip: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    posts = (
        db.query(BlogPost)
        .filter(BlogPost.status == "PUBLISHED")
        .order_by(BlogPost.publish_date.desc(), BlogPost.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    result = []
    for post in posts:
        translations = post.translations or {}
        lang_data = translations.get(lang, {}) if lang != "en" else {}

        result.append({
            "id": post.id,
            "slug": post.slug,
            "title": lang_data.get("title") or post.title,
            "content": lang_data.get("content") or post.content,
            "featured_image": post.featured_image,
            "tags": post.tags or [],
            "seo_title": post.seo_title,
            "seo_description": post.seo_description,
            "publish_date": post.publish_date.isoformat() if post.publish_date else None,
            "created_at": post.created_at.isoformat() if post.created_at else None
        })

    return result


@router.get("/cms/blog/{slug}")
def get_public_blog_post(
    slug: str,
    lang: str = Query("en", max_length=10),
    db: Session = Depends(get_db)
):
    post = db.query(BlogPost).filter(
        BlogPost.slug == slug,
        BlogPost.status == "PUBLISHED"
    ).first()

    if not post:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Post not found")

    translations = post.translations or {}
    lang_data = translations.get(lang, {}) if lang != "en" else {}

    return {
        "id": post.id,
        "slug": post.slug,
        "title": lang_data.get("title") or post.title,
        "content": lang_data.get("content") or post.content,
        "featured_image": post.featured_image,
        "tags": post.tags or [],
        "seo_title": post.seo_title,
        "seo_description": post.seo_description,
        "publish_date": post.publish_date.isoformat() if post.publish_date else None,
        "created_at": post.created_at.isoformat() if post.created_at else None
    }


# ─── Legal Pages ─────────────────────────────────────────────────────────────

@router.get("/cms/legal/{page_slug}")
def get_legal_page(
    page_slug: str,
    lang: str = Query("en", max_length=10),
    db: Session = Depends(get_db)
):
    page = db.query(CMSPage).filter(
        CMSPage.page_identifier == page_slug,
        CMSPage.status == "PUBLISHED"
    ).first()

    if not page:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Page not found")

    content = page.content_data or {}
    translations = content.get("translations", {})
    lang_data = translations.get(lang, {}) if lang != "en" else {}
    en_data = translations.get("en", {})

    return {
        "page_identifier": page.page_identifier,
        "lang": lang,
        "title": lang_data.get("title") or en_data.get("title") or page_slug.replace("_", " ").title(),
        "content": lang_data.get("content") or en_data.get("content") or content.get("content", ""),
        "updated_at": page.updated_at.isoformat() if page.updated_at else None
    }


# ─── How It Works ─────────────────────────────────────────────────────────────

@router.get("/cms/how-it-works")
def get_how_it_works(
    lang: str = Query("en", max_length=10),
    db: Session = Depends(get_db)
):
    page = db.query(CMSPage).filter(
        CMSPage.page_identifier == "landing_page",
        CMSPage.status == "PUBLISHED"
    ).first()

    if not page or not page.content_data:
        return {"lang": lang, "source": "default", "data": {}}

    content = page.content_data
    fields = ["howItWorksTitle", "howItWorksDesc", "howItWorksVideo", "howItWorksThumbnail"]
    resolved = get_lang_fallback(content, lang, fields)

    return {"lang": lang, "source": "cms", "data": resolved}


# ─── Platform Settings (public subset) ───────────────────────────────────────

@router.get("/settings")
def get_public_settings(db: Session = Depends(get_db)):
    settings = db.query(PlatformSettings).first()
    if not settings:
        return {
            "platform_name": "TERRAVYN",
            "company_name": "TERRAVYN Pvt Ltd",
            "support_email": None,
            "support_phone": None,
            "default_language": "en"
        }

    return {
        "platform_name": settings.platform_name or "TERRAVYN",
        "company_name": settings.company_name or "TERRAVYN Pvt Ltd",
        "support_email": settings.support_email,
        "support_phone": settings.support_phone,
        "default_language": settings.default_language or "en"
    }
