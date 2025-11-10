"""
Utility functions for the LastFM system.
Contains formatting, validation, and embed creation utilities.
"""

import discord
import datetime
from typing import Dict, Any, Optional, List

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

def create_lastfm_embed(title: str = None, description: str = None) -> discord.Embed:
    """Create a LastFM-themed embed."""
    embed = discord.Embed(color=0x2b2d31)  # Dark theme color
    if title:
        embed.title = title
    if description:
        embed.description = description
    return embed

def format_user_profile_embed(user: discord.User, user_info: Dict[str, Any]) -> discord.Embed:
    """
    Format user profile information into an embed.
    
    Args:
        user: Discord user object
        user_info: LastFM user info from API
        
    Returns:
        Formatted discord embed
    """
    embed = create_lastfm_embed()
    
    # Set author with LastFM profile link
    profile_url = user_info.get('url', '')
    username = user_info.get('name', '')
    embed.set_author(
        name=f"Last.fm: {username}", 
        icon_url=user.avatar.url if user.avatar else user.default_avatar.url,
        url=profile_url
    )
    
    # Add user avatar if available
    if user_info.get('image'):
        avatar_url = user_info['image'][-1]['#text']
        if avatar_url:
            embed.set_thumbnail(url=avatar_url)
    
    # Format statistics
    total_scrobbles = user_info.get('playcount', '0')
    registered = int(user_info.get('registered', {}).get('unixtime', 0))
    registered_date = datetime.datetime.fromtimestamp(registered).strftime('%B %d, %Y') if registered else 'Unknown'
    
    stats = f"**Total Scrobbles:** {total_scrobbles}\n"
    stats += f"**Account Created:** {registered_date}\n"
    
    embed.description = stats
    
    return embed

def format_now_playing_embed(user: discord.User, username: str, track_data: Dict[str, Any], 
                            stats_data: Optional[Dict[str, Any]] = None) -> discord.Embed:
    """
    Format now playing track information into an embed.
    
    Args:
        user: Discord user object
        username: LastFM username
        track_data: Track data from API
        stats_data: Optional stats data (scrobble counts)
        
    Returns:
        Formatted discord embed
    """
    embed = create_lastfm_embed()
    
    # Set author
    embed.set_author(
        name=f"Last.fm: {username}", 
        icon_url=user.avatar.url if user.avatar else user.default_avatar.url
    )
    
    # Extract track information
    artist = track_data['artist']['#text']
    song = track_data['name']
    album = track_data.get('album', {}).get('#text', 'No album info')
    image_url = track_data.get('image', [])[-1]['#text'] if track_data.get('image') else None
    
    # Add thumbnail
    if image_url:
        embed.set_thumbnail(url=image_url)
    
    # Create clickable links
    artist_url = f"https://www.last.fm/music/{artist.replace(' ', '+')}"
    track_url = f"https://www.last.fm/music/{artist.replace(' ', '+')}/{song.replace(' ', '+')}"
    album_url = f"https://www.last.fm/music/{artist.replace(' ', '+')}/{album.replace(' ', '+')}"
    
    # Format content
    content = "Track\n"
    content += f"[{song}]({track_url})\n"
    content += "Artist\n"
    content += f"[{artist}]({artist_url})\n"
    content += "Album\n"
    content += f"[{album}]({album_url})"
    
    embed.description = content
    
    # Add scrobble statistics if provided
    if stats_data:
        artist_scrobbles = stats_data.get('artist_scrobbles', '0')
        album_scrobbles = stats_data.get('album_scrobbles', '0')
        track_scrobbles = stats_data.get('track_scrobbles', '0')
        total_scrobbles = stats_data.get('total_scrobbles', '0')
        
        scrobble_stats = f"{artist_scrobbles} artist scrobbles • {album_scrobbles} album scrobbles\n"
        scrobble_stats += f"{track_scrobbles} track scrobbles • {total_scrobbles} total scrobbles"
        embed.add_field(name="", value=scrobble_stats, inline=False)
    
    return embed

def format_no_track_embed(username: str, user: discord.User) -> discord.Embed:
    """
    Format embed for when no track is playing.
    
    Args:
        username: LastFM username
        user: Discord user object
        
    Returns:
        Formatted discord embed
    """
    embed = create_lastfm_embed(description="No track currently playing")
    embed.set_author(
        name=f"Last.fm: {username}", 
        icon_url=user.avatar.url if user.avatar else user.default_avatar.url
    )
    return embed

def format_server_now_playing_embed(playing_users: List[Dict[str, str]], total_users: int) -> discord.Embed:
    """
    Format server now playing embed.
    
    Args:
        playing_users: List of users currently playing music
        total_users: Total number of linked users
        
    Returns:
        Formatted discord embed
    """
    embed = discord.Embed(
        title="Currently Playing in Server",
        color=0x2b2d31
    )
    
    if playing_users:
        description = "\n"  # Initial spacing
        
        for i, user in enumerate(playing_users):
            # Create clickable links
            artist_url = f"https://www.last.fm/music/{user['artist'].replace(' ', '+')}"
            track_url = f"https://www.last.fm/music/{user['artist'].replace(' ', '+')}/{user['song'].replace(' ', '+')}"
            profile_url = f"https://www.last.fm/user/{user['username']}"
            
            description += f"[{user['username']}]({profile_url})\n"
            description += f"[{user['song']}]({track_url}) - [{user['artist']}]({artist_url})"
            
            if i < len(playing_users) - 1:
                description += "\n\n"
        
        # Add summary
        description += "\n\n"
        description += f"Users currently listening: {len(playing_users)} - Total users with LastFM: {total_users}"
        embed.description = description
    else:
        embed.description = f"No one is currently listening to music\nTotal users with LastFM: {total_users}"
    
    return embed

def create_not_linked_embed(user: discord.User) -> discord.Embed:
    """
    Create embed for when user hasn't linked their LastFM account.
    
    Args:
        user: Discord user object
        
    Returns:
        Error embed prompting user to link account
    """
    embed = create_error_embed(
        "LastFM Not Linked",
        "You haven't linked your LastFM account yet. Use `-login [username]` to link it!"
    )
    embed.set_footer(
        text=f"Requested by {user.name}", 
        icon_url=user.avatar.url if user.avatar else user.default_avatar.url
    )
    return embed

def extract_track_info(track_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract track information from API response.
    
    Args:
        track_data: Track data from LastFM API
        
    Returns:
        Dictionary with extracted track information
    """
    return {
        'artist': track_data.get('artist', {}).get('#text', 'Unknown Artist'),
        'song': track_data.get('name', 'Unknown Track'),
        'album': track_data.get('album', {}).get('#text', 'No album info'),
        'image_url': track_data.get('image', [])[-1].get('#text') if track_data.get('image') else None
    }

def safe_get_scrobble_count(data: Dict[str, Any], *keys) -> str:
    """
    Safely extract scrobble count from nested API response.
    
    Args:
        data: API response data
        *keys: Keys to traverse in nested dictionary
        
    Returns:
        Scrobble count as string, '0' if not found
    """
    try:
        result = data
        for key in keys:
            result = result[key]
        return str(result)
    except (KeyError, TypeError):
        return '0'