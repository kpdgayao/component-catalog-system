"""Component views and UI functionality."""

import json
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from typing import Dict, List, Optional
from supabase import Client
from .catalog import get_categories, get_tags, upload_file, clear_metadata_cache
from .utils import get_cached_categories, get_cached_tags
import logging
import time

logger = logging.getLogger(__name__)

def view_component_library(supabase: Client):
    """Display the component library view."""
    st.title("Component Library")
    
    try:
        # Fetch components with related data
        response = supabase.table('components').select(
            "*",
            "categories(name)",
            "component_tags(tags(name))"
        ).execute()
        
        if not response.data:
            st.info("No components found. Add your first component!")
            return
        
        components_df = pd.DataFrame(response.data)
        
        # Search and Filter UI
        with st.expander("Search and Filters", expanded=True):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                search_query = st.text_input("🔍 Search components", 
                    help="Search in name, description, and technology stack")
                
            with col2:
                # Get unique types
                types = components_df['type'].unique().tolist()
                selected_types = st.multiselect("Filter by Type", types)
            
            with col3:
                show_archived = st.checkbox("Show Archived", value=False,
                    help="Include archived components in the results")
        
        # Apply filters
        filtered_df = components_df.copy()
        
        # Filter archived components
        if not show_archived:
            filtered_df = filtered_df[~filtered_df['is_archived']]
        
        if search_query:
            query = search_query.lower()
            filtered_df = filtered_df[
                filtered_df['name'].str.lower().str.contains(query, na=False) |
                filtered_df['description'].str.lower().str.contains(query, na=False) |
                filtered_df['technology_stack'].apply(lambda x: 
                    any(query in str(item).lower() for item in (x or [])))
            ]
        
        if selected_types:
            filtered_df = filtered_df[filtered_df['type'].isin(selected_types)]
        
        # Sort options
        sort_col, sort_order = st.columns([2, 1])
        with sort_col:
            sort_by = st.selectbox(
                "Sort by",
                ["Name", "Last Updated", "Type", "Business Value"],
                index=1
            )
        with sort_order:
            ascending = st.checkbox("Ascending", value=False)
        
        # Apply sorting
        sort_map = {
            "Name": "name",
            "Last Updated": "updated_at",
            "Type": "type",
            "Business Value": "business_value"
        }
        filtered_df = filtered_df.sort_values(
            sort_map[sort_by],
            ascending=ascending,
            na_position='last'
        )
        
        # Display results count
        st.write(f"Showing {len(filtered_df)} of {len(components_df)} components")
        
        # Display components in a grid
        cols = st.columns(3)
        for idx, component in filtered_df.iterrows():
            with cols[idx % 3]:
                with st.container():
                    st.markdown(f"### {component['name']}")
                    st.write(f"**Type:** {component['type']}")
                    
                    # Display category
                    categories = component.get('categories', {})
                    if isinstance(categories, dict):
                        st.write(f"Category: {categories.get('name', 'Uncategorized')}")
                    
                    # Display description preview
                    description = component.get('description', '')
                    if description:
                        st.write(description[:150] + '...' if len(description) > 150 else description)
                    
                    # View details button
                    if st.button("View Details", key=f"view_btn_{component['id']}"):
                        st.session_state.current_component = component['id']
                        st.session_state.editing = False  # Explicitly set editing to False
                        st.rerun()
    except Exception as e:
        st.error(f"Error loading component library: {str(e)}")

