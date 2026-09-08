from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database.connection import get_db
from models.domain import Product
from schemas.product import ProductResponse

router = APIRouter(prefix="/api/public/products", tags=["Public Products"])

@router.get("", response_model=List[ProductResponse])
def get_public_products(db: Session = Depends(get_db)):
    # Return only active and PUBLISHED products
    return db.query(Product).filter(Product.is_active == True, Product.status == "PUBLISHED").all()

@router.get("/{slug}", response_model=ProductResponse)
def get_public_product(slug: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.slug == slug, Product.is_active == True, Product.status == "PUBLISHED").first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or inactive")
    return product
