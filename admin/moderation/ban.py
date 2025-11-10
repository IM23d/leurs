import discord
from discord.ext import commands
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from helpers.data_manager import DataManager
from helpers.utils import admin_only, send_error_embed, send_success_embed

class BanCommand:
    """Ban moderation command"""
    
    def __init__(self):
        self.data_manager = DataManager()
    
    @commands.command(name="ban")
    @admin_only()
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        """Ban a member from the server"""
        
        # Permission checks
        if member == ctx.author:
            await send_error_embed(ctx, "Error", "You cannot ban yourself!")
            return
            
        if member == ctx.guild.owner:
            await send_error_embed(ctx, "Error", "You cannot ban the server owner!")
            return
            
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await send_error_embed(ctx, "Error", "You cannot ban someone with a higher or equal role!")
            return
            
        if member.top_role >= ctx.guild.me.top_role:
            await send_error_embed(ctx, "Error", "I cannot ban someone with a higher or equal role than me!")
            return
        
        try:
            # Try to DM the user before banning
            try:
                dm_embed = discord.Embed(
                    title="🔨 You have been banned",
                    description=f"You were banned from **{ctx.guild.name}**",
                    color=discord.Color.red()
                )
                dm_embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
                dm_embed.add_field(name="Moderator", value=str(ctx.author), inline=False)
                
                await member.send(embed=dm_embed)
                dm_sent = True
            except:
                dm_sent = False
            
            # Ban the member
            await member.ban(reason=f"Banned by {ctx.author}: {reason or 'No reason provided'}")
            
            # Add to user actions
            self.data_manager.add_user_action(ctx.guild.id, member.id, "ban", reason)
            
            # Send confirmation
            embed = discord.Embed(
                title="✅ Member Banned",
                description=f"**{member}** has been banned from the server",
                color=discord.Color.red()
            )
            embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            
            if dm_sent:
                embed.add_field(name="DM", value="✅ User was notified", inline=True)
            else:
                embed.add_field(name="DM", value="❌ Could not notify user", inline=True)
            
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await send_error_embed(ctx, "Error", "I don't have permission to ban this member!")
        except discord.HTTPException as e:
            await send_error_embed(ctx, "Error", f"An error occurred while banning the member: {e}")

def setup_command(cog):
    """Setup function to add this command to the cog"""
    command_handler = BanCommand()
    cog.add_command(command_handler.ban)