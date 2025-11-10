"""
Deposit command for the economy system.
Allows users to transfer money from wallet to bank.
"""

import discord
from discord.ext import commands
import datetime
from ..helpers.data_manager import EconomyDataManager
from ..helpers.utils import format_amount_input, create_error_embed, create_success_embed

class DepositCommand(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.data_manager = EconomyDataManager()

    @commands.command()
    async def deposit(self, ctx, amount=None):
        """Deposit money from wallet to bank."""
        await self.data_manager.open_account(ctx.author)
        
        # Get current balance
        balance_data = await self.data_manager.get_user_balance(ctx.author.id)
        wallet_amt = balance_data["wallet"]
        
        # Parse amount input
        success, parsed_amount, error_msg = format_amount_input(amount, wallet_amt)
        if not success:
            embed = create_error_embed("Error", error_msg)
            await ctx.send(embed=embed)
            return
            
        amount = parsed_amount
        
        # Check if user has enough money in wallet
        if amount > wallet_amt:
            embed = create_error_embed(
                "Error",
                "You don't have that much money in your wallet!"
            )
            await ctx.send(embed=embed)
            return
        
        # Update balances (remove from wallet, add to bank)
        updated_balance = await self.data_manager.update_balance(
            ctx.author.id, 
            wallet_change=-amount, 
            bank_change=amount
        )
        
        # Create success embed
        embed = create_success_embed(
            "Deposit Successful",
            f"You deposited **{amount} coins** into your bank!"
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
    async def dep(self, ctx, amount=None):
        """Alias for deposit command."""
        await self.deposit(ctx, amount)