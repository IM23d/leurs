import discord
from discord.ext import commands
import json
import os
import re
import asyncio
from datetime import datetime, timedelta
import unicodedata

class BlockedTermsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.blocked_terms_file = 'data/blockedterms.json'
        self.punishments_file = 'data/punishments.json'
        self.log_channel_id = 1390812291418558546
        # Use asyncio.create_task to run async init
        asyncio.create_task(self.ensure_files_exist())
        
    async def ensure_files_exist(self):
        if not os.path.exists(self.blocked_terms_file):
            with open(self.blocked_terms_file, 'w') as f:
                json.dump({}, f)
        
        if not os.path.exists(self.punishments_file):
            with open(self.punishments_file, 'w') as f:
                json.dump({}, f)
    
    async def load_blocked_terms(self):
        try:
            with open(self.blocked_terms_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    async def save_blocked_terms(self, terms):
        with open(self.blocked_terms_file, 'w') as f:
            json.dump(terms, f, indent=4)
    
    async def load_punishments(self):
        try:
            with open(self.punishments_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    async def save_punishments(self, punishments):
        with open(self.punishments_file, 'w') as f:
            json.dump(punishments, f, indent=4)
    
    async def add_punishment_record(self, user_id, guild_id, punishment_type, reason, duration=None, moderator=None):
        punishments = await self.load_punishments()
        user_key = f"{user_id}_{guild_id}"
        
        if user_key not in punishments:
            punishments[user_key] = []
        
        record = {
            'type': punishment_type,
            'reason': reason,
            'timestamp': datetime.now().isoformat(),
            'moderator': str(moderator) if moderator else 'Automod',
            'duration': duration
        }
        
        punishments[user_key].append(record)
        await self.save_punishments(punishments)
    
    async def normalize_text(self, text):
        # Convert to lowercase
        text = text.lower()
        # Remove accents and special characters
        text = unicodedata.normalize('NFD', text)
        text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
        # Remove numbers
        text = re.sub(r'\d', '', text)
        # Remove special characters except spaces
        text = re.sub(r'[^\w\s]', '', text)
        # Replace multiple repeated characters with single character
        text = re.sub(r'(.)\1{2,}', r'\1', text)
        # Remove extra spaces
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    async def check_blocked_term(self, message_content, blocked_terms):
        normalized_message = await self.normalize_text(message_content)
        
        for term, data in blocked_terms.items():
            if data.get('advanced_filtering', False):
                # Advanced filtering with normalization
                normalized_term = await self.normalize_text(term)
                if normalized_term in normalized_message:
                    return term, data
            else:
                # Simple case-insensitive check
                if term.lower() in message_content.lower():
                    return term, data
        
        return None, None

    async def parse_duration(self, duration_str):
        if not duration_str:
            return None
        
        # Extract number and unit
        match = re.match(r'^(\d+)([smhd])', duration_str.lower())
        if not match:
            return None
            
        amount, unit = match.groups()
        amount = int(amount)
        
        if unit == 's':
            return amount
        elif unit == 'm':
            return amount * 60
        elif unit == 'h':
            return amount * 3600
        elif unit == 'd':
            return amount * 86400
        
        return None
    
    @commands.command(name='blockterm')
    @commands.has_permissions(administrator=True)
    async def block_term(self, ctx, term: str, punishment_type: str, duration: str = None, 
                        advanced_filtering: str = "false", *, custom_text: str = None):

        punishment_type = punishment_type.lower()
        
        if punishment_type not in ['mute', 'warn', 'kick', 'ban']:
            embed = discord.Embed(
                title="Error",
                description="Invalid punishment type. Use: mute, warn, kick, ban",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Parse duration if provided
        duration_seconds = None
        if duration and duration.lower() != "none":
            duration_seconds = await self.parse_duration(duration)
            if duration_seconds is None:
                embed = discord.Embed(
                    title="Error",
                    description="Invalid duration format. Use format like: 5s, 10m, 5h, 12d",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
        
        # Load current blocked terms
        blocked_terms = await self.load_blocked_terms()
        
        # Add new term
        blocked_terms[term] = {
            'punishment_type': punishment_type,
            'duration': duration_seconds,
            'duration_str': duration if duration and duration.lower() != "none" else None,
            'custom_text': custom_text,
            'advanced_filtering': advanced_filtering.lower() == "true",
            'added_by': str(ctx.author),
            'added_at': datetime.now().isoformat(),
            'guild_id': ctx.guild.id
        }
        
        # Save to file
        await self.save_blocked_terms(blocked_terms)
        
        embed = discord.Embed(
            title="Term Blocked",
            description=f"Successfully blocked term: `{term}`",
            color=discord.Color.green()
        )
        embed.add_field(name="Punishment", value=punishment_type.capitalize(), inline=True)
        if duration_seconds:
            embed.add_field(name="Duration", value=duration, inline=True)
        embed.add_field(name="Advanced Filtering", value=advanced_filtering.capitalize(), inline=True)
        if custom_text:
            embed.add_field(name="Custom Message", value=custom_text[:100] + "..." if len(custom_text) > 100 else custom_text, inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='unblockterm')
    @commands.has_permissions(administrator=True)
    async def unblock_term(self, ctx, *, term: str):
        blocked_terms = await self.load_blocked_terms()
        
        if term not in blocked_terms:
            embed = discord.Embed(
                title="Error",
                description=f"Term `{term}` is not currently blocked.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        del blocked_terms[term]
        self.save_blocked_terms(blocked_terms)
        
        embed = discord.Embed(
            title="Term Unblocked",
            description=f"Successfully unblocked term: `{term}`",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='blockedterms')
    @commands.has_permissions(administrator=True)
    async def list_blocked_terms(self, ctx):
        blocked_terms = await self.load_blocked_terms()

        # Filter terms for this guild
        guild_terms = {term: data for term, data in blocked_terms.items()
                    if data.get('guild_id') == ctx.guild.id}
        if not guild_terms:
            embed = discord.Embed(
                title="Blocked Terms",
                description="No blocked terms configured for this server.",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(
            title="Blocked Terms",
            description=f"Current blocked terms for {ctx.guild.name}:",
            color=discord.Color.blue()
        )
        
        for term, data in list(guild_terms.items())[:10]:  # Limit to 10 terms per page
            punishment_info = data['punishment_type'].capitalize()
            if data.get('duration_str'):
                punishment_info += f" ({data['duration_str']})"
            
            filtering_type = "Advanced" if data.get('advanced_filtering', False) else "Basic"
            
            embed.add_field(
                name=f"`{term}`",
                value=f"**Punishment:** {punishment_info}\n**Filtering:** {filtering_type}",
                inline=True
            )
        
        if len(guild_terms) > 10:
            embed.set_footer(text=f"Showing 10 of {len(guild_terms)} blocked terms")
        
        await ctx.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        if not message.guild:
            return
        
        # Skip if user is administrator
        if message.author.guild_permissions.administrator:
            return
        
        blocked_terms = await self.load_blocked_terms()
        
        # Filter terms for this guild
        guild_terms = {term: data for term, data in blocked_terms.items() 
                      if data.get('guild_id') == message.guild.id}
        
        if not guild_terms:
            return
        
        # Check for blocked terms
        detected_term, term_data = await self.check_blocked_term(message.content, guild_terms)
        
        if detected_term:
            # Delete the message
            try:
                await message.delete()
            except discord.NotFound:
                pass
            except discord.Forbidden:
                pass
            
            # Apply punishment
            await self.apply_punishment(message, detected_term, term_data)
    
    async def apply_punishment(self, message, detected_term, term_data):
        user = message.author
        guild = message.guild
        punishment_type = term_data['punishment_type']
        duration = term_data.get('duration')
        custom_text = term_data.get('custom_text', f"Used blocked term: {detected_term}")
        
        # Log channel
        log_channel = self.bot.get_channel(self.log_channel_id)
        
        try:
            if punishment_type == 'warn':
                # Add warning to record
                self.add_punishment_record(
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
                await message.channel.send(embed=embed)
                
                # Log to admin channel
                if log_channel:
                    log_embed = discord.Embed(
                        title="Auto-Moderation: Warning",
                        description=f"**User:** {user.mention} ({user})\n**Channel:** {message.channel.mention}\n**Reason:** {custom_text}",
                        color=discord.Color.orange(),
                        timestamp=datetime.now()
                    )
                    await log_channel.send(embed=log_embed)
            
            elif punishment_type == 'mute':
                # Find muted role or create it
                muted_role = discord.utils.get(guild.roles, name="Muted")
                if not muted_role:
                    muted_role = await guild.create_role(name="Muted", reason="Auto-moderation")
                    # Set permissions for muted role
                    for channel in guild.channels:
                        await channel.set_permissions(muted_role, send_messages=False, speak=False)
                
                # Add muted role
                await user.add_roles(muted_role, reason=f"Used blocked term: {detected_term}")
                
                # Add to punishment record
                duration_str = term_data.get('duration_str', 'Permanent')
                self.add_punishment_record(
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
                await message.channel.send(embed=embed)
                
                # Log to admin channel
                if log_channel:
                    log_embed = discord.Embed(
                        title="Auto-Moderation: Mute",
                        description=f"**User:** {user.mention} ({user})\n**Channel:** {message.channel.mention}\n**Reason:** {custom_text}",
                        color=discord.Color.red(),
                        timestamp=datetime.now()
                    )
                    if duration:
                        log_embed.add_field(name="Duration", value=term_data.get('duration_str', 'Unknown'), inline=True)
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
            
            elif punishment_type == 'kick':
                # Add to punishment record
                self.add_punishment_record(
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
                await message.channel.send(embed=embed)
                
                # Log to admin channel
                if log_channel:
                    log_embed = discord.Embed(
                        title="Auto-Moderation: Kick",
                        description=f"**User:** {user.mention} ({user})\n**Channel:** {message.channel.mention}\n**Reason:** {custom_text}",
                        color=discord.Color.red(),
                        timestamp=datetime.now()
                    )
                    await log_channel.send(embed=log_embed)
                
                # Kick user
                await user.kick(reason=f"Used blocked term: {detected_term}")
            
            elif punishment_type == 'ban':
                # Add to punishment record
                duration_str = term_data.get('duration_str', 'Permanent')
                self.add_punishment_record(
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
                await message.channel.send(embed=embed)
                
                # Log to admin channel
                if log_channel:
                    log_embed = discord.Embed(
                        title="Auto-Moderation: Ban",
                        description=f"**User:** {user.mention} ({user})\n**Channel:** {message.channel.mention}\n**Reason:** {custom_text}",
                        color=discord.Color.dark_red(),
                        timestamp=datetime.now()
                    )
                    if duration:
                        log_embed.add_field(name="Duration", value=term_data.get('duration_str', 'Unknown'), inline=True)
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

async def setup(bot):
    await bot.add_cog(BlockedTermsCog(bot))