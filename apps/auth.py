"""Authentication module for IOL applications."""

import streamlit as st
from supabase import Client

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
    if 'current_app' not in st.session_state:
        st.session_state.current_app = "Component Library"

def is_valid_iol_email(email: str) -> bool:
    """Check if the email is a valid IOL email address."""
    return email.lower().endswith('@iol.ph')

def check_session(supabase: Client) -> bool:
    """Check if the user's session is valid and refresh if needed."""
    try:
        if st.session_state.access_token:
            user = supabase.auth.get_user(st.session_state.access_token)
            if user:
                st.session_state.authenticated = True
                st.session_state.user = user.user
                return True
    except Exception:
        pass
    
    try:
        if st.session_state.refresh_token:
            response = supabase.auth.refresh_session(st.session_state.refresh_token)
            if response:
                st.session_state.access_token = response.session.access_token
                st.session_state.refresh_token = response.session.refresh_token
                st.session_state.authenticated = True
                st.session_state.user = response.user
                return True
    except Exception:
        pass
    
    return False

def handle_auth_error():
    """Handle authentication errors by clearing the session."""
    st.session_state.clear()
    initialize_session_state()

def login(supabase: Client):
    """Handle user login."""
    if "verification_requested" not in st.session_state:
        st.session_state.verification_requested = False

    st.title("IOL Inc. Platform")
    st.write("Welcome to the IOL Inc. Platform. Please login or sign up to continue.")
    st.info("Note: This system is only accessible to IOL Inc. employees with @iol.ph email addresses.")
    
    # Login form
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            if not email or not password:
                st.error("Please enter both email and password.")
                return
                
            if not is_valid_iol_email(email):
                st.error("Please use your @iol.ph email address.")
                return
                
            try:
                response = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                
                if response.user:
                    st.session_state.access_token = response.session.access_token
                    st.session_state.refresh_token = response.session.refresh_token
                    st.session_state.authenticated = True
                    st.session_state.user = response.user
                    st.rerun()
            except Exception as e:
                st.error(f"Login failed: {str(e)}")
    
    # Sign up section
    st.divider()
    st.write("Don't have an account?")
    
    with st.form("signup_form"):
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submitted = st.form_submit_button("Sign Up")
        
        if submitted:
            if not new_email or not new_password or not confirm_password:
                st.error("Please fill in all fields.")
                return
                
            if not is_valid_iol_email(new_email):
                st.error("Please use your @iol.ph email address.")
                return
                
            if new_password != confirm_password:
                st.error("Passwords do not match.")
                return
                
            try:
                response = supabase.auth.sign_up({
                    "email": new_email,
                    "password": new_password
                })
                
                if response.user:
                    st.session_state.verification_requested = True
                    st.success("Sign up successful! Please check your email to verify your account.")
            except Exception as e:
                st.error(f"Sign up failed: {str(e)}")
                
    if st.session_state.verification_requested:
        st.info("Please check your email and verify your account before logging in.")
