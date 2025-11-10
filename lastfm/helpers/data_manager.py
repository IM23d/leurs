"""
Data management utilities for the LastFM system.
Handles user account linking and data persistence.
"""

import json
import os
from typing import Optional, Dict

class LastFMDataManager:
    """
    Data manager for LastFM user account linking.
    Manages user LastFM username storage and retrieval.
    """
    
    def __init__(self, data_file='data/lastfm.json'):
        self.data_file = data_file
        self._ensure_data_directory()
    
    def _ensure_data_directory(self):
        """Ensure data directory exists."""
        if not os.path.exists('data'):
            os.makedirs('data')
    
    def update_user_data(self, user_id: int, lastfm_username: str) -> bool:
        """
        Link a Discord user to their LastFM username.
        
        Args:
            user_id: Discord user ID
            lastfm_username: LastFM username to link
            
        Returns:
            True if successful, False otherwise
        """
        try:
            user_data = self._load_user_data()
            user_data[str(user_id)] = lastfm_username
            
            with open(self.data_file, 'w') as f:
                json.dump(user_data, f)
            return True
        except Exception as e:
            print(f"Error updating user data: {e}")
            return False
    
    def get_lastfm_username(self, user_id: int) -> Optional[str]:
        """
        Get LastFM username for a Discord user.
        
        Args:
            user_id: Discord user ID
            
        Returns:
            LastFM username if linked, None otherwise
        """
        user_data = self._load_user_data()
        return user_data.get(str(user_id))
    
    def remove_user_data(self, user_id: int) -> bool:
        """
        Unlink a Discord user from their LastFM account.
        
        Args:
            user_id: Discord user ID
            
        Returns:
            True if successful, False if user wasn't linked
        """
        try:
            user_data = self._load_user_data()
            
            if str(user_id) not in user_data:
                return False
            
            del user_data[str(user_id)]
            
            with open(self.data_file, 'w') as f:
                json.dump(user_data, f)
            return True
        except Exception as e:
            print(f"Error removing user data: {e}")
            return False
    
    def get_all_linked_users(self) -> Dict[str, str]:
        """
        Get all linked Discord users and their LastFM usernames.
        
        Returns:
            Dictionary mapping Discord user ID to LastFM username
        """
        return self._load_user_data()
    
    def is_user_linked(self, user_id: int) -> bool:
        """
        Check if a Discord user has linked their LastFM account.
        
        Args:
            user_id: Discord user ID
            
        Returns:
            True if linked, False otherwise
        """
        return self.get_lastfm_username(user_id) is not None
    
    def _load_user_data(self) -> Dict[str, str]:
        """
        Load user data from JSON file.
        
        Returns:
            Dictionary of user data
        """
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}