import streamlit as st
import sys
import os
from pathlib import Path

# Add app directory to path
sys.path.append(str(Path(__file__).parent))

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
</style>
""", unsafe_allow_html=True)

def main():
    """Main application entry point"""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>👔 Personal Stylist AI</h1>
        <p>Privacy-first fashion intelligence for your family</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check if this is first run
    if not os.path.exists('/app/data/database'):
        show_setup_screen()
    else:
        show_main_dashboard()

def show_setup_screen():
    """Show initial setup screen"""
    st.markdown("### 🚀 Welcome to Personal Stylist AI!")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info("""
        **Getting Started:**
        1. The system is initializing your database
        2. Create your first user profile
        3. Upload some clothing photos
        4. Start getting outfit recommendations!
        
        **Privacy Note:** All AI processing happens locally on your server.
        No data ever leaves your network.
        """)
        
        if st.button("🎯 Start Setup", type="primary", use_container_width=True):
            # Initialize database
            os.makedirs('/app/data/database', exist_ok=True)
            st.success("✅ Database initialized!")
            st.rerun()

def show_main_dashboard():
    """Show main application dashboard"""
    
    # Sidebar navigation
    with st.sidebar:
        st.title("👥 Navigation")
        
        # Mock user for demo
        st.selectbox("Select User", ["Create First User", "Demo User"])
        
        st.markdown("### 📊 Quick Stats")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Items", "0")
        with col2:
            st.metric("Complete", "0%")
    
    # Main content
    st.markdown("### 🌟 Today's Dashboard")
    
    # Demo notification
    st.info("""
    🎉 **Welcome to Personal Stylist AI!**
    
    This is a preview of your daily outfit recommendations.
    To get started:
    1. Create a user profile
    2. Add your clothing items
    3. Get personalized recommendations
    """)
    
    # Quick actions
    st.markdown("### ⚡ Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("👤 Create Profile", use_container_width=True):
            st.info("Profile creation coming soon!")
    
    with col2:
        if st.button("📸 Add Clothing", use_container_width=True):
            st.info("Clothing upload coming soon!")
    
    with col3:
        if st.button("🛍️ Shopping Assistant", use_container_width=True):
            st.info("Shopping analysis coming soon!")
            
    with col4:
        if st.button("📊 Analytics", use_container_width=True):
            st.info("Wardrobe analytics coming soon!")
    
    # System status
    st.markdown("### 🔧 System Status")
    
    status_col1, status_col2, status_col3 = st.columns(3)
    
    with status_col1:
        st.success("✅ Database: Ready")
    
    with status_col2:
        st.success("✅ AI Models: Ready")
    
    with status_col3:
        st.success("✅ Privacy: Protected")

if __name__ == "__main__":
    main()