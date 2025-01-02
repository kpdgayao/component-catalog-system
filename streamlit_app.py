import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime
import uuid
import plotly.express as px
import plotly.graph_objects as go
import json
from typing import Optional

# Initialize Supabase client
try:
    url = st.secrets["supabase_url"]
    key = st.secrets["supabase_key"]
    supabase: Client = create_client(url, key)
    # Test connection
    response = supabase.table('components').select("count", count='exact').execute()
    st.success("✅ Successfully connected to Supabase!")
except Exception as e:
    st.error(f"❌ Failed to connect to Supabase: {str(e)}")
    st.info("Please check your .streamlit/secrets.toml file and ensure your Supabase credentials are correct.")
    st.stop()

# Session state initialization
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'current_component' not in st.session_state:
    st.session_state.current_component = None

def handle_auth_error():
    st.error("Your session has expired. Please log in again.")
    st.session_state.authenticated = False
    st.session_state.user = None
    st.rerun()

def login():
    st.title("Component Catalog System")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
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
                    st.session_state.user = response.user
                    st.success("Login successful!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Login failed: {str(e)}")
    
    with tab2:
        with st.form("signup_form"):
            new_email = st.text_input("Email")
            new_password = st.text_input("Password", type='password')
            confirm_password = st.text_input("Confirm Password", type='password')
            submitted = st.form_submit_button("Sign Up")
            
            if submitted:
                if new_password != confirm_password:
                    st.error("Passwords do not match!")
                else:
                    try:
                        response = supabase.auth.sign_up({
                            "email": new_email,
                            "password": new_password
                        })
                        st.success("Sign up successful! Please check your email to verify your account.")
                    except Exception as e:
                        st.error(f"Sign up failed: {str(e)}")

def get_categories():
    try:
        response = supabase.table('categories').select("*").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error fetching categories: {str(e)}")
        return pd.DataFrame()

def get_tags():
    try:
        response = supabase.table('tags').select("*").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error fetching tags: {str(e)}")
        return pd.DataFrame()

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
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.multiselect("Status", ["Active", "Deprecated", "In Development"])
        with col2:
            categories = get_categories()
            category_filter = st.multiselect("Category", categories['name'].tolist() if not categories.empty else [])
        with col3:
            tags = get_tags()
            tag_filter = st.multiselect("Tags", tags['name'].tolist() if not tags.empty else [])
    
    try:
        # Build query
        query = supabase.table('components').select(
            "*, categories(name), component_tags(tags(name))"
        )
        
        if search_query:
            query = query.or_(f"name.ilike.%{search_query}%,description.ilike.%{search_query}%")
        
        if status_filter:
            query = query.in_('status', status_filter)
            
        response = query.execute()
        
        components = pd.DataFrame(response.data)
        
        if not components.empty:
            # Display components in a modern card layout
            for _, component in components.iterrows():
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.subheader(component['name'])
                        st.write(component['description'])
                        # Display tags
                        if 'component_tags' in component and component['component_tags']:
                            tags = [tag['tags']['name'] for tag in component['component_tags']]
                            st.write("Tags:", ", ".join(tags))
                    with col2:
                        st.write(f"Status: {component['status']}")
                        st.write(f"Category: {component['categories']['name'] if component['categories'] else 'N/A'}")
                    with col3:
                        if st.button("View Details", key=f"view_{component['id']}"):
                            st.session_state.current_component = component['id']
                            st.rerun()
                    st.divider()
        else:
            st.info("No components found")
    except Exception as e:
        st.error(f"Error fetching components: {str(e)}")

def upload_file(component_id: str, file) -> Optional[str]:
    try:
        file_path = f"components/{component_id}/{file.name}"
        supabase.storage.from_("component-files").upload(
            file_path,
            file.getvalue()
        )
        
        # Add file record to database
        supabase.table('component_files').insert({
            "component_id": component_id,
            "file_name": file.name,
            "file_path": file_path,
            "file_type": file.type,
            "file_size": len(file.getvalue()),
            "uploaded_by": st.session_state.user.id
        }).execute()
        
        return file_path
    except Exception as e:
        st.error(f"Error uploading file: {str(e)}")
        return None

