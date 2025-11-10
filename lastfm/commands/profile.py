"""
LastFM profile command - Shows user's LastFM profile with statistics.
"""

import discord
from discord.ext import commands
from ..helpers.data_manager import LastFMDataManager
from ..helpers.api_client import LastFMAPIClient
from ..helpers.utils import create_not_linked_embed, format_user_profile_embed, create_error_embed

class ProfileCommand(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.data_manager = LastFMDataManager()
        self.api_client = LastFMAPIClient()

    @commands.command(name="lastfm", aliases=["lf", "profile", "me", "p"])
    async def lastfm_stats(self, ctx):
        """Show your LastFM profile statistics."""
        user_id = ctx.author.id
        lastfm_username = self.data_manager.get_lastfm_username(user_id)
        
        # Check if user has linked their account
        if not lastfm_username:
            embed = create_not_linked_embed(ctx.author)
            await ctx.send(embed=embed)
            return

        try:
            # Get user info from LastFM API
            user_info = self.api_client.get_user_info(lastfm_username)
            
            # Format into embed
            embed = format_user_profile_embed(ctx.author, user_info)
            
            # Get additional track count if possible
            try:
                recent_tracks = self.api_client.get_recent_tracks(lastfm_username, limit=1)
                if recent_tracks and '@attr' in recent_tracks:
                    total_tracks = recent_tracks['@attr']['total']
                    embed.description += f"**Total Tracks:** {total_tracks}"
            except:
                pass  # Don't fail if we can't get track count
            
            await ctx.send(embed=embed)

        except Exception as e:
            embed = create_error_embed(
                "Error",
                f"Failed to fetch data from Last.fm API: {str(e)}"
            )
            await ctx.send(embed=embed)

async def setup(client):
    client.add_cog(ProfileCommand(client))