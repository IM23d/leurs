import discord
from discord.ext import commands
import json
import os
import random
import datetime
import math

class BalanceLeaderboardView(discord.ui.View):
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
        # Get all user data from database 
        users = await self.cog.get_bank_data()
        
        # Create list from all users in the database
        user_list = []
        
        # Add all existing database entries
        for user_id, user_data in users.items():
            try:
                # Try to get the member object
                member = self.ctx.guild.get_member(int(user_id))
                
                # Calculate total balance
                wallet = user_data.get("wallet", 0)
                bank = user_data.get("bank", 0)
                total_balance = wallet + bank
                
                # Get user data
                user_entry = {
                    "id": user_id,
                    "wallet": wallet,
                    "bank": bank,
                    "total": total_balance,
                    "member": member
                }
                user_list.append(user_entry)
            except Exception as e:
                # Skip problematic entries
                continue
        
        # Sort by total balance (highest first)
        user_list.sort(key=lambda x: x["total"], reverse=True)
        
        # Paginate results (10 per page)
        total_pages = max(1, math.ceil(len(user_list) / 10))
        
        # Ensure page is within valid range
        new_page = max(1, min(new_page, total_pages))
        
        start_idx = (new_page - 1) * 10
        end_idx = min(start_idx + 10, len(user_list))
        
        # Create embed
        embed = discord.Embed(
            title=f"💰 Balance Leaderboard",
            description=f"Top members ranked by total wealth.",
            color=discord.Color.gold()
        )
        
        # Add leaderboard entries
        if not user_list:
            embed.description = "No users have any money yet!"
        else:
            # Get rank emojis for top 3
            rank_emoji = {0: "🥇", 1: "🥈", 2: "🥉"}
            
            for idx, user_data in enumerate(user_list[start_idx:end_idx], start=start_idx + 1):
                member = user_data["member"]
                user_id = user_data["id"]
                position = idx - 1 + start_idx  # Zero-based position
                
                # Get appropriate emoji based on rank
                prefix = rank_emoji.get(position, f"{idx}.")
                
                # Get the name and icon url
                if member:
                    name = member.name
                    icon_url = member.avatar.url if member.avatar else member.default_avatar.url
                else:
                    # Try to fetch user info from Discord
                    try:
                        user = await self.cog.client.fetch_user(int(user_id))
                        name = user.name
                        icon_url = user.avatar.url if user.avatar else user.default_avatar.url
                    except:
                        # If all else fails, use a generic name
                        name = f"User-{user_id[-4:]}"
                        icon_url = None
                
                # Create embed field
                field_name = f"{prefix} {name}"
                field_value = f"**{user_data['total']} coins**"
                
                embed.add_field(name=field_name, value=field_value, inline=False)
                
                # Show first-place user as thumbnail
                if position == 0 and icon_url:
                    embed.set_thumbnail(url=icon_url)
        
        embed.set_footer(text=f"Page {new_page}/{total_pages} • Requested by {self.ctx.author.name}", 
                         icon_url=self.ctx.author.avatar.url if self.ctx.author.avatar else self.ctx.author.default_avatar.url)
        embed.timestamp = datetime.datetime.utcnow()
        
        # Create new view with updated page
        new_view = BalanceLeaderboardView(self.cog, self.ctx, new_page, total_pages)
        new_view.message = self.message
        
        # Update the message
        await self.message.edit(embed=embed, view=new_view)

    async def prev_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.update_page(self.page - 1)

    async def next_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.update_page(self.page + 1)

class EconomyCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        
    @commands.command()
    async def balance(self, ctx):
        await self.open_account(ctx.author)
        user = ctx.author
        users = await self.get_bank_data()

        wallet_amt = users[str(ctx.author.id)]["wallet"]
        bank_amt = users[str(ctx.author.id)]["bank"]

        em = discord.Embed(title=f"{ctx.author.name}'s balance", color=discord.Color.from_rgb(255, 255, 255))
        em.add_field(name="Wallet balance", value=wallet_amt)
        em.add_field(name="Bank balance", value=bank_amt)
        await ctx.send(embed=em)

    @commands.command()
    async def bal(self, ctx):
        await self.balance(ctx)

    @commands.command()
    async def dep(self, ctx, amount=None):
        await self.deposit(ctx, amount)

    @commands.command()
    async def wit(self, ctx, amount=None):
        await self.withdraw(ctx, amount)

    @commands.command()
    @commands.cooldown(1, 86400, commands.BucketType.user)  # 1 day cooldown
    async def beg(self, ctx):
        import random
        
        await self.open_account(ctx.author)
        users = await self.get_bank_data()
        user = ctx.author
        
        earnings = random.randrange(101)  # amount the user gets for -beg = max 101
        
        embed = discord.Embed(
            title="Begging Results",
            description=f"Diddy gave you **{earnings} coins**!",
            color=discord.Color.green()
        )
        
        embed.set_thumbnail(url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        
        new_balance = users[str(ctx.author.id)]["wallet"] + earnings
        embed.add_field(
            name="New Wallet Balance", 
            value=f"{new_balance} coins",
            inline=False
        )
        
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.timestamp = datetime.datetime.utcnow()
        
        await ctx.send(embed=embed)
        
        users[str(ctx.author.id)]["wallet"] += earnings
        
        with open('data/bank.json', 'w') as f:
            json.dump(users, f)

    @beg.error  # error handling for -beg
    async def beg_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            hours, remainder = divmod(error.retry_after, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            embed = discord.Embed(
                title="Cooldown Active",
                description="You've already begged recently!",
                color=discord.Color.red()
            )
            
            embed.add_field(
                name="Time Remaining",
                value=f"{int(hours)}h {int(minutes)}m {int(seconds)}s",
                inline=False
            )
                        
            embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            embed.timestamp = datetime.datetime.utcnow()
            
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Error Occurred",
                description=f"An unexpected error happened: {str(error)}",
                color=discord.Color.dark_red()
            )
            embed.set_footer(text="Please report this to the admins")
            await ctx.send(embed=embed)
    
    async def open_account(self, user):
        users = await self.get_bank_data()

        if str(user.id) in users:
            return False
        else:
            users[str(user.id)] = {}
            users[str(user.id)]["wallet"] = 50  # starting balance
            users[str(user.id)]["bank"] = 0

        with open('data/bank.json', 'w') as f:  # opens account for new user
            json.dump(users, f)
        return True
    
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

    @commands.command()
    async def withdraw(self, ctx, amount=None):
        await self.open_account(ctx.author)
        users = await self.get_bank_data()
        user = ctx.author
        
        if amount is None:
            embed = discord.Embed(
                title="Error",
                description="Please specify an amount to withdraw",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
            
        # Handle percentage-based withdrawals
        if amount.lower() == "all":
            amount = users[str(user.id)]["bank"]
        elif "%" in amount:
            try:
                percentage = int(amount.replace("%", ""))
                if percentage <= 0 or percentage > 100:
                    raise ValueError
                amount = int(users[str(user.id)]["bank"] * (percentage / 100))
            except ValueError:
                embed = discord.Embed(
                    title="Error",
                    description="Please enter a valid percentage between 1% and 100%",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
        else:
            try:
                amount = int(amount)
            except ValueError:
                embed = discord.Embed(
                    title="Error",
                    description="Please enter a valid number, percentage, or 'all'",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
        
        if amount <= 0:
            embed = discord.Embed(
                title="Error",
                description="Amount must be positive!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
            
        if amount > users[str(user.id)]["bank"]:
            embed = discord.Embed(
                title="Error",
                description="You don't have that much money in your bank!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
            
        # Update balances
        users[str(user.id)]["bank"] -= amount
        users[str(user.id)]["wallet"] += amount
        
        # Save updated data
        with open('data/bank.json', 'w') as f:
            json.dump(users, f)
            
        # Create and send embed
        embed = discord.Embed(
            title="Withdrawal Successful",
            description=f"You withdrew **{amount} coins** from your bank!",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="Wallet Balance", 
            value=f"{users[str(user.id)]['wallet']} coins",
            inline=True
        )
        
        embed.add_field(
            name="Bank Balance", 
            value=f"{users[str(user.id)]['bank']} coins",
            inline=True
        )
        
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.timestamp = datetime.datetime.utcnow()
        
        await ctx.send(embed=embed)

    @commands.command()
    async def deposit(self, ctx, amount=None):
        await self.open_account(ctx.author)
        users = await self.get_bank_data()
        user = ctx.author
        
        if amount is None:
            embed = discord.Embed(
                title="Error",
                description="Please specify an amount to deposit",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
            
        # Handle percentage-based deposits
        if amount.lower() == "all":
            amount = users[str(user.id)]["wallet"]
        elif "%" in amount:
            try:
                percentage = int(amount.replace("%", ""))
                if percentage <= 0 or percentage > 100:
                    raise ValueError
                amount = int(users[str(user.id)]["wallet"] * (percentage / 100))
            except ValueError:
                embed = discord.Embed(
                    title="Error",
                    description="Please enter a valid percentage between 1% and 100%",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
        else:
            try:
                amount = int(amount)
            except ValueError:
                embed = discord.Embed(
                    title="Error",
                    description="Please enter a valid number, percentage, or 'all'",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
        
        if amount <= 0:
            embed = discord.Embed(
                title="Error",
                description="Amount must be positive!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
            
        if amount > users[str(user.id)]["wallet"]:
            embed = discord.Embed(
                title="Error",
                description="You don't have that much money in your wallet!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
                    
        # Update balances
        users[str(user.id)]["wallet"] -= amount
        users[str(user.id)]["bank"] += amount
        
        # Save updated data
        with open('data/bank.json', 'w') as f:
            json.dump(users, f)
            
        # Create and send embed
        embed = discord.Embed(
            title="Deposit Successful",
            description=f"You deposited **{amount} coins** into your bank!",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="Wallet Balance", 
            value=f"{users[str(user.id)]['wallet']} coins",
            inline=True
        )
        
        embed.add_field(
            name="Bank Balance", 
            value=f"{users[str(user.id)]['bank']} coins",
            inline=True
        )
        
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.timestamp = datetime.datetime.utcnow()
        
        await ctx.send(embed=embed)

    @commands.command(aliases=["baltop"])
    async def balancetop(self, ctx, page: int = 1):
        # Get all user data from the database file directly
        users = await self.get_bank_data()
        
        # Create list from all users in the database
        user_list = []
        
        # First, add all existing database entries
        for user_id, user_data in users.items():
            try:
                # Try to get the member object, fetch from Discord if needed
                member = ctx.guild.get_member(int(user_id))
                
                # Calculate total balance
                wallet = user_data.get("wallet", 0)
                bank = user_data.get("bank", 0)
                total_balance = wallet + bank
                
                # Get user data
                user_entry = {
                    "id": user_id,
                    "wallet": wallet,
                    "bank": bank,
                    "total": total_balance,
                    "member": member
                }
                user_list.append(user_entry)
            except Exception as e:
                # Skip problematic entries
                continue
        
        # Now sort and display
        # Sort by total balance (highest first)
        user_list.sort(key=lambda x: x["total"], reverse=True)
        
        # Paginate results (10 per page)
        total_pages = max(1, math.ceil(len(user_list) / 10))
        
        # Ensure page is within valid range
        page = max(1, min(page, total_pages))
        
        start_idx = (page - 1) * 10
        end_idx = min(start_idx + 10, len(user_list))
        
        # Create embed
        embed = discord.Embed(
            title=f"💰 Balance Leaderboard",
            description=f"Top members ranked by total wealth.",
            color=discord.Color.gold()
        )
        
        # Add leaderboard entries
        if not user_list:
            embed.description = "No users have any money yet!"
        else:
            # Get rank emojis for top 3
            rank_emoji = {0: "🥇", 1: "🥈", 2: "🥉"}
            
            for idx, user_data in enumerate(user_list[start_idx:end_idx], start=start_idx + 1):
                member = user_data["member"]
                user_id = user_data["id"]
                position = idx - 1 + start_idx  # Zero-based position
                
                # Get appropriate emoji based on rank
                prefix = rank_emoji.get(position, f"{idx}.")
                
                # Get the name and icon url
                if member:
                    name = member.name
                    icon_url = member.avatar.url if member.avatar else member.default_avatar.url
                else:
                    # Try to fetch user info from Discord
                    try:
                        user = await self.client.fetch_user(int(user_id))
                        name = user.name
                        icon_url = user.avatar.url if user.avatar else user.default_avatar.url
                    except:
                        # If all else fails, use a generic name
                        name = f"User-{user_id[-4:]}"
                        icon_url = None
                
                # Create embed field
                field_name = f"{prefix} {name}"
                field_value = f"**{user_data['total']} coins**"
                
                embed.add_field(name=field_name, value=field_value, inline=False)
                
                # Show first-place user as thumbnail
                if position == 0 and icon_url:
                    embed.set_thumbnail(url=icon_url)
        
        embed.set_footer(text=f"Page {page}/{total_pages} • Requested by {ctx.author.name}", 
                         icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.timestamp = datetime.datetime.utcnow()
        
        # Create view with pagination buttons
        view = BalanceLeaderboardView(self, ctx, page, total_pages)
        
        # Send embed with view
        view.message = await ctx.send(embed=embed, view=view)

    async def add_balance(self, user_id, amount):
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
        
        # Save updated data
        with open('data/bank.json', 'w') as f:
            json.dump(users, f)
            
        return users[user_id]["wallet"]
    
    async def remove_balance(self, user_id, amount):
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
        
        # Save updated data
        with open('data/bank.json', 'w') as f:
            json.dump(users, f)
            
        return True
import discord
from discord.ext import commands
import json
import os
import random
import datetime
import math

class BalanceLeaderboardView(discord.ui.View):
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
        # Get all user data from database 
        users = await self.cog.get_bank_data()
        
        # Create list from all users in the database
        user_list = []
        
        # Add all existing database entries
        for user_id, user_data in users.items():
            try:
                # Try to get the member object
                member = self.ctx.guild.get_member(int(user_id))
                
                # Calculate total balance
                wallet = user_data.get("wallet", 0)
                bank = user_data.get("bank", 0)
                total_balance = wallet + bank
                
                # Get user data
                user_entry = {
                    "id": user_id,
                    "wallet": wallet,
                    "bank": bank,
                    "total": total_balance,
                    "member": member
                }
                user_list.append(user_entry)
            except Exception as e:
                # Skip problematic entries
                continue
        
        # Sort by total balance (highest first)
        user_list.sort(key=lambda x: x["total"], reverse=True)
        
        # Paginate results (10 per page)
        total_pages = max(1, math.ceil(len(user_list) / 10))
        
        # Ensure page is within valid range
        new_page = max(1, min(new_page, total_pages))
        
        start_idx = (new_page - 1) * 10
        end_idx = min(start_idx + 10, len(user_list))
        
        # Create embed
        embed = discord.Embed(
            title=f"💰 Balance Leaderboard",
            description=f"Top members ranked by total wealth.",
            color=discord.Color.gold()
        )
        
        # Add leaderboard entries
        if not user_list:
            embed.description = "No users have any money yet!"
        else:
            # Get rank emojis for top 3
            rank_emoji = {0: "🥇", 1: "🥈", 2: "🥉"}
            
            for idx, user_data in enumerate(user_list[start_idx:end_idx], start=start_idx + 1):
                member = user_data["member"]
                user_id = user_data["id"]
                position = idx - 1 + start_idx  # Zero-based position
                
                # Get appropriate emoji based on rank
                prefix = rank_emoji.get(position, f"{idx}.")
                
                # Get the name and icon url
                if member:
                    name = member.name
                    icon_url = member.avatar.url if member.avatar else member.default_avatar.url
                else:
                    # Try to fetch user info from Discord
                    try:
                        user = await self.cog.client.fetch_user(int(user_id))
                        name = user.name
                        icon_url = user.avatar.url if user.avatar else user.default_avatar.url
                    except:
                        # If all else fails, use a generic name
                        name = f"User-{user_id[-4:]}"
                        icon_url = None
                
                # Create embed field
                field_name = f"{prefix} {name}"
                field_value = f"**{user_data['total']} coins**"
                
                embed.add_field(name=field_name, value=field_value, inline=False)
                
                # Show first-place user as thumbnail
                if position == 0 and icon_url:
                    embed.set_thumbnail(url=icon_url)
        
        embed.set_footer(text=f"Page {new_page}/{total_pages} • Requested by {self.ctx.author.name}", 
                         icon_url=self.ctx.author.avatar.url if self.ctx.author.avatar else self.ctx.author.default_avatar.url)
        embed.timestamp = datetime.datetime.utcnow()
        
        # Create new view with updated page
        new_view = BalanceLeaderboardView(self.cog, self.ctx, new_page, total_pages)
        new_view.message = self.message
        
        # Update the message
        await self.message.edit(embed=embed, view=new_view)

    async def prev_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.update_page(self.page - 1)

    async def next_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.update_page(self.page + 1)

class EconomyCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        
    @commands.command()
    async def balance(self, ctx):
        await self.open_account(ctx.author)
        user = ctx.author
        users = await self.get_bank_data()

        wallet_amt = users[str(ctx.author.id)]["wallet"]
        bank_amt = users[str(ctx.author.id)]["bank"]

        em = discord.Embed(title=f"{ctx.author.name}'s balance", color=discord.Color.from_rgb(255, 255, 255))
        em.add_field(name="Wallet balance", value=wallet_amt)
        em.add_field(name="Bank balance", value=bank_amt)
        await ctx.send(embed=em)

    @commands.command()
    async def bal(self, ctx):
        await self.balance(ctx)

    @commands.command()
    async def dep(self, ctx, amount=None):
        await self.deposit(ctx, amount)

    @commands.command()
    async def wit(self, ctx, amount=None):
        await self.withdraw(ctx, amount)

    @commands.command()
    @commands.cooldown(1, 86400, commands.BucketType.user)  # 1 day cooldown
    async def beg(self, ctx):
        import random
        
        await self.open_account(ctx.author)
        users = await self.get_bank_data()
        user = ctx.author
        
        earnings = random.randrange(101)  # amount the user gets for -beg = max 101
        
        embed = discord.Embed(
            title="Begging Results",
            description=f"Diddy gave you **{earnings} coins**!",
            color=discord.Color.green()
        )
        
        embed.set_thumbnail(url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        
        new_balance = users[str(ctx.author.id)]["wallet"] + earnings
        embed.add_field(
            name="New Wallet Balance", 
            value=f"{new_balance} coins",
            inline=False
        )
        
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.timestamp = datetime.datetime.utcnow()
        
        await ctx.send(embed=embed)
        
        users[str(ctx.author.id)]["wallet"] += earnings
        
        with open('data/bank.json', 'w') as f:
            json.dump(users, f)

    @beg.error  # error handling for -beg
    async def beg_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            hours, remainder = divmod(error.retry_after, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            embed = discord.Embed(
                title="Cooldown Active",
                description="You've already begged recently!",
                color=discord.Color.red()
            )
            
            embed.add_field(
                name="Time Remaining",
                value=f"{int(hours)}h {int(minutes)}m {int(seconds)}s",
                inline=False
            )
                        
            embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            embed.timestamp = datetime.datetime.utcnow()
            
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Error Occurred",
                description=f"An unexpected error happened: {str(error)}",
                color=discord.Color.dark_red()
            )
            embed.set_footer(text="Please report this to the admins")
            await ctx.send(embed=embed)
    
    async def open_account(self, user):
        users = await self.get_bank_data()

        if str(user.id) in users:
            return False
        else:
            users[str(user.id)] = {}
            users[str(user.id)]["wallet"] = 50  # starting balance
            users[str(user.id)]["bank"] = 0

        with open('data/bank.json', 'w') as f:  # opens account for new user
            json.dump(users, f)
        return True
    
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

    @commands.command()
    async def withdraw(self, ctx, amount=None):
        await self.open_account(ctx.author)
        users = await self.get_bank_data()
        user = ctx.author
        
        if amount is None:
            embed = discord.Embed(
                title="Error",
                description="Please specify an amount to withdraw",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
            
        # Handle percentage-based withdrawals
        if amount.lower() == "all":
            amount = users[str(user.id)]["bank"]
        elif "%" in amount:
            try:
                percentage = int(amount.replace("%", ""))
                if percentage <= 0 or percentage > 100:
                    raise ValueError
                amount = int(users[str(user.id)]["bank"] * (percentage / 100))
            except ValueError:
                embed = discord.Embed(
                    title="Error",
                    description="Please enter a valid percentage between 1% and 100%",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
        else:
            try:
                amount = int(amount)
            except ValueError:
                embed = discord.Embed(
                    title="Error",
                    description="Please enter a valid number, percentage, or 'all'",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
        
        if amount <= 0:
            embed = discord.Embed(
                title="Error",
                description="Amount must be positive!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
            
        if amount > users[str(user.id)]["bank"]:
            embed = discord.Embed(
                title="Error",
                description="You don't have that much money in your bank!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
            
        # Update balances
        users[str(user.id)]["bank"] -= amount
        users[str(user.id)]["wallet"] += amount
        
        # Save updated data
        with open('data/bank.json', 'w') as f:
            json.dump(users, f)
            
        # Create and send embed
        embed = discord.Embed(
            title="Withdrawal Successful",
            description=f"You withdrew **{amount} coins** from your bank!",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="Wallet Balance", 
            value=f"{users[str(user.id)]['wallet']} coins",
            inline=True
        )
        
        embed.add_field(
            name="Bank Balance", 
            value=f"{users[str(user.id)]['bank']} coins",
            inline=True
        )
        
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.timestamp = datetime.datetime.utcnow()
        
        await ctx.send(embed=embed)

    @commands.command()
    async def deposit(self, ctx, amount=None):
        await self.open_account(ctx.author)
        users = await self.get_bank_data()
        user = ctx.author
        
        if amount is None:
            embed = discord.Embed(
                title="Error",
                description="Please specify an amount to deposit",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
            
        # Handle percentage-based deposits
        if amount.lower() == "all":
            amount = users[str(user.id)]["wallet"]
        elif "%" in amount:
            try:
                percentage = int(amount.replace("%", ""))
                if percentage <= 0 or percentage > 100:
                    raise ValueError
                amount = int(users[str(user.id)]["wallet"] * (percentage / 100))
            except ValueError:
                embed = discord.Embed(
                    title="Error",
                    description="Please enter a valid percentage between 1% and 100%",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
        else:
            try:
                amount = int(amount)
            except ValueError:
                embed = discord.Embed(
                    title="Error",
                    description="Please enter a valid number, percentage, or 'all'",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
        
        if amount <= 0:
            embed = discord.Embed(
                title="Error",
                description="Amount must be positive!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
            
        if amount > users[str(user.id)]["wallet"]:
            embed = discord.Embed(
                title="Error",
                description="You don't have that much money in your wallet!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
                    
        # Update balances
        users[str(user.id)]["wallet"] -= amount
        users[str(user.id)]["bank"] += amount
        
        # Save updated data
        with open('data/bank.json', 'w') as f:
            json.dump(users, f)
            
        # Create and send embed
        embed = discord.Embed(
            title="Deposit Successful",
            description=f"You deposited **{amount} coins** into your bank!",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="Wallet Balance", 
            value=f"{users[str(user.id)]['wallet']} coins",
            inline=True
        )
        
        embed.add_field(
            name="Bank Balance", 
            value=f"{users[str(user.id)]['bank']} coins",
            inline=True
        )
        
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.timestamp = datetime.datetime.utcnow()
        
        await ctx.send(embed=embed)

    @commands.command(aliases=["baltop"])
    async def balancetop(self, ctx, page: int = 1):
        # Get all user data from the database file directly
        users = await self.get_bank_data()
        
        # Create list from all users in the database
        user_list = []
        
        # First, add all existing database entries
        for user_id, user_data in users.items():
            try:
                # Try to get the member object, fetch from Discord if needed
                member = ctx.guild.get_member(int(user_id))
                
                # Calculate total balance
                wallet = user_data.get("wallet", 0)
                bank = user_data.get("bank", 0)
                total_balance = wallet + bank
                
                # Get user data
                user_entry = {
                    "id": user_id,
                    "wallet": wallet,
                    "bank": bank,
                    "total": total_balance,
                    "member": member
                }
                user_list.append(user_entry)
            except Exception as e:
                # Skip problematic entries
                continue
        
        # Now sort and display
        # Sort by total balance (highest first)
        user_list.sort(key=lambda x: x["total"], reverse=True)
        
        # Paginate results (10 per page)
        total_pages = max(1, math.ceil(len(user_list) / 10))
        
        # Ensure page is within valid range
        page = max(1, min(page, total_pages))
        
        start_idx = (page - 1) * 10
        end_idx = min(start_idx + 10, len(user_list))
        
        # Create embed
        embed = discord.Embed(
            title=f"💰 Balance Leaderboard",
            description=f"Top members ranked by total wealth.",
            color=discord.Color.gold()
        )
        
        # Add leaderboard entries
        if not user_list:
            embed.description = "No users have any money yet!"
        else:
            # Get rank emojis for top 3
            rank_emoji = {0: "🥇", 1: "🥈", 2: "🥉"}
            
            for idx, user_data in enumerate(user_list[start_idx:end_idx], start=start_idx + 1):
                member = user_data["member"]
                user_id = user_data["id"]
                position = idx - 1 + start_idx  # Zero-based position
                
                # Get appropriate emoji based on rank
                prefix = rank_emoji.get(position, f"{idx}.")
                
                # Get the name and icon url
                if member:
                    name = member.name
                    icon_url = member.avatar.url if member.avatar else member.default_avatar.url
                else:
                    # Try to fetch user info from Discord
                    try:
                        user = await self.client.fetch_user(int(user_id))
                        name = user.name
                        icon_url = user.avatar.url if user.avatar else user.default_avatar.url
                    except:
                        # If all else fails, use a generic name
                        name = f"User-{user_id[-4:]}"
                        icon_url = None
                
                # Create embed field
                field_name = f"{prefix} {name}"
                field_value = f"**{user_data['total']} coins**"
                
                embed.add_field(name=field_name, value=field_value, inline=False)
                
                # Show first-place user as thumbnail
                if position == 0 and icon_url:
                    embed.set_thumbnail(url=icon_url)
        
        embed.set_footer(text=f"Page {page}/{total_pages} • Requested by {ctx.author.name}", 
                         icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.timestamp = datetime.datetime.utcnow()
        
        # Create view with pagination buttons
        view = BalanceLeaderboardView(self, ctx, page, total_pages)
        
        # Send embed with view
        view.message = await ctx.send(embed=embed, view=view)

    async def add_balance(self, user_id, amount):
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
        
        # Save updated data
        with open('data/bank.json', 'w') as f:
            json.dump(users, f)
            
        return users[user_id]["wallet"]
    
    async def remove_balance(self, user_id, amount):
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
        
        # Save updated data
        with open('data/bank.json', 'w') as f:
            json.dump(users, f)
            
        return True