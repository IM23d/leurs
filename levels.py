"""
Levels main cog module.
Handles XP gaining, voice tracking, and dynamically loads all level command modules.
"""

import discord
from discord.ext import commands
import os
import importlib
import asyncio
from pathlib import Path

class LevelsCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.command_modules = []
        
        # Initialize helpers - will be set in cog_load
        self.xp_manager = None
        self.data_manager = None
        
        # Voice time tracking task
        self.voice_task = None
        
    async def cog_load(self):
        """Called when the cog is loaded."""
        # Import and initialize helpers
        from levels.helpers.xp_manager import XPManager
        from levels.helpers.data_manager import LevelsDataManager
        
        self.xp_manager = XPManager()
        self.data_manager = LevelsDataManager()
        
        # Start voice time tracker
        self.voice_task = self.client.loop.create_task(self.voice_time_tracker())
        
        # Load all command modules
        await self.load_commands()
        
    def cog_unload(self):
        """Called when the cog is unloaded."""
        if self.voice_task:
            self.voice_task.cancel()
    
    async def load_commands(self):
        """Dynamically load all command modules from the commands directory."""
        commands_dir = Path(__file__).parent / 'levels' / 'commands'
        
        if not commands_dir.exists():
            print(f"Commands directory not found: {commands_dir}")
            return
        
        # Get all Python files in commands directory
        command_files = [f.stem for f in commands_dir.glob('*.py') if not f.stem.startswith('__')]
        
        for command_file in command_files:
            try:
                # Import the command module
                module_path = f'levels.commands.{command_file}'
                module = importlib.import_module(module_path)
                
                # Add the cog to the client
                await module.setup(self.client)
                self.command_modules.append(module_path)
                
                print(f"Loaded Levels command: {command_file}")
                
            except Exception as e:
                print(f"Error loading Levels command {command_file}: {e}")
    
    # Event listeners
    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle XP gain from messages."""
        # Don't process if helpers aren't loaded yet
        if not self.xp_manager:
            return
            
        # Don't process bot messages
        if message.author.bot:
            return
            
        # Don't process commands
        ctx = await self.client.get_context(message)
        if ctx.valid:
            return
            
        # Handle XP gain
        await self.xp_manager.add_xp(message.author, message.channel)
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Handle voice state changes for tracking voice time."""
        # Don't process if helpers aren't loaded yet
        if not self.xp_manager:
            return
            
        if member.bot:  # Ignore bots
            return
            
        user_id = str(member.id)
        
        # User joined a voice channel
        if not before.channel and after.channel and not after.afk:
            self.xp_manager.start_voice_tracking(user_id, after.channel.id)
            
        # User left a voice channel
        elif before.channel and not after.channel:
            self.xp_manager.stop_voice_tracking(user_id)
                
        # User switched channels
        elif before.channel and after.channel and before.channel != after.channel:
            if after.afk:  # Moving to AFK
                self.xp_manager.stop_voice_tracking(user_id)
            elif not after.afk:  # Moving to a non-AFK channel
                if before.afk:  # Coming from AFK
                    self.xp_manager.start_voice_tracking(user_id, after.channel.id)
                else:  # Moving between normal channels
                    self.xp_manager.update_voice_tracking(user_id, after.channel.id)
    
    async def voice_time_tracker(self):
        """Periodic task to update voice time for all active users."""
        try:
            while True:
                # Don't process if helpers aren't loaded yet
                if self.xp_manager:
                    # Save all current voice sessions every 60 seconds
                    self.xp_manager.save_all_voice_sessions()
                
                # Wait for 60 seconds before next update
                await asyncio.sleep(60)
        except asyncio.CancelledError:
            # Handle task cancellation gracefully
            pass
        except Exception as e:
            print(f"Error in voice time tracker: {e}")
            # Restart the task if it fails
            if self.xp_manager:
                self.voice_task = self.client.loop.create_task(self.voice_time_tracker())

async def setup(client):
    """Setup function for the Levels cog."""
    try:
        cog = LevelsCog(client)
        await client.add_cog(cog)
        
        print("Levels cog and commands loaded successfully")
        
    except Exception as e:
        print(f"Error loading Levels cog: {e}")

async def teardown(client):
    """Teardown function for the Levels cog."""
    try:
        cog = client.get_cog('LevelsCog')
        if cog:
            await client.remove_cog('LevelsCog')
        
        print("Levels cog unloaded successfully")
        
    except Exception as e:
        print(f"Error unloading Levels cog: {e}")
