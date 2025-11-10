"""
Data management for levels and voice tracking.
Handles JSON persistence for user statistics.
"""

import json
import os
from typing import Dict, Any

class LevelsDataManager:
    """Manages levels data persistence and retrieval."""
    
    def __init__(self):
        self.levels_file = 'data/levels.json'
        self.voice_file = 'data/voice_levels.json'
        self._ensure_data_directory()
    
    def _ensure_data_directory(self):
        """Ensure the data directory exists."""
        if not os.path.exists('data'):
            os.makedirs('data')
    
    def get_levels_data(self) -> Dict[str, Any]:
        """
        Get all levels data from the JSON file.
        
        Returns:
            Dictionary containing all user level data
        """
        if not os.path.exists(self.levels_file):
            with open(self.levels_file, 'w') as f:
                json.dump({}, f)
            return {}
        
        try:
            with open(self.levels_file, 'r') as f:
                content = f.read().strip()
                if not content:
                    return {}
                return json.loads(content)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def save_levels_data(self, data: Dict[str, Any]):
        """
        Save levels data to the JSON file.
        
        Args:
            data: Dictionary containing user level data
        """
        with open(self.levels_file, 'w') as f:
            json.dump(data, f, indent=4)
    
    def get_voice_data(self) -> Dict[str, Any]:
        """
        Get all voice data from the JSON file.
        
        Returns:
            Dictionary containing all user voice time data
        """
        if not os.path.exists(self.voice_file):
            with open(self.voice_file, 'w') as f:
                json.dump({}, f)
            return {}
        
        try:
            with open(self.voice_file, 'r') as f:
                content = f.read().strip()
                if not content:
                    return {}
                return json.loads(content)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def save_voice_data(self, data: Dict[str, Any]):
        """
        Save voice data to the JSON file.
        
        Args:
            data: Dictionary containing user voice time data
        """
        with open(self.voice_file, 'w') as f:
            json.dump(data, f, indent=4)
    
    def get_user_levels(self, user_id: str) -> Dict[str, Any]:
        """
        Get level data for a specific user.
        
        Args:
            user_id: Discord user ID as string
            
        Returns:
            User's level data or default values
        """
        data = self.get_levels_data()
        return data.get(user_id, {
            "xp": 0,
            "level": 0,
            "total_messages": 0,
            "last_message": 0
        })
    
    def update_user_levels(self, user_id: str, user_data: Dict[str, Any]):
        """
        Update level data for a specific user.
        
        Args:
            user_id: Discord user ID as string
            user_data: User's level data to save
        """
        data = self.get_levels_data()
        data[user_id] = user_data
        self.save_levels_data(data)
    
    def get_user_voice(self, user_id: str) -> Dict[str, Any]:
        """
        Get voice data for a specific user.
        
        Args:
            user_id: Discord user ID as string
            
        Returns:
            User's voice data or default values
        """
        data = self.get_voice_data()
        return data.get(user_id, {"voice_time": 0})
    
    def update_user_voice(self, user_id: str, voice_time: float):
        """
        Update voice time for a specific user.
        
        Args:
            user_id: Discord user ID as string
            voice_time: Total voice time in seconds
        """
        data = self.get_voice_data()
        if user_id not in data:
            data[user_id] = {"voice_time": 0}
        
        data[user_id]["voice_time"] = voice_time
        self.save_voice_data(data)
    
    def add_voice_time(self, user_id: str, time_to_add: float):
        """
        Add voice time to a user's total.
        
        Args:
            user_id: Discord user ID as string
            time_to_add: Time in seconds to add
        """
        data = self.get_voice_data()
        if user_id not in data:
            data[user_id] = {"voice_time": 0}
        
        data[user_id]["voice_time"] = data[user_id].get("voice_time", 0) + time_to_add
        self.save_voice_data(data)
    
    def ensure_user_exists(self, user_id: str):
        """
        Ensure a user exists in the levels database.
        
        Args:
            user_id: Discord user ID as string
        """
        data = self.get_levels_data()
        if user_id not in data:
            data[user_id] = {
                "xp": 0,
                "level": 0,
                "total_messages": 0,
                "last_message": 0
            }
            self.save_levels_data(data)