def view_component_details(supabase: Client, component_id: str):
    """Display detailed view of a component."""
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
        
        # Header
        col1, col2 = st.columns([3, 1])
        with col1:
            st.title(component['name'])
            if component.get('is_archived'):
                st.caption("🗃️ Archived")
            st.write(f"**Type:** {component['type']}")
            st.write(f"**Version:** {component['version']}")
            created_at = datetime.fromisoformat(component['created_at'].replace('Z', '+00:00'))
            st.info(f"Created on: {created_at.strftime('%Y-%m-%d %H:%M:%S')} by {component.get('created_by', 'Unknown')}")
        with col2:
            st.write(f"**Last updated:** {component['updated_at'][:10]}")
            
            # Edit button
            if st.button("✏️ Edit Component", key=f"edit_btn_{component_id}_view", use_container_width=True):
                st.session_state.editing = True
                st.rerun()
            
            # Archive button
            is_archived = component.get('is_archived', False)
            archive_btn_label = "🗃️ Unarchive" if is_archived else "🗃️ Archive"
            if st.button(archive_btn_label, key=f"archive_btn_{component_id}_view", use_container_width=True):
                try:
                    supabase.table('components').update(
                        {"is_archived": not is_archived}
                    ).eq('id', component_id).execute()
                    st.success(f"Component {'unarchived' if is_archived else 'archived'} successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to update archive status: {str(e)}")
            
            # Return button
            if st.button("← Return", key=f"return_btn_{component_id}_view", use_container_width=True):
                st.session_state.current_component = None
                st.rerun()
        
        # Component Details in Tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["Overview", "Technical Details", "Testing & Documentation", "Files", "Business Value"])
        
        with tab1:
            st.subheader("Basic Information")
            st.write(f"**Original Project:** {component.get('original_project', 'N/A')}")
            st.write(f"**Primary Developers:** {', '.join(component.get('primary_developers', [])) if component.get('primary_developers') else 'N/A'}")
            st.write(f"**Documentation Status:** {component.get('documentation_status', 'N/A')}")
            
            st.subheader("Description")
            st.write(component.get('description', 'No description available'))
            
            # Tags and Categories
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Category:**", component['categories']['name'] if component.get('categories') else 'Uncategorized')
            with col2:
                if component.get('component_tags'):
                    tags = [tag['tags']['name'] for tag in component['component_tags']]
                    st.write("**Tags:**", ", ".join(tags))
        
        with tab2:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Technology Stack")
                if component.get('technology_stack'):
                    for tech in component['technology_stack']:
                        st.write(f"- {tech}")
                else:
                    st.write("No technology stack specified")
                
                st.subheader("Dependencies")
                if component.get('dependencies'):
                    for dep in component['dependencies']:
                        st.write(f"- {dep}")
                else:
                    st.write("No dependencies specified")
            
            with col2:
                st.subheader("AWS Services")
                if component.get('aws_services'):
                    for service in component['aws_services']:
                        st.write(f"- {service}")
                else:
                    st.write("No AWS services specified")
            
            st.subheader("Requirements")
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Authentication Requirements:**")
                st.write(component.get('auth_requirements', 'None specified'))
                st.write("**API Endpoints:**")
                st.write(component.get('api_endpoints', 'None specified'))
            with col2:
                st.write("**Database Requirements:**")
                st.write(component.get('db_requirements', 'None specified'))
            
            st.subheader("Integration Details")
            st.write("**Setup Instructions:**")
            st.write(component.get('setup_instructions', 'None provided'))
            st.write("**Configuration Requirements:**")
            st.write(component.get('configuration_requirements', 'None specified'))
            st.write("**Integration Patterns:**")
            st.write(component.get('integration_patterns', 'None documented'))
            st.write("**Troubleshooting Guide:**")
            st.write(component.get('troubleshooting_guide', 'No guide available'))
        
        with tab3:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Testing Status")
                
                # Test coverage gauge chart
                test_coverage = component.get('test_coverage', 0)
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = test_coverage,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    gauge = {
                        'axis': {'range': [0, 100]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, 50], 'color': "lightgray"},
                            {'range': [50, 80], 'color': "gray"},
                            {'range': [80, 100], 'color': "darkgray"}
                        ],
                    },
                    title = {'text': "Test Coverage"}
                ))
                st.plotly_chart(fig, use_container_width=True)
                
                # Test availability
                st.write("**Available Tests:**")
                col1, col2 = st.columns(2)
                with col1:
                    st.write("Unit Tests:", "✅" if component.get('has_unit_tests') else "❌")
                    st.write("Integration Tests:", "✅" if component.get('has_integration_tests') else "❌")
                with col2:
                    st.write("E2E Tests:", "✅" if component.get('has_e2e_tests') else "❌")
            
            with col2:
                st.subheader("Documentation")
                st.write("**Documentation Status:**", component.get('documentation_status', 'N/A'))
                st.write("**Known Limitations:**")
                st.write(component.get('known_limitations', 'None documented'))
                st.write("**Performance Metrics:**")
                st.write(component.get('performance_metrics', 'None documented'))
        
        with tab4:
            st.subheader("Component Files")
            # File upload
            uploaded_file = st.file_uploader("Upload new file", key=f"file_upload_{component_id}")
            if uploaded_file:
                try:
                    file_path = f"components/{component_id}/{uploaded_file.name}"
                    supabase.storage.from_("component-files").upload(
                        file_path,
                        uploaded_file.getvalue()
                    )
                    
                    # Add file record
                    supabase.table('component_files').insert({
                        "component_id": component_id,
                        "file_name": uploaded_file.name,
                        "file_path": file_path,
                        "file_type": uploaded_file.type,
                        "file_size": len(uploaded_file.getvalue()),
                        "uploaded_by": st.session_state.user.id if hasattr(st.session_state, 'user') else None
                    }).execute()
                    
                    st.success("File uploaded successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error uploading file: {str(e)}")
            
            # Display existing files
            files_response = supabase.table('component_files').select("*").eq('component_id', component_id).execute()
            if files_response.data:
                for file in files_response.data:
                    with st.container():
                        col1, col2, col3 = st.columns([3, 1, 1])
                        with col1:
                            st.write(f"📄 {file['file_name']}")
                            if file.get('description'):
                                st.write(file['description'])
                        with col2:
                            st.write(f"{file['file_size']/1024:.1f} KB")
                        with col3:
                            try:
                                file_url = supabase.storage.from_("component-files").get_public_url(file['file_path'])
                                st.markdown(f"[Download]({file_url})")
                            except Exception as e:
                                st.error(f"Error getting file URL: {str(e)}")
            else:
                st.info("No files uploaded yet")
        
        with tab5:
            st.subheader("Business Value")
            
            # Business metrics
            col1, col2 = st.columns(2)
            with col1:
                business_value = component.get('business_value', {})
                if isinstance(business_value, str):
                    try:
                        business_value = json.loads(business_value)
                    except:
                        business_value = {}
                
                time_saved = business_value.get('time_saved', 0)
                st.metric("Time Saved", f"{time_saved:,} hours")
            with col2:
                cost_savings = business_value.get('cost_savings', 0)
                st.metric("Cost Savings", f"${cost_savings:,.2f}")
            
            st.write("**Risk Reduction:**")
            st.write(business_value.get('risk_reduction', 'None specified'))
            st.write("**Client Benefits:**")
            st.write(business_value.get('client_benefits', 'None specified'))
            
            st.subheader("Integration & Support")
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Setup Instructions:**")
                st.write(component.get('setup_instructions', 'None provided'))
                st.write("**Configuration Requirements:**")
                st.write(component.get('configuration_requirements', 'None specified'))
            with col2:
                st.write("**Integration Patterns:**")
                st.write(component.get('integration_patterns', 'None documented'))
                st.write("**Support Contact:**")
                st.write(component.get('support_contact', 'Not specified'))
            
            st.write("**Troubleshooting Guide:**")
            st.write(component.get('troubleshooting_guide', 'No guide available'))
            
            # Maintenance information
            st.subheader("Maintenance Information")
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Update Frequency:**")
                st.write(component.get('update_frequency', 'Not specified'))
                st.write("**Breaking Changes History:**")
                st.write(component.get('breaking_changes_history', 'No history available'))
            with col2:
                st.write("**Backward Compatibility:**")
                st.write(component.get('backward_compatibility_notes', 'No notes available'))
    
    except Exception as e:
        st.error(f"Error loading component details: {str(e)}")

