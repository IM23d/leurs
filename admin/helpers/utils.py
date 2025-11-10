import discord
from discord.ext import commands

def admin_only():
    """Decorator that checks if user has administrator permissions"""
    return commands.has_permissions(administrator=True)

def moderator_only():
    """Decorator that checks if user has moderation permissions"""
    def predicate(ctx):
        return (ctx.author.guild_permissions.kick_members or 
                ctx.author.guild_permissions.ban_members or
                ctx.author.guild_permissions.administrator)
    return commands.check(predicate)

async def send_error_embed(ctx, title, description):
    """Send a standardized error embed"""
    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)

async def send_success_embed(ctx, title, description):
    """Send a standardized success embed"""
    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

async def send_info_embed(ctx, title, description):
    """Send a standardized info embed"""
    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

def parse_duration(duration_str):
    """Parse duration string and return seconds"""
    if duration_str.endswith('s'):
        return int(duration_str[:-1])
    elif duration_str.endswith('m'):
        return int(duration_str[:-1]) * 60
    elif duration_str.endswith('h'):
        return int(duration_str[:-1]) * 3600
    elif duration_str.endswith('d'):
        return int(duration_str[:-1]) * 86400
    else:
        try:
            return int(duration_str) * 60  # Default to minutes
        except ValueError:
            raise commands.CommandError(f"Invalid duration format: {duration_str}. Use formats like '30s', '10m', '1h', or '1d'.")

def parse_color(color):
    """Parse color string and return Discord color"""
    # Default color
    embed_color = discord.Color.light_grey()
    
    if color:
        # Check if it's a hex code
        if color.startswith('#'):
            color = color[1:]  # Remove the # if present
            
        try:
            # Try to interpret as hex code
            if len(color) == 6:
                # Convert hex to decimal
                r = int(color[0:2], 16)
                g = int(color[2:4], 16)
                b = int(color[4:6], 16)
                embed_color = discord.Color.from_rgb(r, g, b)
            else:
                # Check for named colors
                color_lower = color.lower()
                color_map = {
                    "red": discord.Color.red(),
                    "blue": discord.Color.blue(),
                    "green": discord.Color.green(),
                    "yellow": discord.Color.yellow(),
                    "orange": discord.Color.orange(),
                    "purple": discord.Color.purple(),
                    "gold": discord.Color.gold(),
                    "black": discord.Color.default(),
                    "white": discord.Color.from_rgb(255, 255, 255),
                    "teal": discord.Color.teal(),
                    "magenta": discord.Color.magenta(),
                    "blurple": discord.Color.blurple(),
                    "dark_blue": discord.Color.dark_blue(),
                    "dark_green": discord.Color.dark_green(),
                    "dark_red": discord.Color.dark_red(),
                    "dark_purple": discord.Color.dark_purple(),
                    "dark_orange": discord.Color.dark_orange(),
                    "dark_gold": discord.Color.dark_gold(),
                    "dark_teal": discord.Color.dark_teal(),
                    "dark_magenta": discord.Color.dark_magenta()
                }
                embed_color = color_map.get(color_lower, discord.Color.light_grey())
        except ValueError:
            # If color parsing fails, use default
            embed_color = discord.Color.light_grey()
            
    return embed_color