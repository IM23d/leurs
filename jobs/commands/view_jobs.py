"""
View jobs command - displays the job market with pagination.
"""

import discord
from discord.ext import commands
import sys
import os

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ..helpers.data_manager import JobDataManager
from ..helpers.utils import paginate_jobs, create_job_market_embed
from ..ui.job_market_view import JobMarketView

class ViewJobsCommand(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.job_manager = JobDataManager()

    @commands.command()
    async def jobs(self, ctx, page: int = 1):
        """Display the job market with pagination."""
        await self.job_manager.ensure_user_account(ctx.author)
        
        user_id = str(ctx.author.id)
        user_jobs = self.job_manager.get_user_jobs(user_id)
        all_jobs = self.job_manager.get_all_jobs()
        
        # Paginate jobs
        paginated_jobs, total_pages, page = paginate_jobs(all_jobs, page, 3)
        
        # Create embed
        embed = create_job_market_embed(paginated_jobs, user_jobs, page, total_pages)
        
        # Create view with navigation buttons
        view = JobMarketView(self.job_manager, ctx, page, total_pages)
        
        # Send message
        view.message = await ctx.send(embed=embed, view=view)