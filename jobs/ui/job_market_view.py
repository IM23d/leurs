"""
UI components for the jobs system.
Contains Discord UI views and interactions.
"""

import discord
from ..helpers.utils import paginate_jobs, create_job_market_embed

class JobMarketView(discord.ui.View):
    """Interactive pagination view for the job market."""
    
    def __init__(self, job_manager, ctx, page, total_pages):
        super().__init__(timeout=60)
        self.job_manager = job_manager
        self.ctx = ctx
        self.page = page
        self.total_pages = total_pages
        
        # Add previous page button if not on first page
        if page > 1:
            prev_button = discord.ui.Button(
                label="Previous",
                style=discord.ButtonStyle.primary,
                emoji="⬅️",
                custom_id="prev_page",
                row=0
            )
            prev_button.callback = self.prev_callback
            self.add_item(prev_button)
        
        # Add next page button if not on last page
        if page < total_pages:
            next_button = discord.ui.Button(
                label="Next",
                style=discord.ButtonStyle.primary,
                emoji="➡️",
                custom_id="next_page",
                row=0
            )
            next_button.callback = self.next_callback
            self.add_item(next_button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check if the user can interact with this view."""
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("This menu is not for you!", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        """Disable all buttons when the view times out."""
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(view=self)
        except:
            pass

    async def update_page(self, new_page: int):
        """Update the job market to show a different page."""
        user_id = str(self.ctx.author.id)
        user_jobs = self.job_manager.get_user_jobs(user_id)
        all_jobs = self.job_manager.get_all_jobs()
        
        # Paginate jobs
        paginated_jobs, total_pages, new_page = paginate_jobs(all_jobs, new_page, 3)
        
        # Create embed
        embed = create_job_market_embed(paginated_jobs, user_jobs, new_page, total_pages)
        
        # Create new view with updated page
        new_view = JobMarketView(self.job_manager, self.ctx, new_page, total_pages)
        new_view.message = self.message
        
        # Update the message
        await self.message.edit(embed=embed, view=new_view)

    async def prev_callback(self, interaction: discord.Interaction):
        """Handle previous page button click."""
        await interaction.response.defer()
        await self.update_page(self.page - 1)

    async def next_callback(self, interaction: discord.Interaction):
        """Handle next page button click."""
        await interaction.response.defer()
        await self.update_page(self.page + 1)