def add_component(supabase: Client):
    """Add a new component."""
    from .forms import component_form
    component_form(supabase, mode="add")

def edit_component(component: dict):
    """Edit an existing component."""
    from .forms import component_form
    component_form(st.session_state.supabase, mode="edit", component_data=component)

def manage_metadata(supabase: Client):
    """Manage component metadata like tags and categories."""
    st.title("Manage Metadata")
    
    # Initialize session state for tracking form submissions
    if "category_submitted" not in st.session_state:
        st.session_state.category_submitted = False
    if "tag_submitted" not in st.session_state:
        st.session_state.tag_submitted = False
    
    def on_category_submit():
        st.session_state.category_submitted = True
        
    def on_tag_submit():
        st.session_state.tag_submitted = True
    
    def handle_operation_result(success: bool, message: str):
        """Handle operation result and store in session state."""
        if success:
            st.session_state.last_operation_status = "success"
            st.success(message)
        else:
            st.session_state.last_operation_status = "error"
            st.error(message)
        st.session_state.last_operation_message = message
    
    def validate_name(name: str, existing_names: list) -> tuple[bool, str]:
        """Validate metadata name."""
        if not name or not name.strip():
            return False, "Name cannot be empty"
        if name.strip() in existing_names:
            return False, f"'{name}' already exists"
        return True, ""
    
    def test_permissions():
        """Test database permissions for metadata operations."""
        try:
            # Test category operations
            test_response = supabase.table('categories').select('*').limit(1).execute()
            logger.info("Categories read permission: OK")
            
            if test_response.data:
                test_id = test_response.data[0]['id']
                # Test update permission
                try:
                    current_name = test_response.data[0]['name']
                    supabase.table('categories').update(
                        {"name": current_name}
                    ).eq('id', test_id).execute()
                    logger.info("Categories update permission: OK")
                except Exception as e:
                    logger.error(f"Categories update permission denied: {str(e)}")
                    st.error("⚠️ You don't have permission to edit categories. Please contact your administrator.")
                    return False
            
            # Test tag operations
            test_response = supabase.table('tags').select('*').limit(1).execute()
            logger.info("Tags read permission: OK")
            
            if test_response.data:
                test_id = test_response.data[0]['id']
                # Test update permission
                try:
                    current_name = test_response.data[0]['name']
                    supabase.table('tags').update(
                        {"name": current_name}
                    ).eq('id', test_id).execute()
                    logger.info("Tags update permission: OK")
                except Exception as e:
                    logger.error(f"Tags update permission denied: {str(e)}")
                    st.error("⚠️ You don't have permission to edit tags. Please contact your administrator.")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error testing permissions: {str(e)}")
            st.error("⚠️ Unable to verify database permissions. Please contact your administrator.")
            return False
    
    # Test permissions before proceeding
    if not test_permissions():
        return
    
    tab1, tab2 = st.tabs(["Categories", "Tags"])
    
    with tab1:
        st.header("Categories")
        
        # Add new category form
        with st.form("add_category_form", clear_on_submit=True):
            new_category = st.text_input("Add New Category")
            submit_category = st.form_submit_button("Add Category", on_click=on_category_submit)
            
            if st.session_state.category_submitted and new_category:
                try:
                    # Check for duplicates
                    existing = supabase.table('categories').select('name').execute()
                    if any(cat['name'].lower() == new_category.lower() for cat in existing.data):
                        st.error(f"Category '{new_category}' already exists.")
                    else:
                        supabase.table('categories').insert({"name": new_category}).execute()
                        handle_operation_result(True, f"Added new category: {new_category}")
                        clear_metadata_cache()
                        time.sleep(0.1)
                except Exception as e:
                    handle_operation_result(False, f"Error adding category: {str(e)}")
                finally:
                    st.session_state.category_submitted = False
                    st.rerun()
        
        st.divider()
        
        # Display and manage existing categories
        categories_df = get_cached_categories(supabase)
        if not categories_df.empty:
            for _, row in categories_df.iterrows():
                col1, col2, col3 = st.columns([4, 1, 1])
                
                # Display name
                col1.write(row['name'])
                
                # Edit/Delete buttons
                edit_clicked = col2.button("✏️", key=f"edit_cat_{row['id']}", help="Edit category")
                delete_clicked = col3.button("🗑️", key=f"del_cat_{row['id']}", help="Delete category")
                
                # Edit form
                if st.session_state.editing_category == row['id']:
                    with st.form(key=f"edit_cat_form_{row['id']}"):
                        other_categories = [name for name in categories_df['name'].tolist() if name != row['name']]
                        edited_name = st.text_input("New Name", value=row['name']).strip()
                        col1, col2 = st.columns(2)
                        save = col1.form_submit_button("Save")
                        cancel = col2.form_submit_button("Cancel")
                        
                        if save:
                            valid, error_msg = validate_name(edited_name, other_categories)
                            if valid:
                                try:
                                    # First verify we can still access the record
                                    verify = supabase.table('categories').select('*').eq('id', row['id']).execute()
                                    if not verify.data:
                                        handle_operation_result(False, "Category no longer exists")
                                        st.session_state.editing_category = None
                                        st.rerun()
                                        return
                                    
                                    # Log the current user's role
                                    user = supabase.auth.get_user()
                                    logger.info(f"Current user role: {user.user.role if user else 'anonymous'}")
                                    
                                    # Attempt the update
                                    result = supabase.table('categories').update(
                                        {
                                            "name": edited_name,
                                            "updated_at": "now()"
                                        }
                                    ).eq('id', row['id']).execute()
                                    
                                    # Log the response
                                    logger.info(f"Update response: {result}")
                                    
                                    clear_metadata_cache()
                                    time.sleep(0.1)
                                    st.session_state.editing_category = None
                                    handle_operation_result(True, f"Updated category to: {edited_name}")
                                    st.rerun()
                                except Exception as e:
                                    error_msg = str(e)
                                    logger.error(f"Update error: {error_msg}")
                                    
                                    if "new row violates row-level security" in error_msg.lower():
                                        handle_operation_result(False, "⚠️ You don't have permission to edit categories. Please sign in or contact your administrator.")
                                    elif "duplicate key value" in error_msg.lower():
                                        handle_operation_result(False, f"A category with the name '{edited_name}' already exists.")
                                    elif "permission denied" in error_msg.lower():
                                        handle_operation_result(False, "⚠️ Permission denied. Please sign in or contact your administrator.")
                                    else:
                                        handle_operation_result(False, f"Error updating category: {error_msg}")
                            else:
                                handle_operation_result(False, error_msg)
                        
                        if cancel:
                            st.session_state.editing_category = None
                            st.rerun()
                
                # Handle edit button click
                if edit_clicked:
                    st.session_state.editing_category = row['id']
                    st.rerun()
                
                # Handle delete button click
                if delete_clicked:
                    try:
                        # Update components to remove this category
                        supabase.table('components').update(
                            {"category_id": None}
                        ).eq('category_id', row['id']).execute()
                        
                        # Delete the category
                        supabase.table('categories').delete().eq('id', row['id']).execute()
                        clear_metadata_cache()
                        time.sleep(0.1)
                        handle_operation_result(True, f"Deleted category: {row['name']}")
                        st.rerun()
                    except Exception as e:
                        handle_operation_result(False, f"Error deleting category: {str(e)}")
                
                st.divider()
        else:
            st.info("No categories found")
    
    with tab2:
        st.header("Tags")
        
        # Add new tag form
        with st.form("add_tag_form", clear_on_submit=True):
            new_tag = st.text_input("Add New Tag")
            submit_tag = st.form_submit_button("Add Tag", on_click=on_tag_submit)
            
            if st.session_state.tag_submitted and new_tag:
                try:
                    # Check for duplicates
                    existing = supabase.table('tags').select('name').execute()
                    if any(tag['name'].lower() == new_tag.lower() for tag in existing.data):
                        st.error(f"Tag '{new_tag}' already exists.")
                    else:
                        supabase.table('tags').insert({"name": new_tag}).execute()
                        handle_operation_result(True, f"Added new tag: {new_tag}")
                        clear_metadata_cache()
                        time.sleep(0.1)
                except Exception as e:
                    handle_operation_result(False, f"Error adding tag: {str(e)}")
                finally:
                    st.session_state.tag_submitted = False
                    st.rerun()
        
        st.divider()
        
        # Display and manage existing tags
        tags_df = get_cached_tags(supabase)
        if not tags_df.empty:
            for _, row in tags_df.iterrows():
                col1, col2, col3 = st.columns([4, 1, 1])
                
                # Display name
                col1.write(row['name'])
                
                # Edit/Delete buttons
                edit_clicked = col2.button("✏️", key=f"edit_tag_{row['id']}", help="Edit tag")
                delete_clicked = col3.button("🗑️", key=f"del_tag_{row['id']}", help="Delete tag")
                
                # Edit form
                if st.session_state.editing_tag == row['id']:
                    with st.form(key=f"edit_tag_form_{row['id']}"):
                        other_tags = [name for name in tags_df['name'].tolist() if name != row['name']]
                        edited_name = st.text_input("New Name", value=row['name']).strip()
                        col1, col2 = st.columns(2)
                        save = col1.form_submit_button("Save")
                        cancel = col2.form_submit_button("Cancel")
                        
                        if save:
                            valid, error_msg = validate_name(edited_name, other_tags)
                            if valid:
                                try:
                                    # First verify we can still access the record
                                    verify = supabase.table('tags').select('*').eq('id', row['id']).execute()
                                    if not verify.data:
                                        handle_operation_result(False, "Tag no longer exists")
                                        st.session_state.editing_tag = None
                                        st.rerun()
                                        return
                                    
                                    # Log the current user's role
                                    user = supabase.auth.get_user()
                                    logger.info(f"Current user role: {user.user.role if user else 'anonymous'}")
                                    
                                    # Attempt the update
                                    result = supabase.table('tags').update(
                                        {
                                            "name": edited_name,
                                            "updated_at": "now()"
                                        }
                                    ).eq('id', row['id']).execute()
                                    
                                    # Log the response
                                    logger.info(f"Update response: {result}")
                                    
                                    clear_metadata_cache()
                                    time.sleep(0.1)
                                    st.session_state.editing_tag = None
                                    handle_operation_result(True, f"Updated tag to: {edited_name}")
                                    st.rerun()
                                except Exception as e:
                                    error_msg = str(e)
                                    logger.error(f"Update error: {error_msg}")
                                    
                                    if "new row violates row-level security" in error_msg.lower():
                                        handle_operation_result(False, "⚠️ You don't have permission to edit tags. Please sign in or contact your administrator.")
                                    elif "duplicate key value" in error_msg.lower():
                                        handle_operation_result(False, f"A tag with the name '{edited_name}' already exists.")
                                    elif "permission denied" in error_msg.lower():
                                        handle_operation_result(False, "⚠️ Permission denied. Please sign in or contact your administrator.")
                                    else:
                                        handle_operation_result(False, f"Error updating tag: {error_msg}")
                            else:
                                handle_operation_result(False, error_msg)
                        
                        if cancel:
                            st.session_state.editing_tag = None
                            st.rerun()
                
                # Handle edit button click
                if edit_clicked:
                    st.session_state.editing_tag = row['id']
                    st.rerun()
                
                # Handle delete button click
                if delete_clicked:
                    try:
                        # Delete tag (component_tags entries will be deleted by cascade)
                        supabase.table('tags').delete().eq('id', row['id']).execute()
                        clear_metadata_cache()
                        time.sleep(0.1)
                        handle_operation_result(True, f"Deleted tag: {row['name']}")
                        st.rerun()
                    except Exception as e:
                        handle_operation_result(False, f"Error deleting tag: {str(e)}")
                
                st.divider()
        else:
            st.info("No tags found")

