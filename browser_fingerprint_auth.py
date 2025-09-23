import streamlit as st
import json
import os
import time
import secrets
import hashlib
import requests
from datetime import datetime

# Configuration
SESSION_TIMEOUT_HOURS = 1
SESSIONS_DIR = "simple_sessions"

# SSO Server Configuration
SSO_SERVER_URL = "http://localhost:5000"

def init_storage():
    """Initialize session storage"""
    if not os.path.exists(SESSIONS_DIR):
        os.makedirs(SESSIONS_DIR)

def get_browser_id():
    """Simple browser identification using headers"""
    try:
        # Try to get some browser info from streamlit context
        user_agent = st.context.headers.get("User-Agent", "unknown")
        # Create a simple hash from user agent
        browser_hash = hashlib.md5(user_agent.encode()).hexdigest()[:16]
        return f"browser_{browser_hash}"
    except:
        # Fallback - use session state with persistence
        if 'browser_id' not in st.session_state:
            st.session_state.browser_id = f"browser_{secrets.token_hex(8)}"
        return st.session_state.browser_id

def get_session_token():
    """Get session token from URL or create new one"""
    # Check URL parameters first
    query_params = st.query_params
    
    if 'token' in query_params:
        token = query_params['token']
        # Store in session state for persistence
        st.session_state.session_token = token
        return token
    
    # Check session state
    if 'session_token' in st.session_state:
        token = st.session_state.session_token
        # Make sure it's in URL too
        st.query_params['token'] = token
        return token
    
    # Create new token
    token = secrets.token_urlsafe(32)
    st.session_state.session_token = token
    st.query_params['token'] = token
    return token

def create_user_session(user_info):
    """Create user session with SSO user info"""
    init_storage()
    
    token = get_session_token()
    browser_id = get_browser_id()
    
    session_data = {
        "username": user_info.get("email", user_info.get("user_id")),
        "name": user_info.get("name", "Unknown User"),
        "email": user_info.get("email"),
        "role": user_info.get("role", "user"),
        "user_id": user_info.get("user_id"),
        "token": token,
        "browser_id": browser_id,
        "created_at": time.time(),
        "expires_at": time.time() + (SESSION_TIMEOUT_HOURS * 3600),
        "last_activity": time.time()
    }
    
    # Save session using token as filename
    session_file = f"{SESSIONS_DIR}/{token}.json"
    with open(session_file, 'w') as f:
        json.dump(session_data, f)
    
    # Set session state
    st.session_state.logged_in = True
    st.session_state.username = session_data["username"]
    st.session_state.user_name = session_data["name"]
    st.session_state.user_info = user_info

def validate_session():
    """Validate current session"""
    token = get_session_token()
    browser_id = get_browser_id()
    
    session_file = f"{SESSIONS_DIR}/{token}.json"
    
    # Check if session file exists
    if not os.path.exists(session_file):
        return False
    
    try:
        with open(session_file, 'r') as f:
            session_data = json.load(f)
        
        # Check if browser ID matches (basic security)
        stored_browser_id = session_data.get("browser_id")
        if stored_browser_id and stored_browser_id != browser_id:
            # Different browser - reject silently and create new session
            cleanup_session(token)
            return False
        
        # Check expiration
        if time.time() > session_data.get("expires_at", 0):
            cleanup_session(token)
            return False
        
        # Valid session - restore state
        st.session_state.logged_in = True
        st.session_state.username = session_data["username"]
        st.session_state.user_name = session_data["name"]
        st.session_state.user_info = {
            "email": session_data.get("email"),
            "role": session_data.get("role"),
            "user_id": session_data.get("user_id")
        }
        
        # Update last activity
        session_data["last_activity"] = time.time()
        with open(session_file, 'w') as f:
            json.dump(session_data, f)
        
        return True
        
    except (json.JSONDecodeError, FileNotFoundError):
        return False

def cleanup_session(token):
    """Remove session file"""
    session_file = f"{SESSIONS_DIR}/{token}.json"
    if os.path.exists(session_file):
        os.remove(session_file)

