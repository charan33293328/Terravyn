from database.connection import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE orders ADD COLUMN product_id INT NULL;"))
        conn.execute(text("ALTER TABLE orders ADD CONSTRAINT fk_order_product FOREIGN KEY (product_id) REFERENCES products(id);"))
        
        # Link existing orders to the default product (assumes product id 1 is the migrated one)
        conn.execute(text("UPDATE orders SET product_id = 1 WHERE product_id IS NULL;"))
        
        conn.commit()
    print("Column product_id added successfully to orders.")
except Exception as e:
    print(f"Error: {e}")
