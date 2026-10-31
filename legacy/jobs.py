import discord
from discord.ext import commands
import json
import os
import random
import datetime
from typing import Dict, List

class JobMarketView(discord.ui.View):
    def __init__(self, cog, ctx, page, total_pages):
        super().__init__(timeout=60)
        self.cog = cog
        self.ctx = ctx
        self.page = page
        self.total_pages = total_pages
        
        if page > 1:
            prev_button = discord.ui.Button(
                label="Previous",
                style=discord.ButtonStyle.primary,
                emoji="⬅️",
                custom_id="prev_page",
                row=0
            )
            prev_button.callback = self.prev_callback
            self.add_item(prev_button)
        
        if page < total_pages:
            next_button = discord.ui.Button(
                label="Next",
                style=discord.ButtonStyle.primary,
                emoji="➡️",
                custom_id="next_page",
                row=0
            )
            next_button.callback = self.next_callback
            self.add_item(next_button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("This menu is not for you!", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(view=self)
        except:
            pass

    async def update_page(self, new_page: int):
        # Calculate total pages
        jobs_per_page = 3
        total_jobs = len(self.cog.jobs)
        total_pages = (total_jobs + jobs_per_page - 1) // jobs_per_page
        
        # Ensure page is within valid range
        new_page = max(1, min(new_page, total_pages))
        
        # Get jobs for current page
        start_idx = (new_page - 1) * jobs_per_page
        end_idx = min(start_idx + jobs_per_page, total_jobs)
        current_jobs = list(self.cog.jobs.items())[start_idx:end_idx]
        
        user_id = str(self.ctx.author.id)
        user_jobs = self.cog.get_user_jobs(user_id)
        
        embed = discord.Embed(
            title="📋 Job Market",
            description=f"Here are all available jobs (Page {new_page}/{total_pages}):",
            color=discord.Color.blue()
        )
        
        for job_name, job_info in current_jobs:
            status = "✅ Unlocked" if job_name in user_jobs else "🔒 Locked"
            value = f"Base Pay: {job_info['base_pay']} coins\n"
            value += f"Bonus Chance: {job_info['bonus_chance']*100}%\n"
            value += f"Bonus Amount: {job_info['bonus_amount']} coins"
            if job_name not in user_jobs:
                value += f"\nCost to Unlock: {job_info['cost']} coins"
            
            embed.add_field(
                name=f"{status} {job_name}",
                value=value,
                inline=False
            )
        
        embed.add_field(
            name="📝 Commands",
            value="`-buyjob <job>` - Purchase a job to unlock it\n"
                  "`-work <job>` - Work at a job you've unlocked\n"
                  "`-jobs` - View this job market",
            inline=False
        )
        
        embed.set_footer(text="Work once per day to earn coins!")
        
        # Create new view for the updated page
        new_view = JobMarketView(self.cog, self.ctx, new_page, total_pages)
        new_view.message = self.message
        
        # Update the message
        await self.message.edit(embed=embed, view=new_view)

    async def prev_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.update_page(self.page - 1)

    async def next_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.update_page(self.page + 1)

class JobMarketCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.jobs_file = 'data/jobs.json'
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
        if not os.path.exists('data'):
            os.makedirs('data')
        
        if os.path.exists(self.jobs_file):
            with open(self.jobs_file, 'r') as f:
                data = json.load(f)
                self.current_jobs = data.get('current_jobs', [])
                # Load user jobs
                self.user_jobs = data.get('user_jobs', {})
        else:
            self.rotate_jobs()

    def save_job_data(self):
        data = {
            'current_jobs': self.current_jobs,
            'user_jobs': self.user_jobs
        }
        with open(self.jobs_file, 'w') as f:
            json.dump(data, f)

    def rotate_jobs(self):
        # Make all jobs available
        self.current_jobs = list(self.jobs.keys())
        self.save_job_data()
        print(f"Available jobs: {self.current_jobs}")

    async def get_bank_data(self):
        if not os.path.exists('data'):
            os.makedirs('data')
        
        if not os.path.exists('data/bank.json'):
            with open('data/bank.json', 'w') as f:
                json.dump({}, f)

        with open('data/bank.json', 'r') as f:
            content = f.read().strip()
            if not content:
                users = {}
            else:
                try:
                    users = json.loads(content)
                except json.JSONDecodeError:
                    users = {}
            
        if not content:
            with open('data/bank.json', 'w') as f:
                json.dump(users, f)
                
        return users

    async def open_account(self, user):
        users = await self.get_bank_data()
        user_id = str(user.id)

        if user_id not in users:
            users[user_id] = {}
            users[user_id]["wallet"] = 50
            users[user_id]["bank"] = 0
            users[user_id]["last_work"] = None
            with open('data/bank.json', 'w') as f:
                json.dump(users, f)

        if user_id not in self.user_jobs:
            self.user_jobs[user_id] = []
            self.save_job_data()

        return True

    def get_user_jobs(self, user_id: str) -> List[str]:
        return self.user_jobs.get(user_id, [])

    @commands.command()
    async def jobs(self, ctx, page: int = 1):
        await self.open_account(ctx.author)
        
        user_id = str(ctx.author.id)
        user_jobs = self.get_user_jobs(user_id)
        
        # Calculate total pages
        jobs_per_page = 3
        total_jobs = len(self.jobs)
        total_pages = (total_jobs + jobs_per_page - 1) // jobs_per_page
        
        # Ensure page is within valid range
        page = max(1, min(page, total_pages))
        
        # Get jobs for current page
        start_idx = (page - 1) * jobs_per_page
        end_idx = min(start_idx + jobs_per_page, total_jobs)
        current_jobs = list(self.jobs.items())[start_idx:end_idx]
        
        embed = discord.Embed(
            title="📋 Job Market",
            description=f"Here are all available jobs (Page {page}/{total_pages}):",
            color=discord.Color.blue()
        )
        
        for job_name, job_info in current_jobs:
            status = "✅ Unlocked" if job_name in user_jobs else "🔒 Locked"
            value = f"Base Pay: {job_info['base_pay']} coins\n"
            value += f"Bonus Chance: {job_info['bonus_chance']*100}%\n"
            value += f"Bonus Amount: {job_info['bonus_amount']} coins"
            if job_name not in user_jobs:
                value += f"\nCost to Unlock: {job_info['cost']} coins"
            
            embed.add_field(
                name=f"{status} {job_name}",
                value=value,
                inline=False
            )
        
        embed.add_field(
            name="📝 Commands",
            value="`-buyjob <job>` - Purchase a job to unlock it\n"
                  "`-work <job>` - Work at a job you've unlocked\n"
                  "`-jobs` - View this job market",
            inline=False
        )
        
        embed.set_footer(text="Work once per day to earn coins!")
        
        # Create view with navigation buttons
        view = JobMarketView(self, ctx, page, total_pages)
        
        # Send or update the message
        if not hasattr(view, 'message'):
            view.message = await ctx.send(embed=embed, view=view)
        else:
            await view.message.edit(embed=embed, view=view)

    @commands.command()
    async def buyjob(self, ctx, *, job_name: str = None):
        await self.open_account(ctx.author)
        
        if not job_name:
            embed = discord.Embed(
                title="Error",
                description="Please specify a job to purchase. Use -jobs to see available jobs.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
            
        job_name = job_name.title()
        if job_name not in self.jobs:
            embed = discord.Embed(
                title="Error",
                description=f"'{job_name}' is not a valid job. Use -jobs to see available jobs.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
            
        user_id = str(ctx.author.id)
        user_jobs = self.get_user_jobs(user_id)
        
        if job_name in user_jobs:
            embed = discord.Embed(
                title="Error",
                description=f"You already have the {job_name} job unlocked!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
            
        # Check if user has reached the maximum number of jobs
        if len(user_jobs) >= 3:
            embed = discord.Embed(
                title="Error",
                description="You can only have a maximum of 3 jobs at a time! Use `-removejob <job>` to remove a job before buying a new one.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
            
        job_info = self.jobs[job_name]
        users = await self.get_bank_data()
        
        if users[user_id]["wallet"] < job_info['cost']:
            embed = discord.Embed(
                title="Error",
                description=f"You don't have enough coins! You need {job_info['cost']} coins to unlock this job.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
            
        # Purchase the job
        users[user_id]["wallet"] -= job_info['cost']
        user_jobs.append(job_name)
        self.user_jobs[user_id] = user_jobs
        self.save_job_data()
        
        # Save updated wallet
        with open('data/bank.json', 'w') as f:
            json.dump(users, f)
            
        embed = discord.Embed(
            title="🎉 Job Unlocked!",
            description=f"Congratulations! You've unlocked the {job_name} job!",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="New Wallet Balance",
            value=f"{users[user_id]['wallet']} coins",
            inline=False
        )
        
        embed.add_field(
            name="Current Jobs",
            value="\n".join(user_jobs),
            inline=False
        )
        
        embed.set_footer(text=f"Requested by {ctx.author.name}", 
                        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.timestamp = datetime.datetime.utcnow()
        
        await ctx.send(embed=embed)

    @commands.command()
    async def removejob(self, ctx, *, job_name: str = None):
        await self.open_account(ctx.author)
        
        if not job_name:
            embed = discord.Embed(
                title="Error",
                description="Please specify a job to remove. Use -jobs to see your current jobs.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
            
        job_name = job_name.title()
        user_id = str(ctx.author.id)
        user_jobs = self.get_user_jobs(user_id)
        
        if job_name not in user_jobs:
            embed = discord.Embed(
                title="Error",
                description=f"You don't have the {job_name} job!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
            
        # Remove the job
        user_jobs.remove(job_name)
        self.user_jobs[user_id] = user_jobs
        self.save_job_data()
        
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
        
        embed.set_footer(text=f"Requested by {ctx.author.name}", 
                        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.timestamp = datetime.datetime.utcnow()
        
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 86400, commands.BucketType.user)  # 24 hour cooldown
    async def work(self, ctx):
        await self.open_account(ctx.author)
        self.rotate_jobs()
        
        user_id = str(ctx.author.id)
        user_jobs = self.get_user_jobs(user_id)
        
        if not user_jobs:
            embed = discord.Embed(
                title="Error",
                description="You don't have any jobs! Use -jobs to see available jobs.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
            
        users = await self.get_bank_data()
        total_earnings = 0
        earnings_breakdown = []
        
        # Calculate earnings for each job
        for job_name in user_jobs:
            job_info = self.jobs[job_name]
            earnings = job_info['base_pay']
            bonus_earned = 0
            
            # Check for bonus
            if random.random() < job_info['bonus_chance']:
                bonus_earned = job_info['bonus_amount']
                earnings += bonus_earned
                earnings_breakdown.append(f"🎉 {job_name}: {job_info['base_pay']} coins + {bonus_earned} coins bonus")
            else:
                earnings_breakdown.append(f"{job_name}: {earnings} coins")
            
            total_earnings += earnings
            
        # Update user's wallet
        users[user_id]["wallet"] += total_earnings
        
        # Save updated data
        with open('data/bank.json', 'w') as f:
            json.dump(users, f)
            
        # Create and send embed
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
            value=f"{users[user_id]['wallet']} coins",
            inline=False
        )
        
        embed.set_footer(text=f"Requested by {ctx.author.name}", 
                        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.timestamp = datetime.datetime.utcnow()
        
        await ctx.send(embed=embed)

    @work.error
    async def work_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            hours, remainder = divmod(error.retry_after, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            embed = discord.Embed(
                title="⏰ Cooldown Active",
                description="You've already worked today!",
                color=discord.Color.red()
            )
            
            embed.add_field(
                name="Time Remaining",
                value=f"{int(hours)}h {int(minutes)}m {int(seconds)}s",
                inline=False
            )
            
            embed.set_footer(text=f"Requested by {ctx.author.name}", 
                           icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            embed.timestamp = datetime.datetime.utcnow()
            
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Error",
                description=f"An unexpected error occurred: {str(error)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command()
    async def myjobs(self, ctx):
        await self.open_account(ctx.author)
        
        user_id = str(ctx.author.id)
        user_jobs = self.get_user_jobs(user_id)
        
        if not user_jobs:
            embed = discord.Embed(
                title="💼 Your Jobs",
                description="You don't have any jobs yet! Use `-jobs` to see available jobs and `-buyjob <job>` to purchase one.",
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Requested by {ctx.author.name}", 
                           icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            embed.timestamp = datetime.datetime.utcnow()
            await ctx.send(embed=embed)
            return
            
        embed = discord.Embed(
            title="💼 Your Jobs",
            description=f"You currently have {len(user_jobs)} job(s):",
            color=discord.Color.blue()
        )
        
        for job_name in user_jobs:
            job_info = self.jobs[job_name]
            value = f"Base Pay: {job_info['base_pay']} coins\n"
            value += f"Bonus Chance: {job_info['bonus_chance']*100}%\n"
            value += f"Bonus Amount: {job_info['bonus_amount']} coins"
            
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
        
        embed.set_footer(text=f"Requested by {ctx.author.name}", 
                        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.timestamp = datetime.datetime.utcnow()
        
        await ctx.send(embed=embed) 
import discord
from discord.ext import commands
import json
import os
import random
import datetime
from typing import Dict, List

class JobMarketView(discord.ui.View):
    def __init__(self, cog, ctx, page, total_pages):
        super().__init__(timeout=60)
        self.cog = cog
        self.ctx = ctx
        self.page = page
        self.total_pages = total_pages
        
        # Add previous page button if not on first page
        if page > 1:
            prev_button = discord.ui.Button(
                label="Previous",
                style=discord.ButtonStyle.primary,
                emoji="⬅️",
                custom_id="prev_page",
                row=0
            )
            prev_button.callback = self.prev_callback
            self.add_item(prev_button)
        
        # Add next page button if not on last page
        if page < total_pages:
            next_button = discord.ui.Button(
                label="Next",
                style=discord.ButtonStyle.primary,
                emoji="➡️",
                custom_id="next_page",
                row=0
            )
            next_button.callback = self.next_callback
            self.add_item(next_button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("This menu is not for you!", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(view=self)
        except:
            pass

    async def update_page(self, new_page: int):
        # Calculate total pages
        jobs_per_page = 3
        total_jobs = len(self.cog.jobs)
        total_pages = (total_jobs + jobs_per_page - 1) // jobs_per_page
        
        # Ensure page is within valid range
        new_page = max(1, min(new_page, total_pages))
        
        # Get jobs for current page
        start_idx = (new_page - 1) * jobs_per_page
        end_idx = min(start_idx + jobs_per_page, total_jobs)
        current_jobs = list(self.cog.jobs.items())[start_idx:end_idx]
        
        user_id = str(self.ctx.author.id)
        user_jobs = self.cog.get_user_jobs(user_id)
        
        embed = discord.Embed(
            title="📋 Job Market",
            description=f"Here are all available jobs (Page {new_page}/{total_pages}):",
            color=discord.Color.blue()
        )
        
        for job_name, job_info in current_jobs:
            status = "✅ Unlocked" if job_name in user_jobs else "🔒 Locked"
            value = f"Base Pay: {job_info['base_pay']} coins\n"
            value += f"Bonus Chance: {job_info['bonus_chance']*100}%\n"
            value += f"Bonus Amount: {job_info['bonus_amount']} coins"
            if job_name not in user_jobs:
                value += f"\nCost to Unlock: {job_info['cost']} coins"
            
            embed.add_field(
                name=f"{status} {job_name}",
                value=value,
                inline=False
            )
        
        embed.add_field(
            name="📝 Commands",
            value="`-buyjob <job>` - Purchase a job to unlock it\n"
                  "`-work <job>` - Work at a job you've unlocked\n"
                  "`-jobs` - View this job market",
            inline=False
        )
        
        embed.set_footer(text="Work once per day to earn coins!")
        
        # Create new view for the updated page
        new_view = JobMarketView(self.cog, self.ctx, new_page, total_pages)
        new_view.message = self.message
        
        # Update the message
        await self.message.edit(embed=embed, view=new_view)

    async def prev_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.update_page(self.page - 1)

    async def next_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.update_page(self.page + 1)

class JobMarketCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.jobs_file = 'data/jobs.json'
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
        if not os.path.exists('data'):
            os.makedirs('data')
        
        if os.path.exists(self.jobs_file):
            with open(self.jobs_file, 'r') as f:
                data = json.load(f)
                self.current_jobs = data.get('current_jobs', [])
                # Load user jobs
                self.user_jobs = data.get('user_jobs', {})
        else:
            self.rotate_jobs()

    def save_job_data(self):
        data = {
            'current_jobs': self.current_jobs,
            'user_jobs': self.user_jobs
        }
        with open(self.jobs_file, 'w') as f:
            json.dump(data, f)

    def rotate_jobs(self):
        # Make all jobs available
        self.current_jobs = list(self.jobs.keys())
        self.save_job_data()
        print(f"Available jobs: {self.current_jobs}")

    async def get_bank_data(self):
        if not os.path.exists('data'):
            os.makedirs('data')
        
        if not os.path.exists('data/bank.json'):
            with open('data/bank.json', 'w') as f:
                json.dump({}, f)

        with open('data/bank.json', 'r') as f:
            content = f.read().strip()
            if not content:
                users = {}
            else:
                try:
                    users = json.loads(content)
                except json.JSONDecodeError:
                    users = {}
            
        if not content:
            with open('data/bank.json', 'w') as f:
                json.dump(users, f)
                
        return users

    async def open_account(self, user):
        users = await self.get_bank_data()
        user_id = str(user.id)

        if user_id not in users:
            users[user_id] = {}
            users[user_id]["wallet"] = 50
            users[user_id]["bank"] = 0
            users[user_id]["last_work"] = None
            with open('data/bank.json', 'w') as f:
                json.dump(users, f)

        if user_id not in self.user_jobs:
            self.user_jobs[user_id] = []
            self.save_job_data()

        return True

    def get_user_jobs(self, user_id: str) -> List[str]:
        return self.user_jobs.get(user_id, [])

    @commands.command()
    async def jobs(self, ctx, page: int = 1):
        await self.open_account(ctx.author)
        
        user_id = str(ctx.author.id)
        user_jobs = self.get_user_jobs(user_id)
        
        # Calculate total pages
        jobs_per_page = 3
        total_jobs = len(self.jobs)
        total_pages = (total_jobs + jobs_per_page - 1) // jobs_per_page
        
        # Ensure page is within valid range
        page = max(1, min(page, total_pages))
        
        # Get jobs for current page
        start_idx = (page - 1) * jobs_per_page
        end_idx = min(start_idx + jobs_per_page, total_jobs)
        current_jobs = list(self.jobs.items())[start_idx:end_idx]
        
        embed = discord.Embed(
            title="📋 Job Market",
            description=f"Here are all available jobs (Page {page}/{total_pages}):",
            color=discord.Color.blue()
        )
        
        for job_name, job_info in current_jobs:
            status = "✅ Unlocked" if job_name in user_jobs else "🔒 Locked"
            value = f"Base Pay: {job_info['base_pay']} coins\n"
            value += f"Bonus Chance: {job_info['bonus_chance']*100}%\n"
            value += f"Bonus Amount: {job_info['bonus_amount']} coins"
            if job_name not in user_jobs:
                value += f"\nCost to Unlock: {job_info['cost']} coins"
            
            embed.add_field(
                name=f"{status} {job_name}",
                value=value,
                inline=False
            )
        
        embed.add_field(
            name="📝 Commands",
            value="`-buyjob <job>` - Purchase a job to unlock it\n"
                  "`-work <job>` - Work at a job you've unlocked\n"
                  "`-jobs` - View this job market",
            inline=False
        )
        
        embed.set_footer(text="Work once per day to earn coins!")
        
        # Create view with navigation buttons
        view = JobMarketView(self, ctx, page, total_pages)
        
        # Send or update the message
        if not hasattr(view, 'message'):
            view.message = await ctx.send(embed=embed, view=view)
        else:
            await view.message.edit(embed=embed, view=view)

    @commands.command()
    async def buyjob(self, ctx, *, job_name: str = None):
        await self.open_account(ctx.author)
        
        if not job_name:
            embed = discord.Embed(
                title="Error",
                description="Please specify a job to purchase. Use -jobs to see available jobs.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
            
        job_name = job_name.title()
        if job_name not in self.jobs:
            embed = discord.Embed(
                title="Error",
                description=f"'{job_name}' is not a valid job. Use -jobs to see available jobs.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
            
        user_id = str(ctx.author.id)
        user_jobs = self.get_user_jobs(user_id)
        
        if job_name in user_jobs:
            embed = discord.Embed(
                title="Error",
                description=f"You already have the {job_name} job unlocked!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
            
        # Check if user has reached the maximum number of jobs
        if len(user_jobs) >= 3:
            embed = discord.Embed(
                title="Error",
                description="You can only have a maximum of 3 jobs at a time! Use `-removejob <job>` to remove a job before buying a new one.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
            
        job_info = self.jobs[job_name]
        users = await self.get_bank_data()
        
        if users[user_id]["wallet"] < job_info['cost']:
            embed = discord.Embed(
                title="Error",
                description=f"You don't have enough coins! You need {job_info['cost']} coins to unlock this job.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
            
        # Purchase the job
        users[user_id]["wallet"] -= job_info['cost']
        user_jobs.append(job_name)
        self.user_jobs[user_id] = user_jobs
        self.save_job_data()
        
        # Save updated wallet
        with open('data/bank.json', 'w') as f:
            json.dump(users, f)
            
        embed = discord.Embed(
            title="🎉 Job Unlocked!",
            description=f"Congratulations! You've unlocked the {job_name} job!",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="New Wallet Balance",
            value=f"{users[user_id]['wallet']} coins",
            inline=False
        )
        
        embed.add_field(
            name="Current Jobs",
            value="\n".join(user_jobs),
            inline=False
        )
        
        embed.set_footer(text=f"Requested by {ctx.author.name}", 
                        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.timestamp = datetime.datetime.utcnow()
        
        await ctx.send(embed=embed)

    @commands.command()
    async def removejob(self, ctx, *, job_name: str = None):
        await self.open_account(ctx.author)
        
        if not job_name:
            embed = discord.Embed(
                title="Error",
                description="Please specify a job to remove. Use -jobs to see your current jobs.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
            
        job_name = job_name.title()
        user_id = str(ctx.author.id)
        user_jobs = self.get_user_jobs(user_id)
        
        if job_name not in user_jobs:
            embed = discord.Embed(
                title="Error",
                description=f"You don't have the {job_name} job!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
            
        # Remove the job
        user_jobs.remove(job_name)
        self.user_jobs[user_id] = user_jobs
        self.save_job_data()
        
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
        
        embed.set_footer(text=f"Requested by {ctx.author.name}", 
                        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.timestamp = datetime.datetime.utcnow()
        
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 86400, commands.BucketType.user)  # 24 hour cooldown
    async def work(self, ctx):
        await self.open_account(ctx.author)
        self.rotate_jobs()
        
        user_id = str(ctx.author.id)
        user_jobs = self.get_user_jobs(user_id)
        
        if not user_jobs:
            embed = discord.Embed(
                title="Error",
                description="You don't have any jobs! Use -jobs to see available jobs.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
            
        users = await self.get_bank_data()
        total_earnings = 0
        earnings_breakdown = []
        
        # Calculate earnings for each job
        for job_name in user_jobs:
            job_info = self.jobs[job_name]
            earnings = job_info['base_pay']
            bonus_earned = 0
            
            # Check for bonus
            if random.random() < job_info['bonus_chance']:
                bonus_earned = job_info['bonus_amount']
                earnings += bonus_earned
                earnings_breakdown.append(f"🎉 {job_name}: {job_info['base_pay']} coins + {bonus_earned} coins bonus")
            else:
                earnings_breakdown.append(f"{job_name}: {earnings} coins")
            
            total_earnings += earnings
            
        # Update user's wallet
        users[user_id]["wallet"] += total_earnings
        
        # Save updated data
        with open('data/bank.json', 'w') as f:
            json.dump(users, f)
            
        # Create and send embed
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
            value=f"{users[user_id]['wallet']} coins",
            inline=False
        )
        
        embed.set_footer(text=f"Requested by {ctx.author.name}", 
                        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.timestamp = datetime.datetime.utcnow()
        
        await ctx.send(embed=embed)

    @work.error
    async def work_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            hours, remainder = divmod(error.retry_after, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            embed = discord.Embed(
                title="⏰ Cooldown Active",
                description="You've already worked today!",
                color=discord.Color.red()
            )
            
            embed.add_field(
                name="Time Remaining",
                value=f"{int(hours)}h {int(minutes)}m {int(seconds)}s",
                inline=False
            )
            
            embed.set_footer(text=f"Requested by {ctx.author.name}", 
                           icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            embed.timestamp = datetime.datetime.utcnow()
            
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Error",
                description=f"An unexpected error occurred: {str(error)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command()
    async def myjobs(self, ctx):
        await self.open_account(ctx.author)
        
        user_id = str(ctx.author.id)
        user_jobs = self.get_user_jobs(user_id)
        
        if not user_jobs:
            embed = discord.Embed(
                title="💼 Your Jobs",
                description="You don't have any jobs yet! Use `-jobs` to see available jobs and `-buyjob <job>` to purchase one.",
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Requested by {ctx.author.name}", 
                           icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            embed.timestamp = datetime.datetime.utcnow()
            await ctx.send(embed=embed)
            return
            
        embed = discord.Embed(
            title="💼 Your Jobs",
            description=f"You currently have {len(user_jobs)} job(s):",
            color=discord.Color.blue()
        )
        
        for job_name in user_jobs:
            job_info = self.jobs[job_name]
            value = f"Base Pay: {job_info['base_pay']} coins\n"
            value += f"Bonus Chance: {job_info['bonus_chance']*100}%\n"
            value += f"Bonus Amount: {job_info['bonus_amount']} coins"
            
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
        
        embed.set_footer(text=f"Requested by {ctx.author.name}", 
                        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.timestamp = datetime.datetime.utcnow()
        
        await ctx.send(embed=embed) 