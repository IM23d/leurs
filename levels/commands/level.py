"""
Level command - Shows user's level statistics and progress.
"""

import discord
from discord.ext import commands
from ..helpers.data_manager import LevelsDataManager
from ..helpers.xp_manager import XPManager
from ..helpers.utils import create_level_embed, create_error_embed

class LevelCommand(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.data_manager = LevelsDataManager()
        self.xp_manager = XPManager()

    @commands.command(aliases=["xp", "lvl", "rank"])
    async def level(self, ctx, member: discord.Member = None):
        """Show level statistics for yourself or another member."""
        try:
            if member is None:
                member = ctx.author
            
            # Get user data
            user_id = str(member.id)
            user_data = self.data_manager.get_user_levels(user_id)
            voice_data = self.data_manager.get_user_voice(user_id)
            
            # Ensure user exists in database
            if user_data["xp"] == 0 and user_data["level"] == 0 and user_data["total_messages"] == 0:
                self.data_manager.ensure_user_exists(user_id)
            
            # Create and send embed
            embed = create_level_embed(member, user_data, voice_data, self.xp_manager)
            embed.set_footer(
                text=f"Requested by {ctx.author.name}", 
                icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = create_error_embed(
                "Error",
                f"An error occurred while fetching level data for {member.mention if member else 'user'}.\nPlease try again later."
            )
            await ctx.send(embed=embed)
            print(f"Error in level command: {str(e)}")

async def setup(client):
    await client.add_cog(LevelCommand(client))