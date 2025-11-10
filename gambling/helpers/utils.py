"""
Utility functions for the gambling system.
Contains game logic, bet parsing, and result formatting.
"""

import discord
import random
import datetime

def parse_bet_amount(amount_str, current_balance):
    """
    Parse bet amount input string and return the numeric amount.
    Handles 'all', percentages, and regular numbers.
    
    Args:
        amount_str (str): The input string (e.g., "100", "50%", "all")
        current_balance (int): The current wallet balance
        
    Returns:
        tuple: (success, amount, error_message)
    """
    if amount_str is None:
        return False, 0, "Please specify an amount to gamble"
    
    # Handle "all" keyword
    if amount_str.lower() == "all":
        return True, current_balance, None
    
    # Handle percentage
    if isinstance(amount_str, str) and "%" in amount_str:
        try:
            percentage = int(amount_str.replace("%", ""))
            if percentage <= 0 or percentage > 100:
                return False, 0, "Please enter a valid percentage between 1% and 100%"
            amount = int(current_balance * (percentage / 100))
            return True, amount, None
        except ValueError:
            return False, 0, "Please enter a valid percentage between 1% and 100%"
    
    # Handle regular number
    try:
        amount = int(amount_str)
        if amount <= 0:
            return False, 0, "Amount must be positive!"
        return True, amount, None
    except ValueError:
        return False, 0, "Please enter a valid number, percentage, or 'all'"

def play_coin_flip():
    """
    Simulate a coin flip game.
    
    Returns:
        tuple: (result, is_win) where result is "heads" or "tails" and is_win is boolean
    """
    result = "heads" if random.randint(1, 2) == 1 else "tails"
    is_win = result == "heads"  # Win on heads, lose on tails
    return result, is_win

def create_gambling_embed(user, bet_amount, result, is_win, new_balance):
    """
    Create an embed for gambling results.
    
    Args:
        user: Discord user object
        bet_amount (int): Amount that was bet
        result (str): The game result (e.g., "heads", "tails")
        is_win (bool): Whether the user won or lost
        new_balance (int): User's new wallet balance
        
    Returns:
        discord.Embed: Formatted embed with results
    """
    if is_win:
        color = discord.Color.green()
        title = "🎉 You Won!"
        description = f"The coin landed on **{result}**! You won **{bet_amount} coins**!"
        emoji = "🪙"
    else:
        color = discord.Color.red()
        title = "💸 You Lost!"
        description = f"The coin landed on **{result}**! You lost **{bet_amount} coins**!"
        emoji = "😞"
    
    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )
    
    embed.add_field(
        name=f"{emoji} New Balance", 
        value=f"{new_balance} coins",
        inline=False
    )
    
    embed.set_footer(
        text=f"Requested by {user.name}", 
        icon_url=user.avatar.url if user.avatar else user.default_avatar.url
    )
    embed.timestamp = datetime.datetime.utcnow()
    
    return embed

def create_error_embed(title, description):
    """Create a standardized error embed."""
    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.red()
    )
    return embed

def validate_bet(amount, wallet_balance):
    """
    Validate if a bet amount is valid.
    
    Args:
        amount (int): The bet amount
        wallet_balance (int): User's current wallet balance
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if amount <= 0:
        return False, "Amount must be positive!"
    
    if amount > wallet_balance:
        return False, "You don't have enough coins!"
    
    return True, None

def format_game_stats(games_played, total_won, total_lost):
    """
    Format gambling statistics (for future feature).
    
    Args:
        games_played (int): Total number of games
        total_won (int): Total amount won
        total_lost (int): Total amount lost
        
    Returns:
        str: Formatted statistics string
    """
    net_result = total_won - total_lost
    win_rate = (total_won / (total_won + total_lost) * 100) if (total_won + total_lost) > 0 else 0
    
    return f"""
    **Games Played:** {games_played}
    **Total Won:** {total_won} coins
    **Total Lost:** {total_lost} coins
    **Net Result:** {net_result:+} coins
    **Win Rate:** {win_rate:.1f}%
    """