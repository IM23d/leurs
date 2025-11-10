"""
Utility functions for the jobs system.
Contains formatting, validation, and pagination utilities.
"""

import discord
import datetime
import math
from typing import Dict, List, Tuple

def create_error_embed(title: str, description: str) -> discord.Embed:
    """Create a standardized error embed."""
    return discord.Embed(
        title=title,
        description=description,
        color=discord.Color.red()
    )

def create_success_embed(title: str, description: str) -> discord.Embed:
    """Create a standardized success embed."""
    return discord.Embed(
        title=title,
        description=description,
        color=discord.Color.green()
    )

def create_info_embed(title: str, description: str, color=discord.Color.blue()) -> discord.Embed:
    """Create a standardized info embed."""
    return discord.Embed(
        title=title,
        description=description,
        color=color
    )

def format_job_info(job_name: str, job_info: Dict, is_owned: bool = False) -> str:
    """
    Format job information for display.
    
    Args:
        job_name: Name of the job
        job_info: Dictionary containing job data
        is_owned: Whether the user owns this job
        
    Returns:
        Formatted string with job details
    """
    status = "✅ Unlocked" if is_owned else "🔒 Locked"
    
    value = f"Base Pay: {job_info['base_pay']} coins\n"
    value += f"Bonus Chance: {job_info['bonus_chance']*100}%\n"
    value += f"Bonus Amount: {job_info['bonus_amount']} coins"
    
    if not is_owned:
        value += f"\nCost to Unlock: {job_info['cost']} coins"
    
    return value

def get_job_display_name(job_name: str, is_owned: bool = False) -> str:
    """Get formatted job name with status indicator."""
    status = "✅ Unlocked" if is_owned else "🔒 Locked"
    return f"{status} {job_name}"

def paginate_jobs(jobs_dict: Dict, page: int = 1, items_per_page: int = 3) -> Tuple[List, int, int]:
    """
    Paginate jobs for display.
    
    Args:
        jobs_dict: Dictionary of all jobs
        page: Current page number (1-indexed)
        items_per_page: Number of jobs per page
        
    Returns:
        Tuple of (paginated_jobs, total_pages, valid_page)
    """
    total_jobs = len(jobs_dict)
    total_pages = max(1, math.ceil(total_jobs / items_per_page))
    
    # Ensure page is within valid range
    page = max(1, min(page, total_pages))
    
    # Get jobs for current page
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, total_jobs)
    
    all_jobs = list(jobs_dict.items())
    paginated_jobs = all_jobs[start_idx:end_idx]
    
    return paginated_jobs, total_pages, page

