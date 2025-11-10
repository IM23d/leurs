import discord
from discord.ext import commands
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from helpers.data_manager import DataManager
from helpers.utils import admin_only, send_error_embed, send_success_embed

class OverviewCommand:
    """User overview command"""
    
    def __init__(self):
        self.data_manager = DataManager()
    
    @commands.command(name="overview", aliases=["o"])
    @admin_only()
    async def overview(self, ctx, member: discord.Member):
        """Show comprehensive overview of a user's admin history"""
        try:
            guild_id_str = str(ctx.guild.id)
            user_id_str = str(member.id)
            
            # Create embed
            embed = discord.Embed(
                title=f"👤 User Overview: {member.display_name}",
                description=f"History of admin actions for {member.mention}",
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            
            # Add user info
            embed.add_field(name="🆔 User ID", value=member.id, inline=True)
            embed.add_field(name="📅 Account Created", value=member.created_at.strftime("%Y-%m-%d"), inline=True)
            embed.add_field(name="📥 Joined Server", value=member.joined_at.strftime("%Y-%m-%d") if member.joined_at else "Unknown", inline=True)
            
            # Get warnings count
            warnings_data = self.data_manager.load_json("warnings")
            warnings_count = 0
            if guild_id_str in warnings_data and user_id_str in warnings_data[guild_id_str]:
                warnings_count = len(warnings_data[guild_id_str][user_id_str])
            
            # Get user actions
            actions_data = self.data_manager.load_json("user_actions")
            action_counts = {"ban": 0, "kick": 0, "mute": 0, "jail": 0}
            recent_actions = []
            
            if guild_id_str in actions_data and user_id_str in actions_data[guild_id_str]:
                actions = actions_data[guild_id_str][user_id_str]
                
                # Count actions by type
                for action in actions:
                    action_type = action["action"]
                    if action_type in action_counts:
                        action_counts[action_type] += 1
                
                # Get 5 most recent actions
                sorted_actions = sorted(actions, key=lambda x: x["timestamp"], reverse=True)
                recent_actions = sorted_actions[:5]
            
            # Add warnings count
            action_counts["warn"] = warnings_count
            
            # Add action counts to embed
            action_summary = "\n".join([f"**{action.title()}s:** {count}" for action, count in action_counts.items() if count > 0])
            if action_summary:
                embed.add_field(name="📊 Action Summary", value=action_summary, inline=False)
            else:
                embed.add_field(name="📊 Action Summary", value="No actions recorded", inline=False)
            
            # Add recent actions to embed
            if recent_actions:
                recent_list = []
                for action in recent_actions:
                    from datetime import datetime
                    action_time = datetime.fromisoformat(action["timestamp"])
                    time_str = action_time.strftime("%Y-%m-%d %H:%M")
                    reason = action.get("reason", "No reason provided")
                    duration = f" ({action['duration']})" if "duration" in action else ""
                    
                    recent_list.append(f"**{action['action'].title()}**{duration} - {time_str}\n> {reason}")
                
                embed.add_field(name="🕐 Recent Actions", value="\n\n".join(recent_list), inline=False)
            
            # Add warnings detail if any
            if warnings_count > 0:
                warnings = warnings_data[guild_id_str][user_id_str]
                sorted_warnings = sorted(warnings, key=lambda x: x["timestamp"], reverse=True)
                
                # Only show up to 3 most recent warnings
                warnings_to_show = sorted_warnings[:3]
                warnings_list = []
                
                for i, warning in enumerate(warnings_to_show, 1):
                    from datetime import datetime
                    warning_time = datetime.fromisoformat(warning["timestamp"])
                    time_str = warning_time.strftime("%Y-%m-%d %H:%M")
                    reason = warning.get("reason", "No reason provided")
                    
                    warnings_list.append(f"**Warning {i}** - {time_str}\n> {reason}")
                
                if warnings_count > 3:
                    warnings_list.append(f"*...and {warnings_count - 3} more warnings*")
                    
                embed.add_field(name="⚠️ Recent Warnings", value="\n\n".join(warnings_list), inline=False)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await send_error_embed(ctx, "Error", f"Failed to get user overview: {str(e)}")

def setup_command(cog):
    """Setup function to add this command to the cog"""
    command_handler = OverviewCommand()
    cog.add_command(command_handler.overview)