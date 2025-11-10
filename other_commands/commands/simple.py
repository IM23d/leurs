"""
Simple utility commands.
"""

import discord
from discord.ext import commands
import random
import os
import requests

class SimpleCommands(commands.Cog):
    def __init__(self, client):
        self.client = client
        
    @commands.command()
    async def code(self, ctx):
        """Display a mysterious code."""
        await ctx.send("zgte5dr6ftgzhujikokztrdeswa536edfr65fm ,WU83 34 FTZFTBFTBF7677U6")
    
    @commands.command()
    async def geschichte(self, ctx):
        """Tell a German story."""
        await ctx.send("ich habe mal david in migros getroffen und ein foto mit david gemacht. das hat mich glücklich gemacht. dann hatten wir französisch...")
    
    @commands.command()
    async def info(self, ctx):
        """Show bot information."""
        embed = discord.Embed(
            title="Leurs: Discord Balance Bot",
            description="A Discord bot for managing balances and other utilities.",
            color=0xFFFFFF
        )
        
        embed.add_field(name="GitHub Repository", value="https://github.com/IM23d/leurs", inline=False)
        embed.add_field(name="Developers", value="@bettercallmilan, @reazndev", inline=True)
        embed.add_field(name="Contributors", value="@lhilfiker", inline=True)
        embed.add_field(name="Was also there", value="@seakyy", inline=True)
        embed.add_field(name="Version", value="1.0.0", inline=True)
        embed.add_field(name="Commands", value="Use `-help` to see all available commands", inline=False)
        
        embed.set_footer(text="Leurs: Discord Balance Bot")
        
        await ctx.send(embed=embed)

    @commands.command()
    async def david(self, ctx):
        """Send a random David image."""
        random_num_david = random.randint(1, 20)
        jpeg_path = f"images/david/{random_num_david}.jpeg"
        gif_path = f"images/david/{random_num_david}.gif"
        
        if os.path.exists(jpeg_path):
            file = discord.File(jpeg_path)
        elif os.path.exists(gif_path):
            file = discord.File(gif_path)
        else:
            await ctx.send("Couldn't find image for David")
            return
            
        await ctx.send(file=file)

    @commands.command()
    async def hwmo(self, ctx):
        """Check if we have school tomorrow."""
        await ctx.send("https://habenwirmorgenopl.info (might be down)")

    @commands.command()
    async def hi(self, ctx):
        """Greet the bot."""
        await ctx.send("Hi I'm coffee!")
    
    @commands.command()
    async def lyric(self, ctx):
        """Send a random lyric."""
        random_num_lyric = random.randint(1, 7)
        file_path = f"data/{random_num_lyric}.txt"

        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                content = file.read()
            await ctx.send(content)
        else:
            await ctx.send("Couldn't find the lyric file")

    @commands.command()
    async def github(self, ctx):
        """Send GitHub help link."""
        await ctx.send("https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request")
        
    @commands.command(aliases=['fortune', 'cookie', 'fc'])
    async def fortunecookie(self, ctx):
        """Get a fortune cookie."""
        try:
            temp_msg = await ctx.send("Breaking open a fortune cookie...")
            
            response = requests.get("https://api.viewbits.com/v1/fortunecookie?mode=random")
            
            if response.status_code != 200:
                await temp_msg.edit(content="Failed to get a fortune cookie. Try again later.")
                return
                
            fortune_data = response.json()
            
            # Extract and clean the fortune text
            fortune_text = fortune_data.get("text", "No fortune found")
            fortune_text = fortune_text.replace("\\u2019", "'").replace("\\u2018", "'")
            fortune_text = fortune_text.replace("\\u201c", """).replace("\\u201d", """)
            
            embed = discord.Embed(
                title="🥠 Fortune Cookie",
                description=f"**{fortune_text}**",
                color=0xFFD700
            )
            
            await ctx.send(embed=embed)
            await temp_msg.delete()
            
        except Exception as e:
            await ctx.send(f"Error getting fortune cookie: {str(e)}")

async def setup(client):
    """Setup function for the Simple commands."""
    client.add_cog(SimpleCommands(client))