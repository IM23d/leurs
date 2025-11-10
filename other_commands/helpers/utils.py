"""
Utility functions for other cog functionality.
"""

import os
import requests
import io
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Optional
import discord

class OtherUtils:
    def __init__(self):
        self.language_codes = {
            "af": "Afrikaans", "sq": "Albanian", "am": "Amharic", "ar": "Arabic", "hy": "Armenian",
            "az": "Azerbaijani", "eu": "Basque", "be": "Belarusian", "bn": "Bengali", "bs": "Bosnian",
            "bg": "Bulgarian", "ca": "Catalan", "ceb": "Cebuano", "ny": "Chichewa", "zh": "Chinese",
            "co": "Corsican", "hr": "Croatian", "cs": "Czech", "da": "Danish", "nl": "Dutch",
            "en": "English", "eo": "Esperanto", "et": "Estonian", "tl": "Filipino", "fi": "Finnish",
            "fr": "French", "fy": "Frisian", "gl": "Galician", "ka": "Georgian", "de": "German",
            "el": "Greek", "gu": "Gujarati", "ht": "Haitian Creole", "ha": "Hausa", "haw": "Hawaiian",
            "iw": "Hebrew", "he": "Hebrew", "hi": "Hindi", "hmn": "Hmong", "hu": "Hungarian",
            "is": "Icelandic", "ig": "Igbo", "id": "Indonesian", "ga": "Irish", "it": "Italian",
            "ja": "Japanese", "jw": "Javanese", "kn": "Kannada", "kk": "Kazakh", "km": "Khmer",
            "ko": "Korean", "ku": "Kurdish", "ky": "Kyrgyz", "lo": "Lao", "la": "Latin",
            "lv": "Latvian", "lt": "Lithuanian", "lb": "Luxembourgish", "mk": "Macedonian",
            "mg": "Malagasy", "ms": "Malay", "ml": "Malayalam", "mt": "Maltese", "mi": "Maori",
            "mr": "Marathi", "mn": "Mongolian", "my": "Myanmar", "ne": "Nepali", "no": "Norwegian",
            "or": "Odia", "ps": "Pashto", "fa": "Persian", "pl": "Polish", "pt": "Portuguese",
            "pa": "Punjabi", "ro": "Romanian", "ru": "Russian", "sm": "Samoan", "gd": "Scots Gaelic",
            "sr": "Serbian", "st": "Sesotho", "sn": "Shona", "sd": "Sindhi", "si": "Sinhala",
            "sk": "Slovak", "sl": "Slovenian", "so": "Somali", "es": "Spanish", "su": "Sundanese",
            "sw": "Swahili", "sv": "Swedish", "tg": "Tajik", "ta": "Tamil", "te": "Telugu",
            "th": "Thai", "tr": "Turkish", "uk": "Ukrainian", "ur": "Urdu", "ug": "Uyghur",
            "uz": "Uzbek", "vi": "Vietnamese", "cy": "Welsh", "xh": "Xhosa", "yi": "Yiddish",
            "yo": "Yoruba", "zu": "Zulu"
        }
        
        # Translation cache
        self.translation_cache: Dict[str, str] = {}
        
        # Font handling
        os.makedirs('data/fonts', exist_ok=True)
        self.font_path = self.get_font_path()
        
    def get_font_path(self) -> Optional[str]:
        """Get a suitable font path for image generation."""
        font_path = 'data/fonts/arial.ttf'
        
        if not os.path.exists(font_path):
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
            
            return None
        
        return font_path
        
    async def create_quote_image(self, avatar_url: str, message_content: str, username: str) -> Optional[io.BytesIO]:
        """Create a quote image with user's avatar and message."""
        try:
            # Download the user's avatar
            response = requests.get(avatar_url)
            avatar_image = Image.open(io.BytesIO(response.content))
            
            size = 1000
            width, height = avatar_image.size
            
            # Resize and crop to square
            if width > height:
                new_width = int(width * size / height)
                new_height = size
                left_crop = (new_width - size) // 2
                top_crop = 0
            else:
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
            overlay = Image.new('RGBA', (size, size), (0, 0, 0, 230))
            quote_img = Image.alpha_composite(quote_img.convert('RGBA'), overlay)
            quote_img = quote_img.convert('RGB')
            
            # Create text overlay
            text_img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(text_img)
            
            # Try to find a working font
            system_fonts = [
                '/usr/share/fonts/TTF/DejaVuSans-Bold.ttf',
                '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
                '/Library/Fonts/Arial Bold.ttf',
                'C:\\Windows\\Fonts\\arialbd.ttf',
                '/usr/share/fonts/TTF/Arial.ttf',
                '/usr/share/fonts/truetype/msttcorefonts/Arial.ttf',
                self.font_path
            ]
            
            font_path = None
            for font in system_fonts:
                if font and os.path.exists(font):
                    font_path = font
                    break
            
            if not font_path:
                # Use default font
                draw.text((50, 50), f'"{message_content}"', fill=(255, 255, 255), font=ImageFont.load_default())
                draw.text((50, 100), f"- {username}", fill=(255, 255, 255), font=ImageFont.load_default())
            else:
                # Custom text wrapping
                def wrap_text(text, words_per_line=4):
                    words = text.split()
                    lines = []
                    current_line = []
                    
                    for word in words:
                        current_line.append(word)
                        if len(current_line) >= words_per_line:
                            lines.append(' '.join(current_line))
                            current_line = []
                    
                    if current_line:
                        lines.append(' '.join(current_line))
                    
                    return '\n'.join(lines)
                
                wrapped_text = wrap_text(message_content, 4)
                quote_text = f'"{wrapped_text}"'
                
                # Calculate font size
                target_text_width = int(size * 0.8)
                font_size = 20
                
                for test_size in range(20, 500, 10):
                    try:
                        test_font = ImageFont.truetype(font_path, test_size)
                        longest_line = max(wrapped_text.split('\n'), key=len)
                        bbox = draw.textbbox((0, 0), f'"{longest_line}"', font=test_font)
                        if bbox[2] - bbox[0] > target_text_width:
                            break
                        font_size = test_size
                    except Exception:
                        break
                
                try:
                    quote_font = ImageFont.truetype(font_path, font_size)
                    username_font = ImageFont.truetype(font_path, font_size // 2)
                    
                    # Get text dimensions and center
                    quote_bbox = draw.textbbox((0, 0), quote_text, font=quote_font)
                    quote_width = quote_bbox[2] - quote_bbox[0]
                    quote_height = quote_bbox[3] - quote_bbox[1]
                    
                    quote_x = (size - quote_width) // 2
                    quote_y = (size - quote_height) // 2 - size // 8
                    
                    # Draw shadow
                    shadow_offset = max(3, font_size // 20)
                    for dx, dy in [(shadow_offset, shadow_offset), (-shadow_offset, shadow_offset),
                                  (shadow_offset, -shadow_offset), (-shadow_offset, -shadow_offset)]:
                        draw.text((quote_x + dx, quote_y + dy), quote_text, fill=(0, 0, 0), font=quote_font)
                    
                    # Draw main text
                    draw.text((quote_x, quote_y), quote_text, fill=(255, 255, 255), font=quote_font)
                    
                    # Add username
                    username_text = f"- {username}"
                    username_bbox = draw.textbbox((0, 0), username_text, font=username_font)
                    username_width = username_bbox[2] - username_bbox[0]
                    
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
            
            # Scale up final image
            final_size = 2000
            quote_img = quote_img.resize((final_size, final_size), Image.Resampling.LANCZOS)
            
            # Save to buffer
            buffer = io.BytesIO()
            quote_img.convert('RGB').save(buffer, format='PNG')
            buffer.seek(0)
            
            return buffer
        except Exception as e:
            print(f"Error creating quote image: {e}")
            return None
            
    def create_typing_result_embed(self, result: Dict, user: discord.User) -> discord.Embed:
        """Create an embed for typing test results."""
        embed = discord.Embed(
            title="⌨️ Typing Test Results",
            color=0x00FF00 if result["accuracy"] > 90 else (0xFFFF00 if result["accuracy"] > 75 else 0xFF0000)
        )
        
        embed.add_field(name="Speed", value=f"**{result['wpm']:.1f}** WPM", inline=True)
        embed.add_field(name="Accuracy", value=f"**{result['accuracy']:.1f}%**", inline=True)
        embed.add_field(name="Time", value=f"**{result['time']:.1f}** seconds", inline=True)
        
        embed.add_field(
            name="Characters",
            value=f"Correct: **{result['correct_chars']}** / Total: **{result['total_chars']}**",
            inline=False
        )
        
        # Add rating based on WPM
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
        
        embed.add_field(name="Rating", value=rating, inline=False)
        embed.set_footer(text=f"Typing test completed by {user.display_name}")
        
        return embed
        
    def create_image_embed(self, image_info: Dict, query: str, index: int, total: int) -> discord.Embed:
        """Create an embed for image search results."""
        embed = discord.Embed(
            title=f"Image Search: {query}",
            description=image_info["title"],
            color=0x3498db
        )
        
        embed.set_image(url=image_info["url"])
        embed.add_field(
            name="Source",
            value=f"[{image_info['source']}]({image_info['context']})",
            inline=True
        )
        embed.set_footer(text=f"Image {index + 1} of {total} | Use ⬅️ ➡️ to navigate")
        
        return embed