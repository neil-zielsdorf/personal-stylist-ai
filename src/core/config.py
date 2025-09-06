"""
Configuration management for Personal Stylist AI
"""

import os
from pathlib import Path

class Config:
    """Application configuration with environment variable support"""
    
    # Base paths
    BASE_PATH = Path(os.environ.get('APP_BASE_PATH', '/app'))
    SRC_PATH = BASE_PATH / 'src'
    DATA_PATH = BASE_PATH / 'data'
    UPLOADS_PATH = BASE_PATH / 'uploads'
    MODELS_PATH = BASE_PATH / 'models'
    
    # Database configuration
    DATABASE_PATH = DATA_PATH / 'database' / 'stylist.db'
    DATABASE_TIMEOUT = float(os.environ.get('DATABASE_TIMEOUT', 30.0))
    
    # Authentication configuration
    SESSION_TIMEOUT = int(os.environ.get('SESSION_TIMEOUT', 86400))  # 24 hours
    MAX_LOGIN_ATTEMPTS = int(os.environ.get('MAX_LOGIN_ATTEMPTS', 5))
    LOCKOUT_DURATION = int(os.environ.get('LOCKOUT_DURATION', 900))  # 15 minutes
    PASSWORD_HASH_ITERATIONS = int(os.environ.get('PASSWORD_HASH_ITERATIONS', 100000))
    
    # Security configuration
    ENABLE_RATE_LIMITING = os.environ.get('ENABLE_RATE_LIMITING', 'true').lower() == 'true'
    LOG_SECURITY_EVENTS = os.environ.get('LOG_SECURITY_EVENTS', 'true').lower() == 'true'
    
    # Application configuration
    DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'
    STREAMLIT_PORT = int(os.environ.get('STREAMLIT_PORT', 8501))
    
    # Model configuration
    AI_MODELS_ENABLED = os.environ.get('AI_MODELS_ENABLED', 'true').lower() == 'true'
    MODEL_CACHE_PATH = MODELS_PATH / 'cache'
    
    # Upload configuration
    MAX_UPLOAD_SIZE = int(os.environ.get('MAX_UPLOAD_SIZE', 50 * 1024 * 1024))  # 50MB
    ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp']
    
    # Privacy configuration
    IMMEDIATE_PHOTO_ANONYMIZATION = True
    LOG_RETENTION_DAYS = int(os.environ.get('LOG_RETENTION_DAYS', 90))
    
    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist"""
        directories = [
            cls.DATA_PATH / 'database',
            cls.DATA_PATH / 'users',
            cls.UPLOADS_PATH / 'temp',
            cls.UPLOADS_PATH / 'clothing',
            cls.UPLOADS_PATH / 'body_analysis',
            cls.MODEL_CACHE_PATH
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_user_upload_path(cls, user_id: str) -> Path:
        """Get user-specific upload directory"""
        user_path = cls.UPLOADS_PATH / 'users' / user_id
        user_path.mkdir(parents=True, exist_ok=True)
        return user_path
    
    @classmethod
    def get_user_data_path(cls, user_id: str) -> Path:
        """Get user-specific data directory"""
        user_path = cls.DATA_PATH / 'users' / user_id
        user_path.mkdir(parents=True, exist_ok=True)
        return user_path

# Create global config instance
config = Config()