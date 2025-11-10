"""
Data management utilities for the gambling system.
This module handles integration with the economy system for gambling operations.
"""

import sys
import os

# Add the parent directory to the path to import economy module
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from economy.helpers.data_manager import EconomyDataManager

class GamblingDataManager:
    """
    Data manager for gambling operations.
    Uses the economy system as the backend for all money operations.
    """
    
    def __init__(self):
        self.economy_manager = EconomyDataManager()
    
    async def get_user_balance(self, user_id):
        """Get a user's current wallet balance for gambling."""
        balance_data = await self.economy_manager.get_user_balance(user_id)
        return balance_data["wallet"]
    
    async def ensure_account_exists(self, user):
        """Ensure user has an economy account for gambling."""
        return await self.economy_manager.open_account(user)
    
    async def place_bet(self, user_id, amount):
        """
        Place a bet by removing money from user's wallet.
        Returns True if successful, False if insufficient funds.
        """
        current_balance = await self.get_user_balance(user_id)
        
        if current_balance >= amount:
            await self.economy_manager.update_balance(user_id, wallet_change=-amount)
            return True
        return False
    
    async def payout_winnings(self, user_id, amount):
        """Add winnings to user's wallet."""
        await self.economy_manager.update_balance(user_id, wallet_change=amount)
        return await self.get_user_balance(user_id)
    
    async def get_balance_after_loss(self, user_id):
        """Get user's balance after a loss (for display purposes)."""
        return await self.get_user_balance(user_id)