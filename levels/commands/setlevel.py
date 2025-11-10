"""
Set level admin command - Allows administrators to set user levels.
"""

import discord
from discord.ext import commands
from ..helpers.xp_manager import XPManager
from ..helpers.utils import create_success_embed, create_error_embed

class SetLevelCommand(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.xp_manager = XPManager()

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setlevel(self, ctx, member: discord.Member, messages: int):
        """Set a user's level based on message count (Admin only)."""
        try:
            if messages < 0:
                embed = create_error_embed(
                    "Invalid Input",
                    "Message count cannot be negative!"
                )
                await ctx.send(embed=embed)
                return
            
            # Set user level from message count
            user_id = str(member.id)
            stats = self.xp_manager.set_user_level_from_messages(user_id, messages)
            
            # Create success embed
            embed = create_success_embed(
                "Level Updated",
                f"Set {member.mention}'s stats:\n"
                f"Messages: **{stats['messages']:,}**\n"
                f"XP: **{stats['xp']:,}**\n"
                f"Level: **{stats['level']:,}**"
            )
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = create_error_embed(
                "Error",
                f"An error occurred while updating {member.mention}'s level.\nPlease try again later."
            )
            await ctx.send(embed=embed)
            print(f"Error in setlevel command: {str(e)}")

    @setlevel.error
    async def setlevel_error(self, ctx, error):
        """Handle setlevel command errors."""
        if isinstance(error, commands.MissingPermissions):
            embed = create_error_embed(
                "Permission Denied",
                "You don't have permission to use this command."
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MemberNotFound):
            embed = create_error_embed(
                "Error",
                "Member not found."
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = create_error_embed(
                "Error",
                "Please provide both a member and message count.\nUsage: `setlevel @user message_count`"
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.BadArgument):
            embed = create_error_embed(
                "Error",
                "Invalid argument. Message count must be a number.\nUsage: `setlevel @user message_count`"
            )
            await ctx.send(embed=embed)
        else:
            # Re-raise unhandled errors
            raise error

async def setup(client):
    await client.add_cog(SetLevelCommand(client))