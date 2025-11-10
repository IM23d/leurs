"""
Avatar commands for displaying user avatars and banners.
"""

import discord
from discord.ext import commands

class AvatarCommands(commands.Cog):
    def __init__(self, client):
        self.client = client
        
    @commands.command(aliases=['av'])
    async def avatar(self, ctx, member: discord.Member = None):
        """Display a user's global avatar."""
        member = member or ctx.author
        
        embed = discord.Embed(
            title=f"{member.display_name}'s Avatar",
            color=0x00FFFF
        )
        
        avatar_url = member.avatar.with_size(4096).url if member.avatar else member.default_avatar.url
        embed.set_image(url=avatar_url)
        
        await ctx.send(embed=embed)
        
    @commands.command(aliases=['sav'])
    async def serveravatar(self, ctx, member: discord.Member = None):
        """Display a user's server-specific avatar."""
        member = member or ctx.author
        
        if not member.guild_avatar:
            await ctx.send(f"{member.display_name} doesn't have a server-specific avatar.")
            return
        
        embed = discord.Embed(
            title=f"{member.display_name}'s Server Avatar",
            color=0x00FFFF
        )
        
        avatar_url = member.guild_avatar.with_size(4096).url
        embed.set_image(url=avatar_url)
        
        await ctx.send(embed=embed)
        
    @commands.command()
    async def banner(self, ctx, user: discord.User = None):
        """Display a user's banner."""
        user = user or ctx.author
        
        try:
            user = await self.client.fetch_user(user.id)
            
            if not user.banner:
                await ctx.send(f"{user.display_name} doesn't have a banner.")
                return
            
            embed = discord.Embed(
                title=f"{user.display_name}'s Banner",
                color=0x00FFFF
            )
            
            banner_url = user.banner.with_size(4096).url
            embed.set_image(url=banner_url)
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"Error fetching banner: {str(e)}")
            
    @commands.command()
    async def sbanner(self, ctx, member: discord.Member = None):
        """Display a user's server banner."""
        member = member or ctx.author
        
        try:
            if not hasattr(member, 'guild_banner') or not member.guild_banner:
                await ctx.send(f"{member.display_name} doesn't have a server banner.")
                return
            
            embed = discord.Embed(
                title=f"{member.display_name}'s Server Banner",
                color=0x00FFFF
            )
            
            banner_url = member.guild_banner.with_size(4096).url
            embed.set_image(url=banner_url)
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"Error fetching server banner: {str(e)}")

async def setup(client):
    """Setup function for the Avatar commands."""
    client.add_cog(AvatarCommands(client))