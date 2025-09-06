import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path

class DatabaseManager:
    """Enhanced database manager with authentication support"""
    
    def __init__(self, db_path="/app/data/database/stylist.db"):
        self.db_path = db_path
        self.ensure_database_exists()
    
    def ensure_database_exists(self):
        """Create database and all required tables"""
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Enable foreign keys
            cursor.execute("PRAGMA foreign_keys = ON")
            
            # Users table (main user profiles)
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
            
            # User authentication table (handled by AuthenticationManager)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_auth (
                    user_id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    is_admin BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    failed_login_attempts INTEGER DEFAULT 0,
                    locked_until TIMESTAMP,
                    password_reset_token TEXT,
                    password_reset_expires TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # User sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (user_id) REFERENCES users (id)
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
            
            # Shopping analysis table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS shopping_analysis (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    product_url TEXT,
                    analysis_data TEXT,
                    fit_prediction TEXT,
                    recommendation TEXT,
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
            
            # Security audit log table (for authentication events)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS security_audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    action TEXT NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    success BOOLEAN,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def get_connection(self):
        """Get database connection with proper configuration"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def create_user_profile(self, user_data):
        """Create user profile (called after authentication user is created)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO users (id, name, email, location, timezone, preferences)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                user_data['id'],
                user_data['name'],
                user_data.get('email', ''),
                user_data.get('location', ''),
                user_data.get('timezone', 'UTC'),
                json.dumps(user_data.get('preferences', {}))
            ))
            conn.commit()
    
    def get_user_profile(self, user_id):
        """Get user profile information"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            if row:
                user_data = dict(row)
                if user_data.get('preferences'):
                    user_data['preferences'] = json.loads(user_data['preferences'])
                return user_data
            return None
    
    def update_user_profile(self, user_id, updates):
        """Update user profile"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Build dynamic update query
            set_clauses = []
            values = []
            
            for key, value in updates.items():
                if key in ['name', 'email', 'location', 'timezone']:
                    set_clauses.append(f"{key} = ?")
                    values.append(value)
                elif key == 'preferences':
                    set_clauses.append("preferences = ?")
                    values.append(json.dumps(value))
            
            if set_clauses:
                set_clauses.append("updated_at = ?")
                values.append(datetime.now().isoformat())
                values.append(user_id)
                
                query = f"UPDATE users SET {', '.join(set_clauses)} WHERE id = ?"
                cursor.execute(query, values)
                conn.commit()
    
    def save_clothing_item(self, item_data):
        """Save clothing item to database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO clothing_items 
                (id, user_id, category, name, colors, pattern, material, 
                 formality_level, season, weather_rating, image_path, analysis_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                item_data['id'],
                item_data['user_id'],
                item_data['category'],
                item_data['name'],
                json.dumps(item_data['colors']) if isinstance(item_data['colors'], list) else item_data['colors'],
                item_data['pattern'],
                item_data['material'],
                item_data['formality_level'],
                item_data['season'],
                json.dumps(item_data['weather_rating']) if isinstance(item_data['weather_rating'], dict) else item_data['weather_rating'],
                item_data.get('image_path'),
                json.dumps(item_data.get('analysis_data', {}))
            ))
            conn.commit()
    
    def get_user_clothing(self, user_id, category=None):
        """Get clothing items for user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if category:
                cursor.execute('''
                    SELECT * FROM clothing_items 
                    WHERE user_id = ? AND category = ?
                    ORDER BY created_at DESC
                ''', (user_id, category))
            else:
                cursor.execute('''
                    SELECT * FROM clothing_items 
                    WHERE user_id = ? 
                    ORDER BY created_at DESC
                ''', (user_id,))
            
            items = []
            for row in cursor.fetchall():
                item = dict(row)
                # Parse JSON fields
                if item.get('colors'):
                    try:
                        item['colors'] = json.loads(item['colors'])
                    except (json.JSONDecodeError, TypeError):
                        pass
                if item.get('weather_rating'):
                    try:
                        item['weather_rating'] = json.loads(item['weather_rating'])
                    except (json.JSONDecodeError, TypeError):
                        pass
                if item.get('analysis_data'):
                    try:
                        item['analysis_data'] = json.loads(item['analysis_data'])
                    except (json.JSONDecodeError, TypeError):
                        pass
                items.append(item)
            
            return items
    
    def get_clothing_count(self, user_id):
        """Get count of clothing items for user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM clothing_items WHERE user_id = ?', (user_id,))
            return cursor.fetchone()[0]
    
    def get_wardrobe_completeness(self, user_id):
        """Calculate wardrobe completeness percentage"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT category, COUNT(*) as count 
                FROM clothing_items 
                WHERE user_id = ? 
                GROUP BY category
            ''', (user_id,))
            
            categories = dict(cursor.fetchall())
            
            # Essential categories and minimum counts for a complete wardrobe
            essentials = {
                'shirt': 3, 'pants': 3, 'shoes': 2, 'jacket': 1,
                'dress': 1, 'top': 2, 'bottom': 2, 'outerwear': 1
            }
            
            score = 0
            for category, min_count in essentials.items():
                actual_count = categories.get(category, 0)
                score += min(actual_count / min_count, 1.0)
            
            return int((score / len(essentials)) * 100)
    
    def save_outfit_recommendation(self, recommendation_data):
        """Save outfit recommendation"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO outfit_recommendations 
                (id, user_id, date, occasion, weather_data, items, styling_tips, 
                 confidence_score, reasoning)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                recommendation_data['id'],
                recommendation_data['user_id'],
                recommendation_data['date'],
                recommendation_data['occasion'],
                json.dumps(recommendation_data.get('weather_data', {})),
                json.dumps(recommendation_data.get('items', [])),
                json.dumps(recommendation_data.get('styling_tips', [])),
                recommendation_data.get('confidence_score', 0.0),
                recommendation_data.get('reasoning', '')
            ))
            conn.commit()
    
    def get_outfit_recommendations(self, user_id, limit=10):
        """Get recent outfit recommendations for user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM outfit_recommendations 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (user_id, limit))
            
            recommendations = []
            for row in cursor.fetchall():
                rec = dict(row)
                # Parse JSON fields
                for field in ['weather_data', 'items', 'styling_tips']:
                    if rec.get(field):
                        try:
                            rec[field] = json.loads(rec[field])
                        except (json.JSONDecodeError, TypeError):
                            rec[field] = {}
                recommendations.append(rec)
            
            return recommendations
    
    def cleanup_expired_data(self):
        """Clean up expired sessions and old data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Clean up expired sessions (handled by AuthenticationManager)
            # Clean up old privacy audit logs (keep last 1000 entries)
            cursor.execute('''
                DELETE FROM privacy_audit_log 
                WHERE id NOT IN (
                    SELECT id FROM privacy_audit_log 
                    ORDER BY timestamp DESC 
                    LIMIT 1000
                )
            ''')
            
            # Clean up old security audit logs (keep last 5000 entries)
            cursor.execute('''
                DELETE FROM security_audit_log 
                WHERE id NOT IN (
                    SELECT id FROM security_audit_log 
                    ORDER BY timestamp DESC 
                    LIMIT 5000
                )
            ''')
            
            conn.commit()