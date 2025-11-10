"""
Utility functions for levels system.
Contains formatting, embed creation, and data processing utilities.
"""

import discord
import datetime
import math
from typing import List, Dict, Any, Optional, Tuple

def create_progress_bar(percentage: int, length: int = 10) -> str:
    """
    Create a visual progress bar.
    
    Args:
        percentage: Progress percentage (0-100)
        length: Length of progress bar in characters
        
    Returns:
        Progress bar string with filled and empty blocks
    """
    filled_bars = math.floor(percentage / (100 / length))
    empty_bars = length - filled_bars
    return "🟦" * filled_bars + "⬜" * empty_bars

def format_time(seconds: float) -> str:
    """
    Format seconds into a readable time string.
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted time string (e.g. "2h 30m" or "1d 5h 23m 45s")
    """
    total_seconds = int(seconds)
    
    if total_seconds == 0:
        return "0s"
    
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    time_parts = []
    if days > 0:
        time_parts.append(f"{days}d")
    if hours > 0:
        time_parts.append(f"{hours}h")
    if minutes > 0:
        time_parts.append(f"{minutes}m")
    if seconds > 0 and len(time_parts) < 2:  # Only show seconds if less than 2 other units
        time_parts.append(f"{seconds}s")
    
    return " ".join(time_parts)

def create_level_embed(member: discord.Member, user_data: Dict[str, Any], 
                      voice_data: Dict[str, Any], xp_manager) -> discord.Embed:
    """
    Create a level status embed for a user.
    
    Args:
        member: Discord member object
        user_data: User's level data
        voice_data: User's voice data
        xp_manager: XP manager for calculations
        
    Returns:
        Formatted discord embed
    """
    xp = user_data["xp"]
    level = user_data["level"]
    total_messages = user_data["total_messages"]
    
    # Calculate progress to next level
    current_level_xp, needed_for_next_level, percentage = xp_manager.calculate_level_progress(xp, level)
    progress_bar = create_progress_bar(percentage)
    
    # Format voice time
    voice_time = voice_data.get("voice_time", 0)
    voice_time_str = format_time(voice_time)
    
    # Create embed
    embed = discord.Embed(
        title=f"{member.name}'s Stats",
        color=discord.Color.blue()
    )
    
    # Add fields
    embed.add_field(name="Level", value=f"**{level}**", inline=True)
    embed.add_field(name="Total XP", value=f"**{xp:,}**", inline=True)
    embed.add_field(name="Messages", value=f"**{total_messages:,}**", inline=True)
    
    embed.add_field(
        name=f"Progress to Level {level+1}", 
        value=f"{progress_bar} **{percentage}%**\n{current_level_xp:,}/{needed_for_next_level:,} XP", 
        inline=False
    )
    
    embed.add_field(name="Time in Voice", value=f"**{voice_time_str}**", inline=True)
    
    # Set thumbnail and footer
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    embed.timestamp = datetime.datetime.utcnow()
    
    return embed

def create_error_embed(title: str, description: str) -> discord.Embed:
    """Create a standardized error embed."""
    return discord.Embed(
        title=title,
        description=description,
        color=discord.Color.red()
    )

def create_success_embed(title: str, description: str) -> discord.Embed:
    """Create a standardized success embed."""
    return discord.Embed(
        title=title,
        description=description,
        color=discord.Color.green()
    )

def format_leaderboard_user(member: Optional[discord.Member], user_id: str, 
                           client) -> Tuple[str, str]:
    """
    Format a user for leaderboard display.
    
    Args:
        member: Discord member object (can be None)
        user_id: User ID string
        client: Discord client for fetching users
        
    Returns:
        Tuple of (name, icon_url)
    """
    if member:
        name = member.name
        icon_url = member.avatar.url if member.avatar else member.default_avatar.url
    else:
        # Try to fetch user info from Discord
        try:
            user = client.get_user(int(user_id))
            if user:
                name = user.name
                icon_url = user.avatar.url if user.avatar else user.default_avatar.url
            else:
                name = f"User-{user_id[-4:]}"
                icon_url = None
        except:
            name = f"User-{user_id[-4:]}"
            icon_url = None
    
    return name, icon_url

