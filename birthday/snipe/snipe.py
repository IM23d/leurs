import discord
from discord.ext import commands
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from helpers.snipe_manager import SnipeManager
from helpers.utils import create_error_embed

class SnipeCommand:
    """Snipe deleted messages command"""
    
    def __init__(self, snipe_manager: SnipeManager):
        self.snipe_manager = snipe_manager
    
    @commands.command(name='s')
    async def snipe(self, ctx):
        """Show the most recently deleted message in this channel"""
        channel_id = ctx.channel.id
        
        if not self.snipe_manager.has_messages(channel_id):
            embed = create_error_embed("No recently deleted messages found in this channel!")
            await ctx.send(embed=embed)
            return

        # Get the most recent deleted message
        deleted_msg = self.snipe_manager.get_latest_deleted_message(channel_id)
        
        if not deleted_msg:
            embed = create_error_embed("No recently deleted messages found in this channel!")
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(
            color=0x2F3136,
            timestamp=deleted_msg.deleted_at
        )
        
        embed.set_author(
            name=f"{deleted_msg.author.name}#{deleted_msg.author.discriminator}",
            icon_url=deleted_msg.author.avatar.url if deleted_msg.author.avatar else None
        )
        
        if deleted_msg.content:
            embed.description = deleted_msg.content

        if deleted_msg.attachments:
            # Check for image attachments to set as embed image
            image_attachments = [
                att for att in deleted_msg.attachments
                if att.get('content_type', '').startswith('image/')
                or any(att['filename'].lower().endswith(ext) for ext in ('.png', '.jpg', '.jpeg', '.gif', '.webp'))
            ]
            
            if image_attachments:
                embed.set_image(url=image_attachments[0]['url'])
            
            # List all attachments
            attachment_list = []
            for i, att in enumerate(deleted_msg.attachments, 1):
                size_mb = att['size'] / (1024 * 1024)
                attachment_list.append(
                    f"[{att['filename']}]({att['url']}) ({size_mb:.2f}MB)"
                )
            
            if attachment_list:
                embed.add_field(
                    name="📎 Attachments",
                    value="\n".join(attachment_list),
                    inline=False
                )

        embed.set_footer(text="Message deleted")
        
        await ctx.send(embed=embed)
        
        # Send any embeds that were in the original message
        for original_embed in deleted_msg.embeds:
            try:
                await ctx.send(embed=original_embed)
            except:
                continue

def setup_command(cog, snipe_manager):
    """Setup function to add this command to the cog"""
    command_handler = SnipeCommand(snipe_manager)
    cog.add_command(command_handler.snipe)