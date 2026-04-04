#!/usr/bin/env python3
"""
Echo Agent Proxy - Database Initialization
Run this once to create the SQLite database from schema.sql
"""

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path("database/echo.db")

def init_database():
    DB_PATH.parent.mkdir(exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Read and execute the schema
    schema_path = Path("database/schema.sql")
    if not schema_path.exists():
        print("Error: schema.sql not found!")
        sys.exit(1)
    
    with open(schema_path, "r") as f:
        schema_sql = f.read()
    
    try:
        cursor.executescript(schema_sql)
        conn.commit()
        print(f"✅ Database initialized successfully at: {DB_PATH}")
        print(f"   Created tables: sessions, audit_log, summaries, session_memory")
        
        # Show active sessions view
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view';")
        views = cursor.fetchall()
        if views:
            print(f"   Created views: {[v[0] for v in views]}")
            
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    init_database()