def view_component_details(component_id):
    try:
        # Fetch component details with related data
        response = supabase.table('components').select(
            "*, categories(name), component_tags(tags(name)), component_files(*), version_history(*)"
        ).eq('id', component_id).execute()
        
        component = response.data[0]
        
        # Header
        col1, col2 = st.columns([3, 1])
        with col1:
            st.header(component['name'])
            st.write(f"Status: {component['status']}")
        with col2:
            st.write(f"Last updated: {component['updated_at'][:10]}")
            if st.button("Edit Component"):
                st.session_state.editing = True
        
        # Tabs for different sections
        tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Files", "Version History", "Usage Stats"])
        
        with tab1:
            st.subheader("Description")
            st.write(component['description'])
            
            # Tags
            if component['component_tags']:
                tags = [tag['tags']['name'] for tag in component['component_tags']]
                st.write("Tags:", ", ".join(tags))
            
            # Category
            st.write("Category:", component['categories']['name'] if component['categories'] else 'N/A')
            
            # Technical Specifications
            specs_response = supabase.table('technical_specifications').select("*").eq('component_id', component_id).execute()
            if specs_response.data:
                st.subheader("Technical Specifications")
                for spec in specs_response.data:
                    st.write(f"**{spec['spec_name']}:** {spec['spec_value']}")
        
        with tab2:
            st.subheader("Files")
            # File upload
            uploaded_file = st.file_uploader("Upload new file", key="file_upload")
            if uploaded_file:
                if upload_file(component_id, uploaded_file):
                    st.success("File uploaded successfully!")
                    st.rerun()
            
            # Display existing files
            if component['component_files']:
                for file in component['component_files']:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"📎 {file['file_name']}")
                    with col2:
                        if st.button("Download", key=f"download_{file['id']}"):
                            try:
                                file_data = supabase.storage.from_("component-files").download(file['file_path'])
                                st.download_button(
                                    label="Save File",
                                    data=file_data,
                                    file_name=file['file_name'],
                                    key=f"save_{file['id']}"
                                )
                            except Exception as e:
                                st.error(f"Error downloading file: {str(e)}")
        
        with tab3:
            st.subheader("Version History")
            if component['version_history']:
                for version in sorted(component['version_history'], key=lambda x: x['created_at'], reverse=True):
                    st.write(f"**Version {version['version_number']}** - {version['created_at'][:10]}")
                    st.write(version['change_description'])
                    st.divider()
        
        with tab4:
            st.subheader("Usage Statistics")
            usage_response = supabase.table('usage_statistics').select("*").eq('component_id', component_id).execute()
            if usage_response.data:
                usage_df = pd.DataFrame(usage_response.data)
                
                # Usage over time
                usage_df['usage_date'] = pd.to_datetime(usage_df['usage_date'])
                usage_by_date = usage_df.groupby(usage_df['usage_date'].dt.date).size()
                
                fig = px.line(
                    x=usage_by_date.index,
                    y=usage_by_date.values,
                    title="Component Usage Over Time",
                    labels={'x': 'Date', 'y': 'Number of Uses'}
                )
                st.plotly_chart(fig)
                
                # Project usage
                project_usage = usage_df['project_name'].value_counts()
                fig = px.pie(
                    values=project_usage.values,
                    names=project_usage.index,
                    title="Usage by Project"
                )
                st.plotly_chart(fig)
            
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
            version = st.text_input("Version")
            status = st.selectbox("Status", ["Active", "In Development", "Deprecated"])
        with col2:
            categories = get_categories()
            category = st.selectbox(
                "Category",
                options=categories['id'].tolist() if not categories.empty else [],
                format_func=lambda x: categories.loc[categories['id'] == x, 'name'].iloc[0] if not categories.empty else 'N/A'
            )
        
        # Tags
        tags = get_tags()
        selected_tags = st.multiselect(
            "Tags",
            options=tags['id'].tolist() if not tags.empty else [],
            format_func=lambda x: tags.loc[tags['id'] == x, 'name'].iloc[0] if not tags.empty else 'N/A'
        )
        
        # Technical Specifications
        st.subheader("Technical Specifications")
        specs = []
        for i in range(3):  # Allow up to 3 specifications
            col1, col2 = st.columns(2)
            with col1:
                spec_name = st.text_input(f"Specification {i+1} Name", key=f"spec_name_{i}")
            with col2:
                spec_value = st.text_input(f"Specification {i+1} Value", key=f"spec_value_{i}")
            if spec_name and spec_value:
                specs.append({"name": spec_name, "value": spec_value})
        
        submitted = st.form_submit_button("Add Component")
        if submitted:
            try:
                # Create component
                component_data = {
                    "id": str(uuid.uuid4()),
                    "name": name,
                    "description": description,
                    "version": version,
                    "status": status,
                    "category_id": category if category else None,
                    "created_by": st.session_state.user.id,
                }
                
                response = supabase.table('components').insert(component_data).execute()
                component_id = response.data[0]['id']
                
                # Add tags
                if selected_tags:
                    tag_data = [{"component_id": component_id, "tag_id": tag_id} for tag_id in selected_tags]
                    supabase.table('component_tags').insert(tag_data).execute()
                
                # Add specifications
                if specs:
                    spec_data = [{
                        "component_id": component_id,
                        "spec_name": spec["name"],
                        "spec_value": spec["value"]
                    } for spec in specs]
                    supabase.table('technical_specifications').insert(spec_data).execute()
                
                # Add initial version history
                supabase.table('version_history').insert({
                    "component_id": component_id,
                    "version_number": version or "1.0.0",
                    "change_description": "Initial version",
                    "changed_by": st.session_state.user.id
                }).execute()
                
                st.success("Component added successfully!")
                st.session_state.current_component = component_id
                st.rerun()
                
            except Exception as e:
                st.error(f"Error adding component: {str(e)}")

