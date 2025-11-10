import discord
from discord.ext import commands
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from helpers.data_manager import BlockedTermsDataManager
from helpers.utils import create_error_embed, create_info_embed

class ListTermsCommand:
    """List blocked terms command"""
    
    def __init__(self):
        self.data_manager = BlockedTermsDataManager()
    
    @commands.command(name='blockedterms')
    @commands.has_permissions(administrator=True)
    async def list_blocked_terms(self, ctx):
        """List all blocked terms for the server"""
        
        # Get terms for this guild
        guild_terms = await self.data_manager.get_guild_terms(ctx.guild.id)
        
        if not guild_terms:
            embed = create_error_embed("No blocked terms configured for this server.")
            await ctx.send(embed=embed)
            return
        
        embed = create_info_embed(
            "Blocked Terms",
            f"Current blocked terms for {ctx.guild.name}:"
        )
        
        # Show up to 10 terms per page
        terms_to_show = list(guild_terms.items())[:10]
        
        for term, data in terms_to_show:
            punishment_info = data['punishment_type'].capitalize()
            if data.get('duration_str'):
                punishment_info += f" ({data['duration_str']})"
            
            filtering_type = "Advanced" if data.get('advanced_filtering', False) else "Basic"
            
            embed.add_field(
                name=f"`{term}`",
                value=f"**Punishment:** {punishment_info}\n**Filtering:** {filtering_type}",
                inline=True
            )
        
        if len(guild_terms) > 10:
            embed.set_footer(text=f"Showing 10 of {len(guild_terms)} blocked terms")
        
        await ctx.send(embed=embed)

def setup_command(cog):
    """Setup function to add this command to the cog"""
    command_handler = ListTermsCommand()
    cog.add_command(command_handler.list_blocked_terms)