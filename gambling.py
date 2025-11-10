"""
Gambling main cog module.
Handles gambling games and betting functionality.
Dynamically loads all gambling command modules and integrates with the economy system.
"""

import discord
from discord.ext import commands
import os
import importlib
import asyncio
from pathlib import Path

class GamblingCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.command_modules = []
        
        # Initialize helpers - will be set in cog_load
        self.data_manager = None
        
    async def cog_load(self):
        """Called when the cog is loaded."""
        # Import and initialize helpers
        from gambling.helpers.data_manager import GamblingDataManager
        
        self.data_manager = GamblingDataManager()
        
        # Load all command modules
        await self.load_commands()
        
    async def load_commands(self):
        """Dynamically load all command modules from the gambling directory."""
        gambling_dir = Path(__file__).parent / 'gambling'
        
        if not gambling_dir.exists():
            print(f"Gambling directory not found: {gambling_dir}")
            return
        
        # Define subdirectories to load from
        subdirs = ['commands']
        
        for subdir in subdirs:
            subdir_path = gambling_dir / subdir
            if not subdir_path.exists():
                continue
                
            # Get all Python files in subdirectory
            command_files = [f.stem for f in subdir_path.glob('*.py') if not f.stem.startswith('__')]
            
            for command_file in command_files:
                try:
                    # Import the command module
                    module_path = f'gambling.{subdir}.{command_file}'
                    module = importlib.import_module(module_path)
                    
                    # Check if module has a command class to add
                    if hasattr(module, 'GambleCommand'):
                        command_class = getattr(module, 'GambleCommand')
                        if issubclass(command_class, commands.Cog):
                            # Add the command cog to the client
                            command_cog = command_class(self.client)
                            await self.client.add_cog(command_cog)
                            self.command_modules.append(module_path)
                            print(f"Loaded Gambling command: {subdir}/{command_file}")
                    else:
                        print(f"Warning: Gambling command {subdir}/{command_file} has no recognized command class")
                        
                except Exception as e:
                    print(f"Error loading Gambling command {subdir}/{command_file}: {e}")
    
    # Global gambling error handler
    async def gambling_command_error(self, ctx, error):
        """Handle errors for gambling commands."""
        if isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="❌ Invalid Amount",
                description="Please provide a valid amount. You can use numbers, 'all', or percentages like '50%'.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return True
        elif isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                title="⏰ Cooldown Active",
                description=f"Please wait {error.retry_after:.1f} seconds before gambling again.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            return True
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="❌ Missing Amount",
                description="Please specify an amount to gamble. Example: `!gamble 100` or `!gamble all`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return True
        
        # Return False to let the global error handler deal with it
        return False

async def setup(client):
    """Setup function for the Gambling cog."""
    try:
        cog = GamblingCog(client)
        await client.add_cog(cog)
        
        print("Gambling cog and commands loaded successfully")
        
    except Exception as e:
        print(f"Error loading Gambling cog: {e}")

async def teardown(client):
    """Teardown function for the Gambling cog."""
    try:
        # Remove main cog
        cog = client.get_cog('GamblingCog')
        if cog:
            await client.remove_cog('GamblingCog')
        
        # Remove command cogs
        gamble_cog = client.get_cog('GambleCommand')
        if gamble_cog:
            await client.remove_cog('GambleCommand')
        
        print("Gambling cog unloaded successfully")
        
    except Exception as e:
        print(f"Error unloading Gambling cog: {e}")
