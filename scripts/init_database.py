#!/usr/bin/env python3

import sys
import os
from pathlib import Path

# Add app directory to path with better path handling
current_dir = Path(__file__).parent
app_src_dir = current_dir.parent / 'src'
sys.path.insert(0, str(app_src_dir))
sys.path.insert(0, str(current_dir.parent))

def main():
    """Initialize database with authentication support"""
    
    print("Initializing Personal Stylist AI database...")
    
    try:
        # Get base path from environment or use default
        base_path = os.environ.get('APP_BASE_PATH', '/app')
        
        # Create base directories first
        directories = [
            os.path.join(base_path, 'data', 'database'),
            os.path.join(base_path, 'data', 'users'),
            os.path.join(base_path, 'uploads', 'temp'),
            os.path.join(base_path, 'uploads', 'clothing'),
            os.path.join(base_path, 'uploads', 'body_analysis'),
            os.path.join(base_path, 'models', 'cache')
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            print(f"✓ Created directory: {directory}")
        
        print("✓ Directory structure created")
        
        # Initialize main database FIRST (creates base tables)
        from core.database import DatabaseManager
        db_manager = DatabaseManager()
        print("✓ Main database tables created")
        
        # THEN initialize authentication system (adds auth tables)
        from core.authentication import AuthenticationManager
        auth_manager = AuthenticationManager()
        print("✓ Authentication system initialized")
        
        # Verify database is working
        try:
            # Test database connection
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                table_count = cursor.fetchone()[0]
                print(f"✓ Database verified with {table_count} tables")
        except Exception as e:
            print(f"⚠ Database verification warning: {e}")
        
        # Set proper permissions on data directory
        try:
            data_path = os.path.join(base_path, 'data')
            os.chmod(data_path, 0o755)
            
            db_file = os.path.join(base_path, 'data', 'database', 'stylist.db')
            if os.path.exists(db_file):
                os.chmod(db_file, 0o644)
                print("✓ Database permissions set")
        except Exception as e:
            print(f"⚠ Permission setting warning: {e}")
        
        print("✓ Database initialization complete!")
        return True
        
    except ImportError as e:
        print(f"✗ Import error - missing module: {e}")
        print("Make sure all required dependencies are installed")
        return False
        
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        print("This might be a temporary issue - the app will retry on startup")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)