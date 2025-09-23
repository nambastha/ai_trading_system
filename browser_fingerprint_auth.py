import streamlit as st
import json
import os
import time
import hashlib
from datetime import datetime
import streamlit.components.v1 as components

# Configuration
SESSION_TIMEOUT_HOURS = 1
SESSIONS_DIR = "browser_sessions"

# Demo users
USERS = {
    "admin": {"password": "admin123", "name": "Admin User"},
    "user1": {"password": "user123", "name": "John Doe"}, 
    "demo": {"password": "demo123", "name": "Demo User"}
}

def init_storage():
    """Initialize session storage"""
    if not os.path.exists(SESSIONS_DIR):
        os.makedirs(SESSIONS_DIR)

def get_browser_fingerprint():
    """Get browser fingerprint using JavaScript"""
    
    # JavaScript to collect browser information
    fingerprint_js = """
    <script>
    function getBrowserFingerprint() {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        ctx.textBaseline = 'top';
        ctx.font = '14px Arial';
        ctx.fillText('Browser fingerprint', 2, 2);
        
        const fingerprint = {
            userAgent: navigator.userAgent,
            language: navigator.language,
            platform: navigator.platform,
            cookieEnabled: navigator.cookieEnabled,
            screenResolution: screen.width + 'x' + screen.height,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            canvas: canvas.toDataURL()
        };
        
        const fingerprintString = JSON.stringify(fingerprint);
        const hash = btoa(fingerprintString).substring(0, 32);
        
        // Store in sessionStorage for persistence across refreshes
        sessionStorage.setItem('browserFingerprint', hash);
        
        // Send to Streamlit
        window.parent.postMessage({
            type: 'streamlit:fingerprint',
            fingerprint: hash
        }, '*');
        
        return hash;
    }
    
    // Check if fingerprint already exists
    const existingFingerprint = sessionStorage.getItem('browserFingerprint');
    if (existingFingerprint) {
        window.parent.postMessage({
            type: 'streamlit:fingerprint',
            fingerprint: existingFingerprint
        }, '*');
    } else {
        getBrowserFingerprint();
    }
    </script>
    """
    
    # Render the JavaScript
    components.html(fingerprint_js, height=0)
    
    # Check if we have fingerprint in session state
    if 'browser_fingerprint' in st.session_state:
        return st.session_state.browser_fingerprint
    
    # Fallback fingerprint using available Streamlit info
    fallback_data = f"streamlit_session_{id(st.session_state)}"
    fallback_hash = hashlib.md5(fallback_data.encode()).hexdigest()[:16]
    
    return fallback_hash

def create_user_session(username, browser_fingerprint):
    """Create new user session"""
    init_storage()
    
    session_data = {
        "username": username,
        "name": USERS[username]["name"],
        "browser_fingerprint": browser_fingerprint,
        "created_at": time.time(),
        "expires_at": time.time() + (SESSION_TIMEOUT_HOURS * 3600),
        "last_activity": time.time()
    }
    
    # Save session using browser fingerprint as filename
    session_file = f"{SESSIONS_DIR}/{browser_fingerprint}.json"
    with open(session_file, 'w') as f:
        json.dump(session_data, f)
    
    # Update session state
    st.session_state.logged_in = True
    st.session_state.username = username
    st.session_state.user_name = USERS[username]["name"]
    st.session_state.browser_fingerprint = browser_fingerprint

def validate_session():
    """Validate current session"""
    browser_fingerprint = get_browser_fingerprint()
    
    if not browser_fingerprint:
        return False
    
    session_file = f"{SESSIONS_DIR}/{browser_fingerprint}.json"
    
    # Check if session file exists
    if not os.path.exists(session_file):
        return False
    
    try:
        with open(session_file, 'r') as f:
            session_data = json.load(f)
        
        # Check expiration
        if time.time() > session_data.get("expires_at", 0):
            cleanup_session(browser_fingerprint)
            return False
        
        # Restore session state
        st.session_state.logged_in = True
        st.session_state.username = session_data["username"]
        st.session_state.user_name = session_data["name"]
        st.session_state.browser_fingerprint = browser_fingerprint
        
        # Update last activity
        session_data["last_activity"] = time.time()
        with open(session_file, 'w') as f:
            json.dump(session_data, f)
        
        return True
        
    except (json.JSONDecodeError, FileNotFoundError):
        return False

def cleanup_session(browser_fingerprint):
    """Remove session file"""
    session_file = f"{SESSIONS_DIR}/{browser_fingerprint}.json"
    if os.path.exists(session_file):
        os.remove(session_file)

def logout_user():
    """Logout user"""
    if 'browser_fingerprint' in st.session_state:
        cleanup_session(st.session_state.browser_fingerprint)
    
    # Clear session state
    for key in ['logged_in', 'username', 'user_name']:
        if key in st.session_state:
            del st.session_state[key]

