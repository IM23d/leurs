import discord
from discord.ext import commands
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from helpers.data_manager import DataManager
from helpers.utils import admin_only, send_error_embed, send_success_embed

class KickCommand:
    """Kick moderation command"""
    
    def __init__(self):
        self.data_manager = DataManager()
    
    @commands.command(name="kick")
    @admin_only()
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        """Kick a member from the server"""
        
        # Permission checks
        if member == ctx.author:
            await send_error_embed(ctx, "Error", "You cannot kick yourself!")
            return
            
        if member == ctx.guild.owner:
            await send_error_embed(ctx, "Error", "You cannot kick the server owner!")
            return
            
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await send_error_embed(ctx, "Error", "You cannot kick someone with a higher or equal role!")
            return
            
        if member.top_role >= ctx.guild.me.top_role:
            await send_error_embed(ctx, "Error", "I cannot kick someone with a higher or equal role than me!")
            return
        
        try:
            # Try to DM the user before kicking
            try:
                dm_embed = discord.Embed(
                    title="🦶 You have been kicked",
                    description=f"You were kicked from **{ctx.guild.name}**",
                    color=discord.Color.orange()
                )
                dm_embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
                dm_embed.add_field(name="Moderator", value=str(ctx.author), inline=False)
                
                await member.send(embed=dm_embed)
                dm_sent = True
            except:
                dm_sent = False
            
            # Kick the member
            await member.kick(reason=f"Kicked by {ctx.author}: {reason or 'No reason provided'}")
            
            # Add to user actions
            self.data_manager.add_user_action(ctx.guild.id, member.id, "kick", reason)
            
            # Send confirmation
            embed = discord.Embed(
                title="✅ Member Kicked",
                description=f"**{member}** has been kicked from the server",
                color=discord.Color.orange()
            )
            embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            
            if dm_sent:
                embed.add_field(name="DM", value="✅ User was notified", inline=True)
            else:
                embed.add_field(name="DM", value="❌ Could not notify user", inline=True)
            
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await send_error_embed(ctx, "Error", "I don't have permission to kick this member!")
        except discord.HTTPException as e:
            await send_error_embed(ctx, "Error", f"An error occurred while kicking the member: {e}")

def setup_command(cog):
    """Setup function to add this command to the cog"""
    command_handler = KickCommand()
    cog.add_command(command_handler.kick)