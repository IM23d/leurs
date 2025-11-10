import re
import unicodedata
import discord
from datetime import datetime

def create_error_embed(description):
    """Create a standardized error embed"""
    return discord.Embed(
        title="Error",
        description=description,
        color=discord.Color.red()
    )

def create_success_embed(title, description):
    """Create a standardized success embed"""
    return discord.Embed(
        title=title,
        description=description,
        color=discord.Color.green()
    )

def create_info_embed(title, description):
    """Create a standardized info embed"""
    return discord.Embed(
        title=title,
        description=description,
        color=discord.Color.blue()
    )

async def normalize_text(text):
    """Normalize text for advanced filtering"""
    # Convert to lowercase
    text = text.lower()
    # Remove accents and special characters
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    # Remove numbers
    text = re.sub(r'\d', '', text)
    # Remove special characters except spaces
    text = re.sub(r'[^\w\s]', '', text)
    # Replace multiple repeated characters with single character
    text = re.sub(r'(.)\1{2,}', r'\1', text)
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text

async def check_blocked_term(message_content, blocked_terms):
    """Check if message content contains blocked terms"""
    normalized_message = await normalize_text(message_content)
    
    for term, data in blocked_terms.items():
        if data.get('advanced_filtering', False):
            # Advanced filtering with normalization
            normalized_term = await normalize_text(term)
            if normalized_term in normalized_message:
                return term, data
        else:
            # Simple case-insensitive check
            if term.lower() in message_content.lower():
                return term, data
    
    return None, None

async def parse_duration(duration_str):
    """Parse duration string and return seconds"""
    if not duration_str:
        return None
    
    # Extract number and unit
    match = re.match(r'^(\d+)([smhd])', duration_str.lower())
    if not match:
        return None
        
    amount, unit = match.groups()
    amount = int(amount)
    
    if unit == 's':
        return amount
    elif unit == 'm':
        return amount * 60
    elif unit == 'h':
        return amount * 3600
    elif unit == 'd':
        return amount * 86400
    
    return None

def create_log_embed(title, user, channel, reason, color=discord.Color.blue(), duration=None):
    """Create a standardized log embed for moderation actions"""
    embed = discord.Embed(
        title=title,
        description=f"**User:** {user.mention} ({user})\n**Channel:** {channel.mention}\n**Reason:** {reason}",
        color=color,
        timestamp=datetime.now()
    )
    
    if duration:
        embed.add_field(name="Duration", value=duration, inline=True)
    
    return embed

def validate_punishment_type(punishment_type):
    """Validate punishment type"""
    valid_types = ['mute', 'warn', 'kick', 'ban']
    return punishment_type.lower() in valid_types