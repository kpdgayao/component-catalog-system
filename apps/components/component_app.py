"""Component Library Application."""

import streamlit as st
from typing import Optional
from .views import view_component_library, view_component_details, analytics_dashboard, manage_metadata
from .forms import component_form, add_component, edit_component

class ComponentApp:
    def __init__(self, supabase=None):
        """Initialize ComponentApp with optional supabase client."""
        self.supabase = supabase
        
        # Initialize all session state variables
        default_states = {
            'current_component': None,
            'editing': False,
            'show_analytics': False,
            'show_metadata': False,
            'adding_component': False,
            'editing_category': None,
            'editing_tag': None,
            'confirm_delete': None,
            'confirm_delete_type': None,
            'metadata_operation': None,
            'last_operation_status': None,
            'last_operation_message': None
        }
        
        # Initialize all states at once
        for key, default_value in default_states.items():
            if key not in st.session_state:
                st.session_state[key] = default_value

    def render(self):
        """Run the component library application."""
        if not self.supabase:
            st.error("Supabase client not initialized")
            return

        # Sidebar navigation
        with st.sidebar:
            st.title("Navigation")
            
            # Add Component button at the top
            if st.button("➕ Add Component", use_container_width=True):
                st.session_state.adding_component = True
                st.session_state.current_component = None
                st.session_state.editing = False
                st.session_state.show_analytics = False
                st.session_state.show_metadata = False
                st.rerun()
            
            st.divider()
            
            if st.button("📚 Component Library", use_container_width=True):
                st.session_state.current_component = None
                st.session_state.editing = False
                st.session_state.show_analytics = False
                st.session_state.show_metadata = False
                st.session_state.adding_component = False
                st.rerun()
                
            if st.button("📊 Analytics", use_container_width=True):
                st.session_state.show_analytics = True
                st.session_state.current_component = None
                st.session_state.editing = False
                st.session_state.show_metadata = False
                st.session_state.adding_component = False
                st.rerun()
                
            if st.button("🏷️ Manage Metadata", use_container_width=True):
                st.session_state.show_metadata = True
                st.session_state.current_component = None
                st.session_state.editing = False
                st.session_state.show_analytics = False
                st.session_state.adding_component = False
                st.rerun()

        # Main content
        if st.session_state.adding_component:
            add_component(self.supabase)
        elif st.session_state.show_analytics:
            analytics_dashboard(self.supabase)
        elif st.session_state.show_metadata:
            manage_metadata(self.supabase)
        elif st.session_state.current_component:
            if st.session_state.editing:
                # Fetch component data for editing
                response = self.supabase.table('components').select(
                    "*",
                    "categories(name)",
                    "component_tags(tags(name))"
                ).eq('id', st.session_state.current_component).single().execute()
                
                if response.data:
                    component_form(self.supabase, mode="edit", component_data=response.data)
                else:
                    st.error("Component not found!")
            else:
                view_component_details(self.supabase, st.session_state.current_component)
        else:
            view_component_library(self.supabase)
