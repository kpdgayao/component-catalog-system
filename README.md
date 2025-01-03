# Component Catalog System

A comprehensive Streamlit-based web application for managing and tracking reusable software components at IOL Inc. This system helps teams discover, share, and maintain software components across the organization.

Last updated: 2025-01-03

## Features

### Component Management
- **Component Library**: Browse, search, and filter components with an intuitive interface
- **Detailed Views**: View comprehensive component information including documentation, testing status, and usage metrics
- **Component Creation**: Multi-step wizard for adding new components with validation
- **Version Control**: Track component versions and changes over time
- **File Attachments**: Support for documentation files and code samples

### Analytics & Insights
- **Usage Dashboard**: Track component adoption and usage patterns
- **Performance Metrics**: Monitor component performance and reliability
- **Business Value Tracking**: Measure and visualize component impact
- **Custom Reports**: Generate insights based on various metrics

### Metadata Management
- **Categories**: Organize components by type and function
- **Tags**: Flexible tagging system for better discoverability
- **Custom Fields**: Support for additional metadata as needed
- **Bulk Operations**: Efficient management of metadata across multiple components

### Security & Access Control
- **Role-based Access**: Granular control over user permissions
- **Secure Authentication**: Integration with Supabase for robust auth
- **Audit Logging**: Track changes and access patterns
- **Data Validation**: Input validation and sanitization

## Technical Stack

- **Frontend**: Streamlit (v1.31.0)
- **Backend**: Python with Supabase integration
- **Database**: PostgreSQL (via Supabase)
- **Authentication**: Supabase Auth
- **Storage**: Supabase Storage for file attachments
- **Visualization**: Plotly (v5.18.0) and Matplotlib (v3.8.2)

## Setup Instructions

1. Clone the repository:
```bash
git clone https://github.com/kpdgayao/component-catalog-system.git
cd component-catalog-system
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure Supabase credentials:
   - Create a `.streamlit/secrets.toml` file with your Supabase credentials:
```toml
supabase_url = "your-supabase-url"
supabase_key = "your-supabase-anon-key"
```

5. Run the application:
```bash
streamlit run main.py
```

## Project Structure

```
component-catalog-system/
├── apps/
│   ├── components/          # Component management module
│   │   ├── catalog.py      # Component catalog utilities
│   │   ├── component_app.py # Main component application
│   │   ├── forms.py        # Form handling and validation
│   │   ├── utils.py        # Utility functions
│   │   └── views.py        # UI views and layouts
│   └── auth.py             # Authentication handling
├── db/
│   └── policies.sql        # Database policies and security rules
├── tests/                  # Test suite
├── main.py                 # Application entry point
└── requirements.txt        # Project dependencies
```

## Usage Guide

1. **Login**: Access the system using your organization credentials
2. **Navigation**: Use the sidebar to switch between different views:
   - Component Library
   - Analytics Dashboard
   - Metadata Management
3. **Component Operations**:
   - Browse components using search and filters
   - View detailed component information
   - Add new components using the wizard
   - Edit existing components as needed
4. **Analytics**: Access the dashboard for insights on:
   - Component usage trends
   - Adoption metrics
   - Performance indicators
   - Business value assessment

## Testing

Run the test suite:
```bash
pytest
```

For coverage report:
```bash
pytest --cov=apps tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

Proprietary - IOL Inc. All rights reserved.

## Support

For issues and support, please contact the development team or create an issue in the repository.
