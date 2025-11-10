import discord
from discord.ext import commands
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from helpers.data_manager import DataManager
from helpers.utils import admin_only, send_error_embed, send_success_embed

class WarnCommand:
    """Warning moderation command"""
    
    def __init__(self):
        self.data_manager = DataManager()
    
    @commands.command(name="warn")
    @admin_only()
    async def warn(self, ctx, member: discord.Member, *, reason=None):
        """Warn a member"""
        if reason is None:
            reason = "No reason provided"
            
        try:
            # Add warning to history
            self.data_manager.add_warning(ctx.guild.id, member.id, reason)
            
            # Create DM embed
            dm_embed = discord.Embed(
                title="⚠️ Warning",
                description=f"You have been warned in **{ctx.guild.name}**",
                color=discord.Color.yellow()
            )
            dm_embed.add_field(name="Reason", value=reason, inline=False)
            dm_embed.set_footer(text=f"Moderator: {ctx.author}")
            
            # Send DM to user
            try:
                await member.send(embed=dm_embed)
                dm_sent = True
            except discord.Forbidden:
                dm_sent = False
                
            # Create confirmation embed for the channel
            channel_embed = discord.Embed(
                title="⚠️ Member Warned",
                description=f"{member.mention} has been warned.",
                color=discord.Color.yellow()
            )
            channel_embed.add_field(name="Reason", value=reason, inline=False)
            channel_embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            
            if not dm_sent:
                channel_embed.add_field(name="Note", value="Could not send DM to user", inline=False)
                
            await ctx.send(embed=channel_embed)
            
        except Exception as e:
            await send_error_embed(ctx, "Error", f"Failed to warn user: {str(e)}")

    @commands.command(name="warnings")
    @admin_only()
    async def warnings(self, ctx, member: discord.Member):
        """View warnings for a member"""
        try:
            data = self.data_manager.load_json("warnings")
            guild_id_str = str(ctx.guild.id)
            user_id_str = str(member.id)
            
            if (guild_id_str not in data or 
                user_id_str not in data[guild_id_str] or
                not data[guild_id_str][user_id_str]):
                
                embed = discord.Embed(
                    title="📝 User Warnings",
                    description=f"{member.mention} has no warnings.",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
                return
            
            warnings = data[guild_id_str][user_id_str]
            
            embed = discord.Embed(
                title="📝 User Warnings",
                description=f"Warning history for {member.mention}",
                color=discord.Color.yellow()
            )
            
            # Show up to 10 most recent warnings
            warnings_to_show = warnings[-10:] if len(warnings) > 10 else warnings
            
            for i, warning in enumerate(warnings_to_show, 1):
                from datetime import datetime
                warning_time = datetime.fromisoformat(warning["timestamp"])
                time_str = warning_time.strftime("%Y-%m-%d %H:%M UTC")
                
                embed.add_field(
                    name=f"Warning {i}/{len(warnings)}",
                    value=f"**Reason:** {warning['reason']}\n**Date:** {time_str}",
                    inline=False
                )
            
            if len(warnings) > 10:
                embed.set_footer(text=f"Showing 10 most recent warnings. Total: {len(warnings)}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await send_error_embed(ctx, "Error", f"Failed to get warnings: {str(e)}")

    @commands.command(name="clearwarnings")
    @admin_only()
    async def clearwarnings(self, ctx, member: discord.Member):
        """Clear all warnings for a member"""
        try:
            data = self.data_manager.load_json("warnings")
            guild_id_str = str(ctx.guild.id)
            user_id_str = str(member.id)
            
            if (guild_id_str in data and 
                user_id_str in data[guild_id_str]):
                
                warning_count = len(data[guild_id_str][user_id_str])
                data[guild_id_str][user_id_str] = []
                self.data_manager.save_json("warnings", data)
                
                embed = discord.Embed(
                    title="✅ Warnings Cleared",
                    description=f"Cleared {warning_count} warnings for {member.mention}.",
                    color=discord.Color.green()
                )
            else:
                embed = discord.Embed(
                    title="📝 No Warnings",
                    description=f"{member.mention} has no warnings to clear.",
                    color=discord.Color.blue()
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await send_error_embed(ctx, "Error", f"Failed to clear warnings: {str(e)}")

def setup_command(cog):
    """Setup function to add this command to the cog"""
    command_handler = WarnCommand()
    cog.add_command(command_handler.warn)
    cog.add_command(command_handler.warnings)
    cog.add_command(command_handler.clearwarnings)