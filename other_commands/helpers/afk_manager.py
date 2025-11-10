"""
AFK manager for handling away-from-keyboard functionality.
"""

import time
from typing import Dict, Tuple, Optional

class AFKManager:
    def __init__(self):
        # Format: user_id -> (reason, afk_timestamp, command_timestamp)
        self.afk_users: Dict[int, Tuple[str, float, float]] = {}
        
    def set_afk(self, user_id: int, reason: str = "AFK") -> None:
        """Set a user as AFK with the given reason."""
        current_time = time.time()
        self.afk_users[user_id] = (reason, current_time, current_time)
        
    def remove_afk(self, user_id: int) -> Optional[Tuple[str, str]]:
        """Remove a user from AFK status and return AFK info."""
        if user_id not in self.afk_users:
            return None
            
        reason, afk_timestamp, command_timestamp = self.afk_users[user_id]
        
        # Check if this is too soon after the command
        if time.time() - command_timestamp <= 1:
            return None
            
        del self.afk_users[user_id]
        elapsed = time.time() - afk_timestamp
        minutes = int(elapsed / 60)
        hours = int(minutes / 60)
        
        if hours > 0:
            time_text = f"{hours} hours and {minutes % 60} minutes"
        else:
            time_text = f"{minutes} minutes"
            
        return reason, time_text
        
    def is_afk(self, user_id: int) -> bool:
        """Check if a user is currently AFK."""
        return user_id in self.afk_users
        
    def get_afk_info(self, user_id: int) -> Optional[Tuple[str, str]]:
        """Get AFK information for a user."""
        if user_id not in self.afk_users:
            return None
            
        reason, afk_timestamp, _ = self.afk_users[user_id]
        elapsed = time.time() - afk_timestamp
        minutes = int(elapsed / 60)
        hours = int(minutes / 60)
        
        if hours > 0:
            time_text = f"{hours} hours and {minutes % 60} minutes"
        else:
            time_text = f"{minutes} minutes"
            
        return reason, time_text