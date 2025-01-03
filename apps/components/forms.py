"""Form handling for the component catalog."""
import streamlit as st
import pandas as pd
import uuid
import json
from datetime import datetime
from typing import Optional, Dict, Any
from supabase import Client
import logging

from .validators import validate_component_data
from .utils import (
    handle_supabase_error,
    get_cached_tags,
    get_cached_categories,
    performance_monitor
)

logger = logging.getLogger(__name__)

# Constants
COMPONENT_TYPES = ["Frontend", "Backend", "Full Stack", "UI", "Service", "Utility", "Integration"]

def clear_form_state():
    """Clear all form-related state."""
    keys_to_clear = [
        "form_data",
        "component_step",
        "edit_component",
        "current_component",
        "adding_component",
        "editing"
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

def render_progress_bar(current_step: int, total_steps: int):
    """Render a progress bar with step information."""
    progress = (current_step + 1) / total_steps
    st.progress(progress)
    st.write(f"Step {current_step + 1} of {total_steps}")

def validate_current_step(step: int, form_data: Dict[str, Any]) -> bool:
    """Validate the current section of the form."""
    required_fields = {
        0: ['name', 'type', 'version', 'description'],  # Basic Info
        1: ['technology_stack'],  # Technical Details
        2: [],  # Testing
        3: [],  # Documentation
        4: ['category_id']  # Metadata
    }
    
    fields_to_check = required_fields[step]
    missing_fields = [field for field in fields_to_check if not form_data.get(field)]
    
    if missing_fields:
        st.error(f"Please fill in all required fields: {', '.join(missing_fields)}")
        return False
    return True

def render_navigation_buttons(current_step: int, total_steps: int, form_key: str, form_data: Dict[str, Any]) -> bool:
    """Render navigation buttons for the form wizard."""
    cols = st.columns([1, 1, 1])
    submitted = False
    
    with cols[0]:
        if current_step > 0:
            if st.form_submit_button("Previous"):
                # Save form data before navigation
                for key in st.session_state:
                    if key.startswith("form_"):
                        field_name = key[5:]  # Remove 'form_' prefix
                        st.session_state.form_data[field_name] = st.session_state[key]
                st.session_state[f"{form_key}_step"] = current_step - 1
                st.rerun()
    
    with cols[2]:
        if current_step < total_steps - 1:
            if st.form_submit_button("Next"):
                if validate_current_step(current_step, form_data):
                    # Save form data before navigation
                    for key in st.session_state:
                        if key.startswith("form_"):
                            field_name = key[5:]  # Remove 'form_' prefix
                            st.session_state.form_data[field_name] = st.session_state[key]
                    st.session_state[f"{form_key}_step"] = current_step + 1
                    st.rerun()
        else:
            if st.form_submit_button("Save", type="primary"):
                # Save form data before final submission
                for key in st.session_state:
                    if key.startswith("form_"):
                        field_name = key[5:]  # Remove 'form_' prefix
                        st.session_state.form_data[field_name] = st.session_state[key]
                submitted = validate_current_step(current_step, form_data)
    
    return submitted

@handle_supabase_error
def component_form(supabase: Client, mode: str = "add", component_data: Optional[Dict] = None) -> None:
    """Render the component form wizard."""
    # Add return to library button
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("← Return to Library"):
            clear_form_state()  # Clear all form state
            st.rerun()
    
    form_key = "component"
    
    # Initialize session state for form data
    if "form_data" not in st.session_state:
        st.session_state.form_data = component_data.copy() if component_data else {}
    
    # Initialize step counter
    if f"{form_key}_step" not in st.session_state:
        st.session_state[f"{form_key}_step"] = 0
    
    current_step = st.session_state[f"{form_key}_step"]
    
    # Form steps with their render functions
    steps = [
        ("Basic Info", lambda data: render_basic_info(data)),
        ("Technical Details", lambda data: render_technical_details(data)),
        ("Testing", lambda data: render_testing_info(data)),
        ("Documentation", lambda data: render_documentation(data)),
        ("Metadata", lambda data: render_metadata(data, supabase))
    ]
    total_steps = len(steps)
    
    # Progress bar
    progress = current_step / (total_steps - 1)
    st.progress(progress)
    
    # Step title and description
    st.subheader(f"Step {current_step + 1}: {steps[current_step][0]}")
    
    with st.form(key=f"{form_key}_wizard_{current_step}"):
        # Render current step
        steps[current_step][1](st.session_state.form_data)
        
        # Navigation
        st.markdown("---")
        if render_navigation_buttons(current_step, total_steps, form_key, st.session_state.form_data):
            if save_component(supabase, st.session_state.form_data, mode):
                clear_form_state()  # Clear form state after successful save
                st.rerun()

def render_basic_info(form_data: Dict[str, Any]):
    """Render the basic information form."""
    form_data['name'] = st.text_input(
        "Component Name *",
        value=form_data.get('name', ''),
        key="form_name",
        help="Enter a unique name for your component"
    )
    
    form_data['type'] = st.selectbox(
        "Component Type *",
        COMPONENT_TYPES,
        index=COMPONENT_TYPES.index(form_data.get('type', 'Frontend')),
        key="form_type"
    )
    
    form_data['version'] = st.text_input(
        "Version *",
        value=form_data.get('version', '1.0.0'),
        key="form_version",
        help="Semantic version (e.g., 1.0.0)"
    )
    
    form_data['description'] = st.text_area(
        "Description *",
        value=form_data.get('description', ''),
        key="form_description",
        help="Detailed description of the component"
    )
    
    form_data['original_project'] = st.text_input(
        "Original Project",
        value=form_data.get('original_project', ''),
        key="form_original_project",
        help="Project where this component was first created"
    )
    
    st.form_submit_button("Save Basic Info")

def render_technical_details(form_data: Dict[str, Any]):
    """Render the technical details form."""
    # Common technology options
    COMMON_TECHNOLOGIES = [
        "Python", "JavaScript", "TypeScript", "React", "Vue", "Angular",
        "Node.js", "Django", "Flask", "FastAPI", "PostgreSQL", "MySQL",
        "MongoDB", "Redis", "Docker", "Kubernetes", "AWS", "Azure",
        "Google Cloud", "REST API", "GraphQL", "Microservices"
    ]
    
    # Technology Stack - always ensure it's a list
    current_tech = []
    if 'technology_stack' in form_data:
        if isinstance(form_data['technology_stack'], list):
            current_tech = form_data['technology_stack']
        elif isinstance(form_data['technology_stack'], str):
            try:
                current_tech = json.loads(form_data['technology_stack'])
                if not isinstance(current_tech, list):
                    current_tech = []
            except (json.JSONDecodeError, TypeError):
                current_tech = []
    
    # Use multiselect for technology stack
    form_data['technology_stack'] = st.multiselect(
        "Technology Stack *",
        options=COMMON_TECHNOLOGIES + [tech for tech in current_tech if tech not in COMMON_TECHNOLOGIES],
        default=current_tech,
        key="form_technology_stack"
    )
    
    # Dependencies - always ensure it's a list
    current_deps = []
    if 'dependencies' in form_data:
        if isinstance(form_data['dependencies'], list):
            current_deps = form_data['dependencies']
        elif isinstance(form_data['dependencies'], str):
            try:
                current_deps = json.loads(form_data['dependencies'])
                if not isinstance(current_deps, list):
                    current_deps = []
            except (json.JSONDecodeError, TypeError):
                current_deps = []
    
    # Use multiselect for dependencies
    form_data['dependencies'] = st.multiselect(
        "Dependencies",
        options=list(set(current_deps)),  # Use existing dependencies as options
        default=current_deps,
        key="form_dependencies"
    )
    
    # AWS Services - always ensure it's a list
    current_aws = []
    if 'aws_services' in form_data:
        if isinstance(form_data['aws_services'], list):
            current_aws = form_data['aws_services']
        elif isinstance(form_data['aws_services'], str):
            try:
                current_aws = json.loads(form_data['aws_services'])
                if not isinstance(current_aws, list):
                    current_aws = []
            except (json.JSONDecodeError, TypeError):
                current_aws = []
    
    # Use multiselect for AWS services
    form_data['aws_services'] = st.multiselect(
        "AWS Services",
        options=list(set(current_aws)),  # Use existing services as options
        default=current_aws,
        key="form_aws_services"
    )
    
    # Text fields remain the same
    form_data['auth_requirements'] = st.text_area(
        "Authentication Requirements",
        value=form_data.get('auth_requirements', ''),
        key="form_auth_requirements"
    )
    
    form_data['db_requirements'] = st.text_area(
        "Database Requirements",
        value=form_data.get('db_requirements', ''),
        key="form_db_requirements"
    )
    
    form_data['api_endpoints'] = st.text_area(
        "API Endpoints",
        value=form_data.get('api_endpoints', ''),
        key="form_api_endpoints"
    )
    
    st.subheader("Integration Details")
    form_data['setup_instructions'] = st.text_area(
        "Setup Instructions",
        value=form_data.get('setup_instructions', ''),
        key="form_setup_instructions",
        help="Step-by-step setup guide"
    )
    
    form_data['configuration_requirements'] = st.text_area(
        "Configuration Requirements",
        value=form_data.get('configuration_requirements', ''),
        key="form_configuration_requirements",
        help="Required configuration settings"
    )
    
    form_data['integration_patterns'] = st.text_area(
        "Integration Patterns",
        value=form_data.get('integration_patterns', ''),
        key="form_integration_patterns",
        help="Common integration patterns and best practices"
    )
    
    form_data['troubleshooting_guide'] = st.text_area(
        "Troubleshooting Guide",
        value=form_data.get('troubleshooting_guide', ''),
        key="form_troubleshooting_guide",
        help="Common issues and solutions"
    )
    
    st.form_submit_button("Save Technical Details")

def render_testing_info(form_data: Dict[str, Any]):
    """Render the testing information form."""
    col1, col2 = st.columns(2)
    
    with col1:
        form_data['has_unit_tests'] = st.checkbox(
            "Has Unit Tests",
            value=form_data.get('has_unit_tests', False),
            key="form_has_unit_tests"
        )
        
        if form_data['has_unit_tests']:
            # Handle the case where test_coverage is None or not a number
            current_coverage = form_data.get('test_coverage')
            if current_coverage is None or not isinstance(current_coverage, (int, float)):
                current_coverage = 0
            
            form_data['test_coverage'] = st.number_input(
                "Test Coverage (%)",
                min_value=0,
                max_value=100,
                value=int(current_coverage),
                key="form_test_coverage"
            )
    
    with col2:
        form_data['has_integration_tests'] = st.checkbox(
            "Has Integration Tests",
            value=form_data.get('has_integration_tests', False),
            key="form_has_integration_tests"
        )
        
        form_data['has_e2e_tests'] = st.checkbox(
            "Has E2E Tests",
            value=form_data.get('has_e2e_tests', False),
            key="form_has_e2e_tests"
        )
    
    st.subheader("Performance")
    form_data['performance_metrics'] = st.text_area(
        "Performance Metrics",
        value=form_data.get('performance_metrics', ''),
        key="form_performance_metrics",
        help="Key performance indicators and metrics"
    )
    
    form_data['known_limitations'] = st.text_area(
        "Known Limitations",
        value=form_data.get('known_limitations', ''),
        key="form_known_limitations",
        help="Known issues or constraints"
    )
    
    st.form_submit_button("Save Testing Info")

def render_documentation(form_data: Dict[str, Any]):
    """Render the documentation form."""
    form_data['documentation_status'] = st.selectbox(
        "Documentation Status",
        ["Complete", "Partial", "Needs Update", "None"],
        index=["Complete", "Partial", "Needs Update", "None"].index(
            form_data.get('documentation_status', 'None')
        ),
        key="form_documentation_status"
    )
    
    st.subheader("Business Value")
    col1, col2 = st.columns(2)
    with col1:
        # Handle business_value properly
        business_value = form_data.get('business_value', {})
        if isinstance(business_value, str):
            try:
                business_value = json.loads(business_value)
            except:
                business_value = {}
        if not isinstance(business_value, dict):
            business_value = {}
            
        time_saved = st.number_input(
            "Time Saved (hours)",
            min_value=0.0,
            value=float(business_value.get('time_saved', 0)),
            step=0.5,
            format="%.1f",
            key="form_time_saved"
        )
    with col2:
        cost_savings = st.number_input(
            "Cost Savings ($)",
            min_value=0.0,
            value=float(business_value.get('cost_savings', 0)),
            step=100.0,
            format="%.2f",
            key="form_cost_savings"
        )
    
    risk_reduction = st.text_area(
        "Risk Reduction",
        value=business_value.get('risk_reduction', ''),
        key="form_risk_reduction",
        help="How this component reduces risk"
    )
    
    client_benefits = st.text_area(
        "Client Benefits",
        value=business_value.get('client_benefits', ''),
        key="form_client_benefits",
        help="Direct benefits to clients"
    )
    
    # Store business value in form_data
    form_data['business_value'] = {
        'time_saved': time_saved,
        'cost_savings': cost_savings,
        'risk_reduction': risk_reduction,
        'client_benefits': client_benefits
    }
    
    st.subheader("Maintenance")
    form_data['update_frequency'] = st.text_input(
        "Update Frequency",
        value=form_data.get('update_frequency', ''),
        key="form_update_frequency",
        help="How often the component is updated"
    )
    
    form_data['breaking_changes_history'] = st.text_area(
        "Breaking Changes History",
        value=form_data.get('breaking_changes_history', ''),
        key="form_breaking_changes_history",
        help="History of major breaking changes"
    )
    
    form_data['backward_compatibility_notes'] = st.text_area(
        "Backward Compatibility Notes",
        value=form_data.get('backward_compatibility_notes', ''),
        key="form_backward_compatibility_notes",
        help="Notes about version compatibility"
    )
    
    form_data['support_contact'] = st.text_input(
        "Support Contact",
        value=form_data.get('support_contact', ''),
        key="form_support_contact",
        help="Primary contact for support"
    )
    
    st.form_submit_button("Save Documentation")

def render_metadata(form_data: Dict[str, Any], supabase: Client):
    """Render the metadata form."""
    # Categories
    categories = get_cached_categories(supabase)
    if not categories.empty:
        # Convert to plain Python lists
        category_names = categories['name'].tolist()
        category_ids = categories['id'].tolist()
        
        # Create a mapping of names to IDs
        category_map = dict(zip(category_names, category_ids))
        
        # Find current category name if exists
        current_category = None
        if form_data.get('category_id'):
            current_category = next(
                (name for name, id_ in category_map.items() 
                 if str(id_) == str(form_data['category_id'])),
                category_names[0]
            )
        
        selected_category = st.selectbox(
            "Category *",
            options=category_names,
            index=category_names.index(current_category) if current_category else 0,
            key="form_category"
        )
        
        # Store the selected category ID
        form_data['category_id'] = category_map[selected_category]
    
    # Tags
    tags = get_cached_tags(supabase)
    if not tags.empty:
        # Convert to plain Python lists
        tag_names = tags['name'].tolist()
        tag_ids = tags['id'].tolist()
        tag_map = dict(zip(tag_names, tag_ids))
        
        # Get current tags if they exist
        current_tags = []
        if form_data.get('component_tags'):
            current_tags = [
                tag['tags']['name'] 
                for tag in form_data['component_tags'] 
                if isinstance(tag, dict) and 'tags' in tag
            ]
        
        selected_tags = st.multiselect(
            "Tags",
            options=tag_names,
            default=current_tags,
            key="form_tags"
        )
        
        # Store the selected tag IDs
        form_data['selected_tags'] = [tag_map[tag] for tag in selected_tags]

    st.form_submit_button("Save Metadata")

def clean_component_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Clean component data before saving to database."""
    # Create a new dict instead of copying to avoid circular references
    cleaned_data = {}
    
    # Define fields that should be included in the database
    db_fields = {
        # Basic Info
        'name', 'type', 'version', 'description', 'original_project',
        # Technical Details
        'technology_stack', 'dependencies', 'aws_services',
        'auth_requirements', 'db_requirements', 'api_endpoints',
        'setup_instructions', 'configuration_requirements',
        'integration_patterns', 'troubleshooting_guide',
        # Testing
        'has_unit_tests', 'test_coverage', 'has_integration_tests',
        'has_e2e_tests', 'performance_metrics', 'known_limitations',
        # Documentation
        'documentation_status', 'business_value',
        'update_frequency', 'breaking_changes_history',
        'backward_compatibility_notes', 'support_contact',
        # Metadata
        'category_id', 'id'
    }
    
    # Only copy fields that should go to the database
    for field in db_fields:
        if field in data:
            cleaned_data[field] = data[field]
    
    # Handle list fields
    list_fields = ['technology_stack', 'dependencies', 'aws_services']
    for field in list_fields:
        if field not in cleaned_data:
            cleaned_data[field] = []
        elif not isinstance(cleaned_data[field], list):
            # Convert to list if it's not already
            if isinstance(cleaned_data[field], str):
                try:
                    cleaned_data[field] = json.loads(cleaned_data[field])
                except (json.JSONDecodeError, TypeError):
                    cleaned_data[field] = [cleaned_data[field]] if cleaned_data[field] else []
            else:
                cleaned_data[field] = []
        
        # Clean the list items
        cleaned_data[field] = [
            str(item).strip()
            for item in cleaned_data[field]
            if item and str(item).strip()
        ]
    
    # Handle business_value field
    if 'business_value' in cleaned_data:
        if isinstance(cleaned_data['business_value'], str):
            try:
                cleaned_data['business_value'] = json.loads(cleaned_data['business_value'])
            except (json.JSONDecodeError, TypeError):
                cleaned_data['business_value'] = {}
        if not isinstance(cleaned_data['business_value'], dict):
            cleaned_data['business_value'] = {}
    else:
        cleaned_data['business_value'] = {}
    
    # Convert empty strings to None for non-list fields
    for key, value in cleaned_data.items():
        if key not in list_fields and isinstance(value, str) and not value.strip():
            cleaned_data[key] = None
    
    return cleaned_data

@handle_supabase_error
def save_component(supabase: Client, form_data: Dict[str, Any], mode: str = "add") -> bool:
    """Save component data to the database."""
    try:
        # Validate data
        if not validate_component_data(form_data):
            return False
        
        # Clean data
        component_data = clean_component_data(form_data)
        
        # Get selected tags
        selected_tags = form_data.get('selected_tags', [])
        
        if mode == "add":
            # Insert new component
            response = supabase.table('components').insert(component_data).execute()
            if not response.data:
                st.error("Failed to create component")
                return False
            
            component_id = response.data[0]['id']
            
            # Add tags
            if selected_tags:
                tag_data = [
                    {"component_id": component_id, "tag_id": tag_id}
                    for tag_id in selected_tags
                ]
                supabase.table('component_tags').insert(tag_data).execute()
            
            st.success("Component created successfully!")
            return True
            
        else:  # Edit mode
            component_id = form_data.get('id')
            if not component_id:
                st.error("Component ID not found")
                return False
            
            # Update component
            response = supabase.table('components').update(
                component_data
            ).eq('id', component_id).execute()
            
            if not response.data:
                st.error("Failed to update component")
                return False
            
            # Update tags
            if selected_tags is not None:
                # Delete existing tags
                supabase.table('component_tags').delete().eq(
                    'component_id', component_id
                ).execute()
                
                # Insert new tags
                if selected_tags:
                    tag_data = [
                        {"component_id": component_id, "tag_id": tag_id}
                        for tag_id in selected_tags
                    ]
                    supabase.table('component_tags').insert(tag_data).execute()
            
            st.success("Component updated successfully!")
            return True
            
    except Exception as e:
        logger.error(f"Error saving component: {str(e)}")
        st.error(f"Error saving component: {str(e)}")
        return False

@handle_supabase_error
def edit_component(supabase: Client, component: Dict[str, Any]):
    """Edit an existing component."""
    st.title("Edit Component")
    component_form(supabase, mode="edit", component_data=component)

@handle_supabase_error
def add_component(supabase: Client):
    """Add a new component."""
    st.title("Add New Component")
    component_form(supabase, mode="add")
