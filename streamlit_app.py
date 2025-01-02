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
except Exception as e:
    st.error(f"Failed to connect to Supabase: {str(e)}")
    st.info("Please check your .streamlit/secrets.toml file and ensure your Supabase credentials are correct.")
    st.stop()

def initialize_session_state():
    """Initialize session state variables."""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'access_token' not in st.session_state:
        st.session_state.access_token = None
    if 'refresh_token' not in st.session_state:
        st.session_state.refresh_token = None
    if 'current_component' not in st.session_state:
        st.session_state.current_component = None
    if 'page' not in st.session_state:
        st.session_state.page = "Component Library"
    if 'show_success' not in st.session_state:
        st.session_state.show_success = False
    if 'success_message' not in st.session_state:
        st.session_state.success_message = ""
    if 'verification_requested' not in st.session_state:
        st.session_state.verification_requested = False

def navigate_to(page: str):
    """Handle navigation to different pages."""
    st.session_state.page = page
    if page == "Component Library":
        st.session_state.current_component = None

def handle_nav_change():
    """Handle navigation changes."""
    # Force a rerun if view is different from nav_selection
    if st.session_state.page != st.session_state.nav_selection:
        st.session_state.page = st.session_state.nav_selection
        if st.session_state.nav_selection == "Component Library":
            st.session_state.current_component = None
        st.rerun()

def check_session():
    """Check and refresh the user's session if needed."""
    try:
        # Check URL parameters
        query_params = st.experimental_get_query_params()
        
        # Handle email verification
        if 'type' in query_params and query_params['type'][0] == 'signup':
            if 'token' in query_params:
                try:
                    # Verify the token
                    response = supabase.auth.verify_signup({
                        'token': query_params['token'][0],
                        'type': 'signup',
                    })
                    if response and response.user:
                        st.session_state.authenticated = True
                        st.session_state.user = response.user
                        st.session_state.access_token = response.session.access_token
                        st.session_state.refresh_token = response.session.refresh_token
                        st.session_state.verification_requested = True
                        # Clear URL parameters
                        st.experimental_set_query_params()
                        return True
                except Exception as e:
                    print(f"Verification error: {str(e)}")
                    st.experimental_set_query_params()
                    return False

        # Check existing session
        if st.session_state.access_token:
            try:
                user = supabase.auth.get_user(st.session_state.access_token)
                if user:
                    st.session_state.authenticated = True
                    st.session_state.user = user.user
                    return True
            except Exception:
                if st.session_state.refresh_token:
                    try:
                        response = supabase.auth.refresh_session(st.session_state.refresh_token)
                        st.session_state.access_token = response.session.access_token
                        st.session_state.refresh_token = response.session.refresh_token
                        st.session_state.authenticated = True
                        st.session_state.user = response.user
                        return True
                    except Exception:
                        pass
        return False
    except Exception as e:
        print(f"Session check error: {str(e)}")
        return False

def handle_auth_error():
    """Handle authentication errors by clearing the session."""
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.access_token = None
    st.session_state.refresh_token = None
    st.rerun()

def is_valid_iol_email(email):
    """Check if the email is a valid IOL email address."""
    return email.lower().endswith('@iol.ph')

