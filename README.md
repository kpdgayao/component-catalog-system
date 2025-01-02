# Component Catalog System

A Streamlit-based web application for managing reusable software components at IOL Inc.

Last updated: 2025-01-02

## Setup Instructions

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure Supabase credentials:
   - Create a `.streamlit/secrets.toml` file with your Supabase credentials:
```toml
supabase_url = "your-supabase-url"
supabase_key = "your-supabase-anon-key"
```

3. Run the application:
```bash
streamlit run streamlit_app.py
```

## Features

- Component Library with search and filtering
- Add and edit components
- Analytics dashboard
- Role-based access control
- Secure authentication via Supabase

## Usage

1. Log in using your Supabase credentials
2. Use the sidebar to navigate between different views
3. View, add, or edit components as needed
4. Check analytics in the dashboard
