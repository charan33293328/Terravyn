import sqlite3
import os
from sqlalchemy import create_engine, text, inspect
from models.domain import Base, TicketInternalNote

# Path to DB
DB_PATH = os.path.join(os.path.dirname(__file__), "terravyn.db")

def migrate():
    print("Starting Phase 6E Support Center Migration...")
    
    # 1. Connect to SQLite
    engine = create_engine(f"sqlite:///{DB_PATH}")
    inspector = inspect(engine)

    # Check if tables exist
    tables = inspector.get_table_names()
    
    with engine.connect() as conn:
        if 'support_tickets' in tables:
            tickets_columns = [col['name'] for col in inspector.get_columns('support_tickets')]
            if 'ticket_number' not in tickets_columns:
                print("Adding ticket_number to support_tickets...")
                conn.execute(text("ALTER TABLE support_tickets ADD COLUMN ticket_number VARCHAR(50)"))
                conn.execute(text("CREATE UNIQUE INDEX ix_support_tickets_ticket_number ON support_tickets (ticket_number)"))
                
            if 'category' not in tickets_columns:
                print("Adding category to support_tickets...")
                conn.execute(text("ALTER TABLE support_tickets ADD COLUMN category VARCHAR(50) DEFAULT 'GENERAL_INQUIRY'"))
                
            if 'closed_at' not in tickets_columns:
                print("Adding closed_at to support_tickets...")
                conn.execute(text("ALTER TABLE support_tickets ADD COLUMN closed_at DATETIME"))
        else:
            print("Table support_tickets does not exist, will be created by create_all.")
        
        if 'ticket_messages' in tables:
            messages_columns = [col['name'] for col in inspector.get_columns('ticket_messages')]
            
            if 'sender_type' not in messages_columns:
                print("Adding sender_type to ticket_messages...")
                conn.execute(text("ALTER TABLE ticket_messages ADD COLUMN sender_type VARCHAR(50) DEFAULT 'CUSTOMER'"))
                
            if 'attachment_url' not in messages_columns:
                print("Adding attachment_url to ticket_messages...")
                conn.execute(text("ALTER TABLE ticket_messages ADD COLUMN attachment_url VARCHAR(500)"))
        else:
            print("Table ticket_messages does not exist, will be created by create_all.")
            
        conn.commit()

    # Create new tables if they don't exist (like ticket_internal_notes)
    print("Creating new tables...")
    Base.metadata.create_all(engine)
    
    print("Phase 6E Support Center Migration completed successfully.")

if __name__ == "__main__":
    migrate()
