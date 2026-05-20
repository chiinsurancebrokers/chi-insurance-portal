#!/usr/bin/env python3
"""
Migration script to add agent and payment_code columns to policies table.
Run this after deploying to update the Railway PostgreSQL database.
"""
import os
from sqlalchemy import create_engine, text

def get_database_url():
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        return db_url
    return 'sqlite:///data/database/chi_insurance.db'

def migrate():
    engine = create_engine(get_database_url())
    
    with engine.connect() as conn:
        # Check if columns exist before adding
        try:
            # Add agent column
            conn.execute(text("""
                ALTER TABLE policies ADD COLUMN IF NOT EXISTS agent VARCHAR(10) DEFAULT '3p'
            """))
            print("✅ Added 'agent' column to policies table")
        except Exception as e:
            if 'already exists' in str(e).lower() or 'duplicate column' in str(e).lower():
                print("ℹ️ 'agent' column already exists")
            else:
                # For SQLite (doesn't support IF NOT EXISTS in ALTER)
                try:
                    conn.execute(text("ALTER TABLE policies ADD COLUMN agent VARCHAR(10) DEFAULT '3p'"))
                    print("✅ Added 'agent' column to policies table")
                except:
                    print("ℹ️ 'agent' column already exists or cannot be added")
        
        try:
            # Add payment_code column
            conn.execute(text("""
                ALTER TABLE policies ADD COLUMN IF NOT EXISTS payment_code VARCHAR(50)
            """))
            print("✅ Added 'payment_code' column to policies table")
        except Exception as e:
            if 'already exists' in str(e).lower() or 'duplicate column' in str(e).lower():
                print("ℹ️ 'payment_code' column already exists")
            else:
                # For SQLite
                try:
                    conn.execute(text("ALTER TABLE policies ADD COLUMN payment_code VARCHAR(50)"))
                    print("✅ Added 'payment_code' column to policies table")
                except:
                    print("ℹ️ 'payment_code' column already exists or cannot be added")
        
        conn.commit()
        print("\n✅ Migration completed successfully!")

if __name__ == '__main__':
    print("Running database migration for agent and payment_code columns...")
    migrate()
