"""Tests for WPR application."""

import pytest
from datetime import datetime
import pandas as pd
from unittest.mock import MagicMock, patch

from apps.wpr.models.user_profile import UserProfile, UserRole, TeamRole
from apps.wpr.validators import InputValidator
from apps.wpr.utils import DataUtils, AnalyticsUtils

class TestUserProfile:
    """Test user profile functionality."""
    
    def test_profile_creation(self, sample_user_profile):
        """Test user profile creation."""
        assert sample_user_profile.user_id == "test123"
        assert sample_user_profile.email == "test@example.com"
        assert sample_user_profile.role == UserRole.EMPLOYEE
    
    def test_profile_permissions(self, sample_user_profile):
        """Test profile permissions."""
        # Test self-access
        assert sample_user_profile.can_view_wpr(sample_user_profile.user_id)
        assert sample_user_profile.can_edit_wpr(sample_user_profile.user_id)
        
        # Test access to others
        assert not sample_user_profile.can_view_wpr("other_user")
        assert not sample_user_profile.can_edit_wpr("other_user")
        
        # Test manager access
        sample_user_profile.role = UserRole.MANAGER
        assert sample_user_profile.can_view_wpr("other_user")
        assert not sample_user_profile.can_edit_wpr("other_user")
    
    def test_profile_preferences(self, sample_user_profile):
        """Test profile preferences update."""
        new_notification_prefs = {"email_wpr_reminder": False}
        new_ui_prefs = {"dark_mode": True}
        
        sample_user_profile.update_preferences(
            notification_prefs=new_notification_prefs,
            ui_prefs=new_ui_prefs
        )
        
        assert not sample_user_profile.notification_preferences["email_wpr_reminder"]
        assert sample_user_profile.ui_preferences["dark_mode"]

class TestWPRValidation:
    """Test WPR input validation."""
    
    def test_email_validation(self):
        """Test email validation."""
        assert InputValidator.validate_email("test@example.com")
        assert not InputValidator.validate_email("invalid_email")
    
    def test_task_validation(self):
        """Test task validation."""
        tasks = "Task 1\nTask 2\nTask 3"
        validated = InputValidator.validate_tasks(tasks)
        assert len(validated) == 3
        assert all(task.strip() for task in validated)
    
    def test_project_validation(self):
        """Test project validation."""
        projects = "Project A, 75%\nProject B, 30%"
        validated = InputValidator.validate_projects(projects)
        assert len(validated) == 2
        assert validated[0]["completion"] == 75
    
    def test_productivity_rating(self):
        """Test productivity rating validation."""
        assert InputValidator.validate_productivity_rating(4)
        assert not InputValidator.validate_productivity_rating(6)

class TestAnalytics:
    """Test analytics functionality."""
    
    def test_week_stats_calculation(self, sample_wpr_data):
        """Test weekly statistics calculation."""
        df = pd.DataFrame([sample_wpr_data])
        stats = AnalyticsUtils.calculate_week_stats(df)
        
        assert stats["total_completed"] == 2
        assert stats["total_pending"] == 1
        assert stats["total_dropped"] == 0
        assert stats["avg_productivity"] == 4.0
    
    def test_performance_metrics(self, sample_wpr_data):
        """Test performance metrics calculation."""
        # Add project data to match expected progress
        sample_wpr_data['Projects'] = [
            {'name': 'Project 1', 'completion': 75},
            {'name': 'Project 2', 'completion': 75}
        ]
        
        current = pd.Series(sample_wpr_data)
        metrics = AnalyticsUtils.calculate_performance_metrics(current)
        
        assert metrics["productivity_score"] == 4.0
        assert round(metrics["task_completion_rate"], 2) == 66.67
        assert round(metrics["project_progress"], 2) == 75.00
        assert round(metrics["collaboration_score"], 2) == 3.50

class TestDataUtils:
    """Test data utility functions."""
    
    def test_safe_get_nested(self):
        """Test nested dictionary access."""
        data = {"a": {"b": {"c": 1}}}
        assert DataUtils.safe_get_nested(data, ["a", "b", "c"]) == 1
        assert DataUtils.safe_get_nested(data, ["x", "y"]) is None
    
    def test_timestamp_formatting(self):
        """Test timestamp formatting."""
        now = datetime.now()
        formatted = DataUtils.format_timestamp(now)
        assert isinstance(formatted, str)
        assert len(formatted) > 0

@pytest.mark.asyncio
class TestProfileManager:
    """Test profile manager functionality."""
    
    async def test_profile_creation(self, profile_manager, sample_user_profile):
        """Test creating a new profile."""
        profile = await profile_manager.create_profile(
            user_id=sample_user_profile.user_id,
            email=sample_user_profile.email,
            full_name=sample_user_profile.full_name
        )
        assert profile is not None
    
    async def test_profile_update(self, profile_manager, sample_user_profile):
        """Test updating a profile."""
        updated = await profile_manager.update_profile(sample_user_profile)
        assert updated is not None
    
    async def test_team_management(self, profile_manager, sample_user_profile):
        """Test team management functions."""
        # Set up mock data
        sample_user_profile.team_id = "team123"
        profile_manager.supabase.table("profiles")._data = sample_user_profile.to_dict()
        
        # Test get_team_profiles
        team_profiles = await profile_manager.get_team_profiles(sample_user_profile.team_id)
        assert isinstance(team_profiles, list)
        assert len(team_profiles) == 1
        
        # Test role update
        updated_data = sample_user_profile.to_dict()
        updated_data['team_role'] = TeamRole.LEAD.value
        updated_profile = UserProfile(**updated_data)
        profile_manager.supabase.table("profiles")._data = updated_profile.to_dict()
        
        updated = await profile_manager.update_team_role(
            sample_user_profile.user_id,
            sample_user_profile.team_id,
            TeamRole.LEAD
        )
        assert updated is not None
        assert updated.team_role == TeamRole.LEAD
