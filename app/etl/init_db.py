#!/usr/bin/env python3
import sqlite3
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database path from environment
DB_PATH = os.getenv('SENECHAL_DB_PATH')
if not DB_PATH:
    raise ValueError("SENECHAL_DB_PATH environment variable not set")

def init_db():
    """Initialize the Senechal database with schema"""
    print(f"Initializing database at {DB_PATH}")
    
    # Create directory if it doesn't exist
    db_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
        print(f"Created directory: {db_dir}")

    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Connect and create schema
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Execute schema.sql
        with open(os.path.join(script_dir, 'schema.sql'), 'r',encoding='utf-8') as f:
            cursor.executescript(f.read())
            
        # Execute init.sql
        with open(os.path.join(script_dir, 'init.sql'), 'r',encoding='utf-8') as f:
            cursor.executescript(f.read())

        conn.commit()
        print("✅ Database initialized successfully")

    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()