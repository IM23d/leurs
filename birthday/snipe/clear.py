import discord
from discord.ext import commands
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from helpers.snipe_manager import SnipeManager

class ClearSnipeCommand:
    """Clear snipe data command"""
    
    def __init__(self, snipe_manager: SnipeManager):
        self.snipe_manager = snipe_manager
    
    @commands.command(name='cs')
    async def clear_snipe(self, ctx):
        """Clear all deleted message data for this channel"""
        channel_id = ctx.channel.id
        self.snipe_manager.clear_channel_messages(channel_id)
        await ctx.message.add_reaction('✅')

def setup_command(cog, snipe_manager):
    """Setup function to add this command to the cog"""
    command_handler = ClearSnipeCommand(snipe_manager)
    cog.add_command(command_handler.clear_snipe)