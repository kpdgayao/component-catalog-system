"""IOL Inc. Platform main application."""

import streamlit as st
from supabase import create_client, Client
from apps.components.component_app import ComponentApp
from apps.wpr.wpr_app import WPRApp
from apps.auth import (
    initialize_session_state,
    check_session,
    login,
    handle_auth_error
)

# Set page config at the very start
st.set_page_config(
    page_title="IOL Unified Platform",
    page_icon="🏢",
    layout="wide"
)

# Initialize Supabase client
try:
    url = st.secrets["supabase_url"]
    key = st.secrets["supabase_key"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error(f"Failed to connect to Supabase: {str(e)}")
    st.info("Please check your .streamlit/secrets.toml file and ensure your Supabase credentials are correct.")
    st.stop()

class UnifiedApp:
    def __init__(self):
        # Initialize apps
        self.component_app = ComponentApp(supabase)  # Pass supabase directly to constructor
        self.wpr_app = WPRApp(supabase)
        
    def run(self):
        # Initialize session state
        initialize_session_state()
        
        # Handle authentication
        if not check_session(supabase):
            login(supabase)
            return
            
        # Show navigation
        with st.sidebar:
            st.title("IOL Platform")
            st.write(f"Welcome, {st.session_state.user.email}")
            
            # App selection
            apps = ["Component Catalog", "Weekly Progress Report"]
            current_app = st.session_state.get('current_app', 'Component Catalog')
            try:
                default_index = apps.index(current_app)
            except ValueError:
                default_index = 0
                
            selected_app = st.selectbox(
                "Select Application",
                apps,
                index=default_index
            )
            
            # Update current app in session state
            if selected_app != st.session_state.get('current_app'):
                st.session_state.current_app = selected_app
                st.rerun()
            
            st.divider()
            
            # Logout button
            if st.button("Logout", use_container_width=True):
                handle_auth_error()
                st.rerun()
        
        # Render selected app
        if st.session_state.current_app == "Component Catalog":
            self.component_app.render()
        else:
            self.wpr_app.render()

if __name__ == "__main__":
    app = UnifiedApp()
    app.run()
