# =============================================================================
# CORE/AUTHENTICATION.PY - Secure authentication system
# =============================================================================

import streamlit as st
import hashlib
import secrets
import sqlite3
import json
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
import re
import hmac

class AuthenticationManager:
    """Secure authentication system for Personal Stylist AI"""
    
    def __init__(self, db_path="/app/data/database/stylist.db"):
        self.db_path = db_path
        self.session_timeout = 24 * 60 * 60  # 24 hours in seconds
        self.max_login_attempts = 5
        self.lockout_duration = 15 * 60  # 15 minutes in seconds
        self.ensure_auth_tables()
    
    def ensure_auth_tables(self):
        """Create authentication tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # User authentication table
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
            
            # Active sessions table
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
            
            # Security audit log table
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
    
    def hash_password(self, password: str, salt: str = None) -> Tuple[str, str]:
        """Securely hash password with salt"""
        if salt is None:
            salt = secrets.token_hex(32)
        
        # Use PBKDF2 with SHA-256
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # 100,000 iterations
        )
        
        return password_hash.hex(), salt
    
    def verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """Verify password against hash"""
        computed_hash, _ = self.hash_password(password, salt)
        return hmac.compare_digest(computed_hash, password_hash)
    
    def validate_password_strength(self, password: str) -> Tuple[bool, str]:
        """Validate password meets security requirements"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if len(password) > 128:
            return False, "Password must be less than 128 characters"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r'[0-9]', password):
            return False, "Password must contain at least one number"
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        
        # Check for common weak passwords
        weak_patterns = [
            r'password', r'123456', r'qwerty', r'admin', r'login',
            r'welcome', r'letmein', r'monkey', r'dragon', r'master'
        ]
        
        for pattern in weak_patterns:
            if re.search(pattern, password.lower()):
                return False, f"Password cannot contain common words like '{pattern}'"
        
        return True, "Password meets security requirements"
    
    def create_user(self, username: str, email: str, password: str, is_admin: bool = False) -> Tuple[bool, str]:
        """Create new user with secure authentication"""
        
        # Validate inputs
        if not username or len(username) < 3:
            return False, "Username must be at least 3 characters long"
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            return False, "Username can only contain letters, numbers, underscore, and dash"
        
        if not email or not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            return False, "Please enter a valid email address"
        
        # Validate password strength
        is_strong, message = self.validate_password_strength(password)
        if not is_strong:
            return False, message
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if username or email already exists
                cursor.execute(
                    "SELECT username, email FROM user_auth WHERE username = ? OR email = ?",
                    (username, email)
                )
                existing = cursor.fetchone()
                
                if existing:
                    if existing[0] == username:
                        return False, "Username already exists"
                    else:
                        return False, "Email already registered"
                
                # Generate user ID and hash password
                user_id = secrets.token_hex(16)
                password_hash, salt = self.hash_password(password)
                
                # Create user profile first
                cursor.execute('''
                    INSERT INTO users (id, name, email, location, timezone, preferences)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    user_id, username, email, '', 'UTC',
                    json.dumps({
                        'temperature_unit': 'celsius',
                        'measurement_system': 'metric'
                    })
                ))
                
                # Create authentication record
                cursor.execute('''
                    INSERT INTO user_auth 
                    (user_id, username, email, password_hash, salt, is_admin, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, username, email, password_hash, salt, is_admin, True))
                
                conn.commit()
                
                # Log the creation
                self.log_security_event(
                    user_id=user_id,
                    action="USER_CREATED",
                    success=True,
                    details=f"User '{username}' created"
                )
                
                return True, f"User '{username}' created successfully"
        
        except Exception as e:
            return False, f"Error creating user: {str(e)}"
    
    def authenticate_user(self, username: str, password: str, ip_address: str = None, user_agent: str = None) -> Tuple[bool, str, Optional[str]]:
        """Authenticate user login"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get user authentication info
                cursor.execute('''
                    SELECT user_id, username, password_hash, salt, is_active, 
                           failed_login_attempts, locked_until
                    FROM user_auth 
                    WHERE username = ? OR email = ?
                ''', (username, username))
                
                user_auth = cursor.fetchone()
                
                if not user_auth:
                    self.log_security_event(
                        action="LOGIN_FAILED",
                        success=False,
                        details=f"User '{username}' not found",
                        ip_address=ip_address,
                        user_agent=user_agent
                    )
                    return False, "Invalid username or password", None
                
                user_id, db_username, password_hash, salt, is_active, failed_attempts, locked_until = user_auth
                
                # Check if account is active
                if not is_active:
                    self.log_security_event(
                        user_id=user_id,
                        action="LOGIN_FAILED",
                        success=False,
                        details="Account is disabled",
                        ip_address=ip_address,
                        user_agent=user_agent
                    )
                    return False, "Account is disabled", None
                
                # Check if account is locked
                if locked_until and datetime.now() < datetime.fromisoformat(locked_until):
                    remaining_time = datetime.fromisoformat(locked_until) - datetime.now()
                    minutes = int(remaining_time.total_seconds() / 60)
                    
                    self.log_security_event(
                        user_id=user_id,
                        action="LOGIN_FAILED",
                        success=False,
                        details="Account is locked",
                        ip_address=ip_address,
                        user_agent=user_agent
                    )
                    return False, f"Account locked. Try again in {minutes} minutes", None
                
                # Verify password
                if not self.verify_password(password, password_hash, salt):
                    # Increment failed attempts
                    failed_attempts += 1
                    
                    # Lock account if too many failed attempts
                    locked_until = None
                    if failed_attempts >= self.max_login_attempts:
                        locked_until = (datetime.now() + timedelta(seconds=self.lockout_duration)).isoformat()
                    
                    cursor.execute('''
                        UPDATE user_auth 
                        SET failed_login_attempts = ?, locked_until = ?
                        WHERE user_id = ?
                    ''', (failed_attempts, locked_until, user_id))
                    
                    conn.commit()
                    
                    self.log_security_event(
                        user_id=user_id,
                        action="LOGIN_FAILED",
                        success=False,
                        details=f"Invalid password (attempt {failed_attempts})",
                        ip_address=ip_address,
                        user_agent=user_agent
                    )
                    
                    if locked_until:
                        return False, f"Too many failed attempts. Account locked for {self.lockout_duration // 60} minutes", None
                    else:
                        remaining = self.max_login_attempts - failed_attempts
                        return False, f"Invalid password. {remaining} attempts remaining", None
                
                # Successful login - reset failed attempts and create session
                cursor.execute('''
                    UPDATE user_auth 
                    SET failed_login_attempts = 0, locked_until = NULL, last_login = ?
                    WHERE user_id = ?
                ''', (datetime.now().isoformat(), user_id))
                
                # Create session
                session_id = self.create_session(user_id, ip_address, user_agent)
                
                conn.commit()
                
                self.log_security_event(
                    user_id=user_id,
                    action="LOGIN_SUCCESS",
                    success=True,
                    details="User logged in successfully",
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                
                return True, "Login successful", session_id
        
        except Exception as e:
            self.log_security_event(
                action="LOGIN_ERROR",
                success=False,
                details=f"Login error: {str(e)}",
                ip_address=ip_address,
                user_agent=user_agent
            )
            return False, "Login error occurred", None
    
    def create_session(self, user_id: str, ip_address: str = None, user_agent: str = None) -> str:
        """Create new user session"""
        
        session_id = secrets.token_hex(32)
        expires_at = datetime.now() + timedelta(seconds=self.session_timeout)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Deactivate old sessions for this user
            cursor.execute('''
                UPDATE user_sessions 
                SET is_active = FALSE 
                WHERE user_id = ? AND is_active = TRUE
            ''', (user_id,))
            
            # Create new session
            cursor.execute('''
                INSERT INTO user_sessions 
                (session_id, user_id, expires_at, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?)
            ''', (session_id, user_id, expires_at.isoformat(), ip_address, user_agent))
            
            conn.commit()
        
        return session_id
    
    def validate_session(self, session_id: str) -> Tuple[bool, Optional[str]]:
        """Validate session and return user_id if valid"""
        
        if not session_id:
            return False, None
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT s.user_id, s.expires_at, u.is_active
                    FROM user_sessions s
                    JOIN user_auth u ON s.user_id = u.user_id
                    WHERE s.session_id = ? AND s.is_active = TRUE
                ''', (session_id,))
                
                session_data = cursor.fetchone()
                
                if not session_data:
                    return False, None
                
                user_id, expires_at, user_active = session_data
                
                # Check if user is still active
                if not user_active:
                    return False, None
                
                # Check if session has expired
                if datetime.now() > datetime.fromisoformat(expires_at):
                    # Deactivate expired session
                    cursor.execute('''
                        UPDATE user_sessions 
                        SET is_active = FALSE 
                        WHERE session_id = ?
                    ''', (session_id,))
                    conn.commit()
                    return False, None
                
                # Update last activity
                cursor.execute('''
                    UPDATE user_sessions 
                    SET last_activity = ? 
                    WHERE session_id = ?
                ''', (datetime.now().isoformat(), session_id))
                
                conn.commit()
                
                return True, user_id
        
        except Exception as e:
            return False, None
    
    def logout_user(self, session_id: str) -> bool:
        """Logout user by deactivating session"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get user_id for logging
                cursor.execute(
                    "SELECT user_id FROM user_sessions WHERE session_id = ?",
                    (session_id,)
                )
                result = cursor.fetchone()
                
                if result:
                    user_id = result[0]
                    
                    # Deactivate session
                    cursor.execute('''
                        UPDATE user_sessions 
                        SET is_active = FALSE 
                        WHERE session_id = ?
                    ''', (session_id,))
                    
                    conn.commit()
                    
                    self.log_security_event(
                        user_id=user_id,
                        action="LOGOUT",
                        success=True,
                        details="User logged out"
                    )
                    
                    return True
        
        except Exception as e:
            return False
        
        return False
    
    def get_user_info(self, user_id: str) -> Optional[Dict]:
        """Get user information"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT u.id, u.name, u.email, u.location, u.preferences,
                           a.username, a.is_admin, a.last_login
                    FROM users u
                    JOIN user_auth a ON u.id = a.user_id
                    WHERE u.id = ? AND a.is_active = TRUE
                ''', (user_id,))
                
                result = cursor.fetchone()
                
                if result:
                    return {
                        'id': result[0],
                        'name': result[1],
                        'email': result[2],
                        'location': result[3],
                        'preferences': json.loads(result[4]) if result[4] else {},
                        'username': result[5],
                        'is_admin': bool(result[6]),
                        'last_login': result[7]
                    }
        
        except Exception as e:
            return None
        
        return None
    
    def log_security_event(self, action: str, success: bool, details: str = "", 
                          user_id: str = None, ip_address: str = None, user_agent: str = None):
        """Log security events for auditing"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO security_audit_log 
                    (user_id, action, ip_address, user_agent, success, details)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, action, ip_address, user_agent, success, details))
                
                conn.commit()
        
        except Exception as e:
            # Don't fail the main operation if logging fails
            pass
    
    def get_security_logs(self, limit: int = 100) -> list:
        """Get recent security logs for admin review"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT l.timestamp, l.action, l.success, l.details, 
                           l.ip_address, a.username
                    FROM security_audit_log l
                    LEFT JOIN user_auth a ON l.user_id = a.user_id
                    ORDER BY l.timestamp DESC
                    LIMIT ?
                ''', (limit,))
                
                return [
                    {
                        'timestamp': row[0],
                        'action': row[1],
                        'success': bool(row[2]),
                        'details': row[3],
                        'ip_address': row[4],
                        'username': row[5] or 'Unknown'
                    }
                    for row in cursor.fetchall()
                ]
        
        except Exception as e:
            return []
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions (run periodically)"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE user_sessions 
                    SET is_active = FALSE 
                    WHERE expires_at < ? AND is_active = TRUE
                ''', (datetime.now().isoformat(),))
                
                conn.commit()
        
        except Exception as e:
            pass

# =============================================================================
# STREAMLIT AUTHENTICATION INTEGRATION
# =============================================================================

def init_session_state():
    """Initialize Streamlit session state for authentication"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    if 'session_id' not in st.session_state:
        st.session_state.session_id = None

