import discord
from discord.ext import commands
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from helpers.data_manager import BlockedTermsDataManager
from helpers.utils import create_error_embed, create_success_embed

class UnblockTermCommand:
    """Remove blocked term command"""
    
    def __init__(self):
        self.data_manager = BlockedTermsDataManager()
    
    @commands.command(name='unblockterm')
    @commands.has_permissions(administrator=True)
    async def unblock_term(self, ctx, *, term: str):
        """Remove a blocked term"""
        
        # Check if term exists
        blocked_terms = await self.data_manager.load_blocked_terms()
        
        if term not in blocked_terms:
            embed = create_error_embed(f"Term `{term}` is not currently blocked.")
            await ctx.send(embed=embed)
            return
        
        # Remove the term
        success = await self.data_manager.remove_blocked_term(term)
        
        if not success:
            embed = create_error_embed("Failed to remove blocked term. Please try again.")
            await ctx.send(embed=embed)
            return
        
        embed = create_success_embed("Term Unblocked", f"Successfully unblocked term: `{term}`")
        await ctx.send(embed=embed)

def setup_command(cog):
    """Setup function to add this command to the cog"""
    command_handler = UnblockTermCommand()
    cog.add_command(command_handler.unblock_term)