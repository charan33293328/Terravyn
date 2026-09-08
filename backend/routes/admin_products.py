from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import os
import shutil
from datetime import datetime
from database.connection import get_db
from models.domain import Product, ProductImage, ProductSpecification, ProductFeature, PriceHistory, AuditLog, User, RoleEnum, Order
from schemas.product import ProductCreate, ProductUpdate, ProductPriceUpdate, ProductResponse, PriceHistoryResponse, ProductTemplateRequest
from auth.security import get_current_user

router = APIRouter(prefix="/api/admin/products", tags=["Admin Products"])

def check_admin(user: User):
    if user.role not in [RoleEnum.super_admin, RoleEnum.admin, RoleEnum.operations_manager]:
        raise HTTPException(status_code=403, detail="Not enough privileges")

def log_audit(db: Session, admin_id: int, action: str, resource: str):
    log = AuditLog(
        admin_id=admin_id,
        action=action,
        resource=resource
    )
    db.add(log)
    db.commit()

@router.get("", response_model=List[ProductResponse])
def get_products(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    return db.query(Product).order_by(Product.id.desc()).all()


FRONTEND_PUBLIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/public"))

def process_template_image(image_url: str, slug: str) -> str:
    if not image_url or not image_url.startswith("/images/templates/"):
        return image_url
        
    filename = os.path.basename(image_url)
    dest_dir = os.path.join(FRONTEND_PUBLIC_DIR, "images", "products", slug)
    os.makedirs(dest_dir, exist_ok=True)
    
    src_path = os.path.join(FRONTEND_PUBLIC_DIR, "images", "templates", filename)
    dest_path = os.path.join(dest_dir, filename)
    
    if os.path.exists(src_path):
        shutil.copy2(src_path, dest_path)
        
    return f"/images/products/{slug}/{filename}"

@router.post("", response_model=ProductResponse)
def create_product(prod_in: ProductCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    
    if db.query(Product).filter(Product.sku == prod_in.sku).first():
        raise HTTPException(status_code=400, detail="SKU already exists")
    if db.query(Product).filter(Product.slug == prod_in.slug).first():
        raise HTTPException(status_code=400, detail="Slug already exists")
        
    discount = 0.0
    if prod_in.mrp > 0:
        if prod_in.mrp < prod_in.current_price:
            raise HTTPException(status_code=400, detail="MRP cannot be less than selling price")
        discount = round(((prod_in.mrp - prod_in.current_price) / prod_in.mrp) * 100, 2)
        
    # Process template images
    prod_in.primary_image = process_template_image(prod_in.primary_image, prod_in.slug)
    for img in (prod_in.images or []):
        img.image_url = process_template_image(img.image_url, prod_in.slug)
        
    prod = Product(
        name=prod_in.name,
        slug=prod_in.slug,
        sku=prod_in.sku,
        short_description=prod_in.short_description,
        full_description=prod_in.full_description,
        category=prod_in.category,
        tagline=prod_in.tagline,
        current_price=prod_in.current_price,
        mrp=prod_in.mrp,
        discount_percentage=discount,
        tax_percentage=prod_in.tax_percentage,
        shipping_charges=prod_in.shipping_charges,
        primary_image=prod_in.primary_image,
        status=prod_in.status,
        is_active=prod_in.is_active,
        stock_status=prod_in.stock_status
    )
    db.add(prod)
    db.commit()
    db.refresh(prod)
    
    if prod_in.images:
        for img in prod_in.images:
            db.add(ProductImage(product_id=prod.id, image_url=img.image_url, display_order=img.display_order))
    if prod_in.specifications:
        for spec in prod_in.specifications:
            db.add(ProductSpecification(product_id=prod.id, key=spec.key, value=spec.value))
    if prod_in.features:
        for feat in prod_in.features:
            db.add(ProductFeature(product_id=prod.id, feature=feat.feature, display_order=feat.display_order))
            
    db.commit()
    
    log_audit(db, current_user.id, f"Created Product: {prod.sku}", "Product")
    
    hist = PriceHistory(
        product_id=prod.id,
        old_price=0,
        new_price=prod.current_price,
        old_mrp=0,
        new_mrp=prod.mrp,
        changed_by=current_user.id,
        reason="Initial Creation"
    )
    db.add(hist)
    db.commit()
    db.refresh(prod)
    
    return prod

@router.put("/{id}", response_model=ProductResponse)
def update_product(id: int, prod_in: ProductUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    prod = db.query(Product).filter(Product.id == id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
        
    if prod_in.sku and prod_in.sku != prod.sku:
        if db.query(Product).filter(Product.sku == prod_in.sku).first():
            raise HTTPException(status_code=400, detail="SKU already exists")
    if prod_in.slug and prod_in.slug != prod.slug:
        if db.query(Product).filter(Product.slug == prod_in.slug).first():
            raise HTTPException(status_code=400, detail="Slug already exists")
            
    update_data = prod_in.model_dump(exclude_unset=True)
    
    # Handle nested relationships explicitly if present
    if "images" in update_data:
        db.query(ProductImage).filter(ProductImage.product_id == id).delete()
        for img in update_data.pop("images"):
            db.add(ProductImage(product_id=id, image_url=img["image_url"], display_order=img["display_order"]))
            
    if "specifications" in update_data:
        db.query(ProductSpecification).filter(ProductSpecification.product_id == id).delete()
        for spec in update_data.pop("specifications"):
            db.add(ProductSpecification(product_id=id, key=spec["key"], value=spec["value"]))
            
    if "features" in update_data:
        db.query(ProductFeature).filter(ProductFeature.product_id == id).delete()
        for feat in update_data.pop("features"):
            db.add(ProductFeature(product_id=id, feature=feat["feature"], display_order=feat["display_order"]))
            
    for k, v in update_data.items():
        setattr(prod, k, v)
        
    db.commit()
    db.refresh(prod)
    log_audit(db, current_user.id, f"Updated Product Details: {prod.sku}", "Product")
    return prod

@router.put("/{id}/price", response_model=ProductResponse)
def update_product_price(id: int, price_in: ProductPriceUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    prod = db.query(Product).filter(Product.id == id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
        
    if price_in.current_price <= 0:
        raise HTTPException(status_code=400, detail="Selling price must be greater than 0")
        
    if price_in.mrp < price_in.current_price:
        raise HTTPException(status_code=400, detail="MRP cannot be less than selling price")
        
    old_price = prod.current_price
    old_mrp = prod.mrp
    
    latest_hist = db.query(PriceHistory).filter(PriceHistory.product_id == id, PriceHistory.effective_until == None).order_by(PriceHistory.id.desc()).first()
    if latest_hist:
        latest_hist.effective_until = datetime.utcnow()
        
    discount = 0.0
    if price_in.mrp > 0:
        discount = round(((price_in.mrp - price_in.current_price) / price_in.mrp) * 100, 2)
        
    prod.current_price = price_in.current_price
    prod.mrp = price_in.mrp
    prod.discount_percentage = discount
    
    new_hist = PriceHistory(
        product_id=prod.id,
        old_price=old_price,
        new_price=prod.current_price,
        old_mrp=old_mrp,
        new_mrp=prod.mrp,
        changed_by=current_user.id,
        reason=price_in.reason
    )
    db.add(new_hist)
    db.commit()
    db.refresh(prod)
    
    log_audit(db, current_user.id, f"Updated Product Price: {prod.sku} (₹{old_price} -> ₹{prod.current_price})", "Product")
    return prod

@router.put("/{id}/status", response_model=ProductResponse)
def update_product_status(id: int, is_active: bool, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    prod = db.query(Product).filter(Product.id == id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
        
    prod.is_active = is_active
    db.commit()
    db.refresh(prod)
    log_audit(db, current_user.id, f"Updated Product Active Status: {prod.sku} (Active: {is_active})", "Product")
    return prod

@router.put("/{id}/publish", response_model=ProductResponse)
def publish_product(id: int, status: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    if status not in ["DRAFT", "PUBLISHED", "ARCHIVED"]:
        raise HTTPException(status_code=400, detail="Invalid status")
        
    prod = db.query(Product).filter(Product.id == id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
        
    prod.status = status
    db.commit()
    db.refresh(prod)
    log_audit(db, current_user.id, f"Updated Product Status to {status}: {prod.sku}", "Product")
    return prod

@router.delete("/{id}")
def delete_product(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    prod = db.query(Product).filter(Product.id == id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
        
    sku = prod.sku
    
    # Unlink product from orders to prevent foreign key constraint violations
    orders = db.query(Order).filter(Order.product_id == prod.id).all()
    for order in orders:
        order.product_id = None
        
    db.delete(prod)
    db.commit()
    log_audit(db, current_user.id, f"Deleted Product: {sku}", "Product")
    return {"status": "success", "message": "Product deleted"}

@router.get("/{id}/price-history", response_model=List[PriceHistoryResponse])
def get_price_history(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    return db.query(PriceHistory).filter(PriceHistory.product_id == id).order_by(PriceHistory.created_at.desc()).all()

@router.post("/generate-template", response_model=ProductCreate)
def generate_product_template(req: ProductTemplateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    
    name = req.name
    category = req.category
    
    # 1. Base Configuration Mapping
    config = {
        "Smart Agriculture Device": {
            "prefix": "SAD",
            "image_prefix": "sad",
            "tagline": "Precision Insights for Modern Agriculture.",
            "short_desc": "A next-generation smart agriculture device designed to provide farmers with real-time field insights.",
            "full_desc": "The TERRAVYN Smart Agriculture Device is built for modern farming. It provides real-time data and integrates perfectly into the TERRAVYN ecosystem.\n\nKey Advantages:\n- Real-time monitoring\n- Cloud integration\n- Rugged, weather-proof design",
            "features": [
                "Real-Time Monitoring",
                "SIM Connectivity",
                "Remote Notifications",
                "Cloud Dashboard Integration",
                "QR-Based Activation",
                "ESP32 Architecture",
                "Weather Resistant Design"
            ],
            "specs": {
                "Processor": "ESP32",
                "Connectivity": "4G SIM + Wi-Fi",
                "Enclosure Rating": "IP67",
                "Power Source": "Solar + Battery Backup",
                "Provisioning": "QR-Based Activation",
                "Dashboard Support": "Web + Mobile"
            }
        },
        "Sensor Kit": {
            "prefix": "SEN",
            "image_prefix": "sensor",
            "tagline": "Accurate Sensor Data for Better Yields.",
            "short_desc": "A plug-and-play multi-sensor kit designed for precise agricultural monitoring.",
            "full_desc": "The TERRAVYN Sensor Kit provides accurate, multi-sensor data collection for any agricultural environment. Easily deployable with zero configuration.\n\nKey Advantages:\n- Plug-and-play installation\n- High accuracy calibration\n- Low power consumption",
            "features": [
                "Plug-and-Play Deployment",
                "Multi-Sensor Support",
                "Easy Calibration",
                "Low Power Consumption",
                "Weather Resistant Components"
            ],
            "specs": {
                "Sensor Type": "Multi-Sensor",
                "Interface": "Analog / Digital",
                "Calibration": "Supported",
                "Operating Temp": "-10°C to 60°C",
                "Ingress Protection": "IP65"
            }
        },
        "Water Monitoring Device": {
            "prefix": "WMD",
            "image_prefix": "water",
            "tagline": "Smart Water Insights for Sustainable Agriculture.",
            "short_desc": "Continuous water level and leak detection monitoring for agricultural applications.",
            "full_desc": "The TERRAVYN Water Monitoring Device ensures you never lose track of your water resources. From tank levels to field irrigation, it keeps you informed.\n\nKey Advantages:\n- Real-time water level alerts\n- Leak detection algorithms\n- Solar-powered continuous operation",
            "features": [
                "Water Level Monitoring",
                "Leak Detection",
                "Remote Alerts",
                "Cloud Dashboard Integration",
                "Continuous Monitoring"
            ],
            "specs": {
                "Monitoring Type": "Water Level",
                "Connectivity": "4G SIM",
                "Dashboard Support": "Web + Mobile",
                "Alerting": "SMS + Dashboard",
                "Power Source": "Solar + Battery"
            }
        },
        "Weather Monitoring Device": {
            "prefix": "WX",
            "image_prefix": "weather",
            "tagline": "Real-Time Weather Intelligence for Your Farm.",
            "short_desc": "A complete weather station providing hyper-local climate data and forecasts.",
            "full_desc": "The TERRAVYN Weather Station monitors rain, temperature, and humidity, helping you make informed decisions based on hyper-local weather patterns.\n\nKey Advantages:\n- Hyper-local weather data\n- Historical trends analysis\n- Automated forecasting",
            "features": [
                "Rain Monitoring",
                "Temperature Monitoring",
                "Humidity Monitoring",
                "Weather Forecast Insights",
                "Historical Trends"
            ],
            "specs": {
                "Rain Sensor": "Included",
                "Temperature Range": "-20°C to 80°C",
                "Humidity Range": "0–100%",
                "Connectivity": "4G SIM",
                "Dashboard Support": "Web + Mobile"
            }
        },
        "Pest Management Device": {
            "prefix": "PMD",
            "image_prefix": "pest",
            "tagline": "Eco-Friendly Pest Defense and Detection.",
            "short_desc": "Automated pest detection and repellent system to protect your valuable crops.",
            "full_desc": "The TERRAVYN Pest Defender uses automated detection to keep pests away without harmful chemicals. Get alerts when activity is detected.\n\nKey Advantages:\n- Eco-friendly repellent\n- Automated detection\n- Remote field alerts",
            "features": [
                "Pest Detection",
                "Repellent Automation",
                "Field Alerts",
                "Eco-Friendly Operation",
                "Remote Monitoring"
            ],
            "specs": {
                "Detection Type": "Automated",
                "Coverage Area": "Configurable",
                "Power Source": "Solar",
                "Connectivity": "4G SIM",
                "Alerting": "Mobile Dashboard"
            }
        },
        "Expansion Module": {
            "prefix": "EXP",
            "image_prefix": "exp",
            "tagline": "Expand Your TERRAVYN Ecosystem.",
            "short_desc": "Add more capabilities and sensor support to your existing TERRAVYN devices.",
            "full_desc": "The TERRAVYN Expansion Module allows you to easily plug in additional sensors and features to your main device.\n\nKey Advantages:\n- Modular design\n- Seamless integration\n- IP65 rated housing",
            "features": [
                "Additional Sensor Support",
                "Modular Design",
                "Easy Integration",
                "Weather Resistant Housing"
            ],
            "specs": {
                "Expansion Ports": "Multiple",
                "Compatibility": "TERRAVYN Devices",
                "Enclosure Rating": "IP65",
                "Power Input": "Standardized"
            }
        },
        "Subscription Service": {
            "prefix": "SUB",
            "image_prefix": "sub",
            "tagline": "Unlock the Full Power of TERRAVYN.",
            "short_desc": "Premium subscription unlocking advanced analytics, priority support, and unlimited devices.",
            "full_desc": "A TERRAVYN Premium Subscription provides you with the ultimate farm management tools, predictive insights, and historical reporting.\n\nKey Advantages:\n- Predictive analytics\n- Advanced historical reports\n- Priority customer support",
            "features": [
                "Advanced Analytics",
                "Priority Support",
                "Unlimited Devices",
                "Historical Reports",
                "Predictive Insights"
            ],
            "specs": {
                "Billing Cycle": "Annual",
                "Dashboard Access": "Premium",
                "Reports": "Advanced",
                "Support": "Priority"
            }
        }
    }
    
    base = config.get(category, {
        "prefix": "GEN",
        "image_prefix": "generic",
        "tagline": "Precision Insights for Modern Agriculture.",
        "short_desc": "A generic product template.",
        "full_desc": "A TERRAVYN generic product.",
        "features": [],
        "specs": {}
    })
    
    features = list(base["features"])
    specs_dict = dict(base["specs"])
    
    # 2. Name Intelligence overrides
    name_lower = name.lower()
    if "soil" in name_lower:
        if "Soil Moisture Monitoring" not in features:
            features.append("Soil Moisture Monitoring")
        if "Nutrient Monitoring" not in features:
            features.append("Nutrient Monitoring")
        specs_dict["Soil Compatibility"] = "Supported"
        specs_dict["Moisture Detection"] = "Included"
        
    if "weather" in name_lower:
        if "Rain Alerts" not in features:
            features.append("Rain Alerts")
        if "Temperature Trends" not in features:
            features.append("Temperature Trends")
            
    if "water" in name_lower:
        if "Irrigation Monitoring" not in features:
            features.append("Irrigation Monitoring")
        if "Tank Monitoring" not in features:
            features.append("Tank Monitoring")

    # 3. Format Features and Specs for Database
    final_features = [{"feature": f, "display_order": idx+1} for idx, f in enumerate(features)]
    final_specs = [{"key": k, "value": v} for k, v in specs_dict.items()]

    # 4. SKU Generation
    prefix = f"TRV-{base['prefix']}-"
    existing = db.query(Product).filter(Product.sku.like(f"{prefix}%")).all()
    max_seq = 0
    for p in existing:
        try:
            seq = int(p.sku.split("-")[-1])
            if seq > max_seq: max_seq = seq
        except:
            pass
    sku = f"{prefix}{(max_seq + 1):03d}"
    
    # 5. Slug
    import re
    base_slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    slug = base_slug
    counter = 1
    while db.query(Product).filter(Product.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
        
    # 6. Images
    # Use actual stored images from the system rather than generic templates
    stored_images_map = {
        "Smart Agriculture Device": ["terravyn_front.png", "terravyn_angle.png", "terravyn_field.png"],
        "Sensor Kit": ["terravyn_sensors.png", "prod_6fb7d73b.png", "prod_7078ec15.png"],
        "Water Monitoring Device": ["prod_86ac412d.png", "terravyn_field.png", "terravyn_packaging.png"],
        "Weather Monitoring Device": ["terravyn_angle.png", "prod_b9a077da.png", "terravyn_field.png"],
        "Pest Management Device": ["prod_6fb7d73b.png", "terravyn_front.png", "prod_86ac412d.png"],
        "Expansion Module": ["prod_7078ec15.png", "terravyn_sensors.png", "terravyn_packaging.png"],
        "Subscription Service": ["prod_b9a077da.png", "terravyn_front.png", "terravyn_angle.png"]
    }
    
    selected_images = stored_images_map.get(category, ["terravyn_front.png", "terravyn_angle.png", "terravyn_field.png"])
    
    images = [
        {"image_url": f"/images/products/terravyn/{img}", "display_order": idx + 1}
        for idx, img in enumerate(selected_images)
    ]
    primary_img = f"/images/products/terravyn/{selected_images[0]}"
    
    return {
        "name": name,
        "category": category,
        "sku": sku,
        "slug": slug,
        "tagline": base["tagline"],
        "short_description": base["short_desc"],
        "full_description": base["full_desc"],
        "current_price": 14999.0,
        "mrp": 19999.0,
        "discount_percentage": 25.0,
        "tax_percentage": 18.0,
        "shipping_charges": 0.0,
        "primary_image": primary_img,
        "status": "DRAFT",
        "is_active": True,
        "stock_status": "IN_STOCK",
        "features": final_features,
        "specifications": final_specs,
        "images": images
    }
