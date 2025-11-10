"""
Data management utilities for the economy system.
Handles all JSON file operations for user bank data.
"""

import json
import os

class EconomyDataManager:
    def __init__(self, data_file='data/bank.json'):
        self.data_file = data_file
        
    async def get_bank_data(self):
        """Load bank data from JSON file."""
        if not os.path.exists('data'):
            os.makedirs('data')
        
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w') as f:
                json.dump({}, f)

        with open(self.data_file, 'r') as f:
            content = f.read().strip()
            if not content:
                users = {}
            else:
                try:
                    users = json.loads(content)
                except json.JSONDecodeError:
                    users = {}
            
        if not content:
            with open(self.data_file, 'w') as f:
                json.dump(users, f)
                
        return users
    
    async def save_bank_data(self, users):
        """Save bank data to JSON file."""
        with open(self.data_file, 'w') as f:
            json.dump(users, f)
    
    async def open_account(self, user, starting_wallet=50, starting_bank=0):
        """Create a new account for a user if they don't have one."""
        users = await self.get_bank_data()

        if str(user.id) in users:
            return False
        else:
            users[str(user.id)] = {}
            users[str(user.id)]["wallet"] = starting_wallet
            users[str(user.id)]["bank"] = starting_bank

        await self.save_bank_data(users)
        return True
    
    async def add_balance(self, user_id, amount):
        """Add money to a user's wallet."""
        users = await self.get_bank_data()
        
        # Convert user_id to string for consistency
        user_id = str(user_id)
        
        # Create account if user doesn't exist
        if user_id not in users:
            users[user_id] = {}
            users[user_id]["wallet"] = 0
            users[user_id]["bank"] = 0
        
        # Add amount to wallet
        users[user_id]["wallet"] += amount
        
        await self.save_bank_data(users)
        return users[user_id]["wallet"]
    
    async def remove_balance(self, user_id, amount):
        """Remove money from a user's account."""
        users = await self.get_bank_data()
        
        # Convert user_id to string for consistency
        user_id = str(user_id)
        
        # Create account if user doesn't exist
        if user_id not in users:
            users[user_id] = {}
            users[user_id]["wallet"] = 0
            users[user_id]["bank"] = 0
            return False  # Can't remove from empty account
        
        # Check if user has enough in wallet
        if users[user_id]["wallet"] >= amount:
            users[user_id]["wallet"] -= amount
        # If not enough in wallet, check combined balance
        elif (users[user_id]["wallet"] + users[user_id]["bank"]) >= amount:
            # Take what we can from wallet
            remainder = amount - users[user_id]["wallet"]
            users[user_id]["wallet"] = 0
            # Take the rest from bank
            users[user_id]["bank"] -= remainder
        else:
            # Not enough money, set to zero
            users[user_id]["wallet"] = 0
            users[user_id]["bank"] = 0
        
        await self.save_bank_data(users)
        return True
    
    async def get_user_balance(self, user_id):
        """Get a user's wallet and bank balance."""
        users = await self.get_bank_data()
        user_id = str(user_id)
        
        if user_id not in users:
            return {"wallet": 0, "bank": 0}
            
        return {
            "wallet": users[user_id].get("wallet", 0),
            "bank": users[user_id].get("bank", 0)
        }
    
    async def update_balance(self, user_id, wallet_change=0, bank_change=0):
        """Update a user's wallet and/or bank balance."""
        users = await self.get_bank_data()
        user_id = str(user_id)
        
        if user_id not in users:
            users[user_id] = {"wallet": 0, "bank": 0}
        
        users[user_id]["wallet"] += wallet_change
        users[user_id]["bank"] += bank_change
        
        # Ensure balances don't go negative
        users[user_id]["wallet"] = max(0, users[user_id]["wallet"])
        users[user_id]["bank"] = max(0, users[user_id]["bank"])
        
        await self.save_bank_data(users)
        return users[user_id]