def login():
    st.title("IOL Inc. Component Catalog")
    st.write("Welcome to the IOL Inc. Component Catalog System. Please login or sign up to continue.")
    st.info("Note: This system is only accessible to IOL Inc. employees with @iol.ph email addresses.")
    
    # Show verification success message if needed
    if st.session_state.verification_requested:
        st.success("""
        Email verified successfully! 
        
        Please log in with your email and password below.
        """)
        st.session_state.verification_requested = False
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        with st.form("login_form"):
            st.write("Sign in to your account")
            email = st.text_input("Email")
            password = st.text_input("Password", type='password')
            submitted = st.form_submit_button("Login", use_container_width=True)
            
            if submitted:
                if not email or not password:
                    st.error("Please fill in all fields.")
                elif not is_valid_iol_email(email):
                    st.error("Please use your IOL Inc. email address (@iol.ph)")
                else:
                    try:
                        response = supabase.auth.sign_in_with_password({
                            "email": email,
                            "password": password
                        })
                        st.session_state.authenticated = True
                        st.session_state.user = response.user
                        st.session_state.access_token = response.session.access_token
                        st.session_state.refresh_token = response.session.refresh_token
                        st.success("Login successful!")
                        st.rerun()
                    except Exception as e:
                        error_msg = str(e).lower()
                        if "email not confirmed" in error_msg:
                            st.error("""
                            Please verify your email address before logging in.
                            
                            1. Check your @iol.ph email inbox for the verification link
                            2. Click the link in the email
                            3. You'll be redirected back to this app
                            4. Log in with your credentials
                            
                            Can't find the email? Check your spam folder or click the resend button below.
                            """)
                            if st.button("Resend Verification Email"):
                                try:
                                    supabase.auth.resend_signup_email(email)
                                    st.success("Verification email resent! Please check your inbox.")
                                except Exception as resend_error:
                                    st.error(f"Failed to resend verification email: {str(resend_error)}")
                        else:
                            st.error(f"Login failed: {str(e)}")
    
    with tab2:
        with st.form("signup_form"):
            st.write("Create a new account")
            st.write("""
            **Important Email Verification Instructions:**
            1. After signing up, you'll receive a verification email at your @iol.ph address
            2. Click the verification link in the email
            3. You'll be redirected back to this app
            4. If you see an access error, simply return to this page and log in
            
            Note: Check your spam folder if you don't see the verification email.
            """)
            
            new_email = st.text_input("Email")
            new_password = st.text_input("Password", type='password', 
                                       help="Password must be at least 8 characters long")
            confirm_password = st.text_input("Confirm Password", type='password')
            submitted = st.form_submit_button("Sign Up", use_container_width=True)
            
            if submitted:
                if not new_email or not new_password or not confirm_password:
                    st.error("Please fill in all fields.")
                elif not is_valid_iol_email(new_email):
                    st.error("Please use your IOL Inc. email address (@iol.ph)")
                elif len(new_password) < 8:
                    st.error("Password must be at least 8 characters long.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match!")
                else:
                    try:
                        response = supabase.auth.sign_up({
                            "email": new_email,
                            "password": new_password
                        })
                        st.success("""
                        Sign up successful! 
                        
                        **Next Steps:**
                        1. Check your @iol.ph email for the verification link
                        2. Click the link to verify your account
                        3. If you see an access error after verification, simply return to this page
                        4. Log in with your email and password
                        
                        Can't find the email? Check your spam folder.
                        """)
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
            type_filter = st.multiselect("Type", ["Frontend", "Backend", "Full Stack"])
        with col2:
            categories = get_categories()
            category_filter = st.multiselect(
                "Category",
                categories['name'].tolist() if not categories.empty else []
            )
        with col3:
            tags = get_tags()
            tag_filter = st.multiselect(
                "Tags",
                tags['name'].tolist() if not tags.empty else []
            )
    
    try:
        # Build query
        query = supabase.table('components').select(
            "*, categories(name), component_tags(tags(name))"
        )
        
        # Apply search filter
        if search_query:
            query = query.or_(f"name.ilike.%{search_query}%,description.ilike.%{search_query}%")
        
        # Apply type filter
        if type_filter:
            query = query.in_('type', type_filter)
        
        # Apply sort
        if sort_by == "Name":
            query = query.order('name')
        elif sort_by == "Created Date":
            query = query.order('created_at', desc=True)
        elif sort_by == "Updated Date":
            query = query.order('updated_at', desc=True)
            
        response = query.execute()
        
        if not response.data:
            st.info("No components found. Click on 'Add Component' to create your first component.")
            return
        
        components = pd.DataFrame(response.data)
        
        # Display components in a modern card layout
        for _, component in components.iterrows():
            with st.container():
                st.markdown("---")
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.subheader(component['name'])
                    st.write(component.get('description', ''))
                    # Display tags
                    if component.get('component_tags'):
                        tags = [tag['tags']['name'] for tag in component['component_tags']]
                        st.write(" ", ", ".join(tags))
                with col2:
                    st.write(f"**Type:** {component.get('type', 'N/A')}")
                    st.write(f"**Version:** {component.get('version', 'N/A')}")
                    st.write(f"**Category:** {component['categories']['name'] if component.get('categories') else 'N/A'}")
                with col3:
                    st.write(f"**Last Updated:**  \n{component['updated_at'][:10]}")
                    if st.button("View Details", key=f"view_{component['id']}", use_container_width=True):
                        st.session_state.current_component = component['id']
                        st.rerun()
                
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

