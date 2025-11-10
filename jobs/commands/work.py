"""
Work command - allows users to work at all their jobs once per day.
"""

import discord
from discord.ext import commands
import sys
import os

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ..helpers.data_manager import JobDataManager
from ..helpers.utils import create_error_embed, create_work_results_embed, format_cooldown_time

class WorkCommand(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.job_manager = JobDataManager()

    @commands.command()
    @commands.cooldown(1, 86400, commands.BucketType.user)  # 24 hour cooldown
    async def work(self, ctx):
        """Work at all your jobs to earn coins (once per day)."""
        await self.job_manager.ensure_user_account(ctx.author)
        self.job_manager.rotate_jobs()
        
        user_id = str(ctx.author.id)
        user_jobs = self.job_manager.get_user_jobs(user_id)
        
        # Check if user has any jobs
        if not user_jobs:
            embed = create_error_embed(
                "Error",
                "You don't have any jobs! Use `-jobs` to see available jobs."
            )
            await ctx.send(embed=embed)
            return
        
        # Calculate earnings from all jobs
        total_earnings, earnings_breakdown = await self.job_manager.work_all_jobs(user_id)
        
        # Get new balance
        new_balance = await self.job_manager.get_user_wallet_balance(user_id)
        
        # Create and send result embed
        embed = create_work_results_embed(
            ctx.author, 
            total_earnings, 
            earnings_breakdown, 
            new_balance
        )
        await ctx.send(embed=embed)

    @work.error
    async def work_error(self, ctx, error):
        """Error handling for work command."""
        if isinstance(error, commands.CommandOnCooldown):
            time_remaining = format_cooldown_time(error.retry_after)
            
            embed = create_error_embed(
                "⏰ Cooldown Active",
                "You've already worked today!"
            )
            
            embed.add_field(
                name="Time Remaining",
                value=time_remaining,
                inline=False
            )
            
            embed.set_footer(
                text=f"Requested by {ctx.author.name}", 
                icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
            )
            
            await ctx.send(embed=embed)
        else:
            embed = create_error_embed(
                "Error",
                f"An unexpected error occurred: {str(error)}"
            )
            await ctx.send(embed=embed)