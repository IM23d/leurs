"""
Balance command for the economy system.
Shows user's wallet and bank balance.
"""

import discord
from discord.ext import commands
from ..helpers.data_manager import EconomyDataManager
from ..helpers.utils import create_balance_embed

class BalanceCommand(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.data_manager = EconomyDataManager()

    @commands.command()
    async def balance(self, ctx):
        """Display user's wallet and bank balance."""
        await self.data_manager.open_account(ctx.author)
        
        balance_data = await self.data_manager.get_user_balance(ctx.author.id)
        wallet_amt = balance_data["wallet"]
        bank_amt = balance_data["bank"]

        embed = create_balance_embed(ctx.author, wallet_amt, bank_amt)
        await ctx.send(embed=embed)

    @commands.command()
    async def bal(self, ctx):
        """Alias for balance command."""
        await self.balance(ctx)