#!/usr/bin/env python3

import sys
import os
import sqlite3
from datetime import datetime

def main():
    """Initialize database with default structure"""
    
    print("Initializing Personal Stylist database...")
    
    try:
        # Ensure database directory exists
        db_dir = '/app/data/database'
        os.makedirs(db_dir, exist_ok=True)
        
        db_path = os.path.join(db_dir, 'stylist.db')
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT,
                location TEXT,
                timezone TEXT,
                preferences TEXT,
                body_measurements TEXT,
                foot_measurements TEXT,
                style_preferences TEXT,
                notification_settings TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Clothing items table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clothing_items (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                category TEXT,
                name TEXT,
                colors TEXT,
                pattern TEXT,
                material TEXT,
                formality_level INTEGER,
                season TEXT,
                weather_rating TEXT,
                fit_notes TEXT,
                purchase_date TEXT,
                cost_per_wear REAL,
                image_path TEXT,
                analysis_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Outfit recommendations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS outfit_recommendations (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                date TEXT,
                occasion TEXT,
                weather_data TEXT,
                items TEXT,
                styling_tips TEXT,
                confidence_score REAL,
                reasoning TEXT,
                feedback TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Privacy audit log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS privacy_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                event_type TEXT,
                user_id TEXT,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
        print("✓ Database initialized successfully")
        return True
        
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)