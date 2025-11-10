import json
import os
from pathlib import Path
from datetime import datetime

class DataManager:
    """Helper class for managing JSON data files"""
    
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
    
    def load_json(self, filename):
        """Load JSON data from file"""
        file_path = self.data_dir / f"{filename}.json"
        try:
            if file_path.exists():
                with open(file_path, 'r') as f:
                    return json.load(f)
            else:
                # Create empty file
                with open(file_path, 'w') as f:
                    json.dump({}, f)
                return {}
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return {}
    
    def save_json(self, filename, data):
        """Save JSON data to file"""
        file_path = self.data_dir / f"{filename}.json"
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving {filename}: {e}")
            return False
    
    def get_guild_data(self, filename, guild_id, user_id=None):
        """Get data for a specific guild and optionally user"""
        data = self.load_json(filename)
        guild_str = str(guild_id)
        
        if guild_str not in data:
            data[guild_str] = {}
            
        if user_id:
            user_str = str(user_id)
            if user_str not in data[guild_str]:
                data[guild_str][user_str] = []
            return data, data[guild_str][user_str]
        
        return data, data[guild_str]
    
    def add_user_action(self, guild_id, user_id, action_type, reason=None, duration=None):
        """Add action to user history"""
        try:
            data, user_data = self.get_guild_data("user_actions", guild_id, user_id)
            
            action = {
                "action": action_type,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if reason:
                action["reason"] = reason
            if duration:
                action["duration"] = duration
                
            user_data.append(action)
            return self.save_json("user_actions", data)
        except Exception as e:
            print(f"Error adding user action: {e}")
            return False
    
    def add_warning(self, guild_id, user_id, reason):
        """Add warning to user history"""
        try:
            data, user_data = self.get_guild_data("warnings", guild_id, user_id)
            
            user_data.append({
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return self.save_json("warnings", data)
        except Exception as e:
            print(f"Error adding warning: {e}")
            return False
    
    def add_nickname_change(self, guild_id, user_id, old_nick, new_nick):
        """Add nickname change to history"""
        try:
            data, user_data = self.get_guild_data("nickname_history", guild_id, user_id)
            
            user_data.append({
                "old_nick": old_nick,
                "new_nick": new_nick,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return self.save_json("nickname_history", data)
        except Exception as e:
            print(f"Error adding nickname change: {e}")
            return False
    
    def get_previous_nickname(self, guild_id, user_id):
        """Get previous nickname from history"""
        try:
            data, user_data = self.get_guild_data("nickname_history", guild_id, user_id)
            
            if user_data:
                return user_data[-1]["old_nick"]
            return None
        except Exception as e:
            print(f"Error getting previous nickname: {e}")
            return None