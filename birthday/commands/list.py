import discord
from discord.ext import commands
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from helpers.data_manager import BirthdayDataManager
from helpers.utils import (
    get_next_birthday_date,
    calculate_next_age,
    create_error_embed,
    create_info_embed
)
from datetime import datetime

class BirthdayListCommand:
    """List birthdays command"""
    
    def __init__(self):
        self.data_manager = BirthdayDataManager()
    
    @commands.command(name="list")
    async def list_birthdays(self, ctx):
        """List upcoming birthdays in the server"""
        all_birthdays = self.data_manager.get_all_birthdays()
        
        if not all_birthdays:
            embed = create_error_embed("No birthdays have been set yet!")
            await ctx.send(embed=embed)
            return

        # Get all birthdays and sort them by next occurrence
        upcoming = []
        for user_id, bday in all_birthdays.items():
            try:
                member = await ctx.guild.fetch_member(int(user_id))
                if member:  # Only include members still in the server
                    next_date = get_next_birthday_date(bday)
                    next_age = calculate_next_age(bday)
                    upcoming.append((next_date, member, next_age))
            except discord.NotFound:
                continue

        # Sort by next occurrence
        upcoming.sort(key=lambda x: x[0])

        if not upcoming:
            embed = create_error_embed("No upcoming birthdays found!")
            await ctx.send(embed=embed)
            return

        # Limit to top 10 upcoming birthdays
        upcoming = upcoming[:10]

        description = "\n".join(
            f"{member.mention}\nTurns **{next_age}** on **{next_date.strftime('%B %d')}**\n(<t:{int(datetime.combine(next_date, datetime.min.time()).timestamp())}:R>)\n"
            for next_date, member, next_age in upcoming
        )

        embed = create_info_embed("🎂 Upcoming Birthdays", description)
        await ctx.send(embed=embed)

def setup_command(cog):
    """Setup function to add this command to the cog"""
    command_handler = BirthdayListCommand()
    cog.add_command(command_handler.list_birthdays)