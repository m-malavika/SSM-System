"""
Quick script to drop the orphaned index and recreate the notifications table
"""
from sqlalchemy import create_engine, text
from app.core.config import settings

def fix_notifications_table():
    engine = create_engine(settings.get_database_url())
    
    with engine.begin() as conn:  # Using begin() for automatic commit
        # Check what exists
        print("Checking for existing notifications-related objects...")
        result = conn.execute(text("""
            SELECT tablename FROM pg_tables 
            WHERE tablename = 'notifications'
        """))
        if result.fetchone():
            print("  - notifications table exists")
        
        result = conn.execute(text("""
            SELECT indexname FROM pg_indexes 
            WHERE indexname = 'ix_notifications_student_id'
        """))
        if result.fetchone():
            print("  - ix_notifications_student_id index exists")
        
        # Drop the orphaned index if it exists
        print("\nDropping index if exists...")
        conn.execute(text("DROP INDEX IF EXISTS ix_notifications_student_id CASCADE"))
        print("  ✓ Index dropped")
        
        # Drop the table if it exists
        print("Dropping table if exists...")
        conn.execute(text("DROP TABLE IF EXISTS notifications CASCADE"))
        print("  ✓ Table dropped")
        
        print("\n✓ Successfully cleaned up notifications table and index")
        print("Now run: alembic upgrade head")

if __name__ == "__main__":
    fix_notifications_table()
