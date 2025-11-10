"""
Jobs main cog module.
Handles job market functionality with comprehensive job management system.
Dynamically loads all job command modules and provides economy integration.
"""

import discord
from discord.ext import commands
import os
import importlib
import asyncio
from pathlib import Path

class JobMarketCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.command_modules = []
        self.command_cogs = {}
        
        # Initialize helpers - will be set in cog_load
        self.data_manager = None
        self.utils = None
        
    async def cog_load(self):
        """Called when the cog is loaded."""
        # Import and initialize helpers
        from jobs.helpers.data_manager import JobDataManager
        from jobs.helpers.utils import JobUtils
        
        self.data_manager = JobDataManager()
        self.utils = JobUtils()
        
        # Load all command modules
        await self.load_commands()
        
        # Set up managers for command cogs
        await self.setup_command_managers()
        
    async def load_commands(self):
        """Dynamically load all command modules from the jobs directory."""
        jobs_dir = Path(__file__).parent / 'jobs'
        
        if not jobs_dir.exists():
            print(f"Jobs directory not found: {jobs_dir}")
            return
        
        # Get all Python files in commands subdirectory
        commands_path = jobs_dir / 'commands'
        if not commands_path.exists():
            return
            
        command_files = [f.stem for f in commands_path.glob('*.py') if not f.stem.startswith('__')]
        
        for command_file in command_files:
            try:
                # Import the command module
                module_path = f'jobs.commands.{command_file}'
                module = importlib.import_module(module_path)
                
                # Get all classes in the module that are command cogs
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        issubclass(attr, commands.Cog) and 
                        attr != commands.Cog and
                        'Command' in attr.__name__):
                        
                        # Create instance and add to client
                        command_cog = attr(self.client)
                        await self.client.add_cog(command_cog)
                        
                        # Store reference for manager setup
                        self.command_cogs[command_file] = command_cog
                        self.command_modules.append(module_path)
                        
                        print(f"Loaded Jobs command: {command_file}")
                        break
                        
            except Exception as e:
                print(f"Error loading Jobs command {command_file}: {e}")
                
    async def setup_command_managers(self):
        """Set up managers for command cogs after they're loaded."""
        # Wait a moment for cogs to be fully loaded
        await asyncio.sleep(0.1)
        
        # Set managers on command cogs that need them
        for command_name, command_cog in self.command_cogs.items():
            try:
                # Set data manager on all command cogs
                if hasattr(command_cog, 'set_job_manager'):
                    command_cog.set_job_manager(self.data_manager)
                
                # Set utils on command cogs that need them
                if hasattr(command_cog, 'set_utils'):
                    command_cog.set_utils(self.utils)
                    
            except Exception as e:
                print(f"Error setting up managers for {command_name}: {e}")
    
    # Global jobs error handler
    async def jobs_command_error(self, ctx, error):
        """Handle errors for jobs commands."""
        if isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="❌ Invalid Input",
                description="Please check your input and try again. Use `!jobs` to see available jobs.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return True
        elif isinstance(error, commands.MissingRequiredArgument):
            if 'job_name' in str(error):
                embed = discord.Embed(
                    title="❌ Missing Job Name",
                    description="Please specify a job name. Example: `!buyjob Artist`",
                    color=discord.Color.red()
                )
            elif 'page' in str(error):
                embed = discord.Embed(
                    title="❌ Invalid Page",
                    description="Please provide a valid page number. Example: `!jobs 2`",
                    color=discord.Color.red()
                )
            else:
                embed = discord.Embed(
                    title="❌ Missing Required Argument",
                    description=str(error),
                    color=discord.Color.red()
                )
            await ctx.send(embed=embed)
            return True
        elif isinstance(error, commands.CommandOnCooldown):
            hours = int(error.retry_after // 3600)
            minutes = int((error.retry_after % 3600) // 60)
            seconds = int(error.retry_after % 60)
            
            time_str = []
            if hours > 0:
                time_str.append(f"{hours} hour{'s' if hours != 1 else ''}")
            if minutes > 0:
                time_str.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
            if seconds > 0:
                time_str.append(f"{seconds} second{'s' if seconds != 1 else ''}")
                
            embed = discord.Embed(
                title="⏰ Work Cooldown Active",
                description=f"You can work again in {', '.join(time_str)}.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            return True
        
        # Return False to let the global error handler deal with it
        return False

async def setup(client):
    """Setup function for the Jobs cog."""
    try:
        cog = JobMarketCog(client)
        await client.add_cog(cog)
        
        print("Jobs cog and commands loaded successfully")
        
    except Exception as e:
        print(f"Error loading Jobs cog: {e}")

async def teardown(client):
    """Teardown function for the Jobs cog."""
    try:
        # Remove main cog
        cog = client.get_cog('JobMarketCog')
        if cog:
            await client.remove_cog('JobMarketCog')
        
        # Remove command cogs
        command_cog_names = [
            'ViewJobsCommand', 'BuyJobCommand', 'RemoveJobCommand', 
            'WorkCommand', 'MyJobsCommand'
        ]
        
        for cog_name in command_cog_names:
            command_cog = client.get_cog(cog_name)
            if command_cog:
                await client.remove_cog(cog_name)
        
        print("Jobs cog unloaded successfully")
        
    except Exception as e:
        print(f"Error unloading Jobs cog: {e}")