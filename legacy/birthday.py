import discord
from discord.ext import commands
import json
import os
from datetime import datetime, date, timedelta
from collections import defaultdict
import asyncio
from typing import Dict, List, Tuple, Optional

class DeletedMessage:
    def __init__(self, content: str, author: discord.Member, deleted_at: datetime,
                 attachments: List[Dict[str, str]], embeds: List[discord.Embed]):
        self.content = content
        self.author = author
        self.deleted_at = deleted_at
        self.attachments = attachments
        self.embeds = embeds

class BirthdayCog(commands.Cog, name="birthday"):
    def __init__(self, bot):
        self.bot = bot
        self.birthdays_file = "data/birthdays.json"
        self.load_birthdays()
        self.deleted_messages: Dict[int, List[DeletedMessage]] = defaultdict(list)
        self.bot.loop.create_task(self.clean_old_messages())

    def load_birthdays(self):
        if not os.path.exists("data"):
            os.makedirs("data")
        
        if os.path.exists(self.birthdays_file):
            with open(self.birthdays_file, "r") as f:
                self.birthdays = json.load(f)
        else:
            self.birthdays = {}
            self.save_birthdays()

    def save_birthdays(self):
        with open(self.birthdays_file, "w") as f:
            json.dump(self.birthdays, f, indent=4)

    def get_next_birthday_timestamp(self, birthday_str):
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

    def calculate_next_age(self, birthday_str):
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

    def get_next_birthday_date(self, birthday_str):
        # Convert stored date string to date object
        birthday = datetime.strptime(birthday_str, "%d-%m-%Y").date()
        today = date.today()
        
        # Create this year's birthday
        this_year_bday = date(today.year, birthday.month, birthday.day)
        
        # If this year's birthday has passed, use next year's birthday
        if this_year_bday < today:
            return date(today.year + 1, birthday.month, birthday.day)
        return this_year_bday

    @commands.group(name="bday", invoke_without_command=True)
    async def birthday(self, ctx, member: discord.Member = None):
        target_member = member or ctx.author
        user_id = str(target_member.id)

        if user_id not in self.birthdays:
            embed = discord.Embed(
                description=f"❌ {target_member.mention} hasn't set their birthday yet!" if member else "❌ You haven't set your birthday yet! Use `bday set DD-MM-YYYY` to set it.",
                color=0x2F3136
            )
            await ctx.send(embed=embed)
            return

        birthday_date = self.birthdays[user_id]
        next_birthday_ts = self.get_next_birthday_timestamp(birthday_date)
        formatted_date = datetime.strptime(birthday_date, "%d-%m-%Y").strftime("%B %d")
        next_age = self.calculate_next_age(birthday_date)

        if target_member == ctx.author:
            description = f"Your **birthday** is **{formatted_date}**. That's <t:{next_birthday_ts}:R>!\nYou'll turn **{next_age}**!"
        else:
            description = f"{target_member.mention}'s **birthday** is **{formatted_date}**. That's <t:{next_birthday_ts}:R>!\nThey'll turn **{next_age}**!"

        embed = discord.Embed(
            description=description,
            color=0x2F3136 
        )
        
        await ctx.send(embed=embed)

    @birthday.command(name="set")
    async def set_birthday(self, ctx, date_str: str):
        try:
            try:
                birthday_date = datetime.strptime(date_str, "%d-%m-%Y")
            except ValueError:
                try:
                    birthday_date = datetime.strptime(date_str, "%d.%m.%Y")
                except ValueError:
                    embed = discord.Embed(
                        description="❌ Invalid date format! Please use DD-MM-YYYY or DD.MM.YYYY (e.g., 31-12-2000 or 31.12.2000)",
                        color=0x2F3136
                    )
                    await ctx.send(embed=embed)
                    return
            
            if birthday_date.date() > date.today():
                embed = discord.Embed(
                    description="❌ You can't set a birthday in the future!",
                    color=0x2F3136
                )
                await ctx.send(embed=embed)
                return
            
            if birthday_date.year < 1900:
                embed = discord.Embed(
                    description="❌ Please enter a valid year after 1900!",
                    color=0x2F3136
                )
                await ctx.send(embed=embed)
                return

            date_str_standard = birthday_date.strftime("%d-%m-%Y")
            self.birthdays[str(ctx.author.id)] = date_str_standard
            self.save_birthdays()

            # Format response
            formatted_date = birthday_date.strftime("%B %d")
            next_birthday_ts = self.get_next_birthday_timestamp(date_str_standard)
            next_age = self.calculate_next_age(date_str_standard)
            
            embed = discord.Embed(
                description=f"Your **birthday** is **{formatted_date}**. That's <t:{next_birthday_ts}:R>!\nYou'll turn **{next_age}**!",
                color=0x2F3136
            )
            await ctx.send(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                description="❌ Invalid date format! Please use DD-MM-YYYY or DD.MM.YYYY (e.g., 31-12-2000 or 31.12.2000)",
                color=0x2F3136
            )
            await ctx.send(embed=embed)

    @birthday.command(name="list")
    async def list_birthdays(self, ctx):
        if not self.birthdays:
            embed = discord.Embed(
                description="No birthdays have been set yet!",
                color=0x2F3136
            )
            await ctx.send(embed=embed)
            return

        # Get all birthdays and sort them by next occurrence
        upcoming = []
        for user_id, bday in self.birthdays.items():
            try:
                member = await ctx.guild.fetch_member(int(user_id))
                if member:  # Only include members still in the server
                    next_date = self.get_next_birthday_date(bday)
                    next_age = self.calculate_next_age(bday)
                    upcoming.append((next_date, member, next_age))
            except discord.NotFound:
                continue

        # Sort by next occurrence
        upcoming.sort(key=lambda x: x[0])

        if not upcoming:
            embed = discord.Embed(
                description="No upcoming birthdays found!",
                color=0x2F3136
            )
            await ctx.send(embed=embed)
            return

        upcoming = upcoming[:10]

        embed = discord.Embed(
            title="🎂 Upcoming Birthdays",
            color=0x2F3136,
            description="\n".join(
                f"{member.mention}\nTurns **{next_age}** on **{next_date.strftime('%B %d')}**\n(<t:{int(datetime.combine(next_date, datetime.min.time()).timestamp())}:R>)\n"
                for next_date, member, next_age in upcoming
            )
        )

        await ctx.send(embed=embed)

    async def clean_old_messages(self):
        while True:
            try:
                current_time = datetime.utcnow()
                for channel_id in list(self.deleted_messages.keys()):
                    self.deleted_messages[channel_id] = [
                        msg for msg in self.deleted_messages[channel_id]
                        if (current_time - msg.deleted_at).total_seconds() < 7200
                    ]
                    # Remove empty channel entries
                    if not self.deleted_messages[channel_id]:
                        del self.deleted_messages[channel_id]
                await asyncio.sleep(300)  # Clean every 5 minutes
            except Exception as e:
                print(f"Error in clean_old_messages: {e}")
                await asyncio.sleep(300)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return

        # Store attachment information
        attachments = []
        for attachment in message.attachments:
            attachments.append({
                'url': attachment.url,
                'filename': attachment.filename,
                'content_type': attachment.content_type if hasattr(attachment, 'content_type') else None,
                'size': attachment.size
            })

        # Create DeletedMessage object
        deleted_msg = DeletedMessage(
            content=message.content,
            author=message.author,
            deleted_at=datetime.utcnow(),
            attachments=attachments,
            embeds=message.embeds
        )
        
        # Store the deleted message
        self.deleted_messages[message.channel.id].append(deleted_msg)

    @commands.command(name='s')
    async def snipe(self, ctx):
        channel_id = ctx.channel.id
        if channel_id not in self.deleted_messages or not self.deleted_messages[channel_id]:
            embed = discord.Embed(
                description="❌ No recently deleted messages found in this channel!",
                color=0x2F3136
            )
            await ctx.send(embed=embed)
            return

        # Get the most recent deleted message
        deleted_msg = self.deleted_messages[channel_id][-1]
        
        embed = discord.Embed(
            color=0x2F3136,
            timestamp=deleted_msg.deleted_at
        )
        
        embed.set_author(
            name=f"{deleted_msg.author.name}#{deleted_msg.author.discriminator}",
            icon_url=deleted_msg.author.avatar.url if deleted_msg.author.avatar else None
        )
        
        if deleted_msg.content:
            embed.description = deleted_msg.content

        if deleted_msg.attachments:
            image_attachments = [
                att for att in deleted_msg.attachments
                if att.get('content_type', '').startswith('image/')
                or any(att['filename'].lower().endswith(ext) for ext in ('.png', '.jpg', '.jpeg', '.gif', '.webp'))
            ]
            
            if image_attachments:
                embed.set_image(url=image_attachments[0]['url'])
            
            attachment_list = []
            for i, att in enumerate(deleted_msg.attachments, 1):
                size_mb = att['size'] / (1024 * 1024)
                attachment_list.append(
                    f"[{att['filename']}]({att['url']}) ({size_mb:.2f}MB)"
                )
            
            if attachment_list:
                embed.add_field(
                    name="📎 Attachments",
                    value="\n".join(attachment_list),
                    inline=False
                )

        embed.set_footer(text="Message deleted")
        
        await ctx.send(embed=embed)
        
        for original_embed in deleted_msg.embeds:
            try:
                await ctx.send(embed=original_embed)
            except:
                continue

    @commands.command(name='cs')
    async def clear_snipe(self, ctx):
        channel_id = ctx.channel.id
        if channel_id in self.deleted_messages:
            del self.deleted_messages[channel_id]
        await ctx.message.add_reaction('✅')

async def setup(bot):
    await bot.add_cog(BirthdayCog(bot)) 