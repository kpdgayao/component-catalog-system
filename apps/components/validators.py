"""Validation functions for component data."""

import streamlit as st
from typing import Dict, Any

def validate_component_data(data: Dict[str, Any]) -> bool:
    """Validate component data before saving."""
    required_fields = {
        'name': 'Component Name',
        'type': 'Component Type',
        'version': 'Version',
        'description': 'Description',
        'category_id': 'Category'
    }
    
    # Check required fields
    missing_fields = []
    for field, label in required_fields.items():
        if not data.get(field):
            missing_fields.append(label)
    
    if missing_fields:
        st.error(f"Please fill in all required fields: {', '.join(missing_fields)}")
        return False
    
    # Validate version format (basic semver check)
    version = data.get('version', '')
    if not version.replace('.', '').isdigit():
        st.error("Version must be in semantic versioning format (e.g., 1.0.0)")
        return False
    
    # Validate lists
    list_fields = ['technology_stack', 'dependencies', 'aws_services']
    for field in list_fields:
        value = data.get(field, [])
        if value and not isinstance(value, list):
            st.error(f"{field} must be a list")
            return False
    
    return True
