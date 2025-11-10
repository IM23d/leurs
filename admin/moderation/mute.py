import discord
from discord.ext import commands
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from helpers.data_manager import DataManager
from helpers.utils import admin_only, send_error_embed, send_success_embed, parse_duration

class MuteCommand:
    """Mute moderation command"""
    
    def __init__(self):
        self.data_manager = DataManager()
    
    async def get_or_create_muted_role(self, ctx):
        """Get or create the Muted role"""
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not muted_role:
            muted_role = await ctx.guild.create_role(name="Muted")
            for channel in ctx.guild.channels:
                await channel.set_permissions(muted_role, speak=False, send_messages=False)
        return muted_role

    async def schedule_unmute(self, ctx, member, muted_role, duration):
        """Schedule automatic unmute"""
        duration_seconds = parse_duration(duration)
        await asyncio.sleep(duration_seconds)
        
        try:
            member = await ctx.guild.fetch_member(member.id)
        except discord.NotFound:
            return  # Member left the server
            
        if muted_role in member.roles:
            await member.remove_roles(muted_role)
            embed = discord.Embed(
                title="🔊 Automatic Unmute",
                description=f"{member.mention} has been automatically unmuted.",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
    
    @commands.command(name="mute")
    @admin_only()
    async def mute(self, ctx, member: discord.Member, duration: str = "10m", *, reason=None):
        """Mute a member for a specified duration"""
        
        muted_role = await self.get_or_create_muted_role(ctx)
        
        if muted_role in member.roles:
            await send_error_embed(ctx, "Error", f"{member.mention} is already muted.")
            return
        
        try:
            # Add muted role
            await member.add_roles(muted_role)
            
            # Add to user actions
            self.data_manager.add_user_action(ctx.guild.id, member.id, "mute", reason, duration)
            
            # Send confirmation
            embed = discord.Embed(
                title="🔇 Member Muted",
                description=f"{member.mention} has been muted for {duration}.",
                color=discord.Color.red()
            )
            embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            
            await ctx.send(embed=embed)
            
            # Schedule automatic unmute
            asyncio.create_task(self.schedule_unmute(ctx, member, muted_role, duration))
            
        except discord.Forbidden:
            await send_error_embed(ctx, "Error", "I don't have permission to manage roles.")
        except Exception as e:
            await send_error_embed(ctx, "Error", f"An error occurred while muting: {e}")

    @commands.command(name="unmute")
    @admin_only()
    async def unmute(self, ctx, member: discord.Member):
        """Unmute a member"""
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        
        if not muted_role or muted_role not in member.roles:
            await send_error_embed(ctx, "Error", f"{member.mention} is not muted.")
            return
        
        try:
            await member.remove_roles(muted_role)
            
            embed = discord.Embed(
                title="🔊 Member Unmuted",
                description=f"{member.mention} has been unmuted.",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await send_error_embed(ctx, "Error", "I don't have permission to manage roles.")

def setup_command(cog):
    """Setup function to add this command to the cog"""
    command_handler = MuteCommand()
    cog.add_command(command_handler.mute)
    cog.add_command(command_handler.unmute)