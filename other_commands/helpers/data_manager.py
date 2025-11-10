"""
Data manager for other functionality.
Handles general data operations and utilities.
"""

import json
import os
from typing import Dict, Any

class OtherDataManager:
    def __init__(self):
        self.data_dir = 'data'
        self.ensure_data_dir()
        
        # Data files
        self.prefix_file = os.path.join(self.data_dir, 'prefix.json')
        
    def ensure_data_dir(self):
        """Ensure the data directory exists."""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
    def load_prefix_config(self) -> Dict[str, str]:
        """Load prefix configuration from file."""
        try:
            with open(self.prefix_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            with open(self.prefix_file, 'w') as f:
                json.dump({}, f)
            return {}
            
    def save_prefix_config(self, config: Dict[str, str]) -> bool:
        """Save prefix configuration to file."""
        try:
            with open(self.prefix_file, 'w') as f:
                json.dump(config, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving prefix config: {e}")
            return False
            
    def get_guild_prefix(self, guild_id: int, default: str = '-') -> str:
        """Get the prefix for a specific guild."""
        config = self.load_prefix_config()
        return config.get(str(guild_id), default)
        
    def set_guild_prefix(self, guild_id: int, prefix: str) -> bool:
        """Set the prefix for a specific guild."""
        config = self.load_prefix_config()
        config[str(guild_id)] = prefix
        return self.save_prefix_config(config)