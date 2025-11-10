"""
Weather manager for handling weather functionality.
"""

import requests
from datetime import datetime
from typing import Optional, Tuple, Dict, List

class WeatherManager:
    def __init__(self):
        # Weather code to emoji mapping
        self.weather_codes = {
            # Clear
            0: "☀️", 
            # Partly cloudy
            1: "🌤️",  
            2: "⛅",  
            3: "☁️",  
            # Fog
            45: "🌫️",
            48: "🌫️",
            # Drizzle
            51: "🌦️",
            53: "🌦️",
            55: "🌧️",
            # Freezing Drizzle
            56: "🌨️",
            57: "🌨️",
            # Rain
            61: "🌦️",
            63: "🌧️",
            65: "🌧️",
            # Freezing Rain
            66: "🌨️",
            67: "🌨️",
            # Snow
            71: "🌨️",
            73: "❄️",
            75: "❄️",
            # Snow grains
            77: "❄️",
            # Rain showers
            80: "🌦️",
            81: "🌧️",
            82: "🌧️",
            # Snow showers
            85: "🌨️", 
            86: "❄️",
            # Thunderstorm
            95: "⛈️",
            96: "⛈️",
            99: "⛈️",
            # Default
            -1: "🌡️"
        }
        
    def get_weather_emoji(self, weather_code: int) -> str:
        """Get emoji for weather code."""
        return self.weather_codes.get(weather_code, self.weather_codes[-1])
        
    async def geocode_location(self, location: str) -> Optional[Tuple[float, float, str, str]]:
        """Geocode a location to get coordinates."""
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
            
    async def get_weather(self, location: str) -> Optional[Dict]:
        """Get weather data for a location."""
        try:
            # Geocode the location
            geocode_result = await self.geocode_location(location)
            
            if not geocode_result:
                return {"error": f"Couldn't find location: {location}"}
                
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
                return {"error": "Error fetching weather data. Please try again later."}
                
            weather_data = response.json()
            
            # Process current weather data
            current = weather_data["current"]
            current_temp = round(current["temperature_2m"])
            feels_like = round(current["apparent_temperature"])
            humidity = current["relative_humidity_2m"]
            wind_speed = current["wind_speed_10m"]
            weather_code = current["weather_code"]
            weather_emoji = self.get_weather_emoji(weather_code)
            
            daily = weather_data["daily"]
            today_min = round(daily["temperature_2m_min"][0])
            today_max = round(daily["temperature_2m_max"][0])
            
            # Build forecast
            forecast = []
            for i in range(1, min(6, len(daily["time"]))):
                date_str = daily["time"][i]
                dt = datetime.fromisoformat(date_str)
                day_name = dt.strftime("%A")
                
                min_temp = round(daily["temperature_2m_min"][i])
                max_temp = round(daily["temperature_2m_max"][i])
                day_weather_code = daily["weather_code"][i]
                day_emoji = self.get_weather_emoji(day_weather_code)
                
                forecast.append({
                    "day": day_name,
                    "emoji": day_emoji,
                    "min_temp": min_temp,
                    "max_temp": max_temp
                })
            
            location_name = f"{city_name}, {country}" if country else city_name
            
            return {
                "location": location_name,
                "current_temp": current_temp,
                "feels_like": feels_like,
                "weather_emoji": weather_emoji,
                "humidity": humidity,
                "wind_speed": wind_speed,
                "today_min": today_min,
                "today_max": today_max,
                "forecast": forecast,
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            print(f"Weather error: {e}")
            return {"error": f"Error getting weather data: {str(e)}"}