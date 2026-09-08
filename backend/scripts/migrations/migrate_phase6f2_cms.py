import os
import sys

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from app.main import Base
from models.domain import CMSPage, FAQ, BlogPost, MediaAsset, ContentRevision
from database.connection import settings

def migrate():
    print("Starting Phase 6F.2 CMS Migration...")
    
    # Use the live database URL
    engine = create_engine(settings.DATABASE_URL)
    
    print("Creating new CMS tables...")
    # This will only create tables that do not exist yet
    Base.metadata.create_all(bind=engine)
    
    print("Phase 6F.2 CMS Migration completed successfully.")

if __name__ == "__main__":
    migrate()
