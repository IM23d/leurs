"""
Admin main cog module.
Handles administrative commands and functionality.
Dynamically loads all admin command modules.
"""

import discord
from discord.ext import commands
import os
import importlib
import asyncio
from pathlib import Path

class AdminCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.command_modules = []
        
        # Initialize helpers - will be set in cog_load
        self.data_manager = None
        
    async def cog_load(self):
        """Called when the cog is loaded."""
        # Import and initialize helpers
        from admin.helpers.data_manager import DataManager
        
        self.data_manager = DataManager()
        
        # Load all command modules
        await self.load_commands()
        
    async def load_commands(self):
        """Dynamically load all command modules from the admin directory."""
        admin_dir = Path(__file__).parent / 'admin'
        
        if not admin_dir.exists():
            print(f"Admin directory not found: {admin_dir}")
            return
        
        # Define subdirectories to load from
        subdirs = ['moderation', 'users', 'channels', 'utility', 'economy', 'roles']
        
        for subdir in subdirs:
            subdir_path = admin_dir / subdir
            if not subdir_path.exists():
                continue
                
            # Get all Python files in subdirectory
            command_files = [f.stem for f in subdir_path.glob('*.py') if not f.stem.startswith('__')]
            
            for command_file in command_files:
                try:
                    # Import the command module
                    module_path = f'admin.{subdir}.{command_file}'
                    module = importlib.import_module(module_path)
                    
                    # Check if module has setup_command function
                    if hasattr(module, 'setup_command'):
                        setup_func = getattr(module, 'setup_command')
                        if callable(setup_func):
                            setup_func(self)
                            self.command_modules.append(module_path)
                            print(f"Loaded Admin command: {subdir}/{command_file}")
                    else:
                        print(f"Warning: Admin command {subdir}/{command_file} has no setup_command function")
                        
                except Exception as e:
                    print(f"Error loading Admin command {subdir}/{command_file}: {e}")
    
    # Global admin error handler
    async def admin_command_error(self, ctx, error):
        """Handle errors for admin commands."""
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You don't have permission to use this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return True
        elif isinstance(error, commands.MemberNotFound):
            embed = discord.Embed(
                title="❌ Member Not Found",
                description="The specified member could not be found.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return True
        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="❌ Invalid Argument",
                description=str(error),
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return True
        
        # Return False to let the global error handler deal with it
        return False

async def setup(client):
    """Setup function for the Admin cog."""
    try:
        cog = AdminCog(client)
        await client.add_cog(cog)
        
        print("Admin cog and commands loaded successfully")
        
    except Exception as e:
        print(f"Error loading Admin cog: {e}")

async def teardown(client):
    """Teardown function for the Admin cog."""
    try:
        cog = client.get_cog('AdminCog')
        if cog:
            await client.remove_cog('AdminCog')
        
        print("Admin cog unloaded successfully")
        
    except Exception as e:
        print(f"Error unloading Admin cog: {e}")