def edit_component(component):
    st.title("Edit Component")
    
    with st.form("edit_component_form"):
        # 1. Component Basic Information
        st.subheader("1. Basic Information")
        name = st.text_input("Component Name", value=component.get('name', ''), help="Unique identifier for the component")
        component_type = st.selectbox("Component Type", ["Frontend", "Backend", "Full Stack"], index=["Frontend", "Backend", "Full Stack"].index(component.get('type', 'Frontend')))
        original_project = st.text_input("Original Project", value=component.get('original_project', ''), help="Project where component was first developed")
        version = st.text_input("Current Version", value=component.get('version', ''), help="Latest stable version")
        
        col1, col2 = st.columns(2)
        with col1:
            primary_developers = st.text_input("Primary Developer(s)", value=','.join(component.get('primary_developers', [])), help="Team members who built/maintain it")
        with col2:
            documentation_status = st.selectbox("Documentation Status", ["Complete", "Partial", "Needs Update"], 
                                             index=["Complete", "Partial", "Needs Update"].index(component.get('documentation_status', 'Partial')))
        
        description = st.text_area("Description", value=component.get('description', ''))
        
        # 2. Technical Specifications
        st.subheader("2. Technical Specifications")
        technology_stack = st.text_area("Technology Stack", value='\n'.join(component.get('technology_stack', [])), 
                                      help="List of technologies used (e.g., React, Node.js, AWS services)")
        dependencies = st.text_area("Dependencies", value='\n'.join(component.get('dependencies', [])), 
                                  help="Required libraries, frameworks, or services")
        aws_services = st.text_area("AWS Services Used", value='\n'.join(component.get('aws_services', [])), 
                                  help="List of AWS services if applicable")
        
        col1, col2 = st.columns(2)
        with col1:
            auth_requirements = st.text_area("Authentication Requirements", value=component.get('auth_requirements', ''), 
                                          help="Auth requirements/integration points")
        with col2:
            db_requirements = st.text_area("Database Requirements", value=component.get('db_requirements', ''), 
                                        help="Required database structure/schema")
        
        api_endpoints = st.text_area("API Endpoints", value=component.get('api_endpoints', ''), 
                                   help="List of endpoints if applicable")
        
        # 3. Testing and Quality
        st.subheader("3. Testing and Quality")
        col1, col2, col3 = st.columns(3)
        with col1:
            test_coverage = st.number_input("Test Coverage (%)", min_value=0, max_value=100, 
                                          value=component.get('test_coverage', 0))
        with col2:
            has_unit_tests = st.checkbox("Unit Tests Available", value=component.get('has_unit_tests', False))
            has_integration_tests = st.checkbox("Integration Tests Available", value=component.get('has_integration_tests', False))
        with col3:
            has_e2e_tests = st.checkbox("E2E Tests Available", value=component.get('has_e2e_tests', False))
        
        known_limitations = st.text_area("Known Issues/Limitations", value=component.get('known_limitations', ''))
        performance_metrics = st.text_area("Performance Metrics", value=component.get('performance_metrics', ''))
        
        # 4. Maintenance Information
        st.subheader("4. Maintenance Information")
        update_frequency = st.text_input("Update Frequency", value=component.get('update_frequency', ''))
        breaking_changes_history = st.text_area("Breaking Changes History", value=component.get('breaking_changes_history', ''))
        backward_compatibility_notes = st.text_area("Backward Compatibility Notes", value=component.get('backward_compatibility_notes', ''))
        support_contact = st.text_input("Support Contact", value=component.get('support_contact', ''))
        
        # 5. Business Value
        st.subheader("5. Business Value")
        business_value = component.get('business_value', {})
        col1, col2 = st.columns(2)
        with col1:
            time_saved = st.number_input("Time Saved (hours)", min_value=0, value=int(business_value.get('time_saved', 0)))
        with col2:
            cost_savings = st.number_input("Cost Savings ($)", min_value=0, value=int(business_value.get('cost_savings', 0)))
        risk_reduction = st.text_area("Risk Reduction", value=business_value.get('risk_reduction', ''))
        client_benefits = st.text_area("Client Benefits", value=business_value.get('client_benefits', ''))
        
        # 6. Integration Guidelines
        st.subheader("6. Integration Guidelines")
        setup_instructions = st.text_area("Setup Instructions", value=component.get('setup_instructions', ''))
        configuration_requirements = st.text_area("Configuration Requirements", value=component.get('configuration_requirements', ''))
        integration_patterns = st.text_area("Common Integration Patterns", value=component.get('integration_patterns', ''))
        troubleshooting_guide = st.text_area("Troubleshooting Guide", value=component.get('troubleshooting_guide', ''))
        
        # 7. Classification
        st.subheader("7. Classification")
        col1, col2 = st.columns(2)
        with col1:
            categories = get_categories()
            category = st.selectbox(
                "Category",
                options=categories['id'].tolist() if not categories.empty else [],
                format_func=lambda x: categories.loc[categories['id'] == x, 'name'].iloc[0] if not categories.empty else 'N/A',
                index=categories['id'].tolist().index(component['category_id']) if not categories.empty and component.get('category_id') in categories['id'].tolist() else 0
            )
        
        with col2:
            tags = get_tags()
            current_tags = [tag['tags']['id'] for tag in component.get('component_tags', [])]
            selected_tags = st.multiselect(
                "Tags",
                options=tags['id'].tolist() if not tags.empty else [],
                format_func=lambda x: tags.loc[tags['id'] == x, 'name'].iloc[0] if not tags.empty else 'N/A',
                default=current_tags
            )
        
        submitted = st.form_submit_button("Save Changes", use_container_width=True)
        if submitted:
            try:
                # Update component data
                update_data = {
                    "name": name,
                    "type": component_type,
                    "original_project": original_project,
                    "version": version,
                    "primary_developers": primary_developers.split(',') if primary_developers else [],
                    "documentation_status": documentation_status,
                    "description": description,
                    "technology_stack": technology_stack.split('\n') if technology_stack else [],
                    "dependencies": dependencies.split('\n') if dependencies else [],
                    "aws_services": aws_services.split('\n') if aws_services else [],
                    "auth_requirements": auth_requirements,
                    "db_requirements": db_requirements,
                    "api_endpoints": api_endpoints,
                    "test_coverage": test_coverage,
                    "has_unit_tests": has_unit_tests,
                    "has_integration_tests": has_integration_tests,
                    "has_e2e_tests": has_e2e_tests,
                    "known_limitations": known_limitations,
                    "performance_metrics": performance_metrics,
                    "update_frequency": update_frequency,
                    "breaking_changes_history": breaking_changes_history,
                    "backward_compatibility_notes": backward_compatibility_notes,
                    "support_contact": support_contact,
                    "business_value": {
                        "time_saved": time_saved,
                        "cost_savings": cost_savings,
                        "risk_reduction": risk_reduction,
                        "client_benefits": client_benefits
                    },
                    "setup_instructions": setup_instructions,
                    "configuration_requirements": configuration_requirements,
                    "integration_patterns": integration_patterns,
                    "troubleshooting_guide": troubleshooting_guide,
                    "category_id": category if category else None,
                }
                
                # Update component
                supabase.table('components').update(update_data).eq('id', component['id']).execute()
                
                # Update tags
                if selected_tags != current_tags:
                    # Delete existing tags
                    supabase.table('component_tags').delete().eq('component_id', component['id']).execute()
                    # Add new tags
                    if selected_tags:
                        tag_data = [{"component_id": component['id'], "tag_id": tag_id} for tag_id in selected_tags]
                        supabase.table('component_tags').insert(tag_data).execute()
                
                st.success("Component updated successfully!")
                st.session_state.editing = False
                st.rerun()
                
            except Exception as e:
                st.error(f"Error updating component: {str(e)}")