def analytics_dashboard(supabase: Client):
    """Display the analytics dashboard."""
    try:
        st.title("Analytics Dashboard")
        
        # Get all components
        response = supabase.table('components').select("*").execute()
        if not response.data:
            st.info("No component data available for analytics")
            return
        
        df = pd.DataFrame(response.data)
        
        # Component Types Distribution
        st.subheader("Component Types Distribution")
        type_counts = df['type'].value_counts()
        fig = px.pie(values=type_counts.values, names=type_counts.index, title='Component Types')
        st.plotly_chart(fig)
        
        # Documentation Status
        st.subheader("Documentation Status")
        doc_status = df['documentation_status'].value_counts()
        fig = px.bar(x=doc_status.index, y=doc_status.values, title='Documentation Status')
        fig.update_layout(xaxis_title="Status", yaxis_title="Count")
        st.plotly_chart(fig)
        
        # Testing Coverage
        st.subheader("Testing Coverage")
        test_coverage = df[df['test_coverage'].notna()]['test_coverage']
        if not test_coverage.empty:
            fig = go.Figure(data=[go.Histogram(x=test_coverage)])
            fig.update_layout(title='Test Coverage Distribution',
                            xaxis_title="Coverage (%)",
                            yaxis_title="Count")
            st.plotly_chart(fig)
        else:
            st.info("No test coverage data available")
        
        # Components by Category
        st.subheader("Components by Category")
        categories = get_cached_categories(supabase)
        if not categories.empty:
            # Merge with categories and handle components without a category
            df_with_categories = df.merge(
                categories[['id', 'name']].rename(columns={'name': 'category_name'}),
                left_on='category_id',
                right_on='id',
                how='left'
            )
            # Fill missing category names with 'Uncategorized'
            df_with_categories['category_name'] = df_with_categories['category_name'].fillna('Uncategorized')
            
            category_counts = df_with_categories['category_name'].value_counts()
            fig = px.bar(x=category_counts.index, y=category_counts.values, title='Components by Category')
            fig.update_layout(xaxis_title="Category", yaxis_title="Count")
            st.plotly_chart(fig)
        
    except Exception as e:
        logger.error(f"Error generating analytics: {str(e)}")
        st.error("Error generating analytics dashboard")
