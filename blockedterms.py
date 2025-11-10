import discord
from discord.ext import commands
import importlib
import sys
import os
import asyncio

class BlockedTermsCog(commands.Cog):
    """Auto-moderation system for blocked terms"""
    
    def __init__(self, bot):
        self.bot = bot
        self.automod_handler = None
        
        # Initialize file system
        asyncio.create_task(self.initialize())
        
        # Load all individual command modules
        self.load_all_commands()
    
    async def initialize(self):
        """Initialize the blocked terms system"""
        # Get the blockedterms directory path
        blockedterms_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blockedterms")
        
        # Add blockedterms directory to Python path for imports
        if blockedterms_dir not in sys.path:
            sys.path.insert(0, blockedterms_dir)
        
        # Initialize auto-moderation handler
        try:
            automod_module = importlib.import_module("moderation.automod")
            self.automod_handler = automod_module.setup_handler(self, self.bot)
        except Exception as e:
            print(f"❌ Failed to initialize auto-moderation handler: {e}")
    
    def load_all_commands(self):
        """Load all command modules from the blockedterms directory"""
        # Get the blockedterms directory path
        blockedterms_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blockedterms")
        
        # Add blockedterms directory to Python path for imports
        if blockedterms_dir not in sys.path:
            sys.path.insert(0, blockedterms_dir)
        
        # Define all command modules to load
        command_modules = [
            "commands.add_term",
            "commands.remove_term", 
            "commands.list_terms",
        ]
        
        # Load each command module
        for module_path in command_modules:
            try:
                # Import the module
                module = importlib.import_module(module_path)
                
                # Call the setup_command function
                if hasattr(module, "setup_command"):
                    module.setup_command(self)
                    print(f"✅ Loaded blockedterms command: {module_path}")
                else:
                    print(f"⚠️  No setup_command function found in {module_path}")
                    
            except Exception as e:
                print(f"❌ Failed to load blockedterms command {module_path}: {e}")
                import traceback
                traceback.print_exc()
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle incoming messages for auto-moderation"""
        if self.automod_handler:
            await self.automod_handler.handle_message(message)
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Called when the cog is ready"""
        print(f"🛡️ BlockedTermsCog loaded with {len(self.get_commands())} commands")

async def setup(bot):
    """Setup function for the cog"""
    await bot.add_cog(BlockedTermsCog(bot))