"""
Voice levels command - Shows voice time leaderboard.
"""

import discord
from discord.ext import commands
from ..helpers.data_manager import LevelsDataManager
from ..helpers.utils import (
    create_leaderboard_embed, 
    process_leaderboard_data, 
    paginate_data, 
    create_error_embed
)
from .leveltop import LevelLeaderboardView

class VoiceLevelsCommand(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.data_manager = LevelsDataManager()

    @commands.command(aliases=["voicetop", "vtop"])
    async def voicelevels(self, ctx, page: int = 1):
        """Show the voice time leaderboard."""
        try:
            # Get all voice data
            users = self.data_manager.get_voice_data()
            
            # Process and sort data
            user_list = process_leaderboard_data(users, ctx.guild, "voice_time")
            
            # Paginate results (10 per page)
            page_data, total_pages, start_idx, end_idx = paginate_data(user_list, page, 10)
            
            # Create embed
            embed = create_leaderboard_embed(
                title="🎤 Voice Time Leaderboard",
                description="Top members ranked by time spent in voice channels.",
                user_list=user_list,
                page=page,
                total_pages=total_pages,
                start_idx=start_idx,
                ctx=ctx,
                client=self.client,
                leaderboard_type="voice"
            )
            
            # Create view with navigation buttons if needed
            if total_pages > 1:
                view = LevelLeaderboardView(self, ctx, page, total_pages, "voice")
                message = await ctx.send(embed=embed, view=view)
                view.message = message
            else:
                await ctx.send(embed=embed)
                
        except Exception as e:
            embed = create_error_embed(
                "Error",
                "An error occurred while fetching the voice leaderboard.\nPlease try again later."
            )
            await ctx.send(embed=embed)
            print(f"Error in voicelevels command: {str(e)}")

async def setup(client):
    await client.add_cog(VoiceLevelsCommand(client))