"""
Data management utilities for the jobs system.
Handles job definitions, user job ownership, and economy integration.
"""

import json
import os
import sys
from typing import Dict, List

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from economy.helpers.data_manager import EconomyDataManager

class JobDataManager:
    """
    Data manager for the jobs system.
    Manages job definitions, user job ownership, and integrates with economy system.
    """
    
    def __init__(self):
        self.jobs_file = 'data/jobs.json'
        self.economy_manager = EconomyDataManager()
        
        # Job definitions with pay rates, bonuses, and costs
        self.jobs: Dict[str, Dict] = {
            "McDonalds-Employee": {"base_pay": 75, "bonus_chance": 0.2, "bonus_amount": 50, "cost": 0},
            "Artist": {"base_pay": 300, "bonus_chance": 0.25, "bonus_amount": 250, "cost": 1000},
            "Teacher": {"base_pay": 350, "bonus_chance": 0.1, "bonus_amount": 100, "cost": 2000},
            "Software-Developer": {"base_pay": 500, "bonus_chance": 0.2, "bonus_amount": 200, "cost": 5000},
            "Police-Officer": {"base_pay": 450, "bonus_chance": 0.15, "bonus_amount": 150, "cost": 7500},
            "Engineer": {"base_pay": 550, "bonus_chance": 0.2, "bonus_amount": 250, "cost": 10000},
            "Doctor": {"base_pay": 600, "bonus_chance": 0.1, "bonus_amount": 300, "cost": 15000},
            "Politician": {"base_pay": 750, "bonus_chance": 0.3, "bonus_amount": 350, "cost": 25000},
            "Stripper": {"base_pay": 150, "bonus_chance": 0.5, "bonus_amount": 150, "cost": 1000},
            "Pilot": {"base_pay": 800, "bonus_chance": 0.15, "bonus_amount": 400, "cost": 30000},
            "Scientist": {"base_pay": 700, "bonus_chance": 0.25, "bonus_amount": 300, "cost": 20000},
            "Lawyer": {"base_pay": 650, "bonus_chance": 0.3, "bonus_amount": 250, "cost": 18000},
            "Real-Estate-Agent": {"base_pay": 400, "bonus_chance": 0.4, "bonus_amount": 300, "cost": 10000},
            "Stock-Trader": {"base_pay": 600, "bonus_chance": 0.5, "bonus_amount": 400, "cost": 20000},
            "Youtuber": {"base_pay": 300, "bonus_chance": 0.6, "bonus_amount": 500, "cost": 5000},
            "Streamer": {"base_pay": 250, "bonus_chance": 0.55, "bonus_amount": 400, "cost": 4000},
            "Esportler": {"base_pay": 400, "bonus_chance": 0.45, "bonus_amount": 300, "cost": 8000},
            "Astronaut": {"base_pay": 1000, "bonus_chance": 0.2, "bonus_amount": 500, "cost": 50000},
            "Flight-Attendant": {"base_pay": 250, "bonus_chance": 0.2, "bonus_amount": 100, "cost": 3000},
            "Delivery-Driver": {"base_pay": 150, "bonus_chance": 0.25, "bonus_amount": 50, "cost": 0},
            "Plumber": {"base_pay": 300, "bonus_chance": 0.2, "bonus_amount": 100, "cost": 4000},
            "Farmer": {"base_pay": 220, "bonus_chance": 0.2, "bonus_amount": 80, "cost": 2000},
            "Life-Coach": {"base_pay": 350, "bonus_chance": 0.3, "bonus_amount": 150, "cost": 6000},
        }
        
        self.current_jobs: List[str] = []
        self.user_jobs: Dict[str, List[str]] = {}  # Store unlocked jobs per user
        self.load_job_data()
    
    def load_job_data(self):
        """Load job data from JSON file."""
        if not os.path.exists('data'):
            os.makedirs('data')
        
        if os.path.exists(self.jobs_file):
            with open(self.jobs_file, 'r') as f:
                data = json.load(f)
                self.current_jobs = data.get('current_jobs', [])
                self.user_jobs = data.get('user_jobs', {})
        else:
            self.rotate_jobs()
    
    def save_job_data(self):
        """Save job data to JSON file."""
        data = {
            'current_jobs': self.current_jobs,
            'user_jobs': self.user_jobs
        }
        with open(self.jobs_file, 'w') as f:
            json.dump(data, f)
    
    def rotate_jobs(self):
        """Make all jobs available in the market."""
        self.current_jobs = list(self.jobs.keys())
        self.save_job_data()
        print(f"Available jobs: {self.current_jobs}")
    
    def get_all_jobs(self) -> Dict[str, Dict]:
        """Get all job definitions."""
        return self.jobs
    
    def get_job_info(self, job_name: str) -> Dict:
        """Get information about a specific job."""
        return self.jobs.get(job_name, {})
    
    def job_exists(self, job_name: str) -> bool:
        """Check if a job exists in the system."""
        return job_name in self.jobs
    
    async def ensure_user_account(self, user):
        """Ensure user has both economy account and job tracking."""
        await self.economy_manager.open_account(user)
        
        user_id = str(user.id)
        if user_id not in self.user_jobs:
            self.user_jobs[user_id] = []
            self.save_job_data()
        
        return True
    
    def get_user_jobs(self, user_id: str) -> List[str]:
        """Get list of jobs owned by a user."""
        return self.user_jobs.get(user_id, [])
    
    def user_owns_job(self, user_id: str, job_name: str) -> bool:
        """Check if user owns a specific job."""
        return job_name in self.get_user_jobs(user_id)
    
    async def purchase_job(self, user_id: str, job_name: str) -> bool:
        """
        Purchase a job for a user if they have enough coins.
        Returns True if successful, False otherwise.
        """
        if not self.job_exists(job_name):
            return False
        
        if self.user_owns_job(user_id, job_name):
            return False
        
        user_jobs = self.get_user_jobs(user_id)
        if len(user_jobs) >= 3:  # Max 3 jobs
            return False
        
        job_info = self.get_job_info(job_name)
        cost = job_info.get('cost', 0)
        
        # Check if user has enough money
        balance_data = await self.economy_manager.get_user_balance(user_id)
        if balance_data['wallet'] < cost:
            return False
        
        # Deduct cost and add job
        await self.economy_manager.update_balance(user_id, wallet_change=-cost)
        user_jobs.append(job_name)
        self.user_jobs[user_id] = user_jobs
        self.save_job_data()
        
        return True
    
    def remove_user_job(self, user_id: str, job_name: str) -> bool:
        """Remove a job from user's collection."""
        user_jobs = self.get_user_jobs(user_id)
        if job_name in user_jobs:
            user_jobs.remove(job_name)
            self.user_jobs[user_id] = user_jobs
            self.save_job_data()
            return True
        return False
    
    async def work_all_jobs(self, user_id: str):
        """
        Calculate earnings from working all user's jobs.
        Returns tuple: (total_earnings, earnings_breakdown)
        """
        import random
        
        user_jobs = self.get_user_jobs(user_id)
        if not user_jobs:
            return 0, []
        
        total_earnings = 0
        earnings_breakdown = []
        
        for job_name in user_jobs:
            job_info = self.get_job_info(job_name)
            base_pay = job_info.get('base_pay', 0)
            bonus_chance = job_info.get('bonus_chance', 0)
            bonus_amount = job_info.get('bonus_amount', 0)
            
            earnings = base_pay
            bonus_earned = 0
            
            # Check for bonus
            if random.random() < bonus_chance:
                bonus_earned = bonus_amount
                earnings += bonus_earned
                earnings_breakdown.append(f"🎉 {job_name}: {base_pay} coins + {bonus_earned} coins bonus")
            else:
                earnings_breakdown.append(f"{job_name}: {earnings} coins")
            
            total_earnings += earnings
        
        # Add earnings to wallet
        await self.economy_manager.update_balance(user_id, wallet_change=total_earnings)
        
        return total_earnings, earnings_breakdown
    
    async def get_user_wallet_balance(self, user_id: str) -> int:
        """Get user's current wallet balance."""
        balance_data = await self.economy_manager.get_user_balance(user_id)
        return balance_data['wallet']