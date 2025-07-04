import discord
from discord.ext import commands
import random
import os
import asyncio
import re
from discord.ext.commands import has_permissions
import json
from datetime import datetime, timedelta
from collections import defaultdict
import pathlib

class AdminCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.pending_cclear = {}  # Store pending clear operations
        
        # Create data directory if it doesn't exist
        self.data_dir = pathlib.Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Cache file paths
        self.message_cache_file = self.data_dir / "message_cache.json"
        self.message_index_file = self.data_dir / "message_index.json"
        self.last_scan_file = self.data_dir / "last_scan.txt"
        self.word_index = defaultdict(list)  # In-memory index for faster searching
        
        # Role saver file paths
        self.roles_file = self.data_dir / "saved_roles.json"
        self.roles_info_file = self.data_dir / "roles_info.json"
        
        # Nickname history file path
        self.nickname_file = self.data_dir / "nickname_history.json"
        
        # Blocked terms file paths
        self.blocked_terms_file = self.data_dir / "blocked_terms.json"
        self.punishments_file = self.data_dir / "punishments.json"
        
        # Initialize role saving task
        self.role_save_task = None
        self.last_save_time = None
        self.next_save_time = None
        
        # Load role save info if exists
        self.load_role_save_info()
        
        # Initialize nickname history
        self.load_nickname_history()
        
        # Initialize blocked terms
        self.ensure_files_exist()

    def cog_unload(self):
        # Cancel the role save task when the cog is unloaded
        if self.role_save_task:
            self.role_save_task.cancel()
            
    async def cog_load(self):
        # Start the role save task when the cog is loaded
        self.role_save_task = self.client.loop.create_task(self.role_save_loop())

    # Load nickname history from file
    def load_nickname_history(self):
        """Load nickname history from JSON file"""
        try:
            if os.path.exists(self.nickname_file):
                with open(self.nickname_file, 'r') as f:
                    return json.load(f)
            else:
                # Create empty nickname history file
                with open(self.nickname_file, 'w') as f:
                    json.dump({}, f)
                return {}
        except Exception as e:
            print(f"Error loading nickname history: {e}")
            return {}
            
    # Save nickname history to file
    def save_nickname_history(self, history):
        """Save nickname history to JSON file"""
        try:
            with open(self.nickname_file, 'w') as f:
                json.dump(history, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving nickname history: {e}")
            return False
            
    # Add nickname change to history
    async def add_nickname_change(self, guild_id, user_id, old_nick, new_nick):
        """Add a nickname change to the history"""
        try:
            # Load current history
            history = self.load_nickname_history()
            
            # Initialize guild section if not exists
            guild_id_str = str(guild_id)
            if guild_id_str not in history:
                history[guild_id_str] = {}
                
            # Initialize user section if not exists
            user_id_str = str(user_id)
            if user_id_str not in history[guild_id_str]:
                history[guild_id_str][user_id_str] = []
                
            # Add new nickname change with timestamp
            history[guild_id_str][user_id_str].append({
                "old_nick": old_nick,
                "new_nick": new_nick,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Save updated history
            self.save_nickname_history(history)
            return True
        except Exception as e:
            print(f"Error adding nickname change: {e}")
            return False

    # Get previous nickname from history
    async def get_previous_nickname(self, guild_id, user_id):
        """Get the previous nickname for a user"""
        try:
            # Load current history
            history = self.load_nickname_history()
            
            # Check if we have history for this user in this guild
            guild_id_str = str(guild_id)
            user_id_str = str(user_id)
            
            if (guild_id_str in history and 
                user_id_str in history[guild_id_str] and 
                len(history[guild_id_str][user_id_str]) > 0):
                
                # Get the most recent nickname change
                changes = history[guild_id_str][user_id_str]
                if changes:
                    return changes[-1]["old_nick"]
            
            return None
        except Exception as e:
            print(f"Error getting previous nickname: {e}")
            return None

    # ============ BLOCKED TERMS FUNCTIONALITY ============
    
    def ensure_files_exist(self):
        """Ensure blocked terms and punishments files exist"""
        try:
            # Create blocked terms file if it doesn't exist
            if not self.blocked_terms_file.exists():
                with open(self.blocked_terms_file, 'w') as f:
                    json.dump([], f)
            
            # Create punishments file if it doesn't exist
            if not self.punishments_file.exists():
                with open(self.punishments_file, 'w') as f:
                    json.dump([], f)
        except Exception as e:
            print(f"Error ensuring blocked terms files exist: {e}")

    def load_blocked_terms(self):
        """Load blocked terms from JSON file"""
        try:
            with open(self.blocked_terms_file, 'r') as f:
                content = f.read().strip()
                if not content:
                    return []
                return json.loads(content)
        except Exception as e:
            print(f"Error loading blocked terms: {e}")
            return []

    def save_blocked_terms(self, terms):
        """Save blocked terms to JSON file"""
        try:
            with open(self.blocked_terms_file, 'w') as f:
                json.dump(terms, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving blocked terms: {e}")
            return False

    def load_punishments(self):
        """Load punishment records from JSON file"""
        try:
            with open(self.punishments_file, 'r') as f:
                content = f.read().strip()
                if not content:
                    return []
                return json.loads(content)
        except Exception as e:
            print(f"Error loading punishments: {e}")
            return []

    def save_punishments(self, punishments):
        """Save punishment records to JSON file"""
        try:
            with open(self.punishments_file, 'w') as f:
                json.dump(punishments, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving punishments: {e}")
            return False

    def add_punishment_record(self, user_id, guild_id, term, punishment_type, duration=None):
        """Add a punishment record to the file"""
        try:
            punishments = self.load_punishments()
            record = {
                "user_id": str(user_id),
                "guild_id": str(guild_id),
                "term": term,
                "punishment_type": punishment_type,
                "duration": duration,
                "timestamp": datetime.utcnow().isoformat()
            }
            punishments.append(record)
            return self.save_punishments(punishments)
        except Exception as e:
            print(f"Error adding punishment record: {e}")
            return False

    def normalize_text(self, text):
        """Normalize text for comparison (remove spaces, special chars, convert to lowercase)"""
        if not text:
            return ""
        # Convert to lowercase and remove spaces, punctuation, and special characters
        normalized = re.sub(r'[^a-z0-9]', '', text.lower())
        return normalized

    def check_blocked_term(self, text):
        """Check if text contains any blocked terms"""
        if not text:
            return None
            
        blocked_terms = self.load_blocked_terms()
        normalized_text = self.normalize_text(text)
        
        for term_data in blocked_terms:
            if isinstance(term_data, dict):
                term = term_data.get('term', '')
                punishment = term_data.get('punishment', 'mute')
                duration = term_data.get('duration', '10m')
            else:
                # Handle old format (just strings)
                term = str(term_data)
                punishment = 'mute'
                duration = '10m'
            
            normalized_term = self.normalize_text(term)
            if normalized_term and normalized_term in normalized_text:
                return {
                    'term': term,
                    'punishment': punishment,
                    'duration': duration
                }
        
        return None

    def parse_duration(self, duration_str):
        """Parse duration string and return seconds. Reuses existing logic from admin commands"""
        if not duration_str:
            return 600  # Default 10 minutes
        
        try:
            # Regular expression to parse time format (reuse from existing commands)
            time_pattern = re.compile(r'(\d+)([smhd])')
            match = time_pattern.match(duration_str.lower())
            
            if not match:
                # Try parsing as just a number (assume minutes)
                try:
                    return int(duration_str) * 60
                except ValueError:
                    return 600  # Default 10 minutes
            
            amount = int(match.group(1))
            unit = match.group(2)
            
            # Convert to seconds
            multipliers = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
            return amount * multipliers[unit]
            
        except Exception as e:
            print(f"Error parsing duration {duration_str}: {e}")
            return 600  # Default 10 minutes

    async def apply_punishment(self, message, term_data):
        """Apply punishment for blocked term usage"""
        try:
            member = message.author
            guild = message.guild
            
            if not member or not guild:
                return
            
            punishment_type = term_data.get('punishment', 'mute')
            duration = term_data.get('duration', '10m')
            term = term_data.get('term', 'unknown')
            
            # Record the punishment
            self.add_punishment_record(
                member.id, 
                guild.id, 
                term, 
                punishment_type, 
                duration
            )
            
            # Apply the punishment
            if punishment_type == 'mute':
                muted_role = await self.get_or_create_muted_role_for_message(guild)
                if muted_role and muted_role not in member.roles:
                    await member.add_roles(muted_role)
                    
                    # Delete the message
                    try:
                        await message.delete()
                    except:
                        pass
                    
                    # Send notification
                    embed = discord.Embed(
                        title="Blocked Term Detected",
                        description=f"{member.mention} has been muted for {duration} for using a blocked term.",
                        color=discord.Color.red()
                    )
                    embed.add_field(name="Term", value=f"||{term}||", inline=True)
                    embed.add_field(name="Duration", value=duration, inline=True)
                    await message.channel.send(embed=embed)
                    
                    # Schedule unmute
                    duration_seconds = self.parse_duration(duration)
                    asyncio.create_task(self.schedule_unmute_for_blocked_term(guild, member, muted_role, duration_seconds))
            
            elif punishment_type == 'kick':
                try:
                    await message.delete()
                except:
                    pass
                
                embed = discord.Embed(
                    title="Blocked Term Detected",
                    description=f"{member.mention} has been kicked for using a blocked term.",
                    color=discord.Color.red()
                )
                embed.add_field(name="Term", value=f"||{term}||", inline=True)
                await message.channel.send(embed=embed)
                
                await member.kick(reason=f"Used blocked term: {term}")
            
            elif punishment_type == 'ban':
                try:
                    await message.delete()
                except:
                    pass
                
                embed = discord.Embed(
                    title="Blocked Term Detected",
                    description=f"{member.mention} has been banned for using a blocked term.",
                    color=discord.Color.red()
                )
                embed.add_field(name="Term", value=f"||{term}||", inline=True)
                await message.channel.send(embed=embed)
                
                await member.ban(reason=f"Used blocked term: {term}")
                
        except Exception as e:
            print(f"Error applying punishment: {e}")

    async def get_or_create_muted_role_for_message(self, guild):
        """Get or create muted role for blocked terms (reuses existing logic)"""
        try:
            muted_role = discord.utils.get(guild.roles, name="Muted")
            if not muted_role:
                muted_role = await guild.create_role(name="Muted")
                for channel in guild.channels:
                    await channel.set_permissions(muted_role, speak=False, send_messages=False)
            return muted_role
        except Exception as e:
            print(f"Error creating muted role: {e}")
            return None

    async def schedule_unmute_for_blocked_term(self, guild, member, muted_role, duration_seconds):
        """Schedule unmute for blocked term punishment"""
        try:
            await asyncio.sleep(duration_seconds)
            
            # Re-fetch member to ensure they're still in the server
            try:
                member = await guild.fetch_member(member.id)
                if muted_role in member.roles:
                    await member.remove_roles(muted_role)
            except discord.NotFound:
                pass  # Member left the server
        except Exception as e:
            print(f"Error in scheduled unmute: {e}")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen for messages and check for blocked terms"""
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Ignore DMs
        if not message.guild:
            return
        
        # Ignore messages from administrators
        if message.author.guild_permissions.administrator:
            return
        
        # Check for blocked terms
        term_data = self.check_blocked_term(message.content)
        if term_data:
            await self.apply_punishment(message, term_data)

    # ============ BLOCKED TERMS COMMANDS ============

    @commands.command()
    @has_permissions(administrator=True)
    async def blockterm(self, ctx, *, args):
        """Add a blocked term with punishment type and duration
        
        Usage: 
        blockterm <term> [mute|kick|ban] [duration]
        
        Examples:
        blockterm badword
        blockterm "bad phrase" mute 30m
        blockterm spam kick
        blockterm severe ban
        """
        try:
            parts = args.split()
            if not parts:
                raise commands.CommandError("Please specify a term to block.")
            
            # Parse arguments
            if args.startswith('"') and '"' in args[1:]:
                # Handle quoted terms
                end_quote = args.find('"', 1)
                term = args[1:end_quote]
                remaining = args[end_quote+1:].strip().split()
            else:
                # Handle single word terms
                term = parts[0]
                remaining = parts[1:]
            
            # Set defaults
            punishment = 'mute'
            duration = '10m'
            
            # Parse remaining arguments
            if len(remaining) >= 1:
                if remaining[0].lower() in ['mute', 'kick', 'ban']:
                    punishment = remaining[0].lower()
                    if len(remaining) >= 2:
                        duration = remaining[1]
                else:
                    # First arg is duration, keep default punishment
                    duration = remaining[0]
            
            if len(remaining) >= 2 and remaining[0].lower() in ['mute', 'kick', 'ban']:
                duration = remaining[1]
            
            # Validate punishment type
            if punishment not in ['mute', 'kick', 'ban']:
                raise commands.CommandError("Punishment type must be 'mute', 'kick', or 'ban'.")
            
            # Load current terms
            blocked_terms = self.load_blocked_terms()
            
            # Check if term already exists
            for existing_term in blocked_terms:
                if isinstance(existing_term, dict):
                    if existing_term.get('term', '').lower() == term.lower():
                        raise commands.CommandError(f"Term '{term}' is already blocked.")
                elif str(existing_term).lower() == term.lower():
                    raise commands.CommandError(f"Term '{term}' is already blocked.")
            
            # Add new term
            new_term = {
                'term': term,
                'punishment': punishment,
                'duration': duration,
                'added_by': str(ctx.author.id),
                'added_at': datetime.utcnow().isoformat()
            }
            
            blocked_terms.append(new_term)
            
            if self.save_blocked_terms(blocked_terms):
                embed = discord.Embed(
                    title="Term Blocked",
                    description=f"Successfully added blocked term.",
                    color=discord.Color.green()
                )
                embed.add_field(name="Term", value=f"||{term}||", inline=True)
                embed.add_field(name="Punishment", value=punishment.title(), inline=True)
                if punishment == 'mute':
                    embed.add_field(name="Duration", value=duration, inline=True)
                await ctx.send(embed=embed)
            else:
                raise commands.CommandError("Failed to save blocked term.")
                
        except commands.CommandError:
            raise
        except Exception as e:
            raise commands.CommandError(f"An error occurred: {str(e)}")

    @commands.command()
    @has_permissions(administrator=True)
    async def unblockterm(self, ctx, *, term):
        """Remove a blocked term
        
        Usage: unblockterm <term>
        """
        try:
            blocked_terms = self.load_blocked_terms()
            
            # Find and remove the term
            removed = False
            for i, blocked_term in enumerate(blocked_terms):
                if isinstance(blocked_term, dict):
                    if blocked_term.get('term', '').lower() == term.lower():
                        blocked_terms.pop(i)
                        removed = True
                        break
                elif str(blocked_term).lower() == term.lower():
                    blocked_terms.pop(i)
                    removed = True
                    break
            
            if not removed:
                raise commands.CommandError(f"Term '{term}' is not in the blocked list.")
            
            if self.save_blocked_terms(blocked_terms):
                embed = discord.Embed(
                    title="Term Unblocked",
                    description=f"Successfully removed blocked term: ||{term}||",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
            else:
                raise commands.CommandError("Failed to save changes.")
                
        except commands.CommandError:
            raise
        except Exception as e:
            raise commands.CommandError(f"An error occurred: {str(e)}")

    @commands.command()
    @has_permissions(administrator=True)
    async def blockedterms(self, ctx):
        """List all blocked terms"""
        try:
            blocked_terms = self.load_blocked_terms()
            
            if not blocked_terms:
                embed = discord.Embed(
                    title="Blocked Terms",
                    description="No terms are currently blocked.",
                    color=discord.Color.blue()
                )
                await ctx.send(embed=embed)
                return
            
            embed = discord.Embed(
                title="Blocked Terms",
                description=f"Total blocked terms: {len(blocked_terms)}",
                color=discord.Color.blue()
            )
            
            # Group terms by punishment type
            mute_terms = []
            kick_terms = []
            ban_terms = []
            
            for term_data in blocked_terms:
                if isinstance(term_data, dict):
                    term = term_data.get('term', 'Unknown')
                    punishment = term_data.get('punishment', 'mute')
                    duration = term_data.get('duration', '10m')
                    
                    if punishment == 'mute':
                        mute_terms.append(f"||{term}|| ({duration})")
                    elif punishment == 'kick':
                        kick_terms.append(f"||{term}||")
                    elif punishment == 'ban':
                        ban_terms.append(f"||{term}||")
                else:
                    # Handle old format
                    mute_terms.append(f"||{term_data}|| (10m)")
            
            if mute_terms:
                embed.add_field(
                    name="🔇 Mute Terms",
                    value="\n".join(mute_terms[:10]) + ("\n..." if len(mute_terms) > 10 else ""),
                    inline=False
                )
            
            if kick_terms:
                embed.add_field(
                    name="👢 Kick Terms",
                    value="\n".join(kick_terms[:10]) + ("\n..." if len(kick_terms) > 10 else ""),
                    inline=False
                )
            
            if ban_terms:
                embed.add_field(
                    name="🔨 Ban Terms",
                    value="\n".join(ban_terms[:10]) + ("\n..." if len(ban_terms) > 10 else ""),
                    inline=False
                )
            
            if len(blocked_terms) > 30:
                embed.set_footer(text="Only showing first 10 terms per category. Use individual commands to manage specific terms.")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            raise commands.CommandError(f"An error occurred: {str(e)}")

    @commands.command()
    @has_permissions(administrator=True)
    async def nick(self, ctx, member: discord.Member = None, *, new_nickname = None):
        """Change a user's nickname (Admin only)
        
        Usage:
        !nick @user New Nickname - Change another user's nickname
        !nick New Nickname - Change your own nickname
        """
        # If no member is specified, use the command author
        if member is None and new_nickname is None:
            raise commands.CommandError("Please provide a nickname.")
            
        # If only one argument is provided, it's the new nickname for the author
        if new_nickname is None:
            new_nickname = str(member)
            member = ctx.author
            
        try:
            # Store the old nickname before changing
            old_nickname = member.nick or member.name
            
            # Change the nickname
            await member.edit(nick=new_nickname)
            
            # Add to nickname history
            await self.add_nickname_change(ctx.guild.id, member.id, old_nickname, new_nickname)
            
            embed = discord.Embed(
                title="Nickname Changed",
                description=f"Changed {member.mention}'s nickname to: **{new_nickname}**",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            raise commands.CommandError("I don't have permission to change that user's nickname.")
        except discord.HTTPException as e:
            raise commands.CommandError(f"Failed to change nickname: {str(e)}")

    @commands.command()
    @has_permissions(administrator=True)
    async def nickremove(self, ctx, member: discord.Member = None):
        """Remove a user's nickname (Admin only)
        
        Usage:
        !nickremove @user - Remove another user's nickname
        !nickremove - Remove your own nickname
        """
        # If no member is specified, use the command author
        if member is None:
            member = ctx.author
            
        try:
            # Store the old nickname before removing
            old_nickname = member.nick or member.name
            
            # Remove the nickname by setting it to None
            await member.edit(nick=None)
            
            # Add to nickname history
            await self.add_nickname_change(ctx.guild.id, member.id, old_nickname, None)
            
            embed = discord.Embed(
                title="Nickname Removed",
                description=f"Removed {member.mention}'s nickname. They are now displayed as: **{member.name}**",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            raise commands.CommandError("I don't have permission to change that user's nickname.")
        except discord.HTTPException as e:
            raise commands.CommandError(f"Failed to remove nickname: {str(e)}")

    @commands.command()
    @has_permissions(administrator=True)
    async def nickrevert(self, ctx, member: discord.Member = None):
        """Revert a user's nickname to their previous one (Admin only)
        
        Usage:
        !nickrevert @user - Revert another user's nickname
        !nickrevert - Revert your own nickname
        """
        # If no member is specified, use the command author
        if member is None:
            member = ctx.author
            
        try:
            # Get the previous nickname
            previous_nickname = await self.get_previous_nickname(ctx.guild.id, member.id)
            
            if previous_nickname is None:
                raise commands.CommandError(f"No previous nickname found for {member.mention}.")
                
            # Store the current nickname before changing
            current_nickname = member.nick or member.name
            
            # Change the nickname to the previous one
            await member.edit(nick=previous_nickname)
            
            # Add to nickname history
            await self.add_nickname_change(ctx.guild.id, member.id, current_nickname, previous_nickname)
            
            embed = discord.Embed(
                title="Nickname Reverted",
                description=f"Reverted {member.mention}'s nickname to: **{previous_nickname}**",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            raise commands.CommandError("I don't have permission to change that user's nickname.")
        except discord.HTTPException as e:
            raise commands.CommandError(f"Failed to revert nickname: {str(e)}")

    @nick.error
    @nickremove.error
    @nickrevert.error
    async def nickname_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="Permission Denied",
                description="You don't have permission to use this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return True
        elif isinstance(error, commands.MemberNotFound):
            embed = discord.Embed(
                title="Error",
                description="Member not found.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return True
        elif isinstance(error, commands.CommandError):
            embed = discord.Embed(
                title="Error",
                description=str(error),
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return True
        return False
        
    @commands.command()
    async def nickme(self, ctx, *, new_nickname=None):
        """Change your own nickname
        
        Usage:
        !nickme New Nickname - Change your own nickname
        """
        if new_nickname is None:
            raise commands.CommandError("Please provide a new nickname.")
            
        try:
            # Store the old nickname before changing
            old_nickname = ctx.author.nick or ctx.author.name
            
            # Change the nickname
            await ctx.author.edit(nick=new_nickname)
            
            # Add to nickname history
            await self.add_nickname_change(ctx.guild.id, ctx.author.id, old_nickname, new_nickname)
            
            embed = discord.Embed(
                title="Nickname Changed",
                description=f"Changed your nickname to: **{new_nickname}**",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            raise commands.CommandError("I don't have permission to change your nickname.")
        except discord.HTTPException as e:
            raise commands.CommandError(f"Failed to change nickname: {str(e)}")
            
    @commands.command()
    async def nickmeremove(self, ctx):
        """Remove your own nickname
        
        Usage:
        !nickmeremove - Remove your own nickname
        """
        try:
            # Store the old nickname before removing
            old_nickname = ctx.author.nick or ctx.author.name
            
            # Remove the nickname by setting it to None
            await ctx.author.edit(nick=None)
            
            # Add to nickname history
            await self.add_nickname_change(ctx.guild.id, ctx.author.id, old_nickname, None)
            
            embed = discord.Embed(
                title="Nickname Removed",
                description=f"Removed your nickname. You are now displayed as: **{ctx.author.name}**",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            raise commands.CommandError("I don't have permission to change your nickname.")
        except discord.HTTPException as e:
            raise commands.CommandError(f"Failed to remove nickname: {str(e)}")
            
    @commands.command()
    async def nickmerevert(self, ctx):
        """Revert your nickname to your previous one
        
        Usage:
        !nickmerevert - Revert your own nickname
        """
        try:
            # Get the previous nickname
            previous_nickname = await self.get_previous_nickname(ctx.guild.id, ctx.author.id)
            
            if previous_nickname is None:
                raise commands.CommandError("No previous nickname found for you.")
                
            # Store the current nickname before changing
            current_nickname = ctx.author.nick or ctx.author.name
            
            # Change the nickname to the previous one
            await ctx.author.edit(nick=previous_nickname)
            
            # Add to nickname history
            await self.add_nickname_change(ctx.guild.id, ctx.author.id, current_nickname, previous_nickname)
            
            embed = discord.Embed(
                title="Nickname Reverted",
                description=f"Reverted your nickname to: **{previous_nickname}**",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            raise commands.CommandError("I don't have permission to change your nickname.")
        except discord.HTTPException as e:
            raise commands.CommandError(f"Failed to revert nickname: {str(e)}")
            
    @nickme.error
    @nickmeremove.error
    @nickmerevert.error
    async def nickme_command_error(self, ctx, error):
        if isinstance(error, commands.CommandError):
            embed = discord.Embed(
                title="Error",
                description=str(error),
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return True
        return False
        
    async def role_save_loop(self):
        """Loop that saves roles every 6 hours"""
        await self.client.wait_until_ready()
        while not self.client.is_closed():
            try:
                # Save roles for all guilds
                for guild in self.client.guilds:
                    await self.save_roles(guild)
                
                # Update save times
                self.last_save_time = datetime.utcnow()
                self.next_save_time = self.last_save_time + timedelta(hours=6)
                self.save_role_save_info()
                
                # Wait for 6 hours
                await asyncio.sleep(6 * 60 * 60)  # 6 hours in seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in role save loop: {e}")
                # Wait a bit before retrying if there was an error
                await asyncio.sleep(300)  # 5 minutes

    async def save_roles(self, guild):
        """Save roles for all members in a guild"""
        try:
            # Load existing saved roles if any
            saved_roles = {}
            if os.path.exists(self.roles_file):
                with open(self.roles_file, 'r') as f:
                    saved_roles = json.load(f)
            
            # Initialize guild section if not exists
            if str(guild.id) not in saved_roles:
                saved_roles[str(guild.id)] = {}
            
            # Save roles for each member
            for member in guild.members:
                # Skip bots
                if member.bot:
                    continue
                    
                # Save role IDs for the member
                role_ids = [role.id for role in member.roles if role.id != guild.default_role.id]
                saved_roles[str(guild.id)][str(member.id)] = role_ids
            
            # Save to file
            with open(self.roles_file, 'w') as f:
                json.dump(saved_roles, f, indent=2)
                
            return True
        except Exception as e:
            print(f"Error saving roles: {e}")
            return False

    def load_role_save_info(self):
        """Load role save timing information"""
        try:
            if os.path.exists(self.roles_info_file):
                with open(self.roles_info_file, 'r') as f:
                    info = json.load(f)
                    
                if 'last_save' in info:
                    self.last_save_time = datetime.fromisoformat(info['last_save'])
                if 'next_save' in info:
                    self.next_save_time = datetime.fromisoformat(info['next_save'])
        except Exception as e:
            print(f"Error loading role save info: {e}")
            # Set default times if loading fails
            self.last_save_time = None
            self.next_save_time = datetime.utcnow() + timedelta(hours=6)

    def save_role_save_info(self):
        """Save role save timing information"""
        try:
            info = {
                'last_save': self.last_save_time.isoformat() if self.last_save_time else None,
                'next_save': self.next_save_time.isoformat() if self.next_save_time else None
            }
            
            with open(self.roles_info_file, 'w') as f:
                json.dump(info, f, indent=2)
        except Exception as e:
            print(f"Error saving role save info: {e}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Restore roles when a member rejoins the server"""
        # Skip bots
        if member.bot:
            return
            
        try:
            # Check if we have saved roles for this member
            if not os.path.exists(self.roles_file):
                return
                
            with open(self.roles_file, 'r') as f:
                saved_roles = json.load(f)
            
            guild_id = str(member.guild.id)
            member_id = str(member.id)
            
            # Check if we have roles saved for this member in this guild
            if guild_id in saved_roles and member_id in saved_roles[guild_id]:
                role_ids = saved_roles[guild_id][member_id]
                
                # Get valid roles that still exist in the server
                roles_to_add = []
                for role_id in role_ids:
                    role = member.guild.get_role(int(role_id))
                    if role and not role.managed:  # Skip managed roles (bots, integrations)
                        roles_to_add.append(role)
                
                # Add roles if any
                if roles_to_add:
                    await member.add_roles(*roles_to_add, reason="Restoring saved roles")
                    
                    # Log in system channel if available
                    system_channel = member.guild.system_channel
                    if system_channel:
                        role_mentions = [role.mention for role in roles_to_add]
                        role_list = ", ".join(role_mentions) if role_mentions else "None"
                        
                        embed = discord.Embed(
                            title="Roles Restored",
                            description=f"Restored roles for {member.mention}: {role_list}",
                            color=discord.Color.green()
                        )
                        await system_channel.send(embed=embed)
        except Exception as e:
            print(f"Error restoring roles: {e}")

    @commands.command()
    @has_permissions(administrator=True)
    async def saveroles(self, ctx, option: str = None):
        """Save roles for all members or show save info
        
        Usage:
        !saveroles - Save roles now
        !saveroles info - Show last and next save times
        """
        if option and option.lower() == "info":
            # Show save info
            if not self.last_save_time:
                last_save_str = "Never"
            else:
                # Format as relative time
                time_diff = datetime.utcnow() - self.last_save_time
                hours, remainder = divmod(time_diff.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                if time_diff.days > 0:
                    last_save_str = f"{time_diff.days} days, {hours} hours ago"
                elif hours > 0:
                    last_save_str = f"{hours} hours, {minutes} minutes ago"
                else:
                    last_save_str = f"{minutes} minutes ago"
            
            if not self.next_save_time:
                next_save_str = "Not scheduled"
            else:
                # Format as relative time
                time_diff = self.next_save_time - datetime.utcnow()
                hours, remainder = divmod(time_diff.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                if time_diff.days > 0:
                    next_save_str = f"In {time_diff.days} days, {hours} hours"
                elif hours > 0:
                    next_save_str = f"In {hours} hours, {minutes} minutes"
                else:
                    next_save_str = f"In {minutes} minutes"
            
            embed = discord.Embed(
                title="Role Save Information",
                description="Status of the automatic role saving system",
                color=discord.Color.blue()
            )
            embed.add_field(name="Last Save", value=last_save_str, inline=False)
            embed.add_field(name="Next Save", value=next_save_str, inline=False)
            
            await ctx.send(embed=embed)
        else:
            # Save roles now
            status_msg = await ctx.send(embed=discord.Embed(
                title="Saving Roles",
                description="Saving roles for all members...",
                color=discord.Color.blue()
            ))
            
            success = await self.save_roles(ctx.guild)
            
            if success:
                # Update save times
                self.last_save_time = datetime.utcnow()
                self.next_save_time = self.last_save_time + timedelta(hours=6)
                self.save_role_save_info()
                
                await status_msg.edit(embed=discord.Embed(
                    title="Roles Saved",
                    description=f"Successfully saved roles for all members in {ctx.guild.name}",
                    color=discord.Color.green()
                ))
            else:
                await status_msg.edit(embed=discord.Embed(
                    title="Error",
                    description="Failed to save roles. Check console for details.",
                    color=discord.Color.red()
                ))

    @saveroles.error
    async def saveroles_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="Permission Denied",
                description="You don't have permission to use this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return True
        elif isinstance(error, commands.CommandError):
            embed = discord.Embed(
                title="Error",
                description=str(error),
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return True
        return False

    @commands.command()
    @has_permissions(administrator=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        """Ban a member from the server"""
        await member.ban(reason=reason)
        embed = discord.Embed(
            title="Ban",
            description=f"{member.mention} has been banned.\nReason: {reason or 'No reason provided'}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

    @commands.command()
    @has_permissions(administrator=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        """Kick a member from the server"""
        await member.kick(reason=reason)
        embed = discord.Embed(
            title="Kick",
            description=f"{member.mention} has been kicked.\nReason: {reason or 'No reason provided'}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

    @commands.command()
    @has_permissions(administrator=True)
    async def mute(self, ctx, member: discord.Member, duration: str = "10m", *, reason=None):
        """Mute a member for a specified duration (e.g., '60s' for seconds, '10m' for minutes)"""
        muted_role = await self.get_or_create_muted_role(ctx)
        if muted_role in member.roles:
            raise commands.CommandError(f"{member.mention} is already muted.")
        
        await self.apply_mute(ctx, member, muted_role, duration, reason)

    async def get_or_create_muted_role(self, ctx):
        """Retrieve or create the 'Muted' role."""
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not muted_role:
            muted_role = await ctx.guild.create_role(name="Muted")
            for channel in ctx.guild.channels:
                await channel.set_permissions(muted_role, speak=False, send_messages=False)
        return muted_role

    async def apply_mute(self, ctx, member, muted_role, duration, reason):
        """Apply the mute to the member."""
        await member.add_roles(muted_role)
        embed = discord.Embed(
            title="Mute",
            description=f"{member.mention} has been muted for {duration}.\nReason: {reason or 'No reason provided'}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        
        asyncio.create_task(self.schedule_unmute(ctx, member, muted_role, duration))

    async def schedule_unmute(self, ctx, member, muted_role, duration):
        """Schedule the unmute after the specified duration."""
        if duration.endswith('s'):
            duration_seconds = int(duration[:-1])
        elif duration.endswith('m'):
            duration_seconds = int(duration[:-1]) * 60
        elif duration.endswith('h'):
            duration_seconds = int(duration[:-1]) * 3600
        elif duration.endswith('d'):
            duration_seconds = int(duration[:-1]) * 86400
        else:
            try:
                duration_seconds = int(duration) * 60
            except ValueError:
                raise commands.CommandError(f"Invalid duration format: {duration}. Use formats like '30s', '10m', '1h', or '1d'.")
        
        await asyncio.sleep(duration_seconds)
        
        try:
            member = await ctx.guild.fetch_member(member.id)
        except discord.NotFound:
            return  # Member left the server, no need to unmute
            
        if muted_role in member.roles:
            await member.remove_roles(muted_role)
            unmute_embed = discord.Embed(
                title="Unmute",
                description=f"{member.mention} has been automatically unmuted.",
                color=discord.Color.green()
            )
            await ctx.send(embed=unmute_embed)
            
    @commands.command()
    @has_permissions(administrator=True)
    async def unmute(self, ctx, member: discord.Member):
        """Unmute a member"""
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if muted_role and muted_role in member.roles:
            await member.remove_roles(muted_role)
            embed = discord.Embed(
                title="Unmute",
                description=f"{member.mention} has been unmuted.",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            raise commands.CommandError(f"{member.mention} is not muted.")

    @commands.command()
    @has_permissions(administrator=True)
    async def addbalance(self, ctx, member: discord.Member, amount: int):
        """Add balance to a user's account"""
        economy_cog = self.client.get_cog("EconomyCog")
        if economy_cog:
            await economy_cog.add_balance(member.id, amount)
            embed = discord.Embed(
                title="Balance Added",
                description=f"Added {amount} coins to {member.mention}'s balance.",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            raise commands.CommandError("Economy system is not available.")

    @commands.command()
    @has_permissions(administrator=True)
    async def removebalance(self, ctx, member: discord.Member, amount: int):
        """Remove balance from a user's account"""
        economy_cog = self.client.get_cog("EconomyCog")
        if economy_cog:
            await economy_cog.remove_balance(member.id, amount)
            embed = discord.Embed(
                title="Balance Removed",
                description=f"Removed {amount} coins from {member.mention}'s balance.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        else:
            raise commands.CommandError("Economy system is not available.")

    @commands.command()
    @has_permissions(administrator=True)
    async def grant(self, ctx, member: discord.Member, time: str = None):
        """Grant a special role to a user for a specified duration (e.g., '30s', '5m', '2h', '7d') or permanently if no time specified"""
        try:
            role = ctx.guild.get_role(1225863450308378644)
            if not role:
                raise commands.CommandError("The specified role could not be found.")

            # If no time specified or 'perm'/'permanent', make it permanent
            if not time or time.lower() in ['perm', 'permanent']:
                duration_seconds = None
                time_str = "permanently"
            else:
                # Regular expression to parse time format
                time_pattern = re.compile(r'(\d+)([smhd])')
                match = time_pattern.match(time.lower())
                
                if not match:
                    raise commands.CommandError("Invalid time format. Use numbers followed by s/m/h/d (e.g., 30s, 5m, 2h, 7d) or no time for permanent.")
                    
                amount = int(match.group(1))
                unit = match.group(2)
                
                # Convert to seconds
                multipliers = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
                duration_seconds = amount * multipliers[unit]
                
                # Create human-readable time string
                units = {'s': 'seconds', 'm': 'minutes', 'h': 'hours', 'd': 'days'}
                time_str = f"for {amount} {units[unit]}"

            # Add role
            await member.add_roles(role)
            
            embed = discord.Embed(
                title="Role Granted",
                description=f"Granted {role.mention} to {member.mention} {time_str}.",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
            
            # If not permanent, schedule role removal
            if duration_seconds is not None:
                await asyncio.sleep(duration_seconds)
                try:
                    member = await ctx.guild.fetch_member(member.id)
                    if role in member.roles:  # Check if user still has the role
                        await member.remove_roles(role)
                        embed = discord.Embed(
                            title="Role Expired",
                            description=f"Removed {role.mention} from {member.mention} (Duration expired).",
                            color=discord.Color.blue()
                        )
                        await ctx.send(embed=embed)
                except discord.NotFound:
                    # Member left the server
                    pass
                    
        except discord.Forbidden:
            raise commands.CommandError("I don't have permission to manage roles.")

    @commands.command()
    @has_permissions(administrator=True)
    async def ungrant(self, ctx, member: discord.Member, time: str = None):
        """Temporarily remove the special role from a user for specified duration (e.g., '30s', '5m', '2h', '7d') or permanently if no time specified"""
        try:
            role = ctx.guild.get_role(1225863450308378644)
            if not role:
                raise commands.CommandError("The specified role could not be found.")

            if not role in member.roles:
                raise commands.CommandError(f"{member.mention} doesn't have the role to remove.")

            # If no time specified, remove permanently
            if not time:
                await member.remove_roles(role)
                embed = discord.Embed(
                    title="Role Removed",
                    description=f"Removed {role.mention} from {member.mention} permanently.",
                    color=discord.Color.blue()
                )
                await ctx.send(embed=embed)
                return

            # Parse time for temporary removal
            time_pattern = re.compile(r'(\d+)([smhd])')
            match = time_pattern.match(time.lower())
            
            if not match:
                raise commands.CommandError("Invalid time format. Use numbers followed by s/m/h/d (e.g., 30s, 5m, 2h, 7d) or no time for permanent removal.")
                
            amount = int(match.group(1))
            unit = match.group(2)
            
            # Convert to seconds
            multipliers = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
            duration_seconds = amount * multipliers[unit]
            
            # Create human-readable time string
            units = {'s': 'seconds', 'm': 'minutes', 'h': 'hours', 'd': 'days'}
            time_str = f"for {amount} {units[unit]}"

            # Remove the role
            await member.remove_roles(role)
            embed = discord.Embed(
                title="Role Temporarily Removed",
                description=f"Removed {role.mention} from {member.mention} {time_str}.",
                color=discord.Color.yellow()
            )
            await ctx.send(embed=embed)
            
            # Schedule role restoration
            await asyncio.sleep(duration_seconds)
            try:
                member = await ctx.guild.fetch_member(member.id)
                if not role in member.roles:  # Only add if they don't already have it
                    await member.add_roles(role)
                    embed = discord.Embed(
                        title="Role Restored",
                        description=f"Restored {role.mention} to {member.mention} (Temporary removal period ended).",
                        color=discord.Color.green()
                    )
                    await ctx.send(embed=embed)
            except discord.NotFound:
                # Member left the server
                pass
                    
        except discord.Forbidden:
            raise commands.CommandError("I don't have permission to manage roles.")

    @commands.command()
    @has_permissions(administrator=True)
    async def clear(self, ctx, amount: int):
        """Clear a specified number of messages from the channel"""
        try:
            # Add 1 to include the command message itself
            amount = amount + 1
            
            # Check if amount is within Discord's limits
            if amount > 100:
                raise commands.CommandError("Cannot delete more than 99 messages at once.")
            elif amount < 1:
                raise commands.CommandError("Please specify a positive number of messages to delete.")
                
            # Delete messages
            deleted = await ctx.channel.purge(limit=amount)
            
            # Send confirmation message
            confirm_msg = await ctx.send(embed=discord.Embed(
                title="Messages Cleared",
                description=f"Deleted {len(deleted)-1} messages.",
                color=discord.Color.green()
            ))
            
            # Delete confirmation message after 1 second
            await asyncio.sleep(1)
            await confirm_msg.delete()
            
        except discord.Forbidden:
            raise commands.CommandError("I don't have permission to delete messages.")
        except discord.HTTPException as e:
            raise commands.CommandError(f"Failed to delete messages: {str(e)}")

    @commands.command()
    @has_permissions(administrator=True)
    async def jail(self, ctx, member: discord.Member, time: str = None):
        """Jail a user for a specified duration (e.g., '30s', '5m', '2h', '7d') or permanently if no time specified"""
        try:
            role = ctx.guild.get_role(1211618366763044874)
            if not role:
                raise commands.CommandError("The jail role could not be found.")

            # If no time specified or 'perm'/'permanent', make it permanent
            if not time or time.lower() in ['perm', 'permanent']:
                duration_seconds = None
                time_str = "permanently"
            else:
                # Regular expression to parse time format
                time_pattern = re.compile(r'(\d+)([smhd])')
                match = time_pattern.match(time.lower())
                
                if not match:
                    raise commands.CommandError("Invalid time format. Use numbers followed by s/m/h/d (e.g., 30s, 5m, 2h, 7d) or no time for permanent.")
                    
                amount = int(match.group(1))
                unit = match.group(2)
                
                # Convert to seconds
                multipliers = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
                duration_seconds = amount * multipliers[unit]
                
                # Create human-readable time string
                units = {'s': 'seconds', 'm': 'minutes', 'h': 'hours', 'd': 'days'}
                time_str = f"for {amount} {units[unit]}"

            # Add role
            await member.add_roles(role)
            
            embed = discord.Embed(
                title="User Jailed",
                description=f"Jailed {member.mention} {time_str}.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            
            # If not permanent, schedule role removal
            if duration_seconds is not None:
                await asyncio.sleep(duration_seconds)
                try:
                    member = await ctx.guild.fetch_member(member.id)
                    if role in member.roles:  # Check if user still has the role
                        await member.remove_roles(role)
                        embed = discord.Embed(
                            title="Jail Time Ended",
                            description=f"Released {member.mention} from jail (Time served).",
                            color=discord.Color.green()
                        )
                        await ctx.send(embed=embed)
                except discord.NotFound:
                    # Member left the server
                    pass
                    
        except discord.Forbidden:
            raise commands.CommandError("I don't have permission to manage roles.")

    @commands.command()
    @has_permissions(administrator=True)
    async def unjail(self, ctx, member: discord.Member, time: str = None):
        """Temporarily release a user from jail for specified duration (e.g., '30s', '5m', '2h', '7d') or permanently if no time specified"""
        try:
            role = ctx.guild.get_role(1211618366763044874)
            if not role:
                raise commands.CommandError("The jail role could not be found.")

            if not role in member.roles:
                raise commands.CommandError(f"{member.mention} is not jailed.")

            # If no time specified, remove permanently
            if not time:
                await member.remove_roles(role)
                embed = discord.Embed(
                    title="User Released",
                    description=f"Released {member.mention} from jail permanently.",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
                return

            # Parse time for temporary release
            time_pattern = re.compile(r'(\d+)([smhd])')
            match = time_pattern.match(time.lower())
            
            if not match:
                raise commands.CommandError("Invalid time format. Use numbers followed by s/m/h/d (e.g., 30s, 5m, 2h, 7d) or no time for permanent release.")
                
            amount = int(match.group(1))
            unit = match.group(2)
            
            # Convert to seconds
            multipliers = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
            duration_seconds = amount * multipliers[unit]
            
            # Create human-readable time string
            units = {'s': 'seconds', 'm': 'minutes', 'h': 'hours', 'd': 'days'}
            time_str = f"for {amount} {units[unit]}"

            # Remove the role
            await member.remove_roles(role)
            embed = discord.Embed(
                title="Temporary Release",
                description=f"Released {member.mention} from jail {time_str}.",
                color=discord.Color.yellow()
            )
            await ctx.send(embed=embed)
            
            # Schedule return to jail
            await asyncio.sleep(duration_seconds)
            try:
                member = await ctx.guild.fetch_member(member.id)
                if not role in member.roles:  # Only add if they don't already have it
                    await member.add_roles(role)
                    embed = discord.Embed(
                        title="Return to Jail",
                        description=f"Returned {member.mention} to jail (Temporary release period ended).",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=embed)
            except discord.NotFound:
                # Member left the server
                pass
                    
        except discord.Forbidden:
            raise commands.CommandError("I don't have permission to manage roles.")

    @commands.command()
    @has_permissions(administrator=True)
    async def cclear(self, ctx, *args):
        """Clear messages containing specific text. Usage:
        cclear [text] - Search in all channels
        cclear -current [text] - Search only in current channel
        cclear [@user] [text] - Search messages from specific user
        cclear -scan - Scan and cache all messages
        cclear -p [percentage] [text] - Delete only specified percentage of matches
        cclear yes/no - Confirm or cancel pending deletion"""
        
        if not args:
            raise commands.CommandError("Please provide search text or yes/no for confirmation.")

        # Handle scan command
        if args[0] == '-scan':
            return await self.scan_all_messages(ctx)

        # Handle confirmation responses
        if args[0].lower() in ['yes', 'no']:
            return await self.handle_cclear_confirmation(ctx, args[0].lower())

        # Check if we have a recent cache
        if not self.is_cache_recent():
            await ctx.send(embed=discord.Embed(
                title="Cache Not Found or Outdated",
                description="Message cache is outdated or doesn't exist. Please run `cclear -scan` first.",
                color=discord.Color.red()
            ))
            return

        # Parse arguments
        target_user = None
        current_channel_only = False
        search_text = ""
        percentage = 100  # Default to 100%

        # Handle percentage flag
        if args[0] in ['-p', '-%']:
            if len(args) < 3:
                raise commands.CommandError("Please provide percentage and search text after -p flag.")
            try:
                percentage = float(args[1].strip('%'))  # Remove % if present
                if not 0 < percentage <= 100:
                    raise ValueError
                args = args[2:]  # Remove percentage arguments
            except ValueError:
                raise commands.CommandError("Percentage must be a number between 0 and 100.")
        
        if args[0] == '-current':
            if len(args) < 2:
                raise commands.CommandError("Please provide search text after -current flag.")
            current_channel_only = True
            search_text = ' '.join(args[1:])
        elif args[0].startswith('<@') and args[0].endswith('>'):
            if len(args) < 2:
                raise commands.CommandError("Please provide search text after user mention.")
            try:
                target_user = await commands.MemberConverter().convert(ctx, args[0])
                search_text = ' '.join(args[1:])
            except:
                raise commands.CommandError("Invalid user mention.")
        else:
            search_text = ' '.join(args)

        # Search in cached messages
        messages_to_delete = await self.search_cached_messages(ctx, search_text, current_channel_only, target_user)

        if not messages_to_delete:
            raise commands.CommandError(f"No messages found containing '{search_text}'")

        # Apply percentage if less than 100%
        if percentage < 100:
            # Calculate how many messages to keep and take the first N%
            messages_to_keep = int(len(messages_to_delete) * (percentage / 100))
            messages_to_delete = messages_to_delete[:messages_to_keep]

        # Store the pending operation
        self.pending_cclear[ctx.author.id] = {
            'messages': messages_to_delete,
            'search_text': search_text,
            'timestamp': ctx.message.created_at,
            'percentage': percentage
        }

        # Send confirmation message
        embed = discord.Embed(
            title="Confirm Message Deletion",
            description=f"Found {len(messages_to_delete)} messages containing '{search_text}'\n"
                      f"Will delete {percentage}% ({len(messages_to_delete)} messages)\n"
                      f"Type `cclear yes` to confirm deletion or `cclear no` to cancel.",
            color=discord.Color.yellow()
        )
        await ctx.send(embed=embed)

    async def scan_all_messages(self, ctx):
        """Scan and cache all messages in the server"""
        status_msg = await ctx.send(embed=discord.Embed(
            title="Scanning Messages",
            description="Starting scan... This might take a while.",
            color=discord.Color.blue()
        ))

        cached_messages = []
        channels_to_scan = ctx.guild.text_channels
        total_channels = len(channels_to_scan)
        processed_channels = 0
        total_messages = 0

        # Clear existing index
        self.word_index.clear()

        for channel in channels_to_scan:
            try:
                processed_channels += 1
                await status_msg.edit(embed=discord.Embed(
                    title="Scanning Messages",
                    description=f"Channel {processed_channels}/{total_channels}: {channel.name}\n"
                              f"Total messages scanned: {total_messages}",
                    color=discord.Color.blue()
                ))

                async for message in channel.history(limit=None):
                    total_messages += 1
                    
                    # Update progress every 100 messages
                    if total_messages % 100 == 0:
                        await status_msg.edit(embed=discord.Embed(
                            title="Scanning Messages",
                            description=f"Channel {processed_channels}/{total_channels}: {channel.name}\n"
                                      f"Total messages scanned: {total_messages}",
                            color=discord.Color.blue()
                        ))

                    # Cache message data
                    message_data = {
                        'content': message.content,
                        'channel_id': channel.id,
                        'message_id': message.id,
                        'author_id': message.author.id,
                        'timestamp': message.created_at.isoformat()
                    }
                    
                    # Add to cached messages
                    msg_index = len(cached_messages)
                    cached_messages.append(message_data)
                    
                    # Index words for faster searching
                    words = set(message.content.lower().split())  # Using set to avoid duplicate words
                    for word in words:
                        self.word_index[word].append(msg_index)

            except discord.Forbidden:
                await status_msg.edit(embed=discord.Embed(
                    title="Scanning Messages",
                    description=f"Skipped channel {channel.name} (No access)\n"
                              f"Total messages scanned: {total_messages}",
                    color=discord.Color.blue()
                ))
                continue
            except Exception as e:
                await ctx.send(f"Error in channel {channel.name}: {str(e)}")
                continue

        # Save to cache files
        try:
            # Save messages
            with open(self.message_cache_file, 'w', encoding='utf-8') as f:
                json.dump(cached_messages, f, ensure_ascii=False, indent=2)
            
            # Save word index
            with open(self.message_index_file, 'w', encoding='utf-8') as f:
                json.dump(dict(self.word_index), f, ensure_ascii=False, indent=2)
            
            # Save scan timestamp
            with open(self.last_scan_file, 'w') as f:
                f.write(datetime.utcnow().isoformat())

            await status_msg.edit(embed=discord.Embed(
                title="Scan Complete",
                description=f"Successfully cached {total_messages} messages from {total_channels} channels.\n"
                          f"Created search index with {len(self.word_index)} unique words.",
                color=discord.Color.green()
            ))
        except Exception as e:
            await ctx.send(f"Error saving cache: {str(e)}")

    def load_cache(self):
        """Load cache files into memory"""
        try:
            # Load messages
            with open(self.message_cache_file, 'r', encoding='utf-8') as f:
                cached_messages = json.load(f)
            
            # Load word index
            with open(self.message_index_file, 'r', encoding='utf-8') as f:
                self.word_index = defaultdict(list, json.load(f))
            
            return cached_messages
        except:
            raise commands.CommandError("Error reading cache files. Please run `cclear -scan` again.")

    async def search_cached_messages(self, ctx, search_text, current_channel_only, target_user):
        """Search through cached messages using the word index"""
        status_msg = await ctx.send(embed=discord.Embed(
            title="Searching Messages",
            description="Reading cache files...",
            color=discord.Color.blue()
        ))

        try:
            cached_messages = self.load_cache()
        except Exception as e:
            await status_msg.delete()
            raise e

        messages_to_delete = []
        search_words = search_text.lower().split()
        
        # Get potential message indices from the word index
        potential_indices = set()
        if search_words:
            # Start with indices from the first word
            potential_indices = set(self.word_index[search_words[0]])
            # Intersect with indices from other words
            for word in search_words[1:]:
                potential_indices &= set(self.word_index[word])
        
        await status_msg.edit(embed=discord.Embed(
            title="Searching Messages",
            description=f"Found {len(potential_indices)} potential matches. Verifying...",
            color=discord.Color.blue()
        ))

        # Verify matches and fetch messages
        for msg_index in potential_indices:
            msg_data = cached_messages[msg_index]
            
            # Check channel filter
            if current_channel_only and msg_data['channel_id'] != ctx.channel.id:
                continue

            # Check user filter
            if target_user and msg_data['author_id'] != target_user.id:
                continue

            # Double check content (for partial word matches)
            if search_text.lower() in msg_data['content'].lower():
                try:
                    channel = ctx.guild.get_channel(msg_data['channel_id'])
                    if channel:
                        message = await channel.fetch_message(msg_data['message_id'])
                        messages_to_delete.append(message)
                except:
                    continue

        await status_msg.delete()
        return messages_to_delete

    async def handle_cclear_confirmation(self, ctx, response):
        """Handle the confirmation response for cclear command"""
        if ctx.author.id not in self.pending_cclear:
            raise commands.CommandError("No pending clear operation. Please start a new search.")

        pending = self.pending_cclear[ctx.author.id]
        
        # Check if the confirmation has expired (5 minutes)
        if (ctx.message.created_at - pending['timestamp']).total_seconds() > 300:
            del self.pending_cclear[ctx.author.id]
            raise commands.CommandError("Confirmation expired. Please start a new search.")

        if response == 'no':
            del self.pending_cclear[ctx.author.id]
            embed = discord.Embed(
                title="Operation Cancelled",
                description="Message deletion cancelled.",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
            return

        # Process deletion
        total_messages = len(pending['messages'])
        deleted_count = 0
        failed_count = 0
        
        status_msg = await ctx.send(embed=discord.Embed(
            title="Deleting Messages",
            description=f"Starting deletion of {total_messages} messages...",
            color=discord.Color.blue()
        ))

        # Group messages by channel for bulk deletion
        messages_by_channel = {}
        for message in pending['messages']:
            if message.channel.id not in messages_by_channel:
                messages_by_channel[message.channel.id] = {
                    'channel': message.channel,
                    'recent': [],  # Messages < 14 days old
                    'old': []      # Messages > 14 days old
                }
            
            # Check if message is less than 14 days old
            if (ctx.message.created_at - message.created_at).days < 14:
                messages_by_channel[message.channel.id]['recent'].append(message)
            else:
                messages_by_channel[message.channel.id]['old'].append(message)

        # Process each channel
        for channel_data in messages_by_channel.values():
            channel = channel_data['channel']
            recent_messages = channel_data['recent']
            old_messages = channel_data['old']

            # Bulk delete recent messages in chunks of 100
            if recent_messages:
                chunks = [recent_messages[i:i + 100] for i in range(0, len(recent_messages), 100)]
                for chunk in chunks:
                    try:
                        await channel.delete_messages(chunk)
                        deleted_count += len(chunk)
                        
                        # Update status every chunk
                        await status_msg.edit(embed=discord.Embed(
                            title="Deleting Messages",
                            description=f"Progress: {deleted_count + failed_count}/{total_messages}\n"
                                      f"Successfully deleted: {deleted_count}\n"
                                      f"Failed: {failed_count}",
                            color=discord.Color.blue()
                        ))
                        
                        # Small delay between chunks to avoid rate limits
                        await asyncio.sleep(1)
                    except Exception as e:
                        failed_count += len(chunk)

            # Delete old messages individually (can't bulk delete)
            if old_messages:
                for i, message in enumerate(old_messages):
                    try:
                        await message.delete()
                        deleted_count += 1
                        
                        # Update status every 20 messages for old messages
                        if (i + 1) % 20 == 0:
                            await status_msg.edit(embed=discord.Embed(
                                title="Deleting Messages",
                                description=f"Progress: {deleted_count + failed_count}/{total_messages}\n"
                                          f"Successfully deleted: {deleted_count}\n"
                                          f"Failed: {failed_count}",
                                color=discord.Color.blue()
                            ))
                    except:
                        failed_count += 1

                    # Only add delay every 5 messages for old messages
                    if (i + 1) % 5 == 0:
                        await asyncio.sleep(1)

        del self.pending_cclear[ctx.author.id]
        await status_msg.delete()

        # Send completion message
        embed = discord.Embed(
            title="Messages Deleted",
            description=f"Successfully deleted {deleted_count} messages.\n"
                      f"Failed to delete {failed_count} messages.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    def is_cache_recent(self):
        """Check if cache exists and is less than 24 hours old"""
        try:
            if not os.path.exists(self.last_scan_file) or not os.path.exists(self.message_cache_file):
                return False

            with open(self.last_scan_file, 'r') as f:
                last_scan = datetime.fromisoformat(f.read().strip())
                
            # Check if cache is less than 24 hours old
            return (datetime.utcnow() - last_scan).total_seconds() < 86400
        except:
            return False

    @ban.error
    @kick.error
    @mute.error
    @unmute.error
    @addbalance.error
    @removebalance.error
    @grant.error
    @ungrant.error
    @jail.error
    @unjail.error
    @clear.error
    @cclear.error
    @blockterm.error
    @unblockterm.error
    @blockedterms.error
    async def admin_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="Permission Denied",
                description="You don't have permission to use this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return True  # Signal that we handled this error
        elif isinstance(error, commands.MemberNotFound):
            embed = discord.Embed(
                title="Error",
                description="Member not found.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return True  # Signal that we handled this error
        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="Error",
                description="Please provide a valid number of messages to delete.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return True
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="Error",
                description="Please specify the number of messages to delete.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return True
        elif isinstance(error, commands.CommandError):
            embed = discord.Embed(
                title="Error",
                description=str(error),
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return True  # Signal that we handled this error
        return False  # Signal that we did not handle this error

async def setup(client):
    await client.add_cog(AdminCog(client))