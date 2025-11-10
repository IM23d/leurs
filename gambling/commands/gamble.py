"""
Gamble command for the gambling system.
Allows users to bet coins on a coin flip game.
"""

import discord
from discord.ext import commands
import sys
import os

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from economy.helpers.data_manager import EconomyDataManager
from ..helpers.utils import parse_bet_amount, create_gambling_embed, create_error_embed, validate_bet
from ..games.coin_flip import CoinFlipGame

class GambleCommand(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.economy_manager = EconomyDataManager()
        self.coin_flip_game = CoinFlipGame()

    @commands.command()
    async def gamble(self, ctx, amount=None):
        """Gamble coins on a coin flip! Heads wins, tails loses."""
        # Ensure user has an account
        await self.economy_manager.open_account(ctx.author)
        
        # Get current balance
        balance_data = await self.economy_manager.get_user_balance(ctx.author.id)
        wallet_balance = balance_data["wallet"]
        
        # Parse bet amount
        success, bet_amount, error_msg = parse_bet_amount(amount, wallet_balance)
        if not success:
            embed = create_error_embed("Error", error_msg)
            await ctx.send(embed=embed)
            return
        
        # Validate bet
        is_valid, validation_error = validate_bet(bet_amount, wallet_balance)
        if not is_valid:
            embed = create_error_embed("Error", validation_error)
            await ctx.send(embed=embed)
            return
        
        # Place the bet (remove money from wallet)
        await self.economy_manager.update_balance(ctx.author.id, wallet_change=-bet_amount)
        
        # Play the game
        game_result = self.coin_flip_game.play(bet_amount)
        
        # Handle winnings
        if game_result["is_win"]:
            # Add winnings to wallet (bet amount + payout)
            await self.economy_manager.update_balance(ctx.author.id, wallet_change=game_result["payout"])
        
        # Get new balance
        new_balance_data = await self.economy_manager.get_user_balance(ctx.author.id)
        new_balance = new_balance_data["wallet"]
        
        # Create and send result embed
        embed = create_gambling_embed(
            user=ctx.author,
            bet_amount=bet_amount,
            result=game_result["result"],
            is_win=game_result["is_win"],
            new_balance=new_balance
        )
        
        await ctx.send(embed=embed)