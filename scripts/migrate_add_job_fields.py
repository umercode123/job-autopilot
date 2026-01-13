"""
Manual database migration script
Adds new columns to jobs table for Apify data
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import create_engine, text
from modules.database import get_db_url
from modules.logger_config import app_logger

def migrate_db():
    """Add new columns to jobs table"""
    
    db_url = get_db_url()
    engine = create_engine(db_url)
    
    # SQL statements to add new columns (safe to run multiple times - will skip if exists)
    migrations = [
        # Date fields
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS expiration_date TIMESTAMP",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS job_age VARCHAR",
        
        # URLs
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS apply_url VARCHAR",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS company_url VARCHAR",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS company_logo_url VARCHAR",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS header_image_url VARCHAR",
        
        # Job details
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS job_type VARCHAR",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS occupation VARCHAR",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS benefits TEXT",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS rating VARCHAR",
    ]
    
    try:
        with engine.connect() as conn:
            for sql in migrations:
                try:
                    conn.execute(text(sql))
                    conn.commit()
                    app_logger.info(f"Executed: {sql}")
                except Exception as e:
                    app_logger.warning(f"Migration skipped (column may exist): {sql}")
                    app_logger.debug(f"Error: {e}")
        
        app_logger.info("✅ Database migration completed successfully!")
        print("✅ Database migration completed successfully!")
        
    except Exception as e:
        app_logger.error(f"Migration failed: {e}")
        print(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    migrate_db()
