"""
Remove job command - allows users to remove jobs from their collection.
"""

import discord
from discord.ext import commands
import sys
import os

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ..helpers.data_manager import JobDataManager
from ..helpers.utils import create_error_embed, validate_job_name, create_job_removal_embed

class RemoveJobCommand(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.job_manager = JobDataManager()

    @commands.command()
    async def removejob(self, ctx, *, job_name: str = None):
        """Remove a job from your current jobs."""
        await self.job_manager.ensure_user_account(ctx.author)
        
        if not job_name:
            embed = create_error_embed(
                "Error",
                "Please specify a job to remove. Use `-myjobs` to see your current jobs."
            )
            await ctx.send(embed=embed)
            return
        
        # Normalize job name
        job_name = job_name.title()
        user_id = str(ctx.author.id)
        user_jobs = self.job_manager.get_user_jobs(user_id)
        
        # Check if user owns the job
        if not self.job_manager.user_owns_job(user_id, job_name):
            embed = create_error_embed(
                "Error",
                f"You don't have the {job_name} job!"
            )
            await ctx.send(embed=embed)
            return
        
        # Remove the job
        success = self.job_manager.remove_user_job(user_id, job_name)
        if success:
            # Get updated job list
            updated_user_jobs = self.job_manager.get_user_jobs(user_id)
            
            # Create success embed
            embed = create_job_removal_embed(ctx.author, job_name, updated_user_jobs)
            await ctx.send(embed=embed)
        else:
            embed = create_error_embed(
                "Error",
                "Failed to remove job. Please try again."
            )
            await ctx.send(embed=embed)