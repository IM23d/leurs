from datetime import datetime, date
import discord

def get_next_birthday_timestamp(birthday_str):
    """Get timestamp for next birthday occurrence"""
    # Convert stored date string to date object
    birthday = datetime.strptime(birthday_str, "%d-%m-%Y").date()
    today = date.today()
    
    # Create this year's birthday
    this_year_bday = date(today.year, birthday.month, birthday.day)
    
    # If this year's birthday has passed, use next year's birthday
    if this_year_bday < today:
        this_year_bday = date(today.year + 1, birthday.month, birthday.day)
    
    # Convert to datetime at midnight
    next_birthday = datetime.combine(this_year_bday, datetime.min.time())
    return int(next_birthday.timestamp())

def calculate_next_age(birthday_str):
    """Calculate the age the person will turn on their next birthday"""
    # Convert stored date string to date object
    birthday = datetime.strptime(birthday_str, "%d-%m-%Y").date()
    today = date.today()
    
    # Calculate next birthday
    this_year_bday = date(today.year, birthday.month, birthday.day)
    
    # If this year's birthday hasn't happened yet, use this year
    # If this year's birthday has passed, use next year
    next_birthday_year = today.year if this_year_bday >= today else today.year + 1
    
    # Calculate the age they will turn on their next birthday
    return next_birthday_year - birthday.year

def get_next_birthday_date(birthday_str):
    """Get the date of the next birthday occurrence"""
    # Convert stored date string to date object
    birthday = datetime.strptime(birthday_str, "%d-%m-%Y").date()
    today = date.today()
    
    # Create this year's birthday
    this_year_bday = date(today.year, birthday.month, birthday.day)
    
    # If this year's birthday has passed, use next year's birthday
    if this_year_bday < today:
        return date(today.year + 1, birthday.month, birthday.day)
    return this_year_bday

def validate_birthday_date(date_str):
    """Validate and parse birthday date string"""
    try:
        # Try DD-MM-YYYY format first
        try:
            birthday_date = datetime.strptime(date_str, "%d-%m-%Y")
        except ValueError:
            # Try DD.MM.YYYY format
            birthday_date = datetime.strptime(date_str, "%d.%m.%Y")
        
        # Check if date is in the future
        if birthday_date.date() > date.today():
            raise ValueError("Birthday cannot be in the future")
        
        # Check if year is reasonable
        if birthday_date.year < 1900:
            raise ValueError("Year must be after 1900")
        
        return birthday_date, None
        
    except ValueError as e:
        return None, str(e)

def create_error_embed(description):
    """Create a standardized error embed"""
    return discord.Embed(
        description=f"❌ {description}",
        color=0x2F3136
    )

def create_success_embed(description):
    """Create a standardized success embed"""
    return discord.Embed(
        description=description,
        color=0x2F3136
    )

def create_info_embed(title, description):
    """Create a standardized info embed"""
    return discord.Embed(
        title=title,
        description=description,
        color=0x2F3136
    )