def view_component_details(component_id):
    try:
        # Fetch component details with related data
        response = supabase.table('components').select(
            "*",
            "categories(name)",
            "component_tags(tags(*))"
        ).eq('id', component_id).execute()
        
        if not response.data:
            st.error("Component not found")
            return
        
        component = response.data[0]
        
        if 'editing' not in st.session_state:
            st.session_state.editing = False
        
        # Header
        col1, col2 = st.columns([3, 1])
        with col1:
            st.header(component['name'])
            st.write(f"Type: {component['type']}")
            st.write(f"Version: {component['version']}")
        with col2:
            st.write(f"Last updated: {component['updated_at'][:10]}")
            if st.button("", key=f"edit_btn_{component_id}", use_container_width=True):
                st.session_state.editing = True
                st.rerun()
        
        if st.session_state.editing:
            edit_component(component)
        else:
            # Tabs for different sections
            tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Technical Details", "Files", "Business Value"])
            
            with tab1:
                st.subheader("Basic Information")
                st.write(f"**Original Project:** {component['original_project']}")
                st.write(f"**Primary Developers:** {', '.join(component['primary_developers']) if component['primary_developers'] else 'N/A'}")
                st.write(f"**Documentation Status:** {component['documentation_status']}")
                
                st.subheader("Description")
                st.write(component['description'])
                
                # Tags
                if component['component_tags']:
                    tags = [tag['tags']['name'] for tag in component['component_tags']]
                    st.write("**Tags:**", ", ".join(tags))
                
                # Category
                st.write("**Category:**", component['categories']['name'] if component['categories'] else 'N/A')
            
            with tab2:
                st.subheader("Technical Stack")
                if component['technology_stack']:
                    for tech in component['technology_stack']:
                        st.write(f"- {tech}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Dependencies")
                    if component['dependencies']:
                        for dep in component['dependencies']:
                            st.write(f"- {dep}")
            
                with col2:
                    st.subheader("AWS Services")
                    if component['aws_services']:
                        for service in component['aws_services']:
                            st.write(f"- {service}")
            
                st.subheader("Requirements")
                st.write("**Authentication Requirements:**")
                st.write(component['auth_requirements'])
                st.write("**Database Requirements:**")
                st.write(component['db_requirements'])
                st.write("**API Endpoints:**")
                st.write(component['api_endpoints'])
                
                st.subheader("Testing")
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Test Coverage:** {component['test_coverage']}%")
                    st.write("**Available Tests:**")
                    st.write(f"- Unit Tests: {'' if component['has_unit_tests'] else ''}")
                    st.write(f"- Integration Tests: {'' if component['has_integration_tests'] else ''}")
                    st.write(f"- E2E Tests: {'' if component['has_e2e_tests'] else ''}")
            
                with col2:
                    st.write("**Known Limitations:**")
                    st.write(component['known_limitations'])
                    st.write("**Performance Metrics:**")
                    st.write(component['performance_metrics'])
            
            with tab3:
                st.subheader("Files")
                # File upload
                uploaded_file = st.file_uploader("Upload new file", key=f"file_upload_{component_id}")
                if uploaded_file:
                    if upload_file(component_id, uploaded_file):
                        st.success("File uploaded successfully!")
                        st.rerun()
            
                # Display existing files
                files_response = supabase.table('component_files').select("*").eq('component_id', component_id).execute()
                if files_response.data:
                    for file in files_response.data:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f" {file['file_name']}")
                            if file['description']:
                                st.write(file['description'])
                        with col2:
                            if st.button("Download", key=f"download_{file['id']}_{component_id}"):
                                try:
                                    file_data = supabase.storage.from_("component-files").download(file['file_path'])
                                    st.download_button(
                                        label="Save File",
                                        data=file_data,
                                        file_name=file['file_name'],
                                        key=f"save_{file['id']}_{component_id}"
                                    )
                                except Exception as e:
                                    st.error(f"Error downloading file: {str(e)}")
            
            with tab4:
                st.subheader("Business Value")
                if component['business_value']:
                    st.write(f"**Time Saved:** {component['business_value'].get('time_saved', 0)} hours")
                    st.write(f"**Cost Savings:** ${component['business_value'].get('cost_savings', 0):,.2f}")
                    st.write("**Risk Reduction:**")
                    st.write(component['business_value'].get('risk_reduction', ''))
                    st.write("**Client Benefits:**")
                    st.write(component['business_value'].get('client_benefits', ''))
            
                st.subheader("Integration Guidelines")
                st.write("**Setup Instructions:**")
                st.write(component['setup_instructions'])
                st.write("**Configuration Requirements:**")
                st.write(component['configuration_requirements'])
                st.write("**Common Integration Patterns:**")
                st.write(component['integration_patterns'])
                st.write("**Troubleshooting Guide:**")
                st.write(component['troubleshooting_guide'])
            
    except Exception as e:
        st.error(f"Error loading component details: {str(e)}")