def format_cooldown_time(retry_after: float) -> str:
    """Format cooldown time into hours, minutes, seconds."""
    hours, remainder = divmod(retry_after, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"

def validate_job_name(job_name: str, available_jobs: Dict) -> Tuple[bool, str, str]:
    """
    Validate and normalize job name input.
    
    Args:
        job_name: User input job name
        available_jobs: Dictionary of available jobs
        
    Returns:
        Tuple of (is_valid, normalized_name, error_message)
    """
    if not job_name:
        return False, "", "Please specify a job name"
    
    # Normalize job name (title case)
    normalized = job_name.title()
    
    if normalized not in available_jobs:
        return False, "", f"'{job_name}' is not a valid job. Use `-jobs` to see available jobs."
    
    return True, normalized, ""

def create_job_market_embed(paginated_jobs: List, user_jobs: List[str], page: int, total_pages: int) -> discord.Embed:
    """
    Create the job market embed with pagination info.
    
    Args:
        paginated_jobs: List of (job_name, job_info) tuples for current page
        user_jobs: List of jobs owned by the user
        page: Current page number
        total_pages: Total number of pages
        
    Returns:
        Discord embed for job market
    """
    embed = discord.Embed(
        title="📋 Job Market",
        description=f"Here are all available jobs (Page {page}/{total_pages}):",
        color=discord.Color.blue()
    )
    
    for job_name, job_info in paginated_jobs:
        is_owned = job_name in user_jobs
        field_name = get_job_display_name(job_name, is_owned)
        field_value = format_job_info(job_name, job_info, is_owned)
        
        embed.add_field(
            name=field_name,
            value=field_value,
            inline=False
        )
    
    embed.add_field(
        name="📝 Commands",
        value="`-buyjob <job>` - Purchase a job to unlock it\n"
              "`-work` - Work at all your jobs\n"
              "`-myjobs` - View your current jobs\n"
              "`-removejob <job>` - Remove a job from your list",
        inline=False
    )
    
    embed.set_footer(text="Work once per day to earn coins!")
    
    return embed

def create_my_jobs_embed(user: discord.User, user_jobs: List[str], jobs_data: Dict) -> discord.Embed:
    """
    Create embed showing user's current jobs.
    
    Args:
        user: Discord user object
        user_jobs: List of job names owned by user
        jobs_data: Dictionary of all job information
        
    Returns:
        Discord embed showing user's jobs
    """
    if not user_jobs:
        embed = discord.Embed(
            title="💼 Your Jobs",
            description="You don't have any jobs yet! Use `-jobs` to see available jobs and `-buyjob <job>` to purchase one.",
            color=discord.Color.blue()
        )
    else:
        embed = discord.Embed(
            title="💼 Your Jobs",
            description=f"You currently have {len(user_jobs)} job(s):",
            color=discord.Color.blue()
        )
        
        for job_name in user_jobs:
            job_info = jobs_data.get(job_name, {})
            value = format_job_info(job_name, job_info, is_owned=True)
            
            embed.add_field(
                name=f"✅ {job_name}",
                value=value,
                inline=False
            )
        
        embed.add_field(
            name="📝 Commands",
            value="`-work` - Work at all your jobs\n"
                  "`-removejob <job>` - Remove a job from your list\n"
                  "`-jobs` - View the job market",
            inline=False
        )
    
    embed.set_footer(
        text=f"Requested by {user.name}", 
        icon_url=user.avatar.url if user.avatar else user.default_avatar.url
    )
    embed.timestamp = datetime.datetime.utcnow()
    
    return embed

def create_work_results_embed(user: discord.User, total_earnings: int, earnings_breakdown: List[str], new_balance: int) -> discord.Embed:
    """
    Create embed showing work results.
    
    Args:
        user: Discord user object
        total_earnings: Total coins earned
        earnings_breakdown: List of earnings per job
        new_balance: User's new wallet balance
        
    Returns:
        Discord embed with work results
    """
    embed = discord.Embed(
        title="💼 Work Results",
        description=f"You worked at your jobs and earned a total of {total_earnings} coins!",
        color=discord.Color.green()
    )
    
    embed.add_field(
        name="Earnings Breakdown",
        value="\n".join(earnings_breakdown),
        inline=False
    )
    
    embed.add_field(
        name="New Wallet Balance",
        value=f"{new_balance} coins",
        inline=False
    )
    
    embed.set_footer(
        text=f"Requested by {user.name}", 
        icon_url=user.avatar.url if user.avatar else user.default_avatar.url
    )
    embed.timestamp = datetime.datetime.utcnow()
    
    return embed

def create_job_purchase_embed(user: discord.User, job_name: str, user_jobs: List[str], new_balance: int) -> discord.Embed:
    """
    Create embed for successful job purchase.
    
    Args:
        user: Discord user object
        job_name: Name of purchased job
        user_jobs: Updated list of user's jobs
        new_balance: User's new wallet balance
        
    Returns:
        Discord embed for purchase confirmation
    """
    embed = discord.Embed(
        title="🎉 Job Unlocked!",
        description=f"Congratulations! You've unlocked the {job_name} job!",
        color=discord.Color.green()
    )
    
    embed.add_field(
        name="New Wallet Balance",
        value=f"{new_balance} coins",
        inline=False
    )
    
    embed.add_field(
        name="Current Jobs",
        value="\n".join(user_jobs),
        inline=False
    )
    
    embed.set_footer(
        text=f"Requested by {user.name}", 
        icon_url=user.avatar.url if user.avatar else user.default_avatar.url
    )
    embed.timestamp = datetime.datetime.utcnow()
    
    return embed

def create_job_removal_embed(user: discord.User, job_name: str, user_jobs: List[str]) -> discord.Embed:
    """
    Create embed for job removal confirmation.
    
    Args:
        user: Discord user object
        job_name: Name of removed job
        user_jobs: Updated list of user's jobs
        
    Returns:
        Discord embed for removal confirmation
    """
    embed = discord.Embed(
        title="🗑️ Job Removed",
        description=f"You've removed the {job_name} job from your current jobs.",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="Current Jobs",
        value="\n".join(user_jobs) if user_jobs else "No jobs",
        inline=False
    )
    
    embed.set_footer(
        text=f"Requested by {user.name}", 
        icon_url=user.avatar.url if user.avatar else user.default_avatar.url
    )
    embed.timestamp = datetime.datetime.utcnow()
    
    return embed