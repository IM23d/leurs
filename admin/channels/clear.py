import discord
from discord.ext import commands
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from helpers.utils import admin_only, send_error_embed

class ClearCommand:
    """Channel clearing command"""
    
    @commands.command(name="clear")
    @admin_only()
    async def clear(self, ctx, amount: int):
        """Clear a specified number of messages"""
        try:
            # Add 1 to include the command message itself
            amount = amount + 1
            
            # Check if amount is within Discord's limits
            if amount > 100:
                await send_error_embed(ctx, "Error", "Cannot delete more than 99 messages at once.")
                return
            elif amount < 1:
                await send_error_embed(ctx, "Error", "Please specify a positive number of messages to delete.")
                return
                
            # Delete messages
            deleted = await ctx.channel.purge(limit=amount)
            
            # Send confirmation message
            confirm_msg = await ctx.send(embed=discord.Embed(
                title="✅ Messages Cleared",
                description=f"Deleted {len(deleted)-1} messages.",
                color=discord.Color.green()
            ))
            
            # Delete confirmation message after 3 seconds
            await asyncio.sleep(3)
            await confirm_msg.delete()
            
        except discord.Forbidden:
            await send_error_embed(ctx, "Error", "I don't have permission to delete messages.")
        except discord.HTTPException as e:
            await send_error_embed(ctx, "Error", f"Failed to delete messages: {str(e)}")

def setup_command(cog):
    """Setup function to add this command to the cog"""
    command_handler = ClearCommand()
    cog.add_command(command_handler.clear)