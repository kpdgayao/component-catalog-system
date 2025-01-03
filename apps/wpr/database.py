"""Database interface for WPR application."""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import streamlit as st
from supabase import Client

logger = logging.getLogger(__name__)

class WPRDatabase:
    def __init__(self, supabase: Optional[Client] = None):
        """Initialize database interface."""
        try:
            self.supabase = supabase or st.session_state.get('supabase_client')
            if not self.supabase:
                raise ValueError("No Supabase client provided")
            self.table = "wpr_data"
            logger.info("WPRDatabase initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing WPRDatabase: {str(e)}")
            raise
            
    def submit_wpr(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a new WPR entry."""
        try:
            # Format data to match table schema
            wpr_data = {
                "Name": data.get("name"),
                "Team": data.get("team"),
                "Week Number": data.get("week_number"),
                "Year": data.get("year"),
                "Completed Tasks": data.get("completed_tasks"),
                "Number of Completed Tasks": len(data.get("completed_tasks", [])),
                "Pending Tasks": data.get("pending_tasks"),
                "Number of Pending Tasks": len(data.get("pending_tasks", [])),
                "Dropped Tasks": data.get("dropped_tasks"),
                "Number of Dropped Tasks": len(data.get("dropped_tasks", [])),
                "Productivity Rating": data.get("productivity_rating"),
                "Productivity Suggestions": data.get("productivity_suggestions"),
                "Productivity Details": data.get("productivity_details"),
                "Productive Time": data.get("productive_time"),
                "Productive Place": data.get("productive_place"),
                "Projects": data.get("projects"),
                "Peer Ratings": data.get("peer_ratings"),
                "Peer_Evaluations": data.get("peer_evaluations")
            }
            
            result = self.supabase.table(self.table).insert(wpr_data).execute()
            return result.data[0] if result.data else {}
            
        except Exception as e:
            logger.error(f"Error submitting WPR: {str(e)}")
            raise
            
    def get_wpr(self, name: str, week: int, year: int) -> Optional[Dict[str, Any]]:
        """Get a specific WPR entry."""
        try:
            result = (self.supabase.table(self.table)
                     .select("*")
                     .eq("Name", name)
                     .eq("Week Number", week)
                     .eq("Year", year)
                     .execute())
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Error getting WPR: {str(e)}")
            raise
            
    def update_wpr(self, id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing WPR entry."""
        try:
            # Format data to match table schema
            wpr_data = {
                "Name": data.get("name"),
                "Team": data.get("team"),
                "Week Number": data.get("week_number"),
                "Year": data.get("year"),
                "Completed Tasks": data.get("completed_tasks"),
                "Number of Completed Tasks": len(data.get("completed_tasks", [])),
                "Pending Tasks": data.get("pending_tasks"),
                "Number of Pending Tasks": len(data.get("pending_tasks", [])),
                "Dropped Tasks": data.get("dropped_tasks"),
                "Number of Dropped Tasks": len(data.get("dropped_tasks", [])),
                "Productivity Rating": data.get("productivity_rating"),
                "Productivity Suggestions": data.get("productivity_suggestions"),
                "Productivity Details": data.get("productivity_details"),
                "Productive Time": data.get("productive_time"),
                "Productive Place": data.get("productive_place"),
                "Projects": data.get("projects"),
                "Peer Ratings": data.get("peer_ratings"),
                "Peer_Evaluations": data.get("peer_evaluations")
            }
            
            result = self.supabase.table(self.table).update(wpr_data).eq("id", id).execute()
            return result.data[0] if result.data else {}
            
        except Exception as e:
            logger.error(f"Error updating WPR: {str(e)}")
            raise
            
    def get_team_wprs(self, team: str, week: int, year: int) -> List[Dict[str, Any]]:
        """Get all WPR entries for a team in a specific week."""
        try:
            result = (self.supabase.table(self.table)
                     .select("*")
                     .eq("Team", team)
                     .eq("Week Number", week)
                     .eq("Year", year)
                     .execute())
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error getting team WPRs: {str(e)}")
            raise
            
    def get_user_wprs(self, user_name: str) -> List[Dict[str, Any]]:
        """Get all WPR submissions for a user."""
        try:
            # Remove any team suffix from the name if present
            user_name = user_name.split(" (")[0]
            
            response = self.supabase.table("WPR").select("*").eq("Name", user_name).execute()
            if response.data:
                return sorted(response.data, key=lambda x: (x.get("Year", 0), x.get("Week Number", 0)), reverse=True)
            return []
        except Exception as e:
            logger.error(f"Error retrieving user WPRs: {str(e)}")
            return []

    def get_user_profile(self, user_name: str) -> Optional[Dict[str, Any]]:
        """Get user profile information."""
        try:
            response = self.supabase.table("Users").select("*").eq("email", user_name).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error retrieving user profile: {str(e)}")
            return None

    def update_user_profile(self, user_name: str, profile_data: Dict[str, Any]) -> bool:
        """Update user profile information."""
        try:
            response = self.supabase.table("Users").update(profile_data).eq("email", user_name).execute()
            return bool(response.data)
        except Exception as e:
            logger.error(f"Error updating user profile: {str(e)}")
            return False

    def search_components(self, query: str) -> List[Dict[str, Any]]:
        """Search for components using a text query."""
        try:
            # Use ilike for case-insensitive partial matching
            response = self.supabase.table("Components").select("*").ilike("name", f"%{query}%").execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error searching components: {str(e)}")
            return []
