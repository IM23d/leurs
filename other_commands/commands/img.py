"""
Image search command using Google API or Unsplash fallback.
"""

import discord
from discord.ext import commands
import asyncio

class ImageCommand(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.image_manager = None
        self.utils = None
        
    def set_managers(self, image_manager, utils):
        """Set the manager instances."""
        self.image_manager = image_manager
        self.utils = utils
        
    @commands.command(aliases=["image", "search"])
    async def img(self, ctx, *, query: str = None):
        """Search for images."""
        if not self.image_manager or not self.utils:
            await ctx.send("Image search system not available.")
            return
            
        # Check if query was provided
        if not query:
            embed = discord.Embed(
                title="Image Search Help",
                description="Search for images using Google search.",
                color=0x3498db
            )
            embed.add_field(name="Usage", value="`-img [search term]`", inline=False)
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
                value="Regular users can use this command once every 5 minutes.\nAdministrators are not subject to this cooldown.", 
                inline=False
            )
            await ctx.send(embed=embed)
            return
            
        # Check if the user is an admin (bypass cooldown)
        is_admin = ctx.author.guild_permissions.administrator
        
        # Check for cooldown if not an admin
        if not is_admin:
            on_cooldown, time_remaining = self.image_manager.check_user_cooldown(ctx.author.id)
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
                    value="This cooldown helps prevent hitting Google API limits.\nServer administrators are not subject to this cooldown.",
                    inline=False
                )
                await ctx.send(embed=embed)
                return
        
        # Send a loading message
        loading_msg = await ctx.send(f"🔍 Searching for images of '{query}'...")
        
        try:
            # Search for images
            images = await self.image_manager.search_images(query)
            
            if not images:
                embed = discord.Embed(
                    title="No Results",
                    description=f"No images found for '{query}'",
                    color=0xFF9900
                )
                embed.add_field(
                    name="Suggestions",
                    value="• Try a different search term\n• Check for spelling errors\n• Use more general keywords\n• Try `-img random` for random images",
                    inline=False
                )
                await loading_msg.edit(content=None, embed=embed)
                return
                
            # Create an embed for the first image
            current_index = 0
            embed = self.utils.create_image_embed(images[current_index], query, current_index, len(images))
            
            # Add API source note if using fallback
            if not self.image_manager.google_api_key or not self.image_manager.google_cse_id or self.image_manager.daily_search_count >= self.image_manager.daily_limit:
                embed.add_field(
                    name="Note",
                    value="Using Unsplash for images. For better results, administrators can set up Google API",
                    inline=False
                )
            
            # Send the embed and delete the loading message
            image_msg = await ctx.send(embed=embed)
            await loading_msg.delete()
            
            # Store the active search
            self.image_manager.store_active_search(image_msg.id, query, current_index, images)
            
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
                        pass
                    
                    # Get the current search data
                    search_data = self.image_manager.get_active_search(image_msg.id)
                    if not search_data:
                        break
                        
                    query, current_index, images = search_data
                    
                    # Update the index based on the reaction
                    if str(reaction.emoji) == "⬅️":
                        current_index = (current_index - 1) % len(images)
                    elif str(reaction.emoji) == "➡️":
                        current_index = (current_index + 1) % len(images)
                        
                    # Update the stored index
                    self.image_manager.update_search_index(image_msg.id, current_index)
                    
                    # Update the embed
                    new_embed = self.utils.create_image_embed(images[current_index], query, current_index, len(images))
                    
                    # Add API source note if using fallback
                    if not self.image_manager.google_api_key or not self.image_manager.google_cse_id or self.image_manager.daily_search_count >= self.image_manager.daily_limit:
                        new_embed.add_field(
                            name="Note",
                            value="Using Unsplash for images. For better results, administrators can set up Google API",
                            inline=False
                        )
                    
                    await image_msg.edit(embed=new_embed)
                    
                except asyncio.TimeoutError:
                    # Remove the message from active searches
                    self.image_manager.remove_active_search(image_msg.id)
                    
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
    
    @commands.command()
    async def set_google_api_key(self, ctx, api_key: str):
        """Set Google API key (admin only)."""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("Only administrators can set the API key.")
            return
            
        if not self.image_manager:
            await ctx.send("Image search system not available.")
            return
            
        self.image_manager.set_google_credentials(api_key)
        
        # Delete the message to keep the API key private
        try:
            await ctx.message.delete()
        except:
            pass
            
        await ctx.send("Google API key has been set successfully!", delete_after=5)
    
    @commands.command()
    async def set_google_cse_id(self, ctx, cse_id: str):
        """Set Google Custom Search Engine ID (admin only)."""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("Only administrators can set the CSE ID.")
            return
            
        if not self.image_manager:
            await ctx.send("Image search system not available.")
            return
            
        self.image_manager.set_google_credentials(None, cse_id)
        
        # Delete the message to keep the CSE ID private
        try:
            await ctx.message.delete()
        except:
            pass
            
        await ctx.send("Google Custom Search Engine ID has been set successfully!", delete_after=5)
    
    @commands.command()
    async def imgstats(self, ctx):
        """Show image search statistics (admin only)."""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("Only administrators can view search statistics.")
            return
            
        if not self.image_manager:
            await ctx.send("Image search system not available.")
            return
            
        stats = self.image_manager.get_stats()
        
        embed = discord.Embed(title="Image Search Statistics", color=0x00FF00)
        
        embed.add_field(name="Daily Search Count", value=f"{stats['daily_count']}/{stats['daily_limit']}", inline=True)
        embed.add_field(name="Resets In", value=f"{stats['reset_hours']} hours, {stats['reset_minutes']} minutes", inline=True)
        embed.add_field(name="Cache Size", value=f"{stats['cache_size']}/{stats['max_cache']} queries", inline=True)
        embed.add_field(name="Users on Cooldown", value=f"{stats['active_cooldowns']} users", inline=True)
        
        api_status = "✅ Configured" if stats['api_configured'] else "❌ Not Configured"
        embed.add_field(name="Google API Status", value=api_status, inline=True)
        
        embed.add_field(
            name="Admin Commands",
            value="`-img_reset_cooldowns` - Reset all user cooldowns\n`-img_reset_count` - Reset the daily search count",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command()
    async def img_reset_cooldowns(self, ctx):
        """Reset all user cooldowns (admin only)."""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("Only administrators can reset cooldowns.")
            return
            
        if not self.image_manager:
            await ctx.send("Image search system not available.")
            return
            
        self.image_manager.reset_user_cooldowns()
        await ctx.send("✅ All user cooldowns have been reset.")
    
    @commands.command()
    async def img_reset_count(self, ctx):
        """Reset the daily search count (admin only)."""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("Only administrators can reset the daily count.")
            return
            
        if not self.image_manager:
            await ctx.send("Image search system not available.")
            return
            
        self.image_manager.reset_daily_count()
        await ctx.send("✅ Daily search count has been reset.")

async def setup(client):
    """Setup function for the Image command."""
    client.add_cog(ImageCommand(client))