def add_component():
    st.title("Add New Component")
    
    with st.form("add_component_form"):
        # 1. Component Basic Information
        st.subheader("1. Basic Information")
        name = st.text_input("Component Name", help="Unique identifier for the component", key="name")
        component_type = st.selectbox("Component Type", ["Frontend", "Backend", "Full Stack"], key="type")
        original_project = st.text_input("Original Project", help="Project where component was first developed", key="project")
        version = st.text_input("Current Version", help="Latest stable version", key="version")
        
        col1, col2 = st.columns(2)
        with col1:
            primary_developers = st.text_input("Primary Developer(s)", help="Team members who built/maintain it", key="devs")
        with col2:
            documentation_status = st.selectbox("Documentation Status", ["Complete", "Partial", "Needs Update"], key="docs")
        
        description = st.text_area("Description", key="desc")
        
        # 2. Technical Specifications
        st.subheader("2. Technical Specifications")
        technology_stack = st.text_area("Technology Stack", help="List of technologies used (e.g., React, Node.js, AWS services)", key="tech")
        dependencies = st.text_area("Dependencies", help="Required libraries, frameworks, or services", key="deps")
        aws_services = st.text_area("AWS Services Used", help="List of AWS services if applicable", key="aws")
        
        col1, col2 = st.columns(2)
        with col1:
            auth_requirements = st.text_area("Authentication Requirements", help="Auth requirements/integration points", key="auth")
        with col2:
            db_requirements = st.text_area("Database Requirements", help="Required database structure/schema", key="db")
        
        api_endpoints = st.text_area("API Endpoints", help="List of endpoints if applicable", key="api")
        
        # 3. Testing and Quality
        st.subheader("3. Testing and Quality")
        col1, col2, col3 = st.columns(3)
        with col1:
            test_coverage = st.number_input("Test Coverage (%)", min_value=0, max_value=100, key="coverage")
        with col2:
            has_unit_tests = st.checkbox("Unit Tests Available", key="unit")
            has_integration_tests = st.checkbox("Integration Tests Available", key="integration")
        with col3:
            has_e2e_tests = st.checkbox("E2E Tests Available", key="e2e")
        
        known_limitations = st.text_area("Known Issues/Limitations", key="limits")
        performance_metrics = st.text_area("Performance Metrics", key="perf")
        
        # 4. Maintenance Information
        st.subheader("4. Maintenance Information")
        update_frequency = st.text_input("Update Frequency", key="freq")
        breaking_changes_history = st.text_area("Breaking Changes History", key="changes")
        backward_compatibility_notes = st.text_area("Backward Compatibility Notes", key="compat")
        support_contact = st.text_input("Support Contact", key="support")
        
        # 5. Business Value
        st.subheader("5. Business Value")
        col1, col2 = st.columns(2)
        with col1:
            time_saved = st.number_input("Time Saved (hours)", min_value=0, key="time")
        with col2:
            cost_savings = st.number_input("Cost Savings ($)", min_value=0, key="cost")
        risk_reduction = st.text_area("Risk Reduction", key="risk")
        client_benefits = st.text_area("Client Benefits", key="benefits")
        
        # 6. Integration Guidelines
        st.subheader("6. Integration Guidelines")
        setup_instructions = st.text_area("Setup Instructions", key="setup")
        configuration_requirements = st.text_area("Configuration Requirements", key="config")
        integration_patterns = st.text_area("Common Integration Patterns", key="patterns")
        troubleshooting_guide = st.text_area("Troubleshooting Guide", key="guide")
        
        # 7. Classification
        st.subheader("7. Classification")
        col1, col2 = st.columns(2)
        with col1:
            categories = get_categories()
            category = st.selectbox(
                "Category",
                options=categories['id'].tolist() if not categories.empty else [],
                format_func=lambda x: categories.loc[categories['id'] == x, 'name'].iloc[0] if not categories.empty else 'N/A',
                key="category"
            )
        with col2:
            tags = get_tags()
            selected_tags = st.multiselect(
                "Tags",
                options=tags['id'].tolist() if not tags.empty else [],
                format_func=lambda x: tags.loc[tags['id'] == x, 'name'].iloc[0] if not tags.empty else 'N/A',
                key="tags"
            )
        
        submitted = st.form_submit_button("Add Component", use_container_width=True)
        
        if submitted and name:  # Ensure at least the name is provided
            try:
                # Create component
                component_data = {
                    "id": str(uuid.uuid4()),
                    "name": name,
                    "type": component_type,
                    "original_project": original_project,
                    "version": version,
                    "primary_developers": primary_developers.split(',') if primary_developers else [],
                    "documentation_status": documentation_status,
                    "description": description,
                    "technology_stack": technology_stack.split('\n') if technology_stack else [],
                    "dependencies": dependencies.split('\n') if dependencies else [],
                    "aws_services": aws_services.split('\n') if aws_services else [],
                    "auth_requirements": auth_requirements,
                    "db_requirements": db_requirements,
                    "api_endpoints": api_endpoints,
                    "test_coverage": test_coverage,
                    "has_unit_tests": has_unit_tests,
                    "has_integration_tests": has_integration_tests,
                    "has_e2e_tests": has_e2e_tests,
                    "known_limitations": known_limitations,
                    "performance_metrics": performance_metrics,
                    "update_frequency": update_frequency,
                    "breaking_changes_history": breaking_changes_history,
                    "backward_compatibility_notes": backward_compatibility_notes,
                    "support_contact": support_contact,
                    "business_value": {
                        "time_saved": time_saved,
                        "cost_savings": cost_savings,
                        "risk_reduction": risk_reduction,
                        "client_benefits": client_benefits
                    },
                    "setup_instructions": setup_instructions,
                    "configuration_requirements": configuration_requirements,
                    "integration_patterns": integration_patterns,
                    "troubleshooting_guide": troubleshooting_guide,
                    "category_id": category if category else None,
                }
                
                response = supabase.table('components').insert(component_data).execute()
                
                if response.data:
                    component_id = response.data[0]['id']
                    
                    # Add tags
                    if selected_tags:
                        tag_data = [{"component_id": component_id, "tag_id": tag_id} for tag_id in selected_tags]
                        supabase.table('component_tags').insert(tag_data).execute()
                    
                    # Set success state
                    st.session_state.show_success = True
                    st.session_state.success_message = "Component added successfully!"
                    st.session_state.page = "Component Library"
                    st.session_state.current_component = None
                    
                    # Clear form by removing all form-related keys from session state
                    form_keys = [key for key in st.session_state.keys() if key.startswith(('name_', 'type_', 'project_', 'version_', 'devs_', 'docs_', 'desc_'))]
                    for key in form_keys:
                        del st.session_state[key]
                    
                    st.rerun()
                else:
                    st.error("Failed to add component. No data returned from the server.")
            except Exception as e:
                st.error(f"Error adding component: {str(e)}")
        elif submitted:
            st.warning("Please provide at least the component name.")

