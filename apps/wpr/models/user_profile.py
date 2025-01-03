"""User profile model for WPR application."""

from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

class UserRole(Enum):
    """User role enumeration."""
    EMPLOYEE = "employee"
    MANAGER = "manager"
    ADMIN = "admin"

class TeamRole(Enum):
    """Team role enumeration."""
    MEMBER = "member"
    LEAD = "lead"

@dataclass
class UserProfile:
    """User profile data model."""
    
    # Core user information
    user_id: str
    email: str
    full_name: str
    role: UserRole = UserRole.EMPLOYEE
    
    # Team information
    team_id: Optional[str] = None
    team_name: Optional[str] = None
    team_role: TeamRole = TeamRole.MEMBER
    
    # Profile details
    department: Optional[str] = None
    position: Optional[str] = None
    manager_id: Optional[str] = None
    direct_reports: List[str] = field(default_factory=list)
    
    # Preferences
    notification_preferences: Dict[str, bool] = field(default_factory=lambda: {
        "email_wpr_reminder": True,
        "email_wpr_submitted": True,
        "email_hr_analysis": True,
        "email_team_updates": True
    })
    ui_preferences: Dict[str, Any] = field(default_factory=lambda: {
        "default_view": "current_week",
        "charts_expanded": True,
        "dark_mode": False,
        "compact_view": False
    })
    
    # WPR specific settings
    wpr_settings: Dict[str, Any] = field(default_factory=lambda: {
        "reminder_day": "Friday",
        "reminder_time": "10:00",
        "auto_share_with_manager": True,
        "default_project_view": "list"  # or "kanban"
    })
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary."""
        return {
            "user_id": self.user_id,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role.value if isinstance(self.role, UserRole) else self.role,
            "team_id": self.team_id,
            "team_name": self.team_name,
            "team_role": self.team_role.value if isinstance(self.team_role, TeamRole) else self.team_role,
            "department": self.department,
            "position": self.position,
            "manager_id": self.manager_id,
            "direct_reports": self.direct_reports,
            "notification_preferences": self.notification_preferences,
            "ui_preferences": self.ui_preferences,
            "wpr_settings": self.wpr_settings,
            "created_at": self.created_at if isinstance(self.created_at, str) else self.created_at.isoformat(),
            "updated_at": self.updated_at if isinstance(self.updated_at, str) else self.updated_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login and not isinstance(self.last_login, str) else self.last_login
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserProfile':
        """Create profile from dictionary."""
        # Convert string roles to enums
        data['role'] = UserRole(data.get('role', UserRole.EMPLOYEE.value))
        data['team_role'] = TeamRole(data.get('team_role', TeamRole.MEMBER.value))
        
        # Convert ISO strings to datetime
        for field in ['created_at', 'updated_at']:
            if field in data and isinstance(data[field], str):
                data[field] = datetime.fromisoformat(data[field])
        
        if 'last_login' in data and data['last_login']:
            data['last_login'] = datetime.fromisoformat(data['last_login'])
        
        return cls(**data)
    
    def update_login(self) -> None:
        """Update last login time."""
        self.last_login = datetime.now()
        self.updated_at = datetime.now()
    
    def update_preferences(self, 
                         notification_prefs: Optional[Dict[str, bool]] = None,
                         ui_prefs: Optional[Dict[str, Any]] = None,
                         wpr_settings: Optional[Dict[str, Any]] = None) -> None:
        """Update user preferences."""
        if notification_prefs:
            self.notification_preferences.update(notification_prefs)
        if ui_prefs:
            self.ui_preferences.update(ui_prefs)
        if wpr_settings:
            self.wpr_settings.update(wpr_settings)
        self.updated_at = datetime.now()
    
    def get_team_members(self) -> List[str]:
        """Get list of team member IDs."""
        return ([self.manager_id] if self.manager_id else []) + self.direct_reports
    
    def can_view_wpr(self, wpr_user_id: str) -> bool:
        """Check if user can view another user's WPR."""
        return (
            self.role in [UserRole.ADMIN, UserRole.MANAGER] or
            wpr_user_id == self.user_id or
            (self.team_role == TeamRole.LEAD and wpr_user_id in self.direct_reports)
        )
    
    def can_edit_wpr(self, wpr_user_id: str) -> bool:
        """Check if user can edit another user's WPR."""
        return wpr_user_id == self.user_id
    
    def can_manage_team(self) -> bool:
        """Check if user can manage team settings."""
        return self.role == UserRole.MANAGER or self.team_role == TeamRole.LEAD
