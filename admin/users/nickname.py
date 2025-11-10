import discord
from discord.ext import commands
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from helpers.data_manager import DataManager
from helpers.utils import admin_only, send_error_embed, send_success_embed

class NicknameCommand:
    """Nickname management commands"""
    
    def __init__(self):
        self.data_manager = DataManager()
    
    @commands.command(name="nick")
    @admin_only()
    async def nick(self, ctx, member: discord.Member = None, *, new_nickname = None):
        """Change a member's nickname"""
        # If no member is specified, use the command author
        if member is None and new_nickname is None:
            await send_error_embed(ctx, "Error", "Please provide a nickname.")
            return
            
        # If only one argument is provided, it's the new nickname for the author
        if new_nickname is None:
            new_nickname = str(member)
            member = ctx.author
            
        try:
            # Store the old nickname before changing
            old_nickname = member.nick or member.name
            
            # Change the nickname
            await member.edit(nick=new_nickname)
            
            # Add to nickname history
            self.data_manager.add_nickname_change(ctx.guild.id, member.id, old_nickname, new_nickname)
            
            embed = discord.Embed(
                title="✅ Nickname Changed",
                description=f"Changed {member.mention}'s nickname to: **{new_nickname}**",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await send_error_embed(ctx, "Error", "I don't have permission to change that user's nickname.")
        except discord.HTTPException as e:
            await send_error_embed(ctx, "Error", f"Failed to change nickname: {str(e)}")

    @commands.command(name="nickremove")
    @admin_only()
    async def nickremove(self, ctx, member: discord.Member = None):
        """Remove a member's nickname"""
        # If no member is specified, use the command author
        if member is None:
            member = ctx.author
            
        try:
            # Store the old nickname before removing
            old_nickname = member.nick or member.name
            
            # Remove the nickname by setting it to None
            await member.edit(nick=None)
            
            # Add to nickname history
            self.data_manager.add_nickname_change(ctx.guild.id, member.id, old_nickname, None)
            
            embed = discord.Embed(
                title="✅ Nickname Removed",
                description=f"Removed {member.mention}'s nickname. They are now displayed as: **{member.name}**",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await send_error_embed(ctx, "Error", "I don't have permission to change that user's nickname.")
        except discord.HTTPException as e:
            await send_error_embed(ctx, "Error", f"Failed to remove nickname: {str(e)}")

    @commands.command(name="nickrevert")
    @admin_only()
    async def nickrevert(self, ctx, member: discord.Member = None):
        """Revert a member's nickname to their previous one"""
        # If no member is specified, use the command author
        if member is None:
            member = ctx.author
            
        try:
            # Get the previous nickname
            previous_nickname = self.data_manager.get_previous_nickname(ctx.guild.id, member.id)
            
            if previous_nickname is None:
                await send_error_embed(ctx, "Error", f"No previous nickname found for {member.mention}.")
                return
                
            # Store the current nickname before changing
            current_nickname = member.nick or member.name
            
            # Change the nickname to the previous one
            await member.edit(nick=previous_nickname)
            
            # Add to nickname history
            self.data_manager.add_nickname_change(ctx.guild.id, member.id, current_nickname, previous_nickname)
            
            embed = discord.Embed(
                title="✅ Nickname Reverted",
                description=f"Reverted {member.mention}'s nickname to: **{previous_nickname}**",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await send_error_embed(ctx, "Error", "I don't have permission to change that user's nickname.")
        except discord.HTTPException as e:
            await send_error_embed(ctx, "Error", f"Failed to revert nickname: {str(e)}")

    @commands.command(name="nickme")
    async def nickme(self, ctx, *, new_nickname=None):
        """Change your own nickname"""
        if new_nickname is None:
            await send_error_embed(ctx, "Error", "Please provide a new nickname.")
            return
            
        try:
            # Store the old nickname before changing
            old_nickname = ctx.author.nick or ctx.author.name
            
            # Change the nickname
            await ctx.author.edit(nick=new_nickname)
            
            # Add to nickname history
            self.data_manager.add_nickname_change(ctx.guild.id, ctx.author.id, old_nickname, new_nickname)
            
            embed = discord.Embed(
                title="✅ Nickname Changed",
                description=f"Changed your nickname to: **{new_nickname}**",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await send_error_embed(ctx, "Error", "I don't have permission to change your nickname.")
        except discord.HTTPException as e:
            await send_error_embed(ctx, "Error", f"Failed to change nickname: {str(e)}")
            
    @commands.command(name="nickmeremove")
    async def nickmeremove(self, ctx):
        """Remove your own nickname"""
        try:
            # Store the old nickname before removing
            old_nickname = ctx.author.nick or ctx.author.name
            
            # Remove the nickname by setting it to None
            await ctx.author.edit(nick=None)
            
            # Add to nickname history
            self.data_manager.add_nickname_change(ctx.guild.id, ctx.author.id, old_nickname, None)
            
            embed = discord.Embed(
                title="✅ Nickname Removed",
                description=f"Removed your nickname. You are now displayed as: **{ctx.author.name}**",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await send_error_embed(ctx, "Error", "I don't have permission to change your nickname.")
        except discord.HTTPException as e:
            await send_error_embed(ctx, "Error", f"Failed to remove nickname: {str(e)}")
            
    @commands.command(name="nickmerevert")
    async def nickmerevert(self, ctx):
        """Revert your nickname to the previous one"""
        try:
            # Get the previous nickname
            previous_nickname = self.data_manager.get_previous_nickname(ctx.guild.id, ctx.author.id)
            
            if previous_nickname is None:
                await send_error_embed(ctx, "Error", "No previous nickname found for you.")
                return
                
            # Store the current nickname before changing
            current_nickname = ctx.author.nick or ctx.author.name
            
            # Change the nickname to the previous one
            await ctx.author.edit(nick=previous_nickname)
            
            # Add to nickname history
            self.data_manager.add_nickname_change(ctx.guild.id, ctx.author.id, current_nickname, previous_nickname)
            
            embed = discord.Embed(
                title="✅ Nickname Reverted",
                description=f"Reverted your nickname to: **{previous_nickname}**",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await send_error_embed(ctx, "Error", "I don't have permission to change your nickname.")
        except discord.HTTPException as e:
            await send_error_embed(ctx, "Error", f"Failed to revert nickname: {str(e)}")

def setup_command(cog):
    """Setup function to add this command to the cog"""
    command_handler = NicknameCommand()
    cog.add_command(command_handler.nick)
    cog.add_command(command_handler.nickremove)
    cog.add_command(command_handler.nickrevert)
    cog.add_command(command_handler.nickme)
    cog.add_command(command_handler.nickmeremove)
    cog.add_command(command_handler.nickmerevert)