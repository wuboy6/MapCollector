from dataclasses import dataclass
from typing import Optional, Dict


@dataclass
class UserProfile:
    user_id: str
    email: str
    permissions: list
    current_map: Optional[str] = None


class UserSession:
    def __init__(self):
        self.profile: Optional[UserProfile] = None

    def start(self, user_data: Dict):
        """初始化用户会话"""
        self.profile = UserProfile(
            user_id=user_data['id'],
            email=user_data['email'],
            permissions=user_data['permissions']
        )

    @property
    def is_authenticated(self) -> bool:
        return self.profile is not None

    def has_permission(self, perm: str) -> bool:
        return perm in self.profile.permissions if self.profile else False