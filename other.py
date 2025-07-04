import discord
from discord.ext import commands
import random
import os
from datetime import datetime, timedelta
import time
import re
import asyncio
from typing import Optional, Tuple, Dict, List, Union
import pytz
import requests
import io
from PIL import Image, ImageDraw, ImageFont
import textwrap
import traceback
import json
import collections
import base64

class OtherCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.afk_users = {}  # Store user_id: (reason, timestamp, command_timestamp)
        self.reminder_tasks = {}  # Store user_id: list of asyncio tasks
        self.google_api_key = os.getenv("GOOGLE_API_KEY", "")
        self.google_cse_id = os.getenv("GOOGLE_CSE_ID", "")
        self.image_search_cache = {}  # Store search results: query: [list of image URLs]
        self.active_image_searches = {}  # Store active searches: message_id: (query, current_index)
        self.max_cache_size = 50  # Maximum number of queries to cache
        
        # Rate limiting for image search
        self.daily_search_count = 0  # Count of searches today
        self.last_count_reset = datetime.now()  # When the count was last reset
        self.user_cooldowns = {}  # Store user_id: last_use_timestamp
        self.cooldown_time = 300  # 5 minutes in seconds
        self.daily_limit = 100  # Google's free tier limit
        
        # For AI command
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", "")
        self.ai_user_cooldowns = {}  # Store user_id: last_use_timestamp
        self.ai_cooldown_time = 30  # 30 seconds cooldown
        self.ai_daily_usage = {}  # Store user_id: count
        self.ai_daily_limit = 30  # 30 requests per day
        self.ai_last_reset = datetime.now()  # When the count was last reset
        
        # For monkeytype command
        self.active_typing_tests = {}  # Store user_id: {"words": [], "start_time": datetime, "message_id": int}
        self.typing_challenges = {}  # Store challenge_id: {"challenger": user_id, "challenged": user_id, "word_count": int, "words": [], "results": {}}
        self.pending_challenges = {}  # Store challenged_user_id: [list of challenge_ids]
        self.common_words = [
            "the", "be", "to", "of", "and", "a", "in", "that", "have", "I", "it", "for", "not", "on", "with", "he", "as", 
            "you", "do", "at", "this", "but", "his", "by", "from", "they", "we", "say", "her", "she", "or", "an", "will", 
            "my", "one", "all", "would", "there", "their", "what", "so", "up", "out", "if", "about", "who", "get", "which", 
            "go", "me", "when", "make", "can", "like", "time", "no", "just", "him", "know", "take", "people", "into", "year", 
            "your", "good", "some", "could", "them", "see", "other", "than", "then", "now", "look", "only", "come", "its", 
            "over", "think", "also", "back", "after", "use", "two", "how", "our", "work", "first", "well", "way", "even", 
            "new", "want", "because", "any", "these", "give", "day", "most", "us", "is", "was", "were", "are", "has", "had", 
            "been", "being", "am", "did", "does", "doing", "done", "should", "must", "might", "may", "shall", "can", "could", 
            "would", "should", "ought", "need", "dare", "used", "going", "let", "help", "keep", "try", "start", "stop", 
            "begin", "end", "continue", "finish", "complete", "succeed", "fail", "win", "lose", "find", "search", "seek", 
            "try", "attempt", "avoid", "achieve", "accomplish", "reach", "attain", "obtain", "acquire", "get", "gain", 
            "earn", "receive", "accept", "reject", "refuse", "deny", "admit", "acknowledge", "recognize", "identify", 
            "understand", "comprehend", "grasp", "know", "learn", "study", "teach", "instruct", "educate", "train", 
            "develop", "improve", "enhance", "increase", "decrease", "reduce", "lower", "raise", "lift", "elevate", 
            "climb", "ascend", "descend", "fall", "drop", "sink", "rise", "grow", "expand", "shrink", "contract", 
            "condense", "compress", "squeeze", "stretch", "extend", "spread", "distribute", "gather", "collect", 
            "accumulate", "amass", "assemble", "build", "construct", "create", "design", "develop", "invent", 
            "discover", "explore", "investigate", "research", "analyze", "examine", "inspect", "observe", "watch", 
            "monitor", "track", "follow", "lead", "guide", "direct", "manage", "control", "regulate", "govern", 
            "rule", "dominate", "influence", "affect", "impact", "change", "alter", "modify", "transform"
        ]
        
        # Language codes for translation
        self.language_codes = {
            "af": "Afrikaans",
            "sq": "Albanian",
            "am": "Amharic",
            "ar": "Arabic",
            "hy": "Armenian",
            "az": "Azerbaijani",
            "eu": "Basque",
            "be": "Belarusian",
            "bn": "Bengali",
            "bs": "Bosnian",
            "bg": "Bulgarian",
            "ca": "Catalan",
            "ceb": "Cebuano",
            "ny": "Chichewa",
            "zh": "Chinese",
            "co": "Corsican",
            "hr": "Croatian",
            "cs": "Czech",
            "da": "Danish",
            "nl": "Dutch",
            "en": "English",
            "eo": "Esperanto",
            "et": "Estonian",
            "tl": "Filipino",
            "fi": "Finnish",
            "fr": "French",
            "fy": "Frisian",
            "gl": "Galician",
            "ka": "Georgian",
            "de": "German",
            "el": "Greek",
            "gu": "Gujarati",
            "ht": "Haitian Creole",
            "ha": "Hausa",
            "haw": "Hawaiian",
            "iw": "Hebrew",
            "he": "Hebrew",
            "hi": "Hindi",
            "hmn": "Hmong",
            "hu": "Hungarian",
            "is": "Icelandic",
            "ig": "Igbo",
            "id": "Indonesian",
            "ga": "Irish",
            "it": "Italian",
            "ja": "Japanese",
            "jw": "Javanese",
            "kn": "Kannada",
            "kk": "Kazakh",
            "km": "Khmer",
            "ko": "Korean",
            "ku": "Kurdish",
            "ky": "Kyrgyz",
            "lo": "Lao",
            "la": "Latin",
            "lv": "Latvian",
            "lt": "Lithuanian",
            "lb": "Luxembourgish",
            "mk": "Macedonian",
            "mg": "Malagasy",
            "ms": "Malay",
            "ml": "Malayalam",
            "mt": "Maltese",
            "mi": "Maori",
            "mr": "Marathi",
            "mn": "Mongolian",
            "my": "Myanmar",
            "ne": "Nepali",
            "no": "Norwegian",
            "or": "Odia",
            "ps": "Pashto",
            "fa": "Persian",
            "pl": "Polish",
            "pt": "Portuguese",
            "pa": "Punjabi",
            "ro": "Romanian",
            "ru": "Russian",
            "sm": "Samoan",
            "gd": "Scots Gaelic",
            "sr": "Serbian",
            "st": "Sesotho",
            "sn": "Shona",
            "sd": "Sindhi",
            "si": "Sinhala",
            "sk": "Slovak",
            "sl": "Slovenian",
            "so": "Somali",
            "es": "Spanish",
            "su": "Sundanese",
            "sw": "Swahili",
            "sv": "Swedish",
            "tg": "Tajik",
            "ta": "Tamil",
            "te": "Telugu",
            "th": "Thai",
            "tr": "Turkish",
            "uk": "Ukrainian",
            "ur": "Urdu",
            "ug": "Uyghur",
            "uz": "Uzbek",
            "vi": "Vietnamese",
            "cy": "Welsh",
            "xh": "Xhosa",
            "yi": "Yiddish",
            "yo": "Yoruba",
            "zu": "Zulu"
        }
        
        # Translation cache
        self.translation_cache = {}  # Store {source_text + target_lang: translated_text}
        
        # Create fonts directory if it doesn't exist
        os.makedirs('data/fonts', exist_ok=True)
        
        # Font paths - we'll use default fonts if custom ones aren't available
        self.font_path = self.get_font_path()
        print(f"Font path: {self.font_path}")
        
        # Weather condition emoji mappings
        self.weather_codes = {
            # Clear
            0: "☀️",  # Clear sky
            
            # Partly cloudy
            1: "🌤️",  # Mainly clear
            2: "⛅",   # Partly cloudy
            3: "☁️",   # Overcast
            
            # Fog
            45: "🌫️",  # Fog
            48: "🌫️",  # Depositing rime fog
            
            # Drizzle
            51: "🌦️",  # Light drizzle
            53: "🌦️",  # Moderate drizzle
            55: "🌧️",  # Dense drizzle
            
            # Freezing Drizzle
            56: "🌨️",  # Light freezing drizzle
            57: "🌨️",  # Dense freezing drizzle
            
            # Rain
            61: "🌦️",  # Slight rain
            63: "🌧️",  # Moderate rain
            65: "🌧️",  # Heavy rain
            
            # Freezing Rain
            66: "🌨️",  # Light freezing rain
            67: "🌨️",  # Heavy freezing rain
            
            # Snow
            71: "🌨️",  # Slight snow fall
            73: "❄️",   # Moderate snow fall
            75: "❄️",   # Heavy snow fall
            
            # Snow grains
            77: "❄️",   # Snow grains
            
            # Rain showers
            80: "🌦️",  # Slight rain showers
            81: "🌧️",  # Moderate rain showers
            82: "🌧️",  # Violent rain showers
            
            # Snow showers
            85: "🌨️",  # Slight snow showers
            86: "❄️",   # Heavy snow showers
            
            # Thunderstorm
            95: "⛈️",   # Thunderstorm
            96: "⛈️",   # Thunderstorm th slight hail
            99: "⛈️",   # Thunderstorm with heavy hail
            
            # Default
            -1: "🌡️"   # Default/unknown
        }
    
    def parse_time(self, time_str: str, reason: str) -> Tuple[Optional[datetime], str]:
        """Parse various time formats and return a datetime object and the cleaned reason"""
        now = datetime.now()
        
        # Handle relative time formats (15m, 2h, 3d)
        relative_match = re.match(r'^(\d+)([smhd])$', time_str.lower())
        if relative_match:
            amount, unit = relative_match.groups()
            amount = int(amount)
            delta = {
                's': timedelta(seconds=amount),
                'm': timedelta(minutes=amount),
                'h': timedelta(hours=amount),
                'd': timedelta(days=amount)
            }[unit]
            return now + delta, reason
            
        # Handle "tomorrow" or "tm"
        if time_str.lower() in ['tomorrow', 'tm']:
            return now + timedelta(days=1), reason
            
        # Handle HH:MM format (both 24h and 12h with am/pm)
        time_match = re.match(r'^(\d{1,2})(?::(\d{2}))?\s*(am|pm)?$', time_str.lower())
        if time_match:
            hour, minute, meridiem = time_match.groups()
            hour = int(hour)
            minute = int(minute) if minute else 0
            
            if meridiem:
                if meridiem == 'pm' and hour < 12:
                    hour += 12
                elif meridiem == 'am' and hour == 12:
                    hour = 0
                    
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target <= now:
                target += timedelta(days=1)
            return target, reason
            
        # Handle date formats (15.05 or 15.05.26 or 15.05.2026)
        date_match = re.match(r'^(\d{1,2})\.(\d{1,2})(?:\.(\d{2}|\d{4}))?$', time_str)
        if date_match:
            day, month, year = date_match.groups()
            day = int(day)
            month = int(month)
            
            if year:
                year = int(year)
                if year < 100:
                    year += 2000
            else:
                year = now.year
                
            try:
                target = datetime(year, month, day, 0, 0, 0)
                if target <= now:
                    if not year:
                        target = target.replace(year=target.year + 1)
                return target, reason
            except ValueError:
                return None, reason
                
        # Handle full datetime format (15.07:15:25:00 or 15.07:15:25)
        datetime_match = re.match(r'^(\d{1,2})\.(\d{1,2}):(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?$', time_str)
        if datetime_match:
            day, month, hour, minute, second = datetime_match.groups()
            try:
                target = now.replace(
                    day=int(day),
                    month=int(month),
                    hour=int(hour),
                    minute=int(minute),
                    second=int(second) if second else 0,
                    microsecond=0
                )
                if target <= now:
                    target = target.replace(year=target.year + 1)
                return target, reason
            except ValueError:
                return None, reason
                
        return None, reason
        
    async def send_reminder(self, ctx, user_id: int, channel_id: int, remind_time: datetime, reason: str):
        """Send a reminder to the user at the specified time"""
        try:
            await asyncio.sleep((remind_time - datetime.now()).total_seconds())
            channel = self.client.get_channel(channel_id)
            if channel:
                user = await self.client.fetch_user(user_id)
                embed = discord.Embed(
                    title="Reminder",
                    description=f"{user.mention}, here's your reminder: {reason}",
                    color=0x00FF00
                )
                await channel.send(embed=embed)
        except asyncio.CancelledError:
            pass
        finally:
            if user_id in self.reminder_tasks:
                self.reminder_tasks[user_id] = [task for task in self.reminder_tasks[user_id] if not task.done()]
                
    @commands.command(aliases=['rm'])
    async def remindme(self, ctx, time_str: str, *, reason: str = "No reason provided"):
        """Set a reminder with various time formats"""
        remind_time, cleaned_reason = self.parse_time(time_str, reason)
        
        if not remind_time:
            embed = discord.Embed(
                title="Invalid Time Format",
                description="Please use one of these formats:\n"
                           "• `-rm 20:00 reason` (24h format)\n"
                           "• `-rm 8pm reason` (12h format)\n"
                           "• `-rm 15m reason` (15 minutes, also s/h/d)\n"
                           "• `-rm tomorrow reason` or `-rm tm reason`\n"
                           "• `-rm 15.05 reason` (date)\n"
                           "• `-rm 15.05.26 reason` (date with year)\n"
                           "• `-rm 15.07:15:25 reason` (full datetime)",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
            return
            
        # Don't allow reminders more than a year in the future
        if remind_time > datetime.now() + timedelta(days=365):
            await ctx.send("Reminders cannot be set more than a year in the future.")
            return
            
        # Create and store the reminder task
        if ctx.author.id not in self.reminder_tasks:
            self.reminder_tasks[ctx.author.id] = []
            
        reminder_task = asyncio.create_task(
            self.send_reminder(ctx, ctx.author.id, ctx.channel.id, remind_time, cleaned_reason)
        )
        self.reminder_tasks[ctx.author.id].append(reminder_task)
        
        # Calculate time difference for display
        time_diff = remind_time - datetime.now()
        days = time_diff.days
        hours, remainder = divmod(time_diff.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        time_parts = []
        if days > 0:
            time_parts.append(f"{days} days")
        if hours > 0:
            time_parts.append(f"{hours} hours")
        if minutes > 0:
            time_parts.append(f"{minutes} minutes")
        if seconds > 0 and not (days or hours or minutes):
            time_parts.append(f"{seconds} seconds")
            
        time_str = ", ".join(time_parts)
        
        embed = discord.Embed(
            title="Reminder Set",
            description=f"I'll remind you in {time_str}\n"
                       f"**Reason:** {cleaned_reason}\n"
                       f"**Time:** <t:{int(remind_time.timestamp())}:F>",
            color=0x00FF00
        )
        await ctx.send(embed=embed)
    
    @commands.command()
    async def afk(self, ctx, *, reason="AFK"):
        """Set your AFK status with an optional reason"""
        current_time = time.time()
        self.afk_users[ctx.author.id] = (reason, current_time, current_time)
        
        embed = discord.Embed(
            description=f"{ctx.author.mention} is now AFK - {reason}",
            color=0x808080
        )
        await ctx.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # Check if the message author was AFK and is now back
        if message.author.id in self.afk_users:
            reason, afk_timestamp, command_timestamp = self.afk_users[message.author.id]
            
            # Ignore if this is the command message or messages sent within 1 second of the command
            if time.time() - command_timestamp <= 1:
                return
                
            del self.afk_users[message.author.id]
            elapsed = time.time() - afk_timestamp
            minutes = int(elapsed / 60)
            hours = int(minutes / 60)
            
            if hours > 0:
                time_text = f"{hours} hours and {minutes % 60} minutes"
            else:
                time_text = f"{minutes} minutes"
            
            embed = discord.Embed(
                description=f"👋 {message.author.mention} has returned after being AFK for {time_text}",
                color=0x00FF00
            )
            await message.channel.send(embed=embed)
            
        # Check if any mentioned users are AFK
        for mention in message.mentions:
            if mention.id in self.afk_users:
                reason, timestamp, _ = self.afk_users[mention.id]
                elapsed = time.time() - timestamp
                minutes = int(elapsed / 60)
                hours = int(minutes / 60)
                
                if hours > 0:
                    time_text = f"{hours} hours and {minutes % 60} minutes"
                else:
                    time_text = f"{minutes} minutes"
                
                embed = discord.Embed(
                    description=f"{mention.mention} is AFK: {reason} - Been Away for {time_text}",
                    color=0xFF0000
                )
                await message.channel.send(embed=embed)
        
        # Check if this is a response to a typing test
        if message.author.id in self.active_typing_tests:
            test_info = self.active_typing_tests[message.author.id]
            
            # Only process if the message is in the same channel as the test
            if message.channel.id == test_info["channel_id"]:
                # Calculate time elapsed
                end_time = datetime.now()
                elapsed_seconds = (end_time - test_info["start_time"]).total_seconds()
                
                # Get the original words and the typed words
                original_words = test_info["words"]
                typed_text = message.content.strip()
                typed_words = typed_text.split()
                
                # Calculate accuracy
                correct_chars = 0
                total_chars = sum(len(word) for word in original_words)
                original_text = " ".join(original_words)
                
                # Compare character by character
                for i in range(min(len(original_text), len(typed_text))):
                    if original_text[i] == typed_text[i]:
                        correct_chars += 1
                
                # Calculate accuracy percentage - ensure it doesn't exceed 100%
                accuracy = min(100, (correct_chars / total_chars) * 100) if total_chars > 0 else 0
                
                # Calculate words per minute (WPM)
                # Standard: 5 characters = 1 word
                standard_word_length = 5
                characters_per_minute = (correct_chars / elapsed_seconds) * 60
                wpm = characters_per_minute / standard_word_length
                
                # Create result object
                result = {
                    "wpm": wpm,
                    "accuracy": accuracy,
                    "time": elapsed_seconds,
                    "correct_chars": correct_chars,
                    "total_chars": total_chars
                }
                
                # Check if this is part of a challenge
                if "challenge_id" in test_info:
                    challenge_id = test_info["challenge_id"]
                    
                    if challenge_id in self.typing_challenges:
                        # Add the result to the challenge
                        self.typing_challenges[challenge_id]["results"][message.author.id] = result
                        
                        # Check if both users have completed the challenge
                        challenge = self.typing_challenges[challenge_id]
                        
                        if len(challenge["results"]) == 2:
                            # Both users have completed the challenge, compare results
                            await self.compare_challenge_results(message.channel, challenge_id)
                            
                            # Delete the challenge
                            del self.typing_challenges[challenge_id]
                        else:
                            # Only one user has completed the challenge
                            # Create result embed for the individual
                            embed = self.create_typing_result_embed(result, message.author)
                            
                            # Add challenge info
                            embed.add_field(
                                name="Challenge Status",
                                value="Waiting for opponent to complete the test...",
                                inline=False
                            )
                            
                            await message.channel.send(embed=embed)
                    else:
                        # Challenge doesn't exist anymore, show individual result
                        embed = self.create_typing_result_embed(result, message.author)
                        await message.channel.send(embed=embed)
                else:
                    # Regular typing test, show result
                    embed = self.create_typing_result_embed(result, message.author)
                    await message.channel.send(embed=embed)
                
                # Remove the test from active tests
                del self.active_typing_tests[message.author.id]
    
    def create_typing_result_embed(self, result, user):
        """Create an embed for typing test results"""
        embed = discord.Embed(
            title="⌨️ Typing Test Results",
            color=0x00FF00 if result["accuracy"] > 90 else (0xFFFF00 if result["accuracy"] > 75 else 0xFF0000)
        )
        
        # Add fields with results
        embed.add_field(
            name="Speed",
            value=f"**{result['wpm']:.1f}** WPM",
            inline=True
        )
        
        embed.add_field(
            name="Accuracy",
            value=f"**{result['accuracy']:.1f}%**",
            inline=True
        )
        
        embed.add_field(
            name="Time",
            value=f"**{result['time']:.1f}** seconds",
            inline=True
        )
        
        # Add correct/incorrect character counts
        embed.add_field(
            name="Characters",
            value=f"Correct: **{result['correct_chars']}** / Total: **{result['total_chars']}**",
            inline=False
        )
        
        # Add a rating based on WPM
        rating = ""
        if result["wpm"] < 20:
            rating = "Beginner - Keep practicing!"
        elif result["wpm"] < 40:
            rating = "Average - You're getting there!"
        elif result["wpm"] < 60:
            rating = "Good - Above average typing speed!"
        elif result["wpm"] < 80:
            rating = "Fast - Very good typing speed!"
        elif result["wpm"] < 100:
            rating = "Expert - Impressive typing skills!"
        else:
            rating = "Master - Professional level typing!"
        
        embed.add_field(
            name="Rating",
            value=rating,
            inline=False
        )
        
        embed.set_footer(text=f"Typing test completed by {user.display_name}")
        
        return embed
    
    async def compare_challenge_results(self, channel, challenge_id):
        """Compare and display the results of a typing challenge"""
        challenge = self.typing_challenges[challenge_id]
        
        # Get the users
        try:
            challenger = await self.client.fetch_user(challenge["challenger"])
            challenged = await self.client.fetch_user(challenge["challenged"])
        except:
            await channel.send("Could not find the users for this challenge.")
            return
            
        # Get the results
        challenger_result = challenge["results"][challenger.id]
        challenged_result = challenge["results"][challenged.id]
        
        # Determine the winner based on WPM
        if challenger_result["wpm"] > challenged_result["wpm"]:
            winner = challenger
            winner_result = challenger_result
            loser = challenged
            loser_result = challenged_result
        else:
            winner = challenged
            winner_result = challenged_result
            loser = challenger
            loser_result = challenger_result
        
        # Calculate the difference
        wpm_diff = abs(challenger_result["wpm"] - challenged_result["wpm"])
        accuracy_diff = abs(challenger_result["accuracy"] - challenged_result["accuracy"])
        
        # Create embed for the results
        embed = discord.Embed(
            title="⚔️ Typing Challenge Results",
            description=f"**{winner.display_name}** wins the typing challenge!",
            color=0xFFD700  # Gold
        )
        
        # Add winner's results
        embed.add_field(
            name=f"{winner.display_name}'s Results",
            value=f"• Speed: **{winner_result['wpm']:.1f}** WPM\n"
                 f"• Accuracy: **{winner_result['accuracy']:.1f}%**\n"
                 f"• Time: **{winner_result['time']:.1f}s**",
            inline=True
        )
        
        # Add loser's results
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
            value=f"• Speed: **{wpm_diff:.1f}** WPM\n"
                 f"• Accuracy: **{accuracy_diff:.1f}%**",
            inline=False
        )
        
        # Add a fun message based on the difference
        if wpm_diff < 5:
            message = "A very close match! Both typists are evenly matched."
        elif wpm_diff < 15:
            message = f"{winner.display_name} has a slight edge in typing speed."
        elif wpm_diff < 30:
            message = f"{winner.display_name} is notably faster than {loser.display_name}."
        else:
            message = f"{winner.display_name} completely outclassed {loser.display_name} in this challenge!"
            
        embed.add_field(
            name="Analysis",
            value=message,
            inline=False
        )
        
        embed.set_footer(text=f"Challenge completed | {challenge['word_count']} words")
        
        await channel.send(embed=embed)
    
    @commands.command()
    async def code(self, ctx):
        await ctx.send("zgte5dr6ftgzhujikokztrdeswa536edfr65fm ,WU83 34 FTZFTBFTBF7677U6")
    
    @commands.command()
    async def geschichte(self, ctx):
        await ctx.send("ich habe mal david in migros getroffen und ein foto mit david gemacht. das hat mich glücklich gemacht. dann hatten wir französisch...")
    
    @commands.command()
    async def info(self, ctx):
        embed = discord.Embed(
            title="Leurs: Discord Balance Bot",
            description="A Discord bot for managing balances and other utilities.",
            color=0xFFFFFF
        )
        
        embed.add_field(name="GitHub Repository", value="https://github.com/IM23d/leurs", inline=False)
        embed.add_field(name="Developers", value="@bettercallmilan, @reazndev", inline=True)
        embed.add_field(name="Contributors", value="@lhilfiker", inline=True)
        embed.add_field(name="Was also there", value="@seakyy", inline=True)
        embed.add_field(name="Version", value="1.0.0", inline=True)
        embed.add_field(name="Commands", value="Use `-help` to see all available commands", inline=False)
        
        embed.set_footer(text="Leurs: Discord Balance Bot")
        
        await ctx.send(embed=embed)
        

    @commands.command()
    async def david(self, ctx):
        random_num_david = random.randint(1, 20)
        jpeg_path = f"images/david/{random_num_david}.jpeg"
        gif_path = f"images/david/{random_num_david}.gif"
        
        if os.path.exists(jpeg_path):
            file = discord.File(jpeg_path)
        elif os.path.exists(gif_path):
            file = discord.File(gif_path)
        else:
            await ctx.send("Couldn't find image for David")
            return
            
        await ctx.send(file=file)

    @commands.command()
    async def hwmo(self, ctx):
        await ctx.send("https://habenwirmorgenopl.info (might be down)")

    @commands.command()
    async def hi(self, ctx):
        await ctx.send("Hi I'm coffee!")
    
    @commands.command() # please work git
    async def lyric(self, ctx):
        random_num_lyric = random.randint(1, 7)
        file_path = f"data/{random_num_lyric}.txt" # comment 

        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                content = file.read()
            await ctx.send(content)
        else:
            await ctx.send("Couldn't find the lyric file")

    @commands.command()
    async def github(self, ctx):
        await ctx.send("https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request")
    
    @commands.command(aliases=['list', 'reminders'])
    async def remindme_list(self, ctx):
        """List all your active reminders"""
        if ctx.author.id not in self.reminder_tasks or not self.reminder_tasks[ctx.author.id]:
            embed = discord.Embed(
                title="Your Reminders",
                description="You don't have any active reminders.",
                color=0x808080
            )
            await ctx.send(embed=embed)
            return

        # Clean up completed tasks first
        self.reminder_tasks[ctx.author.id] = [task for task in self.reminder_tasks[ctx.author.id] if not task.done()]
        
        if not self.reminder_tasks[ctx.author.id]:
            embed = discord.Embed(
                title="Your Reminders",
                description="You don't have any active reminders.",
                color=0x808080
            )
            await ctx.send(embed=embed)
            return

        # Get reminder details from task names
        reminders = []
        now = datetime.now()
        
        for task in self.reminder_tasks[ctx.author.id]:
            # Extract reminder time and reason from the task's internal data
            # The send_reminder coroutine contains these as arguments
            coro = task.get_coro()
            frame = coro.cr_frame
            remind_time = frame.f_locals.get('remind_time')
            reason = frame.f_locals.get('reason')
            
            if remind_time and reason:
                time_diff = remind_time - now
                days = time_diff.days
                hours, remainder = divmod(time_diff.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                
                time_parts = []
                if days > 0:
                    time_parts.append(f"{days} days")
                if hours > 0:
                    time_parts.append(f"{hours} hours")
                if minutes > 0:
                    time_parts.append(f"{minutes} minutes")
                if seconds > 0 and not (days or hours or minutes):
                    time_parts.append(f"{seconds} seconds")
                
                time_until = ", ".join(time_parts)
                reminders.append({
                    'time': remind_time,
                    'reason': reason,
                    'time_until': time_until
                })
        
        # Sort reminders by time
        reminders.sort(key=lambda x: x['time'])
        
        # Create embed with reminder list
        embed = discord.Embed(
            title="📝 Your Reminders",
            color=0x00FF00
        )
        
        for i, reminder in enumerate(reminders, 1):
            embed.add_field(
                name=f"Reminder #{i}",
                value=f"**Time:** <t:{int(reminder['time'].timestamp())}:F>\n"
                      f"**Relative:** <t:{int(reminder['time'].timestamp())}:R>\n"
                      f"**Reason:** {reminder['reason']}",
                inline=False
            )
            
        await ctx.send(embed=embed)
    
    def get_font_path(self):
        """Get the font path, downloading it if necessary"""
        # Check if we have a font in data/fonts
        font_path = 'data/fonts/arial.ttf'
        
        # If the font doesn't exist, use a system font
        if not os.path.exists(font_path):
            # Try to use a system font that's likely to exist
            system_fonts = [
                '/usr/share/fonts/TTF/Arial.ttf',  # Linux
                '/usr/share/fonts/truetype/msttcorefonts/Arial.ttf',  # Some Linux
                '/Library/Fonts/Arial.ttf',  # macOS
                'C:\\Windows\\Fonts\\arial.ttf'  # Windows
            ]
            
            for font in system_fonts:
                if os.path.exists(font):
                    return font
            
            # If no system font found, download a free font
            try:
                font_url = "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Regular.ttf"
                response = requests.get(font_url)
                if response.status_code == 200:
                    os.makedirs(os.path.dirname(font_path), exist_ok=True)
                    with open(font_path, 'wb') as f:
                        f.write(response.content)
                    return font_path
            except Exception as e:
                print(f"Error downloading font: {e}")
            
            # If all else fails, we'll use default font in PIL
            return None
    
    async def create_quote_image(self, avatar_url, message_content, username):
        """Create a quote image with user's avatar and message content"""
        try:
            # Download the user's avatar
            response = requests.get(avatar_url)
            avatar_image = Image.open(io.BytesIO(response.content))
            
            # Create a square image (1:1 aspect ratio)
            size = 1000  # Standard size - we'll scale the image later
            
            # Resize avatar to fill the entire background
            # Calculate dimensions to maintain aspect ratio while filling the square
            width, height = avatar_image.size
            
            # Determine which dimension to use for cropping
            if width > height:
                # Image is wider than tall
                new_width = int(width * size / height)
                new_height = size
                left_crop = (new_width - size) // 2
                top_crop = 0
            else:
                # Image is taller than wide
                new_width = size
                new_height = int(height * size / width)
                left_crop = 0
                top_crop = (new_height - size) // 2
                
            # Resize and crop to fill the square
            avatar_image = avatar_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            avatar_image = avatar_image.crop((left_crop, top_crop, left_crop + size, top_crop + size))
            
            # Create the base image using the avatar
            quote_img = avatar_image.copy()
            
            # Add a dark overlay to make text more readable
            overlay = Image.new('RGBA', (size, size), (0, 0, 0, 230))  # Very dark overlay
            quote_img = Image.alpha_composite(quote_img.convert('RGBA'), overlay)
            
            # Convert to RGB for final output
            quote_img = quote_img.convert('RGB')
            
            # Create a blank image for the text with transparent background
            text_img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(text_img)
            
            # Try to find a system font that works well
            system_fonts = [
                '/usr/share/fonts/TTF/DejaVuSans-Bold.ttf',  # Linux
                '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',  # Ubuntu
                '/Library/Fonts/Arial Bold.ttf',  # macOS
                'C:\\Windows\\Fonts\\arialbd.ttf',  # Windows
                # Add fallbacks
                '/usr/share/fonts/TTF/Arial.ttf',
                '/usr/share/fonts/truetype/msttcorefonts/Arial.ttf',
                self.font_path
            ]
            
            font_path = None
            for font in system_fonts:
                if font and os.path.exists(font):
                    font_path = font
                    break
            
            # If no font found, we'll have to use default
            if not font_path:
                # Create a simple text overlay with basic text
                draw.text((50, 50), f'"{message_content}"', fill=(255, 255, 255), font=ImageFont.load_default())
                draw.text((50, 100), f"- {username}", fill=(255, 255, 255), font=ImageFont.load_default())
            else:
                # Custom line wrapping function that wraps after 3-5 words
                def wrap_text(text, words_per_line=4):
                    words = text.split()
                    lines = []
                    current_line = []
                    
                    for word in words:
                        current_line.append(word)
                        if len(current_line) >= words_per_line:
                            lines.append(' '.join(current_line))
                            current_line = []
                    
                    # Add any remaining words
                    if current_line:
                        lines.append(' '.join(current_line))
                    
                    return '\n'.join(lines)
                
                # Wrap the text with 3-5 words per line
                wrapped_text = wrap_text(message_content, 4)  # 4 words per line on average
                
                # Add quotation marks
                quote_text = f'"{wrapped_text}"'
                
                # Calculate text size based on image dimensions
                # We'll make the text take up about 80% of the image width
                target_text_width = int(size * 0.8)
                
                # Start with a reasonable size and adjust
                test_size = 20
                max_size = 500
                
                # Find the largest font size that fits within our target width
                font_size = test_size
                for test_size in range(20, max_size, 10):
                    try:
                        test_font = ImageFont.truetype(font_path, test_size)
                        # Check the width of the longest line
                        longest_line = max(wrapped_text.split('\n'), key=len)
                        bbox = draw.textbbox((0, 0), f'"{longest_line}"', font=test_font)
                        if bbox[2] - bbox[0] > target_text_width:
                            break
                        font_size = test_size
                    except Exception:
                        break
                
                try:
                    quote_font = ImageFont.truetype(font_path, font_size)
                    username_font = ImageFont.truetype(font_path, font_size // 2)  # Username half the size
                    
                    # Get text dimensions
                    quote_bbox = draw.textbbox((0, 0), quote_text, font=quote_font)
                    quote_width = quote_bbox[2] - quote_bbox[0]
                    quote_height = quote_bbox[3] - quote_bbox[1]
                    
                    # Center the text
                    quote_x = (size - quote_width) // 2
                    quote_y = (size - quote_height) // 2 - size // 8  # Slightly above center
                    
                    # Draw text with shadow for better visibility
                    shadow_offset = max(3, font_size // 20)  # Scale shadow with font size
                    
                    # Draw shadow
                    for dx, dy in [(shadow_offset, shadow_offset), (-shadow_offset, shadow_offset),
                                  (shadow_offset, -shadow_offset), (-shadow_offset, -shadow_offset)]:
                        draw.text((quote_x + dx, quote_y + dy), quote_text, fill=(0, 0, 0), font=quote_font)
                    
                    # Draw main text
                    draw.text((quote_x, quote_y), quote_text, fill=(255, 255, 255), font=quote_font)
                    
                    # Add username
                    username_text = f"- {username}"
                    username_bbox = draw.textbbox((0, 0), username_text, font=username_font)
                    username_width = username_bbox[2] - username_bbox[0]
                    
                    # Position username at bottom right
                    username_x = size - username_width - (size // 20)
                    username_y = size - (size // 5)
                    
                    # Draw username shadow
                    for dx, dy in [(shadow_offset//2, shadow_offset//2), (-shadow_offset//2, shadow_offset//2),
                                  (shadow_offset//2, -shadow_offset//2), (-shadow_offset//2, -shadow_offset//2)]:
                        draw.text((username_x + dx, username_y + dy), username_text, fill=(0, 0, 0), font=username_font)
                    
                    # Draw username
                    draw.text((username_x, username_y), username_text, fill=(255, 255, 255), font=username_font)
                    
                except Exception:
                    # Fallback to basic text
                    draw.text((50, 50), f'"{message_content}"', fill=(255, 255, 255), font=ImageFont.load_default())
                    draw.text((50, 100), f"- {username}", fill=(255, 255, 255), font=ImageFont.load_default())
            
            # Composite the text onto the background
            quote_img = Image.alpha_composite(quote_img.convert('RGBA'), text_img)
            
            # IMPORTANT: Scale up the final image to ensure it's large enough
            final_size = 2000  # Final output size
            quote_img = quote_img.resize((final_size, final_size), Image.Resampling.LANCZOS)
            
            # Save the image to a bytes buffer
            buffer = io.BytesIO()
            quote_img.convert('RGB').save(buffer, format='PNG')
            buffer.seek(0)
            
            return buffer
        except Exception as e:
            return None
    
    @commands.command()
    async def quote(self, ctx):
        """Create a quote image from a replied message"""
        try:
            # Send a temporary confirmation message
            temp_msg = await ctx.send("Generating quote image...")
            
            # Check if the command is replying to a message
            if not ctx.message.reference:
                await temp_msg.edit(content="You need to reply to a message to quote it!")
                return
            
            # Get the message being replied to
            try:
                replied_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            except discord.NotFound:
                await temp_msg.edit(content="I couldn't find the message you're replying to.")
                return
            except Exception:
                await temp_msg.edit(content="Error fetching the message.")
                return
            
            # Get the message author's avatar URL
            avatar_url = replied_msg.author.display_avatar.url
            
            # Create the quote image
            image_buffer = await self.create_quote_image(
                avatar_url, 
                replied_msg.content, 
                replied_msg.author.display_name
            )
            
            if image_buffer:
                # Send the image
                await ctx.send(file=discord.File(fp=image_buffer, filename='quote.png'))
                # Delete the temporary message
                await temp_msg.delete()
            else:
                await temp_msg.edit(content="Failed to create quote image.")
        except Exception:
            await ctx.send("An error occurred while creating the quote image.")
    
    @commands.command(aliases=['av'])
    async def avatar(self, ctx, member: discord.Member = None):
        """Display a user's global avatar in high quality"""
        # If no member is specified, use the command author
        member = member or ctx.author
        
        # Create an embed with the avatar
        embed = discord.Embed(
            title=f"{member.display_name}'s Avatar",
            color=0x00FFFF
        )
        
        # Get the global avatar URL with maximum size (4096)
        avatar_url = member.avatar.with_size(4096).url if member.avatar else member.default_avatar.url
        
        # Set the image in the embed
        embed.set_image(url=avatar_url)
        
        await ctx.send(embed=embed)
    
    @commands.command(aliases=['sav'])
    async def serveravatar(self, ctx, member: discord.Member = None):
        """Display a user's server-specific avatar in high quality"""
        # If no member is specified, use the command author
        member = member or ctx.author
        
        # Check if the user has a server-specific avatar
        if not member.guild_avatar:
            await ctx.send(f"{member.display_name} doesn't have a server-specific avatar.")
            return
        
        # Create an embed with the server avatar
        embed = discord.Embed(
            title=f"{member.display_name}'s Server Avatar",
            color=0x00FFFF
        )
        
        # Get the server avatar URL with maximum size (4096)
        avatar_url = member.guild_avatar.with_size(4096).url
        
        # Set the image in the embed
        embed.set_image(url=avatar_url)
        
        await ctx.send(embed=embed)
    
    @commands.command()
    async def banner(self, ctx, user: discord.User = None):
        """Display a user's banner in high quality"""
        # If no user is specified, use the command author
        user = user or ctx.author
        
        # Fetch the user to get the banner info
        try:
            user = await self.client.fetch_user(user.id)
            
            # Check if the user has a banner
            if not user.banner:
                await ctx.send(f"{user.display_name} doesn't have a banner.")
                return
            
            # Create an embed with the banner
            embed = discord.Embed(
                title=f"{user.display_name}'s Banner",
                color=0x00FFFF
            )
            
            # Get the banner URL with maximum size (4096)
            banner_url = user.banner.with_size(4096).url
            
            # Set the image in the embed
            embed.set_image(url=banner_url)
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"Error fetching banner: {str(e)}")
    
    @commands.command()
    async def sbanner(self, ctx, member: discord.Member = None):
        """Display a user's server banner in high quality"""
        # If no member is specified, use the command author
        member = member or ctx.author
        
        try:
            # Check if the user has a server banner
            if not hasattr(member, 'guild_banner') or not member.guild_banner:
                await ctx.send(f"{member.display_name} doesn't have a server banner.")
                return
            
            # Create an embed with the server banner
            embed = discord.Embed(
                title=f"{member.display_name}'s Server Banner",
                color=0x00FFFF
            )
            
            # Get the server banner URL with maximum size (4096)
            banner_url = member.guild_banner.with_size(4096).url
            
            # Set the image in the embed
            embed.set_image(url=banner_url)
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"Error fetching server banner: {str(e)}")
    
    @commands.command(aliases=['fortune', 'cookie', 'fc'])
    async def fortunecookie(self, ctx):
        """Get a random fortune cookie message"""
        try:
            # Send a temporary message while fetching the fortune
            temp_msg = await ctx.send("Breaking open a fortune cookie...")
            
            # Fetch a random fortune from the API
            response = requests.get("https://api.viewbits.com/v1/fortunecookie?mode=random")
            
            if response.status_code != 200:
                await temp_msg.edit(content="Failed to get a fortune cookie. Try again later.")
                return
                
            # Parse the JSON response
            fortune_data = response.json()
            
            # Extract only the fortune text
            # Handle escaped unicode characters
            fortune_text = fortune_data.get("text", "No fortune found")
            # Replace common escaped characters
            fortune_text = fortune_text.replace("\\u2019", "'").replace("\\u2018", "'")
            fortune_text = fortune_text.replace("\\u201c", """).replace("\\u201d", """)
            
            # Create an embed for the fortune with only the quote
            embed = discord.Embed(
                title="🥠 Fortune Cookie",
                description=f"**{fortune_text}**",
                color=0xFFD700  # Gold color
            )
            
            # Send the embed and delete the temporary message
            await ctx.send(embed=embed)
            await temp_msg.delete()
            
        except Exception as e:
            await ctx.send(f"Error getting fortune cookie: {str(e)}")
    
    @commands.command()
    async def set_weather_api_key(self, ctx, api_key: str):
        """Set the OpenWeatherMap API key (admin only)"""
        # Check if the user has admin permissions
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("Only administrators can set the API key.")
            return
            
        # Store the API key
        self.weather_api_key = api_key
        
        # Delete the message to keep the API key private
        try:
            await ctx.message.delete()
        except:
            pass
            
        await ctx.send("Weather API key has been set successfully!", delete_after=5)
    
    def get_weather_emoji(self, weather_code: int) -> str:
        """Get emoji for weather code"""
        return self.weather_codes.get(weather_code, self.weather_codes[-1])
    
    async def geocode_location(self, location: str) -> Optional[Tuple[float, float, str, str]]:
        """Convert location name to coordinates using Open-Meteo Geocoding API"""
        try:
            # URL encode the location
            encoded_location = location.replace(" ", "+")
            
            # Make request to geocoding API
            geocode_url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded_location}&count=1&language=en&format=json"
            response = requests.get(geocode_url)
            
            if response.status_code != 200:
                return None
                
            data = response.json()
            
            # Check if results were found
            if not data.get("results"):
                return None
                
            # Get the first result
            result = data["results"][0]
            
            # Extract coordinates and location info
            latitude = result["latitude"]
            longitude = result["longitude"]
            name = result["name"]
            country = result.get("country", "")
            
            return (latitude, longitude, name, country)
        except Exception:
            return None
    
    def get_daily_weather_summary(self, hourly_data: Dict) -> List[Dict]:
        """Process hourly data to get daily summaries"""
        daily_summary = []
        
        # Get the hourly timestamps and convert to datetime objects
        times = [datetime.fromisoformat(t.replace('Z', '+00:00')) for t in hourly_data["time"]]
        
        # Group by day
        daily_data = {}
        
        for i, time in enumerate(times):
            # Skip past hours of today
            if time.date() < datetime.now().date():
                continue
                
            # Convert to local date
            date_str = time.date().isoformat()
            
            # Initialize if this is the first entry for this date
            if date_str not in daily_data:
                daily_data[date_str] = {
                    "temp_min": float('inf'),
                    "temp_max": float('-inf'),
                    "weather_codes": [],
                    "date": time.date()
                }
                
            # Update min/max temps
            temp = hourly_data["temperature_2m"][i]
            if temp < daily_data[date_str]["temp_min"]:
                daily_data[date_str]["temp_min"] = temp
            if temp > daily_data[date_str]["temp_max"]:
                daily_data[date_str]["temp_max"] = temp
                
            # If we have weather codes, add them
            if "weather_code" in hourly_data:
                daily_data[date_str]["weather_codes"].append(hourly_data["weather_code"][i])
        
        # Convert to list and sort by date
        for date_str, data in daily_data.items():
            # Find most common weather code for the day
            if data["weather_codes"]:
                # Count occurrences of each code
                code_counts = {}
                for code in data["weather_codes"]:
                    if code not in code_counts:
                        code_counts[code] = 0
                    code_counts[code] += 1
                    
                most_common_code = max(code_counts, key=code_counts.get)
            else:
                most_common_code = -1  # Default/unknown
                
            daily_summary.append({
                "date": data["date"],
                "temp_min": round(data["temp_min"]),
                "temp_max": round(data["temp_max"]),
                "weather_code": most_common_code
            })
            
        # Sort by date
        daily_summary.sort(key=lambda x: x["date"])
        
        # Limit to 5 days
        return daily_summary[:5]
    
    @commands.command()
    async def weather(self, ctx, *, location: str = None):
        """Get current weather and 5-day forecast for a location"""
        if not location:
            await ctx.send("Please provide a location. Example: `-weather London`")
            return
            
        # Send a temporary message while fetching weather data
        temp_msg = await ctx.send(f"Fetching weather data for {location}...")
        
        try:
            # First, geocode the location to get coordinates
            geocode_result = await self.geocode_location(location)
            
            if not geocode_result:
                await temp_msg.edit(content=f"Couldn't find location: {location}")
                return
                
            latitude, longitude, city_name, country = geocode_result
            
            # Fetch weather data from Open-Meteo API
            weather_url = (
                f"https://api.open-meteo.com/v1/forecast"
                f"?latitude={latitude}&longitude={longitude}"
                f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m"
                f"&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code"
                f"&daily=temperature_2m_max,temperature_2m_min,weather_code"
                f"&timezone=auto"
            )
            
            response = requests.get(weather_url)
            
            if response.status_code != 200:
                await temp_msg.edit(content="Error fetching weather data. Please try again later.")
                return
                
            weather_data = response.json()
            
            # Process current weather data
            current = weather_data["current"]
            current_temp = round(current["temperature_2m"])
            feels_like = round(current["apparent_temperature"])
            humidity = current["relative_humidity_2m"]
            wind_speed = current["wind_speed_10m"]
            weather_code = current["weather_code"]
            weather_emoji = self.get_weather_emoji(weather_code)
            
            # Get daily forecast
            daily = weather_data["daily"]
            
            # Create embed for weather data
            location_name = f"{city_name}, {country}" if country else city_name
            embed = discord.Embed(
                title=f"Weather for {location_name}",
                description=f"**Current Conditions:** {weather_emoji} {current_temp}°C",
                color=0x3498db
            )
            
            # Add current weather information
            embed.add_field(
                name="Feels Like",
                value=f"**{feels_like}°C**",
                inline=True
            )
            
            # Today's min/max from daily data
            today_min = round(daily["temperature_2m_min"][0])
            today_max = round(daily["temperature_2m_max"][0])
            
            embed.add_field(
                name="Today's Range",
                value=f"🔽 {today_min}°C / 🔼 {today_max}°C",
                inline=True
            )
            
            embed.add_field(
                name="Humidity & Wind",
                value=f"💧 {humidity}% | 💨 {wind_speed} km/h",
                inline=True
            )
            
            # Add 5-day forecast
            forecast_text = ""
            
            # Start from tomorrow (index 1)
            for i in range(1, min(6, len(daily["time"]))):
                date_str = daily["time"][i]
                dt = datetime.fromisoformat(date_str)
                day_name = dt.strftime("%A")
                
                min_temp = round(daily["temperature_2m_min"][i])
                max_temp = round(daily["temperature_2m_max"][i])
                day_weather_code = daily["weather_code"][i]
                day_emoji = self.get_weather_emoji(day_weather_code)
                
                forecast_text += f"{day_name}: {day_emoji} {min_temp}°C - {max_temp}°C\n"
                
            if forecast_text:
                embed.add_field(
                    name="5-Day Forecast",
                    value=forecast_text,
                    inline=False
                )
                
            # Add timestamp
            embed.set_footer(text=f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Send the embed and delete the temporary message
            await ctx.send(embed=embed)
            await temp_msg.delete()
            
        except Exception as e:
            await temp_msg.edit(content=f"Error getting weather data: {str(e)}")
            print(f"Weather error: {traceback.format_exc()}")
    
    def clean_image_cache(self):
        """Clean up the image search cache if it gets too large"""
        if len(self.image_search_cache) > self.max_cache_size:
            # Get the oldest items (we'll remove 20% of the cache)
            num_to_remove = max(1, int(self.max_cache_size * 0.2))
            keys_to_remove = list(self.image_search_cache.keys())[:num_to_remove]
            
            # Remove the oldest items
            for key in keys_to_remove:
                del self.image_search_cache[key]
    
    def check_reset_daily_count(self):
        """Check if we need to reset the daily search count"""
        now = datetime.now()
        # Reset count if it's a new day
        if now.date() > self.last_count_reset.date():
            self.daily_search_count = 0
            self.last_count_reset = now
            return True
        return False
    
    def increment_search_count(self):
        """Increment the daily search count and return True if limit exceeded"""
        self.check_reset_daily_count()
        self.daily_search_count += 1
        return self.daily_search_count > self.daily_limit
    
    def check_user_cooldown(self, user_id: int) -> Tuple[bool, int]:
        """Check if a user is on cooldown
        
        Returns:
            Tuple[bool, int]: (is_on_cooldown, seconds_remaining)
        """
        now = time.time()
        
        if user_id in self.user_cooldowns:
            last_use = self.user_cooldowns[user_id]
            elapsed = now - last_use
            
            if elapsed < self.cooldown_time:
                return True, int(self.cooldown_time - elapsed)
        
        # Update the last use time
        self.user_cooldowns[user_id] = now
        return False, 0
    
    def check_ai_reset_daily_count(self):
        """Check if we need to reset the daily AI usage count"""
        now = datetime.now()
        # Reset count if it's a new day
        if now.date() > self.ai_last_reset.date():
            self.ai_daily_usage = {}  # Reset all users' counts
            self.ai_last_reset = now
            return True
        return False
    
    def check_ai_user_limit(self, user_id: int) -> bool:
        """Check if a user has reached their daily AI usage limit
        
        Returns:
            bool: True if limit exceeded, False otherwise
        """
        self.check_ai_reset_daily_count()
        
        # Initialize if this is the first request of the day
        if user_id not in self.ai_daily_usage:
            self.ai_daily_usage[user_id] = 0
            
        # Increment and check
        self.ai_daily_usage[user_id] += 1
        return self.ai_daily_usage[user_id] > self.ai_daily_limit
    
    def check_ai_cooldown(self, user_id: int) -> Tuple[bool, int]:
        """Check if a user is on AI cooldown
        
        Returns:
            Tuple[bool, int]: (is_on_cooldown, seconds_remaining)
        """
        now = time.time()
        
        if user_id in self.ai_user_cooldowns:
            last_use = self.ai_user_cooldowns[user_id]
            elapsed = now - last_use
            
            if elapsed < self.ai_cooldown_time:
                return True, int(self.ai_cooldown_time - elapsed)
        
        # Update the last use time
        self.ai_user_cooldowns[user_id] = now
        return False, 0
    
    @commands.command()
    async def set_google_api_key(self, ctx, api_key: str):
        """Set the Google API key (admin only)"""
        # Check if the user has admin permissions
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("Only administrators can set the API key.")
            return
            
        # Store the API key
        self.google_api_key = api_key
        
        # Delete the message to keep the API key private
        try:
            await ctx.message.delete()
        except:
            pass
            
        await ctx.send("Google API key has been set successfully!", delete_after=5)
    
    @commands.command()
    async def set_google_cse_id(self, ctx, cse_id: str):
        """Set the Google Custom Search Engine ID (admin only)"""
        # Check if the user has admin permissions
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("Only administrators can set the CSE ID.")
            return
            
        # Store the CSE ID
        self.google_cse_id = cse_id
        
        # Delete the message to keep the CSE ID private
        try:
            await ctx.message.delete()
        except:
            pass
            
        await ctx.send("Google Custom Search Engine ID has been set successfully!", delete_after=5)
    
    async def search_images(self, query: str, num: int = 10) -> List[Dict]:
        """Search for images using Google Custom Search API or fallback to free API"""
        # Special case for random images
        if query.lower() == "random":
            # Generate random categories for Unsplash
            categories = ["nature", "animals", "technology", "architecture", "food", "travel", 
                         "people", "business", "sports", "health", "fashion", "art"]
            random_categories = random.sample(categories, min(5, len(categories)))
            query = ",".join(random_categories)
        
        # Check if we have this query cached
        if query in self.image_search_cache:
            return self.image_search_cache[query]
            
        # Check if we have Google API credentials
        if self.google_api_key and self.google_cse_id:
            try:
                # Check if we've hit the daily limit
                if self.increment_search_count():
                    print("Daily Google API search limit reached, falling back to free API")
                    # Fall through to free API
                else:
                    # Build the search URL for Google Custom Search
                    search_url = "https://www.googleapis.com/customsearch/v1"
                    params = {
                        "q": query,
                        "cx": self.google_cse_id,
                        "key": self.google_api_key,
                        "searchType": "image",
                        "num": num
                    }
                    
                    # Make the request
                    response = requests.get(search_url, params=params, timeout=10)
                    
                    if response.status_code != 200:
                        print(f"Error searching for images: {response.status_code} {response.text}")
                        # Fall through to free API
                    else:
                        # Parse the response
                        data = response.json()
                        
                        # Extract image information
                        images = []
                        if "items" in data:
                            for item in data["items"]:
                                image_info = {
                                    "title": item.get("title", "No title"),
                                    "url": item.get("link", ""),
                                    "source": item.get("displayLink", ""),
                                    "thumbnail": item.get("image", {}).get("thumbnailLink", ""),
                                    "context": item.get("image", {}).get("contextLink", "")
                                }
                                images.append(image_info)
                                
                            # Cache the results
                            self.image_search_cache[query] = images
                            
                            # Clean up the cache if needed
                            self.clean_image_cache()
                            
                            return images
            except Exception as e:
                print(f"Error searching for images with Google API: {str(e)}")
                # Fall through to free API
        
        # Fallback to Unsplash API (free, no key required)
        try:
            # Use Unsplash Source API
            encoded_query = query.replace(" ", "-").replace(",", ",")
            images = []
            
            # Generate images based on the query
            for i in range(min(10, num)):
                try:
                    # Unsplash Source provides random images for a given search term
                    # Add a random number to prevent caching
                    random_param = random.randint(1, 1000000)
                    image_url = f"https://source.unsplash.com/featured/?{encoded_query}&sig={i}&random={random_param}"
                    
                    # Verify the image URL is valid by making a HEAD request
                    head_response = requests.head(image_url, timeout=5)
                    if head_response.status_code != 200:
                        continue
                    
                    # Create image info object
                    image_info = {
                        "title": f"{query.title()} - Image {i+1}",
                        "url": image_url,
                        "source": "Unsplash",
                        "thumbnail": image_url,
                        "context": f"https://unsplash.com/s/photos/{encoded_query}"
                    }
                    images.append(image_info)
                except Exception as e:
                    print(f"Error with individual Unsplash image {i}: {str(e)}")
                    continue
            
            # If we got at least one image, cache the results
            if images:
                self.image_search_cache[query] = images
                
                # Clean up the cache if needed
                self.clean_image_cache()
                
                return images
            else:
                return []
                
        except Exception as e:
            print(f"Error searching for images with free API: {str(e)}")
            return []
    
    @commands.command(aliases=["image", "search"])
    async def img(self, ctx, *, query: str = None):
        """Search for images and navigate through results with reactions"""
        # Check if query was provided
        if not query:
            embed = discord.Embed(
                title="Image Search Help",
                description="Search for images using Google search.",
                color=0x3498db
            )
            embed.add_field(
                name="Usage",
                value="`-img [search term]`",
                inline=False
            )
            embed.add_field(
                name="Examples",
                value="`-img cute cats`\n`-img sunset beach`\n`-img random` (for random images)",
                inline=False
            )
            embed.add_field(
                name="Navigation",
                value="Use the ⬅️ and ➡️ reactions to navigate through search results.",
                inline=False
            )
            embed.add_field(
                name="Rate Limits",
                value="Regular users can use this command once every 5 minutes.\n"
                      "Administrators are not subject to this cooldown.",
                inline=False
            )
            await ctx.send(embed=embed)
            return
            
        # Check if the user is an admin (bypass cooldown)
        is_admin = ctx.author.guild_permissions.administrator
        
        # Check for cooldown if not an admin
        if not is_admin:
            on_cooldown, time_remaining = self.check_user_cooldown(ctx.author.id)
            if on_cooldown:
                minutes = time_remaining // 60
                seconds = time_remaining % 60
                time_str = f"{minutes} minutes and {seconds} seconds" if minutes > 0 else f"{seconds} seconds"
                
                embed = discord.Embed(
                    title="Cooldown Active",
                    description=f"You need to wait {time_str} before using this command again.",
                    color=0xFF9900
                )
                embed.add_field(
                    name="Why?",
                    value="This cooldown helps prevent hitting Google API limits.\n"
                          "Server administrators are not subject to this cooldown.",
                    inline=False
                )
                await ctx.send(embed=embed)
                return
        
        # Check if we've hit the daily limit
        if self.google_api_key and self.google_cse_id and self.daily_search_count >= self.daily_limit:
            self.check_reset_daily_count()  # Check if we need to reset the count
            
            # If we're still over the limit, show a warning
            if self.daily_search_count >= self.daily_limit:
                embed = discord.Embed(
                    title="Daily Limit Reached",
                    description="The daily Google API search limit has been reached.",
                    color=0xFF0000
                )
                embed.add_field(
                    name="Alternative",
                    value="Using Unsplash as a fallback for image searches.\n"
                          "Results may be less accurate.",
                    inline=False
                )
                embed.set_footer(text="The limit will reset at midnight UTC")
                await ctx.send(embed=embed)
        
        # Send a loading message
        loading_msg = await ctx.send(f"🔍 Searching for images of '{query}'...")
        
        try:
            # Search for images (will use Google API or fallback to free API)
            images = await self.search_images(query)
            
            if not images:
                embed = discord.Embed(
                    title="No Results",
                    description=f"No images found for '{query}'",
                    color=0xFF9900
                )
                embed.add_field(
                    name="Suggestions",
                    value="• Try a different search term\n"
                          "• Check for spelling errors\n"
                          "• Use more general keywords\n"
                          "• Try `-img random` for random images",
                    inline=False
                )
                await loading_msg.edit(content=None, embed=embed)
                return
                
            # Create an embed for the first image
            current_index = 0
            embed = await self.create_image_embed(images[current_index], query, current_index, len(images))
            
            # Add API source note if using fallback
            if not self.google_api_key or not self.google_cse_id or self.daily_search_count >= self.daily_limit:
                embed.add_field(
                    name="Note",
                    value="Using Unsplash for images. For better results, administrators can set up Google API with `-img_setup`",
                    inline=False
                )
            
            # Send the embed and delete the loading message
            image_msg = await ctx.send(embed=embed)
            await loading_msg.delete()
            
            # Store the active search
            self.active_image_searches[image_msg.id] = (query, current_index, images)
            
            # Add navigation reactions
            await image_msg.add_reaction("⬅️")
            await image_msg.add_reaction("➡️")
            
            # Create a reaction check function
            def check(reaction, user):
                return (
                    reaction.message.id == image_msg.id and
                    user != self.client.user and
                    str(reaction.emoji) in ["⬅️", "➡️"]
                )
                
            # Wait for reactions
            while True:
                try:
                    reaction, user = await self.client.wait_for("reaction_add", timeout=60.0, check=check)
                    
                    # Remove the user's reaction
                    try:
                        await reaction.remove(user)
                    except:
                        # If we can't remove the reaction (missing permissions), continue anyway
                        pass
                    
                    # Get the current index
                    query, current_index, images = self.active_image_searches[image_msg.id]
                    
                    # Update the index based on the reaction
                    if str(reaction.emoji) == "⬅️":
                        current_index = (current_index - 1) % len(images)
                    elif str(reaction.emoji) == "➡️":
                        current_index = (current_index + 1) % len(images)
                        
                    # Update the stored index
                    self.active_image_searches[image_msg.id] = (query, current_index, images)
                    
                    # Update the embed
                    new_embed = await self.create_image_embed(images[current_index], query, current_index, len(images))
                    
                    # Add API source note if using fallback
                    if not self.google_api_key or not self.google_cse_id or self.daily_search_count >= self.daily_limit:
                        new_embed.add_field(
                            name="Note",
                            value="Using Unsplash for images. For better results, administrators can set up Google API with `-img_setup`",
                            inline=False
                        )
                    
                    await image_msg.edit(embed=new_embed)
                    
                except asyncio.TimeoutError:
                    # Remove the message from active searches
                    if image_msg.id in self.active_image_searches:
                        del self.active_image_searches[image_msg.id]
                    
                    # Try to clear reactions after timeout
                    try:
                        await image_msg.clear_reactions()
                    except:
                        pass
                    
                    # Update footer to show that navigation has ended
                    embed = image_msg.embeds[0]
                    embed.set_footer(text=f"Image {current_index + 1} of {len(images)} | Navigation timeout")
                    await image_msg.edit(embed=embed)
                    break
                    
                except Exception as e:
                    print(f"Error in image navigation: {str(e)}")
                    break
                    
        except Exception as e:
            error_embed = discord.Embed(
                title="Error",
                description=f"An error occurred while searching for images: {str(e)}",
                color=0xFF0000
            )
            await loading_msg.edit(content=None, embed=error_embed)
            print(f"Image search error: {traceback.format_exc()}")
    
    @commands.command()
    async def imgstats(self, ctx):
        """Show image search usage statistics (admin only)"""
        # Check if the user has admin permissions
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("Only administrators can view search statistics.")
            return
            
        # Create an embed with the stats
        embed = discord.Embed(
            title="Image Search Statistics",
            color=0x00FF00
        )
        
        # Check if we need to reset the daily count
        self.check_reset_daily_count()
        
        # Add daily search count
        embed.add_field(
            name="Daily Search Count",
            value=f"{self.daily_search_count}/{self.daily_limit}",
            inline=True
        )
        
        # Add reset time
        next_reset = datetime.combine(self.last_count_reset.date() + timedelta(days=1), datetime.min.time())
        time_until_reset = next_reset - datetime.now()
        hours, remainder = divmod(time_until_reset.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        embed.add_field(
            name="Resets In",
            value=f"{hours} hours, {minutes} minutes",
            inline=True
        )
        
        # Add cache stats
        embed.add_field(
            name="Cache Size",
            value=f"{len(self.image_search_cache)}/{self.max_cache_size} queries",
            inline=True
        )
        
        # Add active users on cooldown
        now = time.time()
        active_cooldowns = sum(1 for last_use in self.user_cooldowns.values() 
                             if now - last_use < self.cooldown_time)
        
        embed.add_field(
            name="Users on Cooldown",
            value=f"{active_cooldowns} users",
            inline=True
        )
        
        # Add API status
        api_status = "✅ Configured" if self.google_api_key and self.google_cse_id else "❌ Not Configured"
        embed.add_field(
            name="Google API Status",
            value=api_status,
            inline=True
        )
        
        # Add command to clear cooldowns
        embed.add_field(
            name="Admin Commands",
            value="`-img_reset_cooldowns` - Reset all user cooldowns\n"
                  "`-img_reset_count` - Reset the daily search count",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command()
    async def img_reset_cooldowns(self, ctx):
        """Reset all user cooldowns (admin only)"""
        # Check if the user has admin permissions
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("Only administrators can reset cooldowns.")
            return
            
        # Reset all cooldowns
        self.user_cooldowns.clear()
        
        await ctx.send("✅ All user cooldowns have been reset.")
    
    @commands.command()
    async def img_reset_count(self, ctx):
        """Reset the daily search count (admin only)"""
        # Check if the user has admin permissions
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("Only administrators can reset the daily count.")
            return
            
        # Reset the count
        self.daily_search_count = 0
        self.last_count_reset = datetime.now()
        
        await ctx.send("✅ Daily search count has been reset.")
    
    @commands.command()
    async def set_deepseek_api_key(self, ctx, api_key: str):
        """Set the DeepSeek API key (admin only)"""
        # Check if the user has admin permissions
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("Only administrators can set the API key.")
            return
            
        # Store the API key
        self.deepseek_api_key = api_key
        
        # Delete the message to keep the API key private
        try:
            await ctx.message.delete()
        except:
            pass
            
        await ctx.send("DeepSeek API key has been set successfully!", delete_after=5)
    
    @commands.command()
    async def ai_reset_cooldowns(self, ctx):
        """Reset all AI user cooldowns (admin only)"""
        # Check if the user has admin permissions
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("Only administrators can reset cooldowns.")
            return
            
        # Reset all cooldowns
        self.ai_user_cooldowns.clear()
        
        await ctx.send("✅ All AI user cooldowns have been reset.")
    
    @commands.command()
    async def ai_reset_count(self, ctx):
        """Reset the daily AI usage count (admin only)"""
        # Check if the user has admin permissions
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("Only administrators can reset the daily count.")
            return
            
        # Reset the count
        self.ai_daily_usage = {}
        self.ai_last_reset = datetime.now()
        
        await ctx.send("✅ Daily AI usage count has been reset.")
    
    @commands.command()
    async def ai_stats(self, ctx):
        """Show AI usage statistics (admin only)"""
        # Check if the user has admin permissions
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("Only administrators can view AI statistics.")
            return
            
        # Create an embed with the stats
        embed = discord.Embed(
            title="AI Usage Statistics",
            color=0x00FF00
        )
        
        # Check if we need to reset the daily count
        self.check_ai_reset_daily_count()
        
        # Count total usage today
        total_usage = sum(self.ai_daily_usage.values())
        
        # Add daily usage count
        embed.add_field(
            name="Total Usage Today",
            value=f"{total_usage} requests",
            inline=True
        )
        
        # Add user count
        embed.add_field(
            name="Users Today",
            value=f"{len(self.ai_daily_usage)} users",
            inline=True
        )
        
        # Add reset time
        next_reset = datetime.combine(self.ai_last_reset.date() + timedelta(days=1), datetime.min.time())
        time_until_reset = next_reset - datetime.now()
        hours, remainder = divmod(time_until_reset.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        embed.add_field(
            name="Resets In",
            value=f"{hours} hours, {minutes} minutes",
            inline=True
        )
        
        # Add active users on cooldown
        now = time.time()
        active_cooldowns = sum(1 for last_use in self.ai_user_cooldowns.values() 
                             if now - last_use < self.ai_cooldown_time)
        
        embed.add_field(
            name="Users on Cooldown",
            value=f"{active_cooldowns} users",
            inline=True
        )
        
        # Add API status
        api_status = "✅ Configured" if self.deepseek_api_key else "❌ Not Configured"
        embed.add_field(
            name="DeepSeek API Status",
            value=api_status,
            inline=True
        )
        
        # Add top users
        if self.ai_daily_usage:
            top_users = sorted(self.ai_daily_usage.items(), key=lambda x: x[1], reverse=True)[:5]
            top_users_text = ""
            
            for user_id, count in top_users:
                try:
                    user = await self.client.fetch_user(user_id)
                    username = user.display_name
                except:
                    username = f"User {user_id}"
                
                top_users_text += f"{username}: **{count}/{self.ai_daily_limit}** requests\n"
                
            embed.add_field(
                name="Top Users Today",
                value=top_users_text or "No usage today",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command()
    async def ai(self, ctx, *, prompt: str = None):
        """Generate a response using DeepSeek AI"""
        # Check if there's no prompt but there are attachments
        if not prompt and not ctx.message.attachments:
            embed = discord.Embed(
                title="AI Command Help",
                description="Generate text using DeepSeek AI.",
                color=0x3498db
            )
            embed.add_field(
                name="Usage",
                value="`-ai [prompt]` or attach an image with `-ai [prompt]`",
                inline=False
            )
            embed.add_field(
                name="Examples",
                value="`-ai Tell me a joke about programming`\n"
                      "`-ai Write a short poem about nature`\n"
                      "`-ai What is the capital of France?`\n"
                      "`-ai [attach image] What's in this image?`",
                inline=False
            )
            embed.add_field(
                name="Rate Limits",
                value="Regular users can use this command once every 30 seconds with a limit of 30 requests per day.\n"
                      "Administrators are not subject to these limitations.",
                inline=False
            )
            await ctx.send(embed=embed)
            return
        
        # Set default prompt if only an image is attached
        if not prompt and ctx.message.attachments:
            prompt = "Describe what you see in this image in detail."
        
        # Check if the API key is configured
        if not self.deepseek_api_key:
            await ctx.send("❌ DeepSeek API is not configured. Please ask an administrator to set it up.")
            return
            
        # Check if the user is an admin (bypass cooldown and limits)
        is_admin = ctx.author.guild_permissions.administrator
        
        # Check for cooldown if not an admin
        if not is_admin:
            on_cooldown, time_remaining = self.check_ai_cooldown(ctx.author.id)
            if on_cooldown:
                seconds = time_remaining
                time_str = f"{seconds} seconds"
                
                embed = discord.Embed(
                    title="Cooldown Active",
                    description=f"You need to wait {time_str} before using this command again.",
                    color=0xFF9900
                )
                embed.add_field(
                    name="Why?",
                    value="This cooldown helps prevent API rate limits.\n"
                          "Server administrators are not subject to this cooldown.",
                    inline=False
                )
                await ctx.send(embed=embed)
                return
            
            # Check daily limit if not an admin
            if self.check_ai_user_limit(ctx.author.id):
                embed = discord.Embed(
                    title="Daily Limit Reached",
                    description=f"You've reached your limit of {self.ai_daily_limit} AI requests for today.",
                    color=0xFF0000
                )
                embed.add_field(
                    name="When does it reset?",
                    value="The limit resets at midnight UTC.",
                    inline=False
                )
                embed.set_footer(text="Server administrators are not subject to this limit.")
                await ctx.send(embed=embed)
                return
        
        # Send a loading message
        loading_msg = await ctx.send("🧠 Thinking...")
        
        try:
            # Check if there are attachments
            has_image = False
            image_content = None
            
            if ctx.message.attachments:
                for attachment in ctx.message.attachments:
                    # Check if the attachment is an image
                    if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
                        # Check file size - DeepSeek API typically has limits (e.g., 10MB)
                        max_size_mb = 10
                        if attachment.size > max_size_mb * 1024 * 1024:
                            await loading_msg.edit(content=f"❌ Image is too large (max {max_size_mb}MB). Please upload a smaller image.")
                            return
                            
                        # Download the image
                        image_bytes = await attachment.read()
                        
                        # Convert to base64
                        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
                        
                        # Create image content for the API - use the correct format for DeepSeek API
                        # Format as per DeepSeek API requirements
                        file_ext = attachment.filename.split('.')[-1].lower()
                        mime_type = {
                            'png': 'image/png',
                            'jpg': 'image/jpeg',
                            'jpeg': 'image/jpeg',
                            'gif': 'image/gif',
                            'webp': 'image/webp'
                        }.get(file_ext, 'image/jpeg')
                        
                        image_content = f"data:{mime_type};base64,{image_b64}"
                        has_image = True
                        break  # Only use the first image
            
            # Make request to DeepSeek API
            headers = {
                "Authorization": f"Bearer {self.deepseek_api_key}",
                "Content-Type": "application/json"
            }
            
            # Prepare messages based on whether there's an image
            messages = [
                {"role": "system", "content": "You are a helpful assistant. Provide short, concise answers limited to about 750 tokens. Be direct and get straight to the point while still being helpful."}
            ]
            
            if has_image:
                # Use DeepSeek Chat model for image understanding (DeepSeek API doesn't have a separate vision model)
                model = "deepseek-chat"
                
                # Add the image message
                # For DeepSeek Chat API, we need to use a simpler format without image_url
                messages.append({
                    "role": "user",
                    "content": prompt + "\n[IMAGE]"  # Indicate there's an image in the prompt
                })
            else:
                # Use regular DeepSeek Chat model for text-only
                model = "deepseek-chat"
                messages.append({"role": "user", "content": prompt})
            
            # For image requests, we need to use a different approach
            if has_image:
                # Save the image to a temporary file
                temp_image_path = f"temp_image_{ctx.author.id}.{file_ext}"
                with open(temp_image_path, "wb") as f:
                    f.write(image_bytes)
                
                # Create multipart form data
                data = {
                    "model": model,
                    "messages": json.dumps(messages),
                    "temperature": 0.7,
                    "max_tokens": 750
                }
                
                files = {
                    "image": (f"image.{file_ext}", open(temp_image_path, "rb"), mime_type)
                }
                
                # Debug info
                print(f"Using model: {model} with image")
                print(f"Request data: {json.dumps(data, indent=2)[:500]}...")  # Print first 500 chars
                
                try:
                    response = requests.post(
                        "https://api.deepseek.com/v1/chat/completions",
                        headers=headers,
                        data=data,
                        files=files,
                        timeout=60  # Increased timeout for image processing
                    )
                    
                    # Clean up the temporary file
                    try:
                        os.remove(temp_image_path)
                    except:
                        pass
                except Exception as e:
                    await loading_msg.edit(content=f"❌ Error with image upload: {str(e)}")
                    # Clean up the temporary file
                    try:
                        os.remove(temp_image_path)
                    except:
                        pass
                    return
            else:
                # Regular text request
                data = {
                    "model": model,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 750
                }
                
                # Debug info
                print(f"Using model: {model}")
                print(f"Request data: {json.dumps(data, indent=2)[:500]}...")  # Print first 500 chars
                
                response = requests.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=60  # Increased timeout for image processing
                )
            
            # Check if the request was successful
            if response.status_code != 200:
                error_message = f"API Error: {response.status_code}"
                try:
                    error_data = response.json()
                    print(f"API Error Response: {json.dumps(error_data, indent=2)}")
                    if "error" in error_data:
                        error_message = f"API Error: {error_data['error']['message']}"
                except Exception as e:
                    print(f"Error parsing API error response: {str(e)}")
                    try:
                        error_text = response.text
                        print(f"Raw API Error Response: {error_text[:500]}")  # Print first 500 chars
                        error_message = f"API Error {response.status_code}: {error_text[:100]}..."
                    except:
                        pass
                
                # For 422 errors (validation errors), provide more helpful information
                if response.status_code == 422:
                    error_message += "\n\nPossible causes:\n- Image format not supported (try JPG or PNG)\n- Image too large (try a smaller image)\n- Invalid model name"
                
                await loading_msg.edit(content=f"❌ {error_message}")
                return
            
            # Parse the response
            result = response.json()
            ai_response = result["choices"][0]["message"]["content"]
            
            # Create embed for the response
            embed = discord.Embed(
                title="DeepSeek AI Response",
                description=ai_response,
                color=0x00AAFF
            )
            
            # Add footer with prompt
            truncated_prompt = prompt[:100] + "..." if len(prompt) > 100 else prompt
            embed.set_footer(text=f"Prompt: {truncated_prompt}")
            
            # If there was an image, add it to the embed
            if has_image and ctx.message.attachments:
                embed.set_thumbnail(url=ctx.message.attachments[0].url)
            
            # Edit the loading message with the embed
            await loading_msg.edit(content=None, embed=embed)
            
        except Exception as e:
            await loading_msg.edit(content=f"❌ Error: {str(e)}")
            print(f"AI command error: {traceback.format_exc()}")
    
    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        """Handle manual reaction removal for image navigation"""
        # Ignore bot reactions
        if user.bot:
            return
            
        # Check if this is for an active image search
        if reaction.message.id in self.active_image_searches and str(reaction.emoji) in ["⬅️", "➡️"]:
            query, current_index, images = self.active_image_searches[reaction.message.id]
            
            # Update the index based on the reaction
            if str(reaction.emoji) == "⬅️":
                current_index = (current_index - 1) % len(images)
            elif str(reaction.emoji) == "➡️":
                current_index = (current_index + 1) % len(images)
                
            # Update the stored index
            self.active_image_searches[reaction.message.id] = (query, current_index, images)
            
            # Update the embed
            new_embed = await self.create_image_embed(images[current_index], query, current_index, len(images))
            await reaction.message.edit(embed=new_embed)
    
    async def create_image_embed(self, image_info: Dict, query: str, index: int, total: int) -> discord.Embed:
        """Create an embed for an image search result"""
        embed = discord.Embed(
            title=f"Image Search: {query}",
            description=image_info["title"],
            color=0x3498db
        )
        
        # Add the image
        embed.set_image(url=image_info["url"])
        
        # Add source information
        embed.add_field(
            name="Source",
            value=f"[{image_info['source']}]({image_info['context']})",
            inline=True
        )
        
        # Add navigation information
        embed.set_footer(text=f"Image {index + 1} of {total} | Use ⬅️ ➡️ to navigate")
        
        return embed
    
    async def detect_language(self, text: str) -> str:
        """Detect the language of a text using LibreTranslate API"""
        try:
            api_url = "https://libretranslate.de/detect"
            data = {"q": text}
            
            response = requests.post(api_url, data=data, timeout=10)
            
            if response.status_code != 200:
                return "en"  # Default to English if detection fails
                
            detected = response.json()
            
            if isinstance(detected, list) and len(detected) > 0:
                return detected[0].get("language", "en")
            
            return "en"
        except Exception as e:
            print(f"Error detecting language: {str(e)}")
            return "en"  # Default to English on error
    
    async def translate_text(self, text: str, target_lang: str = "en", source_lang: str = None) -> Union[str, None]:
        """Translate text using LibreTranslate API"""
        if not text:
            return None
            
        # Check cache first
        cache_key = f"{text}_{target_lang}_{source_lang or 'auto'}"
        if cache_key in self.translation_cache:
            return self.translation_cache[cache_key]
            
        try:
            # If source language is not provided, detect it
            if not source_lang:
                source_lang = await self.detect_language(text)
                
            # Don't translate if source and target are the same
            if source_lang == target_lang:
                return text
                
            # Try LibreTranslate API
            api_url = "https://libretranslate.de/translate"
            data = {
                "q": text,
                "source": source_lang,
                "target": target_lang
            }
            
            response = requests.post(api_url, data=data, timeout=15)
            
            if response.status_code != 200:
                # Try an alternative API as fallback
                return await self.translate_text_fallback(text, target_lang, source_lang)
                
            result = response.json()
            
            if "translatedText" in result:
                translated = result["translatedText"]
                # Cache the result
                self.translation_cache[cache_key] = translated
                return translated
                
            return await self.translate_text_fallback(text, target_lang, source_lang)
            
        except Exception as e:
            print(f"Error translating with primary API: {str(e)}")
            # Try fallback on exception
            return await self.translate_text_fallback(text, target_lang, source_lang)
    
    async def translate_text_fallback(self, text: str, target_lang: str = "en", source_lang: str = None) -> Union[str, None]:
        """Fallback translation method using another free API"""
        try:
            # Try LingvaTranslate API as fallback
            api_url = f"https://lingva.ml/api/v1/{source_lang or 'auto'}/{target_lang}/{text}"
            
            response = requests.get(api_url, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                if "translation" in result:
                    translated = result["translation"]
                    # Cache the result
                    cache_key = f"{text}_{target_lang}_{source_lang or 'auto'}"
                    self.translation_cache[cache_key] = translated
                    return translated
            
            # If that fails too, try one more fallback
            api_url = f"https://translate.mentality.rip/translate"
            data = {
                "source": source_lang or "auto",
                "target": target_lang,
                "q": text
            }
            
            response = requests.post(api_url, json=data, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                if "translatedText" in result:
                    translated = result["translatedText"]
                    # Cache the result
                    cache_key = f"{text}_{target_lang}_{source_lang or 'auto'}"
                    self.translation_cache[cache_key] = translated
                    return translated
            
            # If all fails, return the original text
            return text
            
        except Exception as e:
            print(f"Error translating with fallback API: {str(e)}")
            return text  # Return original text on error
    
    @commands.command(aliases=["t", "tr"])
    async def translate(self, ctx, target_lang: str = "en", *, text: str = None):
        """Translate text to another language. Reply to a message or provide text."""
        # Check if it's a reply to a message
        if ctx.message.reference:
            try:
                # Get the message being replied to
                replied_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                
                # If there's no explicit target language in the command, but there's text,
                # then the first argument might actually be text not a language code
                if text is None and target_lang and target_lang.lower() not in self.language_codes:
                    text = target_lang
                    target_lang = "en"  # Default to English
                
                # Send a loading message
                loading_msg = await ctx.send(f"🔄 Translating...")
                
                # Check if the target language is valid
                if target_lang.lower() not in self.language_codes:
                    await loading_msg.edit(content=f"❌ Invalid language code: `{target_lang}`\nUse `-languages` to see available language codes.")
                    return
                
                # Get the content to translate
                content_to_translate = replied_msg.content
                
                # If there's no content but there are embeds, try to extract text from them
                if not content_to_translate and replied_msg.embeds:
                    for embed in replied_msg.embeds:
                        if embed.description:
                            content_to_translate = embed.description
                            break
                
                if not content_to_translate:
                    await loading_msg.edit(content="❌ No text content to translate.")
                    return
                
                # Translate the text
                translated = await self.translate_text(content_to_translate, target_lang.lower())
                
                if translated:
                    # Get source and target language names
                    source_lang = await self.detect_language(content_to_translate)
                    source_lang_name = self.language_codes.get(source_lang, "Unknown")
                    target_lang_name = self.language_codes.get(target_lang.lower(), "Unknown")
                    
                    # Create embed with translation
                    embed = discord.Embed(
                        title=f"Translation: {source_lang_name} → {target_lang_name}",
                        color=0x3498db
                    )
                    
                    # Add original text (truncate if too long)
                    if len(content_to_translate) > 1024:
                        content_to_translate = content_to_translate[:1020] + "..."
                    embed.add_field(
                        name="Original",
                        value=content_to_translate,
                        inline=False
                    )
                    
                    # Add translated text (truncate if too long)
                    if len(translated) > 1024:
                        translated = translated[:1020] + "..."
                    embed.add_field(
                        name="Translation",
                        value=translated,
                        inline=False
                    )
                    
                    # Add author info
                    embed.set_author(
                        name=replied_msg.author.display_name,
                        icon_url=replied_msg.author.display_avatar.url
                    )
                    
                    # Send the embed and delete the loading message
                    await ctx.send(embed=embed)
                    await loading_msg.delete()
                else:
                    await loading_msg.edit(content="❌ Translation failed. Please try again later.")
                
            except discord.NotFound:
                await ctx.send("❌ Could not find the message to translate.")
            except Exception as e:
                await ctx.send(f"❌ An error occurred during translation: {str(e)}")
                traceback.print_exc()
        
        # Direct text translation
        elif text:
            # Send a loading message
            loading_msg = await ctx.send(f"🔄 Translating...")
            
            # Check if the target language is valid
            if target_lang.lower() not in self.language_codes:
                await loading_msg.edit(content=f"❌ Invalid language code: `{target_lang}`\nUse `-languages` to see available language codes.")
                return
            
            # Translate the text
            translated = await self.translate_text(text, target_lang.lower())
            
            if translated:
                # Get source and target language names
                source_lang = await self.detect_language(text)
                source_lang_name = self.language_codes.get(source_lang, "Unknown")
                target_lang_name = self.language_codes.get(target_lang.lower(), "Unknown")
                
                # Create embed with translation
                embed = discord.Embed(
                    title=f"Translation: {source_lang_name} → {target_lang_name}",
                    color=0x3498db
                )
                
                # Add original text (truncate if too long)
                if len(text) > 1024:
                    text = text[:1020] + "..."
                embed.add_field(
                    name="Original",
                    value=text,
                    inline=False
                )
                
                # Add translated text (truncate if too long)
                if len(translated) > 1024:
                    translated = translated[:1020] + "..."
                embed.add_field(
                    name="Translation",
                    value=translated,
                    inline=False
                )
                
                # Send the embed and delete the loading message
                await ctx.send(embed=embed)
                await loading_msg.delete()
            else:
                await loading_msg.edit(content="❌ Translation failed. Please try again later.")
        
        # No text provided and not a reply
        else:
            embed = discord.Embed(
                title="Translation Help",
                description="Translate text to another language.",
                color=0x3498db
            )
            
            embed.add_field(
                name="Usage",
                value="• Reply to a message with `-translate [language_code]`\n"
                      "• Directly translate with `-translate [language_code] [text]`\n"
                      "• Default target language is English if not specified",
                inline=False
            )
            
            embed.add_field(
                name="Examples",
                value="• `-translate fr Hello world`  (English to French)\n"
                      "• `-translate`  (Reply to translate to English)\n"
                      "• `-translate de`  (Reply to translate to German)\n"
                      "• `-translate es Bonjour`  (French to Spanish)",
                inline=False
            )
            
            embed.add_field(
                name="Common Language Codes",
                value="• `en` - English\n"
                      "• `es` - Spanish\n"
                      "• `fr` - French\n"
                      "• `de` - German\n"
                      "• `it` - Italian\n"
                      "• `ja` - Japanese\n"
                      "• `ko` - Korean\n"
                      "• `zh` - Chinese\n"
                      "• `ru` - Russian\n"
                      "• `ar` - Arabic\n"
                      "Use `-languages` for a full list",
                inline=False
            )
            
            await ctx.send(embed=embed)
    
    @commands.command(aliases=["langs", "language", "lang"])
    async def languages(self, ctx):
        """Show available language codes for translation"""
        # Create a paginated embed for language codes
        embeds = []
        
        # Sort languages by name
        sorted_languages = sorted(self.language_codes.items(), key=lambda x: x[1])
        
        # Split into chunks for pagination (20 languages per page)
        chunks = [sorted_languages[i:i + 20] for i in range(0, len(sorted_languages), 20)]
        
        # Create an embed for each chunk
        for i, chunk in enumerate(chunks):
            embed = discord.Embed(
                title=f"Available Languages (Page {i+1}/{len(chunks)})",
                description="Use these language codes with the translation command.",
                color=0x3498db
            )
            
            # Add language codes and names
            lang_text = ""
            for code, name in chunk:
                lang_text += f"`{code}` - {name}\n"
                
            embed.add_field(
                name="Language Codes",
                value=lang_text,
                inline=False
            )
            
            embed.set_footer(text=f"Page {i+1}/{len(chunks)} • Use -translate [code] to translate")
            embeds.append(embed)
        
        # Send the first embed
        current_page = 0
        message = await ctx.send(embed=embeds[current_page])
        
        # Add navigation reactions if there are multiple pages
        if len(embeds) > 1:
            await message.add_reaction("⬅️")
            await message.add_reaction("➡️")
            
            # Define a check function for reactions
            def check(reaction, user):
                return (
                    reaction.message.id == message.id and
                    user == ctx.author and
                    str(reaction.emoji) in ["⬅️", "➡️"]
                )
                
            # Wait for reactions and change pages
            while True:
                try:
                    reaction, user = await self.client.wait_for("reaction_add", timeout=60.0, check=check)
                    
                    # Handle page change
                    if str(reaction.emoji) == "⬅️":
                        current_page = (current_page - 1) % len(embeds)
                    elif str(reaction.emoji) == "➡️":
                        current_page = (current_page + 1) % len(embeds)
                        
                    # Update the message with the new embed
                    await message.edit(embed=embeds[current_page])
                    
                    # Remove the user's reaction
                    try:
                        await reaction.remove(user)
                    except:
                        pass
                        
                except asyncio.TimeoutError:
                    # End pagination after timeout
                    try:
                        await message.clear_reactions()
                    except:
                        pass
                    break
                except Exception as e:
                    print(f"Error in language pagination: {str(e)}")
                    break
    
    @commands.command(aliases=['mt', 'type'])
    async def monkeytype(self, ctx, word_count: int = 30):
        """Start a typing test with the specified number of words"""
        # Validate word count
        if word_count < 10:
            await ctx.send("Please specify at least 10 words for the typing test.")
            return
        if word_count > 250:
            await ctx.send("Please specify at most 250 words for the typing test.")
            return
            
        # Generate random words
        selected_words = random.sample(self.common_words, min(len(self.common_words), word_count))
        
        # Create image with the words
        image_buffer = await self.create_typing_test_image(selected_words)
        
        if not image_buffer:
            await ctx.send("Failed to create typing test image. Please try again.")
            return
            
        # Create embed for the typing test
        embed = discord.Embed(
            title="🖮 Monkeytype Typing Test",
            description=f"Type the following {word_count} words as fast and accurately as possible.",
            color=0x00FFFF
        )
        
        embed.add_field(
            name="Instructions",
            value="• Type all words in a single message\n"
                 "• Be careful with capitalization and punctuation\n"
                 "• The timer starts when you see the image\n"
                 "• Your typing speed and accuracy will be calculated",
            inline=False
        )
        
        embed.set_footer(text=f"Typing test for {ctx.author.display_name} | {word_count} words")
        
        # Send the embed with the image
        test_msg = await ctx.send(
            embed=embed,
            file=discord.File(fp=image_buffer, filename='typing_test.png')
        )
        
        # Store the test information
        self.active_typing_tests[ctx.author.id] = {
            "words": selected_words,
            "start_time": datetime.now(),
            "message_id": test_msg.id,
            "channel_id": ctx.channel.id
        }
        
        # Notify the user that the test has started
        await ctx.send(f"{ctx.author.mention} Your typing test has started! Type the words shown in the image.")
    
    @commands.command(aliases=['mtc', 'challenge'])
    async def mtchallenge(self, ctx, user: discord.Member, word_count: int = 30):
        """Challenge another user to a typing test"""
        # Check if the user is challenging themselves
        if user.id == ctx.author.id:
            await ctx.send("You can't challenge yourself!")
            return
            
        # Check if the user is a bot
        if user.bot:
            await ctx.send("You can't challenge a bot!")
            return
            
        # Validate word count
        if word_count < 10:
            await ctx.send("Please specify at least 10 words for the typing test.")
            return
        if word_count > 250:
            await ctx.send("Please specify at most 250 words for the typing test.")
            return
            
        # Generate a unique challenge ID
        challenge_id = f"{ctx.author.id}-{user.id}-{int(time.time())}"
        
        # Generate random words for the challenge
        selected_words = random.sample(self.common_words, min(len(self.common_words), word_count))
        
        # Store the challenge information
        self.typing_challenges[challenge_id] = {
            "challenger": ctx.author.id,
            "challenged": user.id,
            "word_count": word_count,
            "words": selected_words,
            "results": {},
            "channel_id": ctx.channel.id,
            "created_at": datetime.now()
        }
        
        # Add to pending challenges
        if user.id not in self.pending_challenges:
            self.pending_challenges[user.id] = []
        self.pending_challenges[user.id].append(challenge_id)
        
        # Create embed for the challenge
        embed = discord.Embed(
            title="⚔️ Typing Challenge!",
            description=f"{ctx.author.mention} has challenged {user.mention} to a typing test!",
            color=0xFF9900
        )
        
        embed.add_field(
            name="Details",
            value=f"• {word_count} words\n"
                 f"• Both users will type the same text\n"
                 f"• Speed and accuracy will be compared",
            inline=False
        )
        
        embed.add_field(
            name="How to Accept",
            value=f"{user.mention}, type `-accept` to accept the challenge!",
            inline=False
        )
        
        embed.set_footer(text=f"Challenge ID: {challenge_id} | Expires in 10 minutes")
        
        # Send the challenge
        await ctx.send(embed=embed)
        
        # Set a timer to delete the challenge if not accepted
        self.client.loop.create_task(self.delete_challenge_after_timeout(challenge_id, 600))  # 10 minutes
    
    async def delete_challenge_after_timeout(self, challenge_id, timeout):
        """Delete a challenge after a timeout period"""
        await asyncio.sleep(timeout)
        
        # Check if the challenge still exists
        if challenge_id in self.typing_challenges:
            challenge = self.typing_challenges[challenge_id]
            
            # If the challenge hasn't been started by both users, delete it
            if len(challenge["results"]) < 2:
                # Get the channel
                channel = self.client.get_channel(challenge["channel_id"])
                
                if channel:
                    # Get the users
                    try:
                        challenger = await self.client.fetch_user(challenge["challenger"])
                        challenged = await self.client.fetch_user(challenge["challenged"])
                        
                        # Send a timeout message
                        await channel.send(f"⏰ The typing challenge between {challenger.mention} and {challenged.mention} has expired.")
                    except:
                        pass
                
                # Remove from pending challenges
                if challenge["challenged"] in self.pending_challenges:
                    if challenge_id in self.pending_challenges[challenge["challenged"]]:
                        self.pending_challenges[challenge["challenged"]].remove(challenge_id)
                        
                        if not self.pending_challenges[challenge["challenged"]]:
                            del self.pending_challenges[challenge["challenged"]]
                
                # Delete the challenge
                del self.typing_challenges[challenge_id]
    
    @commands.command()
    async def accept(self, ctx, challenge_id: str = None):
        """Accept a typing challenge"""
        # If no challenge_id is provided, check if the user has any pending challenges
        if not challenge_id:
            if ctx.author.id not in self.pending_challenges or not self.pending_challenges[ctx.author.id]:
                await ctx.send("You don't have any pending typing challenges. Please provide a challenge ID.")
                return
            
            # Use the most recent challenge
            challenge_id = self.pending_challenges[ctx.author.id][-1]
        
        # Check if the challenge exists
        if challenge_id not in self.typing_challenges:
            await ctx.send("This challenge doesn't exist or has expired.")
            return
            
        challenge = self.typing_challenges[challenge_id]
        
        # Check if the user is the one being challenged
        if ctx.author.id != challenge["challenged"]:
            await ctx.send("This challenge is not for you.")
            return
            
        # Check if the challenge has already been accepted
        if ctx.author.id in challenge["results"]:
            await ctx.send("You've already accepted this challenge.")
            return
            
        # Remove from pending challenges
        if ctx.author.id in self.pending_challenges and challenge_id in self.pending_challenges[ctx.author.id]:
            self.pending_challenges[ctx.author.id].remove(challenge_id)
            
            if not self.pending_challenges[ctx.author.id]:
                del self.pending_challenges[ctx.author.id]
        
        # Get the challenger
        try:
            challenger = await self.client.fetch_user(challenge["challenger"])
        except:
            await ctx.send("Could not find the challenger. The challenge has been cancelled.")
            del self.typing_challenges[challenge_id]
            return
        
        # Send a notification that the challenge has been accepted
        embed = discord.Embed(
            title="⚔️ Challenge Accepted!",
            description=f"{ctx.author.mention} has accepted {challenger.mention}'s typing challenge!",
            color=0xFF9900
        )
        
        embed.add_field(
            name="Get Ready!",
            value="The typing test will begin shortly. Both users will see the same text.",
            inline=False
        )
        
        await ctx.send(embed=embed)
        
        # Start the countdown
        countdown_msg = await ctx.send("Starting in 5...")
        
        for i in range(4, 0, -1):
            await asyncio.sleep(1)
            await countdown_msg.edit(content=f"Starting in {i}...")
        
        await asyncio.sleep(1)
        await countdown_msg.edit(content="Go!")
        
        # Create image with the words
        image_buffer = await self.create_typing_test_image(challenge["words"])
        
        if not image_buffer:
            await ctx.send("Failed to create typing test image. Please try again.")
            return
            
        # Create embed for the typing test
        embed = discord.Embed(
            title="⚔️ Challenge Typing Test",
            description=f"Type the following {challenge['word_count']} words as fast and accurately as possible.",
            color=0xFF9900
        )
        
        
        embed.add_field(
            name="Instructions",
            value="• Type all words in a single message\n"
                 "• Be careful with capitalization and punctuation\n"
                 "• The timer starts now\n"
                 "• Your results will be compared with your opponent",
            inline=False
        )
        
        embed.add_field(
            name="Challenge",
            value=f"{challenger.mention} vs {ctx.author.mention}",
            inline=False
        )
        
        embed.set_footer(text=f"Challenge ID: {challenge_id}")
        
        # Send the embed with the image to both users in the same channel
        test_msg = await ctx.send(
            content=f"{challenger.mention} {ctx.author.mention}",
            embed=embed,
            file=discord.File(fp=image_buffer, filename='challenge_test.png')
        )
        
        # Store the test information in active typing tests for both users
        current_time = datetime.now()
        
        # For the challenged user
        self.active_typing_tests[ctx.author.id] = {
            "words": challenge["words"],
            "start_time": current_time,
            "message_id": test_msg.id,
            "channel_id": ctx.channel.id,
            "challenge_id": challenge_id
        }
        
        # For the challenger
        self.active_typing_tests[challenger.id] = {
            "words": challenge["words"],
            "start_time": current_time,
            "message_id": test_msg.id,
            "channel_id": ctx.channel.id,
            "challenge_id": challenge_id
        }
        
        # Notify both users that the test has started
        await ctx.send(f"The typing test has started! {challenger.mention} and {ctx.author.mention}, type the words shown in the image.")
    
    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        """Handle button interactions"""
        if not interaction.data or "custom_id" not in interaction.data:
            return
            
        custom_id = interaction.data["custom_id"]
        
        # Check if this is a challenge start button
        if custom_id.startswith("start_challenge_"):
            challenge_id = custom_id.replace("start_challenge_", "")
            
            # Check if the challenge exists
            if challenge_id not in self.typing_challenges:
                await interaction.response.send_message("This challenge doesn't exist or has expired.", ephemeral=True)
                return
                
            challenge = self.typing_challenges[challenge_id]
            
            # Check if the user is the challenger
            if interaction.user.id != challenge["challenger"]:
                await interaction.response.send_message("This challenge is not for you.", ephemeral=True)
                return
                
            # Check if the challenger has already taken the test
            if interaction.user.id in challenge["results"]:
                await interaction.response.send_message("You've already taken this challenge test.", ephemeral=True)
                return
                
            # Create image with the words
            image_buffer = await self.create_typing_test_image(challenge["words"])
            
            if not image_buffer:
                await interaction.response.send_message("Failed to create typing test image. Please try again.", ephemeral=True)
                return
                
            # Acknowledge the interaction
            await interaction.response.defer()
                
            # Create embed for the typing test
            embed = discord.Embed(
                title="⚔️ Challenge Typing Test",
                description=f"Type the following {challenge['word_count']} words as fast and accurately as possible.",
                color=0xFF9900
            )
            
            embed.add_field(
                name="Instructions",
                value="• Type all words in a single message\n"
                     "• Be careful with capitalization and punctuation\n"
                     "• The timer starts when you see the image\n"
                     "• Your results will be compared with your opponent",
                inline=False
            )
            
            # Get the challenged user
            try:
                challenged = await self.client.fetch_user(challenge["challenged"])
                embed.add_field(
                    name="Challenge",
                    value=f"{interaction.user.mention} vs {challenged.mention}",
                    inline=False
                )
            except:
                embed.add_field(
                    name="Challenge",
                    value=f"Typing challenge",
                    inline=False
                )
            
            embed.set_footer(text=f"Challenge ID: {challenge_id}")
            
            # Send the embed with the image
            test_msg = await interaction.followup.send(
                embed=embed,
                file=discord.File(fp=image_buffer, filename='challenge_test.png')
            )
            
            # Store the test information in active typing tests
            self.active_typing_tests[interaction.user.id] = {
                "words": challenge["words"],
                "start_time": datetime.now(),
                "message_id": test_msg.id,
                "channel_id": interaction.channel_id,
                "challenge_id": challenge_id
            }
            
            # Notify the user that the test has started
            await interaction.followup.send(f"{interaction.user.mention} Your challenge typing test has started! Type the words shown in the image.")
    
    @commands.command(aliases=['mtl', 'challenges'])
    async def mtlist(self, ctx):
        """List your pending typing challenges"""
        if ctx.author.id not in self.pending_challenges or not self.pending_challenges[ctx.author.id]:
            await ctx.send("You don't have any pending typing challenges.")
            return
            
        # Create embed for the pending challenges
        embed = discord.Embed(
            title="📝 Your Pending Typing Challenges",
            color=0xFF9900
        )
        
        for challenge_id in self.pending_challenges[ctx.author.id]:
            if challenge_id in self.typing_challenges:
                challenge = self.typing_challenges[challenge_id]
                
                # Get the challenger
                try:
                    challenger = await self.client.fetch_user(challenge["challenger"])
                    challenger_name = challenger.display_name
                except:
                    challenger_name = "Unknown User"
                    
                # Calculate time left
                time_created = challenge["created_at"]
                time_left = 600 - (datetime.now() - time_created).total_seconds()
                
                if time_left <= 0:
                    # This challenge should be deleted soon by the timeout task
                    continue
                    
                minutes_left = int(time_left / 60)
                seconds_left = int(time_left % 60)
                
                embed.add_field(
                    name=f"Challenge from {challenger_name}",
                    value=f"• {challenge['word_count']} words\n"
                         f"• Expires in {minutes_left}m {seconds_left}s\n"
                         f"• To accept: `-accept {challenge_id}`",
                    inline=False
                )
        
        if not embed.fields:
            await ctx.send("You don't have any pending typing challenges.")
            return
            
        await ctx.send(embed=embed)
    
    async def create_typing_test_image(self, words):
        """Create an image with the words for the typing test"""
        try:
            # Create a blank image with white background
            width = 1000
            height = 600
            image = Image.new('RGB', (width, height), (255, 255, 255))
            draw = ImageDraw.Draw(image)
            
            # Try to find a system font
            system_fonts = [
                '/usr/share/fonts/TTF/DejaVuSans.ttf',  # Linux
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',  # Ubuntu
                '/Library/Fonts/Arial.ttf',  # macOS
                'C:\\Windows\\Fonts\\arial.ttf',  # Windows
                self.font_path
            ]
            
            font_path = None
            for font in system_fonts:
                if font and os.path.exists(font):
                    font_path = font
                    break
                    
            # Use default font if none found
            if not font_path:
                # Add text using default font
                text = " ".join(words)
                lines = textwrap.wrap(text, width=40)
                y_position = 50
                
                for line in lines:
                    draw.text((50, y_position), line, fill=(0, 0, 0), font=ImageFont.load_default())
                    y_position += 20
            else:
                # Use custom font
                font_size = 24
                font = ImageFont.truetype(font_path, font_size)
                
                # Join words with spaces
                text = " ".join(words)
                
                # Wrap text to fit the image width
                lines = []
                current_line = []
                current_width = 0
                max_width = width - 100  # Leave some margin
                
                for word in words:
                    # Get word dimensions
                    word_bbox = draw.textbbox((0, 0), word + " ", font=font)
                    word_width = word_bbox[2] - word_bbox[0]
                    
                    if current_width + word_width <= max_width:
                        current_line.append(word)
                        current_width += word_width
                    else:
                        lines.append(" ".join(current_line))
                        current_line = [word]
                        current_width = word_width
                
                # Add the last line
                if current_line:
                    lines.append(" ".join(current_line))
                
                # Draw the text
                y_position = 50
                for line in lines:
                    draw.text((50, y_position), line, fill=(0, 0, 0), font=font)
                    y_position += font_size * 1.5
                    
                # Add some visual noise to prevent OCR
                for _ in range(30):
                    x1 = random.randint(0, width)
                    y1 = random.randint(0, height)
                    x2 = random.randint(0, width)
                    y2 = random.randint(0, height)
                    color = (random.randint(100, 200), random.randint(100, 200), random.randint(100, 200))
                    draw.line([(x1, y1), (x2, y2)], fill=color, width=2)
            
            # Save the image to a bytes buffer
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            buffer.seek(0)
            
            return buffer
        except Exception as e:
            print(f"Error creating typing test image: {str(e)}")
            return None
    