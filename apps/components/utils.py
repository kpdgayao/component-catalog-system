"""Utility functions for the component catalog."""

import functools
import time
import logging
import pandas as pd
import streamlit as st
from typing import Any, Callable, Optional
from supabase import Client

logger = logging.getLogger(__name__)

# Cache keys for better management
CACHE_KEYS = {
    'tags': 'component_tags_cache',
    'categories': 'component_categories_cache'
}

def handle_supabase_error(func: Callable) -> Callable:
    """Decorator to handle Supabase errors."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            logger.debug(f"Supabase operation successful: {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            if hasattr(e, 'code'):
                logger.error(f"Error code: {e.code}")
            if hasattr(e, 'details'):
                logger.error(f"Error details: {e.details}")
            st.error(f"An error occurred: {str(e)}")
            return None
    return wrapper

def performance_monitor(func: Callable) -> Callable:
    """Decorator to monitor function performance."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        if duration > 1.0:  # Log if execution takes more than 1 second
            logger.warning(f"{func.__name__} took {duration:.2f} seconds to execute")
        return result
    return wrapper

def clear_metadata_cache():
    """Clear all metadata-related caches."""
    try:
        # Clear Streamlit cache
        st.cache_data.clear()
        
        # Clear specific cache keys from session state
        for cache_key in CACHE_KEYS.values():
            if cache_key in st.session_state:
                del st.session_state[cache_key]
        
        logger.info("Cleared metadata cache")
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise

@st.cache_data(ttl=30, show_spinner=False)
def get_cached_tags(_supabase: Client) -> pd.DataFrame:
    """Get cached tags data with improved error handling and caching."""
    try:
        # Check session state cache first
        cache_key = CACHE_KEYS['tags']
        if cache_key in st.session_state:
            return st.session_state[cache_key]

        # Fetch from database
        response = _supabase.table('tags').select('*').order('name').execute()
        if not response.data:
            df = pd.DataFrame(columns=['id', 'name'])
        else:
            df = pd.DataFrame(response.data)
            df['id'] = df['id'].astype(str)
        
        # Update session state cache
        st.session_state[cache_key] = df
        return df
    except Exception as e:
        logger.error(f"Error fetching tags: {str(e)}")
        # Return empty DataFrame with correct schema
        return pd.DataFrame(columns=['id', 'name'])

@st.cache_data(ttl=30, show_spinner=False)
def get_cached_categories(_supabase: Client) -> pd.DataFrame:
    """Get cached categories data with improved error handling and caching."""
    try:
        # Check session state cache first
        cache_key = CACHE_KEYS['categories']
        if cache_key in st.session_state:
            return st.session_state[cache_key]

        # Fetch from database
        response = _supabase.table('categories').select('*').order('name').execute()
        if not response.data:
            df = pd.DataFrame(columns=['id', 'name'])
        else:
            df = pd.DataFrame(response.data)
            df['id'] = df['id'].astype(str)
        
        # Update session state cache
        st.session_state[cache_key] = df
        return df
    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}")
        # Return empty DataFrame with correct schema
        return pd.DataFrame(columns=['id', 'name'])
