"""
Quote command for creating quote images.
"""

import discord
from discord.ext import commands

class QuoteCommand(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.utils = None
        
    def set_utils(self, utils):
        """Set the utils instance."""
        self.utils = utils
        
    @commands.command()
    async def quote(self, ctx):
        """Create a quote image from a replied message."""
        if not self.utils:
            await ctx.send("Quote system not available.")
            return
            
        try:
            temp_msg = await ctx.send("Generating quote image...")
            
            if not ctx.message.reference:
                await temp_msg.edit(content="You need to reply to a message to quote it!")
                return
            
            # Get the message being replied to
            try:
                replied_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            except discord.NotFound:
                await temp_msg.edit(content="I couldn't find the message you're replying to.")
                return
            except Exception:
                await temp_msg.edit(content="Error fetching the message.")
                return
            
            # Get the message author's avatar URL
            avatar_url = replied_msg.author.display_avatar.url
            
            # Create the quote image
            image_buffer = await self.utils.create_quote_image(
                avatar_url, 
                replied_msg.content, 
                replied_msg.author.display_name
            )
            
            if image_buffer:
                # Send the image
                await ctx.send(file=discord.File(fp=image_buffer, filename='quote.png'))
                # Delete the temporary message
                await temp_msg.delete()
            else:
                await temp_msg.edit(content="Failed to create quote image.")
        except Exception:
            await ctx.send("An error occurred while creating the quote image.")

async def setup(client):
    """Setup function for the Quote command."""
    client.add_cog(QuoteCommand(client))