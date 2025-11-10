"""
Coin flip gambling game implementation.
A simple heads or tails betting game.
"""

import random

class CoinFlipGame:
    """
    Coin flip gambling game.
    Players bet on heads or tails - currently defaults to heads wins.
    """
    
    def __init__(self):
        self.name = "Coin Flip"
        self.description = "Bet on a coin flip! Heads wins, tails loses."
        self.win_probability = 0.5  # 50/50 chance
    
    def play(self, bet_amount):
        """
        Play a single coin flip game.
        
        Args:
            bet_amount (int): Amount being bet
            
        Returns:
            dict: Game result containing:
                - result: "heads" or "tails"
                - is_win: boolean
                - payout: amount won (0 if lost)
                - description: text description of result
        """
        # Flip the coin
        result = "heads" if random.randint(1, 2) == 1 else "tails"
        is_win = result == "heads"  # Win condition: heads
        
        # Calculate payout (1:1 odds)
        payout = bet_amount if is_win else 0
        
        # Create description
        if is_win:
            description = f"The coin landed on **{result}**! You won **{bet_amount} coins**!"
        else:
            description = f"The coin landed on **{result}**! You lost **{bet_amount} coins**!"
        
        return {
            "result": result,
            "is_win": is_win,
            "payout": payout,
            "description": description,
            "game_type": "coin_flip"
        }
    
    def get_odds_description(self):
        """Get a description of the game odds."""
        return "50% chance to win (heads wins, tails loses) with 1:1 payout"