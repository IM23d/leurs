"""
AFK command for setting away status.
"""

import discord
from discord.ext import commands

class AFKCommand(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.afk_manager = None
        
    def set_afk_manager(self, afk_manager):
        """Set the AFK manager instance."""
        self.afk_manager = afk_manager
        
    @commands.command()
    async def afk(self, ctx, *, reason="AFK"):
        """Set yourself as AFK with an optional reason."""
        if not self.afk_manager:
            await ctx.send("AFK system not available.")
            return
            
        self.afk_manager.set_afk(ctx.author.id, reason)
        
        embed = discord.Embed(
            description=f"{ctx.author.mention} is now AFK - {reason}",
            color=0x808080
        )
        await ctx.send(embed=embed)

async def setup(client):
    """Setup function for the AFK command."""
    client.add_cog(AFKCommand(client))