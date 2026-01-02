#!/usr/bin/env python3
"""
Database Migration Script
Adds access_code and last_activity columns to game_sessions table
"""

import sqlite3
from datetime import datetime

def migrate():
    """Add new columns to game_sessions table."""
    conn = sqlite3.connect('instance/game.db')
    cursor = conn.cursor()

    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(game_sessions)")
        columns = [col[1] for col in cursor.fetchall()]

        # Add access_code column if it doesn't exist
        if 'access_code' not in columns:
            print("Adding access_code column...")
            cursor.execute("ALTER TABLE game_sessions ADD COLUMN access_code VARCHAR(6)")
            print("✓ access_code column added")
        else:
            print("✓ access_code column already exists")

        # Add last_activity column if it doesn't exist
        if 'last_activity' not in columns:
            print("Adding last_activity column...")
            cursor.execute(f"ALTER TABLE game_sessions ADD COLUMN last_activity DATETIME DEFAULT '{datetime.utcnow().isoformat()}'")
            print("✓ last_activity column added")
        else:
            print("✓ last_activity column already exists")

        # Update existing rows to have last_activity set to created_at if NULL
        cursor.execute("UPDATE game_sessions SET last_activity = created_at WHERE last_activity IS NULL")

        conn.commit()
        print("\nMigration completed successfully!")

    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
