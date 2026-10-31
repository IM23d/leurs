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
        
        # Auto reactions file path
        self.reactions_file = self.data_dir / "auto_reactions.json"
        
        # Reaction roles file path
        self.reaction_roles_file = self.data_dir / "reaction_roles.json"
        
        # Warnings file path
        self.warnings_file = self.data_dir / "warnings.json"
        
        # User actions file path
        self.user_actions_file = self.data_dir / "user_actions.json"
        
        # Initialize role saving task
        self.role_save_task = None
        self.last_save_time = None
        self.next_save_time = None
        
        # Load role save info if exists
        self.load_role_save_info()
        
        # Initialize nickname history
        self.load_nickname_history()
        
        # Initialize auto reactions
        self.auto_reactions = self.load_auto_reactions()
        
        # Initialize reaction roles
        self.reaction_roles = self.load_reaction_roles()
        
        # Initialize warnings
        self.warnings = self.load_warnings()
        
        # Initialize user actions
        self.user_actions = self.load_user_actions()

    def cog_unload(self):
        # Cancel the role save task when the cog is unloaded
        if self.role_save_task:
            self.role_save_task.cancel()
            
    async def cog_load(self):
        # Start the role save task when the cog is loaded
        self.role_save_task = self.client.loop.create_task(self.role_save_loop())

    # Load user actions from file
    def load_user_actions(self):
        try:
            if os.path.exists(self.user_actions_file):
                with open(self.user_actions_file, 'r') as f:
                    return json.load(f)
            else:
                # Create empty user actions file
                with open(self.user_actions_file, 'w') as f:
                    json.dump({}, f)
                return {}
        except Exception as e:
            print(f"Error loading user actions: {e}")
            return {}
            
    # Save user actions to file
    def save_user_actions(self):
        try:
            with open(self.user_actions_file, 'w') as f:
                json.dump(self.user_actions, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving user actions: {e}")
            return False
            
    # Add action to user history
    async def add_user_action(self, guild_id, user_id, action_type, reason=None, duration=None):
        try:
            # Load current actions
            if not self.user_actions:
                self.user_actions = self.load_user_actions()
            
            # Initialize guild section if not exists
            guild_id_str = str(guild_id)
            if guild_id_str not in self.user_actions:
                self.user_actions[guild_id_str] = {}
                
            # Initialize user section if not exists
            user_id_str = str(user_id)
            if user_id_str not in self.user_actions[guild_id_str]:
                self.user_actions[guild_id_str][user_id_str] = []
                
            # Add new action with timestamp
            action = {
                "action": action_type,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if reason:
                action["reason"] = reason
                
            if duration:
                action["duration"] = duration
                
            self.user_actions[guild_id_str][user_id_str].append(action)
            
            # Save updated actions
            self.save_user_actions()
            return True
        except Exception as e:
            print(f"Error adding user action: {e}")
            return False

    # Load warnings from file
    def load_warnings(self):
        try:
            if os.path.exists(self.warnings_file):
                with open(self.warnings_file, 'r') as f:
                    return json.load(f)
            else:
                # Create empty warnings file
                with open(self.warnings_file, 'w') as f:
                    json.dump({}, f)
                return {}
        except Exception as e:
            print(f"Error loading warnings: {e}")
            return {}
            
    # Save warnings to file
    def save_warnings(self):
        try:
            with open(self.warnings_file, 'w') as f:
                json.dump(self.warnings, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving warnings: {e}")
            return False
            
    # Add warning to history
    async def add_warning(self, guild_id, user_id, reason):
        try:
            # Load current warnings
            if not self.warnings:
                self.warnings = self.load_warnings()
            
            # Initialize guild section if not exists
            guild_id_str = str(guild_id)
            if guild_id_str not in self.warnings:
                self.warnings[guild_id_str] = {}
                
            # Initialize user section if not exists
            user_id_str = str(user_id)
            if user_id_str not in self.warnings[guild_id_str]:
                self.warnings[guild_id_str][user_id_str] = []
                
            # Add new warning with timestamp
            self.warnings[guild_id_str][user_id_str].append({
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Save updated warnings
            self.save_warnings()
            return True
        except Exception as e:
            print(f"Error adding warning: {e}")
            return False

    @commands.command()
    @has_permissions(administrator=True)
    async def warn(self, ctx, member: discord.Member, *, reason=None):
        if reason is None:
            reason = "No reason provided"
            
        try:
            # Add warning to history
            await self.add_warning(ctx.guild.id, member.id, reason)
            
            # Add to user actions - REMOVED to prevent double counting
            # await self.add_user_action(ctx.guild.id, member.id, "warn", reason)
            
            # Create DM embed
            dm_embed = discord.Embed(
                title="Warning",
                description=f"You have been warned in **{ctx.guild.name}**",
                color=discord.Color.yellow()
            )
            dm_embed.add_field(name="Reason", value=reason, inline=False)
            dm_embed.set_footer(text=f"Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
            
            # Send DM to user
            try:
                await member.send(embed=dm_embed)
                dm_sent = True
            except discord.Forbidden:
                dm_sent = False
                
            # Create confirmation embed for the channel
            channel_embed = discord.Embed(
                title="User Warned",
                description=f"{member.mention} has been warned.",
                color=discord.Color.yellow()
            )
            channel_embed.add_field(name="Reason", value=reason, inline=False)
            
            if not dm_sent:
                channel_embed.add_field(name="Note", value="Could not send DM to user (DMs disabled)", inline=False)
                
            await ctx.send(embed=channel_embed)
            
        except Exception as e:
            raise commands.CommandError(f"Failed to warn user: {str(e)}")

    @commands.command(aliases=["o"])
    @has_permissions(administrator=True)
    async def overview(self, ctx, member: discord.Member):

        try:
            guild_id_str = str(ctx.guild.id)
            user_id_str = str(member.id)
            
            # Create embed
            embed = discord.Embed(
                title=f"User Overview: {member.display_name}",
                description=f"History of admin actions for {member.mention}",
                color=discord.Color.blue()
            )
            
            # Add user info
            embed.add_field(name="User ID", value=member.id, inline=True)
            embed.add_field(name="Account Created", value=member.created_at.strftime("%Y-%m-%d"), inline=True)
            embed.add_field(name="Joined Server", value=member.joined_at.strftime("%Y-%m-%d") if member.joined_at else "Unknown", inline=True)
            
            # Get warnings count
            warnings_count = 0
            if guild_id_str in self.warnings and user_id_str in self.warnings[guild_id_str]:
                warnings_count = len(self.warnings[guild_id_str][user_id_str])
            
            # Get user actions
            action_counts = {"ban": 0, "kick": 0, "mute": 0, "jail": 0, "warn": 0}
            recent_actions = []
            
            if guild_id_str in self.user_actions and user_id_str in self.user_actions[guild_id_str]:
                actions = self.user_actions[guild_id_str][user_id_str]
                
                # Count actions by type
                for action in actions:
                    action_type = action["action"]
                    if action_type in action_counts:
                        action_counts[action_type] += 1
                    else:
                        action_counts[action_type] = 1
                
                # Get 5 most recent actions
                sorted_actions = sorted(actions, key=lambda x: x["timestamp"], reverse=True)
                recent_actions = sorted_actions[:5]
            
            # Set warnings count from warnings file (not from user_actions)
            action_counts["warn"] = warnings_count
            
            # Add action counts to embed
            action_summary = "\n".join([f"**{action.title()}s:** {count}" for action, count in action_counts.items() if count > 0])
            if action_summary:
                embed.add_field(name="Action Summary", value=action_summary, inline=False)
            else:
                embed.add_field(name="Action Summary", value="No actions recorded", inline=False)
            
            # Add recent actions to embed
            if recent_actions:
                recent_list = []
                for action in recent_actions:
                    action_time = datetime.fromisoformat(action["timestamp"])
                    time_str = action_time.strftime("%Y-%m-%d %H:%M")
                    reason = action.get("reason", "No reason provided")
                    duration = f" ({action['duration']})" if "duration" in action else ""
                    
                    recent_list.append(f"**{action['action'].title()}**{duration} - {time_str}\n> {reason}")
                
                embed.add_field(name="Recent Actions", value="\n\n".join(recent_list), inline=False)
            
            # Add warnings detail if any
            if warnings_count > 0:
                warnings = self.warnings[guild_id_str][user_id_str]
                sorted_warnings = sorted(warnings, key=lambda x: x["timestamp"], reverse=True)
                
                # Only show up to 5 most recent warnings
                warnings_to_show = sorted_warnings[:5]
                warnings_list = []
                
                for i, warning in enumerate(warnings_to_show, 1):
                    warning_time = datetime.fromisoformat(warning["timestamp"])
                    time_str = warning_time.strftime("%Y-%m-%d %H:%M")
                    reason = warning.get("reason", "No reason provided")
                    
                    warnings_list.append(f"**Warning {i}/{warnings_count}** - {time_str}\n> {reason}")
                
                if warnings_count > 5:
                    warnings_list.append(f"*...and {warnings_count - 5} more warnings*")
                    
                embed.add_field(name="Warning History", value="\n\n".join(warnings_list), inline=False)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            raise commands.CommandError(f"Failed to get user overview: {str(e)}")

    @warn.error
    @overview.error
    async def admin_command_error(self, ctx, error):
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

    # Load nickname history from file
    def load_nickname_history(self):
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
        try:
            with open(self.nickname_file, 'w') as f:
                json.dump(history, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving nickname history: {e}")
            return False
            
    # Add nickname change to history
    async def add_nickname_change(self, guild_id, user_id, old_nick, new_nick):
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

    @commands.command()
    @has_permissions(administrator=True)
    async def nick(self, ctx, member: discord.Member = None, *, new_nickname = None):
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
        await member.ban(reason=reason)
        
        # Add to user actions
        await self.add_user_action(ctx.guild.id, member.id, "ban", reason)
        
        embed = discord.Embed(
            title="Ban",
            description=f"{member.mention} has been banned.\nReason: {reason or 'No reason provided'}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

    @commands.command()
    @has_permissions(administrator=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        await member.kick(reason=reason)
        
        # Add to user actions
        await self.add_user_action(ctx.guild.id, member.id, "kick", reason)
        
        embed = discord.Embed(
            title="Kick",
            description=f"{member.mention} has been kicked.\nReason: {reason or 'No reason provided'}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

    @commands.command()
    @has_permissions(administrator=True)
    async def mute(self, ctx, member: discord.Member, duration: str = "10m", *, reason=None):
        muted_role = await self.get_or_create_muted_role(ctx)
        if muted_role in member.roles:
            raise commands.CommandError(f"{member.mention} is already muted.")
        
        # Add to user actions
        await self.add_user_action(ctx.guild.id, member.id, "mute", reason, duration)
        
        await self.apply_mute(ctx, member, muted_role, duration, reason)

    async def get_or_create_muted_role(self, ctx):
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not muted_role:
            muted_role = await ctx.guild.create_role(name="Muted")
            for channel in ctx.guild.channels:
                await channel.set_permissions(muted_role, speak=False, send_messages=False)
        return muted_role

    async def apply_mute(self, ctx, member, muted_role, duration, reason):
        await member.add_roles(muted_role)
        embed = discord.Embed(
            title="Mute",
            description=f"{member.mention} has been muted for {duration}.\nReason: {reason or 'No reason provided'}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        
        asyncio.create_task(self.schedule_unmute(ctx, member, muted_role, duration))

    async def schedule_unmute(self, ctx, member, muted_role, duration):
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
    async def jail(self, ctx, member: discord.Member, time: str = None, *, reason=None):
        try:
            role = ctx.guild.get_role(1211618366763044874)
            if not role:
                raise commands.CommandError("The jail role could not be found.")

            # If no time specified or 'perm'/'permanent', make it permanent
            if not time or time.lower() in ['perm', 'permanent']:
                duration_seconds = None
                time_str = "permanently"
                duration = "permanent"
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
                duration = time

            # Add to user actions
            await self.add_user_action(ctx.guild.id, member.id, "jail", reason, duration)

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
    async def reaction(self, ctx, term: str = None, emoji: str = None):
        if term is None:
            await ctx.send("Usage: `!reaction [term] [emoji]` or `!reaction list` or `!reaction remove [term]`")
            return
            
        guild_id = str(ctx.guild.id)
        
        # Initialize guild section if not exists
        if guild_id not in self.auto_reactions:
            self.auto_reactions[guild_id] = {}
            
        # List all reactions
        if term.lower() == "list":
            if not self.auto_reactions.get(guild_id):
                await ctx.send("No auto reactions set up for this server.")
                return
                
            embed = discord.Embed(
                title="Auto Reactions",
                description="Terms that trigger auto reactions",
                color=discord.Color.blue()
            )
            
            for term, emoji in self.auto_reactions[guild_id].items():
                embed.add_field(name=term, value=emoji, inline=True)
                
            await ctx.send(embed=embed)
            return
            
        # Remove a reaction
        if term.lower() == "remove":
            if emoji is None:
                await ctx.send("Please specify a term to remove.")
                return
                
            if emoji in self.auto_reactions.get(guild_id, {}):
                del self.auto_reactions[guild_id][emoji]
                self.save_auto_reactions()
                await ctx.send(f"Removed auto reaction for term: `{emoji}`")
            else:
                await ctx.send(f"No auto reaction found for term: `{emoji}`")
            return
            
        # Add new reaction
        if emoji is None:
            await ctx.send("Please provide both a term and an emoji.")
            return
            
        # Try to find the emoji in the server
        try:
            # Check if it's a custom emoji
            if emoji.startswith('<:') and emoji.endswith('>'):
                emoji_id = int(emoji.split(':')[2][:-1])
                emoji_obj = discord.utils.get(ctx.guild.emojis, id=emoji_id)
                if emoji_obj is None:
                    await ctx.send(f"Emoji {emoji} not found in this server. The bot must have access to the emoji.")
                    return
            # Test if it's a Unicode emoji by trying to add it as a reaction
            else:
                test_msg = await ctx.send("Testing emoji...")
                try:
                    await test_msg.add_reaction(emoji)
                    await test_msg.delete()
                except discord.errors.HTTPException:
                    await test_msg.delete()
                    await ctx.send(f"Invalid emoji: {emoji}")
                    return
                    
            # Add the reaction to our dictionary
            self.auto_reactions[guild_id][term] = emoji
            self.save_auto_reactions()
            
            await ctx.send(f"Added auto reaction: When someone mentions `{term}`, I'll react with {emoji}")
            
        except Exception as e:
            await ctx.send(f"Error setting up auto reaction: {str(e)}")
    
    @commands.command()
    @has_permissions(administrator=True)
    async def reactionremove(self, ctx, *, term: str = None):
        if term is None:
            await ctx.send("Please specify a term to remove: `!reactionremove [term]`")
            return
            
        guild_id = str(ctx.guild.id)
        
        # Check if guild has any reactions
        if guild_id not in self.auto_reactions or not self.auto_reactions[guild_id]:
            await ctx.send("No auto reactions set up for this server.")
            return
            
        # Check if term exists
        if term in self.auto_reactions[guild_id]:
            emoji = self.auto_reactions[guild_id][term]
            del self.auto_reactions[guild_id][term]
            self.save_auto_reactions()
            await ctx.send(f"Removed auto reaction: `{term}` → {emoji}")
        else:
            await ctx.send(f"No auto reaction found for term: `{term}`")
    
    @commands.command()
    @has_permissions(administrator=True)
    async def unjail(self, ctx, member: discord.Member, time: str = None):
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

    def load_auto_reactions(self):
        try:
            if os.path.exists(self.reactions_file):
                with open(self.reactions_file, 'r') as f:
                    return json.load(f)
            else:
                # Create empty auto reactions file
                with open(self.reactions_file, 'w') as f:
                    json.dump({}, f)
                return {}
        except Exception as e:
            print(f"Error loading auto reactions: {e}")
            return {}

    def save_auto_reactions(self):
        try:
            with open(self.reactions_file, 'w') as f:
                json.dump(self.auto_reactions, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving auto reactions: {e}")
            return False
            
    def is_cache_recent(self):
        try:
            if not os.path.exists(self.last_scan_file) or not os.path.exists(self.message_cache_file):
                return False

            with open(self.last_scan_file, 'r') as f:
                last_scan = datetime.fromisoformat(f.read().strip())
                
            # Check if cache is less than 24 hours old
            return (datetime.utcnow() - last_scan).total_seconds() < 86400
        except:
            return False

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore messages from bots
        if message.author.bot:
            return
            
        # Check if we have auto reactions for this guild
        guild_id = str(message.guild.id) if message.guild else None
        if not guild_id or guild_id not in self.auto_reactions:
            return
            
        # Check message content for trigger terms
        for term, emoji in self.auto_reactions[guild_id].items():
            if term.lower() in message.content.lower():
                try:
                    await message.add_reaction(emoji)
                except Exception as e:
                    print(f"Error adding reaction {emoji}: {e}")
    
    @commands.command()
    @has_permissions(administrator=True)
    async def embed(self, ctx, color: str = None, *, text: str = None):
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
                embed_color = self.parse_color(color)
                
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
                raise commands.CommandError("Please provide text for the embed.")
            else:
                # Only color provided, use it as text and set color to default
                text = color
                color = None
                
        # Set up the embed color
        embed_color = self.parse_color(color)
        
        # Create and send the embed
        embed = discord.Embed(
            description=text,
            color=embed_color
        )
        
        await ctx.send(embed=embed)
        
    def parse_color(self, color):
        # Default color
        embed_color = discord.Color.light_grey()
        
        if color:
            # Check if it's a hex code
            if color.startswith('#'):
                color = color[1:]  # Remove the # if present
                
            try:
                # Try to interpret as hex code
                if len(color) == 6:
                    # Convert hex to decimal
                    r = int(color[0:2], 16)
                    g = int(color[2:4], 16)
                    b = int(color[4:6], 16)
                    embed_color = discord.Color.from_rgb(r, g, b)
                else:
                    # Check for named colors
                    color_lower = color.lower()
                    if color_lower == "red":
                        embed_color = discord.Color.red()
                    elif color_lower == "blue":
                        embed_color = discord.Color.blue()
                    elif color_lower == "green":
                        embed_color = discord.Color.green()
                    elif color_lower == "yellow":
                        embed_color = discord.Color.yellow()
                    elif color_lower == "orange":
                        embed_color = discord.Color.orange()
                    elif color_lower == "purple":
                        embed_color = discord.Color.purple()
                    elif color_lower == "gold":
                        embed_color = discord.Color.gold()
                    elif color_lower == "black":
                        embed_color = discord.Color.default()
                    elif color_lower == "white":
                        embed_color = discord.Color.from_rgb(255, 255, 255)
                    elif color_lower == "teal":
                        embed_color = discord.Color.teal()
                    elif color_lower == "magenta":
                        embed_color = discord.Color.magenta()
                    elif color_lower == "blurple":
                        embed_color = discord.Color.blurple()
                    elif color_lower == "dark_blue":
                        embed_color = discord.Color.dark_blue()
                    elif color_lower == "dark_green":
                        embed_color = discord.Color.dark_green()
                    elif color_lower == "dark_red":
                        embed_color = discord.Color.dark_red()
                    elif color_lower == "dark_purple":
                        embed_color = discord.Color.dark_purple()
                    elif color_lower == "dark_orange":
                        embed_color = discord.Color.dark_orange()
                    elif color_lower == "dark_gold":
                        embed_color = discord.Color.dark_gold()
                    elif color_lower == "dark_teal":
                        embed_color = discord.Color.dark_teal()
                    elif color_lower == "dark_magenta":
                        embed_color = discord.Color.dark_magenta()
            except ValueError:
                # If color parsing fails, use default
                embed_color = discord.Color.light_grey()
                
        return embed_color

    @cclear.error
    @reaction.error
    @reactionremove.error
    @embed.error
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
    async def admin_command_error(self, ctx, error):
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
            return True
        return False

    def load_reaction_roles(self):
        try:
            if os.path.exists(self.reaction_roles_file):
                with open(self.reaction_roles_file, 'r') as f:
                    return json.load(f)
            else:
                # Create empty reaction roles file
                with open(self.reaction_roles_file, 'w') as f:
                    json.dump({}, f)
                return {}
        except Exception as e:
            print(f"Error loading reaction roles: {e}")
            return {}

    def save_reaction_roles(self):
        try:
            with open(self.reaction_roles_file, 'w') as f:
                json.dump(self.reaction_roles, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving reaction roles: {e}")
            return False

    @commands.command()
    @has_permissions(administrator=True)
    async def reactrole(self, ctx, role_id: int, emoji: str, *, message: str):
        try:
            # Check if the role exists
            role = ctx.guild.get_role(role_id)
            if not role:
                raise commands.CommandError(f"Role with ID {role_id} not found.")
            
            # Create the embed
            embed = discord.Embed(
                description=message,
                color=discord.Color.blue()
            )
            
            # Send the message with the embed
            react_message = await ctx.send(embed=embed)
            
            # Add the reaction to the message
            try:
                await react_message.add_reaction(emoji)
            except discord.HTTPException:
                await react_message.delete()
                raise commands.CommandError(f"Invalid emoji: {emoji}")
            
            # Save the reaction role information
            guild_id = str(ctx.guild.id)
            message_id = str(react_message.id)
            
            if guild_id not in self.reaction_roles:
                self.reaction_roles[guild_id] = {}
            
            if message_id not in self.reaction_roles[guild_id]:
                self.reaction_roles[guild_id][message_id] = {}
            
            self.reaction_roles[guild_id][message_id][emoji] = role_id
            self.save_reaction_roles()
            
        except discord.Forbidden:
            raise commands.CommandError("I don't have permission to add reactions or manage roles.")
        except Exception as e:
            raise commands.CommandError(f"Error creating reaction role: {str(e)}")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # Ignore bot reactions
        if payload.member.bot:
            return
            
        guild_id = str(payload.guild_id)
        message_id = str(payload.message_id)
        emoji = str(payload.emoji)
        
        # Check if this is a reaction role message
        if (guild_id in self.reaction_roles and 
            message_id in self.reaction_roles[guild_id] and 
            emoji in self.reaction_roles[guild_id][message_id]):
            
            try:
                # Get the role ID and assign it
                role_id = self.reaction_roles[guild_id][message_id][emoji]
                role = payload.member.guild.get_role(role_id)
                
                if role:
                    await payload.member.add_roles(role, reason="Reaction role")
            except Exception as e:
                print(f"Error assigning reaction role: {e}")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        guild_id = str(payload.guild_id)
        message_id = str(payload.message_id)
        emoji = str(payload.emoji)
        
        # Check if this is a reaction role message
        if (guild_id in self.reaction_roles and 
            message_id in self.reaction_roles[guild_id] and 
            emoji in self.reaction_roles[guild_id][message_id]):
            
            try:
                # Get the guild and member
                guild = self.client.get_guild(payload.guild_id)
                if not guild:
                    return
                    
                member = guild.get_member(payload.user_id)
                if not member or member.bot:
                    return
                
                # Get the role ID and remove it
                role_id = self.reaction_roles[guild_id][message_id][emoji]
                role = guild.get_role(role_id)
                
                if role and role in member.roles:
                    await member.remove_roles(role, reason="Reaction role removed")
            except Exception as e:
                print(f"Error removing reaction role: {e}")

    @reactrole.error
    async def reactrole_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="Permission Denied",
                description="You don't have permission to use this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return True
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="Error",
                description="Missing required argument. Usage: `!reactrole [role_id] [emoji] [message]`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return True
        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="Error",
                description="Invalid role ID. Please provide a valid role ID.",
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

async def setup(client):
    await client.add_cog(AdminCog(client))