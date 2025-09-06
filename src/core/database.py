import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path

# Import configuration
try:
    from .config import config
except ImportError:
    # Fallback if config not available
    class FallbackConfig:
        DATABASE_PATH = "/app/data/database/stylist.db"
        DATABASE_TIMEOUT = 30.0
        
        @staticmethod
        def ensure_directories():
            os.makedirs(os.path.dirname(FallbackConfig.DATABASE_PATH), exist_ok=True)
    
    config = FallbackConfig()

class DatabaseManager:
    """Enhanced database manager with authentication support"""
    
    def __init__(self, db_path=None):
        if db_path is None:
            self.db_path = str(config.DATABASE_PATH)
        else:
            self.db_path = db_path
            
        self.timeout = getattr(config, 'DATABASE_TIMEOUT', 30.0)
        self.ensure_database_exists()
    
    def ensure_database_exists(self):
        """Create database and all required tables"""
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        try:
            with sqlite3.connect(self.db_path, timeout=self.timeout) as conn:
                cursor = conn.cursor()
                
                # Enable foreign keys and WAL mode for better concurrency
                cursor.execute("PRAGMA foreign_keys = ON")
                cursor.execute("PRAGMA journal_mode = WAL")
                cursor.execute("PRAGMA synchronous = NORMAL")
                cursor.execute("PRAGMA cache_size = 10000")
                cursor.execute("PRAGMA temp_store = MEMORY")
                
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
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
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
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
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
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
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
                
                # Create indexes for better performance
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_clothing_user_id 
                    ON clothing_items (user_id)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_clothing_category 
                    ON clothing_items (user_id, category)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_outfit_user_date 
                    ON outfit_recommendations (user_id, date)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_privacy_audit_user 
                    ON privacy_audit_log (user_id, timestamp)
                ''')
                
                conn.commit()
                
        except sqlite3.Error as e:
            print(f"Database initialization error: {e}")
            # Don't raise - let the app continue and try again later
    
    def get_connection(self):
        """Get database connection with proper configuration"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=self.timeout)
            conn.row_factory = sqlite3.Row
            
            # Set pragmas for performance and consistency
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            
            return conn
        except sqlite3.Error as e:
            print(f"Database connection failed: {e}")
            raise ConnectionError(f"Unable to connect to database: {e}")
    
    def create_user_profile(self, user_data):
        """Create user profile (called after authentication user is created)"""
        try:
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
                return True
        except Exception as e:
            print(f"Error creating user profile: {e}")
            return False
    
    def get_user_profile(self, user_id):
        """Get user profile information"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
                row = cursor.fetchone()
                if row:
                    user_data = dict(row)
                    if user_data.get('preferences'):
                        try:
                            user_data['preferences'] = json.loads(user_data['preferences'])
                        except (json.JSONDecodeError, TypeError):
                            user_data['preferences'] = {}
                    return user_data
                return None
        except Exception as e:
            print(f"Error getting user profile: {e}")
            return None
    
    def update_user_profile(self, user_id, updates):
        """Update user profile"""
        try:
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
                    return True
                return False
        except Exception as e:
            print(f"Error updating user profile: {e}")
            return False
    
    def save_clothing_item(self, item_data):
        """Save clothing item to database"""
        try:
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
                return True
        except Exception as e:
            print(f"Error saving clothing item: {e}")
            return False
    
    def get_user_clothing(self, user_id, category=None):
        """Get clothing items for user"""
        try:
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
                    # Parse JSON fields safely
                    for json_field in ['colors', 'weather_rating', 'analysis_data']:
                        if item.get(json_field):
                            try:
                                item[json_field] = json.loads(item[json_field])
                            except (json.JSONDecodeError, TypeError):
                                item[json_field] = {} if json_field != 'colors' else []
                    items.append(item)
                
                return items
        except Exception as e:
            print(f"Error getting user clothing: {e}")
            return []
    
    def get_clothing_count(self, user_id):
        """Get count of clothing items for user"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM clothing_items WHERE user_id = ?', (user_id,))
                result = cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            print(f"Error getting clothing count: {e}")
            return 0
    
    def get_wardrobe_completeness(self, user_id):
        """Calculate wardrobe completeness percentage"""
        try:
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
        except Exception as e:
            print(f"Error calculating wardrobe completeness: {e}")
            return 0
    
    def save_outfit_recommendation(self, recommendation_data):
        """Save outfit recommendation"""
        try:
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
                return True
        except Exception as e:
            print(f"Error saving outfit recommendation: {e}")
            return False
    
    def get_outfit_recommendations(self, user_id, limit=10):
        """Get recent outfit recommendations for user"""
        try:
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
                    # Parse JSON fields safely
                    for field in ['weather_data', 'items', 'styling_tips']:
                        if rec.get(field):
                            try:
                                rec[field] = json.loads(rec[field])
                            except (json.JSONDecodeError, TypeError):
                                rec[field] = {} if field == 'weather_data' else []
                    recommendations.append(rec)
                
                return recommendations
        except Exception as e:
            print(f"Error getting outfit recommendations: {e}")
            return []
    
    def log_privacy_event(self, session_id, event_type, user_id=None, details=""):
        """Log privacy-related events"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO privacy_audit_log 
                    (session_id, event_type, user_id, details)
                    VALUES (?, ?, ?, ?)
                ''', (session_id, event_type, user_id, details))
                conn.commit()
        except Exception as e:
            print(f"Error logging privacy event: {e}")
    
    def cleanup_expired_data(self):
        """Clean up expired sessions and old data"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Clean up old privacy audit logs (keep last 1000 entries)
                cursor.execute('''
                    DELETE FROM privacy_audit_log 
                    WHERE id NOT IN (
                        SELECT id FROM privacy_audit_log 
                        ORDER BY timestamp DESC 
                        LIMIT 1000
                    )
                ''')
                
                conn.commit()
                
        except Exception as e:
            print(f"Error during data cleanup: {e}")
    
    def health_check(self):
        """Perform database health check"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if tables exist
                cursor.execute('''
                    SELECT COUNT(*) FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ''')
                table_count = cursor.fetchone()[0]
                
                # Check database integrity
                cursor.execute("PRAGMA integrity_check")
                integrity = cursor.fetchone()[0]
                
                return {
                    'status': 'healthy' if integrity == 'ok' else 'error',
                    'tables': table_count,
                    'integrity': integrity,
                    'file_size': os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
                }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'tables': 0,
                'integrity': 'unknown',
                'file_size': 0
            }