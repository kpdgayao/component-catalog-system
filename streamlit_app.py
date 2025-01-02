import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime
import uuid
import plotly.express as px
import plotly.graph_objects as go

# Initialize Supabase client
url = st.secrets["supabase_url"]
key = st.secrets["supabase_key"]
supabase: Client = create_client(url, key)

# Session state initialization
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'current_component' not in st.session_state:
    st.session_state.current_component = None

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
    col1, col2 = st.columns([2, 1])
    with col1:
        search_query = st.text_input("Search components", key="search")
    with col2:
        sort_by = st.selectbox("Sort by", ["Name", "Created Date", "Updated Date"])
    
    # Filters
    with st.expander("Advanced Filters"):
        col1, col2 = st.columns(2)
        with col1:
            status_filter = st.multiselect("Status", ["Active", "Deprecated", "In Development"])
        with col2:
            tech_filter = st.multiselect("Technology", ["Python", "JavaScript", "Java", "Other"])
    
    try:
        # Fetch components from Supabase
        response = supabase.table('components').select("*").execute()
        components = pd.DataFrame(response.data)
        
        if not components.empty:
            # Apply filters and sorting
            if search_query:
                components = components[components['name'].str.contains(search_query, case=False) | 
                                     components['description'].str.contains(search_query, case=False)]
            
            # Display components in a modern card layout
            for _, component in components.iterrows():
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.subheader(component['name'])
                        st.write(component['description'])
                    with col2:
                        st.write(f"Created: {component['created_at'][:10]}")
                    with col3:
                        if st.button("View Details", key=f"view_{component['id']}"):
                            st.session_state.current_component = component['id']
                            st.session_state.current_view = "component_details"
                    st.divider()
        else:
            st.info("No components found")
    except Exception as e:
        st.error(f"Error fetching components: {str(e)}")

def view_component_details(component_id):
    try:
        # Fetch component details
        response = supabase.table('components').select("*").eq('id', component_id).execute()
        component = response.data[0]
        
        # Header
        st.header(component['name'])
        st.write(f"Last updated: {component['updated_at'][:10]}")
        
        # Tabs for different sections
        tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Technical Details", "Examples", "History"])
        
        with tab1:
            st.subheader("Description")
            st.write(component['description'])
            
            # Key metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Usage Count", "15")
            with col2:
                st.metric("Success Rate", "98%")
            with col3:
                st.metric("Avg Implementation Time", "2.5 days")
        
        with tab2:
            st.subheader("Technical Specifications")
            # Add technical details here
            
        with tab3:
            st.subheader("Implementation Examples")
            # Add examples here
            
        with tab4:
            st.subheader("Version History")
            # Add version history here
            
    except Exception as e:
        st.error(f"Error loading component details: {str(e)}")

def add_component():
    st.header("Add New Component")
    
    with st.form("add_component_form"):
        # Basic Information
        st.subheader("Basic Information")
        name = st.text_input("Component Name")
        description = st.text_area("Description")
        
        # Technical Details
        st.subheader("Technical Details")
        col1, col2 = st.columns(2)
        with col1:
            technology = st.selectbox("Primary Technology", ["Python", "JavaScript", "Java", "Other"])
            version = st.text_input("Version")
        with col2:
            status = st.selectbox("Status", ["Active", "In Development", "Deprecated"])
            category = st.selectbox("Category", ["UI Component", "Backend Service", "Database", "Other"])
        
        # Documentation
        st.subheader("Documentation")
        documentation = st.text_area("Technical Documentation")
        example_code = st.text_area("Example Code")
        
        submitted = st.form_submit_button("Add Component")
        if submitted:
            try:
                new_component = {
                    "id": str(uuid.uuid4()),
                    "name": name,
                    "description": description,
                    "technology": technology,
                    "version": version,
                    "status": status,
                    "category": category,
                    "documentation": documentation,
                    "example_code": example_code,
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
        # Fetch components data
        response = supabase.table('components').select("*").execute()
        components = pd.DataFrame(response.data)
        
        # Key Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Components", len(components))
        with col2:
            st.metric("Active Components", len(components[components['status'] == 'Active']))
        with col3:
            st.metric("In Development", len(components[components['status'] == 'In Development']))
        with col4:
            st.metric("Deprecated", len(components[components['status'] == 'Deprecated']))
        
        # Components by Technology
        if not components.empty:
            tech_counts = components['technology'].value_counts()
            fig = px.pie(values=tech_counts.values, names=tech_counts.index, title="Components by Technology")
            st.plotly_chart(fig)
            
            # Components by Category
            cat_counts = components['category'].value_counts()
            fig = px.bar(x=cat_counts.index, y=cat_counts.values, title="Components by Category")
            st.plotly_chart(fig)
            
            # Timeline of Component Creation
            components['created_at'] = pd.to_datetime(components['created_at'])
            timeline_data = components.groupby(components['created_at'].dt.date).size()
            fig = px.line(x=timeline_data.index, y=timeline_data.values, title="Component Creation Timeline")
            st.plotly_chart(fig)
        
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
            if st.session_state.current_component:
                view_component_details(st.session_state.current_component)
                if st.button("Back to Library"):
                    st.session_state.current_component = None
                    st.rerun()
            else:
                view_component_library()
        elif view == "Add Component":
            add_component()
        elif view == "Analytics Dashboard":
            analytics_dashboard()

if __name__ == '__main__':
    main()
