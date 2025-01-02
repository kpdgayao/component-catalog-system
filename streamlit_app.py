import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime
import uuid

# Initialize Supabase client
url = st.secrets["supabase_url"]
key = st.secrets["supabase_key"]
supabase: Client = create_client(url, key)

# Session state initialization
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None

def login():
    st.title("Component Catalog System")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type='password')
        submitted = st.form_submit_button("Login")
        
        if submitted:
            try:
                response = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                st.session_state.authenticated = True
                st.session_state.user_role = "developer"  # You can implement role fetching from Supabase
                st.success("Login successful!")
                st.rerun()
            except Exception as e:
                st.error("Login failed. Please check your credentials.")

def view_component_library():
    st.header("Component Library")
    
    # Search and filters
    search_query = st.text_input("Search components")
    
    # Fetch components from Supabase
    try:
        response = supabase.table('components').select("*").execute()
        components = pd.DataFrame(response.data)
        
        if not components.empty:
            for _, component in components.iterrows():
                with st.expander(f"{component['name']}"):
                    st.write(f"Description: {component['description']}")
                    if st.button(f"Edit {component['name']}", key=f"edit_{component['id']}"):
                        st.session_state.selected_component = component['id']
                        st.session_state.current_view = "edit_component"
        else:
            st.info("No components found")
    except Exception as e:
        st.error(f"Error fetching components: {str(e)}")

def add_component():
    st.header("Add New Component")
    
    with st.form("add_component_form"):
        name = st.text_input("Component Name")
        description = st.text_area("Description")
        
        submitted = st.form_submit_button("Add Component")
        if submitted:
            try:
                new_component = {
                    "id": str(uuid.uuid4()),
                    "name": name,
                    "description": description,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                supabase.table('components').insert(new_component).execute()
                st.success("Component added successfully!")
            except Exception as e:
                st.error(f"Error adding component: {str(e)}")

def analytics_dashboard():
    st.header("Analytics Dashboard")
    
    try:
        # Fetch components count
        components_count = len(supabase.table('components').select("*").execute().data)
        st.metric("Total Components", components_count)
        
        # Add more analytics as needed
        st.info("More detailed analytics coming soon!")
    except Exception as e:
        st.error(f"Error fetching analytics: {str(e)}")

def main():
    if not st.session_state.authenticated:
        login()
    else:
        # Sidebar navigation
        st.sidebar.title("Navigation")
        view = st.sidebar.radio(
            "Select View",
            ["Component Library", "Add Component", "Analytics Dashboard"]
        )
        
        # Logout button
        if st.sidebar.button("Logout"):
            st.session_state.authenticated = False
            st.rerun()
        
        # Main content
        if view == "Component Library":
            view_component_library()
        elif view == "Add Component":
            add_component()
        elif view == "Analytics Dashboard":
            analytics_dashboard()

if __name__ == '__main__':
    main()