def logout_user():
    """Logout user"""
    token = get_session_token()
    cleanup_session(token)
    
    # Clear everything
    if 'token' in st.query_params:
        del st.query_params['token']
    
    for key in ['logged_in', 'username', 'user_name', 'user_info', 'session_token', 'browser_id']:
        if key in st.session_state:
            del st.session_state[key]

def check_sso_server():
    """Check if SSO server is running"""
    try:
        response = requests.get(f"{SSO_SERVER_URL}/health", timeout=2)
        return response.status_code == 200
    except requests.RequestException:
        return False

def handle_sso_login():
    """Handle SSO login flow"""
    query_params = st.query_params
    
    # Check for OAuth callback
    if 'code' in query_params and 'state' in query_params:
        auth_code = query_params.get('code')
        state = query_params.get('state')
        
        # Verify state
        if state != st.session_state.get('oauth_state'):
            st.error("Invalid OAuth state")
            return None
        
        try:
            # Exchange code for token
            token_response = requests.post(
                f"{SSO_SERVER_URL}/oauth/token",
                data={
                    'code': auth_code,
                    'client_id': 'streamlit_app',
                    'grant_type': 'authorization_code'
                },
                timeout=10
            )
            
            if token_response.status_code != 200:
                st.error("Failed to get access token")
                return None
            
            token_data = token_response.json()
            access_token = token_data.get('access_token')
            
            # Get user info
            user_response = requests.get(
                f"{SSO_SERVER_URL}/oauth/userinfo",
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=10
            )
            
            if user_response.status_code != 200:
                st.error("Failed to get user info")
                return None
            
            user_info = user_response.json()
            
            # Clear OAuth params
            del st.query_params['code']
            del st.query_params['state']
            
            return user_info
            
        except requests.RequestException as e:
            st.error(f"SSO error: {str(e)}")
            return None
    
    return None

def show_login_page():
    """Show SSO login page"""
    st.title("🔐 SSO Authentication")
    st.markdown("*Secure login with local SSO server*")
    st.markdown("---")
    
    # Check for SSO callback
    user_info = handle_sso_login()
    if user_info:
        create_user_session(user_info)
        st.success(f"Welcome {user_info['name']}!")
        st.rerun()
    
    # Check SSO server status
    if not check_sso_server():
        st.error("❌ SSO Server not running!")
        st.markdown("### 🚀 Start SSO Server")
        st.code("python local_sso_server.py")
        st.info("The SSO server must be running on http://localhost:5000")
        return
    
    st.success("✅ SSO Server is running")
    
    # Show login button
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("🔐 Login with SSO")
        
        if st.button("🚀 Login with Local SSO", use_container_width=True):
            # Generate OAuth state
            state = secrets.token_urlsafe(32)
            st.session_state.oauth_state = state
            
            # Build OAuth URL
            oauth_url = f"{SSO_SERVER_URL}/oauth/authorize"
            oauth_params = f"?client_id=streamlit_app&redirect_uri=http://localhost:8502&state={state}&response_type=code"
            
            full_oauth_url = oauth_url + oauth_params
            
            # Redirect to SSO
            st.markdown(f'<meta http-equiv="refresh" content="0;url={full_oauth_url}">', unsafe_allow_html=True)
            st.info("Redirecting to SSO server...")
    
    # Show available accounts
    with st.expander("👥 Available SSO Accounts"):
        st.markdown("""
        **Demo accounts on SSO server:**
        - **admin** / admin123 (Admin User)
        - **user1** / user123 (John Doe)
        - **user2** / user123 (Jane Smith)
        - **demo** / demo123 (Demo User)
        """)
    
    # Show debug info
    token = get_session_token()
    browser_id = get_browser_id()
    
    with st.expander("🔧 Debug Info"):
        st.write(f"**Session Token:** {token[:16]}...")
        st.write(f"**Browser ID:** {browser_id}")
        st.write(f"**SSO Server:** {SSO_SERVER_URL}")
        st.info("Session persists on refresh, blocks URL sharing")

