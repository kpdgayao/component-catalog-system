"""Main WPR application module."""

import streamlit as st
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from supabase import Client
from .config import WPRConfig
from .database import WPRDatabase
from .ui import WPRUI

logger = logging.getLogger(__name__)

class WPRApp:
    def __init__(self, supabase: Optional[Client] = None):
        """Initialize the WPR application."""
        self.supabase = supabase
        self.config = WPRConfig()
        self.database = WPRDatabase(supabase)
        self.ui = WPRUI(self.config, self.database)
        
        # Initialize session state
        if 'wpr_week_number' not in st.session_state:
            st.session_state.wpr_week_number = datetime.now().isocalendar()[1]
        if 'wpr_year' not in st.session_state:
            st.session_state.wpr_year = datetime.now().year
            
    def _handle_authentication(self) -> bool:
        """Handle user authentication."""
        try:
            # Check if authenticated in main app
            if not st.session_state.get('authenticated', False):
                return False
                
            # Get user from main app session
            user = st.session_state.get('user')
            if not user:
                return False
                
            # Get user profile
            user_profile = self.database.get_user_profile(user.email)
            if not user_profile:
                logger.warning(f"No profile found for user: {user.email}")
                return False
                
            # Store profile in session
            st.session_state.wpr_user_profile = user_profile
            st.session_state.wpr_selected_name = user.email
            
            return True
            
        except Exception as e:
            logger.error(f"Error in authentication: {str(e)}")
            return False
            
    def render(self):
        """Render the WPR application."""
        try:
            # Render header
            self.ui.render_header()
            
            # Handle authentication
            if not self._handle_authentication():
                st.error("Please log in to access the WPR application.")
                return
                
            # Main application logic
            if st.session_state.wpr_user_profile:
                if st.session_state.wpr_user_profile.get('role', '').lower() in ['hr', 'admin']:
                    self.ui.render_hr_view()
                else:
                    self.ui.render_employee_view()
            else:
                st.error("Please log in to access the WPR application.")
                
        except Exception as e:
            logger.error(f"Error rendering application: {str(e)}")
            st.error("An error occurred while rendering the application. Please try again later.")
