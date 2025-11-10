"""
Buy job command - allows users to purchase jobs with coins.
"""

import discord
from discord.ext import commands
import sys
import os

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ..helpers.data_manager import JobDataManager
from ..helpers.utils import create_error_embed, validate_job_name, create_job_purchase_embed

class BuyJobCommand(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.job_manager = JobDataManager()

    @commands.command()
    async def buyjob(self, ctx, *, job_name: str = None):
        """Purchase a job to unlock it."""
        await self.job_manager.ensure_user_account(ctx.author)
        
        # Validate job name
        is_valid, normalized_name, error_msg = validate_job_name(job_name, self.job_manager.get_all_jobs())
        if not is_valid:
            embed = create_error_embed("Error", error_msg)
            await ctx.send(embed=embed)
            return
        
        job_name = normalized_name
        user_id = str(ctx.author.id)
        user_jobs = self.job_manager.get_user_jobs(user_id)
        
        # Check if already owned
        if self.job_manager.user_owns_job(user_id, job_name):
            embed = create_error_embed(
                "Error",
                f"You already have the {job_name} job unlocked!"
            )
            await ctx.send(embed=embed)
            return
        
        # Check job limit (max 3 jobs)
        if len(user_jobs) >= 3:
            embed = create_error_embed(
                "Error",
                "You can only have a maximum of 3 jobs at a time! Use `-removejob <job>` to remove a job before buying a new one."
            )
            await ctx.send(embed=embed)
            return
        
        # Check if user has enough money
        job_info = self.job_manager.get_job_info(job_name)
        cost = job_info.get('cost', 0)
        wallet_balance = await self.job_manager.get_user_wallet_balance(user_id)
        
        if wallet_balance < cost:
            embed = create_error_embed(
                "Error",
                f"You don't have enough coins! You need {cost} coins to unlock this job."
            )
            await ctx.send(embed=embed)
            return
        
        # Purchase the job
        success = await self.job_manager.purchase_job(user_id, job_name)
        if success:
            # Get updated data
            updated_user_jobs = self.job_manager.get_user_jobs(user_id)
            new_balance = await self.job_manager.get_user_wallet_balance(user_id)
            
            # Create success embed
            embed = create_job_purchase_embed(ctx.author, job_name, updated_user_jobs, new_balance)
            await ctx.send(embed=embed)
        else:
            embed = create_error_embed(
                "Error",
                "Failed to purchase job. Please try again."
            )
            await ctx.send(embed=embed)