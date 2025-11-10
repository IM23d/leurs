import json
import os
from pathlib import Path
from datetime import datetime, date

class BirthdayDataManager:
    """Helper class for managing birthday data"""
    
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.birthdays_file = self.data_dir / "birthdays.json"
        self.birthdays = {}
        self.load_birthdays()
    
    def load_birthdays(self):
        """Load birthday data from file"""
        try:
            if self.birthdays_file.exists():
                with open(self.birthdays_file, "r") as f:
                    self.birthdays = json.load(f)
            else:
                self.birthdays = {}
                self.save_birthdays()
        except Exception as e:
            print(f"Error loading birthdays: {e}")
            self.birthdays = {}
    
    def save_birthdays(self):
        """Save birthday data to file"""
        try:
            with open(self.birthdays_file, "w") as f:
                json.dump(self.birthdays, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving birthdays: {e}")
            return False
    
    def set_birthday(self, user_id, birthday_str):
        """Set birthday for a user"""
        try:
            self.birthdays[str(user_id)] = birthday_str
            return self.save_birthdays()
        except Exception as e:
            print(f"Error setting birthday: {e}")
            return False
    
    def get_birthday(self, user_id):
        """Get birthday for a user"""
        return self.birthdays.get(str(user_id))
    
    def get_all_birthdays(self):
        """Get all birthdays"""
        return self.birthdays
    
    def remove_birthday(self, user_id):
        """Remove birthday for a user"""
        try:
            if str(user_id) in self.birthdays:
                del self.birthdays[str(user_id)]
                return self.save_birthdays()
            return True
        except Exception as e:
            print(f"Error removing birthday: {e}")
            return False