def check_authentication():
    """Check if user is authenticated and session is valid"""
    
    init_session_state()
    auth_manager = AuthenticationManager()
    
    # Check if we have a session ID
    if st.session_state.session_id:
        is_valid, user_id = auth_manager.validate_session(st.session_state.session_id)
        
        if is_valid and user_id:
            # Session is valid, update user info
            user_info = auth_manager.get_user_info(user_id)
            if user_info:
                st.session_state.authenticated = True
                st.session_state.user_id = user_id
                st.session_state.user_info = user_info
                return True
    
    # No valid session
    st.session_state.authenticated = False
    st.session_state.user_id = None
    st.session_state.user_info = None
    st.session_state.session_id = None
    return False

def show_login_page():
    """Display login/registration page"""
    
    auth_manager = AuthenticationManager()
    
    # Check if this is the first user (admin setup)
    with sqlite3.connect(auth_manager.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM user_auth")
        user_count = cursor.fetchone()[0]
    
    if user_count == 0:
        show_admin_setup()
        return
    
    st.markdown("""
    <div style="max-width: 400px; margin: 0 auto; padding: 2rem;">
        <div style="text-align: center; margin-bottom: 2rem;">
            <h1>👔 Personal Stylist AI</h1>
            <p>Sign in to access your private fashion assistant</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Sign In", "Create Account"])
    
    with tab1:
        with st.form("login_form"):
            st.subheader("Sign In")
            
            username = st.text_input("Username or Email", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            
            remember_me = st.checkbox("Keep me signed in", value=True)
            
            submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)
            
            if submitted:
                if username and password:
                    # Get client info for logging
                    ip_address = st.context.headers.get("x-forwarded-for", "unknown")
                    user_agent = st.context.headers.get("user-agent", "unknown")
                    
                    success, message, session_id = auth_manager.authenticate_user(
                        username, password, ip_address, user_agent
                    )
                    
                    if success:
                        st.session_state.session_id = session_id
                        st.success(message)
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Please enter both username and password")
    
    with tab2:
        with st.form("register_form"):
            st.subheader("Create Account")
            
            reg_username = st.text_input("Username", key="reg_username")
            reg_email = st.text_input("Email", key="reg_email")
            reg_password = st.text_input("Password", type="password", key="reg_password")
            reg_confirm = st.text_input("Confirm Password", type="password", key="reg_confirm")
            
            # Password requirements
            st.caption("""
            Password requirements:
            • At least 8 characters long
            • At least one uppercase letter
            • At least one lowercase letter  
            • At least one number
            • At least one special character
            """)
            
            submitted = st.form_submit_button("Create Account", type="primary", use_container_width=True)
            
            if submitted:
                if not all([reg_username, reg_email, reg_password, reg_confirm]):
                    st.error("Please fill in all fields")
                elif reg_password != reg_confirm:
                    st.error("Passwords do not match")
                else:
                    success, message = auth_manager.create_user(
                        reg_username, reg_email, reg_password, is_admin=False
                    )
                    
                    if success:
                        st.success(message + " Please sign in with your new account.")
                    else:
                        st.error(message)

def show_admin_setup():
    """Show initial admin user setup"""
    
    st.markdown("""
    <div style="max-width: 500px; margin: 0 auto; padding: 2rem;">
        <div style="text-align: center; margin-bottom: 2rem;">
            <h1>👔 Personal Stylist AI</h1>
            <h3>🔧 Initial Setup</h3>
            <p>Create your administrator account to get started</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("admin_setup_form"):
        st.subheader("Create Administrator Account")
        
        admin_username = st.text_input("Administrator Username")
        admin_email = st.text_input("Administrator Email") 
        admin_password = st.text_input("Administrator Password", type="password")
        admin_confirm = st.text_input("Confirm Password", type="password")
        
        # Security notice
        st.info("""
        🔒 **Security Notice**: This account will have full administrative access.
        Choose a strong password as this system will be accessible via the internet.
        """)
        
        # Password requirements
        st.caption("""
        Password requirements:
        • At least 8 characters long
        • At least one uppercase letter
        • At least one lowercase letter  
        • At least one number
        • At least one special character
        """)
        
        submitted = st.form_submit_button("Create Administrator", type="primary", use_container_width=True)
        
        if submitted:
            if not all([admin_username, admin_email, admin_password, admin_confirm]):
                st.error("Please fill in all fields")
            elif admin_password != admin_confirm:
                st.error("Passwords do not match")
            else:
                auth_manager = AuthenticationManager()
                success, message = auth_manager.create_user(
                    admin_username, admin_email, admin_password, is_admin=True
                )
                
                if success:
                    st.success(message + " You can now sign in!")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error(message)

def logout_user():
    """Logout current user"""
    
    if st.session_state.session_id:
        auth_manager = AuthenticationManager()
        auth_manager.logout_user(st.session_state.session_id)
    
    # Clear session state
    st.session_state.authenticated = False
    st.session_state.user_id = None
    st.session_state.user_info = None
    st.session_state.session_id = None
    
    st.rerun()

def require_authentication(func):
    """Decorator to require authentication for functions"""
    def wrapper(*args, **kwargs):
        if not check_authentication():
            show_login_page()
            return None
        return func(*args, **kwargs)
    return wrapper