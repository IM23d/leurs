"""
Beg command for the economy system.
Allows users to earn a small random amount once per day.
"""

import discord
from discord.ext import commands
import random
import datetime
from ..helpers.data_manager import EconomyDataManager
from ..helpers.utils import create_success_embed, create_error_embed, format_cooldown_time

class BegCommand(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.data_manager = EconomyDataManager()

    @commands.command()
    @commands.cooldown(1, 86400, commands.BucketType.user)  # 1 day cooldown
    async def beg(self, ctx):
        """Beg for coins - once per day."""
        await self.data_manager.open_account(ctx.author)
        
        # Generate random earnings
        earnings = random.randrange(101)  # Max 100 coins
        
        # Add earnings to wallet
        new_wallet = await self.data_manager.add_balance(ctx.author.id, earnings)
        
        # Create success embed
        embed = create_success_embed(
            "Begging Results",
            f"Diddy gave you **{earnings} coins**!"
        )
        
        embed.set_thumbnail(url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        
        embed.add_field(
            name="New Wallet Balance", 
            value=f"{new_wallet} coins",
            inline=False
        )
        
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.timestamp = datetime.datetime.utcnow()
        
        await ctx.send(embed=embed)

    @beg.error
    async def beg_error(self, ctx, error):
        """Error handling for beg command."""
        if isinstance(error, commands.CommandOnCooldown):
            time_remaining = format_cooldown_time(error.retry_after)
            
            embed = create_error_embed(
                "Cooldown Active",
                "You've already begged recently!"
            )
            
            embed.add_field(
                name="Time Remaining",
                value=time_remaining,
                inline=False
            )
                        
            embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            embed.timestamp = datetime.datetime.utcnow()
            
            await ctx.send(embed=embed)
        else:
            embed = create_error_embed(
                "Error Occurred",
                f"An unexpected error happened: {str(error)}"
            )
            embed.set_footer(text="Please report this to the admins")
            await ctx.send(embed=embed)