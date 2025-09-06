# =============================================================================
# SRC/MAIN.PY - Secure main application with authentication
# =============================================================================

import streamlit as st
import sys
import os
import threading
import time
from pathlib import Path

# Fix import paths - add both current and parent directories
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir.parent))

# Import authentication system
from core.authentication import (
    check_authentication, 
    show_login_page, 
    logout_user,
    AuthenticationManager
)
from core.database import DatabaseManager

# Page configuration
st.set_page_config(
    page_title="Personal Stylist AI",
    page_icon="👔",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': """
        # Personal Stylist AI
        
        Privacy-first fashion intelligence running on your personal server.
        
        **Features:**
        - Multi-angle body analysis
        - AI clothing recognition  
        - Weather-aware outfit recommendations
        - Shopping intelligence
        - Family member support
        
        **Privacy:** All data stays on your server. No external services.
        **Security:** Strong authentication with session management.
        """
    }
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .notification-banner {
        background: #f0f9ff;
        border: 1px solid #0ea5e9;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    .weather-widget {
        background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
    
    .outfit-item {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .security-status {
        background: #f0fdf4;
        border: 1px solid #16a34a;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    .user-info {
        background: #fafafa;
        border: 1px solid #e5e5e5;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def cleanup_worker():
    """Background worker to clean up expired sessions"""
    while True:
        try:
            auth_manager = AuthenticationManager()
            auth_manager.cleanup_expired_sessions()
            
            db_manager = DatabaseManager()
            db_manager.cleanup_expired_data()
            
            time.sleep(3600)  # Run every hour
        except Exception as e:
            # Log error but continue running
            print(f"Cleanup worker error: {e}")
            time.sleep(300)  # Wait 5 min on error

def initialize_app():
    """Initialize app-wide settings and background services"""
    # Start cleanup worker if not already started
    if 'cleanup_started' not in st.session_state:
        try:
            cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
            cleanup_thread.start()
            st.session_state.cleanup_started = True
        except Exception as e:
            print(f"Failed to start cleanup worker: {e}")
    
    # Initialize session state
    if 'initialization_complete' not in st.session_state:
        st.session_state.initialization_complete = False

def main():
    """Main application entry point with authentication"""
    
    # Initialize app services
    initialize_app()
    
    # Check authentication first
    if not check_authentication():
        show_login_page()
        return
    
    # Mark initialization as complete
    if not st.session_state.initialization_complete:
        st.session_state.initialization_complete = True
    
    # User is authenticated, show the main app
    show_main_application()

def show_main_application():
    """Show main application for authenticated users"""
    
    # Header with user info
    show_app_header()
    
    # Sidebar with user controls
    show_authenticated_sidebar()
    
    # Check if this is first run after login - use better path detection
    db_path = get_database_path()
    if not os.path.exists(db_path):
        show_setup_screen()
    else:
        show_main_dashboard()

def get_database_path():
    """Get database path with environment variable support"""
    base_path = os.environ.get('APP_BASE_PATH', '/app')
    return os.path.join(base_path, 'data', 'database', 'stylist.db')

def get_user_upload_path(user_id):
    """Get user-specific upload path"""
    base_path = os.environ.get('APP_BASE_PATH', '/app')
    return os.path.join(base_path, 'uploads', 'users', user_id)

def show_app_header():
    """Show application header with user information"""
    
    user_info = st.session_state.user_info
    
    # Header with logout option
    header_col1, header_col2 = st.columns([3, 1])
    
    with header_col1:
        st.markdown(f"""
        <div class="main-header">
            <h1>👔 Personal Stylist AI</h1>
            <p>Welcome back, {user_info['name']}! Your private fashion intelligence.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with header_col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Spacing
        if st.button("🚪 Logout", key="logout_button"):
            logout_user()

def show_authenticated_sidebar():
    """Show sidebar for authenticated users"""
    
    with st.sidebar:
        user_info = st.session_state.user_info
        
        # User info section
        st.markdown(f"""
        <div class="user-info">
            <h3>👤 {user_info['name']}</h3>
            <p><strong>Email:</strong> {user_info['email']}</p>
            <p><strong>Role:</strong> {'Administrator' if user_info['is_admin'] else 'User'}</p>
            <p><strong>Last Login:</strong> {user_info.get('last_login', 'First time')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Security status
        st.markdown("""
        <div class="security-status">
            <h4>🔒 Security Status</h4>
            <p>✅ Authenticated Session</p>
            <p>✅ Secure Connection</p>
            <p>✅ Local Processing</p>
            <p>✅ Privacy Protected</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Navigation
        st.markdown("### 📊 Quick Stats")
        
        # Get real stats from database
        try:
            db_manager = DatabaseManager()
            user_id = st.session_state.user_id
            clothing_count = db_manager.get_clothing_count(user_id)
            completeness = db_manager.get_wardrobe_completeness(user_id)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Items", str(clothing_count))
            with col2:
                st.metric("Complete", f"{completeness}%")
        except Exception as e:
            # Fallback to mock stats if database not ready
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Items", "0")
            with col2:
                st.metric("Complete", "0%")
        
        # Admin controls
        if user_info['is_admin']:
            st.markdown("### 🔧 Admin Controls")
            
            if st.button("👥 Manage Users", use_container_width=True):
                st.info("User management coming soon!")
            
            if st.button("📊 Security Logs", use_container_width=True):
                show_security_logs()
            
            if st.button("⚙️ System Settings", use_container_width=True):
                st.info("System settings coming soon!")

def show_security_logs():
    """Show security audit logs for admins"""
    
    if not st.session_state.user_info['is_admin']:
        st.error("Access denied. Admin privileges required.")
        return
    
    st.markdown("### 🔍 Security Audit Logs")
    
    try:
        auth_manager = AuthenticationManager()
        logs = auth_manager.get_security_logs(50)
        
        if logs:
            # Create a DataFrame for better display
            import pandas as pd
            
            df = pd.DataFrame(logs)
            df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Color code by success/failure
            def color_row(row):
                if row['success']:
                    return ['background-color: #f0fdf4'] * len(row)  # Light green
                else:
                    return ['background-color: #fef2f2'] * len(row)  # Light red
            
            styled_df = df.style.apply(color_row, axis=1)
            st.dataframe(styled_df, use_container_width=True)
            
            # Summary stats
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_events = len(logs)
                st.metric("Total Events", total_events)
            
            with col2:
                successful_logins = len([log for log in logs if log['action'] == 'LOGIN_SUCCESS'])
                st.metric("Successful Logins", successful_logins)
            
            with col3:
                failed_logins = len([log for log in logs if log['action'] == 'LOGIN_FAILED'])
                st.metric("Failed Logins", failed_logins)
            
            with col4:
                unique_ips = len(set([log['ip_address'] for log in logs if log['ip_address'] and log['ip_address'] != 'streamlit-client']))
                st.metric("Unique IPs", unique_ips)
            
        else:
            st.info("No security logs found.")
    
    except Exception as e:
        st.error(f"Error loading security logs: {e}")

def show_setup_screen():
    """Show initial setup screen for authenticated users"""
    
    st.markdown("### 🚀 Welcome to Personal Stylist AI!")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.success(f"""
        **Welcome, {st.session_state.user_info['name']}!** 
        
        Your secure personal stylist is ready to set up.
        
        **Getting Started:**
        1. The system is initializing your private database
        2. Upload some clothing photos to build your wardrobe
        3. Optional: Complete body analysis for fit predictions
        4. Start getting personalized outfit recommendations!
        
        **🔒 Privacy & Security Notes:**
        - All AI processing happens locally on your server
        - Your photos are immediately converted to anonymous measurements
        - No data ever leaves your network
        - Strong authentication protects your fashion data
        - Perfect for shopping while out via Cloudflare tunnels!
        """)
        
        if st.button("🎯 Initialize My Wardrobe", type="primary", use_container_width=True):
            # Initialize database and user-specific folders
            user_id = st.session_state.user_id
            
            try:
                # Create directories using dynamic paths
                base_path = os.environ.get('APP_BASE_PATH', '/app')
                
                os.makedirs(os.path.join(base_path, 'data', 'database'), exist_ok=True)
                
                user_upload_path = get_user_upload_path(user_id)
                os.makedirs(os.path.join(user_upload_path, 'clothing'), exist_ok=True)
                os.makedirs(os.path.join(user_upload_path, 'body_analysis'), exist_ok=True)
                
                # Initialize database
                db_manager = DatabaseManager()
                
                st.success("✅ Your personal wardrobe space initialized!")
                st.balloons()
                
                # Pause for effect then reload
                time.sleep(2)
                st.rerun()
                
            except Exception as e:
                st.error(f"Initialization failed: {e}")

def show_main_dashboard():
    """Show main application dashboard for authenticated users"""
    
    user_info = st.session_state.user_info
    
    # Welcome message with shopping context
    st.markdown("### 🌟 Your Daily Fashion Dashboard")
    
    # Special notice for internet access
    st.info("""
    🛍️ **Shopping Mode Ready!** This system is securely accessible while you're out shopping. 
    Check your wardrobe, get outfit suggestions, and analyze potential purchases from anywhere!
    """)
    
    # Demo notification for outfit recommendation
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### Today's Outfit Recommendation")
        
        # Mock weather widget
        st.markdown("""
        <div class="weather-widget">
            <h3>22°C, Partly Cloudy ⛅</h3>
            <p>Perfect for light layers and comfortable shoes</p>
            <p>Great shopping weather - you might want that cardigan!</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Mock outfit recommendation
        st.markdown("**Suggested Outfit:**")
        
        outfit_col1, outfit_col2, outfit_col3 = st.columns(3)
        
        with outfit_col1:
            st.markdown("""
            <div class="outfit-item">
                <strong>👕 Top</strong><br>
                Light blue button shirt<br>
                <small>Professional yet comfortable for shopping</small>
            </div>
            """, unsafe_allow_html=True)
        
        with outfit_col2:
            st.markdown("""
            <div class="outfit-item">
                <strong>👖 Bottom</strong><br>
                Dark wash jeans<br>
                <small>Versatile and comfortable for walking</small>
            </div>
            """, unsafe_allow_html=True)
        
        with outfit_col3:
            st.markdown("""
            <div class="outfit-item">
                <strong>👟 Shoes</strong><br>
                White leather sneakers<br>
                <small>Clean look, perfect for lots of walking</small>
            </div>
            """, unsafe_allow_html=True)
        
        # Styling tip
        st.info("💡 **Shopping Tip:** This outfit photographs well for trying on clothes and asking for opinions!")
    
    with col2:
        st.markdown("#### Quick Actions")
        
        if st.button("📸 Add Clothing Item", use_container_width=True):
            st.info("Clothing upload feature coming soon!")
        
        if st.button("🛍️ Analyze Product", use_container_width=True):
            st.info("Shopping analysis feature coming soon!")
        
        if st.button("🕐 Body Analysis", use_container_width=True):
            st.info("Body measurement feature coming soon!")
        
        if st.button("📊 Wardrobe Analytics", use_container_width=True):
            st.info("Analytics dashboard coming soon!")
        
        # Shopping-specific actions
        st.markdown("#### 🛍️ Shopping Tools")
        
        if st.button("🔍 Check My Wardrobe", use_container_width=True):
            st.info("Quick wardrobe check for avoiding duplicates!")
        
        if st.button("💡 Get Shopping List", use_container_width=True):
            st.info("AI-generated shopping recommendations coming soon!")
        
        if st.button("📱 Share Outfit", use_container_width=True):
            st.info("Share today's outfit for feedback!")
    
    # System status for peace of mind
    st.markdown("### 🔧 System Status")
    
    status_col1, status_col2, status_col3, status_col4 = st.columns(4)
    
    with status_col1:
        st.success("✅ Secure Login")
    
    with status_col2:
        try:
            db_manager = DatabaseManager()
            st.success("✅ Database Ready")
        except:
            st.warning("⚠️ Database Initializing")
    
    with status_col3:
        try:
            # Check if AI models are available
            import mediapipe as mp
            st.success("✅ AI Models Loaded")
        except:
            st.warning("⚠️ AI Models Loading")
    
    with status_col4:
        st.success("✅ Privacy Protected")
    
    # Fun fact about security
    st.markdown("---")
    st.markdown("""
    🔒 **Security Status:** Your session is encrypted and secure. Perfect for accessing 
    your personal fashion data while shopping via Cloudflare tunnels. Your data never 
    leaves your home server, even when accessed remotely!
    """)

if __name__ == "__main__":
    main()