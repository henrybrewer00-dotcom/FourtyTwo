#!/usr/bin/env python3
"""
GAME 42 - Database Initialization Script
========================================
Run this script to initialize the SQLite database with required tables.
"""

import os
import sys

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from models import db
from models.user import User
from models.game_session import GameSession

def create_app():
    """Create a Flask app for database initialization."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'init-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///game.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app


def init_database():
    """Initialize the database."""
    app = create_app()

    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")

        # Print table info
        print("\nCreated tables:")
        print("  - users (for user accounts and authentication)")
        print("  - game_sessions (for game state persistence)")

        # Check if database file exists
        db_path = os.path.join(os.path.dirname(__file__), 'instance', 'game.db')
        if os.path.exists(db_path):
            print(f"\nDatabase file: {db_path}")
        else:
            # Flask-SQLAlchemy may create in different location
            alt_path = os.path.join(os.path.dirname(__file__), 'game.db')
            if os.path.exists(alt_path):
                print(f"\nDatabase file: {alt_path}")


def reset_database():
    """Reset the database (drop all tables and recreate)."""
    app = create_app()

    with app.app_context():
        print("Dropping all tables...")
        db.drop_all()
        print("Creating fresh tables...")
        db.create_all()
        print("Database reset complete!")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='GAME 42 Database Management')
    parser.add_argument('--reset', action='store_true',
                        help='Reset database (drop and recreate all tables)')

    args = parser.parse_args()

    if args.reset:
        confirm = input("Are you sure you want to reset the database? This will delete all data. (y/N): ")
        if confirm.lower() == 'y':
            reset_database()
        else:
            print("Reset cancelled.")
    else:
        init_database()

    print("\nDone!")
