import discord
from discord.ext import commands
import random
import json
import os
import datetime

class GamblingCog(commands.Cog):
    def __init__(self, client):
        self.client = client
    
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

        if str(user.id) in users:
            return False
        else:
            users[str(user.id)] = {}
            users[str(user.id)]["wallet"] = 0
            users[str(user.id)]["bank"] = 0

        with open('data/bank.json', 'w') as f:
            json.dump(users, f)
        return True
    
    @commands.command()
    async def gamble(self, ctx, amount=None):
        await self.open_account(ctx.author)
        users = await self.get_bank_data()
        user = ctx.author
        
        if amount is None:
            embed = discord.Embed(
                title="Error",
                description="Please specify an amount to gamble",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
            
        if amount == "all":
            amount = users[str(user.id)]["wallet"]
        elif isinstance(amount, str) and "%" in amount:
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
        
        wallet_amt = users[str(user.id)]["wallet"]
        
        if amount <= 0:
            embed = discord.Embed(
                title="Error",
                description="Amount must be positive!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
            
        if amount > wallet_amt:
            embed = discord.Embed(
                title="Error",
                description="You don't have enough coins!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Coin flip - heads or tails
        result = "heads" if random.randint(1, 2) == 1 else "tails"
        win = result == "heads"  # Win on heads, lose on tails
        
        # Update balance
        if win:
            users[str(user.id)]["wallet"] += amount
            new_balance = users[str(user.id)]["wallet"]
            color = discord.Color.green()
            title = "You Won!"
            description = f"The coin landed on **{result}**! You won **{amount} coins**!"
        else:
            users[str(user.id)]["wallet"] -= amount
            new_balance = users[str(user.id)]["wallet"]
            color = discord.Color.red()
            title = "You Lost!"
            description = f"The coin landed on **{result}**! You lost **{amount} coins**!"
        
        # Save updated data
        with open('data/bank.json', 'w') as f:
            json.dump(users, f)
        
        # Create and send embed
        embed = discord.Embed(
            title=title,
            description=description,
            color=color
        )
        
        embed.add_field(
            name="New Balance", 
            value=f"{new_balance} coins",
            inline=False
        )
        
        # Remove thumbnail images and just use color coding
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.timestamp = datetime.datetime.utcnow()
        
        await ctx.send(embed=embed)
import discord
from discord.ext import commands
import random
import json
import os
import datetime

class GamblingCog(commands.Cog):
    def __init__(self, client):
        self.client = client
    
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

        if str(user.id) in users:
            return False
        else:
            users[str(user.id)] = {}
            users[str(user.id)]["wallet"] = 0
            users[str(user.id)]["bank"] = 0

        with open('data/bank.json', 'w') as f:
            json.dump(users, f)
        return True
    
    @commands.command()
    async def gamble(self, ctx, amount=None):
        await self.open_account(ctx.author)
        users = await self.get_bank_data()
        user = ctx.author
        
        if amount is None:
            embed = discord.Embed(
                title="Error",
                description="Please specify an amount to gamble",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
            
        if amount == "all":
            amount = users[str(user.id)]["wallet"]
        elif isinstance(amount, str) and "%" in amount:
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
        
        wallet_amt = users[str(user.id)]["wallet"]
        
        if amount <= 0:
            embed = discord.Embed(
                title="Error",
                description="Amount must be positive!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
            
        if amount > wallet_amt:
            embed = discord.Embed(
                title="Error",
                description="You don't have enough coins!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Coin flip - heads or tails
        result = "heads" if random.randint(1, 2) == 1 else "tails"
        win = result == "heads"  # Win on heads, lose on tails
        
        # Update balance
        if win:
            users[str(user.id)]["wallet"] += amount
            new_balance = users[str(user.id)]["wallet"]
            color = discord.Color.green()
            title = "You Won!"
            description = f"The coin landed on **{result}**! You won **{amount} coins**!"
        else:
            users[str(user.id)]["wallet"] -= amount
            new_balance = users[str(user.id)]["wallet"]
            color = discord.Color.red()
            title = "You Lost!"
            description = f"The coin landed on **{result}**! You lost **{amount} coins**!"
        
        # Save updated data
        with open('data/bank.json', 'w') as f:
            json.dump(users, f)
        
        # Create and send embed
        embed = discord.Embed(
            title=title,
            description=description,
            color=color
        )
        
        embed.add_field(
            name="New Balance", 
            value=f"{new_balance} coins",
            inline=False
        )
        
        # Remove thumbnail images and just use color coding
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.timestamp = datetime.datetime.utcnow()
        
        await ctx.send(embed=embed)