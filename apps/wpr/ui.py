"""WPR UI components."""

import streamlit as st
import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime
from .config import WPRConfig
from .database import WPRDatabase

logger = logging.getLogger(__name__)

class WPRUI:
    def __init__(self, config: WPRConfig, database: WPRDatabase):
        """Initialize WPR UI."""
        self.config = config
        self.database = database
        
    def render_header(self):
        """Render the WPR header."""
        st.title("IOL Weekly Progress Report")
        st.write(f"Week {st.session_state.wpr_week_number}, {st.session_state.wpr_year}")
        
    def render_employee_view(self):
        """Render the employee view."""
        if not st.session_state.get('authenticated', False):
            st.error("Please log in to submit your WPR.")
            return
            
        # Week selector
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.wpr_week_number = st.selectbox(
                "Select Week",
                range(1, 53),
                index=st.session_state.wpr_week_number - 1
            )
        with col2:
            st.session_state.wpr_year = st.selectbox(
                "Select Year",
                [2023, 2024, 2025],
                index=[2023, 2024, 2025].index(st.session_state.wpr_year)
            )
            
        # Get existing report
        report = self.database.get_report(
            st.session_state.user.email,
            st.session_state.wpr_week_number,
            st.session_state.wpr_year
        )
        
        if report:
            st.info("You have already submitted a report for this week. You can edit it below.")
            
        # Display form
        self.render_wpr_form(report)
        
    def render_hr_view(self):
        """Render the HR view."""
        if not st.session_state.get('authenticated', False):
            st.error("Please log in to access the HR dashboard.")
            return
            
        st.header("HR Dashboard")
        
        # Team filter
        teams = self.config.get_teams()
        selected_team = st.selectbox("Select Team", teams)
        
        # Week filter
        col1, col2 = st.columns(2)
        with col1:
            week = st.selectbox(
                "Select Week",
                range(1, 53),
                index=st.session_state.wpr_week_number - 1
            )
        with col2:
            year = st.selectbox(
                "Select Year",
                [2023, 2024, 2025],
                index=[2023, 2024, 2025].index(st.session_state.wpr_year)
            )
            
        # Get team reports
        reports = self.database.get_team_reports(selected_team, week, year)
        if not reports:
            st.warning("No reports found for this team and week.")
            return
            
        # Display reports
        for report in reports:
            with st.expander(f"{report['name']} - {report['email']}", expanded=True):
                self.display_report(report)
                
    def render_wpr_form(self, existing_report: Dict[str, Any] = None):
        """Render the WPR form."""
        with st.form("wpr_form"):
            # Tasks
            st.subheader("Tasks")
            completed_tasks = st.text_area(
                "Completed Tasks",
                value="\n".join(existing_report.get('completed_tasks', [])) if existing_report else "",
                height=150,
                help="Enter each task on a new line"
            )
            
            pending_tasks = st.text_area(
                "Pending Tasks",
                value="\n".join(existing_report.get('pending_tasks', [])) if existing_report else "",
                height=150,
                help="Enter each task on a new line"
            )
            
            # Projects
            st.subheader("Projects")
            projects = st.text_area(
                "Project Updates",
                value=self._format_projects(existing_report.get('projects', [])) if existing_report else "",
                height=150,
                help="Format: Project Name, Completion % (e.g., 'UI Redesign, 75')"
            )
            
            # Productivity
            st.subheader("Productivity")
            productivity_rating = st.slider(
                "Rate your productivity this week",
                1, 4,
                value=existing_report.get('productivity_rating', 3),
                help="1 = Low, 4 = High"
            )
            
            productivity_suggestions = st.multiselect(
                "What would help improve your productivity?",
                self.config.PRODUCTIVITY_SUGGESTIONS,
                default=existing_report.get('productivity_suggestions', []) if existing_report else []
            )
            
            productivity_details = st.text_area(
                "Additional productivity details",
                value=existing_report.get('productivity_details', ''),
                help="Any other factors affecting your productivity"
            )
            
            # Time and location preferences
            col1, col2 = st.columns(2)
            with col1:
                productive_time = st.selectbox(
                    "Most productive time of day",
                    self.config.TIME_SLOTS,
                    index=self.config.TIME_SLOTS.index(existing_report.get('productive_time', 'Morning')) if existing_report and existing_report.get('productive_time') else 0
                )
            with col2:
                productive_place = st.selectbox(
                    "Most productive work location",
                    self.config.WORK_LOCATIONS,
                    index=self.config.WORK_LOCATIONS.index(existing_report.get('productive_place', 'Office')) if existing_report and existing_report.get('productive_place') else 0
                )
            
            # Peer evaluation
            st.subheader("Peer Evaluation")
            team = self.config.get_team_for_member(st.session_state.user.email)
            if team:
                teammates = [
                    member for member in self.config.TEAMS[team]
                    if member != st.session_state.user.email
                ]
                peer_ratings = {}
                for teammate in teammates:
                    rating = st.slider(
                        f"Rate {teammate}'s contribution",
                        1, 4,
                        value=existing_report.get('peer_ratings', {}).get(teammate, 3) if existing_report else 3,
                        help="1 = Low, 4 = High"
                    )
                    peer_ratings[teammate] = rating
                    
            # Submit button
            if st.form_submit_button("Submit WPR"):
                try:
                    # Validate inputs
                    if not completed_tasks.strip() and not pending_tasks.strip():
                        st.error("Please enter at least one completed or pending task.")
                        return
                        
                    # Prepare data
                    data = {
                        "email": st.session_state.user.email,
                        "week_number": st.session_state.wpr_week_number,
                        "year": st.session_state.wpr_year,
                        "completed_tasks": [t.strip() for t in completed_tasks.split("\n") if t.strip()],
                        "pending_tasks": [t.strip() for t in pending_tasks.split("\n") if t.strip()],
                        "projects": self._parse_projects(projects),
                        "productivity_rating": productivity_rating,
                        "productivity_suggestions": productivity_suggestions,
                        "productivity_details": productivity_details,
                        "productive_time": productive_time,
                        "productive_place": productive_place,
                        "peer_ratings": peer_ratings if team else {}
                    }
                    
                    # Save report
                    if existing_report:
                        success = self.database.update_report(data, existing_report['id'])
                        message = "Report updated successfully!"
                    else:
                        success = self.database.save_report(data)
                        message = "Report submitted successfully!"
                        
                    if success:
                        st.success(message)
                        st.balloons()
                    else:
                        st.error("Error saving report. Please try again.")
                        
                except Exception as e:
                    logger.error(f"Error submitting report: {str(e)}")
                    st.error(f"Error: {str(e)}")
                    
    def display_report(self, report: Dict[str, Any]):
        """Display a WPR report."""
        st.write("### Tasks")
        if report.get('completed_tasks'):
            st.write("**Completed Tasks:**")
            for task in report['completed_tasks']:
                st.write(f"- {task}")
                
        if report.get('pending_tasks'):
            st.write("**Pending Tasks:**")
            for task in report['pending_tasks']:
                st.write(f"- {task}")
                
        if report.get('projects'):
            st.write("### Projects")
            for project in report['projects']:
                st.write(f"- {project['name']}: {project['completion']}% complete")
                
        st.write("### Productivity")
        st.write(f"Rating: {report.get('productivity_rating', 'Not specified')}/4")
        st.write(f"Most productive time: {report.get('productive_time', 'Not specified')}")
        st.write(f"Preferred location: {report.get('productive_place', 'Not specified')}")
        
        if report.get('productivity_suggestions'):
            st.write("Suggestions for improvement:")
            for suggestion in report['productivity_suggestions']:
                st.write(f"- {suggestion}")
                
        if report.get('productivity_details'):
            st.write(f"Additional details: {report['productivity_details']}")
            
        if report.get('peer_ratings'):
            st.write("### Peer Ratings")
            for teammate, rating in report['peer_ratings'].items():
                st.write(f"- {teammate}: {rating}/4")
                
    def _format_projects(self, projects: List[Dict[str, Any]]) -> str:
        """Format projects for display in text area."""
        if not projects:
            return ""
        return "\n".join([
            f"{p['name']}, {p['completion']}"
            for p in projects
        ])
        
    def _parse_projects(self, projects_text: str) -> List[Dict[str, Any]]:
        """Parse projects from text area."""
        projects = []
        if not projects_text:
            return projects
            
        for line in projects_text.split("\n"):
            if line.strip():
                try:
                    name, completion = line.split(",")
                    projects.append({
                        "name": name.strip(),
                        "completion": int(completion.strip())
                    })
                except Exception as e:
                    logger.error(f"Error parsing project line '{line}': {str(e)}")
                    st.error(f"Invalid project format: {line}")
        return projects
