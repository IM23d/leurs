import discord
from discord.ext import commands
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from helpers.utils import admin_only, send_error_embed, parse_color

class EmbedCommand:
    """Embed utility command"""
    
    @commands.command(name="embed")
    @admin_only()
    async def embed(self, ctx, color: str = None, *, text: str = None):
        """Create a custom embed"""
        # Delete the command message
        try:
            await ctx.message.delete()
        except:
            pass
            
        # Check if this is a reply to another message
        reference = ctx.message.reference
        if reference and reference.message_id:
            try:
                # Get the message being replied to
                replied_msg = await ctx.channel.fetch_message(reference.message_id)
                
                # Use the replied message's content as text
                if text is None:
                    text = replied_msg.content
                
                # Set up the embed color
                embed_color = parse_color(color)
                
                # Create the embed
                embed = discord.Embed(
                    description=text,
                    color=embed_color
                )
                
                # Add author information
                embed.set_author(
                    name=replied_msg.author.display_name,
                    icon_url=replied_msg.author.display_avatar.url
                )
                
                # Add timestamp
                embed.timestamp = replied_msg.created_at
                
                # Add attachments if any
                if replied_msg.attachments:
                    # If there's an image, set it as the embed image
                    for attachment in replied_msg.attachments:
                        if attachment.content_type and attachment.content_type.startswith('image/'):
                            embed.set_image(url=attachment.url)
                            break
                
                await ctx.send(embed=embed)
                
                # Try to delete the original message if bot has permissions
                try:
                    await replied_msg.delete()
                except:
                    pass
                    
                return
            except discord.NotFound:
                # Message not found, continue with normal embed
                pass
                
        # Check if text is provided
        if text is None:
            if color is None:
                # Neither color nor text provided
                await send_error_embed(ctx, "Error", "Please provide text for the embed.")
                return
            else:
                # Only color provided, use it as text and set color to default
                text = color
                color = None
                
        # Set up the embed color
        embed_color = parse_color(color)
        
        # Create and send the embed
        embed = discord.Embed(
            description=text,
            color=embed_color
        )
        
        await ctx.send(embed=embed)

def setup_command(cog):
    """Setup function to add this command to the cog"""
    command_handler = EmbedCommand()
    cog.add_command(command_handler.embed)