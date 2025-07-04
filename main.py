import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import random
import json
import datetime
import asyncio
import re
from discord.ext.commands import CommandOnCooldown

from economy import EconomyCog
from gambling import GamblingCog
from other import OtherCog
from jobs import JobMarketCog
from levels import LevelsCog
from admin import AdminCog
from lastfm import LastFMCog
from birthday import BirthdayCog
from timezone import TimezoneCog
from snipe import SnipeCog
# Import your new cog here
# from mycog import MyCog

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Create data directory if it doesn't exist
if not os.path.exists('data'):
    os.makedirs('data')

# Load or create prefix configuration
def load_prefix_config():
    try:
        with open('data/prefix.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        with open('data/prefix.json', 'w') as f:
            json.dump({}, f)
        return {}

def get_prefix(bot, message):
    prefixes = load_prefix_config()
    # Default prefix if no custom prefix is set
    return prefixes.get(str(message.guild.id), '-')

async def check_cooldown(ctx):
    # Skip cooldown for administrators
    if ctx.author.guild_permissions.administrator:
        return True
    
    # Get the bucket for the user
    bucket = ctx.bot.cooldown_bucket.get_bucket(ctx.message)
    
    # Check if the user is on cooldown
    retry_after = bucket.update_rate_limit()
    if retry_after:
        # User is on cooldown
        remaining = round(retry_after, 1)
        embed = discord.Embed(
            title="Cooldown",
            description=f"Please wait {remaining} seconds before using commands again.",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)
        return False
    return True

intents = discord.Intents.all()  # Enable all intents to properly handle messages and attachments

class CustomBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Create a global cooldown for all users (1 command per 2 seconds)
        self.cooldown_bucket = commands.CooldownMapping.from_cooldown(1, 3, commands.BucketType.user)
        
    async def process_commands(self, message):
        if message.author.bot:
            return

        ctx = await self.get_context(message)
        if ctx.valid and ctx.command:
            # Check cooldown before processing command
            if await check_cooldown(ctx):
                await self.invoke(ctx)

client = CustomBot(command_prefix=get_prefix, intents=intents)

# Remove default help command
client.remove_command('help')

@client.command(name='help')
async def help_command(ctx):
    """Redirects to the documentation website"""
    embed = discord.Embed(
        title="Leurs Bot Documentation",
        description="For a complete list of commands and their usage, please visit our documentation website:",
        color=discord.Color.blue(),
        url="https://docs.leurs.ch"
    )
    
    embed.add_field(
        name="Website",
        value="[docs.leurs.ch](https://docs.leurs.ch)",
        inline=False
    )
    
    embed.set_footer(text="Click the link above to view all commands")
    
    await ctx.send(embed=embed)


@client.command(name='prefix')
@commands.has_permissions(administrator=True)
async def change_prefix(ctx, new_prefix: str):
    """Change the bot's prefix for this server (Admin only)"""
    if len(new_prefix) > 3:
        embed = discord.Embed(
            title="Error",
            description="Prefix must be 3 characters or less!",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    # Load current prefixes
    prefixes = load_prefix_config()
    # Update prefix for this guild
    prefixes[str(ctx.guild.id)] = new_prefix
    
    # Save to file
    with open('data/prefix.json', 'w') as f:
        json.dump(prefixes, f, indent=4)
    
    embed = discord.Embed(
        title="Prefix Updated",
        description=f"Bot prefix has been changed to: `{new_prefix}`",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

@client.event
async def on_command_error(ctx, error):
    # Check if the error was already handled by a cog
    if hasattr(error, "handled") and error.handled:
        return
        
    # Check if the cog has an error handler
    if hasattr(ctx.cog, f"{ctx.command.name}_error"):
        # Let the cog handle the error
        if await ctx.cog.admin_command_error(ctx, error):
            return

    if isinstance(error, commands.CommandNotFound):
        embed = discord.Embed(
            title="Error",
            description=f"Command `{ctx.invoked_with}` not found. Please use a valid command.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="Error",
            description=f"An error occurred: {str(error)}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

async def setup_hook():
    try:
        await client.add_cog(EconomyCog(client))
        await client.add_cog(GamblingCog(client))
        await client.add_cog(OtherCog(client))
        await client.add_cog(JobMarketCog(client))
        await client.add_cog(LevelsCog(client))
        await client.add_cog(AdminCog(client))
        await client.add_cog(LastFMCog(client))
        await client.add_cog(BirthdayCog(client))
        await client.add_cog(TimezoneCog(client))
        await client.add_cog(SnipeCog(client))
        # Add your new cog here
        # await client.add_cog(MyCog(client))
        print("All cogs loaded successfully")
    except Exception as e:
        print(f"Error loading cogs: {e}")

client.setup_hook = setup_hook

@client.event
async def on_ready():
    print('Bot is ready.')
    print(f'Logged in as {client.user.name}')

if __name__ == "__main__":
    load_dotenv()
    token = os.getenv('bot_token')
    
    if token:
        client.run(token)
    else:
        print("Error: Bot token not found.")