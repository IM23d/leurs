import discord
from discord.ext import commands
import json
import os
from datetime import datetime
import pytz
from typing import Optional

class TimezoneCog(commands.Cog, name="timezone"):
    def __init__(self, bot):
        self.bot = bot
        self.timezones_file = "data/timezones.json"
        self.preferences_file = "data/timezone_preferences.json"
        self.load_timezones()
        self.load_preferences()

    def load_timezones(self):
        if not os.path.exists("data"):
            os.makedirs("data")
        
        if os.path.exists(self.timezones_file):
            with open(self.timezones_file, "r") as f:
                self.timezones = json.load(f)
        else:
            self.timezones = {}
            self.save_timezones()

    def load_preferences(self):
        if os.path.exists(self.preferences_file):
            with open(self.preferences_file, "r") as f:
                self.preferences = json.load(f)
        else:
            self.preferences = {}
            self.save_preferences()

    def save_timezones(self):
        with open(self.timezones_file, "w") as f:
            json.dump(self.timezones, f, indent=4)

    def save_preferences(self):
        with open(self.preferences_file, "w") as f:
            json.dump(self.preferences, f, indent=4)

    def format_time(self, time: datetime, user_id: str) -> str:
        format_24h = self.preferences.get(str(user_id), False)
        date_str = time.strftime("%B %d")
        if format_24h:
            time_str = time.strftime("%H:%M")
        else:
            time_str = time.strftime("%I:%M %p")
        return f"{date_str}, {time_str}"

    def find_timezone(self, query: str) -> Optional[str]:
        # Convert to lowercase for case-insensitive matching
        query = query.lower()
        
        # Common city mappings (add more as needed)
        city_mappings = {
            # Europe
            'london': 'Europe/London',
            'berlin': 'Europe/Berlin',
            'paris': 'Europe/Paris',
            'amsterdam': 'Europe/Amsterdam',
            'rome': 'Europe/Rome',
            'madrid': 'Europe/Madrid',
            'vienna': 'Europe/Vienna',
            'brussels': 'Europe/Brussels',
            'stockholm': 'Europe/Stockholm',
            'oslo': 'Europe/Oslo',
            'copenhagen': 'Europe/Copenhagen',
            'helsinki': 'Europe/Helsinki',
            'athens': 'Europe/Athens',
            'moscow': 'Europe/Moscow',
            'warsaw': 'Europe/Warsaw',
            'budapest': 'Europe/Budapest',
            'prague': 'Europe/Prague',
            'zurich': 'Europe/Zurich',
            'lisbon': 'Europe/Lisbon',
            'dublin': 'Europe/Dublin',
            'sofia': 'Europe/Sofia',
            'belgrade': 'Europe/Belgrade',
            'zagreb': 'Europe/Zagreb',
            'ljubljana': 'Europe/Ljubljana',
            'sarajevo': 'Europe/Sarajevo',
            'tirana': 'Europe/Tirane',
            'skopje': 'Europe/Skopje',
            'reykjavik': 'Atlantic/Reykjavik',
            'vilnius': 'Europe/Vilnius',
            'riga': 'Europe/Riga',
            'tallinn': 'Europe/Tallinn',

            # Asia
            'dubai': 'Asia/Dubai',
            'tokyo': 'Asia/Tokyo',
            'seoul': 'Asia/Seoul',
            'shanghai': 'Asia/Shanghai',
            'singapore': 'Asia/Singapore',
            'hong_kong': 'Asia/Hong_Kong',
            'bangkok': 'Asia/Bangkok',
            'jakarta': 'Asia/Jakarta',
            'manila': 'Asia/Manila',
            'kuala_lumpur': 'Asia/Kuala_Lumpur',
            'taipei': 'Asia/Taipei',
            'mumbai': 'Asia/Kolkata',
            'delhi': 'Asia/Kolkata',
            'karachi': 'Asia/Karachi',
            'beijing': 'Asia/Shanghai',
            'tehran': 'Asia/Tehran',
            'riyadh': 'Asia/Riyadh',
            'doha': 'Asia/Qatar',
            'kuwait_city': 'Asia/Kuwait',
            'baku': 'Asia/Baku',
            'tashkent': 'Asia/Tashkent',
            'almaty': 'Asia/Almaty',
            'bishkek': 'Asia/Bishkek',
            'kathmandu': 'Asia/Kathmandu',
            'yangon': 'Asia/Yangon',
            'male': 'Indian/Maldives',
            'colombo': 'Asia/Colombo',

            # Americas
            'los_angeles': 'America/Los_Angeles',
            'new_york': 'America/New_York',
            'chicago': 'America/Chicago',
            'toronto': 'America/Toronto',
            'vancouver': 'America/Vancouver',
            'sao_paulo': 'America/Sao_Paulo',
            'mexico_city': 'America/Mexico_City',
            'buenos_aires': 'America/Argentina/Buenos_Aires',
            'santiago': 'America/Santiago',
            'lima': 'America/Lima',
            'bogota': 'America/Bogota',
            'miami': 'America/New_York',
            'dallas': 'America/Chicago',
            'denver': 'America/Denver',
            'phoenix': 'America/Phoenix',
            'houston': 'America/Chicago',
            'montreal': 'America/Toronto',
            'quebec': 'America/Toronto',
            'san_francisco': 'America/Los_Angeles',
            'seattle': 'America/Los_Angeles',
            'atlanta': 'America/New_York',
            'orlando': 'America/New_York',
            'caracas': 'America/Caracas',
            'montevideo': 'America/Montevideo',
            'quito': 'America/Guayaquil',
            'panama_city': 'America/Panama',

            # Oceania
            'sydney': 'Australia/Sydney',
            'melbourne': 'Australia/Melbourne',
            'brisbane': 'Australia/Brisbane',
            'perth': 'Australia/Perth',
            'adelaide': 'Australia/Adelaide',
            'auckland': 'Pacific/Auckland',
            'wellington': 'Pacific/Auckland',
            'christchurch': 'Pacific/Auckland',

            # more tz
            'cairo': 'Africa/Cairo',
            'johannesburg': 'Africa/Johannesburg',
            'lagos': 'Africa/Lagos',
            'nairobi': 'Africa/Nairobi',
            'casablanca': 'Africa/Casablanca',
            'cape_town': 'Africa/Johannesburg',
            'tunis': 'Africa/Tunis',

            'darwin': 'Australia/Darwin',
            'hobart': 'Australia/Hobart',
            'port_moresby': 'Pacific/Port_Moresby',
            'suva': 'Pacific/Fiji',

            # Africa
            'kampala': 'Africa/Kampala',
            'addis_ababa': 'Africa/Addis_Ababa',
            'accra': 'Africa/Accra',
            'abidjan': 'Africa/Abidjan',
            'algiers': 'Africa/Algiers',
            'dakar': 'Africa/Dakar',

            # Middle East
            'amman': 'Asia/Amman',
            'jerusalem': 'Asia/Jerusalem',
            'baghdad': 'Asia/Baghdad',
            'beirut': 'Asia/Beirut',
            'muscat': 'Asia/Muscat'
        }

        # Common timezone abbreviations
        tz_mappings = {
            'cet': 'Europe/Paris',
            'cest': 'Europe/Paris',
            'est': 'America/New_York',
            'edt': 'America/New_York',
            'pst': 'America/Los_Angeles',
            'pdt': 'America/Los_Angeles',
            'gmt': 'Etc/GMT',
            'utc': 'UTC',
            'bst': 'Europe/London',
            'ist': 'Asia/Kolkata',
            'jst': 'Asia/Tokyo',
            'aest': 'Australia/Sydney',
            'aedt': 'Australia/Sydney',
            'nzst': 'Pacific/Auckland',
            'nzdt': 'Pacific/Auckland',
            'hkt': 'Asia/Hong_Kong',
            'mst': 'America/Denver',
            'mdt': 'America/Denver',
            'cst': 'America/Chicago',
            'cdt': 'America/Chicago',
            'wat': 'Africa/Lagos',
            'eat': 'Africa/Nairobi',
            'sgt': 'Asia/Singapore',

            'gmt+0': 'Etc/GMT',
            'gmt+1': 'Etc/GMT-1',
            'gmt+2': 'Etc/GMT-2',
            'gmt+3': 'Etc/GMT-3',
            'gmt+4': 'Etc/GMT-4',
            'gmt+5': 'Etc/GMT-5',
            'gmt+6': 'Etc/GMT-6',
            'gmt+7': 'Etc/GMT-7',
            'gmt+8': 'Etc/GMT-8',
            'gmt+9': 'Etc/GMT-9',
            'gmt+10': 'Etc/GMT-10',
            'gmt+11': 'Etc/GMT-11',
            'gmt+12': 'Etc/GMT-12',
            'gmt-1': 'Etc/GMT+1',
            'gmt-2': 'Etc/GMT+2',
            'gmt-3': 'Etc/GMT+3',
            'gmt-4': 'Etc/GMT+4',
            'gmt-5': 'Etc/GMT+5',
            'gmt-6': 'Etc/GMT+6',
            'gmt-7': 'Etc/GMT+7',
            'gmt-8': 'Etc/GMT+8',
            'gmt-9': 'Etc/GMT+9',
            'gmt-10': 'Etc/GMT+10',
            'gmt-11': 'Etc/GMT+11',
            'gmt-12': 'Etc/GMT+12'
        }

        # Try exact matches first
        if query in pytz.all_timezones_set:
            return query
        
        # Check city mappings
        if query in city_mappings:
            return city_mappings[query]
        
        # Check timezone abbreviations
        if query in tz_mappings:
            return tz_mappings[query]

        # Try to find partial matches in city names
        for city, tz in city_mappings.items():
            if query in city:
                return tz

        return None

    @commands.group(name="tz", invoke_without_command=True)
    async def timezone(self, ctx, member: discord.Member = None):
        target_member = member or ctx.author
        user_id = str(target_member.id)

        if user_id not in self.timezones:
            if member:
                embed = discord.Embed(
                    description=f"❌ {target_member.mention} hasn't set their timezone yet!",
                    color=0x2F3136
                )
            else:
                embed = discord.Embed(
                    description="❌ You haven't set your timezone yet! Use `tz set <timezone/city>` to set it.",
                    color=0x2F3136
                )
            await ctx.send(embed=embed)
            return

        timezone_str = self.timezones[user_id]
        timezone = pytz.timezone(timezone_str)
        current_time = datetime.now(timezone)
        
        # Use the viewer's time format preference
        formatted_time = self.format_time(current_time, str(ctx.author.id))
        
        if target_member == ctx.author:
            description = f"{ctx.author.mention} Your current time is **{formatted_time}**"
        else:
            description = f"{target_member.mention} Their current time is **{formatted_time}**"

        embed = discord.Embed(
            description=description,
            color=0x2F3136
        )
        await ctx.send(embed=embed)

    @timezone.command(name="set")
    async def set_timezone(self, ctx, *, timezone_str: str):
        timezone_id = self.find_timezone(timezone_str)
        
        if not timezone_id:
            embed = discord.Embed(
                description="❌ Invalid timezone! Please use a valid timezone code (e.g., CEST) or city name (e.g., Berlin).",
                color=0x2F3136
            )
            await ctx.send(embed=embed)
            return

        try:
            timezone = pytz.timezone(timezone_id)
            current_time = datetime.now(timezone)
            formatted_time = self.format_time(current_time, str(ctx.author.id))
            
            self.timezones[str(ctx.author.id)] = timezone_id
            self.save_timezones()

            embed = discord.Embed(
                description=f"{ctx.author.mention} Your current time is **{formatted_time}**",
                color=0x2F3136
            )
            await ctx.send(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                description="❌ An error occurred while setting your timezone. Please try again.",
                color=0x2F3136
            )
            await ctx.send(embed=embed)

    @timezone.command(name="format")
    async def toggle_format(self, ctx):
        user_id = str(ctx.author.id)
        current_format = self.preferences.get(user_id, False)
        self.preferences[user_id] = not current_format
        self.save_preferences()

        new_format = "24-hour" if self.preferences[user_id] else "12-hour"
        
        if user_id in self.timezones:
            timezone = pytz.timezone(self.timezones[user_id])
            current_time = datetime.now(timezone)
            formatted_time = self.format_time(current_time, user_id)
            
            embed = discord.Embed(
                description=f"{ctx.author.mention} Time format set to **{new_format}**\nYour current time is **{formatted_time}**",
                color=0x2F3136
            )
        else:
            embed = discord.Embed(
                description=f"{ctx.author.mention} Time format set to **{new_format}**\nSet your timezone with `tz set <timezone/city>` to see the current time",
                color=0x2F3136
            )
            
        await ctx.send(embed=embed) 