import discord
from datetime import datetime
from collections import defaultdict
from typing import Dict, List
import asyncio

class DeletedMessage:
    """Class to store deleted message information"""
    def __init__(self, content: str, author: discord.Member, deleted_at: datetime,
                 attachments: List[Dict[str, str]], embeds: List[discord.Embed]):
        self.content = content
        self.author = author
        self.deleted_at = deleted_at
        self.attachments = attachments
        self.embeds = embeds

class SnipeManager:
    """Manager for deleted message tracking (snipe functionality)"""
    
    def __init__(self):
        self.deleted_messages: Dict[int, List[DeletedMessage]] = defaultdict(list)
        self._cleanup_task = None
    
    def start_cleanup_task(self, bot):
        """Start the cleanup task for old messages"""
        if self._cleanup_task is None:
            self._cleanup_task = bot.loop.create_task(self.clean_old_messages())
    
    def stop_cleanup_task(self):
        """Stop the cleanup task"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None
    
    async def clean_old_messages(self):
        """Clean up old deleted messages (older than 2 hours)"""
        while True:
            try:
                current_time = datetime.utcnow()
                for channel_id in list(self.deleted_messages.keys()):
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
    
    def add_deleted_message(self, message: discord.Message):
        """Add a deleted message to the tracking system"""
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
    
    def get_latest_deleted_message(self, channel_id: int) -> DeletedMessage:
        """Get the most recent deleted message for a channel"""
        if channel_id not in self.deleted_messages or not self.deleted_messages[channel_id]:
            return None
        return self.deleted_messages[channel_id][-1]
    
    def clear_channel_messages(self, channel_id: int):
        """Clear all stored deleted messages for a channel"""
        if channel_id in self.deleted_messages:
            del self.deleted_messages[channel_id]
    
    def has_messages(self, channel_id: int) -> bool:
        """Check if channel has any stored deleted messages"""
        return channel_id in self.deleted_messages and bool(self.deleted_messages[channel_id])