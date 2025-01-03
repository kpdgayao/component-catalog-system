"""Component catalog utilities."""

import pandas as pd
from typing import Optional
from supabase import Client
import streamlit as st
from .utils import (
    get_cached_categories,
    get_cached_tags,
    clear_metadata_cache,
    handle_supabase_error
)

@handle_supabase_error
def get_categories(supabase: Client) -> pd.DataFrame:
    """Get categories data with error handling."""
    return get_cached_categories(supabase)

@handle_supabase_error
def get_tags(supabase: Client) -> pd.DataFrame:
    """Get tags data with error handling."""
    return get_cached_tags(supabase)

@handle_supabase_error
def upload_file(supabase: Client, file_data: bytes, file_name: str, component_id: str) -> bool:
    """Upload a file for a component with improved error handling."""
    try:
        # Generate storage path
        storage_path = f"components/{component_id}/{file_name}"
        
        # Upload to storage
        supabase.storage.from_("component-files").upload(
            storage_path,
            file_data
        )
        
        # Create file record
        file_type = file_name.split('.')[-1] if '.' in file_name else 'unknown'
        file_size = len(file_data)
        
        supabase.table('component_files').insert({
            'component_id': component_id,
            'file_name': file_name,
            'file_type': file_type,
            'storage_path': storage_path,
            'file_size': file_size
        }).execute()
        
        return True
    except Exception as e:
        st.error(f"Error uploading file: {str(e)}")
        return False

def clear_all_metadata_cache() -> None:
    """Clear all metadata cache with improved error handling."""
    try:
        from .utils import clear_metadata_cache as utils_clear_cache
        utils_clear_cache()
        st.success("Cache cleared successfully")
    except Exception as e:
        st.error(f"Error clearing cache: {str(e)}")
