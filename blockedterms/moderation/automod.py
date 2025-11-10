import discord
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from helpers.data_manager import BlockedTermsDataManager
from helpers.utils import check_blocked_term
from helpers.punishment_manager import PunishmentManager

class AutoModerationHandler:
    """Handles automatic moderation for blocked terms"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_manager = BlockedTermsDataManager()
        self.punishment_manager = PunishmentManager(bot, self.data_manager)
    
    async def handle_message(self, message):
        """Handle incoming message for blocked term detection"""
        # Skip bots
        if message.author.bot:
            return
        
        # Skip if not in guild
        if not message.guild:
            return
        
        # Skip if user is administrator
        if message.author.guild_permissions.administrator:
            return
        
        # Get blocked terms for this guild
        guild_terms = await self.data_manager.get_guild_terms(message.guild.id)
        
        if not guild_terms:
            return
        
        # Check for blocked terms
        detected_term, term_data = await check_blocked_term(message.content, guild_terms)
        
        if detected_term:
            # Delete the message
            try:
                await message.delete()
            except (discord.NotFound, discord.Forbidden):
                pass
            
            # Apply punishment
            await self.punishment_manager.apply_punishment(message, detected_term, term_data)

def setup_handler(cog, bot):
    """Setup function to create the auto-moderation handler"""
    handler = AutoModerationHandler(bot)
    return handler