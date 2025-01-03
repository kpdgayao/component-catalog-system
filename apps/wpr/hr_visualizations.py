"""HR dashboard visualization components."""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
from .styles import WPRStyles

class HRVisualizations:
    """HR dashboard visualization components."""
    
    @staticmethod
    def display_hr_dashboard(current_analysis: Dict[str, Any], historical_data: Optional[List[Dict[str, Any]]] = None):
        """Display comprehensive HR analysis dashboard."""
        try:
            if not current_analysis:
                WPRStyles.show_warning("No HR analysis data available to display.")
                return

            WPRStyles.section_header("HR Analysis Dashboard")

            # Create tabs for different views
            overview_tab, skills_tab, trends_tab, wellness_tab = st.tabs([
                "📊 Overview",
                "💪 Skills & Development",
                "📈 Performance Trends",
                "🌟 Wellness"
            ])
            
            with overview_tab:
                HRVisualizations._display_performance_overview(
                    current_analysis.get('metrics', {}),
                    current_analysis.get('recommendations', [])
                )
            
            with skills_tab:
                HRVisualizations._display_skills_overview(
                    current_analysis.get('skill_assessment', {})
                )
            
            with trends_tab:
                if historical_data:
                    HRVisualizations._display_performance_trends(historical_data)
                else:
                    st.info("No historical data available yet.")
            
            with wellness_tab:
                HRVisualizations._display_wellness_overview(
                    current_analysis.get('wellness_indicators', {}),
                    current_analysis.get('risk_factors', {})
                )

        except Exception as e:
            logging.error(f"Error displaying HR dashboard: {str(e)}")
            WPRStyles.show_warning("Error displaying HR analytics dashboard. Please try again later.")

    @staticmethod
    def _display_performance_overview(metrics: Dict[str, Any], recommendations: List[str]):
        """Display performance metrics and key recommendations."""
        WPRStyles.subsection_header("Performance Metrics")
        
        # Display metrics in columns
        col1, col2, col3, col4 = st.columns(4)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        
        with col1:
            st.metric(
                "Productivity",
                f"{metrics.get('productivity_score', 0):.1f}/4",
                delta=metrics.get('productivity_delta', None),
                help="Overall productivity rating"
            )
        
        with col2:
            st.metric(
                "Task Completion",
                f"{metrics.get('task_completion_rate', 0):.1f}%",
                delta=metrics.get('completion_delta', None),
                help="Percentage of completed tasks"
            )
        
        with col3:
            st.metric(
                "Project Progress",
                f"{metrics.get('project_progress', 0):.1f}%",
                delta=metrics.get('progress_delta', None),
                help="Overall project completion rate"
            )
        
        with col4:
            st.metric(
                "Collaboration",
                f"{metrics.get('collaboration_score', 0):.1f}/4",
                delta=metrics.get('collaboration_delta', None),
                help="Team collaboration rating"
            )
        
        # Display key recommendations
        if recommendations:
            WPRStyles.subsection_header("Key Recommendations")
            for rec in recommendations[:3]:  # Show top 3 recommendations
                st.info(f"📌 {rec}")
            
            if len(recommendations) > 3:
                with st.expander("View All Recommendations"):
                    for rec in recommendations[3:]:
                        st.write(f"• {rec}")

    @staticmethod
    def _display_skills_overview(skills: Dict[str, Any]):
        """Display skills assessment and development areas."""
        try:
            col1, col2 = st.columns(2)
            
            with col1:
                WPRStyles.subsection_header("💪 Key Strengths")
                strengths = skills.get('strengths', [])
                if strengths:
                    for strength in strengths:
                        st.success(f"✓ {strength}")
                else:
                    st.info("No key strengths identified yet.")
            
            with col2:
                WPRStyles.subsection_header("📈 Growth Areas")
                areas = skills.get('development_areas', [])
                if areas:
                    for area in areas:
                        st.warning(f"→ {area}")
                else:
                    st.info("No development areas identified yet.")
            
            # Development Goals
            if skills.get('development_goals'):
                with st.expander("View Development Goals"):
                    for goal in skills['development_goals']:
                        st.write(f"🎯 {goal}")
            
            # Training Recommendations
            if skills.get('training_needs'):
                with st.expander("View Training Recommendations"):
                    for training in skills['training_needs']:
                        st.write(f"📚 {training}")
                        
        except Exception as e:
            logging.error(f"Error displaying skills overview: {str(e)}")
            WPRStyles.show_warning("Error displaying skills assessment.")

    @staticmethod
    def _display_performance_trends(historical_data: List[Dict[str, Any]]):
        """Display performance trends using Plotly charts."""
        try:
            df = pd.DataFrame(historical_data)
            
            # Productivity trend
            if 'metrics' in df.columns:
                productivity_scores = [d.get('productivity_score', 0) for d in df['metrics']]
                fig = go.Figure(data=go.Scatter(
                    x=df['week_number'],
                    y=productivity_scores,
                    mode='lines+markers',
                    name='Productivity Score',
                    line=dict(color='#2E86C1', width=2),
                    marker=dict(size=8)
                ))
                fig.update_layout(
                    title='Productivity Score Trend',
                    xaxis_title='Week',
                    yaxis_title='Score',
                    template='plotly_white'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Task completion trend
            if 'metrics' in df.columns:
                completion_rates = [d.get('task_completion_rate', 0) for d in df['metrics']]
                fig = go.Figure(data=go.Scatter(
                    x=df['week_number'],
                    y=completion_rates,
                    mode='lines+markers',
                    name='Task Completion Rate',
                    line=dict(color='#28B463', width=2),
                    marker=dict(size=8)
                ))
                fig.update_layout(
                    title='Task Completion Rate Trend',
                    xaxis_title='Week',
                    yaxis_title='Completion Rate (%)',
                    template='plotly_white'
                )
                st.plotly_chart(fig, use_container_width=True)
                
        except Exception as e:
            logging.error(f"Error displaying performance trends: {str(e)}")
            WPRStyles.show_warning("Error displaying performance trends.")

    @staticmethod
    def _display_wellness_overview(wellness: Dict[str, Any], risk_factors: Dict[str, Any]):
        """Display wellness indicators and risk assessment."""
        try:
            col1, col2 = st.columns(2)
            
            with col1:
                WPRStyles.subsection_header("Wellness Indicators")
                
                # Work-Life Balance
                balance = wellness.get('work_life_balance', 'N/A')
                st.write(f"🔋 Work-Life Balance: {balance}")
                
                # Workload
                workload = wellness.get('workload_assessment', 'N/A')
                st.write(f"📊 Workload: {workload}")
                
                # Engagement
                engagement = wellness.get('engagement_level', 'N/A')
                st.write(f"⭐ Engagement: {engagement}")
            
            with col2:
                WPRStyles.subsection_header("Risk Assessment")
                
                # Risk Indicators
                burnout = risk_factors.get('burnout_risk', 'N/A')
                retention = risk_factors.get('retention_risk', 'N/A')
                trend = risk_factors.get('performance_trend', 'N/A')
                
                st.write(f"🔥 Burnout Risk: {burnout}")
                st.write(f"🎯 Retention Risk: {retention}")
                st.write(f"📈 Performance Trend: {trend}")
            
            # Additional wellness metrics if available
            if wellness.get('additional_metrics'):
                with st.expander("View Additional Wellness Metrics"):
                    for metric, value in wellness['additional_metrics'].items():
                        st.write(f"• {metric}: {value}")
                        
        except Exception as e:
            logging.error(f"Error displaying wellness overview: {str(e)}")
            WPRStyles.show_warning("Error displaying wellness information.")
