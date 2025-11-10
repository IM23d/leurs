"""
Level leaderboard command - Shows top users ranked by level and XP.
"""

import discord
from discord.ext import commands
from ..helpers.data_manager import LevelsDataManager
from ..helpers.utils import (
    create_leaderboard_embed, 
    process_leaderboard_data, 
    paginate_data, 
    create_error_embed
)

class LevelTopCommand(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.data_manager = LevelsDataManager()

    @commands.command(aliases=["lvltop"])
    async def leveltop(self, ctx, page: int = 1):
        """Show the level leaderboard."""
        try:
            # Get all user data
            users = self.data_manager.get_levels_data()
            
            # Process and sort data
            user_list = process_leaderboard_data(users, ctx.guild, "level")
            
            # Paginate results (5 per page)
            page_data, total_pages, start_idx, end_idx = paginate_data(user_list, page, 5)
            
            # Create embed
            embed = create_leaderboard_embed(
                title="🏆 Level Leaderboard",
                description="Top members ranked by level and XP.",
                user_list=user_list,
                page=page,
                total_pages=total_pages,
                start_idx=start_idx,
                ctx=ctx,
                client=self.client,
                leaderboard_type="level"
            )
            
            # Create view with navigation buttons if needed
            if total_pages > 1:
                view = LevelLeaderboardView(self, ctx, page, total_pages, "level")
                message = await ctx.send(embed=embed, view=view)
                view.message = message
            else:
                await ctx.send(embed=embed)
                
        except Exception as e:
            embed = create_error_embed(
                "Error",
                "An error occurred while fetching the leaderboard.\nPlease try again later."
            )
            await ctx.send(embed=embed)
            print(f"Error in leveltop command: {str(e)}")

async def setup(client):
    await client.add_cog(LevelTopCommand(client))

class LevelLeaderboardView(discord.ui.View):
    """Navigation view for leaderboards."""
    
    def __init__(self, cog, ctx, page, total_pages, leaderboard_type):
        super().__init__(timeout=60)
        self.cog = cog
        self.ctx = ctx
        self.page = page
        self.total_pages = total_pages
        self.leaderboard_type = leaderboard_type
        
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
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("This menu is not for you!", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(view=self)
        except:
            pass

    async def update_page(self, new_page: int):
        """Update the leaderboard to show a different page."""
        try:
            # Get data based on leaderboard type
            if self.leaderboard_type == "level":
                data = self.cog.data_manager.get_levels_data()
                title = "🏆 Level Leaderboard"
                description = "Top members ranked by level and XP."
                items_per_page = 5
            else:  # voice
                data = self.cog.data_manager.get_voice_data()
                title = "🎤 Voice Time Leaderboard"
                description = "Top members ranked by time spent in voice channels."
                items_per_page = 10
            
            # Process and sort data
            user_list = process_leaderboard_data(data, self.ctx.guild, 
                                               "level" if self.leaderboard_type == "level" else "voice_time")
            
            # Paginate results
            page_data, total_pages, start_idx, end_idx = paginate_data(user_list, new_page, items_per_page)
            
            # Create embed
            embed = create_leaderboard_embed(
                title=title,
                description=description,
                user_list=user_list,
                page=new_page,
                total_pages=total_pages,
                start_idx=start_idx,
                ctx=self.ctx,
                client=self.cog.client,
                leaderboard_type=self.leaderboard_type
            )
            
            # Create new view with updated page
            new_view = LevelLeaderboardView(self.cog, self.ctx, new_page, total_pages, self.leaderboard_type)
            new_view.message = self.message
            
            # Update the message
            await self.message.edit(embed=embed, view=new_view)
            
        except Exception as e:
            print(f"Error updating leaderboard page: {e}")

    async def prev_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.update_page(self.page - 1)

    async def next_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.update_page(self.page + 1)