"""
Weather command for displaying weather information.
"""

import discord
from discord.ext import commands

class WeatherCommand(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.weather_manager = None
        
    def set_weather_manager(self, weather_manager):
        """Set the weather manager instance."""
        self.weather_manager = weather_manager
        
    @commands.command()
    async def weather(self, ctx, *, location: str = None):
        """Get weather information for a location."""
        if not self.weather_manager:
            await ctx.send("Weather system not available.")
            return
            
        if not location:
            await ctx.send("Please provide a location. Example: `-weather London`")
            return
            
        temp_msg = await ctx.send(f"Fetching weather data for {location}...")
        
        weather_data = await self.weather_manager.get_weather(location)
        
        if "error" in weather_data:
            await temp_msg.edit(content=weather_data["error"])
            return
            
        embed = discord.Embed(
            title=f"Weather for {weather_data['location']}",
            description=f"**Current Conditions:** {weather_data['weather_emoji']} {weather_data['current_temp']}°C",
            color=0x3498db
        )
        
        embed.add_field(
            name="Feels Like",
            value=f"**{weather_data['feels_like']}°C**",
            inline=True
        )
        
        embed.add_field(
            name="Today's Range",
            value=f"🔽 {weather_data['today_min']}°C / 🔼 {weather_data['today_max']}°C",
            inline=True
        )
        
        embed.add_field(
            name="Humidity & Wind",
            value=f"💧 {weather_data['humidity']}% | 💨 {weather_data['wind_speed']} km/h",
            inline=True
        )
        
        # Add 5-day forecast
        if weather_data['forecast']:
            forecast_text = ""
            for day_data in weather_data['forecast']:
                forecast_text += f"{day_data['day']}: {day_data['emoji']} {day_data['min_temp']}°C - {day_data['max_temp']}°C\n"
                
            embed.add_field(
                name="5-Day Forecast",
                value=forecast_text,
                inline=False
            )
            
        embed.set_footer(text=f"Last updated: {weather_data['timestamp']}")
        
        await ctx.send(embed=embed)
        await temp_msg.delete()

async def setup(client):
    """Setup function for the Weather command."""
    client.add_cog(WeatherCommand(client))