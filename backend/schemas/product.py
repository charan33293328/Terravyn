from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ProductImageBase(BaseModel):
    image_url: str
    display_order: int = 0

class ProductImageCreate(ProductImageBase):
    pass

class ProductImageResponse(ProductImageBase):
    id: int
    product_id: int
    
    class Config:
        from_attributes = True

class ProductSpecificationBase(BaseModel):
    key: str
    value: str

class ProductSpecificationCreate(ProductSpecificationBase):
    pass

class ProductSpecificationResponse(ProductSpecificationBase):
    id: int
    product_id: int
    
    class Config:
        from_attributes = True

class ProductFeatureBase(BaseModel):
    feature: str
    display_order: int = 0

class ProductFeatureCreate(ProductFeatureBase):
    pass

class ProductFeatureResponse(ProductFeatureBase):
    id: int
    product_id: int
    
    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    name: str
    slug: str
    sku: str
    short_description: Optional[str] = None
    full_description: Optional[str] = None
    category: Optional[str] = None
    tagline: Optional[str] = None
    
    current_price: float
    mrp: float
    discount_percentage: float = 0.0
    tax_percentage: float = 0.0
    shipping_charges: float = 0.0
    
    primary_image: Optional[str] = None
    status: str = "DRAFT" # DRAFT, PUBLISHED, ARCHIVED
    is_active: bool = True
    stock_status: str = "IN_STOCK"

class ProductTemplateRequest(BaseModel):
    name: str
    category: str

class ProductCreate(ProductBase):
    images: Optional[List[ProductImageCreate]] = []
    specifications: Optional[List[ProductSpecificationCreate]] = []
    features: Optional[List[ProductFeatureCreate]] = []

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    sku: Optional[str] = None
    short_description: Optional[str] = None
    full_description: Optional[str] = None
    category: Optional[str] = None
    tagline: Optional[str] = None
    current_price: Optional[float] = None
    mrp: Optional[float] = None
    discount_percentage: Optional[float] = None
    tax_percentage: Optional[float] = None
    shipping_charges: Optional[float] = None
    primary_image: Optional[str] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None
    stock_status: Optional[str] = None
    
    # We will accept these lists to completely replace existing ones on update
    images: Optional[List[ProductImageCreate]] = None
    specifications: Optional[List[ProductSpecificationCreate]] = None
    features: Optional[List[ProductFeatureCreate]] = None

class ProductPriceUpdate(BaseModel):
    current_price: float
    mrp: float
    reason: str

class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    images: List[ProductImageResponse] = []
    specifications: List[ProductSpecificationResponse] = []
    features: List[ProductFeatureResponse] = []
    
    class Config:
        from_attributes = True

class PriceHistoryResponse(BaseModel):
    id: int
    product_id: int
    old_price: float
    new_price: float
    old_mrp: float
    new_mrp: float
    changed_by: Optional[int] = None
    reason: Optional[str] = None
    effective_from: datetime
    effective_until: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
