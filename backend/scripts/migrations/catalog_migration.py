import json
from sqlalchemy import create_engine, text
from database.connection import engine
import time

def run_migration():
    print("Starting Product Catalog database migration...")
    
    with engine.connect() as conn:
        print("1. Extending products table...")
        # Check if columns exist and add them
        try:
            conn.execute(text("ALTER TABLE products ADD COLUMN slug VARCHAR(255) UNIQUE;"))
            print("Added slug")
        except Exception as e:
            print(f"slug might exist: {e}")
            
        try:
            conn.execute(text("ALTER TABLE products ADD COLUMN short_description TEXT;"))
            print("Added short_description")
        except Exception as e:
            pass
            
        try:
            conn.execute(text("ALTER TABLE products ADD COLUMN full_description TEXT;"))
            print("Added full_description")
        except Exception as e:
            pass
            
        try:
            conn.execute(text("ALTER TABLE products ADD COLUMN category VARCHAR(100);"))
            print("Added category")
        except Exception as e:
            pass
            
        try:
            conn.execute(text("ALTER TABLE products ADD COLUMN tagline VARCHAR(255);"))
            print("Added tagline")
        except Exception as e:
            pass
            
        try:
            conn.execute(text("ALTER TABLE products ADD COLUMN tax_percentage FLOAT DEFAULT 0.0;"))
            print("Added tax_percentage")
        except Exception as e:
            pass
            
        try:
            conn.execute(text("ALTER TABLE products ADD COLUMN shipping_charges FLOAT DEFAULT 0.0;"))
            print("Added shipping_charges")
        except Exception as e:
            pass
            
        try:
            conn.execute(text("ALTER TABLE products ADD COLUMN primary_image VARCHAR(255);"))
            print("Added primary_image")
        except Exception as e:
            pass
            
        try:
            conn.execute(text("ALTER TABLE products ADD COLUMN status VARCHAR(50) DEFAULT 'DRAFT';"))
            print("Added status")
        except Exception as e:
            pass
            
        conn.commit()

        print("2. Creating new tables...")
        # Create tables explicitly
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS product_images (
            id INT AUTO_INCREMENT PRIMARY KEY,
            product_id INT NOT NULL,
            image_url VARCHAR(255) NOT NULL,
            display_order INT DEFAULT 0,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
        );
        """))
        
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS product_specifications (
            id INT AUTO_INCREMENT PRIMARY KEY,
            product_id INT NOT NULL,
            `key` VARCHAR(255) NOT NULL,
            value VARCHAR(255) NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
        );
        """))
        
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS product_features (
            id INT AUTO_INCREMENT PRIMARY KEY,
            product_id INT NOT NULL,
            feature VARCHAR(255) NOT NULL,
            display_order INT DEFAULT 0,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
        );
        """))
        conn.commit()

        print("3. Migrating existing data...")
        # Get existing products
        result = conn.execute(text("SELECT id, name, description, images FROM products"))
        products = result.mappings().all()
        
        for p in products:
            product_id = p['id']
            # Set default new fields
            # Generate slug from name
            slug = str(p['name']).lower().replace(" ", "-").replace("/", "-")
            if not slug:
                slug = f"product-{product_id}"
                
            conn.execute(text("""
                UPDATE products 
                SET slug = :slug,
                    status = 'PUBLISHED',
                    short_description = :desc,
                    full_description = :desc
                WHERE id = :id AND status IS NULL
            """), {"slug": slug, "desc": p['description'], "id": product_id})
            
            # If the database doesn't enforce JSON strictly, images might be string or list.
            images_data = p.get('images')
            image_list = []
            if isinstance(images_data, str):
                try:
                    image_list = json.loads(images_data)
                except:
                    pass
            elif isinstance(images_data, list):
                image_list = images_data
            
            # Also check if it's already migrated (has images in product_images)
            existing_imgs = conn.execute(text("SELECT count(*) as c FROM product_images WHERE product_id = :id"), {"id": product_id}).fetchone()
            if existing_imgs[0] == 0 and image_list:
                for idx, img_url in enumerate(image_list):
                    if idx == 0:
                        # set as primary
                        conn.execute(text("UPDATE products SET primary_image = :img WHERE id = :id"), {"img": img_url, "id": product_id})
                    
                    conn.execute(text("INSERT INTO product_images (product_id, image_url, display_order) VALUES (:id, :img, :order)"), 
                                 {"id": product_id, "img": img_url, "order": idx})
        
        conn.commit()
        print("Migration completed successfully.")

if __name__ == "__main__":
    run_migration()
