"""
AI command for AI chat functionality.
"""

import discord
from discord.ext import commands

class AICommand(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.ai_manager = None
        
    def set_ai_manager(self, ai_manager):
        """Set the AI manager instance."""
        self.ai_manager = ai_manager
        
    @commands.command()
    async def ai(self, ctx, *, prompt: str = None):
        """Generate text using AI."""
        if not self.ai_manager:
            await ctx.send("AI system not available.")
            return
            
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
        
        if not prompt and ctx.message.attachments:
            prompt = "Describe what you see in this image in detail."
            
        is_admin = ctx.author.guild_permissions.administrator
        
        # Check for cooldown if not an admin
        if not is_admin:
            on_cooldown, time_remaining = self.ai_manager.check_ai_cooldown(ctx.author.id)
            if on_cooldown:
                embed = discord.Embed(
                    title="Cooldown Active",
                    description=f"You need to wait {time_remaining} seconds before using this command again.",
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
            if self.ai_manager.check_ai_user_limit(ctx.author.id):
                embed = discord.Embed(
                    title="Daily Limit Reached",
                    description=f"You've reached your limit of {self.ai_manager.ai_daily_limit} AI requests for today.",
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
        
        loading_msg = await ctx.send("🧠 Thinking...")
        
        # Check for image attachments
        image_bytes = None
        image_filename = None
        
        if ctx.message.attachments:
            for attachment in ctx.message.attachments:
                if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
                    # Check file size (10MB limit)
                    if attachment.size > 10 * 1024 * 1024:
                        await loading_msg.edit(content="❌ Image is too large (max 10MB). Please upload a smaller image.")
                        return
                        
                    image_bytes = await attachment.read()
                    image_filename = attachment.filename
                    break
        
        # Generate response
        response, error = await self.ai_manager.generate_response(prompt, image_bytes, image_filename)
        
        if error:
            await loading_msg.edit(content=f"❌ {error}")
            return
            
        # Create embed for the response
        embed = discord.Embed(
            title="DeepSeek AI Response",
            description=response,
            color=0x00AAFF
        )
        
        # Add footer with prompt
        truncated_prompt = prompt[:100] + "..." if len(prompt) > 100 else prompt
        embed.set_footer(text=f"Prompt: {truncated_prompt}")
        
        # If there was an image, add it to the embed
        if image_bytes and ctx.message.attachments:
            embed.set_thumbnail(url=ctx.message.attachments[0].url)
        
        await loading_msg.edit(content=None, embed=embed)
        
    @commands.command()
    async def set_deepseek_api_key(self, ctx, api_key: str):
        """Set the DeepSeek API key (admin only)."""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("Only administrators can set the API key.")
            return
            
        if not self.ai_manager:
            await ctx.send("AI system not available.")
            return
            
        self.ai_manager.set_api_key(api_key)
        
        # Delete the message to keep the API key private
        try:
            await ctx.message.delete()
        except:
            pass
            
        await ctx.send("DeepSeek API key has been set successfully!", delete_after=5)
        
    @commands.command()
    async def ai_stats(self, ctx):
        """Show AI usage statistics (admin only)."""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("Only administrators can view AI statistics.")
            return
            
        if not self.ai_manager:
            await ctx.send("AI system not available.")
            return
            
        stats = self.ai_manager.get_stats(self.client)
        
        embed = discord.Embed(
            title="AI Usage Statistics",
            color=0x00FF00
        )
        
        embed.add_field(name="Total Usage Today", value=f"{stats['total_usage']} requests", inline=True)
        embed.add_field(name="Users Today", value=f"{stats['user_count']} users", inline=True)
        embed.add_field(name="Resets In", value=f"{stats['reset_hours']} hours, {stats['reset_minutes']} minutes", inline=True)
        embed.add_field(name="Users on Cooldown", value=f"{stats['active_cooldowns']} users", inline=True)
        
        api_status = "✅ Configured" if stats['api_configured'] else "❌ Not Configured"
        embed.add_field(name="DeepSeek API Status", value=api_status, inline=True)
        
        if stats['top_users']:
            top_users_text = ""
            for user_data in stats['top_users']:
                try:
                    user = await self.client.fetch_user(user_data['user_id'])
                    username = user.display_name
                except:
                    username = f"User {user_data['user_id']}"
                
                top_users_text += f"{username}: **{user_data['count']}/{user_data['limit']}** requests\n"
                
            embed.add_field(
                name="Top Users Today",
                value=top_users_text or "No usage today",
                inline=False
            )
        
        await ctx.send(embed=embed)
        
    @commands.command()
    async def ai_reset_cooldowns(self, ctx):
        """Reset all AI user cooldowns (admin only)."""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("Only administrators can reset cooldowns.")
            return
            
        if not self.ai_manager:
            await ctx.send("AI system not available.")
            return
            
        self.ai_manager.reset_user_cooldowns()
        await ctx.send("✅ All AI user cooldowns have been reset.")
        
    @commands.command()
    async def ai_reset_count(self, ctx):
        """Reset the daily AI usage count (admin only)."""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("Only administrators can reset the daily count.")
            return
            
        if not self.ai_manager:
            await ctx.send("AI system not available.")
            return
            
        self.ai_manager.reset_daily_usage()
        await ctx.send("✅ Daily AI usage count has been reset.")

async def setup(client):
    """Setup function for the AI command."""
    client.add_cog(AICommand(client))