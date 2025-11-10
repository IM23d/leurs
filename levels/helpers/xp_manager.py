"""
XP management and leveling calculations.
Handles XP gain, level calculations, and anti-spam mechanisms.
"""

import math
import random
import datetime
from typing import Dict, Tuple, Optional
import discord
from .data_manager import LevelsDataManager

class XPManager:
    """Manages XP calculations, leveling, and anti-spam mechanisms."""
    
    def __init__(self):
        self.base_xp = 15  # Base XP per message
        self.xp_per_level = 3500  # XP needed for each level
        self.data_manager = LevelsDataManager()
        
        # Anti-spam tracking
        self.message_count = {}  # Track messages per minute
        self.window_start = {}  # Track when the 60-second window started
        
        # Voice tracking
        self.voice_users = {}  # Track users in voice channels
    
    def calculate_xp_gain(self) -> int:
        """
        Calculate XP gain for a message with randomness.
        
        Returns:
            XP amount to award
        """
        xp_gained = self.base_xp + random.randint(-5, 5)
        return max(5, xp_gained)  # Minimum XP gain
    
    def calculate_level_from_xp(self, xp: int) -> int:
        """
        Calculate level from total XP.
        
        Args:
            xp: Total XP amount
            
        Returns:
            Current level
        """
        return math.floor(xp / self.xp_per_level)
    
    def calculate_level_progress(self, xp: int, level: int) -> Tuple[int, int, int]:
        """
        Calculate progress toward next level.
        
        Args:
            xp: Current XP
            level: Current level
            
        Returns:
            Tuple of (current_level_xp, needed_for_next_level, percentage)
        """
        xp_for_current_level = level * self.xp_per_level
        xp_for_next_level = (level + 1) * self.xp_per_level
        current_level_xp = xp - xp_for_current_level
        needed_for_next_level = xp_for_next_level - xp_for_current_level
        percentage = min(100, max(0, int((current_level_xp / needed_for_next_level) * 100)))
        
        return current_level_xp, needed_for_next_level, percentage
    
    def check_rate_limit(self, user_id: str) -> bool:
        """
        Check if user is within rate limit (max 60 messages per minute).
        
        Args:
            user_id: Discord user ID as string
            
        Returns:
            True if within rate limit, False if rate limited
        """
        current_time = datetime.datetime.now().timestamp()
        
        # Initialize tracking for new users
        if user_id not in self.message_count:
            self.message_count[user_id] = 0
            self.window_start[user_id] = current_time
        
        # Check if 60 seconds have passed, reset if true
        if current_time - self.window_start[user_id] > 60:
            self.message_count[user_id] = 0
            self.window_start[user_id] = current_time
        
        # Increment message count and check if under limit
        self.message_count[user_id] += 1
        return self.message_count[user_id] <= 60
    
    async def add_xp(self, user: discord.User, channel: discord.TextChannel) -> Optional[int]:
        """
        Add XP to a user and check for level up.
        
        Args:
            user: Discord user object
            channel: Channel to send level up message
            
        Returns:
            New level if level up occurred, None otherwise
        """
        user_id = str(user.id)
        
        # Check rate limit
        if not self.check_rate_limit(user_id):
            return None
        
        # Calculate XP gain
        xp_gained = self.calculate_xp_gain()
        
        # Get current user data
        user_data = self.data_manager.get_user_levels(user_id)
        current_level = user_data["level"]
        current_xp = user_data["xp"]
        new_xp = current_xp + xp_gained
        
        # Calculate if user leveled up
        new_level = self.calculate_level_from_xp(new_xp)
        level_up = new_level > current_level
        
        # Update user data
        user_data.update({
            "xp": new_xp,
            "level": new_level,
            "total_messages": user_data["total_messages"] + 1,
            "last_message": datetime.datetime.now().timestamp()
        })
        
        # Save data
        self.data_manager.update_user_levels(user_id, user_data)
        
        # Send level up message if user leveled up
        if level_up and channel:
            await self.send_level_up_message(user, channel, new_level)
            return new_level
        
        return None
    
    async def send_level_up_message(self, user: discord.User, channel: discord.TextChannel, level: int):
        """
        Send a level up message to the channel.
        
        Args:
            user: User who leveled up
            channel: Channel to send message
            level: New level reached
        """
        embed = discord.Embed(
            title="LEVEL UP! 🎉",
            description=f"Congratulations {user.mention}! You've reached **Level {level}**!",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
        await channel.send(embed=embed)
    
    def set_user_level_from_messages(self, user_id: str, messages: int) -> Dict[str, int]:
        """
        Set user level based on message count (admin command).
        
        Args:
            user_id: Discord user ID as string
            messages: Message count to set
            
        Returns:
            Dictionary with new stats (xp, level, messages)
        """
        # Calculate XP based on message count
        xp = messages * self.base_xp
        level = self.calculate_level_from_xp(xp)
        
        # Update user data
        user_data = {
            "xp": xp,
            "level": level,
            "total_messages": messages,
            "last_message": datetime.datetime.now().timestamp()
        }
        
        self.data_manager.update_user_levels(user_id, user_data)
        
        return {"xp": xp, "level": level, "messages": messages}
    
    # Voice tracking methods
    def start_voice_tracking(self, user_id: str, channel_id: int):
        """
        Start tracking voice time for a user.
        
        Args:
            user_id: Discord user ID as string
            channel_id: Voice channel ID
        """
        self.voice_users[user_id] = {
            "start_time": datetime.datetime.now().timestamp(),
            "channel_id": channel_id
        }
    
    def stop_voice_tracking(self, user_id: str) -> float:
        """
        Stop tracking voice time for a user and return session time.
        
        Args:
            user_id: Discord user ID as string
            
        Returns:
            Time spent in voice (seconds)
        """
        if user_id in self.voice_users:
            current_time = datetime.datetime.now().timestamp()
            start_time = self.voice_users[user_id]["start_time"]
            session_time = current_time - start_time
            
            # Add to total voice time
            self.data_manager.add_voice_time(user_id, session_time)
            
            # Remove from tracking
            del self.voice_users[user_id]
            
            return session_time
        return 0.0
    
    def update_voice_tracking(self, user_id: str, new_channel_id: int = None):
        """
        Update voice tracking for channel changes.
        
        Args:
            user_id: Discord user ID as string
            new_channel_id: New channel ID (optional)
        """
        if user_id in self.voice_users:
            if new_channel_id:
                self.voice_users[user_id]["channel_id"] = new_channel_id
            else:
                # Reset start time for new session
                self.voice_users[user_id]["start_time"] = datetime.datetime.now().timestamp()
    
    def save_all_voice_sessions(self):
        """Save all current voice sessions (for periodic updates)."""
        current_time = datetime.datetime.now().timestamp()
        
        for user_id, data in self.voice_users.items():
            start_time = data["start_time"]
            session_time = current_time - start_time
            
            # Add session time to total
            self.data_manager.add_voice_time(user_id, session_time)
            
            # Reset start time for next interval
            self.voice_users[user_id]["start_time"] = current_time