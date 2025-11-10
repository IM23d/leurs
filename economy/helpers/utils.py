"""
Utility functions for the economy system.
"""

import discord
import math

def format_amount_input(amount_str, current_balance):
    """
    Parse amount input string and return the numeric amount.
    Handles 'all', percentages, and regular numbers.
    
    Args:
        amount_str (str): The input string (e.g., "100", "50%", "all")
        current_balance (int): The current balance to calculate percentages from
        
    Returns:
        tuple: (success, amount, error_message)
    """
    if amount_str is None:
        return False, 0, "Please specify an amount"
    
    # Handle "all" keyword
    if amount_str.lower() == "all":
        return True, current_balance, None
    
    # Handle percentage
    if "%" in amount_str:
        try:
            percentage = int(amount_str.replace("%", ""))
            if percentage <= 0 or percentage > 100:
                return False, 0, "Please enter a valid percentage between 1% and 100%"
            amount = int(current_balance * (percentage / 100))
            return True, amount, None
        except ValueError:
            return False, 0, "Please enter a valid percentage between 1% and 100%"
    
    # Handle regular number
    try:
        amount = int(amount_str)
        if amount <= 0:
            return False, 0, "Amount must be positive!"
        return True, amount, None
    except ValueError:
        return False, 0, "Please enter a valid number, percentage, or 'all'"

def create_balance_embed(user, wallet_amt, bank_amt):
    """Create a balance display embed."""
    embed = discord.Embed(
        title=f"{user.name}'s balance", 
        color=discord.Color.from_rgb(255, 255, 255)
    )
    embed.add_field(name="Wallet balance", value=f"{wallet_amt} coins")
    embed.add_field(name="Bank balance", value=f"{bank_amt} coins")
    
    total = wallet_amt + bank_amt
    embed.add_field(name="Total balance", value=f"{total} coins", inline=False)
    
    embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
    embed.set_footer(text=f"Requested by {user.name}", icon_url=user.avatar.url if user.avatar else user.default_avatar.url)
    
    return embed

def create_error_embed(title, description):
    """Create a standardized error embed."""
    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.red()
    )
    return embed

def create_success_embed(title, description, color=discord.Color.green()):
    """Create a standardized success embed."""
    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )
    return embed

def format_cooldown_time(retry_after):
    """Format cooldown time into hours, minutes, seconds."""
    hours, remainder = divmod(retry_after, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"

def get_rank_emoji(position):
    """Get appropriate emoji for leaderboard position."""
    rank_emojis = {0: "🥇", 1: "🥈", 2: "🥉"}
    return rank_emojis.get(position, f"{position + 1}.")

async def get_user_display_info(client, user_id, guild=None):
    """
    Get display information for a user (name, avatar).
    
    Args:
        client: Discord client
        user_id (str): User ID as string
        guild: Guild object to check for member info
        
    Returns:
        tuple: (name, icon_url)
    """
    try:
        # Try to get member from guild first
        if guild:
            member = guild.get_member(int(user_id))
            if member:
                name = member.name
                icon_url = member.avatar.url if member.avatar else member.default_avatar.url
                return name, icon_url
        
        # Try to fetch user from Discord
        user = await client.fetch_user(int(user_id))
        name = user.name
        icon_url = user.avatar.url if user.avatar else user.default_avatar.url
        return name, icon_url
    except:
        # If all else fails, use a generic name
        name = f"User-{user_id[-4:]}"
        return name, None

def paginate_leaderboard(user_list, page=1, items_per_page=10):
    """
    Paginate a leaderboard list.
    
    Args:
        user_list (list): List of user data dictionaries
        page (int): Current page number (1-indexed)
        items_per_page (int): Number of items per page
        
    Returns:
        tuple: (paginated_items, total_pages, valid_page)
    """
    total_pages = max(1, math.ceil(len(user_list) / items_per_page))
    
    # Ensure page is within valid range
    page = max(1, min(page, total_pages))
    
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(user_list))
    
    paginated_items = user_list[start_idx:end_idx]
    
    return paginated_items, total_pages, page