"""
Other main cog module.
Handles various utility commands and functionality like reminders, AFK, typing tests, etc.
Dynamically loads all other command modules.
"""

import discord
from discord.ext import commands
import os
import importlib
import asyncio
import time
from pathlib import Path

class OtherCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.command_modules = []
        
        # Initialize helpers - will be set in cog_load
        self.data_manager = None
        self.reminder_manager = None
        self.afk_manager = None
        self.typing_manager = None
        self.image_manager = None
        self.ai_manager = None
        self.weather_manager = None
        self.utils = None
        
        # Store references to command cogs for setting managers
        self.command_cogs = {}
        
    async def cog_load(self):
        """Called when the cog is loaded."""
        # Import and initialize helpers
        from other_commands.helpers.data_manager import OtherDataManager
        from other_commands.helpers.reminder_manager import ReminderManager
        from other_commands.helpers.afk_manager import AFKManager
        from other_commands.helpers.typing_manager import TypingManager
        from other_commands.helpers.image_manager import ImageManager
        from other_commands.helpers.ai_manager import AIManager
        from other_commands.helpers.weather_manager import WeatherManager
        from other_commands.helpers.utils import OtherUtils
        
        self.data_manager = OtherDataManager()
        self.reminder_manager = ReminderManager(self.client)
        self.afk_manager = AFKManager()
        self.typing_manager = TypingManager()
        self.image_manager = ImageManager()
        self.ai_manager = AIManager()
        self.weather_manager = WeatherManager()
        self.utils = OtherUtils()
        
        # Load all command modules
        await self.load_commands()
        
        # Set up managers for command cogs
        await self.setup_command_managers()
        
    async def load_commands(self):
        """Dynamically load all command modules from the commands directory."""
        # Get all command files from the other/commands directory
        commands_dir = Path(__file__).parent / "other_commands" / "commands"
        
        if not commands_dir.exists():
            print(f"Commands directory not found: {commands_dir}")
            return
        
        # Get all Python files in commands directory
        command_files = [f.stem for f in commands_dir.glob('*.py') if not f.stem.startswith('__')]
        
        for command_file in command_files:
            try:
                # Import the command module
                module_path = f'other_commands.commands.{command_file}'
                module = importlib.import_module(module_path)
                
                # Add the cog to the client
                await module.setup(self.client)
                self.command_modules.append(module_path)
                
                print(f"Loaded Other command: {command_file}")
                
            except Exception as e:
                print(f"Error loading Other command {command_file}: {e}")
                
    async def setup_command_managers(self):
        """Set up managers for command cogs after they're loaded."""
        # Wait a moment for cogs to be fully loaded
        await asyncio.sleep(0.1)
        
        # Set up managers for specific command cogs
        reminder_cog = self.client.get_cog('RemindMeCommand')
        if reminder_cog and hasattr(reminder_cog, 'set_reminder_manager'):
            reminder_cog.set_reminder_manager(self.reminder_manager)
            
        afk_cog = self.client.get_cog('AFKCommand')
        if afk_cog and hasattr(afk_cog, 'set_afk_manager'):
            afk_cog.set_afk_manager(self.afk_manager)
            
        quote_cog = self.client.get_cog('QuoteCommand')
        if quote_cog and hasattr(quote_cog, 'set_utils'):
            quote_cog.set_utils(self.utils)
            
        weather_cog = self.client.get_cog('WeatherCommand')
        if weather_cog and hasattr(weather_cog, 'set_weather_manager'):
            weather_cog.set_weather_manager(self.weather_manager)
            
        ai_cog = self.client.get_cog('AICommand')
        if ai_cog and hasattr(ai_cog, 'set_ai_manager'):
            ai_cog.set_ai_manager(self.ai_manager)
            
        image_cog = self.client.get_cog('ImageCommand')
        if image_cog and hasattr(image_cog, 'set_managers'):
            image_cog.set_managers(self.image_manager, self.utils)
    
    # Event listeners
    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle AFK status and typing test responses."""
        if message.author.bot:
            return

        # Check if the message author was AFK and is now back
        if self.afk_manager and self.afk_manager.is_afk(message.author.id):
            afk_info = self.afk_manager.remove_afk(message.author.id)
            if afk_info:
                reason, time_text = afk_info
                embed = discord.Embed(
                    description=f"👋 {message.author.mention} has returned after being AFK for {time_text}",
                    color=0x00FF00
                )
                await message.channel.send(embed=embed)
            
        # Check if any mentioned users are AFK
        if self.afk_manager:
            for mention in message.mentions:
                if self.afk_manager.is_afk(mention.id):
                    afk_info = self.afk_manager.get_afk_info(mention.id)
                    if afk_info:
                        reason, time_text = afk_info
                        embed = discord.Embed(
                            description=f"{mention.mention} is AFK: {reason} - Been Away for {time_text}",
                            color=0xFF0000
                        )
                        await message.channel.send(embed=embed)
        
        # Check if this is a response to a typing test
        if self.typing_manager and self.typing_manager.is_user_typing(message.author.id):
            await self.handle_typing_response(message)
            
    async def handle_typing_response(self, message):
        """Handle typing test response."""
        try:
            # Calculate results
            result = self.typing_manager.calculate_results(message.author.id, message.content.strip())
            
            if not result:
                return
                
            # Check if this is part of a challenge
            challenge_id = result.get("challenge_id")
            
            if challenge_id and challenge_id in self.typing_manager.typing_challenges:
                # Add result to challenge
                self.typing_manager.add_challenge_result(challenge_id, message.author.id, result)
                
                # Check if both users have completed the challenge
                if self.typing_manager.is_challenge_complete(challenge_id):
                    # Both users completed, compare results
                    await self.show_challenge_results(message.channel, challenge_id)
                    self.typing_manager.remove_challenge(challenge_id)
                else:
                    # Only one user completed
                    embed = self.utils.create_typing_result_embed(result, message.author)
                    embed.add_field(
                        name="Challenge Status",
                        value="Waiting for opponent to complete the test...",
                        inline=False
                    )
                    await message.channel.send(embed=embed)
            else:
                # Regular typing test
                embed = self.utils.create_typing_result_embed(result, message.author)
                await message.channel.send(embed=embed)
                
            # Remove the test from active tests
            self.typing_manager.finish_typing_test(message.author.id)
            
        except Exception as e:
            print(f"Error handling typing response: {e}")
            
    async def show_challenge_results(self, channel, challenge_id):
        """Show typing challenge results comparison."""
        try:
            results_data = self.typing_manager.get_challenge_results(challenge_id)
            
            if not results_data:
                await channel.send("Could not retrieve challenge results.")
                return
                
            # Get the users
            try:
                winner = await self.client.fetch_user(results_data["winner_id"])
                loser = await self.client.fetch_user(results_data["loser_id"])
            except:
                await channel.send("Could not find the users for this challenge.")
                return
                
            # Create results embed
            embed = discord.Embed(
                title="⚔️ Typing Challenge Results",
                description=f"**{winner.display_name}** wins the typing challenge!",
                color=0xFFD700  # Gold
            )
            
            # Add winner's results
            winner_result = results_data["winner_result"]
            embed.add_field(
                name=f"{winner.display_name}'s Results",
                value=f"• Speed: **{winner_result['wpm']:.1f}** WPM\n"
                     f"• Accuracy: **{winner_result['accuracy']:.1f}%**\n"
                     f"• Time: **{winner_result['time']:.1f}s**",
                inline=True
            )
            
            # Add loser's results
            loser_result = results_data["loser_result"]
            embed.add_field(
                name=f"{loser.display_name}'s Results",
                value=f"• Speed: **{loser_result['wpm']:.1f}** WPM\n"
                     f"• Accuracy: **{loser_result['accuracy']:.1f}%**\n"
                     f"• Time: **{loser_result['time']:.1f}s**",
                inline=True
            )
            
            # Add difference
            embed.add_field(
                name="Difference",
                value=f"• Speed: **{results_data['wpm_diff']:.1f}** WPM\n"
                     f"• Accuracy: **{results_data['accuracy_diff']:.1f}%**",
                inline=False
            )
            
            # Add analysis message
            wpm_diff = results_data['wpm_diff']
            if wpm_diff < 5:
                message = "A very close match! Both typists are evenly matched."
            elif wpm_diff < 15:
                message = f"{winner.display_name} has a slight edge in typing speed."
            elif wpm_diff < 30:
                message = f"{winner.display_name} is notably faster than {loser.display_name}."
            else:
                message = f"{winner.display_name} completely outclassed {loser.display_name} in this challenge!"
                
            embed.add_field(name="Analysis", value=message, inline=False)
            embed.set_footer(text=f"Challenge completed | {results_data['word_count']} words")
            
            await channel.send(embed=embed)
            
        except Exception as e:
            print(f"Error showing challenge results: {e}")

async def setup(client):
    """Setup function for the Other cog."""
    try:
        cog = OtherCog(client)
        await client.add_cog(cog)
        
        print("Other cog and commands loaded successfully")
        
    except Exception as e:
        print(f"Error loading Other cog: {e}")

async def teardown(client):
    """Teardown function for the Other cog."""
    try:
        cog = client.get_cog('OtherCog')
        if cog:
            await client.remove_cog('OtherCog')
        
        print("Other cog unloaded successfully")
        
    except Exception as e:
        print(f"Error unloading Other cog: {e}")
