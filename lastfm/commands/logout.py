"""
LastFM logout command - Unlinks a user's Discord account from their LastFM profile.
"""

import discord
from discord.ext import commands
from ..helpers.data_manager import LastFMDataManager
from ..helpers.utils import create_success_embed, create_error_embed

class LogoutCommand(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.data_manager = LastFMDataManager()

    @commands.command()
    async def logout(self, ctx):
        """Unlink your LastFM account from the bot."""
        user_id = ctx.author.id
        
        try:
            # Check if user has an account linked
            if not self.data_manager.get_lastfm_username(user_id):
                embed = create_error_embed(
                    "Not Logged In",
                    "You don't have a LastFM account linked."
                )
                embed.set_footer(
                    text=f"Requested by {ctx.author.name}", 
                    icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
                )
                await ctx.send(embed=embed)
                return
            
            # Remove the user's data
            self.data_manager.unlink_user(user_id)
            
            # Send success message
            embed = create_success_embed(
                "LastFM Account Unlinked",
                "Your LastFM account has been unlinked from Leurs!"
            )
            embed.set_footer(
                text=f"Requested by {ctx.author.name}", 
                icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
            )
            await ctx.send(embed=embed)
            
        except Exception as e:
            print(f"Error in logout: {str(e)}")
            embed = create_error_embed(
                "Error",
                "An error occurred while trying to unlink your LastFM account."
            )
            await ctx.send(embed=embed)

async def setup(client):
    client.add_cog(LogoutCommand(client))