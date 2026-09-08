import os
import sys

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import Base
from models.domain import Product
from database.connection import settings

def migrate():
    print("Starting Phase 7 Pricing Migration...")
    
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    print("Creating new Pricing tables...")
    Base.metadata.create_all(bind=engine)
    
    print("Checking for existing default product...")
    default_product = session.query(Product).filter(Product.sku == "TRV-SMART-AG-01").first()
    
    if not default_product:
        print("Seeding default TERRAVYN Smart Agriculture System...")
        new_product = Product(
            name="TERRAVYN Smart Agriculture System",
            sku="TRV-SMART-AG-01",
            description="An AI-powered smart agriculture solution designed to automate irrigation, monitor environmental conditions, and help farmers improve productivity while conserving resources.",
            current_price=14999.0,
            mrp=18000.0,
            discount_percentage=16.67,
            is_active=True,
            stock_status="IN_STOCK"
        )
        session.add(new_product)
        session.commit()
        print("Default product seeded successfully.")
    else:
        print("Default product already exists.")
        
    print("Phase 7 Pricing Migration completed successfully.")
    session.close()

if __name__ == "__main__":
    migrate()
