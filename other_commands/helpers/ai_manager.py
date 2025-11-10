"""
AI manager for handling AI chat functionality using DeepSeek API.
"""

import os
import time
import json
import base64
import requests
import traceback
from datetime import datetime
from typing import Dict, Any, Tuple, List

class AIManager:
    def __init__(self):
        # API configuration
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", "")
        
        # Rate limiting
        self.ai_user_cooldowns: Dict[int, float] = {}
        self.ai_cooldown_time = 30  # 30 seconds
        self.ai_daily_usage: Dict[int, int] = {}
        self.ai_daily_limit = 30
        self.ai_last_reset = datetime.now()
        
    def set_api_key(self, api_key: str):
        """Set the DeepSeek API key."""
        self.deepseek_api_key = api_key
        
    def check_ai_reset_daily_count(self):
        """Reset daily usage count if it's a new day."""
        now = datetime.now()
        if now.date() > self.ai_last_reset.date():
            self.ai_daily_usage = {}
            self.ai_last_reset = now
            return True
        return False
        
    def check_ai_user_limit(self, user_id: int) -> bool:
        """Check if user has exceeded daily limit."""
        self.check_ai_reset_daily_count()
        
        if user_id not in self.ai_daily_usage:
            self.ai_daily_usage[user_id] = 0
            
        self.ai_daily_usage[user_id] += 1
        return self.ai_daily_usage[user_id] > self.ai_daily_limit
        
    def check_ai_cooldown(self, user_id: int) -> Tuple[bool, int]:
        """Check if user is on cooldown."""
        now = time.time()
        
        if user_id in self.ai_user_cooldowns:
            last_use = self.ai_user_cooldowns[user_id]
            elapsed = now - last_use
            
            if elapsed < self.ai_cooldown_time:
                return True, int(self.ai_cooldown_time - elapsed)
        
        self.ai_user_cooldowns[user_id] = now
        return False, 0
        
    async def generate_response(self, prompt: str, image_bytes: bytes = None, image_filename: str = None) -> Tuple[str, str]:
        """Generate AI response using DeepSeek API."""
        if not self.deepseek_api_key:
            return None, "DeepSeek API key not configured"
            
        try:
            headers = {
                "Authorization": f"Bearer {self.deepseek_api_key}",
                "Content-Type": "application/json"
            }
            
            # Prepare messages
            messages = [
                {"role": "system", "content": "You are a helpful assistant. Provide short, concise answers limited to about 750 tokens. Be direct and get straight to the point while still being helpful."}
            ]
            
            model = "deepseek-chat"
            
            if image_bytes and image_filename:
                # Handle image input
                file_ext = image_filename.split('.')[-1].lower()
                mime_type = {
                    'png': 'image/png',
                    'jpg': 'image/jpeg',
                    'jpeg': 'image/jpeg',
                    'gif': 'image/gif',
                    'webp': 'image/webp'
                }.get(file_ext, 'image/jpeg')
                
                # Convert to base64
                image_b64 = base64.b64encode(image_bytes).decode('utf-8')
                image_content = f"data:{mime_type};base64,{image_b64}"
                
                # For DeepSeek, we need to use a different approach for images
                # Create temporary file and use multipart upload
                temp_image_path = f"temp_image_{int(time.time())}.{file_ext}"
                
                try:
                    with open(temp_image_path, "wb") as f:
                        f.write(image_bytes)
                    
                    messages.append({
                        "role": "user", 
                        "content": prompt + "\n[IMAGE]"
                    })
                    
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
                    
                    response = requests.post(
                        "https://api.deepseek.com/v1/chat/completions",
                        headers=headers,
                        data=data,
                        files=files,
                        timeout=60
                    )
                    
                    # Clean up temp file
                    try:
                        os.remove(temp_image_path)
                    except:
                        pass
                        
                except Exception as e:
                    # Clean up temp file on error
                    try:
                        os.remove(temp_image_path)
                    except:
                        pass
                    raise e
                    
            else:
                # Text-only request
                messages.append({"role": "user", "content": prompt})
                
                data = {
                    "model": model,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 750
                }
                
                response = requests.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=60
                )
            
            # Check response
            if response.status_code != 200:
                error_message = f"API Error: {response.status_code}"
                try:
                    error_data = response.json()
                    print(f"API Error Response: {json.dumps(error_data, indent=2)}")
                    if "error" in error_data:
                        error_message = f"API Error: {error_data['error']['message']}"
                except Exception:
                    try:
                        error_text = response.text
                        print(f"Raw API Error Response: {error_text[:500]}")
                        error_message = f"API Error {response.status_code}: {error_text[:100]}..."
                    except:
                        pass
                
                # For 422 errors, provide helpful information
                if response.status_code == 422:
                    error_message += "\n\nPossible causes:\n- Image format not supported (try JPG or PNG)\n- Image too large (try a smaller image)\n- Invalid model name"
                
                return None, error_message
            
            # Parse response
            result = response.json()
            ai_response = result["choices"][0]["message"]["content"]
            
            return ai_response, None
            
        except Exception as e:
            print(f"AI generation error: {traceback.format_exc()}")
            return None, f"Error: {str(e)}"
            
    def reset_user_cooldowns(self):
        """Reset all user cooldowns."""
        self.ai_user_cooldowns.clear()
        
    def reset_daily_usage(self):
        """Reset daily usage counts."""
        self.ai_daily_usage = {}
        self.ai_last_reset = datetime.now()
        
    def get_stats(self, client) -> Dict[str, Any]:
        """Get AI usage statistics."""
        self.check_ai_reset_daily_count()
        
        total_usage = sum(self.ai_daily_usage.values())
        
        # Calculate time until next reset
        next_reset = datetime.combine(self.ai_last_reset.date() + timedelta(days=1), datetime.min.time())
        time_until_reset = next_reset - datetime.now()
        hours, remainder = divmod(time_until_reset.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        # Count active cooldowns
        now = time.time()
        active_cooldowns = sum(1 for last_use in self.ai_user_cooldowns.values() 
                             if now - last_use < self.ai_cooldown_time)
        
        # Get top users
        top_users = []
        if self.ai_daily_usage:
            sorted_users = sorted(self.ai_daily_usage.items(), key=lambda x: x[1], reverse=True)[:5]
            
            for user_id, count in sorted_users:
                try:
                    # This would need to be handled by the calling function since we don't have client access
                    top_users.append({
                        "user_id": user_id,
                        "count": count,
                        "limit": self.ai_daily_limit
                    })
                except:
                    pass
        
        return {
            "total_usage": total_usage,
            "user_count": len(self.ai_daily_usage),
            "reset_hours": hours,
            "reset_minutes": minutes,
            "active_cooldowns": active_cooldowns,
            "api_configured": bool(self.deepseek_api_key),
            "top_users": top_users
        }
        
from datetime import timedelta