def analytics_dashboard():
    st.header("Analytics Dashboard")
    
    try:
        # Fetch all necessary data
        components = pd.DataFrame(supabase.table('components').select("*").execute().data)
        usage_stats = pd.DataFrame(supabase.table('usage_statistics').select("*").execute().data)
        version_history = pd.DataFrame(supabase.table('version_history').select("*").execute().data)
        
        # Key Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Components", len(components))
        with col2:
            active_count = len(components[components['status'] == 'Active'])
            st.metric("Active Components", active_count)
        with col3:
            usage_count = len(usage_stats)
            st.metric("Total Uses", usage_count)
        with col4:
            avg_versions = len(version_history) / len(components) if len(components) > 0 else 0
            st.metric("Avg Versions", f"{avg_versions:.1f}")
        
        # Components by Status
        if not components.empty:
            status_counts = components['status'].value_counts()
            fig = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title="Components by Status"
            )
            st.plotly_chart(fig)
        
        # Usage Over Time
        if not usage_stats.empty:
            usage_stats['usage_date'] = pd.to_datetime(usage_stats['usage_date'])
            usage_by_date = usage_stats.groupby(usage_stats['usage_date'].dt.date).size()
            
            fig = px.line(
                x=usage_by_date.index,
                y=usage_by_date.values,
                title="Component Usage Trend",
                labels={'x': 'Date', 'y': 'Number of Uses'}
            )
            st.plotly_chart(fig)
        
        # Most Used Components
        if not usage_stats.empty:
            component_usage = usage_stats['component_id'].value_counts().head(10)
            component_names = components.set_index('id')['name']
            
            fig = px.bar(
                x=[component_names[id] for id in component_usage.index],
                y=component_usage.values,
                title="Most Used Components",
                labels={'x': 'Component', 'y': 'Number of Uses'}
            )
            fig.update_layout(xaxis_tickangle=-45)
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
        
        # User info and logout
        st.sidebar.divider()
        st.sidebar.write(f"Logged in as: {st.session_state.user.email}")
        if st.sidebar.button("Logout"):
            supabase.auth.sign_out()
            st.session_state.authenticated = False
            st.session_state.user = None
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
