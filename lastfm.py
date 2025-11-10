"""
LastFM main cog module.
Dynamically loads all LastFM command modules.
"""

import discord
from discord.ext import commands
import os
import importlib
from pathlib import Path

class LastFMCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.command_modules = []
        
        # Ensure data directory exists
        if not os.path.exists('data'):
            os.makedirs('data')

    async def cog_load(self):
        """Called when the cog is loaded."""
        # Load all command modules
        await self.load_commands()

    async def load_commands(self):
        """Dynamically load all command modules from the commands directory."""
        commands_dir = Path(__file__).parent / 'lastfm' / 'commands'
        
        if not commands_dir.exists():
            print(f"Commands directory not found: {commands_dir}")
            return
        
        # Get all Python files in commands directory
        command_files = [f.stem for f in commands_dir.glob('*.py') if not f.stem.startswith('__')]
        
        for command_file in command_files:
            try:
                # Import the command module
                module_path = f'lastfm.commands.{command_file}'
                module = importlib.import_module(module_path)
                
                # Add the cog to the client
                await module.setup(self.client)
                self.command_modules.append(module_path)
                
                print(f"Loaded LastFM command: {command_file}")
                
            except Exception as e:
                print(f"Error loading LastFM command {command_file}: {e}")

    async def unload_commands(self):
        """Unload all dynamically loaded command modules."""
        for module_path in self.command_modules:
            try:
                # Get the cog class name from the module
                module = importlib.import_module(module_path)
                
                # Find the cog class in the module
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        issubclass(attr, commands.Cog) and 
                        attr != commands.Cog):
                        
                        cog_name = attr.__name__
                        await self.client.remove_cog(cog_name)
                        break
                        
            except Exception as e:
                print(f"Error unloading LastFM command module {module_path}: {e}")

async def setup(client):
    """Setup function for the LastFM cog."""
    try:
        cog = LastFMCog(client)
        await client.add_cog(cog)
        
        # Load all command modules
        await cog.load_commands()
        
        print("LastFM cog and commands loaded successfully")
        
    except Exception as e:
        print(f"Error loading LastFM cog: {e}")

async def teardown(client):
    """Teardown function for the LastFM cog."""
    try:
        cog = client.get_cog('LastFMCog')
        if cog:
            await cog.unload_commands()
            await client.remove_cog('LastFMCog')
        
        print("LastFM cog unloaded successfully")
        
    except Exception as e:
        print(f"Error unloading LastFM cog: {e}")
