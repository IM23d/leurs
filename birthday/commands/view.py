import discord
from discord.ext import commands
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from helpers.data_manager import BirthdayDataManager
from helpers.utils import (
    get_next_birthday_timestamp, 
    calculate_next_age, 
    create_error_embed, 
    create_success_embed
)
from datetime import datetime

class BirthdayViewCommand:
    """View birthday command"""
    
    def __init__(self):
        self.data_manager = BirthdayDataManager()
    
    @commands.group(name="bday", invoke_without_command=True)
    async def birthday(self, ctx, member: discord.Member = None):
        """View a user's birthday information"""
        target_member = member or ctx.author
        user_id = str(target_member.id)

        birthday_date = self.data_manager.get_birthday(user_id)
        
        if not birthday_date:
            if member:
                description = f"❌ {target_member.mention} hasn't set their birthday yet!"
            else:
                description = "❌ You haven't set your birthday yet! Use `bday set DD-MM-YYYY` to set it."
            
            embed = create_error_embed(description)
            await ctx.send(embed=embed)
            return

        next_birthday_ts = get_next_birthday_timestamp(birthday_date)
        formatted_date = datetime.strptime(birthday_date, "%d-%m-%Y").strftime("%B %d")
        next_age = calculate_next_age(birthday_date)

        if target_member == ctx.author:
            description = f"Your **birthday** is **{formatted_date}**. That's <t:{next_birthday_ts}:R>!\nYou'll turn **{next_age}**!"
        else:
            description = f"{target_member.mention}'s **birthday** is **{formatted_date}**. That's <t:{next_birthday_ts}:R>!\nThey'll turn **{next_age}**!"

        embed = create_success_embed(description)
        await ctx.send(embed=embed)

def setup_command(cog):
    """Setup function to add this command to the cog"""
    command_handler = BirthdayViewCommand()
    cog.add_command(command_handler.birthday)