"""
LastFM login command - Links a user's Discord account to their LastFM profile.
"""

import discord
from discord.ext import commands
from ..helpers.data_manager import LastFMDataManager
from ..helpers.utils import create_success_embed

class LoginCommand(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.data_manager = LastFMDataManager()

    @commands.command()
    async def login(self, ctx, lastfm_username):
        """Link your LastFM account to the bot."""
        user_id = ctx.author.id
        
        # Store the link
        self.data_manager.link_user(user_id, lastfm_username)
        
        # Create success embed
        embed = create_success_embed(
            "LastFM Account Linked",
            "Your LastFM account has been linked to Leurs!"
        )
        embed.set_footer(
            text=f"Requested by {ctx.author.name}", 
            icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
        )
        
        await ctx.send(embed=embed)

async def setup(client):
    client.add_cog(LoginCommand(client))