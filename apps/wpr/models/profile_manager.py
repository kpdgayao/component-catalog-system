"""Profile manager for WPR application."""

from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
from supabase import Client
from .user_profile import UserProfile, UserRole, TeamRole

class ProfileManager:
    """Manager for user profiles."""
    
    def __init__(self, supabase: Client):
        """Initialize profile manager."""
        self.supabase = supabase
        self.table = "user_profiles"
    
    async def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile by ID."""
        try:
            if hasattr(self.supabase, 'get_user_profile'):
                # For testing with mock client
                data = self.supabase.get_user_profile(user_id)
                if not data:
                    return None
                return UserProfile(**data)
            else:
                # For real Supabase client
                response = await self.supabase.table(self.table).select("*").eq("user_id", user_id).single()
                if response and response.data:
                    return UserProfile.from_dict(response.data)
                return None
            
        except Exception as e:
            logging.error(f"Error fetching user profile: {str(e)}")
            return None
    
    async def create_profile(self, user_id: str, email: str, full_name: str) -> Optional[UserProfile]:
        """Create a new user profile."""
        try:
            data = {
                'user_id': user_id,
                'email': email,
                'full_name': full_name,
                'role': UserRole.EMPLOYEE.value,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            result = await self.supabase.table(self.table).insert(data).execute()
            if result and result.data:
                return UserProfile(**result.data[0])
            return None
            
        except Exception as e:
            logging.error(f"Error creating user profile: {str(e)}")
            return None

    async def update_profile(self, profile: UserProfile) -> Optional[UserProfile]:
        """Update an existing user profile."""
        try:
            data = profile.to_dict()
            data['updated_at'] = datetime.now().isoformat()
            
            result = await self.supabase.table(self.table)\
                .update(data)\
                .eq('user_id', profile.user_id)\
                .execute()
                
            if result and result.data:
                return UserProfile(**result.data[0])
            return None
            
        except Exception as e:
            logging.error(f"Error updating user profile: {str(e)}")
            return None
    
    async def get_team_profiles(self, team_id: str) -> List[UserProfile]:
        """Get all profiles in a team."""
        try:
            result = await self.supabase.table(self.table)\
                .select('*')\
                .eq('team_id', team_id)\
                .execute()
                
            if result and result.data:
                return [UserProfile(**data) for data in result.data]
            return []
            
        except Exception as e:
            logging.error(f"Error fetching team profiles: {str(e)}")
            return []
    
    async def get_manager_profiles(self, manager_id: str) -> List[UserProfile]:
        """Get all profiles for direct reports."""
        try:
            response = await self.supabase.table(self.table)\
                .select("*")\
                .eq("manager_id", manager_id)\
                .execute()
            
            if response and response.data:
                return [UserProfile.from_dict(data) for data in response.data]
            return []
            
        except Exception as e:
            logging.error(f"Error fetching direct report profiles: {str(e)}")
            return []
    
    async def update_team_role(self, user_id: str, team_id: str, new_role: TeamRole) -> Optional[UserProfile]:
        """Update a user's team role."""
        try:
            # Get current profile
            profile = await self.get_profile(user_id)
            if not profile:
                return None

            # Update role
            profile.team_role = new_role
            profile.team_id = team_id

            # Save to database
            result = await self.supabase.table(self.table).update(profile.to_dict()).eq("user_id", user_id).execute()
            if not result.data:
                return None

            # Return updated profile
            return profile

        except Exception as e:
            logging.error(f"Error updating team role: {e}")
            return None
    
    async def update_preferences(self,
                               user_id: str,
                               notification_prefs: Optional[Dict[str, bool]] = None,
                               ui_prefs: Optional[Dict[str, Any]] = None,
                               wpr_settings: Optional[Dict[str, Any]] = None) -> Optional[UserProfile]:
        """Update user preferences."""
        try:
            profile = await self.get_profile(user_id)
            if not profile:
                return None
            
            profile.update_preferences(notification_prefs, ui_prefs, wpr_settings)
            return await self.update_profile(profile)
            
        except Exception as e:
            logging.error(f"Error updating preferences: {str(e)}")
            return None
    
    async def record_login(self, user_id: str) -> None:
        """Record user login."""
        try:
            profile = await self.get_profile(user_id)
            if profile:
                profile.update_login()
                await self.update_profile(profile)
                
        except Exception as e:
            logging.error(f"Error recording login: {str(e)}")
    
    async def get_active_users(self, days: int = 30) -> List[UserProfile]:
        """Get active users within specified days."""
        try:
            cutoff_date = (datetime.now() - datetime.timedelta(days=days)).isoformat()
            
            response = await self.supabase.table(self.table)\
                .select("*")\
                .gte("last_login", cutoff_date)\
                .execute()
            
            if response and response.data:
                return [UserProfile.from_dict(data) for data in response.data]
            return []
            
        except Exception as e:
            logging.error(f"Error fetching active users: {str(e)}")
            return []

    async def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get a user profile by ID."""
        try:
            if hasattr(self.supabase, 'get_user_profile'):
                # For testing with mock client
                data = self.supabase.get_user_profile(user_id)
                if not data:
                    return None
                return UserProfile(**data)
            else:
                # For real Supabase client
                result = await self.supabase.table("profiles").select("*").eq("user_id", user_id).single().execute()
                if not result.data:
                    return None
                return UserProfile(**result.data)
        except Exception as e:
            logging.error(f"Error fetching user profile: {e}")
            return None
