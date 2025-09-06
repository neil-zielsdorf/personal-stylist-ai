#!/usr/bin/env python3

import sys
import os
sys.path.append('/app/src')

from core.database import DatabaseManager
from core.authentication import AuthenticationManager

def main():
    """Initialize database with authentication support"""
    
    print("Initializing Personal Stylist AI database...")
    
    try:
        # Initialize main database
        db_manager = DatabaseManager()
        print("✓ Main database tables created")
        
        # Initialize authentication system
        auth_manager = AuthenticationManager()
        print("✓ Authentication system initialized")
        
        # Create required directories
        os.makedirs('/app/data/users', exist_ok=True)
        os.makedirs('/app/uploads/temp', exist_ok=True)
        print("✓ Directory structure created")
        
        print("✓ Database initialization complete!")
        return True
        
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)