def create_leaderboard_embed(title: str, description: str, user_list: List[Dict[str, Any]], 
                           page: int, total_pages: int, start_idx: int, 
                           ctx, client, leaderboard_type: str = "level") -> discord.Embed:
    """
    Create a leaderboard embed.
    
    Args:
        title: Embed title
        description: Embed description
        user_list: List of user data dictionaries
        page: Current page number
        total_pages: Total number of pages
        start_idx: Starting index for current page
        ctx: Command context
        client: Discord client
        leaderboard_type: Type of leaderboard ("level" or "voice")
        
    Returns:
        Formatted discord embed
    """
    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.gold() if leaderboard_type == "level" else discord.Color.purple()
    )
    
    # Add leaderboard entries
    if not user_list:
        embed.description = ("No users have earned XP yet! Send some messages to start gaining levels." 
                           if leaderboard_type == "level" 
                           else "No users have spent time in voice channels yet!")
    else:
        # Get rank emojis for top 3
        rank_emoji = {0: "🥇", 1: "🥈", 2: "🥉"}
        
        items_per_page = 5 if leaderboard_type == "level" else 10
        end_idx = min(start_idx + items_per_page, len(user_list))
        
        for idx, user_data in enumerate(user_list[start_idx:end_idx], start=start_idx + 1):
            member = user_data["member"]
            user_id = user_data["id"]
            position = idx - 1 + start_idx  # Zero-based position
            
            # Get appropriate emoji based on rank
            prefix = rank_emoji.get(position, f"{idx}.")
            
            # Get the name and icon url
            name, icon_url = format_leaderboard_user(member, user_id, client)
            
            # Create field content based on leaderboard type
            if leaderboard_type == "level":
                field_name = f"{prefix} {name}"
                field_value = f"Level: **{user_data['level']}**\nXP: **{user_data['xp']}**\nMessages: **{user_data['total_messages']}**"
            else:  # voice leaderboard
                time_str = format_time(user_data["voice_time"])
                field_name = f"{prefix} {name}"
                field_value = f"Time in Voice: **{time_str}**"
            
            embed.add_field(name=field_name, value=field_value, inline=False)
            
            # Show first-place user as thumbnail
            if position == 0 and icon_url:
                embed.set_thumbnail(url=icon_url)
    
    # Set footer
    embed.set_footer(
        text=f"Page {page}/{total_pages} • Requested by {ctx.author.name}", 
        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
    )
    embed.timestamp = datetime.datetime.utcnow()
    
    return embed

def process_leaderboard_data(data: Dict[str, Any], guild, 
                           sort_key: str = "level") -> List[Dict[str, Any]]:
    """
    Process leaderboard data and sort appropriately.
    
    Args:
        data: Raw data dictionary
        guild: Discord guild object
        sort_key: Key to sort by ("level" for levels, "voice_time" for voice)
        
    Returns:
        Sorted list of user data for leaderboard
    """
    user_list = []
    
    for user_id, user_data in data.items():
        try:
            member = guild.get_member(int(user_id))
            
            # Skip if member not found in guild (for most leaderboards)
            # Include all data that exists
            if sort_key in user_data or sort_key == "level":
                user_entry = {
                    "id": user_id,
                    "member": member,
                    **user_data
                }
                user_list.append(user_entry)
        except Exception as e:
            print(f"Error processing user {user_id}: {e}")
            continue
    
    # Sort based on type
    if sort_key == "level":
        user_list.sort(key=lambda x: (x.get("level", 0), x.get("xp", 0)), reverse=True)
    else:
        user_list.sort(key=lambda x: x.get(sort_key, 0), reverse=True)
    
    return user_list

def paginate_data(data_list: List[Any], page: int, items_per_page: int) -> Tuple[List[Any], int, int, int]:
    """
    Paginate a list of data.
    
    Args:
        data_list: List to paginate
        page: Current page number
        items_per_page: Number of items per page
        
    Returns:
        Tuple of (page_data, total_pages, start_idx, end_idx)
    """
    total_pages = max(1, math.ceil(len(data_list) / items_per_page))
    page = max(1, min(page, total_pages))
    
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(data_list))
    
    return data_list[start_idx:end_idx], total_pages, start_idx, end_idx