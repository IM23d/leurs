"""
Withdraw command for the economy system.
Allows users to transfer money from bank to wallet.
"""

import discord
from discord.ext import commands
import datetime
from ..helpers.data_manager import EconomyDataManager
from ..helpers.utils import format_amount_input, create_error_embed, create_success_embed

class WithdrawCommand(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.data_manager = EconomyDataManager()

    @commands.command()
    async def withdraw(self, ctx, amount=None):
        """Withdraw money from bank to wallet."""
        await self.data_manager.open_account(ctx.author)
        
        # Get current balance
        balance_data = await self.data_manager.get_user_balance(ctx.author.id)
        bank_amt = balance_data["bank"]
        
        # Parse amount input
        success, parsed_amount, error_msg = format_amount_input(amount, bank_amt)
        if not success:
            embed = create_error_embed("Error", error_msg)
            await ctx.send(embed=embed)
            return
            
        amount = parsed_amount
        
        # Check if user has enough money in bank
        if amount > bank_amt:
            embed = create_error_embed(
                "Error",
                "You don't have that much money in your bank!"
            )
            await ctx.send(embed=embed)
            return
        
        # Update balances (remove from bank, add to wallet)
        updated_balance = await self.data_manager.update_balance(
            ctx.author.id, 
            wallet_change=amount, 
            bank_change=-amount
        )
        
        # Create success embed
        embed = create_success_embed(
            "Withdrawal Successful",
            f"You withdrew **{amount} coins** from your bank!"
        )
        
        embed.add_field(
            name="Wallet Balance", 
            value=f"{updated_balance['wallet']} coins",
            inline=True
        )
        
        embed.add_field(
            name="Bank Balance", 
            value=f"{updated_balance['bank']} coins",
            inline=True
        )
        
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.timestamp = datetime.datetime.utcnow()
        
        await ctx.send(embed=embed)

    @commands.command()
    async def wit(self, ctx, amount=None):
        """Alias for withdraw command."""
        await self.withdraw(ctx, amount)