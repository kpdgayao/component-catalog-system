"""UI styling and theme components for WPR application."""

import streamlit as st

class WPRStyles:
    @staticmethod
    def load_custom_css():
        """Load custom CSS styles for WPR application."""
        custom_css = """
            <style>
                /* Main title styling */
                .title {
                    font-size: 36px;
                    font-weight: bold;
                    color: #2E86C1;
                    margin-bottom: 20px;
                    text-align: center;
                }
                
                /* Section headers */
                .section-header {
                    font-size: 24px;
                    font-weight: bold;
                    color: #2E86C1;
                    margin-top: 40px;
                    margin-bottom: 20px;
                }
                
                /* Subsection headers */
                .subsection-header {
                    font-size: 20px;
                    font-weight: bold;
                    color: #2E86C1;
                    margin-top: 30px;
                    margin-bottom: 10px;
                }
                
                /* Message styling */
                .success-message {
                    font-size: 18px;
                    font-weight: bold;
                    color: #28B463;
                    margin-top: 20px;
                    padding: 10px;
                    border-radius: 5px;
                    background-color: #EAFAF1;
                }
                
                .warning-message {
                    font-size: 18px;
                    font-weight: bold;
                    color: #F39C12;
                    margin-top: 20px;
                    padding: 10px;
                    border-radius: 5px;
                    background-color: #FEF9E7;
                }
                
                /* Button styling */
                .stButton>button {
                    background-color: #2E86C1;
                    color: white;
                    font-weight: bold;
                    padding: 10px 20px;
                    border-radius: 5px;
                    border: none;
                    transition: all 0.3s ease;
                }
                
                .stButton>button:hover {
                    background-color: #21618C;
                    transform: translateY(-2px);
                }
                
                /* Input field styling */
                .stTextInput>div>div>input {
                    border-radius: 5px;
                }
                
                /* Expander styling */
                .streamlit-expanderHeader {
                    font-weight: bold;
                    color: #2E86C1;
                }
                
                /* Metric styling */
                .stMetric {
                    background-color: #F8F9FA;
                    padding: 10px;
                    border-radius: 5px;
                }
                
                /* Chart styling */
                .plotly-chart {
                    background-color: white;
                    border-radius: 10px;
                    padding: 10px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
            </style>
        """
        st.markdown(custom_css, unsafe_allow_html=True)
    
    @staticmethod
    def show_success(message: str):
        """Display a styled success message."""
        st.markdown(
            f'<div class="success-message">{message}</div>',
            unsafe_allow_html=True
        )
    
    @staticmethod
    def show_warning(message: str):
        """Display a styled warning message."""
        st.markdown(
            f'<div class="warning-message">{message}</div>',
            unsafe_allow_html=True
        )
    
    @staticmethod
    def section_header(title: str):
        """Display a styled section header."""
        st.markdown(
            f'<div class="section-header">{title}</div>',
            unsafe_allow_html=True
        )
    
    @staticmethod
    def subsection_header(title: str):
        """Display a styled subsection header."""
        st.markdown(
            f'<div class="subsection-header">{title}</div>',
            unsafe_allow_html=True
        )