def analytics_dashboard():
    st.title("Analytics Dashboard")
    
    try:
        # Fetch all necessary data
        components = pd.DataFrame(supabase.table('components').select("*").execute().data)
        
        # Key Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Components", len(components))
        with col2:
            frontend_count = len(components[components['type'] == 'Frontend'])
            st.metric("Frontend Components", frontend_count)
        with col3:
            backend_count = len(components[components['type'] == 'Backend'])
            st.metric("Backend Components", backend_count)
        with col4:
            fullstack_count = len(components[components['type'] == 'Full Stack'])
            st.metric("Full Stack Components", fullstack_count)
        
        # Components by Type
        if not components.empty:
            type_counts = components['type'].value_counts()
            fig = px.pie(
                values=type_counts.values,
                names=type_counts.index,
                title="Components by Type"
            )
            st.plotly_chart(fig)
        
        # Components by Category
        if not components.empty and 'category_id' in components.columns:
            categories = get_categories()
            if not categories.empty:
                components_with_categories = components.merge(
                    categories, 
                    left_on='category_id', 
                    right_on='id', 
                    how='left'
                )
                category_counts = components_with_categories['name_y'].value_counts()
                
                fig = px.bar(
                    x=category_counts.index,
                    y=category_counts.values,
                    title="Components by Category",
                    labels={'x': 'Category', 'y': 'Number of Components'}
                )
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig)
        
        # Business Value Analysis
        if not components.empty:
            total_time_saved = sum(
                component.get('business_value', {}).get('time_saved', 0) 
                for component in components['business_value'] if isinstance(component, dict)
            )
            total_cost_savings = sum(
                component.get('business_value', {}).get('cost_savings', 0) 
                for component in components['business_value'] if isinstance(component, dict)
            )
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Time Saved", f"{total_time_saved:,} hours")
            with col2:
                st.metric("Total Cost Savings", f"${total_cost_savings:,.2f}")
        
        # Recent Activity
        st.subheader("Recent Activity")
        if not components.empty:
            recent_components = components.sort_values('updated_at', ascending=False).head(5)
            for _, component in recent_components.iterrows():
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{component['name']}** ({component['type']})")
                        st.write(f"_{component['description'][:100]}..._" if len(component.get('description', '')) > 100 else component.get('description', ''))
                    with col2:
                        st.write(f"Updated: {component['updated_at'][:10]}")
                    st.markdown("---")
        
    except Exception as e:
        st.error(f"Error fetching analytics: {str(e)}")

def main():
    # Initialize session state
    initialize_session_state()
    
    # Check if user is already logged in
    if not st.session_state.authenticated and not check_session():
        login()
        return

    # Navigation sidebar
    with st.sidebar:
        st.title("Navigation")
        pages = ["Component Library", "Add Component", "Analytics Dashboard"]
        selected_page = st.selectbox(
            "Go to",
            pages,
            index=pages.index(st.session_state.page),
            key="page_selection",
            on_change=lambda: navigate_to(st.session_state.page_selection)
        )
        
        st.divider()
        if st.button("Logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            initialize_session_state()
            st.rerun()

    # Main content area
    try:
        if st.session_state.page == "Component Library":
            if st.session_state.current_component:
                view_component_details(st.session_state.current_component)
            else:
                view_component_library()
        elif st.session_state.page == "Add Component":
            add_component()
        elif st.session_state.page == "Analytics Dashboard":
            analytics_dashboard()
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        if "Invalid JWT" in str(e) or "JWT expired" in str(e):
            handle_auth_error()
        
        # Show current user
        st.sidebar.markdown("---")
        if st.session_state.user:
            st.sidebar.write(f"Logged in as: {st.session_state.user.email}")

if __name__ == '__main__':
    main()
