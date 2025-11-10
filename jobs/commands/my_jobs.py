"""
My jobs command - displays user's current jobs.
"""

import discord
from discord.ext import commands
import sys
import os

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ..helpers.data_manager import JobDataManager
from ..helpers.utils import create_my_jobs_embed

class MyJobsCommand(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.job_manager = JobDataManager()

    @commands.command()
    async def myjobs(self, ctx):
        """Display your current jobs."""
        await self.job_manager.ensure_user_account(ctx.author)
        
        user_id = str(ctx.author.id)
        user_jobs = self.job_manager.get_user_jobs(user_id)
        all_jobs = self.job_manager.get_all_jobs()
        
        # Create and send embed
        embed = create_my_jobs_embed(ctx.author, user_jobs, all_jobs)
        await ctx.send(embed=embed)