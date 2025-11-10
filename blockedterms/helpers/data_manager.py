import json
import os
from pathlib import Path
from datetime import datetime

class BlockedTermsDataManager:
    """Helper class for managing blocked terms data"""
    
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.blocked_terms_file = self.data_dir / "blockedterms.json"
        self.punishments_file = self.data_dir / "punishments.json"
        
        # Ensure files exist
        self.ensure_files_exist()
    
    def ensure_files_exist(self):
        """Ensure data files exist"""
        if not self.blocked_terms_file.exists():
            with open(self.blocked_terms_file, 'w') as f:
                json.dump({}, f)
        
        if not self.punishments_file.exists():
            with open(self.punishments_file, 'w') as f:
                json.dump({}, f)
    
    async def load_blocked_terms(self):
        """Load blocked terms from file"""
        try:
            with open(self.blocked_terms_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    async def save_blocked_terms(self, terms):
        """Save blocked terms to file"""
        try:
            with open(self.blocked_terms_file, 'w') as f:
                json.dump(terms, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving blocked terms: {e}")
            return False
    
    async def load_punishments(self):
        """Load punishments from file"""
        try:
            with open(self.punishments_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    async def save_punishments(self, punishments):
        """Save punishments to file"""
        try:
            with open(self.punishments_file, 'w') as f:
                json.dump(punishments, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving punishments: {e}")
            return False
    
    async def add_punishment_record(self, user_id, guild_id, punishment_type, reason, duration=None, moderator=None):
        """Add a punishment record for a user"""
        try:
            punishments = await self.load_punishments()
            user_key = f"{user_id}_{guild_id}"
            
            if user_key not in punishments:
                punishments[user_key] = []
            
            record = {
                'type': punishment_type,
                'reason': reason,
                'timestamp': datetime.now().isoformat(),
                'moderator': str(moderator) if moderator else 'Automod',
                'duration': duration
            }
            
            punishments[user_key].append(record)
            return await self.save_punishments(punishments)
        except Exception as e:
            print(f"Error adding punishment record: {e}")
            return False
    
    async def get_guild_terms(self, guild_id):
        """Get blocked terms for a specific guild"""
        try:
            blocked_terms = await self.load_blocked_terms()
            return {term: data for term, data in blocked_terms.items() 
                   if data.get('guild_id') == guild_id}
        except Exception as e:
            print(f"Error getting guild terms: {e}")
            return {}
    
    async def add_blocked_term(self, term, guild_id, punishment_type, duration=None, 
                              duration_str=None, custom_text=None, advanced_filtering=False, added_by=None):
        """Add a new blocked term"""
        try:
            blocked_terms = await self.load_blocked_terms()
            
            blocked_terms[term] = {
                'punishment_type': punishment_type,
                'duration': duration,
                'duration_str': duration_str,
                'custom_text': custom_text,
                'advanced_filtering': advanced_filtering,
                'added_by': str(added_by) if added_by else 'Unknown',
                'added_at': datetime.now().isoformat(),
                'guild_id': guild_id
            }
            
            return await self.save_blocked_terms(blocked_terms)
        except Exception as e:
            print(f"Error adding blocked term: {e}")
            return False
    
    async def remove_blocked_term(self, term):
        """Remove a blocked term"""
        try:
            blocked_terms = await self.load_blocked_terms()
            
            if term not in blocked_terms:
                return False
            
            del blocked_terms[term]
            return await self.save_blocked_terms(blocked_terms)
        except Exception as e:
            print(f"Error removing blocked term: {e}")
            return False