def show_dashboard():
    """Show dashboard"""
    username = st.session_state.username
    user_name = st.session_state.user_name
    user_info = st.session_state.get('user_info', {})
    token = get_session_token()
    
    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title(f"👋 Welcome {user_name}!")
        st.success("🔐 Authenticated via SSO")
    with col2:
        if st.button("🚪 Logout"):
            logout_user()
            st.rerun()
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["🔄 Test Refresh", "👤 Profile", "🔒 Session Info"])
    
    with tab1:
        st.markdown("### 🔄 Session Persistence Test")
        
        if 'counter' not in st.session_state:
            st.session_state.counter = 0
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Counter", st.session_state.counter)
        
        with col2:
            if st.button("➕ Add 1"):
                st.session_state.counter += 1
                st.rerun()
        
        with col3:
            if st.button("🔄 Refresh"):
                st.rerun()
        
        st.markdown("### 📋 Test Instructions")
        st.markdown("""
        **✅ Refresh Test:**
        1. Click "Add 1" to increment counter
        2. Refresh browser (F5/Ctrl+R)
        3. You should stay logged in with counter preserved
        
        **❌ URL Sharing Test:**
        1. Copy current URL from address bar
        2. Open different browser (Chrome→Safari)
        3. Paste URL - both users will be logged out!
        """)
    
    with tab2:
        st.markdown("### 👤 SSO User Profile")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Name:** {user_name}")
            st.write(f"**Email:** {user_info.get('email', 'N/A')}")
            st.write(f"**User ID:** {user_info.get('user_id', 'N/A')}")
        
        with col2:
            st.write(f"**Role:** {user_info.get('role', 'user')}")
            st.write(f"**Username:** {username}")
            st.write(f"**Provider:** Local SSO")
        
        # Notes that persist
        if 'user_notes' not in st.session_state:
            st.session_state.user_notes = ""
        
        st.markdown("### 📝 Persistent Notes")
        notes = st.text_area("Your notes (survive refresh):", 
                           value=st.session_state.user_notes, height=100)
        
        if notes != st.session_state.user_notes:
            st.session_state.user_notes = notes
            st.success("Notes saved! Try refreshing...")
    
    with tab3:
        st.markdown("### 🔒 Session Details")
        
        try:
            session_file = f"{SESSIONS_DIR}/{token}.json"
            if os.path.exists(session_file):
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    login_time = datetime.fromtimestamp(session_data['created_at'])
                    st.write(f"**Login Time:** {login_time.strftime('%H:%M:%S')}")
                    st.write(f"**Email:** {session_data.get('email', 'N/A')}")
                    st.write(f"**Role:** {session_data.get('role', 'user')}")
                
                with col2:
                    expires_time = datetime.fromtimestamp(session_data['expires_at'])
                    st.write(f"**Expires:** {expires_time.strftime('%H:%M:%S')}")
                    remaining = int((session_data['expires_at'] - time.time()) / 60)
                    st.write(f"**Time Left:** {remaining} minutes")
                    st.write(f"**Session Token:** {token[:16]}...")
                
                # Extend session
                if st.button("⏰ Extend Session (+1 hour)"):
                    session_data['expires_at'] = time.time() + (SESSION_TIMEOUT_HOURS * 3600)
                    with open(session_file, 'w') as f:
                        json.dump(session_data, f)
                    st.success("Session extended!")
                    st.rerun()
            
        except (FileNotFoundError, json.JSONDecodeError):
            st.error("Session file not found")

def cleanup_expired_sessions():
    """Clean expired sessions"""
    if not os.path.exists(SESSIONS_DIR):
        return
    
    current_time = time.time()
    for filename in os.listdir(SESSIONS_DIR):
        if filename.endswith('.json'):
            file_path = os.path.join(SESSIONS_DIR, filename)
            try:
                with open(file_path, 'r') as f:
                    session_data = json.load(f)
                
                if current_time > session_data.get("expires_at", 0):
                    os.remove(file_path)
            except:
                try:
                    os.remove(file_path)
                except:
                    pass

def main():
    """Main app"""
    st.set_page_config(
        page_title="SSO Authentication",
        page_icon="🔐",
        layout="wide"
    )
    
    cleanup_expired_sessions()
    
    if validate_session():
        show_dashboard()
    else:
        show_login_page()

if __name__ == "__main__":
    main()