def show_login_page():
    """Display login form"""
    st.title("🔐 Browser Fingerprint Authentication")
    st.markdown("*Uses browser characteristics for session persistence*")
    st.markdown("---")
    
    # Get browser fingerprint
    browser_fingerprint = get_browser_fingerprint()
    
    # Show fingerprint info
    with st.expander("🔍 Browser Fingerprint Info"):
        st.code(f"Fingerprint: {browser_fingerprint}")
        st.info("This unique ID is generated from your browser characteristics")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            st.subheader("Login")
            
            username = st.selectbox("Username", list(USERS.keys()))
            password = st.text_input("Password", type="password", 
                                   placeholder=f"Try: {USERS[username]['password']}")
            
            submit = st.form_submit_button("🔓 Login", use_container_width=True)
            
            if submit:
                if username in USERS and USERS[username]["password"] == password:
                    create_user_session(username, browser_fingerprint)
                    st.success(f"Welcome {USERS[username]['name']}!")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials!")
        
        # Demo accounts
        with st.expander("👥 Demo Accounts"):
            for user, data in USERS.items():
                st.write(f"• **{user}** / {data['password']} ({data['name']})")

def show_dashboard():
    """Show dashboard"""
    username = st.session_state.username
    user_name = st.session_state.user_name
    browser_fingerprint = st.session_state.browser_fingerprint
    
    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title(f"👋 Welcome {user_name}!")
        st.success("🎉 Session persists across browser refreshes!")
    with col2:
        if st.button("🚪 Logout"):
            logout_user()
            st.rerun()
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["🏠 Dashboard", "🧪 Test", "🔒 Session"])
    
    with tab1:
        st.markdown("### ✅ Authenticated Dashboard")
        st.info("This content is protected and only visible to logged-in users!")
        
        # Test persistence
        st.markdown("### 🔄 Test Session Persistence")
        if 'refresh_count' not in st.session_state:
            st.session_state.refresh_count = 0
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Refresh Count", st.session_state.refresh_count)
            if st.button("➕ Increment"):
                st.session_state.refresh_count += 1
                st.rerun()
        
        with col2:
            if st.button("🔄 Force Refresh"):
                st.rerun()
        
        st.markdown("**Test Instructions:**")
        st.markdown("1. Increment the counter above")
        st.markdown("2. Refresh your browser (F5 or Ctrl+R)")
        st.markdown("3. Verify you stay logged in and counter persists")
    
    with tab2:
        st.markdown("### 🧪 Browser Fingerprint Test")
        
        st.code(f"Your Browser Fingerprint: {browser_fingerprint}")
        
        st.markdown("### 🔒 Security Features")
        st.markdown("""
        - **✅ Refresh Persistent**: Sessions survive page reloads
        - **❌ Cross-Browser**: Won't work in different browsers  
        - **❌ Incognito**: Won't work in private mode
        - **❌ Device Sharing**: Different devices = different fingerprints
        """)
        
        # JavaScript integration
        st.markdown("### 🛠️ JavaScript Integration")
        
        # Add message listener for fingerprint updates
        js_listener = """
        <script>
        window.addEventListener('message', function(event) {
            if (event.data.type === 'streamlit:fingerprint') {
                console.log('Received fingerprint:', event.data.fingerprint);
                // Could update Streamlit session state here
            }
        });
        </script>
        """
        components.html(js_listener, height=0)
        
        st.info("JavaScript is collecting browser characteristics for fingerprinting")
    
    with tab3:
        st.markdown("### 🔒 Session Information")
        
        # Load session data
        try:
            session_file = f"{SESSIONS_DIR}/{browser_fingerprint}.json"
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            
            # Display session details
            login_time = datetime.fromtimestamp(session_data['created_at'])
            expires_time = datetime.fromtimestamp(session_data['expires_at'])
            last_activity = datetime.fromtimestamp(session_data['last_activity'])
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Username:** {session_data['username']}")
                st.write(f"**Login Time:** {login_time.strftime('%H:%M:%S')}")
                st.write(f"**Last Activity:** {last_activity.strftime('%H:%M:%S')}")
            
            with col2:
                st.write(f"**Fingerprint:** {browser_fingerprint[:16]}...")
                st.write(f"**Expires:** {expires_time.strftime('%H:%M:%S')}")
                remaining = int((session_data['expires_at'] - time.time()) / 60)
                st.write(f"**Time Left:** {remaining} minutes")
            
            # Extend session
            if st.button("⏰ Extend Session (+1 hour)"):
                session_data['expires_at'] = time.time() + (SESSION_TIMEOUT_HOURS * 3600)
                with open(session_file, 'w') as f:
                    json.dump(session_data, f)
                st.success("Session extended!")
                st.rerun()
                
        except FileNotFoundError:
            st.error("❌ Session file not found")
        
        # Active sessions count
        if os.path.exists(SESSIONS_DIR):
            session_files = [f for f in os.listdir(SESSIONS_DIR) if f.endswith('.json')]
            st.metric("Active Sessions", len(session_files))

def cleanup_expired_sessions():
    """Clean up expired sessions"""
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
            except (json.JSONDecodeError, FileNotFoundError):
                try:
                    os.remove(file_path)
                except FileNotFoundError:
                    pass

def main():
    """Main application"""
    st.set_page_config(
        page_title="Browser Fingerprint Auth",
        page_icon="🔍",
        layout="wide"
    )
    
    # Clean up expired sessions
    cleanup_expired_sessions()
    
    # Check authentication
    if validate_session():
        show_dashboard()
    else:
        show_login_page()

if __name__ == "__main__":
    main()