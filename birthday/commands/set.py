import discord
from discord.ext import commands
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from helpers.data_manager import BirthdayDataManager
from helpers.utils import (
    validate_birthday_date,
    get_next_birthday_timestamp,
    calculate_next_age,
    create_error_embed,
    create_success_embed
)
from datetime import datetime

class BirthdaySetCommand:
    """Set birthday command"""
    
    def __init__(self):
        self.data_manager = BirthdayDataManager()
    
    @commands.command(name="set")
    async def set_birthday(self, ctx, date_str: str):
        """Set your birthday"""
        birthday_date, error = validate_birthday_date(date_str)
        
        if error:
            if "format" in error.lower():
                description = "Invalid date format! Please use DD-MM-YYYY or DD.MM.YYYY (e.g., 31-12-2000 or 31.12.2000)"
            elif "future" in error.lower():
                description = "You can't set a birthday in the future!"
            elif "1900" in error.lower():
                description = "Please enter a valid year after 1900!"
            else:
                description = "Invalid date format! Please use DD-MM-YYYY or DD.MM.YYYY (e.g., 31-12-2000 or 31.12.2000)"
            
            embed = create_error_embed(description)
            await ctx.send(embed=embed)
            return

        # Save birthday in standard format
        date_str_standard = birthday_date.strftime("%d-%m-%Y")
        success = self.data_manager.set_birthday(ctx.author.id, date_str_standard)
        
        if not success:
            embed = create_error_embed("Failed to save birthday. Please try again.")
            await ctx.send(embed=embed)
            return

        # Format response
        formatted_date = birthday_date.strftime("%B %d")
        next_birthday_ts = get_next_birthday_timestamp(date_str_standard)
        next_age = calculate_next_age(date_str_standard)
        
        description = f"Your **birthday** is **{formatted_date}**. That's <t:{next_birthday_ts}:R>!\nYou'll turn **{next_age}**!"
        embed = create_success_embed(description)
        await ctx.send(embed=embed)

def setup_command(cog):
    """Setup function to add this command to the cog"""
    command_handler = BirthdaySetCommand()
    cog.add_command(command_handler.set_birthday)