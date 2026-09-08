import sys

with open("admin_products.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Import os, shutil
content = content.replace("from typing import List", "from typing import List\nimport os\nimport shutil")

# 2. Add process_template_image logic before create_product
process_img_logic = """
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

@router.post("", response_model=ProductResponse)"""

content = content.replace("@router.post(\"\", response_model=ProductResponse)\ndef create_product", process_img_logic + "\ndef create_product")

# 3. Modify create_product to use process_template_image
old_create_prod = """    prod = Product(
        name=prod_in.name,"""

new_create_prod = """    # Process template images
    prod_in.primary_image = process_template_image(prod_in.primary_image, prod_in.slug)
    for img in (prod_in.images or []):
        img.image_url = process_template_image(img.image_url, prod_in.slug)
        
    prod = Product(
        name=prod_in.name,"""

content = content.replace(old_create_prod, new_create_prod)

# 4. Add generate_template endpoint at the end
generator_logic = """
@router.post("/generate-template", response_model=ProductCreate)
def generate_product_template(req: ProductTemplateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    
    name = req.name
    category = req.category
    
    # 1. Determine Tagline
    tagline = f"Intelligent Farming Through {name} Monitoring."
    if "Water" in name:
        tagline = "Smart Water Insights for Sustainable Agriculture."
    elif "Sensor" in name:
        tagline = "Precision Insights for Modern Agriculture."
        
    # 2. Descriptions
    short_description = f"A next-generation agricultural monitoring solution designed to provide farmers with real-time insights and enhanced field visibility through intelligent sensor integration."
    full_description = f"The {name} is built for modern farming. Purpose-built to provide real-time data, it integrates perfectly into the TERRAVYN ecosystem.\\n\\nKey Advantages:\\n- Real-time precision\\n- Seamless dashboard integration\\n- Rugged, weather-proof design for outdoor use."
    
    # 3. Features
    features = [
        {"feature": "Real-Time Monitoring", "display_order": 1},
        {"feature": "SIM Connectivity", "display_order": 2},
        {"feature": "Remote Notifications", "display_order": 3},
        {"feature": "Weather Resistant Design", "display_order": 4},
        {"feature": "ESP32-Based Architecture", "display_order": 5},
        {"feature": "Cloud Dashboard Integration", "display_order": 6},
        {"feature": "Scalable Deployment", "display_order": 7},
        {"feature": "Secure Device Provisioning", "display_order": 8}
    ]
    
    # 4. Specifications
    specs = [
        {"key": "Connectivity", "value": "4G SIM / Wi-Fi"},
        {"key": "Processor", "value": "ESP32"},
        {"key": "Power Source", "value": "Solar + Battery Backup"},
        {"key": "Enclosure Rating", "value": "IP67"},
        {"key": "Operating Temp", "value": "-10°C to 60°C"},
        {"key": "Dashboard Support", "value": "Web + Mobile"},
        {"key": "Provisioning", "value": "QR-Based Activation"},
        {"key": "Sensor Expansion", "value": "Supported"}
    ]
    
    # 5. SKU Generation
    prefix = "TRV-"
    if "Agriculture" in category:
        prefix += "SAD-"
    elif "Water" in category:
        prefix += "WMD-"
    elif "Sensor" in category:
        prefix += "SEN-"
    elif "Expansion" in category:
        prefix += "EXP-"
    else:
        prefix += "GEN-"
        
    # Find max sequence
    existing = db.query(Product).filter(Product.sku.like(f"{prefix}%")).all()
    max_seq = 0
    for p in existing:
        try:
            seq = int(p.sku.split("-")[-1])
            if seq > max_seq: max_seq = seq
        except:
            pass
    
    sku = f"{prefix}{(max_seq + 1):03d}"
    
    # 6. Slug
    import re
    base_slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    slug = base_slug
    counter = 1
    while db.query(Product).filter(Product.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
        
    # 7. Images
    images = [
        {"image_url": "/images/templates/front.png", "display_order": 1},
        {"image_url": "/images/templates/perspective.png", "display_order": 2},
        {"image_url": "/images/templates/field.png", "display_order": 3}
    ]
    
    return {
        "name": name,
        "category": category,
        "sku": sku,
        "slug": slug,
        "tagline": tagline,
        "short_description": short_description,
        "full_description": full_description,
        "current_price": 14999.0,
        "mrp": 19999.0,
        "discount_percentage": 25.0,
        "tax_percentage": 18.0,
        "shipping_charges": 0.0,
        "primary_image": "/images/templates/front.png",
        "status": "DRAFT",
        "is_active": True,
        "stock_status": "IN_STOCK",
        "features": features,
        "specifications": specs,
        "images": images
    }
"""

content += generator_logic

with open("admin_products.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Updated admin_products.py")
