import discord
from discord.ext import commands
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from helpers.data_manager import BlockedTermsDataManager
from helpers.utils import create_error_embed, create_success_embed, parse_duration, validate_punishment_type

class BlockTermCommand:
    """Add blocked term command"""
    
    def __init__(self):
        self.data_manager = BlockedTermsDataManager()
    
    @commands.command(name='blockterm')
    @commands.has_permissions(administrator=True)
    async def block_term(self, ctx, term: str, punishment_type: str, duration: str = None, 
                        advanced_filtering: str = "false", *, custom_text: str = None):
        """Block a term with specified punishment"""
        
        # Validate punishment type
        if not validate_punishment_type(punishment_type):
            embed = create_error_embed("Invalid punishment type. Use: mute, warn, kick, ban")
            await ctx.send(embed=embed)
            return
        
        punishment_type = punishment_type.lower()
        
        # Parse duration if provided
        duration_seconds = None
        if duration and duration.lower() != "none":
            duration_seconds = await parse_duration(duration)
            if duration_seconds is None:
                embed = create_error_embed("Invalid duration format. Use format like: 5s, 10m, 5h, 12d")
                await ctx.send(embed=embed)
                return
        
        # Add the blocked term
        success = await self.data_manager.add_blocked_term(
            term=term,
            guild_id=ctx.guild.id,
            punishment_type=punishment_type,
            duration=duration_seconds,
            duration_str=duration if duration and duration.lower() != "none" else None,
            custom_text=custom_text,
            advanced_filtering=advanced_filtering.lower() == "true",
            added_by=ctx.author
        )
        
        if not success:
            embed = create_error_embed("Failed to add blocked term. Please try again.")
            await ctx.send(embed=embed)
            return
        
        # Create success embed
        embed = create_success_embed("Term Blocked", f"Successfully blocked term: `{term}`")
        embed.add_field(name="Punishment", value=punishment_type.capitalize(), inline=True)
        
        if duration_seconds:
            embed.add_field(name="Duration", value=duration, inline=True)
            
        embed.add_field(name="Advanced Filtering", value=advanced_filtering.capitalize(), inline=True)
        
        if custom_text:
            embed.add_field(
                name="Custom Message", 
                value=custom_text[:100] + "..." if len(custom_text) > 100 else custom_text, 
                inline=False
            )
        
        await ctx.send(embed=embed)

def setup_command(cog):
    """Setup function to add this command to the cog"""
    command_handler = BlockTermCommand()
    cog.add_command(command_handler.block_term)