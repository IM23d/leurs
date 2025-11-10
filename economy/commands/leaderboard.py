"""
Leaderboard command for the economy system.
Shows top users ranked by total balance.
"""

import discord
from discord.ext import commands
import datetime
from ..helpers.data_manager import EconomyDataManager
from ..helpers.utils import get_user_display_info, paginate_leaderboard, get_rank_emoji
from ..ui.leaderboard_view import BalanceLeaderboardView

class LeaderboardCommand(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.data_manager = EconomyDataManager()

    @commands.command(aliases=["baltop"])
    async def balancetop(self, ctx, page: int = 1):
        """Display balance leaderboard with pagination."""
        # Get all user data from the database
        users = await self.data_manager.get_bank_data()
        
        # Create list from all users in the database
        user_list = []
        
        for user_id, user_data in users.items():
            try:
                # Try to get the member object
                member = ctx.guild.get_member(int(user_id))
                
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
        paginated_items, total_pages, page = paginate_leaderboard(user_list, page, 10)
        
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
            start_idx = (page - 1) * 10
            
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
                    name, icon_url = await get_user_display_info(self.client, user_id, ctx.guild)
                
                # Create embed field
                field_name = f"{prefix} {name}"
                field_value = f"**{user_data['total']} coins**"
                
                embed.add_field(name=field_name, value=field_value, inline=False)
                
                # Show first-place user as thumbnail
                if position == 0 and icon_url:
                    embed.set_thumbnail(url=icon_url)
        
        embed.set_footer(text=f"Page {page}/{total_pages} • Requested by {ctx.author.name}", 
                         icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.timestamp = datetime.datetime.utcnow()
        
        # Create view with pagination buttons
        view = BalanceLeaderboardView(self, ctx, page, total_pages)
        
        # Send embed with view
        view.message = await ctx.send(embed=embed, view=view)