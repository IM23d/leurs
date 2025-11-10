"""
Birthday main cog module.
Handles birthday management and message snipe functionality.
Dynamically loads all birthday command modules.
"""

import discord
from discord.ext import commands
import os
import importlib
import asyncio
from pathlib import Path

class BirthdayCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.command_modules = []
        
        # Initialize helpers - will be set in cog_load
        self.data_manager = None
        self.snipe_manager = None
        
    async def cog_load(self):
        """Called when the cog is loaded."""
        # Import and initialize helpers
        from birthday.helpers.data_manager import BirthdayDataManager
        from birthday.helpers.snipe_manager import SnipeManager
        
        self.data_manager = BirthdayDataManager()
        self.snipe_manager = SnipeManager()
        
        # Load all command modules
        await self.load_commands()
        
        # Set up managers for command cogs
        await self.setup_command_managers()
        
    async def load_commands(self):
        """Dynamically load all command modules from the birthday directory."""
        birthday_dir = Path(__file__).parent / 'birthday'
        
        if not birthday_dir.exists():
            print(f"Birthday directory not found: {birthday_dir}")
            return
        
        # Define subdirectories to load from
        subdirs = ['commands', 'snipe']
        
        for subdir in subdirs:
            subdir_path = birthday_dir / subdir
            if not subdir_path.exists():
                continue
                
            # Get all Python files in subdirectory
            command_files = [f.stem for f in subdir_path.glob('*.py') if not f.stem.startswith('__')]
            
            for command_file in command_files:
                try:
                    # Import the command module
                    module_path = f'birthday.{subdir}.{command_file}'
                    module = importlib.import_module(module_path)
                    
                    # Check if module has setup_command function
                    if hasattr(module, 'setup_command'):
                        setup_func = getattr(module, 'setup_command')
                        if callable(setup_func):
                            setup_func(self)
                            self.command_modules.append(module_path)
                            print(f"Loaded Birthday command: {subdir}/{command_file}")
                    else:
                        print(f"Warning: Birthday command {subdir}/{command_file} has no setup_command function")
                        
                except Exception as e:
                    print(f"Error loading Birthday command {subdir}/{command_file}: {e}")
                    
    async def setup_command_managers(self):
        """Set up managers for command cogs after they're loaded."""
        # Wait a moment for cogs to be fully loaded
        await asyncio.sleep(0.1)
        
        # Find snipe command cogs and set up their managers
        for command_module_path in self.command_modules:
            if 'snipe' in command_module_path:
                try:
                    # Re-import the module to access the command class
                    module = importlib.import_module(command_module_path)
                    
                    # For snipe commands, we need to pass the snipe_manager to the command class
                    # This is done during the command loading process
                    
                except Exception as e:
                    print(f"Error setting up managers for {command_module_path}: {e}")
    
    # Event listener for message deletion (snipe functionality)
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """Handle message deletion for snipe functionality."""
        if not self.snipe_manager:
            return
            
        # Don't track bot messages
        if message.author.bot:
            return
            
        # Store the deleted message
        self.snipe_manager.store_message(
            channel_id=message.channel.id,
            author=message.author,
            content=message.content,
            attachments=[att.url for att in message.attachments],
            embeds=message.embeds
        )

async def setup(client):
    """Setup function for the Birthday cog."""
    try:
        cog = BirthdayCog(client)
        await client.add_cog(cog)
        
        print("Birthday cog and commands loaded successfully")
        
    except Exception as e:
        print(f"Error loading Birthday cog: {e}")

async def teardown(client):
    """Teardown function for the Birthday cog."""
    try:
        cog = client.get_cog('BirthdayCog')
        if cog:
            await client.remove_cog('BirthdayCog')
        
        print("Birthday cog unloaded successfully")
        
    except Exception as e:
        print(f"Error unloading Birthday cog: {e}")