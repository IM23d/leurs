"""
Image search manager for handling image search functionality.
"""

import time
import random
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple

class ImageManager:
    def __init__(self):
        # API keys and configuration
        self.google_api_key = ""
        self.google_cse_id = ""
        
        # Caching
        self.image_search_cache: Dict[str, List[Dict]] = {}
        self.active_image_searches: Dict[int, Tuple[str, int, List[Dict]]] = {}
        self.max_cache_size = 50
        
        # Rate limiting
        self.daily_search_count = 0
        self.last_count_reset = datetime.now()
        self.user_cooldowns: Dict[int, float] = {}
        self.cooldown_time = 300  # 5 minutes
        self.daily_limit = 100
        
    def set_google_credentials(self, api_key: str, cse_id: str = None):
        """Set Google API credentials."""
        self.google_api_key = api_key
        if cse_id:
            self.google_cse_id = cse_id
            
    def clean_image_cache(self):
        """Clean up image cache if it gets too large."""
        if len(self.image_search_cache) > self.max_cache_size:
            num_to_remove = max(1, int(self.max_cache_size * 0.2))
            keys_to_remove = list(self.image_search_cache.keys())[:num_to_remove]
            
            for key in keys_to_remove:
                del self.image_search_cache[key]
                
    def check_reset_daily_count(self):
        """Reset daily count if it's a new day."""
        now = datetime.now()
        if now.date() > self.last_count_reset.date():
            self.daily_search_count = 0
            self.last_count_reset = now
            return True
        return False
        
    def increment_search_count(self) -> bool:
        """Increment search count and check if limit exceeded."""
        self.check_reset_daily_count()
        self.daily_search_count += 1
        return self.daily_search_count > self.daily_limit
        
    def check_user_cooldown(self, user_id: int) -> Tuple[bool, int]:
        """Check if user is on cooldown."""
        now = time.time()
        
        if user_id in self.user_cooldowns:
            last_use = self.user_cooldowns[user_id]
            elapsed = now - last_use
            
            if elapsed < self.cooldown_time:
                return True, int(self.cooldown_time - elapsed)
        
        self.user_cooldowns[user_id] = now
        return False, 0
        
    async def search_images(self, query: str, num: int = 10) -> List[Dict]:
        """Search for images using Google API or fallback to Unsplash."""
        # Special case for random images
        if query.lower() == "random":
            categories = ["nature", "animals", "technology", "architecture", "food", "travel", 
                         "people", "business", "sports", "health", "fashion", "art"]
            random_categories = random.sample(categories, min(5, len(categories)))
            query = ",".join(random_categories)
        
        # Check if we have this query cached
        if query in self.image_search_cache:
            return self.image_search_cache[query]
            
        # Try Google API first if available
        if self.google_api_key and self.google_cse_id:
            try:
                # Check if we've hit the daily limit
                if self.increment_search_count():
                    print("Daily Google API search limit reached, falling back to free API")
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
                    
                    response = requests.get(search_url, params=params, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
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
                        self.clean_image_cache()
                        return images
                    else:
                        print(f"Error searching for images: {response.status_code} {response.text}")
            except Exception as e:
                print(f"Error searching for images with Google API: {str(e)}")
        
        # Fallback to Unsplash API (free, no key required)
        try:
            encoded_query = query.replace(" ", "-").replace(",", ",")
            images = []
            
            for i in range(min(10, num)):
                try:
                    random_param = random.randint(1, 1000000)
                    image_url = f"https://source.unsplash.com/featured/?{encoded_query}&sig={i}&random={random_param}"
                    
                    # Verify the image URL is valid
                    head_response = requests.head(image_url, timeout=5)
                    if head_response.status_code != 200:
                        continue
                    
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
            
            # Cache results if we got some images
            if images:
                self.image_search_cache[query] = images
                self.clean_image_cache()
                
            return images
                
        except Exception as e:
            print(f"Error searching for images with free API: {str(e)}")
            return []
            
    def store_active_search(self, message_id: int, query: str, index: int, images: List[Dict]):
        """Store an active image search for navigation."""
        self.active_image_searches[message_id] = (query, index, images)
        
    def get_active_search(self, message_id: int) -> Tuple[str, int, List[Dict]]:
        """Get an active image search."""
        return self.active_image_searches.get(message_id)
        
    def update_search_index(self, message_id: int, new_index: int):
        """Update the index of an active search."""
        if message_id in self.active_image_searches:
            query, _, images = self.active_image_searches[message_id]
            self.active_image_searches[message_id] = (query, new_index, images)
            
    def remove_active_search(self, message_id: int):
        """Remove an active search."""
        if message_id in self.active_image_searches:
            del self.active_image_searches[message_id]
            
    def reset_user_cooldowns(self):
        """Reset all user cooldowns."""
        self.user_cooldowns.clear()
        
    def reset_daily_count(self):
        """Reset the daily search count."""
        self.daily_search_count = 0
        self.last_count_reset = datetime.now()
        
    def get_stats(self) -> Dict[str, Any]:
        """Get image search statistics."""
        self.check_reset_daily_count()
        
        # Calculate time until next reset
        next_reset = datetime.combine(self.last_count_reset.date() + timedelta(days=1), datetime.min.time())
        time_until_reset = next_reset - datetime.now()
        hours, remainder = divmod(time_until_reset.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        # Count active cooldowns
        now = time.time()
        active_cooldowns = sum(1 for last_use in self.user_cooldowns.values() 
                             if now - last_use < self.cooldown_time)
        
        return {
            "daily_count": self.daily_search_count,
            "daily_limit": self.daily_limit,
            "reset_hours": hours,
            "reset_minutes": minutes,
            "cache_size": len(self.image_search_cache),
            "max_cache": self.max_cache_size,
            "active_cooldowns": active_cooldowns,
            "api_configured": bool(self.google_api_key and self.google_cse_id)
        }