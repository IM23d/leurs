import discord
import asyncio
from datetime import datetime
from .utils import create_log_embed

class PunishmentManager:
    """Manages punishment application for blocked terms"""
    
    def __init__(self, bot, data_manager, log_channel_id=1390812291418558546):
        self.bot = bot
        self.data_manager = data_manager
        self.log_channel_id = log_channel_id
    
    async def get_log_channel(self):
        """Get the log channel"""
        return self.bot.get_channel(self.log_channel_id)
    
    async def apply_punishment(self, message, detected_term, term_data):
        """Apply punishment for using a blocked term"""
        user = message.author
        guild = message.guild
        punishment_type = term_data['punishment_type']
        duration = term_data.get('duration')
        custom_text = term_data.get('custom_text', f"Used blocked term: {detected_term}")
        
        log_channel = await self.get_log_channel()
        
        try:
            if punishment_type == 'warn':
                await self._apply_warning(user, guild, detected_term, custom_text, message.channel, log_channel)
            elif punishment_type == 'mute':
                await self._apply_mute(user, guild, detected_term, custom_text, duration, term_data, message.channel, log_channel)
            elif punishment_type == 'kick':
                await self._apply_kick(user, guild, detected_term, custom_text, message.channel, log_channel)
            elif punishment_type == 'ban':
                await self._apply_ban(user, guild, detected_term, custom_text, duration, term_data, message.channel, log_channel)
        
        except discord.Forbidden:
            if log_channel:
                error_embed = discord.Embed(
                    title="Auto-Moderation Error",
                    description=f"Failed to apply {punishment_type} to {user.mention}. Insufficient permissions.",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
                await log_channel.send(embed=error_embed)
        except Exception as e:
            if log_channel:
                error_embed = discord.Embed(
                    title="Auto-Moderation Error",
                    description=f"Error applying {punishment_type} to {user.mention}: {str(e)}",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
                await log_channel.send(embed=error_embed)
    
    async def _apply_warning(self, user, guild, detected_term, custom_text, channel, log_channel):
        """Apply warning punishment"""
        # Add warning to record
        await self.data_manager.add_punishment_record(
            user.id, guild.id, 'warn', 
            f"Used blocked term: {detected_term}",
            moderator="Automod"
        )
        
        # Send warning message
        embed = discord.Embed(
            title="Warning",
            description=f"{user.mention}, you have been warned for using a blocked term.",
            color=discord.Color.orange()
        )
        embed.add_field(name="Reason", value=custom_text, inline=False)
        await channel.send(embed=embed)
        
        # Log to admin channel
        if log_channel:
            log_embed = create_log_embed(
                "Auto-Moderation: Warning",
                user, channel, custom_text,
                discord.Color.orange()
            )
            await log_channel.send(embed=log_embed)
    
    async def _apply_mute(self, user, guild, detected_term, custom_text, duration, term_data, channel, log_channel):
        """Apply mute punishment"""
        # Find muted role or create it
        muted_role = discord.utils.get(guild.roles, name="Muted")
        if not muted_role:
            muted_role = await guild.create_role(name="Muted", reason="Auto-moderation")
            # Set permissions for muted role
            for guild_channel in guild.channels:
                await guild_channel.set_permissions(muted_role, send_messages=False, speak=False)
        
        # Add muted role
        await user.add_roles(muted_role, reason=f"Used blocked term: {detected_term}")
        
        # Add to punishment record
        duration_str = term_data.get('duration_str', 'Permanent')
        await self.data_manager.add_punishment_record(
            user.id, guild.id, 'mute',
            f"Used blocked term: {detected_term}",
            duration_str, "Automod"
        )
        
        # Send mute message
        embed = discord.Embed(
            title="Muted",
            description=f"{user.mention}, you have been muted for using a blocked term.",
            color=discord.Color.red()
        )
        embed.add_field(name="Reason", value=custom_text, inline=False)
        if duration:
            embed.add_field(name="Duration", value=term_data.get('duration_str', 'Unknown'), inline=True)
        await channel.send(embed=embed)
        
        # Log to admin channel
        if log_channel:
            log_embed = create_log_embed(
                "Auto-Moderation: Mute",
                user, channel, custom_text,
                discord.Color.red(),
                term_data.get('duration_str') if duration else None
            )
            await log_channel.send(embed=log_embed)
        
        # Set up unmute timer
        if duration:
            await asyncio.sleep(duration)
            try:
                await user.remove_roles(muted_role, reason="Automatic unmute")
                if log_channel:
                    unmute_embed = discord.Embed(
                        title="Auto-Unmute",
                        description=f"**User:** {user.mention} ({user})\n**Reason:** Mute duration expired",
                        color=discord.Color.green(),
                        timestamp=datetime.now()
                    )
                    await log_channel.send(embed=unmute_embed)
            except discord.NotFound:
                pass
    
    async def _apply_kick(self, user, guild, detected_term, custom_text, channel, log_channel):
        """Apply kick punishment"""
        # Add to punishment record
        await self.data_manager.add_punishment_record(
            user.id, guild.id, 'kick',
            f"Used blocked term: {detected_term}",
            moderator="Automod"
        )
        
        # Send kick message
        embed = discord.Embed(
            title="Kicked",
            description=f"{user.mention}, you have been kicked for using a blocked term.",
            color=discord.Color.red()
        )
        embed.add_field(name="Reason", value=custom_text, inline=False)
        await channel.send(embed=embed)
        
        # Log to admin channel
        if log_channel:
            log_embed = create_log_embed(
                "Auto-Moderation: Kick",
                user, channel, custom_text,
                discord.Color.red()
            )
            await log_channel.send(embed=log_embed)
        
        # Kick user
        await user.kick(reason=f"Used blocked term: {detected_term}")
    
    async def _apply_ban(self, user, guild, detected_term, custom_text, duration, term_data, channel, log_channel):
        """Apply ban punishment"""
        # Add to punishment record
        duration_str = term_data.get('duration_str', 'Permanent')
        await self.data_manager.add_punishment_record(
            user.id, guild.id, 'ban',
            f"Used blocked term: {detected_term}",
            duration_str, "Automod"
        )
        
        # Send ban message
        embed = discord.Embed(
            title="Banned",
            description=f"{user.mention}, you have been banned for using a blocked term.",
            color=discord.Color.dark_red()
        )
        embed.add_field(name="Reason", value=custom_text, inline=False)
        if duration:
            embed.add_field(name="Duration", value=term_data.get('duration_str', 'Unknown'), inline=True)
        await channel.send(embed=embed)
        
        # Log to admin channel
        if log_channel:
            log_embed = create_log_embed(
                "Auto-Moderation: Ban",
                user, channel, custom_text,
                discord.Color.dark_red(),
                term_data.get('duration_str') if duration else None
            )
            await log_channel.send(embed=log_embed)
        
        # Ban user
        await user.ban(reason=f"Used blocked term: {detected_term}")
        
        # Set up unban timer
        if duration:
            await asyncio.sleep(duration)
            try:
                await guild.unban(user, reason="Automatic unban")
                if log_channel:
                    unban_embed = discord.Embed(
                        title="Auto-Unban",
                        description=f"**User:** {user.mention} ({user})\n**Reason:** Ban duration expired",
                        color=discord.Color.green(),
                        timestamp=datetime.now()
                    )
                    await log_channel.send(embed=unban_embed)
            except discord.NotFound:
                pass