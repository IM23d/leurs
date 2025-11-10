"""
Remind me command for setting reminders.
"""

import discord
from discord.ext import commands
from datetime import datetime, timedelta

class RemindMeCommand(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.reminder_manager = None
        
    def set_reminder_manager(self, reminder_manager):
        """Set the reminder manager instance."""
        self.reminder_manager = reminder_manager
        
    @commands.command(aliases=['rm'])
    async def remindme(self, ctx, time_str: str, *, reason: str = "No reason provided"):
        """Set a reminder for a specific time."""
        if not self.reminder_manager:
            await ctx.send("Reminder system not available.")
            return
            
        remind_time, cleaned_reason = self.reminder_manager.parse_time(time_str, reason)
        
        if not remind_time:
            embed = discord.Embed(
                title="Invalid Time Format",
                description="Please use one of these formats:\n"
                           "• `-rm 20:00 reason` (24h format)\n"
                           "• `-rm 8pm reason` (12h format)\n"
                           "• `-rm 15m reason` (15 minutes, also s/h/d)\n"
                           "• `-rm tomorrow reason` or `-rm tm reason`\n"
                           "• `-rm 15.05 reason` (date)\n"
                           "• `-rm 15.05.26 reason` (date with year)\n"
                           "• `-rm 15.07:15:25 reason` (full datetime)",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
            return
            
        # Try to create the reminder
        if not self.reminder_manager.create_reminder(ctx, ctx.author.id, ctx.channel.id, remind_time, cleaned_reason):
            await ctx.send("Reminders cannot be set more than a year in the future.")
            return
            
        # Calculate time difference for display
        time_diff = remind_time - datetime.now()
        days = time_diff.days
        hours, remainder = divmod(time_diff.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        time_parts = []
        if days > 0:
            time_parts.append(f"{days} days")
        if hours > 0:
            time_parts.append(f"{hours} hours")
        if minutes > 0:
            time_parts.append(f"{minutes} minutes")
        if seconds > 0 and not (days or hours or minutes):
            time_parts.append(f"{seconds} seconds")
            
        time_str = ", ".join(time_parts)
        
        embed = discord.Embed(
            title="Reminder Set",
            description=f"I'll remind you in {time_str}\n"
                       f"**Reason:** {cleaned_reason}\n"
                       f"**Time:** <t:{int(remind_time.timestamp())}:F>",
            color=0x00FF00
        )
        await ctx.send(embed=embed)
        
    @commands.command(aliases=['list', 'reminders'])
    async def remindme_list(self, ctx):
        """List all active reminders for the user."""
        if not self.reminder_manager:
            await ctx.send("Reminder system not available.")
            return
            
        reminders = self.reminder_manager.get_user_reminders(ctx.author.id)
        
        if not reminders:
            embed = discord.Embed(
                title="Your Reminders",
                description="You don't have any active reminders.",
                color=0x808080
            )
            await ctx.send(embed=embed)
            return
            
        # Create embed with reminder list
        embed = discord.Embed(
            title="📝 Your Reminders",
            color=0x00FF00
        )
        
        for i, reminder in enumerate(reminders, 1):
            embed.add_field(
                name=f"Reminder #{i}",
                value=f"**Time:** <t:{int(reminder['time'].timestamp())}:F>\n"
                      f"**Relative:** <t:{int(reminder['time'].timestamp())}:R>\n"
                      f"**Reason:** {reminder['reason']}",
                inline=False
            )
            
        await ctx.send(embed=embed)

async def setup(client):
    """Setup function for the RemindMe command."""
    client.add_cog(RemindMeCommand(client))