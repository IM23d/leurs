import discord
from discord.ext import commands
from datetime import datetime
from collections import defaultdict
import asyncio
from typing import Dict, List

class DeletedMessage:
    def __init__(self, content: str, author: discord.Member, deleted_at: datetime,
                 attachments: List[Dict[str, str]], embeds: List[discord.Embed]):
        self.content = content
        self.author = author
        self.deleted_at = deleted_at
        self.attachments = attachments
        self.embeds = embeds

class SnipeCog(commands.Cog, name="snipe"):
    def __init__(self, bot):
        self.bot = bot
        self.deleted_messages: Dict[int, List[DeletedMessage]] = defaultdict(list)
        self.bot.loop.create_task(self.clean_old_messages())

    async def clean_old_messages(self):
        while True:
            try:
                current_time = datetime.utcnow()
                for channel_id in list(self.deleted_messages.keys()):
                    # Remove messages older than 2 hours
                    self.deleted_messages[channel_id] = [
                        msg for msg in self.deleted_messages[channel_id]
                        if (current_time - msg.deleted_at).total_seconds() < 7200
                    ]
                    # Remove empty channel entries
                    if not self.deleted_messages[channel_id]:
                        del self.deleted_messages[channel_id]
                await asyncio.sleep(300)  # Clean every 5 minutes
            except Exception as e:
                print(f"Error in clean_old_messages: {e}")
                await asyncio.sleep(300)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return

        # Store attachment information
        attachments = []
        for attachment in message.attachments:
            attachments.append({
                'url': attachment.url,
                'filename': attachment.filename,
                'content_type': attachment.content_type if hasattr(attachment, 'content_type') else None,
                'size': attachment.size
            })

        # Create DeletedMessage object
        deleted_msg = DeletedMessage(
            content=message.content,
            author=message.author,
            deleted_at=datetime.utcnow(),
            attachments=attachments,
            embeds=message.embeds
        )
        
        # Store the deleted message
        self.deleted_messages[message.channel.id].append(deleted_msg)

    @commands.command(name='snipe')
    async def snipe(self, ctx):
        channel_id = ctx.channel.id
        if channel_id not in self.deleted_messages or not self.deleted_messages[channel_id]:
            embed = discord.Embed(
                description="❌ No recently deleted messages found in this channel!",
                color=0x2F3136
            )
            await ctx.send(embed=embed)
            return

        # Get the most recent deleted message
        deleted_msg = self.deleted_messages[channel_id][-1]
        
        # Create the main embed
        embed = discord.Embed(
            color=0x2F3136,
            timestamp=deleted_msg.deleted_at
        )
        
        # Add author info
        embed.set_author(
            name=f"{deleted_msg.author.name}#{deleted_msg.author.discriminator}",
            icon_url=deleted_msg.author.avatar.url if deleted_msg.author.avatar else None
        )
        
        # Add message content if it exists
        if deleted_msg.content:
            embed.description = deleted_msg.content

        # Handle attachments
        if deleted_msg.attachments:
            # Get the first image attachment if any exist
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
        
        # Send the main embed
        await ctx.send(embed=embed)
        
        # Send any additional embeds from the original message
        for original_embed in deleted_msg.embeds:
            try:
                await ctx.send(embed=original_embed)
            except:
                continue

    @commands.command(name='clearsnipe')
    async def clear_snipe(self, ctx):
        channel_id = ctx.channel.id
        if channel_id in self.deleted_messages:
            del self.deleted_messages[channel_id]
        await ctx.message.add_reaction('✅')

async def setup(bot):
    await bot.add_cog(SnipeCog(bot))  