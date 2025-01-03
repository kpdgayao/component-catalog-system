"""Test configuration and fixtures."""

import pytest
from datetime import datetime
from typing import Dict, Any
import pandas as pd
from supabase import Client, create_client
import os
from unittest.mock import MagicMock

from apps.wpr.models.user_profile import UserProfile, UserRole, TeamRole
from apps.wpr.config import WPRConfig
from apps.wpr.database import WPRDatabase
from apps.wpr.models.profile_manager import ProfileManager

@pytest.fixture
def mock_supabase():
    """Create a mock Supabase client for testing."""
    class MockSupabase:
        def __init__(self):
            self._table = None
            self._query = None
            self._data = None
            
        def table(self, name):
            self._table = name
            return self
            
        def select(self, *args):
            self._query = "select"
            return self
            
        def insert(self, data):
            self._data = data
            return self
            
        def update(self, data):
            self._data = data
            return self
            
        def eq(self, field, value):
            return self
            
        def ilike(self, field, pattern):
            return self
            
        def single(self):
            return self
            
        async def execute(self):
            class Result:
                def __init__(self, data):
                    self.data = data
            return Result([self._data] if self._data else [])

        def get_user_profile(self, user_id):
            return self._data
            
    return MockSupabase()

@pytest.fixture
def wpr_config():
    """Create a test WPR configuration."""
    return WPRConfig()

@pytest.fixture
def sample_user_profile():
    """Create a sample user profile."""
    return UserProfile(
        user_id="test123",
        email="test@example.com",
        full_name="Test User",
        role=UserRole.EMPLOYEE,
        team_id="team1",
        team_name="Engineering",
        team_role=TeamRole.MEMBER
    )

@pytest.fixture
def sample_wpr_data():
    """Create sample WPR data."""
    return {
        "Name": "Test User",
        "Team": "Engineering",
        "Week Number": 1,
        "Year": 2025,
        "Completed Tasks": ["Task 1", "Task 2"],
        "Pending Tasks": ["Task 3"],
        "Dropped Tasks": [],
        "Projects": [
            {"name": "Project A", "completion": 75},
            {"name": "Project B", "completion": 30}
        ],
        "Productivity Rating": 4,
        "Productivity Suggestions": ["Better task prioritization"],
        "Productivity Details": "Good progress this week",
        "Productive Time": "Morning",
        "Productive Place": "Office",
        "Peer_Evaluations": {"user1": 4, "user2": 3}
    }

@pytest.fixture
def sample_component_data():
    """Create sample component catalog data."""
    return {
        "name": "TestButton",
        "category": "Buttons",
        "description": "A test button component",
        "props": {
            "label": "string",
            "onClick": "function",
            "disabled": "boolean"
        },
        "examples": [
            {
                "title": "Basic Usage",
                "code": "<TestButton label='Click Me' />"
            }
        ],
        "metadata": {
            "author": "Test Author",
            "created_at": datetime.now().isoformat(),
            "version": "1.0.0"
        }
    }

@pytest.fixture
def mock_db(mock_supabase):
    """Create a mock database instance."""
    return WPRDatabase(mock_supabase)

@pytest.fixture
def profile_manager(mock_supabase):
    """Create a profile manager instance."""
    return ProfileManager(mock_supabase)

@pytest.fixture
def mock_ai_response():
    """Create a mock AI analysis response."""
    return {
        "analysis_text": "Test analysis",
        "metrics": {
            "productivity_score": 3.5,
            "task_completion_rate": 80,
            "collaboration_score": 4.0
        },
        "recommendations": [
            "Focus on task prioritization",
            "Schedule more focused work time"
        ],
        "wellness_indicators": {
            "work_life_balance": "Good",
            "workload_assessment": "Moderate",
            "engagement_level": "High"
        }
    }
