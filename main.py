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

# Import available cogs - only those that have main cog files
# Import only essential modules for testing
from other import OtherCog

# Temporarily disabled imports (add back later):
# from gambling import GamblingCog
# from jobs import JobMarketCog
# from levels import LevelsCog
# from admin import AdminCog
# from lastfm import LastFMCog
# from birthday import BirthdayCog
# from timezone import TimezoneCog
# from blockedterms import BlockedTermsCog
# Import your new cog here
# from mycog import MyCog

# Note: economy and snipe are integrated into other modules
# - Economy functionality is integrated into other modules
# - Snipe functionality is part of the birthday module

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
        # Create a global cooldown for all users (1 command per 3 seconds)
        self.cooldown_bucket = commands.CooldownMapping.from_cooldown(1, 3, commands.BucketType.user)
        self.cogs_loaded = False

client = CustomBot(command_prefix=get_prefix, intents=intents)

# Remove default help command
client.remove_command('help')

@client.command(name='help')
async def help_command(ctx):
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
async def on_message(message):
    # Don't process bot messages
    if message.author.bot:
        return
    
    # Process commands normally - this handles cooldowns through the command system
    await client.process_commands(message)

@client.event
async def on_command_error(ctx, error):
    # Check if the error was already handled by a cog
    if hasattr(error, "handled") and error.handled:
        return
        
    # Check if the cog has specific error handlers
    if ctx.cog:
        # AdminCog has admin_command_error
        if hasattr(ctx.cog, 'admin_command_error'):
            if await ctx.cog.admin_command_error(ctx, error):
                return
        # GamblingCog has gambling_command_error  
        elif hasattr(ctx.cog, 'gambling_command_error'):
            if await ctx.cog.gambling_command_error(ctx, error):
                return
        # JobMarketCog has jobs_command_error
        elif hasattr(ctx.cog, 'jobs_command_error'):
            if await ctx.cog.jobs_command_error(ctx, error):
                return
        # Other cogs might have their own error handlers
        elif hasattr(ctx.cog, f"{type(ctx.cog).__name__.lower()}_command_error"):
            error_handler = getattr(ctx.cog, f"{type(ctx.cog).__name__.lower()}_command_error")
            if await error_handler(ctx, error):
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

@client.event
async def on_ready():
    # Load cogs only once
    if not client.cogs_loaded:
        try:
            print("🧪 Loading cogs...", flush=True)
            
            other_cog = OtherCog(client)
            client.add_cog(other_cog)
            
            # Call cog_load manually for OtherCog
            if hasattr(other_cog, 'cog_load'):
                await other_cog.cog_load()
            
            print("✅ OtherCog loaded successfully", flush=True)
            
            # Temporarily disabled cogs (uncomment to enable):
            # from gambling import GamblingCog
            # await client.add_cog(GamblingCog(client))
            # from jobs import JobMarketCog
            # await client.add_cog(JobMarketCog(client))
            # from levels import LevelsCog
            # await client.add_cog(LevelsCog(client))
            # from admin import AdminCog
            # await client.add_cog(AdminCog(client))
            # from lastfm import LastFMCog
            # await client.add_cog(LastFMCog(client))
            # from birthday import BirthdayCog
            # await client.add_cog(BirthdayCog(client))
            # from timezone import TimezoneCog
            # await client.add_cog(TimezoneCog(client))
            # from blockedterms import BlockedTermsCog
            # await client.add_cog(BlockedTermsCog(client))
            
            client.cogs_loaded = True
            
        except Exception as e:
            print(f"❌ Error loading cogs: {e}", flush=True)
            import traceback
            traceback.print_exc()
    
    print('Bot is ready.', flush=True)
    print(f'Logged in as {client.user.name}', flush=True)
    print(f'📋 Commands available: {[cmd.name for cmd in client.commands]}', flush=True)
    print(f'📋 Cogs loaded: {list(client.cogs.keys())}', flush=True)

if __name__ == "__main__":
    load_dotenv()
    token = os.getenv('DISCORD_TOKEN')
    
    if token:
        client.run(token)
    else:
        print("Error: Bot token not found.")
