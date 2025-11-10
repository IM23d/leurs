"""
UI components for the economy system.
Contains Discord UI views and interactions.
"""

import discord
import datetime
from ..helpers.utils import get_user_display_info, paginate_leaderboard, get_rank_emoji

class BalanceLeaderboardView(discord.ui.View):
    """Interactive pagination view for the balance leaderboard."""
    
    def __init__(self, cog, ctx, page, total_pages):
        super().__init__(timeout=60)
        self.cog = cog
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
        """Update the leaderboard to show a different page."""
        # Get all user data from database 
        users = await self.cog.data_manager.get_bank_data()
        
        # Create list from all users in the database
        user_list = []
        
        # Add all existing database entries
        for user_id, user_data in users.items():
            try:
                # Try to get the member object
                member = self.ctx.guild.get_member(int(user_id))
                
                # Calculate total balance
                wallet = user_data.get("wallet", 0)
                bank = user_data.get("bank", 0)
                total_balance = wallet + bank
                
                # Get user data
                user_entry = {
                    "id": user_id,
                    "wallet": wallet,
                    "bank": bank,
                    "total": total_balance,
                    "member": member
                }
                user_list.append(user_entry)
            except Exception as e:
                # Skip problematic entries
                continue
        
        # Sort by total balance (highest first)
        user_list.sort(key=lambda x: x["total"], reverse=True)
        
        # Paginate results
        paginated_items, total_pages, new_page = paginate_leaderboard(user_list, new_page, 10)
        
        # Create embed
        embed = discord.Embed(
            title=f"💰 Balance Leaderboard",
            description=f"Top members ranked by total wealth.",
            color=discord.Color.gold()
        )
        
        # Add leaderboard entries
        if not user_list:
            embed.description = "No users have any money yet!"
        else:
            start_idx = (new_page - 1) * 10
            
            for idx, user_data in enumerate(paginated_items):
                member = user_data["member"]
                user_id = user_data["id"]
                position = start_idx + idx
                
                # Get appropriate emoji based on rank
                prefix = get_rank_emoji(position)
                
                # Get the name and icon url
                if member:
                    name = member.name
                    icon_url = member.avatar.url if member.avatar else member.default_avatar.url
                else:
                    name, icon_url = await get_user_display_info(self.cog.client, user_id, self.ctx.guild)
                
                # Create embed field
                field_name = f"{prefix} {name}"
                field_value = f"**{user_data['total']} coins**"
                
                embed.add_field(name=field_name, value=field_value, inline=False)
                
                # Show first-place user as thumbnail
                if position == 0 and icon_url:
                    embed.set_thumbnail(url=icon_url)
        
        embed.set_footer(text=f"Page {new_page}/{total_pages} • Requested by {self.ctx.author.name}", 
                         icon_url=self.ctx.author.avatar.url if self.ctx.author.avatar else self.ctx.author.default_avatar.url)
        embed.timestamp = datetime.datetime.utcnow()
        
        # Create new view with updated page
        new_view = BalanceLeaderboardView(self.cog, self.ctx, new_page, total_pages)
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